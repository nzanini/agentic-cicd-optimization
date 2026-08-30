"""Select required jobs from change impact. No scenario IDs, no LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agentic_cicd.b0.graph import (
    FLOW_DEV_MAIN,
    FLOW_ILLEGAL,
    JOBS,
    PROMOTE_REBUILD,
    PROMOTE_REUSE,
    classify_flow,
    jobs_for_flow,
)
from agentic_cicd.b1.cache import has_valid
from agentic_cicd.b1.classify import (
    COMPONENT_DEPENDENCIES,
    COMPONENT_ORCHESTRATOR,
    COMPONENT_UNKNOWN,
    CONSERVATIVE_COMPONENTS,
    classify_paths,
)
from agentic_cicd.b1.impact import (
    BUNDLE_ARTIFACTS,
    CONSUMES,
    PRODUCER,
    invalidated_artifacts,
)
from agentic_cicd.ranker.io_util import read_json

DECISION_RUN = "RUN"
DECISION_SKIP = "SKIP"

REASON_ALWAYS = "always_required"
REASON_INVALIDATED = "artifact_invalidated"
REASON_CONSUMER = "producer_required_for_consumer"
REASON_CACHE_MISS = "cache_miss"
REASON_CONSERVATIVE = "conservative_unknown_or_ambiguous"
REASON_ILLEGAL = "illegal_flow"
REASON_NOT_ON_FLOW = "not_on_flow"
REASON_UNCHANGED = "inputs_unchanged"
REASON_CACHE_HIT = "cache_hit"
REASON_CLEAN_PROMOTE = "clean_promote_reuse"
REASON_NO_IMPACT = "no_artifact_impact"


@dataclass(frozen=True)
class JobDecision:
    job_name: str
    decision: str
    reason_code: str
    reason: str


@dataclass
class Plan:
    flow: str
    promote_mode: str | None
    run: list[str]
    decisions: list[JobDecision] = field(default_factory=list)
    components: tuple[str, ...] = ()
    invalidated: tuple[str, ...] = ()


def plan_jobs(
    *,
    source: str,
    target: str,
    changed_paths: list[str] | None,
    fixtures_dir: Path,
    cache_dir: Path | None,
    registry_dir: Path | None = None,
) -> Plan:
    flow = classify_flow(source, target)
    components = classify_paths(changed_paths)
    if flow == FLOW_ILLEGAL:
        return _illegal_plan(components)

    conservative = bool(components & CONSERVATIVE_COMPONENTS)
    invalidated = invalidated_artifacts(components)
    reasons: dict[str, tuple[str, str]] = {}
    cache_hits: dict[str, str] = {}

    if flow == FLOW_DEV_MAIN:
        pointer = _has_development_pointer(registry_dir)
        bundle_dirty = bool(invalidated & BUNDLE_ARTIFACTS) or conservative
        if not conservative and not bundle_dirty and pointer:
            mode = PROMOTE_REUSE
            run = {"branch_guard", "promote"}
            reasons["branch_guard"] = (REASON_ALWAYS, "branch_guard is required on every flow")
            reasons["promote"] = (
                REASON_CLEAN_PROMOTE,
                "no bundle input invalidated; reuse validated development artifact id",
            )
        else:
            mode = PROMOTE_REBUILD
            run = {"branch_guard", "promote"}
            reasons["branch_guard"] = (REASON_ALWAYS, "branch_guard is required on every flow")
            reasons["promote"] = (
                REASON_INVALIDATED,
                "dirty promote must point production at the new artifact",
            )
            if conservative:
                run.update(name for name in jobs_for_flow(flow, PROMOTE_REBUILD))
                _mark_run(run, reasons, REASON_CONSERVATIVE, _conservative_text(components))
            elif not pointer:
                run.update(name for name in jobs_for_flow(flow, PROMOTE_REBUILD))
                _mark_run(
                    run,
                    reasons,
                    REASON_CACHE_MISS,
                    "no validated development artifact; rebuild rather than reuse",
                )
            else:
                _add_producers(run, reasons, invalidated)
            run = _expand_producers(
                run, reasons, cache_hits, invalidated, fixtures_dir, cache_dir, mode
            )
            run.discard("publish")
    else:
        mode = None
        run = {"branch_guard"}
        reasons["branch_guard"] = (REASON_ALWAYS, "branch_guard is required on every flow")
        if conservative:
            run.update(jobs_for_flow(flow))
            _mark_run(run, reasons, REASON_CONSERVATIVE, _conservative_text(components))
        else:
            _add_producers(run, reasons, invalidated)
            if "bundle" in invalidated:
                run.add("publish")
                reasons.setdefault(
                    "publish",
                    (REASON_INVALIDATED, "new bundle must be recorded on development"),
                )
            run = _expand_producers(
                run, reasons, cache_hits, invalidated, fixtures_dir, cache_dir, mode
            )
        run.discard("promote")

    if mode == PROMOTE_REUSE:
        ordered = ["branch_guard", "promote"]
    else:
        ordered = [name for name in jobs_for_flow(flow, mode) if name in run]

    decisions = _build_decisions(set(ordered), reasons, cache_hits, flow, mode)
    return Plan(
        flow=flow,
        promote_mode=mode,
        run=ordered,
        decisions=decisions,
        components=tuple(sorted(components)),
        invalidated=tuple(sorted(invalidated)),
    )


def _illegal_plan(components: frozenset[str]) -> Plan:
    decisions = [
        JobDecision(
            "branch_guard",
            DECISION_RUN,
            REASON_ILLEGAL,
            "illegal source/target; fail closed and do not publish or promote",
        )
    ]
    for name in JOBS:
        if name == "branch_guard":
            continue
        decisions.append(
            JobDecision(
                name,
                DECISION_SKIP,
                REASON_NOT_ON_FLOW,
                "job is not scheduled on an illegal flow",
            )
        )
    return Plan(
        flow=FLOW_ILLEGAL,
        promote_mode=None,
        run=["branch_guard"],
        decisions=decisions,
        components=tuple(sorted(components)),
        invalidated=(),
    )


def _has_development_pointer(registry_dir: Path | None) -> bool:
    if registry_dir is None:
        return False
    path = registry_dir / "development.json"
    if not path.is_file():
        return False
    try:
        pointer = read_json(path)
    except (OSError, ValueError):
        return False
    return bool(isinstance(pointer, dict) and pointer.get("artifact_id"))


def _mark_run(
    run: set[str],
    reasons: dict[str, tuple[str, str]],
    code: str,
    text: str,
) -> None:
    for name in run:
        reasons.setdefault(name, (code, text))


def _add_producers(
    run: set[str],
    reasons: dict[str, tuple[str, str]],
    invalidated: frozenset[str],
) -> None:
    for artifact in invalidated:
        job = PRODUCER.get(artifact)
        if job is None:
            continue
        run.add(job)
        reasons.setdefault(
            job,
            (REASON_INVALIDATED, f"{artifact} invalidated by classified change"),
        )


def _expand_producers(
    run: set[str],
    reasons: dict[str, tuple[str, str]],
    cache_hits: dict[str, str],
    invalidated: frozenset[str],
    fixtures_dir: Path,
    cache_dir: Path | None,
    promote_mode: str | None,
) -> set[str]:
    changed = True
    while changed:
        changed = False
        for job in list(run):
            needs = CONSUMES.get(job, ())
            if job == "promote" and promote_mode == PROMOTE_REUSE:
                needs = ()
            for artifact in needs:
                producer = PRODUCER[artifact]
                if artifact in invalidated:
                    if producer not in run:
                        run.add(producer)
                        reasons.setdefault(
                            producer,
                            (REASON_CONSUMER, f"{job} requires invalidated {artifact}"),
                        )
                        changed = True
                    continue
                if has_valid(cache_dir, artifact, fixtures_dir):
                    cache_hits[producer] = artifact
                    continue
                if producer not in run:
                    run.add(producer)
                    reasons.setdefault(
                        producer,
                        (
                            REASON_CACHE_MISS,
                            f"{job} needs {artifact} and no verified cache exists",
                        ),
                    )
                    changed = True
    return run


def _conservative_text(components: frozenset[str]) -> str:
    if COMPONENT_UNKNOWN in components:
        return "unclassified path; fail closed and run every legal job"
    if COMPONENT_DEPENDENCIES in components:
        return "dependency metadata may affect every stage; run every legal job"
    if COMPONENT_ORCHESTRATOR in components:
        return "orchestrator/CLI change is not proven local; run every legal job"
    return "ambiguous impact; fail closed and run every legal job"


def _build_decisions(
    run: set[str],
    reasons: dict[str, tuple[str, str]],
    cache_hits: dict[str, str],
    flow: str,
    mode: str | None,
) -> list[JobDecision]:
    legal = set(jobs_for_flow(flow, mode or PROMOTE_REBUILD))
    if mode == PROMOTE_REUSE:
        legal = {"branch_guard", "promote"}
    decisions: list[JobDecision] = []
    for name in sorted(JOBS, key=lambda item: (JOBS[item].order, item)):
        if name in run:
            code, text = reasons.get(name, (REASON_ALWAYS, "required by impact expansion"))
            decisions.append(JobDecision(name, DECISION_RUN, code, text))
            continue
        if name not in legal and name not in jobs_for_flow(flow, PROMOTE_REBUILD):
            decisions.append(
                JobDecision(name, DECISION_SKIP, REASON_NOT_ON_FLOW, f"{name} is not on this flow")
            )
            continue
        if name in cache_hits:
            artifact = cache_hits[name]
            decisions.append(
                JobDecision(
                    name,
                    DECISION_SKIP,
                    REASON_CACHE_HIT,
                    f"{artifact} input identity is unchanged and a verified cache exists",
                )
            )
            continue
        decisions.append(JobDecision(name, DECISION_SKIP, _skip_code(name), _skip_text(name, flow)))
    return decisions


def _skip_code(name: str) -> str:
    if name in {"ingest", "prepare", "score", "evaluate", "package", "validate", "test"}:
        return REASON_UNCHANGED
    return REASON_NO_IMPACT


def _skip_text(name: str, flow: str) -> str:
    if name == "validate":
        return "no schema/config/manifest impact that requires validate"
    if name == "test":
        return "no application-code, test, or dependency change that requires test"
    if name == "publish":
        return "no new bundle to record on development"
    if name == "promote":
        return f"promote is not on flow {flow}"
    if name == "package":
        return "bundle payload is unchanged"
    return f"{name} output is not invalidated and is not required by a running consumer"
