"""Testes do comando prefixado de limpeza, sem acesso ao Discord."""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import discord
import pytest
from discord.ext import commands

from bot.cogs.general import (
    CLEANUP_DM_MESSAGE,
    CLEANUP_HTTP_ERROR_MESSAGE,
    CLEANUP_NOT_FOUND_MESSAGE,
    General,
)


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Cria uma exceção Discord sem uma requisição real."""
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


class FakeContext:
    """Contexto mínimo para executar o comando prefixado diretamente."""

    def __init__(self, channel: FakeChannel, *, guild: object | None = object()) -> None:
        self.channel = channel
        self.guild = guild
        self.author = SimpleNamespace(id=4321)
        self.messages: list[tuple[str, int | None]] = []

    async def send(self, content: str, *, delete_after: int | None = None) -> None:
        self.messages.append((content, delete_after))


class FakeNotificationSender:
    """Dependência não usada pelo comando de limpeza."""


def cleanup_cog(*, maximum: int = 100) -> General:
    """Monta o cog com o limite configurável usado no teste."""
    return General(FakeNotificationSender(), max_messages_to_delete=maximum)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_cleanup_purges_requested_messages_and_the_command_message() -> None:
    """A limpeza pede quantidade + 1 e confirma somente mensagens anteriores."""
    channel = FakeChannel(messages=[object() for _ in range(11)])
    ctx = FakeContext(channel)

    await General.limpar.callback(cleanup_cog(), ctx, 10)  # type: ignore[arg-type]

    assert channel.purge_limits == [11]
    assert ctx.messages == [("🧹 10 mensagens foram apagadas.", 5)]


@pytest.mark.asyncio
async def test_cleanup_confirmation_never_reports_a_negative_count() -> None:
    """Uma limitação do Discord que omita o comando ainda produz uma contagem segura."""
    channel = FakeChannel(messages=[])
    ctx = FakeContext(channel)

    await General.limpar.callback(cleanup_cog(), ctx, 1)  # type: ignore[arg-type]

    assert ctx.messages == [("🧹 0 mensagens foram apagadas.", 5)]


@pytest.mark.asyncio
@pytest.mark.parametrize("quantity", [0, -1])
async def test_cleanup_rejects_non_positive_quantities(quantity: int) -> None:
    """Zero e valores negativos não chamam a API de exclusão."""
    channel = FakeChannel()
    ctx = FakeContext(channel)

    await General.limpar.callback(cleanup_cog(), ctx, quantity)  # type: ignore[arg-type]

    assert channel.purge_limits == []
    assert ctx.messages == [("Informe uma quantidade maior que zero.", 5)]


@pytest.mark.asyncio
async def test_cleanup_rejects_a_quantity_above_the_configured_limit() -> None:
    """O limite configurado bloqueia a limpeza antes de qualquer exclusão."""
    channel = FakeChannel()
    ctx = FakeContext(channel)

    await General.limpar.callback(cleanup_cog(maximum=3), ctx, 4)  # type: ignore[arg-type]

    assert channel.purge_limits == []
    assert ctx.messages == [("Você pode apagar no máximo 3 mensagens por vez.", 5)]


@pytest.mark.asyncio
async def test_cleanup_handles_not_found_and_http_errors() -> None:
    """Falhas Discord são convertidas em respostas temporárias e sem detalhes internos."""
    missing_ctx = FakeContext(FakeChannel(purge_error=discord_error(discord.NotFound, 404)))
    http_ctx = FakeContext(FakeChannel(purge_error=discord_error(discord.HTTPException, 500)))

    await General.limpar.callback(cleanup_cog(), missing_ctx, 1)  # type: ignore[arg-type]
    await General.limpar.callback(cleanup_cog(), http_ctx, 1)  # type: ignore[arg-type]

    assert missing_ctx.messages == [(CLEANUP_NOT_FOUND_MESSAGE, 5)]
    assert http_ctx.messages == [(CLEANUP_HTTP_ERROR_MESSAGE, 5)]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            commands.MissingPermissions(["manage_messages"]),
            "Você precisa da permissão “Gerenciar mensagens” para usar este comando.",
        ),
        (
            commands.BotMissingPermissions(["manage_messages"]),
            "Eu preciso da permissão “Gerenciar mensagens” para executar este comando.",
        ),
        (
            commands.BadArgument(),
            "Uso correto: `/limpar <quantidade>`\nExemplo: `/limpar 10`",
        ),
        (
            commands.NoPrivateMessage(),
            CLEANUP_DM_MESSAGE,
        ),
    ],
)
async def test_cleanup_error_handler_handles_permissions_bad_argument_and_dm(
    error: commands.CommandError,
    message: str,
) -> None:
    """Os erros previsíveis não chegam ao canal como traceback."""
    ctx = FakeContext(FakeChannel(), guild=None)

    await General.limpar_error(cleanup_cog(), ctx, error)  # type: ignore[arg-type]

    assert ctx.messages == [(message, 5)]


@pytest.mark.asyncio
async def test_cleanup_error_handler_handles_missing_quantity() -> None:
    """A ausência de argumento recebe instrução de uso específica."""
    parameter = commands.Parameter(
        "quantidade",
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.empty,
        int,
        "",
        "",
        "quantidade",
    )
    ctx = FakeContext(FakeChannel())

    await General.limpar_error(
        cleanup_cog(),
        ctx,  # type: ignore[arg-type]
        commands.MissingRequiredArgument(parameter),
    )

    assert ctx.messages == [("Informe a quantidade de mensagens.\nUso: `/limpar <quantidade>`", 5)]
