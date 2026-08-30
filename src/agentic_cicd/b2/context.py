"""Bounded B2 context. No scenario id, required_jobs, or secrets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_cicd.b0.graph import JOBS
from agentic_cicd.b1.cache import CACHEABLE, fixture_identity, has_valid
from agentic_cicd.b1.classify import CONSERVATIVE_COMPONENTS, classify_path
from agentic_cicd.b1.impact import CONSUMES, PRODUCER
from agentic_cicd.b1.planner import Plan
from agentic_cicd.b2.tools import BLOCKED_NAMES, BLOCKED_SUFFIXES, MAX_READ_CHARS, resolve_readable
from agentic_cicd.ranker.io_util import read_json

PREVIEW_CHARS = 4000


def build_context(
    *,
    source: str,
    target: str,
    changed_paths: list[str] | None,
    plan: Plan,
    fixtures_dir: Path,
    cache_dir: Path | None,
    registry_dir: Path | None,
    workspace: Path | None,
    repo: Path | None,
) -> dict[str, Any]:
    roots = [path for path in (workspace, repo) if path is not None and path.is_dir()]
    return {
        "source": source,
        "target": target,
        "flow": plan.flow,
        "changed_paths": None if changed_paths is None else list(changed_paths),
        "b1_plan": {
            "promote_mode": plan.promote_mode,
            "run": list(plan.run),
            "components": list(plan.components),
            "invalidated": list(plan.invalidated),
            "decisions": [
                {
                    "job": item.job_name,
                    "decision": item.decision,
                    "reason_code": item.reason_code,
                    "reason": item.reason,
                }
                for item in plan.decisions
            ],
        },
        "job_graph": {
            "costs": {name: spec.simulated_cost for name, spec in JOBS.items()},
            "produces": dict(PRODUCER),
            "consumes": {job: list(arts) for job, arts in CONSUMES.items()},
        },
        "cache": _cache_view(fixtures_dir, cache_dir),
        "pointers": _pointers(registry_dir),
        "unclassified_previews": _previews(changed_paths, roots),
        "rules": [
            "Return one JSON object with schema_version 1 and kind=b2_proposal.",
            "Cover every known job. Do not execute jobs; the verifier decides.",
            "Never skip branch_guard.",
            "Absence of search hits is not proof that a file is inert.",
            "Only propose a narrower SKIP with mechanically checkable evidence.",
            "Tools are optional; unclassified previews are already included.",
        ],
    }


def _cache_view(fixtures_dir: Path, cache_dir: Path | None) -> dict[str, Any]:
    identity = fixture_identity(fixtures_dir)
    artifacts = {}
    for name in CACHEABLE:
        artifacts[name] = {"has_valid": has_valid(cache_dir, name, fixtures_dir)}
    return {"current_identity": identity, "artifacts": artifacts}


def _pointers(registry_dir: Path | None) -> dict[str, str | None]:
    result: dict[str, str | None] = {"development": None, "production": None}
    if registry_dir is None:
        return result
    for name in result:
        path = registry_dir / f"{name}.json"
        if not path.is_file():
            continue
        try:
            payload = read_json(path)
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            artifact_id = payload.get("artifact_id")
            result[name] = artifact_id if isinstance(artifact_id, str) else None
    return result


def _previews(changed_paths: list[str] | None, roots: list[Path]) -> list[dict[str, Any]]:
    if not changed_paths:
        return []
    previews: list[dict[str, Any]] = []
    for path in changed_paths:
        if classify_path(path) not in CONSERVATIVE_COMPONENTS:
            continue
        name = Path(path).name
        suffix = Path(path).suffix
        if name in BLOCKED_NAMES or name.startswith(".env") or suffix in BLOCKED_SUFFIXES:
            continue
        try:
            resolved = resolve_readable(path, roots)
            text = resolved.read_text(encoding="utf-8", errors="replace")[:PREVIEW_CHARS]
        except (OSError, ValueError):
            previews.append({"path": path, "available": False})
            continue
        previews.append(
            {
                "path": path,
                "available": True,
                "truncated": len(text) >= PREVIEW_CHARS,
                "content": text[:MAX_READ_CHARS],
            }
        )
    return previews
