"""B2 agentic optimizer. Agent proposes; verifier decides. No skip without B1+verifier."""

from agentic_cicd.b2.runner import record_from_result, run_b2

__all__ = ["record_from_result", "run_b2"]
