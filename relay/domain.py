from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RelayError(Exception):
    def __init__(self, code: str, message: str, details=None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details

    def as_dict(self):
        return dict(code=self.code, message=self.message, details=self.details)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def instant(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError('An explicit UTC offset is required')
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError) as exc:
        raise RelayError('PARSE_FAILED', 'Use an ISO date/time with a UTC offset; ambiguous dates are not guessed.') from exc


class Interval(BaseModel):
    start: str
    end: str

    @field_validator('start', 'end')
    @classmethod
    def aware(cls, v):
        instant(v)
        return v


class Task(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    title: str = Field(min_length=1, max_length=180)
    course: str = 'Unassigned course'
    minutes: int | None = Field(default=None, ge=30, le=10080, multiple_of=30)
    effort_max: int | None = Field(default=None, ge=30, le=10080, multiple_of=30)
    due: str | None = None
    priority: int = Field(default=1, ge=1, le=10)
    dependencies: list[str] = Field(default_factory=list, max_length=50)
    source_ids: list[str] = Field(default_factory=list)
    rubric: list[str] = Field(default_factory=list)
    completion: Literal['planned', 'worked_on', 'self_reported', 'externally_observed'] = 'planned'

    @field_validator('due')
    @classmethod
    def due_aware(cls, v):
        if v is not None:
            instant(v)
        return v


class Block(Interval):
    task_id: str
    pinned: bool = False


class PlanInput(BaseModel):
    tasks: list[Task] = Field(max_length=50)
    windows: list[Interval] = Field(max_length=100)
    busy: list[Interval] = Field(default_factory=list, max_length=500)
    pins: list[Block] = Field(default_factory=list, max_length=100)
    baseline: list[Block] = Field(default_factory=list, max_length=200)
    timezone: str = 'Asia/Almaty'
    daily_cap_minutes: int = Field(default=240, ge=30, le=720, multiple_of=30)
    conservative: bool = False


def overlaps(a, b):
    return instant(a['start']) < instant(b['end']) and instant(b['start']) < instant(a['end'])
