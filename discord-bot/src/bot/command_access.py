"""Controle global de acesso aos comandos slash por cargo Discord."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

logger = logging.getLogger(__name__)

COMMAND_REQUIRED_ROLE_MESSAGE = "Você não possui o cargo necessário para usar comandos do bot."


class CommandAccessTree(app_commands.CommandTree):
    """Impede a execução de slash commands por membros sem o cargo configurado."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Valida o cargo antes de qualquer comando registrado na árvore."""
        settings = getattr(self.client, "settings", None)
        required_role_id = getattr(settings, "command_required_role_id", None)
        if required_role_id is None:
            return True

        member = interaction.user
        if interaction.guild is not None and any(
            role.id == required_role_id for role in getattr(member, "roles", ())
        ):
            return True

        logger.warning(
            "Comando slash recusado por cargo: usuário=%s guild=%s comando=%s.",
            interaction.user.id,
            interaction.guild_id,
            interaction.command.qualified_name if interaction.command else "desconhecido",
        )
        if interaction.response.is_done():
            await interaction.followup.send(COMMAND_REQUIRED_ROLE_MESSAGE, ephemeral=True)
        else:
            await interaction.response.send_message(COMMAND_REQUIRED_ROLE_MESSAGE, ephemeral=True)
        return False
