"""Tenant-owned, expiring bounded chat history and idempotent remote run outcomes."""
import secrets
import time
from .domain import RelayError, digest, now

LIFETIME=7200
MAX_TURNS=8
RUN_SECONDS=90


def conversation(store, tenant, id=None):
    if id:
        record=store.get(tenant,'conversations',id)
        if record['expires']<=time.time() or record.get('closed'):
            raise RelayError('AUTH_REQUIRED','Conversation expired or reset. Start a new conversation.')
        return record
    id=secrets.token_hex(16)
    record=dict(id=id,created_at=now(),expires=time.time()+LIFETIME,turns=[],closed=False)
    store.put(tenant,'conversations',id,record,create=True)
    return record


def begin_run(store,tenant,conversation_id,request_id,message):
    c=conversation(store,tenant,conversation_id)
    key=digest([conversation_id,request_id])[:32]
    record=dict(id=key,conversation_id=c['id'],request_id=request_id,input_digest=digest(message),status='running',began=time.time())
    if not store.put(tenant,'agent_runs',key,record,create=True):
        previous=store.get(tenant,'agent_runs',key)
        if previous['input_digest']!=record['input_digest']:
            raise RelayError('ACCESS_DENIED','A request identifier cannot be reused for a different message.')
        return previous,False
    # Atomic durable conversation lease works across gateway instances.
    store.put(tenant,'conversation_leases',c['id'],dict(owner=None,until=0),create=True)
    lease=store.get(tenant,'conversation_leases',c['id'])
    if lease['until']>time.time() or not store.claim(tenant,'conversation_leases',c['id'],lease,dict(owner=key,until=time.time()+RUN_SECONDS+30)):
        store.put(tenant,'agent_runs',key,dict(record,status='failed',result=dict(status='failed',text='',reason='Another turn is still running. Retry with a new request after it finishes.')))
        raise RelayError('RUN_IN_PROGRESS','A turn is already running in this conversation.')
    return record,True


def classify_result(result):
    value=dict(result) if isinstance(result,dict) else {}
    text=value.get('text')
    status=value.get('status','unknown')
    if status not in ('complete','partial','failed','cancelled','unknown'):
        status='unknown'
    if not isinstance(text,str) or not text.strip():
        value.update(text='',status=status if status in ('unknown','cancelled') else 'failed',reason=value.get('reason') or 'No usable final answer was returned.')
    else:
        value['text']=text[:24000]
        value['status']=status
        if value.get('required_tool_failed') or value.get('external_effect_unverified'):
            value['status']='partial'
    return value


def finish_run(store,tenant,record,message,result):
    value=classify_result(result)
    latest=store.get(tenant,'agent_runs',record['id'])
    if latest.get('status')=='cancel_requested':
        value.update(status='unknown',reason='Client stopped waiting. Remote work may have continued; inspect evidence before retrying.',remote_compute_stopped=False)
    c=store.get(tenant,'conversations',record['conversation_id'])
    c['turns']=(c['turns']+[dict(user=message[:6000],assistant=value['text'],status=value['status'],run_id=record['id'])])[-MAX_TURNS:]
    store.put(tenant,'conversations',c['id'],c)
    store.put(tenant,'agent_runs',record['id'],dict(record,status=value['status'],result=value,finished_at=now()))
    store.claim(tenant,'conversation_leases',c['id'],{'owner':record['id']},{'owner':None,'until':0})
    return value


def availability(store, resource):
    if not resource:return dict(configured=False,verified=False,resource=None)
    try:e=store.get('_server','agent_evidence',digest(resource))
    except RelayError:return dict(configured=True,verified=False,resource=resource)
    return dict(configured=True,resource=resource,verified=e.get('resource')==resource and e.get('revision') not in (None,'unreported') and e.get('expires',0)>time.time(),evidence=e)
