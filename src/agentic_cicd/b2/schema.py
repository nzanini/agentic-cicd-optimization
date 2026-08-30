"""Validate b2_proposal. Invalid proposals never reach the executor."""

from __future__ import annotations

from typing import Any

from agentic_cicd.b0.graph import JOBS

KNOWN_JOBS = frozenset(JOBS)
KNOWN_JOBS_ORDER: tuple[str, ...] = tuple(JOBS)
KNOWN_COMPONENTS = frozenset(
    {
        "documentation",
        "tests",
        "pipeline_metadata",
        "scoring_overlay",
        "catalog",
        "personas",
        "frozen_model",
        "ingest_code",
        "prepare_code",
        "score_code",
        "evaluate_code",
        "package_code",
        "dependencies",
        "orchestrator",
        "unknown",
    }
)
CACHEABLE_ARTIFACTS = frozenset({"raw_dataset", "prepared_catalog", "predictions", "metrics"})


class ProposalError(ValueError):
    """b2_proposal failed schema validation."""


def proposal_template() -> dict[str, Any]:
    """Minimal valid shape shown to the model. Not an accepted plan."""
    return {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": False,
        "notes": "",
        "discovered_edges": [],
        "jobs": [
            {
                "job": name,
                "decision": "RUN",
                "reason_code": "copy_b1",
                "reason": "keep B1 unless checkable evidence exists",
                "confidence": 0.9,
                "dependencies_considered": [],
                "artifacts_required": [],
                "artifacts_reused": [],
                "evidence": [],
            }
            for name in KNOWN_JOBS_ORDER
        ],
    }


def expand_copy_b1(raw: dict[str, Any]) -> dict[str, Any]:
    """Fill omitted jobs as RUN. Verifier still judges every SKIP."""
    if raw.get("copy_b1") is not True:
        return raw
    jobs = raw.get("jobs")
    if jobs is None:
        jobs = []
    if not isinstance(jobs, list):
        raise ProposalError("jobs must be a list")
    seen: set[str] = set()
    filled: list[Any] = []
    for item in jobs:
        if isinstance(item, dict) and item.get("job") in KNOWN_JOBS:
            seen.add(str(item["job"]))
            if item.get("decision") not in {"RUN", "SKIP"}:
                item = {
                    **item,
                    "decision": "RUN",
                    "reason_code": item.get("reason_code") or "copy_b1",
                }
        filled.append(item)
    for name in KNOWN_JOBS_ORDER:
        if name in seen:
            continue
        filled.append(
            {
                "job": name,
                "decision": "RUN",
                "reason_code": "copy_b1",
                "reason": "unspecified job copied as RUN",
                "confidence": 0.9,
                "dependencies_considered": [],
                "artifacts_required": [],
                "artifacts_reused": [],
                "evidence": [],
            }
        )
    expanded = dict(raw)
    expanded["jobs"] = filled
    return expanded


def validate_proposal(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ProposalError("proposal is not an object")
    raw = expand_copy_b1(raw)
    if raw.get("kind") != "b2_proposal":
        raise ProposalError("kind must be b2_proposal")
    if raw.get("schema_version") != 1:
        raise ProposalError("schema_version must be 1")
    if not isinstance(raw.get("uncertain"), bool):
        raise ProposalError("uncertain must be a boolean")
    jobs = raw.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ProposalError("jobs must be a non-empty list")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in jobs:
        normalized.append(_job(item))
        name = normalized[-1]["job"]
        if name in seen:
            raise ProposalError(f"duplicate job {name}")
        seen.add(name)
    missing = KNOWN_JOBS - seen
    if missing:
        raise ProposalError(f"missing jobs: {sorted(missing)}")
    extra = seen - KNOWN_JOBS
    if extra:
        raise ProposalError(f"unknown jobs: {sorted(extra)}")
    edges = raw.get("discovered_edges") or []
    if not isinstance(edges, list):
        raise ProposalError("discovered_edges must be a list")
    parsed_edges = [_edge(item) for item in edges]
    return {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": raw["uncertain"],
        "notes": str(raw.get("notes") or ""),
        "discovered_edges": parsed_edges,
        "jobs": normalized,
    }


def _job(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ProposalError("job entry must be an object")
    name = item.get("job")
    if name not in KNOWN_JOBS:
        raise ProposalError(f"unknown job: {name!r}")
    decision = item.get("decision")
    if decision not in {"RUN", "SKIP"}:
        raise ProposalError(f"{name}: decision must be RUN or SKIP")
    confidence = item.get("confidence", 1.0)
    if not isinstance(confidence, int | float) or not 0.0 <= float(confidence) <= 1.0:
        raise ProposalError(f"{name}: confidence must be in [0, 1]")
    evidence = item.get("evidence") or []
    if not isinstance(evidence, list):
        raise ProposalError(f"{name}: evidence must be a list")
    reused = item.get("artifacts_reused") or []
    if not isinstance(reused, list):
        raise ProposalError(f"{name}: artifacts_reused must be a list")
    for artifact in reused:
        if artifact not in CACHEABLE_ARTIFACTS:
            raise ProposalError(f"{name}: unsupported artifact reuse {artifact!r}")
    return {
        "job": name,
        "decision": decision,
        "reason_code": str(item.get("reason_code") or ""),
        "reason": str(item.get("reason") or ""),
        "confidence": float(confidence),
        "dependencies_considered": list(item.get("dependencies_considered") or []),
        "artifacts_required": list(item.get("artifacts_required") or []),
        "artifacts_reused": list(reused),
        "evidence": [_evidence(entry) for entry in evidence],
    }


def _edge(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ProposalError("discovered_edge must be an object")
    component = item.get("to_component")
    if component not in KNOWN_COMPONENTS:
        raise ProposalError(f"unknown to_component: {component!r}")
    evidence = item.get("evidence") or []
    if not isinstance(evidence, list):
        raise ProposalError("edge evidence must be a list")
    return {
        "from_path": str(item.get("from_path") or ""),
        "to_component": component,
        "via": str(item.get("via") or ""),
        "evidence": [_evidence(entry) for entry in evidence],
    }


def _evidence(item: Any) -> dict[str, str]:
    if not isinstance(item, dict):
        raise ProposalError("evidence must be an object")
    return {
        "type": str(item.get("type") or ""),
        "path": str(item.get("path") or ""),
        "detail": str(item.get("detail") or ""),
    }
