import os
import mysql.connector
from collections import defaultdict


class Artist:

    def __init__(self, name, artist_id: str, guild_id: int = None, latest_release_id: str = None,
                 latest_release_name=None, role_id: int = None):
        self.id = artist_id
        self.name = name
        self.role_id = role_id
        self.latest_release_id = latest_release_id
        self.latest_release_name = latest_release_name
        self.guild_id = guild_id


class Guild:

    def __init__(self, guild_id, music_channel_id):
        self.id = guild_id
        self.music_channel_id = music_channel_id


class MusicDatabase:

    def __init__(self):
        self.db = mysql.connector
        # Populate cache
        self.guilds = self.get_all_guilds()
        self.guild_to_artists = self.get_all_guilds_to_artists()

    def get_connection(self):
        return self.db.connect(
            host='localhost',
            user='fanbot',
            password=os.environ.get('FANBOT_DB_PASSWORD'),
            database='fanbot',
        )

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

    # TODO: Remove int conversion once DB is fixed
    def get_all_guilds_to_artists(self):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM Artists")
        rows = cur.fetchall()
        all_artists = [Artist(name=row[2], artist_id=row[1], role_id=int(row[3]), latest_release_id=row[4],
                              latest_release_name=row[5], guild_id=int(row[6])) for row in rows]
        artists_dict = defaultdict(dict)
        for artist in all_artists:
            artists_dict[artist.guild_id][artist.id] = artist
        con.close()
        return artists_dict

    def remove_guild(self, guild_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"DELETE FROM Guilds WHERE guild_id='{guild_id}'")
        cur.execute(f"DELETE FROM Artists WHERE guild_id='{guild_id}'")
        con.commit()
        self.guilds.pop(guild_id, None)
        self.guild_to_artists[guild_id] = {}

    def add_artist(self, artist):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("INSERT INTO Artists(artist_id, name, role_id, guild_id) VALUES(%s, %s, %s, %s)",
                    (artist.id, artist.name, artist.role_id, artist.guild_id))
        self.guild_to_artists[artist.guild_id][artist.id] = artist
        con.commit()
        con.close()

    def remove_artist(self, artist):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute("DELETE FROM Artists WHERE artist_id='%s' and guild_id='%s'" % (artist.id, artist.guild_id))
        del self.guild_to_artists[artist.guild_id][artist.id]
        con.commit()
        con.close()

    def get_all_artists(self):
        artists = []
        for artist_dict in self.guild_to_artists.values():
            artists.extend(artist_dict.values())
        return artists

    def get_all_artists_for_guild(self, guild_id):
        return self.guild_to_artists[guild_id]

    def get_artist_for_guild(self, artist_id, guild_id):
        return self.guild_to_artists[guild_id].get(artist_id)

    def set_latest_release_for_artists(self, artists, new_release_id, new_release_name):
        con = self.get_connection()
        cur = con.cursor()
        for artist in artists:
            cur.execute("UPDATE Artists SET latest_release_id='%s' WHERE "
                        "artist_id='%s' AND guild_id='%s'" % (new_release_id, artist.id, artist.guild_id))
            try:
                cur.execute("UPDATE Artists SET latest_release_name='%s' WHERE "
                            "artist_id='%s' AND guild_id='%s'" % (new_release_name, artist.id, artist.guild_id))
            except mysql.connector.errors.DatabaseError:
                continue
        con.commit()
        for artist in artists:
            self.guild_to_artists[artist.guild_id][artist.id].latest_release_id = new_release_id
            self.guild_to_artists[artist.guild_id][artist.id].latest_release_name = new_release_name
        con.close()

    def get_music_channel_id_for_guild_id(self, guild_id):
        return self.guilds.get(guild_id).music_channel_id

    def is_guild_in_db(self, guild_id):
        return guild_id in self.guilds.keys()

    def add_guild(self, guild):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"INSERT INTO Guilds VALUES({guild.id},{guild.music_channel_id})")
        con.commit()
        con.close()
        self.guilds[guild.id] = guild

    def update_guild_channel_id(self, guild_id, new_channel_id):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(f"UPDATE Guilds SET channel_id={new_channel_id} WHERE guild_id='{guild_id}'")
        con.commit()
        con.close()
        self.guilds[guild_id].music_channel_id = new_channel_id

