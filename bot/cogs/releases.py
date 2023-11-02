from datetime import datetime
import pytz
from discord.ext import commands, tasks
from discord.utils import get
import logging
from services import spotify
from services.fanbotdatabase import Artist


class Releases(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_new_releases.start()

    @tasks.loop(minutes=1)
    async def check_new_releases(self):
        eastern = pytz.timezone('US/Eastern')
        eastern_now = datetime.now(eastern)
        if eastern_now.hour != 0 and eastern_now.minute != 0:
            return
        logging.info('Checking for new releases')
        artists = self.bot.db.get_all_artists()
        for artist in artists:
            await self.check_new_release_for_artist(artist)

    async def check_new_release_for_artist(self, artist: Artist):
        if len(artist.guilds) == 0:
            self.bot.db.delete_artist_by_id(artist.id)

        newest_release = await spotify.get_newest_release_by_artist(artist.id)
        if newest_release is None:
            return
        if newest_release['id'] == artist.latest_release_id or \
                newest_release['name'] == artist.latest_release_name:
            return

        for guild in artist.guilds:
            if self.bot.get_guild(guild.id) is None:
                self.bot.db.delete_guild_by_id(guild.id)
            if self.bot.get_guild(guild.id) is None or \
                    self.bot.get_guild(guild.id).get_channel(guild.music_channel_id) is None:
                continue
            role_ids = self.get_role_ids(newest_release, guild)
            if len(role_ids) == 0:
                self.bot.db.unfollow_artist_for_guild(artist.id, guild.id)
            else:
                await self.notify_release(newest_release, guild, role_ids)

    async def notify_release(self, release, guild, role_ids, channel):
        logging.info(f"Notifying a new release by artist id {role_ids[0]} to Guild {guild.id}")
        release_url = release['url'] if 'url' in release.keys() else release['external_urls']['spotify']
        message_text = ""
        for i in range(1, len(role_ids)):
            message_text += '<@&%s>, ' % role_ids[i].id
        await guild.get_channel(guild.music_channel_id).send(message_text + "<@&%s> New Release!\n%s"
                                                             % (role_ids[0], release_url))

    def get_role_ids(self, release, guild):
        relevant_artists = []
        for artist in release['artists']:
            if guild.artists.get(artist['id']) is not None:
                relevant_artists.append(guild.artists.get(artist['id']))
        artist_role_ids = []
        for artist in relevant_artists:
            role = get(self.bot.get_guild(guild.id).roles, name=f"{artist.name}Fan")
            if role is None:
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
