"""Execute a B1 plan. Reuses B0 job bodies; does not change B0 scheduling."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from agentic_cicd.b0.graph import JOBS, PROMOTE_REUSE
from agentic_cicd.b0.jobs import JobError, run_job
from agentic_cicd.b0.runner import JobRecord, RunResult
from agentic_cicd.b0.state import RunState
from agentic_cicd.b1.cache import has_valid, hydrate
from agentic_cicd.b1.impact import CONSUMES, PRODUCER
from agentic_cicd.b1.planner import DECISION_RUN, DECISION_SKIP, JobDecision, Plan, plan_jobs
from agentic_cicd.ranker.io_util import write_json

_ARTIFACT_STATE_KEYS = {
    "raw_dataset": {
        "raw_catalog.json": "catalog",
        "personas.json": "personas",
        "dataset_manifest.json": "dataset_manifest",
    },
    "prepared_catalog": {"prepared_catalog.json": "prepared_items"},
    "predictions": {"predictions.json": "predictions"},
    "metrics": {"metrics.json": "metrics"},
}


def run_b1(
    *,
    source: str,
    target: str,
    fixtures_dir: Path,
    work_dir: Path,
    registry_dir: Path,
    changed_paths: list[str] | None,
    cache_dir: Path | None = None,
) -> RunResult:
    run_started = datetime.now(UTC)
    wall_start = perf_counter()
    run_id = str(uuid4())
    plan = plan_jobs(
        source=source,
        target=target,
        changed_paths=changed_paths,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
    )
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

    skipped = [item for item in plan.decisions if item.decision == DECISION_SKIP]
    for decision in skipped:
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
        system="optimized",
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


def _hydrate_required(
    plan: Plan,
    cache_dir: Path | None,
    fixtures_dir: Path,
    state: RunState,
) -> None:
    """Restore verified intermediates that running jobs consume."""
    if cache_dir is None:
        return
    needed: set[str] = set()
    running = set(plan.run)
    for job in plan.run:
        needs = CONSUMES.get(job, ())
        if job == "promote" and plan.promote_mode == PROMOTE_REUSE:
            needs = ()
        for artifact in needs:
            producer = PRODUCER[artifact]
            if producer not in running:
                needed.add(artifact)
    workload = state.workload_dir()
    for artifact in sorted(needed):
        if not has_valid(cache_dir, artifact, fixtures_dir):
            msg = f"refusing to skip {PRODUCER[artifact]}: {artifact} cache is missing or stale"
            raise JobError(msg)
        restored = hydrate(cache_dir, artifact, workload)
        _apply_state(state, artifact, restored)


def _apply_state(state: RunState, artifact: str, restored: dict[str, Any]) -> None:
    mapping = _ARTIFACT_STATE_KEYS.get(artifact, {})
    for filename, key in mapping.items():
        payload = restored[filename]
        if key == "prepared_items":
            state.data["prepared"] = payload["items"]
        else:
            state.data[key] = payload


def _first_failed_dependency(depends_on: tuple[str, ...], records: list[JobRecord]) -> str | None:
    by_name = {record.job_name: record for record in records}
    for dep in depends_on:
        record = by_name.get(dep)
        if record is None:
            continue
        if record.status == "failed":
            return dep
        if record.status == "blocked":
            return record.blocked_by or dep
    return None


def _decision_dict(decision: JobDecision) -> dict[str, str]:
    return {
        "job": decision.job_name,
        "decision": decision.decision,
        "reason_code": decision.reason_code,
        "reason": decision.reason,
    }


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


def decisions_from_result(result: RunResult) -> list[dict[str, str]]:
    path = result.work_dir / "decisions.json"
    if not path.is_file():
        return [
            {
                "job": job.job_name,
                "decision": DECISION_RUN if job.status == "executed" else job.status.upper(),
                "reason_code": "",
                "reason": job.skip_reason or job.error or "",
            }
            for job in result.jobs
        ]
    from agentic_cicd.ranker.io_util import read_json

    payload = read_json(path)
    return list(payload) if isinstance(payload, list) else []
