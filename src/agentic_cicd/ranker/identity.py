"""Content-addressed artifact identity.

Algorithm (D-018): SHA-256 hex digest of canonical JSON (sorted keys,
compact separators, UTF-8). Bundle payload excludes run timestamps.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HASH_ALGORITHM = "sha256"


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_canonical(obj: Any) -> str:
    return sha256_text(canonical_dumps(obj))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compute_artifact_id(payload: dict[str, Any]) -> str:
    """Return the artifact id for a bundle payload dict."""
    return sha256_canonical(payload)
