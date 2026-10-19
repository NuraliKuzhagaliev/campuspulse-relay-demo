import base64,time,threading
from concurrent.futures import ThreadPoolExecutor
import httpx
from relay.connectors import GitHub
from relay import public_demo

def test_shared_singleflight_for_manual_mcp_and_background_read(monkeypatch):
    public_demo._public_cache.clear();GitHub._entity_cache.clear();GitHub._immutable_documents.clear()
    calls=[];real=httpx.Client
    def reply(request):
        calls.append(request.url.path)
        if '/commits/' in request.url.path:return httpx.Response(200,json={'sha':'b'*40,'commit':{'committer':{'date':'2026-10-19T12:00:00Z'}}})
        return httpx.Response(200,json={'size':22,'encoding':'base64','content':base64.b64encode(b'Assignment: Shared lab').decode(),'sha':'c'*40})
    monkeypatch.setattr('relay.connectors.httpx.Client',lambda **kw:real(transport=httpx.MockTransport(reply),**kw));monkeypatch.setattr(GitHub,'_public_backoff_until',0)
    with ThreadPoolExecutor(max_workers=10) as pool:values=list(pool.map(lambda _:GitHub('sample/cache-holdout').read('coursework.md'),range(30)))
    assert len(calls)==2 and len({v['fetched_at'] for v in values})==1 and len({v['commit'] for v in values})==1
    assert any(v['cache_age_seconds']>=0 for v in values)

def test_etag_304_preserves_original_immutable_fetch(monkeypatch):
    public_demo._public_cache.clear();GitHub._entity_cache.clear();GitHub._immutable_documents.clear()
    real=httpx.Client;requests=[]
    def reply(request):
        requests.append(request)
        if '/commits/' in request.url.path:
            if request.headers.get('if-none-match')=='"ref-1"':return httpx.Response(304)
            return httpx.Response(200,headers={'etag':'"ref-1"'},json={'sha':'d'*40,'commit':{'committer':{'date':'2026-10-19T12:00:00Z'}}})
        return httpx.Response(200,json={'size':19,'encoding':'base64','content':base64.b64encode(b'Assignment: Cached').decode(),'sha':'e'*40})
    monkeypatch.setattr('relay.connectors.httpx.Client',lambda **kw:real(transport=httpx.MockTransport(reply),**kw));monkeypatch.setattr(GitHub,'_public_backoff_until',0)
    first=GitHub('sample/etag-holdout').read('coursework.md');public_demo._public_cache.clear()
    second=GitHub('sample/etag-holdout').read('coursework.md')
    assert len(requests)==3 and second['immutable_content_cached'] and first['fetched_at']==second['fetched_at'] and second['ref_checked_at']
