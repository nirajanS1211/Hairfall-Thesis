"""Seed initial login users into MongoDB.

Usage (from backend/):
    python scripts/seed_users.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import db  # noqa: E402
from auth import hash_password  # noqa: E402

USERS = [
    {"email": "krishna@gmail.com", "password": "krishna@123"},
    {"email": "nirajan@gmail.com", "password": "nirajan@123"},
]


def main():
    database = db.init_db()
    if database is None:
        print("Could not connect to MongoDB. Check MONGODB_URI.")
        sys.exit(1)

    for u in USERS:
        email = u["email"].lower().strip()
        if database[db.USERS_COLLECTION].find_one({"email": email}):
            print(f"Skipping {email} (already exists)")
            continue
        database[db.USERS_COLLECTION].insert_one(
            {"email": email, "password_hash": hash_password(u["password"])}
        )
        print(f"Seeded {email}")


if __name__ == "__main__":
    main()
