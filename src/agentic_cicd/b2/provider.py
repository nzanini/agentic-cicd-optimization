"""OpenAI-compatible chat client. One provider path; tests inject a fake."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from agentic_cicd.b2.settings import B2Settings, estimate_usd


class ProviderError(Exception):
    """Transport or API failure. Never fail-open; caller falls back to B1."""

    def __init__(self, kind: str, message: str) -> None:
        self.kind = kind
        super().__init__(message)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        json_object: bool = False,
    ) -> LLMResponse: ...


class OpenAICompatProvider:
    """Single HTTP client. Works with OpenAI, Groq, or Ollama `/v1`."""

    name = "openai_compatible"

    def __init__(self, settings: B2Settings) -> None:
        if not settings.available:
            raise ProviderError("offline", "provider is not available")
        self.settings = settings
        self.model = settings.model

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        json_object: bool = False,
    ) -> LLMResponse:
        try:
            return self._post(messages, tools, json_object)
        except ProviderError as exc:
            if not _is_http400(exc):
                raise
            if tools:
                try:
                    return self._post(messages, [], json_object)
                except ProviderError as retry_exc:
                    if json_object and _is_http400(retry_exc):
                        return self._post(messages, [], False)
                    raise
            if json_object:
                return self._post(messages, [], False)
            raise

    def _post(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        json_object: bool,
    ) -> LLMResponse:
        body = completion_body(self.settings.model, messages, tools, json_object)
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.settings.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.settings.auth_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_s) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise ProviderError("timeout", "request timed out") from exc
        except urllib.error.HTTPError as exc:
            raise ProviderError(_http_kind(exc.code), _http_message(exc)) from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason)
            kind = "timeout" if "timed out" in reason.lower() else "unavailable"
            raise ProviderError(kind, reason) from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("malformed", "provider returned non-JSON") from exc
        return _parse_completion(data)


def probe_runtime(settings: B2Settings, timeout_s: float = 2.0) -> bool:
    """True if an OpenAI-compatible `/models` endpoint answers."""
    request = urllib.request.Request(
        f"{settings.base_url}/models",
        headers={"Authorization": f"Bearer {settings.auth_token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return 200 <= response.status < 300
    except (TimeoutError, urllib.error.URLError, OSError):
        return False


class FakeProvider:
    """Deterministic stand-in for unit tests. Never opens a network socket."""

    name = "fake"

    def __init__(
        self,
        *,
        model: str = "fake-b2",
        proposal: dict[str, Any] | None = None,
        content: str | None = None,
        error: ProviderError | None = None,
        tool_script: list[LLMResponse] | None = None,
    ) -> None:
        self.model = model
        self._proposal = proposal
        self._content = content
        self._error = error
        self._script = list(tool_script or [])
        self.calls = 0

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        json_object: bool = False,
    ) -> LLMResponse:
        del messages, tools, json_object
        self.calls += 1
        if self._error is not None:
            raise self._error
        if self._script:
            return self._script.pop(0)
        if self._content is not None:
            return LLMResponse(content=self._content)
        if self._proposal is not None:
            return LLMResponse(content=json.dumps(self._proposal))
        raise ProviderError("unavailable", "fake provider has no payload")


def usage_cost_usd(response: LLMResponse) -> float:
    return estimate_usd(response.prompt_tokens, response.completion_tokens)


def completion_body(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    json_object: bool,
) -> dict[str, Any]:
    """Request body for tests. No network."""
    body: dict[str, Any] = {"model": model, "messages": messages, "temperature": 0}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if json_object:
        body["response_format"] = {"type": "json_object"}
    return body


def _is_http400(exc: ProviderError) -> bool:
    return exc.kind == "unavailable" and "HTTP 400" in str(exc)


def _http_kind(code: int) -> str:
    if code in {401, 403}:
        return "auth"
    if code == 429:
        return "rate_limit"
    if code == 408:
        return "timeout"
    return "unavailable"


def _http_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")[:200]
    except OSError:
        body = ""
    return f"HTTP {exc.code} {body}".strip()


def _parse_completion(data: dict[str, Any]) -> LLMResponse:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderError("malformed", "completion has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ProviderError("malformed", "completion has no message")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    calls: list[ToolCall] = []
    for item in message.get("tool_calls") or []:
        if not isinstance(item, dict):
            continue
        function = item.get("function") if isinstance(item.get("function"), dict) else {}
        raw_args = function.get("arguments") or "{}"
        try:
            parsed = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}
        calls.append(
            ToolCall(
                id=str(item.get("id") or f"call_{len(calls)}"),
                name=str(function.get("name") or ""),
                arguments=parsed,
            )
        )
    content = message.get("content")
    return LLMResponse(
        content=content if isinstance(content, str) else None,
        tool_calls=calls,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
    )
