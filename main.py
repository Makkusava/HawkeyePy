import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Awaitable, Callable

import socketio
from fastapi import FastAPI

from config import load_settings
from app.watcher import HawkeyWatcher
from app.pipeline import make_enqueue, events_consumer
from app.loggers.db_logger import init_db
from app.loggers.log_journal_handler import LogJournalQueueHandler
from app.loggers.log_journal_pipeline import log_journal_consumer


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("hawkeye")


settings = load_settings()

path = Path("/watch")
path.mkdir(parents=True, exist_ok=True)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

events_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=settings.queue_maxsize)
logs_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=settings.queue_maxsize)

watcher = HawkeyWatcher(watch_dirs=settings.watch_dirs, use_polling=settings.use_polling, recursive=settings.watch_recursive)


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socket connected: %s", sid)
    await sio.emit("hello", {"status": "connected"}, to=sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected: %s", sid)


async def _emit_socket(event_name: str, payload: Dict[str, Any]) -> None:
    await sio.emit(event_name, payload)


async def _cancel_task(task: Optional[asyncio.Task]) -> None:
    if not task:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def _attach_global_log_handler(
    *,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[Dict[str, Any]],
    level: int = logging.INFO,
) -> LogJournalQueueHandler:
    root_logger = logging.getLogger()
    handler = LogJournalQueueHandler(loop=loop, queue=queue)
    handler.setLevel(level)
    root_logger.addHandler(handler)
    return handler


def _detach_global_log_handler(handler: LogJournalQueueHandler) -> None:
    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)
    handler.close()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    loop = asyncio.get_running_loop()

    if not settings.watch_dirs:
        logger.warning("WATCH_DIRS is empty. Nothing will be watched.")

    db_conn = await init_db(settings.db_path)

    watcher.emitter.add(make_enqueue(loop=loop, queue=events_queue))
    watcher.start()

    journal_handler = _attach_global_log_handler(loop=loop, queue=logs_queue, level=logging.DEBUG)

    events_task = asyncio.create_task(
        events_consumer(
            queue=events_queue,
            db_conn=db_conn,
            emit_socket=lambda p: _emit_socket(settings.socket_file_change_event_name, p),
        ),
        name="hawkeye-events-consumer",
    )

    logs_task = asyncio.create_task(
        log_journal_consumer(
            queue=logs_queue,
            db_conn=db_conn,
            emit_socket=lambda p: _emit_socket(settings.socket_log_event_name, p),
        ),
        name="hawkeye-logs-consumer",
    )

    logger.info("Startup complete")

    yield

    await _cancel_task(events_task)
    await _cancel_task(logs_task)

    _detach_global_log_handler(journal_handler)

    watcher.stop()
    await db_conn.close()
    logger.info("SQLite closed")


fastapi_app = FastAPI(lifespan=lifespan)


@fastapi_app.get("/")
async def root():
    return {
        "app": "Hawkeye",
        "socket_file_change_event": settings.socket_file_change_event_name,
        "socket_log_event": settings.socket_log_event_name
    }


@fastapi_app.get("/health")
async def health():
    return {"status": "OK"}


socketio_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
fastapi_app.mount("/", socketio_app)
