"""Testes do comando público /chamar."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import discord

from bot.cogs.general import CALL_NOT_CONFIGURED_MESSAGE, General


class FakeResponse:
    """Registra respostas iniciais da interação."""

    def __init__(self) -> None:
        self.deferred: list[bool] = []
        self.messages: list[tuple[str, bool]] = []

    async def defer(self, *, ephemeral: bool) -> None:
        self.deferred.append(ephemeral)

    async def send_message(self, content: str, *, ephemeral: bool) -> None:
        self.messages.append((content, ephemeral))


class FakeFollowup:
    """Registra respostas posteriores ao defer."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    async def send(self, content: str, *, ephemeral: bool) -> None:
        self.messages.append((content, ephemeral))


class FakeModerator:
    """Destinatário da DM sem conexão com a API Discord."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, discord.AllowedMentions]] = []

    async def send(self, content: str, *, allowed_mentions: discord.AllowedMentions) -> None:
        self.messages.append((content, allowed_mentions))


class FakeDiscordClient:
    """Cliente com o moderador disponível somente por fetch."""

    def __init__(self, moderator: FakeModerator) -> None:
        self.moderator = moderator
        self.requested_ids: list[int] = []

    def get_user(self, user_id: int) -> None:
        return None

    async def fetch_user(self, user_id: int) -> FakeModerator:
        self.requested_ids.append(user_id)
        return self.moderator


class FakeInteraction:
    """Interação que representa o membro que executou o comando."""

    def __init__(self) -> None:
        self.user = SimpleNamespace(id=456, display_name="Pessoa chamando", name="pessoa")
        self.response = FakeResponse()
        self.followup = FakeFollowup()


def test_call_moderator_sends_dm_to_fixed_configured_user() -> None:
    moderator = FakeModerator()
    client = FakeDiscordClient(moderator)
    cog = General(
        object(),
        call_moderator_user_id=123,
        discord_client=client,  # type: ignore[arg-type]
    )
    interaction = FakeInteraction()

    asyncio.run(General.call_moderator.callback(cog, interaction))  # type: ignore[arg-type]

    assert client.requested_ids == [123]
    assert (
        moderator.messages[0][0] == "📣 Pessoa chamando pediu a atenção de um moderador. (ID: 456)"
    )
    assert moderator.messages[0][1].everyone is False
    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [("O moderador foi avisado.", True)]


def test_call_moderator_is_disabled_without_a_configured_user() -> None:
    cog = General(object())
    interaction = FakeInteraction()

    asyncio.run(General.call_moderator.callback(cog, interaction))  # type: ignore[arg-type]

    assert interaction.response.messages == [(CALL_NOT_CONFIGURED_MESSAGE, True)]


def test_user_id_command_returns_the_selected_user_id() -> None:
    cog = General(object())
    interaction = FakeInteraction()
    user = SimpleNamespace(id=789, display_name="Usuário selecionado")

    asyncio.run(General.user_id_command.callback(cog, interaction, user))  # type: ignore[arg-type]

    assert interaction.response.messages == [("ID de Usuário selecionado: `789`", True)]
