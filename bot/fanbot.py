from services.fanbotdatabase import FanbotDatabase
from discord.ext import commands
import bot.cogs
import discord
from settings import logging


class FanBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.db = FanbotDatabase()

    async def setup_hook(self) -> None:
        await self.add_cog(cogs.Configure(self))
        await self.add_cog(cogs.List(self))
        await self.add_cog(cogs.Follow(self))
        await self.add_cog(cogs.Reactions(self))
        await self.add_cog(cogs.Releases(self))
        await self.tree.sync()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('We have logged in as {0.user}'.format(bot))
