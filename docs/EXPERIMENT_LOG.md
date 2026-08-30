# Experiment log

This file records **actual experiments only**.

- Do not add placeholder results.
- Do not copy hoped-for metrics into the “result” fields.
- If an idea has not been run, it does not belong here as a completed experiment. Put it in the roadmap or decision log instead.

**Experiments recorded:** E-001–E-013. Do not overwrite earlier entries. E-003 is the B0→B1 win. E-010/E-011 are B2 misses. E-012/E-013 are verification, not new optimizers. Phase 3.2 (D-053) is documentation only: there is **no E-014**. Do not invent a suite re-run for the Git-detector freeze.

---

## [E-001] 2026-08-29 — B0 on S01–S14

- **Experiment ID:** E-001
- **Date:** 2026-08-29
- **Related iteration:** I-006
- **Objective:** Measure the unoptimized B0 runner on the fixed S01–S14 suite.
- **Hypothesis:** B0 executes every legal job, so false-skip rate is 0. It will over-execute relative to required_jobs. Dirty promote (S10) may fail because B0 refuses to promote a new artifact id.
- **Setup:**
  - environment: `python:3.12-slim` (host `python` not on PATH)
  - software / versions: project 0.1.0, pytest 9.1.1, ruff 0.16.5
  - data / fixtures: `benchmark/scenarios.json`, `fixtures/`, `configs/`
  - commands: `python -m agentic_cicd benchmark --output outputs/benchmark`
  - model / agent: none
  - baseline condition: B0
  - treatment condition: none
- **What was measured:** suite simulated cost, per-scenario cost, wall-clock, jobs executed, correctness vs ground truth, false skips, unnecessary jobs
- **Results:**
  - baseline: 14 scenarios; simulated_cost **401**; median scenario cost **31**; jobs_executed **116**; unnecessary_jobs **44**; false_skip_count **0**; correctness **13/14 (0.928571)**; wall_duration_ms **15091** (noisy)
  - S01–S09, S11–S14: correctness pass
  - **S10 failed** B0 promote: rebuilt id ≠ development pointer (expected limitation)
  - treatment: not run
  - delta: not applicable
- **Failures / errors:** S10 `promote` error: rebuilt artifact does not match validated development artifact
- **Retries:** none after the identity-path fix (absolute workspace paths had made artifact ids non-portable)
- **Notes / confounds:** Wall-clock is container/host dependent. Feature→dev scenarios each cost 31 because B0 always runs the full legal graph. Generated JSON is in `outputs/benchmark/` (not source).
- **Decision that followed:** D-020 (keep S10 ground truth; do not weaken it to match B0)
- **Status:** completed

---

## [E-002] 2026-08-29 — Corrected B0 on S01–S14

- **Experiment ID:** E-002
- **Date:** 2026-08-29
- **Related iteration:** I-007
- **Objective:** Re-measure B0 on the same S01–S14 suite after correcting dirty-promote semantics. Not an optimizer experiment.
- **Hypothesis:** After the Phase 1.6.1 correction, S09 still reuses the development artifact id, S10 promotes a new validated artifact, S11 still fails closed, and suite correctness becomes 14/14 with false-skip rate 0. Cost may change because S09 no longer rebuilds and S10 now executes `promote`. That is a correctness fix, not an optimization.
- **Setup:**
  - environment: `python:3.12-slim` (host `python` not on PATH)
  - software / versions: project 0.1.0; `pip install -e ".[dev]"` in `python:3.12-slim` (same class as E-001)
  - data / fixtures: unchanged `benchmark/scenarios.json`, `fixtures/`, `configs/`
  - commands: `python -m agentic_cicd benchmark --output outputs/benchmark-e002`
  - model / agent: none
  - baseline condition: corrected B0
  - treatment condition: none
- **What was measured:** suite simulated cost, per-scenario cost, wall-clock, jobs executed, correctness vs the same ground truth, false skips, unnecessary jobs
- **Results:**
  - baseline (corrected B0): 14 scenarios; simulated_cost **375**; median scenario cost **31**; jobs_executed **110**; unnecessary_jobs **37**; false_skip_count **0**; correctness **14/14 (1.0)**; wall_duration_ms **13103.446** (noisy)
  - S01–S14: correctness pass
  - S09: cost 3; executed `branch_guard`, `promote`; artifact_id equals seed
  - S10: cost 31; executed full legal rebuild including `promote`; artifact_id differs from seed; production receives the new id
  - S11: failed `branch_guard`; no promote
  - treatment: not run
  - delta vs E-001: cost 401 → 375; jobs 116 → 110; unnecessary 44 → 37; correctness 13/14 → 14/14. **Not an optimization improvement.** S09 dropped 28 cost units because clean promote no longer rebuilds. S10 rose from 29 to 31 because `promote` now executes successfully.
- **Failures / errors:** none on the suite
- **Retries:** two lint-only retries (ruff E501, ruff format) before this recorded run
- **Notes / confounds:** Same scenarios and ground truth as E-001. Generated JSON is in `outputs/benchmark-e002/` so E-001’s `outputs/benchmark/` is not overwritten. Wall-clock is container/host dependent.
- **Decision that followed:** D-021 (correct B0 promote; keep S10 ground truth)
- **Status:** completed

---

## How to log an experiment

When an experiment is actually performed, copy this template.

```md
## [E-XXX] YYYY-MM-DD — short title

- **Experiment ID:** E-XXX
- **Date:** YYYY-MM-DD
- **Related iteration:** I-XXX (IMPROVEMENT_CHANGELOG)
- **Objective:**
- **Hypothesis:**
- **Setup:**
  - environment:
  - software / versions:
  - data / fixtures:
  - commands:
  - model / agent (if any):
  - baseline condition:
  - treatment condition:
- **What was measured:**
- **Results:**
  - baseline:
  - treatment:
  - delta:
- **Failures / errors:**
- **Retries:**
- **Notes / confounds:**
- **Decision that followed:** (link D-XXX)
- **Status:** completed | aborted | invalid
```

---

## [E-003] 2026-08-29 — B0 vs B1 on S01–S14

- **Experiment ID:** E-003
- **Date:** 2026-08-29
- **Related iteration:** I-009
- **Objective:** Measure the deterministic B1 optimizer on the same frozen S01–S14 suite as B0. Not an agent experiment.
- **Hypothesis:** An impact-graph planner with identity-checked cache can reduce suite simulated cost versus B0 while keeping false-skip rate 0 and correctness 14/14, including S12 (overlay is a score input) and S14 (unknown → full graph).
- **Setup:**
  - environment: `python:3.12-slim` (host `python` is the Windows Store stub)
  - software / versions: project 0.1.0; `pip install -e ".[dev]"`
  - data / fixtures: unchanged `benchmark/scenarios.json`, `fixtures/`, `configs/`
  - commands: `python -m agentic_cicd benchmark --system compare --output outputs/benchmark-e003`
  - model / agent: none
  - baseline condition: B0 (same semantics as E-002)
  - treatment condition: B1
- **What was measured:** suite simulated cost, median, jobs executed, unnecessary jobs, false skips, correctness, per-scenario cost and executed jobs, wall-clock (noisy)
- **Results:**
  - baseline (B0): simulated_cost **375**; median **31**; jobs_executed **110**; unnecessary_jobs **37**; false_skip_count **0**; correctness **14/14**; wall_duration_ms **14760.555** (noisy)
  - treatment (B1): simulated_cost **220**; median **19**; jobs_executed **73**; unnecessary_jobs **0**; false_skip_count **0**; correctness **14/14**; illegal_promotion_accepted **0**; wall_duration_ms **14432.445** (noisy)
  - delta: cost 375 → 220 (**−155**, **41.3333%**); jobs 110 → 73; unnecessary 37 → 0. **optimization_win_eligible = true**
  - per scenario (B0 cost → B1 cost): S01 31→1; S02 31→4; S03 31→22; S04 31→28; S05 31→26; S06 31→19; S07 31→31; S08 31→2; S09 3→3; S10 31→22; S11 0→0; S12 31→19; S13 31→12; S14 31→31
- **Failures / errors:** none on the suite
- **Retries:** lint/format and one clean-promote hydrate fix before this recorded run (promote reuse must not require a bundle cache)
- **Notes / confounds:** Same ground truth as E-002. B1 cache is warmed from pre-apply fixtures (not charged as scenario cost). Wall-clock is container/host dependent and similar for B0 and B1 because skipped jobs still do little I/O. Generated JSON is in `outputs/benchmark-e003/` (not source). This is not an agent improvement.
- **Decision that followed:** D-026–D-029
- **Status:** completed

## [E-004] 2026-08-29 — B0 vs B1 vs B2 on S01–S14

- **Experiment ID:** E-004
- **Date:** 2026-08-29
- **Related iteration:** I-011
- **Objective:** Measure the new B2 runner on the frozen S01–S14 suite against B0 and B1. Expect reproduction of B1, not a cheaper plan.
- **Hypothesis:** Without `B2_API_KEY`, B2 will not invoke the agent on conservative rows (S07/S14 → `offline`) and will match B1 on every scenario. A cheaper B2 would be a defect.
- **Setup:**
  - environment: `python:3.12-slim` (host `python` is the Windows Store stub)
  - software / versions: project 0.1.0; `pip install -e ".[dev]"`
  - data / fixtures: unchanged `benchmark/scenarios.json`, `fixtures/`, `configs/`
  - commands: `python -m agentic_cicd benchmark --system ladder --output outputs/benchmark-e004`
  - model / agent: none invoked (`B2_API_KEY` unset)
  - baseline condition: B0 and B1 (same semantics as E-003)
  - treatment condition: B2
- **What was measured:** suite simulated cost, correctness, false skips, unnecessary jobs, agent invocation count, novel_accept / novel_reject, fallback count, agent latency, estimated model USD
- **Results:**
  - B0: simulated_cost **375**; median **31**; jobs_executed **110**; unnecessary_jobs **37**; false_skip_count **0**; correctness **14/14**; wall_duration_ms **14923.12** (noisy)
  - B1: simulated_cost **220**; median **19**; jobs_executed **73**; unnecessary_jobs **0**; false_skip_count **0**; correctness **14/14**; wall_duration_ms **13544.781** (noisy)
  - B2: simulated_cost **220**; median **19**; jobs_executed **73**; unnecessary_jobs **0**; false_skip_count **0**; correctness **14/14**; wall_duration_ms **14848.862** (noisy)
  - delta vs B1: **0**
  - agent_invocation_count **0**; no_invoke_count **14**; novel_accept **0**; novel_reject **0**; fallback_count **0**; estimated_cost_usd **0.0**; agent_latency_ms **0.0**
  - invocation reasons: S01–S06, S08–S10, S12–S13 = `b1_sufficient`; S07, S14 = `offline`; S11 = `illegal_flow`
  - safety_gate / optimization_win_eligible vs B0: true (same as B1). **Not claimed as a win vs B1.**
- **Failures / errors:** none on the suite
- **Retries:** none for this recorded run (lint/unit fixes preceded it)
- **Notes / confounds:** No live model. This does not test gpt-4o-mini quality. Unit tests (not this suite) show verifier `novel_accept` on a synthetic import edge and `novel_reject` on inert-unknown. Generated JSON is in `outputs/benchmark-e004/` (not source).
- **Decision that followed:** D-035–D-037; recommend S15+ (not implemented)
- **Status:** completed

## [E-005] 2026-08-29 — Provider research (no live model)

- **Experiment ID:** E-005
- **Date:** 2026-08-29
- **Related iteration:** I-012
- **Objective:** Confirm that an investigation-only phase does not change measured B0/B1/B2 behavior, and record that **no** paid or live model request was made.
- **Hypothesis:** Documentation-only edits leave E-004 semantics intact. Tests still pass.
- **Setup:**
  - environment: `python:3.12-slim` (same as prior phases; host `python` is the Windows Store stub)
  - software / versions: project 0.1.0
  - data / fixtures: unchanged
  - commands: `python -m pytest` after the doc updates (no `benchmark` re-run; no HTTP to a model host)
  - model / agent: none for B2. Coding agent: Cursor Grok 4.6 (session identity)
  - baseline condition: E-004
  - treatment condition: docs only
- **What was measured:** test pass/fail; confirmation that `src/` and `benchmark/scenarios.json` were not edited for this phase
- **Results:**
  - no new suite costs (E-004 remains the B2 number: 220 / 14/14 / 0 invocations)
  - no model USD
  - no credentials created
- **Failures / errors:** external page timeouts (HackerEarth challenge; Cursor terms/ai 404) — research gaps only
- **Retries:** none
- **Notes / confounds:** This is not an optimization experiment. Findings are in [AGENT_PROVIDER_RESEARCH.md](AGENT_PROVIDER_RESEARCH.md).
- **Decision that followed:** D-038–D-040
- **Status:** completed

## [E-006] 2026-08-29 — First live local B2 on S01–S14

- **Experiment ID:** E-006
- **Date:** 2026-08-29
- **Related iteration:** I-013
- **Objective:** Run the first real B2 agent through local Ollama on the frozen S01–S14 suite. Expect B1 reproduction, not a cheaper plan.
- **Hypothesis:** Policy will invoke only S07 and S14 (`conservative_residue`). A 3B CPU model may fail structured JSON. Verifier / fallback will keep B1. Correctness stays 14/14. False skips stay 0.
- **Setup:**
  - environment: `python:3.12-slim` bind-mounted to the repo; host Ollama 0.33.2 on Windows 8 GB RAM
  - software / versions: project 0.1.0; `pip install -e ".[dev]"`
  - data / fixtures: unchanged `benchmark/scenarios.json`, `fixtures/`, `configs/`
  - commands: `B2_BASE_URL=http://host.docker.internal:11434/v1 B2_MODEL=qwen2.5:3b B2_TIMEOUT_S=180 B2_MAX_TOOL_ROUNDS=4 python -m agentic_cicd benchmark --system ladder --output outputs/benchmark-e006`
  - model / agent: **qwen2.5:3b** (3.1B, Q4_K_M, digest `357c53fb659c`); provider `openai_compatible`; Phase 2.3 read-only tools; structured `b2_proposal` requested
  - coding agent (not B2): Cursor Grok 4.6, Agent, Fast + High, Extra High not used
  - baseline condition: B0 and B1 (same semantics as E-003)
  - treatment condition: live local B2
- **What was measured:** suite simulated cost, correctness, false skips, unnecessary jobs, invocations, novel_accept / novel_reject, fallback, latency, API USD
- **Results:**
  - B0: simulated_cost **375**; jobs_executed **110**; unnecessary **37**; false_skip **0**; correctness **14/14**; wall_duration_ms **12285.316** (noisy)
  - B1: simulated_cost **220**; jobs_executed **73**; unnecessary **0**; false_skip **0**; correctness **14/14**; wall_duration_ms **12882.83** (noisy)
  - B2: simulated_cost **220**; jobs_executed **73**; unnecessary **0**; false_skip **0**; correctness **14/14**; job-only wall_duration_ms **12250.918** (noisy; excludes most model wait in the job timer)
  - delta vs B0: **−155** (same as B1). delta vs B1: **0**
  - agent_invocation_count **2**; no_invoke_count **12**; novel_accept **0**; novel_reject **0**; fallback_count **2**; estimated_cost_usd / api_cost_usd **0.0**; agent_latency_ms **485232.161**
  - invocation reasons: S01–S06, S08–S10, S12–S13 = `b1_sufficient`; S11 = `illegal_flow`; S07 and S14 = `conservative_residue`
  - S07: latency **287366 ms**; tools `inspect_b1_plan`; `proposal` null; `fallback_reason` **malformed**; executed full B1 graph (cost 31)
  - S14: latency **197867 ms**; tools `classify_path` on `unknown/orphan.dat`; `proposal` null; `fallback_reason` **malformed**; executed full B1 graph (cost 31)
  - verifier rejection rate on structured proposals: **n/a** (no valid proposal reached the verifier). Invocation fallback rate: **2/2**
  - safety_gate / optimization_win_eligible vs B0: true (same as B1). **Not a win vs B1.**
- **Failures / errors:** both live proposals malformed. S07/S14 records predate `agent_error` field; later E-007 captured `schema_version must be 1`.
- **Retries:** none for this recorded ladder run
- **Notes / confounds:** Default 30 s timeout is too short for CPU 3B (180 s used). Small models may HTTP 400 on OpenAI tool schema; client retries without tools. Wall-clock of the whole ladder was ~10 minutes, dominated by two inferences. Generated JSON is in `outputs/benchmark-e006/` (not source). S01–S14 were not edited.
- **Decision that followed:** D-041–D-043
- **Status:** completed

## [E-007] 2026-08-29 — Off-suite conceptual S16 (not added to the suite)

- **Experiment ID:** E-007
- **Date:** 2026-08-29
- **Related iteration:** I-013
- **Objective:** See whether a real local agent can demonstrate value on the already-documented S16 shape (unknown file that imports `score`) without editing `scenarios.json`.
- **Hypothesis:** B1 runs the full graph. If the model emits a valid localized proposal with a checkable import edge, the verifier may `novel_accept`. If it proposes an unsafe skip, `novel_reject`. If JSON is invalid, fallback to B1 (neither novel flag).
- **Setup:**
  - environment: same Docker + host Ollama as E-006
  - commands: `B2_BASE_URL=http://host.docker.internal:11434/v1 B2_MODEL=qwen2.5:3b B2_TIMEOUT_S=180 B2_MAX_TOOL_ROUNDS=4 python scripts/run_s16_like_local.py`
  - workspace file: `scripts/tune_weights.py` containing `import agentic_cicd.ranker.score`; `changed_paths=["scripts/tune_weights.py"]`
  - model / agent: `qwen2.5:3b`
  - this is **not** an official suite row
- **What was measured:** invoke, proposal validity, verifier, novel flags, latency, executed jobs, cost
- **Results:**
  - B1 / final plan: full feature→dev graph; simulated_cost **31**
  - agent_invoked **true**; invocation_reason_code `conservative_residue`
  - tool_trace: `inspect_b1_plan` only
  - fallback_reason **malformed**; agent_error **`schema_version must be 1`**; proposal **null**
  - novel_accept **[]**; novel_reject **[]**
  - latency_ms **215023.529**; api_cost_usd **0.0**
  - workflow **succeeded** (B1 fallback executed)
- **Failures / errors:** model produced JSON that failed `schema_version must be 1`. No accepted or rejected novel skip.
- **Retries:** none
- **Notes / confounds:** Unit tests already show `novel_accept` / `novel_reject` with `FakeProvider`. The **live** 3B model did not reach the verifier. Official S16 is still justified as a future suite row, but adding it now would not have changed E-007’s measured flags.
- **Decision that followed:** D-043 — document the need; do not implement S15–S21
- **Status:** completed

## [E-008] 2026-08-29 — Proposal-validity prompts on local qwen2.5:3b

- **Experiment ID:** E-008
- **Date:** 2026-08-29
- **Related iteration:** I-014
- **Objective:** See whether prompt/schema-instruction changes can produce a **valid** `b2_proposal` from the same local model without weakening the verifier. Not a suite cost experiment.
- **Hypothesis:** A compact `copy_b1` template, fewer tool rounds, and one repair turn will raise validity versus E-007 (`schema_version must be 1`). A valid proposal still must pass the verifier. Cost may stay equal to B1.
- **Setup:**
  - environment: `python:3.12-slim` → host Ollama 0.33.2; Windows ~8 GB RAM; CPU
  - model: **qwen2.5:3b** digest `357c53fb659c`
  - coding agent: Cursor Grok 4.6 (this chat; not B2)
  - commands: `scripts/run_proposal_validity_local.py` with `B2_BASE_URL=http://host.docker.internal:11434/v1`
  - S01–S14 not modified; cases are off-suite S16-like and S14-like
- **What was measured:** validity, repair, tools, latency, fallback, novel flags, simulated cost
- **Results:**
  - Attempt A (v2 prompt + tools, timeout 180 s): both cases **timeout**. No proposal.
  - Attempt B (tools off + `json_object`, timeout 300 s): both cases **timeout**.
  - Attempt C (slim prompt, timeout 240 s): S16-like **timeout**.
  - Attempt D (`b2-proposal-v3` compact `copy_b1`, tools off, no local json_object, timeout 180 s):
    - **S16-like:** proposal **valid**; `copy_b1` + `jobs: []`; expanded to all-RUN; verifier `used_proposal=true`; novel_accept **0**; novel_reject **0**; cost **31** (= B1); latency **30951 ms**; prompt_tokens 412; completion_tokens 28; repair false; tools 0; API **$0**
    - **S14-like:** **malformed** (`test: decision must be RUN or SKIP`); repair_attempted true; still no valid proposal; cost **31**; latency **24967 ms**; API **$0**
  - Tiny Ollama health check (`max_tokens=8`) after earlier timeouts: **2613 ms**, content `Ok` — runtime was alive.
- **Failures / errors:** Large templates and tool/`json_object` combinations exceeded 180–300 s. S14-like listed `{"job":"test"}` without `decision`.
- **Retries:** four live prompt shapes; unit-tested `copy_b1` missing-decision → RUN after the S14-like miss (not re-run live)
- **Notes / confounds:** Not an S01–S14 ladder. Valid S16-like proposal **equals B1** (no extra SKIP). That is a validity improvement, not an optimization win.
- **Decision that followed:** D-044, D-045
- **Status:** completed

## [E-009] 2026-08-29 — Agent-value benchmark design (no new suite run)

- **Experiment ID:** E-009
- **Date:** 2026-08-29
- **Related iteration:** I-015
- **Objective:** Record that this phase is methodology only: no new official scenarios executed, no model swap, no verifier change.
- **Hypothesis:** Existing tests still pass; `scenarios.json` still contains only S01–S14.
- **Setup:**
  - environment: `python:3.12-slim`
  - commands: `python -m pytest`; `python -m ruff check .`; `python -m ruff format --check .`
  - model / agent: none for B2. Coding agent: Cursor Grok 4.6
- **What was measured:** test pass/fail; presence/absence of S15+ in `benchmark/scenarios.json`
- **Results:**
  - no new `T` / `W_e2e` numbers
  - S01–S14 unchanged (`test_all_scenarios_load` plus S15/S16 id absence)
  - ruff clean; **80** tests passed
  - no paid API
- **Failures / errors:** none expected for a docs+assert phase
- **Retries:** none
- **Notes / confounds:** Not an optimization experiment. Definitions live in [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md).
- **Decision that followed:** D-046, D-047
- **Status:** completed

## [E-010] 2026-08-29 — Official S16–S18 B1 / B2-offline / B2-live

- **Experiment ID:** E-010
- **Date:** 2026-08-29
- **Related iteration:** I-016
- **Objective:** Implement S16–S18 as official agent-value rows and measure whether B2 can beat conservative B1 under the Phase 2.8 Q1/Q2 rules.
- **Hypothesis:** B1 will over-run (full graph, `T` = 31 per row). Offline B2 will match B1. Live `qwen2.5:3b` may emit valid `copy_b1` (as in E-008) but is unlikely to propose checkable edges. A Q1 win requires `novel_accept` and `T_B2 < T_B1`.
- **Setup:**
  - environment: `python:3.12-slim` bind-mounted to the repo; host Ollama 0.33.2 on Windows ~8 GB RAM; CPU
  - software / versions: project 0.1.0; `pip install -e ".[dev]"`
  - model: **qwen2.5:3b** digest `357c53fb659c`; `B2_BASE_URL=http://host.docker.internal:11434/v1`; `B2_TIMEOUT_S=180`; tools off
  - coding agent: Cursor Grok 4.6 (this chat; not B2)
  - commands:
    - `python -m agentic_cicd benchmark --system optimized --scenarios benchmark/agent_value_scenarios.json --output outputs/benchmark-e010-b1`
    - same with `--system agentic` and no B2 env → `outputs/benchmark-e010-offline`
    - same with local Ollama env → `outputs/benchmark-e010-live`
  - S01–S14 / B0 / B1 / verifier not modified
- **What was measured:** `T`, jobs, unnecessary, correctness, false skips, illegal promotions, invocations, `W_agent`, `W_jobs`, `W_e2e`, tokens, `$`, used_proposal, novel_accept/reject, fallback
- **Results:**
  - **B1:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; illegal **0**; `W_jobs` **4458.195 ms**. Per row `T` = 31 (full graph). S16/S18 extra: ingest, prepare. S17 extra: test, ingest, prepare.
  - **B2 offline:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; invocations **0**; `used_proposal` 0; novel 0/0; tokens 0; `$0`; reason `offline`. `W_jobs` **4703.802 ms**. Q1 **parity**.
  - **B2 live:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; invocations **3**; `used_proposal` **3**; novel_accept **0**; novel_reject **0**; fallback **none** (valid `copy_b1`); `W_agent` **99932.644 ms**; `W_jobs` **5403.174 ms**; `W_e2e` **105335.818 ms**; tokens 1807 / 136; `$0`.
    - S16: 58521 ms; 412/28; `copy_b1` + `jobs: []`
    - S17: 26349 ms; 978/73; first draft `{"job":"validate"}` (no decision); repair → `copy_b1`
    - S18: 15062 ms; 417/35; `copy_b1` + `jobs: []`
  - Q1: **parity** (not a win). Potential save 30 unrealized.
  - Q2: **no**. Live e2e ~101 s worse than B1.
- **Failures / errors:** No safety failure. S17 needed one schema repair. The model did not emit `discovered_edges`.
- **Retries:** one live official pass (D-049: do not keep retrying this tag)
- **Notes / confounds:** Job walls are noisy and cheap. `W_e2e` uses `W_jobs + W_agent`. Offline B2 model field may show the hosted default name because no local URL was set; it did not invoke. Generated JSON is in `outputs/benchmark-e010-*` (not source).
- **Decision that followed:** D-048, D-049
- **Status:** completed

## [E-011] 2026-08-29 — Stronger local model on official S16–S18

- **Experiment ID:** E-011
- **Date:** 2026-08-29
- **Related iteration:** I-017
- **Objective:** Test whether B2’s Q1 miss on S16–S18 is the 3B model or a lack of agentic value, by substituting one stronger free/local model through the existing provider. No B2 redesign.
- **Hypothesis:** `qwen3:4b-instruct` (next Qwen generation, instruct, ~4B, same RAM class) will raise valid-edge / `novel_accept` rate versus `qwen2.5:3b`. A Q1 win still requires verifier-accepted hidden-edge discovery and `T_B2 < T_B1`. Q2 is separate.
- **Setup:**
  - environment: `python:3.12-slim` bind-mounted to the repo; host Ollama 0.33.2 on Windows 8 GB RAM (i3-7100U, Intel HD 620, CPU)
  - software / versions: project 0.1.0; `pip install -e ".[dev]"`
  - model: **`qwen3:4b-instruct`** digest `0edcdef34593`; 4.0B; Q4_K_M; 2.5 GB; `B2_BASE_URL=http://host.docker.internal:11434/v1`; `B2_TIMEOUT_S=180`; tools off
  - coding agent: Cursor Grok 4.6 (this chat; **not** B2)
  - commands:
    - `python -m agentic_cicd benchmark --system optimized --scenarios benchmark/agent_value_scenarios.json --output outputs/benchmark-e011-b1`
    - same with `--system agentic` and no B2 env → `outputs/benchmark-e011-offline`
    - same with local Ollama env + `B2_MODEL=qwen3:4b-instruct` → `outputs/benchmark-e011-live`
  - S01–S14 / B0 / B1 / verifier / S16–S18 oracles not modified
- **What was measured:** `T`, jobs, unnecessary, correctness, false skips, illegal promotions, invocations, `W_agent`, `W_jobs`, `W_e2e`, tokens, `$`, used_proposal, novel_accept/reject, fallback
- **Results:**
  - **B1:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; illegal **0**; `W_jobs` **6437.31 ms**. Per row `T` = 31 (full graph).
  - **B2 offline:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; invocations **0**; `used_proposal` 0; novel 0/0; tokens 0; `$0`; reason `offline`. `W_jobs` **8080.273 ms**. Q1 **parity**.
  - **B2 live:** `T` **93**; jobs **27**; unnecessary **7**; false skips **0**; correctness **3/3**; invocations **3**; `used_proposal` **2**; novel_accept **0**; novel_reject **0**; fallback **1** (S17 malformed); `W_agent` **172583.688 ms**; `W_jobs` **6900.012 ms**; `W_e2e` **179483.7 ms**; tokens 1855 / 233; `$0`.
    - S16: 91355 ms; 412/33; `copy_b1` + `jobs: []`; valid; novel 0
    - S17: 62015 ms; 1026/167; first draft `schema-version` (hyphen) and preview-shaped `discovered_edges`; repair failed; fallback B1
    - S18: 19214 ms; 417/33; `copy_b1` + `jobs: []`; valid; novel 0
  - vs E-010 (`qwen2.5:3b`): same `T` (93); same `novel_accept` (0); validity **worse** (2/3 vs 3/3); `W_agent` **slower** (173 s vs 100 s)
  - Q1: **parity** (not a win). Potential save 30 unrealized.
  - Q2: **no**. Live e2e ~173 s worse than this session’s B1.
- **Failures / errors:** No safety failure. S17 malformed (`schema_version must be 1`). The model did not emit a checkable `from_path` / `to_component` edge.
- **Retries:** one live official pass (one model only)
- **Notes / confounds:** Job walls are noisy. `W_e2e` uses `W_jobs + W_agent`. Health check before the suite: 30806 ms, `Ok`, loaded size 3.2 GB, num_ctx 4096. Generated JSON is in `outputs/benchmark-e011-*` (not source). S01–S14 SHA-256 unchanged (`D63F28050B84C4BE5862EE093B1FD13EDBF670A94FEF1451D51372DF542543B1`).
- **Decision that followed:** D-050
- **Status:** completed

E-001 through E-011 are recorded above. Do not invent additional optimizer runs.

## [E-012] 2026-08-29 — Consolidation verification (no new optimizer)

- **Experiment ID:** E-012
- **Date:** 2026-08-29
- **Related iteration:** I-018
- **Objective:** Confirm that the documented B0/B1 headline numbers still reproduce and that the test suite still passes after documentation consolidation. Not a new comparison design.
- **Hypothesis:** S01–S14 and B0/B1 are unchanged, so `--system compare` still reports B0 **375** and B1 **220** with `optimization_win_eligible` true. Pytest and ruff stay clean.
- **Setup:**
  - environment: `python:3.12-slim` bind-mounted to the repo (host `python` is the Windows Store stub)
  - commands: `python -m agentic_cicd benchmark --system compare --output outputs/benchmark-e012`; `python -m pytest`; `python -m ruff check .`; `python -m ruff format --check .`
  - model / agent: none for B2. Coding agent: Cursor Grok 4.6
- **What was measured:** suite simulated costs, safety gate, test/lint pass
- **Results:**
  - B0: simulated_cost **375**; jobs_executed **110**; unnecessary **37**; median **31**
  - B1: simulated_cost **220**; jobs_executed **73**; unnecessary **0**; median **19**; correctness **14/14**; false_skip_count **0**; `optimization_win_eligible` **true**
  - delta: **−155** / **41.3333%** (same as E-003)
  - pytest **87** passed; ruff check clean; ruff format **66** files already formatted
  - no B2 invocation
- **Failures / errors:** none
- **Retries:** none
- **Notes / confounds:** Does not replace E-003. Wall-clock omitted (noisy). Generated JSON is in `outputs/benchmark-e012/` (not source).
- **Decision that followed:** D-051
- **Status:** completed

## [E-013] 2026-08-29 — Clean-environment judge path (no new optimizer)

- **Experiment ID:** E-013
- **Date:** 2026-08-29
- **Related iteration:** I-019
- **Objective:** Run the documented judge commands in a clean `python:3.12-slim` tree (copy of the working directory, no host `.venv` / `outputs`). Confirm B0 and B1 headline numbers without credentials, Cursor, Ollama, GitHub Actions, or extra Git branches.
- **Hypothesis:** The same commands as the README produce B0 **375** and B1 **220** with `cost_reduction_pct=0.413333` (41.3333%), 14/14, 0 false skips. Pytest and ruff stay clean.
- **Setup:**
  - environment: `python:3.12-slim`; repo copied to `/work` (read-only bind mount of the working tree; **not** `git clone`, because local `main` has no commits and `origin` has no refs)
  - software / versions: Python 3.12.14; pytest 9.1.1; ruff 0.16.5
  - commands: `python -m pip install -e ".[dev]"`; `python -m agentic_cicd benchmark --output outputs/benchmark-b0`; `python -m agentic_cicd benchmark --system compare --output outputs/benchmark-compare`; `python -m pytest`; `python -m ruff check .`; `python -m ruff format --check .`
  - model / agent: none. No `B2_BASE_URL`, no `B2_API_KEY`. Coding agent: Cursor Grok 4.6
- **What was measured:** CLI totals, test count, ruff
- **Results:**
  - B0 baseline CLI: `simulated_cost=375`; `correctness_pass_rate=1.0`; `false_skip_count=0`; `optimization_win_eligible=True`
  - B1 compare CLI: `baseline_cost=375`; `optimized_cost=220`; `cost_reduction_pct=0.413333`; `false_skip_count=0`; `optimization_win_eligible=True`
  - pytest **87** passed in 6.97 s
  - ruff check: All checks passed; ruff format: 78 files already formatted
- **Failures / errors:** none
- **Retries:** first Docker attempt failed because a PowerShell-quoted `bash -c` did not run the script; reran via `scripts/judge_repro_docker_entry.sh`
- **Notes / confounds:** This is a clean **working-tree** copy, not a clone of GitHub. A stranger still cannot `git clone https://github.com/nzanini/agentic-cicd-optimization.git` until the first commit is created and pushed. Wall-clock omitted except pytest. Generated JSON stayed inside the container (`/work/outputs/`, not source).
- **Decision that followed:** D-052
- **Status:** completed
