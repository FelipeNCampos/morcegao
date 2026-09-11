"""Testes do envio de embeds Discord sem conexão externa."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from bot.config import Settings
from bot.integrations.discord_sender import DiscordNotificationError, DiscordNotificationSender
from bot.models import InstagramMedia


class FakeChannel:
    """Canal que registra mensagens enviadas em memória."""

    def __init__(self) -> None:
        self.messages: list[dict[str, object]] = []

    async def send(self, **kwargs: object) -> None:
        self.messages.append(kwargs)


class FakeDiscordClient:
    """Cliente mínimo para testar busca de canal."""

    def __init__(self, channel: FakeChannel | None) -> None:
        self._channel = channel

    def get_channel(self, _: int) -> FakeChannel | None:
        return self._channel

    async def fetch_channel(self, _: int) -> object:
        return self._channel or object()


def instagram_environment(environment: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Retorna configuração Instagram habilitada para o remetente."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "perfil_autorizado",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
        }
    )
    return values


@pytest.mark.asyncio
async def test_sends_instagram_embed(environment: Callable[[], dict[str, str]]) -> None:
    """Uma publicação cria conteúdo e embed com perfil e permalink."""
    channel = FakeChannel()
    sender = DiscordNotificationSender(  # type: ignore[arg-type]
        FakeDiscordClient(channel), Settings.from_environment(instagram_environment(environment))
    )
    media = InstagramMedia(
        media_id="media-1",
        username="perfil_autorizado",
        caption="Legenda de teste",
        media_type="IMAGE",
        media_url="https://cdn.example.test/image.jpg",
        thumbnail_url=None,
        permalink="https://www.instagram.com/p/example/",
        timestamp=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    await sender.send_instagram_notification(media)

    assert len(channel.messages) == 1
    assert "@perfil_autorizado" in str(channel.messages[0]["content"])
    assert channel.messages[0]["embed"].url == media.permalink  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_rejects_missing_discord_channel(environment: Callable[[], dict[str, str]]) -> None:
    """Um ID que não resolve para canal de mensagens não é aceito."""
    sender = DiscordNotificationSender(  # type: ignore[arg-type]
        FakeDiscordClient(None), Settings.from_environment(instagram_environment(environment))
    )
    media = InstagramMedia(
        media_id="media-1",
        username=None,
        caption=None,
        media_type=None,
        media_url=None,
        thumbnail_url=None,
        permalink="https://www.instagram.com/p/example/",
        timestamp=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )

    with pytest.raises(DiscordNotificationError, match="canal"):
        await sender.send_instagram_notification(media)
