"""Testes da composição integrada sem conectar Discord, Twitch ou Uvicorn reais."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest

import bot.main as main_module
from bot.config import Settings


class FakeStore:
    """Store sem I/O para confirmar que a composição cria apenas uma instância."""

    instances: list[FakeStore] = []

    def __init__(self, *_: object, **__: object) -> None:
        self.initialize_calls = 0
        FakeStore.instances.append(self)

    async def initialize(self) -> None:
        self.initialize_calls += 1


class FakeBot:
    """Bot mínimo que permanece ativo até o desligamento coordenado."""

    instances: list[FakeBot] = []

    def __init__(self, *_: object, **__: object) -> None:
        self.closed = False
        self.started = False
        FakeBot.instances.append(self)

    async def start(self, _: str) -> None:
        self.started = True
        await asyncio.Event().wait()

    def is_closed(self) -> bool:
        return self.closed

    async def close(self) -> None:
        self.closed = True


class FakeServer:
    """Servidor que sinaliza startup e encerra, disparando o cleanup integrado."""

    instances: list[FakeServer] = []

    def __init__(self, _: object) -> None:
        self.started = True
        self.should_exit = False
        FakeServer.instances.append(self)

    async def serve(self) -> None:
        return None


@pytest.mark.asyncio
async def test_run_services_composes_single_bot_and_cleans_up_tasks(
    environment: Callable[[], dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Discord e web compartilham objetos criados uma vez e encerram coordenadamente."""
    FakeStore.instances.clear()
    FakeBot.instances.clear()
    FakeServer.instances.clear()

    async def no_twitch(_: Settings) -> None:
        return None

    monkeypatch.setattr(main_module, "NotificationStore", FakeStore)
    monkeypatch.setattr(main_module, "DiscordBot", FakeBot)
    monkeypatch.setattr(main_module.uvicorn, "Server", FakeServer)
    monkeypatch.setattr(main_module, "create_web_app", lambda *_, **__: object())
    monkeypatch.setattr(main_module, "_prepare_twitch_client", no_twitch)

    async def no_instagram(_: Settings) -> tuple[None, None]:
        return None, None

    monkeypatch.setattr(main_module, "_prepare_instagram_client", no_instagram)

    await main_module.run_services(Settings.from_environment(environment()))

    assert len(FakeStore.instances) == 1
    assert len(FakeBot.instances) == 1
    assert len(FakeServer.instances) == 1
    assert FakeBot.instances[0].closed is True
    assert FakeServer.instances[0].should_exit is True
