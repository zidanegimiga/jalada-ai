"""What the exports module adds to the app."""

from fastapi import APIRouter

from jalada.modules.exports.api.routes import exports

ROUTERS: list[APIRouter] = [exports.router]
