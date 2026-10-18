import copy
import pytest
from relay.domain import RelayError
from relay.service import RelayService
from relay.store import Store
from relay.actions import Actions


@pytest.fixture
def service(tmp_path):
    s=RelayService(Store(tmp_path/'db'),'reliability-student');s.seed('2026-10-19')
    c=s.current_conflicts()[0];s.resolve(c['id'],min(c['facts'],key=lambda f:f['value'])['id'])
    return s


def test_partial_apply_reconciles_timeout_after_write(service):
    cal=service.calendar()
    original=cal.insert
    count=0
    def timeout_after_insert(event):
        nonlocal count
        value=original(event);count+=1
        if count==1:
            raise RelayError('UPSTREAM_UNAVAILABLE','Injected timeout after external success')
        return value
    cal.insert=timeout_after_insert
    actions=Actions(service.store,service.tenant,cal,service.source_versions)
    preview=actions.preview(service.plan());id=actions.authorize(preview['id'],preview['digest'],service.tenant)
    first=actions.apply(id)
    assert first['status']=='partial' and first['outcomes'][0]['status']=='unknown'
    cal.insert=original
    second=actions.apply(id)
    assert second['status']=='verified'
    assert len(cal.list(**preview['window']))==len(preview['actions'])+1


def test_mismatch_during_apply_is_partial(service):
    cal=service.calendar();original=cal.get
    def edited_readback(id):
        event=original(id)
        if id!='protected-commitment':
            event['summary']='Unexpected external value'
        return event
    cal.get=edited_readback
    actions=Actions(service.store,service.tenant,cal,service.source_versions)
    preview=actions.preview(service.plan());id=actions.authorize(preview['id'],preview['digest'],service.tenant)
    result=actions.apply(id)
    assert result['status']=='partial'
    assert all(o['status']=='mismatch' for o in result['outcomes'])


def test_wrong_digest_and_expired_approval(service):
    a=service.actions();preview=a.preview(service.plan())
    with pytest.raises(RelayError):
        a.authorize(preview['id'],'tampered',service.tenant)
    preview['expires_at']='2020-01-01T00:00:00Z'
    service.store.put(service.tenant,'previews',preview['id'],preview)
    with pytest.raises(RelayError):
        a.authorize(preview['id'],preview['digest'],service.tenant)


def test_source_replacement_only_invalidates_related_plan(service):
    plan=service.plan()
    independent=copy.deepcopy(plan);independent['id']='independent';independent['input']['tasks']=[dict(plan['input']['tasks'][0],id='different-task',source_ids=['unrelated'])]
    service.store.put(service.tenant,'plans','independent',independent)
    source=service.sources()[0]
    service.import_source('replacement.txt',b'Assignment: Revised lab\nDue: 2026-10-21T18:00:00+05:00\nEffort: 240 minutes',id=source['id'])
    assert service.store.get(service.tenant,'plans',plan['id'])['invalidated']
    assert not service.store.get(service.tenant,'plans','independent').get('invalidated',False)


def test_replanning_same_blocks_keeps_existing_events(service):
    a=service.actions();first=a.preview(service.plan());id=a.authorize(first['id'],first['digest'],service.tenant);a.apply(id)
    next_plan=service.plan();second=a.preview(next_plan)
    assert all(op['operation']=='keep' for op in second['actions'])
    second_id=a.authorize(second['id'],second['digest'],service.tenant)
    assert a.apply(second_id)['status']=='verified'
    assert len(service.calendar().list(**second['window']))==len(first['actions'])+1
    assert all(r['status']=='preserved_existing' for r in a.undo(second_id)['results'])


def test_recovery_preview_contains_exact_removals(service):
    a=service.actions();first=a.preview(service.plan());id=a.authorize(first['id'],first['digest'],service.tenant);a.apply(id)
    task=service.tasks()[0]
    service.store.put(service.tenant,'task_overrides',task['id'],{'id':task['id'],'values':{'minutes':task['minutes']-30}})
    revised=service.plan();second=a.preview(revised)
    assert any(op['operation']=='delete' for op in second['actions'])
    second_id=a.authorize(second['id'],second['digest'],service.tenant)
    assert a.apply(second_id)['status']=='verified'
    assert all(r['matches'] for r in a.verify(second_id)['results'])
