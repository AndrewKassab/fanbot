import mysql.connector
import os


def get_connection():
    return mysql.connector.connect(host='localhost',
                                   user='fanbot',
                                   password=os.environ.get('FANBOT_DB_PASSWORD'),
                                   database='fanbot',
                                   )


con = get_connection()
cur = con.cursor()

cur.execute('DROP TABLE IF EXISTS Guilds')
cur.execute('DROP TABLE IF EXISTS Artists')

cur.execute('CREATE TABLE Guilds (guild_id BIGINT NOT NULL PRIMARY KEY, channel_id BIGINT NOT NULL)')

cur.execute('CREATE TABLE Artists (entry_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            'artist_id VARCHAR(25) NOT NULL, name VARCHAR(100), role_id VARCHAR(25) UNIQUE NOT NULL, '
            'latest_release_id VARCHAR(25), latest_release_name VARCHAR(100), guild_id BIGINT NOT NULL)')

con.commit()
con.close()
