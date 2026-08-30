"""Identity-checked intermediate reuse. Existence alone is not a cache hit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_cicd.b1.impact import (
    ARTIFACT_METRICS,
    ARTIFACT_PREDICTIONS,
    ARTIFACT_PREPARED,
    ARTIFACT_RAW,
)
from agentic_cicd.ranker.evaluate import evaluate_predictions
from agentic_cicd.ranker.identity import sha256_file
from agentic_cicd.ranker.ingest import (
    dataset_manifest,
    fixture_paths,
    load_catalog,
    load_effective_model,
    load_personas,
    scoring_weights_path,
)
from agentic_cicd.ranker.io_util import read_json, write_json
from agentic_cicd.ranker.prepare import prepare_catalog
from agentic_cicd.ranker.score import rank_catalog

CACHEABLE = (ARTIFACT_RAW, ARTIFACT_PREPARED, ARTIFACT_PREDICTIONS, ARTIFACT_METRICS)

_IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    ARTIFACT_RAW: ("catalog_sha256", "personas_sha256"),
    ARTIFACT_PREPARED: ("catalog_sha256", "personas_sha256"),
    ARTIFACT_PREDICTIONS: (
        "catalog_sha256",
        "personas_sha256",
        "model_sha256",
        "overlay_sha256",
    ),
    ARTIFACT_METRICS: (
        "catalog_sha256",
        "personas_sha256",
        "model_sha256",
        "overlay_sha256",
    ),
}


def fixture_identity(fixtures_dir: Path) -> dict[str, str | None]:
    paths = fixture_paths(fixtures_dir)
    overlay = scoring_weights_path(fixtures_dir)
    return {
        "catalog_sha256": sha256_file(paths["catalog"]),
        "personas_sha256": sha256_file(paths["personas"]),
        "model_sha256": sha256_file(paths["model"]),
        "overlay_sha256": sha256_file(overlay) if overlay.is_file() else None,
    }


def warm_cache(fixtures_dir: Path, cache_dir: Path) -> None:
    """Build last-known-good intermediates from the current fixtures.

    This is previous-build state, not a scenario job. Simulated cost is not charged.
    """
    paths = fixture_paths(fixtures_dir)
    catalog = load_catalog(paths["catalog"])
    personas = load_personas(paths["personas"])
    model = load_effective_model(fixtures_dir)
    manifest = dataset_manifest(paths["catalog"], paths["personas"], catalog, personas)
    prepared = prepare_catalog(catalog)
    predictions = rank_catalog(prepared, personas, model)
    metrics = evaluate_predictions(predictions, prepared, personas)
    identity = fixture_identity(fixtures_dir)
    _write_entry(
        cache_dir,
        ARTIFACT_RAW,
        identity,
        {
            "raw_catalog.json": catalog,
            "personas.json": personas,
            "dataset_manifest.json": manifest,
        },
    )
    _write_entry(
        cache_dir,
        ARTIFACT_PREPARED,
        identity,
        {"prepared_catalog.json": {"items": prepared}},
    )
    _write_entry(cache_dir, ARTIFACT_PREDICTIONS, identity, {"predictions.json": predictions})
    _write_entry(cache_dir, ARTIFACT_METRICS, identity, {"metrics.json": metrics})


def has_valid(cache_dir: Path | None, artifact: str, fixtures_dir: Path) -> bool:
    if cache_dir is None or artifact not in CACHEABLE:
        return False
    meta_path = cache_dir / artifact / "meta.json"
    if not meta_path.is_file():
        return False
    meta = read_json(meta_path)
    stored = meta.get("input_identity")
    if not isinstance(stored, dict):
        return False
    current = fixture_identity(fixtures_dir)
    for key in _IDENTITY_KEYS[artifact]:
        if stored.get(key) != current.get(key):
            return False
    payload_dir = cache_dir / artifact
    expected = _payload_names(artifact)
    return all((payload_dir / name).is_file() for name in expected)


def hydrate(cache_dir: Path, artifact: str, workload_dir: Path) -> dict[str, Any]:
    """Copy a verified cache entry into the workload directory. No empty stubs."""
    source = cache_dir / artifact
    restored: dict[str, Any] = {}
    for name in _payload_names(artifact):
        payload = read_json(source / name)
        write_json(workload_dir / name, payload)
        restored[name] = payload
    return restored


def _payload_names(artifact: str) -> tuple[str, ...]:
    if artifact == ARTIFACT_RAW:
        return ("raw_catalog.json", "personas.json", "dataset_manifest.json")
    if artifact == ARTIFACT_PREPARED:
        return ("prepared_catalog.json",)
    if artifact == ARTIFACT_PREDICTIONS:
        return ("predictions.json",)
    if artifact == ARTIFACT_METRICS:
        return ("metrics.json",)
    return ()


def _write_entry(
    cache_dir: Path,
    artifact: str,
    identity: dict[str, str | None],
    files: dict[str, Any],
) -> None:
    dest = cache_dir / artifact
    dest.mkdir(parents=True, exist_ok=True)
    write_json(
        dest / "meta.json",
        {"artifact": artifact, "input_identity": identity},
    )
    for name, payload in files.items():
        write_json(dest / name, payload)
