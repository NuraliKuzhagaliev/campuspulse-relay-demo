"""Version-bound semantic proposals and atomic, explicit per-entity review."""
import copy,re
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
from .domain import RelayError, instant, digest, now, Task
from .identity import assignment_id
ALLOWED={'title','course','term','assignment_key','due','minutes','rubric','submission_requirement'}

def extraction_proposal(source,candidates):
    if not isinstance(candidates,list) or not 0<len(candidates)<=100:
        raise RelayError('UNSUPPORTED_INPUT','Propose 1–100 cited fields from the selected source.')
    pages={p['page']:p['text'] for p in source['pages']};fields=[];groups={}
    for c in candidates:
        if not isinstance(c,dict):raise RelayError('PARSE_FAILED','Each proposed field must be an object.')
        field=c.get('field');quote=c.get('quote');page=c.get('page');entity=c.get('entity_id','document')
        if not isinstance(entity,str) or not 1<=len(entity)<=80:raise RelayError('PARSE_FAILED','Use a bounded entity label.')
        if field not in ALLOWED or not isinstance(quote,str) or not 0<len(quote)<=4000 or not isinstance(page,int) or isinstance(page,bool) or quote not in pages.get(page,''):
            raise RelayError('SOURCE_CONFLICT','Every proposed field must cite an exact quote on its selected source page.')
        value=c.get('value');status='needs_confirmation';expression=c.get('original_expression',quote)
        if not isinstance(expression,str) or expression not in quote:raise RelayError('SOURCE_CONFLICT','The original expression must occur in the exact quote.')
        if value is None:status='unknown'
        elif field=='due':
            if not isinstance(value,str):value=None;status='invalid'
            else:
                try:instant(value)
                except RelayError:value=None;status='ambiguous'
            if status=='needs_confirmation':
                zone_name=c.get('timezone')
                if not zone_name or not c.get('year_explicit') or c.get('ambiguous'):
                    value=None;status='ambiguous'
                else:
                    try:
                        offset=re.fullmatch(r'(?:UTC|GMT)([+-])(\d{1,2})(?::?(\d{2}))?',zone_name,re.I)
                        zone=timezone(timedelta(minutes=(1 if offset[1]=='+' else -1)*(int(offset[2])*60+int(offset[3] or 0)))) if offset else ZoneInfo(zone_name)
                        cited=datetime.fromisoformat(value.replace('Z','+00:00'))
                        actual=cited.astimezone(zone).utcoffset()
                        if cited.utcoffset()!=actual:
                            raise RelayError('SOURCE_CONFLICT','The proposed deadline offset disagrees with its cited timezone. Re-read the original wall time and explicit offset, then correct the proposal; do not shift the deadline.',{'timezone':zone_name,'provided_offset':str(cited.utcoffset()),'expected_offset':str(actual)})
                    except RelayError:raise
                    except (ValueError,TypeError,KeyError):
                        value=None;status='ambiguous'
        elif field=='minutes':
            if type(value) is not int or not 1<=value<=10080:value=None;status='invalid'
        elif field in ('rubric','submission_requirement'):
            if not (isinstance(value,str) or isinstance(value,list) and all(isinstance(v,str) for v in value)):value=None;status='invalid'
        elif not isinstance(value,str) or not value.strip() or len(value)>180:value=None;status='invalid'
        item=dict(field=field,value=value,page=page,quote=quote,original_expression=expression,source_id=source['id'],source_version=source['version'],hash=source['content_hash'],
                  assumptions=str(c.get('assumptions',''))[:1000],context=str(c.get('context',''))[:1000],timezone=c.get('timezone'),validation_status=status,entity_id=entity)
        fields.append(item);groups.setdefault(entity,[]).append(item)
    grouped=[dict(id=digest([source['id'],source['version'],key])[:24],entity_id=key,fields=fs,status='requires_explicit_confirmation') for key,fs in groups.items()]
    return dict(id=digest([source['id'],source['version'],fields])[:24],source_id=source['id'],source_version=source['version'],source_hash=source['content_hash'],
                proposed_at=now(),fields=fields,entities=grouped,status='requires_explicit_confirmation',applied=False)

def record_proposal(svc,proposal):
    def save(tx):
        source=tx.get('sources',proposal['source_id'])
        if not source or source['version']!=proposal['source_version']:raise RelayError('STALE_REVISION','Source changed during extraction. Review its current version.')
        if tx.get('extraction_proposals',proposal['id']):return proposal
        if len(tx.list('extraction_proposals'))>=24:raise RelayError('UNSUPPORTED_INPUT','This temporary workspace reached its proposal limit. Export reviewed coursework or start a fresh workspace.')
        tx.put('extraction_proposals',proposal['id'],proposal)
        if proposal.get('origin')!='deterministic_review':
            source['active_extraction_proposal']=proposal['id'];tx.put('sources',source['id'],source);tx.advance()
        return proposal
    return svc.store.atomic(svc.tenant,save)

def current_proposals(svc):
    versions={s['id']:s['version'] for s in svc.sources()};latest={};records=[]
    for proposal in sorted(svc.store.list(svc.tenant,'extraction_proposals'),key=lambda p:p['proposed_at']):
        if versions.get(proposal['source_id'])!=proposal['source_version']:continue
        records.append(proposal)
        for entity in proposal['entities']:latest[(proposal['source_id'],entity['id'])]=proposal['id']
    return [dict(p,entities=[e for e in p['entities'] if latest[(p['source_id'],e['id'])]==p['id']]) for p in records if any(latest[(p['source_id'],e['id'])]==p['id'] for e in p['entities'])]

def confirm(svc,proposal_id,entity_id,body):
    if body.get('confirmed') is not True:raise RelayError('APPROVAL_REQUIRED','Review and explicitly confirm this one assignment.')
    values=body.get('values',{})
    if not isinstance(values,dict) or set(values)-ALLOWED:raise RelayError('PARSE_FAILED','Unknown reviewed field.')
    for field in ('title','course','term','assignment_key'):
        if not isinstance(values.get(field),str) or not 1<=len(values[field].strip())<=180:raise RelayError('PARSE_FAILED','Confirm title, course, academic term and assignment key.')
    due=values.get('due');minutes=values.get('minutes')
    if due is not None:instant(due)
    if minutes is not None and (type(minutes) is not int or not 1<=minutes<=10080):raise RelayError('PARSE_FAILED','Effort is an exact positive minute count, or unknown.')
    rubric=values.get('rubric',[])
    if not isinstance(rubric,list) or len(rubric)>50 or any(not isinstance(v,str) or not 0<len(v)<=4000 for v in rubric):raise RelayError('PARSE_FAILED','Use at most 50 bounded rubric items.')
    def operation(tx):
        proposal=tx.get('extraction_proposals',proposal_id)
        if not proposal:raise RelayError('ACCESS_DENIED','Proposal unavailable in this workspace.')
        entity=next((e for e in proposal['entities'] if e['id']==entity_id),None)
        if not entity:raise RelayError('ACCESS_DENIED','Entity unavailable in this proposal.')
        fingerprint=digest(values);source=tx.get('sources',proposal['source_id'])
        if not source or source['version']!=proposal['source_version'] or source['content_hash']!=proposal['source_hash'] or body.get('source_version')!=source['version']:raise RelayError('STALE_REVISION','Source changed. Extract and review the current version; nothing was applied.')
        if entity.get('applied'):
            if entity['confirmation_digest']!=fingerprint:raise RelayError('IDEMPOTENCY_CONFLICT','This entity was already confirmed differently.')
            return dict(task_id=entity['task_id'],duplicate=True,revision=tx.revision())
        tid=assignment_id(values['course'],values['term'],values['assignment_key'])
        identity=dict(id=tid,course=values['course'].strip(),term=values['term'].strip(),assignment_key=values['assignment_key'].strip(),status='confirmed',origin='explicit_semantic_review')
        existing=[d for d in source.get('drafts',[]) if d['section_key']==entity['entity_id']]
        if not existing:existing=[d for d in source.get('drafts',[]) if d['id']==tid]
        if not existing:existing=[d for d in source.get('drafts',[]) if d['title'].casefold()==values['title'].casefold()]
        if len(existing)>1:raise RelayError('SOURCE_CONFLICT','Choose the precise source-local entity; identical titles cannot be merged implicitly.')
        prior=existing[0] if existing else None
        if prior and prior['id']!=tid and any(p['id']==prior['id'] for p in tx.list('progress')):raise RelayError('SOURCE_CONFLICT','Existing progress belongs to the prior identity. Preserve it and explicitly review the mapping first.')
        section=prior['section_key'] if prior else entity['id']
        if any(r['proposal_id']==proposal_id and r['entity_id']!=entity_id and r['task']['id']==tid for r in source.get('confirmed_extractions',[])):
            raise RelayError('SOURCE_CONFLICT','This course/term/assignment key already belongs to a different entity in this proposal. Review the keys; no neighbor was changed.')
        task=dict(id=tid,title=values['title'].strip(),course=identity['course'],identity=identity,section_key=section,due=due,minutes=minutes,effort_max=minutes,
                  solver_allocation_minutes=((minutes+29)//30*30 if minutes else None),source_ids=[source['id']],rubric=rubric,
                  completion='planned',dependencies=[],priority=1,extraction_origin='confirmed_semantic_proposal',gaps=[k for k in ('due','minutes') if values.get(k) is None])
        Task.model_validate(task)
        source['drafts']=[d for d in source.get('drafts',[]) if d is not prior and not (d.get('extraction_origin')=='prose_needs_review' and d.get('identity',{}).get('status')!='confirmed')]+[task]
        kept_ids={d['id'] for d in source['drafts']}
        source['facts']=[f for f in source.get('facts',[]) if f['task_id'] in kept_ids]
        if prior:source['facts']=[f for f in source.get('facts',[]) if f['task_id']!=prior['id']]
        for index,f in enumerate(entity['fields']):
            field=f['field'];reviewed=values.get(field)
            if field in ('rubric','submission_requirement'):reviewed=f['value']
            if reviewed is None:continue
            fact=dict(id=digest([proposal_id,entity_id,index,fingerprint])[:24],task_id=tid,field=field,value=reviewed,quote=f['quote'],page=f['page'],source_id=source['id'],source_version=source['version'],
                      hash=source['content_hash'],fetched_at=source['fetched_at'],timezone=source.get('timezone'),kind='user_confirmed_proposal',status='confirmed',proposal_id=proposal_id,
                      interpretation_changed=reviewed!=f['value'],original_expression=f['original_expression'])
            source.setdefault('facts',[]).append(fact)
        source.setdefault('confirmed_extractions',[]).append(dict(task=copy.deepcopy(task),proposal_id=proposal_id,entity_id=entity_id))
        source.setdefault('assignment_mappings',{})[section]=identity
        tx.put('assignment_mappings',source['id']+'-'+section,dict(identity,source_id=source['id'],source_version=source['version'],section_key=section,confirmed_at=now()))
        entity.update(applied=True,task_id=tid,confirmation_digest=fingerprint,confirmed_at=now(),status='confirmed')
        proposal['applied']=all(e.get('applied') for e in proposal['entities'])
        tx.put('sources',source['id'],source);tx.put('extraction_proposals',proposal_id,proposal)
        revision=tx.advance()
        return dict(task_id=tid,duplicate=False,revision=revision)
    return svc.store.atomic(svc.tenant,operation)
