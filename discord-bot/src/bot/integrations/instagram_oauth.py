"""OAuth do Instagram Login para autorizar uma conta profissional sem expor segredos."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from bot.config import InstagramSettings
from bot.integrations.instagram_token_store import InstagramTokenStore
from bot.models import InstagramTokenData

INSTAGRAM_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
INSTAGRAM_CODE_EXCHANGE_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_LONG_LIVED_TOKEN_URL = "https://graph.instagram.com/access_token"
INSTAGRAM_API_BASE_URL = "https://graph.instagram.com"
INSTAGRAM_OAUTH_SCOPE = "instagram_business_basic"
OAUTH_STATE_TTL = timedelta(minutes=10)
REQUEST_TIMEOUT_SECONDS = 10.0


class InstagramOAuthError(RuntimeError):
    """Erro seguro do fluxo OAuth, apropriado para uma resposta HTTP genérica."""


class InstagramOAuthStateStore:
    """Guarda estados de uso único somente pelo tempo necessário para o callback."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._states: dict[str, datetime] = {}
        self._now = now or (lambda: datetime.now(UTC))

    def issue(self) -> str:
        """Cria um state criptograficamente aleatório e registra sua expiração."""
        self._remove_expired()
        state = secrets.token_urlsafe(32)
        self._states[state] = self._now() + OAUTH_STATE_TTL
        return state

    def consume(self, state: str) -> bool:
        """Valida e remove o state, impedindo seu reuso."""
        self._remove_expired()
        expires_at = self._states.pop(state, None)
        return expires_at is not None and expires_at >= self._now()

    def _remove_expired(self) -> None:
        now = self._now()
        for state, expires_at in tuple(self._states.items()):
            if expires_at < now:
                del self._states[state]


class InstagramOAuthClient:
    """Executa Instagram Login, troca o código e salva apenas dados validados."""

    def __init__(
        self,
        settings: InstagramSettings,
        token_store: InstagramTokenStore,
        *,
        http_client: httpx.AsyncClient | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not settings.oauth_is_configured:
            raise ValueError("OAuth do Instagram exige app ID, segredo e redirect URI.")
        self._settings = settings
        self._token_store = token_store
        self._http_client = http_client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        self._owns_http_client = http_client is None
        self._now = now or (lambda: datetime.now(UTC))

    def authorization_url(self, state: str) -> str:
        """Monta a URL de consentimento usando somente a permissão de leitura necessária."""
        assert self._settings.app_id is not None
        assert self._settings.redirect_uri is not None
        query = urlencode(
            {
                "client_id": self._settings.app_id,
                "redirect_uri": self._settings.redirect_uri,
                "response_type": "code",
                "scope": INSTAGRAM_OAUTH_SCOPE,
                "state": state,
            }
        )
        return f"{INSTAGRAM_AUTHORIZE_URL}?{query}"

    async def aclose(self) -> None:
        """Fecha o cliente HTTP privado quando o FastAPI encerrar."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def authorize(self, code: str) -> InstagramTokenData:
        """Troca code por token duradouro, valida a conta e persiste o resultado."""
        if not code.strip():
            raise InstagramOAuthError("O retorno do Instagram não contém um código válido.")
        short_token, user_id = await self._exchange_code(code)
        token, token_type, expires_in = await self._exchange_long_lived_token(short_token)
        profile = await self._get_profile(user_id, token)
        expected_username = self._settings.username
        if (
            expected_username is not None
            and profile["username"].casefold() != expected_username.casefold()
        ):
            raise InstagramOAuthError("A conta autorizada não corresponde ao perfil configurado.")
        authorized_token = InstagramTokenData(
            access_token=token,
            token_type=token_type,
            expires_at=self._now().astimezone(UTC) + timedelta(seconds=expires_in),
            updated_at=self._now().astimezone(UTC),
            user_id=profile["id"],
            username=profile["username"],
        )
        await self._token_store.save_token(authorized_token)
        return authorized_token

    async def _exchange_code(self, code: str) -> tuple[str, str]:
        assert self._settings.app_id is not None
        assert self._settings.app_secret is not None
        assert self._settings.redirect_uri is not None
        payload = await self._request_json(
            "POST",
            INSTAGRAM_CODE_EXCHANGE_URL,
            data={
                "client_id": self._settings.app_id,
                "client_secret": self._settings.app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": self._settings.redirect_uri,
                "code": code,
            },
        )
        token = payload.get("access_token")
        user_id = payload.get("user_id")
        if not isinstance(token, str) or not token or not isinstance(user_id, (str, int)):
            raise InstagramOAuthError("O Instagram não retornou uma autorização válida.")
        return token, str(user_id)

    async def _exchange_long_lived_token(self, short_token: str) -> tuple[str, str | None, int]:
        assert self._settings.app_secret is not None
        payload = await self._request_json(
            "GET",
            INSTAGRAM_LONG_LIVED_TOKEN_URL,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": self._settings.app_secret,
                "access_token": short_token,
            },
        )
        token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        token_type = payload.get("token_type")
        if (
            not isinstance(token, str)
            or not token
            or isinstance(expires_in, bool)
            or not isinstance(expires_in, int)
            or expires_in <= 0
            or (token_type is not None and not isinstance(token_type, str))
        ):
            raise InstagramOAuthError("O Instagram não retornou um token de longa duração válido.")
        return token, token_type, expires_in

    async def _get_profile(self, user_id: str, access_token: str) -> dict[str, str]:
        payload = await self._request_json(
            "GET",
            f"{INSTAGRAM_API_BASE_URL}/{self._settings.api_version}/{user_id}",
            params={"fields": "id,username", "access_token": access_token},
        )
        profile_id = payload.get("id")
        username = payload.get("username")
        if (
            not isinstance(profile_id, str)
            or not profile_id
            or not isinstance(username, str)
            or not username
        ):
            raise InstagramOAuthError("O Instagram não retornou os dados da conta autorizada.")
        return {"id": profile_id, "username": username}

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        data: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        try:
            response = await self._http_client.request(method, url, params=params, data=data)
        except httpx.RequestError:
            raise InstagramOAuthError(
                "Não foi possível comunicar com a autorização do Instagram."
            ) from None
        if response.status_code >= 400:
            raise InstagramOAuthError("O Instagram recusou a autorização da conta.")
        try:
            payload = response.json()
        except ValueError:
            raise InstagramOAuthError(
                "O Instagram retornou uma resposta de autorização inválida."
            ) from None
        if not isinstance(payload, Mapping):
            raise InstagramOAuthError("O Instagram retornou dados de autorização inválidos.")
        return payload
