"""Testes isolados do sistema de cargos automáticos e por reação."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import discord
import pytest

from bot.cogs.role_management import RoleManagement
from bot.config import Settings


def discord_error(error_type: type[discord.HTTPException], status: int) -> discord.HTTPException:
    """Cria um erro Discord controlado sem realizar chamadas de rede."""
    response = SimpleNamespace(status=status, reason="Erro de teste", headers={})
    return error_type(response, "Erro de teste")


class FakeRole:
    """Cargo mínimo com ordenação de hierarquia do Discord."""

    def __init__(self, role_id: int, position: int, *, managed: bool = False) -> None:
        self.id = role_id
        self.position = position
        self.managed = managed

    def __lt__(self, other: object) -> bool:
        return isinstance(other, FakeRole) and self.position < other.position


class FakeMember:
    """Membro controlado que registra alterações de cargos."""

    def __init__(
        self, member_id: int, guild: FakeGuild, roles: list[FakeRole] | None = None
    ) -> None:
        self.id = member_id
        self.guild = guild
        self.roles = roles or []
        self.add_error: discord.HTTPException | None = None
        self.remove_error: discord.HTTPException | None = None

    async def add_roles(self, *roles: FakeRole, reason: str) -> None:
        if self.add_error is not None:
            raise self.add_error
        self.roles.extend(role for role in roles if role not in self.roles)

    async def remove_roles(self, *roles: FakeRole, reason: str) -> None:
        if self.remove_error is not None:
            raise self.remove_error
        self.roles = [role for role in self.roles if role not in roles]


class FakeGuild:
    """Guild com cache de cargos e membros."""

    def __init__(self, roles: list[FakeRole]) -> None:
        self.id = 1
        self._roles = {role.id: role for role in roles}
        self._members: dict[int, FakeMember] = {}
        self.me = SimpleNamespace(
            top_role=FakeRole(999, 100),
            guild_permissions=SimpleNamespace(manage_roles=True),
        )
        self.fetch_error: discord.HTTPException | None = None

    def get_role(self, role_id: int) -> FakeRole | None:
        return self._roles.get(role_id)

    def get_member(self, member_id: int) -> FakeMember | None:
        return self._members.get(member_id)

    async def fetch_member(self, member_id: int) -> FakeMember:
        if self.fetch_error is not None:
            raise self.fetch_error
        return self._members[member_id]


class FakeMessage:
    """Mensagem que registra remoções individuais de reação."""

    def __init__(self) -> None:
        self.removed: list[tuple[object, FakeMember]] = []
        self.added: list[str] = []

    async def remove_reaction(self, emoji: object, member: FakeMember) -> None:
        self.removed.append((emoji, member))

    async def add_reaction(self, emoji: str) -> None:
        self.added.append(emoji)


class FakeChannel:
    """Canal buscável mesmo fora do cache do cliente."""

    def __init__(self, message: FakeMessage) -> None:
        self.message = message
        self.fetch_error: discord.HTTPException | None = None

    async def fetch_message(self, message_id: int) -> FakeMessage:
        if self.fetch_error is not None:
            raise self.fetch_error
        return self.message


class FakeBot:
    """Cliente mínimo, sem conexão real ao Discord."""

    def __init__(self, guild: FakeGuild, channel: FakeChannel) -> None:
        self.user = SimpleNamespace(id=500)
        self._guild = guild
        self._channel = channel

    def get_guild(self, guild_id: int) -> FakeGuild | None:
        return self._guild if guild_id == self._guild.id else None

    def get_channel(self, channel_id: int) -> FakeChannel:
        return self._channel

    async def fetch_channel(self, channel_id: int) -> FakeChannel:
        return self._channel


def role_settings(environment: Callable[[], dict[str, str]]) -> Settings:
    """Retorna os menus de idade e pronomes com IDs e emojis Unicode."""
    values = environment()
    values.update(
        {
            "DISCORD_AUTO_ROLE_ID": "10",
            "DISCORD_ROLE_MENU_CHANNEL_ID": "20",
            "DISCORD_AGE_ROLE_MESSAGE_ID": "30",
            "DISCORD_PRONOUN_ROLE_MESSAGE_ID": "32",
            "DISCORD_ROLE_AGE_PLUS_18_ID": "11",
            "DISCORD_ROLE_AGE_MINUS_18_ID": "12",
            "DISCORD_ROLE_PRONOUN_SHE_HER_ID": "15",
            "DISCORD_ROLE_PRONOUN_HE_HIM_ID": "16",
            "DISCORD_ROLE_PRONOUN_ELU_DELU_ID": "17",
            "DISCORD_ROLE_PRONOUN_ANY_ID": "18",
            "DISCORD_ROLE_PRONOUN_PREFER_NOT_TO_INFORM_ID": "19",
        }
    )
    return Settings.from_environment(values)


def role_cog(
    environment: Callable[[], dict[str, str]],
) -> tuple[RoleManagement, FakeGuild, FakeChannel]:
    """Cria o cog em memória, sem instanciar outro cliente Discord."""
    roles = [FakeRole(role_id, position=role_id) for role_id in range(10, 20)]
    guild = FakeGuild(roles)
    channel = FakeChannel(FakeMessage())
    bot = FakeBot(guild, channel)
    return RoleManagement(bot, role_settings(environment)), guild, channel  # type: ignore[arg-type]


def payload(message_id: int, emoji: str, *, member_id: int = 60) -> SimpleNamespace:
    """Cria um payload raw compatível com os atributos usados pelo cog."""
    return SimpleNamespace(
        guild_id=1,
        channel_id=20,
        message_id=message_id,
        user_id=member_id,
        member=None,
        emoji=SimpleNamespace(id=None, __str__=lambda self: emoji),
    )


class UnicodeEmoji:
    """Emoji Unicode que implementa a conversão usada pelo payload real."""

    def __init__(self, value: str) -> None:
        self.id = None
        self.value = value

    def __str__(self) -> str:
        return self.value


def raw_payload(message_id: int, emoji: str, *, member_id: int = 60) -> SimpleNamespace:
    """Cria payload com emoji de texto confiável."""
    value = payload(message_id, emoji, member_id=member_id)
    value.emoji = UnicodeEmoji(emoji)
    return value


@pytest.mark.asyncio
async def test_member_join_assigns_auto_role(environment: Callable[[], dict[str, str]]) -> None:
    """O membro novo recebe apenas o cargo inicial configurado."""
    cog, guild, _ = role_cog(environment)
    member = FakeMember(60, guild)

    await cog.on_member_join(member)  # type: ignore[arg-type]

    assert [role.id for role in member.roles] == [10]


@pytest.mark.asyncio
async def test_ready_adds_configured_emojis_to_existing_messages(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O bot completa as reações dos menus configurados sem depender do cache."""
    cog, _, channel = role_cog(environment)

    await cog.on_ready()
    await cog.on_ready()

    assert channel.message.added == ["🔞", "🔓", "🌙", "🌞", "⭐", "✨", "❔"]


@pytest.mark.asyncio
async def test_member_join_ignores_existing_or_unassignable_auto_role(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Cargo existente e cargo acima do bot não são alterados."""
    cog, guild, _ = role_cog(environment)
    auto_role = guild.get_role(10)
    assert auto_role is not None
    existing_member = FakeMember(60, guild, [auto_role])
    await cog.on_member_join(existing_member)  # type: ignore[arg-type]
    assert existing_member.roles == [auto_role]

    auto_role.position = 101
    new_member = FakeMember(61, guild)
    await cog.on_member_join(new_member)  # type: ignore[arg-type]
    assert new_member.roles == []


@pytest.mark.asyncio
async def test_age_reaction_toggles_and_removes_reaction(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Reagir adiciona; reagir novamente remove o mesmo cargo exclusivo."""
    cog, guild, channel = role_cog(environment)
    member = FakeMember(60, guild)
    guild._members[member.id] = member
    event = raw_payload(30, "🔞")

    await cog.on_raw_reaction_add(event)  # type: ignore[arg-type]
    assert [role.id for role in member.roles] == [11]
    assert len(channel.message.removed) == 1

    await cog.on_raw_reaction_add(event)  # type: ignore[arg-type]
    assert member.roles == []
    assert len(channel.message.removed) == 2


@pytest.mark.asyncio
async def test_exclusive_age_replaces_the_previous_role(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A escolha -18 substitui +18 e nunca deixa ambos no membro."""
    cog, guild, _ = role_cog(environment)
    plus_18 = guild.get_role(11)
    assert plus_18 is not None
    member = FakeMember(60, guild, [plus_18])
    guild._members[member.id] = member

    await cog.on_raw_reaction_add(raw_payload(30, "🔓"))  # type: ignore[arg-type]

    assert [role.id for role in member.roles] == [12]


@pytest.mark.asyncio
async def test_nonexclusive_pronouns_keep_multiple_roles(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Pronomes não exclusivos permitem adicionar e remover opções independentemente."""
    cog, guild, _ = role_cog(environment)
    member = FakeMember(60, guild)
    guild._members[member.id] = member

    await cog.on_raw_reaction_add(raw_payload(32, "🌙"))  # type: ignore[arg-type]
    await cog.on_raw_reaction_add(raw_payload(32, "✨"))  # type: ignore[arg-type]
    assert {role.id for role in member.roles} == {15, 18}
    await cog.on_raw_reaction_add(raw_payload(32, "🌙"))  # type: ignore[arg-type]
    assert [role.id for role in member.roles] == [18]


@pytest.mark.asyncio
async def test_unknown_events_and_bot_reactions_are_ignored(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Canal, mensagem, emoji e bot fora do mapa jamais recebem cargos."""
    cog, guild, channel = role_cog(environment)
    member = FakeMember(60, guild)
    guild._members[member.id] = member
    events = [
        SimpleNamespace(**{**raw_payload(30, "🔞").__dict__, "channel_id": 99}),
        raw_payload(99, "🔞"),
        raw_payload(30, "❌"),
        raw_payload(30, "🔞", member_id=500),
    ]
    for event in events:
        await cog.on_raw_reaction_add(event)  # type: ignore[arg-type]
    assert member.roles == []
    assert channel.message.removed == []


@pytest.mark.asyncio
async def test_member_is_fetched_and_reaction_stays_after_role_failure(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Cache ausente usa fetch_member e falha de permissão preserva a reação."""
    cog, guild, channel = role_cog(environment)
    member = FakeMember(60, guild)
    member.add_error = discord_error(discord.Forbidden, 403)
    guild._members[member.id] = member

    await cog.on_raw_reaction_add(raw_payload(30, "🔞"))  # type: ignore[arg-type]

    assert member.roles == []
    assert channel.message.removed == []
