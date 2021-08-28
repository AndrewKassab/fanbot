import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Invalid Artist")


client_id = "51303df7e9c245e488c1120dfad0b744"
client_secret = "01e46229d55b4102bcec68debc31bda7"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))


def get_artist_id(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        return artist['id']
    else:
        raise InvalidArtistException


def get_artist_newest_release(artist_id):
    pass