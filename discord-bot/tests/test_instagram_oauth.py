"""Testes do Instagram Login sem chamadas à Meta, Discord ou rede real."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from bot.config import Settings
from bot.integrations.instagram_oauth import InstagramOAuthClient, InstagramOAuthError
from bot.models import InstagramTokenData
from bot.web.app import create_web_app


class MemoryTokenStore:
    """Armazena apenas dados de teste para verificar a persistência do callback."""

    def __init__(self) -> None:
        self.token: InstagramTokenData | None = None

    async def get_token(self) -> InstagramTokenData | None:
        return self.token

    async def save_token(self, token: InstagramTokenData) -> None:
        self.token = token


class TrackingStore:
    """Implementa o contrato mínimo do armazenamento compartilhado do FastAPI."""

    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None


class FakeBot:
    """Evita criar um segundo cliente Discord ao construir o app HTTP."""

    def queue_twitch_notification(self, _: object) -> None:
        return None


class FakeOAuthService:
    """Representa a Meta para testar state e respostas HTTP da aplicação."""

    def __init__(self) -> None:
        self.codes: list[str] = []

    def authorization_url(self, state: str) -> str:
        return f"https://instagram.example/authorize?state={state}"

    async def authorize(self, code: str) -> object:
        self.codes.append(code)
        return object()


def oauth_environment(environment: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Habilita somente a configuração pública necessária para o OAuth de teste."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "nosferarityy",
            "INSTAGRAM_APP_ID": "123456789012345",
            "INSTAGRAM_APP_SECRET": "test-app-secret",
            "INSTAGRAM_REDIRECT_URI": "https://example.test/instagram/oauth/callback",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "1547927129210228767",
        }
    )
    return values


@pytest.mark.asyncio
async def test_oauth_authorizes_expected_account_and_persists_complete_token(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O callback troca code, valida username e salva os dados sem revelar token."""
    settings = Settings.from_environment(oauth_environment(environment)).instagram
    token_store = MemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.instagram.com":
            assert request.method == "POST"
            assert b"code=temporary-code" in request.content
            return httpx.Response(200, json={"access_token": "short", "user_id": "1784"})
        if request.url.path == "/access_token":
            assert request.url.params["grant_type"] == "ig_exchange_token"
            return httpx.Response(
                200,
                json={"access_token": "long-lived", "token_type": "bearer", "expires_in": 3600},
            )
        assert request.url.path == "/v22.0/1784"
        return httpx.Response(200, json={"id": "1784", "username": "nosferarityy"})

    now = datetime(2026, 9, 12, 12, tzinfo=UTC)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InstagramOAuthClient(
            settings,
            token_store,  # type: ignore[arg-type]
            http_client=http_client,
            now=lambda: now,
        )
        result = await client.authorize("temporary-code")

    assert result.user_id == "1784"
    assert result.username == "nosferarityy"
    assert result.expires_at.isoformat() == "2026-09-12T13:00:00+00:00"
    assert token_store.token == result


@pytest.mark.asyncio
async def test_oauth_rejects_an_account_other_than_the_configured_profile(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Uma autorização de outro perfil não sobrescreve o armazenamento atual."""
    settings = Settings.from_environment(oauth_environment(environment)).instagram
    token_store = MemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.instagram.com":
            return httpx.Response(200, json={"access_token": "short", "user_id": "1784"})
        if request.url.path == "/access_token":
            return httpx.Response(200, json={"access_token": "long", "expires_in": 3600})
        return httpx.Response(200, json={"id": "1784", "username": "other_profile"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InstagramOAuthClient(settings, token_store, http_client=http_client)  # type: ignore[arg-type]
        with pytest.raises(InstagramOAuthError, match="não corresponde"):
            await client.authorize("temporary-code")

    assert token_store.token is None


@pytest.mark.asyncio
async def test_oauth_routes_require_one_time_state_and_hide_meta_error_details(
    environment: Callable[[], dict[str, str]],
) -> None:
    """State inválido, replay e erro da Meta não liberam detalhes ao navegador."""
    values = oauth_environment(environment)
    service = FakeOAuthService()
    app = create_web_app(
        Settings.from_environment(values),
        TrackingStore(),  # type: ignore[arg-type]
        FakeBot(),  # type: ignore[arg-type]
        instagram_oauth_service=service,
    )

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://example.test"
        ) as http_client:
            start = await http_client.get("/instagram/oauth/start", follow_redirects=False)
            state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
            invalid = await http_client.get("/instagram/oauth/callback?state=invalid&code=abc")
            meta_error = await http_client.get(
                f"/instagram/oauth/callback?state={state}&error=access_denied&"
                "error_description=secret-value"
            )
            replay = await http_client.get(f"/instagram/oauth/callback?state={state}&code=abc")

    assert start.status_code == 302
    assert invalid.status_code == 400
    assert meta_error.status_code == 400
    assert "secret-value" not in meta_error.text
    assert replay.status_code == 400
    assert service.codes == []


@pytest.mark.asyncio
async def test_oauth_callback_consumes_state_after_success(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Um callback válido é aceito uma vez e sua repetição é bloqueada."""
    service = FakeOAuthService()
    app = create_web_app(
        Settings.from_environment(oauth_environment(environment)),
        TrackingStore(),  # type: ignore[arg-type]
        FakeBot(),  # type: ignore[arg-type]
        instagram_oauth_service=service,
    )

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://example.test"
        ) as http_client:
            start = await http_client.get("/instagram/oauth/start", follow_redirects=False)
            state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
            callback = await http_client.get(f"/instagram/oauth/callback?state={state}&code=abc")
            replay = await http_client.get(f"/instagram/oauth/callback?state={state}&code=abc")

    assert callback.status_code == 200
    assert replay.status_code == 400
    assert service.codes == ["abc"]
