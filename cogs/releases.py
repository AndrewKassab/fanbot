from discord.ext import commands, tasks
import logging
from utils import spotify
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
        for followed_artist in followed_artists:
            guild = self.bot.get_guild(followed_artist.guild_id)
            if guild is None:
                self.bot.db.remove_guild(followed_artist.guild_id)
                continue

            channel_id = self.bot.db.get_music_channel_id_for_guild_id(followed_artist.guild_id)
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            artist_role = channel.guild.get_role(int(followed_artist.role_id))
            if artist_role is None:
                self.bot.db.remove_artist(followed_artist)
                continue

            newest_release = await spotify.get_newest_release_by_artist(followed_artist.id)
            if newest_release is None:
                continue

            relevant_artists = self.get_relevant_artists_for_release(newest_release, followed_artist.guild_id)
            if relevant_artists is not None:
                await self.notify_release(newest_release, relevant_artists, channel)

    def get_relevant_artists_for_release(self, release, guild_id):
        relevant_artists = []
        all_newest_release_ids = []
        all_newest_release_names = []
        curr_guild_artists = self.bot.db.get_all_artists_for_guild(guild_id)
        for artist in release['artists']:
            if artist['id'] in curr_guild_artists.keys():
                relevant_artists.append(curr_guild_artists[artist['id']])
                all_newest_release_ids.append(curr_guild_artists[artist['id']].latest_release_id)
                all_newest_release_names.append(curr_guild_artists[artist['id']].latest_release_name)
        if release['id'] in all_newest_release_ids or release['name'] in all_newest_release_names:
            return None
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
