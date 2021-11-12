from spotify import *
from db.database import *
from discord.ext import tasks, commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

client = commands.Bot(command_prefix="/")
slash = SlashCommand(client, sync_commands=True)

guild_ids = [698320737739603980]


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@tasks.loop(minutes=1)
async def send_new_releases():
    print('here')
    channel = client.get_channel(885018850981195817)
    await channel.send("hello")


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


async def unfollow_artist(message):
    artist_name = message.content[10:]
    if (len(artist_name)) == 0:
        await message.channel.send('Please specify an artist name after this command')
        return
    try:
        remove_artist_from_db(artist_name)
        await message.channel.send('%s has been unfollowed!' % artist_name)
    except NotFollowingArtistException:
        await message.channel.send('You are not following any artist named %s!' % artist_name)


async def show_follows(message):
    artists = get_all_artists_from_db()
    await message.channel.send("Following Artists: %s" % artists)


async def check_new_releases():
    pass


client.run('ODg1MDAwODg4MTMxOTE1Nzk5.YTgrTg.Zb-DwOa6kXp42_5z-B-RLirQEjE')
