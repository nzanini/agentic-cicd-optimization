# Decision log

Decisions, deferred questions, and rejected approaches. Evidence belongs in the experiment log when an experiment exists; this file records the **choice** and **why**.

---

## How to log a decision

```md
## [D-XXX] YYYY-MM-DD — short title

- **Decision ID:** D-XXX
- **Date:** YYYY-MM-DD
- **Status:** accepted | deferred | rejected | superseded
- **Context:**
- **Decision:**
- **Rationale:**
- **Evidence:** (experiment IDs, or `not tested`)
- **Alternatives considered:**
- **Consequences / follow-up:**
```

---

## Accepted

### [D-001] 2026-08-28 — Documentation-first foundation before any system design

- **Decision ID:** D-001
- **Date:** 2026-08-28
- **Status:** accepted
- **Context:** Phase 1.1 of an incremental hackathon project. The repo was empty except for git metadata and a GitHub remote.
- **Decision:** Create only project documentation and repository hygiene (`README`, `docs/*`, `LICENSE`, `.gitignore`). Do not implement pipeline, agent, benchmark, or evaluation code in this step.
- **Rationale:** The evaluation criteria emphasize evidence, measured improvement, and reproducibility. Those require a durable record of hypothesis vs current state vs later changes. Building the system before that record exists would mix exploration with untracked decisions.
- **Evidence:** not tested (process decision, not an empirical result)
- **Alternatives considered:** Scaffold application directories (`src/`, workflow files, empty agent stubs). Rejected as premature architecture.
- **Consequences / follow-up:** Later phases add code only when explicitly requested.

### [D-002] 2026-08-28 — Treat the CI/CD agent idea as a hypothesis, not a locked design

- **Decision ID:** D-002
- **Date:** 2026-08-28
- **Status:** accepted
- **Context:** The working idea includes change-aware job selection and, possibly, promotion/environment symmetry.
- **Decision:** Document both ideas as a **working hypothesis**. Do not freeze job lists, dependency graphs, branch policy, artifact strategy, or agent architecture.
- **Rationale:** Pipeline shape, jobs, and metrics should come from later evidence. Pretending they are known now would make the roadmap look more finished than the project is.
- **Evidence:** not tested
- **Alternatives considered:** Specify a concrete job graph (validate → test → build → publish → deploy) in Phase 1.1. Deferred; that is a later design decision.
- **Consequences / follow-up:** Example job names in the README were illustrative only in Phase 1.1. Phase 1.3 records a proposed topology and contract (`PROBLEM_FRAMING.md`, D-010–D-015) without implementing them.

### [D-003] 2026-08-28 — Prefer a local, reproducible simulation over paid infrastructure

- **Decision ID:** D-003
- **Date:** 2026-08-28
- **Status:** accepted (constraint; implementation TBD)
- **Context:** Hackathon reproducibility and cost.
- **Decision:** The eventual demo should run without requiring real AWS, Airflow, SageMaker, Kubernetes, or other paid/heavy infrastructure. Mock or simulate expensive jobs as needed.
- **Rationale:** Another person must be able to reproduce the work from a clean environment.
- **Evidence:** not tested
- **Alternatives considered:** A “realistic” cloud pipeline. Rejected as incompatible with the reproducibility goal unless a later, evidence-based exception is recorded.
- **Consequences / follow-up:** Exact local toolchain (Docker, GitHub Actions, language, etc.) is still open. Phase 1.2 later chose Python (D-006); in-repo Docker remains deferred.

### [D-004] 2026-08-28 — MIT license for a public hackathon repository

- **Decision ID:** D-004
- **Date:** 2026-08-28
- **Status:** accepted
- **Context:** Public GitHub repository for a hackathon.
- **Decision:** Use the MIT License.
- **Rationale:** Permissive, short, widely understood by judges and cloners. Appropriate when no org policy requires otherwise.
- **Evidence:** not tested (legal/process choice)
- **Alternatives considered:** Apache-2.0 (also reasonable; not chosen for simplicity). Unlicense / proprietary (poor fit for a public hackathon write-up).
- **Consequences / follow-up:** Revisit if an organizer or teammate requires a different license.

### [D-005] 2026-08-28 — Baseline before agent claims

- **Decision ID:** D-005
- **Date:** 2026-08-28
- **Status:** accepted (methodology; baseline not yet defined)
- **Context:** Agent-first methodology required by the project brief.
- **Decision:** No claim of agent improvement is allowed until a baseline exists and a comparable experiment is logged.
- **Rationale:** Measured improvement is an evaluation criterion. Fabricated or premature deltas would invalidate the evidence trail.
- **Evidence:** not tested
- **Alternatives considered:** Build the agent first and backfill a baseline. Rejected; that inverts the intended methodology.
- **Consequences / follow-up:** Phase 1.3 specified B0 (D-014). Implementation remains a later phase.

### [D-006] 2026-08-28 — Python 3.11+ with pyproject.toml as the implementation foundation

- **Decision ID:** D-006
- **Date:** 2026-08-28
- **Status:** accepted
- **Context:** Phase 1.2 asked for a maintainable Python foundation and a clear dependency-management approach, without implementing the optimizer.
- **Decision:** Use CPython **3.11+** (recommended 3.12 via `.python-version`), a `src/agentic_cicd` package, and `pyproject.toml` as the single source of project metadata and dependencies. Runtime `dependencies` stay empty. Dev extras: pytest and ruff. Standard library `venv` + pip; no Poetry/Pdm/uv requirement.
- **Rationale:** PEP 621 `pyproject.toml` is portable and enough for an empty runtime dependency set. A `src/` layout keeps tests from accidentally importing an uninstalled tree. Pinning a package manager beyond pip would add a tool judges may not have.
- **Evidence:** toolchain verification in a clean Python 3.12 environment (see I-002); not an optimization experiment
- **Alternatives considered:** Poetry or uv lockfiles (stronger pins; extra installer). Flat layout without `src/`. Adding a Dockerfile as the primary env (rejected for this phase; local venv is enough and there is no application image to build).
- **Consequences / follow-up:** D-OPEN-11 is resolved for language. Remaining stack choices (Docker in-repo, GitHub Actions, libraries) stay open.

### [D-007] 2026-08-28 — Foundation tests and ruff only; no application tests or Docker image

- **Decision ID:** D-007
- **Date:** 2026-08-28
- **Status:** accepted
- **Context:** Phase 1.2 allows basic tests and code-quality config, and Docker only if there is a foundation-level reason. It forbids fake application tests and a final application image.
- **Decision:** Add one import smoke test and ruff (lint + format) configured in `pyproject.toml`. Do not add mypy, pre-commit, GitHub Actions, or a Dockerfile in this phase.
- **Rationale:** Pytest proves the package is installable. Ruff is one tool for lint and format. A Docker image would imply an application runtime that does not exist yet. Mypy/pre-commit add moving parts before there is code to type-check.
- **Evidence:** not an experiment; see I-002 verification
- **Alternatives considered:** Zero tests (weaker check that packaging works). A `python:3.12` Dockerfile committed to the repo (deferred).
- **Consequences / follow-up:** Application tests wait until there is application behavior.

### [D-008] 2026-08-29 — Separate Cursor conversations per major phase

- **Decision ID:** D-008
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Incremental hackathon work; long chats drift.
- **Decision:** Use separate Cursor conversations for major phases. Log phase, purpose, model, Cursor mode, important instructions, and resulting decisions. Do not store full transcripts unless asked.
- **Rationale:** Keeps each stage focused; the repo docs remain the source of truth.
- **Evidence:** not tested (process)
- **Alternatives considered:** One continuous conversation for the whole project.
- **Consequences / follow-up:** I-003 was produced in a new Agent conversation (Cursor Grok 4.6) from the Phase 1.3 brief. Phase 2.1 restates this as D-022 (reset at phase boundaries; repo docs are the source of truth).

### [D-009] 2026-08-29 — Optimization subject to correctness

- **Decision ID:** D-009
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 1.3 problem statement.
- **Decision:** The goal is to minimize execution time and unnecessary work **without** incorrectly skipping a required job. Skip-count is not the objective. False skips disqualify a claimed suite win.
- **Rationale:** User value is faster correct pipelines, not maximum skips.
- **Evidence:** not tested
- **Alternatives considered:** Maximize skipped jobs; treat correctness as a soft score mixed into one metric.
- **Consequences / follow-up:** Primary metric is gated (D-015).

### [D-010] 2026-08-29 — Catalog Ranker as CI workload, not an ML project

- **Decision ID:** D-010
- **Date:** 2026-08-29
- **Status:** accepted (design; not implemented)
- **Context:** Need a small realistic DAG without training or paid ML infra.
- **Decision:** Use a Catalog Ranker: vendored movie catalog, synthetic personas, frozen weights file, deterministic rankings and JSON artifacts.
- **Rationale:** Judges can inspect top-N lists. The graph has data, model, score, eval, package, and promote — enough skip structure. No training, no quality chase.
- **Evidence:** not tested
- **Alternatives considered:** Train a recommender; large pre-trained download; news/weather live APIs; generic “jobs A–E” with no workload (weaker story).
- **Consequences / follow-up:** Implemented in Phase 1.4 as `weighted_genre_dot` JSON weights (`fixtures/model/ranker.json`). No training libraries.

### [D-011] 2026-08-29 — Fixture-first data; no live API in the benchmark

- **Decision ID:** D-011
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Public APIs were considered for realistic ingestion.
- **Decision:** Ingest is a real job. Default and benchmark I/O are source-controlled fixtures. Live APIs are not required and must not be required to reproduce results. Optional API adapter is out of scope until explicitly requested.
- **Rationale:** Keys, rate limits, and catalog drift would break judge reproduction. The ingest *job* is what creates skip opportunities.
- **Evidence:** not tested (comparison is analytical; see `PROBLEM_FRAMING.md` §3)
- **Alternatives considered:** Live TMDB/OMDb (auth); live Gutendex (drift + network); runtime MovieLens download (network/overkill).
- **Consequences / follow-up:** Phase 1.4 created `fixtures/catalog.json`, `fixtures/personas.json`, and `fixtures/model/ranker.json`.

### [D-012] 2026-08-29 — Ten-job topology

- **Decision ID:** D-012
- **Date:** 2026-08-29
- **Status:** accepted (design; not implemented)
- **Context:** D-OPEN-02.
- **Decision:** Jobs: `branch_guard`, `validate`, `test`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `publish` (feature→dev), `promote` (dev→main). Cost weights 1–10 with `score` dominant. No extra deploy/build jobs in v1.
- **Rationale:** Small enough to explain; large enough that docs-only, data-only, model-only, eval-only, and clean promote skip different suffixes of the DAG.
- **Evidence:** not tested
- **Alternatives considered:** Longer lists (image build, cloud deploy); collapsing evaluate into score (loses S13); collapsing publish/promote (harder ground truth).
- **Consequences / follow-up:** Ground-truth table in `PROBLEM_FRAMING.md` §7.

### [D-013] 2026-08-29 — Branch policy and artifact identity

- **Decision ID:** D-013
- **Date:** 2026-08-29
- **Status:** accepted (design; not implemented)
- **Context:** D-OPEN-04, D-OPEN-05.
- **Decision:** Only `feature → development` and `development → main`. Feature→main fails `branch_guard`. Symmetry = same job definitions and the same content-hashed bundle on a clean promote. Dirty promote must rebuild affected jobs.
- **Rationale:** Matches the intended promotion discipline; makes “skip score on clean promote” a real, testable win.
- **Evidence:** not tested
- **Alternatives considered:** Allow feature→main; rebuild-always on main as the optimized path.
- **Consequences / follow-up:** Hash algorithm chosen in D-018. Promote/publish jobs are still not implemented.

### [D-014] 2026-08-29 — Baseline B0 is always-run-all legal jobs

- **Decision ID:** D-014
- **Date:** 2026-08-29
- **Status:** accepted (definition; not implemented)
- **Context:** D-OPEN-06.
- **Decision:** B0 runs every job legal for the flow (full rebuild on development→main). B0 still rejects illegal promotions. Path-filter B1 is optional later, same scenarios.
- **Rationale:** Honest naive pipeline; produces the same artifact types; easy to implement and compare.
- **Evidence:** not tested
- **Alternatives considered:** Path filters as the only baseline (deferred as B1).
- **Consequences / follow-up:** No B0 timings exist.

### [D-015] 2026-08-29 — Primary metric is gated suite simulated duration

- **Decision ID:** D-015
- **Date:** 2026-08-29
- **Status:** accepted (definition; not measured)
- **Context:** D-OPEN-09.
- **Decision:** Primary metric = sum of executed job cost weights across S01–S14. Report reduction vs B0 only if false-skip rate is 0 and S11 does not promote. Safety metrics stay separate from optimization metrics. Wall-clock and skip counts are secondary.
- **Rationale:** Encodes user wait-time without unreproducible wall-clock as the headline number; blocks unsafe “wins.”
- **Evidence:** not tested
- **Alternatives considered:** Primary = skip count; primary = wall-clock only; blend safety and speed into one score.
- **Consequences / follow-up:** No numbers until an experiment is logged.

### [D-016] 2026-08-29 — Uncertain dependency ⇒ run the job

- **Decision ID:** D-016
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** D-OPEN-14.
- **Decision:** If the system cannot confidently show a job is not required, it must execute it (S14 = all feature→dev jobs).
- **Rationale:** Fail closed. A silent skip is worse than extra work.
- **Evidence:** not tested
- **Alternatives considered:** Skip when unsure; ask a human at runtime (not reproducible for the suite).
- **Consequences / follow-up:** Agent design must expose skip reasons (observability contract).

### [D-017] 2026-08-29 — Fixtures in git; run outputs are not source

- **Decision ID:** D-017
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Reproducibility and artifact storage.
- **Decision:** Fixtures, scenario definitions, and expected required-job sets belong in git. Generated predictions, bundles, and run metrics go to `outputs/` or CI artifacts, not the source tree.
- **Rationale:** Judges need pinned expected answers; they should not need a repo polluted with run timestamps.
- **Evidence:** not tested
- **Alternatives considered:** Commit every workflow output (rejected).
- **Consequences / follow-up:** `.gitignore` already ignores `outputs/`. Phase 1.4 writes generated artifacts there.

### [D-018] 2026-08-29 — SHA-256 canonical JSON artifact id

- **Decision ID:** D-018
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** D-013 left the hash algorithm open. Phase 1.4 needs a minimal identity so two local runs can be compared and later promotes can match.
- **Decision:** `artifact_id` = lowercase hex SHA-256 of canonical JSON of `{predictions, metrics, dataset_manifest, model_manifest, model, code_identity}`. Canonical form uses `sort_keys=True` and compact separators. `run_metadata` is excluded. `code_identity` hashes the ranker source files plus package version.
- **Rationale:** Stdlib only, stable across machines, easy to inspect. Excluding timestamps keeps identity deterministic.
- **Evidence:** verified by tests (`test_repeated_runs_are_equivalent`, `test_model_change_changes_artifact_id`); not a benchmark experiment
- **Alternatives considered:** SHA-1 (weaker); hashing pretty-printed files (whitespace-sensitive); including `run_id` (would break determinism); zip/tar merkle (more moving parts).
- **Consequences / follow-up:** Phase 1.6 manifests use logical paths (`catalog.json`, `model/ranker.json`), not absolute workspace paths, so artifact ids are portable. Overlay hash is included when `configs/scoring_weights.json` exists.

### [D-019] 2026-08-29 — Local sequential B0 runner, no GitHub Actions

- **Decision ID:** D-019
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 1.5. B0 must be executable without paid infra.
- **Decision:** Implement B0 as an in-process Python orchestrator. Sequential topological execution. Simulated cost = Phase 1.3 weights (counter, no sleep). Wall-clock recorded separately. No GitHub Actions in this phase. `publish`/`promote` depend on both `package` and `test`. Promote originally rebuilt, then required the new id to match the development pointer. Feature/custom prefixes and `development`→`main` are the only allowed flows.
- **Rationale:** Matches D-003 and D-014. Fan-in on test avoids publishing after a failed test. The original identity-match-on-rebuild rule was intended as safety, not skip-the-rebuild optimization; D-021 later corrected it so dirty promote can accept a new id.
- **Evidence:** unit tests in `tests/test_b0.py`; not a suite benchmark
- **Alternatives considered:** GitHub Actions now (not required); sleeping to fake duration; skipping rebuild on promote (that is later optimization); path filters (B1).
- **Consequences / follow-up:** D-OPEN-06 and D-OPEN-17 closed for B0. GHA remains optional (D-OPEN-12).

### [D-020] 2026-08-29 — S01–S14 ground truth is independent of B0

- **Decision ID:** D-020
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 1.6 benchmark suite.
- **Decision:** Encode Phase 1.3 required-job sets in `benchmark/scenarios.json`. The runner measures B0 against that file. Extra B0 jobs are unnecessary, not failures. S12 uses a real `configs/scoring_weights.json` overlay. S03/S10 apply a year_weight overlay as a scoring-behavior proxy so the suite does not patch installed package sources. B0’s promote-must-match-dev rule may fail **S10**; that is recorded, not hidden, and B0 is not changed to fit the suite.
- **Rationale:** The benchmark must not be fitted to B0. S12 must be a real dependency or path filters would look correct by accident.
- **Evidence:** suite execution (E-001 / I-006); not an optimized comparison
- **Alternatives considered:** Derive expected jobs from B0 (rejected). Fake S12 by editing `ranker.json` while listing `configs/` (rejected).
- **Consequences / follow-up:** Optimizer later uses the same JSON. The S10-may-fail note is historical; B0 promote was corrected in D-021 without changing this ground truth.

### [D-021] 2026-08-29 — B0 promote honors clean reuse and dirty rebuild

- **Decision ID:** D-021
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 1.6 / E-001 showed S10 failing because `job_promote` rejected a rebuilt artifact whose id differed from the development pointer. The Phase 1.3 contract already required dirty promote to succeed with a new validated artifact (S10) and clean promote to reuse the same id (S09). That mismatch was a baseline correctness defect, not an optimization opportunity.
- **Decision:** Correct B0. `promote_mode` is an explicit input: `reuse` schedules only `branch_guard` + `promote` and copies the development artifact id; `rebuild` (default) runs the full legal development→main graph and promotes the new artifact even if the id changed. The benchmark maps empty `apply` → `reuse` and non-empty `apply` → `rebuild` for development→main. Do not infer mode from file diffs. Do not change S10 ground truth. Do not add B1, path filters, or an agent.
- **Rationale:** Weakening S10 to “must fail if id changed” would hide a contract bug. Teaching B0 to inspect files would be premature change detection. An explicit mode keeps B0 naive while matching the documented promotion rules.
- **Evidence:** E-002; focused tests in `tests/test_b0.py`
- **Alternatives considered:** Keep the reject-new-id rule and change S10 expected status (rejected: weakens correctness). Infer dirty vs clean by hashing fixtures (rejected: change detection). Always rebuild and only accept the new id (would still waste work on S09 and miss the clean-promote contract).
- **Consequences / follow-up:** Refines the D-019 identity-match rule and the D-014 “always rebuild on main” wording for the explicit clean case. D-020’s independent ground truth stands. E-001 is preserved as history.

### [D-022] 2026-08-29 — Repository docs are the source of truth across reset chats

- **Decision ID:** D-022
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** The project uses multiple Cursor chats across major phases (D-008). Phase 2 starts in a new conversation. Conversational memory is not a reliable record.
- **Decision:** Cursor chat context is **intentionally reset** at major phase boundaries. Each chat must begin with enough **repository-based** context to understand the current state independently. The repository documentation — not the previous chat transcript — is the source of truth. Important decisions made during a chat must be persisted into `docs/` (and code when implementation is in scope). Do not rely on conversational memory for critical project decisions.
- **Rationale:** Reproducibility and engineering process. A judge or a later chat must reconstruct “why” from the repo. Long chats drift; transcripts are not the evidence trail.
- **Evidence:** not tested (process)
- **Alternatives considered:** One continuous conversation for the whole project (rejected in D-008). Treating the prior chat as canonical (rejected: not reviewable, not cloneable).
- **Consequences / follow-up:** Phase 2.1 records the optimization contract in `docs/OPTIMIZATION_CONTRACT.md` and this log. Later chats must read the repo first.

### [D-023] 2026-08-29 — Compare B0 → deterministic optimizer → agent

- **Decision ID:** D-023
- **Date:** 2026-08-29
- **Status:** accepted (methodology; only B0 exists)
- **Context:** Phase 2 must eventually show what an agent improved. Jumping from B0 to an unexplained agent would hide whether the gain is rules or the model.
- **Decision:** The architecture will allow comparison of **B0**, then a **deterministic optimized solution**, then an **agentic** optimized solution. The deterministic layer is the safety floor. The agent must later demonstrate meaningful additional capability, not merely replace a few `if` statements with an LLM call. Do not implement the optimizer or the agent in Phase 2.1.
- **Rationale:** The project question is “what exactly did the agent improve?” That requires a strong non-agent baseline after B0.
- **Evidence:** not tested
- **Alternatives considered:** B0 → agent directly (rejected: uninterpretable). Agent as the first optimizer (rejected: safety-critical skips would start in an LLM).
- **Consequences / follow-up:** Phase 2.2 (not started) is the deterministic optimizer. Agent work stays later.

### [D-024] 2026-08-29 — Adopt the Phase 2.1 optimization contract without implementing it

- **Decision ID:** D-024
- **Date:** 2026-08-29
- **Status:** accepted (contract; not implemented)
- **Context:** Phase 2.1 asked for a formal optimization contract before any optimizer.
- **Decision:** `docs/OPTIMIZATION_CONTRACT.md` is the source of truth for the future optimizer’s job dependency model, change-impact chain, safety model (UNKNOWN → RUN), promotion semantics (feature→dev vs clean/dirty dev→main), optimization objective (unchanged gated simulated cost, D-015), S01–S14 relationship, and deterministic/agent/verifier boundary. Skip permission is owned by deterministic verification even if an agent later proposes a job set. Do not change B0 or `benchmark/scenarios.json`.
- **Rationale:** Implementation without a contract would mix exploration with untracked skip rules. The Phase 1.3 document remains the evaluation contract; Phase 2.1 adds the optimizer-facing interpretation.
- **Evidence:** not tested (design). Existing tests still measure B0 only.
- **Alternatives considered:** Implement change detection immediately (rejected: brief forbids it). Change the cost model (rejected: no compelling documented reason). Weaken S05/S13 because B0 executes installed modules (rejected: ground truth is conceptual).
- **Consequences / follow-up:** Phase 2.2 must implement against this contract. Open questions stay in `OPTIMIZATION_CONTRACT.md` §8.

### [D-025] 2026-08-29 — Freeze S01–S14; document ambiguities instead of editing them

- **Decision ID:** D-025
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Several scenarios use a conceptual `files_changed` path and a proxy `apply` mutation (S03/S10 overlay; S05/S13 workspace markers). B0 does not always observe the conceptual file.
- **Decision:** S01–S14 remain the evaluation contract for future optimized systems. Do not silently change ground truth. Document dual representations and uncovered change classes in `OPTIMIZATION_CONTRACT.md` §6. The evaluation signal is the **declared change class**, not “did B0’s installed code observe a different artifact hash.”
- **Rationale:** Fitting the suite to B0 observability would hide false skips (especially S05/S13) and invert D-020.
- **Evidence:** inspection of `benchmark/scenarios.json` vs B0/ranker implementation; not a new suite run
- **Alternatives considered:** Rewrite S03/S10 `files_changed` to the overlay path (rejected: would blur S12). Drop S05/S13 artifact requirements (rejected: silent contract change).
- **Consequences / follow-up:** A later harness must pass change information into the optimizer. How (`files_changed` vs workspace diff) is still open (§8 of the contract). Closed for B1 in D-028 (union).

### [D-026] 2026-08-29 — B1 is an impact graph, not a filename filter

- **Decision ID:** D-026
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 2.2. D-OPEN-15 left B1 as optional path filters.
- **Decision:** Implement B1 as a deterministic component → artifact → job planner. `configs/scoring_weights.json` is classified as a scoring overlay (invalidates predictions), not as pipeline metadata. No scenario IDs in optimizer code. No LLM.
- **Rationale:** Superficial `configs/**` filters would false-skip `score` on S12. The contract already named the hidden dependency.
- **Evidence:** E-003; `tests/test_b1.py`
- **Alternatives considered:** Path-filter B1 only (rejected: fails S12). Jump to an agent (rejected: D-023).
- **Consequences / follow-up:** Closes D-OPEN-15 as “implemented as impact graph.”

### [D-027] 2026-08-29 — Last-known-good cache with identity checks

- **Decision ID:** D-027
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Legal skips of ingest/prepare/score need reusable intermediates. Existence is not validity.
- **Decision:** Warm a local cache from pre-apply fixtures (previous-build state). Reuse only when stored SHA-256 input identity matches current fixtures. Missing or stale cache → run the producer. Do not write empty stubs.
- **Rationale:** Matches the contract reuse rule without a production artifact store.
- **Evidence:** E-003 (S03/S05/S06/S10/S13 skip unused producers); focused cache tests
- **Alternatives considered:** Always run producers (safe, weaker). Count cache warm as scenario cost (would hide skip value).
- **Consequences / follow-up:** Closes D-OPEN-19 for B1.

### [D-028] 2026-08-29 — B1 change signal is files_changed ∪ apply paths

- **Decision ID:** D-028
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** D-025 / D-OPEN-18. Declared paths and apply mutations can disagree.
- **Decision:** The harness passes the conservative union of `files_changed` and apply-touched paths. B1 never sees a scenario id. Omitted `changed_paths` means unknown → full legal graph.
- **Rationale:** Union cannot hide S03/S05/S10/S13 conceptual changes or overlay side effects.
- **Evidence:** E-003 correctness 14/14
- **Alternatives considered:** `files_changed` only; workspace diff only.
- **Consequences / follow-up:** Closes D-OPEN-18 for B1.

### [D-029] 2026-08-29 — Structured skip reasons on every B1 decision

- **Decision ID:** D-029
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Later agent comparison needs inspectable decisions.
- **Decision:** Write `decisions.json` with `job`, `decision` (`RUN`|`SKIP`), `reason_code`, and `reason` for every job. `JobRecord.skip_reason` is optional and unused by B0 scheduling.
- **Rationale:** Checkable reasons are the safety interface; they are also the future agent/verifier log.
- **Evidence:** `tests/test_b1.py::test_every_decision_has_a_reason`
- **Alternatives considered:** Free-text only; reasons only on skips.
- **Consequences / follow-up:** Agent proposals must be comparable to these records.

### [D-030] 2026-08-29 — B2 invokes only to refine conservative B1 over-runs

- **Decision ID:** D-030
- **Date:** 2026-08-29
- **Status:** accepted (contract; not implemented)
- **Context:** Phase 2.3. B1 already answers unknown with a full legal graph. An agent on every PR would replay B1 on S01–S13.
- **Decision:** B1 always runs first. Escalate only when the B1 plan has a conservative residue (`unknown` / `dependencies` / `orchestrator` / missing change set / future history-dirty promote), the residue is inspectable, and expected skip value is non-trivial. Illegal flows, known components, clean promote, and already-tight B1 plans do **not** invoke the agent. Unknown path ≠ automatic agent call (CD-002).
- **Rationale:** Deterministic reasoning whenever sufficient. Agent cost is only justified as refinement.
- **Evidence:** not tested (design). E-003 shows B1 unnecessary = 0 on known rows.
- **Alternatives considered:** Agent on every scenario (rejected). Unknown → always agent (rejected: B1 is already safe).
- **Consequences / follow-up:** Implementation in a later phase. Kill switch / offline → B1.

### [D-031] 2026-08-29 — S01–S14 are B2 regression, not the agent-value suite

- **Decision ID:** D-031
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** CD-001. S14/S07 require the full graph. B1 already matches.
- **Decision:** Do not change S01–S14. B2 must stay 14/14 on them and is **not** expected to beat B1 cost there. Agent-value scenarios (conceptual S15+) get their own localized ground truth later. Do not weaken S14 to flatter an agent.
- **Rationale:** S14 tests fail-closed policy, not “perfect inspection.”
- **Evidence:** E-003; `scenarios.json` S14/S07
- **Alternatives considered:** Edit S14 required_jobs to branch_guard-only (rejected: silent contract change).
- **Consequences / follow-up:** First B2 *value* experiment waits for new scenarios or is limited to no-invoke / reject metrics on S01–S14.

### [D-032] 2026-08-29 — Agent proposes; verifier is final

- **Decision ID:** D-032
- **Date:** 2026-08-29
- **Status:** accepted (implemented in I-011; inert-unknown option withheld — D-036)
- **Context:** D-023, D-024.
- **Decision:** B2 output is a structured proposal (`docs/AGENT_DESIGN.md` §4). The verifier may accept, reject, or expand. Extra RUN is always safe. Narrowing SKIP needs mechanical evidence (localized component, inert unknown, or cache identity). Producer/consumer: skip A only if valid X exists. Malformed / uncertain → B1.
- **Rationale:** Safety stays deterministic.
- **Evidence:** not tested
- **Alternatives considered:** Agent as final skip authority (rejected).
- **Consequences / follow-up:** Verifier code is Phase 2.4+.

### [D-033] 2026-08-29 — B2 value is vs B1, including invocation cost

- **Decision ID:** D-033
- **Date:** 2026-08-29
- **Status:** accepted (methodology)
- **Context:** B1 already cut suite cost 41.33% with 0 false skips.
- **Decision:** Headline comparison is B0 → B1 → B2. Report `delta_vs_b1` only if the safety gate holds. Record invocation rate, latency, token/API cost, verifier reject rate, `novel_accept` / `novel_reject`. Lower simulated cost is not enough if the agent is expensive or unsafe.
- **Rationale:** Avoid celebrating an LLM that copies B1 or cheats S14.
- **Evidence:** not tested
- **Alternatives considered:** B0 vs B2 only (rejected).
- **Consequences / follow-up:** Harness fields specified; not implemented.

### [D-034] 2026-08-29 — Separate Cursor discovery log from runtime B2 log

- **Decision ID:** D-034
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Coding-agent finds vs CI-agent proposals were getting mixed in conversation.
- **Decision:** `docs/CURSOR_DISCOVERIES.md` records what Cursor found during development (belief → discovery → design change). Runtime B2 accept/reject stays in experiment/run records.
- **Rationale:** Engineering process should be visible, not silently absorbed.
- **Evidence:** not tested (process)
- **Alternatives considered:** Only IMPROVEMENT_CHANGELOG (too coarse).
- **Consequences / follow-up:** CD-001–CD-003 logged in Phase 2.3.

### [D-035] 2026-08-29 — One OpenAI-compatible provider

- **Decision ID:** D-035
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 2.4 required a reproducible, inexpensive, structured-JSON path with no committed credentials and a deterministic offline fallback.
- **Decision:** Implement a single stdlib `urllib` client for OpenAI-compatible Chat Completions. Default model `gpt-4o-mini` at `https://api.openai.com/v1`. Enable only with `B2_API_KEY` (not `OPENAI_API_KEY`). Tests use `FakeProvider`. Same client can point at Groq or Ollama via `B2_BASE_URL`.
- **Rationale:** One interface; no extra pip deps; local models are optional, not the primary host (not reproducible across machines).
- **Evidence:** E-004 ran offline ($0, 0 invocations). Unit tests cover API failure and timeout fallback.
- **Alternatives considered:** Native OpenAI SDK (rejected: extra dep). Dedicated Ollama/Groq classes (rejected: no strong reason). Local GGUF as primary (rejected: infra + irreproducible).
- **Consequences / follow-up:** Do not add a second provider unless the current client is insufficient.

### [D-036] 2026-08-29 — Reject inert-unknown skips

- **Decision ID:** D-036
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** AGENT_DESIGN §5 option 2 allowed skipping an unknown file when tools found no imports. CD-004: that is negative evidence and would fail S14.
- **Decision:** The implemented verifier does **not** accept inert-unknown. Narrowing requires a positive checkable localized edge or a valid, non-invalidated cache identity.
- **Rationale:** Never fail open. Do not weaken the verifier to make B2 look cheaper on S14.
- **Evidence:** `test_unsupported_skip_inert_unknown`; E-004 S14 cost 31 (matches B1 / ground truth).
- **Alternatives considered:** Implement option 2 as written (rejected: S14 false skip).
- **Consequences / follow-up:** Agent value needs S15+ with localized oracles, not a softer S14.

### [D-037] 2026-08-29 — compare stays B0 vs B1

- **Decision ID:** D-037
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Existing tests and E-003 treat `--system compare` as B0+B1.
- **Decision:** Keep `compare` = B0 vs B1. Add `agentic` (B2 only) and `ladder` (B0+B1+B2). Do not change B0/B1 test semantics.
- **Rationale:** Protected baselines stay comparable to E-003.
- **Evidence:** `test_benchmark_compare_b0_and_b1` unchanged and passing.
- **Alternatives considered:** Extend `compare` in place (rejected: would break the B1-only contract).
- **Consequences / follow-up:** E-004 used `--system ladder`.

### [D-038] 2026-08-29 — Cursor is not the B2 runtime provider

- **Decision ID:** D-038
- **Date:** 2026-08-29
- **Status:** accepted (investigation; no runtime change)
- **Context:** Phase 2.5. Participant will not spend more money on APIs. Cursor is already paid. Question: can that subscription drive B2?
- **Decision:** **NO.** Do not consume Cursor Cloud Agents / `cursor-sdk` / undocumented IDE hooks as B2’s model. Keep Cursor as the **coding** agent only ([CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md)).
- **Rationale:** Official API is an agent runner, not chat completions; requires a separate key; usage-billed; not judge-reproducible with the participant’s login (CD-005).
- **Evidence:** [cursor.com/docs/api](https://cursor.com/docs/api); [AGENT_PROVIDER_RESEARCH.md](AGENT_PROVIDER_RESEARCH.md)
- **Alternatives considered:** Wire `cursor-sdk` into `LLMProvider` (rejected: wrong shape, cost, extra dep). Scrape the IDE session (rejected: undocumented, unsuitable).
- **Consequences / follow-up:** Next live-model work, if approved, uses the existing OpenAI-compatible adapter — not Cursor.

### [D-039] 2026-08-29 — Stay provider-agnostic; $0 live path is local OpenAI-compat

- **Decision ID:** D-039
- **Date:** 2026-08-29
- **Status:** accepted (implemented in Phase 2.6; see D-041)
- **Context:** D-035 shipped one HTTP client. Participant constraint: $0 additional spend. E-004 already proves offline B2.
- **Decision:** Keep `LLMProvider` + one OpenAI-compatible client. Default remains **no key → B1**. If a later phase invokes a live model, prefer **local Ollama** (or equivalent) via `B2_BASE_URL`, with a pinned model tag. Do not add vendor-specific providers. Do not require judges to have a cloud account.
- **Rationale:** Matches $0, reproducibility, and the adapter already in tree. Groq is a free *tier* (limits; account required), not the preferred primary. OpenAI remains paid.
- **Evidence:** Ollama OpenAI compat docs; Groq rate-limit “Free Plan”; E-004
- **Alternatives considered:** Paid `gpt-4o-mini` as the required host (rejected: spend). Groq as required host (rejected: account + non-portable). Cursor SDK (rejected: D-038).
- **Consequences / follow-up:** Phase 2.6 implemented this path (D-041).

### [D-040] 2026-08-29 — Coding agent vs runtime agent are distinct

- **Decision ID:** D-040
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Hackathon language says “use coding agents”; this repo also has B2.
- **Decision:** Record Cursor (IDE) and B2 (CI optimizer) as two roles. Public challenge text available here does **not** conclusively require a live LLM inside the submitted program. Whether that is a judging requirement is **unresolved**. The repo’s own D-023 still treats B2 as the product comparison layer.
- **Rationale:** Do not reinterpret unofficial or incomplete contest rules.
- **Evidence:** README / public Frontier Engineering posts; HackerEarth page timed out; no official brief in the repo
- **Alternatives considered:** Claim Cursor-only satisfies all “agent” requirements (over-claim). Claim B2 live LLM is mandatory (also over-claim).
- **Consequences / follow-up:** Keep documenting both. Do not drop B2.

### [D-041] 2026-08-29 — Pin one local model: `qwen2.5:3b`

- **Decision ID:** D-041
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 2.6 must run a real B2 agent at $0 API cost on ~8 GB RAM. Multiple downloads were forbidden.
- **Decision:** Use **Ollama** `qwen2.5:3b` (3.1B, Q4_K_M, 1.9 GB, 32k context) as the only pulled model. Default `B2_MODEL` when `B2_BASE_URL` is local. Hosted default remains `gpt-4o-mini` and is unused.
- **Rationale:** Fits 8 GB CPU hosts; one pull command; OpenAI-compat already exists; 7B would not fit comfortably. Benchmark scores were not the selection criterion.
- **Evidence:** `ollama show qwen2.5:3b`; E-006; E-007
- **Alternatives considered:** llama3.2:3b (similar size, typically weaker JSON). 7B+ (RAM). Paid hosted models (rejected). Groq (account).
- **Consequences / follow-up:** Judges reproduce with the same tag. Weights use the Qwen Research License (inspect `ollama show`).

### [D-042] 2026-08-29 — Local B2 needs no API key; missing runtime falls back to B1

- **Decision ID:** D-042
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** E-004 treated “no `B2_API_KEY`” as offline. Local Ollama does not need a participant key. Hosted URLs must still not invoke without a key.
- **Decision:** `settings.available` is true for local hosts (`127.0.0.1`, `localhost`, `::1`, `0.0.0.0`, `host.docker.internal`) without a key. Hosted `B2_BASE_URL` without a key stays offline. If local URL is set but the runtime probe fails, do not invoke (`offline`). Never fail open.
- **Rationale:** $0, no participant secrets, replaceable host via env only.
- **Evidence:** unit tests in `tests/test_b2.py`; E-006 invoked; dead-port test
- **Alternatives considered:** Require a dummy `B2_API_KEY` (unnecessary friction). Auto-start Ollama (too much machinery).
- **Consequences / follow-up:** Unset `B2_BASE_URL` still reproduces E-004.

### [D-043] 2026-08-29 — Do not add S15–S21 without approval; off-suite S16-like is evidence only

- **Decision ID:** D-043
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** S01–S14 cannot show `novel_accept` without violating fail-closed oracles. AGENT_DESIGN §9.2 already names S16.
- **Decision:** Keep S01–S14 frozen. Run conceptual S16 **off-suite** (`scripts/run_s16_like_local.py`). Do not write S15–S21 into `benchmark/scenarios.json` in this phase.
- **Rationale:** An official row needs a declared oracle and human approval. Adding it now would look like optimizing the suite for B2.
- **Evidence:** E-007; AGENT_DESIGN §9.2
- **Alternatives considered:** Add S16 now (rejected). Change S14 (forbidden).
- **Consequences / follow-up:** An official S16 (and maybe S15) is **justified to request**, not implemented.

### [D-044] 2026-08-29 — Compact `copy_b1` wire format; verifier unchanged

- **Decision ID:** D-044
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** E-007 failed with `schema_version must be 1`. Asking the 3B model to emit all 10 full job objects timed out or malformed. AGENT_DESIGN still requires a complete job list for the verifier.
- **Decision:** Accept a short JSON wire form when `copy_b1` is true: omitted jobs (and listed jobs without a decision) expand to **RUN** before `validate_proposal`. Partial jobs without `copy_b1` stay invalid. Prose and non-JSON stay invalid. The verifier is unchanged.
- **Rationale:** Extra RUN is already allowed. This is a translation layer, not a skip authority. It made a live valid proposal possible (E-008 S16-like, 31 s).
- **Evidence:** E-008; unit tests `test_copy_b1_*`
- **Alternatives considered:** Relax `schema_version` (rejected). Accept missing jobs without a flag (rejected). Larger local model (not pulled).
- **Consequences / follow-up:** Prompt id `b2-proposal-v3`. A valid copy_b1 empty-jobs proposal equals B1 and is not an optimization win.

### [D-045] 2026-08-29 — Local default: no tools, no json_object

- **Decision ID:** D-045
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** E-006 used one tool then malformed JSON. E-008 attempts with tools or `response_format=json_object` timed out at 180–300 s on 8 GB CPU.
- **Decision:** Local hosts default `B2_ENABLE_TOOLS=false`. `response_format` json_object is used only for non-local JSON-only rounds. Override with `B2_ENABLE_TOOLS=1`. One schema-repair turn remains.
- **Rationale:** Previews already carry the unclassified file. Tool schemas and forced JSON mode were slower and less reliable on this model.
- **Evidence:** E-008 timeouts vs 31 s compact success
- **Alternatives considered:** Keep tools-first (rejected for local). Require json_object locally (timed out).
- **Consequences / follow-up:** Hosted path still offers tools.

### [D-046] 2026-08-29 — S01–S14 stay regression; S15–S18 are the agent-value design

- **Decision ID:** D-046
- **Date:** 2026-08-29
- **Status:** accepted (design). S16–S18 later loaded via D-048; S15 still not loaded.
- **Context:** B1 already matches S01–S14. E-006/E-008 cannot show a `T` win. D-043 blocked silent suite edits.
- **Decision:** Keep S01–S14 frozen. Define S15–S18 in [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md) only. S15 is a second fail-closed unknown (cheaper B2 = unsafe). S16–S18 are the Q1 value rows (needles the current verifier can check). Do not set S15 oracle to `branch_guard` only. Do not write these IDs into `scenarios.json` in this phase.
- **Rationale:** Q1 needs rows where B1 over-runs and a positive edge exists. Inert-unknown-as-docs is unreachable under D-036.
- **Evidence:** not tested as an official suite (design). E-008 off-suite S16-like is validity-only.
- **Alternatives considered:** Load S15–S18 now (rejected: design phase). Weaken verifier for S15 (rejected).
- **Consequences / follow-up:** Implementation of the rows needs explicit approval.

### [D-047] 2026-08-29 — Split Q1 (pipeline work) from Q2 (e2e latency and $)

- **Decision ID:** D-047
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** User question: does B2’s extra optimization justify agent latency/cost? A 10 s pipeline save vs 3 min reasoning must have a named answer.
- **Decision:** Report `T`, `W_jobs`, `W_agent`, `W_e2e`, and `$` separately. **Q1 win** = safety + `T_B2 < T_B1` on S16–S18. **Q2 win** = measured `W_e2e` improves (or a later, labeled production time model). A valid copy-B1 proposal is parity, not a win. Default evaluation stays $0.
- **Rationale:** Mixing agent seconds into simulated weights would hide both “smart but slow” and “cheap but wrong.”
- **Evidence:** E-003 job walls ~12–13 s/suite; E-006/E-008 agent 31–300 s. Observation: Q2 cannot succeed on this host with current job bodies.
- **Alternatives considered:** Single blended score (rejected). Claim production minutes without a published mapping (rejected).
- **Consequences / follow-up:** Stronger models use the same Q1/Q2 tables via env substitution (D-035/D-041).

### [D-048] 2026-08-29 — Official S16–S18 live in a separate scenario file

- **Decision ID:** D-048
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 2.9 implements the 2.8 design. Default tests require `scenarios.json` to be exactly S01–S14. Mixing S16–S18 into that file would change the 14-row 220-cost contract.
- **Decision:** Put S16–S18 in `benchmark/agent_value_scenarios.json`. Add `--scenarios` to the harness. Keep S01–S14 as the default. Do not load S15 as a cost-win row. Do not put scenario IDs in B2.
- **Rationale:** The value suite must be official and measurable without rewriting the regression suite or manufacturing a B1 win (S17 must not mutate `scoring_weights.json`).
- **Evidence:** E-010; `tests/test_agent_value_benchmark.py`
- **Alternatives considered:** Append to `scenarios.json` (rejected: breaks 14-row tests). Implement S15 as `branch_guard` only (rejected: D-046).
- **Consequences / follow-up:** Default `python -m agentic_cicd benchmark` remains S01–S14.

### [D-049] 2026-08-29 — Do not keep retrying qwen2.5:3b for a Q1 win

- **Decision ID:** D-049
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** E-008 already showed valid `copy_b1` with save 0. E-010 repeated that on official S16–S18 (3/3 valid all-RUN; 0 edges).
- **Decision:** Keep `qwen2.5:3b` as the $0 default runtime. Do not spend another phase retrying the same tag for novel_accept. A later Q1 experiment must substitute a different model through the existing env boundary, or stop.
- **Rationale:** The limitation is model behavior, not missing official rows. Further 3B retries would manufacture effort, not evidence.
- **Evidence:** E-010; CD-010
- **Alternatives considered:** Pull another local tag in this phase (rejected: user said one compatible alternative only if genuinely useful; 3B already answered). Weaken the verifier (rejected).
- **Consequences / follow-up:** Next approved phase is model substitution or an explicit stop. B2 remains the fail-closed wrapper.

### [D-050] 2026-08-29 — After one stronger local model, prefer B1 under $0

- **Decision ID:** D-050
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 2.10. D-049 required a different model, not another 3B retry. Host is 8 GB RAM, dual-core i3-7100U, no CUDA. 7B/8B tags were rejected as unusable. One tag was pulled: `qwen3:4b-instruct`.
- **Decision:** Record E-011 as Q1 **parity** and Q2 **no**. Keep `qwen2.5:3b` as the default live tag. Do **not** promote `qwen3:4b-instruct`. Do **not** pull further local tags for Q1 on this host. Treat **B1 as the preferred product** under the $0 constraint. Keep B2 as a fail-closed wrapper (offline = B1). A later paid model, if approved, is env substitution only.
- **Rationale:** The 4B instruct tag is a real generation step and still produced no `novel_accept` and no `T` save. Validity was worse (S17 malformed). Latency was worse than E-010. Further local retries would manufacture effort, not evidence.
- **Evidence:** E-011; CD-011
- **Alternatives considered:** Promote the 4B tag (rejected: no Q1 gain). Pull 7B (rejected: RAM/CPU). Enable tools / redesign B2 (forbidden this phase). Paid API (forbidden this phase).
- **Consequences / follow-up:** Stop. Wait for approval. Do not start another model hunt without an explicit paid-or-stop decision.

### [D-051] 2026-08-29 — Present B1 as the final optimizer; keep B2 as an experiment

- **Decision ID:** D-051
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Final consolidation. Judges need one product story. E-003 is the only gated suite win. E-010/E-011 show no B2 `T` win.
- **Decision:** The submitted optimization is **B1**. B0 is the baseline. B2 remains in the repo and docs as a **rejected production approach** and a learning. Cursor is documented as the coding agent. Ollama Qwen tags are documented as experimental runtime models only. Do not add new scenarios, models, or optimizer features for submission.
- **Rationale:** Honesty and judge scanability. A second optimizer that copies B1 is not the headline.
- **Evidence:** E-002, E-003, E-010, E-011; I-018
- **Alternatives considered:** Lead with B2 (rejected: no measured win). Delete B2 (rejected: hides the investigation).
- **Consequences / follow-up:** README / INSIGHTS / B1 / B2 labels updated. Stop for approval.

### [D-052] 2026-08-29 — Public repository is `main` only; simulated flows stay in the benchmark

- **Decision ID:** D-052
- **Date:** 2026-08-29
- **Status:** accepted
- **Context:** Phase 3.1. The public GitHub repository will use `main` as the only required branch. `feature`, `development`, and `main` also appear as **simulated CI flows** in B0/B1/S01–S14.
- **Decision:** Treat those names as benchmark model labels, not required Git branches. Judges must not create a `feature` or `dev` branch, open a PR, merge, or enable GitHub Actions. Reproduction is: clone `main`, install, run B0, run B1, run tests and ruff. B2 remains optional and is not required for the headline result. Do not add a `.github/workflows` requirement.
- **Rationale:** A judge should not have to reconstruct the participant’s development workflow. The simulator already encodes promotion rules.
- **Evidence:** I-019; CD-013; E-013
- **Alternatives considered:** Document a multi-branch Git workflow for judges (rejected). Add GitHub Actions as the official path (rejected: local is sufficient and already measured).
- **Consequences / follow-up:** README and PROBLEM_FRAMING state the distinction. First commit + push is still required before a stranger can clone (not done in this phase).

### [D-053] 2026-08-30 — Do not add a Git change detector to the submitted product

- **Decision ID:** D-053
- **Date:** 2026-08-30
- **Status:** accepted
- **Context:** Final freeze. B1 already consumes `changed_paths` from the caller: CLI `--changed`, or the harness union `files_changed ∪ apply` (D-028). Docs listed “no git ancestry walk; the caller must supply the change list” as a limitation. Cursor (Grok 4.6, Agent) was asked to investigate whether automatic Git working-tree discovery (clone → edit a file → run B1) was worth adding before submission.
- **Decision:** Do **not** implement Git detection. Do **not** put Git inside `src/agentic_cicd/b1/`. B1’s job remains: optimize a **supplied** change set. The suite continues to use D-028. The documented limitation is **intentional scope**, not an overlooked defect. A future isolated `--from-git` adapter (working tree vs `HEAD`, outside B1) may exist later; it is not part of this submission. That adapter would not be git-ancestry-for-promote and must never replace the benchmark change signal.
- **Rationale:** A detector does not move E-003 (375 → 220). Wiring Git into the harness would disagree with S03/S05/S10/S13, where the declared change class is not recoverable from a workspace diff. Making Git the CLI default would change omit-`--changed` = unknown (fail closed). D-051 already forbids new optimizer features for submission.
- **Evidence:** not tested as a new suite run (docs-only investigation). CD-014; inspection of `cli.py`, `b1/planner.py`, `b1/classify.py`, `benchmark/apply.py` `change_set`, `benchmark/runner.py`, and S03/S10 overlay proxies.
- **Alternatives considered:** Implement `--from-git` now (rejected: late-stage product surface, no measured gain). Make Git the default change signal (rejected: weakens the fail-closed CLI contract). Replace D-028 with `git diff` in the harness (rejected: would corrupt or fail-close the measured B1 result). Put Git inside `b1/` (rejected: mixes change acquisition with planning).
- **Consequences / follow-up:** Record as a future enhancement only. Freeze the product. No implementation, no new experiment, no commit in this phase.

---

## Deferred (open decisions)

Phase 1.3 closed topology/metrics/safety definitions. Phase 2.1–2.2 closed the optimizer contract and B1. Phase 2.3 closed the B2 *design* contract. Phase 2.4 implemented B2. Phase 2.5 closed Cursor-as-B2-host (D-038). Phase 2.6 implemented the $0 local live path (D-041–D-043). Phase 2.7 improved proposal validity (D-044–D-045). Phase 2.8 designed the agent-value benchmark (D-046–D-047). Phase 2.9 implemented S16–S18 (D-048–D-049). Phase 2.10 substituted one stronger local model (D-050). Phase 3.0 named B1 as the presented solution (D-051). Phase 3.1 fixed public Git topology vs simulated CI flows (D-052). Phase 3.2 investigated a working-tree Git adapter and froze without implementing it (D-053).

| ID | Topic | State after Phase 1.3 |
| --- | --- | --- |
| D-OPEN-01 | User interviews / field evidence | Still open; working definition only |
| D-OPEN-02 | Pipeline topology | **Closed as design (D-012)**; not implemented |
| D-OPEN-03 | Ground-truth skip rules | **Closed as design** (`PROBLEM_FRAMING.md` §7); fixtures later |
| D-OPEN-04 | Branch/promotion model | **Implemented in B0 (D-019)**; no git ancestry walk. Working-tree `--from-git` is **not** this question; **deferred for submission (D-053)** |
| D-OPEN-05 | Artifact identity / symmetry | **Closed (D-013 + D-018)** for local bundle hash; promote flow not implemented |
| D-OPEN-06 | Baseline algorithm | **B0 implemented (D-019)**; **B1 implemented (D-026)** |
| D-OPEN-07 | Agent architecture, tools, and model | **Implemented**; default `qwen2.5:3b`; E-011 tried `qwen3:4b-instruct` (no Q1 win); `copy_b1` wire form (D-044); local tools off (D-045) |
| D-OPEN-08 | Agent input context | **Implemented** (`b2/context.py`; no scenario id) |
| D-OPEN-09 | Evaluation metrics | **Closed (D-015)** + Q1/Q2 (D-047); B0 = E-002; B1 = E-003; B2 = E-004/E-006; value suite = E-010 and E-011 (parity) |
| D-OPEN-10 | Dataset / fixture files | **Closed for v1 fixtures and S01–S14 JSON** |
| D-OPEN-11 | Extra libraries, Docker-in-repo, lockfile | Still open |
| D-OPEN-12 | GitHub Actions vs local runner vs both | **Closed for submission (D-052):** local runner only; GHA not present and not required |
| D-OPEN-13 | How required jobs are labeled | **Closed as design** (per-scenario table); encoding in code later |
| D-OPEN-14 | Uncertainty policy | **Closed (D-016):** run the job; restated in Phase 2.1 safety model |
| D-OPEN-15 | Whether to implement B1 path filters | **Closed (D-026):** impact graph, not path filters |
| D-OPEN-16 | Evaluate quality-gate thresholds | Still open (metrics are reported, not gating the build) |
| D-OPEN-17 | Simulated cost realization | **Closed for B0:** counter only, no sleep |
| D-OPEN-18 | Optimizer change-input signal (`files_changed` vs `apply` diffs) | **Closed for B1 (D-028):** union. Git must not replace this in the harness (D-053) |
| D-OPEN-19 | Intermediate artifact cache for legal skips | **Closed for B1 (D-027):** identity-checked last-known-good cache |
| D-OPEN-20 | Whether dirty promote should advance the development pointer | Open; B0 does not rewrite `development.json` |
| D-OPEN-21 | Optional working-tree Git adapter (`--from-git`) | **Closed for submission (D-053):** analyzed; not implemented; future enhancement only. Not an optimizer rule and not a defect |

---

## Rejected

No implementation approach has been built and discarded.

Design alternatives **rejected on paper** in Phase 1.3 (not empirical): live API as benchmark source; training-centric ML; skip-count or ungated wall-clock as the primary metric; feature→main; rebuild-on-promote as the optimized path. Details: `PROBLEM_FRAMING.md` §12 and D-009–D-015.

Phase 3.2 (D-053, not empirical): shipping an optional `--from-git` working-tree adapter, putting Git inside `b1/`, or replacing the D-028 harness union with a Git/workspace diff. Analyzed with Cursor; not built. A later isolated adapter remains a possible enhancement, not this submission.
