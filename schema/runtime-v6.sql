-- Frozen progressive scan bounds and exact identities; existing revisions remain immutable.
CREATE TABLE scan_runs (
 run_id TEXT PRIMARY KEY REFERENCES ingest_runs(id),expected_count INTEGER NOT NULL CHECK(expected_count BETWEEN 0 AND 1000000),
 recent_after TEXT NOT NULL,last_instant REAL,unknown_started INTEGER NOT NULL DEFAULT 0,phase TEXT NOT NULL DEFAULT 'recent',
 observed INTEGER NOT NULL DEFAULT 0,accepted INTEGER NOT NULL DEFAULT 0,excluded INTEGER NOT NULL DEFAULT 0,
 first_capture TEXT,last_capture TEXT,missing_date INTEGER NOT NULL DEFAULT 0,retry_requested INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE scan_assets (
 run_id TEXT NOT NULL REFERENCES scan_runs(run_id),native_id TEXT NOT NULL,asset_id TEXT NOT NULL REFERENCES assets(id),
 PRIMARY KEY(run_id,native_id)
);
CREATE INDEX scan_assets_identity ON scan_assets(run_id,asset_id);
CREATE TRIGGER scan_assets_immutable BEFORE UPDATE ON scan_assets BEGIN SELECT RAISE(ABORT,'immutable_scan_identity'); END;
CREATE TRIGGER scan_assets_retained BEFORE DELETE ON scan_assets BEGIN SELECT RAISE(ABORT,'retained_scan_identity'); END;
-- Current metadata ordering index, never an authorization cache. Current policy is joined at read.
CREATE TABLE current_asset_index (
 asset_id TEXT PRIMARY KEY REFERENCES assets(id),owner_id TEXT NOT NULL REFERENCES owners(id),revision INTEGER,
 capture_instant REAL,capture_day TEXT,media_type TEXT
);
INSERT INTO current_asset_index
 SELECT a.id,a.owner_id,a.current_revision,r.capture_instant,r.capture_day,r.media_type FROM assets a
 LEFT JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision;
CREATE INDEX current_asset_owner_time ON current_asset_index(owner_id,capture_instant DESC,asset_id);
CREATE INDEX current_asset_owner_type_time ON current_asset_index(owner_id,media_type,capture_instant DESC,asset_id);
CREATE INDEX current_asset_owner_day_time ON current_asset_index(owner_id,capture_day,capture_instant DESC,asset_id);
CREATE TRIGGER asset_index_insert AFTER INSERT ON assets BEGIN
 INSERT INTO current_asset_index(asset_id,owner_id,revision) VALUES(NEW.id,NEW.owner_id,NEW.current_revision);
END;
CREATE TRIGGER asset_index_revision AFTER UPDATE OF current_revision ON assets BEGIN
 UPDATE current_asset_index SET revision=NEW.current_revision,
 capture_instant=(SELECT capture_instant FROM asset_revisions WHERE asset_id=NEW.id AND revision=NEW.current_revision),
 capture_day=(SELECT capture_day FROM asset_revisions WHERE asset_id=NEW.id AND revision=NEW.current_revision),
 media_type=(SELECT media_type FROM asset_revisions WHERE asset_id=NEW.id AND revision=NEW.current_revision)
 WHERE asset_id=NEW.id;
END;
