"""Ponto de entrada que supervisiona o bot Discord e o servidor FastAPI."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
import uvicorn
from dotenv import load_dotenv

from bot.client import DiscordBot
from bot.config import ConfigurationError, Settings
from bot.integrations.instagram import InstagramClient
from bot.integrations.instagram_token_store import (
    InstagramTokenStore,
    InstagramTokenStoreError,
    create_instagram_token_store,
)
from bot.integrations.twitch import TwitchClient
from bot.integrations.twitch_auth import TwitchError
from bot.logging_config import configure_logging
from bot.storage import NotificationStore
from bot.web.app import create_web_app

logger = logging.getLogger(__name__)


async def _prepare_twitch_client(settings: Settings) -> TwitchClient | None:
    """Inicializa Twitch sem impedir o Discord de subir se a integração opcional falhar."""
    if not settings.twitch.enabled:
        logger.info("Integração Twitch desativada; o webhook FastAPI não será iniciado.")
        return None

    twitch_client = TwitchClient(settings.twitch)
    try:
        await twitch_client.initialize()
    except TwitchError:
        logger.exception(
            "A integração Twitch não pôde ser inicializada; o Discord continuará ativo."
        )
        await twitch_client.aclose()
        return None
    return twitch_client


def _prepare_instagram_client(
    settings: Settings,
) -> tuple[InstagramClient | None, InstagramTokenStore | None]:
    """Cria Instagram e seu armazenamento sem derrubar os serviços Discord se falhar."""
    if not settings.instagram.enabled:
        logger.info("Integração Instagram desativada; o polling não será iniciado.")
        return None, None
    try:
        token_store = create_instagram_token_store(settings.instagram)
        return InstagramClient(settings.instagram, token_store=token_store), token_store
    except (InstagramTokenStoreError, ValueError):
        logger.exception(
            "A integração Instagram não pôde ser preparada; o Discord continuará ativo."
        )
        return None, None


async def _wait_for_server_start(server: uvicorn.Server, task: asyncio.Task[None]) -> None:
    """Aguarda o webhook ficar disponível e propaga falhas reais do servidor HTTP."""
    while not server.started:
        if task.done():
            task.result()
            raise RuntimeError("O servidor de webhook foi encerrado antes de iniciar.")
        await asyncio.sleep(0.05)


async def run_services(settings: Settings) -> None:
    """Executa Discord e FastAPI no mesmo loop e garante encerramento coordenado."""
    store = NotificationStore(
        Path("data") / "notifications.sqlite3",
        instagram_user_id=settings.instagram.user_id,
    )

    twitch_client = await _prepare_twitch_client(settings)
    instagram_client, instagram_token_store = _prepare_instagram_client(settings)
    bot = DiscordBot(
        settings,
        store=store,
        twitch_client=twitch_client,
        instagram_client=instagram_client,
        instagram_token_store=instagram_token_store,
    )
    app = create_web_app(settings, store, bot)
    server: uvicorn.Server | None = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.web.host,
            port=settings.web.port,
            log_config=None,
            access_log=True,
        )
    )
    server_task: asyncio.Task[None] | None = asyncio.create_task(
        server.serve(), name="fastapi-server"
    )
    bot_task: asyncio.Task[None] | None = None

    try:
        server_started = False
        if server_task is not None:
            try:
                await _wait_for_server_start(server, server_task)
            except Exception:
                logger.exception(
                    "O webhook Twitch não iniciou; o Discord continuará ativo sem EventSub."
                )
                server = None
                server_task = None
                await store.initialize()
            else:
                server_started = True
                logger.info(
                    "API FastAPI disponível em http://%s:%d.", settings.web.host, settings.web.port
                )

        if server_started and twitch_client is not None:
            try:
                created = await twitch_client.ensure_stream_online_subscription()
                status = "criada" if created else "já existente"
                logger.info("Inscrição EventSub da Twitch %s.", status)
            except TwitchError:
                logger.exception("Não foi possível preparar a inscrição EventSub da Twitch.")
        elif twitch_client is None:
            logger.info("Webhook Twitch não será registrado nesta execução.")

        bot_task = asyncio.create_task(bot.start(settings.discord_token), name="discord-bot")

        tasks: set[asyncio.Task[None]] = {bot_task}
        if server_task is not None:
            tasks.add(server_task)
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        if server is not None:
            server.should_exit = True
        if not bot.is_closed():
            await bot.close()
        tasks_to_stop = [task for task in (bot_task, server_task) if task is not None]
        for task in tasks_to_stop:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks_to_stop, return_exceptions=True)


def main() -> None:
    """Carrega o ambiente, valida a configuração e inicia os serviços."""
    load_dotenv()

    try:
        settings = Settings.from_environment()
    except ConfigurationError as error:
        configure_logging("INFO")
        logger.critical("Erro de configuração: %s", error)
        raise SystemExit(1) from error

    configure_logging(settings.log_level)
    try:
        asyncio.run(run_services(settings))
    except discord.LoginFailure as error:
        logger.critical(
            "O Discord rejeitou o token do bot. Verifique DISCORD_TOKEN sem expor seu valor."
        )
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        logger.info("Encerramento solicitado pelo usuário.")
    except Exception as error:
        logger.exception("O bot foi encerrado devido a uma falha inesperada.")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
