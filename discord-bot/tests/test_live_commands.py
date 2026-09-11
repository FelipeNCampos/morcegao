"""Testes dos comandos slash de reenvio de live e lista de comandos."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import discord
import pytest

from bot.cogs.general import (
    MISSING_MANAGE_GUILD_PERMISSION_MESSAGE,
    NO_OPEN_TWITCH_LIVE_MESSAGE,
    TWITCH_RESEND_ERROR_MESSAGE,
    General,
)
from bot.current_twitch_live import CurrentTwitchLiveStore
from bot.integrations.discord_sender import DiscordNotificationError
from bot.integrations.twitch_auth import TwitchApiError
from bot.models import TwitchOnlineEvent, TwitchStream


class FakeNotificationSender:
    """Registra chamadas de reenvio sem enviar mensagens ao Discord."""

    def __init__(self, *, raises_error: bool = False) -> None:
        self.calls: list[tuple[TwitchOnlineEvent, TwitchStream]] = []
        self._raises_error = raises_error

    async def send_twitch_notification(
        self, event: TwitchOnlineEvent, stream: TwitchStream
    ) -> None:
        if self._raises_error:
            raise DiscordNotificationError("Falha de envio simulada.")
        self.calls.append((event, stream))


class FakeTwitchClient:
    """Retorna o estado atual da live sem acessar a API Twitch."""

    def __init__(self, stream: TwitchStream | TwitchApiError) -> None:
        self.stream = stream
        self.requested_user_ids: list[str] = []

    async def get_stream(self, broadcaster_user_id: str) -> TwitchStream:
        self.requested_user_ids.append(broadcaster_user_id)
        if isinstance(self.stream, TwitchApiError):
            raise self.stream
        return self.stream


class FakeInteractionResponse:
    """Captura a resposta inicial da interação slash."""

    def __init__(self) -> None:
        self.deferred: list[bool] = []
        self.messages: list[dict[str, object]] = []

    async def defer(self, *, ephemeral: bool) -> None:
        self.deferred.append(ephemeral)

    async def send_message(
        self,
        content: str | None = None,
        *,
        ephemeral: bool = False,
        embed: discord.Embed | None = None,
    ) -> None:
        self.messages.append({"content": content, "ephemeral": ephemeral, "embed": embed})


class FakeFollowup:
    """Captura as respostas posteriores ao defer."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    async def send(self, content: str, *, ephemeral: bool) -> None:
        self.messages.append((content, ephemeral))


class FakeInteraction:
    """Interação mínima para executar callbacks do cog diretamente."""

    def __init__(self, *, manage_guild: bool) -> None:
        self.permissions = SimpleNamespace(manage_guild=manage_guild)
        self.response = FakeInteractionResponse()
        self.followup = FakeFollowup()


def open_live() -> tuple[TwitchOnlineEvent, TwitchStream]:
    """Cria dados imutáveis de uma live que está efetivamente online."""
    event = TwitchOnlineEvent(
        message_id="event-1",
        event_type="stream.online",
        broadcaster_user_id="42",
        broadcaster_login="vampirao",
        broadcaster_name="O Vampirão",
        started_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        received_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    stream = TwitchStream(
        title="Live de teste",
        url="https://www.twitch.tv/vampirao",
        is_live=True,
    )
    return event, stream


@pytest.mark.asyncio
async def test_resend_live_sends_the_current_open_live_with_the_existing_sender() -> None:
    """O reenvio usa exatamente o evento e stream atuais no remetente compartilhado."""
    event, stream = open_live()
    state = CurrentTwitchLiveStore()
    await state.set_current(event, stream)
    sender = FakeNotificationSender()
    twitch_client = FakeTwitchClient(stream)
    cog = General(sender, state, twitch_client)  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert twitch_client.requested_user_ids == [event.broadcaster_user_id]
    assert sender.calls == [(event, stream)]
    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [
        ("A notificação da live de O Vampirão foi reenviada com sucesso.", True)
    ]


@pytest.mark.asyncio
async def test_resend_live_refuses_when_there_is_no_open_live() -> None:
    """Sem estado em memória não há envio ou consulta para descobrir uma live."""
    sender = FakeNotificationSender()
    cog = General(sender, CurrentTwitchLiveStore())  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert sender.calls == []
    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [(NO_OPEN_TWITCH_LIVE_MESSAGE, True)]


@pytest.mark.asyncio
async def test_resend_live_blocks_users_without_manage_guild() -> None:
    """O callback não inicia operação administrativa sem a permissão necessária."""
    event, stream = open_live()
    state = CurrentTwitchLiveStore()
    await state.set_current(event, stream)
    sender = FakeNotificationSender()
    cog = General(sender, state)  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=False)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert sender.calls == []
    assert interaction.response.deferred == []
    assert interaction.response.messages == [
        {
            "content": MISSING_MANAGE_GUILD_PERMISSION_MESSAGE,
            "ephemeral": True,
            "embed": None,
        }
    ]


@pytest.mark.asyncio
async def test_resend_live_refuses_a_live_that_the_twitch_api_reports_as_closed() -> None:
    """A confirmação da API limpa estado obsoleto e evita uma nova notificação."""
    event, stream = open_live()
    state = CurrentTwitchLiveStore()
    await state.set_current(event, stream)
    sender = FakeNotificationSender()
    closed_stream = TwitchStream(title=None, url=stream.url, is_live=False)
    cog = General(sender, state, FakeTwitchClient(closed_stream))  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert sender.calls == []
    assert await state.get_current() is None
    assert interaction.followup.messages == [(NO_OPEN_TWITCH_LIVE_MESSAGE, True)]


@pytest.mark.asyncio
async def test_resend_live_handles_discord_notification_error() -> None:
    """Falhas do remetente são ocultadas do administrador e mantêm o estado intacto."""
    event, stream = open_live()
    state = CurrentTwitchLiveStore()
    await state.set_current(event, stream)
    sender = FakeNotificationSender(raises_error=True)
    cog = General(sender, state, FakeTwitchClient(stream))  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert await state.get_current() is not None
    assert interaction.response.deferred == [True]
    assert interaction.followup.messages == [(TWITCH_RESEND_ERROR_MESSAGE, True)]


@pytest.mark.asyncio
async def test_resend_live_handles_twitch_validation_error() -> None:
    """Uma falha ao confirmar a liveness não resulta em reenvio inseguro."""
    event, stream = open_live()
    state = CurrentTwitchLiveStore()
    await state.set_current(event, stream)
    sender = FakeNotificationSender()
    cog = General(sender, state, FakeTwitchClient(TwitchApiError("Falha simulada")))  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.resend_live_command.callback(cog, interaction)  # type: ignore[arg-type]

    assert sender.calls == []
    assert interaction.followup.messages == [(TWITCH_RESEND_ERROR_MESSAGE, True)]


@pytest.mark.asyncio
async def test_commands_list_contains_all_and_only_registered_commands() -> None:
    """O embed é derivado dos comandos registrados e não inventa comandos inexistentes."""
    cog = General(FakeNotificationSender())  # type: ignore[arg-type]
    interaction = FakeInteraction(manage_guild=True)

    await General.commands_list.callback(cog, interaction)  # type: ignore[arg-type]

    response = interaction.response.messages[0]
    embed = response["embed"]
    assert isinstance(embed, discord.Embed)
    registered_names = [command.name for command in cog.get_app_commands()]
    field_names = {field.name for field in embed.fields}
    assert {f"/{name}" for name in registered_names} <= field_names
    assert {"/comandos", "/reenviar_live", "/boasvindas", "/ping", "/limpar"} == field_names
    assert "/inexistente" not in {field.name for field in embed.fields}
    assert "!inexistente" not in field_names
    limpar_field = next(field for field in embed.fields if field.name == "/limpar")
    assert "Limite: 100 mensagens por vez." in limpar_field.value
    assert response["ephemeral"] is False


@pytest.mark.asyncio
async def test_commands_list_explains_temporary_voice_channels_when_configured() -> None:
    """A ajuda apresenta o recurso de voz somente quando o canal criador está configurado."""
    cog = General(  # type: ignore[arg-type]
        FakeNotificationSender(),
        temporary_voice_creator_channel_id=123456789012345678,
    )
    interaction = FakeInteraction(manage_guild=True)

    await General.commands_list.callback(cog, interaction)  # type: ignore[arg-type]

    embed = interaction.response.messages[0]["embed"]
    assert isinstance(embed, discord.Embed)
    voice_field = next(field for field in embed.fields if field.name == "Canais temporários de voz")
    assert "movido automaticamente" in voice_field.value


def test_general_cog_does_not_register_duplicate_slash_commands() -> None:
    """Cada comando é declarado uma única vez no cog carregado pelo setup_hook."""
    cog = General(FakeNotificationSender())  # type: ignore[arg-type]
    command_names = [command.name for command in cog.get_app_commands()]

    assert len(command_names) == len(set(command_names))
    assert set(command_names) == {"ping", "boasvindas", "reenviar_live", "comandos", "limpar"}
