#!/usr/bin/env python3
"""Create the database tables using the Flask app's `db` object.

Place this file in `scripts/` so it is not in the project root.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import app, db


def ensure_data_dir():
    data_dir = ROOT / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)


def main():
    ensure_data_dir()
    with app.app_context():
        db.create_all()
        print('Database tables created (or already exist)')


if __name__ == '__main__':
    main()
