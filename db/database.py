import sqlite3


def add_artist(artist):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("INSERT INTO Artists VALUES('%s','%s')")
    con.commit()
    con.close()


