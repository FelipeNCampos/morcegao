"""Leitura e validação segura da configuração do ambiente."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

MIN_INSTAGRAM_POLL_INTERVAL_SECONDS = 60
DEFAULT_TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS = 3600
DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8000
DEFAULT_INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY = 10
DEFAULT_INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS = 24
DEFAULT_MAX_MESSAGES_TO_DELETE = 100
DEFAULT_MUSIC_IDLE_DISCONNECT_SECONDS = 120


class ConfigurationError(ValueError):
    """Indica que uma variável de configuração é inválida ou está ausente."""


def _required_value(name: str, value: str | None) -> str:
    """Obtém uma variável obrigatória sem revelar seu conteúdo."""
    normalized_value = (value or "").strip()
    if not normalized_value:
        raise ConfigurationError(f"{name} é obrigatório.")
    return normalized_value


def _optional_value(value: str | None) -> str | None:
    """Normaliza uma variável de texto opcional."""
    normalized_value = (value or "").strip()
    return normalized_value or None


def _numeric_id(name: str, value: str | None, *, required: bool = False) -> int | None:
    """Converte IDs opcionais ou obrigatórios sem mostrá-los em mensagens de erro."""
    normalized_value = _optional_value(value)
    if normalized_value is None:
        if required:
            raise ConfigurationError(f"{name} é obrigatório.")
        return None

    if not normalized_value.isascii() or not normalized_value.isdecimal():
        raise ConfigurationError(f"{name} deve ser um ID numérico positivo.")

    identifier = int(normalized_value)
    if identifier <= 0:
        raise ConfigurationError(f"{name} deve ser um ID numérico positivo.")
    return identifier


def _boolean(name: str, value: str | None, *, default: bool = False) -> bool:
    """Converte valores booleanos aceitando true, false, 1 e 0."""
    normalized_value = _optional_value(value)
    if normalized_value is None:
        return default

    if normalized_value.lower() in {"true", "1"}:
        return True
    if normalized_value.lower() in {"false", "0"}:
        return False
    raise ConfigurationError(f"{name} deve ser true, false, 1 ou 0.")


def _log_level(value: str | None) -> str:
    """Obtém um nível de logging válido."""
    level = (_optional_value(value) or "INFO").upper()
    if level not in logging.getLevelNamesMapping():
        raise ConfigurationError(
            "LOG_LEVEL deve ser um nível de logging válido, como INFO ou DEBUG."
        )
    return level


def _profile_login(name: str, value: str | None) -> str:
    """Valida um login de perfil, removendo um único @ inicial."""
    login = _required_value(name, value).removeprefix("@").strip()
    parsed_value = urlparse(login)
    if parsed_value.scheme or parsed_value.netloc or "/" in login:
        raise ConfigurationError(f"{name} deve conter somente o nome do perfil, sem URL.")
    if not re.fullmatch(r"[A-Za-z0-9._]+", login):
        raise ConfigurationError(f"{name} contém caracteres inválidos.")
    return login


def _optional_profile_login(name: str, value: str | None) -> str | None:
    """Valida um login opcional quando ele for informado."""
    return _profile_login(name, value) if _optional_value(value) is not None else None


def _https_url(name: str, value: str | None) -> str:
    """Valida um callback HTTPS sem incluir a URL recebida no erro."""
    callback_url = _required_value(name, value)
    parsed_url = urlparse(callback_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ConfigurationError(f"{name} deve ser uma URL HTTPS válida.")
    return callback_url


def _optional_https_url(name: str, value: str | None) -> str | None:
    """Valida um callback opcional quando ele estiver informado."""
    return _https_url(name, value) if _optional_value(value) is not None else None


def _instagram_api_version(value: str | None) -> str:
    """Valida a versão configurável da API Graph do Instagram."""
    version = _optional_value(value) or "v22.0"
    if not re.fullmatch(r"v\d+\.\d+", version):
        raise ConfigurationError("INSTAGRAM_API_VERSION deve usar o formato vNN.N.")
    return version


def _poll_interval(value: str | None) -> int:
    """Converte e valida um intervalo conservador de polling."""
    normalized_value = _optional_value(value) or "300"
    if not normalized_value.isascii() or not normalized_value.isdecimal():
        raise ConfigurationError("INSTAGRAM_POLL_INTERVAL_SECONDS deve ser um inteiro positivo.")

    interval = int(normalized_value)
    if interval < MIN_INSTAGRAM_POLL_INTERVAL_SECONDS:
        raise ConfigurationError(
            "INSTAGRAM_POLL_INTERVAL_SECONDS deve ser de pelo menos "
            f"{MIN_INSTAGRAM_POLL_INTERVAL_SECONDS} segundos."
        )
    return interval


def _positive_integer(name: str, value: str | None, *, default: int) -> int:
    """Converte uma variável inteira positiva, aplicando um padrão seguro."""
    normalized_value = _optional_value(value)
    if normalized_value is None:
        return default
    if not normalized_value.isascii() or not normalized_value.isdecimal():
        raise ConfigurationError(f"{name} deve ser um inteiro positivo.")

    number = int(normalized_value)
    if number <= 0:
        raise ConfigurationError(f"{name} deve ser um inteiro positivo.")
    return number


def _web_host(value: str | None) -> str:
    """Obtém um host de escuta não vazio sem registrar seu conteúdo."""
    host = _optional_value(value) or DEFAULT_WEB_HOST
    if host in {"0.0.0.0", "::"}:
        raise ConfigurationError("WEB_HOST deve usar um endereço local, como 127.0.0.1.")
    return host


def _web_port(value: str | None) -> int:
    """Converte uma porta TCP válida para o servidor web local."""
    normalized_value = _optional_value(value)
    if normalized_value is None:
        return DEFAULT_WEB_PORT
    if not normalized_value.isascii() or not normalized_value.isdecimal():
        raise ConfigurationError("WEB_PORT deve ser um número entre 1 e 65535.")

    port = int(normalized_value)
    if not 1 <= port <= 65535:
        raise ConfigurationError("WEB_PORT deve ser um número entre 1 e 65535.")
    return port


def _optional_iso_datetime(name: str, value: str | None) -> datetime | None:
    """Interpreta uma data ISO 8601 com fuso horário, normalizada para UTC."""
    normalized_value = _optional_value(value)
    if normalized_value is None:
        return None
    try:
        parsed_value = datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
    except ValueError:
        raise ConfigurationError(f"{name} deve usar o formato ISO 8601 com fuso horário.") from None
    if parsed_value.tzinfo is None:
        raise ConfigurationError(f"{name} deve usar o formato ISO 8601 com fuso horário.")
    return parsed_value.astimezone(UTC)


def _token_storage_backend(value: str | None) -> str:
    """Valida o backend permitido para persistir o token renovado do Instagram."""
    backend = (_optional_value(value) or "env").lower()
    if backend not in {"env", "aws_secrets_manager"}:
        raise ConfigurationError("TOKEN_STORAGE_BACKEND deve ser env ou aws_secrets_manager.")
    return backend


@dataclass(frozen=True, slots=True)
class TwitchSettings:
    """Configurações necessárias para o EventSub da Twitch."""

    enabled: bool
    client_id: str | None
    client_secret: str | None
    broadcaster_login: str | None
    broadcaster_user_id: int | None
    eventsub_secret: str | None
    callback_url: str | None
    token_validate_interval_seconds: int
    retry_on_invalid_token: bool
    notification_channel_id: int | None


@dataclass(frozen=True, slots=True)
class InstagramSettings:
    """Configurações para a consulta oficial de mídia do Instagram."""

    enabled: bool
    username: str | None
    user_id: int | None
    access_token: str | None
    app_id: str | None
    app_secret: str | None
    redirect_uri: str | None
    api_version: str
    poll_interval_seconds: int
    notify_existing_latest: bool
    notification_channel_id: int | None
    auto_refresh_token: bool
    token_refresh_days_before_expiry: int
    token_refresh_check_interval_hours: int
    token_expires_at: datetime | None
    token_storage_backend: str
    aws_secret_name: str | None
    aws_region: str | None

    @property
    def oauth_is_configured(self) -> bool:
        """Indica se as três credenciais necessárias para OAuth foram informadas."""
        return all((self.app_id, self.app_secret, self.redirect_uri))

    @property
    def polling_is_configured(self) -> bool:
        """Indica se há dados mínimos no ambiente para iniciar polling imediatamente."""
        return self.access_token is not None and self.notification_channel_id is not None


@dataclass(frozen=True, slots=True)
class WebSettings:
    """Configurações não sensíveis do servidor FastAPI local."""

    host: str
    port: int


@dataclass(frozen=True, slots=True)
class RoleReactionOption:
    """Vínculo seguro entre um emoji configurado e um cargo do Discord."""

    emoji: str
    role_id: int

    @property
    def emoji_keys(self) -> frozenset[str]:
        """Retorna chaves compatíveis com emojis Unicode e personalizados."""
        keys = {self.emoji}
        custom_emoji = re.fullmatch(r"<a?:[^:]+:(\d+)>", self.emoji)
        if custom_emoji is not None:
            keys.add(custom_emoji.group(1))
        return frozenset(keys)


@dataclass(frozen=True, slots=True)
class RoleCategorySettings:
    """Configuração de uma mensagem de cargos por reação."""

    name: str
    message_id: int | None
    options: tuple[RoleReactionOption, ...]
    exclusive: bool

    def role_id_for_emoji(self, emoji: str, emoji_id: int | None) -> int | None:
        """Localiza somente um cargo explicitamente autorizado para o emoji."""
        candidate_keys = {emoji}
        if emoji_id is not None:
            candidate_keys.add(str(emoji_id))
        for option in self.options:
            if option.emoji_keys.intersection(candidate_keys):
                return option.role_id
        return None


@dataclass(frozen=True, slots=True)
class RoleMenuSettings:
    """Configuração opcional dos cargos automáticos e menus por reação."""

    auto_role_id: int | None
    channel_id: int | None
    categories: tuple[RoleCategorySettings, ...]

    @property
    def has_reaction_menu(self) -> bool:
        """Indica se há ao menos uma mensagem de reação configurada."""
        return self.channel_id is not None and any(
            category.message_id is not None and category.options for category in self.categories
        )


def _role_option(
    source: Mapping[str, str], *, role_variable: str, emoji_variable: str, default_emoji: str
) -> RoleReactionOption | None:
    """Lê uma opção de cargo sem aceitar configurações incompletas."""
    role_id = _numeric_id(role_variable, source.get(role_variable))
    emoji = _optional_value(source.get(emoji_variable))
    if role_id is None:
        if emoji is not None:
            raise ConfigurationError(
                f"{role_variable} é obrigatório quando {emoji_variable} for definido."
            )
        return None
    return RoleReactionOption(emoji=emoji or default_emoji, role_id=role_id)


def _role_category(
    source: Mapping[str, str],
    *,
    name: str,
    message_variable: str,
    exclusive_variable: str,
    default_exclusive: bool,
    options: tuple[tuple[str, str, str], ...],
) -> RoleCategorySettings:
    """Monta uma categoria centralizada de cargos por reação."""
    message_id = _numeric_id(message_variable, source.get(message_variable))
    configured_options = tuple(
        option
        for role_variable, emoji_variable, default_emoji in options
        if (
            option := _role_option(
                source,
                role_variable=role_variable,
                emoji_variable=emoji_variable,
                default_emoji=default_emoji,
            )
        )
        is not None
    )
    if message_id is not None and not configured_options:
        raise ConfigurationError(f"Configure ao menos um cargo para a mensagem {message_variable}.")
    return RoleCategorySettings(
        name=name,
        message_id=message_id,
        options=configured_options,
        exclusive=_boolean(
            exclusive_variable, source.get(exclusive_variable), default=default_exclusive
        ),
    )


def _role_menu_settings(source: Mapping[str, str]) -> RoleMenuSettings:
    """Lê os IDs dos cargos sem depender de nomes mutáveis no Discord."""
    categories = (
        _role_category(
            source,
            name="age",
            message_variable="DISCORD_AGE_ROLE_MESSAGE_ID",
            exclusive_variable="DISCORD_ROLE_AGE_EXCLUSIVE",
            default_exclusive=True,
            options=(
                ("DISCORD_ROLE_AGE_PLUS_18_ID", "DISCORD_ROLE_AGE_PLUS_18_EMOJI", "🔞"),
                ("DISCORD_ROLE_AGE_MINUS_18_ID", "DISCORD_ROLE_AGE_MINUS_18_EMOJI", "🔓"),
            ),
        ),
        _role_category(
            source,
            name="pronouns",
            message_variable="DISCORD_PRONOUN_ROLE_MESSAGE_ID",
            exclusive_variable="DISCORD_ROLE_PRONOUN_EXCLUSIVE",
            default_exclusive=False,
            options=(
                ("DISCORD_ROLE_PRONOUN_SHE_HER_ID", "DISCORD_ROLE_PRONOUN_SHE_HER_EMOJI", "🌙"),
                ("DISCORD_ROLE_PRONOUN_HE_HIM_ID", "DISCORD_ROLE_PRONOUN_HE_HIM_EMOJI", "🌞"),
                ("DISCORD_ROLE_PRONOUN_ELU_DELU_ID", "DISCORD_ROLE_PRONOUN_ELU_DELU_EMOJI", "⭐"),
                (
                    "DISCORD_ROLE_PRONOUN_PREFER_NOT_TO_INFORM_ID",
                    "DISCORD_ROLE_PRONOUN_PREFER_NOT_TO_INFORM_EMOJI",
                    "❔",
                ),
            ),
        ),
    )
    channel_id = _numeric_id(
        "DISCORD_ROLE_MENU_CHANNEL_ID", source.get("DISCORD_ROLE_MENU_CHANNEL_ID")
    )
    if channel_id is None and any(category.message_id is not None for category in categories):
        raise ConfigurationError(
            "DISCORD_ROLE_MENU_CHANNEL_ID é obrigatório quando mensagens de cargos forem definidas."
        )
    return RoleMenuSettings(
        auto_role_id=_numeric_id("DISCORD_AUTO_ROLE_ID", source.get("DISCORD_AUTO_ROLE_ID")),
        channel_id=channel_id,
        categories=categories,
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração tipada e segura para inicializar o bot."""

    discord_token: str
    discord_application_id: int | None
    discord_guild_id: int | None
    temporary_voice_creator_channel_id: int | None
    media_reaction_channel_id: int | None
    role_menu: RoleMenuSettings
    sync_global_commands: bool
    log_level: str
    max_messages_to_delete: int
    music_idle_disconnect_seconds: int
    twitch: TwitchSettings
    instagram: InstagramSettings
    web: WebSettings
    youtube_cookies_file: str | None = None
    command_required_role_id: int | None = None

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> Settings:
        """Cria as configurações a partir de variáveis de ambiente."""
        source = os.environ if environment is None else environment

        twitch_enabled = _boolean("TWITCH_ENABLED", source.get("TWITCH_ENABLED"))
        twitch = TwitchSettings(
            enabled=twitch_enabled,
            client_id=(
                _required_value("TWITCH_CLIENT_ID", source.get("TWITCH_CLIENT_ID"))
                if twitch_enabled
                else _optional_value(source.get("TWITCH_CLIENT_ID"))
            ),
            client_secret=(
                _required_value("TWITCH_CLIENT_SECRET", source.get("TWITCH_CLIENT_SECRET"))
                if twitch_enabled
                else _optional_value(source.get("TWITCH_CLIENT_SECRET"))
            ),
            broadcaster_login=(
                _profile_login("TWITCH_BROADCASTER_LOGIN", source.get("TWITCH_BROADCASTER_LOGIN"))
                if twitch_enabled
                else _optional_profile_login(
                    "TWITCH_BROADCASTER_LOGIN", source.get("TWITCH_BROADCASTER_LOGIN")
                )
            ),
            broadcaster_user_id=_numeric_id(
                "TWITCH_BROADCASTER_USER_ID", source.get("TWITCH_BROADCASTER_USER_ID")
            ),
            eventsub_secret=(
                _required_value("TWITCH_EVENTSUB_SECRET", source.get("TWITCH_EVENTSUB_SECRET"))
                if twitch_enabled
                else _optional_value(source.get("TWITCH_EVENTSUB_SECRET"))
            ),
            callback_url=(
                _https_url("TWITCH_CALLBACK_URL", source.get("TWITCH_CALLBACK_URL"))
                if twitch_enabled
                else _optional_https_url("TWITCH_CALLBACK_URL", source.get("TWITCH_CALLBACK_URL"))
            ),
            token_validate_interval_seconds=_positive_integer(
                "TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS",
                source.get("TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS"),
                default=DEFAULT_TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS,
            ),
            retry_on_invalid_token=_boolean(
                "TWITCH_RETRY_ON_INVALID_TOKEN",
                source.get("TWITCH_RETRY_ON_INVALID_TOKEN"),
                default=True,
            ),
            notification_channel_id=_numeric_id(
                "DISCORD_NOTIFICATION_CHANNEL_ID",
                source.get("DISCORD_NOTIFICATION_CHANNEL_ID"),
                required=twitch_enabled,
            ),
        )

        instagram_enabled = _boolean("INSTAGRAM_ENABLED", source.get("INSTAGRAM_ENABLED"))
        instagram_auto_refresh_token = _boolean(
            "INSTAGRAM_AUTO_REFRESH_TOKEN",
            source.get("INSTAGRAM_AUTO_REFRESH_TOKEN"),
        )
        instagram_token_expires_at = _optional_iso_datetime(
            "INSTAGRAM_TOKEN_EXPIRES_AT", source.get("INSTAGRAM_TOKEN_EXPIRES_AT")
        )
        token_storage_backend = _token_storage_backend(source.get("TOKEN_STORAGE_BACKEND"))
        aws_secret_name = _optional_value(source.get("AWS_SECRET_NAME"))
        aws_region = _optional_value(source.get("AWS_REGION"))
        if (
            instagram_enabled
            and token_storage_backend == "aws_secrets_manager"
            and (aws_secret_name is None or aws_region is None)
        ):
            raise ConfigurationError(
                "AWS_SECRET_NAME e AWS_REGION são obrigatórios para aws_secrets_manager."
            )
        if (
            instagram_enabled
            and instagram_auto_refresh_token
            and instagram_token_expires_at is None
        ):
            raise ConfigurationError(
                "INSTAGRAM_TOKEN_EXPIRES_AT é obrigatório quando a renovação automática está ativa."
            )
        instagram = InstagramSettings(
            enabled=instagram_enabled,
            username=_optional_profile_login(
                "INSTAGRAM_USERNAME", source.get("INSTAGRAM_USERNAME")
            ),
            user_id=_numeric_id(
                "INSTAGRAM_USER_ID",
                source.get("INSTAGRAM_USER_ID"),
            ),
            access_token=_optional_value(source.get("INSTAGRAM_ACCESS_TOKEN")),
            app_id=_optional_value(source.get("INSTAGRAM_APP_ID")),
            app_secret=_optional_value(source.get("INSTAGRAM_APP_SECRET")),
            redirect_uri=_optional_https_url(
                "INSTAGRAM_REDIRECT_URI", source.get("INSTAGRAM_REDIRECT_URI")
            ),
            api_version=_instagram_api_version(source.get("INSTAGRAM_API_VERSION")),
            poll_interval_seconds=_poll_interval(source.get("INSTAGRAM_POLL_INTERVAL_SECONDS")),
            notify_existing_latest=_boolean(
                "INSTAGRAM_NOTIFY_EXISTING_LATEST",
                source.get("INSTAGRAM_NOTIFY_EXISTING_LATEST"),
            ),
            notification_channel_id=_numeric_id(
                "DISCORD_INSTAGRAM_CHANNEL_ID",
                source.get("DISCORD_INSTAGRAM_CHANNEL_ID"),
            ),
            auto_refresh_token=instagram_auto_refresh_token,
            token_refresh_days_before_expiry=_positive_integer(
                "INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY",
                source.get("INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY"),
                default=DEFAULT_INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY,
            ),
            token_refresh_check_interval_hours=_positive_integer(
                "INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS",
                source.get("INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS"),
                default=DEFAULT_INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS,
            ),
            token_expires_at=instagram_token_expires_at,
            token_storage_backend=token_storage_backend,
            aws_secret_name=aws_secret_name,
            aws_region=aws_region,
        )

        return cls(
            discord_token=_required_value("DISCORD_TOKEN", source.get("DISCORD_TOKEN")),
            discord_application_id=_numeric_id(
                "DISCORD_APPLICATION_ID", source.get("DISCORD_APPLICATION_ID")
            ),
            discord_guild_id=_numeric_id("DISCORD_GUILD_ID", source.get("DISCORD_GUILD_ID")),
            temporary_voice_creator_channel_id=_numeric_id(
                "DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID",
                source.get("DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID"),
            ),
            media_reaction_channel_id=_numeric_id(
                "DISCORD_MEDIA_REACTION_CHANNEL_ID",
                source.get("DISCORD_MEDIA_REACTION_CHANNEL_ID"),
            ),
            role_menu=_role_menu_settings(source),
            sync_global_commands=_boolean(
                "SYNC_GLOBAL_COMMANDS", source.get("SYNC_GLOBAL_COMMANDS")
            ),
            log_level=_log_level(source.get("LOG_LEVEL")),
            max_messages_to_delete=_positive_integer(
                "MAX_MESSAGES_TO_DELETE",
                source.get("MAX_MESSAGES_TO_DELETE"),
                default=DEFAULT_MAX_MESSAGES_TO_DELETE,
            ),
            music_idle_disconnect_seconds=_positive_integer(
                "DISCORD_MUSIC_IDLE_DISCONNECT_SECONDS",
                source.get("DISCORD_MUSIC_IDLE_DISCONNECT_SECONDS"),
                default=DEFAULT_MUSIC_IDLE_DISCONNECT_SECONDS,
            ),
            twitch=twitch,
            instagram=instagram,
            web=WebSettings(
                host=_web_host(source.get("WEB_HOST")),
                port=_web_port(source.get("WEB_PORT")),
            ),
            youtube_cookies_file=_optional_value(source.get("YOUTUBE_COOKIES_FILE")),
            command_required_role_id=_numeric_id(
                "DISCORD_COMMAND_REQUIRED_ROLE_ID",
                source.get("DISCORD_COMMAND_REQUIRED_ROLE_ID"),
            ),
        )
