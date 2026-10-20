"""Workspace choices only; original evidence may retain any explicit source zone."""
from .domain import RelayError

WORKSPACE_TIMEZONES = ('Asia/Almaty', 'Europe/Moscow', 'UTC')


def restored_workspace_timezone(original):
    """Restore old archives without altering their original evidence or instants."""
    if original in WORKSPACE_TIMEZONES:return original
    return 'Asia/Almaty' if original == 'Asia/Qyzylorda' else 'UTC'


def workspace_timezone(value):
    if not isinstance(value, str) or value not in WORKSPACE_TIMEZONES:
        raise RelayError('UNSUPPORTED_TIMEZONE', 'Choose Kazakhstan (UTC+05:00), Moscow (UTC+03:00), or UTC.')
    return value
