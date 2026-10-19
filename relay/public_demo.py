"""Guardrails for the unaffiliated, temporary public illustrative demo.

This mode cannot load Google credentials or call a managed model. Anonymous
capability cookies authorize only their own temporary, isolated workspace.
"""
import os
import re
import threading
import time
import copy
from collections import OrderedDict
from .domain import RelayError


def enabled():
    return os.getenv('RELAY_MODE') == 'public_demo'


def temporary_enabled():
    return os.getenv('RELAY_MODE') in ('public_demo', 'alternative_live')


SESSION_SECONDS = 7200
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SOURCES = 12
_lock = threading.Lock()
_cache_lock = threading.Lock()
_buckets = OrderedDict()
_public_cache = OrderedDict()


def limit(scope, operation, count, seconds=60):
    """Bounded in-memory fixed windows; no IPs, cookies or payloads in logs."""
    tick = int(time.time() // seconds)
    key = (scope, operation, tick)
    with _lock:
        while len(_buckets) >= 2048:
            _buckets.popitem(last=False)
        used = _buckets.get(key, 0)
        if used >= count:
            raise RelayError('UPSTREAM_RATE_LIMITED', 'The public demo request allowance is exhausted. Retry after the window resets.')
        _buckets[key] = used + 1
        _buckets.move_to_end(key)


GET = re.compile(r'^/api/(session|health|state|events|conversation|challenge|additions|tasks/[a-f0-9]+/estimate-suggestion|sources/[A-Za-z0-9_-]+|packets/[a-f0-9]+|export)$')
POST = re.compile(r'^/api/(import|import-native|tasks/[a-f0-9]+/progress|work-sessions/[a-f0-9]+/heartbeat|progress/preview|progress/[a-f0-9]+/adopt|clarify|clarify/[a-f0-9]+/(cancel|answer)|gates|gates/notifications/[a-f0-9]+/claim|gates/conditional-preview|gates/[a-f0-9]+/(observe|remove)|passport/(export|preview)|passport/[a-f0-9]+/restore|plan|scenario|preferences|sync|chat|conversation/new|runs/[a-f0-9]+/cancel|rescue|rescues/[a-f0-9]+/choose|preflight|preflights/[a-f0-9]+/recovery|demo/reset|sources/[A-Za-z0-9_-]+/mapping|tasks/[a-f0-9]+/settings|conflicts/[a-f0-9]+/resolve|plans/[a-f0-9]+/preview|previews/[a-f0-9]+/approve|receipts/[a-f0-9]+/(verify|undo))$')


def route_allowed(path, method):
    if method=='GET' and path=='/api/extraction-proposals':return True
    if method=='POST' and re.fullmatch(r'/api/sources/[A-Za-z0-9_-]+/review',path):return True
    if method=='POST' and (path in ('/api/workspace/switch','/api/planning-context') or re.fullmatch(r'/api/extraction-proposals/[a-f0-9]{24}/[a-f0-9]{24}/confirm',path)):return True
    if path == '/' or path.startswith('/assets/') or path.startswith('/samples/') or path == '/robots.txt':
        return method in ('GET', 'HEAD')
    if method == 'GET':
        return bool(GET.fullmatch(path))
    if method == 'POST':
        return bool(POST.fullmatch(path))
    return method == 'DELETE' and path == '/api/workspace'


def configuration():
    forbidden = ('RELAY_AGENT_RESOURCE', 'GOOGLE_CLOUD_PROJECT', 'RELAY_OAUTH_CLIENT_ID',
                 'RELAY_OAUTH_CLIENT_SECRET', 'RELAY_TOKEN_ENCRYPTION_KEY', 'RELAY_MCP_URL')
    if any(os.getenv(key) for key in forbidden):
        raise RuntimeError('Public demo refuses managed-agent, GCP or Google OAuth credentials/configuration.')


def metadata():
    return dict(public=True, storage='temporary', session_seconds=SESSION_SECONDS,
                max_upload_mib=2, max_sources=MAX_SOURCES, github_cache_seconds=300,
                calendar='illustrative_local_adapter', gemini='pending', mandatory_gcp='pending')


def _forget_ai_jobs(db,tenant):
    # Same SQLite transaction as the workspace deletion. Retain no uploaded
    # excerpts or model answers in the global queue after a reset/expiry.
    db.execute("DELETE FROM records WHERE tenant='_server' AND kind IN ('public_ai_jobs','public_ai_waiters') AND json_extract(data,'$.tenant')=?",(tenant,))
    db.execute("DELETE FROM records WHERE tenant='_server' AND kind='public_ai_owners' AND id=?",(tenant,))


def cleanup(store, at=None):
    """Delete expired public documents and their capability sessions together."""
    at = at or time.time()
    with store.connect() as db:
        rows = db.execute("SELECT id,data FROM records WHERE tenant='_server' AND kind='sessions'").fetchall()
        import json
        for session_id, raw in rows:
            session = json.loads(raw)
            tenant = session.get('tenant', '')
            if tenant.startswith('demo-') and session['expires'] < at:
                _forget_ai_jobs(db,tenant)
                db.execute('DELETE FROM records WHERE tenant=?', (tenant,))
                db.execute('DELETE FROM events WHERE tenant=?', (tenant,))
                db.execute("DELETE FROM records WHERE tenant='_server' AND kind='sessions' AND id=?", (session_id,))
                db.execute("DELETE FROM records WHERE tenant='_server' AND kind='workspaces' AND id=?", (tenant,))


def forget(store, tenant):
    import json
    with store.connect() as db:
        _forget_ai_jobs(db,tenant)
        for session_id, raw in db.execute("SELECT id,data FROM records WHERE tenant='_server' AND kind='sessions'").fetchall():
            if json.loads(raw).get('tenant') == tenant:
                db.execute("DELETE FROM records WHERE tenant='_server' AND kind='sessions' AND id=?", (session_id,))
        db.execute('DELETE FROM records WHERE tenant=?', (tenant,))
        db.execute('DELETE FROM events WHERE tenant=?', (tenant,))
        db.execute("DELETE FROM records WHERE tenant='_server' AND kind='workspaces' AND id=?", (tenant,))


def read_public_source(repo, ref, path, loader):
    # Only immutable observations from the one public demo repository are cached.
    # Preserve original fetched_at/commit; never relabel cached data as a fresh read.
    key = (repo, ref, path)
    with _cache_lock:
        cached = _public_cache.get(key)
        if cached and time.time() - cached[0] < 300:
            return dict(copy.deepcopy(cached[1]), cache_age_seconds=round(time.time() - cached[0], 2))
        value = loader()
        while len(_public_cache)>=64:_public_cache.popitem(last=False)
        _public_cache[key] = (time.time(), value)
        return dict(copy.deepcopy(value), cache_age_seconds=0)
