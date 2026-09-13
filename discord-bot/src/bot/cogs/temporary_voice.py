"""Canais de voz temporários criados a partir de um canal configurado."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import cast

import discord
from discord.ext import commands

from bot.client import DiscordBot
from bot.config import Settings

logger = logging.getLogger(__name__)

TEMPORARY_VOICE_PREFIX = "🔊 Sala de "
MAX_VOICE_CHANNEL_NAME_LENGTH = 100


@dataclass(frozen=True, slots=True)
class TemporaryVoiceChannel:
    """Registro em memória de uma sala temporária pertencente a um membro."""

    channel_id: int
    owner_id: int
    guild_id: int


class TemporaryVoice(commands.Cog):
    """Cria, recupera e remove salas de voz temporárias com segurança."""

    def __init__(self, bot: discord.Client, settings: Settings) -> None:
        self._bot = bot
        self._settings = settings
        self._temporary_channels: dict[int, TemporaryVoiceChannel] = {}
        self._owner_channels: dict[tuple[int, int], int] = {}
        self._guild_locks: dict[int, asyncio.Lock] = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Recupera salas reconhecíveis depois de uma inicialização ou reconexão."""
        await self._cleanup_or_recover_temporary_channels()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Cria uma sala ao entrar no criador e remove salas que ficarem vazias."""
        if member.bot:
            if before.channel is not None:
                await self._delete_if_empty(before.channel)
            return
        if before.channel == after.channel:
            return

        if before.channel is not None:
            await self._delete_if_empty(before.channel)

        creator_channel_id = self._settings.temporary_voice_creator_channel_id
        if (
            creator_channel_id is not None
            and after.channel is not None
            and after.channel.id == creator_channel_id
        ):
            await self._create_temporary_voice_channel(member, after.channel)

    async def _create_temporary_voice_channel(
        self,
        member: discord.Member,
        creator_channel: discord.VoiceChannel,
    ) -> None:
        """Cria uma sala e move o membro, sem permitir duplicidade por corrida."""
        guild = creator_channel.guild
        creator_channel_id = self._settings.temporary_voice_creator_channel_id
        if creator_channel_id is None or creator_channel.id != creator_channel_id:
            return

        async with self._lock_for(guild.id):
            if not self._member_is_still_in_creator(member, creator_channel):
                logger.info("Membro saiu do canal criador antes da criação da sala temporária.")
                return

            owner_key = (guild.id, member.id)
            existing_channel_id = self._owner_channels.get(owner_key)
            if existing_channel_id is not None:
                existing_channel = guild.get_channel(existing_channel_id)
                if existing_channel is not None and getattr(existing_channel, "members", None):
                    await self._move_member_to_existing_channel(member, existing_channel)
                    return
                if existing_channel is not None:
                    await self._delete_if_empty_locked(existing_channel)
                if owner_key in self._owner_channels:
                    return

            channel_name = self._temporary_channel_name(member.display_name)
            overwrites = self._temporary_channel_overwrites(member)
            try:
                temporary_channel = await guild.create_voice_channel(
                    name=channel_name,
                    category=creator_channel.category,
                    overwrites=overwrites,
                    reason=f"Sala temporária criada para o membro {member.id}",
                )
            except discord.Forbidden:
                logger.error("Sem permissão para criar sala temporária na guild %s.", guild.id)
                return
            except discord.HTTPException:
                logger.exception("Falha HTTP ao criar sala temporária na guild %s.", guild.id)
                return

            self._register_channel(temporary_channel.id, member.id, guild.id)
            if not self._member_is_still_in_creator(member, creator_channel):
                logger.info("Membro saiu do criador durante a criação da sala temporária.")
                await self._delete_if_empty_locked(temporary_channel)
                return

            try:
                await member.move_to(
                    temporary_channel,
                    reason="Movendo o criador para sua sala temporária",
                )
            except discord.Forbidden:
                logger.error("Sem permissão para mover membro para a sala temporária.")
                await self._delete_if_empty_locked(temporary_channel)
            except discord.HTTPException:
                logger.exception("Falha HTTP ao mover membro para a sala temporária.")
                await self._delete_if_empty_locked(temporary_channel)

    async def _move_member_to_existing_channel(
        self,
        member: discord.Member,
        channel: discord.abc.Snowflake,
    ) -> None:
        """Move o proprietário para sua sala atual quando ele tenta criar outra."""
        try:
            await member.move_to(channel, reason="Movendo o membro para sua sala temporária ativa")
        except discord.Forbidden:
            logger.error("Sem permissão para mover membro para a sala temporária existente.")
        except discord.HTTPException:
            logger.exception("Falha HTTP ao mover membro para a sala temporária existente.")

    async def _delete_if_empty(self, channel: discord.abc.GuildChannel) -> None:
        """Exclui um canal registrado somente quando não há mais participantes."""
        guild = channel.guild
        async with self._lock_for(guild.id):
            await self._delete_if_empty_locked(channel)

    async def _delete_if_empty_locked(self, channel: discord.abc.GuildChannel) -> None:
        """Versão protegida pelo lock de guild para evitar exclusão concorrente."""
        record = self._temporary_channels.get(channel.id)
        creator_channel_id = self._settings.temporary_voice_creator_channel_id
        if record is None or channel.id == creator_channel_id or getattr(channel, "members", None):
            return

        try:
            await channel.delete(reason="Sala temporária vazia")
        except discord.NotFound:
            self._remove_channel_record(record)
        except discord.Forbidden:
            logger.error("Sem permissão para excluir a sala temporária %s.", channel.id)
        except discord.HTTPException:
            logger.exception("Falha HTTP ao excluir a sala temporária %s.", channel.id)
        else:
            self._remove_channel_record(record)
            logger.info("Sala temporária %s excluída por estar vazia.", channel.id)

    async def _cleanup_or_recover_temporary_channels(self) -> None:
        """Reconstrói registros persistentes pelo nome, categoria e overwrite do dono."""
        creator_channel = await self._get_creator_channel()
        if creator_channel is None:
            return

        guild = creator_channel.guild
        async with self._lock_for(guild.id):
            for channel in self._voice_channels_in_creator_category(creator_channel):
                if channel.id == creator_channel.id:
                    continue
                owner_id = self._recoverable_owner_id(channel, guild)
                if owner_id is None:
                    continue
                self._register_channel(channel.id, owner_id, guild.id)
                await self._delete_if_empty_locked(channel)

    async def _get_creator_channel(self) -> discord.VoiceChannel | None:
        """Resolve o canal criador pelo cache e, quando necessário, pela API Discord."""
        creator_channel_id = self._settings.temporary_voice_creator_channel_id
        if creator_channel_id is None:
            return None

        channel = self._bot.get_channel(creator_channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(creator_channel_id)
            except discord.NotFound:
                logger.warning("Canal criador temporário configurado não foi encontrado.")
                return None
            except discord.Forbidden:
                logger.error("Sem permissão para acessar o canal criador temporário.")
                return None
            except discord.HTTPException:
                logger.exception("Falha HTTP ao buscar o canal criador temporário.")
                return None

        if not isinstance(channel, discord.VoiceChannel):
            logger.error("O ID configurado para canal criador não pertence a um canal de voz.")
            return None
        return channel

    def _temporary_channel_overwrites(
        self,
        member: discord.Member,
    ) -> dict[discord.abc.Snowflake, discord.PermissionOverwrite]:
        """Concede ao dono controle restrito à sua própria sala temporária."""
        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True,
                manage_channels=True,
            ),
        }
        if self._bot.user is not None:
            overwrites[self._bot.user] = discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                move_members=True,
            )
        return overwrites

    def _voice_channels_in_creator_category(
        self,
        creator_channel: discord.VoiceChannel,
    ) -> list[discord.VoiceChannel]:
        """Limita a recuperação à categoria do criador (ou canais sem categoria)."""
        if creator_channel.category is not None:
            return list(creator_channel.category.voice_channels)
        return [
            channel for channel in creator_channel.guild.voice_channels if channel.category is None
        ]

    def _recoverable_owner_id(
        self,
        channel: discord.VoiceChannel,
        guild: discord.Guild,
    ) -> int | None:
        """Identifica a marca persistente de dono, evitando canais permanentes parecidos."""
        if not channel.name.startswith(TEMPORARY_VOICE_PREFIX):
            return None

        bot_id = self._bot.user.id if self._bot.user is not None else None
        owner_ids = [
            target.id
            for target, overwrite in channel.overwrites.items()
            if getattr(overwrite, "manage_channels", None) is True
            and target.id not in {guild.default_role.id, bot_id}
            and not isinstance(target, discord.Role)
        ]
        if len(owner_ids) != 1:
            logger.warning(
                "Canal %s com prefixo temporário ignorado na recuperação por dono ambíguo.",
                channel.id,
            )
            return None
        return owner_ids[0]

    @staticmethod
    def _temporary_channel_name(display_name: str) -> str:
        """Normaliza espaços e respeita o limite de cem caracteres dos canais Discord."""
        normalized_name = " ".join(display_name.split()) or "membro"
        return f"{TEMPORARY_VOICE_PREFIX}{normalized_name}"[:MAX_VOICE_CHANNEL_NAME_LENGTH]

    @staticmethod
    def _member_is_still_in_creator(
        member: discord.Member,
        creator_channel: discord.VoiceChannel,
    ) -> bool:
        """Evita mover um membro que saiu durante a operação assíncrona."""
        return member.voice is not None and member.voice.channel == creator_channel

    def _lock_for(self, guild_id: int) -> asyncio.Lock:
        """Retorna um lock independente para evitar bloquear operações de outras guilds."""
        return self._guild_locks.setdefault(guild_id, asyncio.Lock())

    def _register_channel(self, channel_id: int, owner_id: int, guild_id: int) -> None:
        """Mantém os dois índices em memória consistentes."""
        record = TemporaryVoiceChannel(channel_id, owner_id, guild_id)
        self._temporary_channels[channel_id] = record
        self._owner_channels[(guild_id, owner_id)] = channel_id

    def _remove_channel_record(self, record: TemporaryVoiceChannel) -> None:
        """Remove índices apenas quando ainda apontam para o mesmo canal."""
        self._temporary_channels.pop(record.channel_id, None)
        owner_key = (record.guild_id, record.owner_id)
        if self._owner_channels.get(owner_key) == record.channel_id:
            self._owner_channels.pop(owner_key, None)


async def setup(bot: commands.Bot) -> None:
    """Registra o cog de canais temporários na extensão existente do bot."""
    discord_bot = cast(DiscordBot, bot)
    await bot.add_cog(TemporaryVoice(discord_bot, discord_bot.settings))
