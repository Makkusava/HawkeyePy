import pytest

from app.loggers.db_logger import init_db, insert_change_log, insert_log_journal


@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    conn = await init_db(str(db_path))

    async with conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ) as cur:
        rows = await cur.fetchall()
        names = [r[0] for r in rows]

    assert "file_events" in names
    assert "log_journal" in names

    await conn.close()


@pytest.mark.asyncio
async def test_insert_change_log(tmp_path):
    db_path = tmp_path / "test.db"
    conn = await init_db(str(db_path))

    payload = {
        "event": "created",
        "src_path": "a.txt",
        "dest_path": None,
        "is_directory": False,
        "timestamp_utc": "2025-01-01T00:00:00.000+00:00",
    }

    await insert_change_log(conn, payload)

    async with conn.execute("SELECT event, src_path, dest_path, is_directory, timestamp_utc FROM file_events") as cur:
        row = await cur.fetchone()

    assert row == ("created", "a.txt", None, 0, payload["timestamp_utc"])
    await conn.close()


@pytest.mark.asyncio
async def test_insert_log_journal(tmp_path):
    db_path = tmp_path / "test.db"
    conn = await init_db(str(db_path))

    payload = {
        "timestamp_utc": "2025-01-01T00:00:00.000+00:00",
        "level": "INFO",
        "message": "Hello",
        "logger_name": "hawkeye",
    }

    await insert_log_journal(conn, payload)

    async with conn.execute("SELECT timestamp_utc, level, message, logger_name FROM log_journal") as cur:
        row = await cur.fetchone()

    assert row == (payload["timestamp_utc"], "INFO", "Hello", "hawkeye")
    await conn.close()
