# B2 — agentic optimizer contract (Phase 2.3)

**Phase:** 2.3 contract; **2.4** implementation; **2.6–2.7** local path; **2.8–2.10** value suite in [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md)  
**Status:** contract retained; B2 runner implemented (I-011) and **not selected** as the product (D-051). Verifier is stricter than §5 option 2 (D-036). Local model pinned (D-041). S16–S18 official (D-048).  
**Date:** 2026-08-29  
**Does not claim:** a cost win vs B1 (E-004/E-006 `delta_vs_b1 = 0` on S01–S14; E-010/E-011 Q1 parity on S16–S18)

This document is the contract **B2** must satisfy. B0 and B1 remain the protected baselines. B1 is the deterministic safety floor. Implementation details and measured results live in [B2.md](B2.md).

Related: [OPTIMIZATION_CONTRACT.md](OPTIMIZATION_CONTRACT.md), [B1.md](B1.md), [BENCHMARK.md](BENCHMARK.md), [CURSOR_DISCOVERIES.md](CURSOR_DISCOVERIES.md), D-030–D-034.

---

## 0. Why B2 exists

B1 already does this on S01–S14 (E-003):

| | B0 | B1 |
| --- | --- | --- |
| Suite simulated cost | 375 | 220 |
| Correctness | 14/14 | 14/14 |
| False skips | 0 | 0 |
| Unnecessary jobs | 37 | **0** |

B1 matched `required_jobs` on every current scenario. Replacing B1’s `if` statements with an LLM call would not add value on S01–S14.

**Hypothesis:** an agent is useful only where B1 is *conservatively insufficient* — it over-runs because the change is unclassified, ambiguous, history-dependent, or hides a dependency the map does not name — and the agent can produce **checkable evidence** that a smaller sufficient set is safe.

```text
B0  (always run legal jobs)
  →  B1  (deterministic impact graph; fail closed)
    →  B2  (B1 first; agent may refine conservative over-runs; verifier is final)
```

The agent proposes. The **verifier** decides. The agent must not have unilateral skip authority.

---

## 1. Invocation boundary

B1 always runs first. B2 never bypasses B1.

### 1.1 B1 decides alone (do not invoke the agent)

Invoke **only if none of these hold** for the whole change set, or the remaining residue is conservative (see 1.2).

| Condition | B1 already sufficient | Why the agent adds nothing |
| --- | --- | --- |
| Illegal flow | `branch_guard` fail | Policy, not impact reasoning |
| All paths map to **non-conservative** components | Exact required set (S01–S06, S08–S13 class) | B1 already has 0 unnecessary jobs here |
| Known-empty change + development pointer | Clean promote | Identity reuse is deterministic |
| Known cache hit/miss expansion | Producer/consumer already resolved | Hash compare is not an LLM task |
| B1 plan contains **no** `conservative_unknown_or_ambiguous` decision | Floor is already tight | Agent would reproduce rules |
| Expected max save &lt; agent cost budget | Even a perfect skip is not worth the call | See §10 |
| Agent disabled / no API / offline | — | Fail closed to B1 |

Non-conservative components (B1 can finish): `documentation`, `tests`, `pipeline_metadata`, `scoring_overlay`, `catalog`, `personas`, `frozen_model`, `ingest_code`, `prepare_code`, `score_code`, `evaluate_code`, `package_code`.

**Do not invoke** on a docs-only, test-only, known overlay, known model, known catalog, or clean-promote change merely to “have an agent in the loop.”

### 1.2 Eligible to escalate (may invoke)

Escalation is allowed only when B1’s plan is a **conservative over-run** *and* extra inspection could shrink it.

| Residue | B1 behavior today | Why an agent might help |
| --- | --- | --- |
| At least one `unknown` path | Full legal graph | File might be inert, or it might hide a real edge |
| `dependencies` | Full legal graph | Comment-only vs runtime-affecting metadata (still fail closed unless evidence is mechanical) |
| `orchestrator` | Full legal graph | CLI/docs-in-code vs scheduler behavior |
| Mixed known + unknown | Conservative union = full graph | Known subset is exact; unknown residue is the only question |
| `changed_paths is None` | Treated as unknown | Agent might *discover* the change set from a provided diff/index — only if that index is in context |
| History-dependent promote | Empty path list → clean | Ancestry after validation is not in B1 |

**Unknown path does not automatically invoke the agent.** B1 already has a safe answer: RUN the legal graph. Invocation is a *refinement attempt* of that over-run, not a safety replacement.

If the unknown file cannot be inspected (missing workspace, tool budget 0), **do not invoke**; keep B1.

### 1.3 Decision procedure (contract)

```text
plan_b1 ← B1(source, target, changed_paths, cache, registry)
if flow is illegal:
    execute plan_b1          # no agent
if plan_b1 has no conservative residue:
    execute plan_b1          # no agent
if escalation disabled or budget exhausted:
    execute plan_b1
if unknown/ambiguous residue has no inspectable artifacts:
    execute plan_b1
proposal ← Agent(context, tools)   # optional
plan_final ← Verifier(plan_b1, proposal, cache, graph)
execute plan_final
```

`conservative residue` = any classified component in `{unknown, dependencies, orchestrator}` **or** `changed_paths is None` **or** an explicit escalate flag for history-only promote (future).

---

## 2. Agent context

Minimum useful context. Reproducible. No whole-repo dump. No scenario id. No `required_jobs` ground truth.

| Category | Included? | Why |
| --- | --- | --- |
| Flow (`source`, `target`) | Yes | Legal graph and publish/promote differ |
| `changed_paths` (or explicit “unknown set”) | Yes | Same signal B1 used |
| B1 plan (decisions, components, invalidated, promote_mode, run set) | Yes | Agent refines B1; must not rediscover the graph from scratch |
| Job graph, costs, `CONSUMES` / `PRODUCER` | Yes | Producer/consumer proposals must name artifacts |
| Component map (path rules B1 used) | Yes | Agent sees what is already classified |
| Per-artifact cache validity + stored vs current hashes | Yes | Skip-producer evidence |
| Registry pointers (`artifact_id` only) | Yes | Clean/dirty promote |
| Fixture identity hashes | Yes | Same as cache |
| Contents of **unclassified** changed files (byte-capped) | Yes | Localization evidence |
| Import/search hits from tools (bounded) | Yes | Hidden edges |
| Unified diff of changed paths if the harness has one | Yes | Cheaper than whole files |
| Tests that **import** an unclassified path | Optional, via tool | Whether `test` is required |
| Full repository tree | **No** | Noise; use search |
| Other scenarios / ground truth / scenario id | **No** | Would fit the suite |
| Secrets, `.env`, credentials | **No** | Safety |
| Prior chat / other runs | **No** | Reproducibility; use `previous_execution` tool only when the harness attaches a named run |

Context bundle is written to disk as JSON for the run (`agent_context.json` — future). Same bundle → same experiment.

---

## 3. Tools

Minimal set. Each tool is read-only. None of them skip a job.

| Tool | Purpose | Not for |
| --- | --- | --- |
| `read_file(path, offset, limit)` | Inspect an unclassified or referenced file | Dumping the repo |
| `search_repo(pattern, glob?)` | Find imports/string references to a path or symbol | Open-ended browsing |
| `inspect_diff(path)` | See the actual mutation when the harness has a diff | Guessing |
| `inspect_b1_plan()` | Return the B1 decisions already computed | Relitigating illegal flows |
| `inspect_job_graph()` | Jobs, costs, consumes, producers | Inventing new job names |
| `inspect_cache(artifact)` | `has_valid` + identity fields | Treating “file exists” as valid |
| `inspect_pointer(environment)` | Development/production `artifact_id` | Rewriting pointers |
| `classify_path(path)` | What B1 would call this path | Overriding B1 without evidence |

Rejected (this phase): write tools, job execution, web search, shell, “ask human,” unrestricted `find`.

Tool traces are part of the run record (future trajectories).

---

## 4. Output contract

The agent must not return prose such as “run score and evaluate.” It returns one JSON object.

```json
{
  "schema_version": 1,
  "kind": "b2_proposal",
  "uncertain": false,
  "notes": "optional human-readable summary; ignored by the verifier",
  "discovered_edges": [
    {
      "from_path": "scripts/tune_weights.py",
      "to_component": "score_code",
      "via": "import",
      "evidence": [
        {
          "type": "search",
          "path": "scripts/tune_weights.py",
          "detail": "imports agentic_cicd.ranker.score"
        }
      ]
    }
  ],
  "jobs": [
    {
      "job": "score",
      "decision": "SKIP",
      "reason_code": "agent_inert_unknown",
      "reason": "unclassified file is not imported by scoring or package code",
      "confidence": 0.86,
      "dependencies_considered": ["prepare", "evaluate", "package"],
      "artifacts_required": [],
      "artifacts_reused": [],
      "evidence": [
        {
          "type": "search",
          "path": "src/agentic_cicd/ranker",
          "detail": "no reference to unknown/orphan.dat"
        }
      ]
    }
  ]
}
```

### Field rules

| Field | Rule |
| --- | --- |
| `jobs` | Must mention **every** job on the legal flow (same names as B1). Missing job → proposal invalid. |
| `decision` | `RUN` or `SKIP` only |
| `evidence` | Required for every `SKIP` that **narrows** B1 (B1 said RUN). Empty evidence → verifier forces RUN |
| `confidence` | `0.0`–`1.0`. Below `min_confidence` (default 0.7) → treat as uncertain |
| `uncertain` | If `true`, verifier keeps B1 for every contested skip |
| `discovered_edges` | Optional. Verifier accepts an edge only if evidence is mechanically checkable (see §5) |
| `artifacts_reused` | Named cache artifacts; verifier re-checks identity |

Malformed JSON, unknown job names, or missing legal jobs → **reject proposal**, execute B1.

**Wire form (Phase 2.7, D-044):** if `copy_b1` is true, omitted jobs (and listed jobs without `decision`) are filled as **RUN** before validation. This is not a skip. Partial jobs without `copy_b1` remain invalid. The verifier is unchanged.

---

## 5. Deterministic verifier

The verifier is the final authority. It does not call an LLM.

```text
plan_final = plan_b1
if proposal is missing, malformed, or uncertain:
    return plan_b1
for each job:
    if agent says RUN:
        plan_final RUN          # extra RUN is never a safety failure
    if agent says SKIP and B1 said SKIP:
        plan_final SKIP         # already safe
    if agent says SKIP and B1 said RUN:
        if evidence_ok(job) and producer_consumer_ok(job) and policy_ok(job):
            plan_final SKIP
            record novel_accept
        else:
            plan_final RUN
            record novel_reject
return plan_final
```

### Checks (`evidence_ok`)

A skip that narrows B1 is accepted only if **one** of the following is mechanically true:

1. **Localized component.** `discovered_edges` maps every unknown path to a known component, and each edge is checkable (`import` of a ranker module, or explicit read of `scoring_weights.json` / fixtures). Re-plan *as B1 would* on the **localized** component set. The skip set must be a subset of that re-plan’s skips… actually: the final RUN set must be a **superset** of the B1 plan computed on the localized components (plus `branch_guard`). If the agent skipped a job that localized-B1 would run → reject that skip.

2. **Inert unknown (design hypothesis; not implemented).** Every unknown path has tool evidence of **no** import, **no** open/read by ranker, ingest, B0 jobs, or package `code_identity` files. Then the unknown residue adds **no** artifacts. Final plan = B1 plan of the *known* components only. (This is the only way an inert `orphan.dat` becomes skippable — and it is **not** allowed to win against S14 ground truth; see §8.)

   **Phase 2.4 (D-036 / CD-004):** the implemented verifier **rejects** inert-unknown. Absence of search hits is not mechanical proof. Narrowing requires a positive localized edge or a valid cache identity.

3. **Cache identity.** Skip of a producer is backed by `inspect_cache` = valid and the artifact is not in the invalidated set of the localized plan.

Otherwise: force RUN.

### Policy (`policy_ok`)

- Never skip `branch_guard`.
- Never publish/promote on an illegal flow.
- Clean promote: production id must remain the development id; agent cannot invent a rebuild skip that reuses a stale id when bundle inputs localized as dirty.
- No empty/fake artifacts.

### Confidence

`confidence < min_confidence` or `uncertain: true` → do not narrow.

---

## 6. Producer / consumer

Case: **A produces X, B consumes X, B must run, agent proposes skip A.**

The verifier accepts **only** if one of these is true:

| Safe outcome | Required evidence |
| --- | --- |
| Valid cached X | `has_valid(X)` and X not invalidated by the **accepted** impact set |
| Valid previous X | Same identity check against registry/workload, not “file exists” |
| B does not consume X on this flow | Graph says so (e.g. clean `promote` does not consume `bundle`) |
| Otherwise | **A must RUN** |

Forbidden:

- Writing empty `predictions.json` / empty raw catalog so B does not crash
- Skipping A and letting B fail
- Trusting the agent’s prose that “X is probably still good”

This is the same rule B1 already uses. The agent does not get a weaker rule.

---

## 7. Measuring whether the agent adds value

Compare **B0 → B1 → B2** on the **same** fixtures, change set, cache, and ground truth.

B2 vs B0 alone is not enough. B2 vs B1 is the question.

### Primary (gated)

Same as D-015: suite simulated cost, reported as reduction vs B1 only if false skips = 0, correctness 100% on the evaluated suite, and no illegal promote.

A cheaper B2 that false-skips is **not** a win.

### B2-specific metrics

| Metric | Meaning |
| --- | --- |
| `cost_b2` / `cost_b1` / `cost_b0` | Simulated cost |
| `delta_vs_b1` | `cost_b1 − cost_b2` (may be 0 or negative) |
| `correctness` / `false_skips` / `unnecessary` | Same gates as B1 |
| `agent_invocation_rate` | Escalations / scenarios |
| `agent_latency_ms` | Wall time of the agent call (secondary, noisy) |
| `agent_token_cost` | If an API is used; else `null` |
| `verifier_reject_rate` | Narrowing skips rejected / proposed narrowing skips |
| `novel_accept_count` | Skips B1 would not take, verifier accepted |
| `novel_reject_count` | Agent skip rejected; B1 conservative RUN kept |
| `no_invoke_count` | B1-only executions |

**Net value (conceptual):**

```text
value ≈ saved_simulated_cost − k * (latency + api_cost)
```

`k` is a documented experiment knob, not a suite gate. An agent that saves 1 cost unit and spends a paid API call is allowed to be recorded as **not justified**.

On **S01–S14 as they stand**, `delta_vs_b1` is expected to be **0** if B2 is correct: B1 unnecessary jobs are already 0, and S07/S14 *require* the full graph. A B2 that undercuts B1 there is almost certainly a false skip. See §8.

---

## 8. Discovery evidence (runtime B2)

Two record types, written per scenario when B2 runs (future; not implemented).

### 8.1 Novel accept (agent-added value)

```text
B1: conservative RUN (unknown/deps/orchestrator)
Agent: evidence that only component C is affected
Verifier: accept localized plan
```

Record: `discovery_kind=novel_accept`, B1 run set, B2 run set, evidence, verifier notes. This is what README / video / trajectories should quote.

### 8.2 Novel reject (useful failure)

```text
Agent: SKIP
Verifier: insufficient evidence or producer/consumer fail
Final: B1 conservative RUN
```

Record: `discovery_kind=novel_reject`. Failures are evidence, not shame.

### 8.3 Hard limit of the current suite

S14 ground truth is **unknown → all feature→dev jobs**. S07 is **dependencies → all jobs**. Those rows encode the fail-closed *policy*, not “what a perfect inspector would do.”

If B2 inspects `unknown/orphan.dat`, finds no imports, and skips `score`, it **fails S14** even if the file is truly inert.

Therefore: **S01–S14 cannot demonstrate “B2 beat B1 on cost” without failing the frozen contract.** Do not weaken S14 to make the agent look good. Add later scenarios whose ground truth is the *localized* truth (see §9).

S01–S14 **can** demonstrate:

- B2 does not invoke on known cases (S01–S06, S08–S13)
- B2 does not beat B1 by cheating
- Verifier rejects unsafe skips if someone forces escalation
- Correctness stays 14/14

---

## 9. Evaluation scenarios

**Do not modify S01–S14.** They remain the B0/B1 contract and the B2 *regression* suite (B2 must not get worse).

### 9.1 What S01–S14 already cover

Known map, overlay-vs-pipeline (S12), clean/dirty/illegal promote, fail-closed unknown (S14), fail-closed deps (S07). B1 is already at the oracle for these rows.

### 9.2 Agent-value scenarios (Phase 2.8 design; 2.9 official S16–S18)

Canonical definitions, costs, and Q1/Q2 rules: [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md).

S16–S18 live in `benchmark/agent_value_scenarios.json`, not in `scenarios.json` (D-048). S15 remains a documented fail-closed control and is **not** loaded.

| ID | Role | B1 | Oracle `required_jobs` | Official status |
| --- | --- | --- | --- | --- |
| S15 | Fail-closed control (not a cost win) | Full graph 31 | Same as S14. Cheaper B2 = **unsafe**. | Design only |
| S16 | Primary value | Full graph 31 | S03 score chain (22) | Implemented |
| S17 | Hidden overlay | Full graph 31 | S12 overlay chain (19) | Implemented |
| S18 | Docs + S16-like | Full graph 31 | S03 score chain (22) | Implemented |

S19–S21 stay deferred. The old sketch “S15 = `branch_guard` only” is **rejected**.

E-010: B1 `T` = 93; live `qwen2.5:3b` `T` = 93; `novel_accept` = 0; Q1 parity; Q2 no.  
E-011: same rows; live `qwen3:4b-instruct` `T` = 93; `novel_accept` = 0; Q1 parity; Q2 no. Off-suite history: E-007, E-008.

---

## 10. Fair experiment (when B2 exists)

| Held constant | B1 | B2 |
| --- | --- | --- |
| Workspace after `apply` | Yes | Yes |
| `changed_paths` union | Yes | Yes |
| Cache warm (pre-apply) | Yes | Yes |
| Ground truth file | Yes | Yes |
| Scenario id in the optimizer | **No** | **No** |
| `required_jobs` in the optimizer | **No** | **No** |
| File read / search tools | No | Yes (intended capability) |
| Git ancestry | No | Only if a later scenario says so |

Procedure per scenario:

1. Record B1 plan + cost + jobs  
2. Decide invoke / no-invoke from §1  
3. If invoke: store context, tool trace, proposal  
4. Verifier → final plan  
5. Execute final plan (same B0 job bodies)  
6. Judge vs ground truth  
7. Append novel_accept / novel_reject / no_invoke  

B2 may use **more inspection** than B1. That is the capability under test. B2 may not use **answers** B1 is denied (scenario id, required jobs).

---

## 11. When not to use the agent

Repeat of §1.1 in operational form:

- Known documentation-only  
- Known test-only  
- Known pipeline.json-only  
- Known overlay / model / catalog / named ranker file  
- Known clean promote  
- Illegal promotion  
- B1 plan already has zero conservative reasons  
- Agent cost exceeds the remaining skippable weight (if `score` is already skipped, almost nothing left)  
- Offline / no local runtime / no hosted key / kill switch  

The production shape is **B1 by default, agent as a specialist**, not “agent on every PR.”

---

## 12. Cost / latency

Agent calls have wall-clock and possibly API cost. Simulated job weights do not include them.

Record `agent_latency_ms` and `agent_token_cost` separately from `simulated_cost`. Do not mix them into the safety gate.

A justified B2 experiment is defined in [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md) §5–6:

- **Q1:** `T_B2 < T_B1` on S16–S18, safety pass (`novel_accept` with checkable edges).  
- **Q2:** measured end-to-end time (`W_jobs + W_agent`) improves, or a later labeled production mapping.  
- Valid copy-B1 or fallback is **parity**, not a win.  
- 10 s of pipeline save vs 3 min of reasoning is a **Q2 no**.

---

## 13. Unresolved / closed in 2.4

- Model/host: **closed (D-035, D-041)** — one OpenAI-compatible client; live default `qwen2.5:3b` on local URL; hosted `gpt-4o-mini` unused; tests use `FakeProvider`.  
- `min_confidence`: **0.7** (env `B2_MIN_CONFIDENCE`). `k` still unused.  
- S15+: **recommended, not implemented** (D-043). E-007 ran conceptual S16 off-suite only. First live suite run is E-006.  
- Git ancestry tool (only if S19 is in scope)  
- Whether `dependencies` is ever escalated (high false-skip risk vs S07) — not escalated beyond inspectable+offline policy  
- GitHub Actions (still out of scope; **not required** for judges; not present in this repository)

---

## 14. What Phase 2.3 did not do

Phase 2.3 was design only. Phase 2.4 implemented the runner. It still does **not**:

- Change B0, B1, or `benchmark/scenarios.json`  
- Claim a B2 cost win on S01–S14  
- Add S15–S21  
- Add GitHub Actions (intentionally omitted; local reproduction is sufficient)
