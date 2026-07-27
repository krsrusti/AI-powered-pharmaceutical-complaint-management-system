"""
Groq LLM client wrapper.

Two entry points are exposed:
  - call_fast_model()       -> gemma2-9b-it, for extraction/completeness
  - call_reasoning_model()  -> llama-3.3-70b-versatile, for risk assessment

Both return parsed JSON (dict), not raw text. LLM output is inherently
unreliable — it can wrap JSON in markdown fences, add preamble text, or
occasionally return malformed JSON. This wrapper is the single place that
absorbs that unreliability so every node downstream can assume it receives
a clean dict, rather than every node re-implementing its own parsing/retry logic.
"""

import json
import re
from typing import Optional

from groq import Groq

from config import settings

_client: Optional[Groq] = None


class LLMExtractionError(Exception):
    """Raised when the LLM fails to return parseable JSON after all retries."""


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _strip_json_fences(text: str) -> str:
    """LLMs often wrap JSON in ```json ... ``` even when told not to. Strip it."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_model(system_prompt: str, user_prompt: str, model: str) -> dict:
    client = get_client()
    last_error: Optional[Exception] = None

    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=settings.LLM_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_text = response.choices[0].message.content
            cleaned = _strip_json_fences(raw_text)
            return json.loads(cleaned)

        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            last_error = e
            if attempt < settings.LLM_MAX_RETRIES:
                # On retry, be more explicit about the JSON-only requirement —
                # the model likely added preamble/explanation text.
                user_prompt = (
                    user_prompt
                    + "\n\nIMPORTANT: Respond with ONLY valid JSON. "
                      "No explanation, no markdown formatting, no preamble."
                )
                continue

        except Exception as e:
            last_error = e
            break

    raise LLMExtractionError(
        f"Failed to get valid JSON from model '{model}' after "
        f"{settings.LLM_MAX_RETRIES + 1} attempt(s): {last_error}"
    )


def call_fast_model(system_prompt: str, user_prompt: str) -> dict:
    """gemma2-9b-it — extraction, field updates, completeness checks."""
    return _call_model(system_prompt, user_prompt, model=settings.GROQ_MODEL_FAST)


def call_reasoning_model(system_prompt: str, user_prompt: str) -> dict:
    """llama-3.3-70b-versatile — risk assessment reasoning."""
    return _call_model(system_prompt, user_prompt, model=settings.GROQ_MODEL_REASONING)