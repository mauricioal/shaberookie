# Shaberookie Implementation Plan

## Overview
This document outlines the concrete steps to implement the shaberookie virtual assistant project, aligning the architectural requirements with an executable plan.

## Key Architectural Drivers
- Renshuu data ingestion and normalization with resilient API handling.
- Level-aware language profile synthesis for JLPT-aligned interactions.
- LLM orchestration via LangChain with enforceable vocabulary constraints.
- Dual chat interfaces (CLI and Gradio) leveraging a shared conversation core.
- Centralized configuration, logging, and persistence for reproducibility.

## Module Ownership and Targets
- [src/shaberookie/common/](src/shaberookie/common/) — shared DTOs, exceptions, logging setup.
- [src/shaberookie/config/](src/shaberookie/config/) — configuration loading, validation, defaults.
- [src/shaberookie/renshuu_client/](src/shaberookie/renshuu_client/) — API client, schema mapping, repository facade.
- [src/shaberookie/profiling/](src/shaberookie/profiling/) — profile builder, JLPT classification strategy, cache integration.
- [src/shaberookie/llm/](src/shaberookie/llm/) — adapters, prompt management, LangChain driver, response validation.
- [src/shaberookie/chat/](src/shaberookie/chat/) — conversation manager, CLI, Gradio app, session policy enforcement.
- [src/shaberookie/storage/](src/shaberookie/storage/) — profile store, conversation log store, cache facade.
- [src/shaberookie/tests/](src/shaberookie/tests/) — unit and integration test suites with fixtures.

## Implementation Phases
1. **Scaffold & Tooling**
   - Initialize [`pyproject.toml`](pyproject.toml) with Poetry (or fallback `requirements.txt`) and define core dependencies (httpx, pydantic, langchain, gradio, python-dotenv, rich/loguru, redis optional).
   - Create baseline package structure under [src/shaberookie/](src/shaberookie/) with `__init__.py` files and placeholder modules.
   - Provide [.env.example](.env.example) enumerating required secrets and configuration keys.
2. **Foundation Layer**
   - Implement shared data models in [src/shaberookie/common/types.py](src/shaberookie/common/types.py) using `pydantic.BaseModel` for validation.
   - Define custom exception hierarchy in [src/shaberookie/common/exceptions.py](src/shaberookie/common/exceptions.py).
   - Configure structured logging via [src/shaberookie/common/logging_config.py](src/shaberookie/common/logging_config.py).
3. **Configuration Management**
   - Build [`ConfigLoader`](src/shaberookie/config/loader.py) to merge YAML defaults, environment overrides, and runtime validation.
   - Document configuration schema in [src/shaberookie/config/config.yaml](src/shaberookie/config/config.yaml).
4. **Renshuu Integration**
   - Implement [`RenshuuApiClient`](src/shaberookie/renshuu_client/client.py) with retry/backoff support.
   - Map raw payloads via [`RenshuuSchemaMapper`](src/shaberookie/renshuu_client/mapper.py) to internal DTOs.
   - Expose higher-level access through [`RenshuuRepository`](src/shaberookie/renshuu_client/repository.py) supporting caching hooks.
5. **Profiling Layer**
   - Introduce [`JLPTClassificationStrategy`](src/shaberookie/profiling/classification_strategy.py) with configurable thresholds.
   - Build [`ProfileBuilder`](src/shaberookie/profiling/builder.py) that aggregates terms and produces `UserLanguageProfile`.
   - Persist outputs via [`ProfileRepository`](src/shaberookie/storage/profile_store.py).
6. **LLM Layer**
   - Define [`LLMAdapter`](src/shaberookie/llm/adapter.py) interface and [`LLMFactory`](src/shaberookie/llm/adapter.py) for provider instantiation.
   - Implement [`PromptTemplateManager`](src/shaberookie/llm/prompt_manager.py) generating system prompts from profiles.
   - Create [`LangChainDriver`](src/shaberookie/llm/langchain_driver.py) wiring LangChain models and memory.
   - Add [`ResponseValidator`](src/shaberookie/llm/validator.py) ensuring vocabulary compliance.
7. **Chat Interfaces**
   - Develop [`ConversationManager`](src/shaberookie/chat/conversation_manager.py) orchestrating sessions, history, and validation loops.
   - Implement CLI client in [src/shaberookie/chat/console_client.py](src/shaberookie/chat/console_client.py).
   - Build Gradio app in [src/shaberookie/chat/gradio_app.py](src/shaberookie/chat/gradio_app.py) with reusable layout components.
   - Provide unified entrypoint [`main.py`](src/shaberookie/main.py) exposing console and Gradio modes.
8. **Persistence & Caching**
   - Implement [`ConversationLogStore`](src/shaberookie/storage/conversation_store.py) with file or SQLite backend.
   - Add optional Redis-based cache adapter under [src/shaberookie/storage/cache.py](src/shaberookie/storage/cache.py) (or in-memory fallback).
9. **Testing & Tooling**
   - Set up pytest configuration in [src/shaberookie/tests/conftest.py](src/shaberookie/tests/conftest.py).
   - Author fixtures for mocked Renshuu responses under [src/shaberookie/tests/fixtures/](src/shaberookie/tests/fixtures/).
   - Implement unit tests covering mappers, builders, prompt manager, validator, and adapters.
   - Provide integration smoke test exercising end-to-end flow with mocks in [src/shaberookie/tests/integration/test_chat_flow.py](src/shaberookie/tests/integration/test_chat_flow.py).
10. **Documentation & Ops**
    - Extend [README.md](README.md) with setup, configuration, and usage instructions.
    - Add developer scripts under [scripts/](scripts/) (e.g., `run_gradio.sh`, `format.sh`).
    - Optional: add Docker support in [docker/Dockerfile](docker/Dockerfile).

## Risk Mitigation
- Use dependency injection to decouple external services, enabling comprehensive tests.
- Mock Renshuu and LLM calls in automated tests to avoid flaky network dependencies.
- Enforce strict typing and validation to catch schema drifts early.

## Success Criteria
- Both CLI and Gradio clients operate using cached profiles when offline.
- All modules expose clear interfaces with type hints and docstrings.
- Test suite validates core data transformations and prompt generation logic.
- Configuration-driven design allows swapping LLM providers without code changes.