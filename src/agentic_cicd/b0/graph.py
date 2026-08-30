"""B0 job graph: always run every job that is legal on the flow.

This is not an optimizer. There is no path filter and no skip logic.
Clean vs dirty development→main is an explicit promote_mode input, not
inferred from files.
"""

from __future__ import annotations

from dataclasses import dataclass

FLOW_FEATURE_DEV = "feature_dev"
FLOW_DEV_MAIN = "dev_main"
FLOW_ILLEGAL = "illegal"

PROMOTE_REUSE = "reuse"
PROMOTE_REBUILD = "rebuild"
PROMOTE_MODES = (PROMOTE_REUSE, PROMOTE_REBUILD)


@dataclass(frozen=True)
class JobSpec:
    name: str
    depends_on: tuple[str, ...]
    simulated_cost: int
    order: int
    flows: tuple[str, ...]


JOBS: dict[str, JobSpec] = {
    "branch_guard": JobSpec(
        "branch_guard", (), 1, 0, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN, FLOW_ILLEGAL)
    ),
    "validate": JobSpec("validate", ("branch_guard",), 1, 1, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "test": JobSpec("test", ("validate",), 3, 2, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "ingest": JobSpec("ingest", ("validate",), 5, 3, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "prepare": JobSpec("prepare", ("ingest",), 4, 4, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "score": JobSpec("score", ("prepare",), 10, 5, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "evaluate": JobSpec("evaluate", ("score",), 3, 6, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "package": JobSpec("package", ("evaluate",), 2, 7, (FLOW_FEATURE_DEV, FLOW_DEV_MAIN)),
    "publish": JobSpec("publish", ("package", "test"), 2, 8, (FLOW_FEATURE_DEV,)),
    "promote": JobSpec("promote", ("branch_guard", "package", "test"), 2, 8, (FLOW_DEV_MAIN,)),
}


def classify_flow(source: str, target: str) -> str:
    if _is_feature_or_custom(source) and target == "development":
        return FLOW_FEATURE_DEV
    if source == "development" and target == "main":
        return FLOW_DEV_MAIN
    return FLOW_ILLEGAL


def _is_feature_or_custom(source: str) -> bool:
    return source in {"feature", "custom"} or source.startswith(("feature/", "custom/"))


def normalize_promote_mode(promote_mode: str | None) -> str:
    if promote_mode is None:
        return PROMOTE_REBUILD
    if promote_mode not in PROMOTE_MODES:
        msg = f"unknown promote_mode {promote_mode!r}; expected {PROMOTE_MODES}"
        raise ValueError(msg)
    return promote_mode


def jobs_for_flow(flow: str, promote_mode: str | None = None) -> list[str]:
    selected = [spec for spec in JOBS.values() if flow in spec.flows]
    names = [spec.name for spec in selected]
    mode = normalize_promote_mode(promote_mode)
    if flow == FLOW_DEV_MAIN and mode == PROMOTE_REUSE:
        names = ["branch_guard", "promote"]
    return execution_order(names)


def execution_order(names: list[str]) -> list[str]:
    remaining = set(names)
    done: list[str] = []
    while remaining:
        ready = [
            name
            for name in remaining
            if all(dep in done or dep not in remaining for dep in JOBS[name].depends_on)
        ]
        if not ready:
            msg = f"cycle or missing dependency among {sorted(remaining)}"
            raise RuntimeError(msg)
        ready.sort(key=lambda name: (JOBS[name].order, name))
        nxt = ready[0]
        remaining.remove(nxt)
        done.append(nxt)
    return done
