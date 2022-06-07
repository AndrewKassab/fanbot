import os
from datetime import datetime, timedelta
from utils.database import Artist
import spotify


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Artist not found or invalid")


client_id = os.getenv('MUSIC_BOT_CLIENT_ID')
client_secret = os.getenv('MUSIC_BOT_CLIENT_SECRET')

sp = spotify.Client(client_id, client_secret)


async def get_artist_by_id(artist_id):
    try:
        result = await sp.get_artist(artist_id)
        return Artist(artist_id=result.id, name=result.name)
    except spotify.errors.HTTPException:
        raise InvalidArtistException


# New means current day
async def get_newest_release_by_artist_id(artist_id):
    possible_new_releases = []
    artist_albums = []
    offset = 0
    artist = await sp.get_artist(artist_id)
    while (len(artist_albums) != 0) or (offset == 0):
        artist_albums = await artist.get_albums(limit=50, offset=offset)
        possible_new_releases.extend(filter_releases_by_date(artist_albums))
        offset += 50
    # Sometimes utils creates 'albums' featuring multiple artists, we don't want to share these
    actual_new_releases = []
    for release in possible_new_releases:
        if release.artists[0].name != 'Various Artists':
            actual_new_releases.append(release)
    if len(actual_new_releases) > 0:
        return await get_ideal_newest_release(actual_new_releases)
    return None


# If there is an album, just return that instead of all the songs in it, otherwise just get a song
async def get_ideal_newest_release(releases):
    for release in releases:
        if release.type != 'single':
            return release.__dict__
    release = releases[0]
    if release.type == 'single':
        tracks = await release._Album__client.http.album_tracks(release.id)
        release = tracks['items'][0]
    return release


def filter_releases_by_date(albums):
    curr_date = datetime.today()
    today_string = curr_date.strftime('%Y-%m-%d')
    tomorrow_string = (curr_date + timedelta(days=1)).strftime('%Y-%m-%d')
    new_items = []
    for item in albums:
        if item.release_date == today_string or item.release_date == tomorrow_string:
            new_items.append(item)
    return new_items


def extract_artist_id(artist_link):
    if len(artist_link) < 54:
        raise InvalidArtistException
    without_url = artist_link[32:]
    return without_url.split('?')[0]



