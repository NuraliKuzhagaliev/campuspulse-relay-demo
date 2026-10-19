import copy
import os
import time as clock
import uuid
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from .actions import Actions,unchanged_owned_ids
from .domain import RelayError, digest, now, instant, Task
from .evidence import read_upload, extract_facts, conflicts
from .scheduler import build_recovery_plan, compare_plan_scenarios
from .connectors import GitHub, GoogleCalendar, LocalCalendar, busy_intervals
from . import public_demo
from .identity import assignment_id, canonical, section_key
from .conversations import availability


class RelayService:
    def __init__(self,store,tenant):
        self.store,self.tenant=store,tenant

    def settings(self):
        try:
            value=self.store.get(self.tenant,'meta','settings')
        except RelayError:
            if os.getenv('RELAY_MODE')=='cloud':
                raise RelayError('AUTH_REQUIRED','Create or connect an isolated workspace first.')
            self.seed()
            return self.store.get(self.tenant,'meta','settings')
        if value.get('mode') in ('judge','judge_ai') and value.get('judge_expires',0)<clock.time():
            raise RelayError('AUTH_REQUIRED','This judge workspace has expired. Its calendar is retired and is never reassigned to another visitor.')
        return value

    def seed(self,anchor=None):
        if os.getenv('RELAY_MODE')=='cloud':
            raise RelayError('ACCESS_DENIED','Local fixtures are disabled in cloud mode.')
        zone=ZoneInfo('Asia/Almaty')
        today=datetime.now(zone).date()
        monday=datetime.fromisoformat(anchor).date() if anchor else today+timedelta(days=(7-today.weekday())%7)
        def at(day,hour):
            return datetime.combine(monday+timedelta(days=day),time(hour),zone).isoformat()
        sources=[('security-pdf','Network Security · original brief','Network Security lab',at(3,18),240,['Explain the threat model','Capture test evidence','Document mitigations']),
                 ('security-repo','Network Security · revised repo','Network Security lab',at(2,18),240,['Explain the threat model','Capture test evidence','Document mitigations']),
                 ('ml-brief','Machine Learning · report brief','ML report',at(4,18),180,['State the experiment','Compare baseline metrics','Discuss limitations']),
                 ('web-brief','Web Engineering · project brief','Web project',at(4,20),120,['Implement the interface','Show responsive states','Include setup instructions'])]
        for id,name,title,due,minutes,rubric in sources:
            text=f'Assignment: {title}\nCourse: {name.split(" ·")[0]}\nDue: {due}\nEffort: {minutes} minutes\nRubric:\n'+'\n'.join('- [ ] '+r for r in rubric)
            from pathlib import Path
            pdf=Path(__file__).parent.parent/'fixtures/network-security-original.pdf'
            if id=='security-pdf' and monday.isoformat()=='2026-10-19' and pdf.exists():
                self.import_source('network-security-original.pdf',pdf.read_bytes(),id=id,mode='illustrative',title=name)
            else:
                self.import_source(name+'.md',text.encode(),id=id,mode='illustrative',title=name)
        windows=[dict(start=at(d,a),end=at(d,b)) for d,a,b in [(0,18,20),(1,18,20),(2,16,18),(3,16,19),(4,16,17)]]
        settings=dict(mode='illustrative',timezone='Asia/Almaty',anchor=monday.isoformat(),windows=windows,daily_cap_minutes=240,
                      calendar_id='local-illustrative-calendar',github_repo=os.getenv('RELAY_GITHUB_REPO','NuraliKuzhagaliev/campuspulse-relay-demo'),github_ref='main',github_path='coursework.md',watch_enabled=False,calendar_live=False)
        self.store.put(self.tenant,'meta','settings',settings)
        self.store.put(self.tenant,'calendar','protected-commitment',dict(id='protected-commitment',summary='Protected commitment',start={'dateTime':at(1,18)},end={'dateTime':at(1,19)},etag='fixture-1',pinned=True))
        self.store.event(self.tenant,'seed-'+uuid.uuid4().hex,'run_completed',summary='Illustrative workspace loaded. No Gemini or external Calendar calls.',mode='illustrative')

    def calendar(self):
        s=self.settings()
        if public_demo.enabled() and s.get('calendar_live'):
            raise RelayError('ACCESS_DENIED','Real Calendar operations are disabled in the public illustrative demo.')
        if s.get('calendar_live'):
            if s.get('mode')=='personal':
                from .oauth import credentials
                return GoogleCalendar(s['calendar_id'],credentials(self.store,self.tenant))
            return GoogleCalendar(s['calendar_id'])
        if os.getenv('RELAY_MODE')=='cloud':
            raise RelayError('AUTH_REQUIRED','Select and authorize your study calendar before live planning.')
        return LocalCalendar(self.store,self.tenant)

    def source_versions(self):
        versions={s['id']:s['version'] for s in self.sources()}
        versions['_identity']=digest(self.store.list(self.tenant,'assignment_mappings'))
        versions['_resolutions']=digest(self.store.list(self.tenant,'resolutions'))
        versions['_settings']=digest(self.settings())
        versions['_task_overrides']=digest(self.store.list(self.tenant,'task_overrides'))
        versions['_progress']=digest(self.store.list(self.tenant,'progress'))
        versions['_gates']=digest(self.store.list(self.tenant,'gates'))
        from .progress import revision
        versions['_workspace_revision']=revision(self)
        return versions

    def import_source(self,name,content,id=None,mode='selected_upload',title=None,remote=None):
        parsed=read_upload(name,content)
        if public_demo.temporary_enabled() and parsed['type']=='ics' and len(self.store.list(self.tenant,'calendar'))+len(parsed['events'])>100:
            raise RelayError('UNSUPPORTED_INPUT','Use at most 100 calendar events in this temporary demo.')
        if parsed['type']=='ics':
            for event in parsed['events']:
                self.store.put(self.tenant,'calendar','ics-'+digest(event)[:24],dict(id='ics-'+digest(event)[:24],summary=event['title'],start={'dateTime':event['start']},end={'dateTime':event['end']},etag=digest(event),origin='ics_import'))
            return dict(type='ics',imported=len(parsed['events']),mode='imported_snapshot')
        same=[s for s in self.store.list(self.tenant,'sources') if s['content_hash']==parsed['content_hash']]
        if same and (id is None or same[0]['id']==id):
            return dict(same[0],duplicate=True)
        id=id or digest([name,parsed['content_hash']])[:24]
        if public_demo.temporary_enabled() and id not in {s['id'] for s in self.sources()} and len(self.sources())>=public_demo.MAX_SOURCES:
            raise RelayError('UNSUPPORTED_INPUT','This temporary demo reached its source limit. Start a fresh demo to import more.')
        source=dict(**parsed,id=id,title=title or name,filename=name,version=parsed['content_hash'][:24],mode=mode,timezone='Asia/Almaty',remote=remote,observed_monotonic_ns=clock.monotonic_ns())
        if remote and remote.get('fetched_at'):
            source['fetched_at']=remote['fetched_at']
        source['identity_schema']=2
        source['assignment_mappings']=self.source_mappings(source)
        facts,drafts=extract_facts(source)
        source['facts'],source['drafts']=facts,drafts
        self.store.put(self.tenant,'source_versions',id+'-'+source['version'],source,create=True)
        self.store.put(self.tenant,'sources',id,source)
        impacted={t['id'] for t in drafts}
        for plan in self.store.list(self.tenant,'plans'):
            if any(id in t.get('source_ids',[]) or t['id'] in impacted for t in plan['input']['tasks']):
                plan['invalidated']=True
                self.store.put(self.tenant,'plans',plan['id'],plan)
        return source

    def sources(self):
        self.migrate_identity()
        return self.store.list(self.tenant,'sources')

    def source_mappings(self, source):
        mappings={m['section_key']:m for m in self.store.list(self.tenant,'assignment_mappings') if m['source_id']==source['id']}
        # Explicitly owned fixture mapping, never applied to arbitrary uploads or repositories.
        owned=source['id'] in ('security-pdf','security-repo','ml-brief','web-brief') and source.get('mode')=='illustrative'
        owned=owned or (source['id']=='github-coursework' and (source.get('remote') or {}).get('repo')=='NuraliKuzhagaliev/campuspulse-relay-demo')
        if owned:
            for title,course in [('Network Security lab','Network Security'),('ML report','Machine Learning'),('Web project','Web Engineering')]:
                key=section_key(title)
                mappings.setdefault(key,dict(id=assignment_id(course,'Illustrative 2026-10',title),course=course,term='Illustrative 2026-10',assignment_key=title,status='confirmed',origin='owned_fixture_mapping'))
        return mappings

    def migrate_identity(self):
        legacy=[s for s in self.store.list(self.tenant,'sources') if s.get('identity_schema')!=2]
        if not legacy:
            return
        aliases={}
        for source in legacy:
            self.store.put(self.tenant,'identity_history',source['id']+'-'+source['version'],source,create=True)
            old=copy.deepcopy(source.get('drafts',[]))
            source['assignment_mappings']=self.source_mappings(source)
            facts,drafts=extract_facts(source)
            # Keep original fact identifiers for recorded explicit choices and traceable history.
            for fact in facts:
                previous=next((f for f in source.get('facts',[]) if f['field']==fact['field'] and f['quote']==fact['quote'] and f['page']==fact['page']),None)
                if previous: fact['id']=previous['id']
            for before in old:
                for after in drafts:
                    if canonical(before['title'])==canonical(after['title']):
                        aliases.setdefault(before['id'],set()).add(after['id'])
            source.update(facts=facts,drafts=drafts,identity_schema=2)
            self.store.put(self.tenant,'sources',source['id'],source)
        for old_id,new_ids in aliases.items():
            self.store.put(self.tenant,'identity_migrations',old_id,dict(old_id=old_id,new_ids=sorted(new_ids),status='unambiguous' if len(new_ids)==1 else 'review_required',at=now()))
            if len(new_ids)==1:
                for override in self.store.list(self.tenant,'task_overrides'):
                    if override['id']==old_id:
                        new_id=next(iter(new_ids))
                        self.store.put(self.tenant,'task_overrides',new_id,dict(override,id=new_id,migrated_from=old_id),create=True)
        for override in self.store.list(self.tenant,'task_overrides'):
            deps=override.get('values',{}).get('dependencies')
            if deps:
                if all(d not in aliases or len(aliases[d])==1 for d in deps):
                    override['values']['dependencies']=[next(iter(aliases[d])) if d in aliases else d for d in deps]
                    self.store.put(self.tenant,'task_overrides',override['id'],override)
                else:
                    self.store.put(self.tenant,'identity_migrations','dependencies-'+override['id'],dict(old_id=override['id'],status='review_required',reason='Ambiguous legacy prerequisite; preserved for explicit review.'))
        # Rebind a previous decision only when its exact fact remains in a current conflict.
        new_conflicts=conflicts([f for s in self.store.list(self.tenant,'sources') for f in s.get('facts',[])])
        resolutions=self.store.list(self.tenant,'resolutions')
        for c in new_conflicts:
            chosen=next((r for r in resolutions if any(f['id']==r['fact_id'] for f in c['facts'])),None)
            if chosen:self.store.put(self.tenant,'resolutions',c['id'],dict(chosen,id=c['id'],migrated_from=chosen['id']),create=True)
        self.invalidate_plans()

    def invalidate_plans(self):
        for plan in self.store.list(self.tenant,'plans'):
            if not plan.get('invalidated'):
                # Preserve the exact historical proposal and all receipts/approvals unchanged.
                self.store.put(self.tenant,'plan_history',plan['id'],plan,create=True)
                self.store.put(self.tenant,'plans',plan['id'],dict(plan,invalidated=True))

    def map_assignment(self, source_id, key, course, term, assignment_key, target_id=None):
        source=next((s for s in self.sources() if s['id']==source_id),None)
        if not source or not any(t['section_key']==key for t in source['drafts']):
            raise RelayError('ACCESS_DENIED','Choose an assignment section in your own current source.')
        if target_id:
            task=next((t for t in self.tasks() if t['id']==target_id and t['identity']['status']=='confirmed'),None)
            if not task: raise RelayError('ACCESS_DENIED','Choose a confirmed assignment in this workspace.')
            identity=task['identity']
        else:
            if not all(v and v.strip() for v in (course,term,assignment_key)):
                raise RelayError('SOURCE_CONFLICT','Confirm course, academic term and assignment key; missing context is not guessed.')
            identity=dict(id=assignment_id(course,term,assignment_key),course=course.strip(),term=term.strip(),assignment_key=assignment_key.strip(),status='confirmed')
        previous=next(t for t in source['drafts'] if t['section_key']==key)
        record=dict(identity,origin='explicit_user_mapping',source_id=source_id,source_version=source['version'],section_key=key,confirmed_at=now())
        self.store.put(self.tenant,'assignment_mappings',source_id+'-'+key,record)
        source['assignment_mappings']=self.source_mappings(source)
        source['facts'],source['drafts']=extract_facts(source)
        self.store.put(self.tenant,'sources',source_id,source)
        if previous['id']!=record['id']:
            overrides=self.store.list(self.tenant,'task_overrides')
            prior=next((o for o in overrides if o['id']==previous['id']),None)
            target=next((o for o in overrides if o['id']==record['id']),None)
            if prior and not target:
                self.store.put(self.tenant,'task_overrides',record['id'],dict(prior,id=record['id'],migrated_from=previous['id']),create=True)
            self.store.put(self.tenant,'identity_migrations',previous['id'],dict(old_id=previous['id'],new_ids=[record['id']],status='review_required' if prior and target else 'explicit_user_mapping',override_preserved=True,at=now()))
        self.invalidate_plans()
        return record

    def current_facts(self):
        return [f for s in self.sources() for f in s.get('facts',[])]

    def current_conflicts(self):
        out=conflicts(self.current_facts())
        for c in out:
            try:
                r=self.store.get(self.tenant,'resolutions',c['id'])
                c.update(status='resolved',resolution=r)
            except RelayError:
                pass
        return out

    def tasks(self):
        merged={}
        for s in self.sources():
            for task in s.get('drafts',[]):
                if task['id'] in merged:
                    merged[task['id']]['source_ids']=list(set(merged[task['id']]['source_ids']+task['source_ids']))
                else:
                    merged[task['id']]=copy.deepcopy(task)
        for c in self.current_conflicts():
            if c['status']=='unresolved':
                merged[c['task_id']]['due']=None
            else:
                chosen=next(f for f in c['facts'] if f['id']==c['resolution']['fact_id'])
                merged[c['task_id']]['due']=chosen['value']
        for override in self.store.list(self.tenant,'task_overrides'):
            if override['id'] in merged:
                merged[override['id']].update(override['values'])
                merged[override['id']]['user_overrides']=override['values']
        from .progress import overlay
        return overlay(list(merged.values()), self.store.list(self.tenant,'progress'))

    def resolve(self,conflict_id,fact_id):
        c=next((c for c in self.current_conflicts() if c['id']==conflict_id),None)
        if not c or fact_id not in [f['id'] for f in c['facts']]:
            raise RelayError('ACCESS_DENIED','Choose a fact from the current conflict.')
        resolution=dict(id=conflict_id,fact_id=fact_id,policy='explicit_user_choice',resolved_at=now(),user=self.tenant)
        self.store.put(self.tenant,'resolutions',conflict_id,resolution)
        return resolution

    def plan(self,scenario=None,proposal=False):
        s=self.settings()
        tasks=self.tasks()
        if any(t.get('identity',{}).get('status')=='unresolved' for t in tasks):
            raise RelayError('SOURCE_CONFLICT','Confirm unresolved course/term/assignment mappings before planning.')
        start=min((w['start'] for w in s['windows']),default=now())
        end=max((w['end'] for w in s['windows']),default=now())
        initial_versions=self.source_versions()
        run=uuid.uuid4().hex
        self.store.event(self.tenant,run,'run_started',summary='Checking evidence and actual configured availability.',mode=s['mode'])
        if any(c['status']=='unresolved' for c in self.current_conflicts()):
            self.store.event(self.tenant,run,'source_conflict',summary='Two source deadlines disagree. A choice is required.')
            raise RelayError('SOURCE_CONFLICT','Resolve the deadline conflict before repairing this week.')
        began=clock.perf_counter()
        self.store.event(self.tenant,run,'tool_started',tool='get_calendar_window',summary='Reading configured calendar availability.')
        calendar=self.calendar()
        events=calendar.list(start,end)
        self.store.event(self.tenant,run,'tool_finished',tool='get_calendar_window',duration_ms=round((clock.perf_counter()-began)*1000),summary=f'{len(events)} events observed.',mode=calendar.mode)
        own=unchanged_owned_ids(events,self.store.list(self.tenant,'operations'),self.tenant)
        payload=dict(tasks=tasks,windows=s['windows'],busy=busy_intervals(events,s['timezone'],exclude_ids=own),
                     timezone=s['timezone'],daily_cap_minutes=s['daily_cap_minutes'])
        if s.get('mode')!='illustrative' or self.store.list(self.tenant,'progress') or self.store.list(self.tenant,'gates'):
            payload['not_before']=now()
            editable={e['id'] for e in events if e['id'] in own and instant(e['start']['dateTime'])>=instant(payload['not_before'])}
            payload['busy']=busy_intervals(events,s['timezone'],exclude_ids=editable)
        from .handoff import apply_gates
        gate_notes=apply_gates(self,payload)
        prior=self.latest_plan()
        if scenario and prior and prior.get('invalidated'):
            raise RelayError('STALE_PLAN','The baseline is outdated. Repair your week before comparing a scenario.')
        if prior:
            payload['baseline']=[b for b in prior['blocks'] if not payload.get('not_before') or instant(b['start'])>=instant(payload['not_before'])]
            payload['pins']=[b for b in prior.get('input',{}).get('pins',[]) if not payload.get('not_before') or instant(b['start'])>=instant(payload['not_before'])]
            if payload.get('not_before'):
                payload['busy'] += [dict(start=b['start'],end=b['end']) for b in prior['blocks'] if instant(b['start'])<instant(payload['not_before'])<instant(b['end'])]
        if scenario:
            baseline=prior or build_recovery_plan(payload)
            result=compare_plan_scenarios(baseline,scenario)
            result['scenario']=scenario
        else:
            self.store.event(self.tenant,run,'tool_started',tool='build_recovery_plan',summary='Checking deadlines, dependencies, pins and capacity.')
            began=clock.perf_counter()
            result=build_recovery_plan(payload)
            self.store.event(self.tenant,run,'tool_finished',tool='build_recovery_plan',duration_ms=round((clock.perf_counter()-began)*1000),summary=result['solver_status'])
        if initial_versions!=self.source_versions():
            raise RelayError('STALE_PLAN','Workspace changed during planning. No proposal was accepted; refresh and retry.')
        result.update(sources=initial_versions,created_at=now(),run_id=run,mode=s['mode'],gate_notes=gate_notes)
        result['historical_blocks']=(prior or {}).get('historical_blocks',[])+[b for b in (prior or {}).get('blocks',[]) if payload.get('not_before') and instant(b['start'])<instant(payload['not_before'])]
        result['change_reason']='Explicit remaining work, current gate observations and eligible future availability.'
        before={(b['task_id'],b['start'],b['end']) for b in (prior or {}).get('blocks',[])}
        after={(b['task_id'],b['start'],b['end']) for b in result['blocks']}
        result['block_diff']=dict(removed=[list(b) for b in sorted(before-after)],added=[list(b) for b in sorted(after-before)])
        result['id']=digest(result)[:24]
        if not scenario and not proposal:
            self.store.put(self.tenant,'plans',result['id'],result)
            self.store.put(self.tenant,'meta','latest_plan',{'id':result['id']})
        self.store.event(self.tenant,run,'plan_validated',summary='Feasible within every hard constraint.' if result['feasible'] else f"{result['unscheduled_minutes']} minutes remain unscheduled.",solver_status=result['solver_status'])
        self.store.event(self.tenant,run,'run_completed',summary='Scenario computed; baseline unchanged.' if scenario else 'Plan ready for review. No external writes.')
        return result

    def latest_plan(self):
        try:
            return self.store.get(self.tenant,'plans',self.store.get(self.tenant,'meta','latest_plan')['id'])
        except RelayError:
            return None

    def actions(self):
        return Actions(self.store,self.tenant,self.calendar(),self.source_versions)

    def packet(self,task_id):
        task=next((t for t in self.tasks() if t['id']==task_id),None)
        if not task:
            raise RelayError('ACCESS_DENIED','Task unavailable in this workspace.')
        facts=[f for f in self.current_facts() if f['task_id']==task_id]
        return dict(task=task,objective=task['rubric'][0] if task['rubric'] else None,
                    next_action=('Open the cited requirement and draft: '+task['rubric'][0]) if task['rubric'] else 'Read the source and define the missing rubric before starting.',
                    checklist=task['rubric'],facts=facts,duration_assumption=f"{task['minutes']} minutes estimated" if task['minutes'] else 'Effort unknown',
                    completion_origin=task.get('completion','planned'),graph=[dict(from_id=f['source_id'],to_id=task_id,relation='supports',fact_id=f['id']) for f in facts])

    def snapshot(self):
        s=self.settings()
        if os.getenv('RELAY_MODE')=='cloud' and not s.get('calendar_live'):
            events=[];calendar_mode='disconnected'
        else:
            calendar=self.calendar()
            events=calendar.list(min((w['start'] for w in s['windows']),default=now()),max((w['end'] for w in s['windows']),default=now()))
            calendar_mode=calendar.mode
        display_settings=dict(s,poll_seconds=max(30,int(os.getenv('RELAY_POLL_SECONDS','60' if os.getenv('RELAY_GITHUB_TOKEN') else '300'))))
        return dict(workspace_id=self.tenant,workspace_fingerprint=digest(self.source_versions()),settings=display_settings,tasks=self.tasks(),sources=[{k:v for k,v in source.items() if k!='pages'} for source in self.sources()],
                    conflicts=self.current_conflicts(),plan=self.latest_plan(),events=self.store.events(self.tenant),
                    calendar_events=events,calendar_mode=calendar_mode,
                    receipts=self.store.list(self.tenant,'receipts'),snapshot_generated_at=now(),
                    last_sync=self.freshness().get('last_successful_sync'),freshness=self.freshness(),
                    identity_migrations=self.store.list(self.tenant,'identity_migrations'),
                    additions_revision=__import__('relay.progress',fromlist=['revision']).revision(self),
                    progress=self.store.list(self.tenant,'progress'),gates=__import__('relay.handoff',fromlist=['list_gates']).list_gates(self),
                    agent=__import__('relay.providers',fromlist=['current_availability']).current_availability(self.store))

    def freshness(self):
        try:return self.store.get(self.tenant,'meta','freshness')
        except RelayError:return dict(last_successful_sync=None,last_failed_attempt=None,source_fetched_at=None)

    def sync_repo(self,force=True):
        s=self.settings()
        interval=max(30,int(os.getenv('RELAY_POLL_SECONDS','60' if os.getenv('RELAY_GITHUB_TOKEN') else '300')))
        self.store.put(self.tenant,'watermarks','github-poll',{'next_check_epoch':0},create=True)
        poll=self.store.get(self.tenant,'watermarks','github-poll')
        if not force and poll['next_check_epoch']>clock.time():
            return dict(changed=False,mode='cached_poll',next_check_epoch=poll['next_check_epoch'])
        if not force and not self.store.claim(self.tenant,'watermarks','github-poll',{'next_check_epoch':poll['next_check_epoch']},{'next_check_epoch':clock.time()+interval}):
            return dict(changed=False,mode='coalesced_poll')
        repo=GitHub(s['github_repo'],s.get('github_ref','main'),os.getenv('RELAY_GITHUB_TOKEN'))
        try:
            source_path=s.get('github_path','coursework.md')
            observation=public_demo.read_public_source(s['github_repo'],s.get('github_ref','main'),source_path,lambda:repo.read(source_path)) if public_demo.enabled() else repo.read(source_path)
        except RelayError as exc:
            self.store.put(self.tenant,'meta','freshness',dict(self.freshness(),last_failed_attempt=dict(at=now(),code=exc.code)))
            if exc.code=='UPSTREAM_RATE_LIMITED':
                self.store.put(self.tenant,'watermarks','github-poll',{'next_check_epoch':(exc.details or {}).get('retry_at_epoch',clock.time()+interval)})
            raise
        fetched=observation['fetched_at']
        previous_freshness=self.freshness()
        self.store.put(self.tenant,'meta','freshness',dict(previous_freshness,source_fetched_at=fetched,
            last_successful_sync=fetched if not observation.get('cache_age_seconds') else previous_freshness.get('last_successful_sync'),
            last_observation_at=now(),cached=bool(observation.get('cache_age_seconds')),commit=observation['commit']))
        sid='github-coursework'
        try:
            previous=self.store.get(self.tenant,'sources',sid)
        except RelayError:
            previous=None
        parsed_hash=digest(observation['text'].encode().hex())
        if previous and previous['content_hash']==parsed_hash:
            return dict(changed=False,mode='live',commit=observation['commit'])
        source=self.import_source('coursework.md',observation['text'].encode(),id=sid,mode='live_github',title='Live course repository',remote=dict(observation,repo=s['github_repo']))
        run='change-'+source['version']
        claimed=self.store.put(self.tenant,'radar',run,dict(id=run,observed_at=now(),commit=observation['commit']),create=True)
        if claimed:
            self.store.event(self.tenant,run,'run_started',summary='A live repository source changed.',mode='live',commit=observation['commit'])
            self.store.event(self.tenant,run,'decision_summary',summary='Imported the revised evidence. Revalidating affected work; no silent calendar writes.')
            try:
                plan=self.plan()
                self.store.event(self.tenant,run,'approval_required',summary='Revised plan requires a new explicit approval.',plan_id=plan['id'])
            except RelayError as exc:
                self.store.event(self.tenant,run,'source_conflict' if exc.code=='SOURCE_CONFLICT' else 'run_failed',summary=exc.message,code=exc.code)
            self.explain_change(run)
        return dict(changed=True,mode='live',commit=observation['commit'],source_id=sid,run_id=run)

    def explain_change(self,run):
        if not os.getenv('RELAY_AGENT_RESOURCE'):
            self.store.event(self.tenant,run,'decision_summary',summary='Impact recorded with deterministic checks. Gemini is not connected; no model call was made.',mode='implemented_local')
            return
        try:
            from .limits import model_request
            from .auth import sign_context
            import vertexai
            model_request(self.store,self.tenant,judge=self.settings().get('mode')=='judge')
            resource=os.environ['RELAY_AGENT_RESOURCE']
            remote=vertexai.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION']).agent_engines.get(name=resource)
            token=sign_context(self.tenant,os.environ['RELAY_MCP_URL'],os.environ['RELAY_CONTEXT_SECRET'])
            remote.query(user_id=self.tenant,message='An approved source changed. Inspect the current evidence and availability as relevant. Explain affected tasks, conflicts and a proposed recovery. Never authorize or apply calendar writes.',context_token=token,language='en',run_id=run)
        except Exception as exc:
            self.store.event(self.tenant,run,'run_failed',summary='Managed change-impact explanation could not complete; deterministic evidence is retained.',code=exc.code if isinstance(exc,RelayError) else 'UPSTREAM_UNAVAILABLE')

    def sync_calendar(self):
        settings=self.settings()
        if not settings.get('calendar_live'):
            return dict(changed=False,mode='disconnected')
        calendar=self.calendar()
        key='calendar-'+digest(calendar.id)[:24]
        try:
            previous=self.store.get(self.tenant,'watermarks',key)
        except RelayError:
            previous={}
        delta=calendar.sync(previous.get('sync_token'))
        # Persist incremental sync cursor even when changes fall outside the planning horizon.
        events=calendar.list(min(w['start'] for w in settings['windows']),max(w['end'] for w in settings['windows']))
        owned=unchanged_owned_ids(events,self.store.list(self.tenant,'operations'),self.tenant)
        fingerprint=digest(sorted([{'id':e['id'],'etag':e.get('etag'),'start':e.get('start'),'end':e.get('end')} for e in events if e['id'] not in owned],key=lambda e:e['id']))
        changed=bool(previous.get('fingerprint')) and fingerprint!=previous['fingerprint']
        self.store.put(self.tenant,'watermarks',key,dict(sync_token=delta['sync_token'],fingerprint=fingerprint,observed_at=now(),full_resync=delta['full_resync']))
        if changed:
            run='calendar-change-'+fingerprint[:24]
            if self.store.put(self.tenant,'radar',run,dict(id=run,observed_at=now()),create=True):
                self.store.event(self.tenant,run,'run_started',summary='The approved calendar availability changed.',mode='live')
                try:
                    plan=self.plan()
                    self.store.event(self.tenant,run,'approval_required',summary='Calendar impact recomputed. Review a fresh preview.',plan_id=plan['id'])
                except RelayError as exc:
                    self.store.event(self.tenant,run,'run_failed',summary=exc.message,code=exc.code)
                self.explain_change(run)
        return dict(changed=changed,mode='live',full_resync=delta['full_resync'],observed_changes=len(delta['events']))
