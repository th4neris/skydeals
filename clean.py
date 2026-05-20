import sqlite3

conn = sqlite3.connect("skydeals.db")
cur = conn.cursor()

cur.execute("""
DELETE FROM flight_tracks_return
""")

conn.commit()
conn.close()