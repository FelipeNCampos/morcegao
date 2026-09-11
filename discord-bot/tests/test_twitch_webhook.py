"""Testes isolados do webhook EventSub, sem chamadas externas."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from bot.config import Settings
from bot.models import TwitchOnlineEvent
from bot.storage import NotificationStore
from bot.web.routes import create_twitch_router, verify_twitch_signature


class FakeBot:
    """Recebe eventos enfileirados sem iniciar um cliente Discord."""

    def __init__(self) -> None:
        self.events: list[TwitchOnlineEvent] = []

    def queue_twitch_notification(self, event: TwitchOnlineEvent) -> None:
        self.events.append(event)


def signed_headers(
    secret: str, body: bytes, *, timestamp: str, message_type: str
) -> dict[str, str]:
    """Monta os cabeçalhos EventSub assinados para um payload de teste."""
    message_id = "event-message-id"
    signature = (
        "sha256="
        + hmac.new(
            secret.encode(), message_id.encode() + timestamp.encode() + body, hashlib.sha256
        ).hexdigest()
    )
    return {
        "Content-Type": "application/json",
        "Twitch-Eventsub-Message-Id": message_id,
        "Twitch-Eventsub-Message-Timestamp": timestamp,
        "Twitch-Eventsub-Message-Signature": signature,
        "Twitch-Eventsub-Message-Type": message_type,
    }


async def post_webhook(
    app: FastAPI, payload: dict[str, object], headers: dict[str, str]
) -> httpx.Response:
    """Envia uma requisição ASGI local à rota Twitch."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://example.test"
    ) as http_client:
        return await http_client.post(
            "/webhooks/twitch", content=json.dumps(payload).encode(), headers=headers
        )


@pytest.mark.asyncio
async def test_answers_twitch_challenge(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """A verificação inicial responde o challenge somente após assinatura válida."""
    settings = Settings.from_environment(environment())
    store = NotificationStore(tmp_path / "notifications.sqlite3")
    await store.initialize()
    bot = FakeBot()
    app = FastAPI()
    app.include_router(create_twitch_router(settings, store, bot))  # type: ignore[arg-type]
    payload: dict[str, object] = {"challenge": "challenge-value"}
    body = json.dumps(payload).encode()
    headers = signed_headers(
        settings.twitch.eventsub_secret,
        body,
        timestamp=datetime.now(UTC).isoformat(),
        message_type="webhook_callback_verification",
    )

    response = await post_webhook(app, payload, headers)

    assert response.status_code == 200
    assert response.text == "challenge-value"


def test_signature_validation_rejects_invalid_value() -> None:
    """A assinatura HMAC deve falhar quando o valor recebido não confere."""
    assert not verify_twitch_signature(
        secret="test-eventsub-secret",
        message_id="message-id",
        timestamp="2026-09-11T12:00:00+00:00",
        raw_body=b"{}",
        signature="sha256=invalid",
    )


@pytest.mark.asyncio
async def test_rejects_old_timestamp(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """Mensagens antigas são recusadas antes de qualquer processamento."""
    settings = Settings.from_environment(environment())
    store = NotificationStore(tmp_path / "notifications.sqlite3")
    await store.initialize()
    bot = FakeBot()
    app = FastAPI()
    app.include_router(create_twitch_router(settings, store, bot))  # type: ignore[arg-type]
    payload: dict[str, object] = {"challenge": "challenge-value"}
    body = json.dumps(payload).encode()
    headers = signed_headers(
        settings.twitch.eventsub_secret,
        body,
        timestamp=(datetime.now(UTC) - timedelta(minutes=11)).isoformat(),
        message_type="webhook_callback_verification",
    )

    assert (await post_webhook(app, payload, headers)).status_code == 400


@pytest.mark.asyncio
async def test_ignores_other_event_types_and_deduplicates_online_events(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """Apenas stream.online novo entra na fila de entrega Discord."""
    settings = Settings.from_environment(environment())
    store = NotificationStore(tmp_path / "notifications.sqlite3")
    await store.initialize()
    bot = FakeBot()
    app = FastAPI()
    app.include_router(create_twitch_router(settings, store, bot))  # type: ignore[arg-type]
    timestamp = datetime.now(UTC).isoformat()
    ignored_payload: dict[str, object] = {
        "subscription": {"type": "channel.follow"},
        "event": {},
    }
    ignored_body = json.dumps(ignored_payload).encode()
    ignored_headers = signed_headers(
        settings.twitch.eventsub_secret,
        ignored_body,
        timestamp=timestamp,
        message_type="notification",
    )
    assert (await post_webhook(app, ignored_payload, ignored_headers)).status_code == 204

    online_payload: dict[str, object] = {
        "subscription": {"type": "stream.online"},
        "event": {
            "broadcaster_user_id": "42",
            "broadcaster_user_login": "canal_teste",
            "broadcaster_user_name": "Canal Teste",
            "started_at": timestamp,
        },
    }
    body = json.dumps(online_payload).encode()
    headers = signed_headers(
        settings.twitch.eventsub_secret, body, timestamp=timestamp, message_type="notification"
    )

    assert (await post_webhook(app, online_payload, headers)).status_code == 204
    assert (await post_webhook(app, online_payload, headers)).status_code == 204
    assert len(bot.events) == 1
