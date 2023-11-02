import services.spotify as sp
from discord.ext import commands
from discord.errors import Forbidden
from discord import app_commands
from discord.utils import get
import discord
import logging
from settings import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI, FOLLOW_COMMAND, SET_COMMAND
from sqlalchemy.exc import IntegrityError

CONFIGURE_CHANNEL_MESSAGE = f"A server admin must first use `/{SET_COMMAND}` to configure a channel to send updates to."


class Follow(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=FOLLOW_COMMAND,
        description="Follow a spotify artist by their spotify profile share link",
    )
    async def follow_artist(self, interaction: discord.Interaction, artist_link: str):
        logging.info(f'User {interaction.user.id} in guild {interaction.guild.id} used follow with param: {artist_link}')
        await interaction.response.send_message('Attempting to follow artist...', ephemeral=True)

        is_exist = self.bot.db.is_guild_exist(interaction.guild_id)

        if not self.bot.db.is_guild_exist(interaction.guild_id):
            await interaction.edit_original_response(content=CONFIGURE_CHANNEL_MESSAGE)
            return

        try:
            artist = await sp.get_artist_by_link(artist_link)
        except sp.InvalidArtistException:
            await interaction.edit_original_response(
                content="Artist not found, please make sure you are providing a valid spotify artist url")
            return

        guild_id = interaction.guild_id
        try:
            role = await self.get_role_for_artist(artist,guild_id)
        except Forbidden:
            await interaction.edit_original_response(content='Bot is missing Manage Roles permission.')
            return

        try:
            self.bot.db.add_artist(artist)
            await self.send_successful_follow_message(artist, interaction)
        except IntegrityError:
            await interaction.edit_original_response(content='This server is already following %s! We\'ve assigned '
                                                            'you the corresponding role.' % artist.name)
        except:
            await interaction.edit_original_response(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db.')
            return

        await interaction.user.add_roles(role)

    async def get_role_for_artist(self, artist, guild_id):
        guild = self.bot.get_guild(guild_id)
        role = None
        if self.bot.db.is_artist_exist(artist.id):
            role = get(guild.roles, name=f"{artist.name}Fan").id
        if role is None:
            role = await guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'), mentionable=True)
        return role

    async def send_successful_follow_message(self, artist, interaction):
        logging.info(f"Guild {interaction.guild_id} has followed a new artist: {artist.name} {artist.id}")
        message = await self.bot.get_channel(interaction.channel_id).send(
            content="<@&%s> %s has been followed by %s!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name, interaction.user.name))
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)
