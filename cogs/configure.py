from utils.database import Guild
from discord.ext import commands
from discord import app_commands
from settings import SET_COMMAND, FOLLOW_COMMAND, HELP_COMMAND, HELP_MESSAGE
import discord


class Configure(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=SET_COMMAND,
        description="Admins: Sets the current channel to the update channel where new releases will be sent.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_update_channel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to configure current channel for updates...", ephemeral=True)
        if not self.bot.db.is_guild_in_db(interaction.guild_id):
            self.bot.db.add_guild(Guild(interaction.guild_id, interaction.channel_id))
            await interaction.edit_original_message(content="Channel successfully configured for updates. You "
                                                            f"may begin following artists using `/{FOLLOW_COMMAND}`.")
        else:
            self.bot.db.update_guild_channel_id(interaction.guild_id, interaction.channel_id)
            await interaction.edit_original_message(content="Current channel successfully configured for updates.")

    @app_commands.command(
        name=HELP_COMMAND,
        description="How to use fanbot"
    )
    async def send_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(HELP_MESSAGE, ephemeral=True)


    @set_update_channel.error
    async def set_update_channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="Only Administrators can issue this command", ephemeral=True)
