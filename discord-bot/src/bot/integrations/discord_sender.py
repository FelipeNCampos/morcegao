"""Envio seguro de notificações para canais do Discord."""

from __future__ import annotations

import logging
import random
from pathlib import Path

import discord

from bot.config import Settings
from bot.models import InstagramMedia, TwitchOnlineEvent, TwitchStream

logger = logging.getLogger(__name__)

MAX_INSTAGRAM_CAPTION_LENGTH = 1_000

TWITCH_WELCOME_CHANNEL_FALLBACK = "canal de anúncios da Twitch"
INSTAGRAM_WELCOME_CHANNEL_FALLBACK = "canal de anúncios do Instagram"

BASE_ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

TWITCH_IMAGE_DIR = BASE_ASSETS_DIR / "twitch-banner-live"
WELCOME_IMAGE_DIR = BASE_ASSETS_DIR / "welcome-img"
REELS_FALLBACK_IMAGE_PATH = BASE_ASSETS_DIR / "reels-png" / "usar.png"

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
}


class DiscordNotificationError(RuntimeError):
    """Indica que uma notificação não pôde ser entregue no Discord."""


class TwitchNotificationView(discord.ui.View):
    """View com botão de acesso à live da Twitch."""

    def __init__(self, stream_url: str) -> None:
        super().__init__(timeout=None)

        if not stream_url:
            raise ValueError("A URL da live não pode estar vazia.")

        self.add_item(
            discord.ui.Button(
                label="Assistir live",
                style=discord.ButtonStyle.link,
                url=stream_url,
            )
        )


class InstagramNotificationView(discord.ui.View):
    """View com botão para abrir a publicação original no Instagram."""

    def __init__(self, permalink: str) -> None:
        super().__init__(timeout=None)

        if not permalink:
            raise ValueError("O link da publicação Instagram não pode estar vazio.")

        self.add_item(
            discord.ui.Button(
                label="Ver no Instagram",
                style=discord.ButtonStyle.link,
                url=permalink,
            )
        )


class DiscordNotificationSender:
    """Envia notificações usando o cliente Discord já conectado."""

    def __init__(
        self,
        client: discord.Client,
        settings: Settings,
    ) -> None:
        self._client = client
        self._settings = settings

    @staticmethod
    def _choose_image(directory: Path) -> Path | None:
        """Escolhe aleatoriamente uma imagem compatível no diretório."""
        if not directory.is_dir():
            logger.warning(
                "Diretório de imagens não encontrado: %s",
                directory,
            )
            return None

        image_paths = [
            path
            for path in directory.iterdir()
            if (path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS)
        ]

        if not image_paths:
            logger.warning(
                "Nenhuma imagem compatível encontrada em %s",
                directory,
            )
            return None

        return random.choice(image_paths)

    def _choose_twitch_image(self) -> Path | None:
        """Escolhe uma imagem aleatória para a notificação da Twitch."""
        return self._choose_image(TWITCH_IMAGE_DIR)

    def _choose_welcome_image(self) -> Path | None:
        """Escolhe uma imagem aleatória para a mensagem de boas-vindas."""
        return self._choose_image(WELCOME_IMAGE_DIR)

    async def send_twitch_notification(
        self,
        event: TwitchOnlineEvent,
        stream: TwitchStream,
    ) -> None:
        """Envia uma notificação formatada para uma live iniciada."""
        channel_id = self._settings.twitch.notification_channel_id

        if channel_id is None:
            raise DiscordNotificationError("O canal de notificações da Twitch não foi configurado.")

        stream_url = stream.url

        if not stream_url:
            raise DiscordNotificationError("A URL da live não está disponível.")

        broadcaster_name = event.broadcaster_name or event.broadcaster_login

        stream_title = stream.title or "Título não disponível"

        content = f"@everyone\n**𑣲{broadcaster_name} está ao vivo na Twitch!**\n{stream_title}"

        embed = discord.Embed(
            title="Live na Twitch",
            description=stream_title,
            colour=0x9146FF,
            url=stream_url,
        )

        view = TwitchNotificationView(stream_url)
        image_path = self._choose_twitch_image()

        if image_path is None:
            await self._send_to_channel(
                channel_id,
                content,
                embed,
                view=view,
            )
            return

        file = discord.File(
            image_path,
            filename=image_path.name,
        )

        embed.set_image(
            url=f"attachment://{image_path.name}",
        )

        await self._send_to_channel(
            channel_id,
            content,
            embed,
            file=file,
            view=view,
        )

    async def send_instagram_notification(
        self,
        media: InstagramMedia,
    ) -> None:
        """Envia uma notificação para uma nova publicação do Instagram."""
        channel_id = self._settings.instagram.notification_channel_id

        if channel_id is None:
            raise DiscordNotificationError(
                "O canal de notificações do Instagram não foi configurado."
            )

        caption = self._truncate_caption(media.caption)
        media_label = self._instagram_media_label(media)
        title = f"O Vampirão adicionou novo {media_label} no Instagram"
        content = f"📸 **{title}**"

        embed = discord.Embed(
            description=caption or None,
            colour=0xE4405F,
            url=media.permalink or None,
        )

        file: discord.File | None = None
        if media_label == "reels":
            # media_url de Reel costuma apontar para vídeo e não pode ser renderizada
            # como imagem pelo embed. Preferir a miniatura; sem ela, anexar o fallback.
            if media.thumbnail_url:
                embed.set_image(url=media.thumbnail_url)
            else:
                file = self._reels_fallback_file()
                if file is not None:
                    embed.set_image(url=f"attachment://{REELS_FALLBACK_IMAGE_PATH.name}")
        elif media.media_url:
            embed.set_image(url=media.media_url)
        elif media.thumbnail_url:
            embed.set_thumbnail(url=media.thumbnail_url)

        view = InstagramNotificationView(media.permalink) if media.permalink else None
        await self._send_to_channel(channel_id, content, embed, file=file, view=view)

    @staticmethod
    def _instagram_media_label(media: InstagramMedia) -> str:
        """Converte o tipo de produto Instagram em rótulo legível da notificação."""
        product_type = (media.media_product_type or media.media_type or "").upper()
        return "reels" if product_type == "REELS" else "post"

    @staticmethod
    def _reels_fallback_file() -> discord.File | None:
        """Fornece a imagem local do gato quando o Reel não trouxer mídia da API."""
        if not REELS_FALLBACK_IMAGE_PATH.is_file():
            logger.warning("Imagem fallback de Reel não encontrada: %s", REELS_FALLBACK_IMAGE_PATH)
            return None
        return discord.File(REELS_FALLBACK_IMAGE_PATH, filename=REELS_FALLBACK_IMAGE_PATH.name)

    async def send_welcome_message(
        self,
        user: discord.User | discord.Member,
    ) -> None:
        """Envia por DM uma apresentação do Morcegão para o usuário."""
        user_name = self._display_name(user)

        twitch_channel_name = await self._resolve_channel_name(
            self._settings.twitch.notification_channel_id,
            TWITCH_WELCOME_CHANNEL_FALLBACK,
        )

        instagram_channel_name = await self._resolve_channel_name(
            self._settings.instagram.notification_channel_id,
            INSTAGRAM_WELCOME_CHANNEL_FALLBACK,
        )

        content = (
            f"Bem vindo ao servidor {user_name},\n\n"
            "Me chamo Morcegão e vou te manter por dentro de todas "
            "as novidades sobre o Vampirão,\n"
            f"vou te avisar das lives pelo canal {twitch_channel_name} "
            f"e de posts novos pelo canal {instagram_channel_name}, "
            "ambos no Discord O vampirão.\n"
            "Fique à vontade pra interagir com a comunidade e se divertir."
        )

        final_message = "PS: O tipo sanguíneo do O vampirão é A+"
        image_path = self._choose_welcome_image()

        try:
            if image_path is None:
                await user.send(
                    content=f"{content}\n\n{final_message}",
                )
                return

            file = discord.File(
                image_path,
                filename=image_path.name,
            )

            embed = discord.Embed(
                colour=0x9146FF,
            )

            embed.set_image(
                url=f"attachment://{image_path.name}",
            )

            await user.send(
                content=content,
                embed=embed,
                file=file,
            )

            await user.send(
                content=final_message,
            )

        except discord.Forbidden:
            logger.warning("Não foi possível enviar a DM de boas-vindas para o usuário.")
            raise DiscordNotificationError(
                "Não foi possível enviar a mensagem privada; o usuário pode ter bloqueado DMs."
            ) from None

        except discord.NotFound:
            logger.warning("Usuário não encontrado ao enviar a DM de boas-vindas.")
            raise DiscordNotificationError(
                "Não foi possível encontrar o usuário para enviar a mensagem privada."
            ) from None

        except discord.HTTPException as error:
            logger.error(
                "Falha HTTP ao enviar a DM de boas-vindas: %s",
                error.status,
            )
            raise DiscordNotificationError(
                "Não foi possível enviar a mensagem privada. Tente novamente mais tarde."
            ) from None

    async def _resolve_channel_name(
        self,
        channel_id: int | None,
        fallback: str,
    ) -> str:
        """Obtém o nome atual de um canal ou retorna um fallback."""
        if channel_id is None:
            return fallback

        channel = self._client.get_channel(channel_id)

        if channel is None:
            try:
                channel = await self._client.fetch_channel(channel_id)

            except discord.NotFound:
                logger.warning("Canal de boas-vindas configurado não foi encontrado.")
                return fallback

            except discord.Forbidden:
                logger.warning("Sem permissão para acessar o canal configurado.")
                return fallback

            except discord.HTTPException as error:
                logger.warning(
                    "Falha HTTP ao buscar canal de boas-vindas: %s",
                    error.status,
                )
                return fallback

        channel_name = getattr(channel, "name", None)

        if isinstance(channel_name, str) and channel_name.strip():
            return channel_name

        return fallback

    @staticmethod
    def _display_name(user: discord.abc.User) -> str:
        """Retorna o nome público mais adequado do usuário."""
        display_name = getattr(user, "display_name", None)

        if isinstance(display_name, str) and display_name.strip():
            return display_name

        username = getattr(user, "name", None)

        if isinstance(username, str) and username.strip():
            return username

        return "membro"

    async def _send_to_channel(
        self,
        channel_id: int,
        content: str,
        embed: discord.Embed,
        *,
        file: discord.File | None = None,
        view: discord.ui.View | None = None,
    ) -> None:
        """Envia conteúdo, embed, arquivo e componentes para um canal."""
        channel = self._client.get_channel(channel_id)

        if channel is None:
            try:
                channel = await self._client.fetch_channel(channel_id)

            except discord.NotFound:
                logger.error("O canal configurado para notificações não foi encontrado.")
                raise DiscordNotificationError("O canal configurado não foi encontrado.") from None

            except discord.Forbidden:
                logger.error("O bot não tem permissão para acessar o canal.")
                raise DiscordNotificationError(
                    "Permissão insuficiente para acessar o canal."
                ) from None

            except discord.HTTPException as error:
                logger.error(
                    "Falha HTTP ao buscar o canal de notificações: %s",
                    error.status,
                )
                raise DiscordNotificationError(
                    "Não foi possível acessar o canal de notificações."
                ) from None

        send = getattr(channel, "send", None)

        if not callable(send):
            raise DiscordNotificationError(
                "O ID configurado não pertence a um canal que aceita mensagens."
            )

        try:
            await send(
                content=content,
                embed=embed,
                file=file,
                view=view,
            )

        except discord.Forbidden:
            logger.error("O bot não tem permissão para enviar no canal.")
            raise DiscordNotificationError("Permissão insuficiente para enviar no canal.") from None

        except discord.HTTPException as error:
            logger.error(
                "Falha HTTP ao enviar a notificação no Discord: %s",
                error.status,
            )
            raise DiscordNotificationError("Não foi possível enviar a notificação.") from None

    @staticmethod
    def _truncate_caption(
        caption: str | None,
    ) -> str:
        """Evita exceder os limites de texto do embed."""
        if not caption:
            return "Sem legenda."

        if len(caption) <= MAX_INSTAGRAM_CAPTION_LENGTH:
            return caption

        return f"{caption[: MAX_INSTAGRAM_CAPTION_LENGTH - 1]}…"
