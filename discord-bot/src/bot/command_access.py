"""Controle global de acesso aos comandos slash por cargo Discord."""

from __future__ import annotations

import logging

import discord
from discord import app_commands

logger = logging.getLogger(__name__)

COMMAND_REQUIRED_ROLE_MESSAGE = "Você não possui o cargo necessário para usar comandos do bot."
PUBLIC_COMMANDS = frozenset({"chamar", "id_usuario"})


class CommandAccessTree(app_commands.CommandTree):
    """Impede comandos restritos, preservando exceções públicas explícitas."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Valida o cargo antes de qualquer comando registrado na árvore."""
        settings = getattr(self.client, "settings", None)
        required_role_id = getattr(settings, "command_required_role_id", None)
        command_name = interaction.command.qualified_name if interaction.command else None
        if required_role_id is None or command_name in PUBLIC_COMMANDS:
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
            command_name or "desconhecido",
        )
        if interaction.response.is_done():
            await interaction.followup.send(COMMAND_REQUIRED_ROLE_MESSAGE, ephemeral=True)
        else:
            await interaction.response.send_message(COMMAND_REQUIRED_ROLE_MESSAGE, ephemeral=True)
        return False
