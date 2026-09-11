"""Testes unitários do OAuth de App Access Token Twitch, sem rede externa."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from bot.config import Settings
from bot.integrations.twitch_auth import (
    TwitchAuthClient,
    TwitchInvalidClientError,
)


@pytest.mark.asyncio
async def test_requests_token_with_expiration_in_memory(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O token recebido inclui vencimento calculado e não depende de variável legada."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/oauth2/token"
        assert b"grant_type=client_credentials" in request.content
        return httpx.Response(200, json={"access_token": "memory-only-token", "expires_in": 120})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        auth = TwitchAuthClient(
            Settings.from_environment(environment()).twitch,
            http_client=http_client,
            now=lambda: now,
        )
        token = await auth.request_app_access_token()

    assert token.access_token == "memory-only-token"
    assert token.expires_at == now + timedelta(seconds=120)
    assert token.expires_soon(now=now) is False
    assert token.expires_soon(now=now + timedelta(seconds=61)) is True


@pytest.mark.asyncio
async def test_retries_transient_token_endpoint_failure(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Falha HTTP 5xx é repetida de forma limitada antes de aceitar a resposta válida."""
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"access_token": "recovered-token", "expires_in": 3600})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        auth = TwitchAuthClient(
            Settings.from_environment(environment()).twitch, http_client=http_client
        )
        token = await auth.request_app_access_token()

    assert token.access_token == "recovered-token"
    assert calls == 2


@pytest.mark.asyncio
async def test_validate_token_returns_false_for_unauthorized(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O endpoint OAuth de validação sinaliza token inválido sem expor seu valor."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/oauth2/validate"
        return httpx.Response(401)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        auth = TwitchAuthClient(
            Settings.from_environment(environment()).twitch, http_client=http_client
        )
        assert await auth.validate_token("invalid-token") is False


@pytest.mark.asyncio
async def test_invalid_client_error_does_not_include_client_secret(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Credenciais recusadas geram erro claro sem revelar o segredo configurado."""
    values = environment()
    secret_marker = "super-secret-test-value"
    values["TWITCH_CLIENT_SECRET"] = secret_marker

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(401))
    ) as http_client:
        auth = TwitchAuthClient(Settings.from_environment(values).twitch, http_client=http_client)
        with pytest.raises(TwitchInvalidClientError) as error:
            await auth.request_app_access_token()

    assert secret_marker not in str(error.value)
