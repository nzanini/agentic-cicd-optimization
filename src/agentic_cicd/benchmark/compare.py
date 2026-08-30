"""Compare a run against scenario ground truth. No optimization."""

from __future__ import annotations

from typing import Any

from agentic_cicd.b0.runner import RunResult
from agentic_cicd.benchmark.schema import Scenario


def compare_run(
    scenario: Scenario,
    result: RunResult,
    seed_artifact_id: str | None,
) -> dict[str, Any]:
    executed = [job.job_name for job in result.jobs if job.status == "executed"]
    failed = [job.job_name for job in result.jobs if job.status == "failed"]
    blocked = [job.job_name for job in result.jobs if job.status == "blocked"]
    ran = set(executed) | set(failed)
    false_skips = [job for job in scenario.required_jobs if job not in ran]
    unnecessary = [job for job in executed if job not in set(scenario.required_jobs)]
    status_ok = result.status == scenario.expected_run_status
    artifact_ok, artifact_notes = _artifact_ok(scenario, result, seed_artifact_id)
    correctness = status_ok and not false_skips and artifact_ok
    return {
        "status_ok": status_ok,
        "false_skips": false_skips,
        "unnecessary_jobs": unnecessary,
        "executed_jobs": executed,
        "failed_jobs": failed,
        "blocked_jobs": blocked,
        "artifact_ok": artifact_ok,
        "artifact_notes": artifact_notes,
        "correctness_pass": correctness,
    }


def _artifact_ok(
    scenario: Scenario,
    result: RunResult,
    seed_artifact_id: str | None,
) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True
    spec = scenario.artifact
    if spec.get("require_artifact_id_on_success") and result.status == "succeeded":
        if not result.artifact_id:
            ok = False
            notes.append("missing artifact_id on success")
    if spec.get("must_match_seed") and result.status == "succeeded":
        if seed_artifact_id is None or result.artifact_id != seed_artifact_id:
            ok = False
            notes.append("artifact_id must equal seeded development artifact")
    if spec.get("must_differ_from_seed") and result.status == "succeeded":
        if seed_artifact_id is None or result.artifact_id == seed_artifact_id:
            ok = False
            notes.append("artifact_id must differ from seeded development artifact")
    if not spec.get("must_differ_from_seed") and not spec.get("must_match_seed"):
        notes.append("no seed identity assertion")
    return ok, notes
