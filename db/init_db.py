import sqlite3

con = sqlite3.connect('database.db')
cur = con.cursor()

cur.execute('CREATE TABLE Artists (artist_id TEXT NOT NULL PRIMARY KEY, name VARCHAR(100), latest_release_id TEXT)')

con.commit()
con.close()
