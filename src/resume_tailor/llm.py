"""LLM provider layer.

User decision 2026-07-19: wherever the product needs an LLM API, use a cheap
provider (GLM or other OpenAI-compatible endpoints). The Anthropic backend is
kept as a configurable alternative.

Env config:
    RESUME_TAILOR_LLM_PROVIDER   openai-compat (default) | anthropic
    RESUME_TAILOR_LLM_BASE_URL   default https://open.bigmodel.cn/api/paas/v4 (GLM)
    RESUME_TAILOR_LLM_API_KEY    key for the OpenAI-compatible endpoint
    RESUME_TAILOR_MODEL          model id (default glm-4-flash / claude-opus-4-8)
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMBackend(Protocol):
    def complete_structured(
        self, *, system: str, user: str, output_model: type[T]
    ) -> Optional[T]:
        """Return a validated output_model instance, or None if the model refused."""


class OpenAICompatBackend:
    """GLM / any OpenAI-compatible chat-completions endpoint.

    Structured output is enforced by schema-in-prompt + pydantic validation,
    with one retry that feeds the validation error back to the model.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (
            base_url
            or os.environ.get("RESUME_TAILOR_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("RESUME_TAILOR_LLM_API_KEY", "")
        self.model = model or os.environ.get("RESUME_TAILOR_MODEL", "glm-4-flash")
        self.timeout = timeout

    def _chat(self, messages: list[dict]) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "max_tokens": 4096},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_json(text: str) -> str:
        m = _JSON_BLOCK_RE.search(text)
        if m:
            return m.group(1)
        start = text.find("{")
        end = text.rfind("}")
        return text[start : end + 1] if start != -1 and end > start else text

    def complete_structured(
        self, *, system: str, user: str, output_model: type[T]
    ) -> Optional[T]:
        schema = json.dumps(output_model.model_json_schema(), ensure_ascii=False)
        instruction = (
            f"{user}\n\nRespond with ONLY a JSON object matching this schema "
            f"(no prose outside the JSON):\n{schema}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": instruction},
        ]
        for _ in range(2):  # one initial attempt + one repair attempt
            content = self._chat(messages)
            try:
                return output_model.model_validate_json(self._extract_json(content))
            except (ValidationError, ValueError) as exc:
                messages += [
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": f"Invalid JSON for the schema ({exc}). "
                                                "Return ONLY the corrected JSON object."},
                ]
        return None


class AnthropicBackend:
    """Anthropic Messages API with structured outputs + prompt caching."""

    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("RESUME_TAILOR_MODEL", "claude-opus-4-8")

    def complete_structured(
        self, *, system: str, user: str, output_model: type[T]
    ) -> Optional[T]:
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_format=output_model,
        )
        if response.stop_reason == "refusal":
            return None
        return response.parsed_output


def get_backend() -> LLMBackend:
    provider = os.environ.get("RESUME_TAILOR_LLM_PROVIDER", "openai-compat")
    if provider == "anthropic":
        return AnthropicBackend()
    return OpenAICompatBackend()
