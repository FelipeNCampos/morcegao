"""Testes do ciclo de vida do validador periódico de token Twitch."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest

from bot.config import Settings
from bot.tasks.twitch_token_validator import TwitchTokenValidator


class FakeTwitchClient:
    """Cliente mínimo que registra validações sem chamadas HTTP."""

    def __init__(self) -> None:
        self.validations = 0

    async def ensure_valid_access_token(self) -> None:
        self.validations += 1


@pytest.mark.asyncio
async def test_validator_validates_once_and_stops_cleanly(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A tarefa pode ser iniciada uma vez e cancelada sem deixar trabalho pendente."""
    client = FakeTwitchClient()
    validator = TwitchTokenValidator(  # type: ignore[arg-type]
        Settings.from_environment(environment()).twitch,
        client,
    )

    await validator.validate_once()
    validator.start()
    validator.start()
    await asyncio.sleep(0)
    await validator.stop()

    assert client.validations == 1
