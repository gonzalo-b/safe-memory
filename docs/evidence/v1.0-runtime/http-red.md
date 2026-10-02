---
title: "Runtime http-red"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Synthetic fixture evidence only. Candidate backend `fef61393a4a957fbcf04ffdc5743a92eb90dd04c`; RED logs are explicitly pre-fix. Exact commands and revision scope in EVIDENCE.md.

```text
EEE
======================================================================
ERROR: test_edge_clients_have_independent_login_limits (tests.test_runtime_http.HTTPTests.test_edge_clients_have_independent_login_limits)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/memory-v1-runtime/tests/test_runtime_http.py", line 107, in test_edge_clients_have_independent_login_limits
    app=MemoryApp(self.store,origin='https://memory.example.test',trusted_edge='cloudflare')
TypeError: MemoryApp.__init__() got an unexpected keyword argument 'trusted_edge'

======================================================================
ERROR: test_edge_identity_requires_explicit_trust_and_loopback_peer (tests.test_runtime_http.HTTPTests.test_edge_identity_requires_explicit_trust_and_loopback_peer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/memory-v1-runtime/tests/test_runtime_http.py", line 114, in test_edge_identity_requires_explicit_trust_and_loopback_peer
    app=MemoryApp(self.store,origin='https://memory.example.test',trusted_edge='cloudflare')
TypeError: MemoryApp.__init__() got an unexpected keyword argument 'trusted_edge'

======================================================================
ERROR: test_total_body_deadline_bounds_stall_and_drip_without_auth (tests.test_runtime_http.HTTPTests.test_total_body_deadline_bounds_stall_and_drip_without_auth)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py", line 488, in wait_for
    return await fut
           ^^^^^^^^^
  File "/private/tmp/memory-v1-runtime/shell/app.py", line 48, in __call__
    part=await receive()
         ^^^^^^^^^^^^^^^
  File "/private/tmp/memory-v1-runtime/tests/test_runtime_http.py", line 130, in receive
    await asyncio.sleep(0.01 if drip else 2)
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py", line 704, in sleep
    return await future
           ^^^^^^^^^^^^
asyncio.exceptions.CancelledError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/private/tmp/memory-v1-runtime/tests/test_runtime_http.py", line 138, in test_total_body_deadline_bounds_stall_and_drip_without_auth
    for drip in (False,True):asyncio.run(scenario(drip))
                             ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/runners.py", line 205, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/runners.py", line 128, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/base_events.py", line 719, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "/private/tmp/memory-v1-runtime/tests/test_runtime_http.py", line 135, in scenario
    await asyncio.wait_for(app(scope,receive,send),0.2)
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py", line 487, in wait_for
    async with timeouts.timeout(timeout):
               ~~~~~~~~~~~~~~~~^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/timeouts.py", line 115, in __aexit__
    raise TimeoutError from exc_val
TimeoutError

----------------------------------------------------------------------
Ran 3 tests in 1.719s

FAILED (errors=3)

```
