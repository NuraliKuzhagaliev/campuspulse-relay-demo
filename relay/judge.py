"""One-use invitations bound to exclusive, preapproved empty demo calendars.

No public registration, shared passwords, calendar reuse or automatic provisioning.
The owner must verify access and supply one separate calendar per visitor.
"""
import os
import re
import secrets
import time
from datetime import datetime, timedelta, time as day_time
from zoneinfo import ZoneInfo
from .domain import RelayError, digest, now


def register(store, calendar_id, hours=4):
    if not calendar_id or calendar_id == 'primary' or not calendar_id.endswith('@group.calendar.google.com'):
        raise RelayError('ACCESS_DENIED', 'Use an owner-approved separate demo calendar, never a primary calendar.')
    if not 1 <= hours <= 12:
        raise RelayError('PARSE_FAILED', 'Judge invitations must last between 1 and 12 hours.')
    lease_id = digest(calendar_id)
    if not store.put('_server', 'judge_calendars', lease_id,
                     dict(id=lease_id, calendar_id=calendar_id, status='reserved', created_at=now()), create=True):
        raise RelayError('ACCESS_DENIED', 'This calendar is already reserved or retired. It cannot be reused by another visitor.')
    invitation = secrets.token_urlsafe(32)
    store.put('_server', 'judge_invites', digest(invitation),
              dict(lease_id=lease_id, status='pending', expires=time.time()+hours*3600,
                   lifetime_seconds=hours*3600), create=True)
    return invitation


def claim(store, invitation):
    if os.getenv('RELAY_JUDGE_ENABLED') != 'true':
        raise RelayError('AUTH_REQUIRED', 'Judge invitations are not enabled. The owner must configure and verify dedicated Calendar access first.')
    if not os.getenv('RELAY_GITHUB_REPO'):
        raise RelayError('AUTH_REQUIRED', 'The owner must configure the dedicated demo repository first.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{40,100}', invitation):
        raise RelayError('ACCESS_DENIED', 'Invitation is invalid, expired or already used.')
    key=digest(invitation)
    try:
        record=store.get('_server','judge_invites',key)
    except RelayError:
        raise RelayError('ACCESS_DENIED', 'Invitation is invalid, expired or already used.')
    if record['expires'] < time.time() or not store.claim('_server','judge_invites',key,{'status':'pending'},{'status':'consumed'}):
        raise RelayError('ACCESS_DENIED', 'Invitation is invalid, expired or already used.')
    tenant='judge-'+secrets.token_hex(24)
    if record.get('kind')=='read_only_ai':
        from .service import RelayService
        expires=min(record['expires'],time.time()+record['lifetime_seconds'])
        svc=RelayService(store,tenant)
        svc.seed()
        settings=svc.settings()
        settings.update(mode='judge_ai',ai_access=True,calendar_live=False,judge_expires=expires,watch_enabled=False)
        store.put(tenant,'meta','settings',settings)
        store.event(tenant,'judge-open','run_completed',summary='Private AI workspace opened. Gemini uses permitted non-sensitive documents; Calendar actions remain illustrative.',mode='judge_ai')
        return tenant,expires
    lease=store.get('_server','judge_calendars',record['lease_id'])
    expires=time.time()+record['lifetime_seconds']
    if not store.claim('_server','judge_calendars',record['lease_id'],{'status':'reserved'},
                       {'status':'leased','tenant':tenant,'expires':expires}):
        raise RelayError('ACCESS_DENIED', 'This dedicated calendar is unavailable. Ask the owner for a fresh invitation.')
    zone=ZoneInfo('Asia/Almaty')
    today=datetime.now(zone).date()
    monday=today+timedelta(days=(7-today.weekday())%7)
    def at(day,hour):
        return datetime.combine(monday+timedelta(days=day),day_time(hour),zone).isoformat()
    settings=dict(mode='judge',timezone='Asia/Almaty',anchor=monday.isoformat(),
                  windows=[{'start':at(d,18),'end':at(d,20)} for d in range(5)],daily_cap_minutes=240,
                  calendar_id=lease['calendar_id'],calendar_live=True,
                  github_repo=os.environ['RELAY_GITHUB_REPO'],github_ref='main',github_path='coursework.md',
                  watch_enabled=False,judge_expires=expires,
                  availability_assumption='Demo draft windows: weekdays 18:00–20:00. Confirm before planning.')
    store.put(tenant,'meta','settings',settings)
    store.event(tenant,'judge-open','run_completed',summary='Exclusive judge workspace opened. Upload permitted academic material; Calendar operations are real and require approval.',mode='judge')
    return tenant,expires


def register_ai(store,hours=2):
    """Owner-side only: AI invitation grants no Google/Calendar permission."""
    if os.getenv('RELAY_MODE')!='alternative_live' or not 1<=hours<=12:
        raise RelayError('ACCESS_DENIED','Read-only AI invitations require the explicitly configured alternative live host and a bounded lifetime.')
    invitation=secrets.token_urlsafe(32)
    store.put('_server','judge_invites',digest(invitation),dict(kind='read_only_ai',status='pending',expires=time.time()+hours*3600,lifetime_seconds=hours*3600),create=True)
    return invitation
