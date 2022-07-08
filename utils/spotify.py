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

sp = spotify.Client(client_id, client_secret)


async def get_artist_by_id(artist_id):
    try:
        result = await sp.get_artist(artist_id)
        return Artist(artist_id=result.id, name=result.name)
    except spotify.errors.HTTPException:
        raise InvalidArtistException


async def get_artists_by_ids(artist_ids):
    if len(artist_ids) == 0 or artist_ids is None:
        return []

    ceiling = 0
    start = 0
    artists = []
    while ceiling < len(artist_ids):
        ceiling += 50
        artists.extend(await sp.get_artists(','.join(artist_ids[start:ceiling])))
        start = ceiling

    artist_dict = {}
    for artist in artists:
        artist_dict[artist.id] = artist
    return artist_dict


async def get_newest_release_by_artist(artist):
    try:
        newest_album = (await artist.get_albums(limit=1, include_groups='album'))
        if is_release_new(newest_album):
            newest_release = convert_album_to_dict(newest_album[0])
            return newest_release
        newest_single = (await artist.get_albums(limit=1, include_groups='single'))
        if is_release_new(newest_single):
            tracks = (await newest_single[0]._Album__client.http.album_tracks(newest_single[0].id))
            if len(tracks['items']) > 1:
                newest_release = convert_album_to_dict(newest_single[0])
            else:
                newest_release = tracks['items'][0]
            return newest_release
        return None
    except (JSONDecodeError, spotify.errors.NotFound, spotify.errors.BearerTokenError) as e:
        logging.exception(e)
        return None


def is_release_new(release):
    if release is None or len(release) == 0:
        return False
    curr_date = datetime.now(tz=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
    today_string = curr_date.strftime('%Y-%m-%d')
    tomorrow_string = (curr_date + timedelta(days=1)).strftime('%Y-%m-%d')
    if release[0].release_date == today_string or (release[0].release_date == tomorrow_string and
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



