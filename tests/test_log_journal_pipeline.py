import asyncio
import pytest

from app.loggers.log_journal_pipeline import log_journal_consumer  # :contentReference[oaicite:9]{index=9}


@pytest.mark.asyncio
async def test_log_journal_consumer_writes_and_emits(monkeypatch):
    q: asyncio.Queue = asyncio.Queue()
    payload = {
        "timestamp_utc": "2025-01-01T00:00:00.000+00:00",
        "level": "INFO",
        "message": "hi",
        "logger_name": "x",
    }
    await q.put(payload)

    calls = {"db": 0, "socket": 0}

    async def fake_insert_log_journal(db_conn, p):
        assert p is payload
        calls["db"] += 1

    async def fake_emit_socket(p):
        assert p is payload
        calls["socket"] += 1
        raise asyncio.CancelledError()

    monkeypatch.setattr("app.loggers.log_journal_pipeline.insert_log_journal", fake_insert_log_journal)

    task = asyncio.create_task(
        log_journal_consumer(queue=q, db_conn=object(), emit_socket=fake_emit_socket)
    )

    with pytest.raises(asyncio.CancelledError):
        await task

    assert calls["db"] == 1
    assert calls["socket"] == 1
