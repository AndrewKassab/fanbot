from discord.ext import commands, tasks
import logging
from utils import spotify
from utils.database import Artist
from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI


class ReleasesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_new_releases.start()

    @tasks.loop(minutes=10)
    async def check_new_releases(self):
        logging.info('Checking for new releases')
        followed_artists = self.bot.db.get_all_artists()
        for artist in followed_artists:
            await self.check_new_release_for_artist(artist)

    async def check_new_release_for_artist(self, artist: Artist):
        guild = self.bot.get_guild(artist.guild_id)
        if guild is None:
            self.bot.db.remove_guild(artist.guild_id)
            return

        channel_id = self.bot.db.get_music_channel_id_for_guild_id(artist.guild_id)
        channel = guild.get_channel(channel_id)
        if channel is None:
            return

        artist_role = channel.guild.get_role(int(artist.role_id))
        if artist_role is None:
            self.bot.db.remove_artist(artist)
            return

        newest_release = await spotify.get_newest_release_by_artist(artist.id)
        if newest_release is None:
            return

        relevant_artists = self.get_relevant_artists_for_release(newest_release, artist.guild_id)
        if relevant_artists is not None:
            await self.notify_release(newest_release, relevant_artists, channel)

    def get_relevant_artists_for_release(self, release, guild_id):
        relevant_artists = []
        curr_guild_artists = self.bot.db.get_all_artists_for_guild(guild_id)
        for artist in release['artists']:
            db_artist = curr_guild_artists.get(artist['id'])
            if db_artist is not None:
                if release['id'] == db_artist.latest_release_id or release['name'] == db_artist.latest_release_name:
                    return None
                relevant_artists.append(curr_guild_artists[artist['id']])
        return relevant_artists

    async def notify_release(self, release, artists, channel):
        logging.info(f"Notifying a new release by {artists[0].name} {artists[0].id} to Guild {channel.guild.id}")
        release_url = release['url'] if 'url' in release.keys() else release['external_urls']['spotify']
        message_text = ""
        for i in range(1, len(artists)):
            message_text += '<@&%s>, ' % artists[i].role_id
        message = await channel.send(message_text + "<@&%s> New Release!\n:white_check_mark:: Assign Role."
                                                    ":x:: Remove Role.\n%s" % (artists[0].role_id, release_url))
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)
        self.bot.db.set_latest_release_for_artists(artists=artists, new_release_id=release['id'], new_release_name=release['name'])
