#!/usr/bin/env bash
# Optional helper: same commands as the README judge path.
# Not required. Does not use GitHub Actions, Ollama, API keys, or extra Git branches.
set -euo pipefail

ROOT="${1:-/work}"
if [[ ! -f "${ROOT}/pyproject.toml" ]]; then
  echo "usage: judge_repro.sh /path/to/repo" >&2
  exit 2
fi
cd "${ROOT}"

echo "===== python ====="
python --version

echo "===== install ====="
python -m pip install -U pip
python -m pip install -e ".[dev]"

echo "===== B0 baseline ====="
python -m agentic_cicd benchmark --output outputs/benchmark-b0

echo "===== B1 optimized solution (compare) ====="
python -m agentic_cicd benchmark --system compare --output outputs/benchmark-compare

echo "===== tests ====="
python -m pytest

echo "===== lint / format ====="
python -m ruff check .
python -m ruff format --check .

echo "===== judge path done ====="
