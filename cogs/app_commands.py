from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI
from config.commands import *
from utils.spotify import *
from utils.database import Guild
from discord.ext import commands
import logging
from discord import app_commands
import discord


class AppCommandsCog(commands.Cog):

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

    @app_commands.command(
        name=FOLLOW_COMMAND,
        description="Follow a spotify artist",

    )
    #@app_commands.describe(artist_link="The artist's spotify share link")
    async def follow_artist(self, interaction: discord.Interaction, artist_link: str):
        message = await interaction.response.send_message('Attempting to follow artist...')

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

        artist_in_db = self.bot.db.get_artist_for_guild(artist.id, interaction.guild_id)
        if artist_in_db is not None:
            role = interaction.guild.get_role(int(artist_in_db.role_id))
            if role is None:
                self.bot.db.remove_artist(artist_in_db)
            else:
                await interaction.edit_original_message(content='This server is already following %s! We\'ve assigned '
                                           'you the corresponding role.' % artist_in_db.name)
                await interaction.author.add_roles(role)
                return

        role = await interaction.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        artist.guild_id = interaction.guild.id
        try:
            self.bot.db.add_artist(artist)
        except Exception as e:  # TODO: Make specific
            await interaction.edit_original_message(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db: ', str(e))
            return

        logging.info(f"Guild {interaction.guild_id} has followed a new artist: {artist.name} {artist.id}")
        await interaction.edit_original_message(
            content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name))
        await interaction.message.add_reaction(FOLLOW_ROLE_EMOJI)
        await interaction.message.add_reaction(UNFOLLOW_ROLE_EMOJI)
        await message.author.add_roles(role)

    @app_commands.command(
        name=LIST_COMMAND,
        description="list followed artists",
    )
    async def list_follows(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attempting to list all followed artists...")
        artists = self.bot.db.get_all_artists_for_guild(guild_id=interaction.guild_id)
        await interaction.edit_original_message(
            content="Following Artists: %s" % list(artist.name for artist in artists.values()))
