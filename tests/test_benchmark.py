"""Tests for the S01–S14 benchmark definition and B0 measurement harness."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_cicd.benchmark import load_scenarios, run_benchmark
from agentic_cicd.benchmark.apply import apply_changes, materialize_workspace
from agentic_cicd.ranker.ingest import load_catalog, load_effective_model, load_personas
from agentic_cicd.ranker.prepare import prepare_catalog
from agentic_cicd.ranker.score import rank_catalog

REPO = Path(__file__).resolve().parents[1]


def test_all_scenarios_load() -> None:
    scenarios = load_scenarios()
    assert [item.id for item in scenarios] == [f"S{i:02d}" for i in range(1, 15)]
    raw = (REPO / "benchmark" / "scenarios.json").read_text(encoding="utf-8")
    assert '"id": "S15"' not in raw
    assert '"id": "S16"' not in raw
    for item in scenarios:
        assert item.required_jobs
        assert item.rationale
        assert item.expected_run_status in {"succeeded", "failed"}


def test_adversarial_s12_is_not_pipeline_only() -> None:
    s12 = next(item for item in load_scenarios() if item.id == "S12")
    s08 = next(item for item in load_scenarios() if item.id == "S08")
    assert s12.files_changed == ["configs/scoring_weights.json"]
    assert "score" in s12.required_jobs
    assert "score" not in s08.required_jobs
    assert s08.files_changed == ["configs/pipeline.json"]


def test_s11_is_illegal() -> None:
    s11 = next(item for item in load_scenarios() if item.id == "S11")
    assert s11.expected_legal is False
    assert s11.expected_run_status == "failed"
    assert s11.required_jobs == ["branch_guard"]


def test_overlay_changes_scores(tmp_path: Path) -> None:
    workspace = materialize_workspace(REPO, tmp_path / "ws")
    catalog = load_catalog(workspace / "fixtures" / "catalog.json")
    personas = load_personas(workspace / "fixtures" / "personas.json")
    prepared = prepare_catalog(catalog)
    before = rank_catalog(prepared, personas, load_effective_model(workspace / "fixtures"))
    apply_changes(workspace, [{"op": "set_overlay_genre_weight", "genre": "action", "value": 2.0}])
    after = rank_catalog(prepared, personas, load_effective_model(workspace / "fixtures"))
    assert before != after


def test_benchmark_suite_against_b0(tmp_path: Path) -> None:
    report = run_benchmark(output_dir=tmp_path / "bench")
    payload = report.payload
    assert payload["system"] == "baseline"
    assert payload["scenario_count"] == 14
    assert (tmp_path / "bench" / "benchmark_results.json").is_file()
    by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
    assert by_id["S11"]["workflow_status"] == "failed"
    assert by_id["S11"]["correctness_pass"] is True
    assert by_id["S11"]["false_skips"] == []
    assert by_id["S09"]["correctness_pass"] is True
    assert by_id["S09"]["artifact_id"] == by_id["S09"]["seed_artifact_id"]
    assert by_id["S09"]["executed_jobs"] == ["branch_guard", "promote"]
    assert by_id["S09"]["promote_mode"] == "reuse"
    assert by_id["S10"]["correctness_pass"] is True
    assert by_id["S10"]["artifact_id"] != by_id["S10"]["seed_artifact_id"]
    assert by_id["S10"]["promote_mode"] == "rebuild"
    assert "promote" in by_id["S10"]["executed_jobs"]
    assert payload["totals"]["false_skip_count"] == 0
    assert payload["totals"]["correctness_pass_count"] == 14
    assert payload["totals"]["simulated_cost"] > 0


def test_benchmark_compare_b0_and_b1(tmp_path: Path) -> None:
    report = run_benchmark(output_dir=tmp_path / "cmp", system="compare")
    payload = report.payload
    assert payload["system"] == "compare"
    comparison = payload["comparison"]
    b1 = payload["optimized"]
    assert b1["totals"]["false_skip_count"] == 0
    assert b1["totals"]["correctness_pass_count"] == 14
    assert b1["safety_gate"]["optimization_win_eligible"] is True
    assert comparison["optimization_win_eligible"] is True
    assert comparison["simulated_cost_optimized"] < comparison["simulated_cost_baseline"]
    assert len(comparison["scenarios"]) == 14
    by_id = {row["scenario_id"]: row for row in b1["scenarios"]}
    assert "score" in by_id["S12"]["executed_jobs"]
    assert by_id["S09"]["executed_jobs"] == ["branch_guard", "promote"]
    assert by_id["S11"]["workflow_status"] == "failed"
    assert by_id["S01"]["executed_jobs"] == ["branch_guard"]
    assert (tmp_path / "cmp" / "comparison.json").is_file()


def test_benchmark_b2_reproduces_b1_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("B2_API_KEY", raising=False)
    monkeypatch.delenv("B2_BASE_URL", raising=False)
    monkeypatch.delenv("B2_MODEL", raising=False)
    monkeypatch.delenv("B2_DISABLED", raising=False)
    report = run_benchmark(output_dir=tmp_path / "b2", system="agentic")
    payload = report.payload
    assert payload["system"] == "agentic"
    assert payload["totals"]["false_skip_count"] == 0
    assert payload["totals"]["correctness_pass_count"] == 14
    assert payload["totals"]["unnecessary_jobs_count"] == 0
    assert payload["totals"]["simulated_cost"] == 220
    assert payload["agent"]["agent_invocation_count"] == 0
    assert payload["agent"]["novel_accept_count"] == 0
    by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
    assert by_id["S01"]["executed_jobs"] == ["branch_guard"]
    assert by_id["S11"]["workflow_status"] == "failed"
    assert by_id["S14"]["invocation_reason_code"] == "offline"


def test_deterministic_artifacts_across_suite_runs(tmp_path: Path) -> None:
    first = run_benchmark(output_dir=tmp_path / "a").payload
    second = run_benchmark(output_dir=tmp_path / "b").payload
    for left, right in zip(first["scenarios"], second["scenarios"], strict=True):
        assert left["scenario_id"] == right["scenario_id"]
        assert left["correctness_pass"] == right["correctness_pass"]
        assert left["executed_jobs"] == right["executed_jobs"]
        assert left["artifact_id"] == right["artifact_id"]
