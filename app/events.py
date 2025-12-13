from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Awaitable, Union

EventType = Literal["created", "deleted", "modified", "moved"]

logger = logging.getLogger("hawkeye-emitter")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class ChangeFileEvent:
    event: EventType
    src_path: str
    dest_path: Optional[str]
    is_directory: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "src_path": self.src_path,
            "dest_path": getattr(self, "dest_path", None),
            "is_directory": self.is_directory,
            "timestamp_utc": utc_now()
        }


SyncHandler = Callable[[ChangeFileEvent], None]
AsyncHandler = Callable[[ChangeFileEvent], Awaitable[None]]

class EventEmitter:
    def __init__(self) -> None:
        self._sync_handlers: List[SyncHandler] = []
        self._async_handlers: List[AsyncHandler] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def add_sync(self, handler: SyncHandler) -> None:
        self._sync_handlers.append(handler)

    def add_async(self, handler: AsyncHandler) -> None:
        self._async_handlers.append(handler)

    def emit(self, evt: ChangeFileEvent) -> None:
        for h in list(self._sync_handlers):
            try:
                h(evt)
            except Exception:
                logger.exception("Sync handler failed")

        if self._async_handlers:
            if not self._loop:
                logger.warning("Async handlers registered but loop is not set")
                return

            for ah in list(self._async_handlers):
                try:
                    coro = ah(evt)
                    if inspect.isawaitable(coro):
                        self._loop.call_soon_threadsafe(asyncio.create_task, coro)
                except Exception:
                    logger.exception("Async handler scheduling failed")