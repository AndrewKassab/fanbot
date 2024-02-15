from unittest.mock import patch

from bot.cogs.releases import Releases, NEW_RELEASE_FORMATTER
from bot.helpers import get_fan_role_name
from services.fanbotdatabase import Artist, Guild, FanbotDatabase
from settings import TEST_GUILD_TWO_ID, TEST_GUILD_ONE_ID
from tests.integration.base_bot_integration import BotIntegrationTest

CHANNEL_RESET_MESSAGE = 'reset'


class ReleasesIntegrationTest(BotIntegrationTest):
    '''
    Preconditions:

    guild_one and guild_two both exist
    artist_one and artist_two both exist

    guild_one follows both artist_one and artist_two with roles for both existing
    guild_two follows only artist_two
    '''

    @classmethod
    def setUpClass(cls):
        super(ReleasesIntegrationTest, cls).setUpClass()

        cls.new_release_artist_one = {
            'id': '1',
            'name': 'Love You Back',
            'url': 'https://open.spotify.com/track/5wM6LOw2U6XeIFHfsgI6wU?si=4a0575adfae34c76',
            'artists': [
                {
                    'id': cls.artist_one.id,
                    'name': cls.artist_one.name
                }
            ]
        }

        cls.new_release_artist_two = {
            'id': '1',
            'name': 'Look at the Sky',
            'url': 'https://open.spotify.com/track/5lXNcc8QeM9KpAWNHAL0iS?si=c5e9e825b02545cf',
            'artists': [
                {
                    'id': cls.artist_two.id,
                    'name': cls.artist_two.name
                }
            ]
        }

        cls.new_release_two_artists = {
            'id': '2',
            'name': 'Shelter',
            'url': 'https://open.spotify.com/track/2CgOd0Lj5MuvOqzqdaAXtS?si=6b872bcd516b469c',
            'artists': [
                {
                    'id': cls.artist_one.id,
                    'name': cls.artist_one.name
                },
                {
                    'id': cls.artist_two.id,
                    'name': cls.artist_two.name
                }
            ]
        }

        cls.remix_release_another_artist = {
            'id': '4',
            'name': 'Some Song - Andrew Remix',
            'url': 'Some URL',
            'artists': [
                {
                    'id': cls.artist_one.id,
                    'name': cls.artist_one.name
                }
            ]
        }

        cls.remix_release_same_artist = {
            'id': '4',
            'name': 'Some Song - Madeon Remix',
            'url': 'Some URL Valid Remix',
            'artists': [
                {
                    'id': cls.artist_one.id,
                    'name': cls.artist_one.name
                }
            ]
        }

        cls.cog: Releases = cls.bot.get_cog('Releases')
        cls.cog.check_new_releases.cancel()  # stops the loop from automatically triggering

        session = cls.Session()
        new_guild_db = Guild(id=cls.guild_two.id, music_channel_id=cls.guild_two.music_channel_id)
        new_artist_db = Artist(id=cls.artist_two.id, name=cls.artist_two.name)
        session.add(new_guild_db)
        session.add(new_artist_db)

        existing_guild_db = session.query(Guild).filter(Guild.id == cls.guild_one.id).first()

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
        role_name_artist_two = get_fan_role_name(self.artist_two.name)

        self.guild_one_artist_two_role = await self.run_threadsafe(
            guild_one.create_role, name=role_name_artist_two, mentionable=True)
        self.guild_two_artist_two_role = await self.run_threadsafe(
            guild_two.create_role, name=role_name_artist_two, mentionable=True)

        # Overwriting db so that changes can get rolled back per test.
        self.bot.db = FanbotDatabase(self.session)

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.run_threadsafe(self.guild_one_channel.send, 'reset')
        await self.run_threadsafe(self.guild_two_channel.send, 'reset')

    async def test_artist_new_release_guild_one_follows_only(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   side_effect=self.mock_get_newest_release_by_artist_artist_one_new):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)
        guild_two_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_two_channel)
        expected_msg = NEW_RELEASE_FORMATTER % (
            self.guild_one_artist_one_role.id, self.new_release_artist_one['url'])

        self.assertEqual(expected_msg, guild_one_msg)
        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_two_msg)

        artist = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()

        self.assertEqual(self.new_release_artist_one['id'], artist.latest_release_id)

    async def test_artist_new_release_delete_music_channel_no_notification(self):
        guild = self.bot.get_guild(self.guild_one.id)
        try:
            # cheating because I can't mock get_channel (read only)
            guild._channels.pop(self.guild_one_channel.id)

            with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                       return_value=self.new_release_artist_two):
                await self.run_threadsafe(self.cog.check_new_releases)

            guild_one_msg = await self.run_threadsafe(
                self.get_recent_message_content, self.guild_one_channel)
            new_release_msg = NEW_RELEASE_FORMATTER % (
                self.guild_one_artist_one_role.id, self.new_release_artist_one['url'])

            self.assertNotEqual(guild_one_msg, new_release_msg)
        finally:
            guild._channels[self.guild_one_channel.id] = self.guild_one_channel

    async def test_artist_new_release_both_guilds_follow(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   side_effect=self.mock_get_newest_release_by_artist_artist_two_new):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)
        guild_two_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_two_channel)
        expected_msg_guild_one = NEW_RELEASE_FORMATTER % (self.guild_one_artist_two_role.id, self.new_release_artist_two['url'])
        expected_msg_guild_two = NEW_RELEASE_FORMATTER % (self.guild_two_artist_two_role.id, self.new_release_artist_two['url'])

        self.assertEqual(expected_msg_guild_one, guild_one_msg)
        self.assertEqual(expected_msg_guild_two, guild_two_msg)

        artist = self.session.query(Artist).filter(Artist.id == self.artist_two.id).first()

        self.assertEqual(self.new_release_artist_two['id'], artist.latest_release_id)

    async def test_both_artists_shared_new_release(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.new_release_two_artists):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertTrue(str(self.guild_one_artist_one_role.id) in guild_one_msg)
        self.assertTrue(str(self.guild_one_artist_two_role.id) in guild_one_msg)

    async def test_artist_two_deleted_role_not_notified_and_follow_deleted(self):
        await self.run_threadsafe(self.guild_one_artist_two_role.delete)

        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.new_release_two_artists):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertTrue(str(self.guild_one_artist_one_role.id) in guild_one_msg)
        self.assertFalse(str(self.guild_one_artist_two_role.id) in guild_one_msg)

        guild = self.bot.db.get_guild_by_id(self.guild_one.id)

        self.assertTrue(self.artist_two.id not in guild.artist_ids)

    async def test_artist_one_deleted_guild_not_notified_follow_deleted(self):
        await self.run_threadsafe(self.guild_two_artist_two_role.delete)

        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   side_effect=self.mock_get_newest_release_by_artist_artist_two_new):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_two_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_two_channel)

        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_two_msg)

        guild = self.bot.db.get_guild_by_id(self.guild_two.id)

        self.assertTrue(self.artist_two.id not in guild.artist_ids)

    async def test_no_new_release_no_notification(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=None):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_one_msg)

    async def test_guild_removed_bot_when_new_release(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.new_release_artist_two):
            with patch.object(self.bot, 'get_guild', return_value=None):
                await self.run_threadsafe(self.cog.check_new_releases)

        guild_two = self.bot.db.get_guild_by_id(self.guild_two.id)
        artist_two = self.bot.db.get_artist_by_id(self.artist_two.id)

        self.assertIsNone(guild_two)
        self.assertFalse(self.guild_two.id in artist_two.guild_ids)

    async def test_guild_not_notified_when_already_been_notified(self):
        self.artist_one.latest_release_name = self.new_release_artist_one['name']

        self.bot.db.update_artist(self.artist_one)

        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=None):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_one_msg)

    async def test_no_notification_for_other_artist_remix(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.remix_release_another_artist):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertEqual(CHANNEL_RESET_MESSAGE, guild_one_msg)

    async def test_notification_for_followed_artists_remix(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist',
                   return_value=self.remix_release_same_artist):
            await self.run_threadsafe(self.cog.check_new_releases)

        guild_one_msg = await self.run_threadsafe(
            self.get_recent_message_content, self.guild_one_channel)

        self.assertTrue(self.remix_release_same_artist['url'] in guild_one_msg)

    def mock_get_newest_release_by_artist_artist_one_new(self, artist_id):
        if artist_id == self.artist_one.id:
            return self.new_release_artist_one
        else:
            return None

    def mock_get_newest_release_by_artist_artist_two_new(self, artist_id):
        if artist_id == self.artist_two.id:
            return self.new_release_artist_two
        else:
            return None
