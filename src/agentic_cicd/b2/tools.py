"""Read-only B2 tools. No write, shell, or skip authority."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_cicd.b0.graph import JOBS
from agentic_cicd.b1.cache import fixture_identity, has_valid
from agentic_cicd.b1.classify import classify_path, normalize_path
from agentic_cicd.b1.impact import CONSUMES, PRODUCER
from agentic_cicd.b1.planner import Plan
from agentic_cicd.ranker.io_util import read_json

MAX_READ_CHARS = 8000
MAX_SEARCH_HITS = 20
MAX_SEARCH_FILES = 400
MAX_SEARCH_FILE_BYTES = 200_000
SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        "outputs",
        ".ruff_cache",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
        ".mypy_cache",
    }
)
BLOCKED_NAMES = frozenset({".env", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"})
BLOCKED_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx"})

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a bounded slice of a file under the workspace or repo jail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 200},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_repo",
            "description": "Search workspace and repo text files for a regex.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "glob": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_diff",
            "description": "Return the harness-provided diff for a changed path, if any.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_b1_plan",
            "description": "Return the already computed B1 plan.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_job_graph",
            "description": "Jobs, costs, producers, and consumers.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_cache",
            "description": "Identity-checked cache validity for one artifact.",
            "parameters": {
                "type": "object",
                "properties": {"artifact": {"type": "string"}},
                "required": ["artifact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_pointer",
            "description": "Return artifact_id for development or production.",
            "parameters": {
                "type": "object",
                "properties": {"environment": {"type": "string"}},
                "required": ["environment"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "classify_path",
            "description": "What B1 would call this path.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
]


class ToolError(ValueError):
    """Bounded tool refused the call."""


@dataclass
class Toolbelt:
    plan: Plan
    fixtures_dir: Path
    cache_dir: Path | None
    registry_dir: Path | None
    workspace: Path | None
    repo: Path | None
    diffs: dict[str, str]

    def roots(self) -> list[Path]:
        return [path for path in (self.workspace, self.repo) if path is not None and path.is_dir()]

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "read_file":
            return self.read_file(
                str(arguments.get("path") or ""),
                int(arguments.get("offset") or 0),
                int(arguments.get("limit") or 200),
            )
        if name == "search_repo":
            return self.search_repo(str(arguments.get("pattern") or ""), arguments.get("glob"))
        if name == "inspect_diff":
            return self.inspect_diff(str(arguments.get("path") or ""))
        if name == "inspect_b1_plan":
            return self.inspect_b1_plan()
        if name == "inspect_job_graph":
            return self.inspect_job_graph()
        if name == "inspect_cache":
            return self.inspect_cache(str(arguments.get("artifact") or ""))
        if name == "inspect_pointer":
            return self.inspect_pointer(str(arguments.get("environment") or ""))
        if name == "classify_path":
            path = str(arguments.get("path") or "")
            return {"path": path, "component": classify_path(path)}
        raise ToolError(f"unknown tool {name}")

    def read_file(self, path: str, offset: int, limit: int) -> dict[str, Any]:
        resolved = resolve_readable(path, self.roots())
        text = resolved.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        start = max(offset, 0)
        end = start + max(min(limit, 400), 1)
        chunk = "\n".join(lines[start:end])
        if len(chunk) > MAX_READ_CHARS:
            chunk = chunk[:MAX_READ_CHARS]
        return {
            "path": normalize_path(path),
            "offset": start,
            "limit": end - start,
            "truncated": len(text.splitlines()) > end or len(chunk) >= MAX_READ_CHARS,
            "content": chunk,
        }

    def search_repo(self, pattern: str, glob: str | None) -> dict[str, Any]:
        if not pattern or len(pattern) > 200:
            raise ToolError("pattern must be a non-empty regex of at most 200 characters")
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ToolError(f"invalid regex: {exc}") from exc
        hits: list[dict[str, str]] = []
        scanned = 0
        suffix = _glob_suffix(glob)
        for root in self.roots():
            for file_path in _iter_files(root):
                scanned += 1
                if scanned > MAX_SEARCH_FILES or len(hits) >= MAX_SEARCH_HITS:
                    break
                posix = file_path.as_posix()
                if suffix and not file_path.name.endswith(suffix) and suffix not in posix:
                    continue
                if file_path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for index, line in enumerate(text.splitlines(), start=1):
                    if compiled.search(line):
                        rel = file_path.relative_to(root).as_posix()
                        hits.append({"path": rel, "line": str(index), "text": line[:240]})
                        if len(hits) >= MAX_SEARCH_HITS:
                            break
        return {"pattern": pattern, "hits": hits, "truncated": len(hits) >= MAX_SEARCH_HITS}

    def inspect_diff(self, path: str) -> dict[str, Any]:
        key = normalize_path(path)
        if key in self.diffs:
            return {"path": key, "diff": self.diffs[key][:MAX_READ_CHARS]}
        return {"path": key, "diff": None, "note": "no harness diff for this path"}

    def inspect_b1_plan(self) -> dict[str, Any]:
        return {
            "flow": self.plan.flow,
            "promote_mode": self.plan.promote_mode,
            "run": list(self.plan.run),
            "components": list(self.plan.components),
            "invalidated": list(self.plan.invalidated),
            "decisions": [
                {
                    "job": item.job_name,
                    "decision": item.decision,
                    "reason_code": item.reason_code,
                    "reason": item.reason,
                }
                for item in self.plan.decisions
            ],
        }

    def inspect_job_graph(self) -> dict[str, Any]:
        return {
            "jobs": {
                name: {
                    "simulated_cost": spec.simulated_cost,
                    "depends_on": list(spec.depends_on),
                    "order": spec.order,
                }
                for name, spec in JOBS.items()
            },
            "produces": dict(PRODUCER),
            "consumes": {job: list(arts) for job, arts in CONSUMES.items()},
        }

    def inspect_cache(self, artifact: str) -> dict[str, Any]:
        valid = has_valid(self.cache_dir, artifact, self.fixtures_dir)
        stored = None
        if self.cache_dir is not None:
            meta = self.cache_dir / artifact / "meta.json"
            if meta.is_file():
                payload = read_json(meta)
                stored = payload.get("input_identity") if isinstance(payload, dict) else None
        return {
            "artifact": artifact,
            "has_valid": valid,
            "stored_identity": stored,
            "current_identity": fixture_identity(self.fixtures_dir),
            "note": "existence alone is not a cache hit",
        }

    def inspect_pointer(self, environment: str) -> dict[str, Any]:
        if environment not in {"development", "production"}:
            raise ToolError("environment must be development or production")
        if self.registry_dir is None:
            return {"environment": environment, "artifact_id": None}
        path = self.registry_dir / f"{environment}.json"
        if not path.is_file():
            return {"environment": environment, "artifact_id": None}
        payload = read_json(path)
        artifact_id = payload.get("artifact_id") if isinstance(payload, dict) else None
        return {"environment": environment, "artifact_id": artifact_id}


def resolve_readable(path: str, roots: list[Path]) -> Path:
    rel = normalize_path(path)
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise ToolError("path is outside the tool jail")
    name = Path(rel).name
    if name in BLOCKED_NAMES or name.startswith(".env") or Path(rel).suffix in BLOCKED_SUFFIXES:
        raise ToolError("refusing to read a credential or secret path")
    if not roots:
        raise ToolError("no searchable roots")
    for root in roots:
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    raise ToolError(f"file not found in jail: {rel}")


def _glob_suffix(glob: str | None) -> str | None:
    if not glob:
        return None
    if glob.startswith("*."):
        return glob[1:]
    return glob.replace("**/", "")


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name = path.name
        if name in BLOCKED_NAMES or name.startswith(".env") or path.suffix in BLOCKED_SUFFIXES:
            continue
        yield path
