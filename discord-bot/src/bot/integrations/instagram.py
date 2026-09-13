"""Cliente da API oficial Instagram Graph e renovação segura de token."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from bot.config import InstagramSettings
from bot.integrations.instagram_token_store import (
    InMemoryInstagramTokenStore,
    InstagramTokenStore,
)
from bot.models import (
    InstagramMedia,
    InstagramProfile,
    InstagramTokenData,
    InstagramTokenRefreshResult,
)

INSTAGRAM_API_BASE_URL = "https://graph.instagram.com"
INSTAGRAM_TOKEN_REFRESH_URL = f"{INSTAGRAM_API_BASE_URL}/refresh_access_token"
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_TRANSIENT_RETRIES = 2
MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,username"
)


class InstagramAPIError(RuntimeError):
    """Erro seguro para falhas na API oficial do Instagram."""


class InstagramAuthenticationError(InstagramAPIError):
    """Indica token inválido, expirado ou revogado."""


class InstagramTokenExpiredError(InstagramAuthenticationError):
    """Indica que o token já expirou e precisa de nova autorização manual."""


class InstagramTokenRevokedError(InstagramAuthenticationError):
    """Indica que o token foi revogado ou perdeu a autorização."""


class InstagramTokenRefreshError(InstagramAPIError):
    """Indica que a renovação não foi concluída por uma falha recuperável."""


class InstagramPermissionError(InstagramAPIError):
    """Indica que o token não tem permissões para a conta configurada."""


class InstagramProfileNotFoundError(InstagramAPIError):
    """Indica que a conta profissional autorizada não foi encontrada."""


class InstagramRateLimitError(InstagramAPIError):
    """Indica que a API aplicou limite de requisições."""


async def refresh_access_token(
    access_token: str,
    *,
    http_client: httpx.AsyncClient | None = None,
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
    max_transient_retries: int = MAX_TRANSIENT_RETRIES,
    retry_delay_seconds: float = 1.0,
    now: Callable[[], datetime] | None = None,
) -> InstagramTokenRefreshResult:
    """Renova um token ainda válido no endpoint oficial sem expor o valor recebido."""
    client = http_client or httpx.AsyncClient(timeout=timeout_seconds)
    owns_http_client = http_client is None
    current_time = now or (lambda: datetime.now(UTC))
    try:
        for attempt in range(max_transient_retries + 1):
            try:
                response = await client.get(
                    INSTAGRAM_TOKEN_REFRESH_URL,
                    params={"grant_type": "ig_refresh_token", "access_token": access_token},
                )
            except httpx.RequestError:
                raise InstagramTokenRefreshError(
                    "Não foi possível conectar ao serviço de renovação do Instagram."
                ) from None

            if response.status_code >= 500 and attempt < max_transient_retries:
                await asyncio.sleep(retry_delay_seconds * (attempt + 1))
                continue
            if response.status_code in {400, 401}:
                raise _token_authentication_error(response)
            if response.status_code == 403:
                raise InstagramTokenRevokedError(
                    "A autorização do Instagram foi recusada e precisa ser renovada."
                )
            if response.status_code == 429:
                raise InstagramRateLimitError(
                    "A API do Instagram aplicou limite durante a renovação do token."
                )
            if response.status_code >= 500:
                raise InstagramTokenRefreshError(
                    "O serviço de renovação do Instagram falhou temporariamente."
                )
            if response.status_code >= 400:
                raise InstagramTokenRefreshError(
                    f"A API do Instagram recusou a renovação (HTTP {response.status_code})."
                )

            payload = _response_mapping(response, "renovação do token")
            refreshed_token = payload.get("access_token")
            expires_in = payload.get("expires_in")
            token_type = payload.get("token_type")
            if (
                not isinstance(refreshed_token, str)
                or not refreshed_token
                or isinstance(expires_in, bool)
                or not isinstance(expires_in, int)
                or expires_in <= 0
                or (token_type is not None and not isinstance(token_type, str))
            ):
                raise InstagramTokenRefreshError(
                    "A API do Instagram retornou dados inválidos ao renovar o token."
                )
            return InstagramTokenRefreshResult(
                access_token=refreshed_token,
                token_type=token_type,
                expires_in=expires_in,
                expires_at=current_time().astimezone(UTC) + timedelta(seconds=expires_in),
            )
    finally:
        if owns_http_client:
            await client.aclose()

    raise AssertionError("O fluxo de renovação deveria ter retornado ou gerado erro.")


class InstagramClient:
    """Consulta perfis e mídias, sempre usando o token atual do armazenamento configurado."""

    def __init__(
        self,
        settings: InstagramSettings,
        *,
        token_store: InstagramTokenStore | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        max_transient_retries: int = MAX_TRANSIENT_RETRIES,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        if not settings.enabled:
            raise ValueError("INSTAGRAM_ENABLED deve estar ativo para criar o cliente Instagram.")

        self._settings = settings
        self._token_store = token_store or InMemoryInstagramTokenStore(settings)
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_http_client = http_client is None
        self._max_transient_retries = max_transient_retries
        self._retry_delay_seconds = retry_delay_seconds

    async def aclose(self) -> None:
        """Fecha o cliente HTTP criado internamente."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def refresh_access_token(self, access_token: str) -> InstagramTokenRefreshResult:
        """Usa o mesmo cliente HTTP para renovar um token ainda válido."""
        return await refresh_access_token(
            access_token,
            http_client=self._http_client,
            max_transient_retries=self._max_transient_retries,
            retry_delay_seconds=self._retry_delay_seconds,
        )

    def build_profile_url(self, user_id: str | None = None) -> str:
        """Monta a URL oficial para consultar o perfil autorizado."""
        identifier = user_id or (
            str(self._settings.user_id) if self._settings.user_id is not None else "me"
        )
        return f"{INSTAGRAM_API_BASE_URL}/{self._settings.api_version}/{identifier}"

    def build_media_url(self, user_id: str | None = None) -> str:
        """Monta a URL oficial para consultar mídias do perfil autorizado."""
        return f"{self.build_profile_url(user_id)}/media"

    async def get_profile(self) -> InstagramProfile:
        """Obtém os dados básicos do perfil profissional autorizado."""
        token = await self._get_token()
        user_id = (
            str(self._settings.user_id) if self._settings.user_id is not None else token.user_id
        )
        payload = await self._request(
            self.build_profile_url(user_id), fields="id,username", token=token
        )
        user_id = payload.get("id")
        username = payload.get("username")
        if not isinstance(user_id, str) or not isinstance(username, str):
            raise InstagramAPIError("A API do Instagram retornou um perfil inválido.")
        return InstagramProfile(user_id=user_id, username=username)

    async def list_recent_media(self) -> list[InstagramMedia]:
        """Obtém até cinco páginas de mídias e converte campos opcionais com segurança."""
        token = await self._get_token()
        user_id = (
            str(self._settings.user_id) if self._settings.user_id is not None else token.user_id
        )
        if user_id is None:
            profile = await self.get_profile()
            user_id = profile.user_id

        media_items: list[InstagramMedia] = []
        after: str | None = None
        for _ in range(5):
            payload = await self._request(
                self.build_media_url(user_id),
                fields=MEDIA_FIELDS,
                token=token,
                after=after,
            )
            raw_media = payload.get("data")
            if not isinstance(raw_media, list):
                raise InstagramAPIError("A API do Instagram retornou uma lista de mídias inválida.")
            media_items.extend(
                self._parse_media(item) for item in raw_media if isinstance(item, Mapping)
            )
            paging = payload.get("paging")
            cursors = paging.get("cursors") if isinstance(paging, Mapping) else None
            next_after = cursors.get("after") if isinstance(cursors, Mapping) else None
            if not isinstance(next_after, str) or not next_after:
                break
            after = next_after
        return media_items

    async def get_latest_media(self) -> InstagramMedia | None:
        """Retorna a mídia mais recente, se a conta tiver conteúdo disponível."""
        media_items = await self.list_recent_media()
        return max(media_items, key=lambda media: media.timestamp, default=None)

    async def _get_token(self) -> InstagramTokenData:
        """Obtém o token atual sem propagar seu valor para logs ou erros."""
        token = await self._token_store.get_token()
        if token is None:
            raise InstagramAuthenticationError(
                "Instagram habilitado, mas INSTAGRAM_ACCESS_TOKEN não foi configurado."
            )
        return token

    async def _request(
        self,
        url: str,
        *,
        fields: str,
        token: InstagramTokenData,
        after: str | None = None,
    ) -> Mapping[str, Any]:
        """Executa consulta autenticada com repetição limitada para falhas transitórias."""
        params = {"fields": fields, "access_token": token.access_token}
        if after is not None:
            params["after"] = after

        for attempt in range(self._max_transient_retries + 1):
            try:
                response = await self._http_client.get(
                    url,
                    params=params,
                )
            except httpx.RequestError:
                if attempt < self._max_transient_retries:
                    await asyncio.sleep(self._retry_delay_seconds * (attempt + 1))
                    continue
                raise InstagramAPIError("Não foi possível conectar à API do Instagram.") from None

            if response.status_code in {400, 401}:
                raise _token_authentication_error(response)
            if response.status_code == 403:
                raise InstagramPermissionError(
                    "O token não tem permissão para acessar o perfil do Instagram."
                )
            if response.status_code == 429:
                raise InstagramRateLimitError("A API do Instagram aplicou limite de requisições.")
            if response.status_code == 404:
                raise InstagramProfileNotFoundError(
                    "A conta profissional autorizada não foi encontrada."
                )
            if response.status_code >= 500:
                if attempt < self._max_transient_retries:
                    await asyncio.sleep(self._retry_delay_seconds * (attempt + 1))
                    continue
                raise InstagramAPIError("A API do Instagram falhou temporariamente.")
            if response.status_code >= 400:
                raise InstagramAPIError(f"A API do Instagram retornou HTTP {response.status_code}.")
            return _response_mapping(response, "consulta à API")

        raise AssertionError("Fluxo de repetição do Instagram alcançou um estado impossível.")

    @staticmethod
    def _parse_media(payload: Mapping[str, Any]) -> InstagramMedia:
        """Converte uma resposta parcial em um modelo tolerante a campos opcionais."""
        media_id = payload.get("id")
        if not isinstance(media_id, str) or not media_id:
            raise InstagramAPIError("A API do Instagram retornou uma mídia sem ID.")

        return InstagramMedia(
            media_id=media_id,
            username=InstagramClient._optional_string(payload.get("username")),
            caption=InstagramClient._optional_string(payload.get("caption")),
            media_type=InstagramClient._optional_string(payload.get("media_type")),
            media_url=InstagramClient._optional_string(payload.get("media_url")),
            thumbnail_url=InstagramClient._optional_string(payload.get("thumbnail_url")),
            permalink=InstagramClient._optional_string(payload.get("permalink")),
            timestamp=InstagramClient._parse_timestamp(payload.get("timestamp")),
            media_product_type=InstagramClient._optional_string(payload.get("media_product_type")),
        )

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        """Interpreta timestamps ISO 8601 e mantém o bot resiliente a campo ausente."""
        if isinstance(value, str):
            try:
                parsed_timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                parsed_timestamp = None
            if parsed_timestamp is not None:
                return (
                    parsed_timestamp.replace(tzinfo=UTC)
                    if parsed_timestamp.tzinfo is None
                    else parsed_timestamp.astimezone(UTC)
                )
        return datetime.now(UTC)

    @staticmethod
    def _optional_string(value: object) -> str | None:
        """Converte campos opcionais da API em strings, quando disponíveis."""
        return value if isinstance(value, str) and value else None


def _response_mapping(response: httpx.Response, operation: str) -> Mapping[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        raise InstagramAPIError(
            f"A API do Instagram retornou uma resposta inválida durante {operation}."
        ) from None
    if not isinstance(payload, Mapping):
        raise InstagramAPIError(
            f"A API do Instagram retornou um payload inválido durante {operation}."
        )
    return payload


def _token_authentication_error(response: httpx.Response) -> InstagramAuthenticationError:
    """Classifica falhas de autorização sem incluir a resposta nem o token na exceção."""
    message = ""
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping):
            raw_message = error.get("message")
            message = raw_message.lower() if isinstance(raw_message, str) else ""
    if "expired" in message or "expir" in message:
        return InstagramTokenExpiredError(
            "O token Instagram expirou e exige uma nova autorização segura."
        )
    if "revoked" in message or "revog" in message or "invalid" in message:
        return InstagramTokenRevokedError(
            "A autorização do Instagram precisa ser renovada com um novo token."
        )
    return InstagramAuthenticationError("A API do Instagram recusou o token de acesso.")
