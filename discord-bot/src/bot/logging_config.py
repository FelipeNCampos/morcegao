"""Configuração centralizada de logs."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configura logs para o terminal sem registrar dados sensíveis."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    # HTTPX registra URLs completas em INFO. Algumas APIs usam query parameters
    # para tokens e segredos; portanto, essas bibliotecas não podem usar INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # O access log do Uvicorn incluiria o código OAuth na URL de callback.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
