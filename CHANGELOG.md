---
title: "Safe Memory Changelog"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Changelog

## Unreleased — Alpha V1 prerequisites

- Deny malformed Grants instead of silently interpreting invalid expiry/redactions/windows as permission. Close hidden-order tie leakage when both timestamps and IDs are redacted.

- Apply field projection before matching, caller filters and ranking so hidden fields cannot influence returned results.
- Add the reviewed pending `sm_block` transport shape, replacing its unsafe global Markdown read with current Grant window/field/expiry projection and one fail-closed audit receipt.
- Preserve legacy fixture contracts and named tests; reconcile stale roadmap/remote claims. No authenticated server, real ingestion or Alpha milestone is released by these changes.

## 0.1.0 — committed baseline

Fixture-only stdio contract, deterministic Travel Log builder and development workflow. No real Photos connection or deployed Alpha acceptance is claimed. VERSION stays 0.1.0 until a product milestone is verified.
