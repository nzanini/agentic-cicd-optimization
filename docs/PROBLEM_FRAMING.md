# Problem framing and evaluation contract

**Phase:** 1.3 contract; 1.4 workload; 1.5 B0; 1.6 suite; 1.6.1 B0 promote correction; 2.1 optimizer-facing contract  
**Status:** this evaluation contract remains in force. B1 implements [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md) and is the selected optimizer. B2 is implemented per [AGENT_DESIGN.md](AGENT_DESIGN.md) and was **not** selected as the product (E-010, E-011).  
**Date:** 2026-08-29

This document is the source of truth for the problem, workload, pipeline, correctness rules, and evaluation method. It does **not** claim that an agent has improved anything.

Phase 2.1 does **not** replace this file. It records the job-dependency, change-impact, safety, promotion, objective, and agent-boundary contract that a future optimizer must satisfy. B0 and S01–S14 are unchanged.

Related records: [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md), [ROADMAP.md](ROADMAP.md), [DECISION_LOG.md](DECISION_LOG.md), [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md), [IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md).

---

## 1. Problem definition

**User:** a software engineer or CI/platform owner who waits on pipelines that re-run expensive jobs even when a change cannot affect those jobs’ outputs.

**Motivating failure:** CI/CD executes work that is not required for the resulting artifacts, outputs, or promoted state to stay correct.

**Objective (constrained):**

> Minimize CI/CD execution time and unnecessary work **while preserving correctness**.

Correctness is a hard constraint. The system must never skip a job that is required for artifacts, outputs, or promoted state to remain correct. Maximizing the number of skipped jobs is **not** the objective.

**What this project studies:** an agent (later) that chooses a sufficient job set for a given change and promotion context, compared with a simple baseline, on a fixed scenario suite.

**What this project is not:** a machine-learning modeling project, a production CI platform, or a cloud MLOps stack.

---

## 2. Workload / use case

**Name:** Catalog Ranker.

**Kind:** a local **batch** workload. One run consumes committed fixtures, scores the whole catalog for every synthetic persona, evaluates those lists, and packages a content-addressed artifact. It is **not** a production ML training pipeline and **does not train a model**. The ranker weights are frozen in git.

**Use case:** rank a small movie catalog for a handful of synthetic user personas. A judge should be able to open a JSON file and see “user U2 → top 5 titles.”

**Why this workload:** it creates a short, understandable dependency graph (data → features → frozen model → scores → metrics → bundle → promote) without requiring training, GPUs, or paid APIs. The interesting problem is **which CI jobs that graph requires after a given change**, not model quality. Catalog Ranker is the thing being *scheduled*. B0 / B1 / B2 are different strategies for *which jobs to run*.

**Workload components (local implementation in Phase 1.4):**

| Component | Role |
| --- | --- |
| Vendored catalog snapshot | Input items (id, title, year, genres, …) |
| Synthetic personas | Fixed preference vectors; not real users |
| Frozen ranker artifact | Small committed weights file. Not trained or updated in this repository |
| Scoring | Deterministic ranking of the catalog per persona |
| Evaluation | Metrics over those rankings (coverage, score summary, checksum) |
| Bundle | Content-addressed package of predictions, metrics, manifests |

**Concrete outputs (produced by the batch run):**

| Output | Purpose |
| --- | --- |
| `predictions.json` | Ranked titles and scores per persona |
| `metrics.json` | Summary metrics and a predictions checksum |
| `dataset_manifest.json` | Record count and content hash of data used |
| `model_manifest.json` | Model artifact version and hash |
| `run_metadata.json` | Run id, git identity, job decisions, timestamps |
| Addressable bundle | The above plus the model file, hashed as one artifact |

Scoring must be **deterministic** given the same catalog, personas, model, and code. No random seeds in the happy path.

**Phase 1.4 fixture paths**

| File | Role |
| --- | --- |
| `fixtures/catalog.json` | 16 synthetic movies |
| `fixtures/personas.json` | 4 synthetic personas |
| `fixtures/model/ranker.json` | Frozen weights (`weighted_genre_dot`, `top_n=5`) |
| `configs/scoring_weights.json` | Optional overlay; changes scores (S12) |
| `configs/pipeline.json` | Pipeline metadata; not read by the ranker (S08) |
| `benchmark/scenarios.json` | S01–S14 ground truth |

Local command: `python -m agentic_cicd rank --fixtures fixtures --output outputs/latest`. Generated files go under the output directory (gitignored). When present, `configs/scoring_weights.json` is merged into the frozen ranker (S12). That overlay changes scores; it is not training.

**Rejected as the product:** training loops, hyperparameter search, large Hugging Face models, and any design whose main difficulty is model quality.

---

## 3. Data strategy

### Options compared

| Option | Realistic ingestion? | Reproducible without network? | Auth / rate limits | Data stable over time? | Verdict |
| --- | --- | --- | --- | --- | --- |
| Live public API every run (e.g. TMDB, OMDb) | High | No | Often key + quotas | No | **Rejected** for benchmark and demo |
| Live no-key API (e.g. Gutendex) | High | No | Usually none | No | **Rejected** for benchmark |
| Runtime download of MovieLens / similar | Medium | No | License/network | Yes if pinned URL+hash | Overkill; still a network dependency |
| One-time public fetch, **vendored snapshot** in git | Medium (origin story) | Yes | Only for the original fetch | Yes (we pin the file) | Acceptable origin; not required |
| Fully synthetic catalog + personas | Low–medium | Yes | None | Yes | **Acceptable and preferred for fixtures** |
| Hybrid: ingest job reads fixture; optional API adapter unused in benchmark | Medium | Yes if fixture is default | Adapter only | Yes | **Chosen** |

### Decision

**Fixture-first hybrid (D-011).** The ingest job exists so “data changed” and “ingest code changed” are real skip/run distinctions. The benchmark and default path **must not** call a live API.

- Source-controlled fixture: a small catalog (on the order of tens to low hundreds of rows) plus synthetic personas.
- The catalog schema may resemble a public movie API so an optional refresh adapter can be added later. That adapter is **out of scope** until a later phase explicitly asks for it.
- If a snapshot is ever refreshed from the internet, persist it, pin it, and change the fixture hash. Old benchmark scenarios keep the old fixture.
- Synthetic data is preferred wherever it improves determinism.

A public API was **not** selected for curiosity. Live APIs add realism to ingestion but make the hackathon unreproducible. The ingest **job** is what we need; a live service is not.

---

## 4. Branch and promotion model

**This diagram is the simulated CI/CD promotion model used by the benchmark.** It is **not** a Git branch topology that a judge must create. The public submission repository is a single Git branch (`main`). Reproducing B0/B1 does **not** require opening a pull request, creating a `feature` or `development` Git branch, or using GitHub Actions.

```text
feature / custom branch     ← simulated source flow label
        │  pull request     ← simulated promotion (not a GitHub PR to open)
        ▼
   development
        │  pull request     ← simulated promotion (not a GitHub PR to open)
        ▼
   main  (= production)     ← simulated target flow label
```

**Invalid:** any promotion or deploy path from `feature/*` (or other non-`development` heads) directly to `main`. Baseline and optimized systems must fail `branch_guard` and must not publish a production artifact.

### Environment symmetry

Development and production are **symmetric** if they run the same job *definitions* and production serves the **same artifact identity** that development already validated, unless a change after that validation invalidates the artifact.

Production is not “run the recipe again and hope it matches.”

### Artifact identity

An artifact is identified by a **content hash** of the bundle payload (predictions, metrics, dataset manifest, model object, and the scoring-code identity that produced them).

**Phase 1.4 implementation (D-018):** `artifact_id` is the lowercase hex **SHA-256** of canonical JSON (`sort_keys=True`, compact separators, UTF-8) of that payload. `run_metadata.json` (run id, timestamps) is written but **excluded** from the hash so two runs can share an id. This choice can be changed later if a different bundle layout is needed.

- Same inputs and code → same artifact id (deterministic scoring).
- **Clean promote:** production artifact id **must equal** the development artifact id. Rebuilding on `main` is unnecessary work; if a rebuild were to disagree, that is a symmetry failure.
- **Dirty promote:** additional commits after the validated development revision that affect artifact inputs require a **rebuild** on the promotion path, then a new package, then promote. Skipping score here is incorrect.

---

## 5. CI/CD job topology

Jobs are the executable graph implemented by B0 (and reused by B1/B2). Relative costs are **design weights** for the simulator (dimensionless units). They are not measured wall-clock times. These are CI/promotion stages around a batch ranker, **not** training stages.

### Graph (feature → development)

```text
branch_guard → validate → test
                         ↘
                           ingest → prepare → score → evaluate → package → publish
```

`test` may run in parallel with `ingest` after `validate`. Sequential execution is also acceptable in a first simulator.

### Graph (development → main)

```text
branch_guard → validate → …rebuild jobs if artifact inputs changed…
                         → package (if rebuild) → promote
```

On a **clean** promote, only `branch_guard` and `promote` are required. `publish` does not run on this path.

### Job cards

| Job | Purpose | Inputs | Outputs | Depends on | Cost weight | Typical requiring changes | Flows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `branch_guard` | Enforce allowed promotions | Source/target refs | Policy verdict | — | 1 | Always | Both |
| `validate` | Schema/config/manifest sanity | Configs, manifests, graph files | Validation report | `branch_guard` | 1 | Config, manifests, schemas, most code/data PRs | Both (promotion metadata on promote) |
| `test` | Unit tests for ingest/prep/score/eval | Application and test code | Test report | `validate` | 3 | Application code, tests, dependencies | Feature→dev; promote only if rebuild needs code trust |
| `ingest` | Materialize raw catalog from fixture | Fixture / ingest code | Raw dataset + dataset manifest | `validate` | 5 | Ingest code, catalog fixture | Feature→dev; promote only if data inputs changed |
| `prepare` | Deterministic features | Raw dataset, prep code | Prepared dataset | `ingest` (or cached raw) | 4 | Prep code, raw data identity | Feature→dev; promote if those inputs changed |
| `score` | Rank catalog per persona (**dominant cost**) | Prepared data, model artifact, scoring code | `predictions.json` | `prepare` (or cached prepared), model | 10 | Scoring code, model, prepared data | Feature→dev; promote if those inputs changed |
| `evaluate` | Metrics and checksums | Predictions, eval code | `metrics.json` | `score` (or cached predictions) | 3 | Eval code, predictions | Feature→dev; promote if those inputs changed |
| `package` | Content-addressed bundle | Predictions, metrics, manifests, model | Bundle + artifact id | `evaluate` | 2 | Anything that changes bundle payload | Feature→dev; promote if rebuild |
| `publish` | Record bundle as the development artifact | Bundle | Dev pointer / promotion record | `package` | 2 | New bundle on feature→dev | Feature→dev only |
| `promote` | Point production at a **validated** artifact id; verify identity and ancestry | Dev artifact id, git ancestry, optional new bundle | Prod pointer + verification report | `branch_guard`, and `package` if rebuild | 2 | Every development→main PR | Development→main only |

No extra jobs (Docker image build, cloud deploy, metadata-only generators) are in v1. Expensive work is represented by `score` (and, to a lesser degree, `ingest` / `prepare`). Simulated cost is a **counter** equal to the cost weight, not a real model train.

### Why a skipped producer can still be required as an input

Downstream jobs consume upstream **artifacts**, not the fact that the producer ran in this request.

- `prepare` needs the raw catalog / personas from `ingest`.
- `score` needs `prepared_catalog.json` (and personas + the frozen model).
- `evaluate` needs `predictions.json`.
- `package` needs predictions, metrics, the dataset manifest, and the model object.
- `publish` / rebuild `promote` need the packaged `artifact_id`.

Skipping `ingest` or `prepare` is legal only if no required consumer needs that output, **or** a cached output with matching input identity is hydrated into the working directory. Re-doing the work inside another job and not counting the skipped job is not a legal skip. B0 never skips, so it always re-materializes every intermediate. B1 implements the cache/hydrate path. Formal rule: [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md) §2.

---

## 6. Baseline

**Primary baseline (B0): always run every job that is legal on that flow.**

| Flow | B0 executes |
| --- | --- |
| Feature → development | `branch_guard`, `validate`, `test`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `publish` |
| Development → main (rebuild; B0 default) | `branch_guard`, `validate`, `test`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `promote` (rebuild; no `publish`). Promotes the **new** artifact id. |
| Development → main (reuse; explicit) | `branch_guard`, `promote` only. Reuses the validated development artifact id. The caller must pass `promote_mode=reuse`; B0 does not infer this from files. |
| Feature → main | `branch_guard` only; **fail**; no publish/promote |

B0 still **enforces branch rules**. It does not use path filters or job-skip intelligence. Clean vs dirty promote is an explicit `promote_mode` input (benchmark: empty `apply` → reuse, non-empty `apply` → rebuild). That is not the future optimizer.

Phase 1.6.1 corrected a B0 defect: dirty promote used to rebuild and then reject the new id (E-001 S10). The S10 ground truth was not changed.

**Why B0:** it matches a naive “run the whole workflow on every PR” pipeline. It is executable later, produces the same artifact *types* as the optimized system, and is an honest comparison point. It is not claimed to be the smartest non-agent heuristic.

**Stretch baseline (B1), historical Phase 1.3 note:** this paragraph originally deferred path filters. B1 is now implemented as an impact-graph optimizer (not path filters) and is the selected solution. See [`B1.md`](B1.md). It uses the **same** S01–S14 scenarios.

**Phase 1.5 / 1.6.1:** B0 is implemented as a local runner (`python -m agentic_cicd b0`). See [`B0.md`](B0.md). It has been **measured** on S01–S14 (E-001, then corrected E-002). The B0 vs B1 comparison is **E-003**. Simulated costs are the Phase 1.3 weights (counter only, no sleep). `publish` / `promote` also depend on `test` so a failed test cannot write an environment pointer.

---

## 7. Change scenarios and ground truth

Scenarios are the benchmark. The same list is used for B0, B1, and B2. Expected jobs are the **minimum required set** for correctness. Running extra jobs is not a correctness failure.

**B0 vs B1 on this table:** B0 does **not** read the change class. On feature→development it always runs all nine legal jobs. On development→main it runs a full rebuild unless the caller explicitly passes `promote_mode=reuse` (S09). B1 classifies the change and may skip jobs whose outputs remain valid or can be hydrated from cache. High-level scenario map: [BENCHMARK.md](BENCHMARK.md).

`PUB` = `publish`. `PROM` = `promote`. `BG` = `branch_guard`.

| ID | Category | Change (conceptual) | Flow | Required jobs | Notes |
| --- | --- | --- | --- | --- | --- |
| S01 | Documentation-only | Markdown / README / `docs/**` only | feature→dev | `BG` | No artifact inputs change |
| S02 | Test-only | Tests only; no `src` / fixtures / model | feature→dev | `BG`, `test` | Must not ship a new bundle |
| S03 | Scoring / application | Scoring code | feature→dev | `BG`, `validate`, `test`, `score`, `evaluate`, `package`, `PUB` | Reuse raw + prepared data |
| S04 | Data snapshot | Vendored catalog fixture only | feature→dev | `BG`, `validate`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `PUB` | No code tests strictly required |
| S05 | Preparation | Prep code only | feature→dev | `BG`, `validate`, `test`, `prepare`, `score`, `evaluate`, `package`, `PUB` | Reuse raw ingest output |
| S06 | Model artifact | Frozen ranker file only | feature→dev | `BG`, `validate`, `score`, `evaluate`, `package`, `PUB` | Reuse raw + prepared data |
| S07 | Dependencies | `pyproject.toml` / lock | feature→dev | All feature→dev jobs | Conservative: runtime may affect every stage |
| S08 | Pipeline configuration | Workflow / job-graph only (no score weights) | feature→dev | `BG`, `validate` | Must not skip `validate` |
| S09 | Clean promote | PR development→main; no invalidating commits | dev→main | `BG`, `PROM` | Environment symmetry: same artifact id |
| S10 | Dirty promote | Promote PR plus scoring-code change after validation | dev→main | `BG`, `validate`, `test`, `score`, `evaluate`, `package`, `PROM` | Must **not** treat as clean promote |
| S11 | Illegal promotion | feature→main | feature→main | `BG` (fail) | No `PUB`/`PROM` |
| S12 | Adversarial path | Score weights live under `configs/` (looks like “config”) | feature→dev | `BG`, `validate`, `score`, `evaluate`, `package`, `PUB` | Naive `configs/**` → validate-only **false-skips `score`** |
| S13 | Evaluate-only | Eval / metric code only | feature→dev | `BG`, `validate`, `test`, `evaluate`, `package`, `PUB` | Reuse predictions |
| S14 | Ambiguous / unknown | New path not in the known graph | feature→dev | All feature→dev jobs | Fail closed (D-016) |

**Adversarial case:** S12. A superficial path filter that maps `configs/**` to “pipeline configuration” (S08) would skip `score` while changing prediction-affecting weights.

Fourteen scenarios (≥ 10), including illegal promotion, clean vs dirty promote, dependency conservatism, and ambiguity.

**Phase 1.6:** encoded in `benchmark/scenarios.json`. S12 is a real overlay (`configs/scoring_weights.json` is merged into the ranker). S08 changes `configs/pipeline.json`, which the ranker does not read.

---

## 8. Correctness and safety

The optimized system is **correct** on a scenario if and only if all of the following hold:

1. **Required jobs ran.** No job in that scenario’s required set was skipped.
2. **Required outputs exist** when the flow succeeds (predictions/metrics/bundle as applicable).
3. **Branch rules** are enforced (S11 fails closed; only `development` may promote to `main`).
4. **Artifact identity / symmetry:** on S09, production artifact id equals the validated development artifact id.
5. **Determinism:** given identical artifact inputs, predictions checksum matches the fixture expectation (once fixtures exist).
6. **Ambiguity policy:** if the system cannot confidently decide that a job is *not* required, it **must run the job**. Skip is allowed only with an explicit, checkable reason that matches the graph.

**False skip** = a required job skipped. False skips are a **safety failure**. A configuration that false-skips may not claim an optimization win on the suite.

**Unnecessary job** = a job that ran but is not in the required set. These worsen the primary/secondary *optimization* metrics and do not fail correctness.

**Fail conservative, not fail open.** Uncertainty → execute.

Quality-gate *thresholds* (evaluate failing the build because a metric dropped) are **not** set in this phase.

---

## 9. Evaluation contract

B0-only measurements exist (E-001, E-002 in [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md)). The B0 vs B1 comparison is **E-003**.

### Protocol

1. Fix the scenario suite (S01–S14) and job cost weights.
2. Run **B0** on every scenario.
3. Run the **optimized** system on the **same** scenarios, same fixtures, same cost weights.
4. Apply the **correctness gate** before interpreting speedups.
5. Record observability events (section 11).

### Primary metric (one)

**Suite simulated duration**, gated on safety.

- Per scenario, simulated duration = sum of **cost weights** of jobs with status `executed` (skipped jobs add 0).
- Suite score = **sum** of per-scenario simulated durations.
- Report reduction vs B0: `(T_B0 − T_opt) / T_B0`, only if **false-skip rate = 0** and S11 does not promote.

**Why this, not wall-clock:** the user’s value is time waiting on CI, but wall-clock is machine- and runner-dependent. Declared weights make the *comparison* reproducible. Wall-clock is still recorded as secondary.

**Why not “jobs skipped”:** the brief forbids maximizing skips; skipping a cheap job is not equal to skipping `score`. Duration weights encode that.

**Why a gate:** an “optimizer” that skips `score` on S12 is faster and **wrong**.

### Safety / correctness metrics (gates)

| Metric | Role |
| --- | --- |
| Scenario correctness pass rate | Fraction of scenarios satisfying section 8 |
| False-skip rate | Required jobs skipped / required jobs; **target 0** |
| Illegal promotion accepted | Count; **target 0** |
| Clean-promote identity mismatch | Count on S09; **target 0** |

### Secondary optimization / analysis metrics

| Metric | Role |
| --- | --- |
| Per-scenario simulated duration | Table for insight |
| Median scenario simulated duration | Less sensitive to one heavy scenario |
| Jobs executed / skipped (counts) | Explain duration |
| Unnecessary jobs executed | Over-work vs B0 or vs required set |
| Job-level decision accuracy | Run/skip vs ground truth (run extra is a miss on “skip” but not a safety fail) |
| Wall-clock workflow duration | Measured later; noisy |
| Agent latency and cost | Only if an LLM/agent API is used; not defined until then |

Optimization metrics and safety metrics stay **separate**. Safety is not averaged into a single “accuracy” that can hide a false skip.

---

## 10. Reproducibility approach

The judge path is local and is documented in the repository README. It does **not** use GitHub Actions.

1. `git clone` the public repository (`main` only). Do not create branches or open a PR.
2. `cd` into the repository and create the documented Python environment (`venv`, `pip install -e ".[dev]"`).
3. **B0 baseline:** `python -m agentic_cicd benchmark --output outputs/benchmark-b0` (expect simulated cost **375**).
4. **B1 optimized solution:** `python -m agentic_cicd benchmark --system compare --output outputs/benchmark-compare` (expect B0 **375**, B1 **220**, **41.3333%**, correctness **14/14**, false skips **0**).
5. Run tests and ruff (`python -m pytest`; `python -m ruff check .`; `python -m ruff format --check .`).
6. Inspect generated artifacts in local `outputs/` (gitignored). There is no CI artifact store.

No paid cloud. No live API, Cursor subscription, or Ollama install required. **Optional B2 experiment** commands exist but are not part of this path.

### Three kinds of files

| Kind | Lives in git? | Examples |
| --- | --- | --- |
| **Fixtures and configuration** | Yes | Catalog snapshot, personas, model artifact, scenario list, expected required jobs, expected checksums |
| **Generated execution artifacts** | No | Per-run predictions, bundles, logs, local `outputs/` |
| **Benchmark results** | No (run); schema/examples may be yes | Suite metrics JSON, observability dumps |

Do not treat workflow outputs as source. Generated results go to local `outputs/` (gitignored). This project does **not** use GitHub Actions; judges must not expect CI artifacts. Expected *answers* for the benchmark (required job sets, checksums) stay in git.

---

## 11. Observability approach

No dashboard in this phase. Later visualization should be possible from structured records.

**Per workflow run**

- `run_id`, `scenario_id`, `system` (`baseline` \| `optimized`), `git_sha`
- `source_ref`, `target_ref` (branch flow)
- `started_at`, `ended_at`, `wall_duration_ms`
- `simulated_duration` (sum of executed cost weights)
- `correctness_pass`, `false_skip_count`
- `artifact_id_dev`, `artifact_id_prod` (if applicable)

**Per job**

- `run_id`, `job_name`
- `status` (`executed` \| `skipped` \| `failed`)
- `skip_reason` (null if executed)
- `started_at`, `ended_at`, `wall_duration_ms`
- `simulated_cost`
- `input_hash`, `output_hash`
- `depends_on` (job names)

**Per artifact**

- `artifact_id`, `type`, `produced_by_job`, `path` (local or CI artifact name)

These fields are the contract for later logs. Schema files and writers are not created here.

---

## 12. Alternatives considered and rejected

| Alternative | Why rejected (this phase) |
| --- | --- |
| Live public API as the benchmark data source | Reproducibility, auth, drift (section 3) |
| Train a model / optimize quality | Out of scope; ML is only a workload |
| AWS, SageMaker, Airflow, Kubernetes | Conflicts with D-003 |
| Primary metric = count of skipped jobs | Encourages unsafe or trivial skips |
| Primary metric = wall-clock only | Not reproducible across machines |
| Path filters as the *only* baseline | Useful later (B1); weaker story than “naive full pipeline” for B0 |
| Direct feature → main | Violates intended promotion discipline |
| Rebuild-on-promote as the *optimized* behavior | Breaks environment symmetry |
| Large job list (image build, cloud deploy, extra metadata jobs) | No extra optimization insight for v1 |

---

## 13. Unresolved decisions

Still open after Phase 1.3 (see also D-OPEN-* in [DECISION_LOG.md](DECISION_LOG.md)):

- Agent architecture, model, tools, and prompts (D-OPEN-07, D-OPEN-08). Phase 2.1 bounds the agent (it must not be the sole skip authority) but does not design it.
- GitHub Actions vs local runner vs both (D-OPEN-12) — **closed for submission:** local runner only. GHA is not present and not required (D-052).
- Whether to implement stretch baseline B1 — **closed:** B1 is the selected impact-graph optimizer (E-003).
- Exact fixture paths, persona count, and hash algorithm — **closed in 1.4:** `fixtures/catalog.json` (16 titles), `fixtures/personas.json` (4 personas), `fixtures/model/ranker.json`; SHA-256 canonical JSON (D-018). S12 overlay path is implemented.
- Whether `evaluate` may fail the workflow on metric thresholds.
- How simulated cost is realized — **closed for B0:** counter only, no sleep.
- In-repo Docker, lockfile tool, extra libraries (D-OPEN-11).
- User interviews / field evidence (D-OPEN-01 remains; persona is still a working definition).

Phase 2.1 additionally leaves open (see [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md) §8): optimizer input signal (`files_changed` vs `apply`); intermediate cache; dirty-promote development-pointer rewrite; uncovered change classes; how the harness will invoke a non-B0 system.

---

## 14. Phase 2.1 pointer

The optimizer-facing contract lives in [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md). Summary of what that file adds without changing this one:

- Per-job inputs, outputs, dependents, and invalidating change classes.
- Change → component → invalidated output → required jobs (conceptual only).
- Safety: UNKNOWN/AMBIGUOUS → RUN; false skip remains a safety failure.
- Promotion: feature→development is not the same problem as clean vs dirty development→main.
- Objective: keep gated suite simulated duration (D-015). E-002 (`T_B0 = 375`) is the baseline, not an optimization.
- S01–S14 stay the evaluation suite; ambiguities are documented, not silently edited.
- Comparison ladder: B0 → deterministic optimizer → agent. Deterministic verification owns skip permission.
