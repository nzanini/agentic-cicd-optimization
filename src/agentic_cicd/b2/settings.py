"""B2 runtime settings. Credentials come from the environment only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_LOCAL_MODEL = "qwen2.5:3b"
DEFAULT_MIN_CONFIDENCE = 0.7
DEFAULT_MIN_SAVE = 5
DEFAULT_TIMEOUT_S = 30
DEFAULT_MAX_TOOL_ROUNDS = 6
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "0.0.0.0", "::1", "host.docker.internal"})

# Hosted gpt-4o-mini list prices (USD / 1M tokens). Local runs report $0.
USD_PER_M_PROMPT = 0.15
USD_PER_M_COMPLETION = 0.60


@dataclass(frozen=True)
class B2Settings:
    disabled: bool
    api_key: str | None
    base_url: str
    model: str
    min_confidence: float
    min_save: int
    timeout_s: float
    max_tool_rounds: int
    enable_tools: bool

    @property
    def local(self) -> bool:
        return is_local_base_url(self.base_url)

    @property
    def available(self) -> bool:
        if self.disabled:
            return False
        if self.local:
            return True
        return bool(self.api_key)

    @property
    def auth_token(self) -> str:
        return self.api_key or "local"


def is_local_base_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in LOCAL_HOSTS


def load_settings(environ: dict[str, str] | None = None) -> B2Settings:
    env = environ if environ is not None else os.environ
    key = (env.get("B2_API_KEY") or "").strip() or None
    disabled = (env.get("B2_DISABLED") or "").strip().lower() in {"1", "true", "yes"}
    base = (env.get("B2_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    default_model = DEFAULT_LOCAL_MODEL if is_local_base_url(base) else DEFAULT_MODEL
    local = is_local_base_url(base)
    tools_raw = (env.get("B2_ENABLE_TOOLS") or "").strip().lower()
    if tools_raw in {"1", "true", "yes"}:
        enable_tools = True
    elif tools_raw in {"0", "false", "no"}:
        enable_tools = False
    else:
        enable_tools = not local
    return B2Settings(
        disabled=disabled,
        api_key=key,
        base_url=base,
        model=env.get("B2_MODEL") or default_model,
        min_confidence=float(env.get("B2_MIN_CONFIDENCE") or DEFAULT_MIN_CONFIDENCE),
        min_save=int(env.get("B2_MIN_SAVE") or DEFAULT_MIN_SAVE),
        timeout_s=float(env.get("B2_TIMEOUT_S") or DEFAULT_TIMEOUT_S),
        max_tool_rounds=int(env.get("B2_MAX_TOOL_ROUNDS") or DEFAULT_MAX_TOOL_ROUNDS),
        enable_tools=enable_tools,
    )


def estimate_usd(prompt_tokens: int, completion_tokens: int, *, local: bool = False) -> float:
    if local:
        return 0.0
    return (prompt_tokens * USD_PER_M_PROMPT + completion_tokens * USD_PER_M_COMPLETION) / 1_000_000
