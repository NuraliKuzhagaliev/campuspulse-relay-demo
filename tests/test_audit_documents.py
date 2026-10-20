"""Audit U1–U13 holdouts; deterministic checks never invoke Gemini or Calendar."""
import copy
import io
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from relay.domain import RelayError,instant
from relay.evidence import read_upload,extract_facts,MAX_BYTES
from relay.extraction import extraction_proposal,validated_batch,record_proposal,current_proposals,confirm,page_citations,visible_citations
from relay.service import RelayService
from relay.store import Store
from relay.planning_context import local_timestamp,update

def source(text):return read_upload('unseen.md',text.encode())|{'id':'unseen','version':'v1'}
def service(tmp_path):
    svc=RelayService(Store(tmp_path/'audit.sqlite3'),'audit-owner');svc.create_empty();return svc

@pytest.mark.parametrize('title,course,term,due,effort',[
 ('Assignment','Course','Term','Due','Effort'),('Задание','Курс','Семестр','Срок','Оценка'),('Тапсырма','Пән','Семестр','Мерзімі','Ұзақтығы')])
@pytest.mark.parametrize('style',['plain','bold','indented'])
def test_multilingual_shuffled_fields(title,course,term,due,effort,style):
    rows=[f'{title}: Spectrum',f'{term}: Autumn 2026',f'{course}: Optics','Unknown extra field: harmless',f'{effort}: 45 minutes',f'{due}: 2026-10-23T18:00:00+05:00']
    if style=='bold':rows=['**'+r.split(':',1)[0]+':**'+r.split(':',1)[1] for r in rows]
    if style=='indented':rows=['    '+r for r in rows]
    s=source('\n'.join(rows));facts,tasks=extract_facts(s)
    assert len(tasks)==1 and tasks[0]['minutes']==45 and tasks[0]['solver_allocation_minutes']==60
    assert tasks[0]['identity']['status']=='confirmed' and tasks[0]['due']=='2026-10-23T18:00:00+05:00'
    assert all(f['quote'] in s['pages'][f['page']-1]['text'] for f in facts)

def test_continuation_keeps_page_quotes():
    s=source('Assignment: Spectrum\nCourse: Optics\nTerm: Autumn 2026')
    s['pages'].append(dict(page=2,text='Due: 2026-10-23T18:00:00+05:00\nEffort: 75 minutes\n- Explain calibration'))
    f,t=extract_facts(s);assert len(t)==1 and t[0]['minutes']==75 and t[0]['due']
    assert next(x for x in f if x['field']=='due')['page']==2

@pytest.mark.parametrize('text',['Our optics course requires a report. Estimate 45 minutes; due Friday.',
 'По курсу оптики нужно подготовить отчёт. Оценка: 45 минут. Срок — пятница.',
 'Оптика пәні бойынша есеп дайындау керек. Ұзақтығы: 45 минут. Мерзімі — жұма.'])
def test_prose_remains_reviewable_not_fabricated(text):
    f,t=extract_facts(source(text));assert len(t)==1 and t[0]['extraction_origin']=='prose_needs_review' and t[0]['due'] is None

@pytest.mark.parametrize('value,status',[(None,'unknown'),(42,'invalid'),(False,'invalid'),('03/04','ambiguous'),({},'invalid')])
def test_proposal_due_boundary(value,status):
    p=extraction_proposal(source('Assignment: Spectrum'),[dict(field='due',value=value,page=1,quote='Spectrum')])
    assert p['fields'][0]['validation_status']==status
    with pytest.raises(RelayError):instant(value)

def test_same_title_two_courses_mapping_only_one(tmp_path):
    svc=service(tmp_path);s=svc.import_source('labs.md',b'# Assignment: Lab\nCourse: A\nEffort: 45 minutes\n# Assignment: Lab\nCourse: B\nEffort: 75 minutes')
    assert len(s['drafts'])==2 and len({t['section_key'] for t in s['drafts']})==2
    target=s['drafts'][0];other=s['drafts'][1]
    svc.map_assignment(s['id'],target['section_key'],'A','Fall2026','lab-01')
    current=svc.sources()[0]['drafts'];assert len(current)==2
    unchanged=next(t for t in current if t['section_key']==other['section_key']);assert unchanged['id']==other['id'] and unchanged['identity']['status']=='unresolved'

@pytest.mark.parametrize('text',[b' ',b'\n\t\r',b'\xef\xbb\xbf  '])
def test_empty_text_is_typed(text):
    with pytest.raises(RelayError) as e:read_upload('empty.txt',text)
    assert e.value.code=='EMPTY_CONTENT'

def test_nonacademic_and_long_tail():
    f,t=extract_facts(source('A poem about a silver moon.'));assert not f and not t
    s=source('Course overview\n'+'A calm introduction.\n'*1100+'\nAssignment: Late appendix\nCourse: Optics\nTerm: Fall2026\nEffort: 45 minutes')
    f,t=extract_facts(s);assert t[0]['title']=='Late appendix' and t[0]['minutes']==45

@pytest.mark.parametrize('due',['2026-10-23','03/04','Friday','next Friday','2026-10-23T18:00:00'])
def test_incomplete_dates_unknown(due):
    _,tasks=extract_facts(source('Assignment: Spectrum\nDue: '+due+'\nEffort: 45 minutes'));assert tasks[0]['due'] is None

def prepared(svc):
    s=svc.import_source('prose.txt',b'The course requires an optics report. Due 2026-10-23T18:00:00+05:00. Estimate 45 minutes.')
    fields=[dict(entity_id=e,field='title',value=title,page=1,quote=s['pages'][0]['text']) for e,title in [('one','Optics report'),('two','Calibration report')]]
    p=extraction_proposal(s,fields);svc.store.put(svc.tenant,'extraction_proposals',p['id'],p)
    body=dict(source_version=s['version'],confirmed=True,values=dict(title='Optics report',course='Optics',term='Fall2026',assignment_key='optics-7',due='2026-10-23T18:00:00+05:00',minutes=45,rubric=['Explain calibration']))
    return s,p,body

def test_explicit_atomic_one_entity_and_duplicate(tmp_path):
    svc=service(tmp_path);s,p,b=prepared(svc)
    with pytest.raises(RelayError):confirm(svc,p['id'],p['entities'][0]['id'],b|{'confirmed':False})
    result=confirm(svc,p['id'],p['entities'][0]['id'],b)
    assert confirm(svc,p['id'],p['entities'][0]['id'],b)['duplicate']
    current=svc.store.get(svc.tenant,'extraction_proposals',p['id']);assert not current['entities'][1].get('applied')
    assert svc.tasks()[0]['minutes']==45 and result['task_id']==svc.tasks()[0]['id']
    foreign=RelayService(svc.store,'foreign');foreign.create_empty()
    with pytest.raises(RelayError):confirm(foreign,p['id'],p['entities'][0]['id'],b)
    with pytest.raises(RelayError):confirm(svc,p['id'],p['entities'][0]['id'],b|{'values':b['values']|{'minutes':90}})

def test_stale_source_no_partial_changes(tmp_path):
    svc=service(tmp_path);s,p,b=prepared(svc)
    svc.import_source('prose.txt',b'The course requires a different report.',id=s['id'])
    before=svc.tasks()
    with pytest.raises(RelayError) as e:confirm(svc,p['id'],p['entities'][0]['id'],b)
    assert e.value.code=='STALE_REVISION' and svc.tasks()==before

def test_semantic_passport_reopen_and_plan(tmp_path):
    from relay.passport import export,stage,commit
    svc=service(tmp_path);s,p,b=prepared(svc);confirm(svc,p['id'],p['entities'][0]['id'],b)
    update(svc,dict(timezone='Asia/Almaty',start_date='2026-10-20',end_date='2026-10-25',weekdays=[0,1,2,3,4,5,6],start_time='18:00',end_time='20:00'))
    computed=svc.plan();assert computed['required_minutes']==60
    # Regression: extraction-proposal iteration must not shadow plan(proposal=False).
    reopened=RelayService(Store(svc.store.path),svc.tenant)
    assert reopened.snapshot()['plan']['id']==computed['id']
    assert reopened.snapshot()['plan']['required_minutes']==60
    payload=export(svc)['file'];staged=stage(svc,__import__('json').dumps(payload).encode());restored=commit(svc,staged['id'])
    fresh=RelayService(Store(svc.store.path),restored['tenant'])
    assert fresh.tasks()[0]['minutes']==45 and fresh.tasks()[0]['title']=='Optics report'
    assert fresh.plan()['required_minutes']==60

@pytest.mark.parametrize('value',['2026-03-29T01:30','2026-10-25T01:30'])
def test_dst_gap_and_fold_rejected(value):
    with pytest.raises(RelayError):local_timestamp(value,'Europe/London')

def test_explicit_offset_and_overnight_weekend_context(tmp_path):
    svc=service(tmp_path);s=update(svc,dict(timezone='Europe/Moscow',start_date='2026-10-24',end_date='2026-10-25',weekdays=[5,6],start_time='23:00',end_time='01:00'))
    assert len(s['windows'])==2 and all(instant(w['end'])>instant(w['start']) for w in s['windows'])
    assert instant('2026-10-23T18:00:00+09:00').hour==9

def test_ics_uses_workspace_zone(tmp_path):
    svc=service(tmp_path);update(svc,dict(timezone='Europe/Moscow',start_date='2026-10-19',end_date='2026-10-25',weekdays=[0],start_time='18:00',end_time='20:00'))
    raw=b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:day-off\r\nDTSTART;VALUE=DATE:20261019\r\nDTEND;VALUE=DATE:20261020\r\nSUMMARY:No study\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
    svc.import_source('busy.ics',raw);event=svc.store.list(svc.tenant,'calendar')[0]
    assert event['start']['dateTime'].endswith('+03:00')

def test_upload_boundary_and_corrupt_pdf():
    for data in [b'%PDF-corrupt',b'bad\0pdf']:
        with pytest.raises(RelayError):read_upload('broken.pdf',data)
    with pytest.raises(RelayError):read_upload('huge.md',b'x'*(MAX_BYTES+1))

def test_empty_preflight_never_ready():
    from relay.preflight import check_submission
    result=check_submission('draft.md',b'Unrelated draft.',[])
    assert result['assessment_status']=='not_assessed' and result['missing_count']==0

def test_duplicate_semantic_key_cannot_overwrite_neighbor(tmp_path):
    svc=service(tmp_path);s,p,b=prepared(svc);confirm(svc,p['id'],p['entities'][0]['id'],b)
    before=copy.deepcopy(svc.tasks())
    with pytest.raises(RelayError):confirm(svc,p['id'],p['entities'][1]['id'],b)
    assert svc.tasks()==before

@pytest.mark.parametrize('delta',[-1,0,1])
def test_raw_file_byte_boundary_valid_pdf(delta):
    from pathlib import Path
    raw=Path('fixtures/network-security-original.pdf').read_bytes();point=raw.rfind(b'startxref')
    assert point>0
    padding=MAX_BYTES+delta-len(raw)-3
    padded=raw[:point]+b'%'+b' '*padding+b'\n\n'+raw[point:]
    assert len(padded)==MAX_BYTES+delta
    if delta>0:
        with pytest.raises(RelayError):read_upload('boundary.pdf',padded)
    else:assert read_upload('boundary.pdf',padded)['pages']

def test_pdf_decompression_bound_stops_child_and_parent_survives():
    import zlib
    from pypdf import PdfWriter
    from pypdf.generic import EncodedStreamObject,NameObject
    writer=PdfWriter();page=writer.add_blank_page(width=500,height=500)
    stream=EncodedStreamObject();stream[NameObject('/Filter')]=NameObject('/FlateDecode');stream._data=zlib.compress(b'q '*5_000_000)
    page[NameObject('/Contents')]=writer._add_object(stream)
    raw=io.BytesIO();writer.write(raw)
    with pytest.raises(RelayError):read_upload('expanded.pdf',raw.getvalue())
    assert read_upload('healthy.txt',b'A normal document after rejection.')['pages'][0]['text'].startswith('A normal')

def test_document_context_inherited_but_section_course_overrides():
    s=source('Course: Geology\nTerm: Autumn 2026\n# Assignment: Minerals\nEffort: 45 minutes\n# Assignment: Sediment\nEffort: 75 minutes\n# Assignment: Pressure\nCourse: Materials\nEffort: 90 minutes')
    facts,tasks=extract_facts(s)
    assert [t['course'] for t in tasks]==['Geology','Geology','Materials']
    assert all(t['identity']['term']=='Autumn 2026' and t['identity']['status']=='confirmed' for t in tasks)
    third=[f for f in facts if f['task_id']==tasks[2]['id'] and f['field']=='course'];assert len(third)==1 and third[0]['value']=='Materials'

def test_same_course_term_same_title_without_keys_stays_two_drafts():
    _,tasks=extract_facts(source('Course: Geology\nTerm: Autumn 2026\n# Assignment: Lab\nEffort: 45 minutes\n# Assignment: Lab\nEffort: 75 minutes'))
    assert len({t['id'] for t in tasks})==2 and all(t['identity']['status']=='unresolved' for t in tasks)

def test_model_deadline_offset_must_match_cited_timezone():
    s=source('Submit 23 October 2026 at 18:30 in Asia/Qyzylorda (UTC+05:00).')
    candidate=dict(field='due',value='2026-10-23T18:30:00+06:00',page=1,quote=s['pages'][0]['text'],timezone='Asia/Qyzylorda',year_explicit=True)
    with pytest.raises(RelayError) as error:extraction_proposal(s,[candidate])
    assert error.value.code=='SOURCE_CONFLICT' and error.value.details['expected_offset']=='5:00:00'
    correct=extraction_proposal(s,[candidate|{'value':'2026-10-23T18:30:00+05:00'}])
    assert correct['fields'][0]['validation_status']=='needs_confirmation'

@pytest.mark.parametrize('zone',['+05:00','UTC+05:00','Asia/Almaty'])
def test_explicit_pdf_offset_is_not_misclassified_ambiguous(zone):
    s=source('Due: 2026-10-23T18:00:00+05:00')
    proposal=extraction_proposal(s,[dict(field='due',value='2026-10-23T18:00:00+05:00',page=1,quote=s['pages'][0]['text'],timezone=zone,year_explicit=True)])
    assert proposal['fields'][0]['value']=='2026-10-23T18:00:00+05:00' and proposal['fields'][0]['validation_status']=='needs_confirmation'

def test_partial_page_two_keeps_valid_fields_and_correction_merges(tmp_path):
    svc=service(tmp_path)
    s=svc.import_source('continued.txt',b'Assignment: Polarization memo\nCourse: Optics\nTerm: Autumn 2026\nKey: POLAR-16')
    s['pages'].append(dict(page=2,text='Due: 2026-10-23T18:00:00+05:00\nEffort: 75 minutes\n- [ ] Compare two filters'))
    svc.store.put(svc.tenant,'sources',s['id'],s)
    def field(name,value,page,quote,**kw):return dict(entity_id='polarization',field=name,value=value,page=page,quote=quote,**kw)
    p1=record_proposal(svc,validated_batch(s,[field('title','Polarization memo',1,'Assignment: Polarization memo'),field('assignment_key','POLAR-16',1,'Key: POLAR-16')]))
    # Actual model failure: one checklist quote changed its markers. The deadline
    # and effort on that same second page must survive as unconfirmed fields.
    p2=record_proposal(svc,validated_batch(s,[
        field('due','2026-10-23T18:00:00+05:00',2,'Due: 2026-10-23T18:00:00+05:00',timezone='Asia/Almaty',year_explicit=True),
        field('minutes',75,2,'Effort: 75 minutes'),
        field('rubric',['Compare two filters'],2,'- Compare two filters')]))
    assert p2['status']=='partial' and p2['validation_issues'][0]['field']=='rubric'
    assert {f['field'] for f in p2['fields']}=={'title','assignment_key','due','minutes'}
    assert p2['merged_proposal_ids']==[p1['id']] and not p2['applied']
    p3=record_proposal(svc,validated_batch(s,[field('rubric',['Compare two filters'],2,'- [ ] Compare two filters')]))
    assert not p3['validation_issues'] and p3['status']=='requires_explicit_confirmation'
    assert next(f for f in p3['fields'] if f['field']=='minutes')['value']==75
    assert len(current_proposals(svc))==1 and current_proposals(svc)[0]['id']==p3['id']
    assert not any(f.get('kind')=='user_confirmed_proposal' for f in svc.sources()[0]['facts'])
    assert not svc.sources()[0].get('confirmed_extractions')

def test_rejected_semantic_batch_does_not_apply_or_cross_entities(tmp_path):
    svc=service(tmp_path);s=svc.import_source('notes.txt',b'Optics report: 45 minutes. Calibration: 75 minutes.')
    a=dict(entity_id='optics',field='minutes',value=45,page=1,quote='45 minutes')
    record_proposal(svc,validated_batch(s,[a]))
    b=record_proposal(svc,validated_batch(s,[a|{'entity_id':'calibration','value':75,'quote':'75 minutes'}]))
    assert len(b['entities'])==1 and b['fields'][0]['value']==75
    assert len(current_proposals(svc))==2
    with pytest.raises(RelayError) as error:validated_batch(s,[a|{'quote':'Invented quote'}])
    assert error.value.code=='SOURCE_CONFLICT' and error.value.details['rejected_fields'][0]['reason']=='field_or_exact_page_quote_invalid'
    assert not svc.sources()[0].get('confirmed_extractions')

def test_repaired_neighbor_diagnostics_disappear_from_visible_proposals(tmp_path):
    svc=service(tmp_path);s=svc.import_source('shared.txt',b'Course: Research Methods\nTerm: Autumn 2026\nMeasurement log\nNoise comparison memo')
    def f(entity,name,value,quote):return dict(entity_id=entity,field=name,value=value,page=1,quote=quote)
    original=record_proposal(svc,validated_batch(s,[f('M26','title','Measurement log','Measurement log'),f('N13','title','Noise comparison memo','Noise comparison memo'),f('N13','course','Research Methods','Invented heading')]))
    assert original['status']=='partial'
    corrected=record_proposal(svc,validated_batch(s,[f('N13','course','Research Methods','Course: Research Methods')]))
    visible=current_proposals(svc)
    assert len(visible)==2 and sum(len(p['entities']) for p in visible)==2
    assert all(not p['validation_issues'] and p['status']=='requires_explicit_confirmation' for p in visible)
    assert next(p for p in visible if p['id']==corrected['id'])['entities'][0]['fields'][0]['value']=='Noise comparison memo'

def test_multiline_citation_reference_copies_exact_text_but_never_confirms(tmp_path):
    svc=service(tmp_path);s=svc.import_source('table.txt',b'Course: Earth Science\nSoil | 45 minutes\nCriteria:\n- Explain conductivity\n- Compare samples')
    reference=page_citations(s,1)[0]
    p=record_proposal(svc,validated_batch(s,[dict(entity_id='soil',field='rubric',value=['Explain conductivity','Compare samples'],page=1,citation_id=reference['citation_id'])]))
    field=p['fields'][0];assert field['quote']==reference['quote']==s['pages'][0]['text']
    assert field['original_expression']==reference['quote'] and field['validation_status']=='needs_confirmation'
    assert not p['applied'] and not svc.sources()[0].get('confirmed_extractions')
    # Literal mode still rejects a model's reformatted quote.
    with pytest.raises(RelayError):extraction_proposal(s,[dict(field='rubric',value=['Explain conductivity'],page=1,quote='Criteria: Explain conductivity')])

@pytest.mark.parametrize('change',[{'id':'foreign-source'},{'version':'stale-version'},{'pages':[dict(page=2,text='Same content on another page')]}])
def test_citation_reference_rejects_foreign_stale_or_wrong_page(change):
    s=source('Actual source text.');reference=page_citations(s,1)[0]
    with pytest.raises(RelayError) as error:extraction_proposal(s|change,[dict(field='title',value='Report',page=1,citation_id=reference['citation_id'])])
    assert error.value.code=='SOURCE_CONFLICT' and error.value.details['reason']=='citation_not_current_page'

def test_citation_response_bounded_and_search_tail_refs_exact():
    s=source('intro '*5000+'\nFinal appendix: lithic density\n')
    refs=visible_citations(s,1,29000,30000)
    assert refs and sum(len(r['quote']) for r in refs)<=8000 and len(refs)<=80
    assert all(r['quote']==s['pages'][0]['text'][r['start']:r['end']] for r in refs)

def test_dense_source_citation_index_stays_bounded_and_tail_available():
    s=source('x\n'*100000)
    refs=page_citations(s,1)
    assert len(refs)<=50+256 # full chunks plus a bounded short-line index
    tail=visible_citations(s,1,190000,190200)
    assert tail and all(r['quote']==s['pages'][0]['text'][r['start']:r['end']] for r in tail)
