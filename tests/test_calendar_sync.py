from relay.connectors import GoogleCalendar,busy_intervals
from relay.domain import RelayError


def test_incremental_pagination_keeps_sync_parameters_and_full_resync():
    cal=object.__new__(GoogleCalendar);cal.base='https://www.googleapis.com/calendar/v3/calendars/owned/events'
    calls=[]
    def request(method,url,params):
        calls.append(dict(params))
        if params.get('syncToken')=='expired':
            raise RelayError('SYNC_TOKEN_EXPIRED','Reset required')
        if not params.get('pageToken'):
            return {'items':[{'id':'one'}],'nextPageToken':'second'}
        return {'items':[{'id':'two','status':'cancelled'}],'nextSyncToken':'new-token'}
    cal.request=request
    result=cal.sync('expired')
    assert result['full_resync']
    assert result['sync_token']=='new-token'
    assert len(result['events'])==2
    assert calls[0]['syncToken']=='expired'
    assert all('timeMin' not in call and 'orderBy' not in call for call in calls)
    assert 'syncToken' not in calls[1] and 'syncToken' not in calls[2]


def test_all_day_busy_and_transparency():
    events=[{'id':'all-day','start':{'date':'2026-10-19'},'end':{'date':'2026-10-20'}},
            {'id':'transparent','transparency':'transparent','start':{'date':'2026-10-19'},'end':{'date':'2026-10-20'}}]
    values=busy_intervals(events,'Asia/Almaty')
    assert len(values)==1
    assert values[0]['start']=='2026-10-19T00:00:00+05:00'
    assert values[0]['end']=='2026-10-20T00:00:00+05:00'
