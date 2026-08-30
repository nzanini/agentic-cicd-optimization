# Cursor coding-agent environment

**Purpose:** source of truth for the **coding agent** used to build this repository during the hackathon.  
**Not:** the B2 runtime agent. See [AGENT_PROVIDER_RESEARCH.md](AGENT_PROVIDER_RESEARCH.md) and [CURSOR_DISCOVERIES.md](CURSOR_DISCOVERIES.md).

Do not invent fields. If a value cannot be verified from the session or a file in the repo, it is marked **not programmatically verifiable**.

---

## How to read this file

| Label | Meaning |
| --- | --- |
| `session-verified` | Stated by the Cursor agent identity / tool surface in that conversation |
| `repo-verified` | Recorded in repository docs or git at the time |
| `human-required` | Must be copied from the Cursor UI by the participant |
| `not programmatically verifiable` | This agent cannot read Cursor settings, billing, or the model picker |

The participant should fill the **Human confirmation** table at the end of each phase if they want a stronger audit trail than session identity.

---

## Current session (Phase 3.2 — Git-detector investigation and freeze)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-30 | User/session clock (`user_info`) |
| Phase | 3.2 — Git working-tree detector investigation; docs-only freeze | Human brief |
| Purpose | Analyze whether B1 should auto-discover Git changes; document the decision **not** to implement | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **not programmatically verifiable** (not stated in this brief) | Not exposed |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | none (docs only; no adapter code) | This brief |

Cursor investigated the architecture, proposed an isolated `--from-git` adapter outside B1, found that Git must not replace D-028, and recommended freezing. That recommendation was accepted (D-053). This chat model was **not** used as B2. Judges do **not** need Cursor.

## Prior session (Phase 3.1 — judge reproduction and topology)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 3.1 — Final judge reproduction and repository topology | Human brief |
| Purpose | Clone-and-run docs; public `main` only; no new optimizer | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **not programmatically verifiable** (not restated in this brief) | Not exposed |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | none (docs/audit only) | That brief |

## Prior session (Phase 3.0 — final consolidation)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 3.0 — Final consolidation | Human brief |
| Purpose | Audit and prepare the repo for judges; no new optimizer | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **Fast + High** | Human Phase 3.0 brief (listed as currently known; not read from settings.json) |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | none new (docs/audit only) | This brief |

## Prior session (Phase 2.10)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 2.10 — Stronger local model on S16–S18 | Human brief |
| Purpose | One free/local model substitution; same official value rows | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **not programmatically verifiable** (not stated in that brief) | Not exposed |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | `qwen3:4b-instruct` via Ollama (E-011). Default tag remains `qwen2.5:3b`. | Live run |

## Prior session (Phase 2.9)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 2.9 — Agent-value suite implementation | Human brief |
| Purpose | Implement S16–S18; evaluate B1 / B2-offline / B2-live | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **not programmatically verifiable** (not stated in this brief) | Not exposed |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | `qwen2.5:3b` via Ollama (E-010) | Live run |

## Prior session (Phase 2.8)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 2.8 — Agent-value benchmark design | Human brief |
| Purpose | Design Q1/Q2 methodology and S15–S18; no model swap | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max | **not programmatically verifiable** (not stated in this brief) | Not exposed |
| Extra High | **not claimed** | Not stated |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 in this phase | none new | Docs only |

---

## Prior session (Phase 2.7)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 2.7 — Proposal validity | Human brief |
| Purpose | Improve B2 structured-proposal validity without weakening the verifier | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** | Session tool surface |
| Fast / Slow / Max (or equivalent) | **not programmatically verifiable** (not stated in this brief) | Not exposed to this agent |
| Extra High | **not claimed** | Not stated in this brief |
| Model family | Grok | Session identity |
| Exact model name | **Cursor Grok 4.6** | Session identity |
| Runtime B2 provider used in this phase | local Ollama `qwen2.5:3b` | E-008; not this chat model |

---

## Prior session (Phase 2.6)

| Field | Value | How known |
| --- | --- | --- |
| Date | 2026-08-29 | User/session clock (`user_info`) |
| Phase | 2.6 — Free local agent integration | Human brief |
| Purpose | Wire local Ollama through the existing B2 adapter; run a real $0 B2 experiment | Human brief |
| Coding product | **Cursor** | Session tools and docs |
| Cursor mode | **Agent** (write/search/shell tools available; `SwitchMode` offers `plan` / `agent`) | Session tool surface |
| Model setting | **Fast + High** | Human Phase 2.6 brief (not readable from settings.json) |
| Extra High | **available but NOT used** | Human Phase 2.6 brief |
| Model family | Grok | Session identity (see below) |
| Exact model name | **Cursor Grok 4.6** | Session identity string (see below) |
| Model version build / snapshot | **not programmatically verifiable** | No build id in this session |
| Provider of the chat model | Cursor (identity: jointly trained/owned by SpaceXAI and Cursor) | Session identity |
| Runtime B2 provider used in this phase | local Ollama `qwen2.5:3b` via `B2_BASE_URL` | E-006 / E-007; not this chat model |

### Session identity (verbatim class of statement)

This agent was instructed, for this conversation:

> You are Cursor Grok 4.6, a language model jointly trained and owned by SpaceXAI and Cursor.

That is the **only** exact model name available in-session. It is **not** read from `settings.json`, the Cursor model picker, or an account API.

Cursor’s published Teams pricing page lists **Cursor Grok 4.6** as a first-party “Cursor Model” in the product’s usage pool ([Team Pricing](https://cursor.com/docs/account/teams/pricing)). That supports that the name exists as a Cursor product model. It does **not** prove which picker row the human selected.

**Human action:** open Cursor’s model picker for this chat and record the exact label (and Fast/Slow/Max if shown) in the table below if it differs.

---

## Prior phases (from repo docs, not re-verified here)

These rows summarize what earlier changelog entries already claimed. They are **repo-verified** historical notes, not a new measurement.

| Phase | Date | Repo record | Claimed Cursor model | Claimed mode |
| --- | --- | --- | --- | --- |
| 1.3 | 2026-08-29 | D-008 follow-up | Cursor Grok 4.6 | Agent |
| 2.2 | 2026-08-29 | I-009 | Cursor (Agent) | Agent |
| 2.3 | 2026-08-29 | I-010 | Cursor Grok 4.6 | Agent |
| 2.4 | 2026-08-29 | I-011 | Cursor Grok 4.6 | Agent |
| 2.5 | 2026-08-29 | I-012 | Cursor Grok 4.6 (session identity) | Agent |
| 2.6 | 2026-08-29 | I-013 | Cursor Grok 4.6; Fast + High; Extra High not used | Agent |
| 2.7 | 2026-08-29 | I-014 | Cursor Grok 4.6 (session identity) | Agent |
| 2.8 | 2026-08-29 | this file | Cursor Grok 4.6 (session identity) | Agent |
| 2.9 | 2026-08-29 | this file | Cursor Grok 4.6 (session identity) | Agent |
| 2.10 | 2026-08-29 | this file | Cursor Grok 4.6 (session identity) | Agent |
| 3.0 | 2026-08-29 | this file | Cursor Grok 4.6; Fast + High (human brief) | Agent |
| 3.1 | 2026-08-29 | this file | Cursor Grok 4.6 (session identity) | Agent |
| 3.2 | 2026-08-30 | this file | Cursor Grok 4.6 (session identity) | Agent |

---

## What this environment is not

- It is **not** an API credential.
- It is **not** automatically available to `src/agentic_cicd/b2`.
- Paying for Cursor does **not** mean B2 can call this same chat session as a completions endpoint. See [AGENT_PROVIDER_RESEARCH.md](AGENT_PROVIDER_RESEARCH.md) §3.
- A judge does **not** need a Cursor subscription to reproduce B0 or B1.

## Agent trajectory evidence (honest gaps)

What is in the repository:

- Phase session tables in this file (Cursor Grok 4.6, Agent mode).
- Discoveries [CURSOR_DISCOVERIES.md](CURSOR_DISCOVERIES.md) (CD-001–CD-014).
- Iterations [IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md) (I-001–I-020).
- Experiments [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) (E-001–E-013) with commands and measured numbers. Phase 3.2 added no experiment.
- Decisions [DECISION_LOG.md](DECISION_LOG.md), including D-050 (prefer B1), D-051 (present B1), and D-053 (no Git detector in this submission).

What is **not** in the repository (do not invent it):

- Git commit history. Local `main` currently has **no commits**; `origin` has **no refs**. Trajectory cannot be reconstructed from `git log` until the first commit and push.
- Live B2 JSON (`outputs/benchmark-e006`, `e010`, `e011`, …). `outputs/` is gitignored. Numbers live in the experiment log only.
- Cursor chat transcripts. They are not source-controlled.
- Fast / Slow / Max for most phases (only 2.6 and 3.0 were stated in briefs).
- A filled human confirmation table for every phase (picker labels left blank where not checked).
- An official contest brief PDF.

---

## Human confirmation (fill manually)

Copy from the Cursor UI. Leave blank if not checked.

| Phase | Date | Model picker label | Mode (Agent/Ask/Plan/Debug) | Fast / Slow / Max | Confirmed by |
| --- | --- | --- | --- | --- | --- |
| 2.5 | 2026-08-29 | | Agent (session tools) | | |
| 2.6 | 2026-08-29 | Cursor Grok 4.6 | Agent | Fast + High (Extra High not used) | Phase 2.6 brief |
| 2.7 | 2026-08-29 | Cursor Grok 4.6 (session identity) | Agent | not stated in brief | |
| 2.8 | 2026-08-29 | Cursor Grok 4.6 (session identity) | Agent | not stated in brief | |
| 2.9 | 2026-08-29 | Cursor Grok 4.6 (session identity) | Agent | not stated in brief | |
| 2.10 | 2026-08-29 | Cursor Grok 4.6 (session identity) | Agent | not stated in that brief | |
| 3.0 | 2026-08-29 | Cursor Grok 4.6 | Agent | Fast + High (this brief) | Phase 3.0 brief |
| 3.1 | 2026-08-29 | Cursor Grok 4.6 (session identity) | Agent | not restated in brief | |
| 3.2 | 2026-08-30 | Cursor Grok 4.6 (session identity) | Agent | not stated in brief | |
