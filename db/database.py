import sqlite3
import os

db_path = os.path.abspath(os.path.dirname(__file__) + "/database.db")


class Artist:

    def __init__(self, name, artist_id, guild_id=None, latest_notified_release=None, role_id=None):
        self.name = name
        self.id = artist_id
        self.role_id = role_id
        self.latest_notified_release = latest_notified_release
        self.guild_id = guild_id


class ArtistAlreadyExistsException(Exception):

    def __init__(self):
        super().__init__("Already following artist")


class NotFollowingArtistException(Exception):

    def __init__(self):
        super().__init__("Not following artist")


class MusicDatabase:

    def __init__(self):
        self.db = sqlite3
        pass

    def get_connection(self):
        return self.db.connect(db_path)

    def add_artist_to_db(self, artist):
        con = self.get_connection()
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO Artists(artist_id, name, role_id, guild_id) VALUES('%s','%s','%s','%s')"
                        % (artist.id, artist.name, artist.role_id, artist.guild_id))
        except self.db.IntegrityError:
            raise ArtistAlreadyExistsException()
        con.commit()
        con.close()

    def remove_artist_from_db(self, artist_name):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists WHERE UPPER(name)='%s'" % str.upper(artist_name))
        if len(cur.fetchall()) <= 0:
            raise NotFollowingArtistException
        cur.execute("DELETE FROM Artists WHERE UPPER(name)='%s'" % str.upper(artist_name))
        con.commit()
        con.close()

    def get_all_artists_from_db(self):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists")
        rows = cur.fetchall()
        all_artists = [Artist(name=row[1], artist_id=row[0], role_id=row[2], latest_notified_release=row[3],
                              guild_id=row[4]) for row in rows]
        con.close()
        return all_artists

    def get_artist_from_db(self, artist_name):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists WHERE UPPER(name)='%s'" % str.upper(artist_name))
        rows = cur.fetchall()
        if len(rows) <= 0:
            return None
        row = rows[0]
        artist = Artist(name=row[1], artist_id=row[0], role_id=row[2], latest_notified_release=row[3], guild_id=row[4])
        con.close()
        return artist

    def set_latest_notified_release_for_artist_id(self, new_release_id, artist_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("UPDATE Artists SET latest_release_id='%s' WHERE artist_id='%s'" % (new_release_id, artist_id))
        con.commit()
        con.close()

    def get_music_channel_id_for_guild_id(self, guild_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"SELECT channel_id FROM Guilds WHERE guild_id='{guild_id}'")
        channel_id = cur.fetchall()[0][0]
        con.close()
        return channel_id

    def is_guild_in_db(self, guild_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"SELECT * FROM Guilds WHERE guild_id='{guild_id}'")
        rows = cur.fetchall()
        if len(rows) <= 0:
            return False
        return True

    def add_guild_to_db(self, guild_id, channel_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"INSERT INTO Guilds VALUES({guild_id},{channel_id})")
        con.commit()
        con.close()

    def update_guild_channel_id(self, guild_id, new_channel_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"UPDATE Guilds SET channel_id={new_channel_id} WHERE guild_id='{guild_id}'")
        con.commit()
        con.close()
        pass

