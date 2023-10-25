from utils.spotify import *
import unittest


class TestSpotify(unittest.TestCase):

    valid_artist = 'https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=522cf0f2c0bd4f6f'
    valid_artist_true_id = '3dz0NnIZhtKKeXZxLOxCam'

    async def test_get_artist_id_valid(self):
        artist_id = extract_artist_id(self.valid_artist)
        artist = await get_artist_by_link(artist_id)
        self.assertEqual(self.valid_artist_true_id, artist.id)

    async def test_get_artist_newest_release(self):
        newest_release = await get_newest_release_by_artist(self.valid_artist_true_id)
        curr_date = datetime.today().strftime('%Y-%m-%d')
        if newest_release:
            self.assertTrue(newest_release['release_date'] == curr_date)

    def test_new_release_is_new(self):
        curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        new_release = {
            'release_date': curr_date.strftime('%Y-%m-%d')
        }
        self.assertTrue(is_release_new(new_release))

    def test_old_release_is_not_new(self):
        curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        old_string = (curr_date - timedelta(days=2)).strftime('%Y-%m-%d')
        old_release = {
            'release_date': old_string
        }
        self.assertFalse(is_release_new(old_release))


if __name__ == '__main__':
    unittest.main()
