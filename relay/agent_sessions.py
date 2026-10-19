"""ADK session contract backed by the tenant-owned durable application store.

Full tool transcripts are not persisted. Completed, non-thought text exchanges
are checkpointed as an ADK Session; credentials, tool payloads and hidden model
reasoning remain outside this checkpoint. Gateway conversation leases serialize
turns, and the store CAS rejects stale session snapshots across workers.
"""
import time
from google.adk.sessions import BaseSessionService, Session
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.events import Event
from google.genai import types
from .conversations import conversation
from .domain import RelayError


class RelaySessionService(BaseSessionService):
    def __init__(self, store, tenant, conversation_id):
        self.store, self.tenant, self.conversation_id = store, tenant, conversation_id

    def scope(self, app_name, user_id, session_id=None):
        if app_name != 'campuspulse_relay' or user_id != self.tenant or (session_id and session_id != self.conversation_id):
            raise RelayError('ACCESS_DENIED', 'ADK session identity must match the verified workspace conversation.')
        return conversation(self.store, self.tenant, self.conversation_id)

    async def create_session(self, *, app_name, user_id, state=None, session_id=None):
        self.scope(app_name, user_id, session_id)
        # No client-provided state or identity is trusted as session authority.
        value = Session(id=self.conversation_id, app_name=app_name, user_id=user_id, state={}, last_update_time=time.time())
        self.store.put(self.tenant, 'adk_sessions', value.id, dict(session=value.model_dump(mode='json'), revision=0), create=True)
        return await self.get_session(app_name=app_name, user_id=user_id, session_id=value.id)

    async def get_session(self, *, app_name, user_id, session_id, config=None):
        self.scope(app_name, user_id, session_id)
        try:
            stored = self.store.get(self.tenant, 'adk_sessions', session_id)
        except RelayError:
            return None
        return Session.model_validate(stored['session'])

    async def list_sessions(self, *, app_name, user_id=None):
        self.scope(app_name, user_id)
        value = await self.get_session(app_name=app_name, user_id=user_id, session_id=self.conversation_id)
        return ListSessionsResponse(sessions=[value] if value else [])

    async def delete_session(self, *, app_name, user_id, session_id):
        self.scope(app_name, user_id, session_id)
        self.store.claim(self.tenant, 'conversations', session_id, {'closed': False}, {'closed': True})

    async def append_event(self, session, event):
        self.scope(session.app_name, session.user_id, session.id)
        # ADK receives full events during the current invocation only. Persist
        # plain completed exchanges, never tool results or thought signatures.
        stored = self.store.get(self.tenant, 'adk_sessions', session.id)
        if session.last_update_time < stored['session']['last_update_time']:
            raise RelayError('STALE_PLAN', 'Conversation checkpoint changed. Reload before another turn.')
        result = await super().append_event(session, event)
        if event.partial:
            return result
        safe = []
        for e in session.events:
            parts = getattr(e.content, 'parts', []) or []
            if any(getattr(p, 'function_call', None) or getattr(p, 'function_response', None) for p in parts):
                continue
            texts = [p.text for p in parts if getattr(p, 'text', None) and not getattr(p, 'thought', False)]
            if texts:
                safe.append(Event(author=e.author, invocation_id=e.invocation_id, timestamp=e.timestamp,
                                  content=types.Content(role=e.content.role, parts=[types.Part(text='\n'.join(texts)[:12000])])).model_dump(mode='json'))
        checkpoint = session.model_dump(mode='json')
        checkpoint.update(events=safe[-16:], state={}, last_update_time=max(time.time(), stored['session']['last_update_time'] + 0.000001))
        if not self.store.claim(self.tenant, 'adk_sessions', session.id, {'revision': stored['revision']},
                                dict(session=checkpoint, revision=stored['revision'] + 1)):
            raise RelayError('RUN_IN_PROGRESS', 'Conversation checkpoint was concurrently updated.')
        session.last_update_time = checkpoint['last_update_time']
        return result
