"""Testes sem rede para validação e extração de áudio do YouTube."""

from __future__ import annotations

import threading

import pytest

from bot.integrations.youtube_audio import (
    YouTubeAudioError,
    YouTubeAudioService,
    is_valid_youtube_url,
)


class FakeExtractor:
    """Extrator controlado compatível com o context manager do yt-dlp."""

    def __init__(self, payload: dict[str, object] | Exception) -> None:
        self.payload = payload
        self.thread_id: int | None = None

    def __enter__(self) -> FakeExtractor:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def extract_info(self, url: str, *, download: bool) -> dict[str, object]:
        self.thread_id = threading.get_ident()
        assert download is False
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=abc", True),
        ("https://youtu.be/abc", True),
        ("https://music.youtube.com/watch?v=abc", True),
        ("https://www.youtube.com/watch?v=abc&list=playlist", True),
        (
            "https://www.youtube.com/watch?v=7eLC4LnddHk&list=RD7eLC4LnddHk"
            "&start_radio=1&rv=lbFl6ESBUGA",
            True,
        ),
        ("https://example.test/watch?v=abc", False),
        ("file:///tmp/audio.mp3", False),
        ("http://localhost/video", False),
        ("", False),
    ],
)
def test_youtube_url_validation(url: str, expected: bool) -> None:
    """Somente links públicos que apontem para um vídeo YouTube são aceitos."""
    assert is_valid_youtube_url(url) is expected


@pytest.mark.asyncio
async def test_audio_extraction_uses_worker_thread_and_exposes_only_public_metadata() -> None:
    """A extração não bloqueia o loop e retorna URL temporária apenas ao chamador interno."""
    extractor = FakeExtractor(
        {
            "url": "https://temporary-stream.example.test/signed",
            "title": "Vídeo de teste",
            "webpage_url": "https://www.youtube.com/watch?v=abc",
            "duration": 42,
        }
    )
    service = YouTubeAudioService(lambda _: extractor)

    audio = await service.get_audio_source("https://www.youtube.com/watch?v=abc")

    assert extractor.thread_id is not None
    assert extractor.thread_id != threading.get_ident()
    assert audio.title == "Vídeo de teste"
    assert audio.webpage_url == "https://www.youtube.com/watch?v=abc"
    assert audio.duration == 42


@pytest.mark.asyncio
async def test_audio_extraction_returns_safe_error_when_extractor_fails() -> None:
    """Falhas do yt-dlp não vazam detalhes do vídeo nem do stream."""
    service = YouTubeAudioService(lambda _: FakeExtractor(RuntimeError("falha privada")))

    with pytest.raises(YouTubeAudioError, match="áudio") as error:
        await service.get_audio_source("https://www.youtube.com/watch?v=abc")

    assert "privada" not in str(error.value)
