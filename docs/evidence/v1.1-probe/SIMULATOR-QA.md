# Simulator UI QA prerequisite — 2026-10-02

Result: **not run; no Simulator runtime or device installed**.

The initial sandboxed `xcrun simctl list runtimes` / `list devices available`
attempt failed to connect to CoreSimulatorService and could not write its own
log outside the sandbox. That failure alone did not establish runtime absence.
The same read-only inspection was then executed with approved sandbox escalation.
It succeeded, exit 0, with this complete stdout:

```text
== Runtimes ==
== Devices ==
```

Exact commands:

```sh
xcrun simctl list runtimes
xcrun simctl list devices available
```

Xcode's installed iOS Simulator SDK is not an installed bootable Simulator
runtime. No runtime download, device creation, app installation, permission
request, Photos access, account login, signing change or simulator launch was
performed. No physical device was touched.

Therefore native UI permission, consent and empty states remain **unverified**.
The earlier successful unsigned device-target build and synthetic checks remain
compile/test evidence only. A later authorized session can use an already
installed simulator or a reviewed signed probe on an authorized physical device;
this receipt neither selects a new installation nor substitutes for real-device
acceptance.

Before this QA inspection was filed, the probe branch integrated the locally
fetched `origin/main` revision `a9c2fcaa9de7460507742b9f37669a4bf42a5e38`.
The native implementation subtree is unchanged:
`7bdf6b043f629e49ac7a5682996f95592210d9cc`.
No code change resulted from this inspection.
