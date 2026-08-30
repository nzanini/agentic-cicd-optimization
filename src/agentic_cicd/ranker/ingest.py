"""Load the vendored catalog and persona fixtures. No network I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_cicd.ranker.identity import sha256_file
from agentic_cicd.ranker.io_util import read_json

CATALOG_NAME = "catalog.json"
PERSONAS_NAME = "personas.json"
MODEL_NAME = "model/ranker.json"


def fixture_paths(fixtures_dir: Path) -> dict[str, Path]:
    return {
        "catalog": fixtures_dir / CATALOG_NAME,
        "personas": fixtures_dir / PERSONAS_NAME,
        "model": fixtures_dir / MODEL_NAME,
    }


def load_catalog(path: Path) -> dict[str, Any]:
    data = read_json(path)
    items = data["items"]
    if not isinstance(items, list) or not items:
        msg = f"catalog at {path} must contain a non-empty items list"
        raise ValueError(msg)
    return data


def load_personas(path: Path) -> dict[str, Any]:
    data = read_json(path)
    personas = data["personas"]
    if not isinstance(personas, list) or not personas:
        msg = f"personas at {path} must contain a non-empty personas list"
        raise ValueError(msg)
    return data


def load_model(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if "top_n" not in data or "genre_weights" not in data:
        msg = f"model at {path} must include top_n and genre_weights"
        raise ValueError(msg)
    return data


def configs_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir.parent / "configs"


def scoring_weights_path(fixtures_dir: Path) -> Path:
    return configs_dir(fixtures_dir) / "scoring_weights.json"


def load_effective_model(fixtures_dir: Path) -> dict[str, Any]:
    """Frozen ranker plus optional configs/scoring_weights.json overlay."""
    paths = fixture_paths(fixtures_dir)
    model = load_model(paths["model"])
    overlay_path = scoring_weights_path(fixtures_dir)
    if not overlay_path.is_file():
        return model
    overlay = read_json(overlay_path)
    if not isinstance(overlay, dict):
        msg = f"scoring weights at {overlay_path} must be a JSON object"
        raise ValueError(msg)
    weights = dict(model["genre_weights"])
    extra = overlay.get("genre_weights") or {}
    if extra:
        weights.update({key: float(value) for key, value in extra.items()})
    merged = {**model, "genre_weights": weights}
    if overlay.get("year_weight") is not None:
        merged["year_weight"] = float(overlay["year_weight"])
    if overlay.get("reference_year") is not None:
        merged["reference_year"] = int(overlay["reference_year"])
    if overlay.get("top_n") is not None:
        merged["top_n"] = int(overlay["top_n"])
    return merged


def dataset_manifest(
    catalog_path: Path,
    personas_path: Path,
    catalog: dict[str, Any],
    personas: dict[str, Any],
) -> dict[str, Any]:
    return {
        "catalog_path": CATALOG_NAME,
        "catalog_record_count": len(catalog["items"]),
        "catalog_sha256": sha256_file(catalog_path),
        "personas_path": PERSONAS_NAME,
        "persona_count": len(personas["personas"]),
        "personas_sha256": sha256_file(personas_path),
    }
