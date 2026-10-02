-- Private Gallery revisions and user intent. No source writes or public outputs.
CREATE TABLE artifacts (
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES owners(id),type TEXT NOT NULL CHECK(type='gallery'),
 revision INTEGER NOT NULL,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL
);
CREATE INDEX artifacts_owner ON artifacts(owner_id,created_at,id);
CREATE TABLE artifact_revisions (
 artifact_id TEXT NOT NULL REFERENCES artifacts(id),revision INTEGER NOT NULL,title TEXT NOT NULL,
 layout TEXT NOT NULL CHECK(layout IN ('grid','story')),cover_asset_id TEXT REFERENCES assets(id),
 definition_version TEXT NOT NULL,trip_id TEXT REFERENCES knowledge_trips(id),trip_revision INTEGER,
 generation_id TEXT REFERENCES knowledge_generations(id),origin TEXT NOT NULL,created_at INTEGER NOT NULL,
 PRIMARY KEY(artifact_id,revision)
);
CREATE TABLE artifact_members (
 artifact_id TEXT NOT NULL,revision INTEGER NOT NULL,asset_id TEXT NOT NULL REFERENCES assets(id),
 selected_revision INTEGER NOT NULL,intent TEXT NOT NULL CHECK(intent IN ('included','excluded')),
 position INTEGER NOT NULL,origin TEXT NOT NULL,
 PRIMARY KEY(artifact_id,revision,asset_id),
 FOREIGN KEY(artifact_id,revision) REFERENCES artifact_revisions(artifact_id,revision),
 FOREIGN KEY(asset_id,selected_revision) REFERENCES asset_revisions(asset_id,revision)
);
CREATE TABLE artifact_requests (
 owner_id TEXT NOT NULL REFERENCES owners(id),request_key TEXT NOT NULL,digest TEXT NOT NULL,
 artifact_id TEXT NOT NULL REFERENCES artifacts(id),revision INTEGER NOT NULL,
 operation_id TEXT NOT NULL REFERENCES operations(id),PRIMARY KEY(owner_id,request_key)
);
CREATE TRIGGER artifact_revisions_immutable BEFORE UPDATE ON artifact_revisions BEGIN SELECT RAISE(ABORT,'immutable_artifact_revision'); END;
CREATE TRIGGER artifact_revisions_retained BEFORE DELETE ON artifact_revisions BEGIN SELECT RAISE(ABORT,'retained_artifact_revision'); END;
CREATE TRIGGER artifact_members_immutable BEFORE UPDATE ON artifact_members BEGIN SELECT RAISE(ABORT,'immutable_artifact_members'); END;
CREATE TRIGGER artifact_members_retained BEFORE DELETE ON artifact_members BEGIN SELECT RAISE(ABORT,'retained_artifact_members'); END;
CREATE TRIGGER artifact_requests_immutable BEFORE UPDATE ON artifact_requests BEGIN SELECT RAISE(ABORT,'immutable_artifact_request'); END;
CREATE TRIGGER artifact_requests_retained BEFORE DELETE ON artifact_requests BEGIN SELECT RAISE(ABORT,'retained_artifact_request'); END;
CREATE TRIGGER artifacts_retained BEFORE DELETE ON artifacts BEGIN SELECT RAISE(ABORT,'retained_artifact'); END;
