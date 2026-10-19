"""Explicit, versioned assignment mappings; fuzzy titles never join coursework."""
import re
import unicodedata
from .domain import digest


def canonical(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value or '')).strip().casefold()


def assignment_id(course, term, key):
    return digest(['assignment-v2', canonical(course), canonical(term), canonical(key)])[:24]


def section_key(title):
    return digest(canonical(title))[:24]


def mapping(source, title, course, term, key, entity_key=None, unique_title=True):
    explicit = source.get('assignment_mappings', {}).get(entity_key)
    if not explicit and unique_title:
        explicit = source.get('assignment_mappings', {}).get(section_key(title))
    if explicit:
        return explicit
    if course and term and (key or unique_title):
        return dict(id=assignment_id(course, term, key or title), course=course, term=term,
                    assignment_key=key or title, status='confirmed', origin='exact_structured_fields')
    # Missing context stays a separate draft. Source versions retain the same draft ID.
    return dict(id=digest(['draft-v2', source['id'], entity_key or section_key(title)])[:24],
                course=course or 'Unassigned course', term=term or None,
                assignment_key=key or title, status='unresolved', origin='source_scoped_draft')
