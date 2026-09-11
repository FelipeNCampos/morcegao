"""Comandos gerais do bot."""

from __future__ import annotations

import logging
from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import DiscordBot
from bot.config import DEFAULT_MAX_MESSAGES_TO_DELETE
from bot.current_twitch_live import CurrentTwitchLive, CurrentTwitchLiveStore
from bot.errors import MISSING_MANAGE_GUILD_PERMISSION_MESSAGE
from bot.integrations.discord_sender import DiscordNotificationError, DiscordNotificationSender
from bot.integrations.twitch import TwitchClient
from bot.integrations.twitch_auth import TwitchError

logger = logging.getLogger(__name__)

NO_OPEN_TWITCH_LIVE_MESSAGE = "Não há nenhuma live aberta para reenviar no momento."
TWITCH_RESEND_ERROR_MESSAGE = "Não foi possível reenviar a notificação da live."
CLEANUP_NOT_FOUND_MESSAGE = "Não encontrei as mensagens que deveriam ser apagadas."
CLEANUP_HTTP_ERROR_MESSAGE = "O Discord não conseguiu apagar as mensagens. Tente novamente."
CLEANUP_DM_MESSAGE = "Este comando só pode ser usado em um servidor."

COMMAND_HELP: dict[str, tuple[str, str, str]] = {
    "ping": (
        "Verifica se o bot está respondendo.",
        "/ping",
        "todos os membros.",
    ),
    "boasvindas": (
        "Envia a mensagem privada de boas-vindas para um usuário.",
        "/boasvindas usuario:@membro",
        "Gerenciar servidor.",
    ),
    "reenviar_live": (
        "Reenvia a notificação da última live aberta.",
        "/reenviar_live",
        "Gerenciar servidor.",
    ),
    "comandos": (
        "Lista os comandos disponíveis e como usá-los.",
        "/comandos",
        "todos os membros.",
    ),
}

PREFIX_COMMAND_HELP: dict[str, tuple[str, str, str]] = {
    "limpar": (
        "Apaga a quantidade informada de mensagens anteriores e também a mensagem do comando.",
        "/limpar <quantidade>",
        "Gerenciar mensagens.",
    ),
}


class General(commands.Cog):
    """Agrupa comandos slash de uso geral."""

    def __init__(
        self,
        notification_sender: DiscordNotificationSender,
        current_twitch_live: CurrentTwitchLiveStore | None = None,
        twitch_client: TwitchClient | None = None,
        max_messages_to_delete: int = DEFAULT_MAX_MESSAGES_TO_DELETE,
        temporary_voice_creator_channel_id: int | None = None,
    ) -> None:
        self._notification_sender = notification_sender
        self._current_twitch_live = current_twitch_live or CurrentTwitchLiveStore()
        self._twitch_client = twitch_client
        self._max_messages_to_delete = max_messages_to_delete
        self._temporary_voice_creator_channel_id = temporary_voice_creator_channel_id

    @app_commands.command(name="ping", description="Verifica se o bot está respondendo.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Responde a um teste simples de conectividade."""
        await interaction.response.send_message("Pong!")

    @app_commands.command(
        name="boasvindas",
        description="Envia uma mensagem privada de boas-vindas para um usuário.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_command(
        self,
        interaction: discord.Interaction,
        user: discord.User,
    ) -> None:
        """Dispara uma DM de boas-vindas para o usuário selecionado."""
        if not interaction.permissions.manage_guild:
            await interaction.response.send_message(
                MISSING_MANAGE_GUILD_PERMISSION_MESSAGE,
                ephemeral=True,
            )
            return

        try:
            await self._notification_sender.send_welcome_message(user)
        except DiscordNotificationError as error:
            await interaction.response.send_message(
                str(error),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "A tentativa de envio da mensagem de boas-vindas foi realizada.",
        )

    @app_commands.command(
        name="reenviar_live",
        description="Reenvia a notificação da última live aberta.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def resend_live_command(self, interaction: discord.Interaction) -> None:
        """Reenvia pelo fluxo habitual a última notificação Twitch ainda aberta."""
        if not interaction.permissions.manage_guild:
            await interaction.response.send_message(
                MISSING_MANAGE_GUILD_PERMISSION_MESSAGE,
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            live = await self._get_current_open_twitch_live()
        except TwitchError:
            logger.exception("Não foi possível confirmar o estado atual da live Twitch.")
            await interaction.followup.send(TWITCH_RESEND_ERROR_MESSAGE, ephemeral=True)
            return
        if live is None:
            await interaction.followup.send(NO_OPEN_TWITCH_LIVE_MESSAGE, ephemeral=True)
            return

        try:
            await self._notification_sender.send_twitch_notification(live.event, live.stream)
        except DiscordNotificationError:
            logger.exception("Falha ao reenviar a notificação manual da live Twitch.")
            await interaction.followup.send(TWITCH_RESEND_ERROR_MESSAGE, ephemeral=True)
            return

        broadcaster = live.event.broadcaster_name or live.event.broadcaster_login
        await interaction.followup.send(
            f"A notificação da live de {broadcaster} foi reenviada com sucesso.",
            ephemeral=True,
        )

    @app_commands.command(name="comandos", description="Lista os comandos disponíveis do bot.")
    async def commands_list(self, interaction: discord.Interaction) -> None:
        """Exibe os comandos efetivamente registrados neste cog e suas formas de uso."""
        embed = discord.Embed(
            title="Comandos do Morcegão",
            description=(
                "Sou o Morcegão, fiel pet do Vampirão. Veja abaixo os comandos disponíveis."
            ),
            colour=0x9146FF,
        )

        for command in self.get_app_commands():
            description, usage, permission = COMMAND_HELP.get(
                command.name,
                (command.description, f"/{command.qualified_name}", "consulte um administrador."),
            )
            embed.add_field(
                name=f"/{command.qualified_name}",
                value=(f"{description}\nUso: `{usage}`\nPermissão: {permission}"),
                inline=False,
            )

        for command in self.get_commands():
            description, usage, permission = PREFIX_COMMAND_HELP.get(
                command.name,
                (
                    command.help or command.brief or "Comando prefixado.",
                    f"/{command.qualified_name}",
                    "",
                ),
            )
            limit_hint = (
                "\nExemplo: `/limpar 10`\nLimite: "
                f"{self._max_messages_to_delete} mensagens por vez."
                if command.name == "limpar"
                else ""
            )
            embed.add_field(
                name=f"/{command.qualified_name}",
                value=(f"{description}\nUso: `{usage}`{limit_hint}\nPermissão: {permission}"),
                inline=False,
            )

        if self._temporary_voice_creator_channel_id is not None:
            embed.add_field(
                name="Canais temporários de voz",
                value=(
                    "Entre no canal criador configurado para o Morcegão criar uma sala "
                    "exclusiva para você. Você será movido automaticamente e poderá "
                    "personalizar nome, limite e permissões da própria sala. Quando todos "
                    "saírem, a sala será excluída automaticamente."
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @commands.command(name="limpar")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def limpar(self, ctx: commands.Context, quantidade: int) -> None:
        """Apaga mensagens do próprio canal, incluindo a mensagem de comando."""
        if quantidade <= 0:
            await ctx.send("Informe uma quantidade maior que zero.", delete_after=5)
            return
        if quantidade > self._max_messages_to_delete:
            await ctx.send(
                f"Você pode apagar no máximo {self._max_messages_to_delete} mensagens por vez.",
                delete_after=5,
            )
            return

        try:
            deleted_messages = await ctx.channel.purge(limit=quantidade + 1)
        except discord.NotFound:
            logger.warning(
                "Mensagens não encontradas durante uma limpeza no canal %s.", ctx.channel.id
            )
            await ctx.send(CLEANUP_NOT_FOUND_MESSAGE, delete_after=5)
            return
        except discord.Forbidden:
            logger.warning("Bot sem permissão para limpar mensagens no canal %s.", ctx.channel.id)
            await ctx.send(
                "Eu preciso da permissão “Gerenciar mensagens” para executar este comando.",
                delete_after=5,
            )
            return
        except discord.HTTPException:
            logger.exception("Falha HTTP ao limpar mensagens no canal %s.", ctx.channel.id)
            await ctx.send(CLEANUP_HTTP_ERROR_MESSAGE, delete_after=5)
            return

        deleted_count = max(len(deleted_messages) - 1, 0)
        logger.info(
            "Limpeza executada pelo usuário %s no canal %s: solicitadas=%d, apagadas=%d.",
            ctx.author.id,
            ctx.channel.id,
            quantidade,
            deleted_count,
        )
        await ctx.send(
            f"🧹 {deleted_count} mensagens foram apagadas.",
            delete_after=5,
        )

    @limpar.error
    async def limpar_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Converte falhas de uso e permissões em respostas temporárias e seguras."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "Você precisa da permissão “Gerenciar mensagens” para usar este comando.",
                delete_after=5,
            )
            return
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "Eu preciso da permissão “Gerenciar mensagens” para executar este comando.",
                delete_after=5,
            )
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "Uso correto: `/limpar <quantidade>`\nExemplo: `/limpar 10`",
                delete_after=5,
            )
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Informe a quantidade de mensagens.\nUso: `/limpar <quantidade>`",
                delete_after=5,
            )
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(CLEANUP_DM_MESSAGE, delete_after=5)
            return

        logger.error(
            "Erro não tratado no comando prefixado /limpar.",
            exc_info=(type(error), error, error.__traceback__),
        )
        await ctx.send(CLEANUP_HTTP_ERROR_MESSAGE, delete_after=5)

    async def _get_current_open_twitch_live(self) -> CurrentTwitchLive | None:
        """Obtém a live atual e confirma que ela ainda está online antes do reenvio."""
        live = await self._current_twitch_live.get_current()
        if live is None:
            return None
        if not live.stream.is_live:
            await self._current_twitch_live.clear_if_current(live)
            return None
        if self._twitch_client is None:
            return live

        latest_stream = await self._twitch_client.get_stream(live.event.broadcaster_user_id)
        return await self._current_twitch_live.update_stream_if_current(live, latest_stream)


async def setup(bot: commands.Bot) -> None:
    """Registra o cog de comandos gerais na extensão."""
    discord_bot = cast(DiscordBot, bot)
    await bot.add_cog(
        General(
            discord_bot.notification_sender,
            discord_bot.current_twitch_live,
            discord_bot.twitch_client,
            discord_bot.settings.max_messages_to_delete,
            discord_bot.settings.temporary_voice_creator_channel_id,
        )
    )
