"""Estado em memória da última live Twitch confirmada como aberta."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bot.models import TwitchOnlineEvent, TwitchStream


@dataclass(frozen=True, slots=True)
class CurrentTwitchLive:
    """Combina o evento EventSub e os dados mais recentes de uma live aberta."""

    event: TwitchOnlineEvent
    stream: TwitchStream


class CurrentTwitchLiveStore:
    """Mantém uma única live atual com leituras e alterações consistentes.

    O conteúdo não é persistido. Portanto, ele é descartado ao reiniciar o bot.
    """

    def __init__(self) -> None:
        self._live: CurrentTwitchLive | None = None
        self._lock = asyncio.Lock()

    async def set_current(
        self,
        event: TwitchOnlineEvent,
        stream: TwitchStream,
    ) -> None:
        """Registra a live somente se a API Twitch a confirmou como online."""
        async with self._lock:
            self._live = CurrentTwitchLive(event, stream) if stream.is_live else None

    async def get_current(self) -> CurrentTwitchLive | None:
        """Retorna um instantâneo imutável da live atualmente aberta."""
        async with self._lock:
            return self._live

    async def clear_if_current(self, live: CurrentTwitchLive) -> bool:
        """Limpa o estado somente se ele ainda corresponder ao instantâneo recebido."""
        async with self._lock:
            if self._live != live:
                return False
            self._live = None
            return True

    async def update_stream_if_current(
        self,
        live: CurrentTwitchLive,
        stream: TwitchStream,
    ) -> CurrentTwitchLive | None:
        """Atualiza dados da live sem sobrescrever uma live que chegou depois.

        Retorna ``None`` quando a API a indicou como encerrada ou o instantâneo
        foi substituído concorrentemente.
        """
        async with self._lock:
            if self._live != live:
                return None
            if not stream.is_live:
                self._live = None
                return None
            self._live = CurrentTwitchLive(live.event, stream)
            return self._live
