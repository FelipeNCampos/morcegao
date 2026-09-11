"""Testes isolados para o listener de reações FOFUXO em mídias."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import discord
import pytest
from discord.ext import commands

from bot.client import DiscordBot
from bot.cogs.media_reactions import (
    FOFUXO_REACTIONS,
    PROCESSED_MESSAGE_CACHE_LIMIT,
    MediaReactions,
    _message_contains_media,
)
from bot.config import Settings


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Constrói uma falha Discord controlada sem qualquer chamada de rede."""
    response = SimpleNamespace(status=status, reason="Erro de teste", headers={})
    return error_type(response, "Erro de teste")


class FakeAttachment:
    """Anexo mínimo com metadados suficientes para a detecção local."""

    def __init__(self, filename: str, content_type: str | None) -> None:
        self.filename = filename
        self.content_type = content_type


class FakeMessage:
    """Mensagem controlável que registra reações sem usar Discord real."""

    def __init__(
        self,
        message_id: int,
        channel_id: int,
        attachments: list[FakeAttachment],
        *,
        author_is_bot: bool = False,
        reaction_error: discord.HTTPException | None = None,
    ) -> None:
        self.id = message_id
        self.channel = SimpleNamespace(id=channel_id)
        self.author = SimpleNamespace(id=50, bot=author_is_bot)
        self.attachments = attachments
        self._reaction_error = reaction_error
        self.reactions: list[str] = []

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)
        if self._reaction_error is not None:
            raise self._reaction_error


def media_reaction_settings(environment: Callable[[], dict[str, str]]) -> Settings:
    """Retorna Settings com o listener configurado para o canal fake 10."""
    values = environment()
    values["DISCORD_MEDIA_REACTION_CHANNEL_ID"] = "10"
    return Settings.from_environment(values)


def media_cog(environment: Callable[[], dict[str, str]]) -> MediaReactions:
    """Cria o cog sem instanciar um segundo cliente Discord."""
    return MediaReactions(SimpleNamespace(), media_reaction_settings(environment))  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("imagem.png", "image/png"),
        ("foto.jpg", "image/jpeg"),
        ("animacao.gif", "image/gif"),
        ("live.mp4", "video/mp4"),
    ],
)
async def test_supported_media_receives_fofuxo_reactions(
    environment: Callable[[], dict[str, str]], filename: str, content_type: str
) -> None:
    """PNG, JPG, GIF e vídeo recebem todas as reações na ordem definida."""
    cog = media_cog(environment)
    message = FakeMessage(1, 10, [FakeAttachment(filename, content_type)])

    await cog.on_message(message)  # type: ignore[arg-type]

    assert message.reactions == list(FOFUXO_REACTIONS)


@pytest.mark.asyncio
async def test_extension_is_used_when_content_type_is_missing(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Arquivos sem content type usam a extensão como fallback sem baixar a mídia."""
    cog = media_cog(environment)
    message = FakeMessage(1, 10, [FakeAttachment("video.WEBM", None)])

    await cog.on_message(message)  # type: ignore[arg-type]

    assert _message_contains_media(message) is True  # type: ignore[arg-type]
    assert message.reactions == list(FOFUXO_REACTIONS)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content_type"),
    [("arquivo.pdf", "application/pdf"), ("notas.txt", None)],
)
async def test_non_media_or_messages_without_attachments_are_ignored(
    environment: Callable[[], dict[str, str]], filename: str, content_type: str | None
) -> None:
    """Documentos e mensagens sem anexos não recebem reação."""
    cog = media_cog(environment)
    document_message = FakeMessage(1, 10, [FakeAttachment(filename, content_type)])
    empty_message = FakeMessage(2, 10, [])

    await cog.on_message(document_message)  # type: ignore[arg-type]
    await cog.on_message(empty_message)  # type: ignore[arg-type]

    assert document_message.reactions == []
    assert empty_message.reactions == []


@pytest.mark.asyncio
async def test_other_channel_bot_author_and_disabled_configuration_are_ignored(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O escopo fica estritamente limitado ao canal configurado e a autores humanos."""
    media = FakeAttachment("imagem.png", "image/png")
    cog = media_cog(environment)
    other_channel = FakeMessage(1, 11, [media])
    bot_message = FakeMessage(2, 10, [media], author_is_bot=True)
    disabled_values = environment()
    disabled_cog = MediaReactions(SimpleNamespace(), Settings.from_environment(disabled_values))  # type: ignore[arg-type]
    disabled_message = FakeMessage(3, 10, [media])

    await cog.on_message(other_channel)  # type: ignore[arg-type]
    await cog.on_message(bot_message)  # type: ignore[arg-type]
    await disabled_cog.on_message(disabled_message)  # type: ignore[arg-type]

    assert other_channel.reactions == []
    assert bot_message.reactions == []
    assert disabled_message.reactions == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_type", "status"),
    [(discord.Forbidden, 403), (discord.NotFound, 404), (discord.HTTPException, 500)],
)
async def test_discord_reaction_errors_are_handled_without_retrying(
    environment: Callable[[], dict[str, str]],
    error_type: type[discord.HTTPException],
    status: int,
) -> None:
    """Erros de permissão, ausência e HTTP encerram a sequência sem derrubar o listener."""
    cog = media_cog(environment)
    message = FakeMessage(
        1,
        10,
        [FakeAttachment("imagem.png", "image/png")],
        reaction_error=discord_error(error_type, status),
    )

    await cog.on_message(message)  # type: ignore[arg-type]

    assert message.reactions == [FOFUXO_REACTIONS[0]]


@pytest.mark.asyncio
async def test_message_is_processed_only_once_and_cache_is_bounded(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Eventos duplicados não causam spam e IDs antigos saem do cache limitado."""
    cog = media_cog(environment)
    message = FakeMessage(1, 10, [FakeAttachment("imagem.png", "image/png")])

    await cog.on_message(message)  # type: ignore[arg-type]
    await cog.on_message(message)  # type: ignore[arg-type]
    assert message.reactions == list(FOFUXO_REACTIONS)

    for message_id in range(2, PROCESSED_MESSAGE_CACHE_LIMIT + 3):
        assert cog._remember_processed_message(message_id) is True

    assert len(cog._processed_media_messages) == PROCESSED_MESSAGE_CACHE_LIMIT
    assert 1 not in cog._processed_media_messages


def test_media_listener_is_unique_and_preserves_prefix_command_processing(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O cog registra um listener e mantém o on_message herdado de commands.Bot."""
    listeners = [name for name, _ in media_cog(environment).get_listeners()]

    assert listeners == ["on_message"]
    assert DiscordBot.on_message is commands.Bot.on_message
