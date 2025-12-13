import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any, Dict

import socketio
from fastapi import FastAPI

from app.db_logger import insert_change_log, init_db
from app.watcher import load_from_env
from app.events import ChangeFileEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("hawkeye")

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
_fs_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=10_000)

watcher = load_from_env()


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socket. Client connected: %s", sid)
    await sio.emit("hello", {"status": "connected"}, to=sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket. Client disconnected: %s", sid)


async def _socket_consumer() -> None:
    while True:
        payload = await _fs_queue.get()
        try:
            await sio.emit("fs_event", payload)  # broadcast to all
        finally:
            _fs_queue.task_done()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    loop = asyncio.get_running_loop()

    db_path = os.getenv("DB_PATH", "hawkeye.db")
    db_conn = await init_db(db_path)
    logger.info("SQLite connected: %s", db_path)


    def log(evt: ChangeFileEvent) -> None:
        if evt.event == "moved":
            logger.info("[%s] is_dir: %s | %s -> %s", evt.event, evt.is_directory, evt.src_path, evt.dest_path)
        else:
            logger.info("[%s] is_dir: %s | %s", evt.event, evt.is_directory, evt.src_path)

    def push_to_socket(evt: ChangeFileEvent) -> None:
        payload = evt.to_dict()
        try:
            loop.call_soon_threadsafe(_fs_queue.put_nowait, payload)
        except asyncio.QueueFull:
            pass

    async def insert_to_database(evt: ChangeFileEvent) -> None:
        payload = evt.to_dict()
        await insert_change_log(db_conn, payload)

    watcher.emitter.set_loop(loop)
    watcher.emitter.add_async(insert_to_database)
    watcher.emitter.add_sync(log)
    watcher.emitter.add_sync(push_to_socket)

    watcher.start()
    consumer_task = asyncio.create_task(_socket_consumer())

    yield

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    watcher.stop()


fastapi_app = FastAPI(lifespan=lifespan)


@fastapi_app.get("/")
async def root():
    return {"app": "Hawkeye: Watching your files", "socketio_event": "fs_event"}


@fastapi_app.get("/health")
async def health():
    return {"status": "OK"}


socketio_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
fastapi_app.mount("/", socketio_app)