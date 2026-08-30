# Agent-value benchmark (Phase 2.8–2.9)

**Phase:** 2.8 design; **2.9** official S16–S18; **2.10** stronger local model on the same rows  
**Status:** S16–S18 are executable in `benchmark/agent_value_scenarios.json`. S01–S14 stay in `benchmark/scenarios.json`. S15 is still a documented control, not a loaded row.  
**Date:** 2026-08-29  
**Does not claim:** that B2 beat B1. E-010 and E-011 are **Q1 parity** and **Q2 no**.

**Judges reproducing the headline B0→B1 result can skip this document and every B2 command.** Ollama, API keys, and Cursor are not required for that path. This file records why the optional B2 experiment did not outperform B1.

S01–S14, B0, B1, and the verifier are unchanged. This document answers whether — and under what metrics — B2 adds value.

Related: [AGENT_DESIGN.md](AGENT_DESIGN.md), [BENCHMARK.md](BENCHMARK.md), [B2.md](B2.md), [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md), D-031, D-036, D-043, D-046–D-050, E-003–E-011.

---

## 1. Research questions (two, not one)

| ID | Question | What a “yes” looks like |
| --- | --- | --- |
| Q1 | Can the agent *reason* about the repo well enough to propose a checkable narrower plan? | Valid `b2_proposal` + verifier `novel_accept` > 0 + false skips = 0 |
| Q2 | Does that extra optimization **justify** agent latency and money? | Q1 holds **and** end-to-end time (and $) are not worse under the rules in §6 |

A valid proposal that copies B1 (E-008 S16-like) answers **neither**. It is a validity result, not an optimization win.

B2 failing Q1 or Q2 is an acceptable research conclusion. The goal is not to make B2 win.

---

## 2. Why S01–S14 cannot answer Q1 or Q2

B1 already matches `required_jobs` on every frozen row (E-003: cost 220, 14/14, 0 false skips, 0 unnecessary). Conservative rows S07 and S14 have **full-graph oracles**. A cheaper B2 plan there is a **false skip**.

S01–S14 remain the **regression suite**: B2 must not get worse. They are not the agent-value suite (D-031).

---

## 3. Where B1 is intentionally conservative

B1 maps unmapped paths to `unknown` / `dependencies` / `orchestrator` and runs the full legal graph. That is the safety floor, not a bug.

| Residue | B1 behavior | Why B1 cannot tighten |
| --- | --- | --- |
| Unclassified path | Full feature→dev graph (cost **31**) | No path rule |
| `pyproject.toml` / locks (S07) | Full graph | Comment-only vs runtime-affecting is not mechanical in B1 |
| Unmapped ranker helper | Full graph | Not in `classify_path` |
| Mixed known + unknown | Unknown dominates | Conservative union |
| Empty `files_changed` on promote | Clean reuse | No git ancestry |

The verifier (D-036) accepts a narrower SKIP only with **positive** checkable evidence:

- `discovered_edges` whose file text contains a **needle** for a known component (`score_code`, `scoring_overlay`, …), then re-plan as B1 on the rewritten paths; or
- valid cache identity for a producer.

`documentation` / `tests` have **no needles**. Inert-unknown (no hits) is **rejected**. Therefore an “empty file → skip score” proposal cannot be a legal B2 win without changing the verifier. This phase does **not** change the verifier.

---

## 4. Agent-value suite

S16–S18 are loaded from `benchmark/agent_value_scenarios.json` (D-048). They are **not** in `benchmark/scenarios.json`. The default harness remains S01–S14.

```bash
python -m agentic_cicd benchmark --system optimized --scenarios benchmark/agent_value_scenarios.json
python -m agentic_cicd benchmark --system agentic --scenarios benchmark/agent_value_scenarios.json
```

Feature→dev costs used below (Phase 1.3 weights): full graph **31**; S03 score chain **22**; S12 overlay chain **19**; S01 docs **1**; S05 prepare chain **26**.

### 4.1 Included in v1

#### S15 — Second fail-closed unknown (safety control)

| Field | Value |
| --- | --- |
| Intent | Same *policy* as S14, different path. Not an agent-cost win. |
| Why not S14 | S14 stays frozen. A second unknown path shows fail-closed is a class. |
| `files_changed` | `scratch/todo.txt` |
| Apply / body | Non-empty inert text; **no** ranker needles |
| B1 | Full graph, cost **31** |
| `required_jobs` | `branch_guard`, `validate`, `test`, `ingest`, `prepare`, `score`, `evaluate`, `package`, `publish` |
| Checkable? | Yes: path is unclassified; no needles → verifier must not localize |
| Capable agent | May inspect and still must **not** skip. `copy_b1` all-RUN is correct. |
| B2 cheaper than B1 | **Unsafe** (false skip), same as S14 |
| Distinct from S14 | Different path; explicit B2 scoring: cheaper ⇒ regression |

Do **not** set S15 `required_jobs` to `branch_guard` only. That oracle is unreachable under D-036 and would manufacture a “B2 cannot win” or pressure to weaken the verifier.

#### S16 — Unknown file that imports `score` (primary value row)

| Field | Value |
| --- | --- |
| Intent | Hidden score-code edge B1 cannot name |
| `files_changed` | `scripts/tune_weights.py` |
| Apply / body | `import agentic_cicd.ranker.score` (needle `agentic_cicd.ranker.score`) |
| B1 | Full graph, **31** |
| `required_jobs` | S03 set: `branch_guard`, `validate`, `test`, `score`, `evaluate`, `package`, `publish` (cost **22**) |
| Checkable? | File text contains the score needle; verifier can rewrite to `ranker/score.py` |
| Capable agent | Propose SKIP `ingest`/`prepare`/`promote` with that edge |
| Expected save vs B1 | **9** simulated units if accepted |
| Off-suite history | E-007 malformed; E-008 valid `jobs: []` (save **0**) |

#### S17 — Hidden overlay (not named `scoring_weights.json`)

| Field | Value |
| --- | --- |
| Intent | Overlay-class change on an unmapped config path |
| `files_changed` | `ops/prod_weights.json` |
| Apply / body | JSON overlay that **contains the substring** `scoring_weights.json` (needle for `scoring_overlay`) plus a weight field that would change scores |
| B1 | Full graph, **31** |
| `required_jobs` | S12 set: `branch_guard`, `validate`, `score`, `evaluate`, `package`, `publish` (cost **19**) |
| Checkable? | Needle in file; rewrite to `configs/scoring_weights.json`; B1 overlay plan |
| Capable agent | Edge `to_component=scoring_overlay` |
| Expected save vs B1 | **12** if accepted |
| Why not S12 | S12 is already mapped by filename. S17 is unmapped. |

#### S18 — Docs + S16-like unknown (mixed)

| Field | Value |
| --- | --- |
| Intent | Known cheap class ∪ unknown. B1 lets unknown dominate. |
| `files_changed` | `README.md`, `scripts/tune_weights.py` |
| Apply / body | Docs unchanged-or-trivial; script same as S16 |
| B1 | Full graph, **31** |
| `required_jobs` | Same as S16 / S03 (**22**) — docs jobs are a subset of the score chain |
| Checkable? | Localize only the unknown path; README already classified |
| Capable agent | Same import edge as S16 |
| Expected save vs B1 | **9** if accepted |
| Why not S01+S14 | Union is the point; S14’s oracle is the full graph |

### 4.2 Deferred (not v1)

| ID | Why deferred |
| --- | --- |
| S19 | History-dirty promote needs a git-ancestry tool B2 does not have |
| S20 | `ranker/io_util.py` has no component needles; cannot localize without a verifier/classify extension |
| S21 | Cache + unused sidecar is a second evidence path; defer until S16/S17 exist as executables |
| Old “S15 = skip to branch_guard” | Requires weakening D-036. **Rejected** for this suite |

### 4.3 Fairness constraints (implemented)

- No scenario id or `required_jobs` in the optimizer (`src/agentic_cicd/b2/`).
- Same `files_changed ∪ apply`, same cache warm, same job bodies as B1.
- Needles appear in the **changed file**. S17 writes only `ops/prod_weights.json`; it does **not** mutate `configs/scoring_weights.json` (that would make B1 non-conservative).
- Oracle is independent of B2. S15 is not loaded as a cost-win row.

---

## 5. Verdicts (per scenario and suite)

Safety gate (unchanged): false skips = 0; no illegal promote accepted; correctness vs that row’s `required_jobs`.

| Verdict | Simulated pipeline (`T` = sum of executed weights) | Safety | Meaning |
| --- | --- | --- | --- |
| **B2 improvement** (Q1) | `T_B2 < T_B1` | Pass | Agent + verifier skipped unnecessary B1 work |
| **B2 parity** | `T_B2 = T_B1` | Pass | Includes no-invoke, fallback, and valid copy-B1 |
| **B2 regression** | `T_B2 > T_B1` or extra unnecessary jobs vs B1 | Pass | Worse pipeline work without a safety fail |
| **Unsafe** | any false skip or illegal promote | Fail | Disqualifies all “wins” |

Suite-level Q1 win on the agent-value rows: safety pass **and** sum(`T_B2`) < sum(`T_B1`) on **S16+S17+S18**. S15 is scored only for safety/parity (cheaper is unsafe).

S01–S14: any `T_B2 < T_B1` on S07/S14 is **unsafe**, not a win.

---

## 6. Latency, money, and “10 seconds vs 3 minutes”

### 6.1 Four clocks (always report separately)

| Clock | What it is | Source |
| --- | --- | --- |
| Pipeline simulated cost `T` | Sum of job weights of `executed` | `simulated_cost` |
| Pipeline wall-clock `W_jobs` | Time in job bodies (noisy) | `wall_duration_ms` of the run |
| Agent reasoning latency `W_agent` | Model + tools | `agent_latency_ms` |
| End-to-end `W_e2e` | `W_jobs + W_agent` | derived |
| Monetary | Vendor API invoice | `api_cost_usd` (local = **$0**) |

Do not add `W_agent` into `T`. Do not put `$` into the safety gate.

### 6.2 Two product questions

**Q1 (reasoning / pipeline work):** use `T` and novel_accept. This is the CI “did we skip real jobs?” question. Simulated weights stand in for *work*, not for this laptop’s milliseconds.

**Q2 (is the agent worth calling?):**

```text
e2e_delta = W_e2e(B1) − W_e2e(B2)
          = (W_jobs_B1) − (W_jobs_B2 + W_agent)
```

- `e2e_delta > 0`: end-to-end **win** on that machine.
- `e2e_delta ≤ 0`: end-to-end **not a win**, even if `T` improved.

**Explicit rule for the 10s / 3min case:**

If the pipeline save is ~10 seconds of *real* job time and the agent takes ~180 seconds, **Q2 is no**. That is not a rounding error; it is the conclusion.

### 6.3 Observation about *this* simulation (not a production claim)

On the measured S01–S14 ladder, B0 and B1 job wall-clock are both ~12–13 s for fourteen scenarios (E-003). Skipped jobs barely change wall-clock because bodies are cheap counters. Agent latency was **31 s** (E-008 compact) to **~200–300 s** (E-006).

**Observation:** under current job implementations, **Q2 cannot succeed** on this host: `W_agent` dominates `W_jobs` savings.

**Hypothesis (labeled, not measured):** if production mapped `score` (weight 10) to many minutes of CI, a save of 9–12 weights could beat a 30 s agent. That mapping is **not** a measured number in this repo. Report it only as `projected_ci_minutes` if a later phase publishes an explicit seconds-per-weight table. Until then, Q2 uses **measured** `W_e2e` only.

### 6.4 Monetary

Default path: **$0** API (local Ollama). Local compute is not invoiced.

A paid model may be compared on the **same rows** with `api_cost_usd` reported. A Q1 win that spends money still needs Q2 (and an explicit $ budget) before anyone calls it a product win.

**Default evaluation remains $0.** Paid is optional substitution, not the required host.

---

## 7. Same benchmark, stronger model

No B2 redesign. Substitute:

```text
B2_BASE_URL=...
B2_MODEL=...
# hosted only:
B2_API_KEY=...
B2_TIMEOUT_S=...
B2_ENABLE_TOOLS=...
```

Hold constant: S15–S18 definitions, verifier, B1, S01–S14. Compare `T`, Q1/Q2, novel_accept/reject, fallback, `W_agent`, `$`.

The local default stays `qwen2.5:3b` / no key. E-011 substituted `qwen3:4b-instruct` via the same env only.

---

## 7.5 Measured official evaluation (E-010)

One B1 run, one offline B2 run, one live B2 run on S16–S18. Model: `qwen2.5:3b` (Ollama 0.33.2, digest `357c53fb659c`). `B2_TIMEOUT_S=180`. Tools off (local default). Prompt `b2-proposal-v3`. No paid API. No second model.

| Clock / gate | B1 | B2 offline | B2 live |
| --- | --- | --- | --- |
| Simulated cost `T` | **93** | **93** | **93** |
| Jobs executed | 27 | 27 | 27 |
| Unnecessary jobs | 7 | 7 | 7 |
| Correctness | 3/3 | 3/3 | 3/3 |
| False skips | 0 | 0 | 0 |
| Illegal promotions | 0 | 0 | 0 |
| Agent invocations | — | 0 | **3** |
| `used_proposal` | — | 0 | **3** |
| novel_accept / novel_reject | — | 0 / 0 | **0 / 0** |
| Fallback reason | — | no invoke (`offline`) | none (valid `copy_b1`) |
| Agent latency `W_agent` | 0 | 0 | **99932.644 ms** |
| Job wall `W_jobs` | 4458.195 ms | 4703.802 ms | 5403.174 ms |
| End-to-end `W_e2e` | 4458.195 ms | 4703.802 ms | **105335.818 ms** |
| Tokens (prompt / completion) | 0 | 0 | 1807 / 136 |
| API $ | $0 | $0 | **$0** |
| Q1 | — | parity | **parity** (not a win) |
| Q2 | — | n/a | **no** |

Per scenario (live):

| ID | `T` | Jobs | Unnecessary | Invoke | Latency | Tokens in/out | Proposal | Verifier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S16 | 31 | full graph | ingest, prepare | yes | 58521 ms | 412 / 28 | `copy_b1` + `jobs: []` | accepted all-RUN; novel 0 |
| S17 | 31 | full graph | test, ingest, prepare | yes | 26349 ms | 978 / 73 | first draft `{"job":"validate"}` (no decision); repair → `copy_b1` | accepted all-RUN; novel 0 |
| S18 | 31 | full graph | ingest, prepare | yes | 15062 ms | 417 / 35 | `copy_b1` + `jobs: []` | accepted all-RUN; novel 0 |

Potential simulated save if a capable agent had localized (9+12+9) = **30**. Realized save = **0**.

`W_e2e(B2 live) − W_e2e(B1) ≈ +100.9 s`. The agent was slower end-to-end even though `T` did not improve. That is **not** classified as a win.

Generated artifacts (not source): `outputs/benchmark-e010-b1/`, `outputs/benchmark-e010-offline/`, `outputs/benchmark-e010-live/`.

---

## 7.6 Measured stronger-model substitution (E-011)

One B1 run, one offline B2 run, one live B2 run on the **same** S16–S18 file. Model: `qwen3:4b-instruct` (Ollama 0.33.2, digest `0edcdef34593`, 4.0B, Q4_K_M, 2.5 GB). `B2_TIMEOUT_S=180`. Tools off (local default). Prompt `b2-proposal-v3`. No paid API. Default `qwen2.5:3b` tag **not** changed in code.

| Clock / gate | B1 | B2 offline | B2 live (`qwen3:4b-instruct`) |
| --- | --- | --- | --- |
| Simulated cost `T` | **93** | **93** | **93** |
| Jobs executed | 27 | 27 | 27 |
| Unnecessary jobs | 7 | 7 | 7 |
| Correctness | 3/3 | 3/3 | 3/3 |
| False skips | 0 | 0 | 0 |
| Illegal promotions | 0 | 0 | 0 |
| Agent invocations | — | 0 | **3** |
| `used_proposal` | — | 0 | **2** |
| novel_accept / novel_reject | — | 0 / 0 | **0 / 0** |
| Fallback reason | — | no invoke (`offline`) | S17 `malformed`; S16/S18 none |
| Agent latency `W_agent` | 0 | 0 | **172583.688 ms** |
| Job wall `W_jobs` | 6437.31 ms | 8080.273 ms | 6900.012 ms |
| End-to-end `W_e2e` | 6437.31 ms | 8080.273 ms | **179483.7 ms** |
| Tokens (prompt / completion) | 0 | 0 | 1855 / 233 |
| API $ | $0 | $0 | **$0** |
| Q1 | — | parity | **parity** (not a win) |
| Q2 | — | n/a | **no** |

Per scenario (live):

| ID | `T` | Jobs | Unnecessary | Invoke | Latency | Tokens in/out | Proposal | Verifier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S16 | 31 | full graph | ingest, prepare | yes | 91355 ms | 412 / 33 | `copy_b1` + `jobs: []` | accepted all-RUN; novel 0 |
| S17 | 31 | full graph | test, ingest, prepare | yes | 62015 ms | 1026 / 167 | `schema-version` (hyphen); repair failed | **fallback** malformed; novel 0 |
| S18 | 31 | full graph | ingest, prepare | yes | 19214 ms | 417 / 33 | `copy_b1` + `jobs: []` | accepted all-RUN; novel 0 |

Critical comparison on the same rows:

| | B1 | `qwen2.5:3b` B2 (E-010) | `qwen3:4b-instruct` B2 (E-011) |
| --- | --- | --- | --- |
| `T` | 93 | 93 | 93 |
| novel_accept | — | 0 | 0 |
| Valid proposals | — | 3/3 | **2/3** |
| Fallback | — | 0 | 1 |
| `W_agent` | 0 | 99.9 s | **172.6 s** |
| `W_e2e` | 4.5–6.4 s | ~105 s | **~179 s** |
| API $ | $0 | $0 | $0 |
| Q1 / Q2 | floor | parity / no | parity / no |

Potential simulated save if a capable agent had localized (9+12+9) = **30**. Realized save = **0**.

`W_e2e(B2 live) − W_e2e(B1) ≈ +173 s`. Slower than E-010’s 3B live run. Not a win.

S17 raw preview stuffed the file preview into `discovered_edges` with keys `path` / `available` / `content` (not `from_path` / `to_component`). That is **not** a checkable edge. The proposal never reached the verifier.

Generated artifacts (not source): `outputs/benchmark-e011-b1/`, `outputs/benchmark-e011-offline/`, `outputs/benchmark-e011-live/`.

---

## 8. Cursor coding-agent assessment

**Role:** Cursor Grok 4.6 was the **coding agent** used to design and implement this repository (see [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md)). It is **not** the B2 runtime (D-038, D-040).

Labels: **Observation** = measured or in-repo fact. **Hypothesis** = not demonstrated.

### Where B2 currently provides real value

- **Observation:** B2 is a *safe wrapper*: B1 first, invoke only on conservative residue, verifier final, fallback to B1. E-004/E-006/E-008 never false-skipped the frozen suite. E-010 never false-skipped S16–S18.
- **Observation:** Live local invocation works at **$0** (E-006, E-008, E-010).
- **Observation:** After Phase 2.7 the 3B model can emit a **valid** all-RUN proposal (E-008 S16-like; E-010 official S16–S18). That is validity, not extra skips.
- **Observation:** Unit tests (`FakeProvider`) show `novel_accept` / `novel_reject` *can* fire when evidence is planted. That is harness capability, not live-model value.
- **Observation (E-010):** On official S16–S18, B2 did **not** add incremental optimization value. `T` stayed 93. `novel_accept` stayed 0.
- **Observation (E-011):** Substituting `qwen3:4b-instruct` did **not** change that. `T` stayed 93. `novel_accept` stayed 0. Validity was **worse** (S17 malformed).

### Where B1 is already sufficient

- **Observation:** S01–S06, S08–S13: B1 matches the oracle; policy is `b1_sufficient` or `illegal_flow`. Invoking an LLM there would only add latency.
- **Observation:** S07/S14: B1’s full graph **is** the oracle. B2 should not beat B1.
- **Observation:** E-003 already took suite cost 375 → 220 with 0 false skips. That is the measured optimization in this project so far.

### Strongest reasons not to use B2 (today)

- **Observation:** No measured `T` win vs B1 (E-004, E-006, E-008, **E-010**, **E-011**).
- **Observation:** Agent latency (tens of seconds to minutes) exceeds job wall-clock savings in this simulation (§6.3). E-010 live `W_e2e` was ~101 s worse than B1. E-011 was ~173 s worse.
- **Observation:** `qwen2.5:3b` on 8 GB CPU copies `copy_b1` without edges on the official value rows (CD-008, CD-010).
- **Observation:** `qwen3:4b-instruct` on the same host also failed Q1 (CD-011). Two valid `copy_b1`; one malformed. No edges.
- **Observation:** Local default disables tools (D-045), which usually *are* what would find an import needle if the preview is ignored.
- **Hypothesis:** In a real CI with cheap linters and a 3-minute LLM, Q2 stays “no” unless the skipped jobs are expensive.

### What would justify using B2

All of:

1. Safety gate holds on S01–S14 **and** on S15–S18.
2. Q1: `T_B2 < T_B1` on S16–S18 from a verifier-accepted edge (not a suite edit).
3. Q2: measured `W_e2e` improves, **or** a published production time model shows the `T` save beats `W_agent` — and that model is labeled as assumption.
4. Money within the experiment’s budget (default $0).

### Convincing evidence of agentic value

A live run on **S16** (or S17/S18) where:

- B1 executes the full graph (31);
- the model (or tools) surfaces the import/overlay needle;
- the verifier `novel_accept` includes `ingest` and/or `prepare` (S16) or the overlay extras (S17);
- executed jobs match `required_jobs`;
- false skips = 0;
- `T` drops (22 or 19);
- `W_agent` and `$` are reported beside that drop.

S15 cheaper than B1 is **not** convincing; it is a safety bug.

### Is `qwen2.5:3b` adequate?

- **Observation:** Adequate as a **$0, fail-closed** runtime: it can be invoked, and B1 remains correct if it fails.
- **Observation:** Not adequate for Q1: E-008 and E-010 valid proposals saved **0**.
- **Observation (E-011):** A stronger local 4B instruct tag also failed Q1. The 3B-weakness hypothesis is **not** enough to explain the miss by itself under the $0 / 8 GB constraint.

### Continue under $0?

**Observation / recommendation:** Keep `qwen2.5:3b` as the **default** so the project stays reproducible without a live LLM and judges owe no API key. Do not treat any local tag tried so far as the model that will prove Q1. Continuing B2 *architecture* is justified as a fail-closed wrapper. Continuing B2 *as an enabled optimizer under $0* is **not** justified: B1 is the measured product.

### What a stronger paid model might improve

- **Hypothesis:** Higher chance of a well-formed edge + SKIP set; lower malformed/timeout rate; possible tool use.
- **Observation:** E-011 shows that “next local generation, same RAM class” is not sufficient. A paid model would have to be **substantially** more capable at structured localization, not merely 4B vs 3B.
- **Observation:** It cannot legally skip inert-unknown (S14/S15) unless the verifier changes.
- **Observation:** It adds `$` and still has Q2: a 3-minute call for a 9-weight save may lose on this laptop and win only under a production time model.
- **Observation:** It should **not** require architecture changes. Same `B2_BASE_URL` / `B2_MODEL` / `B2_API_KEY` substitution.

### What must not change if a stronger model is introduced

- B0, B1, S01–S14, S16–S18 oracles, S15 control definition, verifier needles, fail-closed unknown, provider-agnostic env (`B2_BASE_URL` / `B2_MODEL`).
- No Cursor SDK as B2 host (D-038).
- No scenario id in the optimizer.

### E-010 interpretation (Cursor, critical)

| Question | Answer |
| --- | --- |
| Did B2 demonstrate genuine incremental value? | **No.** Official rows exist, B1 over-runs as designed, and the live model only copied B1. |
| Where is the limitation? | Primarily the **model** (3B emits `copy_b1` / empty jobs, no edges). The **architecture** invoked correctly and stayed fail-closed. The **verifier** did not reject a good edge; none was proposed. The **scenario design** is fair: needles are in the files; `FakeProvider` can `novel_accept` the S16 shape. |
| Is continuing with B2 justified? | As a safety wrapper: yes. As a hunt for a 3B `T` win: no. |
| Logical next experiment | Done as E-011. |

### E-011 interpretation (Cursor, critical)

| Question | Answer |
| --- | --- |
| Did the stronger model discover anything `qwen2.5:3b` could not? | **No useful discovery.** S16/S18 were the same `copy_b1` + empty jobs. S17 dumped a file preview into `discovered_edges` with the wrong keys and a hyphenated `schema-version`. That never reached the verifier. |
| Did it produce `novel_accept`? | **No** (0). |
| Did it reduce pipeline work? | **No.** `T` = 93 = B1. |
| Was latency acceptable? | **No** for Q2. ~173 s worse e2e than B1; slower than the 3B live run. |
| Does B2 now justify its complexity? | **No** as an optimizer. Yes only as a fail-closed wrapper. |
| Under $0, should B2 remain enabled? | **Not as a product default.** Keep the code; keep offline fallback. Do not expect a local win. |
| If B2 still does not win, is B1 preferred? | **Yes.** B1 is the measured solution under $0. |
| What would a paid stronger model theoretically change? | **Hypothesis only:** higher valid-edge rate on S16–S18. It would not change the verifier, oracles, or B1. Q2 would still be measured. |
| Would that require architecture changes? | **No.** Env substitution only (D-035). |

---

## 9. What Phase 2.9 did not do

- Edit `benchmark/scenarios.json`, B0, B1, or the verifier
- Pull another model or call a paid API
- Claim a B2 cost or e2e win
- Load S15 as an optimization row
- Hard-code scenario IDs into B2
- Start another phase

## 10. What Phase 2.10 did not do

- Redesign B2, B1, or the verifier
- Change S01–S14 or S16–S18 ground truth
- Enable tools, add skills, or add a second provider
- Call a paid API
- Promote `qwen3:4b-instruct` to the default live tag
- Claim a B2 win
