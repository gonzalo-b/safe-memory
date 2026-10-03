---
title: "Synthetic Playback Audio Host Diagnosis"
project: memory
type: doc
status: done
created: 2026-10-02
source: codex-desktop
---

# Synthetic playback freeze diagnosis

Read-only diagnosis of candidate 85606c5 final media test failures. No app checkout, running process or fixture modification, no login or personal media. Scratch files contain only the synthetic MP4 already returned in the failed trace.

The failed desktop and mobile tests both stopped at `video.currentTime=0.02322` after fulfilled `play()`. The failed desktop trace contains a completed HTTP 206 video response: `bytes 0-11751/11752`, all 11752 bytes received after about 7.6ms wait, about 0.4ms body delivery. The extracted response bytes exactly equal two retained synthetic component complete files.

MP4 SHA256: `403c135fe5a0a1bd00970efbdf0872644dea525ef3370475b1f4f9084c2cca62`. FFprobe: 96x64 H.264,10fps,1s; AAC mono44100Hz,1s. FFmpeg decodes10video frames and88KiB PCM without errors (decode.log).

Isolated discriminator: Chromium148.0.7778.96 launched through the existing pinned Playwright, about:blank with a dataURL of these exact bytes. No React, HTTP, auth, policy or app code. For each variant, inspect currentTime, readyState, buffered ranges, decode byte counters and errors after700ms/1400ms/2100ms.

| Variant | Current time | Audio decoded | Other evidence |
| --- | --- | --- | --- |
| Default launch, element unmuted | 0.02322 at all samples | 2539 at all samples | readyState4,buffered0–1,no error,play resolved,pausedfalse |
| Element muted (diagnostic only) | ~0.67→1 | 8501→8992 | endedtrue |
| `--disable-audio-output`, element unmuted | ~0.665→1 | 8722→8992 | endedtrue,mutedfalse |
| `--disable-features=AudioServiceOutOfProcess`, element unmuted | 0.02322 at all samples | 2539 at all samples | same freeze |

`repeat.cjs` repeated default vs disabled output three times each: all3 defaults froze identically; all3 disabled-output reached1sec with audioDecoded8992 and mutedfalse. Raw sanitized snapshots/CDP media logs: probe.jsonl and repeat.jsonl. Scripts: probe.cjs and repeat.cjs.

Inference strongly supported: host Chromium audio output sink/clock stall, independent of the application transport or encoded bytes. Exact CoreAudio/root device cause was not inspected and no settings were changed.

Recommended bounded test adaptation: use `launchOptions: {args:['--disable-audio-output']}` in the media runtime test configuration. Keep all existing currentTime/audioDecoded, default unmuted/no autoplay/controls, HTTP Range/auth/revocation assertions. Do not change product media element to muted, suppress errors, or lower clock threshold. This proves playable media and AAC decoding with deterministic output sink; it does not prove acoustic output from host speakers or iPhone acceptance. Integrator must rerun the unmodified actual app test with this launch option before claiming it passes.
