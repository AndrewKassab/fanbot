from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI
from config.commands import *
from utils.spotify import *
from utils.database import Guild
from discord.ext import commands
import logging
from bot import bot
from discord import app_commands


class AppCommandsCog(commands.Cog):

    slash = SlashCommand(bot, sync_commands=True)

    def __init__(self, db):
        self.db = db
        slash = SlashCommand(bot, sync_commands=True)

    @slash.slash(
        name=SET_COMMAND,
        description="Set the current channel to the update channel",
    )
    async def set_update_channel(self, ctx: SlashContext):
        message = await ctx.send("Attempting to configure current channel for updates...")
        if not self.db.is_guild_in_db(ctx.guild_id):
            self.db.add_guild(Guild(ctx.guild_id, ctx.channel_id))
            await message.edit(content="Current channel successfully configured for updates. "
                                       f"You may begin following artists using `/{FOLLOW_COMMAND}`.")
        else:
            self.db.update_guild_channel_id(ctx.guild_id, ctx.channel_id)
            await message.edit(content="Current channel successfully configured for updates.")

    @slash.slash(
        name=FOLLOW_COMMAND,
        description="follow a spotify artist by providing their spotify profile link",
        options=[
            create_option(
                name="artist_link",
                description="The artist's spotify share link",
                option_type=3,
                required=True
            )
        ]
    )
    async def follow_artist(self, ctx: SlashContext, artist_link: str):
        message = await ctx.send('Attempting to follow artist...')

        if not self.db.is_guild_in_db(ctx.guild_id):
            await message.edit(content=f"You must first use `/{SET_COMMAND}` to configure a channel to send updates to.")
            return
        try:
            artist_id = extract_artist_id(artist_link)
            artist = await get_artist_by_id(artist_id)
        except InvalidArtistException:
            await message.edit(content="Artist not found, please make sure you are providing a valid spotify artist url")
            return

        artist_in_db = self.db.get_artist_for_guild(artist.id, ctx.guild_id)
        if artist_in_db is not None:
            role = ctx.guild.get_role(int(artist_in_db.role_id))
            if role is None:
                self.db.remove_artist(artist_in_db)
            else:
                await message.edit(content='This server is already following %s! We\'ve assigned '
                                           'you the corresponding role.' % artist_in_db.name)
                await ctx.author.add_roles(role)
                return

        role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        artist.guild_id = ctx.guild.id
        try:
            self.db.add_artist(artist)
        except Exception as e: # TODO: Make specific
            await message.edit(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db: ', str(e))
            return

        logging.info(f"Guild {ctx.guild_id} has followed a new artist: {artist.name} {artist.id}")
        await message.edit(
            content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name))
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)
        await ctx.author.add_roles(role)

    @slash.slash(
        name=LIST_COMMAND,
        description="list followed artists",
    )
    async def list_follows(self, ctx: SlashContext):
        message = await ctx.send('Attempting to list all followed artists...')
        artists = self.db.get_all_artists_for_guild(guild_id=ctx.guild_id)
        await message.edit(content="Following Artists: %s" % list(artist.name for artist in artists.values()))




