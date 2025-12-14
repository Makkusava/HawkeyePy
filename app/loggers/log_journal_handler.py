import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict


class LogJournalQueueHandler(logging.Handler):
    def __init__(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        super().__init__()
        self._loop = loop
        self._queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload: Dict[str, Any] = {
                "timestamp_utc": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger_name": record.name
            }

            self._loop.call_soon_threadsafe(self._safe_put, payload)
        except Exception:
            self.handleError(record)

    def _safe_put(self, payload: Dict[str, Any]) -> None:
        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass
