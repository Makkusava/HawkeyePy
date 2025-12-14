import asyncio
from typing import Any, Dict, Awaitable, Callable

from app.loggers.db_logger import insert_log_journal


async def log_journal_consumer(
    *,
    queue: asyncio.Queue[Dict[str, Any]],
    db_conn,
    emit_socket: Callable[[Dict[str, Any]], Awaitable[None]] | None = None,
) -> None:
    while True:
        payload = await queue.get()
        try:
            await insert_log_journal(db_conn, payload)
            if emit_socket is not None:
                await emit_socket(payload)
        finally:
            queue.task_done()
