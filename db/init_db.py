import mysql.connector
import os


def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='musicbot',
        password=os.environ.get('MUSIC_BOT_DB_PASSWORD'),
        database='musicbot',
    )


con = get_connection()
cur = con.cursor()

cur.execute('CREATE TABLE Guilds (guild_id VARCHAR(18) NOT NULL PRIMARY KEY, channel_id VARCHAR(18) NOT NULL)')
cur.execute('CREATE TABLE Artists (artist_id VARCHAR(22) NOT NULL PRIMARY KEY, name VARCHAR(100), '
            'role_id VARCHAR(18) NOT NULL, latest_release_id VARCHAR(22), guild_id VARCHAR(18) NOT NULL)')

con.commit()
con.close()
