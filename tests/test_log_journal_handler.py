import asyncio
import logging
import pytest

from app.loggers.log_journal_handler import LogJournalQueueHandler


@pytest.mark.asyncio
async def test_log_journal_handler_enqueues_payload(event_loop):
    q: asyncio.Queue = asyncio.Queue()
    handler = LogJournalQueueHandler(loop=event_loop, queue=q)

    record = logging.LogRecord(
        name="test-logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Hello %s",
        args=("world",),
        exc_info=None,
    )

    handler.emit(record)

    await asyncio.sleep(0)

    payload = await q.get()
    assert payload["level"] == "INFO"
    assert payload["message"] == "Hello world"
    assert payload["logger_name"] == "test-logger"
    assert "timestamp_utc" in payload
