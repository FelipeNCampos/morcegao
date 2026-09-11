"""Testes isolados dos canais de voz temporários."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from types import SimpleNamespace

import discord
import pytest

from bot.cogs.temporary_voice import TEMPORARY_VOICE_PREFIX, TemporaryVoice
from bot.config import Settings


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Constrói uma exceção Discord sem conexão externa."""
    response = SimpleNamespace(status=status, reason="Erro de teste", headers={})
    return error_type(response, "Erro de teste")


class FakeRole:
    """Role mínima usada para representar @everyone."""

    def __init__(self, role_id: int) -> None:
        self.id = role_id


class FakePrincipal:
    """Entidade hashable usada como o usuário do bot nos overwrites."""

    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeCategory:
    """Categoria que mantém os canais de voz criados no teste."""

    def __init__(self) -> None:
        self.voice_channels: list[FakeVoiceChannel] = []


class FakeVoiceChannel:
    """Canal de voz em memória, com participantes e exclusão controláveis."""

    def __init__(
        self,
        channel_id: int,
        guild: FakeGuild,
        *,
        category: FakeCategory | None,
        name: str,
        overwrites: dict[object, discord.PermissionOverwrite] | None = None,
        delete_error: discord.HTTPException | None = None,
    ) -> None:
        self.id = channel_id
        self.guild = guild
        self.category = category
        self.name = name
        self.overwrites = overwrites or {}
        self.members: list[FakeMember] = []
        self._delete_error = delete_error
        self.deleted = False

    async def delete(self, *, reason: str) -> None:
        if self._delete_error is not None:
            raise self._delete_error
        self.deleted = True
        self.guild.channels.pop(self.id, None)
        if self.category is not None and self in self.category.voice_channels:
            self.category.voice_channels.remove(self)


class FakeGuild:
    """Guild que cria canais de voz e registra os argumentos recebidos."""

    def __init__(self) -> None:
        self.id = 10
        self.default_role = FakeRole(0)
        self.channels: dict[int, FakeVoiceChannel] = {}
        self._next_channel_id = 100
        self.create_error: discord.HTTPException | None = None
        self.on_create: Callable[[], None] | None = None
        self.create_calls: list[dict[str, object]] = []

    @property
    def voice_channels(self) -> list[FakeVoiceChannel]:
        return list(self.channels.values())

    def get_channel(self, channel_id: int) -> FakeVoiceChannel | None:
        return self.channels.get(channel_id)

    async def create_voice_channel(
        self,
        *,
        name: str,
        category: FakeCategory | None,
        overwrites: dict[object, discord.PermissionOverwrite],
        reason: str,
    ) -> FakeVoiceChannel:
        self.create_calls.append(
            {
                "name": name,
                "category": category,
                "overwrites": overwrites,
                "reason": reason,
            }
        )
        if self.create_error is not None:
            raise self.create_error
        channel = FakeVoiceChannel(
            self._next_channel_id,
            self,
            category=category,
            name=name,
            overwrites=overwrites,
        )
        self._next_channel_id += 1
        self.channels[channel.id] = channel
        if category is not None:
            category.voice_channels.append(channel)
        if self.on_create is not None:
            self.on_create()
        return channel


class FakeVoiceState:
    """Estado de voz mínimo com o canal atual."""

    def __init__(self, channel: FakeVoiceChannel | None) -> None:
        self.channel = channel


class FakeMember:
    """Membro que pode ser movido ou sair durante a criação da sala."""

    def __init__(
        self,
        member_id: int,
        display_name: str,
        channel: FakeVoiceChannel | None,
        *,
        move_error: discord.HTTPException | None = None,
    ) -> None:
        self.id = member_id
        self.display_name = display_name
        self.bot = False
        self.voice = FakeVoiceState(channel) if channel is not None else None
        self._move_error = move_error
        self.move_calls: list[tuple[object, str]] = []
        if channel is not None:
            channel.members.append(self)

    async def move_to(self, channel: FakeVoiceChannel, *, reason: str) -> None:
        self.move_calls.append((channel, reason))
        if self._move_error is not None:
            raise self._move_error
        if self.voice is not None and self in self.voice.channel.members:
            self.voice.channel.members.remove(self)
        channel.members.append(self)
        self.voice = FakeVoiceState(channel)


class FakeBot:
    """Cliente existente simulado, sem criar outra instância Discord real."""

    def __init__(self, channels: dict[int, FakeVoiceChannel]) -> None:
        self.user = FakePrincipal(999)
        self._channels = channels

    def get_channel(self, channel_id: int) -> FakeVoiceChannel | None:
        return self._channels.get(channel_id)

    async def fetch_channel(self, channel_id: int) -> FakeVoiceChannel:
        channel = self._channels.get(channel_id)
        if channel is None:
            raise discord_error(discord.NotFound, 404)
        return channel


def temporary_voice_settings(environment: Callable[[], dict[str, str]]) -> Settings:
    """Retorna Settings com o canal criador apontando para o ID do fake."""
    values = environment()
    values["DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID"] = "1"
    return Settings.from_environment(values)


def build_voice_fixture(
    environment: Callable[[], dict[str, str]],
) -> tuple[TemporaryVoice, FakeGuild, FakeVoiceChannel, FakeCategory]:
    """Monta cog, guild, canal criador e categoria para os cenários de voz."""
    guild = FakeGuild()
    category = FakeCategory()
    creator = FakeVoiceChannel(1, guild, category=category, name="Criar sala")
    guild.channels[creator.id] = creator
    category.voice_channels.append(creator)
    bot = FakeBot(guild.channels)
    return TemporaryVoice(bot, temporary_voice_settings(environment)), guild, creator, category  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_entering_creator_creates_moves_and_grants_owner_permissions(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Entrada no criador cria sala na categoria certa e move o proprietário."""
    cog, guild, creator, category = build_voice_fixture(environment)
    member = FakeMember(20, "  Conde   Drácula  ", creator)

    await cog.on_voice_state_update(  # type: ignore[arg-type]
        member,
        FakeVoiceState(None),
        FakeVoiceState(creator),
    )

    assert len(guild.create_calls) == 1
    created_channel = guild.get_channel(100)
    assert created_channel is not None
    assert guild.create_calls[0]["category"] is category
    assert created_channel.name == "🔊 Sala de Conde Drácula"
    assert member.move_calls[0][0] is created_channel
    owner_overwrite = created_channel.overwrites[member]
    assert owner_overwrite.manage_channels is True
    assert owner_overwrite.administrator is None
    assert guild.default_role not in created_channel.overwrites


@pytest.mark.asyncio
async def test_concurrent_creator_events_do_not_create_two_rooms(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O lock da guild impede duas salas para o mesmo membro."""
    cog, guild, creator, _ = build_voice_fixture(environment)
    member = FakeMember(20, "Conde", creator)

    await asyncio.gather(
        cog.on_voice_state_update(member, FakeVoiceState(None), FakeVoiceState(creator)),  # type: ignore[arg-type]
        cog.on_voice_state_update(member, FakeVoiceState(None), FakeVoiceState(creator)),  # type: ignore[arg-type]
    )

    assert len(guild.create_calls) == 1


@pytest.mark.asyncio
async def test_user_leaving_during_creation_removes_the_orphan_channel(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Se o membro sair antes do move, o canal recém-criado é removido."""
    cog, guild, creator, _ = build_voice_fixture(environment)
    member = FakeMember(20, "Conde", creator)

    def leave_creator() -> None:
        creator.members.remove(member)
        member.voice = None

    guild.on_create = leave_creator
    await cog.on_voice_state_update(  # type: ignore[arg-type]
        member,
        FakeVoiceState(None),
        FakeVoiceState(creator),
    )

    assert guild.get_channel(100) is None
    assert cog._temporary_channels == {}


@pytest.mark.asyncio
async def test_empty_temporary_channel_is_deleted_but_creator_is_preserved(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Somente salas registradas e vazias podem ser removidas."""
    cog, guild, creator, category = build_voice_fixture(environment)
    temporary = FakeVoiceChannel(100, guild, category=category, name="🔊 Sala de Conde")
    guild.channels[temporary.id] = temporary
    category.voice_channels.append(temporary)
    cog._register_channel(temporary.id, 20, guild.id)
    cog._register_channel(creator.id, 21, guild.id)

    await cog._delete_if_empty(temporary)  # type: ignore[arg-type]
    await cog._delete_if_empty(creator)  # type: ignore[arg-type]

    assert temporary.deleted is True
    assert creator.deleted is False


@pytest.mark.asyncio
async def test_occupied_temporary_channel_is_not_deleted(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A presença de qualquer membro impede a exclusão automática."""
    cog, guild, creator, category = build_voice_fixture(environment)
    temporary = FakeVoiceChannel(100, guild, category=category, name="🔊 Sala de Conde")
    guild.channels[temporary.id] = temporary
    category.voice_channels.append(temporary)
    FakeMember(20, "Conde", temporary)
    cog._register_channel(temporary.id, 20, guild.id)

    await cog._delete_if_empty(temporary)  # type: ignore[arg-type]

    assert temporary.deleted is False
    assert 100 in cog._temporary_channels


@pytest.mark.asyncio
async def test_creation_and_move_permission_errors_do_not_leave_orphans(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Falhas de criação ou movimento não criam registros ou salas inúteis."""
    cog, guild, creator, _ = build_voice_fixture(environment)
    guild.create_error = discord_error(discord.Forbidden, 403)
    member = FakeMember(20, "Conde", creator)

    await cog.on_voice_state_update(  # type: ignore[arg-type]
        member,
        FakeVoiceState(None),
        FakeVoiceState(creator),
    )
    assert cog._temporary_channels == {}

    guild.create_error = None
    member._move_error = discord_error(discord.Forbidden, 403)
    await cog.on_voice_state_update(  # type: ignore[arg-type]
        member,
        FakeVoiceState(None),
        FakeVoiceState(creator),
    )
    assert guild.get_channel(100) is None
    assert cog._temporary_channels == {}


@pytest.mark.asyncio
async def test_delete_permission_error_keeps_tracking_for_a_later_voice_event(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Uma falha de exclusão não remove o registro nem cria um loop de tentativas."""
    cog, guild, _, category = build_voice_fixture(environment)
    temporary = FakeVoiceChannel(
        100,
        guild,
        category=category,
        name="🔊 Sala de Conde",
        delete_error=discord_error(discord.Forbidden, 403),
    )
    guild.channels[temporary.id] = temporary
    cog._register_channel(temporary.id, 20, guild.id)

    await cog._delete_if_empty(temporary)  # type: ignore[arg-type]

    assert temporary.deleted is False
    assert 100 in cog._temporary_channels


@pytest.mark.asyncio
async def test_recovery_uses_category_prefix_and_owner_overwrite(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Depois de reiniciar, somente salas com as três marcas esperadas são recuperadas."""
    cog, guild, creator, category = build_voice_fixture(environment)
    owner = FakeMember(20, "Conde", None)
    temporary = FakeVoiceChannel(
        100,
        guild,
        category=category,
        name=f"{TEMPORARY_VOICE_PREFIX}Conde",
        overwrites={
            owner: discord.PermissionOverwrite(manage_channels=True),
            cog._bot.user: discord.PermissionOverwrite(manage_channels=True),
        },
    )
    permanent = FakeVoiceChannel(
        101,
        guild,
        category=category,
        name=f"{TEMPORARY_VOICE_PREFIX}Permanente",
    )
    occupied = FakeMember(30, "Visitante", temporary)
    assert occupied.voice is not None
    guild.channels[temporary.id] = temporary
    guild.channels[permanent.id] = permanent
    category.voice_channels.extend([temporary, permanent])

    async def creator_channel() -> FakeVoiceChannel:
        return creator

    cog._get_creator_channel = creator_channel  # type: ignore[method-assign]
    await cog._cleanup_or_recover_temporary_channels()

    assert cog._owner_channels[(guild.id, owner.id)] == temporary.id
    assert permanent.id not in cog._temporary_channels


@pytest.mark.asyncio
async def test_recovery_deletes_an_empty_recognized_temporary_channel(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A recuperação remove lixo vazio sem tocar no canal criador."""
    cog, guild, creator, category = build_voice_fixture(environment)
    owner = FakeMember(20, "Conde", None)
    temporary = FakeVoiceChannel(
        100,
        guild,
        category=category,
        name=f"{TEMPORARY_VOICE_PREFIX}Conde",
        overwrites={owner: discord.PermissionOverwrite(manage_channels=True)},
    )
    guild.channels[temporary.id] = temporary
    category.voice_channels.append(temporary)

    async def creator_channel() -> FakeVoiceChannel:
        return creator

    cog._get_creator_channel = creator_channel  # type: ignore[method-assign]
    await cog._cleanup_or_recover_temporary_channels()

    assert temporary.deleted is True
    assert cog._temporary_channels == {}
