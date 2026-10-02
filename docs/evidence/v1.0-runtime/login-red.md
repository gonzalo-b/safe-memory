---
title: "Runtime login-red"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Synthetic fixture evidence only. Candidate backend `fef61393a4a957fbcf04ffdc5743a92eb90dd04c`; RED logs are explicitly pre-fix. Exact commands and revision scope in EVIDENCE.md.

```text
E
======================================================================
ERROR: test_successful_sign_in_does_not_exhaust_failed_login_limit (tests.test_runtime.RuntimeTests.test_successful_sign_in_does_not_exhaust_failed_login_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/memory-v1-runtime/tests/test_runtime.py", line 72, in test_successful_sign_in_does_not_exhaust_failed_login_limit
    auth=self.login()
  File "/private/tmp/memory-v1-runtime/tests/test_runtime.py", line 27, in login
    return self.store.login('alice', PASSWORD, 'loopback')
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/memory-v1-runtime/runtime/store.py", line 175, in login
    if error: raise error
              ^^^^^^^^^^^
runtime.store.RuntimeErrorResult: Too many attempts. Try again later.

----------------------------------------------------------------------
Ran 1 test in 2.098s

FAILED (errors=1)

```
