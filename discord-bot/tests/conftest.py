"""Fixtures compartilhadas, sem credenciais reais."""

from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def environment() -> Callable[[], dict[str, str]]:
    """Fornece o mínimo de configuração válida para os testes."""

    def build() -> dict[str, str]:
        return {
            "DISCORD_TOKEN": "test-discord-token",
            "DISCORD_APPLICATION_ID": "123456789012345678",
            "DISCORD_GUILD_ID": "987654321098765432",
            "TWITCH_ENABLED": "true",
            "TWITCH_CLIENT_ID": "test-client-id",
            "TWITCH_CLIENT_SECRET": "test-client-secret",
            "TWITCH_BROADCASTER_LOGIN": "canal_teste",
            "TWITCH_EVENTSUB_SECRET": "test-eventsub-secret",
            "TWITCH_CALLBACK_URL": "https://example.test/webhooks/twitch",
            "DISCORD_NOTIFICATION_CHANNEL_ID": "123456789012345678",
            "INSTAGRAM_API_VERSION": "v22.0",
            "INSTAGRAM_POLL_INTERVAL_SECONDS": "300",
            "INSTAGRAM_ENABLED": "false",
            "INSTAGRAM_NOTIFY_EXISTING_LATEST": "false",
        }

    return build
