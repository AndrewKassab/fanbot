import os
from datetime import datetime, timedelta, time
import pytz
from utils.database import Artist
import spotify
from json import JSONDecodeError
import logging


class InvalidArtistException(Exception):

    def __init__(self):
        super().__init__("Artist not found or invalid")


client_id = os.getenv('FANBOT_SPOTIFY_CLIENT_ID')
client_secret = os.getenv('FANBOT_SPOTIFY_CLIENT_SECRET')


async def get_artist_by_id(artist_id):
    sp = spotify.Client(client_id, client_secret)
    try:
        result = await sp.get_artist(artist_id)
        await sp.close()
        return Artist(artist_id=result.id, name=result.name)
    except spotify.errors.HTTPException:
        await sp.close()
        raise InvalidArtistException


async def get_newest_release_by_artist(artist_id):
    sp = spotify.Client(client_id, client_secret)
    try:
        newest_release = (await sp.http.artist_albums(artist_id, limit=1, include_groups='album'))['items']
        if not is_release_new(newest_release):
            newest_release = (await sp.http.artist_albums(artist_id, limit=1, include_groups='single'))['items']
            if is_release_new(newest_release):
                tracks = await sp.http.album_tracks(newest_release[0]['id'])
                if len(tracks['items']) <= 1:
                    newest_release = tracks['items']
            else:
                newest_release = None
        await sp.close()
        return newest_release[0] if newest_release else None
    except (JSONDecodeError, spotify.errors.NotFound, spotify.errors.BearerTokenError) as e:
        logging.exception(e.msg + ' for artist id: %s' % artist_id)
        await sp.close()
        return None


def is_release_new(release):
    if release is None or len(release) == 0:
        return False
    curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
    today_string = curr_date.strftime('%Y-%m-%d')
    tomorrow_string = (curr_date + timedelta(days=1)).strftime('%Y-%m-%d')
    if release[0]['release_date'] == today_string or (release[0]['release_date'] == tomorrow_string and
                                                   curr_date.time() >= time(21, 0)):
        return True
    return False


def convert_album_to_dict(album):
    for i in range(len(album.artists)):
        album.artists[i] = album.artists[i].__dict__
    return album.__dict__


def extract_artist_id(artist_link):
    if len(artist_link) < 54:
        raise InvalidArtistException
    without_url = artist_link[32:]
    return without_url.split('?')[0]
