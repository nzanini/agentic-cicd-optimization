"""Tests for the B0 CI/CD baseline. Not optimization or agent tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from agentic_cicd.b0 import run_b0
from agentic_cicd.b0.graph import jobs_for_flow

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures"

FEATURE_DEV_JOBS = [
    "branch_guard",
    "validate",
    "test",
    "ingest",
    "prepare",
    "score",
    "evaluate",
    "package",
    "publish",
]


DEV_MAIN_REBUILD_JOBS = [
    "branch_guard",
    "validate",
    "test",
    "ingest",
    "prepare",
    "score",
    "evaluate",
    "package",
    "promote",
]


def _run(
    tmp_path: Path,
    source: str,
    target: str,
    fixtures: Path = FIXTURES,
    name: str = "run",
    promote_mode: str | None = None,
):
    return run_b0(
        source=source,
        target=target,
        fixtures_dir=fixtures,
        work_dir=tmp_path / name,
        registry_dir=tmp_path / "registry",
        promote_mode=promote_mode,
    )


def test_feature_dev_job_order() -> None:
    assert jobs_for_flow("feature_dev") == FEATURE_DEV_JOBS


def test_dev_main_job_order_by_promote_mode() -> None:
    assert jobs_for_flow("dev_main") == DEV_MAIN_REBUILD_JOBS
    assert jobs_for_flow("dev_main", "rebuild") == DEV_MAIN_REBUILD_JOBS
    assert jobs_for_flow("dev_main", "reuse") == ["branch_guard", "promote"]


def test_successful_feature_dev_run(tmp_path: Path) -> None:
    result = _run(tmp_path, "feature", "development")
    assert result.status == "succeeded"
    assert [job.job_name for job in result.jobs] == FEATURE_DEV_JOBS
    assert all(job.status == "executed" for job in result.jobs)
    assert result.artifact_id
    assert (result.work_dir / "run_summary.json").is_file()
    assert (result.work_dir / "workload" / "bundle" / "artifact.json").is_file()
    summary = json.loads((result.work_dir / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["system"] == "baseline"
    assert summary["simulated_cost_total"] == 31
    assert summary["wall_duration_ms"] >= 0
    pointer = json.loads((tmp_path / "registry" / "development.json").read_text(encoding="utf-8"))
    assert pointer["artifact_id"] == result.artifact_id


def test_artifact_id_reproducible_across_b0_runs(tmp_path: Path) -> None:
    first = _run(tmp_path, "feature", "development", name="a")
    second = run_b0(
        source="feature",
        target="development",
        fixtures_dir=FIXTURES,
        work_dir=tmp_path / "b",
        registry_dir=tmp_path / "registry-b",
    )
    assert first.status == second.status == "succeeded"
    assert first.artifact_id == second.artifact_id


def test_invalid_branch_flow_is_rejected(tmp_path: Path) -> None:
    result = _run(tmp_path, "feature", "main")
    assert result.status == "failed"
    assert result.flow == "illegal"
    assert [job.job_name for job in result.jobs] == ["branch_guard"]
    assert result.jobs[0].status == "failed"
    assert not (tmp_path / "registry" / "production.json").exists()
    assert not (result.work_dir / "workload" / "bundle" / "artifact.json").exists()


def test_ingest_failure_blocks_downstream(tmp_path: Path) -> None:
    broken = tmp_path / "fixtures"
    broken.mkdir()
    (broken / "catalog.json").write_text('{"version": "1", "items": []}\n', encoding="utf-8")
    (broken / "personas.json").write_text(
        '{"version": "1", "personas": [{"id": "U1", "name": "x", "genre_prefs": {}}]}\n',
        encoding="utf-8",
    )
    model_dir = broken / "model"
    model_dir.mkdir()
    (model_dir / "ranker.json").write_text(
        '{"version": "1.0.0", "top_n": 5, "genre_weights": {"action": 1.0}}\n',
        encoding="utf-8",
    )
    result = _run(tmp_path, "feature", "development", fixtures=broken)
    assert result.status == "failed"
    by_name = {job.job_name: job for job in result.jobs}
    assert by_name["validate"].status == "executed"
    assert by_name["ingest"].status == "failed"
    for name in ("prepare", "score", "evaluate", "package", "publish"):
        assert by_name[name].status == "blocked", name
        assert by_name[name].simulated_cost == 0
    assert by_name["test"].status in {"executed", "failed"}


def test_clean_promote_preserves_development_artifact_id(tmp_path: Path) -> None:
    published = _run(tmp_path, "feature/demo", "development", name="dev")
    assert published.status == "succeeded"
    promoted = _run(tmp_path, "development", "main", name="prod", promote_mode="reuse")
    assert promoted.status == "succeeded"
    assert [job.job_name for job in promoted.jobs] == ["branch_guard", "promote"]
    assert all(job.status == "executed" for job in promoted.jobs)
    assert promoted.artifact_id == published.artifact_id
    assert not (promoted.work_dir / "workload" / "bundle" / "artifact.json").exists()
    prod = json.loads((tmp_path / "registry" / "production.json").read_text(encoding="utf-8"))
    assert prod["artifact_id"] == published.artifact_id
    assert prod["validated_artifact_id"] == published.artifact_id
    assert prod["promote_mode"] == "reuse"


def test_dirty_promote_produces_and_promotes_new_artifact(tmp_path: Path) -> None:
    published = _run(tmp_path, "feature", "development", name="dev")
    assert published.status == "succeeded"
    alt = tmp_path / "alt-fixtures"
    shutil.copytree(FIXTURES, alt)
    model_path = alt / "model" / "ranker.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["genre_weights"]["action"] = 3.0
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    result = run_b0(
        source="development",
        target="main",
        fixtures_dir=alt,
        work_dir=tmp_path / "prod",
        registry_dir=tmp_path / "registry",
        promote_mode="rebuild",
    )
    assert result.status == "succeeded"
    assert [job.job_name for job in result.jobs] == DEV_MAIN_REBUILD_JOBS
    assert result.artifact_id
    assert result.artifact_id != published.artifact_id
    prod = json.loads((tmp_path / "registry" / "production.json").read_text(encoding="utf-8"))
    assert prod["artifact_id"] == result.artifact_id
    assert prod["artifact_id"] != published.artifact_id
    assert prod["validated_artifact_id"] == published.artifact_id
    assert prod["promote_mode"] == "rebuild"


def test_promote_without_development_pointer_fails(tmp_path: Path) -> None:
    result = _run(tmp_path, "development", "main", promote_mode="rebuild")
    assert result.status == "failed"
    by_name = {job.job_name: job for job in result.jobs}
    assert by_name["package"].status == "executed"
    assert by_name["promote"].status == "failed"
    assert "no development artifact" in (by_name["promote"].error or "")
    assert not (tmp_path / "registry" / "production.json").exists()


def test_failed_required_jobs_cannot_promote(tmp_path: Path) -> None:
    published = _run(tmp_path, "feature", "development", name="dev")
    assert published.status == "succeeded"
    clean = _run(tmp_path, "development", "main", name="prod-clean", promote_mode="reuse")
    assert clean.status == "succeeded"
    original = json.loads((tmp_path / "registry" / "production.json").read_text(encoding="utf-8"))
    broken = tmp_path / "broken-fixtures"
    shutil.copytree(FIXTURES, broken)
    (broken / "catalog.json").write_text('{"version": "1", "items": []}\n', encoding="utf-8")
    failed = run_b0(
        source="development",
        target="main",
        fixtures_dir=broken,
        work_dir=tmp_path / "prod-dirty",
        registry_dir=tmp_path / "registry",
        promote_mode="rebuild",
    )
    assert failed.status == "failed"
    by_name = {job.job_name: job for job in failed.jobs}
    assert by_name["ingest"].status == "failed"
    assert by_name["package"].status == "blocked"
    assert by_name["promote"].status == "blocked"
    prod = json.loads((tmp_path / "registry" / "production.json").read_text(encoding="utf-8"))
    assert prod["artifact_id"] == original["artifact_id"]
    assert prod["artifact_id"] == published.artifact_id


def test_run_records_every_job(tmp_path: Path) -> None:
    result = _run(tmp_path, "custom", "development")
    assert result.status == "succeeded"
    for job in result.jobs:
        record_path = result.work_dir / "jobs" / job.job_name / "record.json"
        assert record_path.is_file()
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        assert payload["status"] == "executed"
        assert payload["wall_duration_ms"] is not None
        assert payload["simulated_cost"] > 0
