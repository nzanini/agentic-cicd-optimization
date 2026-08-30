"""Execute a verified plan through existing B0 job bodies."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from agentic_cicd.b0.graph import JOBS
from agentic_cicd.b0.jobs import JobError, run_job
from agentic_cicd.b0.runner import JobRecord, RunResult
from agentic_cicd.b0.state import RunState
from agentic_cicd.b1.planner import DECISION_SKIP, Plan
from agentic_cicd.b1.runner import _decision_dict, _first_failed_dependency, _hydrate_required
from agentic_cicd.ranker.io_util import write_json


def execute_plan(
    *,
    plan: Plan,
    source: str,
    target: str,
    fixtures_dir: Path,
    work_dir: Path,
    registry_dir: Path,
    cache_dir: Path | None,
    run_id: str,
    system: str = "agentic",
) -> RunResult:
    run_started = datetime.now(UTC)
    wall_start = perf_counter()
    state = RunState(
        source=source,
        target=target,
        fixtures_dir=fixtures_dir,
        work_dir=work_dir,
        registry_dir=registry_dir,
        run_id=run_id,
        promote_mode=plan.promote_mode,
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    _hydrate_required(plan, cache_dir, fixtures_dir, state)

    records: list[JobRecord] = []
    failed: str | None = None
    by_decision = {item.job_name: item for item in plan.decisions}

    for name in plan.run:
        spec = JOBS[name]
        blocker = _first_failed_dependency(spec.depends_on, records)
        if failed is not None and blocker is not None:
            decision = by_decision.get(name)
            records.append(
                JobRecord(
                    job_name=name,
                    status="blocked",
                    depends_on=list(spec.depends_on),
                    simulated_cost=0,
                    blocked_by=blocker,
                    error=f"blocked by failed job {blocker}",
                    skip_reason=decision.reason if decision else None,
                )
            )
            continue

        started = datetime.now(UTC)
        t0 = perf_counter()
        record = JobRecord(
            job_name=name,
            status="executed",
            depends_on=list(spec.depends_on),
            simulated_cost=spec.simulated_cost,
            started_at=started.isoformat(),
        )
        try:
            result = run_job(name, state)
            record.inputs = result.get("inputs", {})
            record.outputs = result.get("outputs", {})
            record.artifact_id = result.get("artifact_id")
        except (JobError, OSError, ValueError, KeyError) as exc:
            record.status = "failed"
            record.error = str(exc)
            record.simulated_cost = spec.simulated_cost
            failed = name
        record.ended_at = datetime.now(UTC).isoformat()
        record.wall_duration_ms = round((perf_counter() - t0) * 1000, 3)
        write_json(state.job_dir(name) / "record.json", asdict(record))
        records.append(record)

    for decision in plan.decisions:
        if decision.decision != DECISION_SKIP:
            continue
        if any(record.job_name == decision.job_name for record in records):
            continue
        spec = JOBS[decision.job_name]
        record = JobRecord(
            job_name=decision.job_name,
            status="skipped",
            depends_on=list(spec.depends_on),
            simulated_cost=0,
            skip_reason=decision.reason,
        )
        write_json(state.job_dir(decision.job_name) / "record.json", asdict(record))
        records.append(record)

    status = "failed" if any(record.status == "failed" for record in records) else "succeeded"
    summary = RunResult(
        run_id=run_id,
        system=system,
        source=source,
        target=target,
        flow=plan.flow,
        promote_mode=plan.promote_mode,
        status=status,
        work_dir=work_dir,
        jobs=records,
        artifact_id=state.data.get("artifact_id"),
        simulated_cost_total=sum(
            record.simulated_cost for record in records if record.status == "executed"
        ),
        wall_duration_ms=round((perf_counter() - wall_start) * 1000, 3),
    )
    write_json(work_dir / "run_summary.json", _run_dict(summary, run_started.isoformat(), plan))
    write_json(work_dir / "decisions.json", [_decision_dict(item) for item in plan.decisions])
    return summary


def _run_dict(result: RunResult, started_at: str, plan: Plan) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "system": result.system,
        "source": result.source,
        "target": result.target,
        "flow": result.flow,
        "promote_mode": result.promote_mode,
        "status": result.status,
        "started_at": started_at,
        "work_dir": result.work_dir.as_posix(),
        "artifact_id": result.artifact_id,
        "simulated_cost_total": result.simulated_cost_total,
        "wall_duration_ms": result.wall_duration_ms,
        "components": list(plan.components),
        "invalidated": list(plan.invalidated),
        "decisions": [_decision_dict(item) for item in plan.decisions],
        "jobs": [asdict(job) for job in result.jobs],
    }
