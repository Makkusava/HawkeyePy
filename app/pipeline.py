import asyncio
import logging
import traceback
from typing import Any, Awaitable, Callable, Dict

from app.events import ChangeFileEvent
from app.loggers.db_logger import insert_change_log

logger = logging.getLogger("hawkeye-pipeline")


def log_payload(p: Dict[str, Any]) -> None:
    if p.get("event") == "moved":
        logger.info(
            "[%s] dir=%s | %s -> %s",
            p.get("event"),
            p.get("is_directory"),
            p.get("src_path"),
            p.get("dest_path"),
        )
    else:
        logger.info(
            "[%s] dir=%s | %s",
            p.get("event"),
            p.get("is_directory"),
            p.get("src_path"),
        )


def make_enqueue(
    *,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[Dict[str, Any]],
) -> Callable[[ChangeFileEvent], None]:
    def enqueue(evt: ChangeFileEvent) -> None:
        payload = evt.to_dict()

        def _safe_put() -> None:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Events queue is full, dropping event")
            except Exception:
                logger.exception("Failed to enqueue event")

        loop.call_soon_threadsafe(_safe_put)

    return enqueue


async def events_consumer(
    *,
    queue: asyncio.Queue[Dict[str, Any]],
    db_conn,
    emit_socket: Callable[[Dict[str, Any]], Awaitable[None]],
) -> None:
    while True:
        payload = await queue.get()
        try:
            log_payload(payload)
            await insert_change_log(db_conn, payload)
            await emit_socket(payload)

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Failed to process file event: %s", payload)

        finally:
            queue.task_done()
