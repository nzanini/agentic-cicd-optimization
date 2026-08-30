# Optimization contract (Phase 2.1)

**Phase:** 2.1 contract; 2.2 B1; 2.3 B2 design; 2.4 B2 implementation  
**Status:** B1 implements this contract. B2 is implemented per [AGENT_DESIGN.md](AGENT_DESIGN.md) and [B2.md](B2.md).  
**Date:** 2026-08-29  
**Does not claim:** that the agent beat B1 on S01–S14. E-003 is B1 vs B0. E-004 is B2 = B1 (delta 0).

This document is the formal contract a future optimized system must satisfy. It is derived from the Phase 1.3 evaluation contract, the executable B0 runner, the S01–S14 ground truth, and the Catalog Ranker workload.

It does **not** implement that system. B0 behavior and `benchmark/scenarios.json` are unchanged.

Related records: [PROBLEM_FRAMING.md](PROBLEM_FRAMING.md) (Phase 1.3 contract), [B0.md](B0.md), [BENCHMARK.md](BENCHMARK.md), [DECISION_LOG.md](DECISION_LOG.md) D-022–D-025, [ROADMAP.md](ROADMAP.md).

---

## 0. Methodological principle

Later work must be able to answer: **what exactly did the agent improve?**

Comparison is therefore a ladder, not a jump:

```text
B0  (always run every legal job)
  →  deterministic optimized solution
    →  agentic optimized solution
```

- **B0** is the measured unoptimized baseline (E-002). It is not an optimizer.
- The **deterministic layer** must establish a strong safety floor: known change classes map to required jobs; unknown impact runs extra work; a required job cannot be skipped.
- The **agent** must later demonstrate meaningful additional capability (ambiguous, adversarial, or novel cases that rules cannot classify confidently). Replacing a few `if` statements with an LLM call is not sufficient value.
- Safety-critical skip permission is **not** delegated solely to an LLM. A deterministic verifier may accept or reject a proposed skip set.

B1 exists (Phase 2.2). E-002 is the B0 baseline. E-003 is the B1 comparison. B2 exists (Phase 2.4). E-004 is B2 vs B1 on S01–S14 with no API key: same cost as B1, no invocations. That is not an agent improvement.

B2 must run B1 first and may invoke an agent only to refine conservative over-runs. The verifier is the skip authority ([AGENT_DESIGN.md](AGENT_DESIGN.md)).

---

## 1. Optimization objective

Retain the Phase 1.3 / D-015 simulated cost model. There is no documented reason to change it.

### Primary metric (gated)

**Suite simulated duration** = sum, over S01–S14, of the Phase 1.3 cost weights of jobs with status `executed`. Skipped and blocked jobs add 0.

Report reduction vs B0 only if **all** of the following hold:

- false-skip rate = 0
- S11 does not publish or promote
- scenario correctness pass rate is 14/14 under [PROBLEM_FRAMING.md](PROBLEM_FRAMING.md) §8

```text
reduction = (T_B0 − T_opt) / T_B0
```

**Current B0 reference (E-002, not an optimization):** `T_B0 = 375`.

### Why this objective

| Not the objective | Why not |
| --- | --- |
| Maximize skipped jobs | Encourages unsafe or trivial skips (D-009) |
| Wall-clock only | Machine- and runner-dependent; recorded as secondary and treated as noisy |
| Blend safety into one “accuracy” score | A false skip can hide inside an average |

User value is **correct pipelines that do less unnecessary work**. `score` (weight 10) is more expensive than `branch_guard` (weight 1). The weights encode that.

### Secondary quantities the optimizer should also reduce

Subject to the safety gate:

- unnecessary jobs executed (ran, not in `required_jobs`)
- median scenario simulated duration
- per-scenario simulated duration (insight table)

Wall-clock workflow duration, agent latency, and agent API cost are observational only until an agent exists.

### Cost weights (unchanged)

| Job | Weight |
| --- | --- |
| `branch_guard` | 1 |
| `validate` | 1 |
| `test` | 3 |
| `ingest` | 5 |
| `prepare` | 4 |
| `score` | 10 |
| `evaluate` | 3 |
| `package` | 2 |
| `publish` | 2 |
| `promote` | 2 |

B0 feature→development legal graph sums to **31**. Clean reuse promote sums to **3**. Dirty rebuild promote sums to **31**.

---

## 2. Job dependency model

Jobs are the Phase 1.3 / B0 graph. The table below is the **contract** for invalidation and reuse. B0 currently ignores reuse and always runs every scheduled job.

```text
branch_guard → validate → test
                         ↘
                           ingest → prepare → score → evaluate → package → publish | promote
```

`publish` is feature→development only. `promote` is development→main only. `publish` / rebuild-`promote` also depend on `test`, so a failed test cannot write an environment pointer.

### Intermediate artifacts (logical)

These are the cacheable outputs a future optimizer may reuse when **input identity is unchanged and the object is available**. B0 does not cache across runs except environment pointers in the registry.

| Artifact | Produced by | Consumed by |
| --- | --- | --- |
| Policy verdict | `branch_guard` | (terminal for illegal flows) |
| Validation report | `validate` | (gate only) |
| Test report | `test` | `publish`, rebuild `promote` |
| Raw catalog + personas + dataset manifest | `ingest` | `prepare`, `package` (manifest) |
| Prepared catalog | `prepare` | `score`, `evaluate` |
| Effective model (frozen file ⊕ optional overlay) | fixtures / `score` load | `score`, `package` |
| Predictions | `score` | `evaluate`, `package` |
| Metrics | `evaluate` | `package` |
| Bundle + `artifact_id` | `package` | `publish`, rebuild `promote` |
| Development pointer | `publish` | `promote` |
| Production pointer | `promote` | (terminal) |

**Reuse rule:** skipping a producer is legal only if (a) no required downstream job needs that output, or (b) a cached output with a matching input identity is available. Re-doing the work inside another job and not counting the skipped job is not a legal skip.

**Why this is not optional:** Catalog Ranker is a **batch pipeline**. Each stage reads the previous stage’s file. If `score` is required and `prepare` is skipped, `score` still needs `prepared_catalog.json` from a previous successful prepare whose inputs have not changed. B0 never takes this path (it always re-runs producers). B1 hydrates cache into the workload directory. Absence of a verified object is a cache miss, not a license to skip the consumer.

### Job cards (contract)

#### `branch_guard`

| | |
| --- | --- |
| **Purpose** | Enforce allowed promotions. |
| **Inputs** | Source ref, target ref. |
| **Outputs** | Policy verdict (`allowed`, `flow`). |
| **Depends on** | — |
| **Dependents** | `validate` (legal flows); `promote` (development→main). |
| **Invalidating changes** | Every workflow request. Always required. |
| **Flows** | All, including illegal. |

Allowed: `feature` / `custom` / `feature/*` / `custom/*` → `development`; `development` → `main`. Anything else (including feature→main) fails closed and must not publish or promote.

#### `validate`

| | |
| --- | --- |
| **Purpose** | Schema / fixture / config sanity. |
| **Inputs** | `fixtures/catalog.json`, `fixtures/personas.json`, `fixtures/model/ranker.json`; optional `configs/scoring_weights.json`; optional `configs/pipeline.json`. |
| **Outputs** | Validation report. |
| **Depends on** | `branch_guard` |
| **Dependents** | `test`, `ingest` |
| **Invalidating changes** | Fixture schema or presence; pipeline metadata; scoring overlay shape; most code/data PRs that can make fixtures unreadable. **Not** required for docs-only (S01), test-only (S02), or clean promote (S09). |
| **Flows** | Feature→dev; dirty/rebuild promote. |

#### `test`

| | |
| --- | --- |
| **Purpose (contract)** | Trust application and test code before shipping a pointer. |
| **B0 implementation note** | In-process ranker smoke; **not** the repo pytest suite and **not** a reader of `tests/**`. The contract follows the conceptual job (S02), not that shortcut. |
| **Inputs (contract)** | Application code, tests, dependencies, fixtures needed to execute those tests. |
| **Outputs** | Test report. |
| **Depends on** | `validate` |
| **Dependents** | `publish`; rebuild `promote`. |
| **Invalidating changes** | Application code (`src/agentic_cicd/ranker/{ingest,prepare,score,evaluate,package}.py` and related), `tests/**`, dependency metadata. **Not** strictly required for docs-only, catalog-only (S04), model-only (S06), pipeline-metadata-only (S08), overlay-only (S12), or clean promote (S09). |
| **Flows** | Feature→dev; dirty/rebuild promote when code trust is required. |

#### `ingest`

| | |
| --- | --- |
| **Purpose** | Materialize raw catalog and personas from fixtures. |
| **Inputs** | `fixtures/catalog.json`, `fixtures/personas.json`, ingest code. |
| **Outputs** | `raw_catalog.json`, copied personas, `dataset_manifest.json` (logical paths + SHA-256). |
| **Depends on** | `validate` |
| **Dependents** | `prepare` |
| **Invalidating changes** | Catalog fixture, personas fixture, ingest code, dependency metadata (conservative). |
| **Reusable when** | Dataset identity (catalog + personas hashes) is unchanged and a cached raw/manifest exists. |

#### `prepare`

| | |
| --- | --- |
| **Purpose** | Deterministic feature vectors from the raw catalog. |
| **Inputs** | Raw catalog, prepare code. |
| **Outputs** | `prepared_catalog.json`. |
| **Depends on** | `ingest` or a cached raw catalog with matching identity. |
| **Dependents** | `score` |
| **Invalidating changes** | Raw data identity, prepare code, dependency metadata (conservative). |

#### `score`

| | |
| --- | --- |
| **Purpose** | Rank the catalog per persona. Dominant cost (weight 10). |
| **Inputs** | Prepared catalog, personas, effective model (`fixtures/model/ranker.json` merged with `configs/scoring_weights.json` when present), scoring code. |
| **Outputs** | `predictions.json`. |
| **Depends on** | `prepare` or cached prepared data with matching identity. |
| **Dependents** | `evaluate` |
| **Invalidating changes** | Prepared data, personas preferences, frozen model, scoring overlay, scoring code, dependency metadata (conservative). |

**Hidden dependency:** `configs/scoring_weights.json` is a score input even though it lives under `configs/`. Treating `configs/**` as pipeline metadata (S08) is a false skip (S12).

#### `evaluate`

| | |
| --- | --- |
| **Purpose** | Metrics and predictions checksum. |
| **Inputs** | Predictions, prepared catalog, personas, evaluate code. |
| **Outputs** | `metrics.json` (includes `predictions_sha256`). |
| **Depends on** | `score` or cached predictions with matching identity. |
| **Dependents** | `package` |
| **Invalidating changes** | Predictions, evaluate code, dependency metadata (conservative). |

#### `package`

| | |
| --- | --- |
| **Purpose** | Content-addressed bundle and `artifact_id`. |
| **Inputs** | Predictions, metrics, dataset manifest, effective model, model path, optional overlay; `code_identity` over ranker sources + package version (D-018). `run_metadata` is excluded. |
| **Outputs** | Bundle directory + SHA-256 `artifact_id`. |
| **Depends on** | `evaluate` |
| **Dependents** | `publish`; rebuild `promote`. |
| **Invalidating changes** | Anything that changes the bundle payload: data, model, overlay, predictions, metrics, or hashed scoring-code identity. |

#### `publish`

| | |
| --- | --- |
| **Purpose** | Record the bundle as the development artifact. |
| **Inputs** | Packaged `artifact_id` and bundle. |
| **Outputs** | `registry/development.json`. |
| **Depends on** | `package` and `test`. |
| **Dependents** | Later `promote`. |
| **Invalidating changes** | A new bundle on feature→development. Must **not** be required when no new bundle is required (S01, S02, S08). |
| **Flows** | Feature→development only. |

#### `promote`

| | |
| --- | --- |
| **Purpose** | Point production at a validated artifact. |
| **Inputs** | Development pointer; on rebuild, the newly packaged `artifact_id`. |
| **Outputs** | `registry/production.json` (`artifact_id`, `validated_artifact_id`, `promote_mode`). |
| **Depends on** | Clean reuse: `branch_guard` only. Dirty rebuild: `branch_guard`, `package`, `test`. |
| **Dependents** | — |
| **Invalidating changes** | Every legal development→main request. |
| **Flows** | Development→main only. |

B0 today takes `promote_mode` as an **explicit caller input**. The future optimizer must **infer** clean vs dirty; it must not require a human to pass the answer.

---

## 3. Change impact model

Conceptual chain (not implemented):

```text
repository change
    → affected component(s)
        → invalidated artifact / output identity
            → required jobs
```

A job is required if it is the only correct way to (re)produce an invalidated output, to enforce policy, or to restore trust before writing an environment pointer.

### Components and typical paths

This map is the intended deterministic classification surface. It is **not** executable path-filter code.

| Component | Typical paths | Primary invalidated outputs |
| --- | --- | --- |
| Documentation | `README.md`, `docs/**`, other markdown with no runtime import | None |
| Tests | `tests/**` | Test report only |
| Pipeline metadata | `configs/pipeline.json` | Validation report only |
| Scoring overlay | `configs/scoring_weights.json` | Effective model, predictions, metrics, bundle |
| Catalog fixture | `fixtures/catalog.json` | Raw dataset, prepared data, predictions, metrics, bundle |
| Personas fixture | `fixtures/personas.json` | Raw dataset / personas, predictions, metrics, bundle |
| Frozen model | `fixtures/model/ranker.json` | Effective model, predictions, metrics, bundle |
| Ingest code | `src/agentic_cicd/ranker/ingest.py` | Raw dataset / manifest, then downstream if identity changes |
| Prepare code | `src/agentic_cicd/ranker/prepare.py` | Prepared data, then score→bundle |
| Score code | `src/agentic_cicd/ranker/score.py` | Predictions, then evaluate→bundle |
| Evaluate code | `src/agentic_cicd/ranker/evaluate.py` | Metrics, then bundle |
| Package / identity code | `src/agentic_cicd/ranker/package.py`, `identity.py` | Bundle identity |
| Dependencies | `pyproject.toml`, lockfiles | Conservative: treat every stage as invalidated |
| Orchestrator / CLI | `src/agentic_cicd/b0/**`, `cli.py` | No dedicated scenario; fail closed unless proven inert |
| Unknown / new path | anything not in this table | All legal jobs on the flow |

Personas-only, ingest-code-only, package-code-only, and orchestrator changes have **no dedicated S01–S14 row**. Until they do, the conservative mapping above is the contract.

### Worked impact (matches ground truth, does not replace it)

| Change class | Affected component | Invalidated outputs | Required jobs (feature→dev unless noted) |
| --- | --- | --- | --- |
| Docs only | Documentation | None | `branch_guard` |
| Tests only | Tests | Test report | `branch_guard`, `test` |
| Score code | Score code | Predictions, metrics, bundle | `branch_guard`, `validate`, `test`, `score`, `evaluate`, `package`, `publish` — reuse raw + prepared if cached |
| Catalog fixture | Catalog | Raw, prepared, predictions, metrics, bundle | `branch_guard`, `validate`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `publish` |
| Prepare code | Prepare code | Prepared, predictions, metrics, bundle | `branch_guard`, `validate`, `test`, `prepare`, `score`, `evaluate`, `package`, `publish` — reuse raw if cached |
| Model file | Frozen model | Predictions, metrics, bundle | `branch_guard`, `validate`, `score`, `evaluate`, `package`, `publish` |
| Dependencies | Dependencies | Unknown / all | Full feature→dev graph |
| Pipeline JSON | Pipeline metadata | Validation report | `branch_guard`, `validate` |
| Overlay weights | Scoring overlay | Predictions, metrics, bundle | `branch_guard`, `validate`, `score`, `evaluate`, `package`, `publish` |
| Evaluate code | Evaluate code | Metrics, bundle | `branch_guard`, `validate`, `test`, `evaluate`, `package`, `publish` — reuse predictions if cached |
| Unknown path | Unknown | Unknown | Full feature→dev graph |
| Clean promote | — | None (artifact still valid) | `branch_guard`, `promote` on development→main |
| Dirty score-like promote | Score inputs after validation | Predictions, metrics, bundle | `branch_guard`, `validate`, `test`, `score`, `evaluate`, `package`, `promote` on development→main |
| Illegal feature→main | Policy | — | `branch_guard` (fail); no publish/promote |

### Skip vs run (deterministic intent)

A future optimizer may skip a job only when it can exhibit a **checkable reason** that matches this graph, for example:

- output identity cannot change because no input component changed;
- a cached output with the same input identity is present;
- the job is not on this flow (`publish` on development→main, `promote` on feature→development);
- the flow is illegal and only `branch_guard` may run.

Absence of a checkable reason is **not** a skip reason.

---

## 4. Safety model

Correctness remains a **hard constraint**. Maximizing skips is not a goal.

### False skip

A **false skip** is a job listed in that scenario’s `required_jobs` that was neither `executed` nor `failed`. That is a **safety failure**. Extra executed jobs are **unnecessary**, not a safety failure.

The current harness (`compare_run`) already uses this definition. Keep it.

### Fail closed

```text
UNKNOWN or AMBIGUOUS impact  →  RUN rather than SKIP
```

Conditions that **must** cause conservative extra execution (run jobs that a perfect oracle might skip):

1. **Unclassified path** — the change is not in the known component map (S14).
2. **Dependency metadata** — runtime effect cannot be proven local (S07).
3. **Hidden / adversarial dependency** — a path that looks inert but feeds a job input (S12 vs naive `configs/**` → validate-only).
4. **Unproven clean promote** — dirty vs clean cannot be shown from the available change set; rebuild rather than reuse.
5. **Missing or unverified cache** — a skip that depends on a reused intermediate is illegal if that object is absent or its input identity cannot be checked.
6. **Ambiguous multi-file or novel interaction** — the classifier cannot name a single component.
7. **Insufficient confidence** — including any future agent proposal that the verifier cannot check.

Skip is allowed only with an explicit, checkable reason that matches the graph (D-016).

### Other safety invariants

- A required job must never be skipped.
- Illegal promotion must fail `branch_guard` and must not write `publish` / `promote` pointers.
- Clean promote (S09): production `artifact_id` **equals** the validated development `artifact_id`.
- Dirty promote (S10): score (and the other required rebuild jobs) must run; production receives the **new** artifact; treating it as clean is a safety failure.
- Failed required jobs block dependents; they must not write environment pointers (already true in B0).
- Determinism: identical artifact inputs produce the same `artifact_id` (D-018).

A configuration that false-skips **may not** claim an optimization win on the suite.

---

## 5. Promotion model

Two different problems. Do not collapse them.

```text
feature / custom  →  development     (build and maybe publish)
development       →  main            (promote a validated artifact)
feature           →  main            (illegal)
```

### feature / custom → development

- Purpose: validate the change and, if the bundle payload is affected, produce and **publish** a development artifact.
- Optimizer may skip jobs whose outputs remain valid under §3–§4.
- Must publish when a new bundle is required.
- Must not be required to publish when no artifact inputs changed (S01, S02, S08).
- This flow never runs `promote`.

### development → main

- Purpose: point production at a **validated** artifact. Production is not “run the recipe again and hope it matches.”
- This flow never runs `publish`.

#### Clean promote

A promote is **clean** when all of the following hold:

1. Source is `development` and target is `main`.
2. A development pointer with an `artifact_id` exists.
3. No change in the promote context invalidates bundle inputs (data, model, overlay, hashed scoring/eval/package code, personas).
4. Therefore the already-validated development `artifact_id` is still the correct production object.

Required jobs: `branch_guard`, `promote`.  
Production `artifact_id` **must equal** the development `artifact_id`. Rebuilding is unnecessary work. A rebuild that produced a *different* id would be a symmetry failure.

B0 implements this only when the caller passes `promote_mode=reuse`. The optimizer must infer cleanliness.

#### Dirty promote

A promote is **dirty** when a change after the validated development revision **invalidates** at least one artifact input.

Required jobs: at least the jobs needed to rebuild invalidated outputs, re-package, and promote. For the suite’s scoring-behavior dirty case (S10): `branch_guard`, `validate`, `test`, `score`, `evaluate`, `package`, `promote`.

Production must receive the **new** `artifact_id`. Reusing the stale development pointer is a false skip of the rebuild (and an identity error if the suite requires `must_differ_from_seed`).

B0 implements this when the caller passes `promote_mode=rebuild` (default). The optimizer must infer dirtiness.

#### Artifact identity

`artifact_id` = lowercase hex SHA-256 of canonical JSON of `{predictions, metrics, dataset_manifest, model_manifest, model, code_identity}` (D-018). Overlay hash is included in `model_manifest` when `configs/scoring_weights.json` exists.

Identity is how clean vs dirty is *checked* after the fact. It is not, by itself, B0’s decision procedure.

#### Current B0 pointer behavior (do not silently change)

On dirty rebuild, B0 writes `production.json` to the **new** id and records `validated_artifact_id` as the previous development id. It does **not** rewrite `development.json`. S10 does not require that rewrite. Whether a later optimizer should also advance the development pointer is an open question (§8).

B0 does **not** walk git ancestry. “What changed after validation” is represented in the suite by `files_changed` / `apply`, not by commits.

---

## 6. Benchmark relationship

S01–S14 **can and should** remain the evaluation contract for future optimized implementations.

| Kind | Role | Mutable in Phase 2.1? |
| --- | --- | --- |
| `benchmark/scenarios.json` `required_jobs` | Ground truth (minimum correct set) | **No** |
| B0 execution | Unoptimized baseline | **No** |
| E-002 totals | Measured B0 reference | Historical record only |
| This contract | How an optimizer must interpret that suite | Documentation only |

Ground truth was written from the Phase 1.3 contract, not generated by B0. Extra jobs are unnecessary, not incorrect. The same scenarios, fixtures, and cost weights must be used for B0, a deterministic optimizer, and a later agent.

The benchmark runner today only invokes B0 (`system=baseline`) and maps development→main `promote_mode` from **explicit** scenario fields: empty `apply` → `reuse` (S09); non-empty `apply` → `rebuild` (S10). That mapping is not change detection and is not available to a real optimizer.

### Clarifications (documented, not silently “fixed”)

These are ambiguities or dual representations. They do **not** authorize edits to `scenarios.json`.

1. **`files_changed` vs `apply`.** Several scenarios declare a conceptual path and apply a proxy mutation:
   - S01: `files_changed` is README/ROADMAP; `apply` writes `docs/NOTE.md`.
   - S02: `files_changed` is `tests/test_catalog_ranker.py`; `apply` writes `tests/extra_note.py`.
   - S03 / S10: `files_changed` is `score.py`; `apply` is `set_year_weight` on the overlay so the suite does not patch installed package sources.
   - S05 / S13: `apply` overwrites workspace `prepare.py` / `evaluate.py` with a marker. B0 still executes the **installed** modules, so B0’s `artifact_id` may not change. Ground truth still requires the rebuild jobs and does **not** require `must_differ_from_seed`.
   - S07: `apply` writes a stub `pyproject.toml` in the workspace. B0 does not read it. Ground truth still requires the full graph.
   - S11: `files_changed` lists `score.py` but `apply` is empty; the illegal flow makes content irrelevant.

   **Implication:** the evaluation signal is the **declared change class** (`files_changed` + scenario id/rationale), not “did B0’s installed code observe a different hash.” An optimizer that only reverse-engineers B0 observability can false-skip S05/S13 against ground truth.

2. **S03/S10 scoring proxy.** The physical mutation is the same class of file as S12 (`scoring_weights.json`). The *intended* class for S03/S10 is scoring-behavior change. Both interpretations still require `score`. Do not collapse S03 and S12; S12 exists to catch naive `configs/**` filters.

3. **Cached intermediates.** S03/S05/S06/S13 omit upstream jobs on the assumption that raw/prepared/predictions can be reused. B0 has no such cache. A future optimizer must provide one or it cannot legally take those skips (§2 reuse rule).

4. **`test` job vs pytest.** S02 requires the `test` job when tests change. B0’s `test` does not read `tests/**`. The contract is the job name in ground truth, not B0’s smoke implementation.

5. **`validate` is not always-on.** S01, S02, and S09 do not require it. An optimizer may still run it (unnecessary, not a false skip).

6. **S04/S06/S12 do not require `test`.** Data, model, and overlay changes are not defined as code-trust events. Conservative extra `test` is allowed.

7. **Uncovered change classes.** No dedicated row for personas-only, ingest.py, package.py, identity.py, or B0/CLI. Until added, fail closed (§3).

8. **`blocked_jobs`.** Every scenario lists `[]`. Failure propagation is covered by B0 unit tests, not by S01–S14.

9. **Harness gap.** Measuring a non-B0 system will need a `system` hook. Not implemented. Do not treat today’s `python -m agentic_cicd benchmark` output as an optimized result.

---

## 7. Deterministic vs agent boundary

The final architecture must not blindly delegate safety-critical decisions to an LLM if deterministic verification can enforce them.

### Deterministic infrastructure / rules (safety floor)

Responsible for:

- the job graph, cost weights, and legal flows;
- `branch_guard`;
- artifact identity (D-018);
- known path → component → invalidated output → required job mapping;
- conservative expansion (unknown, dependencies, missing cache);
- inferring clean vs dirty promote when the change set is fully classified;
- verifying a proposed skip set: every skipped job must have a checkable reason; no required job may be absent;
- environment pointer writes only after required producers succeed;
- the S01–S14 comparison harness and the false-skip gate.

A deterministic optimizer that only implements this floor is a **successful Phase 2 outcome** even if an agent never beats it on the suite.

### Agent (later; not in Phase 2.1)

Candidate responsibilities — only where rules are incomplete:

- classify novel or multi-file changes the map does not name;
- detect hidden dependencies similar in *spirit* to S12 when paths are not pre-listed;
- explain skip/run decisions in natural language;
- propose graph or rule updates after a conservative run;
- assist dirty-promote judgment when history is messy (still subject to the verifier).

The agent must not be the only function that may say `SKIP`.

### Verification / safety mechanisms

Always deterministic, even if an agent proposes the plan:

- required-job / skip-reason checker;
- `branch_guard`;
- clean-promote identity equality; dirty-promote identity inequality when the suite requires it;
- UNKNOWN → RUN;
- suite gate: any false skip fails the experiment;
- observability: `skip_reason` is null if executed and checkable if skipped ([PROBLEM_FRAMING.md](PROBLEM_FRAMING.md) §11).

```text
agent (optional) proposes a job set
        ↓
deterministic verifier accepts, or adds jobs, or rejects the skip
        ↓
runner executes the verified set
        ↓
benchmark judges against required_jobs
```

If the agent and the deterministic optimizer produce the same decisions on S01–S14, the agent has not yet demonstrated additional value.

---

## 8. Unresolved design questions

These are open on purpose. Phase 2.1 does not resolve them by implementing code.

1. **Optimizer input signal.** **Closed for B1 (D-028):** `files_changed ∪ apply` paths. `None` means unknown.
2. **Intermediate cache.** **Closed for B1 (D-027):** last-known-good warm + SHA-256 identity.
3. **First deterministic algorithm.** **Closed (D-026):** impact graph, not path filters.
4. **Dirty promote and the development pointer.** B0 leaves `development.json` stale after a dirty rebuild. Should an optimizer advance it?
5. **Git ancestry.** Specified conceptually; B0 and the suite use explicit change lists. **Working-tree Git detection** (clone → edit → run B1) was investigated in Phase 3.2 (D-053): it belongs in an optional adapter *before* B1, not inside B1, and must **not** replace D-028 (S03/S05/S10/S13 declared classes are not a workspace diff). **Not implemented** for this submission. Ancestry-for-promote (history since last validation) remains a separate open question.
6. **Personas and other uncovered paths.** Add scenarios, or keep fail-closed mapping only?
7. **`test` implementation.** Keep B0 smoke, or later run real pytest, without changing S02 ground truth?
8. **How the harness invokes a non-B0 system.** **Closed for B1:** `--system baseline|optimized|compare`.
9. **Agent model, tools, prompts, and input context** (D-OPEN-07, D-OPEN-08).
10. **Evaluate quality-gate thresholds** (D-OPEN-16) — still not a build gate.
11. **GitHub Actions vs local runner** (D-OPEN-12) — **closed for submission (D-052):** local runner only; GHA is not required.
12. **Whether `validate` should become always-on** in an implementation for engineering simplicity (would add unnecessary cost vs S01/S02/S09).

---

## 9. What Phase 2.1 explicitly did not do

Phase 2.1 was contract-only. Phase 2.2 implemented B1 without an agent, without changing B0 scheduling or S01–S14, and without treating E-002 as an optimization result.
