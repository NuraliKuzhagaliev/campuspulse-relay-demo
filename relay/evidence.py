"""Bounded text imports. Every extracted value retains an exact source quote."""
import io
import re
from datetime import datetime, date, time, timedelta
from pathlib import PurePath
from zoneinfo import ZoneInfo
from .domain import RelayError, digest, now, instant
from .identity import mapping, section_key

MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 250_000
ACADEMIC = re.compile(r'\b(assignment|syllabus|rubric|course|lab|report|project|deliverable|deadline)\b|задани|дедлайн|тапсырма|силлабус|отч[её]т|жоба|есеп|курс|лаборатор', re.I)
ISO = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})'

import threading
_pdf_slot=threading.Semaphore(1)

def bounded_pdf(content):
    import subprocess, sys, json, os
    with _pdf_slot:
        try:
            result=subprocess.run([sys.executable,'-m','relay.pdf_worker'],input=content,stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL,timeout=8,creationflags=0x08000000 if os.name=='nt' else 0)
            value=json.loads(result.stdout) if result.returncode==0 else {}
        except (subprocess.TimeoutExpired,ValueError):value={}
    if not value.get('pages'):
        reason=value.get('error','parse_or_resource_limit')
        raise RelayError('UNSUPPORTED_INPUT','PDF import stopped: '+reason+'. Use an unlocked text PDF within the page/text/resource limits; scanned PDF OCR is unavailable.')
    return value['pages']


def read_upload(name: str, content: bytes, timezone='Asia/Almaty', horizon=None):
    if not content or len(content) > MAX_BYTES:
        raise RelayError('UNSUPPORTED_INPUT', 'Choose a non-empty PDF, Markdown, TXT or ICS file up to 2 MiB.')
    if '/' in name or '\\' in name or '\x00' in name or name.startswith('.'):
        raise RelayError('ACCESS_DENIED', 'Only a filename is accepted; paths are not allowed.')
    ext = PurePath(name).suffix.lower()
    pages = []
    try:
        if ext == '.pdf':
            pages = bounded_pdf(content)
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
    if not any(p['text'].strip() for p in pages):
        raise RelayError('EMPTY_CONTENT','The file has no readable text. Export a non-empty text document.')
    return dict(pages=pages, content_hash=digest(content.hex()), type=ext[1:], fetched_at=now())


from .academic import extract_facts


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
