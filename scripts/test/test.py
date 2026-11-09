from pathlib import Path
import sqlite3
import os

ROOT = Path(__file__).resolve().parents[2]
DB_FILE = ROOT / "database" / "movies.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
print ("os.path.exists(DB_FILE):")
cur.execute (
    "SELECT name FROM movies"
)

rows = cur.fetchmany(10)

for row in rows: 
    print(row)
