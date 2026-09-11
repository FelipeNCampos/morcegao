"""Polling seguro de novas mídias da conta Instagram autorizada."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from bot.config import InstagramSettings
from bot.integrations.discord_sender import DiscordNotificationSender
from bot.integrations.instagram import InstagramClient
from bot.storage import NotificationStore

logger = logging.getLogger(__name__)


class InstagramPoller:
    """Consulta a mídia mais recente sem notificar conteúdo histórico por padrão."""

    def __init__(
        self,
        settings: InstagramSettings,
        instagram_client: InstagramClient,
        store: NotificationStore,
        sender: DiscordNotificationSender,
    ) -> None:
        self._settings = settings
        self._instagram_client = instagram_client
        self._store = store
        self._sender = sender
        self._task: asyncio.Task[None] | None = None
        self._initial_sync_completed = False

    def start(self) -> None:
        """Inicia uma única tarefa de polling quando a integração está ativada."""
        if not self._settings.enabled or (self._task is not None and not self._task.done()):
            return
        self._task = asyncio.create_task(self._run(), name="instagram-poller")
        logger.info("Polling do Instagram iniciado.")

    async def stop(self) -> None:
        """Cancela a tarefa pendente e aguarda seu encerramento."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def poll_once(self) -> None:
        """Executa uma consulta e envia somente uma mídia ainda desconhecida."""
        media = await self._instagram_client.get_latest_media()
        if media is None:
            self._initial_sync_completed = True
            return

        already_processed = await self._store.has_processed_instagram_media(media.media_id)
        if not self._initial_sync_completed:
            self._initial_sync_completed = True
            if already_processed:
                return
            if not self._settings.notify_existing_latest:
                await self._store.mark_instagram_media_processed(media, status="known")
                logger.info("A mídia mais recente do Instagram foi marcada como conhecida.")
                return

        if already_processed:
            return

        await self._sender.send_instagram_notification(media)
        await self._store.mark_instagram_media_processed(media, status="notified")
        logger.info("Notificação de nova mídia do Instagram enviada.")

    async def _run(self) -> None:
        """Mantém o polling ativo sem derrubar o bot após uma falha recuperável."""
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Falha recuperável durante o polling do Instagram.")
            await asyncio.sleep(self._settings.poll_interval_seconds)
