import os
from datetime import datetime, timedelta, time
import pytz
from utils.database import Artist
import spotify
from json import JSONDecodeError
import logging
import time


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Artist not found or invalid")


client_id = os.getenv('FANBOT_SPOTIFY_CLIENT_ID')
client_secret = os.getenv('FANBOT_SPOTIFY_CLIENT_SECRET')


async def get_artist_by_id(artist_id):
    sp = spotify.Client(client_id, client_secret)
    try:
        result = await sp.get_artist(artist_id)
        return Artist(artist_id=result.id, name=result.name)
    except spotify.errors.HTTPException:
        raise InvalidArtistException


async def get_artists_from_spotify(artist_ids):
    sp = spotify.Client(client_id, client_secret)
    if len(artist_ids) == 0 or artist_ids is None:
        return []
    artists = await sp.get_artists(','.join(artist_ids))
    artist_dict = {}
    for artist in artists:
        artist_dict[artist.id] = artist
    return artist_dict


async def get_newest_release_by_artist_from_spotify(artist):
    possible_new_releases = []
    artist_albums = []
    offset = 0
    while (len(artist_albums) != 0) or (offset == 0):
        try:
            artist_albums = await artist.get_albums(limit=50, offset=offset)
        except (JSONDecodeError, spotify.errors.NotFound) as e:
            logging.exception(e)
            return None
        except TypeError as e:
            logging.info("We're being rate limited")
            time.sleep(5)  # Wait before we try again
            continue
        possible_new_releases.extend(filter_releases_by_date(artist_albums))
        offset += 50
    # Sometimes utils creates 'albums' featuring multiple artists, we don't want to share these
    actual_new_releases = []
    for release in possible_new_releases:
        if release.artists[0].name != 'Various Artists' and any(x.name == artist.name for x in release.artists):
            actual_new_releases.append(release)
    if len(actual_new_releases) > 0:
        return await get_ideal_newest_release(actual_new_releases)
    return None


def filter_releases_by_date(albums):
    curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
    today_string = curr_date.strftime('%Y-%m-%d')
    tomorrow_string = (curr_date + timedelta(days=1)).strftime('%Y-%m-%d')
    new_items = []
    for item in albums:
        # Making sure the song has already released (with respect to US)
        if item.release_date == today_string or (item.release_date == tomorrow_string and
                                                 curr_date.time() >= time(21, 0)):
            new_items.append(item)
    return new_items


# If there is an album, just return that instead of all the songs in it, otherwise just get a song
async def get_ideal_newest_release(releases):
    for release in releases:
        if release.type != 'single':
            for i in range(len(release.artists)):
                release.artists[i] = release.artists[i].__dict__
            return release.__dict__
    release = releases[0]
    if release.type == 'single':
        tracks = await release._Album__client.http.album_tracks(release.id)
        release = tracks['items'][0]
    return release


def extract_artist_id(artist_link):
    if len(artist_link) < 54:
        raise InvalidArtistException
    without_url = artist_link[32:]
    return without_url.split('?')[0]



