import time
from unittest.mock import patch

from cogs.releases import Releases, NEW_RELEASE_FORMATTER
from helpers import get_fan_role_name
from services.fanbotdatabase import Artist, Guild
from settings import TEST_GUILD_TWO_ID, TEST_GUILD_ONE_ID
from tests.integration.base_bot_integration import BotIntegrationTest

CHANNEL_RESET_MESSAGE = 'reset'

class ReleasesIntegrationTest(BotIntegrationTest):

    @classmethod
    def setUpClass(cls):
        super(ReleasesIntegrationTest, cls).setUpClass()

        cls.new_release_one_artist = {
            'id': '1',
            'name': 'Love You Back',
            'url': 'https://open.spotify.com/track/5wM6LOw2U6XeIFHfsgI6wU?si=4a0575adfae34c76',
            'artists': [
                {
                    'id': cls.existing_artist.id,
                    'name': cls.existing_artist.name
                }
            ]
        }

        cls.new_release_two_artists = {
            'id': '2',
            'name': 'Shelter',
            'url': 'https://open.spotify.com/track/5wM6LOw2U6XeIFHfsgI6wU?si=4a0575adfae34c76',
            'artists': [
                {
                    'id': cls.existing_artist.id,
                    'name': cls.existing_artist.name
                },
                {
                    'id': cls.new_artist.id,
                    'name': cls.new_artist.name
                }
            ]
        }

        cls.cog: Releases = cls.bot.get_cog('Releases')
        cls.cog.check_new_releases.cancel()  # stops the loop from automatically triggering

        session = cls.Session()
        new_guild_db = Guild(id=cls.new_guild.id, music_channel_id=cls.new_guild.music_channel_id)
        new_artist_db = Artist(id=cls.new_artist.id, name=cls.new_artist.name)
        session.add(new_guild_db)
        session.add(new_artist_db)

        existing_guild_db = session.query(Guild).filter(Guild.id == cls.existing_guild.id).first()

        new_guild_db.artists.append(new_artist_db)
        existing_guild_db.artists.append(new_artist_db)

        session.commit()
        session.close()

        cls.bot.db.load_cache()

    @classmethod
    def tearDownClass(cls):
        super(ReleasesIntegrationTest, cls).tearDownClass()

    async def asyncSetUp(self):
        await super().asyncSetUp()
        guild_one = self.bot.get_guild(TEST_GUILD_ONE_ID)
        guild_two = self.bot.get_guild(TEST_GUILD_TWO_ID)
        role_name_new_artist = get_fan_role_name(self.new_artist.name)

        self.guild_one_new_artist_role = await self.run_threadsafe(
            guild_one.create_role, name=role_name_new_artist, mentionable=True)
        self.guild_two_new_artist_role = await self.run_threadsafe(
            guild_two.create_role, name=role_name_new_artist, mentionable=True)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.run_threadsafe(self.guild_one_channel.send, 'reset')
        await self.run_threadsafe(self.guild_two_channel.send, 'reset')

    async def test_artist_new_release_guild_one_follows_only(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   side_effect=self.mock_get_newest_release_by_artist_existing_artist_new):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(self.get_recent_message_content, self.guild_one_channel)
        guild_two_msg = await self.run_threadsafe(self.get_recent_message_content, self.guild_two_channel)
        expected_msg = NEW_RELEASE_FORMATTER % (
            self.guild_one_existing_artist_role.id, self.new_release_one_artist['url'])

        self.assertEqual(expected_msg, guild_one_msg)
        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_two_msg)

        artist = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()

        self.assertEqual(self.new_release_one_artist['id'], artist.latest_release_id)

    async def test_artist_new_release_delete_music_channel_no_notification(self):
        guild = self.bot.get_guild(self.existing_guild.id)
        try:
            # cheating because I can't mock get_channel (read only)
            guild._channels.pop(self.guild_one_channel.id)

            with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                       return_value=self.new_release_one_artist):
                await self.run_threadsafe(self.cog.check_new_releases)

            guild_one_msg = await self.run_threadsafe(
                self.get_recent_message_content, self.guild_one_channel)
            new_release_msg = NEW_RELEASE_FORMATTER % (
                self.guild_one_existing_artist_role.id, self.new_release_one_artist['url'])

            self.assertNotEqual(guild_one_msg, new_release_msg)
        finally:
            guild._channels[self.guild_one_channel.id] = self.guild_one_channel

    async def test_artist_new_release_both_guilds_follow(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.new_release_one_artist):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(self.get_recent_message_content, self.guild_one_channel)
        guild_two_msg = await self.run_threadsafe(self.get_recent_message_content, self.guild_two_channel)
        expected_msg = NEW_RELEASE_FORMATTER % (self.existing_role.id, self.new_release_one_artist['url'])

        self.assertEqual(expected_msg, guild_one_msg)
        self.assertEqual(expected_msg, guild_two_msg)

        artist = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()

        self.assertEqual(self.new_release_one_artist['id'], artist.latest_release_id)

    def mock_get_newest_release_by_artist_existing_artist_new(self, artist_id):
        if artist_id == self.existing_artist.id:
            return self.new_release_one_artist
        else:
            return None

    def mock_get_newest_release_by_artist_both_artists_new(self, artist_id):
        if artist_id == self.new_artist.id:
            return self.new_release_two_artists
        else:
            return None
