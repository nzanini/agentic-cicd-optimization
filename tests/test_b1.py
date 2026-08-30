"""Tests for the B1 deterministic optimizer. Not agent tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from agentic_cicd.b0 import run_b0
from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b1.classify import (
    COMPONENT_SCORING_OVERLAY,
    COMPONENT_UNKNOWN,
    classify_path,
    classify_paths,
)
from agentic_cicd.b1.planner import plan_jobs
from agentic_cicd.b1.runner import run_b1

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "fixtures"

FEATURE_DEV = [
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


def _run_b1(
    tmp_path: Path,
    source: str,
    target: str,
    changed: list[str] | None,
    *,
    fixtures: Path = FIXTURES,
    warm: bool = True,
    name: str = "b1",
    registry: Path | None = None,
):
    cache = tmp_path / "cache"
    if warm:
        warm_cache(fixtures, cache)
    return run_b1(
        source=source,
        target=target,
        fixtures_dir=fixtures,
        work_dir=tmp_path / name,
        registry_dir=registry or (tmp_path / "registry"),
        changed_paths=changed,
        cache_dir=cache if warm else None,
    )


def _executed(result) -> list[str]:
    return [job.job_name for job in result.jobs if job.status == "executed"]


def _decision_map(result) -> dict[str, dict[str, str]]:
    payload = json.loads((result.work_dir / "decisions.json").read_text(encoding="utf-8"))
    return {row["job"]: row for row in payload}


def test_docs_only_runs_branch_guard(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["README.md", "docs/NOTE.md"])
    assert result.status == "succeeded"
    assert _executed(result) == ["branch_guard"]


def test_test_only_runs_branch_guard_and_test(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["tests/test_catalog_ranker.py"])
    assert _executed(result) == ["branch_guard", "test"]


def test_scoring_code_reuses_raw_and_prepared(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["src/agentic_cicd/ranker/score.py"])
    executed = _executed(result)
    assert "score" in executed
    assert "test" in executed
    assert "publish" in executed
    assert "ingest" not in executed
    assert "prepare" not in executed
    assert (result.work_dir / "workload" / "prepared_catalog.json").is_file()


def test_data_change_runs_ingest_chain_not_test(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["fixtures/catalog.json"])
    executed = _executed(result)
    assert "ingest" in executed
    assert "score" in executed
    assert "publish" in executed
    assert "test" not in executed


def test_model_change_runs_score_not_ingest(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["fixtures/model/ranker.json"])
    executed = _executed(result)
    assert "score" in executed
    assert "ingest" not in executed
    assert "test" not in executed


def test_dependency_change_runs_full_feature_dev_graph(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["pyproject.toml"])
    assert _executed(result) == FEATURE_DEV


def test_pipeline_config_runs_validate_only(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["configs/pipeline.json"])
    assert _executed(result) == ["branch_guard", "validate"]


def test_adversarial_overlay_is_not_pipeline_only(tmp_path: Path) -> None:
    assert classify_path("configs/scoring_weights.json") == COMPONENT_SCORING_OVERLAY
    result = _run_b1(tmp_path, "feature", "development", ["configs/scoring_weights.json"])
    executed = _executed(result)
    assert "score" in executed
    assert "publish" in executed
    assert "test" not in executed


def test_unknown_path_runs_full_graph(tmp_path: Path) -> None:
    assert COMPONENT_UNKNOWN in classify_paths(["unknown/orphan.dat"])
    result = _run_b1(tmp_path, "feature", "development", ["unknown/orphan.dat"])
    assert _executed(result) == FEATURE_DEV


def test_illegal_promotion_fails_closed(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "main", ["src/agentic_cicd/ranker/score.py"])
    assert result.status == "failed"
    assert _executed(result) == []
    assert result.jobs[0].job_name == "branch_guard"
    assert result.jobs[0].status == "failed"
    assert not (tmp_path / "registry" / "production.json").exists()


def test_clean_promote_reuses_development_artifact(tmp_path: Path) -> None:
    published = run_b0(
        source="feature",
        target="development",
        fixtures_dir=FIXTURES,
        work_dir=tmp_path / "seed",
        registry_dir=tmp_path / "registry",
    )
    result = _run_b1(
        tmp_path,
        "development",
        "main",
        [],
        registry=tmp_path / "registry",
        name="prod",
    )
    assert result.status == "succeeded"
    assert _executed(result) == ["branch_guard", "promote"]
    assert result.artifact_id == published.artifact_id
    assert result.promote_mode == "reuse"


def test_dirty_promote_rebuilds_invalidated_jobs(tmp_path: Path) -> None:
    published = run_b0(
        source="feature",
        target="development",
        fixtures_dir=FIXTURES,
        work_dir=tmp_path / "seed",
        registry_dir=tmp_path / "registry",
    )
    alt = tmp_path / "alt-fixtures"
    shutil.copytree(FIXTURES, alt)
    model_path = alt / "model" / "ranker.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["genre_weights"]["action"] = 3.0
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    cache = tmp_path / "cache"
    warm_cache(FIXTURES, cache)
    result = run_b1(
        source="development",
        target="main",
        fixtures_dir=alt,
        work_dir=tmp_path / "prod",
        registry_dir=tmp_path / "registry",
        changed_paths=["fixtures/model/ranker.json"],
        cache_dir=cache,
    )
    executed = _executed(result)
    assert result.status == "succeeded"
    assert result.promote_mode == "rebuild"
    assert "score" in executed
    assert "promote" in executed
    assert "publish" not in executed
    assert "ingest" not in executed
    assert result.artifact_id != published.artifact_id


def test_missing_cache_forces_upstream_producers(tmp_path: Path) -> None:
    result = _run_b1(
        tmp_path,
        "feature",
        "development",
        ["src/agentic_cicd/ranker/score.py"],
        warm=False,
    )
    executed = _executed(result)
    assert "score" in executed
    assert "ingest" in executed
    assert "prepare" in executed


def test_stale_cache_file_is_not_reused(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    pred_dir = cache / "predictions"
    pred_dir.mkdir()
    (pred_dir / "predictions.json").write_text("{}\n", encoding="utf-8")
    result = run_b1(
        source="feature",
        target="development",
        fixtures_dir=FIXTURES,
        work_dir=tmp_path / "run",
        registry_dir=tmp_path / "registry",
        changed_paths=["src/agentic_cicd/ranker/evaluate.py"],
        cache_dir=cache,
    )
    executed = _executed(result)
    assert "evaluate" in executed
    assert "score" in executed


def test_every_decision_has_a_reason(tmp_path: Path) -> None:
    result = _run_b1(tmp_path, "feature", "development", ["README.md"])
    decisions = _decision_map(result)
    assert decisions
    for row in decisions.values():
        assert row["decision"] in {"RUN", "SKIP"}
        assert row["reason_code"]
        assert row["reason"]
    assert decisions["score"]["decision"] == "SKIP"
    assert decisions["branch_guard"]["decision"] == "RUN"


def test_omitted_change_set_is_unknown_and_conservative(tmp_path: Path) -> None:
    plan = plan_jobs(
        source="feature",
        target="development",
        changed_paths=None,
        fixtures_dir=FIXTURES,
        cache_dir=None,
    )
    assert "unknown" in plan.components
    assert set(plan.run) == set(FEATURE_DEV)


def test_b1_modules_do_not_hardcode_scenario_ids() -> None:
    root = REPO / "src" / "agentic_cicd" / "b1"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for scenario in [f"S{i:02d}" for i in range(1, 15)]:
            assert scenario not in text, f"{path} mentions {scenario}"
