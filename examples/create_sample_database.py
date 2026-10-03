"""Create an explicitly fictional course catalog for the read-only SQLite demo."""

import argparse
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="data/sample_courses.db")
args = parser.parse_args()
path = Path(args.path)
path.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(path) as db:
    db.execute(
        "CREATE TABLE IF NOT EXISTS courses(code TEXT PRIMARY KEY,title TEXT,credits INTEGER)"
    )
    db.executemany(
        "INSERT OR IGNORE INTO courses VALUES (?,?,?)",
        [
            ("DEMO101", "Sample Python Programming", 12),
            ("DEMO201", "Sample Database Systems", 12),
            ("DEMO301", "Sample AI Applications", 15),
        ],
    )
print(f"Created fictional sample catalog at {path.resolve()}")
