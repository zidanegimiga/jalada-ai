"""What the telegram module adds to the app."""

from fastapi import APIRouter

from jalada.modules.telegram.api.routes import telegram

ROUTERS: list[APIRouter] = [telegram.router]
