---
title: "Progressive Scan Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Progressive scan candidate

Implementation `a298df3a14cba6757eb6c9c0416d0a2b09e5c65d` contains main `708d6cc3ec82da240effb2770efd18b7ef5cccbc`, additive knowledge schema5, schema6 and the indexed progressive protocol/UI. This follow-up adds evidence and one screenshot-only scroll instruction; runtime, shell, frontend application and native implementations are unchanged. VERSION0.1.0 remains: this is fixture-verified implementation, not device acceptance or deployment.

## Behavior and checks

| Criteria supported, not completed | Evidence |
| --- | --- |
| F1 recent-first pages, bounded resumable checkpoints, unique counts, explicit full/limited scope and category consent | 14 service tests in [gate](gate.log); [HTTP](http.log)3/3; [protocol](../../runtime/PROGRESSIVE.md) |
| F0/Q03 atomic migration, audit failure, restart, restore quarantine and current-policy denial | [Migration](migration.log)3/3 and gate, including scan recovery tests |
| F1/Q02 Source and Debug progress, exact denominator, unknown dates, owner resume request and Photos coverage | [Browser](browser.log)120/120 (prior104 retained), [actual runtime](runtime-visual.log)2/2 desktop/mobile; [screens](desktop-progress.png), [mobile](mobile-progress.png) |
| Q04 compatibility | [Aggregate](gate.log)292/0, [explicit contract](contract.log)67/0; all76 baseline names preserved through the existing approved sm_block wording mapping in [manifest](baseline-preservation.json) |
| Q04 frontend | Production [build](web-build.log), [types](types.log), [DS](ds.log) exit0; [units](unit.log)9/9 |

Commands: `/opt/homebrew/bin/python3 tests/run_all.py`, `tests/test_stub.py`; in web, `npm run build`, `npm run typecheck`, `npm run test`, `npm run check:ds`, `npm run test:e2e`, `npm run test:progressive-runtime`. Raw [mock results](browser-results.json) and [real results](runtime-results.json) retained. The code was committed before final gate and actual runtime tests; application files were unchanged during all final UI runs.

Actual Next8767→Python8766 test has no HTTP mocks. It pairs a synthetic limited device, records a recent page, requests resume through Debug, restarts the scan protocol through the same begin key, appends older/unknown metadata, finishes, checks current coverage and revokes the synthetic device. Runs use unique Sources rather than deleting prior fixtures. Six synthetic Sources from three desktop/mobile executions remain in the isolated fixture root; no personal data or actual iPhone was involved. Integrated-browser unavailability was previously established; approved Playwright fallback supplied repeatable real UI proof.

## Failures retained and corrected

Initial missing service [RED](red.log), missing progress [UI RED](ui-red.log), missing coverage [RED](coverage-red.log) and [green](coverage-green.log) are retained. The first aggregate [285/1](intermediate-gate.log) ran while the new coverage assertion was red; the final292/0 supersedes it. Recovery/index tests reproduce and prevent the underlying ordering and transactional regressions. No prior tests were skipped or weakened.

## Measured capacity

Synthetic benchmark script refuses existing roots, records no source payload, and transfers zero media. Final indexed implementation was already present during its precommit measurement; no index/query code changed before a298df3. Numbers reflect this host and fixture distribution, not an SLA.

| Metadata records | Scan seconds | Page p95 ms | Photos warm p95 ms | Peak RSS MiB | Retained bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10,000 before index | 2.266 | 32.606 | 11.974 | 151.56 | 13,795,328 |
| 100,000 before index | 110.579 | 317.544 | 923.632 | 149.73 | 134,443,008 |
| 100,000 indexed | 75.227 | 154.644 | 2.003 | 151.75 | 177,979,392 |

[10k](benchmark-10k.json), [100k initial](benchmark-100k.json), [100k indexed](benchmark-100k-indexed.json). Initial query plan sorted the entire authorized library; the indexed query now joins exact current revisions and evaluates live permission, without caching authorization. Peak RSS includes earlier scrypt provisioning (indexed baseline150.19MiB). Index storage increases retained bytes. Prototype roots are preserved and rejected by the stricter startup schema guard.

Native enumeration integration, actual permission/PhotoKit changes and iPhone recovery, real media/sample, private hosting, originals, complete knowledge UI and Artifacts remain required. No fixture result substitutes for those criteria. Original dirty checkout is untouched. Goal plan SHA256: ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820.
