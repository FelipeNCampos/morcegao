"""Tratamento de erros de comandos de aplicativo."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

logger = logging.getLogger(__name__)

USER_ERROR_MESSAGE = "Ocorreu um erro ao executar este comando. Tente novamente mais tarde."
MISSING_MANAGE_GUILD_PERMISSION_MESSAGE = (
    "Você precisa da permissão “Gerenciar servidor” para usar este comando."
)


async def handle_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    """Registra um erro técnico e envia uma mensagem segura ao usuário."""
    if isinstance(error, app_commands.MissingPermissions):
        logger.warning(
            "Tentativa sem a permissão necessária no comando slash %s.",
            interaction.command.qualified_name if interaction.command else "desconhecido",
        )
        await _send_error_message(
            interaction,
            MISSING_MANAGE_GUILD_PERMISSION_MESSAGE,
        )
        return

    logger.error(
        "Falha ao executar o comando slash %s.",
        interaction.command.qualified_name if interaction.command else "desconhecido",
        exc_info=(type(error), error, error.__traceback__),
    )

    await _send_error_message(interaction, USER_ERROR_MESSAGE)


async def _send_error_message(interaction: discord.Interaction, message: str) -> None:
    """Envia uma resposta efêmera, inclusive após uma resposta já iniciada."""
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)
