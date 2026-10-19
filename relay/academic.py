"""Conservative multilingual extraction with document-wide, page-cited entities.

Structured fields are exact observations. Prose/table ambiguity is retained for
the semantic proposal/review flow, never silently converted to a deadline.
"""
import re,copy
from collections import Counter
from .domain import digest, instant, RelayError
from .identity import mapping, section_key, canonical

TITLE=r'assignment|lab|report|project|deliverable|задание|лабораторная(?: работа)?|отчёт|отчет|проект|тапсырма|зертханалық жұмыс|жоба|есеп'
KEYS={
 'title':TITLE,
 'course':r'course|курс|пән|дисциплина',
 'term':r'term|semester|семестр|оқу кезеңі',
 'assignment_key':r'assignment id|assignment key|код задания|идентификатор|тапсырма коды',
 'due':r'due|deadline|срок(?: сдачи)?|дедлайн|мерзім[іы]?|тапсыру мерзімі',
 'minutes':r'effort|estimate|оценка|трудоёмкость|трудоемкость|ұзақтығы|еңбек шығыны',
}
ISO=r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})'
EFFORT=re.compile(r'(\d+)(?:\s*[-–]\s*(\d+))?\s*(minutes?|mins?|hours?|h\b|минут\w*|мин\b|час\w*|сағат\w*)',re.I)
FIELD=re.compile(r'^\s*(?:#{1,6}\s*)?(?:\*\*)?('+ '|'.join(KEYS.values())+r')(?:\*\*)?\s*[:：]\s*(?:\*\*)?(.*?)\s*$',re.I)
def clean(value):return value.strip().strip('*').strip()
def kind(key):
    return next((k for k,v in KEYS.items() if re.fullmatch(v,key,re.I)),None)

def extract_facts(source):
    from .evidence import ACADEMIC
    rows=[dict(page=p['page'],quote=line,text=clean(re.sub(r'^\s*#{1,6}\s*','',line))) for p in source['pages'] for line in p['text'].splitlines() if line.strip()]
    if not ACADEMIC.search('\n'.join(r['text'] for r in rows)):return [],[]
    groups=[];current=None;preamble=[];global_rows=[]
    for row in rows:
        field=FIELD.match(row['quote']);k=kind(field[1]) if field else None
        heading=bool(re.match(r'^\s*#{1,6}\s+',row['quote']))
        if k=='title' or (heading and re.search(r'\b('+TITLE+r')\b',row['text'],re.I)):
            title=clean(field[2]) if k=='title' else row['text']
            if current is None:
                global_rows=[dict(r,_global=True) for r in preamble if (m:=FIELD.match(r['quote'])) and kind(m[1]) in ('course','term')]
                context=list(preamble)
            else:context=list(global_rows)
            current=dict(title=title,rows=context+[row]);groups.append(current);preamble=[]
        elif current is None:preamble.append(row)
        else:current['rows'].append(row)
    if not groups:
        # A prose document remains one reviewable entity, rather than zero
        # drafts. Its provisional label is not a source-confirmed task title.
        groups=[dict(title=rows[0]['text'][:120],rows=rows,prose=True)] if rows else []
    counts=Counter(canonical(g['title']) for g in groups);occurrences=Counter();facts=[];drafts=[]
    for group in groups:
        values={};observations=[];rubric=[]
        local_fields={kind(m[1]) for r in group['rows'] if not r.get('_global') and (m:=FIELD.match(r['quote']))}
        for row in group['rows']:
            match=FIELD.match(row['quote'])
            if row.get('_global') and match and kind(match[1]) in local_fields:continue
            if match:
                k=kind(match[1]);value=clean(match[2])
                if k not in ('due','minutes'):values[k]=value
                observations.append(dict(field=k,value=value,quote=row['quote'],page=row['page']))
            # Prose due and effort markers can occur mid-line. An incomplete
            # date stays unknown; locale/month/year are never guessed.
            if (not match or kind(match[1])!='due') and re.search(r'\b(due|deadline)\b|срок|дедлайн|мерзім|тапсыру',row['text'],re.I):
                observations.append(dict(field='due',value=row['text'],quote=row['quote'],page=row['page']))
            if (not match or kind(match[1])!='minutes') and re.search(r'estimat|effort|оцен|минут|сағат|часов|hours?\b',row['text'],re.I) and EFFORT.search(row['text']):
                observations.append(dict(field='minutes',value=row['text'],quote=row['quote'],page=row['page']))
            item=re.match(r'^\s*[-*]\s*(?:\[\s*\]\s*)?(.+)',row['quote'])
            if item and not FIELD.match(item[1]):
                rubric.append(item[1].strip());observations.append(dict(field='rubric',value=item[1].strip(),quote=item[1].strip(),page=row['page']))
            if re.match(r'(?i)^(Filename|Format|Sections|Words|Pages|Required files|Filename exception)\s*:',row['text']):
                observations.append(dict(field='submission_requirement',value=row['text'],quote=row['quote'],page=row['page']))
        title=values.get('title') or group['title'];course=values.get('course');term=values.get('term');key=values.get('assignment_key')
        signature=(canonical(title),canonical(course),canonical(term),canonical(key));occurrences[signature]+=1
        # Source-local context and occurrence disambiguate identical titles.
        entity=digest(['section-v3',signature,occurrences[signature]])[:24]
        identity=mapping(source,title,course,term,key,entity,counts[canonical(title)]==1)
        due=minutes=maximum=None;evidence=[]
        for obs in observations:
            field=obs['field'];value=obs['value'];status='explicit';extra={}
            if field=='due':
                m=re.search(ISO,str(value));value=m.group() if m else None
                if value:
                    try:instant(value);due=value
                    except RelayError:value=None;status='invalid'
                else:status='ambiguous' if re.search(r'\d|friday|monday|пятниц|жұма',obs['quote'],re.I) else 'missing'
            elif field=='minutes':
                m=EFFORT.search(str(value));value=None
                if m:
                    multiplier=60 if re.match(r'h|час|сағат',m[3],re.I) else 1
                    a=int(m[1])*multiplier;b=int(m[2])*multiplier if m[2] else a
                    if 0<a<=b<=10080:minutes,value,maximum=a,a,b
                if value is None:status='invalid'
                extra['kind']='explicit_estimate'
            evidence.append(dict(obs,value=value,status=status,**extra))
        task=dict(id=identity['id'],title=title[:180],course=identity['course'],identity=identity,section_key=entity,
                  due=due,minutes=minutes,effort_max=maximum,solver_allocation_minutes=((minutes+29)//30*30 if minutes else None),
                  source_ids=[source['id']],rubric=rubric,completion='planned',dependencies=[],priority=1,
                  extraction_origin='prose_needs_review' if group.get('prose') else 'deterministic_fields')
        task['gaps']=[k for k in ('due','minutes') if task[k] is None]+(['identity'] if identity['status']=='unresolved' else [])
        if group.get('prose'):task['gaps'].append('semantic_review')
        drafts.append(task)
        for e in sorted(evidence,key=lambda e: {'due':0,'minutes':1,'rubric':2,'submission_requirement':3}.get(e['field'],4)):
            facts.append(dict(id=digest([source['id'],source['version'],entity,e])[:24],task_id=task['id'],source_id=source['id'],
                              source_version=source['version'],hash=source['content_hash'],fetched_at=source['fetched_at'],
                              timezone=source.get('timezone','Asia/Almaty'),**({'kind':'explicit'}|e)))
    accepted={r['task']['id']:r['task'] for r in source.get('confirmed_extractions',[])}
    if accepted:
        drafts=[d for d in drafts if d['id'] not in accepted and d.get('extraction_origin')!='prose_needs_review']+[copy.deepcopy(t) for t in accepted.values()]
        facts=[f for f in facts if f['task_id'] not in accepted]+[copy.deepcopy(f) for f in source.get('facts',[]) if f['task_id'] in accepted]
    return facts,drafts
