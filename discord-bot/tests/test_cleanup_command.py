"""Testes do comando slash /limpar sem acesso ao Discord."""

from __future__ import annotations

from types import SimpleNamespace

import discord
import pytest

from bot.cogs.general import (
    CLEANUP_HTTP_ERROR_MESSAGE,
    CLEANUP_NOT_FOUND_MESSAGE,
    General,
)
from bot.errors import MISSING_MANAGE_MESSAGES_PERMISSION_MESSAGE


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Cria uma falha Discord controlada sem uma requisição real."""
    response = SimpleNamespace(status=status, reason="Erro de teste", headers={})
    return error_type(response, "Erro de teste")


class FakeChannel:
    """Canal que registra o limite recebido por ``purge``."""

    def __init__(
        self,
        messages: list[object] | None = None,
        purge_error: discord.HTTPException | None = None,
    ) -> None:
        self.id = 1234
        self._messages = messages or []
        self._purge_error = purge_error
        self.purge_limits: list[int] = []

    async def purge(self, *, limit: int) -> list[object]:
        self.purge_limits.append(limit)
        if self._purge_error is not None:
            raise self._purge_error
        return self._messages


class FakeResponse:
    """Resposta de interação que registra defer e mensagens efêmeras."""

    def __init__(self) -> None:
        self.deferred: list[bool] = []
        self.messages: list[tuple[str, bool]] = []

    async def defer(self, *, ephemeral: bool) -> None:
        self.deferred.append(ephemeral)

    async def send_message(self, content: str, *, ephemeral: bool) -> None:
        self.messages.append((content, ephemeral))


class FakeFollowup:
    """Follow-up efêmero usado após a limpeza potencialmente demorada."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    async def send(self, content: str, *, ephemeral: bool) -> None:
        self.messages.append((content, ephemeral))


class FakeInteraction:
    """Interação de servidor com permissões e canal controláveis."""

    def __init__(self, channel: FakeChannel, *, manage_messages: bool = True) -> None:
        self.channel = channel
        self.channel_id = channel.id
        self.permissions = SimpleNamespace(manage_messages=manage_messages)
        self.user = SimpleNamespace(id=4321)
        self.response = FakeResponse()
        self.followup = FakeFollowup()


class FakeNotificationSender:
    """Dependência não usada pelo comando de limpeza."""


def cleanup_cog(*, maximum: int = 100) -> General:
    """Monta o cog com o limite configurável usado no teste."""
    return General(FakeNotificationSender(), max_messages_to_delete=maximum)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_cleanup_is_registered_as_a_slash_command_and_purges_requested_messages() -> None:
    """O /limpar apaga exatamente a quantidade solicitada e responde de modo efêmero."""
    channel = FakeChannel(messages=[object() for _ in range(10)])
    interaction = FakeInteraction(channel)
    cog = cleanup_cog()

    await General.limpar.callback(cog, interaction, 10)  # type: ignore[arg-type]

    assert "limpar" in [command.name for command in cog.get_app_commands()]
    assert "limpar" not in [command.name for command in cog.get_commands()]
    assert channel.purge_limits == [10]
    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [("🧹 10 mensagens foram apagadas.", True)]


@pytest.mark.asyncio
@pytest.mark.parametrize("quantity", [0, -1])
async def test_cleanup_rejects_non_positive_quantities(quantity: int) -> None:
    """Zero e valores negativos não chamam a API de exclusão."""
    channel = FakeChannel()
    interaction = FakeInteraction(channel)

    await General.limpar.callback(cleanup_cog(), interaction, quantity)  # type: ignore[arg-type]

    assert channel.purge_limits == []
    assert interaction.response.messages == [("Informe uma quantidade maior que zero.", True)]


@pytest.mark.asyncio
async def test_cleanup_rejects_quantity_above_configured_limit() -> None:
    """O limite configurado bloqueia a operação antes de qualquer exclusão."""
    channel = FakeChannel()
    interaction = FakeInteraction(channel)

    await General.limpar.callback(cleanup_cog(maximum=3), interaction, 4)  # type: ignore[arg-type]

    assert channel.purge_limits == []
    assert interaction.response.messages == [
        ("Você pode apagar no máximo 3 mensagens por vez.", True)
    ]


@pytest.mark.asyncio
async def test_cleanup_requires_manage_messages_permission() -> None:
    """A validação manual também informa a permissão correta antes do purge."""
    channel = FakeChannel()
    interaction = FakeInteraction(channel, manage_messages=False)

    await General.limpar.callback(cleanup_cog(), interaction, 1)  # type: ignore[arg-type]

    assert channel.purge_limits == []
    assert interaction.response.messages == [(MISSING_MANAGE_MESSAGES_PERMISSION_MESSAGE, True)]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "status", "expected_message"),
    [
        (discord.NotFound, 404, CLEANUP_NOT_FOUND_MESSAGE),
        (
            discord.Forbidden,
            403,
            "Eu preciso da permissão “Gerenciar mensagens” para executar este comando.",
        ),
        (discord.HTTPException, 500, CLEANUP_HTTP_ERROR_MESSAGE),
    ],
)
async def test_cleanup_handles_discord_failures(
    error_type: type[discord.HTTPException], status: int, expected_message: str
) -> None:
    """Falhas Discord retornam respostas seguras em vez de traceback para o usuário."""
    channel = FakeChannel(purge_error=discord_error(error_type, status))
    interaction = FakeInteraction(channel)

    await General.limpar.callback(cleanup_cog(), interaction, 1)  # type: ignore[arg-type]

    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [(expected_message, True)]
