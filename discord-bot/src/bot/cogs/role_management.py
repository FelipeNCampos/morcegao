"""Cargos automáticos e menus seguros de cargos por reação."""

from __future__ import annotations

import logging
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import DiscordBot
from bot.config import RoleCategorySettings, Settings

logger = logging.getLogger(__name__)

CATEGORY_TITLES = {
    "age": "Faixa etária",
    "pronouns": "Pronomes",
}


class RoleManagement(commands.Cog):
    """Processa somente cargos e reações previamente mapeados na configuração."""

    def __init__(self, bot: DiscordBot, settings: Settings) -> None:
        self._bot = bot
        self._settings = settings
        self._configuration_validated = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Valida a configuração uma vez, sem impedir a inicialização do bot."""
        if self._configuration_validated:
            return
        self._configuration_validated = True
        await self._validate_configuration()
        await self._add_configured_reactions()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Atribui o cargo inicial configurado a um novo membro."""
        role_id = self._settings.role_menu.auto_role_id
        if role_id is None:
            return

        role = member.guild.get_role(role_id)
        if role is None:
            logger.error(
                "Cargo automático %s não encontrado na guild %s.", role_id, member.guild.id
            )
            return
        if role in member.roles:
            return
        if not self._is_role_assignable(member.guild, role):
            logger.error(
                "Cargo automático %s não pode ser gerenciado pelo bot na guild %s.",
                role.id,
                member.guild.id,
            )
            return

        try:
            await member.add_roles(role, reason="Cargo automático atribuído na entrada do membro")
        except discord.Forbidden:
            logger.warning("Sem permissão para atribuir o cargo automático a %s.", member.id)
        except discord.NotFound:
            logger.warning("Membro %s não encontrado ao atribuir cargo automático.", member.id)
        except discord.HTTPException as error:
            logger.warning(
                "Falha HTTP ao atribuir cargo automático %s a %s: status=%s.",
                role.id,
                member.id,
                error.status,
            )
        else:
            logger.info("Cargo automático %s atribuído ao membro %s.", role.id, member.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Alterna um cargo mapeado mesmo quando a mensagem não está no cache."""
        if (
            payload.guild_id is None
            or self._bot.user is None
            or payload.user_id == self._bot.user.id
        ):
            return
        menu = self._settings.role_menu
        if menu.channel_id is None or payload.channel_id != menu.channel_id:
            return

        category = next(
            (item for item in menu.categories if item.message_id == payload.message_id), None
        )
        if category is None:
            return
        role_id = category.role_id_for_emoji(str(payload.emoji), payload.emoji.id)
        if role_id is None:
            return

        guild = self._bot.get_guild(payload.guild_id)
        if guild is None:
            logger.warning("Guild %s não disponível para a reação de cargos.", payload.guild_id)
            return
        member = await self._get_member(guild, payload)
        if member is None:
            return
        role = guild.get_role(role_id)
        if role is None:
            logger.error("Cargo %s não encontrado na guild %s.", role_id, guild.id)
            return
        if not self._is_role_assignable(guild, role):
            logger.warning("Cargo %s não é gerenciável pelo bot na guild %s.", role.id, guild.id)
            return

        try:
            action = await self._toggle_role(member, role, category)
        except discord.Forbidden:
            logger.warning(
                "Sem permissão para atualizar cargo %s do membro %s.", role.id, member.id
            )
            return
        except discord.NotFound:
            logger.warning("Membro ou cargo não encontrado durante a reação de cargos.")
            return
        except discord.HTTPException as error:
            logger.warning(
                "Falha HTTP ao atualizar cargo %s para membro %s: status=%s.",
                role.id,
                member.id,
                error.status,
            )
            return

        await self._remove_member_reaction(payload, member)
        logger.info(
            "Cargo %s %s para usuário %s: guild=%s canal=%s mensagem=%s emoji=%s.",
            role.id,
            action,
            member.id,
            guild.id,
            payload.channel_id,
            payload.message_id,
            payload.emoji,
        )

    @app_commands.command(
        name="configurar-cargos", description="Publica as mensagens de seleção de cargos."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def configure_roles(self, interaction: discord.Interaction) -> None:
        """Publica os menus uma única vez e devolve IDs para o administrador configurar."""
        channel_id = self._settings.role_menu.channel_id
        if channel_id is None:
            await interaction.response.send_message(
                "Configure DISCORD_ROLE_MENU_CHANNEL_ID antes de publicar os menus.", ephemeral=True
            )
            return
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "O canal de cargos não foi encontrado.", ephemeral=True
                )
                return
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Não tenho acesso ao canal de cargos.", ephemeral=True
                )
                return
            except discord.HTTPException:
                await interaction.response.send_message(
                    "Não consegui acessar o canal de cargos agora.", ephemeral=True
                )
                return
        if not hasattr(channel, "send"):
            await interaction.response.send_message(
                "O canal configurado não aceita mensagens.", ephemeral=True
            )
            return

        created: list[str] = []
        try:
            for category in self._settings.role_menu.categories:
                if not category.options:
                    continue
                message = await channel.send(self._menu_text(category))
                for option in category.options:
                    await message.add_reaction(option.emoji)
                created.append(f"{category.name}: {message.id}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "Não tenho permissão para enviar mensagens ou reações nesse canal.", ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "Não consegui publicar completamente os menus de cargos.", ephemeral=True
            )
            return

        if not created:
            await interaction.response.send_message(
                "Configure pelo menos um cargo por categoria antes de publicar os menus.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Menus publicados. Copie estes IDs para o .env e reinicie o bot:\n"
            + "\n".join(created),
            ephemeral=True,
        )

    async def _toggle_role(
        self, member: discord.Member, role: discord.Role, category: RoleCategorySettings
    ) -> str:
        """Remove o cargo existente ou o adiciona, respeitando exclusividade."""
        if role in member.roles:
            await member.remove_roles(role, reason="Cargo removido pelo menu de reações")
            return "removido"

        if category.exclusive:
            alternative_role_ids = {option.role_id for option in category.options} - {role.id}
            alternatives = [
                alternative
                for alternative in member.roles
                if alternative.id in alternative_role_ids
            ]
            if alternatives:
                await member.remove_roles(
                    *alternatives, reason="Troca de opção exclusiva no menu de cargos"
                )
        await member.add_roles(role, reason="Cargo adicionado pelo menu de reações")
        return "adicionado"

    async def _get_member(
        self, guild: discord.Guild, payload: discord.RawReactionActionEvent
    ) -> discord.Member | None:
        """Resolve um membro do cache e usa API somente quando necessário."""
        member = payload.member or guild.get_member(payload.user_id)
        if member is not None:
            return member
        try:
            return await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            logger.warning("Membro %s não encontrado para reação de cargos.", payload.user_id)
        except discord.Forbidden:
            logger.warning(
                "Sem permissão para buscar membro %s para reação de cargos.", payload.user_id
            )
        except discord.HTTPException as error:
            logger.warning("Falha ao buscar membro %s: status=%s.", payload.user_id, error.status)
        return None

    async def _remove_member_reaction(
        self, payload: discord.RawReactionActionEvent, member: discord.Member
    ) -> None:
        """Remove somente a reação do usuário depois de uma alteração bem-sucedida."""
        channel = self._bot.get_channel(payload.channel_id)
        try:
            if channel is None:
                channel = await self._bot.fetch_channel(payload.channel_id)
            if not hasattr(channel, "fetch_message"):
                logger.warning("Canal %s não aceita busca de mensagens.", payload.channel_id)
                return
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
        except discord.NotFound:
            logger.warning(
                "Canal ou mensagem %s não encontrado para remover reação.", payload.message_id
            )
        except discord.Forbidden:
            logger.warning("Sem permissão para remover reação do membro %s.", member.id)
        except discord.HTTPException as error:
            logger.warning(
                "Falha ao remover reação do membro %s: status=%s.", member.id, error.status
            )

    def _is_role_assignable(self, guild: discord.Guild, role: discord.Role) -> bool:
        """Confere permissão, cargo gerenciado e posição relativa ao bot."""
        bot_member = guild.me
        if bot_member is None and self._bot.user is not None:
            bot_member = guild.get_member(self._bot.user.id)
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            return False
        return not role.managed and role < bot_member.top_role

    async def _validate_configuration(self) -> None:
        """Registra falhas de configuração sem parar o processo principal."""
        menu = self._settings.role_menu
        if menu.auto_role_id is None and not menu.has_reaction_menu:
            logger.info("Sistema de cargos automáticos e por reação está desativado.")
            return
        if menu.auto_role_id is not None:
            logger.info("Cargo automático configurado com ID %s.", menu.auto_role_id)
        if menu.has_reaction_menu:
            logger.info("Sistema de cargos por reação está ativo no canal %s.", menu.channel_id)
        elif menu.channel_id is not None:
            logger.info(
                "Canal de cargos configurado; execute /configurar-cargos para criar mensagens."
            )

    async def _add_configured_reactions(self) -> None:
        """Garante que os emojis configurados estejam nas mensagens de menu existentes."""
        menu = self._settings.role_menu
        if not menu.has_reaction_menu or menu.channel_id is None:
            return

        channel = self._bot.get_channel(menu.channel_id)
        try:
            if channel is None:
                channel = await self._bot.fetch_channel(menu.channel_id)
            if not hasattr(channel, "fetch_message"):
                logger.error("Canal de cargos %s não permite buscar mensagens.", menu.channel_id)
                return
        except discord.NotFound:
            logger.error("Canal de cargos %s não encontrado.", menu.channel_id)
            return
        except discord.Forbidden:
            logger.warning("Sem acesso ao canal de cargos %s.", menu.channel_id)
            return
        except discord.HTTPException as error:
            logger.warning(
                "Falha ao acessar canal de cargos %s: status=%s.", menu.channel_id, error.status
            )
            return

        for category in menu.categories:
            if category.message_id is None or not category.options:
                continue
            try:
                message = await channel.fetch_message(category.message_id)
                for option in category.options:
                    await message.add_reaction(option.emoji)
            except discord.NotFound:
                logger.error(
                    "Mensagem de cargos %s (%s) não encontrada.", category.name, category.message_id
                )
            except discord.Forbidden:
                logger.warning(
                    "Sem permissão para adicionar reações à mensagem de cargos %s.",
                    category.message_id,
                )
            except discord.HTTPException as error:
                logger.warning(
                    "Falha ao adicionar reações à mensagem de cargos %s: status=%s.",
                    category.message_id,
                    error.status,
                )
            else:
                logger.info(
                    "Emojis configurados adicionados à mensagem de cargos %s (%s).",
                    category.name,
                    category.message_id,
                )

    def _menu_text(self, category: RoleCategorySettings) -> str:
        """Monta uma mensagem com menções por ID, sem depender de nomes fixos."""
        title = CATEGORY_TITLES[category.name]
        options = "\n".join(f"{item.emoji} — <@&{item.role_id}>" for item in category.options)
        suffix = (
            "Escolha apenas uma opção."
            if category.exclusive
            else "Você pode escolher mais de uma opção."
        )
        return f"**{title}**\n{options}\n\n{suffix}\nReaja novamente para remover um cargo."


async def setup(bot: commands.Bot) -> None:
    """Registra o cog de cargos no único cliente Discord existente."""
    discord_bot = cast(DiscordBot, bot)
    await bot.add_cog(RoleManagement(discord_bot, discord_bot.settings))
