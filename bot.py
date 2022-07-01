from utils.spotify import *
from utils.database import MusicDatabase, Guild
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s;%(levelname)s;%(message)s")

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

db = MusicDatabase()

FOLLOW_ROLE_EMOJI = '✅'
UNFOLLOW_ROLE_EMOJI = '❌'

SET_COMMAND = "setchannel"
FOLLOW_COMMAND = "follow"
LIST_COMMAND = "list"


@client.event
async def on_ready():
    logging.info('We have logged in as {0.user}'.format(client))
    check_new_releases.start()


# You could optimize this by avoiding spotify calls if we've already updated for this artist within this day
@tasks.loop(minutes=15)
async def check_new_releases():
    logging.info('Checking for new releases')
    followed_artists = db.get_all_artists()
    spotify_artists = await get_artists_from_spotify(set(a.id for a in followed_artists))
    for followed_artist in followed_artists:
        guild = client.get_guild(followed_artist.guild_id)
        if guild is None:
            db.remove_guild(followed_artist.guild_id)
            continue

        channel_id = db.get_music_channel_id_for_guild_id(followed_artist.guild_id)
        channel = guild.get_channel(channel_id)
        if channel is None:
            continue

        artist_role = channel.guild.get_role(int(followed_artist.role_id))
        if artist_role is None:
            db.remove_artist(followed_artist)
            continue

        newest_release = await get_newest_release_by_artist_from_spotify(spotify_artists[followed_artist.id])

        if newest_release is None:
            continue

        relevant_artists = []
        all_newest_release_ids = []
        all_newest_release_names = []
        curr_guild_artists = db.get_all_artists_for_guild(followed_artist.guild_id)
        for artist in newest_release['artists']:
            if artist['id'] in curr_guild_artists.keys():
                relevant_artists.append(curr_guild_artists[artist['id']])
                all_newest_release_ids.append(curr_guild_artists[artist['id']].latest_release_id)
                all_newest_release_names.append(curr_guild_artists[artist['id']].latest_release_name)

        # If we haven't already notified the guild of this release
        if newest_release['id'] not in all_newest_release_ids \
                and newest_release['name'] not in all_newest_release_names:
            await notify_release(newest_release, relevant_artists, channel)


async def notify_release(release, artists, channel):
    logging.info(f"Notifying a new release by {artists[0].name} {artists[0].id} to Guild {channel.guild.id}")
    release_url = release['url'] if 'url' in release.keys() else release['external_urls']['spotify']
    message_text = ""
    for i in range(1, len(artists)):
        message_text += '<@&%s>, ' % artists[i].role_id
    message = await channel.send(message_text + "<@&%s> New Release!\n:white_check_mark:: Assign Role."
                                                ":x:: Remove Role.\n%s" % (artists[0].role_id, release_url))
    await add_role_reactions_to_message(message)
    db.set_latest_release_for_artists(artists=artists, new_release_id=release['id'], new_release_name=release['name'])


@slash.slash(
    name=SET_COMMAND,
    description="Set the current channel to the update channel",
)
async def set_update_channel(ctx: SlashContext):
    message = await ctx.send("Attempting to configure current channel for updates...")
    if not db.is_guild_in_db(ctx.guild_id):
        db.add_guild(Guild(ctx.guild_id, ctx.channel_id))
        await message.edit(content="Current channel successfully configured for updates. "
                                   f"You may begin following artists using `/{FOLLOW_COMMAND}`.")
    else:
        db.update_guild_channel_id(ctx.guild_id, ctx.channel_id)
        await message.edit(content="Current channel successfully configured for updates.")


@slash.slash(
    name=FOLLOW_COMMAND,
    description="follow a spotify artist by providing their spotify profile link",
    options=[
        create_option(
            name="artist_link",
            description="The artist's spotify share link",
            option_type=3,
            required=True
        )
    ]
)
async def follow_artist(ctx: SlashContext, artist_link: str):
    message = await ctx.send('Attempting to follow artist...')

    if not db.is_guild_in_db(ctx.guild_id):
        await message.edit(content=f"You must first use `/{SET_COMMAND}` to configure a channel to send updates to.")
        return
    try:
        artist_id = extract_artist_id(artist_link)
        artist = await get_artist_by_id(artist_id)
    except InvalidArtistException:
        await message.edit(content="Artist not found, please make sure you are providing a valid spotify artist url")
        return

    artist_in_db = db.get_artist_for_guild(artist.id, ctx.guild_id)
    if artist_in_db is not None:
        role = ctx.guild.get_role(int(artist_in_db.role_id))
        if role is None:
            db.remove_artist(artist_in_db)
        else:
            await message.edit(content='This server is already following %s! We\'ve assigned '
                                       'you the corresponding role.' % artist_in_db.name)
            await ctx.author.add_roles(role)
            return

    role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
    artist.role_id = role.id
    artist.guild_id = ctx.guild.id
    try:
        db.add_artist(artist)
    except Exception as e: # TODO: Make specific
        await message.edit(content="Failed to follow artist.")
        await role.delete()
        logging.exception('Failure to follow artist and add to db: ', str(e))
        return

    logging.info(f"Guild {ctx.guild_id} has followed a new artist: {artist.name} {artist.id}")
    await message.edit(
        content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                % (artist.role_id, artist.name))
    await add_role_reactions_to_message(message)
    await ctx.author.add_roles(role)


@slash.slash(
    name=LIST_COMMAND,
    description="list followed artists",
)
async def list_follows(ctx: SlashContext):
    message = await ctx.send('Attempting to list all followed artists...')
    artists = db.get_all_artists_for_guild(guild_id=ctx.guild_id)
    await message.edit(content="Following Artists: %s" % list(artist.name for artist in artists.values()))


@client.event
async def on_raw_reaction_add(payload):
    # Make sure this is a reaction to a valid message (one with a role)
    user = await client.fetch_user(payload.user_id)
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != client.user or user == client.user or len(message.content) < 1 or message.content[1] != '@':
        return
    guild = channel.guild
    member = payload.member
    reaction = payload.emoji
    role_string = message.content.split()[0]
    role_id = int(role_string[3:len(role_string) - 1])
    role = guild.get_role(role_id=role_id)
    if role is None:
        return
    if reaction.name == FOLLOW_ROLE_EMOJI:
        await member.add_roles(role)
    elif reaction.name == UNFOLLOW_ROLE_EMOJI:
        await member.remove_roles(role)


async def add_role_reactions_to_message(message):
    await message.add_reaction(FOLLOW_ROLE_EMOJI)
    await message.add_reaction(UNFOLLOW_ROLE_EMOJI)


client.run(os.environ.get('FANBOT_DISCORD_TOKEN'))
