"""Testes da mensagem privada de boas-vindas, sem conexão com o Discord."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import discord
import pytest
from discord import app_commands

from bot.cogs.general import General
from bot.config import Settings
from bot.errors import handle_app_command_error
from bot.integrations.discord_sender import DiscordNotificationError, DiscordNotificationSender


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Cria uma exceção HTTP do discord.py sem realizar uma requisição."""
    response = SimpleNamespace(status=status, reason="Erro de teste", headers={})
    return error_type(response, "Erro de teste")


class FakeNamedChannel:
    """Representa apenas a parte de um canal usada na mensagem."""

    def __init__(self, name: str) -> None:
        self.name = name


class FakeWelcomeClient:
    """Cliente conectado de mentira, com cache e busca remota controláveis."""

    def __init__(
        self,
        cached_channels: dict[int, object] | None = None,
        fetched_channels: dict[int, object] | None = None,
    ) -> None:
        self._cached_channels = cached_channels or {}
        self._fetched_channels = fetched_channels or {}
        self.fetch_calls: list[int] = []

    def get_channel(self, channel_id: int) -> object | None:
        return self._cached_channels.get(channel_id)

    async def fetch_channel(self, channel_id: int) -> object:
        self.fetch_calls.append(channel_id)
        channel = self._fetched_channels.get(channel_id)
        if channel is None:
            raise discord_error(discord.NotFound, 404)
        return channel


class FakeWelcomeUser:
    """Usuário que registra DMs e pode simular bloqueio de mensagens privadas."""

    def __init__(
        self,
        display_name: str = "Lestat",
        send_error: discord.HTTPException | None = None,
    ) -> None:
        self.display_name = display_name
        self.name = "usuario-teste"
        self._send_error = send_error
        self.messages: list[str] = []

    async def send(self, content: str, **_: object) -> None:
        if self._send_error is not None:
            raise self._send_error
        self.messages.append(content)


class FakeInteractionResponse:
    """Captura respostas de um comando slash."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    def is_done(self) -> bool:
        return False

    async def send_message(self, content: str, *, ephemeral: bool = False) -> None:
        self.messages.append((content, ephemeral))


class FakeInteraction:
    """Interação mínima para testar a proteção local do comando."""

    def __init__(self, *, manage_guild: bool) -> None:
        self.permissions = SimpleNamespace(manage_guild=manage_guild)
        self.response = FakeInteractionResponse()
        self.command = None


class RecordingSender:
    """Remetente injetado no cog para verificar se a DM seria disparada."""

    def __init__(self) -> None:
        self.users: list[object] = []

    async def send_welcome_message(self, user: object) -> None:
        self.users.append(user)


def welcome_environment(environment: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Inclui os dois IDs de canal utilizados na mensagem de boas-vindas."""
    values = environment()
    values["DISCORD_NOTIFICATION_CHANNEL_ID"] = "100000000000000001"
    values["DISCORD_INSTAGRAM_CHANNEL_ID"] = "200000000000000002"
    return values


@pytest.mark.asyncio
async def test_welcome_message_uses_display_name_and_current_channel_names(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A DM usa display_name e nomes resolvidos pelo ID configurado."""
    settings = Settings.from_environment(welcome_environment(environment))
    twitch_channel = FakeNamedChannel("lives-do-vampirao")
    instagram_channel = FakeNamedChannel("posts-do-vampirao")
    client = FakeWelcomeClient(
        {
            settings.twitch.notification_channel_id: twitch_channel,
            settings.instagram.notification_channel_id: instagram_channel,
        }
    )
    sender = DiscordNotificationSender(client, settings)  # type: ignore[arg-type]
    user = FakeWelcomeUser(display_name="Lestat do Vampirão")

    await sender.send_welcome_message(user)  # type: ignore[arg-type]

    assert client.fetch_calls == []
    assert user.messages == [
        "Bem vindo ao servidor Lestat do Vampirão,\n\n"
        "Me chamo Morcegão e vou te manter por dentro de todas as novidades sobre o Vampirão,\n"
        "vou te avisar das lives pelo canal lives-do-vampirao e de posts novos pelo canal "
        "posts-do-vampirao, ambos no Discord O vampirão.\n"
        "Fique à vontade pra interagir com a comunidade e se divertir.",
        "PS: O tipo sanguíneo do O vampirão é O+",
    ]


@pytest.mark.asyncio
async def test_welcome_message_fetches_channel_and_uses_fallback_when_missing(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Canal fora do cache é buscado; se não existir, a DM mantém texto amigável."""
    settings = Settings.from_environment(welcome_environment(environment))
    twitch_channel_id = settings.twitch.notification_channel_id
    instagram_channel_id = settings.instagram.notification_channel_id
    assert twitch_channel_id is not None
    assert instagram_channel_id is not None
    client = FakeWelcomeClient(
        fetched_channels={twitch_channel_id: FakeNamedChannel("avisos-de-live")}
    )
    sender = DiscordNotificationSender(client, settings)  # type: ignore[arg-type]
    user = FakeWelcomeUser()

    await sender.send_welcome_message(user)  # type: ignore[arg-type]

    assert client.fetch_calls == [twitch_channel_id, instagram_channel_id]
    assert "canal avisos-de-live" in user.messages[0]
    assert "canal de anúncios do Instagram" in user.messages[0]


@pytest.mark.asyncio
async def test_welcome_message_handles_forbidden_direct_message(
    environment: Callable[[], dict[str, str]],
) -> None:
    """DM bloqueada não vaza detalhes do Discord e gera erro de domínio."""
    settings = Settings.from_environment(welcome_environment(environment))
    sender = DiscordNotificationSender(  # type: ignore[arg-type]
        FakeWelcomeClient(),
        settings,
    )
    user = FakeWelcomeUser(send_error=discord_error(discord.Forbidden, 403))

    with pytest.raises(DiscordNotificationError, match="bloqueado DMs"):
        await sender.send_welcome_message(user)  # type: ignore[arg-type]

    assert user.messages == []


@pytest.mark.asyncio
async def test_welcome_message_uses_fallback_without_fetching_optional_ids(
    environment: Callable[[], dict[str, str]],
) -> None:
    """IDs ausentes usam os textos de reserva sem uma busca inválida por ``None``."""
    values = environment()
    values["TWITCH_ENABLED"] = "false"
    values.pop("DISCORD_NOTIFICATION_CHANNEL_ID")
    settings = Settings.from_environment(values)
    client = FakeWelcomeClient()
    sender = DiscordNotificationSender(client, settings)  # type: ignore[arg-type]
    user = FakeWelcomeUser()

    await sender.send_welcome_message(user)  # type: ignore[arg-type]

    assert client.fetch_calls == []
    assert "canal de anúncios da Twitch" in user.messages[0]
    assert "canal de anúncios do Instagram" in user.messages[0]


@pytest.mark.asyncio
async def test_welcome_command_blocks_users_without_manage_guild() -> None:
    """A proteção local não dispara a DM quando o chamador não pode gerenciar o servidor."""
    sender = RecordingSender()
    cog = General(sender)  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=False)
    user = FakeWelcomeUser()

    await General.welcome_command.callback(cog, interaction, user)  # type: ignore[arg-type]

    assert sender.users == []
    assert interaction.response.messages == [
        (
            "Você precisa da permissão “Gerenciar servidor” para usar este comando.",
            True,
        )
    ]


@pytest.mark.asyncio
async def test_welcome_command_confirms_attempt_without_revealing_the_dm() -> None:
    """O administrador recebe confirmação pública, mas nunca o texto privado."""
    sender = RecordingSender()
    cog = General(sender)  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)
    user = FakeWelcomeUser()

    await General.welcome_command.callback(cog, interaction, user)  # type: ignore[arg-type]

    assert sender.users == [user]
    assert interaction.response.messages == [
        ("A tentativa de envio da mensagem de boas-vindas foi realizada.", False)
    ]


@pytest.mark.asyncio
async def test_missing_manage_guild_permission_has_a_safe_slash_command_response() -> None:
    """O handler do comando slash informa a ausência de permissão sem detalhes técnicos."""
    interaction = FakeInteraction(manage_guild=False)

    await handle_app_command_error(
        interaction,  # type: ignore[arg-type]
        app_commands.MissingPermissions(["manage_guild"]),
    )

    assert interaction.response.messages == [
        (
            "Você precisa da permissão “Gerenciar servidor” para usar este comando.",
            True,
        )
    ]
