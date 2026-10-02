-- Additive runtime schema. Does not change legacy Record or Grant JSON shapes.
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE owners (
 id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
 verifier TEXT NOT NULL, auth_epoch INTEGER NOT NULL DEFAULT 1, created_at INTEGER NOT NULL
);
CREATE TABLE sessions (
 token_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id),
 csrf_hash TEXT NOT NULL, auth_epoch INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 revoked_at INTEGER, created_at INTEGER NOT NULL
);
CREATE INDEX sessions_owner ON sessions(owner_id);
CREATE TABLE login_limits (key TEXT PRIMARY KEY, window_start INTEGER NOT NULL, attempts INTEGER NOT NULL);
CREATE TABLE vaults (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id), domain TEXT NOT NULL CHECK(domain='Photos'),
 created_at INTEGER NOT NULL, UNIQUE(owner_id,domain)
);
CREATE TABLE connections (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id), vault_id TEXT NOT NULL REFERENCES vaults(id),
 source_key TEXT NOT NULL, name TEXT NOT NULL, permission TEXT NOT NULL DEFAULT 'restricted',
 status TEXT NOT NULL DEFAULT 'awaiting_device', last_success TEXT,
 include_hidden INTEGER NOT NULL DEFAULT 0, include_shared_library INTEGER NOT NULL DEFAULT 0,
 include_shared_albums INTEGER NOT NULL DEFAULT 0, policy_revision INTEGER NOT NULL DEFAULT 1,
 index_count INTEGER NOT NULL DEFAULT 0, media_ready_count INTEGER NOT NULL DEFAULT 0,
 created_at INTEGER NOT NULL, UNIQUE(owner_id,source_key)
);
CREATE TABLE operations (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id), action TEXT NOT NULL,
 status TEXT NOT NULL, created_at INTEGER NOT NULL, completed_at INTEGER
);
CREATE TABLE audit (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
 owner_id TEXT, action TEXT NOT NULL, outcome TEXT NOT NULL, count INTEGER NOT NULL,
 created_at INTEGER NOT NULL
);
CREATE INDEX audit_owner ON audit(owner_id,sequence);
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append_only'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append_only'); END;
