import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Invalid Artist")


sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())


# TODO: Retrieve artist id from searching the artist name on spotify api
def get_artist_id(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        # TODO: return artist id
    else:
        raise InvalidArtistException


def get_artist_newest_release(artist_id):
    pass