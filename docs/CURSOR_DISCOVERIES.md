# Cursor / human discovery log

This file records **engineering discoveries** made with the coding assistant (Cursor) while designing or implementing the project.

It is **not** the runtime B2 decision log (`novel_accept` / `novel_reject` in [AGENT_DESIGN.md](AGENT_DESIGN.md) §8).

- Runtime B2: the CI agent proposes job skips; the verifier records accept/reject.
- This file: the *development* agent (Cursor) found something the human brief or prior docs missed.

Do not treat entries here as benchmark results.

---

## How to log a discovery

```md
## [CD-XXX] YYYY-MM-DD — short title

- **Discovery ID:** CD-XXX
- **Date:** YYYY-MM-DD
- **Phase / iteration:**
- **What we initially believed:**
- **What Cursor discovered:**
- **Evidence:** (files, tests, suite rows — not fabricated metrics)
- **Changed the design?** yes / no
- **Resulting decision:** (D-XXX or “none”)
```

---

## Entries

### [CD-001] 2026-08-29 — S14 ground truth blocks “smart unknown” skips

- **Discovery ID:** CD-001
- **Date:** 2026-08-29
- **Phase / iteration:** 2.3 / I-010
- **What we initially believed:** An agent that inspects `unknown/orphan.dat`, finds no imports, and skips `score` would be a clean demonstration of B2 beating B1 on the existing suite.
- **What Cursor discovered:** S14 `required_jobs` is the **full feature→dev graph** (fail-closed policy, D-016). B1 already matches that oracle (E-003: 0 unnecessary jobs on S14). A localizing agent that skips `score` would be a **false skip** on S14 even if the file is inert. S07 is the same shape for dependencies.
- **Evidence:** `benchmark/scenarios.json` S14; E-003 B1 unnecessary = 0; [AGENT_DESIGN.md](AGENT_DESIGN.md) §8.3
- **Changed the design?** yes
- **Resulting decision:** D-031 — S01–S14 are a B2 *regression* suite, not the agent-value suite. Agent-value needs later scenarios (e.g. conceptual S15) with localized ground truth. Do not edit S14 to flatter B2.

### [CD-002] 2026-08-29 — Unknown path already has a safe B1 answer

- **Discovery ID:** CD-002
- **Date:** 2026-08-29
- **Phase / iteration:** 2.3 / I-010
- **What we initially believed:** Every unknown path should invoke the agent.
- **What Cursor discovered:** B1’s `CONSERVATIVE_COMPONENTS` already maps unknown → full legal graph. That is a complete safety decision. Invocation is optional *refinement* of an over-run, not a missing safety step. If the file cannot be inspected, keep B1 and do not call the model.
- **Evidence:** `src/agentic_cicd/b1/classify.py` (`COMPONENT_UNKNOWN`); `planner.py` `REASON_CONSERVATIVE`
- **Changed the design?** yes
- **Resulting decision:** D-030 — escalate only when B1 is conservative *and* inspection is possible *and* expected value is non-trivial.

### [CD-003] 2026-08-29 — files_changed vs apply (recorded from Phase 2.1, persisted here)

- **Discovery ID:** CD-003
- **Date:** 2026-08-29
- **Phase / iteration:** 2.1–2.2 / I-008–I-009 (logged in 2.3 so the discovery trail is explicit)
- **What we initially believed:** The optimizer could look at workspace diffs or B0 artifact hashes alone.
- **What Cursor discovered:** Several scenarios declare one path and apply another (S03/S10 overlay proxy; S05/S13 workspace markers). B0 executes installed modules, so hashes may not change. Ground truth is the **declared change class**. B1 therefore consumes `files_changed ∪ apply` (D-028).
- **Evidence:** [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md) §6; `benchmark/scenarios.json`
- **Changed the design?** yes (already applied in B1)
- **Resulting decision:** D-025, D-028

### [CD-004] 2026-08-29 — Inert-unknown skips are not mechanically safe

- **Discovery ID:** CD-004
- **Date:** 2026-08-29
- **Phase / iteration:** 2.4 / I-011
- **What we initially believed:** Phase 2.3 §5 allowed an “inert unknown” skip if tools found no import/read of the unclassified path.
- **What Cursor discovered:** “No search hits” is negative evidence. Search is bounded (file cap, hit cap, jail). An unclassified file can still matter (S14 policy) or sit outside the scanned roots. Implementing option 2 as written would let a proposal skip `score` on `unknown/orphan.dat` and **fail S14**.
- **Evidence:** `benchmark/scenarios.json` S14; unit test `test_unsupported_skip_inert_unknown`; verifier rejects narrowing without a positive import/read edge or valid cache identity.
- **Changed the design?** yes (stricter than the 2.3 contract text)
- **Resulting decision:** D-036 — do not accept inert-unknown. Require positive checkable evidence. Keep S14 as fail-closed policy.

### [CD-005] 2026-08-29 — Cursor subscription is not a B2 completions API

- **Discovery ID:** CD-005
- **Date:** 2026-08-29
- **Phase / iteration:** 2.5 / I-012
- **What we initially believed:** A paid Cursor subscription might expose the same chat model (Grok-family) to our Python B2 runner at $0 extra, or at least via an official inference API included with the plan.
- **What Cursor discovered:** Official Cursor APIs/SDKs run **coding agents** (workspace, tools, commands, edits). Docs state they are **not** a standalone chat-completions API. A `CURSOR_API_KEY` must be created in the dashboard; SDK examples default to `composer-2.5`; cloud/SDK usage is billed from Cursor usage pools. The IDE session model is not injected into `src/agentic_cicd/b2`.
- **Evidence:** [cursor.com/docs/api](https://cursor.com/docs/api); [cursor.com/docs/sdk/python](https://cursor.com/docs/sdk/python); [AGENT_PROVIDER_RESEARCH.md](AGENT_PROVIDER_RESEARCH.md) §3
- **Changed the design?** yes (provider strategy; no code)
- **Resulting decision:** D-038 — do not use Cursor as the B2 runtime provider.

### [CD-006] 2026-08-29 — 3B local model invokes but does not emit valid b2_proposal

- **Discovery ID:** CD-006
- **Date:** 2026-08-29
- **Phase / iteration:** 2.6 / I-013
- **What we initially believed:** A small instruct model with tools + JSON instructions would often produce a parseable `b2_proposal` on S07/S14 and conceptual S16.
- **What Cursor discovered:** `qwen2.5:3b` on 8 GB CPU did invoke (S07, S14, S16-like), used one read-only tool, then failed schema (`malformed`; E-007: `schema_version must be 1`). Verifier never scored a live novel skip. HTTP 400 on OpenAI tool schema is retried without tools. Default 30 s timeout is too short (~3–5 min/call).
- **Evidence:** E-006 `b2_record.json` for S07/S14; E-007 `agent_error`; `OpenAICompatProvider` 400 retry
- **Changed the design?** no (fallback already required)
- **Resulting decision:** D-041 keeps the small model for $0/RAM; D-043 does not add official S16 until a model can emit valid JSON *or* a human approves the suite row anyway.

### [CD-007] 2026-08-29 — Live B2 env can leak into the offline suite test

- **Discovery ID:** CD-007
- **Date:** 2026-08-29
- **Phase / iteration:** 2.6 / I-013
- **What we initially believed:** `test_benchmark_b2_reproduces_b1_offline` always measured zero invocations.
- **What Cursor discovered:** Inheriting `B2_BASE_URL` from the Docker experiment env made the “offline” suite test call Ollama (2 invocations). The test now unsets B2 env vars.
- **Evidence:** `tests/test_benchmark.py`
- **Changed the design?** no (test isolation only)
- **Resulting decision:** none (test fix)

### [CD-008] 2026-08-29 — 3B CPU cannot emit a full 10-job proposal in time

- **Discovery ID:** CD-008
- **Date:** 2026-08-29
- **Phase / iteration:** 2.7 / I-014
- **What we initially believed:** A clearer prompt plus `response_format=json_object` would fix E-007’s `schema_version` error.
- **What Cursor discovered:** The same `qwen2.5:3b` answers a 2-token health check in ~2.6 s, but times out at 180–300 s when asked to emit ten full job objects or when tools/`json_object` are attached. A `copy_b1` + empty `jobs` object returned valid JSON in **31 s** (E-008 S16-like). The model still did not propose a checkable narrower SKIP. S14-like listed `{"job":"test"}` without `decision`.
- **Evidence:** E-008 attempts A–D; `outputs/e008-s16-compact/s16_like/run/b2_record.json`
- **Changed the design?** yes (wire format only)
- **Resulting decision:** D-044, D-045

### [CD-009] 2026-08-29 — Inert-unknown cannot be a B2 cost-win row

- **Discovery ID:** CD-009
- **Date:** 2026-08-29
- **Phase / iteration:** 2.8 / I-015
- **What we initially believed:** Conceptual S15 (`required_jobs` = `branch_guard` only) would be the clean “agent beats B1” demo.
- **What Cursor discovered:** The verifier only localizes an unknown path if the file contains a **component needle** (`score_code`, `scoring_overlay`, …). `documentation` has no needles. Inert-unknown is rejected (D-036). An S15 oracle of `branch_guard` only is **unreachable** without weakening the verifier. S15 must be a fail-closed *control* (same policy as S14). Value rows are S16–S18 (positive needles).
- **Evidence:** `verifier.py` `_edge_checkable` / `COMPONENT_NEEDLES`; [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md) §3–4
- **Changed the design?** yes (suite design, not code)
- **Resulting decision:** D-046

### [CD-010] 2026-08-29 — Official S16–S18 confirm 3B copies B1

- **Discovery ID:** CD-010
- **Date:** 2026-08-29
- **Phase / iteration:** 2.9 / I-016
- **What we initially believed:** Loading official S16–S18 might let the live model find the import/overlay needles now that the files are first-class harness rows.
- **What Cursor discovered:** B1 is conservative as designed (`T` = 31/row, suite 93, 7 unnecessary). Live `qwen2.5:3b` invoked on all three rows and emitted valid `copy_b1` (S17 needed one repair). `discovered_edges` stayed empty. `novel_accept` = 0. Realized save = 0. `W_e2e` got ~101 s worse. The limitation is the model, not missing rows or a blocking verifier. `FakeProvider` can still `novel_accept` the S16 shape.
- **Evidence:** E-010; `outputs/benchmark-e010-live/runs/S1{6,7,8}/b2_record.json`
- **Changed the design?** no (evaluation result)
- **Resulting decision:** D-049 — do not keep retrying this 3B tag for Q1

### [CD-011] 2026-08-29 — Stronger local 4B still copies B1

- **Discovery ID:** CD-011
- **Date:** 2026-08-29
- **Phase / iteration:** 2.10 / I-017
- **What we initially believed:** Phase 2.9 concluded the 3B model was the limiter. A next-generation 4B instruct tag on the same host might emit checkable edges on S16–S18.
- **What Cursor discovered:** `qwen3:4b-instruct` (4.0B, Q4_K_M, digest `0edcdef34593`) ran on 8 GB CPU (loaded 3.2 GB, num_ctx 4096). S16 and S18 emitted the same valid `copy_b1` + empty jobs as E-010. S17 was **worse**: `schema-version` (hyphen) and preview-shaped `discovered_edges` (`path` / `content`, not `from_path` / `to_component`); repair failed; B1 fallback. `novel_accept` = 0. `T` = 93. `W_agent` 173 s (slower than 3B). 7B/8B were not pulled (RAM/CPU).
- **Evidence:** E-011; `outputs/benchmark-e011-live/runs/S1{6,7,8}/b2_record.json`
- **Changed the design?** no (evaluation result; default tag unchanged)
- **Resulting decision:** D-050 — B1 is the preferred $0 product; do not hunt more local tags for Q1 on this host

### [CD-012] 2026-08-29 — Mid-project docs still sold B2 as the product

- **Discovery ID:** CD-012
- **Date:** 2026-08-29
- **Phase / iteration:** 3.0 / I-018
- **What we initially believed:** After E-011 / D-050 the repository already presented B1 as the final optimizer.
- **What Cursor discovered:** The README still led with Phase 2.10 status and “B2 is the agentic optimizer.” `docs/B2.md` §7 still said S16–S18 were not official. `PROBLEM_FRAMING.md` still said B2 “is not implemented.” ROADMAP “Rejected approaches” still said none. Those sentences would mislead a judge even though the experiment logs were correct.
- **Evidence:** pre-consolidation `README.md`, `docs/B2.md` §7, `docs/PROBLEM_FRAMING.md` status line, `docs/ROADMAP.md` rejected section
- **Changed the design?** no (documentation only)
- **Resulting decision:** D-051 — present B1; keep B2 labeled as experiment

### [CD-013] 2026-08-29 — Simulated CI flows are not Git branches to create

- **Discovery ID:** CD-013
- **Date:** 2026-08-29
- **Phase / iteration:** 3.1 / I-019
- **What we initially believed:** After 3.0, a judge could clone and run. The remaining risk was wording, not missing commands.
- **What Cursor discovered:** README and PROBLEM_FRAMING still described `feature → development → main` and “pull request” without saying those are **simulator flow labels**. A reader could think they must create Git branches, open a PR, or use GitHub Actions. Ollama/Cursor/key language existed for B2 but was not always labeled optional. Local `main` has **zero commits** and `origin` has **no refs**, so a real `git clone` of the public URL cannot yet obtain this tree.
- **Evidence:** pre-3.1 README reproduce section; PROBLEM_FRAMING §4 diagram; `git status` (all untracked); `git log` (no HEAD); `git ls-remote origin` (empty)
- **Changed the design?** no (documentation and topology only)
- **Resulting decision:** D-052 — public repo is `main` only; judges clone and run locally

### [CD-014] 2026-08-30 — Git detection is an adapter, not a B1 rule

- **Discovery ID:** CD-014
- **Date:** 2026-08-30
- **Phase / iteration:** 3.2 / I-020
- **What we initially believed:** B1’s lack of automatic Git change discovery was a product weakness to fix before submission. A judge should be able to clone, edit a file, run B1, and have the system infer `changed_paths` from Git.
- **What Cursor discovered:** `changed_paths` already enters at the CLI (`--changed`), the harness (`change_set` = `files_changed ∪ apply`, D-028), and tests. B1 only classifies that list (`None` = unknown, `[]` = known-empty). Git belongs in an optional adapter *before* `plan_jobs`, never inside `b1/`. The suite **must not** use Git: S03/S10 declare `score.py` but apply a scoring-overlay proxy; S05/S13 use workspace markers; `materialize_workspace` copies only `fixtures/` and `configs/` and is not a Git repo. Replacing D-028 with a working-tree diff would change or fail-close the measured B1 result. Working tree vs `HEAD` is a demo UX and is **not** git-ancestry-for-promote. Cursor proposed `--from-git` as technically safe, then recommended **freezing** because it does not improve E-003 and adds late-stage surface.
- **Evidence:** inspection of `cli.py`, `b1/planner.py`, `b1/classify.py`, `benchmark/apply.py`, `benchmark/runner.py`, `benchmark/scenarios.json` S03/S05/S10/S13; no new suite run
- **Changed the design?** no (scope/documentation only; no adapter shipped)
- **Resulting decision:** D-053 — do not implement Git detection in this submission; keep the caller-supplied change set as intentional
