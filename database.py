import sqlite3
import csv

connection = sqlite3.connect("skydeals.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS airports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE
)
""")

with open("airports.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)

    airports = []
    seen = set()

    for row in reader:
        code = row[1].strip().upper()
        if code and code not in seen:
            airports.append((code,))
            seen.add(code)

cursor.executemany(
    "INSERT OR IGNORE INTO airports(code) VALUES (?)",
    airports
)

connection.commit()
connection.close()