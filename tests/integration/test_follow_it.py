import time
from threading import Thread
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from bot import FanBot
from bot.cogs.follow import *
from settings import *
from tests.integration.base_integration import BaseIntegrationTest

VALID_ARTIST_LINK = "https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=777f998db77f4e2b"
INVALID_ARTIST_LINK = "12345"


class FollowIntegrationTest(BaseIntegrationTest, IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        super(FollowIntegrationTest, cls).setUpClass()
        try:
            cls.bot = FanBot()
            cls.bot_thread = Thread(target=lambda: cls.bot.run(DISCORD_TOKEN), daemon=True)
            cls.bot_thread.start()
            start_time = time.time()
            while not cls.bot.is_ready():
                if time.time() - start_time > 30:
                    raise TimeoutError("Bot did not get ready in time")
                time.sleep(1)
            cls.cog: Follow = cls.bot.get_cog('Follow')
        finally:
            cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        super(FollowIntegrationTest, cls).tearDownClass()

    def setUp(self):
        super().setUp()
        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = self.existing_guild.id
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        self.mock_interaction.user = AsyncMock(spec=discord.Member)
        self.mock_edit = self.mock_interaction.edit_original_response

    def tearDown(self):
        super().tearDown()

    def test_follow_artist_guild_not_set_up(self):
        self.mock_interaction.guild_id = TEST_GUILD_TWO_ID
        self.cog.follow_artist.callback(self.cog, self.mock_interaction, VALID_ARTIST_LINK)
        self.mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)
