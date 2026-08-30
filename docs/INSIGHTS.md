# Insights and lessons

**Status:** final consolidation (3.0–3.1)  
**Date:** 2026-08-29  
**Does not claim:** that a runtime LLM beat B1.

This is the judge-facing hot take. Numbers come from [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md). Development process: [CURSOR_DISCOVERIES.md](CURSOR_DISCOVERIES.md), [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md).

---

## What worked

**B1 is the product.** An impact graph plus identity-checked cache cut S01–S14 simulated cost from **375 to 220** with **0 false skips** (E-003). That is the only measured optimization win in this project.

**Fail closed is a feature.** S07 (dependencies) and S14 (unknown path) require the full graph. Treating “we didn’t find an import” as a skip would have manufactured a cheaper, **wrong** system (CD-004, D-036).

**Cursor as coding agent was useful.** The repo was designed, implemented, and audited in Agent mode (Cursor Grok 4.6). Discoveries such as “S14 cannot be the B2 win row” and “Cursor is not a B2 completions API” changed the architecture before they could contaminate the benchmark (CD-001, CD-005).

**A ladder beats a jump.** B0 → B1 → B2 made it possible to say *what* improved. Jumping from B0 to an LLM would have hidden that the gain was rules, not the model (D-023).

---

## What failed (and was kept)

**B2 did not beat B1.** Offline (E-004) and live local (E-006, E-010, E-011) all have `delta_vs_b1 = 0` on the suites that matter. `novel_accept` on official S16–S18 is **0**.

**Small local models copy B1 or break the schema.** `qwen2.5:3b` eventually emitted valid `copy_b1` JSON (E-008, E-010) with **zero** extra skips. `qwen3:4b-instruct` did the same on S16/S18 and was **malformed** on S17 (E-011). Both added ~100–180 s of end-to-end latency.

**S01–S14 cannot show agent value.** B1 already matches those oracles. A cheaper B2 on S07/S14 would be a false skip (CD-001). Official S16–S18 exist so that conclusion can be tested fairly. The models still did not localize.

Those failures stay in the logs. They are the evidence that B2 is an experiment, not the submitted optimizer.

---

## Hot take

On a correctness-constrained CI skip problem, **checkable rules beat a $0 local agent wrapper**.

The agent that mattered here is the **coding agent** (Cursor) used to find the contract, implement B1, refuse to weaken the verifier, and measure B2 honestly. Shipping `qwen2.5:3b` or `qwen3:4b-instruct` inside the runner did not reduce pipeline work. A judge does not need Cursor (or Ollama) to verify that conclusion: clone `main` and run B0 then B1.

A stronger **paid** model might raise the valid-edge rate on S16–S18. That is a hypothesis. It would still be an env substitution (`B2_MODEL` / `B2_API_KEY`), still sit behind the same verifier, and would still have to beat B1 on both simulated work **and** end-to-end time. This project does not claim that result.

---

## What we would not do again

- Replace B1 `if` statements with an LLM call and call that “agentic CI.”
- Edit S14 (or S16–S18) so a weak model looks cheaper.
- Treat “no search hits” as proof a file is inert.
- Spend another phase retrying the same 3B/4B local tag for a `T` win (D-049, D-050).
- Use Cursor Cloud Agents / `cursor-sdk` as B2’s runtime (wrong API, billed, not judge-reproducible).
