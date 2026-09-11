"""Reações automáticas para mídias enviadas em um canal configurado."""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import cast

import discord
from discord.ext import commands

from bot.client import DiscordBot
from bot.config import Settings

logger = logging.getLogger(__name__)

FOFUXO_REACTIONS = (
    "🇫",
    "🇴",
    "🇫",
    "🇺",
    "🇽",
    "🇴",
)
MEDIA_CONTENT_TYPE_PREFIXES = ("image/", "video/")
MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".mp4",
    ".mov",
    ".webm",
    ".mkv",
}
PROCESSED_MESSAGE_CACHE_LIMIT = 1_000


def _message_contains_media(message: discord.Message) -> bool:
    """Retorna se ao menos um anexo da mensagem é imagem, GIF ou vídeo."""
    for attachment in message.attachments:
        content_type = attachment.content_type
        if content_type is not None:
            if content_type.startswith(MEDIA_CONTENT_TYPE_PREFIXES):
                return True
            continue

        if Path(attachment.filename).suffix.lower() in MEDIA_EXTENSIONS:
            return True
    return False


class MediaReactions(commands.Cog):
    """Adiciona a sequência FOFUXO a mídias do canal explicitamente configurado."""

    def __init__(self, bot: discord.Client, settings: Settings) -> None:
        self._bot = bot
        self._settings = settings
        self._processed_media_messages: set[int] = set()
        self._processed_message_order: deque[int] = deque()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Processa somente mensagens humanas com mídia no canal configurado."""
        if message.author.bot:
            return

        channel_id = self._settings.media_reaction_channel_id
        if channel_id is None or message.channel.id != channel_id:
            return
        if not _message_contains_media(message):
            return
        if not self._remember_processed_message(message.id):
            return

        attachment = next(
            (
                item
                for item in message.attachments
                if item.content_type is None
                or item.content_type.startswith(MEDIA_CONTENT_TYPE_PREFIXES)
            ),
            message.attachments[0],
        )
        logger.info(
            "Mídia detectada na mensagem %s do canal %s pelo autor %s: arquivo=%s tipo=%s.",
            message.id,
            message.channel.id,
            message.author.id,
            attachment.filename,
            attachment.content_type,
        )
        await self._add_fofuxo_reactions(message)

    async def _add_fofuxo_reactions(self, message: discord.Message) -> None:
        """Adiciona as reações em ordem e encerra com segurança após uma falha."""
        for emoji in FOFUXO_REACTIONS:
            try:
                await message.add_reaction(emoji)
            except discord.Forbidden:
                logger.warning("Sem permissão para reagir à mensagem %s.", message.id)
                return
            except discord.NotFound:
                logger.warning("A mensagem %s não existe mais para receber reações.", message.id)
                return
            except discord.HTTPException as error:
                logger.warning(
                    "Falha ao adicionar a reação %s à mensagem %s: status=%s.",
                    emoji,
                    message.id,
                    error.status,
                )
                return

        logger.info(
            "Reações FOFUXO adicionadas à mensagem %s do canal %s.",
            message.id,
            message.channel.id,
        )

    def _remember_processed_message(self, message_id: int) -> bool:
        """Registra uma mensagem uma vez e limita o cache estritamente em memória."""
        if message_id in self._processed_media_messages:
            return False

        self._processed_media_messages.add(message_id)
        self._processed_message_order.append(message_id)
        if len(self._processed_message_order) > PROCESSED_MESSAGE_CACHE_LIMIT:
            expired_message_id = self._processed_message_order.popleft()
            self._processed_media_messages.discard(expired_message_id)
        return True


async def setup(bot: commands.Bot) -> None:
    """Registra o listener sem substituir o on_message do cliente principal."""
    discord_bot = cast(DiscordBot, bot)
    await bot.add_cog(MediaReactions(discord_bot, discord_bot.settings))
