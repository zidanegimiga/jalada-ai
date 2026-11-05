"""Worker entry point and composition root."""

import logging
import signal
import threading
from typing import Protocol

from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork, create_database_engine
from jalada.adapters.system_clock import SystemClock
from jalada.adapters.text.reader import PlainAndPdfTextReader
from jalada.application.evidence_capture import PROCESS_EVIDENCE_JOB
from jalada.application.evidence_processing import EvidenceProcessor
from jalada.application.job_runner import JobRunner
from jalada.composition import build_evidence_store
from jalada.config.settings import Settings, load_settings
from jalada.pipeline.process import Budget

logger = logging.getLogger("jalada.worker")

POLL_INTERVAL_SECONDS = 5.0


class Runner(Protocol):
    def run_one(self) -> bool: ...


def run(settings: Settings, stop: threading.Event, poll_interval: float, jobs: Runner) -> None:
    """Work through due jobs, then wait. Returns once `stop` is set."""
    logger.info("worker started in %s", settings.environment)
    while not stop.is_set():
        if not jobs.run_one():
            stop.wait(poll_interval)
    logger.info("worker stopped")


def install_stop_signals(stop: threading.Event) -> None:
    """Set `stop` when the process is asked to shut down (Ctrl+C or docker stop)."""
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_: stop.set())


def build_job_runner(settings: Settings) -> JobRunner:
    session_factory = sessionmaker(create_database_engine(settings.database_url))
    clock = SystemClock()
    processor = EvidenceProcessor(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        store=build_evidence_store(settings),
        reader=PlainAndPdfTextReader(),
        clock=clock,
        budget=Budget(),
    )
    return JobRunner(
        lambda: SqlUnitOfWork(session_factory), {PROCESS_EVIDENCE_JOB: processor}, clock
    )


def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level)
    stop = threading.Event()
    install_stop_signals(stop)
    run(settings, stop, POLL_INTERVAL_SECONDS, build_job_runner(settings))
