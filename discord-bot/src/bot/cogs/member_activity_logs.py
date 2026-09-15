"""Logs configuráveis de entrada e saída de membros."""

from __future__ import annotations

import logging
from typing import Any, cast

import discord
from discord.ext import commands

from bot.config import Settings

logger = logging.getLogger(__name__)


class MemberActivityLogs(commands.Cog):
    """Publica eventos de entrada e saída no canal de auditoria configurado."""

    def __init__(self, bot: commands.Bot, settings: Settings) -> None:
        self._bot = bot
        self._settings = settings

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Registra a entrada de um membro no servidor."""
        await self._send_member_log(member, "📥", "entrou no servidor")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Registra a saída de um membro do servidor."""
        await self._send_member_log(member, "📤", "saiu do servidor")

    async def _send_member_log(self, member: discord.Member, icon: str, action: str) -> None:
        channel_id = self._settings.member_log_channel_id
        if channel_id is None:
            return

        channel = await self._resolve_channel(channel_id)
        if channel is None:
            return

        send = getattr(channel, "send", None)
        if not callable(send):
            logger.warning("Canal de logs %s não aceita mensagens.", channel_id)
            return

        message = f"{icon} {member.mention} {action}. (ID: {member.id})"
        try:
            await send(message, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            logger.warning("Sem permissão para enviar logs no canal %s.", channel_id)
        except discord.NotFound:
            logger.warning("Canal de logs %s não foi encontrado ao enviar mensagem.", channel_id)
        except discord.HTTPException as error:
            logger.warning(
                "Falha HTTP ao enviar log de membro no canal %s: status=%s.",
                channel_id,
                error.status,
            )

    async def _resolve_channel(self, channel_id: int) -> Any | None:
        channel = self._bot.get_channel(channel_id)
        if channel is not None:
            return channel

        try:
            return await self._bot.fetch_channel(channel_id)
        except discord.NotFound:
            logger.warning("Canal de logs configurado %s não foi encontrado.", channel_id)
        except discord.Forbidden:
            logger.warning("Sem acesso ao canal de logs configurado %s.", channel_id)
        except discord.HTTPException as error:
            logger.warning(
                "Falha HTTP ao buscar canal de logs %s: status=%s.", channel_id, error.status
            )
        return None


async def setup(bot: commands.Bot) -> None:
    """Registra o cog usando as configurações do cliente principal."""
    settings = cast(Settings, bot.settings)
    await bot.add_cog(MemberActivityLogs(bot, settings))
