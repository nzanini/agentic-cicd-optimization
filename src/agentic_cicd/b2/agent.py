"""Read-only agent loop. Produces a proposal; never executes or skips."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from agentic_cicd.b2.prompts import SYSTEM_PROMPT, format_user_prompt, repair_user_prompt
from agentic_cicd.b2.provider import LLMProvider, LLMResponse, ProviderError
from agentic_cicd.b2.schema import ProposalError, validate_proposal
from agentic_cicd.b2.settings import B2Settings, estimate_usd
from agentic_cicd.b2.tools import TOOL_SCHEMAS, Toolbelt, ToolError


@dataclass
class AgentOutcome:
    proposal: dict[str, Any] | None
    error_kind: str | None
    error: str | None
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    raw_response_preview: str | None = None
    repair_attempted: bool = False


def run_agent(
    *,
    context: dict[str, Any],
    tools: Toolbelt,
    provider: LLMProvider,
    settings: B2Settings,
) -> AgentOutcome:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_user_prompt(context)},
    ]
    started = perf_counter()
    tokens_in = 0
    tokens_out = 0
    trace: list[dict[str, Any]] = []
    last_preview: str | None = None
    repair_attempted = False
    allow_tools = settings.enable_tools

    def _cost() -> float:
        return estimate_usd(tokens_in, tokens_out, local=settings.local)

    try:
        for _round in range(settings.max_tool_rounds):
            json_object = (not allow_tools) and (not settings.local)
            schemas = TOOL_SCHEMAS if allow_tools else []
            response = provider.complete(messages, schemas, json_object=json_object)
            tokens_in += response.prompt_tokens
            tokens_out += response.completion_tokens
            last_preview = _preview(response.content)
            if response.tool_calls and allow_tools:
                messages.append(_assistant_tool_message(response))
                for call in response.tool_calls:
                    result = _run_tool(tools, call.name, call.arguments)
                    trace.append(
                        {
                            "tool": call.name,
                            "arguments": _clip_args(call.arguments),
                            "ok": result.get("ok", True),
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": json.dumps(result)[:8000],
                        }
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Using any needed tool results, return only one "
                            "JSON object. schema_version must be the integer 1."
                        ),
                    }
                )
                allow_tools = False
                continue
            try:
                proposal = parse_proposal(response.content)
            except ProposalError as exc:
                if repair_attempted:
                    raise
                repair_attempted = True
                allow_tools = False
                messages.append({"role": "assistant", "content": response.content or ""})
                messages.append({"role": "user", "content": repair_user_prompt(str(exc))})
                continue
            return AgentOutcome(
                proposal=proposal,
                error_kind=None,
                error=None,
                latency_ms=_ms(started),
                prompt_tokens=tokens_in,
                completion_tokens=tokens_out,
                estimated_cost_usd=_cost(),
                tool_trace=trace,
                raw_response_preview=last_preview,
                repair_attempted=repair_attempted,
            )
        return AgentOutcome(
            proposal=None,
            error_kind="malformed",
            error="agent exceeded tool rounds without a proposal",
            latency_ms=_ms(started),
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            estimated_cost_usd=_cost(),
            tool_trace=trace,
            raw_response_preview=last_preview,
            repair_attempted=repair_attempted,
        )
    except ProviderError as exc:
        return AgentOutcome(
            proposal=None,
            error_kind=exc.kind,
            error=str(exc),
            latency_ms=_ms(started),
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            estimated_cost_usd=_cost(),
            tool_trace=trace,
            raw_response_preview=last_preview,
            repair_attempted=repair_attempted,
        )
    except ProposalError as exc:
        return AgentOutcome(
            proposal=None,
            error_kind="malformed",
            error=str(exc),
            latency_ms=_ms(started),
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
            estimated_cost_usd=_cost(),
            tool_trace=trace,
            raw_response_preview=last_preview,
            repair_attempted=repair_attempted,
        )


def _run_tool(tools: Toolbelt, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"ok": True, **tools.dispatch(name, arguments)}
    except (ToolError, OSError, ValueError, KeyError) as exc:
        return {"ok": False, "error": str(exc)}


def parse_proposal(content: str | None) -> dict[str, Any]:
    return validate_proposal(_load_json_object(content))


def _load_json_object(content: str | None) -> Any:
    if not content or not content.strip():
        raise ProposalError("empty model response")
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ProposalError("prose or non-JSON response")
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProposalError("prose or non-JSON response") from exc


def _assistant_tool_message(response: LLMResponse) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": response.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments),
                },
            }
            for call in response.tool_calls
        ],
    }


def _clip_args(arguments: dict[str, Any]) -> dict[str, Any]:
    clipped: dict[str, Any] = {}
    for key, value in arguments.items():
        text = str(value)
        clipped[key] = text if len(text) <= 120 else f"{text[:117]}..."
    return clipped


def _preview(content: str | None) -> str | None:
    if not content:
        return None
    text = content.strip()
    return text if len(text) <= 500 else f"{text[:497]}..."


def _ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
