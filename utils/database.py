import os
import mysql.connector
from collections import defaultdict


class Artist:

    def __init__(self, name, artist_id, guild_id=None, latest_release_id=None, role_id=None):
        self.id = artist_id
        self.name = name
        self.role_id = role_id
        self.latest_release_id = latest_release_id
        self.guild_id = guild_id


class Guild:

    def __init__(self, guild_id, music_channel_id):
        self.id = guild_id
        self.music_channel_id = music_channel_id


class ArtistAlreadyExistsException(Exception):

    def __init__(self):
        super().__init__("Already following artist")


class NotFollowingArtistException(Exception):

    def __init__(self):
        super().__init__("Not following artist")


class MusicDatabase:

    def __init__(self):
        self.db = mysql.connector
        # Populate cache
        self.guilds = self.get_all_guilds()
        self.artists = self.get_all_artists()

    def get_connection(self):
        return self.db.connect(
            host='localhost',
            user='musicbot',
            password=os.environ.get('MUSIC_BOT_DB_PASSWORD'),
            database='musicbot',
        )

    def add_artist(self, artist):
        con = self.get_connection()
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO Artists(artist_id, name, role_id, guild_id) VALUES('%s','%s','%s','%s')"
                        % (artist.id, artist.name, artist.role_id, artist.guild_id))
            self.artists[artist.id][artist.guild_id] = artist
        except self.db.IntegrityError:
            raise ArtistAlreadyExistsException()
        con.commit()
        con.close()

    def remove_artist(self, artist):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists WHERE artist_id='%s' and guild_id='%s'" % (artist.id, artist.guild_id))
        if len(cur.fetchall()) <= 0:
            raise NotFollowingArtistException
        cur.execute("DELETE FROM Artists WHERE artist_id='%s' and guild_id='%s'" % (artist.id, artist.guild_id))
        self.artists[artist.id][artist.guild_id] = None
        con.commit()
        con.close()

    def get_all_artists(self):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists")
        rows = cur.fetchall()
        all_artists = [Artist(name=row[1], artist_id=row[0], role_id=row[2], latest_release_id=row[3],
                              guild_id=row[4]) for row in rows]
        artists_dict = defaultdict(dict)
        for artist in all_artists:
            artists_dict[artist.id][artist.guild_id] = artist
        con.close()
        return artists_dict

    def get_artist_for_guild(self, artist_id, guild_id):
        return self.artists[artist_id][guild_id]

    def set_latest_notified_release_for_artist_in_guild(self, new_release_id, artist_id, guild_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("UPDATE Artists SET latest_release_id='%s' WHERE "
                    "artist_id='%s' AND guild_id='%s'" % (new_release_id, artist_id, guild_id))
        con.commit()
        self.artists[artist_id][guild_id].latest_release_id = new_release_id
        con.close()

    def get_all_guilds(self):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Guilds")
        rows = cur.fetchall()
        all_guilds = [Guild(guild_id=row[0], music_channel_id=row[1]) for row in rows]
        guilds_dict = {}
        for guild in all_guilds:
            guilds_dict[guild.id] = guild
        con.close()
        return guilds_dict

    def get_music_channel_id_for_guild_id(self, guild_id):
        return self.guilds[guild_id].music_channel_id

    def is_guild_in_db(self, guild_id):
        return guild_id in self.guilds

    def add_guild(self, guild_id, channel_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"INSERT INTO Guilds VALUES({guild_id},{channel_id})")
        con.commit()
        con.close()
        self.guilds[guild_id] = Guild(guild_id, channel_id)

    def update_guild_channel_id(self, guild_id, new_channel_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"UPDATE Guilds SET channel_id={new_channel_id} WHERE guild_id='{guild_id}'")
        con.commit()
        con.close()
        self.guilds[guild_id].music_channel_id = new_channel_id

