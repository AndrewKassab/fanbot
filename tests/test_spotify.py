import unittest
from spotify import InvalidArtistException, get_artist_id


class TestSpotify(unittest.TestCase):

    def test_get_artist_id_invalid(self):
        self.assertRaises(InvalidArtistException, get_artist_id, "invalid artist name")

    def test_get_artist_id_valid(self):
        artist_id = get_artist_id("Porter Robinson")
        self.assertIsNotNone(artist_id)


if __name__ == '__main__':
    unittest.main()
