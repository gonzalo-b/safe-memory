---
title: "Runtime http-green"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Synthetic fixture evidence only. Candidate backend `fef61393a4a957fbcf04ffdc5743a92eb90dd04c`; RED logs are explicitly pre-fix. Exact commands and revision scope in EVIDENCE.md.

```text
test_audit_failure_has_no_sensitive_details (__main__.HTTPTests.test_audit_failure_has_no_sensitive_details) ... ok
test_authenticated_read_and_logout_csrf (__main__.HTTPTests.test_authenticated_read_and_logout_csrf) ... ok
test_edge_clients_have_independent_login_limits (__main__.HTTPTests.test_edge_clients_have_independent_login_limits) ... ok
test_edge_identity_requires_explicit_trust_and_loopback_peer (__main__.HTTPTests.test_edge_identity_requires_explicit_trust_and_loopback_peer) ... ok
test_input_size_and_extra_identity_fields_rejected (__main__.HTTPTests.test_input_size_and_extra_identity_fields_rejected) ... ok
test_login_cookie_and_no_store_headers (__main__.HTTPTests.test_login_cookie_and_no_store_headers) ... ok
test_no_session_denied_and_public_health_has_no_owner_information (__main__.HTTPTests.test_no_session_denied_and_public_health_has_no_owner_information) ... ok
test_origin_and_host_duplicate_rejected (__main__.HTTPTests.test_origin_and_host_duplicate_rejected) ... ok
test_public_deployment_requires_https_and_secure_cookie (__main__.HTTPTests.test_public_deployment_requires_https_and_secure_cookie) ... ok
test_spoofed_owner_header_cannot_select_other_owner (__main__.HTTPTests.test_spoofed_owner_header_cannot_select_other_owner) ... ok
test_total_body_deadline_bounds_stall_and_drip_without_auth (__main__.HTTPTests.test_total_body_deadline_bounds_stall_and_drip_without_auth) ... ok
test_unknown_and_future_routes_require_auth (__main__.HTTPTests.test_unknown_and_future_routes_require_auth) ... ok

----------------------------------------------------------------------
Ran 12 tests in 12.483s

OK
12 passed, 0 failed

```
