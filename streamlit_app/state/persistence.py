from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from tinydb import TinyDB


def _db_path() -> Path:
    env_dir = os.environ.get("APP_DATA_DIR")
    if env_dir:
        data_dir = Path(env_dir)
    else:
        # Default to ./data when not configured
        data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "app.json"


def get_db() -> TinyDB:
    return TinyDB(_db_path())


def save_devices(devices_json: list[dict]) -> None:
    db = get_db()
    table = db.table("devices")
    table.truncate()
    table.insert({"devices": devices_json})
    db.close()


def load_devices() -> list[dict]:
    db = get_db()
    table = db.table("devices")
    rows = table.all()
    db.close()
    if rows:
        row = rows[0]
        if "devices" in row:
            return row["devices"]
    return []


def save_settings(settings: dict) -> None:
    db = get_db()
    table = db.table("settings")
    table.truncate()
    table.insert({**settings})
    db.close()


def load_settings() -> dict:
    db = get_db()
    table = db.table("settings")
    rows = table.all()
    db.close()
    return (rows[0] if rows else {})
