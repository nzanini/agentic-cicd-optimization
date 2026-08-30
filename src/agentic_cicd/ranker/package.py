"""Build a content-addressed bundle. Timestamps are not part of the id."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_cicd import __version__
from agentic_cicd.ranker.identity import HASH_ALGORITHM, sha256_file
from agentic_cicd.ranker.io_util import write_json

_CODE_FILES = ("ingest.py", "prepare.py", "score.py", "evaluate.py", "package.py")


def scoring_code_identity() -> dict[str, Any]:
    ranker_dir = Path(__file__).resolve().parent
    return {
        "package_version": __version__,
        "files": {name: sha256_file(ranker_dir / name) for name in _CODE_FILES},
    }


def model_manifest(
    model_path: Path,
    model: dict[str, Any],
    overlay_path: Path | None = None,
) -> dict[str, Any]:
    meta = {
        "path": "model/ranker.json",
        "version": model.get("version", ""),
        "algorithm": model.get("algorithm", ""),
        "sha256": sha256_file(model_path),
    }
    if overlay_path is not None and overlay_path.is_file():
        meta["scoring_weights_path"] = "configs/scoring_weights.json"
        meta["scoring_weights_sha256"] = sha256_file(overlay_path)
    return meta


def build_bundle_payload(
    *,
    predictions: dict[str, Any],
    metrics: dict[str, Any],
    dataset_manifest: dict[str, Any],
    model_manifest_data: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    return {
        "predictions": predictions,
        "metrics": metrics,
        "dataset_manifest": dataset_manifest,
        "model_manifest": model_manifest_data,
        "model": model,
        "code_identity": scoring_code_identity(),
    }


def write_bundle(output_dir: Path, payload: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    artifact = {
        "artifact_id": artifact_id,
        "hash_algorithm": HASH_ALGORITHM,
        "payload_keys": sorted(payload.keys()),
    }
    bundle_dir = output_dir / "bundle"
    write_json(bundle_dir / "predictions.json", payload["predictions"])
    write_json(bundle_dir / "metrics.json", payload["metrics"])
    write_json(bundle_dir / "dataset_manifest.json", payload["dataset_manifest"])
    write_json(bundle_dir / "model_manifest.json", payload["model_manifest"])
    write_json(bundle_dir / "model.json", payload["model"])
    write_json(bundle_dir / "code_identity.json", payload["code_identity"])
    write_json(bundle_dir / "artifact.json", artifact)
    return artifact
