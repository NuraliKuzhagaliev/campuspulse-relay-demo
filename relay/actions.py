import secrets
from datetime import datetime, timedelta, timezone
from .domain import RelayError, digest, instant, now
from .connectors import busy_intervals


def normalized(event):
    return dict(summary=event.get('summary'),description=event.get('description',''),
                start=instant(event['start']['dateTime']).isoformat(),
                end=instant(event['end']['dateTime']).isoformat(),
                private=event.get('extendedProperties',{}).get('private',{}),
                attendees=event.get('attendees',[]),status=event.get('status','confirmed'))


def calendar_fingerprint(events):
    return digest(sorted([dict(id=e['id'],etag=e.get('etag'),status=e.get('status'),start=e.get('start'),end=e.get('end')) for e in events],key=lambda e:e['id']))


def unchanged_owned_ids(events,operations,tenant):
    owned=set()
    for event in events:
        if event.get('extendedProperties',{}).get('private',{}).get('relay_workspace')!=tenant:
            continue
        for op in operations:
            if op.get('operation','create')!='delete' and op['event_id']==event['id'] and op.get('status')=='verified':
                if normalized(event)==normalized(op['expected']) and event.get('etag')==op.get('verified',{}).get('etag'):
                    owned.add(event['id'])
                    break
    return owned


class Actions:
    def __init__(self,store,tenant,calendar,source_versions):
        self.store,self.tenant,self.calendar,self.source_versions=store,tenant,calendar,source_versions

    def preview(self,plan):
        if not plan['feasible'] or plan.get('invalidated'):
            raise RelayError('INFEASIBLE','Only a current feasible plan can be approved.')
        if plan.get('sources')!=self.source_versions():
            raise RelayError('STALE_PLAN','Sources or conflict decisions changed; repair the plan again.')
        windows=plan['input']['windows']
        a=min(w['start'] for w in windows)
        z=max(w['end'] for w in windows)
        events=self.calendar.list(a,z)
        owned=unchanged_owned_ids(events,self.store.list(self.tenant,'operations'),self.tenant)
        busy=busy_intervals(events,plan['input']['timezone'],exclude_ids=owned)
        for block in plan['blocks']:
            if any(instant(block['start'])<instant(b['end']) and instant(b['start'])<instant(block['end']) for b in busy):
                raise RelayError('STALE_PLAN','Calendar availability changed; refresh and repair before preview.')
        tasks={t['id']:t for t in plan['input']['tasks']}
        actions=[]
        existing={e['id']:e for e in events}
        desired=set()
        for b in plan['blocks']:
            id=digest([self.tenant,b['task_id'],b['start'],b['end']])[:40] # hex is valid base32hex
            desired.add(id)
            event=dict(id=id,summary=f"Study · {tasks[b['task_id']]['title']}",
                       description=f"CampusPulse RELAY | {plan['id']} | planned study, not submission or proof of learning",
                       start={'dateTime':b['start'],'timeZone':plan['input']['timezone']},
                       end={'dateTime':b['end'],'timeZone':plan['input']['timezone']},
                       extendedProperties={'private':{'relay_workspace':self.tenant,'relay_plan':plan['id'],'relay_task':b['task_id']}},
                       reminders={'useDefault':False})
            if id in existing:
                if id not in owned:
                    raise RelayError('SOURCE_CONFLICT','A matching event was edited or is not owned; preserve it and replan.')
                actions.append(dict(operation='keep',event=existing[id]))
            else:
                actions.append(dict(operation='create',event=event))
        for id in sorted(owned-desired):
            actions.append(dict(operation='delete',event=existing[id]))
        preview=dict(id=secrets.token_hex(16),plan_id=plan['id'],calendar_id=self.calendar.id,mode=self.calendar.mode,
                     sources=self.source_versions(),calendar_fingerprint=calendar_fingerprint(events),window={'start':a,'end':z},
                     actions=actions,created_at=now(),expires_at=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat())
        preview['digest']=digest(preview)
        self.store.put(self.tenant,'previews',preview['id'],preview,create=True)
        return preview

    def authorize(self,preview_id,action_digest,user):
        preview=self.store.get(self.tenant,'previews',preview_id)
        if preview['digest']!=action_digest or instant(preview['expires_at'])<datetime.now(timezone.utc):
            raise RelayError('STALE_PLAN','The exact preview expired or changed; preview again.')
        if user!=self.tenant:
            raise RelayError('ACCESS_DENIED','Approval identity does not own this workspace.')
        # Unique key makes double-clicking the same immutable preview return the same durable authorization.
        approval=dict(id=preview_id,preview_id=preview_id,digest=action_digest,user=user,status='approved',expires_at=preview['expires_at'])
        self.store.put(self.tenant,'approvals',preview_id,approval,create=True)
        return preview_id

    def apply(self,approval_id):
        approval=self.store.get(self.tenant,'approvals',approval_id)
        preview=self.store.get(self.tenant,'previews',approval['preview_id'])
        if approval.get('user')!=self.tenant or approval.get('digest')!=preview['digest'] or preview['calendar_id']!=self.calendar.id:
            raise RelayError('APPROVAL_REQUIRED','No matching authenticated approval for this write set.')
        if approval['status']=='complete':
            return self.store.get(self.tenant,'receipts',approval_id)
        if instant(approval['expires_at'])<datetime.now(timezone.utc):
            raise RelayError('STALE_PLAN','Approval expired; generate a fresh preview.')
        if self.source_versions()!=preview['sources']:
            raise RelayError('STALE_PLAN','Source versions changed after preview.')
        journal=self.store.list(self.tenant,'operations')
        own_ids={o['event_id'] for o in journal if o['approval_id']==approval_id}
        events=self.calendar.list(**preview['window'])
        original=[e for e in events if e['id'] not in own_ids]
        expected=preview['calendar_fingerprint']
        # On retries ignore only the exact events durably journaled by this approval.
        if not own_ids and calendar_fingerprint(events)!=expected:
            raise RelayError('STALE_PLAN','Calendar changed after preview; approval was not applied.')
        if own_ids:
            original_at_start=self.store.get(self.tenant,'apply_state',approval_id)['original_events']
            if calendar_fingerprint(original)!=calendar_fingerprint([e for e in original_at_start if e['id'] not in own_ids]):
                raise RelayError('STALE_PLAN','External calendar changed while reconciling a partial apply.')
        self.store.put(self.tenant,'apply_state',approval_id,dict(original_events=events),create=True)
        acquired=self.store.claim(self.tenant,'approvals',approval_id,{'status':'approved'}, {'status':'applying','lease_until':(datetime.now(timezone.utc)+timedelta(seconds=90)).isoformat()})
        if not acquired:
            latest=self.store.get(self.tenant,'approvals',approval_id)
            if latest['status']=='complete':
                return self.store.get(self.tenant,'receipts',approval_id)
            if latest['status']=='applying' and instant(latest.get('lease_until',now()))<datetime.now(timezone.utc):
                acquired=self.store.claim(self.tenant,'approvals',approval_id,{'status':'applying','lease_until':latest['lease_until']},{'status':'applying','lease_until':(datetime.now(timezone.utc)+timedelta(seconds=90)).isoformat()})
            if not acquired:
                raise RelayError('PARTIAL_APPLY','Apply is already running; poll the receipt before retrying.')
        run='apply-'+approval_id
        self.store.event(self.tenant,run,'run_started',summary='Applying the approved write set.',mode=self.calendar.mode)
        outcomes=[]
        for action in preview['actions']:
            event=action['event']
            oid=digest([approval_id,event['id']])[:40]
            operation=action['operation']
            op=dict(id=oid,approval_id=approval_id,event_id=event['id'],expected=event,status='pending',operation=operation)
            self.store.put(self.tenant,'operations',oid,op,create=True)
            try:
                if operation=='create':
                    self.calendar.insert(event)
                elif operation=='delete':
                    try:
                        current=self.calendar.get(event['id'])
                        if current.get('status')!='cancelled':
                            if normalized(current)!=normalized(event) or current.get('etag')!=event.get('etag'):
                                raise RelayError('SOURCE_CONFLICT','An event changed after preview; it was preserved.')
                            self.calendar.delete(event['id'],event.get('etag'))
                    except RelayError as exc:
                        if exc.code!='NOT_FOUND':
                            raise
                self.store.event(self.tenant,run,'action_applied',event_id=event['id'],summary=event['summary'])
                try:
                    actual=self.calendar.get(event['id'])
                    ok=actual.get('status')=='cancelled' if operation=='delete' else normalized(actual)==normalized(event)
                except RelayError as exc:
                    if operation=='delete' and exc.code=='NOT_FOUND':
                        actual={'status':'cancelled'};ok=True
                    else:
                        raise
                outcome=dict(event_id=event['id'],operation=operation,status='verified' if ok else 'mismatch',url=actual.get('htmlLink'),verified_at=now(),observed=actual.get('status') if operation=='delete' else normalized(actual),etag=actual.get('etag'))
                op.update(status=outcome['status'],verified=outcome)
                self.store.event(self.tenant,run,'action_verified' if ok else 'run_failed',event_id=event['id'],summary='External read-back matches.' if ok else 'Read-back differs; not verified.',mode=self.calendar.mode)
            except RelayError as exc:
                outcome=dict(event_id=event['id'],operation=operation,status='unknown' if exc.code=='UPSTREAM_UNAVAILABLE' else 'failed',error=exc.as_dict())
                op.update(status=outcome['status'])
            self.store.put(self.tenant,'operations',oid,op)
            outcomes.append(outcome)
        complete=all(o['status']=='verified' for o in outcomes)
        receipt=dict(id=approval_id,plan_id=preview['plan_id'],calendar_id=self.calendar.id,mode=self.calendar.mode,
                     status='verified' if complete else 'partial',outcomes=outcomes,created_at=now(),digest=preview['digest'])
        self.store.put(self.tenant,'receipts',approval_id,receipt)
        self.store.claim(self.tenant,'approvals',approval_id,{'status':'applying'},{'status':'complete' if complete else 'approved'})
        self.store.event(self.tenant,run,'run_completed' if complete else 'run_failed',summary='All actions verified.' if complete else 'Some operations need reconciliation.',mode=self.calendar.mode)
        return receipt

    def verify(self,receipt_id):
        receipt=self.store.get(self.tenant,'receipts',receipt_id)
        operations=[o for o in self.store.list(self.tenant,'operations') if o['approval_id']==receipt_id]
        results=[]
        for op in operations:
            try:
                actual=self.calendar.get(op['event_id'])
                matches=actual.get('status')=='cancelled' if op.get('operation')=='delete' else normalized(actual)==normalized(op['expected'])
                results.append(dict(event_id=op['event_id'],matches=matches,verified_at=now(),url=actual.get('htmlLink')))
            except RelayError as exc:
                results.append(dict(event_id=op['event_id'],matches=op.get('operation')=='delete' and exc.code=='NOT_FOUND',error=exc.as_dict()))
        return dict(receipt_id=receipt_id,mode=receipt['mode'],results=results)

    def undo(self,receipt_id):
        self.store.get(self.tenant,'receipts',receipt_id)
        results=[]
        for op in self.store.list(self.tenant,'operations'):
            if op['approval_id']!=receipt_id:
                continue
            if op.get('operation')=='keep':
                results.append(dict(event_id=op['event_id'],status='preserved_existing'))
                continue
            if op.get('operation')=='delete':
                results.append(dict(event_id=op['event_id'],status='restore_requires_preview',message='Deleted prior blocks require a fresh conflict-checked preview to restore.'))
                continue
            try:
                actual=self.calendar.get(op['event_id'])
                if actual.get('status')=='cancelled':
                    results.append(dict(event_id=op['event_id'],status='already_removed'))
                    continue
                verified=op.get('verified',{})
                if normalized(actual)!=normalized(op['expected']) or actual.get('etag')!=verified.get('etag'):
                    raise RelayError('SOURCE_CONFLICT','Event was edited; preserved.')
                self.calendar.delete(op['event_id'],actual.get('etag'))
                results.append(dict(event_id=op['event_id'],status='removed'))
            except RelayError as exc:
                results.append(dict(event_id=op['event_id'],status='preserved',error=exc.as_dict()))
        return dict(receipt_id=receipt_id,mode=self.calendar.mode,results=results)
