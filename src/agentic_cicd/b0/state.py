"""Shared filesystem + in-memory state for one B0 run."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentic_cicd.ranker.io_util import read_json, write_json


@dataclass
class RunState:
    source: str
    target: str
    fixtures_dir: Path
    work_dir: Path
    registry_dir: Path
    run_id: str
    promote_mode: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def job_dir(self, name: str) -> Path:
        path = self.work_dir / "jobs" / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def workload_dir(self) -> Path:
        path = self.work_dir / "workload"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_pointer(self, environment: str, payload: dict[str, Any]) -> Path:
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        path = self.registry_dir / f"{environment}.json"
        write_json(path, payload)
        return path

    def read_pointer(self, environment: str) -> dict[str, Any] | None:
        path = self.registry_dir / f"{environment}.json"
        if not path.is_file():
            return None
        data = read_json(path)
        if not isinstance(data, dict):
            msg = f"invalid registry pointer: {path}"
            raise ValueError(msg)
        return data
