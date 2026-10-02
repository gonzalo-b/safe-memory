---
title: "Direct Target Build Recovery"
project: memory
type: doc
status: done
created: 2026-10-02
source: codex-desktop
---

# Direct target build recovery

Tested revision: `956ce8e43fe126c0db02aa26e17f0459e6ff2a12`.
Current source compiles successfully, exit 0. Earlier scheme/destination failure remains in INTEGRATED.md; this command avoids that discovery step by naming the target, SDK and architecture. It does not install platforms, change settings, sign, launch the app or verify an iPhone.

```sh
xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj \
  -target SafeMemoryProbe -sdk iphoneos26.5 -arch arm64 -configuration Debug \
  CODE_SIGNING_ALLOWED=NO \
  OBJROOT=/private/tmp/memory-probe-target-qa/obj \
  SYMROOT=/private/tmp/memory-probe-target-qa/products \
  SHARED_PRECOMPS_DIR=/private/tmp/memory-probe-target-qa/precompiled \
  CLANG_MODULE_CACHE_PATH=/private/tmp/memory-probe-target-qa/modules build
```

A fresh output directory compiled all three Swift sources and linked arm64 for iOS 18. The binary remains unsigned. Simulator, UI, Photos permission, signing, transfer and physical-device acceptance are still pending. PR stays draft.

Build log SHA-256: `bce8c90b0d711b6bc0fbac1a3904749b4277deb4a449db9e8075984f2bfb94ff`.
Complete sanitized local build log: [target-build.log](target-build.log).
