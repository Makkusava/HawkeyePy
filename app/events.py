from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional

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
            "dest_path": self.dest_path,
            "is_directory": self.is_directory,
            "timestamp_utc": utc_now(),
        }


Handler = Callable[[ChangeFileEvent], None]


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: List[Handler] = []

    def add(self, handler: Handler) -> None:
        self._handlers.append(handler)

    def emit(self, evt: ChangeFileEvent) -> None:
        for h in list(self._handlers):
            try:
                h(evt)
            except Exception:
                logger.exception("Event handler failed: %s", evt)
