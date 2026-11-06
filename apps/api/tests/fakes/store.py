"""In-memory storage shared by the fake repositories."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from jalada.application.ports import (
    PipelineRun,
    UserCredentials,
)
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence
from jalada.domain.sessions import Session
from jalada.pipeline.classifier import Preference
from jalada.pipeline.run_types import StepRecord


@dataclass
class Store:
    users: dict[UUID, UserCredentials] = field(default_factory=dict)
    google_subjects: dict[str, UUID] = field(default_factory=dict)
    evidence: dict[UUID, Evidence] = field(default_factory=dict)
    jobs: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    entries: dict[UUID, Entry] = field(default_factory=dict)
    preferences: dict[UUID, dict[str, Preference]] = field(default_factory=dict)
    runs: list[tuple[PipelineRun, list[StepRecord]]] = field(default_factory=list)
    revisions: list[tuple[Entry, Entry]] = field(default_factory=list)
    telegram_codes: dict[str, tuple[UUID, datetime]] = field(default_factory=dict)
    telegram_links: dict[UUID, tuple[int, int]] = field(default_factory=dict)
    # Jobs for the job runner: id to [job, status, run_after].
    queue: dict[int, list[Any]] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    # Payment id to (user id, certificate id).
    certificate_payments: dict[UUID, tuple[UUID, UUID]] = field(default_factory=dict)
