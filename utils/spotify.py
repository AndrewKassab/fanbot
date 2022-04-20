import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from datetime import datetime


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Artist not found or invalid")


class Artist:

    def __init__(self, name, id):
        self.name = name
        self.id = id


client_id = os.getenv('MUSIC_BOT_CLIENT_ID')
client_secret = os.getenv('MUSIC_BOT_CLIENT_SECRET')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))


def get_artist_by_name(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        artist = items[0]
        return Artist(artist['name'], artist['id'])
    else:
        raise InvalidArtistException


# New means current day
def get_newest_release_by_artist_id(artist_id):
    possible_new_releases = []
    curr_date = datetime.today().strftime('%Y-%m-%d')
    artist_albums = []
    offset = 0
    while (len(artist_albums) != 0) or (offset == 0):
        artist_albums = sp.artist_albums(artist_id, limit=50, offset=offset)['items']
        possible_new_releases.extend(filter_releases_by_date(artist_albums, curr_date))
        offset += 50
    # Sometimes utils creates 'albums' featuring multiple artists, we don't want to share these
    actual_new_releases = []
    for release in possible_new_releases:
        if release['artists'][0]['name'] != 'Various Artists':
            actual_new_releases.append(release)
    if len(actual_new_releases) > 0:
        return get_ideal_newest_release(actual_new_releases)
    return None


# If there is an album, just return that instead of all the songs in it, otherwise just get a song
def get_ideal_newest_release(releases):
    for release in releases:
        if release['type'] == 'album' and release['album_type'] != 'single':
            return release
    release = releases[0]
    if release['album_type'] == 'single':
        tracks = sp.album_tracks(releases[0]['id'])
        release = tracks['items'][0]
    return release


def filter_releases_by_date(albums, date):
    new_items = []
    for item in albums:
        if item['release_date'] == date:
            new_items.append(item)
    return new_items

