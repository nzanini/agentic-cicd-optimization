"""Sequential B0 orchestrator. Executes every scheduled job; no skip policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from agentic_cicd.b0.graph import (
    FLOW_DEV_MAIN,
    JOBS,
    classify_flow,
    jobs_for_flow,
    normalize_promote_mode,
)
from agentic_cicd.b0.jobs import JobError, run_job
from agentic_cicd.b0.state import RunState
from agentic_cicd.ranker.io_util import write_json


@dataclass
class JobRecord:
    job_name: str
    status: str
    depends_on: list[str]
    simulated_cost: int
    wall_duration_ms: float | None = None
    started_at: str | None = None
    ended_at: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    artifact_id: str | None = None
    error: str | None = None
    blocked_by: str | None = None
    skip_reason: str | None = None


@dataclass
class RunResult:
    run_id: str
    system: str
    source: str
    target: str
    flow: str
    promote_mode: str | None
    status: str
    work_dir: Path
    jobs: list[JobRecord]
    artifact_id: str | None
    simulated_cost_total: int
    wall_duration_ms: float


def run_b0(
    *,
    source: str,
    target: str,
    fixtures_dir: Path,
    work_dir: Path,
    registry_dir: Path,
    promote_mode: str | None = None,
) -> RunResult:
    run_started = datetime.now(UTC)
    wall_start = perf_counter()
    run_id = str(uuid4())
    flow = classify_flow(source, target)
    mode = normalize_promote_mode(promote_mode) if flow == FLOW_DEV_MAIN else None
    scheduled = jobs_for_flow(flow, mode)
    state = RunState(
        source=source,
        target=target,
        fixtures_dir=fixtures_dir,
        work_dir=work_dir,
        registry_dir=registry_dir,
        run_id=run_id,
        promote_mode=mode,
    )
    work_dir.mkdir(parents=True, exist_ok=True)

    records: list[JobRecord] = []
    failed: str | None = None
    for name in scheduled:
        spec = JOBS[name]
        blocker = _first_failed_dependency(spec.depends_on, records)
        if failed is not None and blocker is not None:
            records.append(
                JobRecord(
                    job_name=name,
                    status="blocked",
                    depends_on=list(spec.depends_on),
                    simulated_cost=0,
                    blocked_by=blocker,
                    error=f"blocked by failed job {blocker}",
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
        write_json(state.job_dir(name) / "record.json", _job_dict(record))
        records.append(record)

    status = "failed" if any(r.status == "failed" for r in records) else "succeeded"
    artifact_id = state.data.get("artifact_id")

    summary = RunResult(
        run_id=run_id,
        system="baseline",
        source=source,
        target=target,
        flow=flow,
        promote_mode=mode,
        status=status,
        work_dir=work_dir,
        jobs=records,
        artifact_id=artifact_id,
        simulated_cost_total=sum(r.simulated_cost for r in records if r.status == "executed"),
        wall_duration_ms=round((perf_counter() - wall_start) * 1000, 3),
    )
    write_json(work_dir / "run_summary.json", _run_dict(summary, run_started.isoformat()))
    return summary


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


def _job_dict(record: JobRecord) -> dict[str, Any]:
    return asdict(record)


def _run_dict(result: RunResult, started_at: str) -> dict[str, Any]:
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
        "jobs": [_job_dict(job) for job in result.jobs],
    }
