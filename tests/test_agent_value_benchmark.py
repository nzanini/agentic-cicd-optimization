"""Official S16–S18 agent-value suite. S01–S14 stay in scenarios.json."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_cicd.b1.classify import COMPONENT_DOCUMENTATION, COMPONENT_UNKNOWN, classify_path
from agentic_cicd.benchmark import load_scenarios, run_benchmark
from agentic_cicd.benchmark.apply import apply_changes, change_set, materialize_workspace
from agentic_cicd.benchmark.schema import agent_value_scenarios_path

REPO = Path(__file__).resolve().parents[1]
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
S03_JOBS = [
    "branch_guard",
    "validate",
    "test",
    "score",
    "evaluate",
    "package",
    "publish",
]
S12_JOBS = [
    "branch_guard",
    "validate",
    "score",
    "evaluate",
    "package",
    "publish",
]
FROZEN_S01_S14 = {
    "S01": (["README.md", "docs/ROADMAP.md"], ["branch_guard"]),
    "S02": (["tests/test_catalog_ranker.py"], ["branch_guard", "test"]),
    "S03": (["src/agentic_cicd/ranker/score.py"], S03_JOBS),
    "S04": (
        ["fixtures/catalog.json"],
        [
            "branch_guard",
            "validate",
            "ingest",
            "prepare",
            "score",
            "evaluate",
            "package",
            "publish",
        ],
    ),
    "S05": (
        ["src/agentic_cicd/ranker/prepare.py"],
        [
            "branch_guard",
            "validate",
            "test",
            "prepare",
            "score",
            "evaluate",
            "package",
            "publish",
        ],
    ),
    "S06": (
        ["fixtures/model/ranker.json"],
        ["branch_guard", "validate", "score", "evaluate", "package", "publish"],
    ),
    "S07": (["pyproject.toml"], FEATURE_DEV),
    "S08": (["configs/pipeline.json"], ["branch_guard", "validate"]),
    "S09": ([], ["branch_guard", "promote"]),
    "S10": (
        ["src/agentic_cicd/ranker/score.py"],
        ["branch_guard", "validate", "test", "score", "evaluate", "package", "promote"],
    ),
    "S11": (["src/agentic_cicd/ranker/score.py"], ["branch_guard"]),
    "S12": (["configs/scoring_weights.json"], S12_JOBS),
    "S13": (
        ["src/agentic_cicd/ranker/evaluate.py"],
        ["branch_guard", "validate", "test", "evaluate", "package", "publish"],
    ),
    "S14": (["unknown/orphan.dat"], FEATURE_DEV),
}


def test_s01_s14_ground_truth_unchanged() -> None:
    scenarios = load_scenarios()
    assert [item.id for item in scenarios] == list(FROZEN_S01_S14)
    raw = (REPO / "benchmark" / "scenarios.json").read_text(encoding="utf-8")
    assert '"id": "S15"' not in raw
    assert '"id": "S16"' not in raw
    assert '"id": "S17"' not in raw
    assert '"id": "S18"' not in raw
    for item in scenarios:
        files, jobs = FROZEN_S01_S14[item.id]
        assert item.files_changed == files
        assert item.required_jobs == jobs


def test_agent_value_scenarios_load() -> None:
    scenarios = load_scenarios(agent_value_scenarios_path())
    assert [item.id for item in scenarios] == ["S16", "S17", "S18"]
    by_id = {item.id: item for item in scenarios}
    assert by_id["S16"].files_changed == ["scripts/tune_weights.py"]
    assert by_id["S16"].required_jobs == S03_JOBS
    assert by_id["S17"].files_changed == ["ops/prod_weights.json"]
    assert by_id["S17"].required_jobs == S12_JOBS
    assert by_id["S18"].files_changed == ["README.md", "scripts/tune_weights.py"]
    assert by_id["S18"].required_jobs == S03_JOBS
    assert classify_path("scripts/tune_weights.py") == COMPONENT_UNKNOWN
    assert classify_path("ops/prod_weights.json") == COMPONENT_UNKNOWN
    assert classify_path("README.md") == COMPONENT_DOCUMENTATION
    raw = agent_value_scenarios_path().read_text(encoding="utf-8")
    assert '"id": "S15"' not in raw


def test_s17_apply_does_not_touch_mapped_overlay(tmp_path: Path) -> None:
    s17 = next(item for item in load_scenarios(agent_value_scenarios_path()) if item.id == "S17")
    workspace = materialize_workspace(REPO, tmp_path / "ws")
    overlay_before = (workspace / "configs" / "scoring_weights.json").read_text(encoding="utf-8")
    apply_changes(workspace, s17.apply)
    overlay_after = (workspace / "configs" / "scoring_weights.json").read_text(encoding="utf-8")
    assert overlay_before == overlay_after
    assert change_set(s17.files_changed, s17.apply) == ["ops/prod_weights.json"]
    hidden = workspace / "ops" / "prod_weights.json"
    assert hidden.is_file()
    text = hidden.read_text(encoding="utf-8")
    assert "scoring_weights.json" in text
    assert "genre_weights" in text


def test_s16_and_s18_apply_write_score_import(tmp_path: Path) -> None:
    suite = {item.id: item for item in load_scenarios(agent_value_scenarios_path())}
    workspace = materialize_workspace(REPO, tmp_path / "ws")
    apply_changes(workspace, suite["S16"].apply)
    script = (workspace / "scripts" / "tune_weights.py").read_text(encoding="utf-8")
    assert "agentic_cicd.ranker.score" in script
    assert change_set(suite["S16"].files_changed, suite["S16"].apply) == ["scripts/tune_weights.py"]
    assert change_set(suite["S18"].files_changed, suite["S18"].apply) == [
        "README.md",
        "scripts/tune_weights.py",
    ]


def test_b2_production_code_has_no_scenario_ids() -> None:
    root = REPO / "src" / "agentic_cicd" / "b2"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for scenario_id in ("S16", "S17", "S18", "S15", "S01"):
            assert f'"{scenario_id}"' not in text
            assert f"'{scenario_id}'" not in text


def test_b1_is_conservative_on_agent_value_suite(tmp_path: Path) -> None:
    report = run_benchmark(
        output_dir=tmp_path / "b1",
        system="optimized",
        scenarios_path=agent_value_scenarios_path(),
    )
    payload = report.payload
    assert payload["scenario_count"] == 3
    assert payload["totals"]["simulated_cost"] == 93
    assert payload["totals"]["false_skip_count"] == 0
    assert payload["totals"]["correctness_pass_count"] == 3
    assert payload["totals"]["unnecessary_jobs_count"] == 7
    by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
    for scenario_id in ("S16", "S17", "S18"):
        assert by_id[scenario_id]["simulated_cost"] == 31
        assert by_id[scenario_id]["executed_jobs"] == FEATURE_DEV
        assert by_id[scenario_id]["correctness_pass"] is True
        assert by_id[scenario_id]["false_skips"] == []
    assert by_id["S16"]["unnecessary_jobs"] == ["ingest", "prepare"]
    assert by_id["S17"]["unnecessary_jobs"] == ["test", "ingest", "prepare"]
    assert by_id["S18"]["unnecessary_jobs"] == ["ingest", "prepare"]


def test_b2_offline_matches_b1_on_agent_value_suite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("B2_API_KEY", raising=False)
    monkeypatch.delenv("B2_BASE_URL", raising=False)
    monkeypatch.delenv("B2_MODEL", raising=False)
    monkeypatch.delenv("B2_DISABLED", raising=False)
    report = run_benchmark(
        output_dir=tmp_path / "b2",
        system="agentic",
        scenarios_path=agent_value_scenarios_path(),
    )
    payload = report.payload
    assert payload["totals"]["simulated_cost"] == 93
    assert payload["totals"]["false_skip_count"] == 0
    assert payload["totals"]["correctness_pass_count"] == 3
    assert payload["totals"]["unnecessary_jobs_count"] == 7
    assert payload["agent"]["agent_invocation_count"] == 0
    assert payload["agent"]["novel_accept_count"] == 0
    assert payload["agent"]["estimated_cost_usd"] == 0.0
    by_id = {row["scenario_id"]: row for row in payload["scenarios"]}
    for scenario_id in ("S16", "S17", "S18"):
        assert by_id[scenario_id]["executed_jobs"] == FEATURE_DEV
        assert by_id[scenario_id]["agent_invoked"] is False
        assert by_id[scenario_id]["invocation_reason_code"] == "offline"
        assert by_id[scenario_id]["used_proposal"] is False
