"""Bounded text imports. Every extracted value retains an exact source quote."""
import io
import re
from datetime import datetime, date, time, timedelta
from pathlib import PurePath
from zoneinfo import ZoneInfo
from .domain import RelayError, digest, now, instant

MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 250_000
ACADEMIC = re.compile(r'\b(assignment|syllabus|rubric|course|lab|report|project|deliverable|deadline)\b|задани|дедлайн|тапсырма|силлабус', re.I)
ISO = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})'


def read_upload(name: str, content: bytes, timezone='Asia/Almaty', horizon=None):
    if not content or len(content) > MAX_BYTES:
        raise RelayError('UNSUPPORTED_INPUT', 'Choose a non-empty file up to 10 MiB.')
    if '/' in name or '\\' in name or '\x00' in name or name.startswith('.'):
        raise RelayError('ACCESS_DENIED', 'Only a filename is accepted; paths are not allowed.')
    ext = PurePath(name).suffix.lower()
    pages = []
    try:
        if ext == '.pdf':
            from pypdf import PdfReader
            doc = PdfReader(io.BytesIO(content))
            if doc.is_encrypted:
                raise RelayError('UNSUPPORTED_INPUT', 'Unlock the encrypted PDF before import.')
            if len(doc.pages)>100:
                raise RelayError('UNSUPPORTED_INPUT', 'Import at most 100 pages at a time.')
            for i, page in enumerate(doc.pages):
                pages.append(dict(page=i+1, text=page.extract_text() or ''))
            if not any(p['text'].strip() for p in pages):
                raise RelayError('UNSUPPORTED_INPUT', 'This PDF has no extractable text. Scanned PDF OCR is not configured.')
        elif ext in ('.md','.txt'):
            pages = [dict(page=1, text=content.decode('utf-8-sig'))]
        elif ext == '.ics':
            return read_ics(content,timezone,horizon)
        else:
            raise RelayError('UNSUPPORTED_INPUT', 'Supported imports: text PDF, Markdown, TXT and ICS.')
    except RelayError:
        raise
    except Exception as exc:
        raise RelayError('PARSE_FAILED', 'The file could not be read. Check encoding or export a fresh copy.') from exc
    if sum(len(p['text']) for p in pages)>MAX_TEXT:
        raise RelayError('UNSUPPORTED_INPUT','Extracted text exceeds 250,000 characters; split the document.')
    return dict(pages=pages, content_hash=digest(content.hex()), type=ext[1:], fetched_at=now())


def extract_facts(source: dict):
    facts, drafts = [], []
    for page in source['pages']:
        text = page['text']
        if not ACADEMIC.search(text):
            continue
        sections = re.split(r'(?m)^#{1,3}\s+', text)
        for section in sections:
            if not ACADEMIC.search(section):
                continue
            title_match = re.search(r'(?im)^(?:Assignment|Lab|Report|Project|Задание|Тапсырма)\s*:\s*(.+)$',section)
            title = title_match.group(1).strip() if title_match else section.split('\n')[0].strip()[:120]
            if not title or title.lower() in ('syllabus','course','rubric'):
                continue
            if not title_match and not re.search(r'\b(assignment|lab|report|project)\b|задани|тапсырма',title,re.I):
                continue # Academic overview/preamble is evidence, not an invented assignment.
            task_id = digest(title.lower())[:16]
            due = None
            evidence = []
            for line in section.splitlines():
                if re.search(r'\b(due|deadline)\b|срок|дедлайн|мерзім',line,re.I):
                    match = re.search(ISO,line)
                    if match:
                        try:
                            instant(match.group())
                            due = match.group()
                            evidence.append(dict(field='due',value=due,quote=line.strip(),page=page['page']))
                        except RelayError:
                            evidence.append(dict(field='due',value=None,quote=line.strip(),page=page['page'],status='invalid'))
                    else:
                        evidence.append(dict(field='due',value=None,quote=line.strip(),page=page['page'],status='ambiguous' if re.search(r'\d|Friday|Monday',line,re.I) else 'missing'))
            effort = re.search(r'(?im)^(?:Effort|Estimate)\s*:\s*(\d+)(?:\s*-\s*(\d+))?\s*(minutes?|mins?|hours?|h)\b',section)
            minutes = None
            effort_max = None
            if effort:
                multiplier = 60 if effort[3].startswith('h') else 1
                minutes = int(effort[1])*multiplier
                effort_max = int(effort[2])*multiplier if effort[2] else minutes
                if minutes < 30 or minutes % 30 or effort_max % 30 or effort_max < minutes:
                    minutes = effort_max = None
                evidence.append(dict(field='minutes',value=minutes,quote=effort.group(),page=page['page'],kind='explicit_estimate'))
            rubric = [m.group(1).strip() for m in re.finditer(r'(?m)^\s*-\s*\[\s*\]\s*(.+)$',section)]
            for quote in rubric:
                evidence.append(dict(field='rubric',value=quote,quote=quote,page=page['page']))
            course = re.search(r'(?im)^Course\s*:\s*(.+)$',section)
            task = dict(id=task_id,title=title,course=course[1].strip() if course else 'Unassigned course',
                        due=due,minutes=minutes,effort_max=effort_max,source_ids=[source['id']],rubric=rubric,
                        completion='planned',dependencies=[],priority=1)
            drafts.append(dict(**task,gaps=[k for k in ('due','minutes') if task[k] is None]))
            for e in evidence:
                facts.append(dict(id=digest([source['id'],source['version'],task_id,e])[:24],task_id=task_id,
                                  source_id=source['id'],source_version=source['version'],hash=source['content_hash'],
                                  fetched_at=source['fetched_at'],timezone=source.get('timezone','Asia/Almaty'),
                                  status=e.get('status','explicit'),kind=e.get('kind','explicit'),**{k:v for k,v in e.items() if k not in ('status','kind')}))
    return facts,drafts


def conflicts(facts):
    grouped = {}
    for f in facts:
        if f['field'] == 'due' and f['value'] is not None:
            grouped.setdefault(f['task_id'], []).append(f)
    return [dict(id=digest([tid,sorted(f['id'] for f in fs)])[:24],task_id=tid,facts=fs,status='unresolved')
            for tid,fs in grouped.items() if len({instant(f['value']) for f in fs})>1]


def read_ics(content, timezone, horizon=None):
    import icalendar
    import recurring_ical_events
    from datetime import timezone as tz
    zone = ZoneInfo(timezone)
    start = instant(horizon['start']) if horizon else datetime.now(tz.utc)
    end = instant(horizon['end']) if horizon else start+timedelta(days=31)
    if end<=start or end-start>timedelta(days=90):
        raise RelayError('UNSUPPORTED_INPUT','ICS expansion horizon must be positive and at most 90 days.')
    calendar = icalendar.Calendar.from_ical(content)
    events = []
    for event in recurring_ical_events.of(calendar).between(start,end):
        if len(events)>=2000:
            raise RelayError('UNSUPPORTED_INPUT','ICS recurrence exceeds 2,000 occurrences.')
        a = event.decoded('dtstart')
        b = event.decoded('dtend', a+timedelta(days=1) if isinstance(a,date) and not isinstance(a,datetime) else a+timedelta(hours=1))
        all_day = not isinstance(a,datetime)
        if all_day:
            a,b = datetime.combine(a,time.min,zone),datetime.combine(b,time.min,zone)
        elif a.tzinfo is None:
            raise RelayError('PARSE_FAILED','Floating ICS times require a TZID or UTC offset.')
        events.append(dict(id=str(event.get('uid',''))+a.isoformat(),title=str(event.get('summary','Unavailable')),
                           start=a.isoformat(),end=b.isoformat(),all_day=all_day))
    return dict(type='ics',events=events,content_hash=digest(content.hex()),fetched_at=now())
