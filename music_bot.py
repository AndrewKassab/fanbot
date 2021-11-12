from spotify import *
from db.database import *
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

guild_ids = [698320737739603980]
music_channel_id = 885018850981195817


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    send_new_releases.start()


@tasks.loop(seconds=15)
async def send_new_releases():
    channel = client.get_channel(music_channel_id)
    artists = get_all_artists_from_db()
    for artist in artists:
        print(artist.name)
        new_releases = get_new_releases_by_artist_id(artist.id)
        print(new_releases)
        if len(new_releases) > 0:
            await channel.send("%s has a new song!: " % artist.name)


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
        add_artist_to_db(artist)
        await ctx.send('%s has been followed!' % artist.name)
    except ArtistAlreadyExistsException:
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
    if (len(artist_name)) == 0:
        await ctx.send('Please specify an artist name after this command')
        return
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


client.run(os.environ.get('MUSIC_BOT_TOKEN'))
