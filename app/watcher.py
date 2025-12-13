import os
import logging
from typing import Iterable, List, Awaitable

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from app.events import EventEmitter, ChangeFileEvent, EventType

logger = logging.getLogger("hawkeye-watcher")


def _parse_watch_dirs(env_value: str | None) -> List[str]:
    if not env_value:
        return []
    raw = [x.strip() for x in env_value.split(";")]
    return [x for x in raw if x]


class _FileCoreHandler(FileSystemEventHandler):
    def __init__(self, emitter: EventEmitter) -> None:
        super().__init__()
        self._emitter = emitter

    def _emit(self, event_type: EventType, event: FileSystemEvent) -> None:
        self._emitter.emit(
            ChangeFileEvent(
                event=event_type,
                src_path=event.src_path,
                dest_path=getattr(event, "dest_path", None),
                is_directory=getattr(event, "is_directory", False),
            )
        )

    def on_created(self, event: FileSystemEvent) -> None:
        self._emit("created", event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._emit("deleted", event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._emit("modified", event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._emit("moved", event)


class HawkeyWatcher:
    def __init__(self, watch_dirs: Iterable[str], recursive: bool = True) -> None:
        self.emitter = EventEmitter()
        self._observer = Observer()
        self._handler = _FileCoreHandler(self.emitter)
        self._watch_dirs = list(watch_dirs)
        self._recursive = recursive

    @property
    def watch_dirs(self) -> List[str]:
        return self._watch_dirs

    def start(self) -> None:
        if not self._watch_dirs:
            logger.warning("No watch dirs configured. Set WATCH_DIRS env var.")
            return

        for d in self._watch_dirs:
            if not os.path.exists(d):
                logger.warning("Watch dir does not exist: %s", d)
                continue

            self._observer.schedule(self._handler, d, recursive=self._recursive)
            logger.info("Start watching: %s (recursive=%s)", d, self._recursive)

        self._observer.start()

    def stop(self) -> None:
        if self._observer.is_alive():
            self._observer.stop()


def load_from_env() -> HawkeyWatcher:
    watch_dirs = _parse_watch_dirs(os.getenv("WATCH_DIRS"))
    recursive = os.getenv("WATCH_RECURSIVE", "true").lower() == "true"
    return HawkeyWatcher(watch_dirs=watch_dirs, recursive=recursive)
