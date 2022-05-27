from utils.spotify import *
from utils.cache import *
from utils.database import MusicDatabase, NotFollowingArtistException
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

db = MusicDatabase()

FOLLOW_ROLE_EMOJI = '✅'
UNFOLLOW_ROLE_EMOJI = '❌'

SET_COMMAND = "musicset"
FOLLOW_COMMAND = "musicfollow"
UNFOLLOW_COMMAND = "musicunfollow"
LIST_COMMAND = "musiclist"

# Cache for storing channel id for a guild
guild_to_channel = {}


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # send_new_releases.start()
    do_something.start()


@tasks.loop(minutes=2)
async def do_something():
    while True:
        continue


# You could optimize this by avoiding spotify calls if we've already updated for this artist within this day
# @tasks.loop(minutes=1)
async def send_new_releases():
    artists = db.get_all_artists()
    for artist in artists:
        channel_id = db.get_music_channel_id_for_guild_id(artist.id)
        channel = client.get_guild(int(artist.id)).get_channel(int(channel_id))
        # update channel hasn't been set yet
        if channel is None:
            continue
        artist_role = channel.guild.get_role(int(artist.role_id))
        # server has manually deleted this artist from their roles
        if artist_role is None:
            db.remove_artist_from_db(artist.name)
            continue
        newest_release = get_newest_release_by_artist_id(artist.id)
        if newest_release is None:
            continue
        newest_release_id = newest_release['id']
        # If we haven't already notified the channel of this release
        if artist.latest_release_id != newest_release_id:
            db.set_latest_notified_release_for_artist_in_guild(artist_id=artist.id, new_release_id=newest_release_id)
            release_url = newest_release['external_urls']['spotify']
            message = await channel.send("<@&%s> New Release!\n:white_check_mark:: Assign Role."
                                         ":x:: Remove Role.\n%s" % (artist.role_id, release_url))
            await add_role_reactions_to_message(message)




@slash.slash(
    name=SET_COMMAND,
    description="Use in the desired channel to receive updates",
)
async def set_update_channel(ctx: SlashContext):
    message = await ctx.send("Attempting to configure current channel for updates...")
    if not db.is_guild_in_db(ctx.guild_id):
        db.add_guild_to_db(ctx.guild_id, ctx.channel_id)
        await message.edit(content="Current channel successfully configured for updates. "
                                   f"You may begin following artists using `/{FOLLOW_COMMAND}`.")
    else:
        db.update_guild_channel_id(ctx.guild_id, ctx.channel_id)
        await message.edit(content="Current channel successfully configured for updates.")
    guild_to_channel[ctx.guild_id] = ctx.channel_id


@slash.slash(
    name=FOLLOW_COMMAND,
    description="follow artist",
    options=[
        create_option(
            name="artist_name_or_id",
            description="The name of the artist or their id",
            option_type=3,
            required=True
        )
    ]
)
async def follow_artist(ctx: SlashContext, artist_name_or_id: str):
    message = await ctx.send(f'Attempting to follow artist {artist_name_or_id}...')
    if not db.is_guild_in_db(ctx.guild_id):
        await message.edit(content=f"You must first use `/{SET_COMMAND}` to configure a channel to send updates to.")
        return
    try:
        artist = get_artist_by_name(str(artist_name_or_id))
    except InvalidArtistException:
        await message.edit(content="Artist %s not found" % artist_name_or_id)
        return
    artist_in_db = db.get_artist_by_name(artist.name)
    if artist_in_db is not None:
        role = ctx.guild.get_role(int(artist_in_db.role_id))
        await message.edit(content='This server is already following %s! We\'ve assigned '
                                   'you the corresponding role.' % artist_in_db.name)
    else:
        role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        artist.id = ctx.guild.id
        db.add_artist_to_db(artist)
        await message.edit(
            content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name))
        await add_role_reactions_to_message(message)
    await ctx.author.add_roles(role)


@slash.slash(
    name=UNFOLLOW_COMMAND,
    description="unfollow artist",
    options=[
        create_option(
            name="artist_name",
            description="The name of the artist",
            option_type=3,
            required=True
        )
    ]
)
async def unfollow_artist(ctx: SlashContext, artist_name: str):
    message = await ctx.send(f'Attempting to unfollow artist {artist_name}...')
    try:
        artist = db.get_artist_by_name(artist_name)
        db.remove_artist_from_db(artist_name)
        role = ctx.guild.get_role(int(artist.role_id))
        if role is not None:
            await role.delete()
        await message.edit(content='%s has been unfollowed!' % artist_name)
    except NotFollowingArtistException:
        await message.edit(content='You are not following any artist named %s!' % artist_name)


@slash.slash(
    name=LIST_COMMAND,
    description="list followed artists",
)
async def list_follows(ctx: SlashContext):
    message = await ctx.send('Attempting to list all followed artists...')
    artists = db.get_all_artists()
    await message.edit(content="Following Artists: %s" % list(artist.name for artist in artists))


@client.event
async def on_raw_reaction_add(payload):
    channel = await client.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await client.fetch_user(payload.user_id)
    guild = channel.guild
    member = payload.member
    reaction = payload.emoji
    # Make sure this is a reaction to a valid message (one with a role)
    if user != client.user and message.content[1] == '@':
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


client.run(os.environ.get('MUSIC_BOT_TOKEN'))
