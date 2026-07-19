import httpx
import pytest
from pydantic import BaseModel

from resume_tailor import llm
from resume_tailor.llm import OpenAICompatBackend


class Verdict(BaseModel):
    label: str
    score: int


def _backend() -> OpenAICompatBackend:
    return OpenAICompatBackend(
        base_url="https://glm.example/api/v4", api_key="test-key", model="glm-4.5-flash"
    )


def _fake_post(responses: list[str]):
    """Return a stand-in for httpx.post yielding canned chat completions."""
    calls = []

    def post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json})
        content = responses[min(len(calls) - 1, len(responses) - 1)]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
            request=httpx.Request("POST", url),
        )

    post.calls = calls
    return post


def test_extract_json_handles_fences_and_prose():
    extract = OpenAICompatBackend._extract_json
    assert extract('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert extract('Here you go: {"a": 1} hope that helps') == '{"a": 1}'
    assert extract('{"a": 1}') == '{"a": 1}'


def test_complete_structured_parses_valid_response(monkeypatch):
    post = _fake_post(['{"label": "fits", "score": 80}'])
    monkeypatch.setattr(llm.httpx, "post", post)
    result = _backend().complete_structured(system="s", user="u", output_model=Verdict)
    assert result == Verdict(label="fits", score=80)
    body = post.calls[0]["json"]
    assert body["model"] == "glm-4.5-flash"
    assert post.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert "schema" in body["messages"][1]["content"].lower()


def test_complete_structured_repairs_invalid_json_once(monkeypatch):
    post = _fake_post(["not json at all", '{"label": "fits", "score": 80}'])
    monkeypatch.setattr(llm.httpx, "post", post)
    result = _backend().complete_structured(system="s", user="u", output_model=Verdict)
    assert result == Verdict(label="fits", score=80)
    assert len(post.calls) == 2
    # repair turn carries the error back to the model
    assert "Invalid JSON" in post.calls[1]["json"]["messages"][-1]["content"]


def test_complete_structured_gives_up_after_repair(monkeypatch):
    post = _fake_post(["garbage", "still garbage"])
    monkeypatch.setattr(llm.httpx, "post", post)
    assert _backend().complete_structured(system="s", user="u", output_model=Verdict) is None


def test_get_backend_defaults_to_openai_compat(monkeypatch):
    monkeypatch.delenv("RESUME_TAILOR_LLM_PROVIDER", raising=False)
    assert isinstance(llm.get_backend(), OpenAICompatBackend)
