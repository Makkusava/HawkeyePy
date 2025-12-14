import logging

import aiosqlite
from typing import Any, Dict

logger = logging.getLogger("hawkeye-db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS file_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    src_path TEXT NOT NULL,
    dest_path TEXT NULL,
    is_directory INTEGER NOT NULL,
    timestamp_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_file_events_event ON file_events(event);
    
CREATE TABLE IF NOT EXISTS log_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    logger_name TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_log_journal_level ON log_journal(level);
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
            payload["event"],
            payload["src_path"],
            payload.get("dest_path"),
            1 if payload["is_directory"] else 0,
            payload["timestamp_utc"],
        ),
    )
    await conn.commit()

async def insert_log_journal(conn: aiosqlite.Connection, payload: Dict[str, Any]) -> None:
    await conn.execute(
        """
        INSERT INTO log_journal(timestamp_utc, level, message, logger_name)
        VALUES(?, ?, ?, ?)
        """,
        (
            payload["timestamp_utc"],
            payload["level"],
            payload["message"],
            payload["logger_name"],
        ),
    )
    await conn.commit()