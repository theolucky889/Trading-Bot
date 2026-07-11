---
name: stock-analysis-orchestrator
description: >-
  Orchestrates the Trading Bot's stock-analysis agent team (market-analyst,
  quant-developer, fullstack-integrator, qa-verifier). Use for any multi-step
  work on the analysis/backtest feature set: adding indicators, signals, or
  strategies; changing scoring or backtest semantics; building or modifying
  the Analysis/Backtest UI; wiring new API endpoints. Also use for follow-ups:
  "run it again", "re-run the backtest", "update the analysis", "improve the
  previous result", "fix the strategy", "redo only the frontend part".
  Simple one-file questions can be answered directly without this skill.
---

# Stock Analysis Orchestrator

Coordinates who does what, in which order, for the Trading Bot's analysis and
backtesting features. Individual how-to lives in the member skills
(`stock-analysis`, `quant-backtest`); this skill owns sequencing and QA gates.

## Team

| Agent | Owns | Skill |
|-------|------|-------|
| market-analyst | quant/harness.py, indicators.py, data.py, sentiment integration | stock-analysis |
| quant-developer | quant/strategies.py, backtest.py, metrics | quant-backtest |
| fullstack-integrator | src/api/*.ts, views, router, Navbar, vite proxy, app.py endpoint wiring | — |
| qa-verifier | cross-boundary verification, smoke tests | — |

All agent definitions are in `.claude/agents/`. Launch every agent with
`model: "opus"`.

## Execution mode

**Agent team** is the default: create the team, assign tasks with
dependencies, and let members coordinate directly (contract changes flow
analyst/quant → integrator → qa). If team tools are unavailable in the
session, or the change touches a single agent's domain with no contract
change, fall back to direct sub-agent calls (`Agent` tool, background for
parallel work) — the ownership table above still applies.

## Phase 0: context check (always first)

- `_workspace/` exists and the request is a partial fix → re-run only the
  owning agent for that part.
- `_workspace/` exists and the request supplies new inputs → move it to
  `_workspace_prev/` and run fresh.
- No `_workspace/` → initial run.

## Phases

1. **Scope** — map the request to owners via the table above. A request that
   changes an API response shape ALWAYS includes fullstack-integrator.
2. **Backend work** — market-analyst and/or quant-developer implement and run
   their skill's verification command. Parallel when independent.
3. **Incremental QA gate** — qa-verifier checks each finished backend module
   (TestClient smoke + invariants) BEFORE frontend work starts.
4. **Integration** — fullstack-integrator updates TS types/views/proxy;
   `npm run type-check` must pass.
5. **Final QA** — qa-verifier does the cross-boundary comparison (actual JSON
   vs TS types vs template usage) and reports findings; owners fix, QA
   re-verifies.
6. **Record** — update CLAUDE.md harness change log; keep intermediate
   artifacts in `_workspace/` (`{phase}_{agent}_{artifact}.md`).

## Data flow

- Coordination: task list with dependencies (backend → QA gate → frontend → final QA).
- Artifacts: files in `_workspace/` at the repo root (gitignored-friendly, audit trail).
- Contract changes: message the affected agent directly; never let TS types drift.

## Error handling

- A failing verification command blocks the phase; the owning agent fixes it
  (one retry) before QA. If it still fails, stop and report — don't ship a
  broken contract to the frontend.
- Live-data failures are NOT errors: the data layer degrades to synthetic
  with a `warning`; surface it, don't retry-loop on the network.
- Conflicting findings between agents: keep both, report with sources; the
  main session decides.

## Test scenarios

- **Normal:** "Add a stochastic oscillator signal and show it in the UI" →
  market-analyst (indicator + signal, verify) → qa gate → fullstack-integrator
  (type + chart + view) → final QA cross-check → change log row.
- **Error:** quant-developer registers a strategy whose params break
  `run_backtest` (TypeError) → QA catches 422-path regression via TestClient
  POST → quant-developer fixes param validation → QA re-verifies → proceed.
