import asyncio
from unittest.mock import AsyncMock

from bot.cogs.follow import *
from bot.helpers import get_fan_role_name
from services.fanbotdatabase import Artist
from settings import *
from tests.integration.base_bot_integration import BotIntegrationTest

NEW_ARTIST_LINK = "https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=777f998db77f4e2b"
EXISTING_ARTIST_LINK = 'https://open.spotify.com/artist/4pb4rqWSoGUgxm63xmJ8xc?si=78d48ae720f140e8'
INVALID_ARTIST_LINK = "12345"


class FollowIntegrationTest(BotIntegrationTest):
    '''
    Preconditions:

    guild_one exists following artist_one

    role exists in guild_one for the relationship
    '''

    @classmethod
    def setUpClass(cls):
        super(FollowIntegrationTest, cls).setUpClass()

        cls.cog: Follow = cls.bot.get_cog('Follow')

    @classmethod
    def tearDownClass(cls):
        super(FollowIntegrationTest, cls).tearDownClass()

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = self.guild_one.id
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        self.mock_interaction.user = AsyncMock(spec=discord.Member)
        self.mock_interaction.user.name = 'Andrew'
        self.mock_interaction.channel_id = TEST_GUILD_ONE_MUSIC_CHANNEL_ID
        self.mock_edit = self.mock_interaction.edit_original_response

    async def asyncTearDown(self):
        await super().asyncTearDown()

    async def test_follow_artist_guild_not_set_up(self):
        self.mock_interaction.guild_id = TEST_GUILD_TWO_ID
        await self.run_threadsafe(
            self.cog.follow_artist.callback, self.cog, self.mock_interaction, NEW_ARTIST_LINK)
        self.mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)

    async def test_follow_invalid_artist_link(self):
        await self.run_threadsafe(
            self.cog.follow_artist.callback, self.cog, self.mock_interaction, INVALID_ARTIST_LINK)
        self.mock_edit.assert_called_once_with(content=ARTIST_NOT_FOUND_MESSAGE)

    async def test_follow_existing_artist_role_assigned(self):
        await self.run_threadsafe(
            self.cog.follow_artist.callback, self.cog, self.mock_interaction, EXISTING_ARTIST_LINK)
        self.mock_interaction.user.add_roles.assert_called_once_with(self.guild_one_artist_one_role)

    async def test_follow_new_artist(self):
        await self.run_threadsafe(
            self.cog.follow_artist.callback, self.cog, self.mock_interaction, NEW_ARTIST_LINK)

        new_role = get(self.bot.get_guild(TEST_GUILD_ONE_ID).roles, name=get_fan_role_name(self.artist_two.name))
        self.assertIsNotNone(new_role)
        self.mock_interaction.user.add_roles.assert_called_once_with(new_role)

        artist = self.session.query(Artist).filter(Artist.id == self.artist_two.id).first()
        self.assertIsNotNone(artist)
        self.assertEqual(self.guild_one.id, artist.guilds[0].id)

        recent_msg = await self.run_threadsafe(self.get_recent_message_content, self.guild_one_channel)
        expected_msg = SUCCESSFULL_MESSAGE_FORMATTER % (
            new_role.id, self.artist_two.name, self.mock_interaction.user.name)
        self.assertEqual(expected_msg, recent_msg)
