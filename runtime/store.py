"""Private SQLite runtime. No network access and no writes to Sources."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import time
import uuid

REPO = Path(__file__).resolve().parents[1]
SESSION_SECONDS = 86400
SCHEMA_VERSION = 7
ACTIONS = {'login', 'session', 'logout', 'overview', 'sources', 'debug', 'connect_source', 'backup', 'restore', 'denied',
           'migration', 'pairing_start', 'pairing_preview', 'pairing_claim', 'pairing_pending',
           'pairing_confirm', 'devices', 'device_revoke', 'device_auth', 'ingest_begin', 'ingest_batch', 'ingest_finish', 'source_policy', 'source_permission', 'assets',
           'media_begin','media_chunk','media_complete','media_read','media_library',
           'artifact_create','artifact_edit','artifact_recompose','artifact_read','artifact_debug','ingest_progress','ingest_retry','knowledge_rebuild','knowledge_read','knowledge_evidence','knowledge_trip','knowledge_correction','knowledge_area'}

class RuntimeErrorResult(Exception):
    def __init__(self, status, code, message=None):
        self.status, self.code = status, code
        self.message = message or {
            'unauthorized': 'Sign in to continue.',
            'invalid_credentials': 'The sign-in details are not valid.',
            'csrf': 'Reload the page and try again.',
            'rate_limited': 'Too many attempts. Try again later.',
            'audit_unavailable': 'This operation cannot be audited. Try again later.',
        }.get(code, 'The operation could not be completed.')
        super().__init__(self.message)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def csrf_for(token):
    return digest('memory-csrf-v1:' + token)

def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def identifier():
    return uuid.uuid4().hex

def verifier(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=131072, r=8, p=1, maxmem=256*1024*1024)
    return 'scrypt-v1$' + salt.hex() + '$' + hashed.hex()

def verify_password(password, stored):
    try:
        kind, salt, expected = stored.split('$')
        if kind != 'scrypt-v1': return False
        actual = verifier(password, bytes.fromhex(salt)).split('$')[-1]
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def private_destination(value, *, must_be_new=False):
    path = Path(value).expanduser()
    system_aliases = {Path('/tmp'): Path('/private/tmp'), Path('/var'): Path('/private/var')}
    for parent in [path, *path.parents]:
        if parent.is_symlink() and system_aliases.get(parent) != parent.resolve():
            raise ValueError('Private path cannot contain symbolic links')
    path = path.resolve()
    vault = (Path.home() / 'base').resolve()
    repo = REPO.resolve()
    if path == repo or repo in path.parents or path == vault or vault in path.parents:
        raise ValueError('Private data must be outside repositories and the document vault')
    if any((parent / '.git').exists() for parent in [path, *path.parents]):
        raise ValueError('Private data must be outside repositories')
    if must_be_new and path.exists():raise ValueError('Destination must be new')
    if path.exists() and path.stat().st_uid != os.getuid():raise ValueError('Private owner mismatch')
    return path

class RuntimeStore:
    def __init__(self, root, *, fixture=False, clock=time.time):
        if not hasattr(hashlib, 'scrypt'):
            raise ValueError('Use the configured Python 3.14 environment with hashlib.scrypt')
        self.root = private_destination(root)
        if (self.root / 'restore.incomplete').exists():
            raise ValueError('Incomplete restore is quarantined; use a new restore destination')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_uid != os.getuid(): raise ValueError('Runtime owner mismatch')
        self.root.chmod(0o700)
        self.path = self.root / 'memory.sqlite3'
        if self.path.is_symlink(): raise ValueError('Database cannot be a symbolic link')
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        os.close(fd); self.path.chmod(0o600)
        self.clock = clock
        self.fixture = bool(fixture)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == 0:
                schema = '\n'.join((REPO/f'schema/runtime-v{n}.sql').read_text() for n in range(1,SCHEMA_VERSION+1))
                db.executescript('BEGIN IMMEDIATE;\n' + schema + f'\nPRAGMA user_version={SCHEMA_VERSION};\nCOMMIT;')
            elif version not in range(1,SCHEMA_VERSION+1): raise ValueError('Unsupported runtime schema')
            db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('fixture', json.dumps(self.fixture)))
            if db.execute('SELECT value FROM metadata WHERE key=?', ('fixture',)).fetchone()[0] != json.dumps(self.fixture):
                raise ValueError('Runtime fixture mode mismatch')
        if 0 < version < SCHEMA_VERSION:
            self._migrate()
        with self._db() as db:
            required={'artifacts':{'owner_id','revision','type'},'artifact_revisions':{'title','layout','generation_id','trip_revision'},'artifact_members':{'selected_revision','intent','position'},'artifact_requests':{'digest','operation_id'},
                      'current_asset_index':{'owner_id','revision','capture_instant','capture_day','media_type'},
                      'scan_runs':{'observed','expected_count','recent_after'},'scan_assets':{'run_id','native_id','asset_id'},
                      'knowledge_facts':{'generation_id','asset_id','revision','capture_day','signature'},
                      'knowledge_generations':{'definition','policy_json','current'},'knowledge_requests':{'digest','result_json'},
                      'knowledge_trip_members':{'trip_revision','evidence_revision','evidence_signature'},
                      'knowledge_area_members':{'area_revision','evidence_revision','evidence_signature'},
                      'knowledge_trips':{'owner_id','state','revision'},'knowledge_area_revisions':{'confirmed','start','end'},
                      'asset_observations':{'sequence','asset_id','source_revision'},
                      'assets':{'last_observation','scope_authorized','restriction_uncertain'},'ingest_runs':{'policy_revision','next_sequence'},
                      'media_uploads':{'next_offset','state'},'media_components':{'storage_key','sha256'},'asset_media_status':{'asset_id','media_state'}}
            for table,columns in required.items():
                actual={row['name'] for row in db.execute('PRAGMA table_info('+table+')')}
                if not columns<=actual:raise ValueError('Incomplete runtime schema; retain this root and restore a verified backup')

    def _migrate(self):
        self.backup(self.root/'migration-backups'/('before-v'+str(SCHEMA_VERSION)+'-'+identifier()))
        with self.transaction() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version==SCHEMA_VERSION:return
            tables=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            before={table:db.execute('SELECT count(*) FROM "'+table+'"').fetchone()[0] for table in tables}
            for target in range(version+1,SCHEMA_VERSION+1):
                statement=''
                for line in (REPO/f'schema/runtime-v{target}.sql').read_text().splitlines(keepends=True):
                    statement+=line
                    if sqlite3.complete_statement(statement):
                        db.execute(statement);statement=''
                if statement.strip():raise ValueError('Incomplete migration SQL')
            if db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Migration relationship validation failed')
            if any(db.execute('SELECT count(*) FROM "'+table+'"').fetchone()[0]!=count for table,count in before.items()):
                raise ValueError('Migration count validation failed')
            db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
            self._audit(db,None,'migration','allowed')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=5000')
        try: yield db
        finally: db.close()

    @contextmanager
    def transaction(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise

    def _audit(self, db, owner, action, outcome, count=0):
        if action not in ACTIONS or outcome not in {'allowed', 'denied'}: raise ValueError('Invalid audit classification')
        try:
            db.execute('INSERT INTO audit(id,owner_id,action,outcome,count,created_at) VALUES(?,?,?,?,?,?)',
                       (identifier(), owner, action, outcome, count, int(self.clock())))
        except sqlite3.Error as error:
            raise RuntimeErrorResult(503, 'audit_unavailable') from error

    def create_owner(self, username, password, display_name):
        if not isinstance(username,str) or not re.fullmatch(r'[a-z0-9_.-]{1,64}',username): raise ValueError('Invalid username')
        if not isinstance(password,str) or not 12 <= len(password) <= 1024: raise ValueError('Password must contain 12–1024 characters')
        if not isinstance(display_name,str) or not 1 <= len(display_name) <= 100: raise ValueError('Invalid display name')
        owner = identifier(); stored = verifier(password)
        with self.transaction() as db:
            db.execute('INSERT INTO owners(id,username,display_name,verifier,created_at) VALUES(?,?,?,?,?)',
                       (owner, username, display_name, stored, int(self.clock())))
        return owner

    def _principal(self, db, token):
        if not isinstance(token,str) or not 20 <= len(token) <= 200: return None
        return db.execute('''SELECT o.id,o.display_name,o.auth_epoch,s.csrf_hash FROM sessions s
          JOIN owners o ON o.id=s.owner_id WHERE s.token_hash=? AND s.revoked_at IS NULL
          AND s.expires_at>? AND s.auth_epoch=o.auth_epoch''', (digest(token), int(self.clock()))).fetchone()

    def login(self, username, password, remote):
        if not isinstance(username,str) or not isinstance(password,str) or len(username)>64 or len(password)>1024:
            raise RuntimeErrorResult(400,'invalid_input')
        error = None; result = None; now = int(self.clock())
        # Persistent account+client and client-wide caps. Raw usernames/IPs never enter the audit.
        keys = [(digest('login:'+remote+':'+username.casefold()),5), (digest('client:'+remote),20)]
        with self.transaction() as db:
            limits=[]
            for key, cap in keys:
                row=db.execute('SELECT window_start,attempts FROM login_limits WHERE key=?',(key,)).fetchone()
                start, attempts=(row['window_start'],row['attempts']) if row and now-row['window_start']<900 else (now,0)
                limits.append((key,cap,start,attempts))
            if any(attempts >= cap for _,cap,_,attempts in limits):
                self._audit(db,None,'login','denied'); error=RuntimeErrorResult(429,'rate_limited')
            else:
                owner=db.execute('SELECT * FROM owners WHERE username=?',(username,)).fetchone()
                if owner: valid=verify_password(password,owner['verifier'])
                else:
                    verifier(password, b'no-account-salt!')
                    valid=False
                for key,_,start,attempts in limits:
                    db.execute('INSERT INTO login_limits VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET window_start=excluded.window_start,attempts=excluded.attempts',
                               (key,start,attempts+1))
                if not valid:
                    self._audit(db,None,'login','denied'); error=RuntimeErrorResult(401,'invalid_credentials')
                else:
                    db.execute('UPDATE login_limits SET attempts=0 WHERE key=?',(keys[0][0],))
                    token=secrets.token_urlsafe(32); csrf=csrf_for(token)
                    db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?)',
                               (digest(token),owner['id'],digest(csrf),owner['auth_epoch'],now+SESSION_SECONDS,None,now))
                    self._audit(db,owner['id'],'login','allowed')
                    result={'owner':{'id':owner['id'],'display_name':owner['display_name']}, 'csrf_token':csrf,'fixture':self.fixture,'token':token}
        if error: raise error
        return result

    def read(self, token, action, reader):
        error=None; result=None
        with self.transaction() as db:
            owner=self._principal(db,token)
            if owner is None:
                self._audit(db,None,action,'denied');error=RuntimeErrorResult(401,'unauthorized')
            else:
                db.execute('SAVEPOINT read_operation')
                try:result=reader(db,owner)
                except RuntimeErrorResult as refusal:
                    db.execute('ROLLBACK TO read_operation');error=refusal
                db.execute('RELEASE read_operation')
                self._audit(db,owner['id'],action,'denied' if error else 'allowed')
        if error: raise error
        return result

    def session(self, token):
        return self.read(token,'session',lambda db,owner:{'owner':{'id':owner['id'],'display_name':owner['display_name']},'csrf_token':csrf_for(token),'fixture':self.fixture})

    def logout(self, token, csrf):
        error=None
        with self.transaction() as db:
            owner=self._principal(db,token)
            if owner is None:
                self._audit(db,None,'logout','denied');error=RuntimeErrorResult(401,'unauthorized')
            elif not isinstance(csrf,str) or not hmac.compare_digest(digest(csrf),owner['csrf_hash']):
                self._audit(db,owner['id'],'logout','denied');error=RuntimeErrorResult(403,'csrf')
            else:
                db.execute('UPDATE sessions SET revoked_at=? WHERE token_hash=?',(int(self.clock()),digest(token)))
                self._audit(db,owner['id'],'logout','allowed')
        if error:raise error
        return {'ok':True}

    def _connect_source(self, db, owner_id, source_key, name):
        """Internal transaction hook. Caller owns authorization and audit commit."""
        if not isinstance(source_key,str) or not 1 <= len(source_key) <= 256:raise ValueError('Invalid source identity')
        if not isinstance(name,str) or not 1 <= len(name) <= 100:raise ValueError('Invalid source name')
        if not db.execute('SELECT id FROM owners WHERE id=?',(owner_id,)).fetchone():raise RuntimeErrorResult(404,'not_found')
        now=int(self.clock())
        db.execute('INSERT OR IGNORE INTO vaults VALUES(?,?,?,?)',(identifier(),owner_id,'Photos',now))
        vault=db.execute('SELECT id FROM vaults WHERE owner_id=? AND domain=?',(owner_id,'Photos')).fetchone()['id']
        db.execute('INSERT OR IGNORE INTO connections(id,owner_id,vault_id,source_key,name,created_at) VALUES(?,?,?,?,?,?)',
                   (identifier(),owner_id,vault,source_key,name,now))
        row=db.execute('SELECT id,vault_id FROM connections WHERE owner_id=? AND source_key=?',(owner_id,source_key)).fetchone()
        return dict(row)

    def connect_source(self, owner_id, source_key, name):
        """Internal post-pairing operation; never exposed as unauthenticated owner_id input."""
        with self.transaction() as db:
            result = self._connect_source(db, owner_id, source_key, name)
            self._audit(db,owner_id,'connect_source','allowed')
            return result

    def _sources(self, db, owner):
        from runtime.ingestion import VISIBLE
        return [dict(row) for row in db.execute('''SELECT c.id,c.name,c.permission,c.status,c.last_success,
          c.include_hidden,c.include_shared_library,c.include_shared_albums,
          (SELECT count(*) FROM assets a WHERE a.connection_id=c.id AND a.owner_id=c.owner_id AND '''+VISIBLE+''') AS index_count,
          (SELECT count(*) FROM assets a JOIN asset_media_status m ON m.asset_id=a.id WHERE a.connection_id=c.id AND a.owner_id=c.owner_id AND m.media_state='ready' AND '''+VISIBLE+''') AS media_ready_count
          FROM connections c WHERE c.owner_id=? ORDER BY c.created_at,c.id''',(owner['id'],))]

    def sources(self, token):
        return self.read(token,'sources',lambda db,owner:{'sources':self._sources(db,owner),'fixture':self.fixture})

    def overview(self, token):
        def build(db,owner):
            vault=db.execute('SELECT id,domain FROM vaults WHERE owner_id=?',(owner['id'],)).fetchone()
            sources=self._sources(db,owner)
            state='not_connected' if not sources else 'indexing' if any(s['status']=='indexing' for s in sources) else 'authorized_scan_indexed' if all(s['status']=='scan_indexed' for s in sources) else 'bounded_sample_indexed' if all(s['status']=='sample_indexed' for s in sources) else 'awaiting_device'
            successful=[s['last_success'] for s in sources if s['last_success']]
            assets=sum(s['index_count'] for s in sources);ready=sum(s['media_ready_count'] for s in sources)
            from runtime.artifacts import ArtifactService
            artifact_count=len(ArtifactService(self)._visible_rows(db,owner))
            from runtime.knowledge import KnowledgeService,scope_value
            trip_sql,trip_args,_=KnowledgeService(self)._trip_query(db,owner,scope_value(None))
            trip_count=db.execute('SELECT count(*) FROM ('+trip_sql+')',trip_args).fetchone()[0]
            return {'vault':dict(vault) if vault else None,'counts':{'assets':assets,'media_ready':ready,'artifacts':artifact_count,'trips':trip_count},
                    'sources':sources,'coverage':{'index_state':state,
                    'media_state':'not_available' if not assets else 'ready' if ready==assets else 'partial' if ready else 'not_transferred','last_success':max(successful) if successful else None},'fixture':self.fixture}
        return self.read(token,'overview',build)

    def debug(self, token):
        def build(db,owner):
            operations=[dict(row) for row in db.execute('SELECT id,action,status,created_at,completed_at FROM operations WHERE owner_id=? ORDER BY created_at DESC LIMIT 50',(owner['id'],))]
            audit=[dict(row) for row in db.execute('SELECT id,action,outcome,count,created_at FROM audit WHERE owner_id=? ORDER BY sequence DESC LIMIT 50',(owner['id'],))]
            return {'version':(REPO/'VERSION').read_text().strip(),'environment':'fixture' if self.fixture else 'private',
                    'health':{'storage':'ok','audit':'ok'},'operations':operations,'audit':audit,'fixture':self.fixture}
        return self.read(token,'debug',build)

    def record_denial(self):
        with self.transaction() as db:self._audit(db,None,'denied','denied')

    def backup(self, destination):
        destination=private_destination(destination,must_be_new=True)
        # The disclosure to a backup cannot happen without a committed receipt.
        with self.transaction() as db:self._audit(db,None,'backup','allowed')
        destination.mkdir(mode=0o700,parents=True)
        target=destination/'memory.sqlite3'
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600);os.close(fd)
        with self._db() as source:
            sink=sqlite3.connect(target)
            try:
                source.backup(sink)
                version=sink.execute('PRAGMA user_version').fetchone()[0]
                media=[]
                if version>=4:
                    from runtime.media import retained_files,copy_retained
                    sink.row_factory=sqlite3.Row;media=retained_files(sink)
                    copy_retained(self.root,destination,media)
            finally:sink.close()
        manifest={'schema':version,'fixture':self.fixture,'sha256':file_digest(target)}
        if version>=4:manifest['media']=media
        path=destination/'manifest.json';path.write_text(json.dumps(manifest));path.chmod(0o600)
        return manifest

    @classmethod
    def restore(cls, backup, destination):
        backup=private_destination(backup)
        destination=private_destination(destination,must_be_new=True)
        if (backup/'manifest.json').is_symlink():raise ValueError('Invalid backup manifest')
        manifest=json.loads((backup/'manifest.json').read_text())
        source=backup/'memory.sqlite3'
        if source.is_symlink() or manifest.get('schema') not in range(1,SCHEMA_VERSION+1) or type(manifest.get('fixture')) is not bool:
            raise ValueError('Backup integrity failed')
        if file_digest(source)!=manifest.get('sha256'):
            raise ValueError('Backup integrity failed')
        destination.mkdir(mode=0o700,parents=True)
        marker=destination/'restore.incomplete'
        fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as output:
            output.write('Access denied until restore validation and revocation commit.\n')
            output.flush();os.fsync(output.fileno())
        # Marker is in place before any historical data/session appears here.
        target=destination/'memory.sqlite3';shutil.copyfile(source,target);target.chmod(0o600)
        db=sqlite3.connect(target,isolation_level=None)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Backup integrity failed')
            if db.execute('PRAGMA user_version').fetchone()[0] != manifest['schema']:
                raise ValueError('Backup schema mismatch')
            if manifest['schema']>=4:
                from runtime.media import retained_files,copy_retained
                db.row_factory=sqlite3.Row
                expected=sorted(retained_files(db),key=lambda row:row['storage_key'])
                supplied=manifest.get('media')
                if not isinstance(supplied,list) or any(not isinstance(row,dict) or set(row)!={'storage_key','size','sha256'} for row in supplied):
                    raise ValueError('Invalid media manifest')
                if sorted(supplied,key=lambda row:row['storage_key'])!=expected:raise ValueError('Media manifest mismatch')
                copy_retained(backup,destination,expected)
            db.execute('BEGIN IMMEDIATE')
            if manifest['schema'] >= 2:
                db.execute('UPDATE devices SET revoked_at=?',(int(time.time()),))
                db.execute('UPDATE pairing_intents SET revoked_at=?',(int(time.time()),))
            if manifest['schema'] >= 3:
                db.execute("UPDATE ingest_runs SET state='interrupted' WHERE state='active'")
                db.execute('UPDATE ingest_leases SET expires_at=0')
            if manifest['schema'] >=4:db.execute("UPDATE media_uploads SET state='interrupted' WHERE state='active'")
            db.execute('UPDATE sessions SET revoked_at=?',(int(time.time()),))
            db.execute('UPDATE owners SET auth_epoch=auth_epoch+1')
            db.execute("UPDATE connections SET permission='restricted',status='reauthorization_required',policy_revision=policy_revision+1")
            try:
                db.execute('INSERT INTO audit(id,owner_id,action,outcome,count,created_at) VALUES(?,?,?,?,?,?)',
                           (identifier(),None,'restore','allowed',0,int(time.time())))
            except sqlite3.Error as error:raise RuntimeErrorResult(503,'audit_unavailable') from error
            db.execute('COMMIT')
        finally:db.close()
        # Retain the receipt. A failure/crash before this rename stays quarantined.
        marker.rename(destination/'restore.completed')
        return cls(destination,fixture=manifest['fixture'])
