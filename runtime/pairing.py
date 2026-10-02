"""Owner-confirmed Photos device pairing; no network and no Source data access.

Secrets/credentials use canonical unpadded base64url of 32 random bytes. The
client creates its credential and retains it privately; the server only stores
SHA256 hashes. fingerprint is the full lowercase credential SHA256, compared
exactly on confirmation. A valid device binding is identity, never a Grant.

Intent expiry is 300 seconds and applies through confirmation. Identical claim
retries work while pending; the secret stops working once confirmed. Confirm
retries return the original live binding even after expiry. Revocation/epoch
changes always override retry behavior. New credentials reconnect to the same
owner/library connection; old credentials can never be rebound/reactivated.
The opaque claim_id becomes device_id only on confirmation, so the client can
check its credential without retaining or replaying the single-use secret.
"""
from __future__ import annotations

import base64
import hmac
import re
import secrets
import unicodedata
from runtime.store import RuntimeErrorResult, digest, identifier

PAIRING_SECONDS = 300


def _secret(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', value):
        return False
    raw = base64.urlsafe_b64decode(value + '=')
    return len(raw) == 32 and base64.urlsafe_b64encode(raw).decode().rstrip('=') == value


def _text(value, maximum):
    return (isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip()
            and all(not unicodedata.category(char).startswith('C') for char in value))


class PairingService:
    def __init__(self, store):
        self.store = store

    def _run(self, action, operation, *, token=None, csrf=None, owner_required=False, mutate=False):
        """No disclosure until receipt commits; denied mutations roll back first."""
        error = result = None
        with self.store.transaction() as db:
            owner = self.store._principal(db, token) if owner_required else None
            db.execute('SAVEPOINT pairing_operation')
            try:
                if owner_required and owner is None:
                    raise RuntimeErrorResult(401, 'unauthorized')
                if mutate and (not isinstance(csrf, str) or not hmac.compare_digest(digest(csrf), owner['csrf_hash'])):
                    raise RuntimeErrorResult(403, 'csrf')
                result, audit_owner = operation(db, owner)
            except RuntimeErrorResult as denied:
                db.execute('ROLLBACK TO pairing_operation')
                error = denied
                audit_owner = owner['id'] if owner else None
            db.execute('RELEASE pairing_operation')
            self.store._audit(db, audit_owner, action, 'denied' if error else 'allowed')
        if error:
            raise error
        return result

    def start(self, token, csrf):
        def create(db, owner):
            now = int(self.store.clock()); secret = secrets.token_urlsafe(32); intent = identifier()
            db.execute('''INSERT INTO pairing_intents(id,owner_id,secret_hash,auth_epoch,created_at,expires_at)
                          VALUES(?,?,?,?,?,?)''',
                       (intent, owner['id'], digest(secret), owner['auth_epoch'], now, now + PAIRING_SECONDS))
            return {'pairing_id': intent, 'secret': secret, 'expires_at': now + PAIRING_SECONDS}, owner['id']
        return self._run('pairing_start', create, token=token, csrf=csrf, owner_required=True, mutate=True)

    def _intent(self, db, secret):
        if not _secret(secret):
            raise RuntimeErrorResult(403, 'pairing_denied')
        intent = db.execute('''SELECT p.* FROM pairing_intents p JOIN owners o ON o.id=p.owner_id
            WHERE p.secret_hash=? AND p.revoked_at IS NULL AND p.auth_epoch=o.auth_epoch
            AND p.expires_at>? AND p.confirmed_at IS NULL''', (digest(secret), int(self.store.clock()))).fetchone()
        if intent is None:
            raise RuntimeErrorResult(403, 'pairing_denied')
        return intent

    def preview(self, secret):
        """Possession-only status preview. Never claims or registers a device."""
        def read(db, owner):
            intent = self._intent(db, secret)
            return {'status': 'awaiting_confirmation' if intent['claim_id'] else 'awaiting_claim',
                    'expires_at': intent['expires_at']}, intent['owner_id']
        return self._run('pairing_preview', read)

    def claim(self, secret, device_name, library_id, credential):
        def request(db, owner):
            if not _text(device_name, 100) or not _text(library_id, 256) or not _secret(credential):
                raise RuntimeErrorResult(400, 'invalid_input')
            intent = self._intent(db, secret); hashed = digest(credential)
            if intent['claim_id']:
                if (not hmac.compare_digest(intent['credential_hash'], hashed)
                        or intent['device_name'] != device_name or intent['library_id'] != library_id):
                    raise RuntimeErrorResult(403, 'pairing_denied')
                claim_id = intent['claim_id']
            else:
                # Includes revoked/expired history: a credential is never rebound.
                if (db.execute('SELECT id FROM pairing_intents WHERE credential_hash=?', (hashed,)).fetchone()
                        or db.execute('SELECT id FROM devices WHERE credential_hash=?', (hashed,)).fetchone()):
                    raise RuntimeErrorResult(403, 'pairing_denied')
                claim_id = identifier()
                db.execute('''UPDATE pairing_intents SET claim_id=?,credential_hash=?,device_name=?,library_id=?,claimed_at=?
                              WHERE id=?''',
                           (claim_id, hashed, device_name, library_id, int(self.store.clock()), intent['id']))
            return {'claim_id': claim_id, 'fingerprint': hashed, 'expires_at': intent['expires_at']}, intent['owner_id']
        return self._run('pairing_claim', request)

    def pending(self, token):
        def read(db, owner):
            rows = db.execute('''SELECT claim_id,device_name,credential_hash AS fingerprint,expires_at
                FROM pairing_intents WHERE owner_id=? AND auth_epoch=? AND claim_id IS NOT NULL
                AND confirmed_at IS NULL AND revoked_at IS NULL AND expires_at>? ORDER BY created_at,id''',
                (owner['id'], owner['auth_epoch'], int(self.store.clock())))
            return {'claims': [dict(row) for row in rows]}, owner['id']
        return self._run('pairing_pending', read, token=token, owner_required=True)

    def _binding(self, db, device_id):
        return db.execute('''SELECT d.id AS device_id,d.owner_id,d.connection_id,c.vault_id
            FROM devices d JOIN owners o ON o.id=d.owner_id
            JOIN connections c ON c.id=d.connection_id AND c.owner_id=d.owner_id
            JOIN vaults v ON v.id=c.vault_id AND v.owner_id=d.owner_id
            WHERE d.id=? AND d.revoked_at IS NULL AND d.auth_epoch=o.auth_epoch''', (device_id,)).fetchone()

    def confirm(self, token, csrf, claim_id, fingerprint):
        def approve(db, owner):
            if (not isinstance(claim_id, str) or not isinstance(fingerprint, str)
                    or not re.fullmatch(r'[0-9a-f]{64}', fingerprint)):
                raise RuntimeErrorResult(403, 'pairing_denied')
            intent = db.execute('''SELECT * FROM pairing_intents WHERE claim_id=? AND owner_id=?
                AND auth_epoch=? AND revoked_at IS NULL''', (claim_id, owner['id'], owner['auth_epoch'])).fetchone()
            if intent is None or not hmac.compare_digest(intent['credential_hash'], fingerprint):
                raise RuntimeErrorResult(403, 'pairing_denied')
            if intent['confirmed_at'] is not None:
                binding = self._binding(db, intent['device_id'])
                if binding is None:
                    raise RuntimeErrorResult(403, 'pairing_denied')
                return dict(binding), owner['id']
            now = int(self.store.clock())
            if intent['expires_at'] <= now:
                raise RuntimeErrorResult(403, 'pairing_denied')
            source = self.store._connect_source(db, owner['id'], intent['library_id'], 'Apple Photos')
            # Pairing never grants read/ingest access or changes collection consent.
            db.execute("UPDATE connections SET permission='restricted',status='awaiting_ingest' WHERE id=?", (source['id'],))
            device = intent['claim_id']
            db.execute('''INSERT INTO devices(id,owner_id,connection_id,credential_hash,device_name,auth_epoch,created_at)
                          VALUES(?,?,?,?,?,?,?)''',
                       (device, owner['id'], source['id'], intent['credential_hash'], intent['device_name'], owner['auth_epoch'], now))
            db.execute('UPDATE pairing_intents SET confirmed_at=?,device_id=? WHERE id=?', (now, device, intent['id']))
            return dict(self._binding(db, device)), owner['id']
        return self._run('pairing_confirm', approve, token=token, csrf=csrf, owner_required=True, mutate=True)

    def devices(self, token):
        def read(db, owner):
            rows = db.execute('''SELECT id AS device_id,connection_id,device_name,credential_hash AS fingerprint,
                created_at,revoked_at FROM devices WHERE owner_id=? ORDER BY created_at,id''', (owner['id'],))
            return {'devices': [dict(row) for row in rows]}, owner['id']
        return self._run('devices', read, token=token, owner_required=True)

    def revoke(self, token, csrf, device_id):
        def disable(db, owner):
            if not isinstance(device_id, str) or not db.execute('SELECT id FROM devices WHERE id=? AND owner_id=?', (device_id, owner['id'])).fetchone():
                raise RuntimeErrorResult(403, 'pairing_denied')
            db.execute('UPDATE devices SET revoked_at=COALESCE(revoked_at,?) WHERE id=?', (int(self.store.clock()), device_id))
            return {'ok': True}, owner['id']
        return self._run('device_revoke', disable, token=token, csrf=csrf, owner_required=True, mutate=True)

    def authenticate(self, device_id, credential):
        """Identity-only check for future ingest. No Source records or Grant returned."""
        def read(db, owner):
            if not isinstance(device_id, str) or not _secret(credential):
                raise RuntimeErrorResult(401, 'unauthorized')
            device = db.execute('SELECT credential_hash FROM devices WHERE id=?', (device_id,)).fetchone()
            if device is None or not hmac.compare_digest(device['credential_hash'], digest(credential)):
                raise RuntimeErrorResult(401, 'unauthorized')
            binding = self._binding(db, device_id)
            if binding is None:
                raise RuntimeErrorResult(401, 'unauthorized')
            return {**dict(binding), 'data_access': False}, binding['owner_id']
        return self._run('device_auth', read)
