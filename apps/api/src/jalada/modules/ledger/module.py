"""What the ledger module adds to the app."""

from fastapi import APIRouter

from jalada.modules.ledger.api.routes import certificates, ledger, review

ROUTERS: list[APIRouter] = [review.router, ledger.router, certificates.router]
