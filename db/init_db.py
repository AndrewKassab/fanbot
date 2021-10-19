import sqlite3

con = sqlite3.connect('database.db')
cur = con.cursor()

cur.execute('CREATE TABLE Artists (artist_id TEXT NOT NULL PRIMARY KEY, name VARCHAR(100))')

con.commit()
con.close()
