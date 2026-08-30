"""B2 runner: B1 first, optional agent, verifier, then existing job bodies."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentic_cicd.b0.graph import JOBS
from agentic_cicd.b0.runner import RunResult
from agentic_cicd.b1.planner import DECISION_RUN, Plan, plan_jobs
from agentic_cicd.b2.agent import run_agent
from agentic_cicd.b2.context import build_context
from agentic_cicd.b2.execute import execute_plan
from agentic_cicd.b2.policy import InvocationDecision, decide_invocation
from agentic_cicd.b2.prompts import PROMPT_ID
from agentic_cicd.b2.provider import LLMProvider, OpenAICompatProvider
from agentic_cicd.b2.settings import B2Settings, load_settings
from agentic_cicd.b2.tools import Toolbelt
from agentic_cicd.b2.verifier import verify_proposal
from agentic_cicd.ranker.io_util import read_json, write_json


def run_b2(
    *,
    source: str,
    target: str,
    fixtures_dir: Path,
    work_dir: Path,
    registry_dir: Path,
    changed_paths: list[str] | None,
    cache_dir: Path | None = None,
    workspace_dir: Path | None = None,
    repo_dir: Path | None = None,
    diffs: dict[str, str] | None = None,
    settings: B2Settings | None = None,
    provider: LLMProvider | None = None,
) -> RunResult:
    run_id = str(uuid4())
    cfg = settings if settings is not None else load_settings()
    workspace = workspace_dir or fixtures_dir.parent
    b1 = plan_jobs(
        source=source,
        target=target,
        changed_paths=changed_paths,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
    )
    invocation = decide_invocation(
        b1, changed_paths=changed_paths, settings=cfg, workspace=workspace, repo=repo_dir
    )
    record = _empty_record(run_id, invocation, cfg, provider)
    final = b1
    verifier_dict: dict[str, Any] = {
        "used_proposal": False,
        "fallback_reason": None,
        "accepted_novel": [],
        "rejected_novel": [],
        "notes": [],
        "final_run": list(b1.run),
    }

    if invocation.invoke:
        outcome, used_provider = _invoke(
            b1=b1,
            source=source,
            target=target,
            changed_paths=changed_paths,
            fixtures_dir=fixtures_dir,
            cache_dir=cache_dir,
            registry_dir=registry_dir,
            workspace=workspace,
            repo=repo_dir,
            diffs=diffs or {},
            settings=cfg,
            provider=provider,
            work_dir=work_dir,
        )
        record["agent_invoked"] = True
        record["provider"] = used_provider.name
        record["model"] = used_provider.model
        record["latency_ms"] = outcome.latency_ms
        record["prompt_tokens"] = outcome.prompt_tokens
        record["completion_tokens"] = outcome.completion_tokens
        record["estimated_cost_usd"] = outcome.estimated_cost_usd
        record["tool_trace"] = outcome.tool_trace
        record["proposal"] = outcome.proposal
        record["agent_error"] = outcome.error
        record["raw_response_preview"] = outcome.raw_response_preview
        record["repair_attempted"] = outcome.repair_attempted
        record["prompt_id"] = PROMPT_ID
        verified = verify_proposal(
            b1=b1,
            proposal=outcome.proposal,
            fallback_reason=outcome.error_kind,
            source=source,
            target=target,
            changed_paths=changed_paths,
            fixtures_dir=fixtures_dir,
            cache_dir=cache_dir,
            registry_dir=registry_dir,
            workspace=workspace,
            repo=repo_dir,
            min_confidence=cfg.min_confidence,
        )
        final = verified.plan
        verifier_dict = verified.as_dict()
        record["fallback_reason"] = verified.fallback_reason
        if outcome.error_kind and outcome.proposal is None:
            record["fallback_reason"] = outcome.error_kind
            verifier_dict["fallback_reason"] = outcome.error_kind
    else:
        record["fallback_reason"] = None

    result = execute_plan(
        plan=final,
        source=source,
        target=target,
        fixtures_dir=fixtures_dir,
        work_dir=work_dir,
        registry_dir=registry_dir,
        cache_dir=cache_dir,
        run_id=run_id,
        system="agentic",
    )
    b1_cost = _plan_cost(b1)
    record.update(
        {
            "invocation_reason": invocation.reason,
            "invocation_reason_code": invocation.reason_code,
            "expected_save": invocation.expected_save,
            "actual_save": b1_cost - result.simulated_cost_total,
            "verifier": verifier_dict,
            "novel_accept": verifier_dict.get("accepted_novel") or [],
            "novel_reject": verifier_dict.get("rejected_novel") or [],
            "final_plan": [
                item.job_name for item in final.decisions if item.decision == DECISION_RUN
            ],
            "final_executed_jobs": [
                job.job_name for job in result.jobs if job.status == "executed"
            ],
            "b1_run": list(b1.run),
            "b1_simulated_cost": b1_cost,
            "b2_simulated_cost": result.simulated_cost_total,
        }
    )
    write_json(work_dir / "b2_record.json", record)
    return result


def _invoke(
    *,
    b1: Plan,
    source: str,
    target: str,
    changed_paths: list[str] | None,
    fixtures_dir: Path,
    cache_dir: Path | None,
    registry_dir: Path | None,
    workspace: Path,
    repo: Path | None,
    diffs: dict[str, str],
    settings: B2Settings,
    provider: LLMProvider | None,
    work_dir: Path,
) -> tuple[Any, LLMProvider]:
    used = provider if provider is not None else OpenAICompatProvider(settings)
    context = build_context(
        source=source,
        target=target,
        changed_paths=changed_paths,
        plan=b1,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
        workspace=workspace,
        repo=repo,
    )
    tools = Toolbelt(
        plan=b1,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
        workspace=workspace,
        repo=repo,
        diffs=diffs,
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    write_json(work_dir / "agent_context.json", context)
    outcome = run_agent(context=context, tools=tools, provider=used, settings=settings)
    return outcome, used


def _empty_record(
    run_id: str,
    invocation: InvocationDecision,
    settings: B2Settings,
    provider: LLMProvider | None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "system": "agentic",
        "agent_invoked": False,
        "invocation_reason": invocation.reason,
        "invocation_reason_code": invocation.reason_code,
        "expected_save": invocation.expected_save,
        "actual_save": 0,
        "provider": (
            provider.name
            if provider is not None
            else ("openai_compatible" if settings.available else "none")
        ),
        "model": provider.model if provider is not None else settings.model,
        "latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "estimated_cost_usd": 0.0,
        "proposal": None,
        "verifier": {},
        "novel_accept": [],
        "novel_reject": [],
        "final_plan": [],
        "final_executed_jobs": [],
        "fallback_reason": None,
        "tool_trace": [],
        "agent_error": None,
        "raw_response_preview": None,
        "repair_attempted": False,
        "prompt_id": PROMPT_ID,
        "enable_tools": settings.enable_tools,
        "started_at": datetime.now(UTC).isoformat(),
        "local": settings.local,
        "api_cost_usd": 0.0 if settings.local else None,
        "base_url": settings.base_url,
    }


def record_from_result(result: RunResult) -> dict[str, Any]:
    path = result.work_dir / "b2_record.json"
    if not path.is_file():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _plan_cost(plan: Plan) -> int:
    return sum(JOBS[name].simulated_cost for name in plan.run if name in JOBS)
