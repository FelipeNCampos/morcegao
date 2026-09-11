"""Armazenamento SQLite assíncrono para eventos de notificação."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from bot.models import InstagramMedia, TwitchOnlineEvent


class NotificationStore:
    """Persiste identificadores processados para evitar notificações duplicadas."""

    def __init__(self, database_path: Path, *, instagram_user_id: int | None = None) -> None:
        self._database_path = database_path
        self._instagram_user_id = str(instagram_user_id) if instagram_user_id is not None else ""

    async def initialize(self) -> None:
        """Cria as tabelas e índices necessários, caso ainda não existam."""
        await asyncio.to_thread(self._initialize_sync)

    async def register_twitch_event(self, event: TwitchOnlineEvent) -> bool:
        """Registra um evento EventSub e retorna se ele ainda não havia sido recebido."""
        return await asyncio.to_thread(self._register_twitch_event_sync, event)

    async def update_twitch_event_status(self, message_id: str, status: str) -> None:
        """Atualiza o estado de envio de uma notificação Twitch."""
        await asyncio.to_thread(self._update_twitch_event_status_sync, message_id, status)

    async def has_processed_instagram_media(self, media_id: str) -> bool:
        """Informa se uma mídia já foi conhecida ou notificada."""
        return await asyncio.to_thread(self._has_processed_instagram_media_sync, media_id)

    async def mark_instagram_media_processed(
        self, media: InstagramMedia, *, status: str = "notified"
    ) -> None:
        """Registra uma mídia depois de conhecida ou enviada com sucesso."""
        await asyncio.to_thread(self._mark_instagram_media_processed_sync, media, status)

    def _connect(self) -> sqlite3.Connection:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize_sync(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS twitch_events (
                    message_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    broadcaster_user_id TEXT NOT NULL,
                    broadcaster_login TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    processed_at TEXT,
                    status TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS instagram_media (
                    instagram_media_id TEXT PRIMARY KEY,
                    instagram_user_id TEXT NOT NULL,
                    instagram_username TEXT,
                    permalink TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    notified_at TEXT,
                    status TEXT NOT NULL
                )
                """
            )

    def _register_twitch_event_sync(self, event: TwitchOnlineEvent) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO twitch_events (
                    message_id, event_type, broadcaster_user_id,
                    broadcaster_login, received_at, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.message_id,
                    event.event_type,
                    event.broadcaster_user_id,
                    event.broadcaster_login,
                    event.received_at.isoformat(),
                    "received",
                ),
            )
            return cursor.rowcount == 1

    def _update_twitch_event_status_sync(self, message_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE twitch_events
                SET status = ?, processed_at = ?
                WHERE message_id = ?
                """,
                (status, datetime.now(UTC).isoformat(), message_id),
            )

    def _has_processed_instagram_media_sync(self, media_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM instagram_media WHERE instagram_media_id = ?", (media_id,)
            ).fetchone()
            return row is not None

    def _mark_instagram_media_processed_sync(self, media: InstagramMedia, status: str) -> None:
        detected_at = datetime.now(UTC).isoformat()
        notified_at = detected_at if status == "notified" else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO instagram_media (
                    instagram_media_id, instagram_user_id, instagram_username, permalink,
                    timestamp, detected_at, notified_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    media.media_id,
                    self._instagram_user_id,
                    media.username,
                    media.permalink,
                    media.timestamp.isoformat(),
                    detected_at,
                    notified_at,
                    status,
                ),
            )
