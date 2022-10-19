from utils.database import MusicDatabase
from discord.ext import commands
import cogs
import discord
from settings import DISCORD_TOKEN, logging


class FanBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.db = MusicDatabase()

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


bot = FanBot()
bot.run(DISCORD_TOKEN)
