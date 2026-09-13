"""Rotas HTTP do Instagram Login, isoladas do webhook da Twitch."""

from __future__ import annotations

import logging
from typing import Protocol

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import Response

from bot.integrations.instagram_oauth import InstagramOAuthError, InstagramOAuthStateStore

logger = logging.getLogger(__name__)


class InstagramOAuthService(Protocol):
    """Parte do cliente OAuth usada pela camada HTTP."""

    def authorization_url(self, state: str) -> str:
        """Monta a URL de consentimento do Instagram."""

    async def authorize(self, code: str) -> object:
        """Troca o código por uma autorização persistida."""


def create_instagram_oauth_router(service: InstagramOAuthService | None) -> APIRouter:
    """Monta endpoints OAuth sem expor segredos nem detalhes da resposta Meta."""
    router = APIRouter()
    state_store = InstagramOAuthStateStore()

    @router.get("/instagram/oauth/start")
    async def start_instagram_oauth() -> Response:
        if service is None:
            return HTMLResponse("<h1>Instagram authorization unavailable</h1>", status_code=503)
        state = state_store.issue()
        return RedirectResponse(service.authorization_url(state), status_code=302)

    @router.get("/instagram/oauth/callback")
    async def instagram_oauth_callback(
        state: str | None = Query(default=None),
        code: str | None = Query(default=None),
        error: str | None = Query(default=None),
    ) -> HTMLResponse:
        if service is None:
            return HTMLResponse("<h1>Instagram authorization unavailable</h1>", status_code=503)
        if state is None or not state_store.consume(state):
            return HTMLResponse(
                "<h1>Invalid or expired authorization request</h1>", status_code=400
            )
        if error is not None or code is None:
            logger.warning("A autorização Instagram foi recusada pelo usuário ou pela Meta.")
            return HTMLResponse(
                "<h1>Instagram authorization was not completed</h1>", status_code=400
            )
        try:
            await service.authorize(code)
        except InstagramOAuthError:
            logger.warning("A autorização Instagram não pôde ser concluída.")
            return HTMLResponse("<h1>Instagram authorization failed</h1>", status_code=400)
        except Exception:
            logger.exception("Falha inesperada ao concluir autorização Instagram.")
            return HTMLResponse("<h1>Instagram authorization failed</h1>", status_code=500)
        return HTMLResponse(
            "<h1>Instagram authorization complete</h1>"
            "<p>You may close this window and restart the bot polling service.</p>"
        )

    return router
