"""Testes sem rede para cliente e polling da API oficial do Instagram."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from bot.config import Settings
from bot.integrations.instagram import (
    InstagramAuthenticationError,
    InstagramClient,
    InstagramTokenExpiredError,
    refresh_access_token,
)
from bot.integrations.instagram_token_store import (
    AwsSecretsManagerInstagramTokenStore,
    JsonFileInstagramTokenStore,
)
from bot.models import InstagramMedia, InstagramTokenData, InstagramTokenRefreshResult
from bot.storage import NotificationStore
from bot.tasks.instagram_poller import InstagramPoller
from bot.tasks.instagram_token_refresh import InstagramTokenRefreshTask


def instagram_environment(environment: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Ativa a integração Instagram com valores de teste não secretos."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "perfil_autorizado",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
        }
    )
    return values


def instagram_refresh_environment(environment: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Ativa a renovação automática com valores seguros e determinísticos para testes."""
    values = instagram_environment(environment)
    values.update(
        {
            "INSTAGRAM_AUTO_REFRESH_TOKEN": "true",
            "INSTAGRAM_TOKEN_EXPIRES_AT": "2026-11-10T03:30:00+00:00",
            "INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY": "10",
            "INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS": "24",
        }
    )
    return values


@pytest.mark.asyncio
async def test_lists_media_with_optional_fields(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A resposta oficial é convertida mesmo quando campos opcionais estão ausentes."""
    values = instagram_environment(environment)

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(
            "https://graph.instagram.com/v22.0/17800000000000000/media"
        )
        assert request.url.params["fields"]
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "media-1",
                        "permalink": "https://www.instagram.com/p/example/",
                        "timestamp": "2026-09-11T12:00:00+00:00",
                        "username": "perfil_autorizado",
                        "media_type": "IMAGE",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InstagramClient(
            Settings.from_environment(values).instagram,
            http_client=http_client,
            retry_delay_seconds=0,
        )
        media = await client.get_latest_media()

    assert media is not None
    assert media.media_id == "media-1"
    assert media.caption is None
    assert media.media_url is None
    assert media.timestamp == datetime(2026, 9, 11, 12, tzinfo=UTC)


@pytest.mark.asyncio
async def test_reports_expired_or_invalid_token_without_exposing_it(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Erros de autenticação são convertidos em exceções seguras."""
    values = instagram_environment(environment)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InstagramClient(
            Settings.from_environment(values).instagram, http_client=http_client
        )
        with pytest.raises(InstagramAuthenticationError) as error:
            await client.list_recent_media()

    assert values["INSTAGRAM_ACCESS_TOKEN"] not in str(error.value)


@pytest.mark.asyncio
async def test_refreshes_access_token_with_official_endpoint(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A renovação usa GET, grant_type oficial e calcula a expiração em UTC."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/refresh_access_token"
        assert request.url.params["grant_type"] == "ig_refresh_token"
        assert request.url.params["access_token"] == "test-instagram-token"
        return httpx.Response(
            200,
            json={
                "access_token": "refreshed-instagram-token",
                "token_type": "bearer",
                "expires_in": 5_184_000,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await refresh_access_token(
            "test-instagram-token",
            http_client=http_client,
            now=lambda: now,
        )

    assert result.token_type == "bearer"
    assert result.expires_at == now + timedelta(seconds=5_184_000)


@pytest.mark.asyncio
async def test_refresh_reports_expired_token_without_exposing_it(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Token expirado pede reautorização e nunca reproduz o valor secreto no erro."""
    token = "test-instagram-token"

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(400, json={"error": {"message": "Token expired"}})
        )
    ) as http_client:
        with pytest.raises(InstagramTokenExpiredError) as error:
            await refresh_access_token(token, http_client=http_client)

    assert token not in str(error.value)


@pytest.mark.asyncio
async def test_refresh_retries_only_transient_server_failure(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Uma falha 5xx tem repetição limitada antes de aceitar a resposta oficial válida."""
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"access_token": "new-token", "expires_in": 3600})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        result = await refresh_access_token(
            "test-instagram-token",
            http_client=http_client,
            retry_delay_seconds=0,
        )

    assert result.access_token == "new-token"
    assert calls == 2


class FakeTokenStore:
    """Armazena o token em memória para testar a tarefa sem persistência externa."""

    def __init__(self, token: InstagramTokenData | None) -> None:
        self.token = token
        self.saved_tokens: list[InstagramTokenData] = []

    async def get_token(self) -> InstagramTokenData | None:
        return self.token

    async def save_token(self, token: InstagramTokenData) -> None:
        self.token = token
        self.saved_tokens.append(token)


class FakeRefreshClient:
    """Registra chamadas de renovação e devolve um resultado controlado."""

    def __init__(self, result: InstagramTokenRefreshResult | Exception) -> None:
        self.result = result
        self.calls = 0

    async def refresh_access_token(self, _: str) -> InstagramTokenRefreshResult:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def token_data(expires_at: datetime) -> InstagramTokenData:
    """Cria token de teste sem usar credenciais reais."""
    return InstagramTokenData(
        access_token="stored-test-token",
        token_type="bearer",
        expires_at=expires_at,
        updated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_instagram_client_reads_current_token_from_store(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Consultas posteriores usam o token salvo após renovação, sem reiniciar o bot."""
    settings = Settings.from_environment(instagram_environment(environment)).instagram
    store = FakeTokenStore(token_data(datetime(2026, 11, 10, 3, 30, tzinfo=UTC)))
    await store.save_token(
        InstagramTokenData(
            access_token="refreshed-token",
            token_type="bearer",
            expires_at=datetime(2027, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 9, 11, 12, tzinfo=UTC),
        )
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["access_token"] == "refreshed-token"
        return httpx.Response(200, json={"data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InstagramClient(settings, token_store=store, http_client=http_client)  # type: ignore[arg-type]
        assert await client.get_latest_media() is None


@pytest.mark.asyncio
async def test_token_refresh_task_skips_token_outside_refresh_window(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Token ainda válido por mais dias que o limite não dispara renovação."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)
    settings = Settings.from_environment(instagram_refresh_environment(environment)).instagram
    store = FakeTokenStore(token_data(now + timedelta(days=20)))
    client = FakeRefreshClient(
        InstagramTokenRefreshResult("new-token", "bearer", 5_184_000, now + timedelta(days=60))
    )
    task = InstagramTokenRefreshTask(settings, client, store, now=lambda: now)  # type: ignore[arg-type]

    await task.check_once()

    assert client.calls == 0
    assert task.last_status == "not_due"


@pytest.mark.asyncio
async def test_token_refresh_task_saves_new_token_once_when_due(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A janela de renovação salva o novo token e o lock evita chamadas concorrentes."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)
    settings = Settings.from_environment(instagram_refresh_environment(environment)).instagram
    store = FakeTokenStore(token_data(now + timedelta(days=7)))
    client = FakeRefreshClient(
        InstagramTokenRefreshResult("new-token", "bearer", 5_184_000, now + timedelta(days=60))
    )
    task = InstagramTokenRefreshTask(settings, client, store, now=lambda: now)  # type: ignore[arg-type]

    await asyncio.gather(task.check_once(), task.check_once())

    assert client.calls == 1
    assert store.saved_tokens[0].access_token == "new-token"
    assert task.last_status == "refreshed"


@pytest.mark.asyncio
async def test_token_refresh_task_does_not_refresh_expired_token(
    environment: Callable[[], dict[str, str]], caplog: pytest.LogCaptureFixture
) -> None:
    """Token vencido exige reautorização e não inicia uma renovação automática."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)
    values = instagram_refresh_environment(environment)
    settings = Settings.from_environment(values).instagram
    store = FakeTokenStore(token_data(now - timedelta(seconds=1)))
    client = FakeRefreshClient(
        InstagramTokenRefreshResult("new-token", "bearer", 5_184_000, now + timedelta(days=60))
    )
    task = InstagramTokenRefreshTask(settings, client, store, now=lambda: now)  # type: ignore[arg-type]

    with caplog.at_level(logging.WARNING, logger="bot.tasks.instagram_token_refresh"):
        await task.check_once()

    assert client.calls == 0
    assert task.last_status == "expired"
    assert values["INSTAGRAM_ACCESS_TOKEN"] not in caplog.text


@pytest.mark.asyncio
async def test_token_refresh_task_stops_cleanly(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A tarefa periódica pode ser cancelada sem ficar pendente no desligamento."""
    now = datetime(2026, 9, 11, 12, tzinfo=UTC)
    settings = Settings.from_environment(instagram_refresh_environment(environment)).instagram
    store = FakeTokenStore(token_data(now + timedelta(days=20)))
    client = FakeRefreshClient(
        InstagramTokenRefreshResult("new-token", "bearer", 5_184_000, now + timedelta(days=60))
    )
    task = InstagramTokenRefreshTask(settings, client, store, now=lambda: now)  # type: ignore[arg-type]

    task.start()
    task.start()
    await asyncio.sleep(0)
    await task.stop()

    assert client.calls == 0


@pytest.mark.asyncio
async def test_json_token_store_persists_refreshed_token_locally(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """O backend local grava token e expiração em JSON fora do repositório."""
    settings = Settings.from_environment(instagram_refresh_environment(environment)).instagram
    token_store = JsonFileInstagramTokenStore(
        settings, token_path=tmp_path / "instagram-token.json"
    )
    expected = token_data(datetime(2026, 11, 10, 3, 30, tzinfo=UTC))

    await token_store.save_token(expected)
    reloaded_store = JsonFileInstagramTokenStore(
        settings, token_path=tmp_path / "instagram-token.json"
    )
    loaded = await reloaded_store.get_token()

    assert loaded is not None
    assert loaded.access_token == expected.access_token
    assert loaded.expires_at == expected.expires_at
    assert loaded.user_id == "17800000000000000"


class FakeSecretStore:
    """Simula AWS Secrets Manager sem acessar rede ou credenciais AWS."""

    def __init__(self) -> None:
        self.value: str | None = None

    async def read(self, _: str) -> str | None:
        return self.value

    async def write(self, _: str, value: str) -> None:
        self.value = value


@pytest.mark.asyncio
async def test_aws_token_store_serializes_token_without_aws_connection() -> None:
    """O adaptador AWS usa o contrato de segredo injetado e preserva os metadados."""
    secret_store = FakeSecretStore()
    token_store = AwsSecretsManagerInstagramTokenStore("instagram-token", secret_store)
    expected = token_data(datetime(2026, 11, 10, 3, 30, tzinfo=UTC))

    await token_store.save_token(expected)
    loaded = await token_store.get_token()

    assert loaded == expected


class FakeInstagramClient:
    """Retorna mídias controladas sem chamar a API real."""

    def __init__(self, media_items: list[InstagramMedia]) -> None:
        self._media_items = media_items

    async def get_latest_media(self) -> InstagramMedia | None:
        return self._media_items.pop(0) if self._media_items else None


class FakeSender:
    """Registra mídias enviadas sem conectar ao Discord."""

    def __init__(self) -> None:
        self.sent_media: list[InstagramMedia] = []

    async def send_instagram_notification(self, media: InstagramMedia) -> None:
        self.sent_media.append(media)


@pytest.mark.asyncio
async def test_first_poll_marks_latest_as_known_then_notifies_new_media(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """A primeira execução não notifica conteúdo antigo e nunca duplica mídia."""
    settings = Settings.from_environment(instagram_environment(environment)).instagram
    old_media = InstagramMedia(
        media_id="old-media",
        username="perfil_autorizado",
        caption=None,
        media_type="IMAGE",
        media_url=None,
        thumbnail_url=None,
        permalink="https://www.instagram.com/p/old/",
        timestamp=datetime(2026, 9, 11, 10, tzinfo=UTC),
    )
    new_media = InstagramMedia(
        media_id="new-media",
        username="perfil_autorizado",
        caption="Nova mídia",
        media_type="IMAGE",
        media_url=None,
        thumbnail_url=None,
        permalink="https://www.instagram.com/p/new/",
        timestamp=datetime(2026, 9, 11, 11, tzinfo=UTC),
    )
    store = NotificationStore(
        tmp_path / "notifications.sqlite3", instagram_user_id=settings.user_id
    )
    await store.initialize()
    sender = FakeSender()
    poller = InstagramPoller(
        settings, FakeInstagramClient([old_media, new_media, new_media]), store, sender
    )  # type: ignore[arg-type]

    await poller.poll_once()
    await poller.poll_once()
    await poller.poll_once()

    assert await store.has_processed_instagram_media("old-media")
    assert sender.sent_media == [new_media]


class FailingSender:
    """Simula uma falha Discord para verificar que a mídia continua pendente."""

    async def send_instagram_notification(self, _: InstagramMedia) -> None:
        raise RuntimeError("Falha de envio simulada.")


@pytest.mark.asyncio
async def test_poller_does_not_persist_media_when_discord_send_fails(
    environment: Callable[[], dict[str, str]], tmp_path: Path
) -> None:
    """Uma mídia só é marcada após a confirmação de envio ao Discord."""
    values = instagram_environment(environment)
    values["INSTAGRAM_NOTIFY_EXISTING_LATEST"] = "true"
    settings = Settings.from_environment(values).instagram
    media = InstagramMedia(
        media_id="unsent-media",
        username="perfil_autorizado",
        caption="Teste",
        media_type="IMAGE",
        media_url=None,
        thumbnail_url=None,
        permalink="https://www.instagram.com/p/unsent/",
        timestamp=datetime(2026, 9, 11, 12, tzinfo=UTC),
    )
    store = NotificationStore(
        tmp_path / "notifications.sqlite3", instagram_user_id=settings.user_id
    )
    await store.initialize()
    poller = InstagramPoller(
        settings,
        FakeInstagramClient([media]),
        store,
        FailingSender(),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="Falha de envio"):
        await poller.poll_once()

    assert not await store.has_processed_instagram_media(media.media_id)


class FailingInstagramClient:
    """Simula uma falha segura da API sem carregar detalhes de requisição."""

    async def get_latest_media(self) -> InstagramMedia | None:
        raise InstagramAuthenticationError("Token do Instagram expirado.")


@pytest.mark.asyncio
async def test_poller_logs_do_not_include_instagram_token(
    environment: Callable[[], dict[str, str]], tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Erros recuperáveis do polling não podem vazar o token configurado."""
    values = instagram_environment(environment)
    settings = Settings.from_environment(values).instagram
    store = NotificationStore(
        tmp_path / "notifications.sqlite3", instagram_user_id=settings.user_id
    )
    await store.initialize()
    poller = InstagramPoller(settings, FailingInstagramClient(), store, FakeSender())  # type: ignore[arg-type]

    with caplog.at_level(logging.ERROR, logger="bot.tasks.instagram_poller"):
        poller.start()
        await asyncio.sleep(0)
        await poller.stop()

    assert values["INSTAGRAM_ACCESS_TOKEN"] not in caplog.text
