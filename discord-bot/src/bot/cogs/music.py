"""Comandos de reprodução de áudio do YouTube por guild."""

from __future__ import annotations

import asyncio
import logging
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import DiscordBot
from bot.config import Settings
from bot.integrations.youtube_audio import (
    YouTubeAudioError,
    YouTubeAudioService,
    is_valid_youtube_url,
)

logger = logging.getLogger(__name__)

FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"
INVALID_URL_MESSAGE = (
    "Envie um link válido de vídeo do YouTube. Exemplo: "
    "/tocar_youtube url:https://www.youtube.com/watch?v=VIDEO_ID"
)


class Music(commands.Cog):
    """Toca uma faixa por vez, com locks e timeout independentes por guild."""

    def __init__(
        self,
        bot: DiscordBot,
        settings: Settings,
        audio_service: YouTubeAudioService | None = None,
    ) -> None:
        self._bot = bot
        self._settings = settings
        self._audio_service = audio_service or YouTubeAudioService()
        self._voice_locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task[None]] = {}

    def cog_unload(self) -> None:
        """Cancela timeouts pendentes quando a extensão for descarregada."""
        for task in self._idle_tasks.values():
            task.cancel()
        self._idle_tasks.clear()

    @app_commands.command(
        name="tocar_youtube", description="Entra na sua call e toca o áudio de um link do YouTube."
    )
    @app_commands.describe(url="Link de um vídeo do YouTube")
    @app_commands.guild_only()
    async def play_youtube(self, interaction: discord.Interaction, url: str) -> None:
        """Conecta ao canal do solicitante e substitui a faixa atual com segurança."""
        voice_channel = await self._requester_voice_channel(interaction)
        if voice_channel is None:
            return
        if not is_valid_youtube_url(url):
            await interaction.response.send_message(INVALID_URL_MESSAGE, ephemeral=True)
            return

        await interaction.response.defer()
        guild = interaction.guild
        assert guild is not None
        async with self._lock_for(guild.id):
            self._cancel_idle_task(guild.id)
            try:
                voice_client = await self._connect_or_move(guild, voice_channel)
            except discord.Forbidden:
                await interaction.followup.send(
                    "Não consigo entrar no seu canal de voz. Verifique as permissões do bot.",
                    ephemeral=True,
                )
                return
            except (discord.ClientException, discord.HTTPException):
                logger.warning(
                    "Falha ao conectar à voz: guild=%s usuário=%s canal=%s.",
                    guild.id,
                    interaction.user.id,
                    voice_channel.id,
                )
                await interaction.followup.send(
                    "Não consegui entrar no seu canal de voz. Tente novamente em instantes.",
                    ephemeral=True,
                )
                return

            try:
                audio = await self._audio_service.get_audio_source(url)
                source = discord.FFmpegPCMAudio(
                    audio.stream_url,
                    before_options=FFMPEG_BEFORE_OPTIONS,
                    options=FFMPEG_OPTIONS,
                    executable="ffmpeg",
                )
            except FileNotFoundError:
                logger.error("FFmpeg não encontrado ao tocar áudio: guild=%s.", guild.id)
                await interaction.followup.send(
                    "O servidor do bot não possui FFmpeg configurado para reprodução de áudio.",
                    ephemeral=True,
                )
                self._schedule_idle_disconnect(guild.id)
                return
            except YouTubeAudioError:
                await interaction.followup.send(
                    "Não consegui obter o áudio desse link do YouTube. Verifique se o vídeo é "
                    "público, está disponível na sua região e possui áudio.",
                    ephemeral=True,
                )
                self._schedule_idle_disconnect(guild.id)
                return

            try:
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                loop = asyncio.get_running_loop()
                voice_client.play(
                    source,
                    after=lambda error: self._schedule_idle_from_audio_thread(
                        guild.id, loop, error
                    ),
                )
            except (discord.ClientException, discord.HTTPException):
                logger.exception("Falha ao iniciar áudio: guild=%s.", guild.id)
                await interaction.followup.send(
                    "Não consegui iniciar a reprodução de áudio nesse canal.", ephemeral=True
                )
                self._schedule_idle_disconnect(guild.id)
                return

        logger.info(
            "Áudio iniciado: guild=%s usuário=%s canal=%s host=youtube título=%s.",
            guild.id,
            interaction.user.id,
            voice_channel.id,
            audio.title,
        )
        await interaction.followup.send(
            f"▶️ Tocando agora: [{audio.title}]({audio.webpage_url})\n"
            f"Canal: {voice_channel.mention}\nSolicitado por: {interaction.user.mention}"
        )

    @app_commands.command(name="parar_musica", description="Interrompe a reprodução atual.")
    @app_commands.guild_only()
    async def stop_music(self, interaction: discord.Interaction) -> None:
        """Para o áudio mantendo a conexão até o timeout de inatividade."""
        voice_client = await self._same_channel_voice_client(interaction)
        if voice_client is None:
            return
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        assert interaction.guild is not None
        self._schedule_idle_disconnect(interaction.guild.id)
        await interaction.response.send_message("⏹️ Reprodução interrompida.", ephemeral=True)

    @app_commands.command(name="sair_call", description="Para a música e sai do seu canal de voz.")
    @app_commands.guild_only()
    async def leave_voice(self, interaction: discord.Interaction) -> None:
        """Para e desconecta do canal do solicitante, limpando o estado da guild."""
        voice_client = await self._same_channel_voice_client(interaction)
        if voice_client is None:
            return
        assert interaction.guild is not None
        guild_id = interaction.guild.id
        self._cancel_idle_task(guild_id)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        try:
            await voice_client.disconnect(force=False)
        except discord.HTTPException:
            logger.warning("Falha ao desconectar da voz: guild=%s.", guild_id)
            await interaction.response.send_message(
                "Não consegui sair do canal de voz agora.", ephemeral=True
            )
            return
        await interaction.response.send_message("👋 Saí do canal de voz.", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        """Sai de uma sala sem humanos para não impedir a limpeza de salas temporárias."""
        if member.bot:
            return
        guild = member.guild
        voice_client = guild.voice_client
        if voice_client is None or voice_client.channel is None:
            return
        if before.channel != voice_client.channel and after.channel != voice_client.channel:
            return
        if self._has_human_members(voice_client.channel):
            return
        self._cancel_idle_task(guild.id)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        try:
            await voice_client.disconnect(force=False)
        except discord.HTTPException:
            logger.warning("Falha ao sair de canal sem humanos: guild=%s.", guild.id)

    async def _requester_voice_channel(
        self, interaction: discord.Interaction
    ) -> discord.abc.Connectable | None:
        """Valida que o comando veio de uma guild e o usuário está em voz."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando só pode ser usado dentro de um servidor.", ephemeral=True
            )
            return None
        member = interaction.user
        if (
            not isinstance(member, discord.Member)
            or member.voice is None
            or member.voice.channel is None
        ):
            await interaction.response.send_message(
                "Você precisa estar em um canal de voz para usar este comando.", ephemeral=True
            )
            return None
        return member.voice.channel

    async def _same_channel_voice_client(
        self, interaction: discord.Interaction
    ) -> discord.VoiceClient | None:
        """Exige que o solicitante esteja no mesmo canal de voz do bot."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando só pode ser usado dentro de um servidor.", ephemeral=True
            )
            return None
        member = interaction.user
        voice_client = interaction.guild.voice_client
        if (
            not isinstance(member, discord.Member)
            or member.voice is None
            or member.voice.channel is None
            or voice_client is None
            or voice_client.channel != member.voice.channel
        ):
            await interaction.response.send_message(
                "Você precisa estar no mesmo canal de voz que o Morcegão.", ephemeral=True
            )
            return None
        return voice_client

    async def _connect_or_move(
        self, guild: discord.Guild, channel: discord.abc.Connectable
    ) -> discord.VoiceClient:
        """Conecta ou move somente para o canal validado do solicitante."""
        voice_client = guild.voice_client
        if voice_client is None:
            return await channel.connect(self_deaf=True)
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
        return voice_client

    def _lock_for(self, guild_id: int) -> asyncio.Lock:
        """Retorna um lock independente para uma guild."""
        return self._voice_locks.setdefault(guild_id, asyncio.Lock())

    def _schedule_idle_from_audio_thread(
        self, guild_id: int, loop: asyncio.AbstractEventLoop, error: Exception | None
    ) -> None:
        """Agenda a desconexão no loop correto após callback síncrono do player."""
        if error is not None:
            logger.warning(
                "Player FFmpeg terminou com erro na guild %s: %s.", guild_id, type(error).__name__
            )
        loop.call_soon_threadsafe(self._schedule_idle_disconnect, guild_id)

    def _schedule_idle_disconnect(self, guild_id: int) -> None:
        """Substitui qualquer timeout anterior por um único timeout da guild."""
        self._cancel_idle_task(guild_id)
        self._idle_tasks[guild_id] = asyncio.create_task(self._disconnect_when_idle(guild_id))

    def _cancel_idle_task(self, guild_id: int) -> None:
        """Cancela timeout pendente quando nova música começa ou há atividade humana."""
        task = self._idle_tasks.pop(guild_id, None)
        if task is not None:
            task.cancel()

    async def _disconnect_when_idle(self, guild_id: int) -> None:
        """Desconecta uma guild inativa sem interferir em nova reprodução."""
        try:
            await asyncio.sleep(self._settings.music_idle_disconnect_seconds)
            guild = self._bot.get_guild(guild_id)
            voice_client = guild.voice_client if guild is not None else None
            if (
                voice_client is not None
                and not voice_client.is_playing()
                and not voice_client.is_paused()
            ):
                await voice_client.disconnect(force=False)
                logger.info("Canal de voz desconectado por inatividade: guild=%s.", guild_id)
        except asyncio.CancelledError:
            raise
        except discord.HTTPException:
            logger.warning("Falha ao desconectar canal inativo: guild=%s.", guild_id)
        finally:
            self._idle_tasks.pop(guild_id, None)

    @staticmethod
    def _has_human_members(channel: discord.abc.GuildChannel) -> bool:
        """Verifica se há alguém além do bot na sala atual."""
        return any(not member.bot for member in channel.members)


async def setup(bot: commands.Bot) -> None:
    """Registra os comandos de música no cliente Discord existente."""
    discord_bot = cast(DiscordBot, bot)
    await bot.add_cog(Music(discord_bot, discord_bot.settings))
