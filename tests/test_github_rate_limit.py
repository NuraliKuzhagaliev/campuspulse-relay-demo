import time
import httpx
import pytest
from relay.connectors import GitHub
from relay.domain import RelayError


def test_public_quota_403_is_typed_and_prevents_repeated_requests(monkeypatch):
    actual_client=httpx.Client
    calls=[]
    def reply(request):
        calls.append(request)
        return httpx.Response(403,headers={'x-ratelimit-remaining':'0','x-ratelimit-reset':str(int(time.time()+600))},json={'message':'API rate limit exceeded'})
    monkeypatch.setattr('relay.connectors.httpx.Client',lambda **kwargs:actual_client(transport=httpx.MockTransport(reply),**kwargs))
    monkeypatch.setattr(GitHub,'_public_backoff_until',0)
    github=GitHub('owner/approved-demo')
    for _ in range(2):
        with pytest.raises(RelayError) as failure:
            github.status()
        assert failure.value.code=='UPSTREAM_RATE_LIMITED'
        assert failure.value.details['retry_at_epoch']>time.time()
    assert len(calls)==1
