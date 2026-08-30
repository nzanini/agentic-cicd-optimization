"""Decide whether B2 should invoke the agent. Machine-readable; no LLM."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_cicd.b0.graph import FLOW_ILLEGAL, JOBS
from agentic_cicd.b1.classify import CONSERVATIVE_COMPONENTS, classify_path
from agentic_cicd.b1.planner import REASON_CONSERVATIVE, Plan
from agentic_cicd.b2.provider import probe_runtime
from agentic_cicd.b2.settings import B2Settings


@dataclass(frozen=True)
class InvocationDecision:
    invoke: bool
    reason: str
    reason_code: str
    expected_save: int
    conservative: bool
    inspectable: bool


def expected_max_save(plan: Plan) -> int:
    """Upper bound: drop every B1 RUN except branch_guard."""
    total = 0
    for name in plan.run:
        if name == "branch_guard":
            continue
        spec = JOBS.get(name)
        if spec is not None:
            total += spec.simulated_cost
    return total


def residue_inspectable(
    changed_paths: list[str] | None,
    workspace: Path | None,
    repo: Path | None = None,
) -> bool:
    roots = [path for path in (workspace, repo) if path is not None and path.is_dir()]
    if not roots:
        return False
    if changed_paths is None:
        return True
    conservative_paths = [path for path in changed_paths if _looks_unmapped_name(path)]
    if not conservative_paths:
        return True
    for path in conservative_paths:
        if any((root / path).exists() for root in roots):
            return True
    return False


def _looks_unmapped_name(path: str) -> bool:
    return classify_path(path) in CONSERVATIVE_COMPONENTS


def decide_invocation(
    plan: Plan,
    *,
    changed_paths: list[str] | None,
    settings: B2Settings,
    workspace: Path | None,
    repo: Path | None = None,
) -> InvocationDecision:
    if plan.flow == FLOW_ILLEGAL:
        return InvocationDecision(
            False, "illegal flow; B1 fail-closed is final", "illegal_flow", 0, False, False
        )
    conservative = _is_conservative(plan, changed_paths)
    save = expected_max_save(plan) if conservative else 0
    inspectable = residue_inspectable(changed_paths, workspace, repo)
    if not conservative:
        return InvocationDecision(
            False,
            "B1 has no conservative residue; agent would only reproduce rules",
            "b1_sufficient",
            0,
            False,
            inspectable,
        )
    if settings.disabled:
        return InvocationDecision(False, "B2_DISABLED is set", "disabled", save, True, inspectable)
    if not settings.available:
        return InvocationDecision(
            False,
            "no local runtime and no API key; remain on B1",
            "offline",
            save,
            True,
            inspectable,
        )
    if settings.local and not probe_runtime(settings):
        return InvocationDecision(
            False,
            "local runtime unavailable; remain on B1",
            "offline",
            save,
            True,
            inspectable,
        )
    if not inspectable:
        return InvocationDecision(
            False,
            "conservative residue is not inspectable; keep B1",
            "not_inspectable",
            save,
            True,
            False,
        )
    if save < settings.min_save:
        return InvocationDecision(
            False,
            f"expected max save {save} < min_save {settings.min_save}",
            "not_worth_it",
            save,
            True,
            inspectable,
        )
    return InvocationDecision(
        True,
        "B1 conservative over-run with inspectable residue; refine if evidence exists",
        "conservative_residue",
        save,
        True,
        True,
    )


def _is_conservative(plan: Plan, changed_paths: list[str] | None) -> bool:
    if changed_paths is None:
        return True
    if any(component in CONSERVATIVE_COMPONENTS for component in plan.components):
        return True
    return any(item.reason_code == REASON_CONSERVATIVE for item in plan.decisions)
