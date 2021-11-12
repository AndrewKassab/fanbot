import sqlite3
import os
from spotify import Artist

db_path = os.path.abspath(os.path.dirname(__file__) + "/database.db")


class ArtistAlreadyExistsException(Exception):

    def __init__(self):
        super().__init__("Already following artist")


class NotFollowingArtistException(Exception):

    def __init__(self):
        super().__init__("Not following artist")


def add_artist_to_db(artist):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO Artists VALUES('%s','%s')" % (artist.id, artist.name) )
    except sqlite3.IntegrityError:
        raise ArtistAlreadyExistsException()
    con.commit()
    con.close()


def remove_artist_from_db(artist_name):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT * FROM Artists WHERE UPPER(name)='%s'" % str.upper(artist_name))
    if len(cur.fetchall()) <= 0:
        raise NotFollowingArtistException
    cur.execute("DELETE FROM Artists WHERE UPPER(name)='%s'" % str.upper(artist_name))
    con.commit()
    con.close()


def get_all_artists_from_db():
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT * FROM Artists")
    rows = cur.fetchall()
    return [Artist(name=row[1], id=row[0]) for row in rows]

