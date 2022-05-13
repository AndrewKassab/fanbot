import sqlite3

con = sqlite3.connect('database.db')
cur = con.cursor()

cur.execute('CREATE TABLE Guilds (guild_id TEXT NOT NULL PRIMARY KEY, channel_id TEXT NOT NULL)')
cur.execute('CREATE TABLE Artists (artist_id TEXT NOT NULL PRIMARY KEY, name VARCHAR(100), role_id TEXT NOT NULL, latest_release_id TEXT, guild_id TEXT NOT NULL)')

con.commit()
con.close()
