"""Worker entry point and composition root."""

import logging
import signal
import threading

from jalada.config.settings import Settings, load_settings

logger = logging.getLogger("jalada.worker")

POLL_INTERVAL_SECONDS = 5.0


def run(settings: Settings, stop: threading.Event, poll_interval: float) -> None:
    """Wait for jobs until `stop` is set. Returns once the worker has stopped."""
    logger.info("worker started in %s", settings.environment)
    while not stop.wait(poll_interval):
        pass
    logger.info("worker stopped")


def install_stop_signals(stop: threading.Event) -> None:
    """Set `stop` when the process is asked to shut down (Ctrl+C or docker stop)."""
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_: stop.set())


def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level)
    stop = threading.Event()
    install_stop_signals(stop)
    run(settings, stop, POLL_INTERVAL_SECONDS)
