import asyncio
import time
from threading import Thread
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
import itertools
from discord.utils import get

from bot import FanBot
from bot.cogs.follow import *
from helpers import get_fan_role_name
from services.fanbotdatabase import Artist
from settings import *
from tests.integration.base_integration import BaseIntegrationTest

NEW_ARTIST_LINK = "https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=777f998db77f4e2b"
EXISTING_ARTIST_LINK = 'https://open.spotify.com/artist/4pb4rqWSoGUgxm63xmJ8xc?si=78d48ae720f140e8'
INVALID_ARTIST_LINK = "12345"


class FollowIntegrationTest(BaseIntegrationTest, IsolatedAsyncioTestCase):
    """
    For the sake of efficiency and rate-limiting, we only start the bot once during the setup.
    This means that we need to use a separate thread since the class setup is synchronous.
    Using a separate thread means that some workarounds had to be employed to use asynchronous
    calls within the bot object.
    """

    @classmethod
    def setUpClass(cls):
        super(FollowIntegrationTest, cls).setUpClass()
        try:
            cls.bot = FanBot()
            cls.bot_thread = Thread(target=lambda: cls.bot.run(DISCORD_TOKEN), daemon=True)
            cls.bot_thread.start()
            start_time = time.time()

            while not cls.bot.is_ready():
                if time.time() - start_time > 60:
                    raise TimeoutError("Bot did not get ready in time")
                time.sleep(1)

            cls.cog: Follow = cls.bot.get_cog('Follow')

            if cls.bot.get_guild(TEST_GUILD_ONE_ID) is None or cls.bot.get_guild(TEST_GUILD_TWO_ID) is None:
                raise Exception("Bot is not properly set up in two test servers.")
        except:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        super(FollowIntegrationTest, cls).tearDownClass()

    async def asyncSetUp(self):
        super().setUp()
        guild_one = self.bot.get_guild(TEST_GUILD_ONE_ID)
        role_name = get_fan_role_name(self.existing_artist.name)

        # make sure it completes since we can't use await
        future = asyncio.run_coroutine_threadsafe(
            guild_one.create_role(name=role_name, mentionable=True), self.bot.loop)
        self.existing_role = future.result()

        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = self.existing_guild.id
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        self.mock_interaction.user = AsyncMock(spec=discord.Member)
        self.mock_interaction.user.name = 'Andrew'
        self.mock_interaction.channel_id = TEST_GUILD_ONE_MUSIC_CHANNEL_ID
        self.mock_edit = self.mock_interaction.edit_original_response

    async def asyncTearDown(self):
        super().tearDown()

        guild_one = self.bot.get_guild(TEST_GUILD_ONE_ID)
        guild_two = self.bot.get_guild(TEST_GUILD_TWO_ID)
        combined_roles = list(itertools.chain(guild_one.roles, guild_two.roles))

        # futures are necessary since we can't use await here
        futures = []
        for role in combined_roles:
            if APP_NAME not in role.name and 'everyone' not in role.name:
                future = asyncio.run_coroutine_threadsafe(role.delete(), self.bot.loop)
                futures.append(future)

        for future in futures:
            future.result()

    async def get_recent_message_content(self, channel):
        messages = [message async for message in channel.history(limit=1)]
        if messages:
            return messages[0].content
        else:
            return None

    async def test_follow_artist_guild_not_set_up(self):
        self.mock_interaction.guild_id = TEST_GUILD_TWO_ID
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, NEW_ARTIST_LINK)
        self.mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)

    async def test_follow_invalid_artist_link(self):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, INVALID_ARTIST_LINK)
        self.mock_edit.assert_called_once_with(content=ARTIST_NOT_FOUND_MESSAGE)

    async def test_follow_existing_artist_role_assigned(self):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, EXISTING_ARTIST_LINK)
        self.mock_interaction.user.add_roles.assert_called_once_with(self.existing_role)

    async def test_follow_new_artist(self):
        future = asyncio.run_coroutine_threadsafe(self.cog.follow_artist.callback(
            self.cog, self.mock_interaction, NEW_ARTIST_LINK), self.bot.loop)
        future.result()

        new_role = get(self.bot.get_guild(TEST_GUILD_ONE_ID).roles, name=get_fan_role_name(self.new_artist.name))
        self.assertIsNotNone(new_role)
        self.mock_interaction.user.add_roles.assert_called_once_with(new_role)

        artist = self.session.query(Artist).filter(Artist.id == self.new_artist.id).first()
        self.assertIsNotNone(artist)
        self.assertEqual(self.existing_guild.id, artist.guilds[0].id)

        channel = self.bot.get_channel(TEST_GUILD_ONE_MUSIC_CHANNEL_ID)
        future = asyncio.run_coroutine_threadsafe(self.get_recent_message_content(channel), self.bot.loop)
        recent_msg = future.result()
        expected_msg = SUCCESSFULL_MESSAGE_FORMATTER % (
            new_role.id, self.new_artist.name, self.mock_interaction.user.name)
        self.assertEqual(expected_msg, recent_msg)
