"""Testes sem rede para Helix e EventSub com token Twitch renovável."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from bot.config import Settings
from bot.integrations.twitch import TwitchClient


def oauth_token_response(token: str = "test-access-token") -> httpx.Response:
    """Retorna uma resposta OAuth curta e válida para os transportes simulados."""
    return httpx.Response(200, json={"access_token": token, "expires_in": 3600})


@pytest.mark.asyncio
async def test_resolves_broadcaster_id_from_login(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O ID do perfil é buscado uma vez quando não foi informado no ambiente."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "id.twitch.tv":
            return oauth_token_response()
        requests.append(request)
        assert request.url.path == "/helix/users"
        assert request.url.params["login"] == "canal_teste"
        return httpx.Response(
            200,
            json={"data": [{"id": "42", "login": "canal_teste", "display_name": "Canal Teste"}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = TwitchClient(
            Settings.from_environment(environment()).twitch, http_client=http_client
        )
        assert await client.resolve_broadcaster_user_id() == "42"
        assert await client.resolve_broadcaster_user_id() == "42"

    assert len(requests) == 1


def test_builds_stream_online_eventsub_payload(environment: Callable[[], dict[str, str]]) -> None:
    """O payload usa stream.online v1, webhook, callback e segredo configurados."""
    client = TwitchClient(Settings.from_environment(environment()).twitch)

    payload = client.build_stream_online_subscription_payload("42")

    assert payload["type"] == "stream.online"
    assert payload["version"] == "1"
    assert payload["condition"] == {"broadcaster_user_id": "42"}
    assert payload["transport"]["method"] == "webhook"
    assert payload["transport"]["callback"] == "https://example.test/webhooks/twitch"


@pytest.mark.asyncio
async def test_does_not_create_duplicate_eventsub_subscription(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Uma inscrição existente para o mesmo perfil e callback impede novo POST."""
    values = environment()
    values["TWITCH_BROADCASTER_USER_ID"] = "42"
    post_attempted = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal post_attempted
        if request.url.host == "id.twitch.tv":
            return oauth_token_response()
        if request.method == "POST":
            post_attempted = True
        assert request.method == "GET"
        assert request.url.path == "/helix/eventsub/subscriptions"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "type": "stream.online",
                        "version": "1",
                        "condition": {"broadcaster_user_id": "42"},
                        "transport": {
                            "method": "webhook",
                            "callback": "https://example.test/webhooks/twitch",
                        },
                    }
                ],
                "pagination": {},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = TwitchClient(Settings.from_environment(values).twitch, http_client=http_client)
        assert await client.ensure_stream_online_subscription() is False

    assert post_attempted is False


@pytest.mark.asyncio
async def test_retries_a_get_once_after_unauthorized_token(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Uma chamada GET recebe um token novo e é repetida uma única vez após HTTP 401."""
    issued_tokens = iter(("first-token", "second-token"))
    stream_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "id.twitch.tv":
            return oauth_token_response(next(issued_tokens))
        stream_requests.append(request)
        if len(stream_requests) == 1:
            return httpx.Response(401)
        return httpx.Response(
            200,
            json={"data": [{"user_login": "canal_teste", "title": "Live de teste"}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = TwitchClient(
            Settings.from_environment(environment()).twitch, http_client=http_client
        )
        stream = await client.get_stream("42")

    assert stream.title == "Live de teste"
    assert len(stream_requests) == 2
    assert stream_requests[0].headers["Authorization"] == "Bearer first-token"
    assert stream_requests[1].headers["Authorization"] == "Bearer second-token"


@pytest.mark.asyncio
async def test_reports_stream_as_offline_when_twitch_returns_no_active_stream(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A ausência de dados de stream permite limpar a live atual sem notificar novamente."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "id.twitch.tv":
            return oauth_token_response()
        return httpx.Response(200, json={"data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = TwitchClient(
            Settings.from_environment(environment()).twitch,
            http_client=http_client,
        )
        stream = await client.get_stream("42")

    assert stream.is_live is False


@pytest.mark.asyncio
async def test_rechecks_eventsub_before_retrying_post_after_unauthorized(
    environment: Callable[[], dict[str, str]],
) -> None:
    """EventSub consulta inscrições depois de 401 para não criar uma duplicata."""
    values = environment()
    values["TWITCH_BROADCASTER_USER_ID"] = "42"
    issued_tokens = iter(("first-token", "second-token"))
    subscription_get_count = 0
    subscription_post_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal subscription_get_count, subscription_post_count
        if request.url.host == "id.twitch.tv":
            return oauth_token_response(next(issued_tokens))
        if request.method == "POST":
            subscription_post_count += 1
            return httpx.Response(401)

        subscription_get_count += 1
        if subscription_get_count == 1:
            return httpx.Response(200, json={"data": [], "pagination": {}})
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "type": "stream.online",
                        "version": "1",
                        "condition": {"broadcaster_user_id": "42"},
                        "transport": {
                            "method": "webhook",
                            "callback": "https://example.test/webhooks/twitch",
                        },
                    }
                ],
                "pagination": {},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = TwitchClient(Settings.from_environment(values).twitch, http_client=http_client)
        assert await client.ensure_stream_online_subscription() is False

    assert subscription_post_count == 1
    assert subscription_get_count == 2
