from config.commands import *
from discord.ext import commands
from discord import app_commands
import discord


class List(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=LIST_COMMAND,
        description="list followed artists",
    )
    async def list_follows(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to list all followed artists...")
        artists = self.bot.db.get_all_artists_for_guild(guild_id=interaction.guild_id)
        await interaction.edit_original_message(
            content="Following Artists: %s" % list(artist.name for artist in artists.values()))
