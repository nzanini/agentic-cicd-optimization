"""Off-suite live experiment matching conceptual S16. Does not edit S01–S14."""

from __future__ import annotations

import os
from pathlib import Path

from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b2.runner import record_from_result, run_b2
from agentic_cicd.b2.settings import load_settings
from agentic_cicd.ranker.io_util import write_json

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    dest = REPO / os.environ.get("B2_S16_OUT", "outputs/e006-s16-like")
    workspace = dest / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    script = workspace / "scripts" / "tune_weights.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("import agentic_cicd.ranker.score\n", encoding="utf-8")
    fixtures = REPO / "fixtures"
    cache = dest / "cache"
    warm_cache(fixtures, cache)
    result = run_b2(
        source="feature",
        target="development",
        fixtures_dir=fixtures,
        work_dir=dest / "run",
        registry_dir=dest / "registry",
        changed_paths=["scripts/tune_weights.py"],
        cache_dir=cache,
        workspace_dir=workspace,
        repo_dir=REPO,
        settings=load_settings(),
    )
    record = record_from_result(result)
    summary = {
        "status": result.status,
        "executed": [job.job_name for job in result.jobs if job.status == "executed"],
        "simulated_cost": result.simulated_cost_total,
        "agent_invoked": record.get("agent_invoked"),
        "fallback_reason": record.get("fallback_reason"),
        "agent_error": record.get("agent_error"),
        "novel_accept": record.get("novel_accept"),
        "novel_reject": record.get("novel_reject"),
        "latency_ms": record.get("latency_ms"),
        "model": record.get("model"),
        "provider": record.get("provider"),
        "api_cost_usd": record.get("api_cost_usd"),
    }
    write_json(dest / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
