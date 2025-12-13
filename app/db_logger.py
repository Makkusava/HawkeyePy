import aiosqlite
from typing import Any, Dict, Optional


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS file_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    src_path TEXT NOT NULL,
    dest_path TEXT NULL,
    is_directory INTEGER NOT NULL,
    timestamp_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_file_events_timestamp ON file_events(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_file_events_event ON file_events(event);
"""


async def init_db(db_path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    await conn.executescript(CREATE_TABLE_SQL)
    await conn.commit()
    return conn


async def insert_change_log(conn: aiosqlite.Connection, payload: Dict[str, Any]) -> None:
    await conn.execute(
        """
        INSERT INTO file_events(event, src_path, dest_path, is_directory, timestamp_utc)
        VALUES(?, ?, ?, ?, ?)
        """,
        (
            payload.get("event"),
            payload.get("src_path"),
            payload.get("dest_path"),
            1 if payload.get("is_directory") else 0,
            payload.get("timestamp_utc"),
        ),
    )
    await conn.commit()
