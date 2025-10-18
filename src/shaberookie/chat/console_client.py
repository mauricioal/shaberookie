"""
Command-line chat interface for shaberookie.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from shaberookie.chat.conversation_manager import ConversationManager
from shaberookie.common import ConversationMessage, ConversationRole
from shaberookie.common.logging_config import configure_logging
from shaberookie.config.loader import get_settings
from shaberookie.llm.adapter import LLMFactory
from shaberookie.llm.prompt_manager import PromptTemplateManager
from shaberookie.profiling.builder import ProfileBuilder
from shaberookie.renshuu_client.client import RenshuuApiClient
from shaberookie.renshuu_client.repository import RenshuuRepository
from shaberookie.storage.profile_store import FileProfileStore

app = typer.Typer(add_completion=False)
console = Console()


def _print_message(message: ConversationMessage) -> None:
    role_label = (
        "[bold blue]Assistant[/bold blue]"
        if message.role == ConversationRole.ASSISTANT
        else "[bold green]User[/bold green]"
    )
    content = Markdown(message.content)
    console.print(f"{role_label}:", justify="left")
    console.print(content, justify="left")
    console.print()


@app.command()
def chat(user_id: str) -> None:
    """
    Start a console chat session for the specified Renshuu user.
    """
    settings = get_settings()
    configure_logging(log_level=settings.app.log_level, log_dir=Path(settings.app.log_dir))

    profile_store = FileProfileStore(settings.app.profile_store_path)

    async def _run_chat() -> None:
        cache_profile = profile_store.load(user_id)
        if cache_profile:
            profile = cache_profile
        else:
            async with RenshuuApiClient.from_settings(settings.renshuu) as api_client:
                repository = RenshuuRepository(api_client)
                builder = ProfileBuilder(repository)
                profile = await builder.build_profile(user_id)
                profile_store.save(profile)

        prompt_manager = PromptTemplateManager(settings.llm)
        llm_adapter = LLMFactory.create(
            settings.llm.provider,
            settings.llm,
        )
        manager = ConversationManager(llm_adapter, prompt_manager, on_message=_print_message)
        session = manager.start_session(profile)

        console.print("[bold magenta]Chat session started. Type 'exit' to quit.[/bold magenta]")
        while True:
            user_input = console.input("[bold green]You[/bold green]: ")
            if user_input.lower() in {"exit", "quit"}:
                break
            response = await manager.send_user_message(session, user_input)
            profile_store.save(session.profile)
        console.print("[bold magenta]Goodbye![/bold magenta]")

    asyncio.run(_run_chat())


def run_console() -> None:
    """Entrypoint for running the CLI using Typer."""
    app()


if __name__ == "__main__":
    run_console()