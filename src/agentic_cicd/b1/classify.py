"""Map repository paths to change components. No scenario IDs."""

from __future__ import annotations

COMPONENT_DOCUMENTATION = "documentation"
COMPONENT_TESTS = "tests"
COMPONENT_PIPELINE_METADATA = "pipeline_metadata"
COMPONENT_SCORING_OVERLAY = "scoring_overlay"
COMPONENT_CATALOG = "catalog"
COMPONENT_PERSONAS = "personas"
COMPONENT_FROZEN_MODEL = "frozen_model"
COMPONENT_INGEST_CODE = "ingest_code"
COMPONENT_PREPARE_CODE = "prepare_code"
COMPONENT_SCORE_CODE = "score_code"
COMPONENT_EVALUATE_CODE = "evaluate_code"
COMPONENT_PACKAGE_CODE = "package_code"
COMPONENT_DEPENDENCIES = "dependencies"
COMPONENT_ORCHESTRATOR = "orchestrator"
COMPONENT_UNKNOWN = "unknown"

CONSERVATIVE_COMPONENTS = frozenset(
    {
        COMPONENT_DEPENDENCIES,
        COMPONENT_ORCHESTRATOR,
        COMPONENT_UNKNOWN,
    }
)

_DEPENDENCY_NAMES = frozenset(
    {
        "pyproject.toml",
        "poetry.lock",
        "pdm.lock",
        "uv.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "Pipfile",
        "Pipfile.lock",
    }
)


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def classify_path(path: str) -> str:
    """Return the component for one changed path. Unmapped paths are unknown."""
    rel = normalize_path(path)
    name = rel.rsplit("/", 1)[-1]

    if rel == "README.md" or rel.startswith("docs/") or ("/" not in rel and rel.endswith(".md")):
        return COMPONENT_DOCUMENTATION
    if rel.startswith("tests/"):
        return COMPONENT_TESTS
    if rel == "configs/pipeline.json":
        return COMPONENT_PIPELINE_METADATA
    if rel == "configs/scoring_weights.json" or name == "scoring_weights.json":
        return COMPONENT_SCORING_OVERLAY
    if rel == "fixtures/catalog.json" or rel.endswith("/catalog.json"):
        return COMPONENT_CATALOG
    if rel == "fixtures/personas.json" or rel.endswith("/personas.json"):
        return COMPONENT_PERSONAS
    if rel == "fixtures/model/ranker.json" or rel.endswith("model/ranker.json"):
        return COMPONENT_FROZEN_MODEL
    if rel.endswith("ranker/ingest.py"):
        return COMPONENT_INGEST_CODE
    if rel.endswith("ranker/prepare.py"):
        return COMPONENT_PREPARE_CODE
    if rel.endswith("ranker/score.py"):
        return COMPONENT_SCORE_CODE
    if rel.endswith("ranker/evaluate.py"):
        return COMPONENT_EVALUATE_CODE
    if rel.endswith("ranker/package.py") or rel.endswith("ranker/identity.py"):
        return COMPONENT_PACKAGE_CODE
    if name in _DEPENDENCY_NAMES or rel.endswith(".lock"):
        return COMPONENT_DEPENDENCIES
    if (
        "/b0/" in rel
        or rel.startswith("src/agentic_cicd/b0")
        or rel.endswith("/cli.py")
        or rel.endswith("/__main__.py")
        or "/benchmark/" in rel
    ):
        return COMPONENT_ORCHESTRATOR
    return COMPONENT_UNKNOWN


def classify_paths(paths: list[str] | None) -> frozenset[str]:
    """Classify a change set.

    ``None`` means the change set is unknown (fail closed).
    An empty list means a known-empty change (docs-like / clean promote).
    """
    if paths is None:
        return frozenset({COMPONENT_UNKNOWN})
    return frozenset(classify_path(path) for path in paths)
