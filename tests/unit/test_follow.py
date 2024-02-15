from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, MagicMock, Mock, call

from bot.cogs.follow import *
from bot.fanbot import FanBot
from services.fanbotdatabase import FanbotDatabase, Artist
from services.spotify import InvalidArtistException

artist_link = "some_artist_link"
artist = Artist(name="Madeon", id="12345")
mock_role = Mock(id="12345", spec=discord.Role)


class FollowTest(IsolatedAsyncioTestCase):

    def setUp(self):
        bot = AsyncMock(spec=FanBot)
        bot.db = AsyncMock(spec=FanbotDatabase)
        self.cog = Follow(bot)
        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = "some_guild"
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)
        self.mock_interaction.user = AsyncMock(spec=discord.Member)
        self.mock_edit = self.mock_interaction.edit_original_response

    async def test_send_message_on_command(self):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
        self.mock_interaction.response.send_message.assert_called_once_with(
            ATTEMPT_FOLLOW_MESSAGE, ephemeral=True)

    async def test_guild_not_in_db(self):
        with patch.object(self.cog.bot.db, 'is_guild_exist', return_value=False):
            await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
            self.mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)

    @patch('bot.cogs.follow.sp.get_artist_by_link', side_effect=InvalidArtistException)
    async def test_invalid_artist_follow_attempt(self, mock_get_artist_by_link):
        await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
        self.mock_edit.assert_called_once_with(content=ARTIST_NOT_FOUND_MESSAGE)

    @patch('bot.cogs.follow.sp.get_artist_by_link')
    async def test_bot_forbidden_manage_roles(self, mock_method):
        with patch('bot.cogs.follow.Follow.get_role_for_artist', side_effect=Forbidden(Mock(), 'msg')):
            await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
            self.mock_edit.assert_called_once_with(content=MISSING_MANAGE_ROLES_MESSAGE)

    @patch('bot.cogs.follow.sp.get_artist_by_link')
    async def test_failed_follow_artist(self, mock_method):
        with patch.object(self.cog, 'get_role_for_artist', return_value=mock_role):
            with patch('bot.cogs.follow.Follow.handle_follow_artist_for_guild',
                       side_effect=InvalidArtistException):
                await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
                self.mock_edit.assert_called_once_with(content=FAILED_MESSAGE)
                mock_role.delete.assert_called()

    @patch('bot.cogs.follow.sp.get_artist_by_link', return_value=artist)
    async def test_successful_follow_artist(self, mock_get_artist_by_link):
        with patch('bot.cogs.follow.Follow.get_role_for_artist') as mock_get_role_for_artist:
            mock_get_role_for_artist.return_value = mock_role
            with patch('bot.cogs.follow.Follow.handle_follow_artist_for_guild') as mock_handle_follow_artist:
                await self.cog.follow_artist.callback(self.cog, self.mock_interaction, artist_link)
                mock_get_artist_by_link.assert_called_once_with(artist_link)
                mock_get_role_for_artist.assert_called_once_with(artist, self.mock_interaction.guild_id)
                mock_handle_follow_artist.assert_called_once_with(self.mock_interaction, artist, mock_role)

    async def test_get_role_for_artist_already_exists(self):
        with patch("bot.cogs.follow.get", return_value=Mock(id=20)) as mock_get:
            with patch("bot.cogs.follow.helpers.get_fan_role_name", return_value=Mock()):
                returned_role = await self.cog.get_role_for_artist(Mock(), Mock())
                mock_get.assert_called()
                self.assertEqual(returned_role.id, 20)

    async def test_get_role_for_artist_not_exist(self):
        mocked_guild = MagicMock(spec=discord.Guild)
        mocked_guild.create_role.return_value = Mock(id=10)
        self.cog.bot.get_guild.return_value = mocked_guild
        with patch.object(self.cog.bot.db, 'is_artist_exist', return_value=False):
            returned_role = await self.cog.get_role_for_artist(artist, Mock())
            self.assertEqual(returned_role.id, 10)

    async def test_handle_follow_artist_already_follows(self):
        await self.cog.handle_follow_artist_for_guild(self.mock_interaction, artist, mock_role)
        self.mock_edit.assert_called_once_with(content=ALREADY_FOLLOW_FORMAT_MESSAGE % artist.name)
        self.mock_interaction.user.add_roles.assert_called_once_with(mock_role)

    @patch('bot.cogs.follow.Follow.send_successful_follow_message')
    async def test_handle_follow_artist_new_artist(self, mock_method):
        with patch.object(self.cog.bot.db, 'does_guild_follow_artist', return_value=False):
            with patch.object(self.cog.bot.db, 'get_artist_by_id', return_value=None):
                await self.cog.handle_follow_artist_for_guild(self.mock_interaction, artist, mock_role)
                self.cog.bot.db.add_new_artist.assert_called_once_with(artist.id, artist.name, self.mock_interaction.guild_id)
                self.mock_interaction.user.add_roles.assert_called_once_with(mock_role)

    @patch('bot.cogs.follow.Follow.send_successful_follow_message')
    async def test_handle_follow_artist_existing_artist(self, mock_method):
        with patch.object(self.cog.bot.db, 'does_guild_follow_artist', return_value=False):
            await self.cog.handle_follow_artist_for_guild(self.mock_interaction, artist, mock_role)
            self.cog.bot.db.follow_existing_artist_for_guild.assert_called_once_with(
                artist.id, self.mock_interaction.guild_id)
            self.mock_interaction.user.add_roles.assert_called_once_with(mock_role)

    async def test_send_successful_follow_message(self):
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock()
        mock_message = Mock(spec=discord.message.PartialMessage)
        mock_channel.send.return_value = mock_message
        with patch.object(self.cog.bot, 'get_channel', return_value=mock_channel) as mock_get_channel:
            await self.cog.send_successful_follow_message(artist, self.mock_interaction, mock_role.id)
            mock_get_channel.assert_called_once_with(self.mock_interaction.channel_id)
            mock_channel.send.assert_called_once_with(content=SUCCESSFULL_MESSAGE_FORMATTER % (
                mock_role.id, artist.name, self.mock_interaction.user.name))
            mock_message.add_reaction.assert_has_calls([call(FOLLOW_ROLE_EMOJI), call(UNFOLLOW_ROLE_EMOJI)])
