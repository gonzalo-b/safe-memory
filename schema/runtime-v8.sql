-- Original resources are distinct from optimized playback readiness.
CREATE TABLE original_requests (
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES owners(id),asset_id TEXT NOT NULL REFERENCES assets(id),revision INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('waiting_for_device','transferring','failed','ready')),error_code TEXT,manifest_digest TEXT,
 created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,
 UNIQUE(owner_id,asset_id,revision),FOREIGN KEY(asset_id,revision) REFERENCES asset_revisions(asset_id,revision)
);
CREATE INDEX original_pending ON original_requests(owner_id,state,created_at,id);
CREATE TABLE original_uploads (
 id TEXT PRIMARY KEY,request_id TEXT NOT NULL REFERENCES original_requests(id),ordinal INTEGER NOT NULL,
 resource_type TEXT NOT NULL,original_filename TEXT NOT NULL,uniform_type_identifier TEXT NOT NULL,
 size INTEGER NOT NULL,sha256 TEXT NOT NULL,next_offset INTEGER NOT NULL DEFAULT 0,
 state TEXT NOT NULL DEFAULT 'active',component_id TEXT,UNIQUE(request_id,ordinal)
);
CREATE TABLE original_chunks (
 upload_id TEXT NOT NULL REFERENCES original_uploads(id),offset INTEGER NOT NULL,size INTEGER NOT NULL,
 sha256 TEXT NOT NULL,storage_key TEXT NOT NULL UNIQUE,PRIMARY KEY(upload_id,offset)
);
CREATE TABLE original_components (
 id TEXT PRIMARY KEY,upload_id TEXT NOT NULL UNIQUE REFERENCES original_uploads(id),storage_key TEXT NOT NULL UNIQUE,
 size INTEGER NOT NULL,sha256 TEXT NOT NULL,created_at INTEGER NOT NULL
);
CREATE TABLE original_owner_receipts (
 owner_id TEXT NOT NULL REFERENCES owners(id),request_key TEXT NOT NULL,digest TEXT NOT NULL,
 request_id TEXT NOT NULL REFERENCES original_requests(id),PRIMARY KEY(owner_id,request_key)
);
CREATE TRIGGER original_chunks_immutable BEFORE UPDATE ON original_chunks BEGIN SELECT RAISE(ABORT,'immutable_original_chunk'); END;
CREATE TRIGGER original_chunks_retained BEFORE DELETE ON original_chunks BEGIN SELECT RAISE(ABORT,'retained_original_chunk'); END;
CREATE TRIGGER original_components_immutable BEFORE UPDATE ON original_components BEGIN SELECT RAISE(ABORT,'immutable_original_component'); END;
CREATE TRIGGER original_components_retained BEFORE DELETE ON original_components BEGIN SELECT RAISE(ABORT,'retained_original_component'); END;
CREATE TRIGGER original_receipts_immutable BEFORE UPDATE ON original_owner_receipts BEGIN SELECT RAISE(ABORT,'immutable_original_receipt'); END;
CREATE TRIGGER original_receipts_retained BEFORE DELETE ON original_owner_receipts BEGIN SELECT RAISE(ABORT,'retained_original_receipt'); END;
CREATE TRIGGER original_requests_retained BEFORE DELETE ON original_requests BEGIN SELECT RAISE(ABORT,'retained_original_request'); END;
CREATE TRIGGER original_uploads_retained BEFORE DELETE ON original_uploads BEGIN SELECT RAISE(ABORT,'retained_original_upload'); END;
CREATE TRIGGER original_upload_identity_immutable BEFORE UPDATE OF request_id,ordinal,resource_type,original_filename,uniform_type_identifier,size,sha256 ON original_uploads BEGIN SELECT RAISE(ABORT,'immutable_original_identity'); END;
CREATE TRIGGER original_request_identity_immutable BEFORE UPDATE OF owner_id,asset_id,revision ON original_requests BEGIN SELECT RAISE(ABORT,'immutable_original_request'); END;
CREATE TRIGGER original_manifest_immutable BEFORE UPDATE OF manifest_digest ON original_requests WHEN OLD.manifest_digest IS NOT NULL AND (NEW.manifest_digest IS NULL OR NEW.manifest_digest!=OLD.manifest_digest) BEGIN SELECT RAISE(ABORT,'immutable_original_manifest'); END;
