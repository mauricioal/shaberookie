"""
Gradio-based chat interface for shaberookie.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import gradio as gr

from shaberookie.chat.conversation_manager import ConversationManager, ConversationSession
from shaberookie.common import ConversationMessage
from shaberookie.common.logging_config import configure_logging
from shaberookie.config.loader import get_settings
from shaberookie.llm.adapter import LLMFactory
from shaberookie.llm.prompt_manager import PromptTemplateManager
from shaberookie.profiling.builder import ProfileBuilder
from shaberookie.renshuu_client.client import RenshuuApiClient
from shaberookie.renshuu_client.repository import RenshuuRepository
from shaberookie.storage.profile_store import FileProfileStore


async def _load_profile(user_id: str):
    settings = get_settings()
    profile_store = FileProfileStore(settings.app.profile_store_path)
    cached = profile_store.load(user_id)
    if cached:
        return cached
    async with RenshuuApiClient.from_settings(settings.renshuu) as client:
        repository = RenshuuRepository(client)
        builder = ProfileBuilder(repository)
        profile = await builder.build_profile(user_id)
        profile_store.save(profile)
        return profile


async def _build_session(user_id: str) -> ConversationSession:
    settings = get_settings()
    prompt_manager = PromptTemplateManager(settings.llm)
    llm_adapter = LLMFactory.create(settings.llm.provider, settings.llm)
    manager = ConversationManager(llm_adapter, prompt_manager)
    profile = await _load_profile(user_id)
    return manager.start_session(profile)


def _format_history(messages: list[ConversationMessage]) -> list[tuple[str, str]]:
    pairs = []
    user_buffer: Optional[str] = None
    for message in messages:
        if message.role == message.role.USER:
            user_buffer = message.content
        elif message.role == message.role.ASSISTANT and user_buffer is not None:
            pairs.append((user_buffer, message.content))
            user_buffer = None
    return pairs


def build_gradio_app() -> gr.Blocks:
    settings = get_settings()
    configure_logging(log_level=settings.app.log_level, log_dir=Path(settings.app.log_dir))

    with gr.Blocks(theme="soft") as demo:
        gr.Markdown("# 喋rookie — Level-aware Japanese Conversation Partner")
        user_id_input = gr.Textbox(label="Renshuu User ID", placeholder="Enter your user id")
        status_output = gr.Markdown()
        chat = gr.Chatbot(show_copy_button=True)
        message_input = gr.Textbox(label="Your Message", placeholder="Type in Japanese or English…")
        send_button = gr.Button("Send")
        clear_button = gr.Button("Clear Conversation")

        state = gr.State()

        async def initialize(user_id: str):
            if not user_id:
                return gr.Markdown.update(value="Please provide a user ID."), None, None
            session = await _build_session(user_id)
            state_value = {
                "user_id": user_id,
                "session": session,
            }
            history = _format_history(session.messages)
            return (
                gr.Markdown.update(value=f"Loaded profile for **{user_id}** (JLPT {session.profile.jlpt_level})."),
                history,
                state_value,
            )

        async def respond(user_message: str, state_value):
            if not state_value:
                return gr.Chatbot.update(), state_value, gr.Markdown.update(
                    value="Initialize session first."
                )
            session: ConversationSession = state_value["session"]
            manager = ConversationManager(
                LLMFactory.create(get_settings().llm.provider, get_settings().llm),
                PromptTemplateManager(get_settings().llm),
            )
            manager._prompt_manager = PromptTemplateManager(get_settings().llm)
            response = await manager.send_user_message(session, user_message)
            history = _format_history(session.messages)
            return gr.Chatbot.update(value=history), state_value, gr.Markdown.update(value="")

        async def clear_session(state_value):
            return gr.Chatbot.update(value=[]), None, gr.Markdown.update(value="Session cleared.")

        user_id_input.submit(initialize, inputs=user_id_input, outputs=[status_output, chat, state])
        send_button.click(
            respond,
            inputs=[message_input, state],
            outputs=[chat, state, status_output],
        )
        clear_button.click(clear_session, inputs=state, outputs=[chat, state, status_output])

    return demo