---
title: "Variable-Red Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

```text
test_css_references_only_local_assets (__main__.AssetTests) ... ok
test_local_font_is_valid_nonempty_woff2 (__main__.AssetTests) ... ok
test_product_css_variables_exist_in_design_system (__main__.AssetTests) ... FAIL

======================================================================
FAIL: test_product_css_variables_exist_in_design_system (__main__.AssetTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/memory-v1-ui/tests/test_ui_assets.py", line 22, in test_product_css_variables_exist_in_design_system
    self.assertEqual(used - declared, set())
AssertionError: Items in the first set but not the second:
'--m-leading-screen'

----------------------------------------------------------------------
Ran 3 tests in 0.002s

FAILED (failures=1)
2 passed, 1 failed

```
