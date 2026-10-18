"""Guardrails for the unaffiliated, temporary public illustrative demo.

This mode cannot load Google credentials or call a managed model. Anonymous
capability cookies authorize only their own temporary, isolated workspace.
"""
import os
import re
import threading
import time
from collections import OrderedDict
from .domain import RelayError


def enabled():
    return os.getenv('RELAY_MODE') == 'public_demo'


SESSION_SECONDS = 7200
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SOURCES = 12
_lock = threading.Lock()
_cache_lock = threading.Lock()
_buckets = OrderedDict()
_public_cache = {}


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


GET = re.compile(r'^/api/(session|health|state|events|sources/[A-Za-z0-9_-]+|packets/[a-f0-9]+|export)$')
POST = re.compile(r'^/api/(import|import-native|plan|scenario|preferences|sync|chat|demo/reset|tasks/[a-f0-9]+/settings|conflicts/[a-f0-9]+/resolve|plans/[a-f0-9]+/preview|previews/[a-f0-9]+/approve|receipts/[a-f0-9]+/(verify|undo))$')


def route_allowed(path, method):
    if path == '/' or path.startswith('/assets/') or path == '/robots.txt':
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
                db.execute('DELETE FROM records WHERE tenant=?', (tenant,))
                db.execute('DELETE FROM events WHERE tenant=?', (tenant,))
                db.execute("DELETE FROM records WHERE tenant='_server' AND kind='sessions' AND id=?", (session_id,))
                db.execute("DELETE FROM records WHERE tenant='_server' AND kind='workspaces' AND id=?", (tenant,))


def forget(store, tenant):
    import json
    with store.connect() as db:
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
            return dict(cached[1], cache_age_seconds=round(time.time() - cached[0], 2))
        value = loader()
        _public_cache.clear()
        _public_cache[key] = (time.time(), value)
        return dict(value, cache_age_seconds=0)
