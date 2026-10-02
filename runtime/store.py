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
ACTIONS = {'login', 'session', 'logout', 'overview', 'sources', 'debug', 'connect_source', 'backup', 'restore', 'denied'}

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
                schema = (REPO/'schema/runtime-v1.sql').read_text()
                db.executescript('BEGIN IMMEDIATE;\n' + schema + '\nPRAGMA user_version=1;\nCOMMIT;')
            elif version != 1: raise ValueError('Unsupported runtime schema')
            db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('fixture', json.dumps(self.fixture)))
            if db.execute('SELECT value FROM metadata WHERE key=?', ('fixture',)).fetchone()[0] != json.dumps(self.fixture):
                raise ValueError('Runtime fixture mode mismatch')

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
                result=reader(db,owner)
                self._audit(db,owner['id'],action,'allowed')
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

    def connect_source(self, owner_id, source_key, name):
        """Internal post-pairing operation; never exposed as unauthenticated owner_id input."""
        if not isinstance(source_key,str) or not 1 <= len(source_key) <= 256:raise ValueError('Invalid source identity')
        if not isinstance(name,str) or not 1 <= len(name) <= 100:raise ValueError('Invalid source name')
        with self.transaction() as db:
            if not db.execute('SELECT id FROM owners WHERE id=?',(owner_id,)).fetchone():raise RuntimeErrorResult(404,'not_found')
            now=int(self.clock())
            db.execute('INSERT OR IGNORE INTO vaults VALUES(?,?,?,?)',(identifier(),owner_id,'Photos',now))
            vault=db.execute('SELECT id FROM vaults WHERE owner_id=? AND domain=?',(owner_id,'Photos')).fetchone()['id']
            db.execute('INSERT OR IGNORE INTO connections(id,owner_id,vault_id,source_key,name,created_at) VALUES(?,?,?,?,?,?)',
                       (identifier(),owner_id,vault,source_key,name,now))
            row=db.execute('SELECT id,vault_id FROM connections WHERE owner_id=? AND source_key=?',(owner_id,source_key)).fetchone()
            self._audit(db,owner_id,'connect_source','allowed')
            return dict(row)

    def _sources(self, db, owner):
        return [dict(row) for row in db.execute('SELECT id,name,permission,status,last_success,index_count,media_ready_count FROM connections WHERE owner_id=? ORDER BY created_at,id',(owner['id'],))]

    def sources(self, token):
        return self.read(token,'sources',lambda db,owner:{'sources':self._sources(db,owner),'fixture':self.fixture})

    def overview(self, token):
        def build(db,owner):
            vault=db.execute('SELECT id,domain FROM vaults WHERE owner_id=?',(owner['id'],)).fetchone()
            sources=self._sources(db,owner)
            return {'vault':dict(vault) if vault else None,'counts':{'assets':0,'media_ready':0,'artifacts':0,'trips':0},
                    'sources':sources,'coverage':{'index_state':'not_connected' if not sources else 'awaiting_device',
                    'media_state':'not_available','last_success':None},'fixture':self.fixture}
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
            try:source.backup(sink)
            finally:sink.close()
        manifest={'schema':1,'fixture':self.fixture,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        path=destination/'manifest.json';path.write_text(json.dumps(manifest));path.chmod(0o600)
        return manifest

    @classmethod
    def restore(cls, backup, destination):
        backup=private_destination(backup)
        destination=private_destination(destination,must_be_new=True)
        manifest=json.loads((backup/'manifest.json').read_text())
        source=backup/'memory.sqlite3'
        if source.is_symlink() or manifest.get('schema')!=1 or type(manifest.get('fixture')) is not bool:
            raise ValueError('Backup integrity failed')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest.get('sha256'):
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
            db.execute('BEGIN IMMEDIATE')
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
