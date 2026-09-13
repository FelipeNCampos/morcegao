"""Testes unitários da configuração do ambiente."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from bot.config import ConfigurationError, Settings


def test_token_is_required(environment: Callable[[], dict[str, str]]) -> None:
    """A ausência de token Discord deve interromper a leitura da configuração."""
    values = environment()
    del values["DISCORD_TOKEN"]

    with pytest.raises(ConfigurationError, match="DISCORD_TOKEN"):
        Settings.from_environment(values)


def test_discord_ids_are_read_as_integers(environment: Callable[[], dict[str, str]]) -> None:
    """IDs válidos devem ser convertidos para inteiros."""
    settings = Settings.from_environment(environment())

    assert settings.discord_application_id == 123456789012345678
    assert settings.discord_guild_id == 987654321098765432
    assert settings.twitch.notification_channel_id == 123456789012345678


def test_temporary_voice_creator_channel_id_is_optional_and_numeric(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O canal criador pode ficar desativado ou ser configurado por um ID Discord válido."""
    values = environment()
    assert Settings.from_environment(values).temporary_voice_creator_channel_id is None

    values["DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID"] = "123456789012345679"
    assert (
        Settings.from_environment(values).temporary_voice_creator_channel_id == 123456789012345679
    )

    values["DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID"] = "invalido"
    with pytest.raises(ConfigurationError, match="DISCORD_TEMPORARY_VOICE_CREATOR_CHANNEL_ID"):
        Settings.from_environment(values)


def test_media_reaction_channel_id_is_optional_and_numeric(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O canal de reações pode ficar desativado ou receber um ID Discord válido."""
    values = environment()
    assert Settings.from_environment(values).media_reaction_channel_id is None

    values["DISCORD_MEDIA_REACTION_CHANNEL_ID"] = "123456789012345679"
    assert Settings.from_environment(values).media_reaction_channel_id == 123456789012345679

    values["DISCORD_MEDIA_REACTION_CHANNEL_ID"] = "invalido"
    with pytest.raises(ConfigurationError, match="DISCORD_MEDIA_REACTION_CHANNEL_ID"):
        Settings.from_environment(values)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("false", False), ("1", True), ("0", False)],
)
def test_boolean_values_are_converted(
    environment: Callable[[], dict[str, str]], value: str, expected: bool
) -> None:
    """Os formatos booleanos aceitos devem ser interpretados corretamente."""
    values = environment()
    values["SYNC_GLOBAL_COMMANDS"] = value

    assert Settings.from_environment(values).sync_global_commands is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("false", False), ("1", True), ("0", False)],
)
def test_twitch_retry_boolean_is_converted(
    environment: Callable[[], dict[str, str]], value: str, expected: bool
) -> None:
    """O controle de repetição Twitch usa os mesmos formatos booleanos aceitos."""
    values = environment()
    values["TWITCH_RETRY_ON_INVALID_TOKEN"] = value

    assert Settings.from_environment(values).twitch.retry_on_invalid_token is expected


def test_twitch_token_validation_interval_is_read_and_validated(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O intervalo do validador Twitch é inteiro positivo e tem padrão documentado."""
    values = environment()
    values["TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS"] = "120"
    assert Settings.from_environment(values).twitch.token_validate_interval_seconds == 120

    values["TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS"] = "0"
    with pytest.raises(ConfigurationError, match="TWITCH_TOKEN_VALIDATE_INTERVAL_SECONDS"):
        Settings.from_environment(values)


def test_max_messages_to_delete_is_configurable_and_positive(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O limite de moderação tem padrão seguro e não aceita valores não positivos."""
    values = environment()
    assert Settings.from_environment(values).max_messages_to_delete == 100

    values["MAX_MESSAGES_TO_DELETE"] = "25"
    assert Settings.from_environment(values).max_messages_to_delete == 25

    values["MAX_MESSAGES_TO_DELETE"] = "0"
    with pytest.raises(ConfigurationError, match="MAX_MESSAGES_TO_DELETE"):
        Settings.from_environment(values)


def test_web_host_and_port_are_configured_and_validated(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O servidor web usa host local configurável e portas TCP válidas."""
    values = environment()
    values.update({"WEB_HOST": "127.0.0.1", "WEB_PORT": "8123"})
    settings = Settings.from_environment(values)

    assert settings.web.host == "127.0.0.1"
    assert settings.web.port == 8123

    values["WEB_PORT"] = "65536"
    with pytest.raises(ConfigurationError, match="WEB_PORT"):
        Settings.from_environment(values)

    values.update({"WEB_PORT": "8000", "WEB_HOST": "0.0.0.0"})
    with pytest.raises(ConfigurationError, match="WEB_HOST"):
        Settings.from_environment(values)


def test_instagram_auto_refresh_configuration_is_validated(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A renovação requer expiração com fuso, dias e horas positivos quando ativa."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "perfil_autorizado",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
            "INSTAGRAM_AUTO_REFRESH_TOKEN": "true",
            "INSTAGRAM_TOKEN_EXPIRES_AT": "2026-11-10T03:30:00+00:00",
            "INSTAGRAM_TOKEN_REFRESH_DAYS_BEFORE_EXPIRY": "10",
            "INSTAGRAM_TOKEN_REFRESH_CHECK_INTERVAL_HOURS": "24",
        }
    )
    settings = Settings.from_environment(values)

    assert settings.instagram.auto_refresh_token is True
    assert settings.instagram.token_expires_at is not None
    assert settings.instagram.token_refresh_days_before_expiry == 10
    assert settings.instagram.token_refresh_check_interval_hours == 24

    del values["INSTAGRAM_TOKEN_EXPIRES_AT"]
    with pytest.raises(ConfigurationError, match="INSTAGRAM_TOKEN_EXPIRES_AT"):
        Settings.from_environment(values)


def test_aws_token_storage_requires_name_and_region(
    environment: Callable[[], dict[str, str]],
) -> None:
    """AWS Secrets Manager só é aceito com os identificadores necessários."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "perfil_autorizado",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
            "TOKEN_STORAGE_BACKEND": "aws_secrets_manager",
        }
    )

    with pytest.raises(ConfigurationError, match="AWS_SECRET_NAME"):
        Settings.from_environment(values)


def test_legacy_twitch_access_token_is_ignored(
    environment: Callable[[], dict[str, str]],
) -> None:
    """A configuração não lê nem mantém a variável legada de token Twitch."""
    values = environment()
    values["TWITCH_APP_ACCESS_TOKEN"] = "must-not-be-read"

    settings = Settings.from_environment(values)

    assert not hasattr(settings.twitch, "app_access_token")


def test_twitch_login_removes_initial_at_sign(environment: Callable[[], dict[str, str]]) -> None:
    """O login Twitch pode ser informado com @, mas é normalizado."""
    values = environment()
    values["TWITCH_BROADCASTER_LOGIN"] = " @canal_teste "

    assert Settings.from_environment(values).twitch.broadcaster_login == "canal_teste"


def test_twitch_login_rejects_url(environment: Callable[[], dict[str, str]]) -> None:
    """Uma URL não é um login Twitch válido."""
    values = environment()
    values["TWITCH_BROADCASTER_LOGIN"] = "https://twitch.tv/canal_teste"

    with pytest.raises(ConfigurationError, match="TWITCH_BROADCASTER_LOGIN"):
        Settings.from_environment(values)


def test_instagram_is_optional_when_disabled(environment: Callable[[], dict[str, str]]) -> None:
    """O bot continua configurável sem dados Instagram com a integração desativada."""
    settings = Settings.from_environment(environment())

    assert settings.instagram.enabled is False
    assert settings.instagram.access_token is None
    assert settings.instagram.user_id is None


def test_twitch_is_optional_when_disabled(environment: Callable[[], dict[str, str]]) -> None:
    """O bot inicia sem credenciais Twitch quando essa integração está desativada."""
    values = environment()
    values["TWITCH_ENABLED"] = "false"
    for key in tuple(key for key in values if key.startswith("TWITCH_")):
        if key != "TWITCH_ENABLED":
            del values[key]
    del values["DISCORD_NOTIFICATION_CHANNEL_ID"]

    settings = Settings.from_environment(values)

    assert settings.twitch.enabled is False
    assert settings.twitch.client_id is None
    assert settings.twitch.notification_channel_id is None


def test_twitch_and_instagram_can_be_enabled_independently(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Cada integração tem seu próprio controle de ativação por ambiente."""
    twitch_only = Settings.from_environment(environment())
    assert twitch_only.twitch.enabled is True
    assert twitch_only.instagram.enabled is False

    instagram_only_values = environment()
    instagram_only_values["TWITCH_ENABLED"] = "false"
    for key in tuple(key for key in instagram_only_values if key.startswith("TWITCH_")):
        if key != "TWITCH_ENABLED":
            del instagram_only_values[key]
    del instagram_only_values["DISCORD_NOTIFICATION_CHANNEL_ID"]
    instagram_only_values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": "perfil_autorizado",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
        }
    )

    instagram_only = Settings.from_environment(instagram_only_values)
    assert instagram_only.twitch.enabled is False
    assert instagram_only.instagram.enabled is True


def test_instagram_enabled_allows_oauth_before_token_is_available(
    environment: Callable[[], dict[str, str]],
) -> None:
    """OAuth pode ser iniciado antes de haver token, ID ou canal para o polling."""
    values = environment()
    values["INSTAGRAM_ENABLED"] = "true"

    instagram = Settings.from_environment(values).instagram

    assert instagram.enabled is True
    assert instagram.access_token is None
    assert instagram.user_id is None
    assert instagram.notification_channel_id is None


def test_instagram_login_is_normalized_and_url_is_rejected(
    environment: Callable[[], dict[str, str]],
) -> None:
    """O perfil Instagram ativo aceita @ inicial, mas nunca uma URL."""
    values = environment()
    values.update(
        {
            "INSTAGRAM_ENABLED": "true",
            "INSTAGRAM_USERNAME": " @perfil_autorizado ",
            "INSTAGRAM_USER_ID": "17800000000000000",
            "INSTAGRAM_ACCESS_TOKEN": "test-instagram-token",
            "DISCORD_INSTAGRAM_CHANNEL_ID": "123456789012345678",
        }
    )
    assert Settings.from_environment(values).instagram.username == "perfil_autorizado"

    values["INSTAGRAM_USERNAME"] = "https://instagram.com/perfil_autorizado"
    with pytest.raises(ConfigurationError, match="INSTAGRAM_USERNAME"):
        Settings.from_environment(values)


def test_instagram_interval_has_a_safe_minimum(environment: Callable[[], dict[str, str]]) -> None:
    """Polling muito frequente é rejeitado para proteger a API oficial."""
    values = environment()
    values["INSTAGRAM_POLL_INTERVAL_SECONDS"] = "30"

    with pytest.raises(ConfigurationError, match="INSTAGRAM_POLL_INTERVAL_SECONDS"):
        Settings.from_environment(values)


def test_required_configuration_error_does_not_include_secret(
    environment: Callable[[], dict[str, str]],
) -> None:
    """Erros de validação nunca devem reproduzir um valor secreto."""
    values = environment()
    secret_marker = "test-secret-marker"
    values["TWITCH_CLIENT_SECRET"] = secret_marker
    del values["TWITCH_CALLBACK_URL"]

    with pytest.raises(ConfigurationError) as error:
        Settings.from_environment(values)

    assert secret_marker not in str(error.value)
