import base64
import os
import re
import time as monotime
import threading,copy
from collections import OrderedDict
from datetime import datetime, time
from urllib.parse import quote
from zoneinfo import ZoneInfo
import httpx
from .domain import RelayError, digest, instant, now


def upstream_error(status):
    code = {401:'AUTH_REQUIRED',403:'ACCESS_DENIED',429:'UPSTREAM_RATE_LIMITED'}.get(status,'UPSTREAM_UNAVAILABLE')
    return RelayError(code, f'External service returned HTTP {status}. Reconnect or retry as appropriate.')


class GitHub:
    _public_backoff_until=0
    _entity_cache=OrderedDict()
    _immutable_documents=OrderedDict()
    _entity_lock=threading.RLock()
    def __init__(self, repo, ref='main', token=None):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo or ''):
            raise RelayError('ACCESS_DENIED','Select an owner/repository before connecting GitHub.')
        if not re.fullmatch(r'[A-Za-z0-9_./-]{1,100}',ref) or '..' in ref:
            raise RelayError('ACCESS_DENIED','Invalid repository ref.')
        self.repo,self.ref,self.token = repo,ref,token

    def get(self,path):
        with self._entity_lock:return self._get(path)

    def _get(self,path):
        if not self.token and monotime.time()<GitHub._public_backoff_until:
            raise RelayError('UPSTREAM_RATE_LIMITED','GitHub public API quota is exhausted. Wait for reset or configure the dedicated repository read credential.',{'retry_at_epoch':GitHub._public_backoff_until})
        headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
        if self.token:
            headers['Authorization']=f'Bearer {self.token}'
        key=(self.repo,path,bool(self.token));cached=self._entity_cache.get(key)
        if cached:
            if cached.get('etag'):headers['If-None-Match']=cached['etag']
            elif cached.get('last_modified'):headers['If-Modified-Since']=cached['last_modified']
        try:
            with httpx.Client(timeout=15,follow_redirects=False) as client:
                with client.stream('GET',f'https://api.github.com/repos/{self.repo}/{path}',headers=headers) as r:
                    if r.status_code==304 and cached:return copy.deepcopy(cached['value'])
                    if r.status_code!=200:
                        if r.status_code==429 or (r.status_code==403 and (r.headers.get('x-ratelimit-remaining')=='0' or r.headers.get('retry-after'))):
                            try:
                                reset=float(r.headers.get('x-ratelimit-reset','0'))+60
                            except ValueError:
                                reset=monotime.time()+900
                            reset=max(reset,monotime.time()+60)
                            try:reset=max(reset,monotime.time()+float(r.headers.get('retry-after','0')))
                            except ValueError:pass
                            if not self.token:
                                GitHub._public_backoff_until=reset
                            raise RelayError('UPSTREAM_RATE_LIMITED','GitHub API quota reached. The last observation is retained; no fresh read is claimed.',{'retry_at_epoch':reset})
                        raise upstream_error(r.status_code)
                    body=b''
                    for chunk in r.iter_bytes():
                        body+=chunk
                        if len(body)>1_500_000:
                            raise RelayError('UNSUPPORTED_INPUT','Repository response exceeds the bounded limit.')
                    import json
                    value=json.loads(body)
                    while len(self._entity_cache)>=32:self._entity_cache.popitem(last=False)
                    self._entity_cache[key]=dict(value=value,etag=r.headers.get('etag'),last_modified=r.headers.get('last-modified'))
                    return copy.deepcopy(value)
        except httpx.RequestError as exc:
            raise RelayError('UPSTREAM_UNAVAILABLE','GitHub could not be reached within 15 seconds.') from exc

    def status(self):
        from .public_demo import read_public_source
        return read_public_source(self.repo,self.ref+('|server-credential' if self.token else ''),'_status',self._status)

    def _status(self):
        commit=self.get('commits/'+quote(self.ref,safe=''))
        issues=self.get('issues?state=all&per_page=30')
        return dict(mode='live',repository=self.repo,url=f'https://github.com/{self.repo}',ref=self.ref,
                    commit=commit['sha'],updated_at=commit['commit']['committer']['date'],
                    issues=[dict(number=i['number'],title=i['title'],state=i['state'],url=i['html_url'],updated_at=i['updated_at']) for i in issues if 'pull_request' not in i],fetched_at=now())

    def read(self,path='README.md'):
        from .public_demo import read_public_source
        return read_public_source(self.repo,self.ref+('|server-credential' if self.token else ''),path,lambda:self._read(path))

    def _read(self,path='README.md'):
        if not re.fullmatch(r'[A-Za-z0-9_./-]{1,160}',path) or '..' in path or path.startswith('/') or not path.lower().endswith(('.md','.txt')):
            raise RelayError('ACCESS_DENIED','Read only a bounded Markdown/TXT file inside the selected repository.')
        # Resolve a ref first so the content URL and recorded commit identify the same immutable bytes.
        commit_info=self.get('commits/'+quote(self.ref,safe=''))
        commit=commit_info['sha']
        key=(self.repo,commit,path,bool(self.token))
        if key in self._immutable_documents:
            return dict(copy.deepcopy(self._immutable_documents[key]),ref_checked_at=now(),immutable_content_cached=True)
        obj=self.get(f'contents/{quote(path,safe="/")}?ref={commit}')
        if obj.get('size',0)>250_000 or obj.get('encoding')!='base64':
            raise RelayError('UNSUPPORTED_INPUT','Choose a text source below 250,000 bytes.')
        text=base64.b64decode(obj['content']).decode('utf-8')
        value=dict(text=text,commit=commit,committed_at=commit_info['commit']['committer']['date'],blob=obj['sha'],url=f'https://github.com/{self.repo}/blob/{commit}/{path}',fetched_at=now(),mode='live')
        while len(self._immutable_documents)>=16:self._immutable_documents.popitem(last=False)
        self._immutable_documents[key]=copy.deepcopy(value)
        return value


class LocalCalendar:
    mode='illustrative'
    id='local-illustrative-calendar'
    def __init__(self,store,tenant):
        self.store,self.tenant=store,tenant

    def list(self,start,end):
        return [e for e in self.store.list(self.tenant,'calendar') if e.get('status')!='cancelled' and instant(e['start']['dateTime'])<instant(end) and instant(start)<instant(e['end']['dateTime'])]

    def get(self,id):
        return self.store.get(self.tenant,'calendar',id)

    def insert(self,event):
        if not self.store.put(self.tenant,'calendar',event['id'],dict(event,etag=digest(event)),create=True):
            return self.get(event['id'])
        return self.get(event['id'])

    def delete(self,id,etag):
        current=self.get(id)
        if current.get('etag')!=etag:
            raise RelayError('SOURCE_CONFLICT','Calendar event changed; it was preserved.')
        current['status']='cancelled'
        self.store.put(self.tenant,'calendar',id,current)


class GoogleCalendar:
    mode='live'
    def __init__(self,calendar_id,credentials=None):
        if not calendar_id or calendar_id=='primary':
            raise RelayError('AUTH_REQUIRED','Configure an explicitly authorized dedicated calendar ID; primary is not accepted for demo writes.')
        self.id=calendar_id
        if credentials is None:
            import google.auth
            try:
                credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/calendar.events'])
            except Exception as exc:
                raise RelayError('AUTH_REQUIRED','Google Calendar consent or shared service-account access is required.') from exc
        from google.auth.transport.requests import AuthorizedSession
        self.session=AuthorizedSession(credentials)
        self.base=f'https://www.googleapis.com/calendar/v3/calendars/{quote(self.id,safe="")}/events'

    def request(self,method,url,**kwargs):
        try:
            r=self.session.request(method,url,timeout=20,**kwargs)
        except Exception as exc:
            raise RelayError('UPSTREAM_UNAVAILABLE','Calendar request failed; the operation may need reconciliation.') from exc
        if r.status_code not in (200,201,204):
            if r.status_code==410:
                raise RelayError('SYNC_TOKEN_EXPIRED','Calendar requires a full resynchronization.')
            if r.status_code==404:
                raise RelayError('NOT_FOUND','Calendar event was not found.')
            if r.status_code==409:
                raise RelayError('ALREADY_EXISTS','Deterministic Calendar ID already exists; read it back.')
            if r.status_code==412:
                raise RelayError('SOURCE_CONFLICT','Event changed since verification; it was preserved.')
            raise upstream_error(r.status_code)
        return r.json() if r.content else {}

    def list(self,start,end):
        params=dict(timeMin=start,timeMax=end,singleEvents='true',maxResults=2500)
        events=[]
        while True:
            result=self.request('GET',self.base,params=params)
            events.extend(e for e in result.get('items',[]) if e.get('status')!='cancelled')
            if len(events)>5000:
                raise RelayError('UNSUPPORTED_INPUT','Calendar window contains too many events; narrow it.')
            if not result.get('nextPageToken'):
                return events
            params['pageToken']=result['nextPageToken']

    def sync(self,token=None):
        # Sync requests intentionally omit timeMin/orderBy and keep the same parameters across pages.
        params=dict(maxResults=2500,showDeleted='true')
        if token:
            params['syncToken']=token
        events=[]
        while True:
            try:
                result=self.request('GET',self.base,params=params)
            except RelayError as exc:
                if exc.code=='SYNC_TOKEN_EXPIRED' and token:
                    return dict(self.sync(None),full_resync=True)
                raise
            events.extend(result.get('items',[]))
            if len(events)>10000:
                raise RelayError('UNSUPPORTED_INPUT','Calendar sync exceeds 10,000 records.')
            if not result.get('nextPageToken'):
                return dict(events=events,sync_token=result.get('nextSyncToken'),full_resync=not bool(token))
            params['pageToken']=result['nextPageToken']

    def get(self,id):
        return self.request('GET',self.base+'/'+quote(id,safe=''))

    def insert(self,event):
        try:
            return self.request('POST',self.base,params={'sendUpdates':'none'},json=event)
        except RelayError as exc:
            if exc.code=='ALREADY_EXISTS':
                return self.get(event['id'])
            raise

    def delete(self,id,etag):
        self.request('DELETE',self.base+'/'+quote(id,safe=''),params={'sendUpdates':'none'},headers={'If-Match':etag})


def busy_intervals(events,timezone='Asia/Almaty',exclude_owned=None,exclude_ids=None):
    zone=ZoneInfo(timezone)
    out=[]
    for e in events:
        if exclude_ids and e['id'] in exclude_ids:
            continue
        if e.get('transparency')=='transparent' or e.get('status')=='cancelled':
            continue
        if exclude_owned and e.get('extendedProperties',{}).get('private',{}).get('relay_workspace')==exclude_owned:
            continue
        a,b=e.get('start',{}),e.get('end',{})
        if 'date' in a:
            a=datetime.combine(datetime.fromisoformat(a['date']).date(),time.min,zone).isoformat()
            b=datetime.combine(datetime.fromisoformat(b['date']).date(),time.min,zone).isoformat()
        else:
            a,b=a.get('dateTime'),b.get('dateTime')
        if a and b:
            out.append(dict(start=a,end=b))
    return out
