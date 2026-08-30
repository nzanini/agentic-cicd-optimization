# Agentic CI/CD Optimization

A [micro1 Agentic Workflows Hackathon](https://micro1.ai) project.

**Problem:** CI/CD often re-runs jobs that a change cannot affect. This repo asks which jobs still need to run **without skipping required work**.

**Read next:** [`docs/INSIGHTS.md`](docs/INSIGHTS.md). Deeper contracts, logs, and implementation notes are linked at the bottom.

---

## Headline result (E-003)

Frozen suite **S01–S14**. Metric: sum of executed job **weights** (simulated pipeline cost, not wall-clock).

| | **B0** baseline | **B1** selected optimizer |
| --- | ---: | ---: |
| Simulated cost `T` | **375** | **220** |
| Reduction | — | **155 (41.3333%)** |
| Correctness | 14/14 | **14/14** |
| False skips | 0 | **0** |
| Unnecessary jobs | 37 | **0** |

B1 is the presented solution. B2 (runtime LLM) was measured and **did not beat B1**. Evidence: [E-003](docs/EXPERIMENT_LOG.md).

---

## Architecture

```text
Catalog Ranker  ← small deterministic batch workload (not the product)
      ↓
B0  always run the legal job graph          (baseline)
B1  path → component → impact → jobs        (selected optimizer; not an LLM)
B2  B1 first; LLM may propose; verifier     (experiment; rejected)
```

| Layer | Role | Status |
| --- | --- | --- |
| **Catalog Ranker** | Workload being scheduled. Frozen weights. No training. | Implemented |
| **B0** | Unoptimized execution: every legal job | Measured (E-002 / E-003) |
| **B1** | Deterministic impact graph + SHA-256 cache | **Selected** (E-003) |
| **B2** | Optional agent proposal; **deterministic verifier** is the only skip authority | Implemented; **not selected** (E-010, E-011) |
| **Cursor** | Coding / research agent that designed, implemented, tested, and evaluated this repo | Development evidence |
| **Ollama (3B/4B)** | B2 runtime models. **Not Cursor.** $0 local inference | No `T` win vs B1 |

Do not collapse Cursor and B2. Cursor built the system. B2’s LLM does not drive the submitted optimizer.

```text
branch_guard → validate → test
                         ↘
                           ingest → prepare → score → evaluate → package → publish | promote
```

---

## Fastest reproduction

Python **3.11+** (recommended 3.12). Runtime dependencies: **none**.

**Not required:** API keys, Cursor, Ollama, GitHub Actions, paid cloud, or any Git branch other than `main`.

```bash
git clone https://github.com/nzanini/agentic-cicd-optimization.git
cd agentic-cicd-optimization
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

```bash
python -m agentic_cicd benchmark --output outputs/benchmark-b0
python -m agentic_cicd benchmark --system compare --output outputs/benchmark-compare
```

**Expect (B0):** `simulated_cost` **375**, correctness **14/14**, `false_skip_count` **0**.  
**Expect (compare):** B0 **375**, B1 **220**, `cost_reduction_pct=0.413333` (that is **41.3333%**), 14/14, false skips **0**, `optimization_win_eligible` **true**.

Optional Docker (`python:3.12-slim`) and `scripts/judge_repro.sh` exist if host Python is missing. They are conveniences, not requirements.

---

## Cursor vs B2

**Cursor** (Cursor Grok 4.6, Agent mode) was the coding/research agent: design, implementation, tests, investigation, and evaluation — including recommending **not** to add a Git change detector at freeze time (D-053). Judges do **not** need Cursor. Record: [`docs/CURSOR_ENVIRONMENT.md`](docs/CURSOR_ENVIRONMENT.md).

**B2** is a separate runtime experiment. A local model may propose extra skips only on conservative B1 over-runs; the verifier never delegates skip authority. Live `$0` models copied B1 or fell back (`delta_vs_b1 = 0`; `novel_accept` = 0 on S16–S18). That is **not** a B2 win.

**Hot take:** a checkable impact graph beat both a naive full pipeline and a local LLM wrapper. The agent work that mattered was **engineering with Cursor**, not shipping a 3B/4B optimizer. Write-up: [`docs/INSIGHTS.md`](docs/INSIGHTS.md).

---

## Limitations (not hidden)

- Catalog Ranker is a **small, intentional** reproducible workload (16 movies, 4 personas). It is not a production ML pipeline.
- B1 is **deterministic** path/component/impact reasoning plus identity-checked cache. It is not an LLM and does not inspect Git (`--changed` is caller-supplied; S01–S14 harness uses `files_changed ∪ apply`, D-028).
- B2 did **not** beat B1. It remains an experiment.
- GitHub Actions are **not** present and **not** required. Reproduction is local.
- The benchmark is a **controlled** scenario suite (`benchmark/scenarios.json`), not live GitHub traffic.
- Primary metric is **simulated** pipeline cost (job weights), not wall-clock.
- Simulated `feature` / `development` / `main` are **CI flow labels**, not Git branches a judge must create. Public repo: **`main` only**. Do not open a PR.

---

## How B1 works

Unknown, dependency, or orchestrator paths **fail closed** (full legal graph). Skip only with a checkable reason. Scenario IDs never appear in the optimizer.

```text
changed paths → components → invalidated artifacts → required jobs
                 ↘ cache identity check
```

If B1 skips `ingest` / `prepare`, it **hydrates** last-known-good cached artifacts so `score` can still run. Extra jobs are unnecessary, not a safety failure. A **false skip** disqualifies any claimed win. UNKNOWN → RUN.

Examples: docs-only (S01) cost 1; score-code (S03) reuses ingest/prepare (cost 22); unclassified (S14) still costs 31. Details: [`docs/B1.md`](docs/B1.md), [`docs/OPTIMIZATION_CONTRACT.md`](docs/OPTIMIZATION_CONTRACT.md).

B0 always runs the legal graph (no file inspection). Clean promote is explicit `promote_mode=reuse`, not change detection. [`docs/B0.md`](docs/B0.md).

B2 on S01–S14 equals B1 (`T` 220; E-004 offline, E-006 live). On S16–S18 both cost **93**. [`docs/B2.md`](docs/B2.md).

---

## Workload

Catalog Ranker ranks a vendored movie catalog for synthetic personas and writes a content-addressed artifact. Frozen `weighted_genre_dot` weights; nothing is trained. A judge can open JSON and see “user U2 → top 5 titles.”

Fixtures in git: `fixtures/catalog.json`, `fixtures/personas.json`, `fixtures/model/ranker.json`. Overlay `configs/scoring_weights.json` changes scores (S12). `configs/pipeline.json` is pipeline metadata and is **not** read by the ranker (S08).

Standalone (no CI graph): `python -m agentic_cicd rank --fixtures fixtures --output outputs/latest`.

| Job | Role |
| --- | --- |
| `branch_guard` | Allowed promotions only. Illegal `feature → main` fails here. |
| `validate` / `test` | Schema sanity; trust application code. |
| `ingest` → `prepare` → `score` → `evaluate` → `package` | Data → features → rank (**dominant cost**) → metrics → bundle. |
| `publish` / `promote` | Point development / production at the artifact. |

---

## Tests, lint, optional B2

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

**Expect:** 87 tests pass; ruff clean. Offline B2 (no `B2_BASE_URL`, no key) equals B1 and is covered here — **not** a live-LLM requirement.

```bash
# optional — not required for the 375 → 220 result
python -m agentic_cicd benchmark --system agentic --output outputs/benchmark-b2
```

Live B2 replay: [`docs/AGENT_PROVIDER_RESEARCH.md`](docs/AGENT_PROVIDER_RESEARCH.md).

Optional single-flow smoke (not required if the suite commands succeed):

```bash
python -m agentic_cicd b0 --source feature --target development --fixtures fixtures --output outputs/b0 --registry outputs/registry
python -m agentic_cicd b1 --source feature --target development --changed README.md --cache outputs/cache --warm-cache --output outputs/b1 --registry outputs/registry
```

---

## Documentation

**Judge path:** this README → [`docs/INSIGHTS.md`](docs/INSIGHTS.md) → deeper docs only if needed.

| Document | Role |
| --- | --- |
| [docs/INSIGHTS.md](docs/INSIGHTS.md) | **Start here after the README.** Lessons and hot take |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Hypothesis, current state, what changed |
| [docs/PROBLEM_FRAMING.md](docs/PROBLEM_FRAMING.md) | Evaluation contract; Catalog Ranker |
| [docs/OPTIMIZATION_CONTRACT.md](docs/OPTIMIZATION_CONTRACT.md) | Optimizer-facing contract |
| [docs/B0.md](docs/B0.md) / [B1.md](docs/B1.md) / [B2.md](docs/B2.md) | Implementations |
| [docs/BENCHMARK.md](docs/BENCHMARK.md) | S01–S14 (+ S16–S18 pointer) |
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
