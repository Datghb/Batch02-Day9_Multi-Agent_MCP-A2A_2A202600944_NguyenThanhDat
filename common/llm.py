"""Shared LLM factory for all agents."""

import os

from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    """Return a ChatOpenAI-compatible client for the configured provider."""
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider == "gemini":
        return ChatOpenAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            openai_api_key=os.getenv("GEMINI_API_KEY"),
            openai_api_base=os.getenv(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "512")),
        )

    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "512")),
    )
