"""Local Catalog Ranker, B0, B1, and B2 (agent proposes; verifier decides)."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentic_cicd.b0 import run_b0
from agentic_cicd.b1 import run_b1
from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b2 import run_b2
from agentic_cicd.benchmark import run_benchmark
from agentic_cicd.ranker.pipeline import run_workload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Catalog Ranker, B0 baseline, B1 optimizer, and experimental B2 agent wrapper."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    rank = sub.add_parser("rank", help="run the Catalog Ranker workload only")
    rank.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    rank.add_argument("--output", type=Path, default=Path("outputs/latest"))

    b0 = sub.add_parser("b0", help="run the unoptimized CI/CD baseline")
    b0.add_argument("--source", required=True, help="source ref, e.g. feature or development")
    b0.add_argument("--target", required=True, help="target ref, e.g. development or main")
    b0.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    b0.add_argument("--output", type=Path, default=Path("outputs/b0"))
    b0.add_argument(
        "--registry",
        type=Path,
        default=Path("outputs/registry"),
        help="local environment pointers (development.json / production.json)",
    )
    b0.add_argument(
        "--promote-mode",
        choices=("reuse", "rebuild"),
        default="rebuild",
        help=(
            "development→main only: reuse the validated development artifact, "
            "or rebuild and promote the new artifact. Default rebuild. "
            "Not change detection."
        ),
    )
    b1 = sub.add_parser("b1", help="run the deterministic CI/CD optimizer")
    b1.add_argument("--source", required=True)
    b1.add_argument("--target", required=True)
    b1.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    b1.add_argument("--output", type=Path, default=Path("outputs/b1"))
    b1.add_argument("--registry", type=Path, default=Path("outputs/registry"))
    b1.add_argument(
        "--changed",
        nargs="*",
        default=None,
        help="changed paths. Omit to treat the change set as unknown (fail closed).",
    )
    b1.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="directory of identity-checked intermediates; omitted means no cache",
    )
    b1.add_argument(
        "--warm-cache",
        action="store_true",
        help="build last-known-good intermediates from --fixtures into --cache first",
    )
    b2 = sub.add_parser("b2", help="run B1 first, then an optional agent + verifier")
    b2.add_argument("--source", required=True)
    b2.add_argument("--target", required=True)
    b2.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    b2.add_argument("--output", type=Path, default=Path("outputs/b2"))
    b2.add_argument("--registry", type=Path, default=Path("outputs/registry"))
    b2.add_argument(
        "--changed",
        nargs="*",
        default=None,
        help="changed paths. Omit to treat the change set as unknown (fail closed).",
    )
    b2.add_argument("--cache", type=Path, default=None)
    b2.add_argument("--workspace", type=Path, default=None)
    b2.add_argument("--repo", type=Path, default=None)
    b2.add_argument(
        "--warm-cache",
        action="store_true",
        help="build last-known-good intermediates from --fixtures into --cache first",
    )
    bench = sub.add_parser("benchmark", help="run a scenario suite against B0, B1, B2, or a ladder")
    bench.add_argument("--output", type=Path, default=Path("outputs/benchmark"))
    bench.add_argument(
        "--scenarios",
        type=Path,
        default=None,
        help="scenario JSON (default: benchmark/scenarios.json = S01–S14)",
    )
    bench.add_argument(
        "--system",
        choices=("baseline", "optimized", "compare", "agentic", "ladder"),
        default="baseline",
        help=(
            "baseline=B0, optimized=B1, compare=B0+B1, agentic=B2, ladder=B0+B1+B2. "
            "compare stays B0 vs B1."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "rank":
        result = run_workload(args.fixtures.resolve(), args.output.resolve())
        print(f"artifact_id={result.artifact_id}")
        print(f"output_dir={result.output_dir}")
        return 0
    if args.command == "b0":
        result = run_b0(
            source=args.source,
            target=args.target,
            fixtures_dir=args.fixtures.resolve(),
            work_dir=args.output.resolve(),
            registry_dir=args.registry.resolve(),
            promote_mode=args.promote_mode,
        )
        print(f"status={result.status}")
        print(f"flow={result.flow}")
        print(f"artifact_id={result.artifact_id}")
        print(f"simulated_cost_total={result.simulated_cost_total}")
        print(f"output_dir={result.work_dir}")
        return 0 if result.status == "succeeded" else 1
    if args.command == "b1":
        cache = args.cache.resolve() if args.cache is not None else None
        if args.warm_cache:
            if cache is None:
                raise SystemExit("--warm-cache requires --cache")
            warm_cache(args.fixtures.resolve(), cache)
        result = run_b1(
            source=args.source,
            target=args.target,
            fixtures_dir=args.fixtures.resolve(),
            work_dir=args.output.resolve(),
            registry_dir=args.registry.resolve(),
            changed_paths=args.changed,
            cache_dir=cache,
        )
        print(f"status={result.status}")
        print(f"flow={result.flow}")
        print(f"artifact_id={result.artifact_id}")
        print(f"simulated_cost_total={result.simulated_cost_total}")
        print(f"output_dir={result.work_dir}")
        return 0 if result.status == "succeeded" else 1
    if args.command == "b2":
        cache = args.cache.resolve() if args.cache is not None else None
        if args.warm_cache:
            if cache is None:
                raise SystemExit("--warm-cache requires --cache")
            warm_cache(args.fixtures.resolve(), cache)
        result = run_b2(
            source=args.source,
            target=args.target,
            fixtures_dir=args.fixtures.resolve(),
            work_dir=args.output.resolve(),
            registry_dir=args.registry.resolve(),
            changed_paths=args.changed,
            cache_dir=cache,
            workspace_dir=args.workspace.resolve() if args.workspace else None,
            repo_dir=args.repo.resolve() if args.repo else None,
        )
        print(f"status={result.status}")
        print(f"flow={result.flow}")
        print(f"artifact_id={result.artifact_id}")
        print(f"simulated_cost_total={result.simulated_cost_total}")
        print(f"output_dir={result.work_dir}")
        return 0 if result.status == "succeeded" else 1
    if args.command == "benchmark":
        report = run_benchmark(
            output_dir=args.output.resolve(),
            system=args.system,
            scenarios_path=args.scenarios.resolve() if args.scenarios else None,
        )
        payload = report.payload
        print(f"system={payload['system']}")
        print(f"scenarios={payload['scenario_count']}")
        if payload["system"] == "compare":
            comparison = payload["comparison"]
            print(f"baseline_cost={comparison['simulated_cost_baseline']}")
            print(f"optimized_cost={comparison['simulated_cost_optimized']}")
            print(f"cost_reduction_pct={comparison['cost_reduction_pct']}")
            print(f"false_skip_count={comparison['false_skip_count_optimized']}")
            print(f"optimization_win_eligible={comparison['optimization_win_eligible']}")
        elif payload["system"] == "ladder":
            comparison = payload["comparison"]
            print(f"baseline_cost={comparison['simulated_cost_baseline']}")
            print(f"optimized_cost={comparison['simulated_cost_optimized']}")
            print(f"agentic_cost={comparison['simulated_cost_agentic']}")
            print(f"delta_vs_b1={comparison['delta_vs_b1']}")
            print(f"false_skip_count={comparison['false_skip_count_agentic']}")
            print(f"agent_invocation_count={comparison['agent_invocation_count']}")
            print(f"novel_accept_count={comparison['novel_accept_count']}")
            print(f"novel_reject_count={comparison['novel_reject_count']}")
            print(f"optimization_win_eligible={comparison['optimization_win_eligible']}")
        else:
            totals = payload["totals"]
            print(f"simulated_cost={totals['simulated_cost']}")
            print(f"correctness_pass_rate={totals['correctness_pass_rate']}")
            print(f"false_skip_count={totals['false_skip_count']}")
            print(
                f"optimization_win_eligible={payload['safety_gate']['optimization_win_eligible']}"
            )
        print(f"output_dir={report.output_dir}")
        return 0
    return 2
