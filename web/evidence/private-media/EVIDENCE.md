---
title: "Private Media Viewer Evidence"
project: memory
type: doc
status: review
created: 2026-10-02
source: codex-desktop
---

# Private photo, video and Live component viewer

Tested frontend revision: `8234844e4e2f8d50e7f93c61d08000aae689d070`. The evidence commit changes no implementation. This agent-owned `web/` folder can be relocated by the integrator into canonical release evidence.

## Scope and behavior

Open media checks the current owner-authenticated manifest and constructs only exact same-origin `/api/media/{32hex}` component paths. Manifest asset identity, component IDs, roles, MIME types, sizes and availability are validated. Reads use the existing session cookie; there is no new authentication, storage, public media path, image optimizer, remote URL or original-request UI.

The native modal uses Memory DS surfaces and native focus containment/background inertness. Close and Escape return focus to the opener. Still images decode in an image element. Video and Live motion use native controls, no autoplay, no automatic muting and unchanged source audio bytes. A Live still becomes the motion player's poster. Still-only Live explicitly says motion and sound are unavailable; missing media remains empty.

Refresh clears the prior frame before reloading. A stream/decode error clears it immediately, then probes the exact component via authenticated HEAD to distinguish authorization loss from a browser decode problem. A 401 clears the owner session. Closing, navigation and filter changes unmount the viewer and stop playback. A current-policy denial cannot keep the prior frame after refresh. Previously displayed bytes cannot be remotely erased; no claim is made beyond refresh/new-request enforcement and the backend's ongoing-read policy checks.

## Criteria evidence and limits

This contributes partial synthetic proof for F3-01, F3-02 and F3-04: private photo decoding, native video with audio decoding, and Live still/motion/partial behavior. The fixture consists only of a generated purple 96×64 JPEG and one-second H.264/AAC tone video, created by the integrator with FFmpeg. Test copies and hashes are retained under `web/tests/fixtures/`; `synthetic-media-probe.json` reports the actual codecs. No personal Photos data or real iPhone was used.

Playback progress plus decoded audio-byte count proves browser decoding; it does not prove audible speaker output, every codec/device, actual iOS behavior, progressive library import, whole-library coverage or original-copy transfer. A single generated clip does not substitute for real-device acceptance. The parent integrator owns the final combined backend/frontend revision and gate.

## Post-commit validation

All final commands below ran after frontend revision 8234844 was committed:

- Production build, TypeScript check and DS guard passed.
- `npm test`: 9/9, preserving the prior 7 names and adding exact manifest path and private HEAD checks.
- `MEMORY_TEST_PORT=8769 npx playwright test`: 104/104 against the production build. All 80 prior browser names are retained. Twenty-four new runs cover JPEG decoding, modal focus/Escape, 320px overflow, motion playback/audio, partial/missing media, refresh denial, 401 removal and untrusted component IDs across desktop/mobile in both themes.
- `/opt/homebrew/bin/python3 tests/run_all.py`: 231 passed, 0 failed in this web checkout's metadata backend base. This is separate from the integrator's additional media backend tests.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: 67 passed, 0 failed.
- `npm run test:media-runtime`: 2/2, no HTTP route mocks, actual Next 8767 → Python 8766.

`api-red.log` preserves the new manifest-path unit failure before support. `ui-red.log` preserves the browser failure before Open media existed. The first implementation exposed an overly broad static-path alternative that allowed a short asset segment; the unit test caught it and the final helper requires the exact manifest endpoint. No prior tests were skipped or renamed. `preserved-test-names.json` and full result JSON retain the names.

## Actual-runtime details

The owner-supplied synthetic fixture `/private/tmp/memory-live-fixture-media` ran through the parent-owned `/private/tmp/memory-v1-media` Python working tree (parent's backend commit was still being prepared). The fixture had one Source and six assets: ready photo, ready H.264/AAC video, complete Live, still-only Live, missing photo media, and ready Hidden photo. Its uploading device had already been revoked; playback therefore did not require a connected device. This is synthetic retained-media proof, not an airplane-mode test on an actual phone.

The actual-runtime suite verified JPEG natural dimensions 96×64, video and Live motion progress, positive decoded audio bytes, no autoplay/mute, Live poster, honest partial/missing states, HEAD 200/no-store/nosniff and Range 206. While the Hidden photo was open it explicitly disabled Hidden using the owner's session/CSRF, then refreshed the viewer: its previous frame disappeared, the manifest was unavailable and byte GET returned 404. Refreshing metadata removed its card. Logout then made an otherwise visible component return 401.

The suite reauthorizes Hidden only for its repeatable synthetic setup and leaves it disabled at completion. No Source, device or asset was created, reset or deleted. Final fixture state retains all six assets, with Hidden excluded. Next QA was stopped after verification; ports 8767 and 8769 were released.

## Visual review

Reviewed both themes, desktop and mobile, with photo dialogs at 320px. The final screenshots disable entry animation only during capture, avoiding a misleading half-faded frame. Product reduced-motion behavior and DS animation remain intact. Native video controls, close action, media bounds and error layout stay inside the viewport. The integrated browser remained unavailable for this environment; the approved Playwright fallback supplied the production-build proof.
