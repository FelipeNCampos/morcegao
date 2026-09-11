"""Validação periódica do App Access Token Twitch em memória."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from bot.config import TwitchSettings
from bot.integrations.twitch import TwitchClient
from bot.integrations.twitch_auth import TwitchError

logger = logging.getLogger(__name__)


class TwitchTokenValidator:
    """Valida e recupera o token Twitch sem interromper o cliente Discord."""

    def __init__(self, settings: TwitchSettings, twitch_client: TwitchClient) -> None:
        self._settings = settings
        self._twitch_client = twitch_client
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Inicia no máximo uma tarefa periódica quando a integração está ativa."""
        if not self._settings.enabled or (self._task is not None and not self._task.done()):
            return
        self._task = asyncio.create_task(self._run(), name="twitch-token-validator")
        logger.info("Validação periódica do token Twitch iniciada.")

    async def stop(self) -> None:
        """Cancela e aguarda a tarefa para encerrar o processo sem pendências."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def validate_once(self) -> None:
        """Executa uma validação para uso em testes ou disparos controlados."""
        await self._twitch_client.ensure_valid_access_token()

    async def _run(self) -> None:
        """Mantém a validação independente e recuperável enquanto o bot estiver aberto."""
        while True:
            await asyncio.sleep(self._settings.token_validate_interval_seconds)
            try:
                await self.validate_once()
                logger.debug("Token Twitch validado com sucesso.")
            except asyncio.CancelledError:
                raise
            except TwitchError:
                logger.exception(
                    "Não foi possível validar o token Twitch; nova tentativa será feita."
                )
