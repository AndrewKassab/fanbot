from config.commands import *
from utils.database import Guild
from discord.ext import commands
from discord import app_commands
import discord


class ConfigureCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=SET_COMMAND,
        description="Set the current channel to the update channel",
    )
    async def set_update_channel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to configure current channel for updates...")
        if not self.bot.db.is_guild_in_db(interaction.guild_id):
            self.bot.db.add_guild(Guild(interaction.guild_id, interaction.channel_id))
            await interaction.edit_original_message(content="Current channel successfully configured for updates. "
                                                            f"You may begin following artists using `/{FOLLOW_COMMAND}`.")
        else:
            self.bot.db.update_guild_channel_id(interaction.guild_id, interaction.channel_id)
            await interaction.edit_original_message(content="Current channel successfully configured for updates.")

