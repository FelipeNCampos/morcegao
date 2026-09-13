"""Armazenamento seguro e intercambiável para tokens autorizados do Instagram."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from bot.config import InstagramSettings
from bot.models import InstagramTokenData

DEFAULT_TOKEN_PATH = Path("data") / "instagram-token.json"


class InstagramTokenStoreError(RuntimeError):
    """Falha segura ao ler ou persistir o token Instagram."""


class InstagramTokenStore(Protocol):
    """Contrato para obter e salvar tokens sem acoplar o cliente à infraestrutura."""

    async def get_token(self) -> InstagramTokenData | None:
        """Retorna o token atual e seus metadados, quando estiver configurado."""

    async def save_token(self, token: InstagramTokenData) -> None:
        """Persiste um token recém-autorizado sem registrá-lo em logs."""


class SecretStore(Protocol):
    """Contrato mínimo para um serviço gerenciado de segredos."""

    async def read(self, key: str) -> str | None:
        """Lê o valor de um segredo pelo identificador configurado."""

    async def write(self, key: str, value: str) -> None:
        """Atualiza o valor de um segredo pelo identificador configurado."""


def _fallback_token(settings: InstagramSettings) -> InstagramTokenData | None:
    """Cria um valor inicial a partir do ambiente, sem gravá-lo em disco."""
    if settings.access_token is None:
        return None
    return InstagramTokenData(
        access_token=settings.access_token,
        token_type=None,
        expires_at=settings.token_expires_at or datetime.max.replace(tzinfo=UTC),
        updated_at=datetime.now(UTC),
        user_id=str(settings.user_id) if settings.user_id is not None else None,
        username=settings.username,
    )


def _validated_token(
    token: InstagramTokenData,
    *,
    previous: InstagramTokenData | None = None,
) -> InstagramTokenData:
    """Valida uma resposta e preserva metadados ausentes de um token válido anterior."""
    if not token.access_token.strip():
        raise InstagramTokenStoreError("O token Instagram recebido é inválido.")
    if token.expires_at.tzinfo is None or token.updated_at.tzinfo is None:
        raise InstagramTokenStoreError("Os dados do token Instagram precisam incluir fuso horário.")
    if token.token_type is not None and not token.token_type.strip():
        raise InstagramTokenStoreError("O tipo do token Instagram é inválido.")
    if token.user_id is not None and not token.user_id.strip():
        raise InstagramTokenStoreError("O ID da conta Instagram é inválido.")
    if token.username is not None and not token.username.strip():
        raise InstagramTokenStoreError("O nome da conta Instagram é inválido.")
    return InstagramTokenData(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at.astimezone(UTC),
        updated_at=token.updated_at.astimezone(UTC),
        user_id=token.user_id or (previous.user_id if previous is not None else None),
        username=token.username or (previous.username if previous is not None else None),
    )


class InMemoryInstagramTokenStore:
    """Armazenamento efêmero usado somente em testes isolados."""

    def __init__(self, settings: InstagramSettings) -> None:
        self._token = _fallback_token(settings)
        self._lock = asyncio.Lock()

    async def get_token(self) -> InstagramTokenData | None:
        """Retorna o token em memória para testes unitários isolados."""
        async with self._lock:
            return self._token

    async def save_token(self, token: InstagramTokenData) -> None:
        """Substitui o token em memória depois de validá-lo."""
        async with self._lock:
            self._token = _validated_token(token, previous=self._token)


class JsonFileInstagramTokenStore:
    """Persiste token em JSON atômico, fora do Git e com modo 0600 em sistemas POSIX."""

    def __init__(self, settings: InstagramSettings, *, token_path: Path | None = None) -> None:
        self._token_path = token_path or DEFAULT_TOKEN_PATH
        self._fallback = _fallback_token(settings)
        self._lock = asyncio.Lock()

    async def get_token(self) -> InstagramTokenData | None:
        """Lê o JSON persistido; usa o ambiente apenas quando ainda não há arquivo."""
        async with self._lock:
            token = await asyncio.to_thread(self._read_token)
            return token or self._fallback

    async def save_token(self, token: InstagramTokenData) -> None:
        """Grava uma resposta completa de modo atômico e atualiza o fallback em memória."""
        async with self._lock:
            previous = await asyncio.to_thread(self._read_token)
            normalized = _validated_token(token, previous=previous or self._fallback)
            await asyncio.to_thread(self._write_token, normalized)
            self._fallback = normalized

    def _read_token(self) -> InstagramTokenData | None:
        if not self._token_path.exists():
            return None
        try:
            payload = json.loads(self._token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise InstagramTokenStoreError(
                "Não foi possível ler o armazenamento seguro do token Instagram."
            ) from None
        if not isinstance(payload, Mapping):
            raise InstagramTokenStoreError(
                "O armazenamento do token Instagram possui formato inválido."
            )
        return self._deserialize_token(payload)

    def _write_token(self, token: InstagramTokenData) -> None:
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._token_path.with_name(
            f".{self._token_path.name}.{secrets.token_hex(8)}.tmp"
        )
        try:
            with temporary_path.open("x", encoding="utf-8") as file:
                json.dump(self._serialize_token(token), file, separators=(",", ":"))
                file.flush()
                os.fsync(file.fileno())
            if os.name != "nt":
                temporary_path.chmod(0o600)
            os.replace(temporary_path, self._token_path)
            if os.name != "nt":
                self._token_path.chmod(0o600)
        finally:
            if temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _serialize_token(token: InstagramTokenData) -> dict[str, str | None]:
        return {
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat(),
            "updated_at": token.updated_at.isoformat(),
            "user_id": token.user_id,
            "username": token.username,
        }

    @staticmethod
    def _deserialize_token(payload: Mapping[str, object]) -> InstagramTokenData:
        access_token = payload.get("access_token")
        expires_at = payload.get("expires_at")
        updated_at = payload.get("updated_at")
        token_type = payload.get("token_type")
        user_id = payload.get("user_id")
        username = payload.get("username")
        if not isinstance(access_token, str) or not access_token:
            raise InstagramTokenStoreError("O armazenamento não possui um token Instagram válido.")
        if not isinstance(expires_at, str) or not isinstance(updated_at, str):
            raise InstagramTokenStoreError("O armazenamento não possui datas de token válidas.")
        if token_type is not None and not isinstance(token_type, str):
            raise InstagramTokenStoreError("O armazenamento possui tipo de token inválido.")
        if user_id is not None and not isinstance(user_id, str):
            raise InstagramTokenStoreError("O armazenamento possui ID Instagram inválido.")
        if username is not None and not isinstance(username, str):
            raise InstagramTokenStoreError("O armazenamento possui usuário Instagram inválido.")
        return _validated_token(
            InstagramTokenData(
                access_token=access_token,
                token_type=token_type,
                expires_at=_parse_expires_at(expires_at),
                updated_at=_parse_expires_at(updated_at),
                user_id=user_id,
                username=username,
            )
        )


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
        self._lock = asyncio.Lock()

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
        return JsonFileInstagramTokenStore._deserialize_token(payload)

    async def save_token(self, token: InstagramTokenData) -> None:
        """Grava dados validados em JSON, sem logs ou arquivos públicos."""
        async with self._lock:
            previous = await self.get_token()
            normalized = _validated_token(token, previous=previous)
            payload = JsonFileInstagramTokenStore._serialize_token(normalized)
            await self._secret_store.write(
                self._secret_name, json.dumps(payload, separators=(",", ":"))
            )


def _parse_expires_at(value: str) -> datetime:
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


def create_instagram_token_store(
    settings: InstagramSettings, *, token_path: Path | None = None
) -> InstagramTokenStore:
    """Seleciona o armazenamento JSON local ou AWS conforme a configuração validada."""
    if settings.token_storage_backend == "env":
        return JsonFileInstagramTokenStore(settings, token_path=token_path)
    if settings.aws_secret_name is None or settings.aws_region is None:
        raise InstagramTokenStoreError("O backend AWS não possui nome de segredo ou região.")
    secret_store = AwsSecretsManagerSecretStore(region_name=settings.aws_region)
    return AwsSecretsManagerInstagramTokenStore(settings.aws_secret_name, secret_store)
