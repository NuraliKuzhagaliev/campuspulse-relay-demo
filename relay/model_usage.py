"""Durable per-model-call accounting, conservative free token reserve and backoff."""
import os
import time
from .domain import RelayError, now


def reserve_call(store, tenant, run_id, request_bytes, judge=False):
    from .limits import model_request, consume
    estimate = request_bytes + 5000  # UTF-8 bytes upper-bound text tokens plus output/schema headroom.
    if estimate > 110000:
        raise RelayError('UPSTREAM_RATE_LIMITED', 'This model context is too large. Start a new conversation or select a shorter permitted document.')
    try:
        backoff = store.get('_server', 'model_state', 'backoff')
        if backoff['until'] > time.time():
            raise RelayError('UPSTREAM_RATE_LIMITED', 'Gemini is temporarily rate limited. Retry after the reported reset; no paid fallback is enabled.')
    except RelayError as exc:
        if exc.code != 'ACCESS_DENIED':
            raise
    model_request(store, tenant, judge=judge)
    consume(store, '_server', 'provider-model-minute', 60, int(os.getenv('RELAY_MODEL_CALLS_PER_MINUTE', '13')))
    key = 'minute-' + str(int(time.time() // 60))
    store.put('_server', 'model_token_reserves', key, {'tokens': 0}, create=True)
    for _ in range(5):
        current = store.get('_server', 'model_token_reserves', key)
        if current['tokens'] + estimate > int(os.getenv('RELAY_MODEL_TOKENS_PER_MINUTE', '240000')):
            raise RelayError('UPSTREAM_RATE_LIMITED', 'The conservative Gemini token allowance is temporarily full. Retry after the minute resets.')
        if store.claim('_server', 'model_token_reserves', key, current, {'tokens': current['tokens'] + estimate}):
            store.event(tenant, run_id, 'model_call_reserved', estimated_max_tokens=estimate,
                        summary='Reserved a bounded free-tier model call; no provider output is yet verified.')
            return
    raise RelayError('UPSTREAM_RATE_LIMITED', 'Model capacity is busy. Retry shortly.')


def record_usage(store, tenant, run_id, metadata):
    if metadata is None:
        return
    value = {key: int(getattr(metadata, attr, 0) or 0) for key, attr in (
        ('input_tokens', 'prompt_token_count'), ('output_tokens', 'candidates_token_count'),
        ('thinking_tokens', 'thoughts_token_count'), ('total_tokens', 'total_token_count'))}
    store.event(tenant, run_id, 'model_usage', **value, observed_at=now(), summary='Provider-reported token usage; billing is not inferred.')


def throttle(store, seconds=60):
    store.put('_server', 'model_state', 'backoff', {'until': time.time() + min(3600, max(60, seconds)), 'observed_at': now()})
