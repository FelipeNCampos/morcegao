"""Testes dos logs de entrada e saída de membros."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import discord

from bot.cogs.member_activity_logs import MemberActivityLogs
from bot.config import Settings


class FakeChannel:
    """Canal mínimo que registra as mensagens enviadas pelo cog."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, discord.AllowedMentions]] = []

    async def send(self, content: str, *, allowed_mentions: discord.AllowedMentions) -> None:
        self.messages.append((content, allowed_mentions))


class FakeBot:
    """Cliente mínimo para isolar cache e busca de canais."""

    def __init__(self, channel: FakeChannel | None = None) -> None:
        self.channel = channel
        self.fetch_calls: list[int] = []

    def get_channel(self, channel_id: int) -> FakeChannel | None:
        return self.channel

    async def fetch_channel(self, channel_id: int) -> FakeChannel | None:
        self.fetch_calls.append(channel_id)
        return self.channel


def _settings(channel_id: int | None) -> Settings:
    return Settings.from_environment(
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_MEMBER_LOG_CHANNEL_ID": "" if channel_id is None else str(channel_id),
        }
    )


def test_member_join_log_uses_configured_channel() -> None:
    channel = FakeChannel()
    cog = MemberActivityLogs(FakeBot(channel), _settings(123))  # type: ignore[arg-type]
    member = SimpleNamespace(id=456, mention="<@456>")

    asyncio.run(cog.on_member_join(member))  # type: ignore[arg-type]

    assert channel.messages[0][0] == "📥 <@456> entrou no servidor. (ID: 456)"
    assert channel.messages[0][1].everyone is False


def test_member_remove_log_fetches_channel_when_cache_is_empty() -> None:
    channel = FakeChannel()
    bot = FakeBot(channel)
    bot.get_channel = lambda channel_id: None  # type: ignore[method-assign]
    cog = MemberActivityLogs(bot, _settings(123))  # type: ignore[arg-type]
    member = SimpleNamespace(id=456, mention="<@456>")

    asyncio.run(cog.on_member_remove(member))  # type: ignore[arg-type]

    assert bot.fetch_calls == [123]
    assert channel.messages[0][0] == "📤 <@456> saiu do servidor. (ID: 456)"


def test_member_logs_are_disabled_without_a_channel() -> None:
    channel = FakeChannel()
    cog = MemberActivityLogs(FakeBot(channel), _settings(None))  # type: ignore[arg-type]
    member = SimpleNamespace(id=456, mention="<@456>")

    asyncio.run(cog.on_member_join(member))  # type: ignore[arg-type]

    assert channel.messages == []
