from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI
from config.commands import *
from utils.spotify import *
from discord.ext import commands
from mysql.connector.errors import IntegrityError
import logging
from discord import app_commands
import discord


class FollowCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=FOLLOW_COMMAND,
        description="Follow a spotify artist",
    )
    async def follow_artist(self, interaction: discord.Interaction, artist_link: str):
        await interaction.response.send_message('Attempting to follow artist...')

        if not self.bot.db.is_guild_in_db(interaction.guild_id):
            await interaction.edit_original_message(
                content=f"You must first use `/{SET_COMMAND}` to configure a channel to send updates to.")
            return

        try:
            artist_id = extract_artist_id(artist_link)
            artist = await get_artist_by_id(artist_id)
        except InvalidArtistException:
            await interaction.edit_original_message(
                content="Artist not found, please make sure you are providing a valid spotify artist url")
            return

        artist.guild_id = interaction.guild_id
        role = await self.get_role_for_artist(artist)
        artist.role_id = role.id

        try:
            self.bot.db.add_artist(artist)
            await self.send_successful_follow_message(artist, interaction)
        except IntegrityError:
            await interaction.edit_original_message(content='This server is already following %s! We\'ve assigned '
                                                            'you the corresponding role.' % artist.name)
        except Exception as e:
            await interaction.edit_original_message(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db: ', e.msg)
            return

        await interaction.user.add_roles(role)

    async def get_role_for_artist(self, artist):
        artist_db = self.bot.db.get_artist_for_guild(artist.id, artist.guild_id)
        if artist_db is not None:
            role = self.bot.get_guild(artist_db.guild_id).get_role(artist_db.role_id)
            if role is None:
                self.bot.db.remove_artist(artist)
                role = await self.bot.get_guild(artist_db.guild_id).create_role(name=(artist_db.name.replace(" ", "") + 'Fan'))
        else:
            role = await self.bot.get_guild(artist.guild_id).create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        return role

    async def send_successful_follow_message(self, artist, interaction):
        logging.info(f"Guild {interaction.guild_id} has followed a new artist: {artist.name} {artist.id}")
        await interaction.edit_original_message(
            content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name))
        message = await interaction.original_message()
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)
