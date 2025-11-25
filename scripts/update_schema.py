#!/usr/bin/env python3
"""Safely update the sqlite schema for `data/keylogger.db`.

Backs up the DB and adds columns only when they don't already exist.
"""

from pathlib import Path
import shutil
import sqlite3
import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DB_PATH = DATA_DIR / 'keylogger.db'


def backup_db():
    if not DB_PATH.exists():
        print(f"No DB found at {DB_PATH}")
        return None
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = DATA_DIR / f'keylogger.db.bak.{ts}'
    shutil.copy2(DB_PATH, dest)
    print(f"Backed up DB to {dest}")
    return dest


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cursor.fetchall()]
    return column in cols


def add_column_if_missing(cursor, table, column_def):
    column = column_def.split()[0]
    if not column_exists(cursor, table, column):
        print(f"Adding column {column} to {table}")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    else:
        print(f"Column {column} already exists on {table}")


def update_schema():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    backup_db()

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='device'")
    if not c.fetchone():
        print('No `device` table found — skipping schema updates')
        conn.close()
        return

    add_column_if_missing(c, 'device', 'os_info TEXT')
    add_column_if_missing(c, 'device', 'hostname TEXT')
    add_column_if_missing(c, 'device', 'battery_level INTEGER')
    add_column_if_missing(c, 'device', 'ip_address TEXT')

    conn.commit()
    conn.close()
    print('Schema updated successfully')


if __name__ == '__main__':
    update_schema()
