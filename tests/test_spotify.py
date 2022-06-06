from utils.spotify import *
import unittest


class TestSpotify(unittest.TestCase):

    valid_artist = 'https://open.spotify.com/artist/3dz0NnIZhtKKeXZxLOxCam?si=522cf0f2c0bd4f6f'
    valid_artist_true_id = '3dz0NnIZhtKKeXZxLOxCam'

    def test_get_artist_id_invalid(self):
        self.assertRaises(InvalidArtistException, get_artist_by_id, "invalid artist name")

    def test_get_artist_id_valid(self):
        artist_id = extract_artist_id(self.valid_artist)
        artist = get_artist_by_id(artist_id)
        self.assertEqual(self.valid_artist_true_id, artist.id)

    def test_get_artist_newest_release(self):
        newest_release = get_newest_release_by_artist_id(self.valid_artist_true_id)
        curr_date = datetime.today().strftime('%Y-%m-%d')
        if newest_release:
            self.assertTrue(newest_release['release_date'] == curr_date)


if __name__ == '__main__':
    unittest.main()
