import sqlite3
import os

db_path = os.path.abspath(os.path.dirname(__file__) + "/database.db")


class ArtistAlreadyExistsException(Exception):

    def __init__(self):
        super().__init__("Already following artist")


def add_artist_to_db(artist):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO Artists VALUES('%s','%s')" % (artist.id, artist.name) )
    except sqlite3.IntegrityError:
        raise ArtistAlreadyExistsException()
    con.commit()
    con.close()


