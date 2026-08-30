# Agent provider / reproducibility (Phase 2.5–2.6)

**Phase:** 2.5 investigation; **2.6** first live local-agent run; **2.10** one stronger local substitution  
**Status:** local Ollama path implemented; hosted paid APIs unused  
**Date:** 2026-08-29  
**Does not claim:** a simulated-cost win vs B1. E-011 Q1 parity on S16–S18.

Phase 2.5 documented why Cursor is not B2’s runtime and recommended local OpenAI-compat. Phase 2.6 **implements that path** with one pinned model. No paid API was used. No participant API key is required. B0, B1, and S01–S14 were not changed.

Related: [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md), [B2.md](B2.md), [AGENT_DESIGN.md](AGENT_DESIGN.md), [AGENT_VALUE_BENCHMARK.md](AGENT_VALUE_BENCHMARK.md), D-038–D-050, E-006–E-011.

---

## 0. How this document is labeled

| Label | Meaning |
| --- | --- |
| **Verified** | Official docs or in-repo facts cited below |
| **Unavailable** | Could not be confirmed from official materials in this phase |
| **Assumption** | Working belief; not treated as fact |
| **Recommendation** | Proposed next path; **not implemented** |

---

## 1. Current facts (verified, in-repo)

B2 already has a provider interface (`LLMProvider` / `OpenAICompatProvider` in `src/agentic_cicd/b2/provider.py`). E-004 ran **without** `B2_API_KEY`:

| Metric | E-004 |
| --- | --- |
| B2 suite cost | 220 (same as B1) |
| Correctness | 14/14 |
| False skips | 0 |
| Agent invocations | 0 |
| Model USD | 0 |

**Verified (E-006):** suite cost **220** (= B1); 2 invocations, both malformed.  
**Verified (E-008):** compact `copy_b1` prompt produced a **valid** live proposal on conceptual S16 in 31 s (all-RUN; no `novel_accept`). Larger templates timed out. Verifier unchanged. Offline B2 remains a safe B1 fallback.

---

## 2. Two different “agents”

| | Cursor (coding agent) | B2 (runtime optimizer) |
| --- | --- | --- |
| Who uses it | The participant, in the IDE | The CI simulation, when invoked |
| Job | Write, review, and document this repo | Propose a `b2_proposal` for one change set |
| Authority | Human + Cursor | **Verifier** is final; model cannot skip |
| Credential | Cursor login / subscription | Optional `B2_BASE_URL` (local) or `B2_API_KEY` (hosted). Never a Cursor key. |
| Recorded in | [CURSOR_ENVIRONMENT.md](CURSOR_ENVIRONMENT.md), I-00x | `b2_record.json`, E-004 |

These must not be collapsed. Using Cursor to build the project does **not** mean B2 called a model.

---

## 3. Can the Cursor subscription be B2’s runtime provider?

### Verdict: **NO**

Meaning: do **not** treat the paid Cursor IDE session as B2’s LLM. Official Cursor APIs exist, but they are the **wrong product surface**, they need a **separate key**, they are **usage-billed**, and a judge **cannot reproduce them with the participant’s login**.

### 3.1 What official Cursor docs say (verified)

| Fact | Source |
| --- | --- |
| Cursor publishes Admin, Analytics, Cloud Agents, and SDK APIs | [Cursor APIs Overview](https://cursor.com/docs/api) |
| Cloud Agents API + SDKs “run Cursor agent workflows (workspace context, tools, commands, and edits). They are **not a standalone model-inference or chat-completions API**.” | same page |
| Python SDK (`cursor-sdk`) requires `CURSOR_API_KEY` (user key from Dashboard → API Keys, or a team service-account key) | [Python SDK](https://cursor.com/docs/sdk/python) |
| SDK default examples use model `composer-2.5`, not the IDE chat picker | same |
| SDK/cloud runs “follow the same pricing, request pools, and Privacy Mode rules as runs from the IDE and Cloud Agents.” Spend appears under an SDK tag. | same |
| Cloud Agents are “charged at API pricing for the selected model” and require a spend limit; docs also say you need a **paid Cursor plan** for cloud agents | [Cloud Agents](https://cursor.com/docs/cloud-agent) |
| Teams usage includes first-party “Cursor Models” (docs name Cursor Grok 4.6, Grok 4.5, Composer 2.5) plus third-party models at list price + a Cursor token rate | [Team Pricing](https://cursor.com/docs/account/teams/pricing) |

**Verified:** a Cursor subscription does **not** automatically hand our Python process an inference credential. A key must be created in the dashboard. This phase did **not** create one.

**Verified:** the official API is an **agent runner** (edit repo, tools, commands), not `POST /v1/chat/completions` for a bounded `b2_proposal`.

### 3.2 Direct questions

| Question | Answer |
| --- | --- |
| Is there an official Cursor API? | **Yes** — Cloud Agents API + TypeScript/Python SDKs. |
| Does the subscription expose inference credentials by itself? | **No.** A dashboard API key is a separate object. |
| Can the same IDE chat model be called from our B2 app? | **Not as a drop-in completions API.** The SDK launches a Cursor *coding agent* (default examples: `composer-2.5`). It is not documented as “call whatever is selected in this chat.” |
| Terms / license? | **Unavailable in full.** `https://cursor.com/terms/ai` returned 404 from this environment. Cloud-agent docs describe usage billing. Using an undocumented/private IDE pipe would be **unsuitable**. |
| Can a judge reproduce it without the participant’s credentials? | **No.** They would need their own Cursor account, API key, and usage budget. |
| Supported local/CLI/headless? | **Yes, as Cursor agents** (SDK local runtime against `cwd`), still requiring `CURSOR_API_KEY` and still an agent runner, not B2’s tool jail. |
| Undocumented IDE hook? | **Unsuitable** even if it existed. |

### 3.3 Why it is a poor B2 fit even if a key existed

- B2 already owns tools, context, schema, and verifier. A Cursor SDK agent brings **its own** tools (including writes/commands). That fights D-032 (verifier-owned skips; read-only tools).
- Usage is billed / drawn from Cursor usage pools. That conflicts with the **$0 additional spend** constraint.
- Reproducibility fails: judges do not share Nahuel’s Cursor login.

**Assumption (not used as a gate):** some Cursor plans may include unused allowance that *could* pay for SDK runs. Even if true, it is personal, non-portable, and the API is still the wrong shape.

---

## 4. Provider-agnostic architecture

Preferred conceptual shape (already mostly true):

```text
B2 contract (context, tools, schema)
        ↓
Provider adapter  (LLMProvider.complete)
        ↓
  OpenAI-compatible host
  (local Ollama / Groq / OpenAI / other)
        ↓
structured b2_proposal
        ↓
deterministic verifier
        ↓
existing job executor
```

**Verified (in-repo):** `LLMProvider` is a tiny protocol. `OpenAICompatProvider` speaks Chat Completions. `FakeProvider` is used in tests. The rest of B2 does not import an SDK.

**Practical?** **Yes.** Keep one adapter. Do **not** add a Cursor SDK adapter unless a later decision explicitly accepts agent-runner semantics (not recommended).

The repository should continue to own: contract, tools, context, schema, verifier, evaluation, observability. The external model only fills the reasoning/proposal slot.

**Recommendation:** remain provider/model agnostic at the HTTP layer. Pin a *documented default live host* later if a live run is approved; do not hard-code a vendor in the planner/verifier.

---

## 5. How a judge reproduces B2

**Judges do not need this section to reproduce the headline result.** The required path is B0 then B1 (README). B2 is an optional experiment and was rejected as the production optimizer.

Personal credentials of the participant are never required. Cursor is not required. Ollama is not required. An API key is not required. GitHub Actions is not required.

### What is always deterministic (no model)

B0, B1, verifier, job graph, cache identity, S01–S14 ground truth, and **offline B2** (no `B2_API_KEY` → no invoke → B1 plan). E-004 is this case: cost 220, 14/14.

A judge with **only** Python 3.11+ (or the documented Docker image) can reproduce E-004 exactly on simulated cost, correctness, and executed jobs. Wall-clock may vary.

### Case A — Judge has an API provider (OpenAI, Groq, …)

| | |
| --- | --- |
| Can B2 run? | Yes. Offline path always. Live path if they set **their** `B2_API_KEY`, `B2_BASE_URL`, `B2_MODEL`. |
| Configure | Env vars only. Never commit keys. |
| Deterministic | Planner + verifier + fallback. |
| Exact reproduce | Offline suite = E-004. Live proposals **may vary** by model/version/temperature/rate limits. Accepted skips still cannot violate the verifier. |
| May vary | Invocation count, `novel_accept` / `novel_reject`, latency, token USD, malformed-fallback rate. |

### Case B — Judge has a local model (Ollama or similar)

| | |
| --- | --- |
| Can B2 run? | Yes. Point `B2_BASE_URL` at `http://127.0.0.1:11434/v1` (or equivalent). `B2_API_KEY` can be a dummy string; Ollama’s OpenAI compat treats it as required-but-ignored ([Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)). |
| Configure | Install Ollama (or other runtime), `ollama pull qwen2.5:3b`, set `B2_MODEL=qwen2.5:3b` and `B2_BASE_URL=http://127.0.0.1:11434/v1`. |
| Deterministic | Same as A for the floor. |
| Exact reproduce | Same model **tag** is the reproducibility unit. Bit-identical logits across CPU/GPU are **not** guaranteed. |
| May vary | Hardware, Ollama version, experimental OpenAI-compat layer ([docs note it can change](https://ollama.readthedocs.io/en/openai/)). |

Ollama’s CLI project is **MIT** ([license](https://github.com/ollama/ollama/blob/main/LICENSE)). Individual **weight** licenses are per model. Ollama’s website also markets hosted/cloud capacity; that is a **different**, not-assumed-free product.

### Case C — Judge has Cursor

| | |
| --- | --- |
| Can B2 run? | **Yes, offline**, like everyone else. Cursor is not required to execute B2. |
| Configure | Nothing Cursor-specific for B2. |
| Cursor as B2 host? | **No** (see §3). Optional: they may also use Cursor as a *coding* agent to read the repo. |
| Exact reproduce | E-004 offline numbers. |

### Case D — Judge has another coding/agent tool

Same as C: the coding tool is irrelevant to B2 execution. They may implement another `LLMProvider` later; not required.

### Case E — Judge has no model / no API

| | |
| --- | --- |
| Can B2 run? | **Yes.** This is the default. |
| Configure | Unset `B2_API_KEY`. |
| Exact reproduce | E-004 (B2 = B1). |
| Live agent value | Not demonstrated. That is honest. |

---

## 6. Cost / free options

No option was purchased. No account was created. Classifications:

| Class | Meaning |
| --- | --- |
| Genuinely free | Software/local inference with $0 vendor invoice if hardware already exists |
| Free tier with limits | Official free plan; account and rate limits; may change |
| Paid | Invoice or prepaid usage |
| Unknown | Official price/terms not confirmed here |

### 6.1 Local open-weight (Ollama / llama.cpp)

| | |
| --- | --- |
| Monetary cost | **Genuinely free** for the *runtime software* (Ollama MIT). Electricity/hardware not $0 in physics, but $0 vendor API. |
| Setup | Medium: install + pull a model (RAM/disk). |
| Reproducibility | Good if the **model tag** is pinned in docs. Not bit-identical across machines. |
| Latency | Hardware-dependent; often seconds on CPU, faster on GPU. |
| Structured JSON | Possible on instruct models; quality varies. Verifier remains the gate. |
| Rate limits | Local process only. |
| Hardware | Small models need a few GB RAM; large models need a GPU. |
| License | Runtime MIT; **weights are per-model**. |

**Implemented in Phase 2.6:** existing `OpenAICompatProvider` + local Ollama + pinned `qwen2.5:3b`. See §11.

### 6.2 Groq API

| | |
| --- | --- |
| Monetary cost | **Free tier with limits** (official “Free Plan” rate-limit tables exist: [Groq Rate Limits](https://console.groq.com/docs/rate-limits)). Developer plan is pay-as-you-go after adding a payment method ([Billing FAQs](https://console.groq.com/docs/billing-faqs)). |
| Setup | Account + API key (this phase did **not** create one). Compatible with current client via `B2_BASE_URL`. |
| Reproducibility | Shared service; limits and catalog can change. Judge needs their own key. |
| Latency | Typically low (hosted LPU). |
| JSON | Chat Completions compatible. |
| Constraint | Creating an account is extra work and is **not** $0-policy-clean if a later Developer upgrade bills usage. |

Do **not** call Groq “free” without the free-tier qualifier.

### 6.3 OpenAI hosted (`gpt-4o-mini` default in D-035)

| | |
| --- | --- |
| Monetary cost | **Paid** (list prices; D-035 documented estimates). Free-tier claims are **unknown** / not relied on. |
| Fit | Already the code default host, but **disabled** without `B2_API_KEY`. Rejected for the next *spend* path. |

### 6.4 Cursor Cloud Agents / `cursor-sdk`

| | |
| --- | --- |
| Monetary cost | **Paid / usage-billed** (official). Not a $0 B2 host. |
| Fit | Wrong API shape (§3). |

### 6.5 Other hosted free tiers (Gemini, OpenRouter “free” models, etc.)

**Unknown** for this write-up: not fetched to a stable official price card in this phase. Do not treat as free.

---

## 7. Does the hackathon require a runtime B2 LLM?

**Unresolved** from official challenge text available here.

**Verified in-repo / public marketing (not the private brief):**

- Repo: [micro1](https://micro1.ai) “Agentic Workflows Hackathon”; methodology says use agents to investigate the problem ([README.md](../README.md)).
- Public posts describe the **Frontier Engineering Challenge 2026** as using **coding agents** on a real engineering problem; judging themes in third-party write-ups include correctness, reproducibility, testability, explanation ([HackerEarth listing](https://www.hackerearth.com/community/challenges/hackathon/micro1-frontier-engineering-challenge-2026/), secondary commentary).
- The HackerEarth challenge page itself **timed out** from this environment; the **full official brief is not in this repo**.

**Do not over-read the rules.** Public language strongly supports **Cursor-as-coding-agent** as the intended “use an agent” requirement. Whether judges also require a **live model inside the submitted program** is **not** established.

**Verified in-repo product hypothesis (D-023):** this project *chose* a runtime B2 so the question “what did the agent improve vs B1?” can be asked. That is our architecture, not a proven contest mandate.

---

## 8. Recommendation (implemented in 2.6)

1. **Keep** the provider-agnostic OpenAI-compatible adapter. Do **not** add a Cursor SDK provider.
2. **Keep** offline B1 fallback as the default anyone can reproduce (E-004).
3. Live B2 uses **local Ollama** at `B2_BASE_URL=http://127.0.0.1:11434/v1` with pinned **`qwen2.5:3b`**. No API key required for that host.
4. **Do not** spend money on OpenAI/Cursor API usage for B2.
5. **Do not** require judges to have any vendor account.
6. Agent-value scenarios (S15+) remain a separate approval; S01–S14 stay the regression suite.

Phase 2.6 executed this path. E-006 shows the suite is safe. E-007 shows a 3B CPU model is not yet reliable enough for structured `b2_proposal` JSON.

---

## 9. Sources

- [Cursor APIs Overview](https://cursor.com/docs/api)
- [Cursor Python SDK](https://cursor.com/docs/sdk/python)
- [Cursor Cloud Agents](https://cursor.com/docs/cloud-agent)
- [Cursor Team Pricing](https://cursor.com/docs/account/teams/pricing)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Ollama MIT license](https://github.com/ollama/ollama/blob/main/LICENSE)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Billing FAQs](https://console.groq.com/docs/billing-faqs)
- In-repo: `src/agentic_cicd/b2/provider.py`, E-004, D-035

---

## 10. What Phase 2.5 did not do

- Change B0, B1, B2, or S01–S14
- Call a live model
- Create or store credentials
- Implement Ollama wiring beyond what already existed (`B2_BASE_URL`)
- Start Phase 2.6

---

## 11. Selected local model (Phase 2.6)

**One model only.** Nothing else was pulled.

| Field | Value |
| --- | --- |
| Model name | Qwen2.5 3B Instruct (Ollama) |
| Exact tag | `qwen2.5:3b` |
| Digest (this machine) | `357c53fb659c` / `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b` |
| Parameters | 3.1B |
| Quantization | Q4_K_M |
| Download size | **1.9 GB** |
| Context window | **32768** (Ollama `show`) |
| Embedding length | 2048 |
| Architecture | qwen2 |
| Ollama capabilities | `completion`, `tools` |
| Weight license | Qwen Research License (Ollama `show`; not Apache-2.0) |
| Runtime | Ollama **0.33.2** (`winget` package `Ollama.Ollama`) |
| Host used here | Windows, **8 GB** RAM (`8451756032` bytes), CPU inference |
| Expected RAM/VRAM | ~3–4 GB for Q4_K_M 3B; 8 GB host is the reason 7B was rejected |
| Expected latency (this host) | **~3–5 minutes per invocation** (E-006: 287 s / 198 s; E-007: 215 s) |
| Structured-output support | Requested as JSON `b2_proposal`. Ollama advertises tools. **Measured:** model often emits invalid schema (`schema_version must be 1` on E-007; malformed on S07/S14). Verifier remains the gate. |
| API cost | **$0** |
| Why this model | Fits 8 GB RAM; better instruction/JSON reputation than llama3.2:3b at the same size class; 32k context; one `ollama pull`; replaceable via `B2_MODEL` |

**Rejected without downloading:** 7B+ (RAM), hosted paid APIs, Groq (account), Cursor SDK, multiple local tags.

### Install and configure

Host (Windows, as used here):

```text
winget install --id Ollama.Ollama
ollama pull qwen2.5:3b
```

Binary observed: `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`  
API: `http://127.0.0.1:11434/v1`

Environment (no participant API key):

```text
B2_BASE_URL=http://127.0.0.1:11434/v1
B2_MODEL=qwen2.5:3b
B2_TIMEOUT_S=180
```

Do **not** set `B2_API_KEY` for local. Hosted URLs still require a key and are unused.

From Docker (`python:3.12-slim`) to a host Ollama:

```text
B2_BASE_URL=http://host.docker.internal:11434/v1
B2_MODEL=qwen2.5:3b
B2_TIMEOUT_S=180
```

Default `B2_TIMEOUT_S` remains **30** so hosted/offline tests stay fast. CPU 3B needs ~180 s.

### Reproduce the live experiment

1. `python -m pip install -e ".[dev]"` (or the documented Docker image).
2. Install Ollama; `ollama pull qwen2.5:3b`.
3. Set `B2_BASE_URL` and `B2_MODEL` as above.
4. `python -m agentic_cicd benchmark --system ladder --output outputs/benchmark-e006`
5. Inspect `outputs/benchmark-e006/comparison.json` and each `b2/runs/Sxx/b2_record.json`.
6. Optional off-suite S16-like: `python scripts/run_s16_like_local.py` → `outputs/e006-s16-like/`.

### Deterministic fallback (no local model)

Unset `B2_BASE_URL` and `B2_API_KEY`. B2 does not invoke. Suite matches E-004 (cost 220, 0 invocations). If `B2_BASE_URL` points at localhost but Ollama is down, policy records `offline` (“local runtime unavailable”) and keeps B1. **Never fail open.**

The repository is fully usable without Ollama.

---

## 12. What Phase 2.6 did not do

- Modify B0, B1, or S01–S14
- Add S15–S21 to `benchmark/scenarios.json`
- Call OpenAI, Anthropic, Cursor, Grok, Groq, or any paid host
- Add a second provider class, RAG, LangGraph, or Cursor adapter
- Claim a B2 cost improvement vs B1 (E-006 `delta_vs_b1 = 0`)

---

## 13. Phase 2.10 model substitution (selected before pull)

**One additional local tag.** Default live model remains `qwen2.5:3b` (D-041). This section records the stronger-model substitution used for E-011. No paid API. No second provider class. B2 architecture unchanged.

### Host (measured this session, before pull)

| Field | Value |
| --- | --- |
| RAM | **8 GB** (2×4 GB; `TotalVisibleMemorySize` 8253668 KiB) |
| Free RAM at inspect | ~3.0 GB |
| CPU | Intel Core i3-7100U @ 2.40 GHz, **2 cores / 4 threads** |
| GPU | Intel HD Graphics 620 (no CUDA; CPU inference) |
| Disk free | ~332 GB |
| Ollama | **0.33.2** |
| Already pulled | `qwen2.5:3b` only (`357c53fb659c`, 1.9 GB) |

### Selected model (documented before `ollama pull`)

| Field | Value |
| --- | --- |
| Model name | Qwen3 4B Instruct 2507 (Ollama) |
| Exact tag | `qwen3:4b-instruct` (alias of `qwen3:4b-instruct-2507-q4_K_M`) |
| Digest (this machine) | `0edcdef34593` (`ollama list` / `ollama show`) |
| Parameters | **4.02B** |
| Quantization | **Q4_K_M** |
| Approximate download size | **2.5 GB** |
| Advertised context | 256K (library page). Runtime KV must stay modest; inspect `num_ctx` after pull. |
| Expected RAM | ~3.8–4.5 GB weights+overhead at a short context (similar class to the existing 3B). 8 GB host is tight but previously ran `qwen2.5:3b`. |
| Expected latency (this host) | Hypothesis: slower than 3B (more params) but in the same minutes-per-invocation band if thinking mode is **off**. Dual-core CPU; no GPU. |
| Weight license | Apache-2.0 (Ollama Qwen3 library page) |
| API cost | **$0** |
| Compatible? | Yes — existing `OpenAICompatProvider` + `B2_MODEL` / `B2_BASE_URL` |

### Why this model over `qwen2.5:3b`

E-010 / D-049: the 3B tag copies `copy_b1` and does not emit checkable edges. The question is whether a **stronger same-host model** changes Q1.

`qwen3:4b-instruct` is the next Qwen generation at nearly the same disk/RAM class (2.5 GB vs 1.9 GB; ~4B vs 3.1B). Official Qwen3 materials claim a large jump in instruction following, coding, and agent/tool use versus Qwen2.5 instruct at this size. The **instruct** (not thinking) tag was chosen so the model emits the JSON `b2_proposal` without a long chain-of-thought that would dominate the 180 s timeout on this CPU (E-008: large templates already timed out on 3B).

### Rejected without downloading

| Candidate | Why not |
| --- | --- |
| `qwen2.5:7b` / `qwen3:8b` (~4.7–5.2 GB) | Previously rejected (D-041). 8 GB Windows + Docker + Ollama would swap; dual-core i3 latency would be worse than the 3B 15–58 s/call. User rule: prefer a runnable model over a theoretically stronger unusable one. |
| `qwen3:4b` / `qwen3:4b-thinking` | Same 2.5 GB class, but thinking mode emits large hidden traces. On this CPU that is likely a timeout, not a fairer Q1 test. |
| `qwen3:4b-instruct` Q8 / fp16 (4.3 / 8.1 GB) | Exceeds comfortable 8 GB RAM. |
| `phi4-mini` (3.8B, 2.5 GB) | Also runnable and reasoning-strong. Not chosen so the substitution stays in the Qwen family (isolates generation, not vendor). One model only. |
| `llama3.2:3b` | Same size class; Phase 2.6 already judged it weaker for JSON than `qwen2.5:3b`. |
| Hosted / Groq / Cursor SDK | Paid or account-gated. Forbidden this experiment. |

### Configure (after pull; default tag unchanged)

```text
B2_BASE_URL=http://127.0.0.1:11434/v1
B2_MODEL=qwen3:4b-instruct
B2_TIMEOUT_S=180
```

Do **not** set `B2_API_KEY`. Do not change `DEFAULT_LOCAL_MODEL` in code unless a later decision promotes this tag.

### Confirmed after pull (before the suite)

`ollama show qwen3:4b-instruct`: architecture `qwen3`; parameters **4.0B**; quantization **Q4_K_M**; advertised context 262144; embedding 2560; capabilities `completion`, `tools`, `thinking`; license Apache-2.0. Runtime `ollama ps` during a 2-token health check: **3.2 GB**, **100% CPU**, **num_ctx 4096** (not the advertised 256K). Health check: **30806 ms**, content `Ok`, tokens 13/2, `$0`. Free RAM after load: **311 MB** of 8060 MB. Runnable; tight.

### E-011 result (same S16–S18)

Live B2 `T` = **93** (= B1). `novel_accept` = **0**. S16/S18 valid `copy_b1`. S17 malformed (`schema-version`). `W_agent` **172584 ms**. `$0`. Q1 parity. Q2 no. Default live tag remains `qwen2.5:3b`.
