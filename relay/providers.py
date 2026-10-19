"""One explicit inference route; no silent provider or billing fallback."""
import os
from .domain import RelayError, digest


def selected():
    mode = os.getenv('RELAY_MODE', 'local')
    provider = os.getenv('RELAY_INFERENCE_PROVIDER', 'vertex')
    deployment = os.getenv('RELAY_DEPLOYMENT_MODE', 'managed_gcp' if mode == 'cloud' else 'local')
    if provider not in ('vertex', 'gemini_developer') or deployment not in ('managed_gcp', 'alternative_hosted', 'local'):
        raise RuntimeError('Unsupported explicit inference provider/deployment mode.')
    if deployment == 'managed_gcp' and (provider != 'vertex' or mode != 'cloud'):
        raise RuntimeError('Managed GCP mode requires Vertex inference and cloud identity.')
    if deployment == 'alternative_hosted' and (provider != 'gemini_developer' or mode != 'alternative_live'):
        raise RuntimeError('Alternative hosting requires explicit Gemini Developer inference and alternative_live mode.')
    if mode == 'cloud' and deployment != 'managed_gcp':
        raise RuntimeError('Cloud mode cannot silently switch to an alternative provider.')
    if mode == 'alternative_live' and deployment != 'alternative_hosted':
        raise RuntimeError('Alternative live mode requires alternative_hosted deployment.')
    if mode == 'public_demo' and (provider != 'vertex' or deployment != 'local' or os.getenv('RELAY_GEMINI_API_KEY')):
        raise RuntimeError('Illustrative public mode refuses Gemini credentials and live inference.')
    developer = provider == 'gemini_developer'
    model = os.getenv('RELAY_GEMINI_DEVELOPER_MODEL', 'gemini-3.5-flash-lite') if developer else os.getenv('GEMINI_MODEL', '')
    resource = 'gemini-developer:' + model if developer else os.getenv('RELAY_AGENT_RESOURCE')
    configured = bool(os.getenv('RELAY_GEMINI_API_KEY') and os.getenv('RELAY_GEMINI_FREE_ONLY') == 'true') if developer else bool(resource)
    return dict(provider=provider, deployment_mode=deployment, model=model, resource=resource,
                configured=configured, managed_agent_engine=deployment == 'managed_gcp',
                mode='live_gemini_alternative' if developer else 'live_agent_engine',
                revision=os.getenv('RELAY_AGENT_REVISION') if not developer else (os.getenv('RELAY_BUILD_REVISION') or os.getenv('RELAY_DEPLOYED_COMMIT') or os.getenv('RENDER_GIT_COMMIT')))


def current_availability(store):
    from .conversations import availability
    config = selected()
    result = availability(store, config['resource'] if config['configured'] else None)
    result.update({k: config[k] for k in ('provider', 'deployment_mode', 'model', 'managed_agent_engine', 'mode')})
    result['configured'] = config['configured']
    from .public_ai import enabled as public_access
    result['public_access'] = public_access()
    if config.get('revision') and result.get('evidence', {}).get('revision') != config['revision']:
        result['verified'] = False
    if config['configured']:
        try:
            failure = store.get('_server', 'agent_failures', digest(config['resource']))
            result['last_failure'] = failure
            if failure.get('failed_at', '') >= result.get('evidence', {}).get('observed_at', ''):
                result['verified'] = False
        except RelayError:
            pass
    return result


def model_instance(config):
    if config['provider'] == 'vertex':
        from google import genai
        from google.genai import types
        from google.adk.models.google_llm import Gemini
        client=genai.Client(vertexai=True,project=os.environ['GOOGLE_CLOUD_PROJECT'],location=os.environ['GOOGLE_CLOUD_LOCATION'],
                            http_options=types.HttpOptions(timeout=70000,retry_options=types.HttpRetryOptions(attempts=1)))
        return Gemini(model=config['model'],client=client)
    if not config['configured']:
        raise RelayError('AUTH_REQUIRED', 'Configure an owner-authorized free-tier Gemini key on the server. No paid fallback is enabled.')
    from google import genai
    from google.genai import types
    from google.adk.models.google_llm import Gemini
    client = genai.Client(vertexai=False, api_key=os.environ['RELAY_GEMINI_API_KEY'],
                          http_options=types.HttpOptions(timeout=70000, retry_options=types.HttpRetryOptions(attempts=1)))
    return Gemini(model=config['model'], client=client)
