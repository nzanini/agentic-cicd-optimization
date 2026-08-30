"""Deterministic B2 verifier. Independent of the LLM. Never fail-open."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentic_cicd.b0.graph import FLOW_ILLEGAL, JOBS, PROMOTE_REUSE, jobs_for_flow
from agentic_cicd.b1.cache import has_valid
from agentic_cicd.b1.classify import CONSERVATIVE_COMPONENTS, classify_path, classify_paths
from agentic_cicd.b1.impact import CONSUMES, PRODUCER
from agentic_cicd.b1.planner import DECISION_RUN, DECISION_SKIP, JobDecision, Plan, plan_jobs
from agentic_cicd.b2.schema import CACHEABLE_ARTIFACTS
from agentic_cicd.b2.tools import resolve_readable

MIN_CONFIDENCE_DEFAULT = 0.7

REPRESENTATIVE_PATHS: dict[str, str] = {
    "documentation": "README.md",
    "tests": "tests/test_package_import.py",
    "pipeline_metadata": "configs/pipeline.json",
    "scoring_overlay": "configs/scoring_weights.json",
    "catalog": "fixtures/catalog.json",
    "personas": "fixtures/personas.json",
    "frozen_model": "fixtures/model/ranker.json",
    "ingest_code": "src/agentic_cicd/ranker/ingest.py",
    "prepare_code": "src/agentic_cicd/ranker/prepare.py",
    "score_code": "src/agentic_cicd/ranker/score.py",
    "evaluate_code": "src/agentic_cicd/ranker/evaluate.py",
    "package_code": "src/agentic_cicd/ranker/package.py",
}

COMPONENT_NEEDLES: dict[str, tuple[str, ...]] = {
    "ingest_code": ("agentic_cicd.ranker.ingest", "ranker/ingest.py", "ranker.ingest"),
    "prepare_code": ("agentic_cicd.ranker.prepare", "ranker/prepare.py", "ranker.prepare"),
    "score_code": ("agentic_cicd.ranker.score", "ranker/score.py", "ranker.score"),
    "evaluate_code": ("agentic_cicd.ranker.evaluate", "ranker/evaluate.py", "ranker.evaluate"),
    "package_code": ("agentic_cicd.ranker.package", "ranker/package.py", "ranker.identity"),
    "scoring_overlay": ("scoring_weights.json",),
    "catalog": ("catalog.json",),
    "personas": ("personas.json",),
    "frozen_model": ("model/ranker.json", "ranker.json"),
    "pipeline_metadata": ("pipeline.json",),
}

PRODUCER_ARTIFACT: dict[str, str] = {job: artifact for artifact, job in PRODUCER.items()}


@dataclass
class NovelEvent:
    job: str
    reason: str


@dataclass
class VerifierResult:
    plan: Plan
    used_proposal: bool
    fallback_reason: str | None
    accepted_novel: list[NovelEvent] = field(default_factory=list)
    rejected_novel: list[NovelEvent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "used_proposal": self.used_proposal,
            "fallback_reason": self.fallback_reason,
            "accepted_novel": [event.__dict__ for event in self.accepted_novel],
            "rejected_novel": [event.__dict__ for event in self.rejected_novel],
            "notes": list(self.notes),
            "final_run": list(self.plan.run),
        }


def verify_proposal(
    *,
    b1: Plan,
    proposal: dict[str, Any] | None,
    fallback_reason: str | None,
    source: str,
    target: str,
    changed_paths: list[str] | None,
    fixtures_dir: Path,
    cache_dir: Path | None,
    registry_dir: Path | None,
    workspace: Path | None,
    repo: Path | None,
    min_confidence: float = MIN_CONFIDENCE_DEFAULT,
) -> VerifierResult:
    if proposal is None:
        return VerifierResult(b1, False, fallback_reason or "missing_proposal")
    if proposal.get("uncertain") is True:
        return _reject_all_narrowing(b1, proposal, "uncertain_proposal")
    localized = _localized_plan(
        b1=b1,
        proposal=proposal,
        source=source,
        target=target,
        changed_paths=changed_paths,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
        workspace=workspace,
        repo=repo,
    )
    b1_by_job = {item.job_name: item for item in b1.decisions}
    proposed = {item["job"]: item for item in proposal["jobs"]}
    final_run: set[str] = set()
    reasons: dict[str, tuple[str, str]] = {}
    accepted: list[NovelEvent] = []
    rejected: list[NovelEvent] = []
    notes: list[str] = []

    for name in JOBS:
        b1_item = b1_by_job[name]
        agent_item = proposed[name]
        agent_decision = agent_item["decision"]
        if agent_decision == DECISION_RUN:
            if _illegal_extra_run(b1.flow, name):
                reasons[name] = (b1_item.reason_code, b1_item.reason)
                notes.append(f"{name}: extra RUN rejected on illegal flow")
                continue
            final_run.add(name)
            reasons[name] = (
                agent_item.get("reason_code") or "agent_run",
                agent_item.get("reason") or "agent requested RUN",
            )
            continue
        if b1_item.decision == DECISION_SKIP:
            reasons[name] = (b1_item.reason_code, b1_item.reason)
            continue
        ok, why = _narrowing_ok(
            job=name,
            agent_item=agent_item,
            b1=b1,
            localized=localized,
            fixtures_dir=fixtures_dir,
            cache_dir=cache_dir,
            min_confidence=min_confidence,
        )
        if ok:
            reasons[name] = (
                agent_item.get("reason_code") or "agent_skip_verified",
                agent_item.get("reason") or why,
            )
            accepted.append(NovelEvent(name, why))
        else:
            final_run.add(name)
            reasons[name] = (b1_item.reason_code, b1_item.reason)
            rejected.append(NovelEvent(name, why))

    final_run = _enforce_producers(
        final_run, localized or b1, fixtures_dir, cache_dir, rejected, notes
    )
    if "branch_guard" not in final_run:
        final_run.add("branch_guard")
        rejected.append(NovelEvent("branch_guard", "branch_guard cannot be skipped"))

    ordered = _ordered(b1.flow, b1.promote_mode, final_run)
    decisions = _decisions_from(b1, ordered, reasons)
    plan = Plan(
        flow=b1.flow,
        promote_mode=b1.promote_mode,
        run=ordered,
        decisions=decisions,
        components=b1.components if localized is None else localized.components,
        invalidated=b1.invalidated if localized is None else localized.invalidated,
    )
    return VerifierResult(
        plan=plan,
        used_proposal=True,
        fallback_reason=None,
        accepted_novel=accepted,
        rejected_novel=rejected,
        notes=notes,
    )


def _reject_all_narrowing(b1: Plan, proposal: dict[str, Any], reason: str) -> VerifierResult:
    b1_run = set(b1.run)
    rejected = [
        NovelEvent(item["job"], reason)
        for item in proposal["jobs"]
        if item["decision"] == DECISION_SKIP and item["job"] in b1_run
    ]
    return VerifierResult(b1, True, reason, rejected_novel=rejected, notes=[reason])


def _illegal_extra_run(flow: str, job: str) -> bool:
    return flow == FLOW_ILLEGAL and job in {"publish", "promote"}


def _localized_plan(
    *,
    b1: Plan,
    proposal: dict[str, Any],
    source: str,
    target: str,
    changed_paths: list[str] | None,
    fixtures_dir: Path,
    cache_dir: Path | None,
    registry_dir: Path | None,
    workspace: Path | None,
    repo: Path | None,
) -> Plan | None:
    if changed_paths is None:
        return None
    rewritten: list[str] = []
    roots = [path for path in (workspace, repo) if path is not None and path.is_dir()]
    complete = True
    for path in changed_paths:
        if classify_path(path) not in CONSERVATIVE_COMPONENTS:
            rewritten.append(path)
            continue
        edge = _matching_edge(path, proposal.get("discovered_edges") or [])
        if edge is None or not _edge_checkable(edge, roots):
            complete = False
            rewritten.append(path)
            continue
        rewritten.append(REPRESENTATIVE_PATHS[edge["to_component"]])
    if not complete:
        return None
    if classify_paths(rewritten) & CONSERVATIVE_COMPONENTS:
        return None
    localized = plan_jobs(
        source=source,
        target=target,
        changed_paths=rewritten,
        fixtures_dir=fixtures_dir,
        cache_dir=cache_dir,
        registry_dir=registry_dir,
    )
    if localized.flow == FLOW_ILLEGAL:
        return None
    return localized


def _matching_edge(path: str, edges: list[dict[str, Any]]) -> dict[str, Any] | None:
    for edge in edges:
        if edge.get("from_path") == path and edge.get("to_component") in REPRESENTATIVE_PATHS:
            return edge
    return None


def _edge_checkable(edge: dict[str, Any], roots: list[Path]) -> bool:
    needles = COMPONENT_NEEDLES.get(edge["to_component"], ())
    if not needles:
        return False
    try:
        text = resolve_readable(edge["from_path"], roots).read_text(
            encoding="utf-8", errors="replace"
        )
    except (OSError, ValueError):
        return False
    return any(needle in text for needle in needles)


def _narrowing_ok(
    *,
    job: str,
    agent_item: dict[str, Any],
    b1: Plan,
    localized: Plan | None,
    fixtures_dir: Path,
    cache_dir: Path | None,
    min_confidence: float,
) -> tuple[bool, str]:
    if job == "branch_guard":
        return False, "never skip branch_guard"
    if float(agent_item.get("confidence") or 0) < min_confidence:
        return False, "confidence below min_confidence"
    if not agent_item.get("evidence"):
        return False, "narrowing SKIP requires evidence"
    if localized is not None:
        localized_run = set(localized.run)
        if job not in localized_run:
            return True, "localized B1 would skip this job"
        return False, "localized B1 still requires this job"
    artifact = PRODUCER_ARTIFACT.get(job)
    reused = list(agent_item.get("artifacts_reused") or [])
    if artifact and artifact in reused and artifact in CACHEABLE_ARTIFACTS:
        if artifact in b1.invalidated:
            return False, f"{artifact} is invalidated; cache reuse rejected"
        if has_valid(cache_dir, artifact, fixtures_dir):
            return True, f"valid cache identity for {artifact}"
        return False, f"cache for {artifact} missing or stale"
    return False, "no mechanical evidence (inert-unknown is not accepted)"


def _enforce_producers(
    run: set[str],
    impact: Plan,
    fixtures_dir: Path,
    cache_dir: Path | None,
    rejected: list[NovelEvent],
    notes: list[str],
) -> set[str]:
    changed = True
    while changed:
        changed = False
        for job in list(run):
            needs = CONSUMES.get(job, ())
            if job == "promote" and impact.promote_mode == PROMOTE_REUSE:
                needs = ()
            for artifact in needs:
                producer = PRODUCER[artifact]
                if producer in run:
                    continue
                invalidated = artifact in impact.invalidated
                cached = has_valid(cache_dir, artifact, fixtures_dir)
                if not invalidated and cached:
                    continue
                run.add(producer)
                rejected.append(
                    NovelEvent(producer, f"{job} requires {artifact}; producer forced RUN")
                )
                notes.append(f"producer/consumer: {producer} restored for {job}")
                changed = True
    return run


def _ordered(flow: str, mode: str | None, run: set[str]) -> list[str]:
    if mode == PROMOTE_REUSE:
        legal = ["branch_guard", "promote"]
    else:
        legal = jobs_for_flow(flow, mode)
    return [name for name in legal if name in run]


def _decisions_from(
    b1: Plan, run: list[str], reasons: dict[str, tuple[str, str]]
) -> list[JobDecision]:
    running = set(run)
    original = {item.job_name: item for item in b1.decisions}
    decisions: list[JobDecision] = []
    for name in sorted(JOBS, key=lambda item: (JOBS[item].order, item)):
        if name in running:
            code, text = reasons.get(name, (original[name].reason_code, original[name].reason))
            decisions.append(JobDecision(name, DECISION_RUN, code, text))
        else:
            prior = original[name]
            code, text = reasons.get(name, (prior.reason_code, prior.reason))
            decisions.append(JobDecision(name, DECISION_SKIP, code, text))
    return decisions
