from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, MagicMock, Mock

from bot.cogs.follow import *
from bot.fanbot import FanBot
from services.fanbotdatabase import FanbotDatabase
from services.spotify import InvalidArtistException


class TestFollow(IsolatedAsyncioTestCase):

    def setUp(self):
        bot = AsyncMock(spec=FanBot)
        bot.db = AsyncMock(spec=FanbotDatabase)
        self.cog = Follow(bot)
        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = "some_guild"
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        self.mock_edit = self.mock_interaction.edit_original_response


    async def test_send_message_on_command(self):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, "some_artist_link")
        self.mock_interaction.response.send_message.assert_called_once_with(
            ATTEMPT_FOLLOW_MESSAGE, ephemeral=True)

    async def test_guild_not_in_db(self):
        with patch.object(self.cog.bot.db, 'is_guild_exist', return_value=False):
            await self.cog.follow_artist.callback(self.cog, self.mock_interaction, "some_artist_link")
            self.mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)

    @patch('bot.cogs.follow.sp.get_artist_by_link', side_effect=InvalidArtistException)
    async def test_invalid_artist_follow_attempt(self, mock_get_artist_by_link):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, "some_artist_link")
        self.mock_edit.assert_called_once_with(content=ARTIST_NOT_FOUND_MESSAGE)

    @patch('bot.cogs.follow.Follow.get_role_for_artist', side_effect=Forbidden)
    async def test_bot_forbidden_manage_roles(self, mock_get_role_for_artist):
        self.mock_sp.get_artist_by_link.return_value = Mock()
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, "some_artist_link")
        self.mock_edit.assert_called_once_with(content=MISSING_MANAGE_ROLES_MESSAGE)

    async def test_get_role_for_artist_already_exists(self):
        with patch("bot.cogs.follow.get", return_value=Mock(id=20)) as mock_get:
            returned_role_id = await self.cog.get_role_for_artist(Mock(), Mock())
            mock_get.assert_called()
            self.assertEqual(returned_role_id, 20)

    async def test_get_role_for_artist_not_exist(self):
        pass
        #with patch.object(self.bot.db, 'is_artist_exist', return_value=False):
