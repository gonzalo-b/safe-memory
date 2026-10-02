-- Metadata ingestion. Immutable revisions and atomic checkpoint receipts.
CREATE TABLE ingest_runs (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES owners(id), connection_id TEXT NOT NULL REFERENCES connections(id),
 device_id TEXT NOT NULL REFERENCES devices(id), request_key TEXT NOT NULL, request_digest TEXT NOT NULL,
 phase TEXT NOT NULL, permission TEXT NOT NULL, policy_revision INTEGER NOT NULL, selected_json TEXT NOT NULL, coverage TEXT NOT NULL,
 state TEXT NOT NULL, next_sequence INTEGER NOT NULL DEFAULT 0, checkpoint TEXT,
 created_at INTEGER NOT NULL, completed_at INTEGER, UNIQUE(connection_id,request_key)
);
CREATE TABLE ingest_leases (connection_id TEXT PRIMARY KEY REFERENCES connections(id),run_id TEXT NOT NULL REFERENCES ingest_runs(id),expires_at INTEGER NOT NULL);
CREATE TABLE ingest_batches (
 run_id TEXT NOT NULL REFERENCES ingest_runs(id),batch_key TEXT NOT NULL,sequence INTEGER NOT NULL,
 payload_digest TEXT NOT NULL,receipt_json TEXT NOT NULL,created_at INTEGER NOT NULL,
 PRIMARY KEY(run_id,batch_key),UNIQUE(run_id,sequence)
);
CREATE TABLE assets (
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES owners(id),connection_id TEXT NOT NULL REFERENCES connections(id),
 native_id TEXT NOT NULL,current_revision INTEGER,last_observation INTEGER NOT NULL DEFAULT 0,restriction_uncertain INTEGER NOT NULL DEFAULT 0,hidden INTEGER NOT NULL,collection TEXT NOT NULL,
 scope_authorized INTEGER NOT NULL,first_seen INTEGER NOT NULL,last_seen INTEGER NOT NULL,
 UNIQUE(connection_id,native_id),
 FOREIGN KEY(id,current_revision) REFERENCES asset_revisions(asset_id,revision) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE asset_revisions (
 asset_id TEXT NOT NULL REFERENCES assets(id),revision INTEGER NOT NULL,source_revision TEXT NOT NULL,payload_digest TEXT NOT NULL,
 raw_json TEXT NOT NULL,media_type TEXT NOT NULL,capture_time TEXT,time_basis TEXT NOT NULL,capture_day TEXT,capture_instant REAL,
 source_modified REAL,owner_presence TEXT NOT NULL,created_at INTEGER NOT NULL,
 PRIMARY KEY(asset_id,revision),UNIQUE(asset_id,source_revision)
);
-- Restriction observations retain ordering even when raw content was excluded.
CREATE TABLE asset_observations (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,asset_id TEXT NOT NULL REFERENCES assets(id),
 source_revision TEXT NOT NULL,payload_digest TEXT NOT NULL,source_modified REAL,
 UNIQUE(asset_id,source_revision)
);
CREATE INDEX assets_owner_connection ON assets(owner_id,connection_id);
CREATE INDEX asset_revision_date ON asset_revisions(capture_day,asset_id);
CREATE TRIGGER asset_observations_no_update BEFORE UPDATE ON asset_observations BEGIN SELECT RAISE(ABORT,'immutable_observation'); END;
CREATE TRIGGER asset_observations_no_delete BEFORE DELETE ON asset_observations BEGIN SELECT RAISE(ABORT,'retained_observation'); END;
CREATE TRIGGER asset_revisions_no_update BEFORE UPDATE ON asset_revisions BEGIN SELECT RAISE(ABORT,'immutable_revision'); END;
CREATE TRIGGER asset_revisions_no_delete BEFORE DELETE ON asset_revisions BEGIN SELECT RAISE(ABORT,'retained_revision'); END;
