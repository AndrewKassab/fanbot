from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI
from config.commands import *
from utils.spotify import *
from utils.database import MusicDatabase, Guild
from discord.ext import commands
from cogs.releases import ReleasesCog
from cogs.app_commands import AppCommandsCog
import logging
import discord

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s;%(levelname)s;%(message)s")

db = MusicDatabase()

bot = commands.Bot(command_prefix="/", intents=discord.Intents.default())


@bot.event
async def on_ready():
    logging.info('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_raw_reaction_add(payload):
    # Make sure this is a reaction to a valid message (one with a role)
    user = await bot.fetch_user(payload.user_id)
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != bot.user or user == bot.user or len(message.content) < 1 or message.content[1] != '@':
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


bot.add_cog(ReleasesCog(bot, db))
bot.add_cog(AppCommandsCog(db))

bot.run(os.environ.get('FANBOT_DISCORD_TOKEN'))
