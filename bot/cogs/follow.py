import services.spotify as sp
from discord.ext import commands
from discord.errors import Forbidden
from discord import app_commands
from discord.utils import get
import discord
import logging
from settings import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI, FOLLOW_COMMAND, SET_COMMAND

ATTEMPT_FOLLOW_MESSAGE = "'Attempting to follow artist...'"
CONFIGURE_CHANNEL_MESSAGE = f"A server admin must first use `/{SET_COMMAND}` to configure a channel to send updates to."
ARTIST_NOT_FOUND_MESSAGE = "Artist not found, please make sure you are providing a valid spotify artist url"
MISSING_MANAGE_ROLES_MESSAGE = "Bot is missing Manage Roles permission."


class Follow(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        logging.info(f'User {ctx.author.id} in guild {ctx.guild.id} used {ctx.command.name} with params: {ctx.args}')

    @app_commands.command(
        name=FOLLOW_COMMAND,
        description="Follow a spotify artist by their spotify profile share link",
    )
    async def follow_artist(self, interaction: discord.Interaction, artist_link: str):
        await interaction.response.send_message(ATTEMPT_FOLLOW_MESSAGE, ephemeral=True)

        if not self.bot.db.is_guild_exist(interaction.guild_id):
            await interaction.edit_original_response(content=CONFIGURE_CHANNEL_MESSAGE)
            return

        try:
            artist = await sp.get_artist_by_link(artist_link)
        except sp.InvalidArtistException:
            await interaction.edit_original_response(content=ARTIST_NOT_FOUND_MESSAGE)
            return

        try:
            role = await self.get_role_for_artist(artist, interaction.guild_id)
        except Forbidden:
            await interaction.edit_original_response(content=MISSING_MANAGE_ROLES_MESSAGE)
            return

        try:
            await self.handle_follow_artist_for_guild(interaction, artist, role)
        except:
            await interaction.edit_original_response(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db.')

    async def get_role_for_artist(self, artist, guild_id):
        guild = self.bot.get_guild(guild_id)
        role = None
        if self.bot.db.is_artist_exist(artist.id):
            role = get(guild.roles, name=f"{artist.name}Fan").id
        if role is None:
            role = await guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'), mentionable=True)
        return role

    async def handle_follow_artist_for_guild(self, interaction, artist, role):
        if self.bot.db.does_guild_follow_artist(interaction.guild_id, artist.id):
            await interaction.edit_original_response(
                content='This server is already following %s! We\'ve assigned you the corresponding role.' % artist.name)
        else:
            if self.bot.db.get_artist_by_id(artist.id) is None:
                self.bot.db.add_artist(artist, interaction.guild_id)
            else:
                self.bot.db.follow_existing_artist_for_guild(artist.id, interaction.guild_id)
            await self.send_successful_follow_message(artist, interaction)
        await interaction.user.add_roles(role)

    async def send_successful_follow_message(self, artist, interaction):
        logging.info(f"Guild {interaction.guild_id} has followed a new artist: {artist.name} {artist.id}")
        message = await self.bot.get_channel(interaction.channel_id).send(
            content="<@&%s> %s has been followed by %s!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name, interaction.user.name))
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)
