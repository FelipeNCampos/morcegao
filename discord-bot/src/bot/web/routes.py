"""Rotas FastAPI para notificações EventSub da Twitch."""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse

from bot.config import Settings
from bot.models import TwitchOnlineEvent
from bot.storage import NotificationStore

if TYPE_CHECKING:
    from bot.client import DiscordBot

logger = logging.getLogger(__name__)

MAX_TWITCH_MESSAGE_AGE = timedelta(minutes=10)


def verify_twitch_signature(
    *,
    secret: str,
    message_id: str,
    timestamp: str,
    raw_body: bytes,
    signature: str,
) -> bool:
    """Valida a assinatura EventSub usando HMAC-SHA256 e comparação segura."""
    message = message_id.encode() + timestamp.encode() + raw_body
    expected_signature = "sha256=" + hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def is_twitch_timestamp_fresh(timestamp: str, *, now: datetime | None = None) -> bool:
    """Rejeita mensagens EventSub com mais de dez minutos."""
    try:
        message_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if message_time.tzinfo is None:
        return False

    current_time = now or datetime.now(UTC)
    age = current_time.astimezone(UTC) - message_time.astimezone(UTC)
    return -timedelta(minutes=1) <= age <= MAX_TWITCH_MESSAGE_AGE


def create_twitch_router(
    settings: Settings, store: NotificationStore, bot: DiscordBot
) -> APIRouter:
    """Monta a rota de webhook usando as dependências da única instância do bot."""
    router = APIRouter()

    @router.post("/webhooks/twitch")
    async def receive_twitch_webhook(request: Request) -> Response:
        raw_body = await request.body()
        message_id = request.headers.get("Twitch-Eventsub-Message-Id")
        timestamp = request.headers.get("Twitch-Eventsub-Message-Timestamp")
        signature = request.headers.get("Twitch-Eventsub-Message-Signature")
        message_type = request.headers.get("Twitch-Eventsub-Message-Type")

        if not all((message_id, timestamp, signature, message_type)):
            return Response(status_code=400)
        if not is_twitch_timestamp_fresh(timestamp):
            return Response(status_code=400)
        if not verify_twitch_signature(
            secret=settings.twitch.eventsub_secret,
            message_id=message_id,
            timestamp=timestamp,
            raw_body=raw_body,
            signature=signature,
        ):
            return Response(status_code=403)

        try:
            payload = await request.json()
        except ValueError:
            return Response(status_code=400)
        if not isinstance(payload, dict):
            return Response(status_code=400)

        if message_type == "webhook_callback_verification":
            challenge = payload.get("challenge")
            if not isinstance(challenge, str):
                return Response(status_code=400)
            return PlainTextResponse(challenge)

        if message_type != "notification":
            logger.info("Mensagem EventSub da Twitch ignorada: tipo não utilizado.")
            return Response(status_code=204)

        subscription = payload.get("subscription")
        event = payload.get("event")
        if not isinstance(subscription, dict) or not isinstance(event, dict):
            return Response(status_code=400)
        if subscription.get("type") != "stream.online":
            logger.info("Evento EventSub da Twitch ignorado: não é stream.online.")
            return Response(status_code=204)

        twitch_event = _parse_twitch_online_event(message_id, event)
        if twitch_event is None:
            return Response(status_code=400)

        is_new = await store.register_twitch_event(twitch_event)
        if not is_new:
            return Response(status_code=204)

        bot.queue_twitch_notification(twitch_event)
        return Response(status_code=204)

    return router


def _parse_twitch_online_event(
    message_id: str, payload: dict[str, Any]
) -> TwitchOnlineEvent | None:
    """Converte um payload EventSub mínimo, tolerando campos opcionais."""
    broadcaster_user_id = payload.get("broadcaster_user_id")
    broadcaster_login = payload.get("broadcaster_user_login")
    if not isinstance(broadcaster_user_id, str) or not isinstance(broadcaster_login, str):
        return None

    started_at = _parse_optional_timestamp(payload.get("started_at"))
    broadcaster_name = payload.get("broadcaster_user_name")
    return TwitchOnlineEvent(
        message_id=message_id,
        event_type="stream.online",
        broadcaster_user_id=broadcaster_user_id,
        broadcaster_login=broadcaster_login,
        broadcaster_name=broadcaster_name if isinstance(broadcaster_name, str) else None,
        started_at=started_at,
        received_at=datetime.now(UTC),
    )


def _parse_optional_timestamp(value: object) -> datetime | None:
    """Converte timestamps opcionais sem rejeitar um evento válido por esse campo."""
    if not isinstance(value, str):
        return None
    try:
        parsed_timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        parsed_timestamp.replace(tzinfo=UTC)
        if parsed_timestamp.tzinfo is None
        else parsed_timestamp
    )


# Futuras rotas /webhooks/instagram poderão validar o desafio e a assinatura da Meta.
# Elas devem processar somente eventos oficialmente suportados, como comentários ou menções.
