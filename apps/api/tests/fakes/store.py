"""In-memory storage shared by the fake repositories."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from jalada.modules.accounts.application.ports import UserCredentials
from jalada.modules.accounts.domain.sessions import Session
from jalada.modules.evidence.domain.evidence import Evidence
from jalada.modules.ledger.domain.audit import AuditEvent
from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.ledger.domain.transactions import EvidenceRole, Transaction, from_entry
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.classifier import Preference
from jalada.modules.pipeline.domain.run_types import StepRecord


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
    money_accounts: dict[UUID, MoneyAccount] = field(default_factory=dict)
    transactions: dict[UUID, Transaction] = field(default_factory=dict)
    audit_events: list[AuditEvent] = field(default_factory=list)

    def save_entries(self, *entries: Entry) -> None:
        """Saves entries with the transactions that stand beside them, as the pipeline,
        review and migration 0011 always do."""
        for entry in entries:
            self.entries[entry.id] = entry
            if entry.kind == EntryKind.TRANSACTION:
                self.transactions[entry.id] = from_entry(entry, None, EvidenceRole.OTHER)
