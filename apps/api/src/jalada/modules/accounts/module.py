"""What the accounts module adds to the app."""

from fastapi import APIRouter

from jalada.modules.accounts.api.routes import account, auth, google, model_consent

ROUTERS: list[APIRouter] = [auth.router, google.router, account.router, model_consent.router]
