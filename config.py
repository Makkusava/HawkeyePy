import os
from dataclasses import dataclass
from typing import List


def parse_watch_dirs(value: str | None) -> List[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(";") if p.strip()]


@dataclass(frozen=True)
class Settings:
    watch_dirs: List[str]
    watch_recursive: bool
    db_path: str
    queue_maxsize: int
    socket_file_change_event_name: str
    socket_log_event_name: str


def load_settings() -> Settings:
    return Settings(
        watch_dirs=parse_watch_dirs(os.getenv("WATCH_DIRS", "watch/WatchDir1;watch/WatchDir2;watch/WatchDir3")),
        watch_recursive=os.getenv("WATCH_RECURSIVE", "true").lower() == "true",
        db_path=os.getenv("DB_PATH", "hawkeye.db"),
        queue_maxsize=int(os.getenv("QUEUE_MAXSIZE", "10000")),
        socket_file_change_event_name=os.getenv("SOCKET_FILE_CHANGE_EVENT_NAME", "file_change_event"),
        socket_log_event_name=os.getenv("SOCKET_LOG_EVENT_NAME", "log_event"),
    )
