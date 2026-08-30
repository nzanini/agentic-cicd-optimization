# Roadmap

This is a **living document**. If the project changes direction, the original idea stays here. Record what changed, why it changed, what evidence motivated the change, and what was retained.

Status labels used below:

| Label | Meaning |
| --- | --- |
| `hypothesis` | Intended direction; not demonstrated |
| `current` | True of the repository today |
| `planned` | Intended future work; details may still be open |
| `in progress` | Actively being done |
| `completed` | Done and reviewable |
| `rejected` | Tried or considered and explicitly not kept |

---

## Original project hypothesis

**Recorded:** 2026-08-28 (Phase 1.1)  
**Status:** `hypothesis`

CI/CD pipelines often run more work than a given change requires. An agent that inspects repository changes could select a sufficient job set, skipping jobs that are not needed, and thereby reduce time and compute without hiding required checks.

A second, related hypothesis is that promotion between symmetric environments (`feature → development → main/production`) is a distinct reasoning problem: not only “which files changed,” but also which validations already happened, what changed after those validations, which jobs must run again, which can be skipped, and whether the promoted artifact is the same object that was tested.

**User (working definition):** a software engineer or CI/platform owner who currently over-runs pipeline jobs because it is safer than reasoning about skip conditions by hand.

**Constraints that are part of the original idea:**

- Prefer a small, self-contained, reproducible simulation.
- Prefer local tools, Docker, GitHub Actions, synthetic or public data, and mocked expensive jobs. *(Historical. GitHub Actions was never added and is **not** required for judges. See D-052.)*
- Do not depend on paid cloud infrastructure for the final demo.
- Establish a simple baseline first; improve the agentic solution through measured iterations.
- Record evidence for every meaningful iteration. Do not fabricate results.

**Not part of the original idea (explicitly out of scope unless later evidence says otherwise):**

- Real AWS / Airflow / SageMaker / Kubernetes production infrastructure.
- A claim of measured improvement before experiments exist.

## Current project state

**As of:** 2026-08-29  
**Phase:** 3.1 — Final judge reproduction and repository topology  
**Status:** `in progress` (awaiting review)

| Area | State |
| --- | --- |
| Workload | Catalog Ranker + optional `configs/scoring_weights.json` overlay |
| B0 | Unoptimized baseline. E-002 / E-003: suite `T` **375**. |
| B1 | **Selected final optimizer.** E-003: suite `T` **220**, 14/14, 0 false skips. |
| B2 | Implemented experimental wrapper. **Rejected** as the production optimizer (D-050). [B2.md](B2.md) |
| Benchmark definition | **S01–S14** regression. **S16–S18** agent-value file. S15 not loaded. |
| Coding agent | **Cursor** Grok 4.6, Agent mode. [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md) |
| Runtime B2 models | Ollama `qwen2.5:3b` (default) and `qwen3:4b-instruct` (E-011). Not Cursor. |
| Measured agent improvement vs B1 | **None.** E-010 and E-011: Q1 parity; Q2 no. |
| Insights | [INSIGHTS.md](INSIGHTS.md) |

What exists today: a complete B0→B1 measured win, an honest B2 miss, and clone-and-run documentation for a public `main` branch. No fabricated B2 win. A first commit + push is still required before GitHub clone works.

## What changed from the original idea

The product hypothesis is **retained**: change-aware job selection plus promotion/symmetry, local simulation, baseline-first, no fabricated results.

**Phase 3.1** makes the public repository clone-and-run (no new optimizer):

- **Date / iteration:** 2026-08-29 / I-019
- **What changed:** README clone path; every command labeled B0 / B1 / optional B2; public Git topology (`main` only); corrected judge-facing text that could be read as “create branches / open a PR / use GHA / need Ollama or Cursor.”
- **Why:** `feature` / `development` / `main` are simulated CI flows, not required Git branches.
- **Evidence:** E-003 numbers unchanged; E-013 judge-path verification
- **Retained:** B1 as the product; B2 as a documented miss; Cursor as the coding agent
- **Pointer:** D-052

**Phase 3.0** consolidates the repository for judges (no new optimizer):

- **Date / iteration:** 2026-08-29 / I-018
- **What changed:** Judge-facing README; [INSIGHTS.md](INSIGHTS.md); B1 named as the presented solution; B2 labeled experimental/rejected; stale B2/PROBLEM_FRAMING text fixed. No suite or verifier edits.
- **Why:** External review needs a fast B0→B1 story and an honest B2 miss.
- **Evidence:** E-002, E-003, E-010, E-011 (unchanged numbers); E-012 verification
- **Retained:** All prior experiments; fail-closed safety; $0 default
- **Pointer:** D-051

**Phase 2.10** substitutes one stronger local model on the same S16–S18 rows:

- **Date / iteration:** 2026-08-29 / I-017
- **What changed:** `B2_MODEL=qwen3:4b-instruct` only. Docs. No B0/B1/verifier/`scenarios.json` edits.
- **Why:** E-010 left open whether Q1 failed because of the 3B model.
- **Evidence:** E-011 — B1 93; offline B2 93; live 4B B2 93 (2 valid `copy_b1`, 1 malformed, 0 novel_accept, $0); Q2 no (~173 s worse)
- **Retained:** S01–S14; S16–S18 oracles; D-036; $0 default tag `qwen2.5:3b`
- **Pointer:** D-050; `docs/AGENT_VALUE_BENCHMARK.md` §7.6

**Phase 2.9** implements S16–S18 and evaluates B1 / B2-offline / B2-live:

- **Date / iteration:** 2026-08-29 / I-016
- **What changed:** `benchmark/agent_value_scenarios.json`; `--scenarios`; Q1/Q2 fields on the ladder; E-010. No B0/B1/verifier/`scenarios.json` edits.
- **Why:** Phase 2.8 defined the rows. This phase makes them official and measures them.
- **Evidence:** E-010 — B1 93; offline B2 93 (0 invocations); live B2 93 (3 valid `copy_b1`, 0 novel_accept, $0)
- **Retained:** S01–S14; fail-closed S14/S15 policy; D-036; $0 default; `qwen2.5:3b` path
- **Pointer:** D-048–D-049; `docs/AGENT_VALUE_BENCHMARK.md`

**Phase 2.8** designs the agent-value benchmark (no suite implementation):

- **Date / iteration:** 2026-08-29 / I-015
- **What changed:** S15–S18 definitions; Q1 vs Q2; Cursor critical assessment. No B0/B1/verifier/`scenarios.json` edits.
- **Why:** S01–S14 cannot show incremental agent value. Need an honest way to fail.
- **Evidence:** E-009 (tests + absence of S15+ in JSON). Prior E-003–E-008 unchanged.
- **Retained:** fail-closed S14; D-036; $0 default; provider env boundary
- **Pointer:** D-046–D-047; `docs/AGENT_VALUE_BENCHMARK.md`

**Phase 2.7** improves proposal validity without touching the verifier:

- **Date / iteration:** 2026-08-29 / I-014
- **What changed:** Prompt v3; `copy_b1` expansion; local tools off; one repair turn. Verifier unchanged.
- **Why:** E-007 malformed JSON; large templates timed out on 3B CPU.
- **Evidence:** E-008 — S16-like valid in 31 s (cost 31); S14-like still malformed; no novel_accept
- **Retained:** B0/B1/S01–S14; fail closed; $0 local model
- **Pointer:** D-044–D-045

**Phase 2.6** implements the $0 local live path:

- **Date / iteration:** 2026-08-29 / I-013
- **What changed:** Local settings and probe; one pinned model `qwen2.5:3b`; E-006 suite run; E-007 off-suite S16-like. Verifier unchanged.
- **Why:** First real B2 experiment without paid APIs.
- **Evidence:** E-006 B2 = B1 (220); 14/14; 0 false skips; 2 malformed invocations; 0 novel_accept. E-007 `schema_version must be 1`.
- **Retained:** B0/B1/S01–S14; fail closed to B1; no S15–S21 in the official suite
- **Pointer:** D-041–D-043

**Phase 2.5** investigates providers without changing runtime behavior:

- **Date / iteration:** 2026-08-29 / I-012
- **What changed:** Docs only. Cursor vs B2 distinction; official Cursor API is an agent runner, not completions; $0 local OpenAI-compat recommended if a live run is later approved.
- **Why:** E-004 has 0 invocations. Must not spend money or treat Cursor chat as B2.
- **Evidence:** official Cursor/Ollama/Groq docs cited in AGENT_PROVIDER_RESEARCH.md; no live call
- **Retained:** B0/B1/B2/S01–S14 unchanged; D-035 adapter stays
- **Pointer:** D-038–D-040

**Phase 2.4** implements B2 without changing B0, B1, or S01–S14:

- **Date / iteration:** 2026-08-29 / I-011
- **What changed:** Isolated B2 package; OpenAI-compatible provider; read-only tools; schema; verifier (no inert-unknown); CLI `b2`; benchmark `agentic` / `ladder`; E-004.
- **Why:** First implementation of the 2.3 contract. Agent is not the skip authority.
- **Evidence:** E-004 — B2 cost 220 = B1; 14/14; 0 false skips; 0 invocations; 0 novel_accept. Unit tests cover fallback and verifier gates.
- **Retained:** B0/B1/suite unchanged; fail closed to B1
- **Pointer:** D-035–D-037; `docs/B2.md`

**Phase 2.3** specifies B2 without implementing it:

- **Date / iteration:** 2026-08-29 / I-010
- **What changed:** Invocation boundary (B1 first; escalate only conservative residues); context/tools/proposal/verifier; producer/consumer evidence; B2-vs-B1 metrics; S15+ conceptual scenarios; Cursor discovery log.
- **Why:** B1 already matches S01–S14. An agent must not blindly replace B1.
- **Evidence:** not tested (design). CD-001: S14 cannot show “smart unknown” skips.
- **Retained:** B0/B1/suite unchanged; verifier owns skips
- **Pointer:** D-030–D-034; `docs/AGENT_DESIGN.md`

**Phase 2.2** implements the first optimized system as deterministic B1:

- **Date / iteration:** 2026-08-29 / I-009
- **What changed:** Impact-graph planner, identity-checked cache, inferred promote mode, B0-vs-B1 harness, E-003. No agent. No ground-truth edits.
- **Why:** Need a strong safety floor before asking whether an agent adds value.
- **Evidence:** E-003 (suite cost 375 → 220; 14/14; 0 false skips)
- **Retained:** B0 unchanged; S01–S14 unchanged; UNKNOWN → RUN
- **Pointer:** D-026–D-029; `docs/B1.md`

**Phase 2.1** adds an optimizer-facing contract without changing the product hypothesis or the Phase 1.3 evaluation rules:

- **Date / iteration:** 2026-08-29 / I-008
- **What changed:** Documented job I/O and invalidation, change-impact chain, safety (UNKNOWN → RUN), promotion semantics, unchanged cost objective, S01–S14 relationship (ambiguities documented, not edited), and deterministic/agent/verifier boundary. Comparison ladder: B0 → deterministic optimizer → agent.
- **Why:** Phase 2 must not jump from B0 to an unexplained agent. The contract is required before implementation.
- **Evidence:** not tested (design; existing tests still measure B0 only)
- **Retained:** correctness-constrained optimization; B0 as naive baseline; S01–S14 ground truth; no fabricated improvement
- **Pointer:** D-022–D-025; `docs/OPTIMIZATION_CONTRACT.md`

Phase 1.3 **narrows** the original idea without erasing it:

- **Date / iteration:** 2026-08-29 / I-003
- **What changed:** Correctness is an explicit hard constraint; the objective is time/unnecessary-work *subject to* correctness, not “skip more jobs.” A Catalog Ranker workload, 10-job graph, B0 baseline, S01–S14 scenarios, and a metric contract are specified. ML is workload only. Live APIs are rejected for the benchmark.
- **Why:** Phase 1.3 asked for an evaluable contract before implementation.
- **Evidence:** not tested (design decisions, not experiments)
- **Retained from the original idea:** agentic job selection, `feature → development → main`, environment symmetry, local/reproducible simulation, baseline before claims
- **Pointer:** D-009–D-017; `docs/PROBLEM_FRAMING.md`

**Earlier phase-plan refinement (I-002):** Phase 1.2 was Python packaging, not problem framing.

Further direction changes should be appended above using the same fields (date, what, why, evidence, retained, pointer).

## Completed work

| ID | Work | Status | Notes |
| --- | --- | --- | --- |
| Phase 1.1 | Repository foundation and durable documentation | `completed` | Approved before starting 1.2 |
| Phase 1.2 | Python packaging, deps, pytest, ruff | `completed` | Approved before starting 1.3 |
| Phase 1.3 | Problem framing and evaluation contract | `completed` | Approved before starting 1.4 |
| Phase 1.4 | Executable Catalog Ranker foundation | `completed` | Approved before starting 1.5 |
| Phase 1.5 | Executable CI/CD baseline (B0) | `completed` | Approved before starting 1.6 |
| Phase 1.6 | Reproducible benchmark suite | `completed` | S01–S14 + E-001 (S10 miss recorded) |
| Phase 1.6.1 | Correct B0 dirty promotion semantics | `completed` | E-002; same ground truth |
| Phase 2.1 | Formal optimization contract | `completed` | Contract only; approved before 2.2 |
| Phase 2.2 | Deterministic optimizer (B1) | `completed` | E-003; approved before 2.3 |
| Phase 2.3 | Agentic optimizer contract | `completed` | Design only; approved before 2.4 |
| Phase 2.4 | Agentic optimizer (B2) | `completed` | E-004; approved before 2.5 |
| Phase 2.5 | Provider / reproducibility investigation | `completed` | Docs only; approved path used in 2.6 |
| Phase 2.6 | Free local agent integration | `completed` | E-006 / E-007 |
| Phase 2.7 | Proposal validity | `completed` | E-008 |
| Phase 2.8 | Agent-value benchmark design | `completed` | E-009; approved before 2.9 |
| Phase 2.9 | Agent-value suite implementation | `completed` | E-010; approved before 2.10 |
| Phase 2.10 | Stronger local model on S16–S18 | `completed` | E-011; B1 preferred (D-050) |
| Phase 3.0 | Final consolidation | `in progress` | I-018; awaiting review |

## Planned phase structure (high level)

Later phases are **intentionally underspecified**. Job names, pipeline topology, agent architecture, models, and metrics listed as examples in the hackathon brief are *illustrative*, not commitments.

### Phase 1 — Foundation and problem framing

**Status:** `completed`

| Micro-phase | Intent | Status |
| --- | --- | --- |
| 1.1 Project foundation and documentation | Make the public repo understandable; create the evidence trail | `completed` |
| 1.2 Python technical foundation | Installable package, dependency management, pytest, ruff | `completed` |
| 1.3 Problem framing and evaluation contract | Workload, job graph, baseline, scenarios, metrics | `completed` |
| 1.4 Executable Catalog Ranker foundation | Local workload, fixtures, artifact id, tests | `completed` |
| 1.5 Executable CI/CD baseline (B0) | Local always-run-all job runner | `completed` |
| 1.6 Reproducible benchmark suite | S01–S14 ground truth + B0 runner | `completed` |
| 1.6.1 Correct B0 dirty promotion | B0 matches clean/dirty promote contract | `completed` |

B0 can be measured on S01–S14. B1 is compared in E-003 (and re-verified in E-012).

### Phase 2 — Deterministic optimization baseline

**Status:** `completed`

Establish a **non-agent deterministic optimizer** so later agent work can be compared against both B0 and a strong safety floor. Do not jump from B0 to an unexplained agent (D-023).

| Micro-phase | Intent | Status |
| --- | --- | --- |
| 2.1 Formal optimization contract | Job graph, change impact, safety, promotion, objective, agent boundary | `completed` |
| 2.2 Deterministic optimizer (B1) | Impact graph + cache; no agent | `completed` |
| 2.3 Agentic optimizer contract | When/how to invoke; verifier; evaluation | `completed` |
| 2.4 Agentic optimizer (B2) | B1 first; agent proposes; verifier final | `completed` |
| 2.5 Provider / reproducibility investigation | Cursor vs B2; $0 path; no live call | `completed` |
| 2.6 Free local agent integration | Ollama `qwen2.5:3b`; first live B2 | `completed` |
| 2.7 Proposal validity | Prompts / `copy_b1` wire form | `completed` |
| 2.8 Agent-value benchmark design | S15–S18 + Q1/Q2; no rows loaded | `completed` |
| 2.9 Agent-value suite implementation | Official S16–S18; B1/B2 eval | `completed` |
| 2.10 Stronger local model on the same rows | `qwen3:4b-instruct` via env | `completed` |
| 2.11+ Paid model | Only after explicit approval; not required for submission | `planned` |

**B0, B1, and B2 are local runners.** A paid-model or S15-control phase must not start without explicit approval.

### Phase 3 — Agentic solution (iterative)

**Status:** `completed` (as an investigation; B2 is not the product)

B2 was implemented (2.4) and measured (2.6–2.10). It did not beat B1. The phase goal “show what the agent improved” is answered: **the coding agent (Cursor) produced B1; the runtime agent did not add a `T` win.** See [INSIGHTS.md](INSIGHTS.md).

### Phase 4 — Evaluation and measured improvement

**Status:** `completed` for the presented comparison

E-003 is the B0 vs B1 win. E-004/E-006/E-010/E-011 are B2 measurements (no win vs B1).

### Phase 5 — Reproducibility and insights

**Status:** `completed` for documentation (3.0–3.1)

Judge README, expected metrics, insights, Cursor vs B2 distinction, and public-`main` clone path (no PR, no GHA, no required Ollama/Cursor/keys).

## Rejected / removed approaches

| Approach | When | Why rejected |
| --- | --- | --- |
| B2 as the production optimizer | D-050 / E-010 / E-011 | No `T` win vs B1; large latency; $0 local models copy B1 or malformed |
| Cursor Cloud Agents / SDK as B2 host | D-038 | Wrong API shape; billed; not judge-reproducible |
| Inert-unknown verifier skips | D-036 | Would false-skip S14 |
| Live public API as benchmark data | D-011 | Reproducibility |
| Skip-count as primary metric | D-009 | Encourages unsafe skips |
| 7B+ local model on this 8 GB host | D-041 / D-050 | Not realistically runnable |

## Chat / agent context logging

Major phases use **separate Cursor conversations**. This is a reproducibility rule, not a convenience (D-008, D-022):

- Chat context is intentionally reset at major phase boundaries.
- Each chat must begin with enough **repository** context to understand the current state on its own.
- Repository documentation, not the previous chat transcript, is the source of truth.
- Decisions made in a chat must be written into `docs/` (and into code only when that phase implements).
- Do not rely on conversational memory for critical project decisions.

## Near-term stop rule

After each micro-phase, work **stops** for human review. Phase 3.0 stops here. Do not start a paid-model phase or load S15 without explicit approval.
