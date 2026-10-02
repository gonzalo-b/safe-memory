---
title: "Native pairing verification"
project: memory
type: evidence
status: preparation
created: 2026-10-02
source: codex-desktop
---

# Explicit native pairing: local verification

Tested candidate: `3500d5b4ea70a7840190a956adf3764d306d7b0e`, based on
exporter candidate `0fe86cc3e6ed94ac5c528a6edeb22b7c42613e5c`. An evidence-only
commit follows; implementation identity is recorded below. No push, merge,
deployment, signing, real credential creation or endpoint operation occurred.

Authorization is the supplied V1.0–V1.4 goal plus the approved
`~/base/projects/memory/docs/Alpha V1 Technical Delta.md`, including iOS-only
outbound Memory requests, HTTPS `memory.lazyagent.ai`, owner-confirmed pairing
and scoped Keychain credentials. An initial automatic review rejected the code
patch for missing specific authorization context. Reading that approval and
the original goal established the existing authorization; the same patch tool
then accepted the code-only change. No alternate execution or network path was
used to bypass review. Real deployment and device consent remain separate.

## Verified behavior

- Request construction enforces the fixed HTTPS origin and two POST paths.
  Claim credentials appear only in the bounded JSON body; status credentials
  appear only in Authorization. Cookies, URL credentials, query/fragment,
  alternate ports/origins, extra headers and extra JSON fields are refused.
- URLSession runs through a catch-all URLProtocol fixture, never the network.
  Tests verify isolated sessions, no Set-Cookie reuse, redirect refusal without
  a second request carrying the bearer, 401 refusal, declared/streamed 8193-byte
  rejection, 8192-byte acceptance and cancellation of a pending response.
- A known independent Python SHA-256 vector verifies hashing of the canonical
  43-character credential UTF-8, rather than the decoded random bytes. Strict
  response checks reject mismatching fingerprints, cross-device status and
  anything except Boolean `data_access: false`.
- A synthetic persistence/service fixture verifies that identity is saved
  before the first claim, survives a failed receipt save without rotation,
  needs explicit status after owner confirmation, clears a prior binding on
  denial and refuses an unrecognized installation without another request.
- Opening/loading the coordinator does not claim, check status or create a key.
  UI actions are explicit Connect and Check status. Full fingerprints are shown;
  no automatic preview, confirmation, retry loop or Photos transmission exists.
- Existing exporter/manifest checks and source-mutation guards still pass.
  Network APIs are allowed only in the reviewed pairing request/transport files;
  Photos reader/export types remain forbidden there. Other native sources keep
  their no-network guard. A guard first rejected general `setValue` usage in
  request construction; headers were changed to a dictionary assignment while
  preserving the existing conservative private-API guard.

## Commands and receipts

At the tested candidate:

- `/opt/homebrew/bin/python3 tests/run_all.py`: **165 passed, 0 failed**, exit 0.
  This includes the unchanged contract gate's **67 passed, 0 failed**.
  Log: `/private/tmp/memory-pairing-candidate-gate.log`.
- Native runner: **11 passed, 0 failed**, including six Swift executables with
  27 named check groups, compiled with Swift 6 and warnings-as-errors. Tests
  use synthetic values, Foundation/CryptoKit and URLProtocol only; Keychain and
  Photos are never invoked. Latest standalone log:
  `/private/tmp/memory-pairing-contract-final.log`.
- README unsigned direct-target build with installed iOS26.5 SDK: **BUILD
  SUCCEEDED**, exit 0. Exact-candidate log:
  `/private/tmp/memory-probe-pairing-candidate-build.log`. Earlier compile log
  `/private/tmp/memory-probe-pairing-build.log` shows actual source compilation.
  Deprecated Keychain UI handling was replaced by a noninteractive LAContext.
  No Swift warnings remain. The full build's only tool warning is skipped
  App Intents metadata extraction because that framework is not used.
- `file` identifies the output as an arm64 Mach-O. `codesign -dv` returns the
  expected exit 1 and reports that the app is not signed. `git diff --check`
  passes. RED preparation/guard logs remain at
  `/private/tmp/memory-pairing-red.log` and
  `/private/tmp/memory-pairing-contract-red.log`.

These temporary logs can expire with host cleanup. Git identities of tested
implementation/test objects allow verification across the evidence-only commit:

| Path | Git object |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `a987c860afff522706e55962cf4ef91dd24c5481` |
| `connectors/ios/tests` | `816429a8ad94a76984ca0e73aeccac22ebc63fa6` |
| `tests/test_ios_probe.py` | `29c91b4cf7d504155f2843e29c563bdab25ad721` |

## Not verified and integration handoff

The app has not run on a simulator or physical device. No usable iOS Simulator
runtime is installed on this host. Keychain persistence/accessibility/reinstall,
native UI layout and lifecycle, TLS/Cloudflare reachability, owner web-to-device
pairing and actual revocation are not device acceptance claims. No Apple
credentials, personal library, Photos sample or source payload was accessed.
The local library alias is not an Apple-verified library identity. Reinstallation,
changed/unrecognized library and lost receipt after confirmation/expiry require
an explicit future recovery/relink flow; silent identity replacement is refused.

The attempted merge of `origin/main` at
`e93f5864544d615300af03d111b0fb5d2aa94a1b` conflicted in shared `PROGRESS.md`.
It was aborted because the subtask owns only native files and its test wrapper.
Root must preserve both checkpoint histories, integrate current main and rerun
the integrated gates/build before PR delivery. PR7 remains a draft; this
preparation does not establish F1 device acceptance or change product VERSION.
