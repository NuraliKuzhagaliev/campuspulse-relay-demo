"""MCP diagnostics that retain schema locations, never submitted values."""
import re
from pydantic import ValidationError

FIELDS = frozenset('source_id candidates entity_id field value page citation_id quote original_expression context assumptions timezone year_explicit ambiguous'.split())


def schema_failure(exc):
    cause = exc
    for _ in range(6):
        if isinstance(cause, ValidationError):
            issues = []
            for error in cause.errors(include_input=False, include_context=False, include_url=False)[:20]:
                location = [part if isinstance(part, int) else part if part in FIELDS else ':redacted' for part in error['loc'][:6]]
                kind = error.get('type', '')
                issues.append(dict(location=location, type=kind if re.fullmatch(r'[a-z_]{1,60}', kind) else 'invalid'))
            return {'error': dict(code='TOOL_INPUT_INVALID', message='Tool input did not match its schema. Correct the listed fields using the original source; no proposal was applied.', details={'issues': issues})}
        cause = getattr(cause, '__cause__', None)
        if cause is None:
            break
    return {'error': dict(code='TOOL_EXECUTION_FAILED', message='The tool could not complete. No successful observation is claimed; inspect the operation before retrying.', details=None)}


def safe_issues(value, depth=0):
    """Read only our finite, already redacted schema diagnostics from MCP envelopes."""
    import json
    if depth > 8:
        return []
    found = []
    if isinstance(value, dict):
        error = value.get('error', {})
        if isinstance(error, dict) and error.get('code') == 'TOOL_INPUT_INVALID':
            for issue in (error.get('details') or {}).get('issues', [])[:20]:
                location = [p if type(p) is int else p if isinstance(p, str) and p in FIELDS else ':redacted' for p in issue.get('location', [])[:6]]
                kind = issue.get('type', '')
                found.append(dict(location=location, type=kind if isinstance(kind, str) and re.fullmatch(r'[a-z_]{1,60}', kind) else 'invalid'))
        if value.get('type') == 'text':
            try:
                found += safe_issues(json.loads(value.get('text', '')), depth+1)
            except (ValueError, TypeError):
                pass
        for key in ('result', 'content', 'response', 'structuredContent'):
            if key in value:
                found += safe_issues(value[key], depth+1)
    elif isinstance(value, list):
        for item in value[:50]:
            found += safe_issues(item, depth+1)
    return found[:20]
