"""Extração segura de URLs temporárias de áudio do YouTube, sem downloads."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

MAX_YOUTUBE_URL_LENGTH = 2_048
YOUTUBE_HOSTS = frozenset(
    {"youtube.com", "www.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}
)
YTDL_OPTIONS: dict[str, object] = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "socket_timeout": 15,
}


class YouTubeAudioError(RuntimeError):
    """Indica uma falha segura durante extração de áudio."""


@dataclass(frozen=True, slots=True)
class YouTubeAudio:
    """Metadados públicos e URL temporária usada somente pelo FFmpeg."""

    stream_url: str
    title: str
    webpage_url: str
    duration: int | None


def is_valid_youtube_url(value: str) -> bool:
    """Aceita somente links públicos de vídeo, sem playlists ou pesquisa por texto."""
    url = value.strip()
    if not url or len(url) > MAX_YOUTUBE_URL_LENGTH:
        return False
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or hostname not in YOUTUBE_HOSTS:
        return False
    if parsed.username or parsed.password or parsed.port is not None:
        return False
    query = parse_qs(parsed.query)
    if "list" in query:
        return False
    if hostname in {"youtu.be", "www.youtu.be"}:
        return bool(parsed.path.strip("/"))
    return bool(query.get("v") or parsed.path.startswith("/shorts/"))


class YouTubeAudioService:
    """Obtém stream temporário em uma thread, preservando o event loop do bot."""

    def __init__(self, extractor_factory: Callable[[dict[str, object]], Any] | None = None) -> None:
        self._extractor_factory = extractor_factory

    async def get_audio_source(self, url: str) -> YouTubeAudio:
        """Extrai metadados e uma URL de áudio sem gravar arquivos em disco."""
        try:
            return await asyncio.to_thread(self._extract, url)
        except YouTubeAudioError:
            raise
        except Exception as error:
            logger.warning(
                "Falha inesperada ao extrair áudio do host %s: %s.",
                self._host(url),
                type(error).__name__,
            )
            raise YouTubeAudioError("Não foi possível extrair o áudio do vídeo.") from None

    def _extract(self, url: str) -> YouTubeAudio:
        """Executa a parte bloqueante do yt-dlp fora do loop assíncrono."""
        try:
            factory = self._extractor_factory or self._default_extractor_factory()
            with factory(YTDL_OPTIONS) as extractor:
                payload = extractor.extract_info(url, download=False)
        except Exception as error:
            logger.warning(
                "yt-dlp recusou um vídeo do host %s: %s.", self._host(url), type(error).__name__
            )
            raise YouTubeAudioError("Não foi possível obter áudio desse vídeo.") from None

        if not isinstance(payload, dict) or not isinstance(payload.get("url"), str):
            raise YouTubeAudioError("O vídeo não forneceu uma fonte de áudio compatível.")
        title = payload.get("title")
        webpage_url = payload.get("webpage_url")
        duration = payload.get("duration")
        return YouTubeAudio(
            stream_url=payload["url"],
            title=title if isinstance(title, str) and title else "Áudio sem título",
            webpage_url=webpage_url if isinstance(webpage_url, str) else url,
            duration=duration if isinstance(duration, int) else None,
        )

    @staticmethod
    def _default_extractor_factory() -> Callable[[dict[str, object]], Any]:
        """Importa yt-dlp apenas quando a integração for efetivamente usada."""
        try:
            import yt_dlp
        except ImportError as error:
            raise YouTubeAudioError("yt-dlp não está instalado no servidor.") from error
        return yt_dlp.YoutubeDL

    @staticmethod
    def _host(url: str) -> str:
        """Retorna somente o host, seguro para logs."""
        return (urlparse(url).hostname or "desconhecido").lower()
