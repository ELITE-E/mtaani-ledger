"""Logging with UTC ISO-8601 timestamps (spec 01: all timestamps are UTC)."""

import logging
import sys
import time


class UTCFormatter(logging.Formatter):
    converter = time.gmtime

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s.%(msecs)03dZ %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(UTCFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
