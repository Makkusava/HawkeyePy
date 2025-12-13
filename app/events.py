from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Awaitable, Union

EventType = Literal["created", "deleted", "modified", "moved"]


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
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._handlers: List[SyncHandler] = []
        self._async_handlers: List[AsyncHandler] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = loop

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def add_sync(self, handler: SyncHandler) -> None:
        self._handlers.append(handler)

    def add_async(self, handler: AsyncHandler) -> None:
        self._async_handlers.append(handler)

    async def emit(self, evt: ChangeFileEvent) -> None:
        for h in list(self._handlers):
            h(evt)
        for ah in list(self._async_handlers):
            await ah(evt)
