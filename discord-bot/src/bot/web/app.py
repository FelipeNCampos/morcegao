"""Fábrica da aplicação FastAPI usada pelo webhook da Twitch."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from bot.config import Settings
from bot.integrations.instagram_oauth import InstagramOAuthClient
from bot.integrations.instagram_token_store import InstagramTokenStore
from bot.storage import NotificationStore
from bot.web.instagram_oauth import InstagramOAuthService, create_instagram_oauth_router
from bot.web.routes import create_twitch_router

if TYPE_CHECKING:
    from bot.client import DiscordBot


def create_web_app(
    settings: Settings,
    store: NotificationStore,
    bot: DiscordBot,
    *,
    instagram_token_store: InstagramTokenStore | None = None,
    instagram_oauth_service: InstagramOAuthService | None = None,
) -> FastAPI:
    """Cria o servidor HTTP sem instanciar um segundo cliente Discord."""
    oauth_service = instagram_oauth_service
    if (
        oauth_service is None
        and settings.instagram.oauth_is_configured
        and instagram_token_store is not None
    ):
        oauth_service = InstagramOAuthClient(settings.instagram, instagram_token_store)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await store.initialize()
        try:
            yield
        finally:
            close_oauth = getattr(oauth_service, "aclose", None)
            if close_oauth is not None:
                await close_oauth()
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
    if settings.instagram.enabled:
        app.include_router(create_instagram_oauth_router(oauth_service))
    return app
