from pathlib import Path
import pytest
from scripts.organizer_agent import configuration,owned_resource

def plan():
    return dict(project='organizer-lab-01234',region='us-central1',model='actual-organizer-model',owned_prefix='relay-audit-001',staging_bucket='gs://organizer-lab-01234-relay-audit',runtime_service_account='relay-runtime@organizer-lab-01234.iam.gserviceaccount.com',context_secret_id='relay-context',context_secret_version=1,public_origin='https://campuspulse-relay-demo.onrender.com',source_commit='a'*40)

def test_minimal_managed_package_preserves_authoritative_state_and_secret_refs(tmp_path):
    config=configuration(plan(),tmp_path)
    assert config.min_instances==0 and config.max_instances==1
    assert config.env_vars['RELAY_STATE_URL']=='https://campuspulse-relay-demo.onrender.com/internal/runtime-state'
    assert config.env_vars['RELAY_STATE_AUDIENCE']=='https://campuspulse-relay-demo.onrender.com'
    assert config.env_vars['RELAY_CONTEXT_SECRET'].version=='1'
    assert not {'RELAY_GEMINI_API_KEY','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY'}&set(config.env_vars)

def test_managed_plan_refuses_foreign_identity(tmp_path):
    with pytest.raises(ValueError):configuration(plan()|{'runtime_service_account':'runtime@foreign-project.iam.gserviceaccount.com'},tmp_path)

def test_owned_resource_accepts_actual_project_number_but_not_foreign_project():
    actual=plan()|{'project_number':'123456789012'}
    assert owned_resource(actual,'projects/123456789012/locations/us-central1/reasoningEngines/456')
    assert owned_resource(actual,'projects/organizer-lab-01234/locations/us-central1/reasoningEngines/456')
    assert not owned_resource(actual,'projects/999999999999/locations/us-central1/reasoningEngines/456')
    assert not owned_resource(actual,'projects/123456789012/locations/europe-west1/reasoningEngines/456')
