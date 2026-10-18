"""Validate Gemini-proposed extraction against selected, versioned page text.

This is a proposal contract, not a fallback model. Live extraction is pending deployment.
"""
from .domain import RelayError, instant, digest, now

ALLOWED={'title','course','term','assignment_key','due','minutes','rubric'}


def extraction_proposal(source, candidates):
    if not isinstance(candidates,list) or len(candidates)>100:
        raise RelayError('UNSUPPORTED_INPUT','Propose at most 100 cited fields from the selected source.')
    pages={p['page']:p['text'] for p in source['pages']}
    fields=[]
    for c in candidates:
        field=c.get('field');quote=c.get('quote','');page=c.get('page')
        if field not in ALLOWED or not quote or len(quote)>4000 or quote not in pages.get(page,''):
            raise RelayError('SOURCE_CONFLICT','Every proposed field must cite an exact quote on its selected source page.')
        value=c.get('value');status='needs_confirmation'
        expression=c.get('original_expression',quote)
        if expression not in quote:
            raise RelayError('SOURCE_CONFLICT','The original expression must occur in the exact quote.')
        if field=='due':
            try:instant(value)
            except RelayError: value=None;status='ambiguous'
            # Do not normalize an incomplete/ambiguous expression without explicit confirmation.
            if not c.get('timezone') or not c.get('year_explicit') or c.get('ambiguous'):
                status='ambiguous'
        if field=='minutes' and (not isinstance(value,int) or isinstance(value,bool) or value<30 or value>10080 or value%30):
            value=None;status='invalid'
        fields.append(dict(field=field,value=value,page=page,quote=quote,original_expression=expression,
            source_id=source['id'],source_version=source['version'],hash=source['content_hash'],
            assumptions=str(c.get('assumptions',''))[:1000],context=str(c.get('context',''))[:1000],
            timezone=c.get('timezone'),validation_status=status))
    return dict(id=digest([source['id'],source['version'],fields])[:24],source_id=source['id'],source_version=source['version'],
                proposed_at=now(),fields=fields,status='requires_explicit_confirmation',applied=False)
