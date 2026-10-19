"""Anonymous, tenant-bound AI jobs and quota-aware FIFO admission.

One outstanding job per capability workspace; bounded workers, no per-judge
codes or reserved seats. Each actual model call acquires a fair quota ticket.
No provider imitation or fallback is available through production endpoints.
"""
import asyncio
import os
import secrets
import time
from datetime import datetime,timedelta,time as daytime
from zoneinfo import ZoneInfo
from .domain import RelayError,digest,now

TERMINAL={'complete','partial','failed','unknown','cancelled'}
ACTIVE={'running','quota_wait','cancel_requested'}
provider_clock=time.time


def enabled():
    return os.getenv('RELAY_MODE')=='alternative_live' and os.getenv('RELAY_PUBLIC_AI_ENABLED')=='true'


def day_window(at):
    local=datetime.fromtimestamp(at,ZoneInfo('America/Los_Angeles'))
    end=datetime.combine(local.date()+timedelta(days=1),daytime.min,local.tzinfo).timestamp()
    return local.date().isoformat(),end


def limits():
    # Values are the account's observed limits, not an invented remaining balance.
    return dict(rpm=max(1,int(os.getenv('RELAY_MODEL_CALLS_PER_MINUTE','15'))),
                tpm=max(1,int(os.getenv('RELAY_MODEL_TOKENS_PER_MINUTE','250000'))),
                rpd=max(1,int(os.getenv('RELAY_MODEL_CALLS_PER_DAY','500'))))


def _capacity(value,at,tokens=5000):
    config=limits();day,end=day_window(at)
    minute=[r for r in value.get('minute',[]) if r['at']>at-60]
    counts={k:v for k,v in value.get('days',{}).items() if k>=day}
    value.update(minute=minute,days=counts)
    waits=[];reason=None
    if value.get('backoff_until',0)>at:waits.append(value['backoff_until']-at);reason='provider_backoff'
    if counts.get(day,0)>=config['rpd']:waits.append(end-at);reason='daily_quota'
    if len(minute)>=config['rpm']:waits.append(minute[0]['at']+60-at);reason=reason or 'minute_quota'
    excess=sum(r['tokens'] for r in minute)+tokens-config['tpm']
    for item in minute:
        if excess<=0:break
        waits.append(item['at']+60-at);excess-=item['tokens'];reason=reason or 'token_quota'
    wait=max([0,*waits])
    return dict(wait_seconds=max(0,round(wait,3)),reason=reason,reset_at=at+wait if wait else None,
                application_day_calls=counts.get(day,0),limits=config,quota_scope='project_limits_local_accounting_provider_authoritative')


class QuotaGate:
    def __init__(self,store,clock=None):self.store,self.clock=store,clock or provider_clock

    def inspect(self):
        at=self.clock()
        def read(tx):return _capacity(tx.get('public_ai_capacity','current',{}),at)
        return self.store.atomic('_server',read)

    def try_reserve(self,tenant,run_id,request_bytes):
        estimate=request_bytes+5000
        if estimate>min(110000,limits()['tpm']):
            raise RelayError('UNSUPPORTED_INPUT','This model context is too large. Start a new conversation or use a shorter permitted document.')
        at=self.clock();key=digest([tenant,run_id])
        def reserve(tx):
            value=tx.get('public_ai_capacity','current',{})
            for stale in tx.list('public_ai_waiters'):
                if stale['until']<=at:tx.delete('public_ai_waiters',stale['id'])
            ticket=tx.get('public_ai_waiters',key)
            if not ticket:
                seq=tx.get('public_ai_meta','tickets',{'next':0})['next']+1
                tx.put('public_ai_meta','tickets',{'next':seq})
                ticket=dict(id=key,tenant=tenant,run_id=run_id,sequence=seq,until=at+610)
                tx.put('public_ai_waiters',key,ticket)
            info=_capacity(value,at,estimate)
            first=min(tx.list('public_ai_waiters'),key=lambda r:r['sequence'])
            if first['id']!=key:
                info.update(wait_seconds=max(info['wait_seconds'],0.25),reason=info['reason'] or 'fair_turn')
            if info['wait_seconds']<=0:
                day,_=day_window(at);value['days'][day]=value['days'].get(day,0)+1
                value['minute'].append(dict(at=at,tokens=estimate))
                tx.delete('public_ai_waiters',key)
                info['reserved']=True
                info['reserved_at']=at
            else:info['reserved']=False
            tx.put('public_ai_capacity','current',value)
            return info
        result=self.store.atomic('_server',reserve)
        if result['reserved']:
            self.store.event(tenant,run_id,'model_call_reserved',estimated_max_tokens=estimate,
                             summary='Reserved an actual model call within the shared free project quota.')
        return result

    def abandon(self,tenant,run_id):
        self.store.atomic('_server',lambda tx:tx.delete('public_ai_waiters',digest([tenant,run_id])))

    def backoff(self,seconds=60,daily=False):
        at=self.clock()
        def update(tx):
            value=tx.get('public_ai_capacity','current',{})
            until=day_window(at)[1] if daily else at+max(1,min(86400,seconds))
            value['backoff_until']=max(value.get('backoff_until',0),until)
            tx.put('public_ai_capacity','current',value)
        self.store.atomic('_server',update)


class PublicQueue:
    def __init__(self,store,clock=None):self.store,self.clock=store,clock or provider_clock

    @staticmethod
    def key(tenant,run_id):return digest([tenant,run_id])

    def submit(self,tenant,body,expires):
        from .conversations import conversation,begin_run
        c=conversation(self.store,tenant,body['conversation_id'])
        run_id=digest([c['id'],body['request_id']])[:32]
        key=self.key(tenant,run_id);at=self.clock()
        def enqueue(tx):
            prior=tx.get('public_ai_jobs',key)
            if prior:
                if prior['input_digest']!=digest(body['message']):
                    raise RelayError('ACCESS_DENIED','A request identifier cannot be reused for different input.')
                return False
            owner=tx.get('public_ai_owners',tenant)
            if owner:raise RelayError('RUN_IN_PROGRESS','This workspace already has a queued or running question.')
            pending=[j for j in tx.list('public_ai_jobs') if j['status'] not in TERMINAL]
            if len(pending)>=256:raise RelayError('UPSTREAM_RATE_LIMITED','The shared queue is full. Your question has not been sent; retry later.')
            seq=tx.get('public_ai_meta','jobs',{'next':0})['next']+1
            tx.put('public_ai_meta','jobs',{'next':seq})
            tx.put('public_ai_jobs',key,dict(id=key,tenant=tenant,run_id=run_id,conversation_id=c['id'],
                message=body['message'],language=body['language'],input_digest=digest(body['message']),
                status='creating',sequence=seq,created_at=now(),expires=min(expires,c['expires']),began=at))
            tx.put('public_ai_owners',tenant,{'job':key})
            return True
        created=self.store.atomic('_server',enqueue)
        if created:
            try:
                begin_run(self.store,tenant,c['id'],body['request_id'],body['message'],queued_until=min(expires,c['expires']))
                self.store.claim('_server','public_ai_jobs',key,{'status':'creating'},{'status':'queued'})
                self.store.event(tenant,run_id,'run_queued',summary='Question joined the fair shared AI queue; no provider call yet.')
            except Exception:
                self.finish(tenant,run_id,dict(status='failed',text='',code='RUN_IN_PROGRESS',reason='Could not enqueue this conversation.'))
                raise
        return self.status(tenant,run_id)

    def status(self,tenant,run_id):
        job=self.store.get('_server','public_ai_jobs',self.key(tenant,run_id))
        if job['status'] in TERMINAL:return dict(job['result'],run_id=run_id,conversation_id=job['conversation_id'])
        pending=sorted([j for j in self.store.list('_server','public_ai_jobs') if j['status'] in ('creating','queued')],key=lambda j:j['sequence'])
        position=next((n+1 for n,j in enumerate(pending) if j['id']==job['id']),0)
        quota=QuotaGate(self.store,self.clock).inspect()
        return dict(status='queued' if job['status']=='creating' else job['status'],text='',run_id=run_id,
                    conversation_id=job['conversation_id'],position=position,quota=quota,
                    poll_after_ms=min(15000,3000+position*150),temporary_storage=True)

    def claim_next(self):
        self.expire()
        if QuotaGate(self.store,self.clock).inspect()['wait_seconds']>0:return None
        at=self.clock()
        def take(tx):
            pending=sorted([j for j in tx.list('public_ai_jobs') if j['status']=='queued'],key=lambda j:j['sequence'])
            if not pending:return None
            job=pending[0];job.update(status='running',started_at=at)
            tx.put('public_ai_jobs',job['id'],job)
            return job
        return self.store.atomic('_server',take)

    def expire(self):
        # Expire even when daily quota prevents dispatch. Drop queued text and
        # release its conversation lease without invoking the provider.
        at=time.time()
        for job in self.store.list('_server','public_ai_jobs'):
            if job['status'] not in TERMINAL and job['expires']<=at:
                self.finish(job['tenant'],job['run_id'],dict(status='cancelled',text='',code='AUTH_REQUIRED',
                    reason='The temporary session expired while queued.',remote_compute_stopped=False))

    def finish(self,tenant,run_id,result):
        from .conversations import classify_result,MAX_TURNS
        key=self.key(tenant,run_id)
        try:
            job=self.store.get('_server','public_ai_jobs',key)
            def complete(tx):
                record=tx.get('agent_runs',run_id)
                c=tx.get('conversations',job['conversation_id'])
                if not record or not c:raise RelayError('AUTH_REQUIRED','Workspace reset or expired.')
                if record['status'] in TERMINAL and record.get('result'):return record['result']
                value=classify_result(result)
                if record['status']=='cancel_requested':
                    value.update(status='unknown',reason='Client stopped waiting. Remote work may have continued; inspect evidence before retrying.',remote_compute_stopped=False)
                c['turns']=(c['turns']+[dict(user=job['message'][:6000],assistant=value['text'],status=value['status'],run_id=run_id)])[-MAX_TURNS:]
                tx.put('conversations',c['id'],c)
                tx.put('agent_runs',run_id,dict(record,status=value['status'],result=value,finished_at=now()))
                lease=tx.get('conversation_leases',c['id'],{})
                if lease.get('owner')==run_id:tx.put('conversation_leases',c['id'],dict(owner=None,until=0))
                return value
            result=self.store.atomic(tenant,complete)
        except RelayError:
            # A reset/expired workspace must never be recreated by a background result.
            result=dict(status='cancelled',text='',code='AUTH_REQUIRED',reason='The originating temporary workspace was reset or expired.')
        def done(tx):
            job=tx.get('public_ai_jobs',key)
            if job:
                job.update(status=result['status'],result=result,finished_at=now())
                job.pop('message',None)
                tx.put('public_ai_jobs',key,job)
            owner=tx.get('public_ai_owners',tenant)
            if owner and owner['job']==key:tx.delete('public_ai_owners',tenant)
        self.store.atomic('_server',done)
        QuotaGate(self.store,self.clock).abandon(tenant,run_id)
        return result

    def cancel(self,tenant,run_id):
        key=self.key(tenant,run_id)
        def request(tx):
            job=tx.get('public_ai_jobs',key)
            if not job:raise RelayError('ACCESS_DENIED','Record unavailable in this workspace.')
            previous=job['status']
            if previous not in TERMINAL:
                job['status']='cancel_requested';tx.put('public_ai_jobs',key,job)
            return previous
        previous=self.store.atomic('_server',request)
        if previous in TERMINAL:return dict(status=previous,remote_compute_stopped=previous!='unknown')
        if previous in ('queued','creating'):
            result=dict(status='cancelled',text='',reason='Cancelled before execution.',remote_compute_stopped=True)
            self.finish(tenant,run_id,result)
            return result
        self.store.claim(tenant,'agent_runs',run_id,{'status':'queued'},{'status':'cancel_requested'})
        self.store.claim(tenant,'agent_runs',run_id,{'status':'running'},{'status':'cancel_requested'})
        return dict(status='cancel_requested',remote_compute_stopped=False)

    def cancel_tenant(self,tenant):
        try:owner=self.store.get('_server','public_ai_owners',tenant)
        except RelayError:return
        job=self.store.get('_server','public_ai_jobs',owner['job']);self.cancel(tenant,job['run_id'])

    def recover(self):
        for job in self.store.list('_server','public_ai_jobs'):
            if job['status'] in ACTIVE or job['status']=='creating':
                self.finish(job['tenant'],job['run_id'],dict(status='unknown',text='',reason='The serving process restarted. No automatic replay; inspect the outcome before retrying.',remote_compute_stopped=False))


async def reserve_public_call(store,tenant,run_id,request_bytes):
    queue=PublicQueue(store);key=queue.key(tenant,run_id);gate=QuotaGate(store)
    while True:
        job=store.get('_server','public_ai_jobs',key)
        if job['status']=='cancel_requested' or job['expires']<=time.time():
            gate.abandon(tenant,run_id)
            raise RelayError('REQUEST_CANCELLED','This queued question was cancelled or expired.')
        store.get('_server','workspaces',tenant)
        info=gate.try_reserve(tenant,run_id,request_bytes)
        if info['reserved']:
            store.claim('_server','public_ai_jobs',key,{'status':'quota_wait'},{'status':'running'})
            return
        store.claim('_server','public_ai_jobs',key,{'status':'running'},{'status':'quota_wait'})
        await asyncio.sleep(min(2,max(0.05,info['wait_seconds'])))


def provider_backoff(store,exc):
    # Typed retry/quota metadata only. Never persist raw provider errors/prompts.
    data=getattr(exc,'response_json',{}) or {};seconds=60;daily=False
    if isinstance(data,dict):
        error=data.get('error',data)
        for item in error.get('details',[]) if isinstance(error,dict) else []:
            if not isinstance(item,dict):continue
            if 'retryDelay' in item:
                try:seconds=max(1,float(str(item['retryDelay']).rstrip('s')))
                except ValueError:pass
            for violation in item.get('violations',[]):
                metric=str(violation.get('quotaId',''))+str(violation.get('quotaMetric',''))
                daily |= 'perday' in metric.replace('_','').lower()
    QuotaGate(store).backoff(seconds,daily=daily)


async def worker(store,invoke,on_complete):
    """Small fixed worker pool; 100 waiting visitors do not create100 SDK threads."""
    from .conversations import conversation
    from .auth import sign_context
    from .providers import selected
    queue=PublicQueue(store)
    while True:
        job=await asyncio.to_thread(queue.claim_next)
        if not job:
            await asyncio.sleep(0.5)
            continue
        tenant,run=job['tenant'],job['run_id']
        try:
            if job['expires']<=time.time():raise RelayError('AUTH_REQUIRED','The temporary session expired while queued.')
            store.get('_server','workspaces',tenant)
            if not any(s['tenant']==tenant and s['expires']>time.time() for s in store.list('_server','sessions')):
                raise RelayError('AUTH_REQUIRED','The originating browser session expired or was reset.')
            history=conversation(store,tenant,job['conversation_id'])['turns']
            if not store.claim(tenant,'agent_runs',run,{'status':'queued'},{'status':'running'}):
                raise RelayError('REQUEST_CANCELLED','The queued request was cancelled.')
            store.event(tenant,run,'run_started',summary='Running a real Gemini question from the shared queue.')
            config=selected()
            token=sign_context(tenant,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'],seconds=max(1,min(600,int(job['expires']-time.time()))))
            result=await asyncio.wait_for(asyncio.to_thread(invoke,config['resource'],user_id=tenant,message=job['message'],
                context_token=token,language=job['language'],run_id=run,conversation_id=job['conversation_id'],history=history),timeout=605)
        except asyncio.TimeoutError:
            result=dict(status='unknown',text='',code='UPSTREAM_UNAVAILABLE',reason='The bounded remote run timed out. Inspect events before retrying.',remote_compute_stopped=False)
        except Exception as exc:
            code=getattr(exc,'code',None)
            if code in (429,'RESOURCE_EXHAUSTED','UPSTREAM_RATE_LIMITED'):
                provider_backoff(store,exc)
                result=dict(status='failed',text='',code='UPSTREAM_RATE_LIMITED',reason='Provider quota reached. The queue will wait for its reset; this turn is not silently replayed.')
            elif code=='REQUEST_CANCELLED':
                result=dict(status='cancelled',text='',code=code,reason='Question cancelled before another model call.',remote_compute_stopped=False)
            else:
                result=dict(status='failed',text='',code=code if isinstance(code,str) else 'UPSTREAM_UNAVAILABLE',reason='The selected free Gemini route could not complete this turn. No fallback was used.')
            # Type and numeric status only: provider exception strings can contain
            # document text or credentials and must never enter events/results.
            result['failure_type']=type(exc).__name__[:80]
            if isinstance(code,int):result['upstream_status']=code
        result['gateway_revision']=os.getenv('RELAY_DEPLOYED_COMMIT') or os.getenv('RENDER_GIT_COMMIT') or os.getenv('RELAY_BUILD_REVISION')
        result=await asyncio.to_thread(queue.finish,tenant,run,result)
        on_complete(tenant,run,result)
