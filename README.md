# Agentic CI/CD Optimization

A [micro1 Agentic Workflows Hackathon](https://micro1.ai) project.

**CI/CD often re-runs jobs that a change cannot affect.** This repository builds a local, reproducible pipeline simulator and asks what actually reduces that waste **without skipping required work**.

**Final presented solution: B1** (deterministic impact-graph optimizer).  
**Headline result (E-003):** suite simulated cost **375 → 220** (−41.3%) on S01–S14, correctness **14/14**, false skips **0**.

B2 (a runtime LLM layer) was investigated and **rejected as the production optimizer** under a $0 constraint: it never beat B1 and added tens to hundreds of seconds of latency. Cursor was the **coding agent** used to design, implement, and evaluate the work.

---

## Problem and user

**User:** a software engineer or CI/platform owner who over-runs pipelines because skipping the wrong job is worse than extra compute.

**Objective:** minimize unnecessary pipeline work **while preserving correctness**. A required job must never be skipped. Uncertainty must **run**, not skip.

**Workload being optimized:** Catalog Ranker — a local **batch** job that ranks a vendored movie catalog for synthetic personas and writes a content-addressed artifact. It is **not** a production ML training pipeline. The model is frozen; nothing is trained. The interesting question is which CI jobs that batch graph still needs after a change.

Simulated promotion path (benchmark model only): `feature → development → main`. Direct `feature → main` is illegal. Those names are **CI flow labels inside the simulator**, not Git branches a judge must create.

---

## What the system is

Four different things. Do not collapse them.

| Layer | Role | Status |
| --- | --- | --- |
| **Catalog Ranker** | The batch workload being scheduled (fixtures → prepare → score → evaluate → package). No training. | Implemented (`python -m agentic_cicd rank`) |
| **B0** | Unoptimized **execution**: run every job that is legal on the flow | Measured (E-002) |
| **B1** | Deterministic **optimization**: path → component → invalidated artifacts → required jobs, plus identity-checked cache | **Selected final solution** (E-003) |
| **B2** | Experimental **agentic optimizer**: optional agent proposes a tighter plan; a **deterministic verifier** is the only skip authority | Implemented, **rejected as the product optimizer** (E-010, E-011) |
| **Cursor** | Coding / reasoning agent used to build the repo (this chat: Cursor Grok 4.6, Agent mode) | Development evidence |
| **Ollama `qwen2.5:3b` / `qwen3:4b-instruct`** | Experimental **runtime** B2 models. Not Cursor. $0 local inference | No `T` win vs B1 |

Do not collapse Cursor and B2. Paying for Cursor does **not** drive the CI optimizer.

---

## Catalog Ranker (batch workload)

Catalog Ranker consumes committed fixtures and produces ranked lists. A judge can open JSON and see “user U2 → top 5 titles.”

**Fixtures (in git):** `fixtures/catalog.json` (16 movies), `fixtures/personas.json` (4 synthetic personas), `fixtures/model/ranker.json` (frozen `weighted_genre_dot` weights). Optional overlay: `configs/scoring_weights.json` (changes scores; S12). `configs/pipeline.json` is pipeline metadata and is **not** read by the ranker (S08).

**What one batch run does:**

1. **Ingest** the catalog and persona fixtures and write a dataset manifest.
2. **Prepare** deterministic feature vectors from the catalog.
3. **Score / rank** every persona against the catalog with the **frozen** weights. No fit, no backprop, no GPU.
4. **Evaluate** those predictions (coverage, score summary, checksum).
5. **Package** a content-addressed artifact: `predictions.json`, `metrics.json`, `dataset_manifest.json`, `model_manifest.json`, plus the model object and scoring-code identity.

The final output is ranked/predicted movie lists plus metrics, manifests, and artifact metadata — **not** a newly trained model. Standalone (no CI graph): `python -m agentic_cicd rank --fixtures fixtures --output outputs/latest`.

Details: [`docs/PROBLEM_FRAMING.md`](docs/PROBLEM_FRAMING.md) §2.

---

## What each job does

The CI graph wraps that batch workload with policy and promotion. Conceptual roles (not training stages):

| Job | Conceptual role |
| --- | --- |
| `branch_guard` | Enforce allowed promotions. Always first. Illegal `feature → main` fails here and must not publish or promote. |
| `validate` | Schema / fixture / config sanity. Does not rank or package. |
| `test` | Trust application and test code before writing an environment pointer. |
| `ingest` | Materialize raw catalog + personas from fixtures; write `dataset_manifest.json`. |
| `prepare` | Build deterministic features (`prepared_catalog.json`) from the raw catalog. |
| `score` | Rank the catalog per persona (**dominant cost**). Writes `predictions.json`. |
| `evaluate` | Metrics and a predictions checksum (`metrics.json`). |
| `package` | Content-addressed bundle + `artifact_id`. |
| `publish` | Point **development** at the new bundle (feature→development only). |
| `promote` | Point **production** at a validated artifact id (development→main only). |

```text
branch_guard → validate → test
                         ↘
                           ingest → prepare → score → evaluate → package → publish | promote
```

## How B0 works

B0 always executes the legal job graph. It does not inspect files to skip work. On feature→development that is nine jobs (simulated cost **31**). Clean promote is an explicit `promote_mode=reuse` input, not change detection. Details: [`docs/B0.md`](docs/B0.md).

---

## How B1 improves it

B1 classifies the change set, invalidates only the artifacts that classification implies, and reuses cached intermediates **only** when SHA-256 input identity matches. Unknown, dependency, or orchestrator paths fail closed to the full legal graph.

Skip is allowed only with a checkable reason. Scenario IDs never appear in the optimizer.

```text
changed paths → components → invalidated artifacts → required jobs
                 ↘ cache identity check
```

**Skipping a producer is not the same as needing no input.** Downstream jobs still consume upstream artifacts. If B1 skips `ingest` / `prepare` because those inputs did not change, it must **hydrate** the last-known-good `raw_catalog` / `prepared_catalog` so `score` can run. A skip is legal only when no required consumer needs that output, or a cached object with matching input identity is present. B0 never skips, so it never uses this path.

Example: docs-only (S01) runs `branch_guard` (cost 1). Score-code (S03) reuses ingest/prepare from cache (cost 22). An unclassified path (S14) still costs 31. Scenario map: [`docs/BENCHMARK.md`](docs/BENCHMARK.md).

B1 does not inspect Git. The CLI takes `--changed`; the S01–S14 harness passes `files_changed ∪ apply` (D-028). Automatic working-tree detection was investigated and left out of this submission (D-053): it would not change the measured 375 → 220 result, and Git must not replace that harness signal.

Details: [`docs/B1.md`](docs/B1.md). Contract: [`docs/OPTIMIZATION_CONTRACT.md`](docs/OPTIMIZATION_CONTRACT.md).

---

## Safety principle

**Optimization is valid only when correctness is preserved.**

- **False skip** (a required job did not run) disqualifies any claimed win.
- **UNKNOWN or AMBIGUOUS impact → RUN**, not SKIP.
- Extra executed jobs are **unnecessary**, not a safety failure.
- B2 cannot skip unless the verifier accepts mechanical evidence. Malformed or uncertain proposals fall back to B1.

---

## Main measured result

Frozen suite: S01–S14 in `benchmark/scenarios.json`. Primary metric: sum of executed job **weights** (not wall-clock). Evidence: [E-003](docs/EXPERIMENT_LOG.md).

| | B0 (E-002 / E-003) | B1 (E-003) |
| --- | --- | --- |
| Suite simulated cost `T` | **375** | **220** |
| Reduction | — | **155 (41.3333%)** |
| Correctness | 14/14 | 14/14 |
| False skips | 0 | 0 |
| Unnecessary jobs | 37 | **0** |
| Jobs executed | 110 | 73 |
| Illegal promotion accepted | 0 | 0 |

B2 on the same 14 rows equals B1 (`T` 220, `delta_vs_b1 = 0`; E-004 offline, E-006 live). On the agent-value rows S16–S18, B1 and live B2 both cost **93**; `novel_accept` = 0 (E-010, E-011). That is **not** a B2 win.

---

## Public Git topology (submission repository)

The public GitHub repository uses **`main` only**.

| Concept | What it is | What a judge must do |
| --- | --- | --- |
| Public repo branch `main` | The only required Git branch | Clone it |
| Simulated `feature` / `development` / `main` | CI **flow labels** inside the Catalog Ranker simulator and S01–S14 | Nothing. They are inputs to the local runner |
| Pull requests | Not part of reproduction | Do **not** open a PR |
| `dev` / `feature` Git branches | Not required and not used for submission | Do **not** create them |
| GitHub Actions | Not present; not required | Run locally |

A judge must **not** create branches, open pull requests, merge anything, or reproduce this project’s internal development workflow. Clone `main`, install, run the commands below.

---

## Reproduce from a clean environment

Python **3.11+** (recommended 3.12). Runtime dependencies: none. Dev extras: pytest, ruff.

**Not required:** API keys, Cursor, an Ollama install, GitHub Actions, paid cloud, or any Git branch other than `main`.

```bash
git clone https://github.com/nzanini/agentic-cicd-optimization.git
cd agentic-cicd-optimization
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

If host `python` is missing or is a store stub, the same install and commands work in `python:3.12-slim` with this repository bind-mounted (or copied) into the container. Docker is a convenience, not a requirement. `scripts/judge_repro.sh` repeats the commands below and is optional.

### B0 baseline

```bash
python -m agentic_cicd benchmark --output outputs/benchmark-b0
```

**Expect:** `simulated_cost` **375**, correctness **14/14**, `false_skip_count` **0**. Writes `outputs/benchmark-b0/benchmark_results.json`.

### B1 optimized solution (and B0 comparison)

```bash
python -m agentic_cicd benchmark --system compare --output outputs/benchmark-compare
```

**Expect:** B0 simulated cost **375**, B1 simulated cost **220**, improvement **41.3333%** (CLI prints `cost_reduction_pct=0.413333`, which is that percentage as a fraction), correctness **14/14**, false skips **0**, `optimization_win_eligible` **true**. Writes `outputs/benchmark-compare/comparison.json`.

Optional single-flow smoke (not required if the suite commands above succeed):

```bash
# B0 baseline — one feature→development flow
python -m agentic_cicd b0 --source feature --target development --fixtures fixtures --output outputs/b0 --registry outputs/registry
# B1 optimized solution — docs-only change
python -m agentic_cicd b1 --source feature --target development --changed README.md --cache outputs/cache --warm-cache --output outputs/b1 --registry outputs/registry
```

### Tests

```bash
python -m pytest
```

**Expect:** all tests pass (currently 87). Offline B2 (no `B2_BASE_URL`, no key) equals B1 and is covered here. That is **not** a live-LLM requirement.

### Lint / format checks

```bash
python -m ruff check .
python -m ruff format --check .
```

**Expect:** ruff clean; files already formatted.

### Optional B2 experiment (not required)

B2 is an **optional experiment**. It is **not** required to reproduce the main B0→B1 result.

B2 was investigated as an agentic runtime wrapper (B1 first, model proposes, verifier final). It was **rejected as the production optimizer** because it did not improve B1 under a $0 constraint (same simulated cost, large extra latency; E-004, E-006, E-010, E-011).

Default B2 with no env vars is offline and equals B1. Do **not** install Ollama or set `B2_API_KEY` unless you specifically want to replay that experiment. Live replay is documented in [`docs/AGENT_PROVIDER_RESEARCH.md`](docs/AGENT_PROVIDER_RESEARCH.md).

```bash
# optional B2 experiment — offline (no Ollama, no API key); equals B1
python -m agentic_cicd benchmark --system agentic --output outputs/benchmark-b2
```

---

## Agents, experiments, and the hot take

**Cursor** (Cursor Grok 4.6, Agent mode) was used throughout to investigate the problem, implement B0/B1/B2, and keep an evidence trail — including recommending **not** to add a Git change detector at freeze time (D-053, CD-014). That usage is recorded in [`docs/CURSOR_ENVIRONMENT.md`](docs/CURSOR_ENVIRONMENT.md) and [`docs/CURSOR_DISCOVERIES.md`](docs/CURSOR_DISCOVERIES.md).

**B2** asked a local model for a structured `b2_proposal` only on conservative B1 over-runs. The verifier never delegated skip authority to the model. Live `$0` models (`qwen2.5:3b`, then `qwen3:4b-instruct`) copied B1 or fell back. They did not discover hidden edges on S16–S18.

**Hot take:** on this problem, a small checkable impact graph beat both a naive full pipeline and a local LLM wrapper. The valuable agent work was **engineering with Cursor**, not shipping a 3B/4B runtime optimizer. Full write-up: [`docs/INSIGHTS.md`](docs/INSIGHTS.md).

Story: baseline (E-002) → deterministic optimization (E-003) → agent investigation → live agent experiments (E-006–E-011) → **select B1** (D-050) → freeze without a Git adapter (D-053).

---

## Documentation map

| Document | Role |
| --- | --- |
| [docs/INSIGHTS.md](docs/INSIGHTS.md) | Lessons and hot take |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Hypothesis, current state, what changed |
| [docs/PROBLEM_FRAMING.md](docs/PROBLEM_FRAMING.md) | Evaluation contract; Catalog Ranker batch workload |
| [docs/OPTIMIZATION_CONTRACT.md](docs/OPTIMIZATION_CONTRACT.md) | Optimizer-facing contract; producer/consumer reuse |
| [docs/B0.md](docs/B0.md) / [B1.md](docs/B1.md) / [B2.md](docs/B2.md) | Implementations (execution vs optimization vs experiment) |
| [docs/BENCHMARK.md](docs/BENCHMARK.md) | S01–S14 change classes (+ S16–S18 pointer) |
| [docs/AGENT_VALUE_BENCHMARK.md](docs/AGENT_VALUE_BENCHMARK.md) | Why B2 did not beat B1 |
| [docs/AGENT_DESIGN.md](docs/AGENT_DESIGN.md) | B2 contract |
| [docs/AGENT_PROVIDER_RESEARCH.md](docs/AGENT_PROVIDER_RESEARCH.md) | Cursor ≠ B2; $0 local path |
| [docs/CURSOR_ENVIRONMENT.md](docs/CURSOR_ENVIRONMENT.md) | Coding-agent sessions |
| [docs/CURSOR_DISCOVERIES.md](docs/CURSOR_DISCOVERIES.md) | Development discoveries |
| [docs/IMPROVEMENT_CHANGELOG.md](docs/IMPROVEMENT_CHANGELOG.md) | Iterations I-001–I-020 |
| [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md) | Experiments E-001–E-013 |
| [docs/DECISION_LOG.md](docs/DECISION_LOG.md) | Decisions, including D-050–D-053 |

Generated runs go to `outputs/` (gitignored). Numbers above are copied from recorded experiments, not from hoped-for metrics.

## License

MIT. See [LICENSE](LICENSE).
