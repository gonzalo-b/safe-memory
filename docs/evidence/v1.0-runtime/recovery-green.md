---
title: "Runtime recovery-green"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Synthetic fixture evidence only. Candidate backend `fef61393a4a957fbcf04ffdc5743a92eb90dd04c`; RED logs are explicitly pre-fix. Exact commands and revision scope in EVIDENCE.md.

```text
test_audit_failure_refuses_read (__main__.RuntimeTests.test_audit_failure_refuses_read) ... ok
test_audit_is_append_only_and_content_free (__main__.RuntimeTests.test_audit_is_append_only_and_content_free) ... ok
test_backup_and_restore_reject_repo_and_symlink_destinations_before_writing (__main__.RuntimeTests.test_backup_and_restore_reject_repo_and_symlink_destinations_before_writing) ... ok
test_backup_requires_audit_before_any_copy (__main__.RuntimeTests.test_backup_requires_audit_before_any_copy) ... ok
test_backup_restore_preserves_facts_but_revokes_old_access (__main__.RuntimeTests.test_backup_restore_preserves_facts_but_revokes_old_access) ... ok
test_corrupt_backup_refused_without_touching_live_store (__main__.RuntimeTests.test_corrupt_backup_refused_without_touching_live_store) ... ok
test_csrf_failure_keeps_session_and_denies_mutation (__main__.RuntimeTests.test_csrf_failure_keeps_session_and_denies_mutation) ... ok
test_failed_restore_is_quarantined_before_old_sessions_can_be_used (__main__.RuntimeTests.test_failed_restore_is_quarantined_before_old_sessions_can_be_used) ... ok
test_files_private_and_symlink_database_refused (__main__.RuntimeTests.test_files_private_and_symlink_database_refused) ... ok
test_fixture_mode_is_persisted_and_cannot_be_silently_changed (__main__.RuntimeTests.test_fixture_mode_is_persisted_and_cannot_be_silently_changed) ... ok
test_login_persists_only_verifier_and_hashed_session (__main__.RuntimeTests.test_login_persists_only_verifier_and_hashed_session) ... ok
test_login_throttle_survives_restart_and_errors_are_generic (__main__.RuntimeTests.test_login_throttle_survives_restart_and_errors_are_generic) ... ok
test_logout_revokes_and_token_spoof_denied (__main__.RuntimeTests.test_logout_revokes_and_token_spoof_denied) ... ok
test_session_survives_restart_and_expires (__main__.RuntimeTests.test_session_survives_restart_and_expires) ... ok
test_vault_and_source_replay_are_unique_and_owner_scoped (__main__.RuntimeTests.test_vault_and_source_replay_are_unique_and_owner_scoped) ... ok

----------------------------------------------------------------------
Ran 15 tests in 15.404s

OK
15 passed, 0 failed

```
