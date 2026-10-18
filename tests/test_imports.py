from pathlib import Path
import pytest
from relay.evidence import read_upload,extract_facts
from relay.domain import RelayError


def test_real_text_pdf_exact_page_quote():
    p=Path('fixtures/network-security-original.pdf')
    source=read_upload(p.name,p.read_bytes())|{'id':'pdf','version':'v1'}
    facts,drafts=extract_facts(source)
    due=next(f for f in facts if f['field']=='due')
    assert due['value']=='2026-10-22T18:00:00+05:00'
    assert due['page']==1 and due['quote'] in source['pages'][0]['text']
    assert drafts[0]['minutes']==240


def test_overview_not_an_assignment():
    content=b'# CampusPulse overview\n\nA university course uses this illustrative material.\n\n## Assignment: Real lab\nDue: 2026-10-22T18:00:00+05:00\nEffort: 60 minutes'
    source=read_upload('course.md',content)|{'id':'course','version':'v1'}
    facts,drafts=extract_facts(source)
    assert [d['title'] for d in drafts]==['Real lab']


def test_encrypted_and_scanned_pdf_rejected():
    import io
    from pypdf import PdfWriter
    writer=PdfWriter();writer.add_blank_page(width=500,height=500)
    raw=io.BytesIO();writer.write(raw)
    with pytest.raises(RelayError,match='no extractable text'):
        read_upload('scanned.pdf',raw.getvalue())
    writer.encrypt('password');raw=io.BytesIO();writer.write(raw)
    with pytest.raises(RelayError,match='encrypted'):
        read_upload('locked.pdf',raw.getvalue())
