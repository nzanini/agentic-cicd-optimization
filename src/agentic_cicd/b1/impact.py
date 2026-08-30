"""Component → invalidated artifacts → producer jobs. No scenario IDs."""

from __future__ import annotations

from agentic_cicd.b1.classify import (
    COMPONENT_CATALOG,
    COMPONENT_DEPENDENCIES,
    COMPONENT_DOCUMENTATION,
    COMPONENT_EVALUATE_CODE,
    COMPONENT_FROZEN_MODEL,
    COMPONENT_INGEST_CODE,
    COMPONENT_ORCHESTRATOR,
    COMPONENT_PACKAGE_CODE,
    COMPONENT_PERSONAS,
    COMPONENT_PIPELINE_METADATA,
    COMPONENT_PREPARE_CODE,
    COMPONENT_SCORE_CODE,
    COMPONENT_SCORING_OVERLAY,
    COMPONENT_TESTS,
    COMPONENT_UNKNOWN,
)

ARTIFACT_VALIDATION = "validation_report"
ARTIFACT_TEST = "test_report"
ARTIFACT_RAW = "raw_dataset"
ARTIFACT_PREPARED = "prepared_catalog"
ARTIFACT_PREDICTIONS = "predictions"
ARTIFACT_METRICS = "metrics"
ARTIFACT_BUNDLE = "bundle"

ALL_ARTIFACTS = frozenset(
    {
        ARTIFACT_VALIDATION,
        ARTIFACT_TEST,
        ARTIFACT_RAW,
        ARTIFACT_PREPARED,
        ARTIFACT_PREDICTIONS,
        ARTIFACT_METRICS,
        ARTIFACT_BUNDLE,
    }
)

BUNDLE_ARTIFACTS = frozenset(
    {
        ARTIFACT_RAW,
        ARTIFACT_PREPARED,
        ARTIFACT_PREDICTIONS,
        ARTIFACT_METRICS,
        ARTIFACT_BUNDLE,
    }
)

PRODUCER: dict[str, str] = {
    ARTIFACT_VALIDATION: "validate",
    ARTIFACT_TEST: "test",
    ARTIFACT_RAW: "ingest",
    ARTIFACT_PREPARED: "prepare",
    ARTIFACT_PREDICTIONS: "score",
    ARTIFACT_METRICS: "evaluate",
    ARTIFACT_BUNDLE: "package",
}

# Jobs that need an artifact before they can run. Graph edges, not B0 always-run.
CONSUMES: dict[str, tuple[str, ...]] = {
    "prepare": (ARTIFACT_RAW,),
    "score": (ARTIFACT_PREPARED,),
    "evaluate": (ARTIFACT_PREDICTIONS, ARTIFACT_PREPARED),
    "package": (ARTIFACT_PREDICTIONS, ARTIFACT_METRICS, ARTIFACT_RAW),
    "publish": (ARTIFACT_BUNDLE,),
    "promote": (ARTIFACT_BUNDLE,),
}

# Hidden dependency: scoring_weights.json invalidates predictions, not pipeline-only.
_COMPONENT_INVALIDATES: dict[str, frozenset[str]] = {
    COMPONENT_DOCUMENTATION: frozenset(),
    COMPONENT_TESTS: frozenset({ARTIFACT_TEST}),
    COMPONENT_PIPELINE_METADATA: frozenset({ARTIFACT_VALIDATION}),
    COMPONENT_SCORING_OVERLAY: frozenset(
        {ARTIFACT_VALIDATION, ARTIFACT_PREDICTIONS, ARTIFACT_METRICS, ARTIFACT_BUNDLE}
    ),
    COMPONENT_CATALOG: frozenset(
        {
            ARTIFACT_VALIDATION,
            ARTIFACT_RAW,
            ARTIFACT_PREPARED,
            ARTIFACT_PREDICTIONS,
            ARTIFACT_METRICS,
            ARTIFACT_BUNDLE,
        }
    ),
    COMPONENT_PERSONAS: frozenset(
        {
            ARTIFACT_VALIDATION,
            ARTIFACT_RAW,
            ARTIFACT_PREPARED,
            ARTIFACT_PREDICTIONS,
            ARTIFACT_METRICS,
            ARTIFACT_BUNDLE,
        }
    ),
    COMPONENT_FROZEN_MODEL: frozenset(
        {ARTIFACT_VALIDATION, ARTIFACT_PREDICTIONS, ARTIFACT_METRICS, ARTIFACT_BUNDLE}
    ),
    COMPONENT_INGEST_CODE: frozenset(
        {
            ARTIFACT_VALIDATION,
            ARTIFACT_TEST,
            ARTIFACT_RAW,
            ARTIFACT_PREPARED,
            ARTIFACT_PREDICTIONS,
            ARTIFACT_METRICS,
            ARTIFACT_BUNDLE,
        }
    ),
    COMPONENT_PREPARE_CODE: frozenset(
        {
            ARTIFACT_VALIDATION,
            ARTIFACT_TEST,
            ARTIFACT_PREPARED,
            ARTIFACT_PREDICTIONS,
            ARTIFACT_METRICS,
            ARTIFACT_BUNDLE,
        }
    ),
    COMPONENT_SCORE_CODE: frozenset(
        {
            ARTIFACT_VALIDATION,
            ARTIFACT_TEST,
            ARTIFACT_PREDICTIONS,
            ARTIFACT_METRICS,
            ARTIFACT_BUNDLE,
        }
    ),
    COMPONENT_EVALUATE_CODE: frozenset(
        {ARTIFACT_VALIDATION, ARTIFACT_TEST, ARTIFACT_METRICS, ARTIFACT_BUNDLE}
    ),
    COMPONENT_PACKAGE_CODE: frozenset({ARTIFACT_VALIDATION, ARTIFACT_TEST, ARTIFACT_BUNDLE}),
    COMPONENT_DEPENDENCIES: ALL_ARTIFACTS,
    COMPONENT_ORCHESTRATOR: ALL_ARTIFACTS,
    COMPONENT_UNKNOWN: ALL_ARTIFACTS,
}


def invalidated_artifacts(components: frozenset[str]) -> frozenset[str]:
    invalidated: set[str] = set()
    for component in components:
        invalidated.update(_COMPONENT_INVALIDATES.get(component, ALL_ARTIFACTS))
    return frozenset(invalidated)
