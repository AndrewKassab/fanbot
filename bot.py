from utils.spotify import *
from db.database import *
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

music_channel_id = 885018850981195817

FOLLOW_ROLE_EMOJI = '✅'
UNFOLLOW_ROLE_EMOJI = '❌'


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    send_new_releases.start()


# You could optimize this by avoiding spotify calls if we've already updated for this artist within this day
@tasks.loop(minutes=1)
async def send_new_releases():
    channel = client.get_channel(music_channel_id)
    artists = get_all_artists_from_db()
    for artist in artists:
        artist_role = channel.guild.get_role(artist.role_id)
        if artist_role is None:
            remove_artist_from_db(artist.name)
            continue
        newest_release = get_newest_release_by_artist_id(artist.id)
        if newest_release is None:
            continue
        latest_notified_release_id = get_latest_notified_release_for_artist_id(artist.id)
        newest_release_id = newest_release['id']
        # If we haven't already notified the channel of this release
        if latest_notified_release_id != newest_release_id:
            set_latest_notified_release_for_artist_id(artist_id=artist.id, new_release_id=newest_release_id)
            release_url = newest_release['external_urls']['spotify']
            message = await channel.send("<@&%s> New Release!\nAssign Role: :white_check_mark: "
                                         "Remove Role: :x: %s" % (artist.role_id, release_url))
            await add_role_reactions_to_message(message)


@slash.slash(
    name="follow",
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
    try:
        artist = get_artist_by_name(str(artist_name_or_id))
    except InvalidArtistException:
        await ctx.send("Artist %s not found" % artist_name_or_id)
        return
    artist_in_db = get_artist_from_db(artist.name)
    if artist_in_db is not None:
        role = ctx.guild.get_role(int(artist_in_db.role_id))
        await ctx.send('This server is already following %s! We\'ve assigned you the corresponding role.' % artist_in_db.name)
    else:
        role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        add_artist_to_db(artist)
        message = await ctx.send("<@&%s> %s has been followed!\nAssign Role: :white_check_mark: Remove Role: :x:"
                                 % (artist.role_id, artist.name))
        await add_role_reactions_to_message(message)
    await ctx.author.add_roles(role)


@slash.slash(
    name="unfollow",
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
    try:
        artist = get_artist_from_db(artist_name)
        remove_artist_from_db(artist_name)
        role = ctx.guild.get_role(int(artist.role_id))
        if role is not None:
            await role.delete()
        await ctx.send('%s has been unfollowed!' % artist_name)
    except NotFollowingArtistException:
        await ctx.send('You are not following any artist named %s!' % artist_name)


@slash.slash(
    name="list",
    description="list followed artists",
)
async def list_follows(ctx: SlashContext):
    artists = get_all_artists_from_db()
    await ctx.send("Following Artists: %s" % list(artist.name for artist in artists))


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
        role_id = int(role_string[3:len(role_string)-1])
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
