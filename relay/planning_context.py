"""Human date/time controls converted in the chosen workspace zone, with DST checks."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .domain import RelayError, instant
from .timezones import workspace_timezone

def local_timestamp(value,timezone):
    try:
        if not isinstance(value,str) or len(value)>32:raise ValueError()
        naive=datetime.fromisoformat(value)
        if naive.tzinfo is not None:raise ValueError()
        zone=ZoneInfo(timezone);a=naive.replace(tzinfo=zone,fold=0);b=naive.replace(tzinfo=zone,fold=1)
        if a.utcoffset()!=b.utcoffset():raise ValueError()
        if instant(a.isoformat()).astimezone(zone).replace(tzinfo=None)!=naive:raise ValueError()
        return a.isoformat()
    except Exception as exc:raise RelayError('AMBIGUOUS_TIME','This local time is invalid or ambiguous in the selected timezone. Choose an unambiguous time; DST is never guessed.') from exc

def update(svc,body):
    zone=workspace_timezone(body.get('timezone'))
    try:
        start=datetime.strptime(body['start_date'],'%Y-%m-%d').date();end=datetime.strptime(body['end_date'],'%Y-%m-%d').date()
        if not 0<=(end-start).days<=30:raise ValueError()
        days=body['weekdays']
        if not isinstance(days,list) or any(type(v) is not int or not 0<=v<=6 for v in days):raise ValueError()
        a=datetime.strptime(body['start_time'],'%H:%M').time();b=datetime.strptime(body['end_time'],'%H:%M').time()
        if a.minute%30 or b.minute%30 or a==b:raise ValueError()
    except Exception as exc:raise RelayError('PARSE_FAILED','Choose a timezone, a date range up to 31 days, weekdays and half-hour study times.') from exc
    windows=[];day=start
    while day<=end:
        if day.weekday() in days:
            finish=day+timedelta(days=1) if b<a else day
            windows.append(dict(start=local_timestamp(day.isoformat()+'T'+a.isoformat(),zone),end=local_timestamp(finish.isoformat()+'T'+b.isoformat(),zone)))
        day+=timedelta(days=1)
    s=svc.settings();s.update(timezone=zone,anchor=start.isoformat(),range_end=end.isoformat(),windows=windows)
    svc.store.put(svc.tenant,'meta','settings',s);svc.invalidate_plans()
    return s
