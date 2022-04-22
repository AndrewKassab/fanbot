from utils.spotify import *
from db.database import *
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

guild_ids = [698320737739603980]
music_channel_id = 885018850981195817

FOLLOW_ROLE_EMOJI = ''
UNFOLLOW_ROLE_EMOJI = ''

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    send_new_releases.start()


@tasks.loop(minutes=1)
async def send_new_releases():
    channel = client.get_channel(music_channel_id)
    artists = get_all_artists_from_db()
    for artist in artists:
        newest_release = get_newest_release_by_artist_id(artist.id)
        if newest_release is None:
            continue
        latest_notified_release_id = get_latest_notified_release_for_artist_id(artist.id)
        newest_release_id = newest_release['id']
        # If we haven't already notified the channel of this release
        if latest_notified_release_id != newest_release_id:
            set_latest_notified_release_for_artist_id(artist_id=artist.id, new_release_id=newest_release_id)
            release_url = newest_release['external_urls']['spotify']
            await channel.send("<@&%s> %s has a new release! : %s" % (artist.role_id, artist.name, release_url))


@slash.slash(
    name="follow",
    description="follow artist",
    guild_ids=guild_ids,
    options=[
        create_option(
            name="artist_name",
            description="The name of the artist",
            option_type=3,
            required=True
        )
    ]
)
async def follow_artist(ctx: SlashContext, artist_name: str):
    try:
        artist = get_artist_by_name(str(artist_name))
    except InvalidArtistException:
        await ctx.send("Artist not found")
        return
    try:
        role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        add_artist_to_db(artist)
        await ctx.author.add_roles(role)
        await ctx.send('<@&%s> %s has been followed!' % (artist.role_id, artist.name))
    except ArtistAlreadyExistsException or Exception:
        await ctx.send('You are already following %s!' % artist.name)


@slash.slash(
    name="unfollow",
    description="unfollow artist",
    guild_ids=guild_ids,
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
        remove_artist_from_db(artist_name)
        await ctx.send('%s has been unfollowed!' % artist_name)
    except NotFollowingArtistException:
        await ctx.send('You are not following any artist named %s!' % artist_name)


@slash.slash(
    name="list",
    description="list followed artists",
    guild_ids=guild_ids,
)
async def list_follows(ctx: SlashContext):
    artists = get_all_artists_from_db()
    await ctx.send("Following Artists: %s" % list(artist.name for artist in artists))


# TODO:
@client.event
async def on_reaction_add_role(reaction, user):
    if user != client.user:
        role_id = reaction.message.content.split()[0]
        if str(reaction.emoji) == FOLLOW_ROLE_EMOJI:
            pass
            # TODO Add role to user
        elif str(reaction.emoji) == UNFOLLOW_ROLE_EMOJI:
            pass
            # TODO Remove role from user

    pass

client.run(os.environ.get('MUSIC_BOT_TOKEN'))
