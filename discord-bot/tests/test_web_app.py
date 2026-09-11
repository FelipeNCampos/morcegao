"""Testes da fábrica FastAPI e do seu lifespan sem iniciar Discord real."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from bot.config import Settings
from bot.web.app import create_web_app


class FakeBot:
    """Representa a única instância compartilhada recebida pela fábrica web."""

    def queue_twitch_notification(self, _: object) -> None:
        """Atende ao contrato da rota sem criar um cliente Discord."""


class TrackingStore:
    """Registra a inicialização do armazenamento pelo lifespan da aplicação."""

    def __init__(self) -> None:
        self.initialize_calls = 0
        self.close_calls = 0

    async def initialize(self) -> None:
        self.initialize_calls += 1

    async def close(self) -> None:
        self.close_calls += 1


@pytest.mark.asyncio
async def test_web_app_exposes_health_and_initializes_shared_store(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A fábrica não instancia Discord e usa o store recebido durante o lifespan."""
    store = TrackingStore()
    bot = FakeBot()
    app = create_web_app(Settings.from_environment(environment()), store, bot)  # type: ignore[arg-type]

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as http_client:
            response = await http_client.get("/health")
            twitch_response = await http_client.post("/webhooks/twitch")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert store.initialize_calls == 1
    assert store.close_calls == 1
    assert twitch_response.status_code == 400


@pytest.mark.asyncio
async def test_web_app_omits_twitch_router_when_integration_is_disabled(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A API de saúde continua disponível sem expor rota Twitch quando ela está desativada."""
    values = environment()
    values["TWITCH_ENABLED"] = "false"
    store = TrackingStore()

    app = create_web_app(Settings.from_environment(values), store, FakeBot())  # type: ignore[arg-type]

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as http_client:
        assert (await http_client.get("/health")).status_code == 200
        assert (await http_client.post("/webhooks/twitch")).status_code == 404
