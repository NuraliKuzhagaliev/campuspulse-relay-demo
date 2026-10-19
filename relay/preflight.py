"""Read-only structural deliverable checks. No execution, submission or grade prediction."""
import fnmatch
import re
from pathlib import PurePath
from .domain import RelayError, digest, now
from .evidence import read_upload


def check_submission(name, content, facts, exceptions=None, present_files=None):
    parsed=read_upload(name,content)
    if 'pages' not in parsed:
        raise RelayError('UNSUPPORTED_INPUT','Choose a text PDF, Markdown or TXT draft; calendar files are not deliverables.')
    exceptions=exceptions or {};present_files=set(present_files or [name])
    text='\n'.join(p['text'] for p in parsed['pages'])
    words=len(re.findall(r'\b\w+\b',text))
    results=[]
    for fact in facts:
        if fact['field'] not in ('submission_requirement','rubric'):continue
        quote=fact['quote'];normalized=fact.get('value') if fact['field']=='submission_requirement' and isinstance(fact.get('value'),str) else quote
        key,sep,value=normalized.partition(':');value=value.strip();key=key.casefold()
        status='needs_review';observed=dict(location='draft text',note='Semantic correctness requires human review.')
        if fact['field']=='submission_requirement':
            status='unknown'
            if key=='filename':
                matches=fnmatch.fnmatchcase(name,value)
                status='verified' if matches else 'missing'
                observed=dict(location='filename',actual=name,expected_pattern=value)
                if not matches and fact['id'] in exceptions:
                    status='needs_review';observed['exception']=str(exceptions[fact['id']])[:500]
            elif key=='format':
                allowed=[x.strip().lower().lstrip('.') for x in value.split(',')]
                status='verified' if PurePath(name).suffix.lstrip('.').lower() in allowed else 'missing'
                observed=dict(location='file metadata',actual=parsed['type'],allowed=allowed)
            elif key=='sections':
                required=[x.strip() for x in value.split(';') if x.strip()]
                headings=[(p['page'],i+1,line.lstrip('# ').strip()) for p in parsed['pages'] for i,line in enumerate(p['text'].splitlines()) if line.strip()]
                found=[dict(section=r,page=p,line=i) for r in required for p,i,t in headings if t.casefold()==r.casefold()]
                missing=[r for r in required if not any(f['section']==r for f in found)]
                status='missing' if missing else 'verified'
                observed=dict(location='named section lines',found=found,missing=missing,semantic_content_verified=False)
            elif key in ('words','pages'):
                bounds=re.fullmatch(r'(\d+)\s*-\s*(\d+)',value)
                if bounds:
                    count=words if key=='words' else len(parsed['pages'])
                    # Markdown/TXT pages are a parser container, not printed page counts.
                    measurable=key=='words' or parsed['type']=='pdf'
                    status=('verified' if int(bounds[1])<=count<=int(bounds[2]) else 'missing') if measurable else 'unknown'
                    observed=dict(location='extracted text token count' if key=='words' else 'PDF page metadata',actual=count if measurable else None,range=value)
            elif key=='required files':
                required=[v.strip() for v in value.split(';') if v.strip()]
                missing=[r for r in required if r not in present_files]
                status='missing' if missing else 'needs_review'
                observed=dict(location='student-declared file inventory',missing=missing,declared=sorted(present_files),contents_verified=False)
        results.append(dict(requirement=fact,status=status,observed=observed))
    return dict(id=digest([name,parsed['content_hash'],[f['id'] for f in facts],exceptions])[:24],checked_at=now(),
                draft=dict(filename=name,hash=parsed['content_hash'],format=parsed['type'],words=words,pages=len(parsed['pages']) if parsed['type']=='pdf' else None),
                results=results,missing_count=sum(r['status']=='missing' for r in results),
                assessment_status='not_assessed' if not results else 'issues_found' if any(r['status']=='missing' for r in results) else 'human_review_required',
                requirement_count=len(results),unassessed_count=sum(r['status'] in ('unknown','needs_review') for r in results),
                structural_only=True,grade_predicted=False,external_submission=False)
