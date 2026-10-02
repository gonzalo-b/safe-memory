-- Private immutable chunks/components; uploads publish only after full verification.
CREATE TABLE media_uploads (
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES owners(id),device_id TEXT NOT NULL REFERENCES devices(id),
 asset_id TEXT NOT NULL REFERENCES assets(id),revision INTEGER NOT NULL,role TEXT NOT NULL,mime TEXT NOT NULL,
 size INTEGER NOT NULL,sha256 TEXT NOT NULL,request_key TEXT NOT NULL,request_digest TEXT NOT NULL,
 next_offset INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL DEFAULT 'active',component_id TEXT,created_at INTEGER NOT NULL,
 UNIQUE(device_id,request_key),FOREIGN KEY(asset_id,revision) REFERENCES asset_revisions(asset_id,revision)
);
CREATE TABLE media_chunks (
 upload_id TEXT NOT NULL REFERENCES media_uploads(id),offset INTEGER NOT NULL,size INTEGER NOT NULL,
 sha256 TEXT NOT NULL,storage_key TEXT NOT NULL UNIQUE,PRIMARY KEY(upload_id,offset)
);
CREATE TABLE media_components (
 id TEXT PRIMARY KEY,asset_id TEXT NOT NULL REFERENCES assets(id),revision INTEGER NOT NULL,
 role TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,storage_key TEXT NOT NULL UNIQUE,
 created_at INTEGER NOT NULL,UNIQUE(asset_id,revision,role),FOREIGN KEY(asset_id,revision) REFERENCES asset_revisions(asset_id,revision)
);
CREATE TRIGGER media_chunks_immutable BEFORE UPDATE ON media_chunks BEGIN SELECT RAISE(ABORT,'immutable_chunk'); END;
CREATE TRIGGER media_chunks_retained BEFORE DELETE ON media_chunks BEGIN SELECT RAISE(ABORT,'retained_chunk'); END;
CREATE TRIGGER media_components_immutable BEFORE UPDATE ON media_components BEGIN SELECT RAISE(ABORT,'immutable_component'); END;
CREATE TRIGGER media_components_retained BEFORE DELETE ON media_components BEGIN SELECT RAISE(ABORT,'retained_component'); END;
CREATE VIEW asset_media_status AS
 SELECT a.id AS asset_id,
 CASE WHEN (SELECT count(*) FROM media_components m WHERE m.asset_id=a.id AND m.revision=a.current_revision)>=CASE WHEN r.media_type='live' THEN 2 ELSE 1 END THEN 'ready'
 WHEN EXISTS(SELECT 1 FROM media_components m WHERE m.asset_id=a.id AND m.revision=a.current_revision) THEN 'partial'
 ELSE 'not_transferred' END AS media_state
 FROM assets a JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision;
