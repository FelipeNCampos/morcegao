"""Fábrica da aplicação FastAPI usada pelo webhook da Twitch."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from bot.config import Settings
from bot.storage import NotificationStore
from bot.web.routes import create_twitch_router

if TYPE_CHECKING:
    from bot.client import DiscordBot


def create_web_app(settings: Settings, store: NotificationStore, bot: DiscordBot) -> FastAPI:
    """Cria o servidor HTTP sem instanciar um segundo cliente Discord."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await store.initialize()
        try:
            yield
        finally:
            close = getattr(store, "close", None)
            if close is not None:
                await close()

    app = FastAPI(title="Discord Bot Webhooks", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Confirma que o processo web está disponível sem revelar configurações."""
        return {"status": "ok"}

    if settings.twitch.enabled:
        app.include_router(create_twitch_router(settings, store, bot))
    return app
