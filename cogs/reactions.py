import discord
from discord.ext import commands
from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI


class Reactions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Make sure this is a reaction to a valid message (one with a role)
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author != self.bot.user or user == self.bot.user or message.content[1] != '@':
            return
        guild = channel.guild
        member = payload.member
        reaction = payload.emoji
        role_string = message.content.split('>')[0]
        role_id = int(role_string[3:])
        role = guild.get_role(role_id)
        if role is None:
            return
        if reaction.name == FOLLOW_ROLE_EMOJI:
            await member.add_roles(role)
        elif reaction.name == UNFOLLOW_ROLE_EMOJI:
            await member.remove_roles(role)
