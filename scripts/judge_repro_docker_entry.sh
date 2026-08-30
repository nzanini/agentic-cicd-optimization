#!/usr/bin/env bash
# Copy a read-only bind mount into /work, then run the README judge path.
# Used to simulate a clean environment. Judges do not need this file.
set -euo pipefail

SRC="${1:-/src}"
DEST="${2:-/work}"

rm -rf "${DEST}"
mkdir -p "${DEST}"
tar -C "${SRC}" \
  --exclude=.venv \
  --exclude=outputs \
  --exclude=.pytest_cache \
  --exclude=.ruff_cache \
  --exclude="*.egg-info" \
  --exclude=__pycache__ \
  --exclude=.git \
  -cf - . | tar -C "${DEST}" -xf -

exec bash "${DEST}/scripts/judge_repro.sh" "${DEST}"
