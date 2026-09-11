"""Autenticação OAuth de App Access Token da Twitch, somente em memória."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from bot.config import TwitchSettings
from bot.models import TwitchToken

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_AUTH_ATTEMPTS = 3


class TwitchError(RuntimeError):
    """Erro seguro e genérico de uma integração com a Twitch."""


class TwitchAuthenticationError(TwitchError):
    """Falha ao autenticar a aplicação Twitch."""


class TwitchInvalidClientError(TwitchAuthenticationError):
    """Client ID ou Client Secret foram recusados pela Twitch."""


class TwitchTokenError(TwitchAuthenticationError):
    """Token Twitch inválido, expirado ou com resposta de validação incorreta."""


class TwitchApiError(TwitchError):
    """Falha segura em uma chamada à API Helix ou EventSub."""


class TwitchAuthClient:
    """Obtém e valida tokens OAuth sem persistir valores sensíveis."""

    def __init__(
        self,
        settings: TwitchSettings,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not settings.enabled or not settings.client_id or not settings.client_secret:
            raise ValueError("A autenticação Twitch precisa de Client ID e Client Secret.")

        self._client_id = settings.client_id
        self._client_secret = settings.client_secret
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_http_client = http_client is None
        self._now = now or (lambda: datetime.now(UTC))

    async def aclose(self) -> None:
        """Fecha somente o cliente HTTP criado por esta instância."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def request_app_access_token(self) -> TwitchToken:
        """Solicita um novo App Access Token pelo fluxo client credentials."""
        response = await self._request_with_retries(
            "POST",
            TWITCH_AUTH_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )
        if response.status_code in {400, 401}:
            raise TwitchInvalidClientError(
                "A Twitch recusou as credenciais da aplicação configurada."
            )
        if response.status_code >= 400:
            raise TwitchAuthenticationError(
                f"A Twitch recusou a solicitação de token (HTTP {response.status_code})."
            )

        payload = self._json_mapping(response, "token")
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if (
            not isinstance(access_token, str)
            or not access_token
            or isinstance(expires_in, bool)
            or not isinstance(expires_in, int)
            or expires_in <= 0
        ):
            raise TwitchTokenError("A Twitch respondeu com um token de acesso inválido.")

        return TwitchToken(
            access_token=access_token,
            expires_at=self._now().astimezone(UTC) + timedelta(seconds=expires_in),
        )

    async def validate_token(self, access_token: str) -> bool:
        """Confirma com a Twitch se um token ainda pode ser usado."""
        response = await self._request_with_retries(
            "GET",
            TWITCH_VALIDATE_URL,
            headers={"Authorization": f"OAuth {access_token}"},
        )
        if response.status_code == 401:
            return False
        if response.status_code >= 400:
            raise TwitchTokenError(
                f"A Twitch não conseguiu validar o token (HTTP {response.status_code})."
            )

        self._json_mapping(response, "validação do token")
        return True

    async def _request_with_retries(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Repete somente falhas transitórias de rede ou servidor, sem registrar segredos."""
        for attempt in range(MAX_AUTH_ATTEMPTS):
            try:
                response = await self._http_client.request(method, url, **kwargs)
            except httpx.RequestError:
                if attempt == MAX_AUTH_ATTEMPTS - 1:
                    raise TwitchAuthenticationError(
                        "Não foi possível conectar ao serviço de autenticação da Twitch."
                    ) from None
            else:
                if response.status_code < 500 or attempt == MAX_AUTH_ATTEMPTS - 1:
                    return response

            await asyncio.sleep(0.1 * (attempt + 1))

        raise AssertionError("A tentativa de autenticação deveria ter retornado ou gerado erro.")

    @staticmethod
    def _json_mapping(response: httpx.Response, operation: str) -> Mapping[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            raise TwitchTokenError(
                f"A Twitch retornou uma resposta inválida durante {operation}."
            ) from None
        if not isinstance(payload, Mapping):
            raise TwitchTokenError(f"A Twitch retornou um payload inválido durante {operation}.")
        return payload
