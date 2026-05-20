import sqlite3

connection = sqlite3.connect("skydeals.db")

cursor = connection.cursor()

codes = cursor.execute("SELECT code FROM airports;")
codes = cursor.fetchall()
connection.commit()
connection.close()

print(codes)
