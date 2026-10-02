---
title: "Knowledge Prerequisite Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# V1.2 internal calculations — unreleased

Pure deterministic modules only; not a persistent server Block or shipped V1.2.

- Implemented date/range/year queries, explicit geography rollups, media statistics, On This Day and last N occasion queries. Only projected source fields are used; missing timezone remains unknown; exact leap-day default preserves unknown occurrences.
- Implemented versioned inferred same-day/overnight trip candidates, observed gaps, known third-party exclusion, historical confirmed habitual-area/commuting exclusion and explicit limitations. Defaults 72h/2000km/min1 are configurable hypotheses, not accuracy claims. Candidate IDs are not persistent correction IDs.
- No storage, auth, HTTP/MCP exposure, durable index generations, correction persistence, habitual suggestions, runtime sample or whole-library scale acceptance. Caller must project all Records/enrichment/habitual areas, audit responses and rebuild per policy revision.

## Test receipts

Tested integrated implementation `7e389d220d83c63b0b032adb71408d90566e3b60` against main e6bf38650371e91a201801e3a88916be9dc382f8. [Aggregate](gate.md): exit0, 147 passed/0 failed. [Transport](contract.md): exit0,67/0. Includes all 118 prior integrated checks plus 18 capability and 11 trip tests.

TDD first runs failed on missing modules. Review regressions for malformed offset minutes, exact leap default and empty statistics failed before correction; final checks pass. Source-free synthetic datasets cover midnight crossings, unknown dates/locations, leap years, unknown intervening occasions, replay IDs, third-party provenance, multiple/historical habitual areas, multi-city observations and gaps. No model or network client.

F2-01/F2-02/F2-05 are partially verified at pure-function level only. F2-04 indexed persistence/performance, F2-06 habitual suggestions/edits and F2-07 persistent corrections are pending. No UI/browser proof applies to these internal modules. Inputs and full sprint criteria remain in ../1.0.0/INPUTS.md and EVIDENCE.md. No VERSION bump.
