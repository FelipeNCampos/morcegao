"""Testes do bloqueio global de comandos slash por cargo."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from bot.command_access import COMMAND_REQUIRED_ROLE_MESSAGE, CommandAccessTree


class FakeResponse:
    """Resposta de interação observável sem conexão com o Discord."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    def is_done(self) -> bool:
        return False

    async def send_message(self, message: str, *, ephemeral: bool) -> None:
        self.messages.append((message, ephemeral))


def make_interaction(*, role_ids: list[int]) -> SimpleNamespace:
    """Cria o mínimo de uma interação em guild para validar autorização."""
    return SimpleNamespace(
        guild=SimpleNamespace(id=1),
        guild_id=1,
        user=SimpleNamespace(id=2, roles=[SimpleNamespace(id=role_id) for role_id in role_ids]),
        command=None,
        response=FakeResponse(),
    )


def test_required_role_allows_a_member_with_the_configured_role() -> None:
    """Membros autorizados executam comandos normalmente."""
    interaction = make_interaction(role_ids=[99])
    tree = SimpleNamespace(
        client=SimpleNamespace(settings=SimpleNamespace(command_required_role_id=99))
    )

    assert asyncio.run(CommandAccessTree.interaction_check(tree, interaction)) is True


def test_required_role_rejects_a_member_without_the_configured_role() -> None:
    """Membros sem o cargo recebem uma resposta efêmera e não executam o comando."""
    interaction = make_interaction(role_ids=[10])
    tree = SimpleNamespace(
        client=SimpleNamespace(settings=SimpleNamespace(command_required_role_id=99))
    )

    assert asyncio.run(CommandAccessTree.interaction_check(tree, interaction)) is False
    assert interaction.response.messages == [(COMMAND_REQUIRED_ROLE_MESSAGE, True)]
