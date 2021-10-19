import unittest
from spotify import *


class TestSpotify(unittest.TestCase):

    valid_artist_name = 'Porter Robinson'
    valid_artist_true_id = '3dz0NnIZhtKKeXZxLOxCam'

    def test_get_artist_id_invalid(self):
        self.assertRaises(InvalidArtistException, get_artist_by_name, "invalid artist name")

    def test_get_artist_id_valid(self):
        artist_id = get_artist_by_name(self.valid_artist_name)
        self.assertEqual(artist_id, self.valid_artist_true_id)

    def test_get_artist_newest_release(self):
        newest_releases = get_new_releases_by_artist_id(self.valid_artist_true_id)
        curr_date = datetime.today().strftime('%Y-%m-%d')
        for release in newest_releases:
            self.assertTrue(release['release_date'] == curr_date)


if __name__ == '__main__':
    unittest.main()
