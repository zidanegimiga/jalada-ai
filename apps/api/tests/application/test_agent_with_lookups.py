"""A whole turn on the real lookups, with a scripted model standing in for the provider."""

import uuid
from dataclasses import replace
from datetime import date
from typing import Any

from fakes import FakeUnitOfWork, FixedClock, ScriptedModel, Store
from fakes.agent import answer, use_tool
from samples import confirmed_entry

from jalada.modules.agent.adapters.orchestration.graph import LangGraphRunner
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.prompts import instructions
from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.tools import ToolRegistry
from jalada.modules.agent.domain.run import Budget, Outcome
from jalada.modules.agent.wiring import build_lookups
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger

ME, SOMEONE_ELSE = uuid.uuid4(), uuid.uuid4()


def kplc(user: uuid.UUID, day: date, cents: int) -> Any:
    entry = confirmed_entry(user, day, cents, "out", "business_other")
    return replace(entry, counterparty="KPLC PREPAID")


def assistant(store: Store, *replies: dict[str, Any]) -> tuple[Conversations, ScriptedModel]:
    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    lookups = build_lookups(
        Ledger(work),
        EntryReview(work, FixedClock()),
        "https://jalada.test",
        ActionProposals(work, FixedClock()),
    )
    model = ScriptedModel(*replies)
    runner = LangGraphRunner(model, ToolRegistry(lookups), Budget())
    return Conversations(work, runner, FixedClock()), model


def test_every_lookup_is_offered_to_the_model(store: Store) -> None:
    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    text = instructions(
        ToolRegistry(build_lookups(Ledger(work), EntryReview(work, FixedClock()), ""))
    )

    for name in [
        "search_payments",
        "add_up_payments",
        "totals_by_category",
        "monthly_summary",
        "waiting_to_check",
        "payment_details",
        "tax_year_workbook",
    ]:
        assert f"- {name}:" in text


def test_a_question_is_answered_from_the_persons_own_totals(store: Store) -> None:
    store.save_entries(
        kplc(ME, date(2026, 7, 4), 250_000),
        kplc(ME, date(2026, 8, 6), 200_000),
        kplc(SOMEONE_ELSE, date(2026, 8, 6), 9_900_000),
    )
    asking, model = assistant(
        store,
        use_tool("add_up_payments", counterparty="KPLC", start="2026-07-01", end="2026-09-30"),
        answer("You paid KPLC Ksh 4,500.00 between July and September, in 2 payments."),
    )

    reply = asking.ask(ME, "How much did I pay KPLC last quarter?")

    assert reply.outcome == Outcome.ANSWERED
    seen = model.calls[1]["content"]
    assert '"money_out": "4500.00"' in seen
    assert "99000.00" not in seen


def test_a_made_up_total_is_never_sent(store: Store) -> None:
    store.save_entries(kplc(ME, date(2026, 7, 4), 250_000))
    asking, _ = assistant(
        store,
        use_tool("add_up_payments", counterparty="KPLC"),
        answer("You paid KPLC Ksh 99,000."),
        answer("You paid KPLC Ksh 99,000."),
    )

    reply = asking.ask(ME, "How much did I pay KPLC?")

    assert reply.outcome == Outcome.WITHHELD
    assert "99,000" not in reply.text


def test_the_workbook_link_points_at_the_web_app(store: Store) -> None:
    asking, model = assistant(
        store, use_tool("tax_year_workbook", year=2025), answer("Here it is.")
    )

    asking.ask(ME, "Can I get my 2025 workbook?")

    assert "https://jalada.test/v1/exports/2025.xlsx" in model.calls[1]["content"]


def test_a_suggested_change_comes_back_with_the_answer_and_changes_nothing(
    store: Store,
) -> None:
    entry = kplc(ME, date(2026, 7, 4), 250_000)
    store.save_entries(entry)
    asking, _ = assistant(
        store,
        use_tool("suggest_category", id=str(entry.id), category="business_rent"),
        answer("I have suggested moving it to Workspace rent. Tap Confirm to change it."),
    )

    reply = asking.ask(ME, "That KPLC payment was rent, can you fix it?")

    [action] = reply.actions
    assert action.summary.startswith("Move Ksh 2,500.00 to KPLC PREPAID")
    assert store.transactions[entry.id].lines[0].category == "business_other"
    view = asking.thread(ME, reply.thread_id)
    assert view.actions == [action]
    assert view.messages[-1].run_id == action.run_id
