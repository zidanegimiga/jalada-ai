"""What the ledger module adds to the app."""

from fastapi import APIRouter

from jalada.modules.ledger.api.routes import (
    certificates,
    changes,
    ledger,
    own_accounts,
    receipts,
    review,
    suggestions,
)

ROUTERS: list[APIRouter] = [
    review.router,
    suggestions.router,
    receipts.router,
    own_accounts.router,
    ledger.router,
    certificates.router,
    changes.router,
]
