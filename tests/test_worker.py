import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from app.log_config import UTCFormatter
from app.worker import run

ROOT = Path(__file__).resolve().parent.parent


def test_run_ticks_until_stopped() -> None:
    stop = threading.Event()
    ticks: list[int] = []

    def tick() -> None:
        ticks.append(1)
        if len(ticks) == 3:
            stop.set()

    run(stop, interval=0.001, tick=tick)
    assert len(ticks) == 3


def test_run_does_not_tick_when_already_stopped() -> None:
    stop = threading.Event()
    stop.set()
    run(stop, interval=10, tick=lambda: (_ for _ in ()).throw(AssertionError("ticked")))


def test_formatter_uses_utc() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hi", None, None)
    record.created = 0.0  # 1970-01-01T00:00:00Z, regardless of local timezone
    record.msecs = 0.0
    assert UTCFormatter().format(record).startswith("1970-01-01T00:00:00.000Z INFO t hi")


def test_worker_process_shuts_down_cleanly_on_sigterm() -> None:
    env = {**os.environ, "WORKER_HEARTBEAT_SECONDS": "0.1", "TZ": "Africa/Nairobi"}
    proc = subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "app.worker"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Wait until the worker is running (handlers installed) before signalling.
    assert proc.stdout is not None
    head: list[str] = []
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        head.append(line)
        if "heartbeat" in line or not line:
            break
    proc.send_signal(signal.SIGTERM)
    rest, _ = proc.communicate(timeout=5)
    out = "".join(head) + rest

    assert proc.returncode == 0, out
    assert "Traceback" not in out
    assert "heartbeat" in out
    assert "received SIGTERM, shutting down" in out
    assert out.rstrip().endswith("worker stopped")
    # Every line carries a UTC timestamp even though TZ is EAT.
    stamp = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z ")
    assert all(stamp.match(line) for line in out.splitlines()), out
