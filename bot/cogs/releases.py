import copy

from discord.ext import commands, tasks
from discord.utils import get
import logging

from sqlalchemy.exc import OperationalError

import services.spotify as sp
from bot.helpers import get_fan_role_name
from services.fanbotdatabase import Artist

NEW_RELEASE_FORMATTER = "<@&%s> New Release!\n%s"


class Releases(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_new_releases.start()

    @tasks.loop(hours=4, reconnect=True)
    async def check_new_releases(self):
        logging.info('Checking for new releases')
        artists = self.bot.db.get_all_artists()
        for artist in artists:
            try:
                await self.check_new_release_for_artist(artist)
            except Exception as e:
                logging.exception(f"Error encountered when checking new releases for artist {artist.name}")
                continue

    async def check_new_release_for_artist(self, artist: Artist):
        if len(artist.guild_ids) == 0:
            self.bot.db.delete_artist_by_id(artist.id)

        newest_release = await sp.get_newest_release_by_artist(artist.id)

        if not self.is_new_release_valid(newest_release, artist):
            return

        for guild_id in copy.deepcopy(artist.guild_ids):
            guild = self.bot.db.get_guild_by_id(guild_id)
            if self.bot.get_guild(guild.id) is None:
                self.bot.db.delete_guild_by_id(guild.id)
                continue
            if self.bot.get_guild(guild.id).get_channel(guild.music_channel_id) is None:
                continue
            try:
                role_ids = self.get_role_ids(newest_release, guild)
            except OperationalError:
                logging.exception(
                    f"Error encountered when retrieving role IDs for artist {artist.name} in guild {guild.id}")
                continue
            if len(role_ids) == 0:
                self.bot.db.unfollow_artist_for_guild(artist.id, guild.id)
            else:
                logging.info(f"Notifying a new release by artist id {role_ids[0]} to Guild {guild.id}")
                channel = self.bot.get_guild(guild.id).get_channel(guild.music_channel_id)
                if channel is not None:
                    await self.notify_release(newest_release, role_ids, channel)

    def is_new_release_valid(self, release, artist):
        if release is None:
            return False
        if release['id'] == artist.latest_release_id or \
                release['name'] == artist.latest_release_name:
            return False
        # If this is a remix, but by another artist, ignore it.
        if 'remix' in release['name'].lower() and f'{artist.name.lower()} remix' \
                not in release['name'].lower():
            return False
        return True

    async def notify_release(self, release, role_ids, channel):
        release_url = release['url'] if 'url' in release.keys() else release['external_urls']['spotify']
        message_text = ""
        for i in range(1, len(role_ids)):
            message_text += '<@&%s>, ' % role_ids[i]
        await channel.send(message_text + NEW_RELEASE_FORMATTER % (role_ids[0], release_url))

    def get_role_ids(self, release, guild):
        relevant_artists = []
        for artist in release['artists']:
            if artist['id'] in guild.artist_ids:
                relevant_artists.append(self.bot.db.get_artist_by_id(artist['id']))
        artist_role_ids = []
        for artist in relevant_artists:
            role = get(self.bot.get_guild(guild.id).roles, name=get_fan_role_name(artist.name))
            if role is None:
                logging.error(f"Role for {artist.name} not found for guild {guild.id}, ")
                self.bot.db.unfollow_artist_for_guild(artist.id, guild.id)
            else:
                artist_role_ids.append(role.id)
        self.update_artist_releases(release, relevant_artists)
        return artist_role_ids

    def update_artist_releases(self, release, artists):
        for artist in artists:
            artist.latest_release_id = release['id']
            artist.latest_release_name = release['name']
            self.bot.db.update_artist(artist)

