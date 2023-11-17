import asyncio
import time
from threading import Thread
from unittest import IsolatedAsyncioTestCase
import itertools

from bot import FanBot
from cogs import Follow
from helpers import get_fan_role_name
from settings import *
from tests.integration.base_integration import IntegrationTest


class BotIntegrationTest(IntegrationTest, IsolatedAsyncioTestCase):
    """
    For the sake of efficiency and rate-limiting, we only start the bot once during the setup.
    This means that we need to use a separate thread since the class setup is synchronous.
    Using a separate thread means that some workarounds had to be employed to use asynchronous
    calls within the bot object.
    """

    @classmethod
    def setUpClass(cls):
        super(BotIntegrationTest, cls).setUpClass()
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
        super(BotIntegrationTest, cls).tearDownClass()

    def asyncSetUp(self):
        super().setUp()
        guild_one = self.bot.get_guild(TEST_GUILD_ONE_ID)
        role_name = get_fan_role_name(self.existing_artist.name)

        # make sure it completes since we can't use await
        future = asyncio.run_coroutine_threadsafe(
            guild_one.create_role(name=role_name, mentionable=True), self.bot.loop)
        self.existing_role = future.result()

    def asyncTearDown(self):
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
