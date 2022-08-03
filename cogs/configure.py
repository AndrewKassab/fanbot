from config.commands import *
from utils.database import Guild
from discord.ext import commands
from discord import app_commands
import discord


class Configure(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=SET_COMMAND,
        description="Set the current channel to the update channel",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_update_channel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to configure current channel for updates...")
        if not self.bot.db.is_guild_in_db(interaction.guild_id):
            self.bot.db.add_guild(Guild(interaction.guild_id, interaction.channel_id))
            await interaction.edit_original_message(content="Channel successfully configured for updates. You "
                                                            f"may begin following artists using `/{FOLLOW_COMMAND}`.")
        else:
            self.bot.db.update_guild_channel_id(interaction.guild_id, interaction.channel_id)
            await interaction.edit_original_message(content="Current channel successfully configured for updates.")

    @set_update_channel.error
    async def set_update_channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="Only Administrators can issue this command", ephemeral=True)
