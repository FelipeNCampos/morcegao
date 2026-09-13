"""Testes sem Discord, FFmpeg ou YouTube reais para os comandos de música."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import bot.cogs.music as music_module
from bot.cogs.music import Music
from bot.integrations.youtube_audio import YouTubeAudio


class FakeResponse:
    """Registra respostas iniciais de uma interaction."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []
        self.deferred = False

    async def send_message(self, message: str, *, ephemeral: bool) -> None:
        self.messages.append((message, ephemeral))

    async def defer(self) -> None:
        self.deferred = True


class FakeFollowup:
    """Registra mensagens posteriores ao defer."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    async def send(self, message: str, *, ephemeral: bool = False) -> None:
        self.messages.append((message, ephemeral))


class FakeVoiceClient:
    """Cliente de voz controlável que não reproduz áudio real."""

    def __init__(self, channel: FakeVoiceChannel) -> None:
        self.channel = channel
        self.playing = False
        self.paused = False
        self.stopped = 0
        self.played: list[object] = []
        self.moved_to: list[FakeVoiceChannel] = []
        self.disconnected = False

    def is_playing(self) -> bool:
        return self.playing

    def is_paused(self) -> bool:
        return self.paused

    def stop(self) -> None:
        self.stopped += 1
        self.playing = False
        self.paused = False

    def play(self, source: object, *, after: object) -> None:
        self.played.append(source)
        self.playing = True

    async def move_to(self, channel: FakeVoiceChannel) -> None:
        self.channel = channel
        self.moved_to.append(channel)

    async def disconnect(self, *, force: bool) -> None:
        self.disconnected = True


class FakeVoiceChannel:
    """Canal de voz com conexão local controlada."""

    def __init__(self, channel_id: int) -> None:
        self.id = channel_id
        self.mention = f"<#${channel_id}>"
        self.members: list[FakeMember] = []
        self.connected_client: FakeVoiceClient | None = None

    async def connect(self, *, self_deaf: bool) -> FakeVoiceClient:
        assert self_deaf is True
        self.connected_client = FakeVoiceClient(self)
        return self.connected_client


class MissingPyNaClChannel(FakeVoiceChannel):
    """Canal que simula a ausência da dependência de voz no host."""

    async def connect(self, *, self_deaf: bool) -> FakeVoiceClient:
        raise RuntimeError("PyNaCl library needed in order to use voice")


class FakeMember:
    """Membro compatível com a checagem de estado de voz do cog."""

    def __init__(self, channel: FakeVoiceChannel | None) -> None:
        self.id = 20
        self.mention = "@membro"
        self.bot = False
        self.voice = SimpleNamespace(channel=channel) if channel is not None else None


class FakeGuild:
    """Guild mínima com apenas um cliente de voz."""

    def __init__(self, voice_client: FakeVoiceClient | None = None) -> None:
        self.id = 10
        self.voice_client = voice_client


class FakeInteraction:
    """Interaction de servidor usada pelos callbacks slash."""

    def __init__(self, guild: FakeGuild | None, member: FakeMember) -> None:
        self.guild = guild
        self.user = member
        self.response = FakeResponse()
        self.followup = FakeFollowup()


class FakeBot:
    """Bot que resolve a única guild de teste."""

    def __init__(self, guild: FakeGuild) -> None:
        self._guild = guild

    def get_guild(self, guild_id: int) -> FakeGuild | None:
        return self._guild if guild_id == self._guild.id else None


class FakeAudioService:
    """Serviço que entrega metadados sem chamar yt-dlp."""

    async def get_audio_source(self, url: str) -> YouTubeAudio:
        return YouTubeAudio("https://temporary.example/audio", "Faixa", url, 10)


def music_cog(guild: FakeGuild) -> Music:
    """Cria o cog com timeout curto e serviço de áudio fake."""
    settings = SimpleNamespace(music_idle_disconnect_seconds=1)
    return Music(FakeBot(guild), settings, FakeAudioService())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_play_requires_member_in_voice_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    """O bot não conecta quando o solicitante não está em uma call."""
    monkeypatch.setattr(music_module.discord, "Member", FakeMember)
    guild = FakeGuild()
    interaction = FakeInteraction(guild, FakeMember(None))

    await Music.play_youtube.callback(music_cog(guild), interaction, "https://youtu.be/abc")  # type: ignore[arg-type]

    assert interaction.response.messages == [
        ("Você precisa estar em um canal de voz para usar este comando.", True)
    ]


@pytest.mark.asyncio
async def test_play_connects_and_replaces_current_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uma nova solicitação conecta e interrompe a faixa anterior de modo previsível."""
    monkeypatch.setattr(music_module.discord, "Member", FakeMember)
    channel = FakeVoiceChannel(30)
    current_client = FakeVoiceClient(channel)
    current_client.playing = True
    guild = FakeGuild(current_client)
    interaction = FakeInteraction(guild, FakeMember(channel))
    monkeypatch.setattr(music_module.discord, "FFmpegPCMAudio", lambda *_args, **_kwargs: object())

    await Music.play_youtube.callback(
        music_cog(guild), interaction, "https://www.youtube.com/watch?v=abc"
    )  # type: ignore[arg-type]

    assert interaction.response.deferred is True
    assert current_client.stopped == 1
    assert len(current_client.played) == 1
    assert "Faixa" in interaction.followup.messages[0][0]
    assert "temporary.example" not in interaction.followup.messages[0][0]


@pytest.mark.asyncio
async def test_play_reports_missing_pynacl_without_propagating_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ausência de PyNaCl gera uma resposta segura e não derruba o comando."""
    monkeypatch.setattr(music_module.discord, "Member", FakeMember)
    channel = MissingPyNaClChannel(35)
    guild = FakeGuild()
    interaction = FakeInteraction(guild, FakeMember(channel))

    await Music.play_youtube.callback(music_cog(guild), interaction, "https://youtu.be/abc")  # type: ignore[arg-type]

    assert interaction.followup.messages == [
        ("O servidor do bot não possui o PyNaCl configurado para reprodução de áudio.", True)
    ]


@pytest.mark.asyncio
async def test_play_moves_only_to_requester_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Conexão existente é movida para a call do solicitante antes de tocar."""
    monkeypatch.setattr(music_module.discord, "Member", FakeMember)
    old_channel = FakeVoiceChannel(31)
    new_channel = FakeVoiceChannel(32)
    voice_client = FakeVoiceClient(old_channel)
    guild = FakeGuild(voice_client)
    interaction = FakeInteraction(guild, FakeMember(new_channel))
    monkeypatch.setattr(music_module.discord, "FFmpegPCMAudio", lambda *_args, **_kwargs: object())

    await Music.play_youtube.callback(music_cog(guild), interaction, "https://youtu.be/abc")  # type: ignore[arg-type]

    assert voice_client.moved_to == [new_channel]


@pytest.mark.asyncio
async def test_stop_and_leave_require_same_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parar e sair nunca permitem controlar uma call alheia."""
    monkeypatch.setattr(music_module.discord, "Member", FakeMember)
    bot_channel = FakeVoiceChannel(40)
    user_channel = FakeVoiceChannel(41)
    client = FakeVoiceClient(bot_channel)
    guild = FakeGuild(client)
    interaction = FakeInteraction(guild, FakeMember(user_channel))
    cog = music_cog(guild)

    await Music.stop_music.callback(cog, interaction)  # type: ignore[arg-type]
    await Music.leave_voice.callback(cog, interaction)  # type: ignore[arg-type]

    assert client.stopped == 0
    assert client.disconnected is False
    assert len(interaction.response.messages) == 2
