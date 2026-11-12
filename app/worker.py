"""Background worker. For now it only emits a heartbeat; outbox, timeouts and
scheduled jobs will run from this loop later.

Shuts down cleanly on SIGTERM (docker stop) and SIGINT (Ctrl-C).
"""

import logging
import signal
import threading
from collections.abc import Callable

from app.config import get_settings
from app.log_config import configure_logging

log = logging.getLogger("app.worker")


def run(stop: threading.Event, interval: float, tick: Callable[[], None]) -> None:
    """Call `tick` every `interval` seconds until `stop` is set."""
    while not stop.is_set():
        tick()
        stop.wait(interval)


def heartbeat() -> None:
    log.info("heartbeat")


def main() -> int:
    configure_logging()
    settings = get_settings()
    stop = threading.Event()
    received: list[str] = []

    # Keep the handler minimal: logging here can re-enter a stream write that the
    # main thread was interrupted in the middle of, which raises. Log after the loop.
    def request_stop(signum: int, _frame: object) -> None:
        received.append(signal.Signals(signum).name)
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    log.info("worker started (heartbeat every %ss)", settings.worker_heartbeat_seconds)
    run(stop, settings.worker_heartbeat_seconds, heartbeat)
    log.info("received %s, shutting down", received[0] if received else "stop")
    log.info("worker stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
