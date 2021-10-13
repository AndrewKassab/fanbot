import discord
from spotify import *

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name != 'music':
        return

    if message.content.startswith('-follow'):
        artist_name = message.content[8:]
        if (len(artist_name)) == 0:
            await message.channel.send('Please specify an artist name after this command')
            return
        artist_id = get_artist_id_by_name(str(artist_name))
        await message.channel.send(artist_id)
    elif message.content.startswith('-unfollow'):
        await unfollow_artist(message)
    elif message.content.startswith('-followlist'):
        await show_follows(message)
    elif message.content.startswith('-help '):
        await show_help()
    else:
        return


async def follow_artist(artist_name, channel):
    pass


async def unfollow_artist(message):
    pass


async def show_follows(message):
    pass


async def show_help():
    pass


async def check_new_releases():
    pass


client.run(os.getenv('MUSIC_BOT_TOKEN'))
