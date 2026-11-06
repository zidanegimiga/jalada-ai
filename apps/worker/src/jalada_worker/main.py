"""Worker entry point. The job loop itself is built in jalada.composition."""

import logging
import signal
import threading

from jalada.application.job_runner import Runs, work_until
from jalada.composition import build_job_runner
from jalada.config.logging import configure_logging
from jalada.config.settings import Settings, load_settings

logger = logging.getLogger("jalada.worker")

POLL_INTERVAL_SECONDS = 5.0


def run(settings: Settings, stop: threading.Event, poll_interval: float, jobs: Runs) -> None:
    """Work through due jobs, then wait. Returns once `stop` is set."""
    logger.info("worker started in %s", settings.environment)
    work_until(stop, jobs, poll_interval)
    logger.info("worker stopped")


def install_stop_signals(stop: threading.Event) -> None:
    """Set `stop` when the process is asked to shut down (Ctrl+C or docker stop)."""
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_: stop.set())


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level, settings.json_logs)
    stop = threading.Event()
    install_stop_signals(stop)
    run(settings, stop, POLL_INTERVAL_SECONDS, build_job_runner(settings))
