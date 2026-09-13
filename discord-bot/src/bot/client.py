"""Cliente principal do bot do Discord."""

from __future__ import annotations

import asyncio
import contextlib
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.config import Settings
from bot.current_twitch_live import CurrentTwitchLiveStore
from bot.errors import handle_app_command_error
from bot.integrations.discord_sender import DiscordNotificationSender
from bot.integrations.instagram import InstagramClient
from bot.integrations.instagram_token_store import InstagramTokenStore
from bot.integrations.twitch import TwitchClient
from bot.models import TwitchOnlineEvent
from bot.storage import NotificationStore
from bot.tasks.instagram_poller import InstagramPoller
from bot.tasks.instagram_token_refresh import InstagramTokenRefreshTask
from bot.tasks.twitch_token_validator import TwitchTokenValidator

logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """Cliente Discord com comandos slash e o comando prefixado de moderação."""

    def __init__(
        self,
        settings: Settings,
        *,
        store: NotificationStore,
        twitch_client: TwitchClient | None = None,
        instagram_client: InstagramClient | None = None,
        instagram_token_store: InstagramTokenStore | None = None,
    ) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        # Necessário para receber on_member_join e resolver membros em reações antigas.
        intents.members = True
        intents.presences = False
        intents.guilds = True
        intents.guild_messages = True
        intents.voice_states = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
            application_id=settings.discord_application_id,
            tree_cls=app_commands.CommandTree,
        )
        self.settings = settings
        self.tree.on_error = handle_app_command_error
        self._store = store
        self.twitch_client = twitch_client
        self._instagram_client = instagram_client
        self._sender = DiscordNotificationSender(self, settings)
        self._current_twitch_live = CurrentTwitchLiveStore()
        self._twitch_notification_queue: asyncio.Queue[TwitchOnlineEvent] = asyncio.Queue()
        self._twitch_worker_task: asyncio.Task[None] | None = None
        self._twitch_token_validator = (
            TwitchTokenValidator(settings.twitch, twitch_client)
            if twitch_client is not None
            else None
        )
        self._instagram_poller = (
            InstagramPoller(settings.instagram, instagram_client, store, self._sender)
            if instagram_client is not None
            else None
        )
        self._instagram_token_refresh_task = (
            InstagramTokenRefreshTask(settings.instagram, instagram_client, instagram_token_store)
            if instagram_client is not None
            and instagram_token_store is not None
            and settings.instagram.auto_refresh_token
            else None
        )

    @property
    def notification_sender(self) -> DiscordNotificationSender:
        """Expõe o remetente compartilhado para extensões do bot."""
        return self._sender

    @property
    def current_twitch_live(self) -> CurrentTwitchLiveStore:
        """Expõe o estado em memória da última live Twitch ainda aberta."""
        return self._current_twitch_live

    @property
    def instagram_client(self) -> InstagramClient | None:
        """Expõe o cliente Instagram compartilhado para comandos administrativos."""
        return self._instagram_client

    async def setup_hook(self) -> None:
        """Carrega extensões e sincroniza comandos antes de conectar ao gateway."""
        await self.load_extension("bot.cogs.general")
        await self.load_extension("bot.cogs.media_reactions")
        await self.load_extension("bot.cogs.role_management")
        await self.load_extension("bot.cogs.temporary_voice")
        await self.load_extension("bot.cogs.music")

        if self.settings.discord_guild_id is not None:
            guild = discord.Object(id=self.settings.discord_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced_commands = await self.tree.sync(guild=guild)
            logger.info(
                "%d comando(s) slash sincronizado(s) no servidor de desenvolvimento.",
                len(synced_commands),
            )
        else:
            logger.warning(
                "DISCORD_GUILD_ID não foi definido; "
                "comandos de desenvolvimento não foram sincronizados."
            )

        if self.settings.sync_global_commands:
            synced_commands = await self.tree.sync()
            logger.info("%d comando(s) slash sincronizado(s) globalmente.", len(synced_commands))

        if self.twitch_client is not None and (
            self._twitch_worker_task is None or self._twitch_worker_task.done()
        ):
            self._twitch_worker_task = asyncio.create_task(
                self._run_twitch_notification_worker(), name="twitch-notification-worker"
            )
        if self._twitch_token_validator is not None:
            self._twitch_token_validator.start()
        if self._instagram_token_refresh_task is not None:
            self._instagram_token_refresh_task.start()

    def queue_twitch_notification(self, event: TwitchOnlineEvent) -> None:
        """Enfileira um evento EventSub sem bloquear a resposta HTTP da Twitch."""
        if self.twitch_client is None:
            logger.warning("Evento Twitch ignorado: integração desativada.")
            return
        expected_broadcaster_id = self.twitch_client.resolved_broadcaster_user_id
        if (
            expected_broadcaster_id is not None
            and event.broadcaster_user_id != expected_broadcaster_id
        ):
            logger.info("Evento Twitch ignorado: perfil diferente do perfil configurado.")
            return
        self._twitch_notification_queue.put_nowait(event)

    async def on_ready(self) -> None:
        """Registra a conexão e inicia serviços que dependem do cliente pronto."""
        if self.user is None:
            logger.info("O bot está pronto.")
        else:
            logger.info("O bot está pronto como %s (ID: %s).", self.user, self.user.id)

        if self._instagram_poller is not None:
            self._instagram_poller.start()

    async def close(self) -> None:
        """Cancela tarefas e fecha clientes auxiliares antes de encerrar o Discord."""
        if self._instagram_poller is not None:
            await self._instagram_poller.stop()

        if self._instagram_token_refresh_task is not None:
            await self._instagram_token_refresh_task.stop()

        if self._twitch_token_validator is not None:
            await self._twitch_token_validator.stop()

        if self._twitch_worker_task is not None:
            self._twitch_worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._twitch_worker_task
            self._twitch_worker_task = None

        if self._instagram_client is not None:
            await self._instagram_client.aclose()
        if self.twitch_client is not None:
            await self.twitch_client.aclose()
        await super().close()

    async def _run_twitch_notification_worker(self) -> None:
        """Entrega eventos Twitch após o cliente Discord ficar disponível."""
        while True:
            event = await self._twitch_notification_queue.get()
            try:
                await self.wait_until_ready()
                if self.twitch_client is None:
                    continue
                stream = await self.twitch_client.get_stream(event.broadcaster_user_id)
                if not stream.is_live:
                    await self._current_twitch_live.set_current(event, stream)
                    await self._store.update_twitch_event_status(event.message_id, "offline")
                    logger.info("Live Twitch encerrada antes do envio da notificação.")
                    continue
                await self._current_twitch_live.set_current(event, stream)
                await self._sender.send_twitch_notification(event, stream)
                await self._store.update_twitch_event_status(event.message_id, "notified")
                logger.info("Notificação de live da Twitch enviada.")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Falha recuperável ao enviar uma notificação da Twitch.")
                with contextlib.suppress(Exception):
                    await self._store.update_twitch_event_status(event.message_id, "failed")
            finally:
                self._twitch_notification_queue.task_done()
