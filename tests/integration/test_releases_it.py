from unittest.mock import patch

from cogs.releases import Releases, NEW_RELEASE_FORMATTER
from services.fanbotdatabase import Artist
from tests.integration.base_bot_integration import BotIntegrationTest


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
        cls.cog.check_new_releases.cancel() # stops the loop from automatically triggering

    @classmethod
    def tearDownClass(cls):
        super(ReleasesIntegrationTest, cls).tearDownClass()

    async def asyncSetUp(self):
        super().asyncSetUp()

    async def asyncTearDown(self):
        super().asyncTearDown()

    async def test_artist_new_release_guild_one_follows_only(self):
        with patch('bot.cogs.releases.sp.get_newest_release_by_artist', return_value=self.new_release_one_artist):
            await self.cog.check_new_releases()
        recent_msg = self.get_recent_message_content(self.guild_one_channel)
        expected_msg = NEW_RELEASE_FORMATTER % (self.existing_role.id, self.new_release_one_artist['url'])
        self.assertEqual(expected_msg, recent_msg)

        artist = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()
        self.assertEqual(self.new_release_one_artist['id'], artist.latest_release_id)
