from spotify import *
from db.database import *
from discord.ext import tasks, commands

client = commands.Bot(command_prefix="/")


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@tasks.loop(minutes=1)
async def send_new_releases():
    print('here')
    channel = client.get_channel(885018850981195817)
    await channel.send("hello")


@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name != 'music':
        return

    if message.content.startswith('-follow '):
        await follow_artist(message)
    elif message.content.startswith('-unfollow'):
        await unfollow_artist(message)
    elif message.content.startswith('-list'):
        await show_follows(message)


async def follow_artist(message):
    artist_name = message.content[8:]
    if (len(artist_name)) == 0:
        await message.channel.send('Please specify an artist name after this command')
        return
    try:
        artist = get_artist_by_name(str(artist_name))
    except InvalidArtistException:
        await message.channel.send(InvalidArtistException)
        return
    try:
        add_artist_to_db(artist)
        await message.channel.send('%s has been followed!' % artist.name)
    except ArtistAlreadyExistsException:
        await message.channel.send('You are already following %s!' % artist.name)


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


client.run(os.getenv('MUSIC_BOT_TOKEN'))
