"""Cliente assíncrono da API Helix e do EventSub da Twitch."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import httpx

from bot.config import TwitchSettings
from bot.integrations.twitch_auth import (
    REQUEST_TIMEOUT_SECONDS,
    TwitchApiError,
    TwitchAuthClient,
    TwitchTokenError,
)
from bot.models import TwitchStream, TwitchToken

logger = logging.getLogger(__name__)

TWITCH_API_BASE_URL = "https://api.twitch.tv/helix"

# Mantido como alias para consumidores internos que usavam o nome anterior.
TwitchAPIError = TwitchApiError


class TwitchUnauthorizedError(TwitchTokenError):
    """Indica um HTTP 401 da API Helix, sem incluir dados sensíveis."""


class TwitchClient:
    """Acessa Helix/EventSub com token renovável e restrito à memória do processo."""

    def __init__(
        self,
        settings: TwitchSettings,
        *,
        auth_client: TwitchAuthClient | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        if (
            not settings.enabled
            or not settings.client_id
            or not settings.client_secret
            or not settings.broadcaster_login
            or not settings.eventsub_secret
            or not settings.callback_url
            or settings.notification_channel_id is None
        ):
            raise ValueError("A integração Twitch precisa estar configurada para criar o cliente.")

        self._settings = settings
        self._client_id = settings.client_id
        self._broadcaster_login = settings.broadcaster_login
        self._eventsub_secret = settings.eventsub_secret
        self._callback_url = settings.callback_url
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout_seconds)
        self._owns_http_client = http_client is None
        self._auth_client = auth_client or TwitchAuthClient(settings, http_client=self._http_client)
        self._owns_auth_client = auth_client is None
        self._token: TwitchToken | None = None
        self._token_lock = asyncio.Lock()
        self._broadcaster_user_id = (
            str(settings.broadcaster_user_id) if settings.broadcaster_user_id is not None else None
        )

    async def aclose(self) -> None:
        """Descarta o token em memória e fecha somente recursos próprios."""
        self._token = None
        if self._owns_auth_client:
            await self._auth_client.aclose()
        if self._owns_http_client:
            await self._http_client.aclose()

    async def initialize(self) -> None:
        """Obtém token novo, valida-o e resolve o perfil antes de usar EventSub."""
        await self.refresh_access_token(force=True)
        await self.ensure_valid_access_token()
        await self.resolve_broadcaster_user_id()

    async def refresh_access_token(self, *, force: bool = False) -> TwitchToken:
        """Obtém um token novo uma única vez mesmo sob chamadas concorrentes."""
        async with self._token_lock:
            if not force and self._token is not None and not self._token.expires_soon():
                return self._token
            self._token = await self._auth_client.request_app_access_token()
            return self._token

    async def get_app_access_token(self) -> str:
        """Retorna um token válido, renovando-o pouco antes do vencimento."""
        return (await self.refresh_access_token()).access_token

    async def ensure_valid_access_token(self) -> None:
        """Valida o token atual e, se permitido, o emite uma vez mais quando inválido."""
        token = await self.refresh_access_token()
        if await self._auth_client.validate_token(token.access_token):
            return

        await self._invalidate_access_token_if_current(token.access_token)
        if not self._settings.retry_on_invalid_token:
            raise TwitchTokenError("O token de acesso da Twitch foi considerado inválido.")

        replacement = await self.refresh_access_token()
        if not await self._auth_client.validate_token(replacement.access_token):
            await self._invalidate_access_token_if_current(replacement.access_token)
            raise TwitchTokenError("A Twitch recusou o token de acesso renovado.")
        logger.info("O token Twitch inválido foi renovado com sucesso.")

    async def get_user_by_login(self, login: str | None = None) -> tuple[str, str, str]:
        """Busca ID, login e nome exibido de um perfil pelo login."""
        response = await self._request(
            "GET",
            "/users",
            params={"login": login or self._broadcaster_login},
        )
        users = response.get("data")
        if not isinstance(users, list) or not users or not isinstance(users[0], Mapping):
            raise TwitchApiError("O perfil configurado não foi encontrado na Twitch.")

        user = users[0]
        user_id = user.get("id")
        user_login = user.get("login")
        display_name = user.get("display_name")
        if not all(
            isinstance(value, str) and value for value in (user_id, user_login, display_name)
        ):
            raise TwitchApiError("A Twitch respondeu com dados de perfil inválidos.")
        return user_id, user_login, display_name

    async def resolve_broadcaster_user_id(self) -> str:
        """Obtém o ID do perfil configurado e o reutiliza apenas em memória."""
        if self._broadcaster_user_id is not None:
            return self._broadcaster_user_id

        user_id, _, _ = await self.get_user_by_login()
        self._broadcaster_user_id = user_id
        logger.info("ID do perfil Twitch resolvido para o login configurado.")
        return user_id

    @property
    def resolved_broadcaster_user_id(self) -> str | None:
        """Expõe somente o ID já resolvido, sem I/O na rota do webhook."""
        return self._broadcaster_user_id

    async def get_stream(self, broadcaster_user_id: str) -> TwitchStream:
        """Busca o título atual da live para enriquecer uma notificação."""
        response = await self._request("GET", "/streams", params={"user_id": broadcaster_user_id})
        streams = response.get("data")
        if not isinstance(streams, list) or not streams or not isinstance(streams[0], Mapping):
            return TwitchStream(
                title=None,
                url=f"https://www.twitch.tv/{self._broadcaster_login}",
                is_live=False,
            )

        stream = streams[0]
        user_login = stream.get("user_login")
        title = stream.get("title")
        login = (
            user_login if isinstance(user_login, str) and user_login else self._broadcaster_login
        )
        return TwitchStream(
            title=title if isinstance(title, str) and title else None,
            url=f"https://www.twitch.tv/{login}",
            is_live=True,
        )

    async def list_subscriptions(self) -> list[Mapping[str, Any]]:
        """Obtém inscrições EventSub para detectar duplicidades antes de criar uma nova."""
        subscriptions: list[Mapping[str, Any]] = []
        cursor: str | None = None

        while True:
            params: dict[str, str] = {"first": "100"}
            if cursor is not None:
                params["after"] = cursor
            response = await self._request("GET", "/eventsub/subscriptions", params=params)
            data = response.get("data")
            if isinstance(data, list):
                subscriptions.extend(item for item in data if isinstance(item, Mapping))

            pagination = response.get("pagination")
            next_cursor = pagination.get("cursor") if isinstance(pagination, Mapping) else None
            if not isinstance(next_cursor, str) or not next_cursor:
                return subscriptions
            cursor = next_cursor

    def build_stream_online_subscription_payload(self, broadcaster_user_id: str) -> dict[str, Any]:
        """Monta o payload EventSub conforme o contrato ``stream.online`` v1."""
        return {
            "type": "stream.online",
            "version": "1",
            "condition": {"broadcaster_user_id": broadcaster_user_id},
            "transport": {
                "method": "webhook",
                "callback": self._callback_url,
                "secret": self._eventsub_secret,
            },
        }

    async def ensure_stream_online_subscription(self) -> bool:
        """Cria EventSub sem duplicar uma inscrição após uma renovação de token."""
        broadcaster_user_id = await self.resolve_broadcaster_user_id()
        subscriptions = await self.list_subscriptions()
        if self._has_matching_subscription(subscriptions, broadcaster_user_id):
            logger.info("A inscrição EventSub stream.online já existe para o perfil configurado.")
            return False

        payload = self.build_stream_online_subscription_payload(broadcaster_user_id)
        try:
            await self._request(
                "POST",
                "/eventsub/subscriptions",
                json=payload,
                retry_on_unauthorized=False,
            )
        except TwitchUnauthorizedError:
            if not self._settings.retry_on_invalid_token:
                raise
            logger.warning(
                "Token Twitch recusado ao criar EventSub; verificando inscrição novamente."
            )
            await self.refresh_access_token()
            subscriptions = await self.list_subscriptions()
            if self._has_matching_subscription(subscriptions, broadcaster_user_id):
                logger.info("A inscrição EventSub foi encontrada após renovar o token Twitch.")
                return False
            await self._request(
                "POST",
                "/eventsub/subscriptions",
                json=payload,
                retry_on_unauthorized=False,
            )

        logger.info("Inscrição EventSub stream.online criada para o perfil configurado.")
        return True

    def _has_matching_subscription(
        self, subscriptions: list[Mapping[str, Any]], broadcaster_user_id: str
    ) -> bool:
        for subscription in subscriptions:
            condition = subscription.get("condition")
            transport = subscription.get("transport")
            if not isinstance(condition, Mapping) or not isinstance(transport, Mapping):
                continue
            if (
                subscription.get("type") == "stream.online"
                and subscription.get("version") == "1"
                and str(condition.get("broadcaster_user_id")) == broadcaster_user_id
                and transport.get("method") == "webhook"
                and transport.get("callback") == self._callback_url
            ):
                return True
        return False

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        retry_on_unauthorized: bool = True,
    ) -> Mapping[str, Any]:
        """Executa Helix com uma única renovação segura após HTTP 401 quando aplicável."""
        token = await self.get_app_access_token()
        response = await self._send_request(method, path, token, params=params, json=json)

        if response.status_code == 401:
            await self._invalidate_access_token_if_current(token)
            if not retry_on_unauthorized or not self._settings.retry_on_invalid_token:
                raise TwitchUnauthorizedError("A API da Twitch recusou o token de acesso.")

            refreshed_token = await self.get_app_access_token()
            response = await self._send_request(
                method,
                path,
                refreshed_token,
                params=params,
                json=json,
            )
            if response.status_code == 401:
                await self._invalidate_access_token_if_current(refreshed_token)
                raise TwitchUnauthorizedError("A API da Twitch recusou o token de acesso renovado.")

        if response.status_code >= 400:
            raise TwitchApiError(f"A API da Twitch retornou HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError:
            raise TwitchApiError("A API da Twitch retornou uma resposta inválida.") from None
        if not isinstance(payload, Mapping):
            raise TwitchApiError("A API da Twitch retornou um payload inválido.")
        return payload

    async def _send_request(
        self,
        method: str,
        path: str,
        token: str,
        *,
        params: Mapping[str, str] | None,
        json: Mapping[str, Any] | None,
    ) -> httpx.Response:
        try:
            return await self._http_client.request(
                method,
                f"{TWITCH_API_BASE_URL}{path}",
                params=params,
                json=json,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Client-Id": self._client_id,
                },
            )
        except httpx.RequestError:
            raise TwitchApiError("Não foi possível conectar à API da Twitch.") from None

    async def _invalidate_access_token_if_current(self, access_token: str) -> None:
        """Descarta apenas o token que gerou a falha, preservando renovação concorrente."""
        async with self._token_lock:
            if self._token is not None and self._token.access_token == access_token:
                self._token = None
