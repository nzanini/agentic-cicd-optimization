"""Model-facing B2 prompts. The verifier is not defined here."""

from __future__ import annotations

import json
from typing import Any

from agentic_cicd.b2.schema import KNOWN_JOBS_ORDER

PROMPT_ID = "b2-proposal-v3"

COMPACT_TEMPLATE = {
    "schema_version": 1,
    "kind": "b2_proposal",
    "uncertain": False,
    "copy_b1": True,
    "notes": "",
    "discovered_edges": [],
    "jobs": [],
}

SYSTEM_PROMPT = (
    """You refine a conservative B1 CI plan. You propose; you do not decide.

Return exactly one JSON object. No prose.

Required fields:
- schema_version: integer 1
- kind: b2_proposal
- uncertain: boolean
- copy_b1: true fills omitted jobs as RUN
- discovered_edges: array
- jobs: only jobs you change; empty is allowed when copy_b1 is true

Known jobs: """
    + ", ".join(KNOWN_JOBS_ORDER)
    + """

Meanings:
- decision: RUN or SKIP. Proposal only; the verifier decides.
- evidence: checkable import/read/cache facts. Needed to SKIP a B1 RUN.
- confidence: [0,1]. Not evidence.
- dependencies_considered: job names. Not evidence.
- uncertain: true keeps B1 RUNs.
- discovered_edges: unclassified path -> known component with checkable evidence.

Rules:
- Do not call tools unless the preview is missing.
- Never skip branch_guard.
- Extra RUN is allowed.
- No search-hit absence is not proof a file is inert.
- No scenario IDs or required_jobs.
"""
)


def format_user_prompt(context: dict[str, Any]) -> str:
    """Compact, model-facing view of the Phase 2.3 context."""
    template = json.dumps(COMPACT_TEMPLATE, separators=(",", ":"))
    b1 = context.get("b1_plan") or {}
    payload = {
        "source": context.get("source"),
        "target": context.get("target"),
        "changed_paths": context.get("changed_paths"),
        "b1_run": b1.get("run"),
        "b1_components": b1.get("components"),
        "unclassified_previews": context.get("unclassified_previews") or [],
    }
    return (
        "Facts:\n"
        f"{json.dumps(payload, separators=(',', ':'))}\n"
        "Return one JSON object. schema_version must be the integer 1. "
        "copy_b1=true. List a job only to change it. "
        "SKIP needs checkable evidence in discovered_edges or job evidence.\n"
        f"{template}"
    )


def repair_user_prompt(error: str) -> str:
    template = json.dumps(COMPACT_TEMPLATE, separators=(",", ":"))
    return (
        f"Invalid proposal: {error}\n"
        "Return only one corrected JSON object. "
        "schema_version must be the integer 1. kind=b2_proposal. copy_b1=true.\n"
        f"{template}"
    )
