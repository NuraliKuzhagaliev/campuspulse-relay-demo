"""Durable configurable request budgets. Billing alerts are not a hard spend cap."""
import os
import time
from .domain import RelayError


def consume(store,scope,kind,window,limit):
    id=f'{kind}-{int(time.time()//window)}'
    store.put(scope,'rate_limits',id,{'count':0},create=True)
    for _ in range(5):
        record=store.get(scope,'rate_limits',id)
        if record['count']>=limit:
            raise RelayError('UPSTREAM_RATE_LIMITED','This workspace reached its configured request allowance. Try after the window resets or ask the owner to adjust judge capacity.')
        if store.claim(scope,'rate_limits',id,{'count':record['count']},{'count':record['count']+1}):
            return
    raise RelayError('UPSTREAM_RATE_LIMITED','Concurrent request limit reached. Retry shortly.')


def model_request(store,tenant,judge=False):
    consume(store,tenant,'minute',60,int(os.getenv('RELAY_REQUESTS_PER_MINUTE','8')))
    consume(store,tenant,'day',86400,int(os.getenv('RELAY_REQUESTS_PER_USER_DAY','100')))
    total=int(os.getenv('RELAY_REQUESTS_TOTAL_DAY','300'))
    reserve=max(0,min(total,int(os.getenv('RELAY_JUDGE_RESERVED_REQUESTS','100'))))
    if not judge:
        consume(store,'_server','personal-model-day',86400,max(0,total-reserve))
    consume(store,'_server','model-day',86400,total)
