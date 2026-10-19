"""Explicit temporary free-host mode with opt-in anonymous queued AI access."""
import os
from urllib.parse import urlparse
from .domain import RelayError


def enabled():
    return os.getenv('RELAY_MODE') == 'alternative_live'


def configuration():
    from .providers import selected
    value = selected()
    if not value['configured'] or not os.getenv('RELAY_GEMINI_API_KEY') or os.getenv('RELAY_GEMINI_FREE_ONLY')!='true':
        raise RuntimeError('Alternative live startup requires an owner-authorized free-tier key. No paid fallback is permitted.')
    for key in ('RELAY_CONTEXT_SECRET', 'RELAY_MCP_SERVICE_SECRET'):
        if len(os.getenv(key, '')) < 32:
            raise RuntimeError('Alternative live startup requires distinct strong server-side transport and workspace secrets.')
    if os.environ['RELAY_CONTEXT_SECRET'] == os.environ['RELAY_MCP_SERVICE_SECRET']:
        raise RuntimeError('Machine transport and workspace signing secrets must be distinct.')
    url = urlparse(os.getenv('RELAY_MCP_URL', ''))
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.path != '/_relay/mcp/':
        raise RuntimeError('Alternative host MCP must use the protected same-process loopback endpoint.')
    if not os.getenv('RELAY_GITHUB_REPO'):
        raise RuntimeError('Configure the approved public demo repository.')


def route_allowed(path, method):
    if path=='/internal/managed-route':return method=='POST'
    if path=='/internal/runtime-state':return method=='POST'
    if path.rstrip('/')=='/managed/mcp':return method in ('POST','GET','DELETE')
    if method=='GET' and path in ('/api/auth/start','/connect','/auth/callback','/api/connections/calendar-list','/api/connections/status'):return True
    if method=='POST' and path in ('/api/auth/poll','/api/auth/pair/approve','/api/connections/calendar','/api/connections/calendar/create','/api/connections/disconnect'):return True
    from .public_ai import enabled as public_access
    if public_access() and path in ('/internal/ai-invitations','/api/judge/claim'):
        return False
    from .public_demo import route_allowed as illustrative_route
    if path.startswith('/_relay/'):
        return path.rstrip('/') == '/_relay/mcp' and method in ('POST', 'GET', 'DELETE')
    if path == '/internal/ai-invitations':
        return method == 'POST'
    import re
    return illustrative_route(path, method) or (path == '/api/judge/claim' and method == 'POST') or (public_access() and method=='GET' and bool(re.fullmatch(r'/api/runs/[a-f0-9]{32}',path)))


def authorize_query(settings, adult_confirmed, permitted_processing, region='KZ'):
    from .public_ai import enabled as public_access
    if not public_access() and not settings.get('ai_access') and settings.get('mode') != 'judge':
        raise RelayError('AUTH_REQUIRED', 'A private owner-issued AI invitation is required. Public illustrative tools remain available.')
    if not adult_confirmed or not permitted_processing or region not in ('KZ','supported_non_eea'):
        raise RelayError('PROCESSING_CONSENT_REQUIRED', 'Free Gemini requires an adult user and permitted non-sensitive documents. Unpaid inputs may be used for product improvement and human review. Do not send personal or confidential coursework.')
