"""B0 job implementations. Each job always does its full work when scheduled."""

from __future__ import annotations

from typing import Any

from agentic_cicd.b0.graph import PROMOTE_REUSE, classify_flow, normalize_promote_mode
from agentic_cicd.b0.state import RunState
from agentic_cicd.ranker.evaluate import evaluate_predictions
from agentic_cicd.ranker.identity import compute_artifact_id
from agentic_cicd.ranker.ingest import (
    configs_dir,
    dataset_manifest,
    fixture_paths,
    load_catalog,
    load_effective_model,
    load_personas,
    scoring_weights_path,
)
from agentic_cicd.ranker.io_util import read_json, write_json
from agentic_cicd.ranker.package import build_bundle_payload, model_manifest, write_bundle
from agentic_cicd.ranker.prepare import prepare_catalog
from agentic_cicd.ranker.score import rank_catalog


class JobError(RuntimeError):
    """A required B0 job failed."""


def run_job(name: str, state: RunState) -> dict[str, Any]:
    handlers = {
        "branch_guard": job_branch_guard,
        "validate": job_validate,
        "test": job_test,
        "ingest": job_ingest,
        "prepare": job_prepare,
        "score": job_score,
        "evaluate": job_evaluate,
        "package": job_package,
        "publish": job_publish,
        "promote": job_promote,
    }
    return handlers[name](state)


def job_branch_guard(state: RunState) -> dict[str, Any]:
    flow = classify_flow(state.source, state.target)
    allowed = flow != "illegal"
    report = {
        "source": state.source,
        "target": state.target,
        "flow": flow,
        "allowed": allowed,
    }
    write_json(state.job_dir("branch_guard") / "verdict.json", report)
    if not allowed:
        msg = f"illegal promotion {state.source} → {state.target}"
        raise JobError(msg)
    return {
        "inputs": {"source": state.source, "target": state.target},
        "outputs": {"verdict": "jobs/branch_guard/verdict.json"},
    }


def job_validate(state: RunState) -> dict[str, Any]:
    paths = fixture_paths(state.fixtures_dir)
    missing = [key for key, path in paths.items() if not path.is_file()]
    if missing:
        msg = f"missing fixtures: {missing}"
        raise JobError(msg)
    catalog = read_json(paths["catalog"])
    personas = read_json(paths["personas"])
    model = read_json(paths["model"])
    problems: list[str] = []
    if not isinstance(catalog, dict) or "items" not in catalog:
        problems.append("catalog.json must contain items")
    if not isinstance(personas, dict) or "personas" not in personas:
        problems.append("personas.json must contain personas")
    if not isinstance(model, dict) or "top_n" not in model or "genre_weights" not in model:
        problems.append("model/ranker.json must contain top_n and genre_weights")
    overlay = scoring_weights_path(state.fixtures_dir)
    if overlay.is_file():
        weights = read_json(overlay)
        if not isinstance(weights, dict):
            problems.append("configs/scoring_weights.json must be a JSON object")
    pipeline_cfg = configs_dir(state.fixtures_dir) / "pipeline.json"
    if pipeline_cfg.is_file():
        pipeline = read_json(pipeline_cfg)
        if not isinstance(pipeline, dict):
            problems.append("configs/pipeline.json must be a JSON object")
    report = {
        "ok": not problems,
        "problems": problems,
        "paths": {k: v.as_posix() for k, v in paths.items()},
    }
    write_json(state.job_dir("validate") / "report.json", report)
    if problems:
        raise JobError("; ".join(problems))
    return {
        "inputs": {"fixtures_dir": state.fixtures_dir.as_posix()},
        "outputs": {"report": "jobs/validate/report.json"},
    }


def job_test(state: RunState) -> dict[str, Any]:
    paths = fixture_paths(state.fixtures_dir)
    catalog = load_catalog(paths["catalog"])
    personas = load_personas(paths["personas"])
    model = load_effective_model(state.fixtures_dir)
    prepared = prepare_catalog(catalog)
    predictions = rank_catalog(prepared, personas, model)
    checks = {
        "prepared_count": len(prepared),
        "persona_count": len(predictions["rankings"]),
        "top_n": predictions["top_n"],
        "passed": True,
    }
    write_json(state.job_dir("test") / "report.json", checks)
    return {
        "inputs": {"fixtures_dir": state.fixtures_dir.as_posix()},
        "outputs": {"report": "jobs/test/report.json"},
        "note": "in-process ranker smoke; not the repo pytest suite",
    }


def job_ingest(state: RunState) -> dict[str, Any]:
    paths = fixture_paths(state.fixtures_dir)
    catalog = load_catalog(paths["catalog"])
    personas = load_personas(paths["personas"])
    manifest = dataset_manifest(paths["catalog"], paths["personas"], catalog, personas)
    work = state.workload_dir()
    write_json(work / "raw_catalog.json", catalog)
    write_json(work / "personas.json", personas)
    write_json(work / "dataset_manifest.json", manifest)
    state.data["catalog"] = catalog
    state.data["personas"] = personas
    state.data["dataset_manifest"] = manifest
    return {
        "inputs": {
            "catalog": paths["catalog"].as_posix(),
            "personas": paths["personas"].as_posix(),
        },
        "outputs": {
            "raw_catalog": "workload/raw_catalog.json",
            "dataset_manifest": "workload/dataset_manifest.json",
        },
        "hashes": {"catalog_sha256": manifest["catalog_sha256"]},
    }


def job_prepare(state: RunState) -> dict[str, Any]:
    catalog = state.data.get("catalog") or read_json(state.workload_dir() / "raw_catalog.json")
    prepared = prepare_catalog(catalog)
    write_json(state.workload_dir() / "prepared_catalog.json", {"items": prepared})
    state.data["prepared"] = prepared
    return {
        "inputs": {"raw_catalog": "workload/raw_catalog.json"},
        "outputs": {"prepared_catalog": "workload/prepared_catalog.json"},
        "record_count": len(prepared),
    }


def job_score(state: RunState) -> dict[str, Any]:
    paths = fixture_paths(state.fixtures_dir)
    prepared = state.data.get("prepared")
    if prepared is None:
        prepared = read_json(state.workload_dir() / "prepared_catalog.json")["items"]
    personas = state.data.get("personas") or read_json(state.workload_dir() / "personas.json")
    model = load_effective_model(state.fixtures_dir)
    predictions = rank_catalog(prepared, personas, model)
    write_json(state.workload_dir() / "predictions.json", predictions)
    state.data["model"] = model
    state.data["predictions"] = predictions
    state.data["model_path"] = paths["model"]
    return {
        "inputs": {
            "prepared_catalog": "workload/prepared_catalog.json",
            "model": paths["model"].as_posix(),
        },
        "outputs": {"predictions": "workload/predictions.json"},
    }


def job_evaluate(state: RunState) -> dict[str, Any]:
    prepared = state.data.get("prepared")
    if prepared is None:
        prepared = read_json(state.workload_dir() / "prepared_catalog.json")["items"]
    personas = state.data.get("personas") or read_json(state.workload_dir() / "personas.json")
    stored = state.data.get("predictions")
    predictions = stored or read_json(state.workload_dir() / "predictions.json")
    metrics = evaluate_predictions(predictions, prepared, personas)
    write_json(state.workload_dir() / "metrics.json", metrics)
    state.data["metrics"] = metrics
    return {
        "inputs": {"predictions": "workload/predictions.json"},
        "outputs": {"metrics": "workload/metrics.json"},
        "hashes": {"predictions_sha256": metrics["predictions_sha256"]},
    }


def job_package(state: RunState) -> dict[str, Any]:
    work = state.workload_dir()
    paths = fixture_paths(state.fixtures_dir)
    predictions = state.data.get("predictions") or read_json(work / "predictions.json")
    metrics = state.data.get("metrics") or read_json(work / "metrics.json")
    manifest = state.data.get("dataset_manifest") or read_json(work / "dataset_manifest.json")
    model = state.data.get("model") or load_effective_model(state.fixtures_dir)
    model_path = state.data.get("model_path") or paths["model"]
    model_meta = model_manifest(model_path, model, scoring_weights_path(state.fixtures_dir))
    payload = build_bundle_payload(
        predictions=predictions,
        metrics=metrics,
        dataset_manifest=manifest,
        model_manifest_data=model_meta,
        model=model,
    )
    artifact_id = compute_artifact_id(payload)
    write_json(work / "model_manifest.json", model_meta)
    write_bundle(work, payload, artifact_id)
    state.data["artifact_id"] = artifact_id
    return {
        "inputs": {"metrics": "workload/metrics.json"},
        "outputs": {"bundle": "workload/bundle/artifact.json"},
        "artifact_id": artifact_id,
    }


def job_publish(state: RunState) -> dict[str, Any]:
    artifact_id = state.data["artifact_id"]
    pointer = {
        "environment": "development",
        "artifact_id": artifact_id,
        "bundle": (state.workload_dir() / "bundle").as_posix(),
        "source": state.source,
        "target": state.target,
        "run_id": state.run_id,
    }
    path = state.write_pointer("development", pointer)
    write_json(state.job_dir("publish") / "pointer.json", pointer)
    return {
        "inputs": {"artifact_id": artifact_id},
        "outputs": {"pointer": path.as_posix()},
        "artifact_id": artifact_id,
    }


def job_promote(state: RunState) -> dict[str, Any]:
    validated = state.read_pointer("development")
    if validated is None:
        raise JobError("no development artifact to promote")
    validated_id = validated.get("artifact_id")
    if not validated_id:
        raise JobError("development pointer is missing artifact_id")
    mode = normalize_promote_mode(state.promote_mode)
    if mode == PROMOTE_REUSE:
        artifact_id = str(validated_id)
        bundle = validated.get("bundle") or (state.workload_dir() / "bundle").as_posix()
    else:
        if "artifact_id" not in state.data:
            raise JobError("no rebuilt artifact to promote")
        artifact_id = str(state.data["artifact_id"])
        bundle = (state.workload_dir() / "bundle").as_posix()
    state.data["artifact_id"] = artifact_id
    pointer = {
        "environment": "production",
        "artifact_id": artifact_id,
        "validated_artifact_id": validated_id,
        "bundle": bundle,
        "source": state.source,
        "target": state.target,
        "run_id": state.run_id,
        "promote_mode": mode,
    }
    path = state.write_pointer("production", pointer)
    write_json(state.job_dir("promote") / "pointer.json", pointer)
    return {
        "inputs": {"artifact_id": artifact_id, "validated_artifact_id": validated_id},
        "outputs": {"pointer": path.as_posix()},
        "artifact_id": artifact_id,
    }
