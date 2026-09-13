"""Modelos tipados trocados entre integrações, armazenamento e tarefas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

TOKEN_REFRESH_SAFETY_MARGIN = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class TwitchToken:
    """App Access Token Twitch mantido exclusivamente na memória do processo."""

    access_token: str
    expires_at: datetime

    def expires_soon(self, *, now: datetime | None = None) -> bool:
        """Informa se o token deve ser renovado antes de uma nova chamada à API."""
        current_time = now or datetime.now(UTC)
        return self.expires_at <= current_time + TOKEN_REFRESH_SAFETY_MARGIN


@dataclass(frozen=True, slots=True)
class TwitchOnlineEvent:
    """Evento ``stream.online`` recebido pelo webhook EventSub."""

    message_id: str
    event_type: str
    broadcaster_user_id: str
    broadcaster_login: str
    broadcaster_name: str | None
    started_at: datetime | None
    received_at: datetime


@dataclass(frozen=True, slots=True)
class TwitchStream:
    """Dados de uma live consultada após a notificação EventSub."""

    title: str | None
    url: str
    is_live: bool = True


@dataclass(frozen=True, slots=True)
class InstagramProfile:
    """Perfil profissional autorizado consultado na API oficial."""

    user_id: str
    username: str


@dataclass(frozen=True, slots=True)
class InstagramTokenData:
    """Token Instagram e metadados mantidos em um armazenamento configurado."""

    access_token: str
    token_type: str | None
    expires_at: datetime
    updated_at: datetime
    user_id: str | None = None
    username: str | None = None


@dataclass(frozen=True, slots=True)
class InstagramTokenRefreshResult:
    """Resultado seguro de uma renovação bem-sucedida de token Instagram."""

    access_token: str
    token_type: str | None
    expires_in: int
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class InstagramMedia:
    """Representa uma mídia retornada pela API Graph do Instagram."""

    media_id: str
    username: str | None
    caption: str | None
    media_type: str | None
    media_url: str | None
    thumbnail_url: str | None
    permalink: str | None
    timestamp: datetime
    media_product_type: str | None = None
