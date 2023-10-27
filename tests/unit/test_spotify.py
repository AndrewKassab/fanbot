import asyncio

from utils.spotify import *
from asynctest.mock import patch, MagicMock, CoroutineMock
import asynctest

class TestSpotify(asynctest.TestCase):

    def setUp(self):
        self.valid_artist = 'https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=522cf0f2c0bd4f6f'
        self.valid_artist_true_id = '3dz0NnIZhtKKeXZxLOxCam'

        curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        curr_date_formatted = curr_date.strftime('%Y-%m-%d')
        two_days_ago_formatted = (curr_date - timedelta(days=2)).strftime('%Y-%m-%d')

        self.new_album_release = {
            'id': 'album',
            'release_date': curr_date_formatted
        }
        self.old_album_release = {
            'id': 'album',
            'release_date': two_days_ago_formatted
        }
        self.new_single_release = {
            'id': 'single',
            'release_date': curr_date_formatted
        }
        self.old_single_release = {
            'id': 'single',
            'release_date': two_days_ago_formatted
        }

    async def mock_artist_albums_both_new(self, artist_id, limit=1, include_groups='album'):
        if include_groups == 'album':
            return {'items': [self.new_album_release]}
        elif include_groups == 'single':
            return {'items': [self.new_single_release]}

    async def mock_artist_albums_single_new(self, artist_id, limit=1, include_groups='album'):
        if include_groups == 'album':
            return {'items': [self.old_album_release]}
        elif include_groups == 'single':
            return {'items': [self.new_single_release]}

    async def mock_artist_albums_no_new(self, artist_id, limit=1, include_groups='album'):
        if include_groups == 'album':
            return {'items': [self.old_album_release]}
        elif include_groups == 'single':
            return {'items': [self.old_single_release]}

    async def test_get_artist_id_valid(self):
        artist = await get_artist_by_link(self.valid_artist)
        self.assertEqual(self.valid_artist_true_id, artist.id)

    @patch('utils.spotify.spotify.Client')
    async def test_get_newest_release_when_new_album(self, MockSpotifyClient):
        mock_http_client = MagicMock()
        mock_http_client.artist_albums = CoroutineMock()
        mock_http_client.artist_albums.side_effect = self.mock_artist_albums_both_new
        MockSpotifyClient.http = mock_http_client

        newest_release = await get_newest_release_by_artist('someid')
        self.assertEqual(newest_release, self.new_album_release)

    @patch('utils.spotify.spotify.Client')
    async def test_get_newest_release_when_new_single(self, MockSpotifyClient):
        mock_http_client = MagicMock()
        mock_http_client.artist_albums = CoroutineMock()
        mock_http_client.artist_albums.side_effect = self.mock_artist_albums_single_new
        MockSpotifyClient.http = mock_http_client

        newest_release = await get_newest_release_by_artist('someid')
        self.assertEqual(newest_release, self.new_single_release)

    @patch('utils.spotify.spotify.Client')
    async def test_get_newest_release_no_new_release(self, MockSpotifyClient):
        mock_http_client = MagicMock()
        mock_http_client.artist_albums = CoroutineMock()
        mock_http_client.artist_albums.side_effect = self.mock_artist_albums_no_new
        MockSpotifyClient.http = mock_http_client

        newest_release = await get_newest_release_by_artist('someid')
        self.assertIsNone(newest_release)


if __name__ == '__main__':
    asynctest.main()
