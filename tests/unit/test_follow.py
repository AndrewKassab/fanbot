from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, MagicMock
import discord

from bot.cogs.follow import *
from settings import SET_COMMAND
from bot.fanbot import FanBot
from services.fanbotdatabase import FanbotDatabase


class TestFollow(IsolatedAsyncioTestCase):

    def setUp(self):
        bot = AsyncMock(spec=FanBot)
        bot.db = AsyncMock(spec=FanbotDatabase)
        self.cog = Follow(bot)
        self.mock_interaction = AsyncMock(spec=discord.Interaction)
        self.mock_interaction.guild_id = "some_guild"
        self.mock_interaction.response = AsyncMock(spec=discord.InteractionResponse)

    async def test_send_message_on_command(self):
        with patch.object(self.mock_interaction.response, 'send_message') as mock_send:
            await self.your_class_instance.follow_artist(self.mock_interaction, "some_artist_link")
            mock_send.assert_called_once_with('Attempting to follow artist...', ephemeral=True)

    async def test_guild_not_in_db(self):
        with patch.object(self.cog.bot.db.is_guild_exist, 'is_guild_exist', new_callable=MagicMock, return_value=False):
            self.cog.bot.db.is_guild_exist.return_value = False
            with patch.object(self.mock_interaction, 'edit_original_response') as mock_edit:
                await self.cog.follow_artist.callback(self.cog, self.mock_interaction, "some_artist_link")
                mock_edit.assert_called_once_with(content=CONFIGURE_CHANNEL_MESSAGE)
