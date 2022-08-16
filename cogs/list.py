from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Button
from utils.database import Artist
import discord
from settings import LIST_COMMAND

DEF_MSG = "Select a role to add or remove it. Page: "


class List(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=LIST_COMMAND,
        description="list followed artists and self-assign roles",
    )
    async def list_follows(self, interaction: discord.Interaction):
        artists = self.bot.db.get_all_artists_for_guild(guild_id=interaction.guild_id).values()
        artists = sorted(artists, key=lambda x: x.name)
        guild = self.bot.get_guild(interaction.guild_id)
        await interaction.response.send_message(content=DEF_MSG + '1', view=RoleAssignView(artists, guild),
                                                ephemeral=True)


class RoleAssignView(View):

    def __init__(self, artists: [Artist], guild: discord.Guild):
        super().__init__(timeout=None)
        self.offset = 0
        self.page = 1
        self.select_options = []
        self.guild = guild
        for artist in artists:
            self.select_options.append(discord.SelectOption(label=artist.name, value=artist.role_id))
        max_values = len(self.select_options) if len(self.select_options) < 25 else 25

        self.select = Select(placeholder="Select an artist", options=self.select_options[:25], max_values=max_values)
        self.select.callback = self.toggle_roles
        self.add_item(self.select)

        if len(self.select_options) > 25:
            self.next_button = Button(label="Next (2)", style=discord.ButtonStyle.blurple)
            self.prev_button = Button(label="Prev", style=discord.ButtonStyle.blurple)
            self.next_button.callback = self.page_next
            self.prev_button.callback = self.page_prev
            self.add_item(self.next_button)

    async def toggle_roles(self, interaction: discord.Interaction):
        roles = []
        for value in self.select.values:
            roles.append(self.guild.get_role(int(value)))
        roles_to_add = []
        roles_to_remove = []
        for role in roles:
            if interaction.user.get_role(role.id):
                roles_to_remove.append(role)
            else:
                roles_to_add.append(role)
        response_message = ""
        if len(roles_to_add) > 0:
            response_message += self.get_roles_added_string(roles_to_add)
            await interaction.user.add_roles(*roles_to_add)
        if len(roles_to_remove) > 0:
            response_message += self.get_roles_removed_string(roles_to_remove)
            await interaction.user.remove_roles(*roles_to_remove)
        await interaction.response.defer()
        await interaction.edit_original_message(content=response_message)

    async def page_next(self, interaction: discord.Interaction):
        self.page += 1
        self.offset += 25
        self.select.options = self.select_options[self.offset:self.offset+25]
        self.select.max_values = len(self.select.options)
        self.prev_button.label = f"Prev ({self.page-1})"
        self.next_button.label = f"Next ({self.page+1})"
        if self.offset == 25:
            self.remove_item(self.next_button)
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
        if self.offset + 25 > len(self.select_options):
            self.remove_item(self.next_button)
        await interaction.response.defer()
        content = DEF_MSG + f"{self.page}"
        await interaction.edit_original_message(content=content, view=self)

    async def page_prev(self, interaction: discord.Interaction):
        self.page -= 1
        self.offset -= 25
        if self.offset == 0:
            self.remove_item(self.prev_button)
        self.select.options = self.select_options[self.offset:self.offset+25]
        self.select.max_values = 25
        self.prev_button.label = f"Prev ({self.page-1})"
        self.next_button.label = f"Next ({self.page+1})"
        self.remove_item(self.next_button)
        self.add_item(self.next_button)
        await interaction.response.defer()
        content = DEF_MSG + f"{self.page}"
        await interaction.edit_original_message(content=content, view=self)

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


