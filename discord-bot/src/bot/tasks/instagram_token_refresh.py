"""Tarefa assíncrona para renovar tokens Instagram antes do vencimento."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from bot.config import InstagramSettings
from bot.integrations.instagram import (
    InstagramAPIError,
    InstagramAuthenticationError,
    InstagramTokenExpiredError,
    InstagramTokenRevokedError,
)
from bot.integrations.instagram_token_store import InstagramTokenStore, InstagramTokenStoreError
from bot.models import InstagramTokenData, InstagramTokenRefreshResult

logger = logging.getLogger(__name__)


class InstagramTokenRefreshClient(Protocol):
    """Parte do cliente Instagram necessária para a tarefa de renovação."""

    async def refresh_access_token(self, access_token: str) -> InstagramTokenRefreshResult:
        """Renova um token atual no endpoint oficial."""


class InstagramTokenRefreshTask:
    """Verifica e renova token uma vez por janela, sem derrubar o bot em falhas."""

    def __init__(
        self,
        settings: InstagramSettings,
        instagram_client: InstagramTokenRefreshClient,
        token_store: InstagramTokenStore,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._instagram_client = instagram_client
        self._token_store = token_store
        self._now = now or (lambda: datetime.now(UTC))
        self._task: asyncio.Task[None] | None = None
        self._refresh_lock = asyncio.Lock()
        self._last_attempt_at: datetime | None = None
        self._last_status: str | None = None

    @property
    def last_attempt_at(self) -> datetime | None:
        """Informa a última tentativa sem expor informações secretas."""
        return self._last_attempt_at

    @property
    def last_status(self) -> str | None:
        """Informa o resultado seguro mais recente da renovação."""
        return self._last_status

    def start(self) -> None:
        """Inicia uma única tarefa se Instagram e renovação automática estiverem ativos."""
        if (
            not self._settings.enabled
            or not self._settings.auto_refresh_token
            or (self._task is not None and not self._task.done())
        ):
            return
        self._task = asyncio.create_task(self._run(), name="instagram-token-refresh")
        logger.info("Renovação automática do token Instagram ativada.")

    async def stop(self) -> None:
        """Cancela e aguarda a tarefa para não deixar trabalho pendente no desligamento."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def check_once(self) -> None:
        """Recarrega, valida a janela e renova o token somente quando necessário."""
        if not self._settings.enabled or not self._settings.auto_refresh_token:
            return

        async with self._refresh_lock:
            now = self._now().astimezone(UTC)
            if self._last_attempt_at is not None and now - self._last_attempt_at < timedelta(
                hours=self._settings.token_refresh_check_interval_hours
            ):
                return

            try:
                token = await self._token_store.get_token()
            except InstagramTokenStoreError:
                self._last_attempt_at = now
                self._last_status = "storage_error"
                logger.exception("Não foi possível ler o token Instagram do armazenamento seguro.")
                return

            if token is None:
                self._last_attempt_at = now
                self._last_status = "missing_token"
                logger.warning(
                    "A autorização do Instagram precisa ser renovada. "
                    "Gere um novo token e atualize a configuração segura do bot."
                )
                return

            remaining = token.expires_at - now
            days_remaining = max(0, math.ceil(remaining.total_seconds() / 86400))
            logger.info("Token do Instagram expira em %d dia(s).", days_remaining)
            if remaining <= timedelta(0):
                self._last_attempt_at = now
                self._last_status = "expired"
                logger.warning(
                    "A autorização do Instagram precisa ser renovada. "
                    "Gere um novo token e atualize a configuração segura do bot."
                )
                return

            if remaining > timedelta(days=self._settings.token_refresh_days_before_expiry):
                self._last_status = "not_due"
                return

            self._last_attempt_at = now
            try:
                result = await self._instagram_client.refresh_access_token(token.access_token)
                await self._token_store.save_token(
                    InstagramTokenData(
                        access_token=result.access_token,
                        token_type=result.token_type,
                        expires_at=result.expires_at,
                        updated_at=now,
                    )
                )
            except (InstagramTokenExpiredError, InstagramTokenRevokedError):
                self._last_status = "reauthorization_required"
                logger.warning(
                    "A autorização do Instagram precisa ser renovada. "
                    "Gere um novo token e atualize a configuração segura do bot."
                )
            except InstagramAuthenticationError:
                self._last_status = "reauthorization_required"
                logger.warning(
                    "A autorização do Instagram precisa ser renovada. "
                    "Gere um novo token e atualize a configuração segura do bot."
                )
            except (InstagramAPIError, InstagramTokenStoreError):
                self._last_status = "refresh_error"
                logger.exception("Não foi possível renovar o token Instagram nesta verificação.")
            else:
                self._last_status = "refreshed"
                logger.info("Token do Instagram renovado com sucesso.")

    async def _run(self) -> None:
        """Executa verificações periódicas sem repetir em ciclo rápido após uma falha."""
        while True:
            try:
                await self.check_once()
                logger.info(
                    "Próxima verificação do token Instagram em %d hora(s).",
                    self._settings.token_refresh_check_interval_hours,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                self._last_status = "unexpected_error"
                logger.exception("Falha recuperável na tarefa de renovação do token Instagram.")
            await asyncio.sleep(self._settings.token_refresh_check_interval_hours * 3600)
