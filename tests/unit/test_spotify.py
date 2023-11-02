from services.spotify import *
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, MagicMock


class TestSpotify(IsolatedAsyncioTestCase):

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

        self.mock_sp = MagicMock(spec = spotify.Client)
        self.mock_sp.http = MagicMock()
        self.mock_sp.http.artist_albums = AsyncMock()
        self.mock_sp.http.album_tracks = AsyncMock()

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

    async def test_get_newest_release_when_new_album(self):
        with patch('services.spotify.spotify.Client', return_value=self.mock_sp):
            self.mock_sp.http.artist_albums.return_value = {'items': [self.new_album_release]}

            newest_release = await get_newest_release_by_artist('someid')
            self.assertEqual(newest_release, self.new_album_release)

    async def test_get_newest_release_when_new_single(self):
        with patch('services.spotify.spotify.Client', return_value=self.mock_sp):
            self.mock_sp.http.artist_albums = self.mock_artist_albums_single_new
            self.mock_sp.http.album_tracks.return_value = {'items': [self.new_single_release]}

            newest_release = await get_newest_release_by_artist('someid')
            self.assertEqual(newest_release, self.new_single_release)

    async def test_get_newest_release_no_new_release(self):
        with patch('services.spotify.spotify.Client', return_value=self.mock_sp):
            self.mock_sp.http.artist_albums.side_effect = self.mock_artist_albums_no_new

            newest_release = await get_newest_release_by_artist('someid')
            self.assertIsNone(newest_release)


if __name__ == '__main__':
    unittest.main()
