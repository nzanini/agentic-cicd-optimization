# Improvement changelog

This log records **meaningful iterations**: what changed, why, with what evidence, and what was decided.

It is not a substitute for Git history.

- Git commits record repository history.
- This file explains reasoning, evidence, and keep / modify / remove decisions.

**Rule:** do not invent results. If something was not tested, say so.

---

## How to log an iteration

Copy the template below for every meaningful future iteration.

```md
## [I-XXX] YYYY-MM-DD — short title

- **Iteration ID:** I-XXX
- **Date:** YYYY-MM-DD
- **Objective:**
- **Hypothesis:**
- **Changes:**
- **Agent / model used:** (or `none`)
- **Agent mode / tooling:** (Cursor mode, CLI, scripts, etc., or `n/a`)
- **Prompt / instructions:** (link or summary; or `n/a`)
- **Files changed:**
- **Experiments performed:** (IDs in EXPERIMENT_LOG.md, or `none`)
- **Baseline result:** (`not measured` if applicable)
- **New result:** (`not measured` if applicable)
- **Metrics:** (`not defined` / `not measured` if applicable)
- **Failures:**
- **Retries:**
- **Human feedback:**
- **Decision:** kept / modified / removed / deferred
- **Rationale:**
- **Lessons learned:**
```

---

## Entries

### [I-001] 2026-08-28 — Phase 1.1 project foundation

- **Iteration ID:** I-001
- **Date:** 2026-08-28
- **Objective:** Establish a durable, judge-readable project record and repository foundation. Do not implement the CI/CD system, agent, or evaluation pipeline.
- **Hypothesis:** A documentation-first start will make later iterations reconstructible (original idea vs current state vs planned vs rejected) and will prevent premature architectural lock-in.
- **Changes:** Added `README.md`, `LICENSE`, `.gitignore`, and `docs/{ROADMAP,IMPROVEMENT_CHANGELOG,EXPERIMENT_LOG,DECISION_LOG}.md`. No application code.
- **Agent / model used:** Cursor Grok 4.6, used as a coding assistant to draft foundation files from the Phase 1.1 brief. No domain agent for CI/CD optimization was built or run.
- **Agent mode / tooling:** Cursor Agent mode (implementation of documentation only).
- **Prompt / instructions:** Human Phase 1.1 brief: inspect repo; create structure and the four docs plus README, `.gitignore`, and a hackathon-suitable license; document hypothesis and high-level phases; do not implement future phases or fabricate metrics/experiments.
- **Files changed:** `README.md`, `LICENSE`, `.gitignore`, `docs/ROADMAP.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`, `docs/DECISION_LOG.md`
- **Experiments performed:** none
- **Baseline result:** not measured (no baseline exists)
- **New result:** not measured
- **Metrics:** not defined
- **Failures:** none for this documentation step
- **Retries:** none
- **Human feedback:** approved; continue with Phase 1.2
- **Decision:** kept. This iteration is scaffolding, not a product improvement.
- **Rationale:** Hackathon evaluation depends on evidence, reproducibility, and a clear evolution from baseline to agent. Those require a written record before any system is built.
- **Lessons learned:** not applicable beyond “the repo was empty; foundation is documentation-only.”

### [I-002] 2026-08-28 — Phase 1.2 Python technical foundation

- **Iteration ID:** I-002
- **Date:** 2026-08-28
- **Objective:** Establish a minimal, maintainable Python project foundation without implementing CI/CD optimization, the agent, benchmark data, or evaluation.
- **Hypothesis:** An installable `src/` package, `pyproject.toml` dependency management, pytest, and ruff are enough to make later phases reproducible, without locking pipeline or agent design.
- **Changes:** Added `pyproject.toml`, `.python-version`, `src/agentic_cicd/__init__.py` (version placeholder), and `tests/test_package_import.py` (import smoke test only). Updated README, roadmap, and decision log. No Dockerfile, no GitHub Actions, no LLM/cloud deps, no application modules.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant for scaffolding. No CI/CD optimization agent was built or run.
- **Agent mode / tooling:** Cursor Agent mode.
- **Prompt / instructions:** Human Phase 1.2 brief: Python foundation, dependency management, basic tests without fake app tests, optional lightweight code quality, Docker only if justified, no optimizer/metrics/infra.
- **Files changed:** `pyproject.toml`, `.python-version`, `src/agentic_cicd/__init__.py`, `tests/test_package_import.py`, `README.md`, `docs/ROADMAP.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/DECISION_LOG.md`
- **Experiments performed:** none (toolchain verification only; not an optimization experiment)
- **Baseline result:** not measured
- **New result:** not measured
- **Metrics:** not defined
- **Failures:** Host `python` was not on PATH (Windows Store stub only). Foundation commands were therefore verified in a throwaway `python:3.12-slim` container, not in a local `.venv`. That container is not part of the project.
- **Retries:** none
- **Human feedback:** approved; continue with Phase 1.3
- **Decision:** kept. Scaffolding only.
- **Rationale:** Later work needs a known runtime, an install path, and a test/lint entrypoint. Product topology, agent design, and metrics remain open (D-OPEN-*).
- **Lessons learned:** This machine did not have a working CPython on PATH. Documented developer commands assume Python 3.11+ is installed locally.
- **Verification performed:** In `python:3.12-slim`, `pip install -e ".[dev]"` then `python -m pytest` (1 passed), `python -m ruff check .` (all checks passed), `python -m ruff format --check .` (already formatted). Resolved dev packages in that run: pytest 9.1.1, ruff 0.16.5. No lockfile was committed; `pyproject.toml` specifies lower bounds only.
- **Still undecided:** (as of I-002) pipeline/jobs, promotion scope, baseline, agent, metrics, fixtures, in-repo Docker, GitHub Actions, lockfile tool. Several of these were specified later in I-003.

### [I-003] 2026-08-29 — Phase 1.3 problem framing and evaluation contract

- **Iteration ID:** I-003
- **Date:** 2026-08-29
- **Objective:** Specify the problem, workload, job topology, baseline, scenarios, correctness rules, and evaluation/reproducibility/observability contracts. Do not implement the system.
- **Hypothesis:** A written contract (Catalog Ranker + 10 jobs + B0 + S01–S14 + gated simulated duration) is enough to implement and measure later without pretending results exist now.
- **Changes:** Added `docs/PROBLEM_FRAMING.md`. Updated README, roadmap, decision log, experiment log header. No application, workflow, Docker, agent, or fixture code.
- **Agent / model used:** Cursor Grok 4.6 as a documentation assistant. No CI/CD optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, **new conversation** for Phase 1.3 (D-008).
- **Prompt / instructions:** Human Phase 1.3 brief: correctness-constrained optimization; ML as workload only; evaluate public-API vs fixtures; define jobs, baseline, ≥10 scenarios including adversarial; one primary metric; no implementation; no fabricated experiments.
- **Files changed:** `docs/PROBLEM_FRAMING.md`, `README.md`, `docs/ROADMAP.md`, `docs/DECISION_LOG.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`
- **Experiments performed:** none
- **Baseline result:** not measured (B0 defined, not run)
- **New result:** not measured
- **Metrics:** defined, not measured
- **Failures:** none for this documentation step
- **Retries:** none
- **Human feedback:** approved; continue with Phase 1.4
- **Decision:** kept. Design specification only.
- **Rationale:** Hackathon scoring needs an evaluable problem and a fair baseline/optimized comparison plan before code.
- **Lessons learned:** Live APIs look “realistic” but fail the reproducibility constraint; the ingest *job* is what matters.
- **Still undecided:** (as of I-003) agent design, GHA vs local, B1, fixture files, hash algorithm, evaluate gates, cost realization. Fixtures and hash algorithm were closed in I-004.

### [I-004] 2026-08-29 — Phase 1.4 executable Catalog Ranker

- **Iteration ID:** I-004
- **Date:** 2026-08-29
- **Objective:** Implement the minimal deterministic Catalog Ranker (fixtures, frozen weights, local CLI, artifact id, tests). Do not implement the CI graph, B0 orchestrator, optimizer, or agent.
- **Hypothesis:** A stdlib-only weighted-genre ranker plus SHA-256 canonical identity is enough for later jobs to wrap, without ML libraries or network.
- **Changes:** Added fixtures, `src/agentic_cicd/ranker/*`, CLI (`python -m agentic_cicd rank`), workload tests. Documented D-018. No GitHub Actions, no job selection, no live API.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant. No CI/CD optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, Phase 1.4 conversation.
- **Prompt / instructions:** Human Phase 1.4 brief: executable baseline *workload* foundation; fixtures; deterministic outputs; artifact identity; tests; local command; no optimizer/GHA/agent/benchmark runner.
- **Files changed:** `fixtures/**`, `src/agentic_cicd/**`, `tests/test_catalog_ranker.py`, `pyproject.toml`, `README.md`, `docs/ROADMAP.md`, `docs/PROBLEM_FRAMING.md`, `docs/DECISION_LOG.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`
- **Experiments performed:** none (workload verification is not a B0 vs optimized experiment)
- **Baseline result:** not measured
- **New result:** not measured
- **Metrics:** CI optimization metrics not measured. Workload `metrics.json` is ranking coverage/mean score/checksum only.
- **Failures:** Host `python` still not on PATH. Verification used `python:3.12-slim` (not an in-repo image). First ruff run failed on line length / unused import; fixed and re-run.
- **Retries:** one lint fix pass
- **Human feedback:** approved; continue with Phase 1.5
- **Decision:** kept
- **Rationale:** Later CI jobs need a real, inspectable, deterministic producer of artifact ids.
- **Lessons learned:** Artifact id stays stable when `run_metadata` is excluded from the hash. Two CLI runs printed the same id.
- **Verification performed:** `pip install -e ".[dev]"`; `python -m pytest` (6 passed); `python -m ruff check .` (clean); `python -m ruff format --check .` (20 files already formatted); two `python -m agentic_cicd rank` runs both produced `artifact_id=edce46746e15e01e6f1bc697b3ac1a8ee316c6a9ae5258010bf2b8432e254c81`. This is not a B0-vs-optimized benchmark.
- **Still undecided:** (as of I-004) B0 job runner, GHA vs local, agent, S12 `configs/` weights, evaluate quality gates, simulated cost, B1. B0 and simulated-cost counter were implemented in I-005.

### [I-005] 2026-08-29 — Phase 1.5 executable B0 baseline

- **Iteration ID:** I-005
- **Date:** 2026-08-29
- **Objective:** Make B0 a real local CI/CD runner that always executes every legal job. No optimizer, agent, change detection, or B1.
- **Hypothesis:** A sequential in-process job graph wrapping the Catalog Ranker is enough to produce run records, artifact pointers, and failure behavior for later comparison.
- **Changes:** Added `src/agentic_cicd/b0/*`, `python -m agentic_cicd b0`, `tests/test_b0.py`, `docs/B0.md`.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant. No CI optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, Phase 1.5 conversation.
- **Prompt / instructions:** Human Phase 1.5 brief: executable B0; local simulation; documented job graph; branch rules; artifact identity; failure propagation; no GHA unless necessary; no optimization.
- **Files changed:** `src/agentic_cicd/b0/**`, `src/agentic_cicd/cli.py`, `tests/test_b0.py`, `docs/B0.md`, `README.md`, `docs/ROADMAP.md`, `docs/PROBLEM_FRAMING.md`, `docs/DECISION_LOG.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`, `pyproject.toml`
- **Experiments performed:** none (B0 execution is verification, not a comparison experiment)
- **Baseline result:** not compared
- **New result:** not measured
- **Metrics:** no optimization metrics. Simulated cost totals are design-weight sums, not improvements.
- **Failures:** Host `python` still not on PATH. Verification used `python:3.12-slim`. First ruff pass failed on line length; fixed and re-run.
- **Retries:** one lint fix pass
- **Human feedback:** approved; continue with Phase 1.6
- **Decision:** kept
- **Rationale:** Later agents need a real always-run-all runner to beat.
- **Verification performed:** `python -m ruff check .` clean; `ruff format --check` 27 files formatted; `python -m pytest` 15 passed. CLI: feature→development succeeded (`artifact_id=edce46746e15e01e6f1bc697b3ac1a8ee316c6a9ae5258010bf2b8432e254c81`, simulated_cost_total=31); development→main succeeded with the **same** artifact id; feature→main failed with `artifact_id=None` and cost 0. Not a B0-vs-optimized experiment.
- **Still undecided:** (as of I-005) agent, GHA wrapper, B1, scenario suite runner, S12 configs path. Suite + S12 overlay landed in I-006.

### [I-006] 2026-08-29 — Phase 1.6 reproducible benchmark suite

- **Iteration ID:** I-006
- **Date:** 2026-08-29
- **Objective:** Encode S01–S14 ground truth and measure B0. No optimizer.
- **Hypothesis:** A JSON required-job contract plus an isolated workspace runner is enough to measure B0 without fitting the suite to B0.
- **Changes:** `benchmark/scenarios.json`, `src/agentic_cicd/benchmark/*`, `configs/*`, scoring-weight overlay, `python -m agentic_cicd benchmark`, tests, docs.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant. No CI optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, Phase 1.6 conversation.
- **Prompt / instructions:** Human Phase 1.6 brief: S01–S14; independent ground truth; adversarial case; B0 measurement; no optimizer/B1/change detection.
- **Files changed:** `benchmark/scenarios.json`, `configs/**`, `src/agentic_cicd/benchmark/**`, `src/agentic_cicd/ranker/ingest.py`, `src/agentic_cicd/ranker/package.py`, `src/agentic_cicd/ranker/pipeline.py`, `src/agentic_cicd/b0/jobs.py`, `src/agentic_cicd/cli.py`, `tests/test_benchmark.py`, docs listed in Phase 1.6
- **Experiments performed:** E-001
- **Baseline result:** suite simulated cost 401; correctness 13/14; false skips 0; S10 is the miss (see E-001)
- **New result:** not applicable (no optimizer)
- **Metrics:** baseline only; not an improvement claim
- **Failures:** Host `python` missing (used `python:3.12-slim`). First determinism test failed because manifests stored absolute workspace paths; fixed to logical names. One ruff line-length fix.
- **Retries:** lint + identity-path fixes
- **Human feedback:** pending review of Phase 1.6
- **Decision:** kept (pending approval)
- **Rationale:** Later optimizers need a frozen required-job contract and a published B0 number.
- **Verification performed:** `ruff check` / `ruff format --check` clean; `pytest` 21 passed; `python -m agentic_cicd benchmark` → cost 401, pass rate 0.928571, false_skip_count 0.
- **Still undecided:** agent, B1, GHA. Dirty-promote identity is closed in I-007 / D-021.

### [I-007] 2026-08-29 — Phase 1.6.1 correct B0 dirty promotion semantics

- **Iteration ID:** I-007
- **Date:** 2026-08-29
- **Objective:** Make B0 match the documented clean/dirty promotion contract. Do not implement B1, change detection, or an optimizer.
- **Hypothesis:** S10 failed because `job_promote` rejected any rebuilt id that differed from the development pointer. Treating that as an optimization problem would be wrong; the baseline itself was incorrect. An explicit `promote_mode` taken from scenario setup/apply is enough.
- **Changes:** `promote_mode=reuse|rebuild` on B0; reuse schedules only `branch_guard` + `promote`; rebuild promotes the new artifact; benchmark maps empty vs non-empty `apply` on development→main; focused tests; E-002 recorded separately from E-001.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant. No CI optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, Phase 1.6.1 conversation.
- **Prompt / instructions:** Human Phase 1.6.1 brief: correct B0 promote; do not weaken S10; do not add B1/change detection/agent; preserve E-001; stop for approval.
- **Files changed:** `src/agentic_cicd/b0/{graph,jobs,runner,state}.py`, `src/agentic_cicd/cli.py`, `src/agentic_cicd/benchmark/runner.py`, `tests/test_b0.py`, `tests/test_benchmark.py`, docs listed in Phase 1.6.1. `benchmark/scenarios.json` not changed.
- **Experiments performed:** E-002 (E-001 preserved)
- **Baseline result:** E-001: cost 401; correctness 13/14; S10 failed
- **New result:** E-002: cost 375; correctness 14/14; S10 passed. Not an optimization claim.
- **Metrics:** suite cost 375; median 31; jobs 110; unnecessary 37; false skips 0; correctness 14/14; wall 13103.446 ms
- **Failures:** Host `python` missing (used `python:3.12-slim`). Two lint fixes (E501, format) before the recorded benchmark.
- **Retries:** lint only
- **Human feedback:** pending review of Phase 1.6.1
- **Decision:** kept (pending approval)
- **Rationale:** The contract already distinguished clean reuse from dirty rebuild. B0 had to implement both without becoming an optimizer.
- **Verification performed:** `python -m pytest` 23 passed; `ruff check` / `ruff format --check` clean; focused clean/dirty/illegal/failed-promote tests passed; `python -m agentic_cicd benchmark --output outputs/benchmark-e002` → cost 375, pass rate 1.0, false_skip_count 0.
- **Still undecided:** agent, B1, GHA. Closed as design (not implemented) in I-008: optimizer contract, comparison ladder, chat-reset source-of-truth rule.

### [I-008] 2026-08-29 — Phase 2.1 formal optimization contract

- **Iteration ID:** I-008
- **Date:** 2026-08-29
- **Objective:** Inspect the repository and write the optimizer-facing contract. Do not implement an optimizer, change detector, or agent. Do not change B0 or S01–S14 ground truth.
- **Hypothesis:** A written dependency / change-impact / safety / promotion / objective / agent-boundary contract is enough to implement a deterministic optimizer later, and to keep the question “what did the agent improve?” answerable.
- **Changes:** Added `docs/OPTIMIZATION_CONTRACT.md`. Updated README, roadmap, problem framing, decision log, benchmark note, B0 pointer, experiment-log header. Documented chat-reset / repo-as-source-of-truth (D-022). No application, B0, scenario, or test-code changes.
- **Agent / model used:** Cursor Grok 4.6 as a documentation assistant. No CI/CD optimization agent.
- **Agent mode / tooling:** Cursor Agent mode, **new conversation** for Phase 2 (D-008 / D-022).
- **Prompt / instructions:** Human Phase 2.1 brief: inspect docs + B0 + benchmark + workload + tests; resolve job model, change impact, safety, promotion, objective, benchmark relationship, agent boundary; persist into docs; run existing verification; stop before Phase 2.2.
- **Files changed:** `docs/OPTIMIZATION_CONTRACT.md`, `docs/DECISION_LOG.md`, `docs/PROBLEM_FRAMING.md`, `docs/ROADMAP.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`, `docs/BENCHMARK.md`, `docs/B0.md`, `README.md`
- **Experiments performed:** none
- **Baseline result:** not re-measured; E-002 remains the B0 reference (suite cost 375, correctness 14/14, false skips 0). Not an optimization.
- **New result:** not measured (no optimizer)
- **Metrics:** not measured
- **Failures:** none for this documentation step
- **Retries:** none
- **Human feedback:** pending review of Phase 2.1; Phase 2.2 must not start without approval
- **Decision:** kept (pending approval). Contract only.
- **Rationale:** Implementing skip logic before the contract would mix exploration with untracked safety rules and would skip the deterministic layer the project needs for later agent comparison.
- **Lessons learned:** S01–S14 `files_changed` and `apply` are not always the same physical mutation. Ground truth is the declared change class. B0’s `test` job is smoke, not pytest. Legal skips of ingest/prepare/score assume a cache that does not exist yet.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: `pip install -e ".[dev]"` then `python -m pytest` (23 passed), `python -m ruff check .` (clean), `python -m ruff format --check .` (35 files already formatted). The suite includes `test_benchmark_suite_against_b0`, so B0 still meets S01–S14 ground truth. No optimized benchmark. No `src/`, `tests/`, or `benchmark/scenarios.json` edits.
- **Still undecided:** optimizer input signal, intermediate cache, B1 vs full impact graph, dirty-promote development pointer, agent design, GHA, how the harness invokes a non-B0 system. Several of these closed in I-009 (D-026–D-028).

### [I-009] 2026-08-29 — Phase 2.2 deterministic optimizer (B1)

- **Iteration ID:** I-009
- **Date:** 2026-08-29
- **Objective:** Implement B1 as a deterministic impact-graph optimizer. Do not implement an agent. Do not change B0 or S01–S14 ground truth.
- **Hypothesis:** Path→component→artifact→job rules plus identity-checked cache can beat B0 on suite simulated cost with zero false skips.
- **Changes:** Added `src/agentic_cicd/b1/*`, `python -m agentic_cicd b1`, `benchmark --system compare`, `tests/test_b1.py`, `docs/B1.md`. B0 scheduling unchanged. `scenarios.json` unchanged.
- **Agent / model used:** Cursor Grok 4.6 as a coding assistant. No CI optimization agent. No LLM in B1.
- **Agent mode / tooling:** Cursor Agent mode, Phase 2.2 conversation.
- **Prompt / instructions:** Human Phase 2.2 brief: implement B1; producer/consumer safety; infer promote; structured reasons; compare B0 vs B1; stop before an agent phase.
- **Files changed:** `src/agentic_cicd/b1/**`, `src/agentic_cicd/benchmark/**`, `src/agentic_cicd/cli.py`, `src/agentic_cicd/b0/runner.py` (`skip_reason` field only), `tests/test_b1.py`, `tests/test_benchmark.py`, docs listed in Phase 2.2
- **Experiments performed:** E-003
- **Baseline result:** E-002 / E-003 B0: cost 375; median 31; jobs 110; unnecessary 37; false skips 0; correctness 14/14
- **New result:** E-003 B1: cost 220; median 19; jobs 73; unnecessary 0; false skips 0; correctness 14/14; win eligible
- **Metrics:** suite reduction 155 / 41.3333%. Not an agent delta.
- **Failures:** first clean-promote run raised because reuse tried to hydrate a bundle cache; fixed by not consuming bundle on `promote_mode=reuse`
- **Retries:** ruff format; clean-promote hydrate fix
- **Human feedback:** pending review of Phase 2.2; no agent phase without approval
- **Decision:** kept (pending approval)
- **Rationale:** The contract required a deterministic floor before an agent. B1 matched required job sets on S01–S14 without scenario-id special cases.
- **Lessons learned:** Overlay-vs-pipeline classification is the S12 rule. Cache hits must be hash-checked. Change-set `None` vs `[]` must mean unknown vs empty.
- **Verification performed:** `python -m pytest` 41 passed; ruff clean; `python -m agentic_cicd benchmark --system compare --output outputs/benchmark-e003`
- **Still undecided:** agent design, GHA, dirty-promote development pointer, git ancestry, quality-gate thresholds. Agent *contract* closed in I-010 (not implemented).

### [I-010] 2026-08-29 — Phase 2.3 agentic optimizer contract

- **Iteration ID:** I-010
- **Date:** 2026-08-29
- **Objective:** Design B2 invocation, context, tools, proposal schema, verifier, evaluation, and Cursor discovery logging. Do not implement an agent. Do not change B0, B1, or S01–S14.
- **Hypothesis:** Because B1 already matches S01–S14, B2 is only justified as a refinement of conservative over-runs, with a deterministic verifier and a separate agent-value suite later.
- **Changes:** Added `docs/AGENT_DESIGN.md`, `docs/CURSOR_DISCOVERIES.md` (CD-001–CD-003). Updated roadmap, decision log (D-030–D-034), contract pointer, README. No application code.
- **Agent / model used:** Cursor Grok 4.6 as a documentation assistant. No CI agent. No LLM client.
- **Agent mode / tooling:** Cursor Agent mode, Phase 2.3 conversation.
- **Prompt / instructions:** Human Phase 2.3 brief: design-only B2 contract; B1 first; verifier final; do not assume unknown → always agent; stop before implementation.
- **Files changed:** `docs/AGENT_DESIGN.md`, `docs/CURSOR_DISCOVERIES.md`, `docs/ROADMAP.md`, `docs/DECISION_LOG.md`, `docs/IMPROVEMENT_CHANGELOG.md`, `docs/EXPERIMENT_LOG.md`, `docs/OPTIMIZATION_CONTRACT.md`, `docs/PROBLEM_FRAMING.md`, `README.md`
- **Experiments performed:** none
- **Baseline result:** E-003 remains the B1 number (220 / 14/14 / 0 false skips). Not re-measured as an optimization.
- **New result:** not measured (no B2)
- **Metrics:** not measured
- **Failures:** none for this documentation step
- **Retries:** none
- **Human feedback:** pending review; Phase 2.4 must not start without approval
- **Decision:** kept (pending approval). Contract only.
- **Rationale:** Implementing an LLM now would hide whether it beats B1 or just copies it.
- **Lessons learned:** S14/S07 encode fail-closed policy; a “smart” skip of an inert unknown file fails the current suite (CD-001).
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: `python -m pytest` 41 passed; ruff clean; 45 files already formatted. No `src/`, `tests/`, or `benchmark/scenarios.json` edits.
- **Still undecided:** model, S15+ implementation, min_confidence, cost knob `k`, GHA. Closed in I-011 except S15+ and GHA.

### [I-011] 2026-08-29 — Phase 2.4 agentic optimizer (B2)

- **Iteration ID:** I-011
- **Date:** 2026-08-29
- **Objective:** Implement B2: B1 first, optional agent, structured proposal, deterministic verifier, B1 fallback, observability, tests, S01–S14 measurement. Do not change B0/B1 behavior or S01–S14.
- **Hypothesis:** On the frozen suite B2 should reproduce B1. Agent value requires later localized scenarios. A verifier that accepts “no search hits” would fail S14.
- **Changes:** Added `src/agentic_cicd/b2/**`. CLI `b2`. Benchmark `agentic` / `ladder` (`compare` unchanged). Unit tests in `tests/test_b2.py`. Docs: B2.md, contract/roadmap/logs, CD-004.
- **Agent / model used:** Cursor Grok 4.6 as the coding assistant. Runtime CI agent is optional (`B2_API_KEY` + `gpt-4o-mini` via OpenAI-compatible HTTP). E-004 did not call a host.
- **Agent mode / tooling:** Cursor Agent mode, Phase 2.4 conversation.
- **Prompt / instructions:** Human Phase 2.4 brief: implement B2; choose one model path; verifier final; do not weaken S14; stop before 2.5; no commit.
- **Files changed:** `src/agentic_cicd/b2/**`, `src/agentic_cicd/cli.py`, `src/agentic_cicd/benchmark/runner.py`, `tests/test_b2.py`, `tests/test_benchmark.py` (additive B2 test only), docs listed above. No `benchmark/scenarios.json`. No B0/B1 scheduling changes.
- **Experiments performed:** E-004
- **Baseline result:** E-003 B0 375 / B1 220, 14/14, 0 false skips
- **New result:** E-004 B2 220, 14/14, 0 false skips, 0 unnecessary, 0 invocations, 0 novel_accept, 0 novel_reject, $0 model cost
- **Metrics:** `delta_vs_b1 = 0`. Safety gate held. Not claimed as an optimization win vs B1.
- **Failures:** none on the suite. First illegal-flow unit test expected `executed=branch_guard`; the job *fails* (same as B1). Test corrected.
- **Retries:** ruff import/line-length/format
- **Human feedback:** stop after 2.4; wait for approval
- **Decision:** kept (pending approval)
- **Rationale:** Implementation matches the contract with a stricter inert-unknown rule (D-036).
- **Lessons learned:** Negative search evidence is not a skip warrant. `compare` must stay B0 vs B1.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 64 passed; `python -m agentic_cicd benchmark --system ladder --output outputs/benchmark-e004`
- **Still undecided:** whether to add S15+; whether to spend a paid `B2_API_KEY` run; GHA; dirty-promote development pointer. Paid API spend rejected in I-012 / D-038–D-039 (docs only).

### [I-012] 2026-08-29 — Phase 2.5 provider / reproducibility investigation

- **Iteration ID:** I-012
- **Date:** 2026-08-29
- **Objective:** Decide how a real model could be consumed without extra spend, without treating Cursor chat as B2, and without changing runtime behavior.
- **Hypothesis:** A Cursor subscription does not provide a B2 chat-completions endpoint. The existing OpenAI-compatible adapter plus offline B1 fallback is enough for judges; a later $0 live path should be local.
- **Changes:** Added `docs/AGENT_PROVIDER_RESEARCH.md`, `docs/CURSOR_ENVIRONMENT.md`. Updated decision/roadmap/changelog/experiment logs and README pointers. **No `src/` or scenario edits.**
- **Agent / model used:** Cursor Grok 4.6 (session identity; see CURSOR_ENVIRONMENT.md). No runtime B2 model.
- **Agent mode / tooling:** Cursor Agent mode, Phase 2.5 conversation.
- **Prompt / instructions:** Human Phase 2.5 brief: investigation only; $0; no credentials; no B2 behavior change; stop before implementation.
- **Files changed:** docs listed above; README documentation map
- **Experiments performed:** E-005 (docs/research only; no live call)
- **Baseline result:** E-004 unchanged (B2 = B1, 0 invocations)
- **New result:** none measured
- **Metrics:** not a cost experiment
- **Failures:** HackerEarth challenge page timed out; Cursor `/terms/ai` 404
- **Retries:** none
- **Human feedback:** stop after 2.5; wait for approval
- **Decision:** kept (pending approval). D-038–D-040
- **Rationale:** Official Cursor API is the wrong shape and is usage-billed. Do not invent a free hosted API.
- **Lessons learned:** “Already paying for Cursor” ≠ “B2 can call this chat.”
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 64 passed. No `src/`, `tests/`, or `benchmark/scenarios.json` edits in this phase.
- **Still undecided:** whether to run local Ollama next; whether to add S15+; GHA.

### [I-013] 2026-08-29 — Phase 2.6 free local agent integration

- **Iteration ID:** I-013
- **Date:** 2026-08-29
- **Objective:** Run the first real B2 agent at $0 API cost through the existing provider abstraction. Do not change B0, B1, S01–S14, or the verifier.
- **Hypothesis:** Local Ollama can be invoked on conservative residues. On S01–S14, B2 should match B1. Agent value needs conceptual S16 (off-suite), not a silent S14 edit.
- **Changes:** Local settings (`qwen2.5:3b`, no key); runtime probe; HTTP 400 tool-schema retry; post-tool JSON nudge; `b2_record` fields (`started_at`, `local`, `api_cost_usd`, `base_url`, `agent_error`); tests; `scripts/run_s16_like_local.py`; docs.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent, Fast + High, Extra High not used. Runtime B2: Ollama `qwen2.5:3b`.
- **Agent mode / tooling:** Cursor Agent mode, Phase 2.6 conversation. Live B2 via Docker → `host.docker.internal:11434`.
- **Prompt / instructions:** Human Phase 2.6 brief: one local model; real run; $0; no paid APIs; stop after 2.6; no commit.
- **Files changed:** `src/agentic_cicd/b2/{settings,provider,policy,agent,runner}.py`; `tests/test_b2.py`; `tests/test_benchmark.py` (env isolation only); `scripts/run_s16_like_local.py`; docs listed in the brief. No `benchmark/scenarios.json`. No B0/B1 scheduling changes.
- **Experiments performed:** E-006 (S01–S14 live), E-007 (off-suite S16-like)
- **Baseline result:** E-003/E-004 B0 375 / B1 220 / offline B2 220, 14/14, 0 false skips
- **New result:** E-006 B2 220, 14/14, 0 false skips, 2 invocations, 2 malformed fallbacks, 0 novel_accept, 0 novel_reject, $0. E-007 same fallback (`schema_version must be 1`).
- **Metrics:** `delta_vs_b1 = 0`. API spend $0. Mean live latency ~3–5 min/invocation on 8 GB CPU.
- **Failures:** Live model did not emit a valid `b2_proposal`. First pytest of the live-env docker inherited `B2_BASE_URL` and invoked the model; offline benchmark test now unsets those vars.
- **Retries:** ruff line-length/format; isolated pytest then E-007
- **Human feedback:** stop after 2.6; wait for approval
- **Decision:** kept (pending approval). D-041–D-043
- **Rationale:** Architecture is in place. Measured honesty: B2 equals B1 on the frozen suite; the 3B model is not yet a reliable proposer.
- **Lessons learned:** Invocation on S01–S14 is rare by design. Structured JSON is the bottleneck, not the verifier. Official S16 is justified to *request*, not to silently add.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 69 passed (offline env). Live ladder: `outputs/benchmark-e006/`. Live S16-like: `outputs/e006-s16-like/`.
- **Still undecided:** whether to add official S15/S16 after approval; whether a larger local model is worth another download; GHA.

### [I-014] 2026-08-29 — Phase 2.7 proposal validity

- **Iteration ID:** I-014
- **Date:** 2026-08-29
- **Objective:** Improve B2’s chance of emitting a valid machine-readable proposal on the pinned local model. Do not weaken the verifier or change B0/B1/S01–S14.
- **Hypothesis:** Prompt/schema instructions, a compact `copy_b1` wire form, fewer local tool rounds, and one repair turn can turn E-007’s malformed JSON into a validated proposal. Value still requires a verifier-accepted narrower plan.
- **Changes:** `prompts.py` (`b2-proposal-v3`); `copy_b1` expansion; JSON extract + one repair; local tools off; optional `response_format` for hosted JSON rounds; record `prompt_id` / `repair_attempted` / `raw_response_preview`; tests; `scripts/run_proposal_validity_local.py`.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent mode. Runtime B2: Ollama `qwen2.5:3b`.
- **Agent mode / tooling:** Cursor Agent. Live B2 via Docker → host Ollama.
- **Prompt / instructions:** Human Phase 2.7 brief: improve proposal validity; keep verifier; no paid APIs; no S01–S14 edits; stop for approval.
- **Files changed:** `src/agentic_cicd/b2/{prompts,agent,schema,provider,settings,context,runner}.py`; `tests/test_b2.py`; scripts above; docs. No `benchmark/scenarios.json`. No verifier rule changes.
- **Experiments performed:** E-008
- **Baseline result:** E-007 S16-like malformed (`schema_version must be 1`), 215 s, cost 31
- **New result:** E-008 S16-like **valid** proposal in 31 s, cost 31, novel_accept 0. S14-like still malformed. Timeouts on larger prompts.
- **Metrics:** Validity improved on the S16-like shape. `delta_vs_b1` simulated cost **0**. Not claimed as an optimization win.
- **Failures:** Attempts A–C timed out. S14-like omitted `decision`.
- **Retries:** ruff; four live prompt shapes
- **Human feedback:** stop after this micro-phase; wait for approval
- **Decision:** kept (pending approval). D-044–D-045
- **Rationale:** The 3B model can copy a short JSON object. It still rarely proposes a checkable narrower SKIP.
- **Lessons learned:** Asking a 3B CPU model to emit ten full job objects is the bottleneck. Empty `copy_b1` is valid but not valuable.
- **Verification performed:** `python:3.12-slim` ruff clean; pytest 80 passed. Live records in `outputs/e008-*` (gitignored).
- **Still undecided:** official S15/S16; larger local model; whether `copy_b1` empty-jobs should skip invocation (`not_worth_it`).

### [I-015] 2026-08-29 — Phase 2.8 agent-value benchmark design

- **Iteration ID:** I-015
- **Date:** 2026-08-29
- **Objective:** Define how to tell whether B2 adds value over B1 under $0, without implementing a new model, verifier change, or S15+ rows.
- **Hypothesis:** S01–S14 cannot show Q1. A small S15–S18 design plus split Q1/Q2 metrics is enough to evaluate a future model on the same terms.
- **Changes:** Added [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md). Updated AGENT_DESIGN §9.2, BENCHMARK, logs, Cursor assessment. Test asserts S15/S16 IDs are absent from `scenarios.json`.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent mode. No new B2 live run.
- **Agent mode / tooling:** Cursor Agent. Phase 2.8 conversation.
- **Prompt / instructions:** Human brief: design agent-value methodology; two research questions; S15+ definitions; latency/$; Cursor critical assessment; no B0/B1/S01–S14/verifier edits.
- **Files changed:** docs listed above; `tests/test_benchmark.py` (S15/S16 absence). No `src/` B2 behavior change. No `scenarios.json` rows.
- **Experiments performed:** E-009 (docs/assert only)
- **Baseline result:** E-003 B1 220; E-006/E-008 B2 `T` = B1
- **New result:** not a cost experiment
- **Metrics:** not measured
- **Failures:** none
- **Retries:** none
- **Human feedback:** stop after 2.8; wait for approval
- **Decision:** kept (pending approval). D-046–D-047
- **Rationale:** Making B2 win is not the objective. Q2 must be able to say “no” when the agent is slow.
- **Lessons learned:** S15-as-docs-only oracle is incompatible with D-036; record that instead of forcing a win row.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 80 passed. `benchmark/scenarios.json` still has only S01–S14.
- **Still undecided:** whether to *load* S16–S18 next; whether to try another local tag; GHA.

### [I-016] 2026-08-29 — Phase 2.9 official S16–S18 evaluation

- **Iteration ID:** I-016
- **Date:** 2026-08-29
- **Objective:** Implement S16–S18 as official agent-value scenarios and run controlled B1 / B2-offline / B2-live evaluation without manufacturing a win.
- **Hypothesis:** B1 is conservative (`T` = 31/row). A capable agent could save 9+12+9. `qwen2.5:3b` is more likely to copy B1 (E-008).
- **Changes:** `benchmark/agent_value_scenarios.json`; `--scenarios`; ladder Q1/Q2 fields; tests; docs. No B0/B1/verifier/`scenarios.json` edits.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent mode. Runtime B2 live: Ollama `qwen2.5:3b`.
- **Agent mode / tooling:** Cursor Agent. Phase 2.9 conversation.
- **Prompt / instructions:** Human Phase 2.9 brief: implement S16–S18; evaluate B1/B2; keep verifier; no paid APIs; no S01–S14 edits; stop for approval.
- **Files changed:** `benchmark/agent_value_scenarios.json`; `src/agentic_cicd/{cli.py,benchmark/{schema,runner,__init__}.py}`; `tests/test_agent_value_benchmark.py`; docs listed in the brief.
- **Experiments performed:** E-010
- **Baseline result:** B1 on S16–S18: `T` 93; 3/3; 0 false skips; 7 unnecessary
- **New result:** Offline B2 = B1 (93, 0 invocations). Live B2 = B1 (93, 3 valid `copy_b1`, 0 novel_accept, $0). Q1 parity. Q2 no (~101 s worse e2e).
- **Metrics:** see E-010
- **Failures:** no safety failure; 3B proposed no edges
- **Retries:** one live official pass
- **Human feedback:** stop after 2.9; wait for approval
- **Decision:** kept (pending approval). D-048–D-049
- **Rationale:** Official rows were required to answer Q1 honestly. A negative result is valid.
- **Lessons learned:** Missing official rows were not the blocker. The 3B model copies B1 even when needles are in the changed files.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 87 passed. `git diff` empty for `benchmark/scenarios.json`, B0, B1, and `b2/verifier.py`.
- **Still undecided:** whether to substitute a stronger model on the same rows; GHA. Closed for one local tag in I-017 (E-011 / D-050).

### [I-017] 2026-08-29 — Phase 2.10 stronger local model on S16–S18

- **Iteration ID:** I-017
- **Date:** 2026-08-29
- **Objective:** Run one controlled B2 experiment with one stronger free/local model on the official S16–S18 rows. Do not redesign B2, B1, the verifier, or the oracles.
- **Hypothesis:** If Q1 failed because `qwen2.5:3b` is too weak, `qwen3:4b-instruct` should raise `novel_accept` and lower `T`. If it also copies B1, the $0 local path is not enough to justify B2 as an optimizer.
- **Changes:** Pulled `qwen3:4b-instruct` (2.5 GB). Env-only `B2_MODEL`. Docs. No `src/` B2/B1/B0 edits. No suite edits.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent mode. Runtime B2 live: Ollama `qwen3:4b-instruct`.
- **Agent mode / tooling:** Cursor Agent. Phase 2.10 conversation (new chat; repo docs as source of truth).
- **Prompt / instructions:** Human Phase 2.10 brief: one stronger free/local model; same S16–S18; no paid APIs; no B2 redesign; stop for approval; no commit.
- **Files changed:** docs listed in the brief. No `benchmark/scenarios.json`. No B0/B1/verifier.
- **Experiments performed:** E-011
- **Baseline result:** E-010 B1 `T` 93; live 3B B2 `T` 93; novel_accept 0
- **New result:** E-011 B1 `T` 93; live 4B B2 `T` 93; novel_accept 0; S17 malformed fallback; Q1 parity; Q2 no (~173 s worse e2e)
- **Metrics:** see E-011
- **Failures:** no safety failure; 4B did not emit checkable edges
- **Retries:** one live official pass
- **Human feedback:** stop after this experiment; wait for approval
- **Decision:** kept (pending approval). D-050
- **Rationale:** A negative result on a stronger local model is the honest answer to “is it the 3B or is it B2?”
- **Lessons learned:** Next-generation 4B instruct on this host is not enough for Q1. 7B was correctly rejected. B1 remains the measured product under $0.
- **Verification performed:** Host `python` is the Windows Store stub. In `python:3.12-slim`: ruff clean; `python -m pytest` 87 passed. `git diff` empty for `benchmark/scenarios.json`, B0, B1, and `b2/verifier.py`.
- **Still undecided:** paid-model substitution (if ever); GHA.

### [I-018] 2026-08-29 — Phase 3.0 final consolidation

- **Iteration ID:** I-018
- **Date:** 2026-08-29
- **Objective:** Audit the repo for judges. Name B1 as the presented optimizer. Keep B2 as a documented miss. Do not add features or manufacture wins.
- **Hypothesis:** Stale mid-project README language and a few outdated B2/PROBLEM_FRAMING sentences are the main submission gaps. The numbers already exist in E-002/E-003/E-010/E-011.
- **Changes:** Judge-facing README; `docs/INSIGHTS.md`; B0/B1/B2/ROADMAP labels; stale B2 §7 and PROBLEM_FRAMING status; Cursor Phase 3.0 session (Fast + High from this brief); D-051. CLI description only. No suite, verifier, B0/B1 planner, or S01–S18 edits.
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent, Fast + High (human brief). No new B2 live run.
- **Agent mode / tooling:** Cursor Agent. Final-consolidation conversation.
- **Prompt / instructions:** Human Phase 3.0 brief: audit requirements; verify numbers; distinguish B0/B1/B2/Cursor/Ollama; reproduce path; safety; changelog story; Cursor env; fix only necessary gaps; no commit.
- **Files changed:** `README.md`, `docs/INSIGHTS.md`, `docs/{B0,B1,B2,ROADMAP,PROBLEM_FRAMING,CURSOR_ENVIRONMENT,CURSOR_DISCOVERIES,DECISION_LOG,IMPROVEMENT_CHANGELOG,EXPERIMENT_LOG,BENCHMARK}.md`, `pyproject.toml`, `src/agentic_cicd/cli.py` (help text).
- **Experiments performed:** E-012 (verification only)
- **Baseline result:** E-003 B0 375 / B1 220; E-010/E-011 B2 `T` = B1
- **New result:** not a cost experiment
- **Metrics:** not re-claimed; E-012 re-runs compare + tests
- **Failures:** none intended
- **Retries:** none
- **Human feedback:** stop after consolidation; wait for approval
- **Decision:** kept (pending approval). D-051
- **Rationale:** Judges need one product and an honest rejected path.
- **Lessons learned:** Documentation drift (B2 still described as “the optimizer”; S16–S18 still “not official” in B2.md) is a real submission risk even when the code is correct.
- **Verification performed:** In `python:3.12-slim`: `benchmark --system compare --output outputs/benchmark-e012` → B0 **375**, B1 **220**, reduction 41.3333%, `optimization_win_eligible` true; `python -m pytest` 87 passed; ruff clean; 66 files already formatted.
- **Still undecided:** GHA; paid B2 (explicitly out of this submission).

### [I-019] 2026-08-29 — Phase 3.1 judge reproduction and Git topology

- **Iteration ID:** I-019
- **Date:** 2026-08-29
- **Objective:** Make the public repository clone-and-run. Separate simulated CI flow names from Git branches. Do not change B0, B1, B2, the verifier, or scenarios.
- **Hypothesis:** A judge can reproduce B0→B1 from a clean Python environment with no credentials, Cursor, Ollama, GitHub Actions, or extra Git branches. The remaining confusion is wording (`feature`/`development`/`main`, PRs, GHA, optional B2).
- **Changes:** README complete clone path with B0 / B1 / optional B2 labels and expected numbers; public-`main` topology; PROBLEM_FRAMING §4/§10; BENCHMARK command labels; optional-B2 clarifications; trajectory-gap note. No `src/` behavior edits. No commit (explicit).
- **Agent / model used:** Coding: Cursor Grok 4.6, Agent mode. No B2 live run.
- **Agent mode / tooling:** Cursor Agent. Phase 3.1 conversation.
- **Prompt / instructions:** Human Phase 3.1 brief: reproduction path; label commands; expected results; B2 optional; Git topology; search/correct misleading judge text; GHA not required; agent-role audit; honest story; trajectory gaps; tests; Docker judge path if possible; no commit.
- **Files changed:** `README.md`, `docs/{PROBLEM_FRAMING,BENCHMARK,AGENT_PROVIDER_RESEARCH,AGENT_VALUE_BENCHMARK,AGENT_DESIGN,ROADMAP,INSIGHTS,CURSOR_ENVIRONMENT,CURSOR_DISCOVERIES,DECISION_LOG,IMPROVEMENT_CHANGELOG,EXPERIMENT_LOG,OPTIMIZATION_CONTRACT,B2}.md`, `scripts/judge_repro.sh`, `scripts/judge_repro_docker_entry.sh`, `.gitattributes`
- **Experiments performed:** E-013 (judge-path verification)
- **Baseline result:** E-003 / E-012 B0 375 / B1 220
- **New result:** not a cost experiment
- **Metrics:** same headline numbers if E-013 matches
- **Failures:** none intended
- **Retries:** none
- **Human feedback:** stop after audit; no commit
- **Decision:** kept. D-052
- **Rationale:** Judges should not reconstruct the participant’s Git workflow.
- **Lessons learned:** Simulated promotion language is easy to misread as a required GitHub process. Zero-commit `main` is a separate publication blocker.
- **Verification performed:** E-013 in `python:3.12-slim`: B0 **375**, B1 **220**, `cost_reduction_pct=0.413333`, 87 tests passed, ruff clean. No keys, no Ollama, no GHA.
- **Still undecided:** first commit and push (participant action; not done here). Paid B2 remains out of scope.
