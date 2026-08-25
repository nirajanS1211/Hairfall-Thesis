import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clean_dataset import load_clean_dataset  # noqa: E402
from db import DATASET_COLLECTION, DB_NAME  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("MONGODB_URI is not set (check your .env file). Aborting.")
        sys.exit(1)

    df = load_clean_dataset()
    records = df.to_dict(orient="records")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    coll = client[DB_NAME][DATASET_COLLECTION]

    existing = coll.count_documents({})
    if existing > 0:
        answer = input(
            f"'{DATASET_COLLECTION}' already has {existing} documents. "
            f"Drop and reseed? [y/N] "
        )
        if answer.strip().lower() != "y":
            print("Aborted, no changes made.")
            return
        coll.delete_many({})

    coll.insert_many(records)
    print(f"Inserted {len(records)} documents into {DB_NAME}.{DATASET_COLLECTION}")


if __name__ == "__main__":
    main()
