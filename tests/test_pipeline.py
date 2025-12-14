import asyncio
import pytest

from app.events import ChangeFileEvent
from app.pipeline import make_enqueue, events_consumer  # :contentReference[oaicite:5]{index=5}


@pytest.mark.asyncio
async def test_make_enqueue_puts_payload_into_queue(event_loop):
    q: asyncio.Queue = asyncio.Queue()
    enqueue = make_enqueue(loop=event_loop, queue=q)

    evt = ChangeFileEvent(event="created", src_path="a", dest_path=None, is_directory=False)
    enqueue(evt)

    await asyncio.sleep(0)

    payload = await q.get()
    assert payload["event"] == "created"
    assert payload["src_path"] == "a"
    assert "timestamp_utc" in payload


@pytest.mark.asyncio
async def test_events_consumer_calls_db_and_socket(monkeypatch):
    q: asyncio.Queue = asyncio.Queue()
    payload = {
        "event": "created",
        "src_path": "a",
        "dest_path": None,
        "is_directory": False,
        "timestamp_utc": "x",
    }

    await q.put(payload)

    calls = {"db": 0, "socket": 0}

    async def fake_insert_change_log(db_conn, p):
        assert p is payload
        calls["db"] += 1

    async def fake_emit_socket(p):
        assert p is payload
        calls["socket"] += 1
        raise asyncio.CancelledError()

    monkeypatch.setattr("app.pipeline.insert_change_log", fake_insert_change_log)

    task = asyncio.create_task(events_consumer(queue=q, db_conn=object(), emit_socket=fake_emit_socket))

    with pytest.raises(asyncio.CancelledError):
        await task

    assert calls["db"] == 1
    assert calls["socket"] == 1
