"""What the ledger module adds to the app."""

from fastapi import APIRouter

from jalada.modules.ledger.api.routes import certificates, ledger, receipts, review, suggestions

ROUTERS: list[APIRouter] = [
    review.router,
    suggestions.router,
    receipts.router,
    ledger.router,
    certificates.router,
]
