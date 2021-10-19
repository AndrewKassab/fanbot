import discord
from spotify import *
import sqlite3

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name != 'music':
        return

    if message.content.startswith('-follow'):
        await follow_artist(message)
    elif message.content.startswith('-unfollow'):
        await unfollow_artist(message)
    elif message.content.startswith('-followlist'):
        await show_follows(message)
    elif message.content.startswith('-help '):
        await show_help()


def follow_artist(message):
    artist_name = message.content[8:]
    if (len(artist_name)) == 0:
        message.channel.send('Please specify an artist name after this command')
        return
    try:
        artist_id = get_artist_id_by_name(str(artist_name))
    except InvalidArtistException:
        message.channel.send('Artist not found or invalid')
        return
    # TODO: Follow artist


async def unfollow_artist(message):
    pass


async def show_follows(message):
    pass


async def show_help():
    pass


async def check_new_releases():
    pass


client.run(os.getenv('MUSIC_BOT_TOKEN'))
