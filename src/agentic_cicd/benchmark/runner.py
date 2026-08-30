"""Run a scenario suite against B0, B1, B2, or the comparison ladder.

Default file is the frozen S01–S14 suite. Pass another JSON for S16–S18.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any
from uuid import uuid4

from agentic_cicd.b0 import run_b0
from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b1.runner import decisions_from_result, run_b1
from agentic_cicd.b2.runner import record_from_result, run_b2
from agentic_cicd.benchmark.apply import apply_changes, change_set, materialize_workspace
from agentic_cicd.benchmark.compare import compare_run
from agentic_cicd.benchmark.schema import Scenario, load_scenarios
from agentic_cicd.ranker.io_util import write_json

SYSTEM_BASELINE = "baseline"
SYSTEM_OPTIMIZED = "optimized"
SYSTEM_COMPARE = "compare"
SYSTEM_AGENTIC = "agentic"
SYSTEM_LADDER = "ladder"
SUPPORTED_SYSTEMS = (
    SYSTEM_BASELINE,
    SYSTEM_OPTIMIZED,
    SYSTEM_COMPARE,
    SYSTEM_AGENTIC,
    SYSTEM_LADDER,
)


@dataclass
class BenchmarkReport:
    output_dir: Path
    payload: dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_benchmark(
    *,
    output_dir: Path,
    repo: Path | None = None,
    scenarios_path: Path | None = None,
    system: str = SYSTEM_BASELINE,
) -> BenchmarkReport:
    if system not in SUPPORTED_SYSTEMS:
        msg = f"unsupported system {system!r}; expected {SUPPORTED_SYSTEMS}"
        raise ValueError(msg)
    root = repo or repo_root()
    scenarios = load_scenarios(scenarios_path)
    if system == SYSTEM_COMPARE:
        return _run_compare(root, output_dir, scenarios)
    if system == SYSTEM_LADDER:
        return _run_ladder(root, output_dir, scenarios)

    started = datetime.now(UTC)
    rows = [_run_one(root, output_dir, scenario, system) for scenario in scenarios]
    payload = _suite_payload(system, started, rows, _single_system_notes(system))
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "benchmark_results.json", payload)
    return BenchmarkReport(output_dir=output_dir, payload=payload)


def _run_compare(root: Path, output_dir: Path, scenarios: list[Scenario]) -> BenchmarkReport:
    started = datetime.now(UTC)
    b0_dir = output_dir / "b0"
    b1_dir = output_dir / "b1"
    b0_rows = [_run_one(root, b0_dir, scenario, SYSTEM_BASELINE) for scenario in scenarios]
    b1_rows = [_run_one(root, b1_dir, scenario, SYSTEM_OPTIMIZED) for scenario in scenarios]
    b0_notes = _single_system_notes(SYSTEM_BASELINE)
    b1_notes = _single_system_notes(SYSTEM_OPTIMIZED)
    b0_payload = _suite_payload(SYSTEM_BASELINE, started, b0_rows, b0_notes)
    b1_payload = _suite_payload(SYSTEM_OPTIMIZED, started, b1_rows, b1_notes)
    comparison = _compare_payloads(b0_payload, b1_payload)
    payload = {
        "run_id": str(uuid4()),
        "system": SYSTEM_COMPARE,
        "started_at": started.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "scenario_count": len(scenarios),
        "baseline": b0_payload,
        "optimized": b1_payload,
        "comparison": comparison,
        "notes": _compare_notes(scenarios),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "benchmark_results.json", payload)
    write_json(b0_dir / "benchmark_results.json", b0_payload)
    write_json(b1_dir / "benchmark_results.json", b1_payload)
    write_json(output_dir / "comparison.json", comparison)
    return BenchmarkReport(output_dir=output_dir, payload=payload)


def _run_ladder(root: Path, output_dir: Path, scenarios: list[Scenario]) -> BenchmarkReport:
    started = datetime.now(UTC)
    b0_dir = output_dir / "b0"
    b1_dir = output_dir / "b1"
    b2_dir = output_dir / "b2"
    b0_rows = [_run_one(root, b0_dir, scenario, SYSTEM_BASELINE) for scenario in scenarios]
    b1_rows = [_run_one(root, b1_dir, scenario, SYSTEM_OPTIMIZED) for scenario in scenarios]
    b2_rows = [_run_one(root, b2_dir, scenario, SYSTEM_AGENTIC) for scenario in scenarios]
    b0_notes = _single_system_notes(SYSTEM_BASELINE)
    b1_notes = _single_system_notes(SYSTEM_OPTIMIZED)
    b2_notes = _single_system_notes(SYSTEM_AGENTIC)
    b0_payload = _suite_payload(SYSTEM_BASELINE, started, b0_rows, b0_notes)
    b1_payload = _suite_payload(SYSTEM_OPTIMIZED, started, b1_rows, b1_notes)
    b2_payload = _suite_payload(SYSTEM_AGENTIC, started, b2_rows, b2_notes)
    comparison = _ladder_payloads(b0_payload, b1_payload, b2_payload)
    payload = {
        "run_id": str(uuid4()),
        "system": SYSTEM_LADDER,
        "started_at": started.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "scenario_count": len(scenarios),
        "baseline": b0_payload,
        "optimized": b1_payload,
        "agentic": b2_payload,
        "comparison": comparison,
        "notes": _ladder_notes(scenarios),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "benchmark_results.json", payload)
    write_json(b0_dir / "benchmark_results.json", b0_payload)
    write_json(b1_dir / "benchmark_results.json", b1_payload)
    write_json(b2_dir / "benchmark_results.json", b2_payload)
    write_json(output_dir / "comparison.json", comparison)
    return BenchmarkReport(output_dir=output_dir, payload=payload)


def _b2_row_fields(record: dict[str, Any]) -> dict[str, Any]:
    accept = record.get("novel_accept") or []
    reject = record.get("novel_reject") or []
    verifier = record.get("verifier") or {}
    return {
        "agent_invoked": bool(record.get("agent_invoked")),
        "invocation_reason": record.get("invocation_reason"),
        "invocation_reason_code": record.get("invocation_reason_code"),
        "fallback_reason": record.get("fallback_reason"),
        "used_proposal": bool(verifier.get("used_proposal")),
        "provider": record.get("provider"),
        "model": record.get("model"),
        "agent_latency_ms": record.get("latency_ms") or 0.0,
        "prompt_tokens": int(record.get("prompt_tokens") or 0),
        "completion_tokens": int(record.get("completion_tokens") or 0),
        "estimated_cost_usd": record.get("estimated_cost_usd") or 0.0,
        "novel_accept": accept,
        "novel_reject": reject,
        "novel_accept_count": len(accept),
        "novel_reject_count": len(reject),
    }


def _run_one(root: Path, output_dir: Path, scenario: Scenario, system: str) -> dict[str, Any]:
    workspace = output_dir / "workspaces" / scenario.id
    materialize_workspace(root, workspace)
    registry = output_dir / "registries" / scenario.id
    seed_id = None
    if scenario.setup == "publish_first":
        seed = run_b0(
            source="feature",
            target="development",
            fixtures_dir=workspace / "fixtures",
            work_dir=output_dir / "runs" / f"{scenario.id}-seed",
            registry_dir=registry,
        )
        seed_id = seed.artifact_id
    cache_dir = None
    if system in {SYSTEM_OPTIMIZED, SYSTEM_AGENTIC}:
        cache_dir = output_dir / "caches" / scenario.id
        warm_cache(workspace / "fixtures", cache_dir)
    apply_changes(workspace, scenario.apply)
    paths = change_set(scenario.files_changed, scenario.apply)
    extra: dict[str, Any] = {}
    if system == SYSTEM_BASELINE:
        result = run_b0(
            source=scenario.source,
            target=scenario.target,
            fixtures_dir=workspace / "fixtures",
            work_dir=output_dir / "runs" / scenario.id,
            registry_dir=registry,
            promote_mode=_promote_mode_for_scenario(scenario),
        )
        decisions: list[dict[str, str]] = []
    elif system == SYSTEM_AGENTIC:
        result = run_b2(
            source=scenario.source,
            target=scenario.target,
            fixtures_dir=workspace / "fixtures",
            work_dir=output_dir / "runs" / scenario.id,
            registry_dir=registry,
            changed_paths=paths,
            cache_dir=cache_dir,
            workspace_dir=workspace,
            repo_dir=root,
        )
        decisions = decisions_from_result(result)
        extra = _b2_row_fields(record_from_result(result))
    else:
        result = run_b1(
            source=scenario.source,
            target=scenario.target,
            fixtures_dir=workspace / "fixtures",
            work_dir=output_dir / "runs" / scenario.id,
            registry_dir=registry,
            changed_paths=paths,
            cache_dir=cache_dir,
        )
        decisions = decisions_from_result(result)
    judged = compare_run(scenario, result, seed_id)
    row = {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "source": scenario.source,
        "target": scenario.target,
        "workflow_status": result.status,
        "flow": result.flow,
        "executed_jobs": judged["executed_jobs"],
        "failed_jobs": judged["failed_jobs"],
        "blocked_jobs": judged["blocked_jobs"],
        "skipped_jobs": [job.job_name for job in result.jobs if job.status == "skipped"],
        "required_jobs": scenario.required_jobs,
        "false_skips": judged["false_skips"],
        "unnecessary_jobs": judged["unnecessary_jobs"],
        "simulated_cost": result.simulated_cost_total,
        "wall_duration_ms": result.wall_duration_ms,
        "artifact_id": result.artifact_id,
        "seed_artifact_id": seed_id,
        "correctness_pass": judged["correctness_pass"],
        "status_ok": judged["status_ok"],
        "artifact_ok": judged["artifact_ok"],
        "artifact_notes": judged["artifact_notes"],
        "error": next((job.error for job in result.jobs if job.error), None),
        "promote_mode": result.promote_mode,
        "decisions": decisions,
    }
    row.update(extra)
    return row


def _promote_mode_for_scenario(scenario: Scenario) -> str | None:
    """Map explicit scenario fields to B0 promote_mode. Not file-diff detection."""
    if scenario.source != "development" or scenario.target != "main":
        return None
    return "rebuild" if scenario.apply else "reuse"


def _suite_payload(
    system: str,
    started: datetime,
    rows: list[dict[str, Any]],
    notes: list[str],
) -> dict[str, Any]:
    costs = [row["simulated_cost"] for row in rows]
    walls = [row["wall_duration_ms"] for row in rows]
    false_skips = sum(len(row["false_skips"]) for row in rows)
    correct = sum(1 for row in rows if row["correctness_pass"])
    illegal_accepted = sum(
        1
        for row in rows
        if row["source"] != "development"
        and row["target"] == "main"
        and row["workflow_status"] == "succeeded"
    )
    safety_ok = false_skips == 0 and correct == len(rows) and illegal_accepted == 0
    b2_metrics = _suite_b2_metrics(rows) if system == SYSTEM_AGENTIC else {}
    payload = {
        "run_id": str(uuid4()),
        "system": system,
        "started_at": started.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "scenario_count": len(rows),
        "totals": {
            "simulated_cost": sum(costs),
            "median_simulated_cost": float(median(costs)) if costs else 0.0,
            "wall_duration_ms": round(sum(walls), 3),
            "jobs_executed": sum(len(row["executed_jobs"]) for row in rows),
            "correctness_pass_count": correct,
            "correctness_pass_rate": round(correct / len(rows), 6) if rows else 0.0,
            "false_skip_count": false_skips,
            "unnecessary_jobs_count": sum(len(row["unnecessary_jobs"]) for row in rows),
            "illegal_promotion_accepted": illegal_accepted,
        },
        "safety_gate": {
            "false_skips_zero": false_skips == 0,
            "correctness_complete": correct == len(rows) if rows else False,
            "illegal_promotion_rejected": illegal_accepted == 0,
            "optimization_win_eligible": safety_ok,
        },
        "scenarios": rows,
        "notes": notes,
    }
    if b2_metrics:
        payload["agent"] = b2_metrics
    return payload


def _suite_b2_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    invoked = sum(1 for row in rows if row.get("agent_invoked"))
    return {
        "agent_invocation_count": invoked,
        "no_invoke_count": len(rows) - invoked,
        "novel_accept_count": sum(int(row.get("novel_accept_count") or 0) for row in rows),
        "novel_reject_count": sum(int(row.get("novel_reject_count") or 0) for row in rows),
        "fallback_count": sum(1 for row in rows if row.get("fallback_reason")),
        "agent_latency_ms": round(sum(float(row.get("agent_latency_ms") or 0) for row in rows), 3),
        "prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in rows),
        "used_proposal_count": sum(1 for row in rows if row.get("used_proposal")),
        "estimated_cost_usd": round(
            sum(float(row.get("estimated_cost_usd") or 0) for row in rows), 8
        ),
    }


def _scenario_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    return [row["scenario_id"] for row in payload.get("scenarios") or []]


def _is_regression_suite(ids: list[str]) -> bool:
    return ids == [f"S{i:02d}" for i in range(1, 15)]


def _compare_notes(scenarios: list[Scenario]) -> list[str]:
    ids = [item.id for item in scenarios]
    notes = [
        "B1 is a deterministic optimizer, not an agent.",
        "An optimization win requires false_skip_count=0 and complete correctness.",
    ]
    if _is_regression_suite(ids):
        notes.insert(0, "S01–S14 ground truth is unchanged.")
    else:
        notes.insert(0, f"Suite ids: {', '.join(ids)}.")
    return notes


def _ladder_notes(scenarios: list[Scenario]) -> list[str]:
    ids = [item.id for item in scenarios]
    notes = [
        "B2 must not beat B1 by skipping required conservative work.",
        "Q1 is a T win only with safety, verifier-accepted evidence, and T_B2 < T_B1.",
        "Q2 also requires measured end-to-end time to improve.",
    ]
    if _is_regression_suite(ids):
        notes.insert(0, "S01–S14 ground truth is unchanged.")
    else:
        notes.insert(0, f"Suite ids: {', '.join(ids)}.")
    return notes


def _single_system_notes(system: str) -> list[str]:
    if system == SYSTEM_BASELINE:
        return [
            "This is a B0 baseline measurement, not an optimized result.",
            "required_jobs is ground truth; extra B0 jobs are unnecessary, not false skips.",
            (
                "development→main promote_mode comes from explicit scenario "
                "apply/setup, not change detection."
            ),
        ]
    if system == SYSTEM_AGENTIC:
        return [
            "This is a B2 agentic measurement. The verifier, not the model, owns SKIP.",
            "B1 runs first. No API key means no agent invoke and B2 should match B1.",
            "required_jobs is ground truth; extra B2 jobs are unnecessary, not false skips.",
            "A cheaper B2 than B1 on a fail-closed oracle is a likely false skip.",
        ]
    return [
        "This is a B1 deterministic measurement, not an agent result.",
        "required_jobs is ground truth; extra B1 jobs are unnecessary, not false skips.",
        "B1 infers clean vs dirty promote from the change set; it does not take promote_mode.",
        "A last-known-good cache is warmed from pre-apply fixtures; reuse requires identity match.",
    ]


def _compare_payloads(baseline: dict[str, Any], optimized: dict[str, Any]) -> dict[str, Any]:
    b0 = baseline["totals"]
    b1 = optimized["totals"]
    t0 = b0["simulated_cost"]
    t1 = b1["simulated_cost"]
    reduction = (t0 - t1) / t0 if t0 else 0.0
    safety = optimized["safety_gate"]
    per_scenario = []
    by_b0 = {row["scenario_id"]: row for row in baseline["scenarios"]}
    for row in optimized["scenarios"]:
        left = by_b0[row["scenario_id"]]
        per_scenario.append(
            {
                "scenario_id": row["scenario_id"],
                "title": row["title"],
                "baseline_cost": left["simulated_cost"],
                "optimized_cost": row["simulated_cost"],
                "cost_delta": left["simulated_cost"] - row["simulated_cost"],
                "baseline_executed": left["executed_jobs"],
                "optimized_executed": row["executed_jobs"],
                "false_skips": row["false_skips"],
                "unnecessary_jobs": row["unnecessary_jobs"],
                "correctness_pass": row["correctness_pass"],
            }
        )
    return {
        "simulated_cost_baseline": t0,
        "simulated_cost_optimized": t1,
        "cost_reduction": t0 - t1,
        "cost_reduction_pct": round(reduction, 6),
        "median_simulated_cost_baseline": b0["median_simulated_cost"],
        "median_simulated_cost_optimized": b1["median_simulated_cost"],
        "jobs_executed_baseline": b0["jobs_executed"],
        "jobs_executed_optimized": b1["jobs_executed"],
        "unnecessary_jobs_baseline": b0["unnecessary_jobs_count"],
        "unnecessary_jobs_optimized": b1["unnecessary_jobs_count"],
        "false_skip_count_optimized": b1["false_skip_count"],
        "correctness_pass_count_optimized": b1["correctness_pass_count"],
        "optimization_win_eligible": safety["optimization_win_eligible"],
        "wall_duration_ms_baseline": b0["wall_duration_ms"],
        "wall_duration_ms_optimized": b1["wall_duration_ms"],
        "scenarios": per_scenario,
        "notes": [
            "Wall-clock is secondary and noisy.",
            "Do not treat this as an agent improvement.",
        ],
    }


def _ladder_payloads(
    baseline: dict[str, Any], optimized: dict[str, Any], agentic: dict[str, Any]
) -> dict[str, Any]:
    comparison = _compare_payloads(baseline, optimized)
    b1 = optimized["totals"]
    b2 = agentic["totals"]
    agent = agentic.get("agent") or _suite_b2_metrics(agentic["scenarios"])
    safety = agentic["safety_gate"]
    delta_t = b1["simulated_cost"] - b2["simulated_cost"]
    e2e_b1 = float(b1["wall_duration_ms"])
    e2e_b2 = float(b2["wall_duration_ms"]) + float(agent["agent_latency_ms"])
    safety_ok = bool(safety["optimization_win_eligible"])
    evidence = int(agent["novel_accept_count"]) > 0
    if not safety_ok:
        q1_verdict = "unsafe"
    elif delta_t > 0 and evidence:
        q1_verdict = "win"
    elif delta_t < 0:
        q1_verdict = "regression"
    else:
        q1_verdict = "parity"
    q1_win = q1_verdict == "win"
    q2_win = q1_win and e2e_b2 < e2e_b1
    ids = _scenario_ids_from_payload(optimized)
    notes = [
        "Wall-clock is secondary and noisy.",
        "Q1 uses T and novel_accept. Q2 uses measured W_e2e = W_jobs + W_agent.",
    ]
    if _is_regression_suite(ids):
        notes.append("B2 vs B1 is the agent question. Delta may be zero on S01–S14.")
    comparison.update(
        {
            "simulated_cost_agentic": b2["simulated_cost"],
            "delta_vs_b1": delta_t,
            "jobs_executed_agentic": b2["jobs_executed"],
            "unnecessary_jobs_agentic": b2["unnecessary_jobs_count"],
            "false_skip_count_agentic": b2["false_skip_count"],
            "correctness_pass_count_agentic": b2["correctness_pass_count"],
            "optimization_win_eligible_agentic": safety_ok,
            "agent_invocation_count": agent["agent_invocation_count"],
            "novel_accept_count": agent["novel_accept_count"],
            "novel_reject_count": agent["novel_reject_count"],
            "fallback_count": agent["fallback_count"],
            "used_proposal_count": agent.get("used_proposal_count", 0),
            "agent_latency_ms": agent["agent_latency_ms"],
            "prompt_tokens": agent.get("prompt_tokens", 0),
            "completion_tokens": agent.get("completion_tokens", 0),
            "estimated_cost_usd": agent["estimated_cost_usd"],
            "wall_duration_ms_agentic": b2["wall_duration_ms"],
            "e2e_ms_optimized": round(e2e_b1, 3),
            "e2e_ms_agentic": round(e2e_b2, 3),
            "e2e_delta_ms": round(e2e_b1 - e2e_b2, 3),
            "q1_verdict": q1_verdict,
            "q1_pipeline_win": q1_win,
            "q2_e2e_win": q2_win,
            "notes": notes,
        }
    )
    return comparison
