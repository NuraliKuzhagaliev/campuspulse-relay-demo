"""Untrusted, versioned manual transfer. No credentials or operational authority."""
import copy
import hashlib
import json
import re
import secrets
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from zoneinfo import ZoneInfo
from .domain import RelayError, digest, now, instant, Task, Interval
from .evidence import extract_facts
from .identity import assignment_id
from .progress import revision, check_revision

MAX_BYTES=2*1024*1024


def encoded(value):
    # JSON.parse/stringify on the web serializes 45.0 as 45. Normalize the same
    # semantic numbers before hashing so a genuine cross-device save is valid.
    def normalized(v):
        if isinstance(v,float) and v.is_integer():return int(v)
        if isinstance(v,dict):return {k:normalized(x) for k,x in v.items()}
        if isinstance(v,list):return [normalized(x) for x in v]
        return v
    return json.dumps(normalized(value),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def checksum(payload):return hashlib.sha256(encoded(payload)).hexdigest()


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')


class Page(Strict):
    page:int=Field(ge=1,le=100)
    text:str=Field(max_length=250000)


class PortableSource(Strict):
    id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
    title:str=Field(max_length=180)
    filename:str=Field(max_length=180)
    version:str=Field(pattern=r'^[a-f0-9]{1,64}$')
    historical_content_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    historical_hash_algorithm:str
    fetched_at:str
    pages:list[Page]=Field(min_length=1,max_length=100)


class Assignment(Strict):
    id:str=Field(pattern=r'^[a-f0-9]{24}$')
    course:str=Field(min_length=1,max_length=180)
    term:str=Field(min_length=1,max_length=180)
    key:str=Field(min_length=1,max_length=180)
    source_ids:list[str]=Field(min_length=1,max_length=12)
    sections:dict[str,str]=Field(max_length=12)


class PassportPayload(Strict):
    reviewed_assignments:list[dict]=Field(default_factory=list,max_length=50)
    sources:list[PortableSource]=Field(min_length=1,max_length=12)
    assignments:list[Assignment]=Field(max_length=50)
    citations:list[dict]=Field(max_length=1000)
    overrides:list[dict]=Field(max_length=50)
    progress:list[dict]=Field(max_length=50)
    logs:list[dict]=Field(max_length=500)
    decisions:list[dict]=Field(max_length=50)
    clarifications:list[dict]=Field(max_length=50)
    gates:list[dict]=Field(max_length=10)
    preferences:dict


class Envelope(Strict):
    format:str
    version:int
    exported_at:str
    payload:PassportPayload
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')


def selected(record, keys):return {k:copy.deepcopy(record[k]) for k in keys.split() if k in record}


def export(svc, source_ids=None):
    sources=svc.sources()
    if source_ids is not None:
        if set(source_ids)-{s['id'] for s in sources}:raise RelayError('ACCESS_DENIED','Select sources in your current workspace.')
        sources=[s for s in sources if s['id'] in source_ids]
    ids={s['id'] for s in sources}
    if not sources:raise RelayError('SOURCE_CONFLICT','Import and review at least one source before exporting a Workspace Passport.')
    tasks=[t for t in svc.tasks() if any(s in ids for s in t['source_ids'])]
    if any(t['identity']['status']!='confirmed' for t in tasks):raise RelayError('SOURCE_CONFLICT','Confirm course, term and assignment identity before portable export.')
    assignments=[dict(id=t['id'],course=t['identity']['course'],term=t['identity']['term'],key=t['identity']['assignment_key'],
                      source_ids=[s for s in t['source_ids'] if s in ids],sections={s['id']:d['section_key'] for s in sources for d in s['drafts'] if d['id']==t['id']}) for t in tasks]
    tids={t['id'] for t in tasks}
    citations=[selected(f,'id task_id source_id source_version field value quote page') for s in sources for f in s['facts']]
    fids={f['id'] for f in citations}
    progress=[selected(p,'id completion remaining_minutes origin category history created_at frozen_estimate frozen_course frozen_at frozen_source_versions frozen_before_work updated_at revision') for p in svc.store.list(svc.tenant,'progress') if p['id'] in tids]
    logs=[selected(l,'id task_id duration_minutes origin created_at updated_at revision corrections interruptions checklist evidence_id') for l in svc.store.list(svc.tenant,'work_logs') if l['task_id'] in tids]
    for log in logs:
        if log.get('evidence_id') and log['evidence_id'] not in fids:raise RelayError('PASSPORT_REFERENCES','Select the source supporting this work log before exporting.')
    overrides=[dict(id=o['id'],values=selected(o['values'],'minutes effort_max due completion remaining_minutes dependencies'),origin=o.get('origin','student_report'),updated_at=o.get('updated_at')) for o in svc.store.list(svc.tenant,'task_overrides') if o['id'] in tids]
    if any(set(o['values'].get('dependencies',[]))-tids for o in overrides):raise RelayError('PASSPORT_REFERENCES','Include prerequisite coursework in the selected sources.')
    # Decisions have no tenant IDs, executable action digests or source credentials.
    decisions=[dict(id=r['id'],fact_id=r['fact_id'],origin=r.get('policy','explicit_user_choice'),at=r.get('resolved_at')) for r in svc.store.list(svc.tenant,'resolutions') if r['fact_id'] in fids]
    clarifications=[selected(r,'id task_id choice origin uncertain at kind alternative') for r in svc.store.list(svc.tenant,'clarification_decisions') if r['task_id'] in tids or r.get('kind')=='availability']
    for record in clarifications:
        if record.get('alternative',{}).get('fact_id') and record['alternative']['fact_id'] not in fids:raise RelayError('PASSPORT_REFERENCES','Include the source supporting this clarification decision.')
    gates=[selected(g,'id task_id repo number condition created_at origin eta') for g in svc.store.list(svc.tenant,'gates') if g['task_id'] in tids and not g.get('disabled')]
    config=svc.settings()
    payload=dict(sources=[dict(id=s['id'],title=s['title'],filename=s['filename'],version=s['version'],historical_content_hash=s['content_hash'],
                    historical_hash_algorithm=s.get('content_hash_algorithm','sha256(canonical_json(content.hex()))'),fetched_at=s['fetched_at'],pages=s['pages']) for s in sources],
                 assignments=assignments,citations=citations,overrides=overrides,progress=progress,logs=logs,decisions=decisions,clarifications=clarifications,gates=gates,
                 preferences=selected(config,'timezone windows daily_cap_minutes'),
                 reviewed_assignments=[dict(task_id=t['id'],**selected(t,'title due minutes effort_max rubric')) for t in tasks if t.get('extraction_origin')=='confirmed_semantic_proposal'])
    envelope=dict(format='campuspulse-relay-workspace',version=1,exported_at=now(),payload=payload,sha256=checksum(payload))
    # Export uses the same strict validator as import, so an invalid partial selection
    # never silently drops a dependency or an evidence reference.
    validate(envelope)
    size=len(encoded(envelope))
    if size>MAX_BYTES:raise RelayError('PASSPORT_TOO_LARGE','Portable workspace exceeds 2 MiB. Explicitly select fewer sources; no evidence was truncated.',{'bytes':size})
    return dict(file=envelope,preview=dict(bytes=size,sources=len(sources),assignments=len(assignments),logs=len(logs),gates=len(gates),
                    originals_included=False,observations='archived',approvals_included=False,temporary_hosted_storage=True))


def walk(value, depth=0):
    if depth>16:raise RelayError('PASSPORT_INVALID','Portable data nesting exceeds its limit.')
    if isinstance(value,dict):
        if len(value)>100:raise RelayError('PASSPORT_INVALID','Too many fields in a portable record.')
        forbidden={'tenant','tenant_id','workspace_id','csrf','cookie','cookies','token','access_token','refresh_token','credentials','secret','approval_id','digest','calendar_id','operations','signed_url','session_id','user','local_path','path'}
        if set(value)&forbidden:raise RelayError('PASSPORT_INVALID','Portable files cannot carry credentials, tenant authority, local paths or executable operations.')
        for item in value.values():walk(item,depth+1)
    elif isinstance(value,list):
        if len(value)>1000:raise RelayError('PASSPORT_INVALID','Too many portable items.')
        for item in value:walk(item,depth+1)
    elif isinstance(value,str) and len(value)>250000:raise RelayError('PASSPORT_INVALID','Portable text is too large.')


def validate(value):
    if 'format' not in value and 'sources' in value:
        raise RelayError('LEGACY_SNAPSHOT_MISSING_EXTRACTS','Legacy snapshots contain settings, task summaries and receipts, but omit source pages. Re-import original documents; this file cannot restore cited coursework. Your workspace is unchanged.')
    if value.get('version')!=1 or value.get('format')!='campuspulse-relay-workspace':raise RelayError('PASSPORT_VERSION','Unsupported portable workspace format/version; supported migration starts at version 1.')
    try: envelope=Envelope.model_validate(value).model_dump(exclude_unset=True)
    except ValidationError as exc:raise RelayError('PASSPORT_INVALID','Portable workspace fields or item limits are invalid.') from exc
    walk(envelope['payload'])
    if checksum(envelope['payload'])!=envelope['sha256']:raise RelayError('PASSPORT_CHECKSUM','Portable checksum does not match. This is an integrity check, never proof of authenticity.')
    instant(envelope['exported_at']);p=envelope['payload']
    sources={s['id']:s for s in p['sources']};tasks={t['id']:t for t in p['assignments']}
    if len(sources)!=len(p['sources']) or len(tasks)!=len(p['assignments']):raise RelayError('PASSPORT_REFERENCES','Duplicate portable identities.')
    for source in sources.values():
        if '/' in source['filename'] or '\\' in source['filename'] or source['filename'].startswith('.') or ':' in source['filename']:raise RelayError('PASSPORT_INVALID','Portable filenames cannot contain paths.')
        if len({page['page'] for page in source['pages']})!=len(source['pages']) or sum(len(x['text']) for x in source['pages'])>250000:raise RelayError('PASSPORT_INVALID','Invalid source page mapping or text limit.')
        instant(source['fetched_at'])
    for task in tasks.values():
        if task['id']!=assignment_id(task['course'],task['term'],task['key']):raise RelayError('PASSPORT_REFERENCES','Course/term/assignment identity does not match its portable key.')
        if set(task['source_ids'])-sources.keys() or set(task['sections'])!=set(task['source_ids']) or any(not re.fullmatch(r'[a-f0-9]{24}',v) for v in task['sections'].values()):raise RelayError('PASSPORT_REFERENCES','Assignment source/section references are invalid.')
    for reviewed in p.get('reviewed_assignments',[]):
        if not isinstance(reviewed,dict) or set(reviewed)!={'task_id','title','due','minutes','effort_max','rubric'} or reviewed['task_id'] not in tasks:raise RelayError('PASSPORT_REFERENCES','Invalid reviewed assignment reference.')
        Task.model_validate(dict(id=reviewed['task_id'],**{k:v for k,v in reviewed.items() if k!='task_id'}))
        if not isinstance(reviewed['rubric'],list) or len(reviewed['rubric'])>50 or any(not isinstance(v,str) or len(v)>4000 for v in reviewed['rubric']):raise RelayError('PASSPORT_INVALID','Invalid reviewed rubric.')
    citations={}
    for fact in p['citations']:
        if set(fact)!={'id','task_id','source_id','source_version','field','value','quote','page'} or fact['task_id'] not in tasks or fact['source_id'] not in sources:raise RelayError('PASSPORT_REFERENCES','Invalid portable citation references.')
        source=sources[fact['source_id']]
        page=next((x for x in source['pages'] if x['page']==fact['page']),None)
        if not page or not isinstance(fact['quote'],str) or not fact['quote'] or fact['quote'] not in page['text'] or fact['source_version']!=source['version']:raise RelayError('PASSPORT_REFERENCES','A citation does not match its included exact extract/page/version.')
        if fact['id'] in citations:raise RelayError('PASSPORT_REFERENCES','Duplicate citation.')
        citations[fact['id']]=fact
    for record in p['overrides']:
        if set(record)-{'id','values','origin','updated_at'} or record.get('id') not in tasks or set(record.get('values',{}))-{'minutes','effort_max','due','completion','remaining_minutes','dependencies'}:raise RelayError('PASSPORT_INVALID','Unsupported portable estimate fields.')
        if set(record['values'].get('dependencies',[]))-tasks.keys():raise RelayError('PASSPORT_REFERENCES','Missing prerequisite assignment.')
        Task.model_validate(dict(id=record['id'],title='Portable task',**record['values']))
    for record in p['progress']:
        if set(record)-set('id completion remaining_minutes origin category history created_at frozen_estimate frozen_course frozen_at frozen_source_versions frozen_before_work updated_at revision'.split()) or record.get('id') not in tasks:raise RelayError('PASSPORT_REFERENCES','Invalid portable progress reference.')
        if record.get('completion') not in ('in_progress','completed') or (record.get('remaining_minutes') is not None and (not isinstance(record['remaining_minutes'],(int,float)) or not 0<=record['remaining_minutes']<=10080)):raise RelayError('PASSPORT_INVALID','Invalid portable remaining effort.')
        if (record['completion']=='completed')!=(record.get('remaining_minutes')==0):raise RelayError('PASSPORT_INVALID','Zero remaining requires a deliberate completion record.')
        if len(record.get('history',[]))>500:raise RelayError('PASSPORT_INVALID','Progress history exceeds limit.')
    for log in p['logs']:
        if set(log)-set('id task_id duration_minutes origin created_at updated_at revision corrections interruptions checklist evidence_id'.split()) or log.get('task_id') not in tasks or log.get('evidence_id') and log['evidence_id'] not in citations:raise RelayError('PASSPORT_REFERENCES','Invalid portable work-log reference.')
        if not isinstance(log.get('duration_minutes'),(int,float)) or not 0<log['duration_minutes']<=1440 or not isinstance(log.get('revision'),int) or log['revision']<1 or len(log.get('corrections',[]))>100:raise RelayError('PASSPORT_INVALID','Invalid portable work-log duration/history.')
        instant(log['created_at']);instant(log['updated_at'])
    for decision in p['decisions']:
        if set(decision)-{'id','fact_id','origin','at'} or decision.get('fact_id') not in citations:raise RelayError('PASSPORT_REFERENCES','Invalid portable decision reference.')
    for record in p['clarifications']:
        if set(record)-set('id task_id choice origin uncertain at kind alternative'.split()) or (record.get('task_id') not in tasks and not (record.get('kind')=='availability' and record.get('task_id') is None)) or record.get('choice') not in (None,0,1):raise RelayError('PASSPORT_REFERENCES','Invalid portable clarification decision.')
        alt=record.get('alternative',{})
        if set(alt)-set('value fact_id source_id quote page origin'.split()) or alt.get('fact_id') and alt['fact_id'] not in citations or alt.get('source_id') and alt['source_id'] not in sources:raise RelayError('PASSPORT_REFERENCES','Invalid portable clarification evidence.')
    for gate in p['gates']:
        if set(gate)-set('id task_id repo number condition created_at origin eta'.split()) or gate.get('task_id') not in tasks or gate.get('condition')!='pr_merged' or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',gate.get('repo','')) or '..' in gate['repo'] or not isinstance(gate.get('number'),int) or not 0<gate['number']<=100000000:raise RelayError('PASSPORT_INVALID','Invalid portable gate definition.')
        if gate.get('eta'):instant(gate['eta'])
    prefs=p['preferences']
    if set(prefs)!={'timezone','windows','daily_cap_minutes'} or not isinstance(prefs['windows'],list) or len(prefs['windows'])>100 or not isinstance(prefs['daily_cap_minutes'],int) or prefs['daily_cap_minutes']%30 or not 30<=prefs['daily_cap_minutes']<=720:raise RelayError('PASSPORT_INVALID','Invalid portable preferences.')
    try:ZoneInfo(prefs['timezone'])
    except Exception as exc:raise RelayError('PASSPORT_INVALID','Invalid portable timezone.') from exc
    for window in prefs['windows']:
        if set(window)!={'start','end'}:raise RelayError('PASSPORT_INVALID','Only permitted availability intervals are portable.')
        w=Interval.model_validate(window)
        if instant(w.end)<=instant(w.start):raise RelayError('PASSPORT_INVALID','Availability end must follow start.')
    return envelope


def stage(svc, content):
    if len(content)>MAX_BYTES:raise RelayError('PASSPORT_TOO_LARGE','Portable workspace limit is 2 MiB.')
    try:
        def unique_pairs(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('Duplicate portable JSON key')
                result[key]=value
            return result
        value=json.loads(content,object_pairs_hook=unique_pairs,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Non-finite portable number')))
        if not isinstance(value,dict):raise ValueError()
        envelope=validate(value)
    except RelayError:raise
    except (ValueError,TypeError,RecursionError,ValidationError,KeyError) as exc:raise RelayError('PASSPORT_INVALID','Portable JSON could not be validated; your workspace is unchanged.') from exc
    def prune(tx):
        for old in tx.list('passport_stages'):
            if old.get('expires_at_epoch',0)<__import__('time').time() and old.get('status')!='committed':tx.delete('passport_stages',old['id'])
    svc.store.atomic(svc.tenant,prune)
    active=[s for s in svc.store.list(svc.tenant,'passport_stages') if s.get('status')=='staged' and s.get('expires_at_epoch',0)>__import__('time').time()]
    if len(active)>=5:raise RelayError('BUSY','Five restore previews are already staged. Wait ten minutes for expiry before importing another file.')
    id=secrets.token_hex(12)
    record=dict(id=id,envelope=envelope,created_at=now(),expires_at_epoch=__import__('time').time()+600,
                expected_revision=revision(svc),source_binding=svc.source_versions(),status='staged')
    svc.store.put(svc.tenant,'passport_stages',id,record)
    p=envelope['payload']
    return dict(id=id,revision=record['expected_revision'],sources=len(p['sources']),assignments=len(p['assignments']),logs=len(p['logs']),gates=len(p['gates']),
                originals_missing=True,observations='archived_untrusted',plans_invalidated=True,reconnections_required=True,
                current_workspace_preserved=True,bytes=len(content))


def commit(svc, stage_id):
    staged=svc.store.get(svc.tenant,'passport_stages',stage_id)
    if staged.get('status')=='committed':return staged['result']
    if __import__('time').time()>staged['expires_at_epoch']:raise RelayError('STALE_REVISION','Restore preview expired. Validate the file again.')
    if staged['source_binding']!=svc.source_versions():raise RelayError('STALE_REVISION','Current workspace changed. Revalidate before switching to a fresh copy.')
    envelope=validate(staged['envelope']);p=envelope['payload']
    from . import public_demo
    destination=('demo-' if public_demo.temporary_enabled() else 'local-')+secrets.token_hex(16) # Server generated, never a file authorization field.
    source_map={s['id']:'portable-'+secrets.token_hex(12) for s in p['sources']}
    sources=[];fact_map={}
    for old in p['sources']:
        sid=source_map[old['id']]
        mappings={t['sections'][old['id']]:dict(id=t['id'],course=t['course'],term=t['term'],assignment_key=t['key'],status='confirmed',origin='untrusted_portable_user_mapping') for t in p['assignments'] if old['id'] in t['source_ids']}
        content_hash=checksum(old['pages'])
        source=dict(id=sid,title=old['title'],filename=old['filename'],version=content_hash[:24],content_hash=content_hash,content_hash_algorithm='sha256(canonical_json(extracted_pages))',
                    pages=old['pages'],fetched_at=old['fetched_at'],type='archived_extract',mode='archived_portable_extract',identity_schema=2,assignment_mappings=mappings,
                    timezone=p['preferences']['timezone'],remote=None,original_file_verified=False,archived=True,
                    historical_original=dict(content_hash=old['historical_content_hash'],algorithm=old['historical_hash_algorithm'],version=old['version'],claim='unverified_historical_hash'))
        source['facts'],source['drafts']=extract_facts(source)
        reviewed_ids=set()
        for reviewed in p.get('reviewed_assignments',[]):
            assignment=next(t for t in p['assignments'] if t['id']==reviewed['task_id'])
            if old['id'] not in assignment['source_ids']:continue
            tid=assignment['id'];reviewed_ids.add(tid)
            identity=dict(id=tid,course=assignment['course'],term=assignment['term'],assignment_key=assignment['key'],status='confirmed',origin='untrusted_portable_reviewed_claim')
            source['drafts']=[d for d in source['drafts'] if d['id']!=tid and d.get('extraction_origin')!='prose_needs_review']
            source['drafts'].append(dict(id=tid,**{k:v for k,v in reviewed.items() if k!='task_id'},identity=identity,course=assignment['course'],section_key=assignment['sections'][old['id']],source_ids=[sid],
                gaps=[k for k in ('due','minutes') if reviewed[k] is None],completion='planned',dependencies=[],priority=1,extraction_origin='confirmed_semantic_proposal'))
            source.setdefault('confirmed_extractions',[]).append(dict(task=copy.deepcopy(source['drafts'][-1]),proposal_id='archived_portable_claim',entity_id=assignment['sections'][old['id']]))
            source['facts']=[f for f in source['facts'] if f['task_id']!=tid]
        for old_fact in p['citations']:
            if old_fact['source_id']!=old['id']:continue
            new=next((f for f in source['facts'] if all(f[k]==old_fact[k] for k in ('task_id','field','value','quote','page'))),None)
            if not new and old_fact['task_id'] in reviewed_ids:
                # Integrity was checked above; these are explicitly untrusted
                # archived interpretations, never newly observed source facts.
                new=dict(old_fact,id=digest([sid,old_fact])[:24],source_id=sid,source_version=source['version'],hash=source['content_hash'],fetched_at=source['fetched_at'],timezone=source['timezone'],status='archived_student_claim')
                source['facts'].append(new)
            if not new:raise RelayError('PASSPORT_REFERENCES','Included facts cannot be reproduced from the included extract. Re-import the original document.')
            fact_map[old_fact['id']]=new['id']
        for fact in source['facts']:fact.update(kind='archived_extract_claim',original_verified=False)
        sources.append(source)
    def switch(tx):
        current=tx.get('passport_stages',stage_id)
        if current['status']=='committed':return current['result']
        check_revision(tx,staged['expected_revision'])
        target=tx.workspace(destination)
        settings=dict(p['preferences'],mode='own_documents',workspace_kind='own',anchor=min((w['start'][:10] for w in p['preferences']['windows']),default=now()[:10]),
                      calendar_id='local-illustrative-calendar',calendar_live=False,watch_enabled=False,github_repo=svc.settings()['github_repo'],github_ref='main',github_path='coursework.md',
                      portable_origin='untrusted_manual_copy',restored_at=now(),external_revalidation_required=True)
        target.put('meta','settings',settings)
        target.put('meta','additions',dict(revision=1,schema=1,updated_at=now()))
        for source in sources:
            target.put('sources',source['id'],source)
            target.put('source_versions',source['id']+'-'+source['version'],source)
            for key,mapping in source['assignment_mappings'].items():target.put('assignment_mappings',source['id']+'-'+key,dict(mapping,source_id=source['id'],section_key=key,source_version=source['version']))
        for override in p['overrides']:target.put('task_overrides',override['id'],dict(override,import_trust='untrusted_student_claim'))
        for progress in p['progress']:
            progress=copy.deepcopy(progress)
            progress['frozen_source_versions']={source_map[k]:v for k,v in progress.get('frozen_source_versions',{}).items() if k in source_map}
            target.put('progress',progress['id'],dict(progress,import_trust='untrusted_student_claim'))
        for log in p['logs']:
            log=copy.deepcopy(log);log['evidence_id']=fact_map.get(log.get('evidence_id'))
            target.put('work_logs',log['id'],dict(log,import_trust='untrusted_student_claim'))
        # Recompute conflict identifiers; a restored choice is an archived student
        # decision about included text, never refreshed upstream evidence.
        from .evidence import conflicts
        for conflict in conflicts([f for s in sources for f in s['facts']]):
            chosen=next((d for d in p['decisions'] if fact_map.get(d['fact_id']) in {f['id'] for f in conflict['facts']}),None)
            if chosen:target.put('resolutions',conflict['id'],dict(id=conflict['id'],fact_id=fact_map[chosen['fact_id']],policy='archived_portable_student_choice',resolved_at=chosen.get('at'),import_trust='untrusted_student_claim'))
        for gate in p['gates']:target.put('gates',gate['id'],dict(gate,archived=True,observation=None,source_versions={},revalidation_required=True))
        for old in p['clarifications']:
            record=copy.deepcopy(old);record['id']=digest([destination,old['id']])[:24]
            if record.get('alternative'):
                alt=record['alternative']
                if alt.get('fact_id'):alt['fact_id']=fact_map[alt['fact_id']]
                if alt.get('source_id'):alt['source_id']=source_map[alt['source_id']]
            target.put('clarification_decisions',record['id'],dict(record,import_trust='untrusted_archived_student_decision'))
        result=dict(tenant=destination,restored=True,external_writes=False,revision=1,operational_authority_restored=False)
        target.put('passport_copies',stage_id,result)
        tx.put('passport_stages',stage_id,dict(current,status='committed',result=result))
        # Scope registration is committed in the same database transaction.
        server=tx.workspace('_server')
        server.put('workspaces',destination,dict(id=destination,origin='authenticated_manual_restore',created_at=now()))
        return result
    return svc.store.atomic(svc.tenant,switch)
