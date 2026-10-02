---
title: "Reusable Memory Shell"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Reusable Memory shell

Presentation-only component for the approved V1 navigation, local design assets and theme controls. This is not an authenticated application or deployment. `mountShell(root, renderContent)` provides a content element and route to the caller; the future runtime must authorize/audit data before rendering and destroy the shell on logout. The shell has no data fetch, login simulation, source connection, permissions, saved media or account persistence. Theme is the only localStorage entry.

Load `theme-bootstrap.js` before `memory-ds/memory.css`, then `shell.css` and the `shell.js` module. Canonical desktop sidebar and four-item mobile navigation are adapted from v1-views.html. Future Agents, Plugins, public sharing and World Map controls are not exposed as working features. Unknown routes render a safe local page. Content rendering uses DOM nodes and textContent; untrusted strings are not interpolated as HTML.

DS CSS and icon sprite come from the approved Memory Design System. CSS is unchanged except replacing its Google font import with a local Inter @font-face. Inter WOFF2 is extracted from the supplied canonical v1-views.html. No remote font requests. No monospaced surface is rendered yet; JetBrains Mono is not bundled and must be resolved before those surfaces ship. The source DS is never edited.

QA fixture: `/e2e/fixtures/shell.html`, explicitly synthetic. With the existing e2e dependencies installed, run `cd e2e && npm test`; all smoke and shell tests run. `playwright test -c shell.config.js` narrows to the shell. No npm install or dependency change was needed on this host; its existing Playwright 1.60.0 was reused read-only through NODE_PATH.

Run `node scripts/check-ds.mjs ui/shell.js ui/shell.css ui/theme-bootstrap.js`. Vendored tokens intentionally contain the original color values and are outside product-style scanning. Python aggregate gate includes local-asset checks. See docs/evidence/v1.0-ui/EVIDENCE.md for current coverage and limitations; component tests do not satisfy full F0 or Q-02 app acceptance.
