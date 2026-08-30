"""Load and validate machine-readable scenario ground truth."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "id",
    "title",
    "description",
    "source",
    "target",
    "files_changed",
    "expected_legal",
    "expected_run_status",
    "required_jobs",
    "blocked_jobs",
    "setup",
    "apply",
    "artifact",
    "rationale",
)

KNOWN_JOBS = {
    "branch_guard",
    "validate",
    "test",
    "ingest",
    "prepare",
    "score",
    "evaluate",
    "package",
    "publish",
    "promote",
}


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    source: str
    target: str
    files_changed: list[str]
    expected_legal: bool
    expected_run_status: str
    required_jobs: list[str]
    blocked_jobs: list[str]
    setup: str
    apply: list[dict[str, Any]]
    artifact: dict[str, Any]
    rationale: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Scenario:
        missing = [field for field in REQUIRED_FIELDS if field not in raw]
        if missing:
            msg = f"scenario missing fields {missing}: {raw.get('id')}"
            raise ValueError(msg)
        required = list(raw["required_jobs"])
        unknown = [job for job in required if job not in KNOWN_JOBS]
        if unknown:
            msg = f"{raw['id']} has unknown required jobs: {unknown}"
            raise ValueError(msg)
        if raw["expected_run_status"] not in {"succeeded", "failed"}:
            msg = f"{raw['id']} has invalid expected_run_status"
            raise ValueError(msg)
        if not required:
            msg = f"{raw['id']} required_jobs must be non-empty"
            raise ValueError(msg)
        return cls(
            id=str(raw["id"]),
            title=str(raw["title"]),
            description=str(raw["description"]),
            source=str(raw["source"]),
            target=str(raw["target"]),
            files_changed=list(raw["files_changed"]),
            expected_legal=bool(raw["expected_legal"]),
            expected_run_status=str(raw["expected_run_status"]),
            required_jobs=required,
            blocked_jobs=list(raw["blocked_jobs"]),
            setup=str(raw["setup"]),
            apply=list(raw["apply"]),
            artifact=dict(raw["artifact"]),
            rationale=str(raw["rationale"]),
        )


def default_scenarios_path() -> Path:
    return Path(__file__).resolve().parents[3] / "benchmark" / "scenarios.json"


def agent_value_scenarios_path() -> Path:
    return Path(__file__).resolve().parents[3] / "benchmark" / "agent_value_scenarios.json"


def load_scenarios(path: Path | None = None) -> list[Scenario]:
    source = path or default_scenarios_path()
    payload = json.loads(source.read_text(encoding="utf-8"))
    raw_list = payload.get("scenarios")
    if not isinstance(raw_list, list) or not raw_list:
        msg = f"no scenarios in {source}"
        raise ValueError(msg)
    scenarios = [Scenario.from_dict(item) for item in raw_list]
    ids = [scenario.id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        msg = "duplicate scenario ids"
        raise ValueError(msg)
    return scenarios
