"""Read-only deployment access inspection; no resource creation."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'project':os.getenv('GOOGLE_CLOUD_PROJECT'),'region':os.getenv('GOOGLE_CLOUD_LOCATION','us-central1'),'agent_resource':os.getenv('RELAY_AGENT_RESOURCE'),'checks':{},'blockers':[]}
    try:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        credentials,project=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        result['checks']['adc']='available'
        session=AuthorizedSession(credentials)
        r=session.get('https://cloudresourcemanager.googleapis.com/v1/projects',timeout=30)
        result['checks']['projects_status']=r.status_code
        result['accessible_projects']=[{k:p.get(k) for k in ('projectId','name','lifecycleState')} for p in r.json().get('projects',[])] if r.status_code==200 else []
        project=result['project'] or project
        if not project:
            result['blockers'].append('Select an authorized dedicated Google Cloud project.')
        else:
            r=session.get(f'https://cloudbilling.googleapis.com/v1/projects/{project}/billingInfo',timeout=30)
            result['checks']['billing_status']=r.status_code
            if r.status_code==200:
                b=r.json();result['billing_enabled']=b.get('billingEnabled',False);result['billing_account_name']=b.get('billingAccountName')
            result['credits']='Not inferred. Check Billing > Credits in Console; billing access does not establish available credit.'
            location=result['region']
            r=session.get(f'https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/reasoningEngines',timeout=30)
            result['checks']['reasoning_engines_status']=r.status_code
            result['reasoning_engines']=[{k:a.get(k) for k in ('name','displayName','createTime','updateTime')} for a in r.json().get('reasoningEngines',[])] if r.status_code==200 else []
    except Exception as exc:
        result['checks']['adc']='unavailable'
        result['blockers'].append('Google Cloud ADC authentication required; run scripts/inspect-access.ps1 -Login, then scripts/connect-gcp.ps1 -ProjectId YOUR_PROJECT_ID.')
        result['exception_type']=type(exc).__name__
    result['provisioned_resources']=False
    result['organizer_credits_expected']=False
    result['personal_spending_authorized_usd']=0
    result['funding_record_present']=Path('.local/funding-verification.json').exists()
    path=Path('docs/evidence/final-access-preflight.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return bool(result['blockers'])

if __name__=='__main__':
    raise SystemExit(main())
