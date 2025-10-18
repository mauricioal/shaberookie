"""
Application entry point for shaberookie.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from shaberookie.chat.console_client import run_console
from shaberookie.chat.gradio_app import build_gradio_app
from shaberookie.common.logging_config import configure_logging
from shaberookie.config.loader import get_settings

app = typer.Typer()


@app.command()
def gradio(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        help="Host interface for the Gradio server.",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        help="Port to bind the Gradio server to.",
    ),
    share: bool = typer.Option(
        False,
        "--share",
        help="Enable the public Gradio sharing tunnel.",
        is_flag=True,
    ),
) -> None:
    """Launch the Gradio interface."""
    settings = get_settings()
    configure_logging(log_level=settings.app.log_level, log_dir=Path(settings.app.log_dir))
    gradio_settings = settings.chat.gradio
    blocks = build_gradio_app()

    resolved_share = share or gradio_settings.share
    resolved_host = host or gradio_settings.host
    resolved_port = port or gradio_settings.port

    # When sharing externally, let Gradio pick an available port/host automatically.
    if resolved_share:
        resolved_host = None
        resolved_port = None

    blocks.launch(
        server_name=resolved_host,
        server_port=resolved_port,
        share=True,
        show_api=False,
    )


@app.command()
def console() -> None:
    """Launch the console client."""
    run_console()


def app_entry() -> None:
    """Poetry console script hook."""
    app()


if __name__ == "__main__":
    app_entry()