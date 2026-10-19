"""Tenant-scoped durable document store with atomic insert/update primitives."""
import json
import os
import sqlite3
from pathlib import Path
from .domain import RelayError, now


class Store:
    def __init__(self, path=None):
        self.path = str(path or Path(os.getenv('RELAY_DATA_DIR', '.local/data'))/'relay.sqlite3')
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (tenant TEXT, kind TEXT, id TEXT, data TEXT, PRIMARY KEY(tenant,kind,id))')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT, run TEXT, data TEXT)')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.execute('PRAGMA journal_mode=WAL')
        return db

    def get(self, tenant, kind, id):
        with self.connect() as db:
            row = db.execute('SELECT data FROM records WHERE tenant=? AND kind=? AND id=?',(tenant,kind,id)).fetchone()
        if row is None:
            raise RelayError('ACCESS_DENIED', 'Record unavailable in this workspace.')
        return json.loads(row[0])

    def list(self, tenant, kind):
        with self.connect() as db:
            rows = db.execute('SELECT data FROM records WHERE tenant=? AND kind=? ORDER BY id',(tenant,kind)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def put(self, tenant, kind, id, data, create=False):
        with self.connect() as db:
            sql = 'INSERT INTO records VALUES(?,?,?,?)' if create else 'INSERT OR REPLACE INTO records VALUES(?,?,?,?)'
            try:
                db.execute(sql,(tenant,kind,id,json.dumps(data)))
            except sqlite3.IntegrityError:
                return False
        return True

    def claim(self, tenant, kind, id, expected, changes):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM records WHERE tenant=? AND kind=? AND id=?',(tenant,kind,id)).fetchone()
            if not row:
                return False
            data = json.loads(row[0])
            if any(data.get(k) != v for k,v in expected.items()):
                return False
            data.update(changes)
            db.execute('UPDATE records SET data=? WHERE tenant=? AND kind=? AND id=?',(json.dumps(data),tenant,kind,id))
        return True

    def atomic(self, tenant, fn):
        """One tenant, one SQLite transaction. Exceptions roll back the entire slice."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return fn(WorkspaceTransaction(db, tenant))

    def delete_workspace(self, tenant):
        with self.connect() as db:
            db.execute('DELETE FROM records WHERE tenant=?',(tenant,))
            db.execute('DELETE FROM events WHERE tenant=?',(tenant,))

    def event(self, tenant, run, type, **fields):
        data = dict(run_id=run, type=type, timestamp=now(), **fields)
        with self.connect() as db:
            seq = db.execute('INSERT INTO events(tenant,run,data) VALUES(?,?,?)',(tenant,run,json.dumps(data))).lastrowid
        return dict(sequence=seq,**data)

    def events(self, tenant, after=0):
        with self.connect() as db:
            rows = db.execute('SELECT seq,data FROM events WHERE tenant=? AND seq>? ORDER BY seq LIMIT 500',(tenant,after)).fetchall()
        return [dict(sequence=seq, **json.loads(data)) for seq,data in rows]


class FirestoreStore:
    def __init__(self):
        from google.cloud import firestore
        self.client = firestore.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'], database=os.getenv('RELAY_FIRESTORE_DATABASE','(default)'))

    def atomic(self, tenant, fn):
        raise RelayError('FEATURE_PENDING', 'Portable/progress transactions require the verified local SQLite store; Firestore acceptance is pending.')

    def collection(self, tenant, kind):
        if '/' in tenant or '/' in kind:
            raise RelayError('ACCESS_DENIED','Invalid scope.')
        return self.client.collection('workspaces').document(tenant).collection(kind)

    def get(self, tenant, kind, id):
        doc = self.collection(tenant,kind).document(id).get()
        if not doc.exists:
            raise RelayError('ACCESS_DENIED','Record unavailable in this workspace.')
        return doc.to_dict()['value']

    def list(self, tenant, kind):
        return [d.to_dict()['value'] for d in self.collection(tenant,kind).stream()]

    def put(self, tenant, kind, id, data, create=False):
        from google.api_core.exceptions import AlreadyExists
        ref = self.collection(tenant,kind).document(id)
        try:
            ref.create({'value':data}) if create else ref.set({'value':data})
        except AlreadyExists:
            return False
        return True

    def claim(self, tenant, kind, id, expected, changes):
        from google.cloud import firestore
        ref = self.collection(tenant,kind).document(id)
        @firestore.transactional
        def update(transaction):
            snap = ref.get(transaction=transaction)
            if not snap.exists:
                return False
            data = snap.to_dict()['value']
            if any(data.get(k)!=v for k,v in expected.items()):
                return False
            transaction.set(ref,{'value':dict(data,**changes)})
            return True
        return update(self.client.transaction())

    def event(self, tenant, run, type, **fields):
        from google.cloud import firestore
        counter = self.collection(tenant,'meta').document('sequence')
        @firestore.transactional
        def append(transaction):
            snap = counter.get(transaction=transaction)
            seq = (snap.to_dict() or {}).get('n',0)+1
            data = dict(sequence=seq,run_id=run,type=type,timestamp=now(),**fields)
            transaction.set(counter,{'n':seq})
            transaction.set(self.collection(tenant,'events').document(f'{seq:020}'),{'value':data})
            return data
        return append(self.client.transaction())

    def events(self,tenant,after=0):
        return [d.to_dict()['value'] for d in self.collection(tenant,'events').order_by('__name__').start_after({'__name__':self.collection(tenant,'events').document(f'{after:020}')}).limit(500).stream()]

    def delete_workspace(self, tenant):
        self.client.recursive_delete(self.client.collection('workspaces').document(tenant))


def make_store():
    return FirestoreStore() if os.getenv('RELAY_MODE') == 'cloud' else Store()


class WorkspaceTransaction:
    def __init__(self, db, tenant):
        self.db, self.tenant = db, tenant

    def get(self, kind, id, default=None):
        row = self.db.execute('SELECT data FROM records WHERE tenant=? AND kind=? AND id=?', (self.tenant, kind, id)).fetchone()
        return json.loads(row[0]) if row else default

    def list(self, kind):
        return [json.loads(r[0]) for r in self.db.execute('SELECT data FROM records WHERE tenant=? AND kind=? ORDER BY id', (self.tenant, kind))]

    def put(self, kind, id, data):
        self.db.execute('INSERT OR REPLACE INTO records VALUES(?,?,?,?)', (self.tenant, kind, id, json.dumps(data)))

    def delete(self, kind, id):
        self.db.execute('DELETE FROM records WHERE tenant=? AND kind=? AND id=?',(self.tenant,kind,id))

    def revision(self):
        return self.get('meta', 'additions', {'revision': 0})['revision']

    def advance(self):
        revision = self.revision() + 1
        self.put('meta', 'additions', {'revision': revision, 'schema': 1, 'updated_at': now()})
        for plan in self.list('plans'):
            if not plan.get('invalidated'):
                self.put('plan_history', plan['id'], plan)
                self.put('plans', plan['id'], dict(plan, invalidated=True))
        return revision
