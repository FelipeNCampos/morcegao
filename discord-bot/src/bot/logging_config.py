"""Configuração centralizada de logs."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configura logs para o terminal sem registrar dados sensíveis."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
