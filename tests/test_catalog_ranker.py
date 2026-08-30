"""Correctness tests for the Catalog Ranker workload.

These are not CI optimization, benchmark, or performance tests.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from agentic_cicd.ranker import run_workload
from agentic_cicd.ranker.identity import HASH_ALGORITHM
from agentic_cicd.ranker.ingest import fixture_paths, load_catalog, load_model, load_personas

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures"

REQUIRED_OUTPUTS = (
    "predictions.json",
    "metrics.json",
    "dataset_manifest.json",
    "model_manifest.json",
    "run_metadata.json",
    "raw_catalog.json",
    "prepared_catalog.json",
    "bundle/artifact.json",
    "bundle/predictions.json",
    "bundle/metrics.json",
    "bundle/model.json",
)


def test_fixtures_can_be_loaded() -> None:
    paths = fixture_paths(FIXTURES)
    catalog = load_catalog(paths["catalog"])
    personas = load_personas(paths["personas"])
    model = load_model(paths["model"])
    assert len(catalog["items"]) == 16
    assert len(personas["personas"]) == 4
    assert model["top_n"] == 5


def test_rank_writes_expected_structure(tmp_path: Path) -> None:
    result = run_workload(FIXTURES, tmp_path / "run")
    for relative in REQUIRED_OUTPUTS:
        assert (result.output_dir / relative).is_file(), relative
    rankings = result.predictions["rankings"]
    assert set(rankings) == {"U1", "U2", "U3", "U4"}
    for rows in rankings.values():
        assert len(rows) == 5
        assert [row["rank"] for row in rows] == [1, 2, 3, 4, 5]


def test_artifact_metadata_is_valid(tmp_path: Path) -> None:
    result = run_workload(FIXTURES, tmp_path / "run")
    artifact_path = result.output_dir / "bundle" / "artifact.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["hash_algorithm"] == HASH_ALGORITHM
    assert artifact["artifact_id"] == result.artifact_id
    assert len(result.artifact_id) == 64
    int(result.artifact_id, 16)
    assert result.metrics["predictions_sha256"]
    assert result.dataset_manifest["catalog_record_count"] == 16
    assert result.model_manifest["version"] == "1.0.0"


def test_repeated_runs_are_equivalent(tmp_path: Path) -> None:
    first = run_workload(FIXTURES, tmp_path / "a")
    second = run_workload(FIXTURES, tmp_path / "b")
    assert first.predictions == second.predictions
    assert first.metrics == second.metrics
    assert first.artifact_id == second.artifact_id
    meta_a = json.loads((first.output_dir / "run_metadata.json").read_text(encoding="utf-8"))
    meta_b = json.loads((second.output_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert meta_a["run_id"] != meta_b["run_id"]
    assert meta_a["artifact_id"] == meta_b["artifact_id"]


def test_model_change_changes_artifact_id(tmp_path: Path) -> None:
    alt = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, alt)
    model_path = alt / "model" / "ranker.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["genre_weights"]["action"] = 2.0
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    baseline = run_workload(FIXTURES, tmp_path / "base")
    changed = run_workload(alt, tmp_path / "changed")
    assert changed.artifact_id != baseline.artifact_id
    assert changed.predictions != baseline.predictions
