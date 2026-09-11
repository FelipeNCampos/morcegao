"""Armazenamento seguro e intercambiável para tokens renováveis do Instagram."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from dotenv import dotenv_values, set_key

from bot.config import InstagramSettings
from bot.models import InstagramTokenData


class InstagramTokenStoreError(RuntimeError):
    """Falha segura ao ler ou persistir o token Instagram."""


class InstagramTokenStore(Protocol):
    """Contrato para obter e salvar tokens sem acoplar o cliente à infraestrutura."""

    async def get_token(self) -> InstagramTokenData | None:
        """Retorna o token atual e seus metadados, quando estiver configurado."""

    async def save_token(self, token: InstagramTokenData) -> None:
        """Persiste um token recém-renovado sem registrá-lo em logs."""


class SecretStore(Protocol):
    """Contrato mínimo para um serviço gerenciado de segredos."""

    async def read(self, key: str) -> str | None:
        """Lê o valor de um segredo pelo identificador configurado."""

    async def write(self, key: str, value: str) -> None:
        """Atualiza o valor de um segredo pelo identificador configurado."""


class InMemoryInstagramTokenStore:
    """Armazenamento efêmero usado somente quando o cliente é criado isoladamente em testes."""

    def __init__(self, settings: InstagramSettings) -> None:
        if settings.access_token is None:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN é obrigatório para criar o armazenamento.")
        self._token = InstagramTokenData(
            access_token=settings.access_token,
            token_type=None,
            expires_at=settings.token_expires_at or datetime.max.replace(tzinfo=UTC),
            updated_at=datetime.now(UTC),
        )
        self._lock = asyncio.Lock()

    async def get_token(self) -> InstagramTokenData | None:
        """Retorna o token em memória para testes unitários isolados."""
        async with self._lock:
            return self._token

    async def save_token(self, token: InstagramTokenData) -> None:
        """Substitui o token em memória para refletir a renovação nos testes."""
        async with self._lock:
            self._token = token


class DotenvInstagramTokenStore:
    """Backend local de desenvolvimento que atualiza o arquivo `.env` ignorado pelo Git."""

    def __init__(self, settings: InstagramSettings, *, dotenv_path: Path | None = None) -> None:
        if settings.access_token is None:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN é obrigatório para o armazenamento local.")
        self._fallback_token = settings.access_token
        self._fallback_expires_at = settings.token_expires_at
        self._dotenv_path = dotenv_path or Path(".env")
        self._lock = asyncio.Lock()

    async def get_token(self) -> InstagramTokenData | None:
        """Recarrega o token persistido para que polling e renovação usem o valor atual."""
        values = await asyncio.to_thread(self._read_values)
        access_token = self._value_or_fallback(
            values, "INSTAGRAM_ACCESS_TOKEN", self._fallback_token
        )
        expires_at = self._parse_expires_at(
            self._value_or_fallback(
                values,
                "INSTAGRAM_TOKEN_EXPIRES_AT",
                self._fallback_expires_at.isoformat() if self._fallback_expires_at else None,
            )
        )
        if access_token is None:
            return None
        return InstagramTokenData(
            access_token=access_token,
            token_type=self._optional_value(values.get("INSTAGRAM_TOKEN_TYPE")),
            expires_at=expires_at,
            updated_at=datetime.now(UTC),
        )

    async def save_token(self, token: InstagramTokenData) -> None:
        """Atualiza o `.env` local de modo serializado, mantendo o token fora do repositório."""
        async with self._lock:
            await asyncio.to_thread(self._write_values, token)
            self._fallback_token = token.access_token
            self._fallback_expires_at = token.expires_at

    def _read_values(self) -> Mapping[str, str | None]:
        if not self._dotenv_path.exists():
            return {}
        return dotenv_values(self._dotenv_path)

    def _write_values(self, token: InstagramTokenData) -> None:
        self._dotenv_path.parent.mkdir(parents=True, exist_ok=True)
        set_key(
            str(self._dotenv_path),
            "INSTAGRAM_ACCESS_TOKEN",
            token.access_token,
            quote_mode="always",
        )
        set_key(
            str(self._dotenv_path),
            "INSTAGRAM_TOKEN_EXPIRES_AT",
            token.expires_at.isoformat(),
            quote_mode="always",
        )
        if token.token_type is not None:
            set_key(
                str(self._dotenv_path),
                "INSTAGRAM_TOKEN_TYPE",
                token.token_type,
                quote_mode="always",
            )
        if os.name != "nt":
            self._dotenv_path.chmod(0o600)

    @staticmethod
    def _value_or_fallback(
        values: Mapping[str, str | None], key: str, fallback: str | None
    ) -> str | None:
        value = DotenvInstagramTokenStore._optional_value(values.get(key))
        return value if value is not None else fallback

    @staticmethod
    def _optional_value(value: str | None) -> str | None:
        normalized_value = (value or "").strip()
        return normalized_value or None

    @staticmethod
    def _parse_expires_at(value: str | None) -> datetime:
        if value is None:
            return datetime.max.replace(tzinfo=UTC)
        try:
            parsed_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise InstagramTokenStoreError(
                "A data de expiração armazenada do Instagram é inválida."
            ) from None
        if parsed_value.tzinfo is None:
            raise InstagramTokenStoreError(
                "A data de expiração armazenada do Instagram precisa incluir fuso horário."
            )
        return parsed_value.astimezone(UTC)


class AwsSecretsManagerSecretStore:
    """Adaptador assíncrono para AWS Secrets Manager via IAM Role da instância EC2."""

    def __init__(self, *, region_name: str, client: Any | None = None) -> None:
        if client is None:
            try:
                import boto3
            except ImportError:
                raise InstagramTokenStoreError(
                    "O backend AWS exige instalar o extra de dependências aws."
                ) from None
            client = boto3.client("secretsmanager", region_name=region_name)
        self._client = client

    async def read(self, key: str) -> str | None:
        """Lê SecretString sem registrar seu conteúdo ou detalhes da resposta AWS."""
        try:
            response = await asyncio.to_thread(self._client.get_secret_value, SecretId=key)
        except Exception:
            raise InstagramTokenStoreError(
                "Não foi possível ler o segredo Instagram na AWS."
            ) from None
        value = response.get("SecretString")
        return value if isinstance(value, str) and value else None

    async def write(self, key: str, value: str) -> None:
        """Persiste SecretString usando as permissões da IAM Role configurada."""
        try:
            await asyncio.to_thread(self._client.put_secret_value, SecretId=key, SecretString=value)
        except Exception:
            raise InstagramTokenStoreError(
                "Não foi possível atualizar o segredo Instagram na AWS."
            ) from None


class AwsSecretsManagerInstagramTokenStore:
    """Armazena a estrutura tipada do token em um único segredo JSON da AWS."""

    def __init__(self, secret_name: str, secret_store: SecretStore) -> None:
        self._secret_name = secret_name
        self._secret_store = secret_store

    async def get_token(self) -> InstagramTokenData | None:
        """Converte o segredo JSON em dados de token sem expor seu valor."""
        raw_value = await self._secret_store.read(self._secret_name)
        if raw_value is None:
            return None
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            raise InstagramTokenStoreError(
                "O segredo Instagram da AWS não contém JSON válido."
            ) from None
        if not isinstance(payload, Mapping):
            raise InstagramTokenStoreError("O segredo Instagram da AWS possui formato inválido.")
        return self._deserialize_token(payload)

    async def save_token(self, token: InstagramTokenData) -> None:
        """Grava dados tipados em JSON, sem logs ou arquivos públicos."""
        payload = {
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat(),
            "updated_at": token.updated_at.isoformat(),
        }
        await self._secret_store.write(
            self._secret_name, json.dumps(payload, separators=(",", ":"))
        )

    @staticmethod
    def _deserialize_token(payload: Mapping[str, object]) -> InstagramTokenData:
        access_token = payload.get("access_token")
        expires_at = payload.get("expires_at")
        updated_at = payload.get("updated_at")
        token_type = payload.get("token_type")
        if not isinstance(access_token, str) or not access_token:
            raise InstagramTokenStoreError("O segredo Instagram da AWS não possui token válido.")
        if token_type is not None and not isinstance(token_type, str):
            raise InstagramTokenStoreError(
                "O segredo Instagram da AWS possui tipo de token inválido."
            )
        if not isinstance(expires_at, str) or not isinstance(updated_at, str):
            raise InstagramTokenStoreError(
                "O segredo Instagram da AWS não possui datas de token válidas."
            )
        return InstagramTokenData(
            access_token=access_token,
            token_type=token_type,
            expires_at=DotenvInstagramTokenStore._parse_expires_at(expires_at),
            updated_at=DotenvInstagramTokenStore._parse_expires_at(updated_at),
        )


def create_instagram_token_store(
    settings: InstagramSettings, *, dotenv_path: Path | None = None
) -> InstagramTokenStore:
    """Seleciona o armazenamento local ou AWS conforme a configuração validada."""
    if settings.token_storage_backend == "env":
        return DotenvInstagramTokenStore(settings, dotenv_path=dotenv_path)
    if settings.aws_secret_name is None or settings.aws_region is None:
        raise InstagramTokenStoreError("O backend AWS não possui nome de segredo ou região.")
    secret_store = AwsSecretsManagerSecretStore(region_name=settings.aws_region)
    return AwsSecretsManagerInstagramTokenStore(settings.aws_secret_name, secret_store)
