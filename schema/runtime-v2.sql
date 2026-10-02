-- Additive pairing migration, applied only after an isolated audited v1 backup.
CREATE TABLE pairing_intents (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id),
 secret_hash TEXT NOT NULL UNIQUE, auth_epoch INTEGER NOT NULL,
 created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 claim_id TEXT UNIQUE, device_name TEXT, library_id TEXT,
 credential_hash TEXT UNIQUE, claimed_at INTEGER, confirmed_at INTEGER,
 device_id TEXT REFERENCES devices(id), revoked_at INTEGER,
 CHECK ((claim_id IS NULL AND credential_hash IS NULL AND device_name IS NULL AND library_id IS NULL)
     OR (claim_id IS NOT NULL AND credential_hash IS NOT NULL AND device_name IS NOT NULL AND library_id IS NOT NULL))
);
CREATE TABLE devices (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id),
 connection_id TEXT NOT NULL REFERENCES connections(id),
 credential_hash TEXT NOT NULL UNIQUE, device_name TEXT NOT NULL,
 auth_epoch INTEGER NOT NULL, created_at INTEGER NOT NULL, revoked_at INTEGER
);
CREATE INDEX pairing_owner_pending ON pairing_intents(owner_id,expires_at);
CREATE INDEX devices_owner ON devices(owner_id);
