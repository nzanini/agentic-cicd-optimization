"""Off-suite live checks for proposal validity. Does not edit S01–S14."""

from __future__ import annotations

import os
from pathlib import Path

from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b2.runner import record_from_result, run_b2
from agentic_cicd.b2.settings import load_settings
from agentic_cicd.ranker.io_util import write_json

REPO = Path(__file__).resolve().parents[1]


def _run(name: str, relative: str, source: str) -> dict:
    root = REPO / os.environ.get("B2_VALIDITY_OUT", "outputs/e008-proposal-validity")
    dest = root / name
    workspace = dest / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    path = workspace / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    fixtures = REPO / "fixtures"
    cache = dest / "cache"
    warm_cache(fixtures, cache)
    result = run_b2(
        source="feature",
        target="development",
        fixtures_dir=fixtures,
        work_dir=dest / "run",
        registry_dir=dest / "registry",
        changed_paths=[relative],
        cache_dir=cache,
        workspace_dir=workspace,
        repo_dir=REPO,
        settings=load_settings(),
    )
    record = record_from_result(result)
    return {
        "case": name,
        "status": result.status,
        "executed": [job.job_name for job in result.jobs if job.status == "executed"],
        "simulated_cost": result.simulated_cost_total,
        "agent_invoked": record.get("agent_invoked"),
        "fallback_reason": record.get("fallback_reason"),
        "agent_error": record.get("agent_error"),
        "repair_attempted": record.get("repair_attempted"),
        "enable_tools": record.get("enable_tools"),
        "prompt_id": record.get("prompt_id"),
        "proposal_valid": record.get("proposal") is not None,
        "novel_accept": record.get("novel_accept"),
        "novel_reject": record.get("novel_reject"),
        "latency_ms": record.get("latency_ms"),
        "tool_trace": record.get("tool_trace"),
        "model": record.get("model"),
        "provider": record.get("provider"),
        "api_cost_usd": record.get("api_cost_usd"),
        "raw_response_preview": record.get("raw_response_preview"),
    }


def main() -> None:
    catalog = {
        "s16_like": ("scripts/tune_weights.py", "import agentic_cicd.ranker.score\n"),
        "s14_like": ("unknown/orphan.dat", "x\n"),
    }
    wanted = os.environ.get("B2_VALIDITY_CASE", "s16_like,s14_like")
    rows = []
    for name in [item.strip() for item in wanted.split(",") if item.strip()]:
        relative, source = catalog[name]
        rows.append(_run(name, relative, source))
    dest = REPO / os.environ.get("B2_VALIDITY_OUT", "outputs/e008-proposal-validity")
    write_json(dest / "summary.json", {"cases": rows})
    print({"cases": rows})


if __name__ == "__main__":
    main()
