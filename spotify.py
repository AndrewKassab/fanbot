import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from datetime import datetime


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Invalid Artist")


client_id = os.getenv('MUSIC_BOT_CLIENT_ID')
client_secret = os.getenv('MUSIC_BOT_CLIENT_SECRET')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))


def get_artist_id_by_name(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        return artist['id']
    else:
        raise InvalidArtistException


# New means current day
def get_new_releases_by_artist_id(artist_id):
    new_releases = []
    curr_date = datetime.today().strftime('%Y-%m-%d')
    artist_albums = []
    offset = 0
    while (len(artist_albums) != 0) or (offset == 0):
        artist_albums = sp.artist_albums(artist_id, limit=50, offset=offset)['items']
        new_releases.extend(filter_releases_by_date(artist_albums, curr_date))
        offset += 50
    return new_releases


def filter_releases_by_date(albums, date):
    new_items = []
    for item in albums:
        if item['release_date'] == date:
            new_items.append(item)
    return new_items
