---
title: "Integrated Private Media Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Integrated private media candidate

Implementation revision `516a0c15c8f6c05c25bebc340fcc02e1b704bea8`, based on main `d9976299684b4a018e1e656ff2855b665521d703`. Evidence relocation and this receipt do not change implementation. Full V1.0–V1.4 remains open; VERSION remains0.1.0.

Private schema4 storage adds immutable bounded chunks/components, verified completion, current-owner/current-revision policy checks before manifests and every streamed chunk, Range/HEAD, accurate readiness and media-aware backup/restore. The frontend decodes JPEG and H.264/AAC from private same-origin paths. Integrated unsigned native history through3c2c5ac supplies pairing and selected metadata/export; its optimized network uploader is a subsequent slice.

## Validation

- Combined core/native gate at9873d5b:266 passed,0 failed, before frontend-only commits8a5a0e4/516a0c1. [Gate](native-integrated-gate.log). Final delivery head gets its own rerun receipt.
- Integrated unsigned arm64 target build succeeds. [Build](native-build.log). No simulator, signing, installation, PhotoKit/Keychain execution or actual iPhone proof is claimed.
- At516a0c1, production web build, TypeScript and DS guard passed;9/9 unit and104/104 mocked browser cases passed. [Build](web-build.log), [types](typecheck.log), [units](unit.log), [DS](ds.log), [browser](browser.log).
- Post-commit actual Next8767→Python8766 test passed2/2 across desktop/mobile. [Runtime](integrated-runtime.log), [results](runtime-results.json). Python was restarted from integrated code before this run. It proves JPEG96×64 decode, video/Live time progression and positive decoded audio bytes, current-policy denial, HEAD/no-store/nosniff, Range206, partial/missing states and logout401 without HTTP mocks.
- Six generated fixture assets only; the synthetic uploading device was revoked before playback. This demonstrates retained server copies, not an actual iPhone airplane-mode test. The Hidden option is explicitly exercised and left off. No personal data was used.
- Integrator visually inspected [desktop Live](desktop-synthetic-live-playback.png) and [mobile photo](mobile-real-private-photo.png). The approved Playwright fallback was used after integrated-browser unavailability; screenshots alone do not establish access control.

## Reproduced defects and limits

Before correction, failed authenticated resource reads omitted denial audit, a partial file could poison retry, media backup omitted required files, and HEAD errors emitted a body. RED→GREEN tests cover the fixes; retained logs in this folder identify the applicable failures and passing reruns. All old implementation files and previous evidence are retained.

Native structural container validation is bounded, not a universal decoder.64MiB/component,1GiB retained budget and256 jobs are deliberate sample bounds, not whole-library capacity. Audio decoding is not a claim about audible speaker output. Real authorized Photos, whole-library recent/backfill, original requests, persistent knowledge/corrections, Artifacts and actual private hosting are still mandatory. No current milestone is accepted merely from fixtures.

The metadata UI agent's original proof moved intact to[its canonical folder](../v1.1-metadata-ui/EVIDENCE.md); viewer proof moved intact to[the viewer folder](../v1.3-viewer/EVIDENCE.md). Their historical revision/timing statements remain unchanged.

## Final focused delivery candidate

Tested candidate `5126e7168d5d0dd628d36d11d58bbf83eeba18a8` integrates the explicit native optimized uploader and a discovered readiness-replay correction. Exact candidate aggregate[268/0](final-gate.log) and explicit contract[67/0](final-contract.log) passed. All76 original baseline names are preserved except the already approved six-tools→sm_block vocabulary update; the exact original-name list is retained in baseline-preservation.json. No failed/skipped prior behavior is hidden by the count.

Runtime, shell, web application/components/lib/tests and lockfile are byte-identical between the post-commit playback candidate516a0c1 and this final candidate (`git diff --exit-code` returned0 for those paths), so the104 mocked,9 unit and2 actual playback proof above applies unchanged. The root's integrated uploader[target build](integrated-uploader-build.log) passed before the one-line readiness guard fix. Final native source/project/test paths match the native agent's4526aeb candidate exactly, whose unsigned target build also passed; see[its final regression receipt](../../../connectors/ios/READINESS-REPLAY-VERIFICATION.md).

Review caught `media_ready == 0` on metadata finish replay after successful media upload. A synthetic completed one-item run with Source-wide readiness123 reproduced invalidReceipt; the guard now accepts a nonnegative decoded integer and still rejects−1. Eleven Swift harnesses exercise51 groups. [Uploader receipt](../../../connectors/ios/MEDIA-TRANSFER-VERIFICATION.md). No real endpoint, Keychain or Photos invocation occurred in those tests. Deployment configuration remains an uncommitted prepared delta outside this focused delivery.
