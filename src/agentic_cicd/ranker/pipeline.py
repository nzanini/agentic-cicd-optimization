"""Run ingest → prepare → score → evaluate → package locally.

This is the Catalog Ranker workload, not the CI job scheduler and not B0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentic_cicd.ranker.evaluate import evaluate_predictions
from agentic_cicd.ranker.identity import compute_artifact_id
from agentic_cicd.ranker.ingest import (
    dataset_manifest,
    fixture_paths,
    load_catalog,
    load_effective_model,
    load_personas,
    scoring_weights_path,
)
from agentic_cicd.ranker.io_util import write_json
from agentic_cicd.ranker.package import build_bundle_payload, model_manifest, write_bundle
from agentic_cicd.ranker.prepare import prepare_catalog
from agentic_cicd.ranker.score import rank_catalog


@dataclass(frozen=True)
class WorkloadResult:
    artifact_id: str
    output_dir: Path
    predictions: dict[str, Any]
    metrics: dict[str, Any]
    dataset_manifest: dict[str, Any]
    model_manifest: dict[str, Any]


def run_workload(fixtures_dir: Path, output_dir: Path) -> WorkloadResult:
    started = datetime.now(UTC)
    paths = fixture_paths(fixtures_dir)
    for key, path in paths.items():
        if not path.is_file():
            msg = f"missing {key} fixture: {path}"
            raise FileNotFoundError(msg)

    catalog = load_catalog(paths["catalog"])
    personas = load_personas(paths["personas"])
    model = load_effective_model(fixtures_dir)

    raw_manifest = dataset_manifest(paths["catalog"], paths["personas"], catalog, personas)
    prepared = prepare_catalog(catalog)
    predictions = rank_catalog(prepared, personas, model)
    metrics = evaluate_predictions(predictions, prepared, personas)
    model_meta = model_manifest(paths["model"], model, scoring_weights_path(fixtures_dir))
    payload = build_bundle_payload(
        predictions=predictions,
        metrics=metrics,
        dataset_manifest=raw_manifest,
        model_manifest_data=model_meta,
        model=model,
    )
    artifact_id = compute_artifact_id(payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "raw_catalog.json", catalog)
    write_json(output_dir / "prepared_catalog.json", {"items": prepared})
    write_json(output_dir / "predictions.json", predictions)
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "dataset_manifest.json", raw_manifest)
    write_json(output_dir / "model_manifest.json", model_meta)
    write_bundle(output_dir, payload, artifact_id)

    ended = datetime.now(UTC)
    write_json(
        output_dir / "run_metadata.json",
        {
            "run_id": str(uuid4()),
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "fixtures_dir": fixtures_dir.as_posix(),
            "output_dir": output_dir.as_posix(),
            "artifact_id": artifact_id,
        },
    )
    return WorkloadResult(
        artifact_id=artifact_id,
        output_dir=output_dir,
        predictions=predictions,
        metrics=metrics,
        dataset_manifest=raw_manifest,
        model_manifest=model_meta,
    )
