from config.commands import *
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import discord


class List(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=LIST_COMMAND,
        description="list followed artists",
    )
    async def list_follows(self, interaction: discord.Interaction):
        artists = self.bot.db.get_all_artists_for_guild(guild_id=interaction.guild_id)
        select_options = []
        for artist in artists.values():
            select_options.append(discord.SelectOption(label=artist.name, value=artist.role_id))
        max_values = len(select_options) if len(select_options) < 25 else 25
        select = Select(placeholder="Select an artist", options=select_options, max_values=max_values)
        view = View()
        view.add_item(select)

        async def toggle_role(ctx):
            roles = []
            guild = self.bot.get_guild(ctx.guild_id)
            for value in select.values:
                roles.append(guild.get_role(int(value)))
            await ctx.user.add_roles(*roles)
            await ctx.response.send_message("Roles added", ephemeral=True)

        select.callback = toggle_role
        await interaction.response.send_message(view=view, ephemeral=True)

