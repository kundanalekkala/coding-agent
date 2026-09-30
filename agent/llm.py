"""Picks an LLM backend based on available API keys.

Free options (no paid plan needed):
  - GROQ_API_KEY    Free tier, no credit card required.
                     Sign up: https://console.groq.com
  - GOOGLE_API_KEY  Gemini free tier, no credit card required.
                     Sign up: https://aistudio.google.com/app/apikey

Paid options:
  - ANTHROPIC_API_KEY  Claude
  - OPENAI_API_KEY     GPT-4o

Set ANY ONE of the four. If more than one is set, the order above is
used (Groq first). Override the exact model with the matching *_MODEL
env var -- model names change over time, so check each provider's docs
before relying on the defaults below.
"""

import os


def get_llm(temperature: float = 0.2):
    if os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq

        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        return ChatGroq(model=model, temperature=temperature)

    if os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)

    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return ChatAnthropic(model=model, temperature=temperature)

    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return ChatOpenAI(model=model, temperature=temperature)

    raise RuntimeError(
        "No LLM API key found. Set one of GROQ_API_KEY, GOOGLE_API_KEY "
        "(both free, no card required), ANTHROPIC_API_KEY, or OPENAI_API_KEY "
        "in your .env file."
    )
