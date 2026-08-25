import logging
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from pymongo import DESCENDING, MongoClient
from pymongo.database import Database

NUMERIC_FIELDS = [
    "age", "total_protein", "calcium", "iron", "vitamin_d", "alt_liver",
    "manganese", "body_water_content", "stress_level", "total_keratine", "hair_texture",
]

logger = logging.getLogger("hairfall.db")

DB_NAME = "hairfall"
DATASET_COLLECTION = "dataset"
PREDICTIONS_COLLECTION = "predictions"

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
connection_error: Optional[str] = None


def init_db() -> Optional[Database]:
    global _client, _db, connection_error

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        connection_error = "MONGODB_URI environment variable is not set."
        logger.warning(connection_error)
        return None

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[DB_NAME]
        _db[PREDICTIONS_COLLECTION].create_index([("timestamp", DESCENDING)])
        logger.info("Connected to MongoDB.")
        return _db
    except Exception as exc:  # noqa: BLE001
        connection_error = f"Failed to connect to MongoDB: {exc}"
        logger.exception(connection_error)
        _client = None
        _db = None
        return None


def get_db() -> Optional[Database]:
    return _db


def log_prediction(record: dict) -> Optional[str]:
    db = get_db()
    if db is None:
        return None
    record = {**record, "timestamp": datetime.now(timezone.utc)}
    result = db[PREDICTIONS_COLLECTION].insert_one(record)
    return str(result.inserted_id)


def get_prediction_history(limit: int = 20, skip: int = 0) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    cursor = (
        db[PREDICTIONS_COLLECTION]
        .find({}, {"_id": 0})
        .sort("timestamp", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


def get_prediction_count() -> int:
    db = get_db()
    if db is None:
        return 0
    return db[PREDICTIONS_COLLECTION].count_documents({})


def get_dataset_summary() -> Optional[dict]:
    db = get_db()
    if db is None:
        return None
    coll = db[DATASET_COLLECTION]
    total = coll.count_documents({})
    if total == 0:
        return None

    class_counts = {
        row["_id"]: row["count"]
        for row in coll.aggregate([{"$group": {"_id": "$hair_fall", "count": {"$sum": 1}}}])
    }

    group_stage = {"_id": None}
    for field in NUMERIC_FIELDS:
        group_stage[f"{field}_mean"] = {"$avg": f"${field}"}
        group_stage[f"{field}_min"] = {"$min": f"${field}"}
        group_stage[f"{field}_max"] = {"$max": f"${field}"}
    stats = next(coll.aggregate([{"$group": group_stage}]), {})
    stats.pop("_id", None)

    docs = list(coll.find({}, {f: 1 for f in NUMERIC_FIELDS}))
    corr = pd.DataFrame(docs)[NUMERIC_FIELDS].corr().round(3)

    return {
        "row_count": total,
        "class_distribution": {
            "Low": class_counts.get(0, 0),
            "Moderate": class_counts.get(1, 0),
            "High": class_counts.get(2, 0),
        },
        "feature_stats": stats,
        "correlation": {row: corr.loc[row].to_dict() for row in corr.index},
        "correlation_fields": NUMERIC_FIELDS,
    }
