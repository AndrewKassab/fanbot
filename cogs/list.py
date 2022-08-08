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

        async def toggle_roles(ctx: discord.Interaction):
            roles = []
            guild = self.bot.get_guild(ctx.guild_id)
            for value in select.values:
                roles.append(guild.get_role(int(value)))
            roles_to_add = []
            roles_to_remove = []
            for role in roles:
                if ctx.user.get_role(role.id):
                    roles_to_remove.append(role)
                else:
                    roles_to_add.append(role)
            response_message = ""
            if len(roles_to_add) > 0:
                response_message += self.get_roles_added_string(roles_to_add)
                await ctx.user.add_roles(*roles_to_add)
            if len(roles_to_remove) > 0:
                response_message += self.get_roles_removed_string(roles_to_remove)
                await ctx.user.remove_roles(*roles_to_remove)
            await ctx.response.send_message(response_message)

        select.callback = toggle_roles
        await interaction.response.send_message(view=view, ephemeral=True)

    def get_roles_added_string(self, roles):
        msg = "Roles added:"
        for i in range(len(roles)-1):
            msg += f" {roles[i].name},"
        msg += f" {roles[-1].name}\n"
        return msg

    def get_roles_removed_string(self, roles):
        msg = "Roles removed:"
        for i in range(len(roles)-1):
            msg += f" {roles[i].name},"
        msg += f" {roles[-1].name}"
        return msg


