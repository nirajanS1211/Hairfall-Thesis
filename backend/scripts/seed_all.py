"""Seed both login users and the prediction dataset into MongoDB.

Idempotent — safe to re-run; skips anything already present.

Usage (from repo root):
    npm run seed

Or directly (from backend/):
    python scripts/seed_all.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import db  # noqa: E402
from auth import hash_password  # noqa: E402
from clean_dataset import load_clean_dataset  # noqa: E402

# Add new students here as needed — re-running the script only inserts new emails.
USERS = [
    {"email": "krishna@gmail.com", "password": "krishna@123"},
    {"email": "nirajan@gmail.com", "password": "nirajan@123"},
]


def seed_users(database) -> None:
    print("Seeding users...")
    for u in USERS:
        email = u["email"].lower().strip()
        if database[db.USERS_COLLECTION].find_one({"email": email}):
            print(f"  Skipping {email} (already exists)")
            continue
        database[db.USERS_COLLECTION].insert_one(
            {"email": email, "password_hash": hash_password(u["password"])}
        )
        print(f"  Seeded {email}")


def seed_dataset(database) -> None:
    print("Seeding prediction dataset...")
    existing = database[db.DATASET_COLLECTION].count_documents({})
    if existing > 0:
        print(f"  Skipping ({existing} documents already present)")
        return
    df = load_clean_dataset()
    records = df.to_dict(orient="records")
    database[db.DATASET_COLLECTION].insert_many(records)
    print(f"  Inserted {len(records)} documents")


def main() -> None:
    database = db.init_db()
    if database is None:
        print("Could not connect to MongoDB. Check MONGODB_URI.")
        sys.exit(1)

    seed_users(database)
    seed_dataset(database)
    print("Done.")


if __name__ == "__main__":
    main()
