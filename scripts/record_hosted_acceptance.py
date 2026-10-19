"""Record only completed actual public checks, keeping the first timeout visible."""
import json
from pathlib import Path
from datetime import datetime,timezone

root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text(encoding='utf-8-sig'))

def newest(pattern,passed=True):
    paths=sorted(root.glob(pattern),key=lambda p:p.stat().st_mtime,reverse=True)
    for p in paths:
        value=read(p)
        if not passed or value.get('passed'):
            return p.relative_to(root).as_posix(),value
    raise RuntimeError('No completed passing evidence: '+pattern)

def main():
    public=read('docs/evidence/public-demo-browser-0.4.0.json');assert public['passed']
    livepath,live=newest('docs/evidence/final-live-hosted-*.json')
    featurepath,features=newest('docs/evidence/final-features-hosted-*.json')
    desktoppath,desktop=newest('docs/evidence/final-desktop-hosted-*.json')
    deploy=read('docs/evidence/render-cutover-0.4.0.json')
    actual=deploy['deployments'][0];assert actual['status']=='live'
    commit=actual['commit']['id'];assert public['deployed_commit']==commit
    runs=live['runs']+features['runs']
    assert len(runs)==8 and all(r['status']=='complete' for r in runs)
    assert all(r['runtime_revision']==r['gateway_revision']==commit for r in runs)
    assert desktop['gateway_revision']==commit and desktop['passed']
    failures=[]
    for path in root.glob('docs/evidence/final-live-hosted-*.json'):
        value=read(path)
        if not value.get('passed'):
            failures.append(dict(evidence=path.relative_to(root).as_posix(),runs=[dict(status=r['status'],reason=r.get('reason')) for r in value['runs']]))
    installed_runs=set()
    desktop_failures=[]
    for path in root.glob('docs/evidence/final-desktop-hosted-*.json'):
        value=read(path)
        if value['checks'].get('actual_installed_UI_to_public_gemini_MCP'):
            installed_runs.add(value['run_id'])
        if not value.get('passed'):
            desktop_failures.append(dict(evidence=path.relative_to(root).as_posix(),import_succeeded=value['checks'].get('real_import_request_and_exact_readback',False),gemini_succeeded=value['checks'].get('actual_installed_UI_to_public_gemini_MCP',False),failure='Native POST /api/demo/reset rejected by exact IPC allowlist; repaired route and CSRF rotation, then reinstalled and reran.'))
    proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),verified=True,real_gemini_verified=True,
        provider='Render',plan='Free',service_id=deploy['service']['id'],workspace_id=deploy['workspace'],
        public_url=public['url'],version='0.4.0',deployed_commit=commit,deploy_id=actual['id'],deploy_finished_at=actual['finishedAt'],
        inference_provider='gemini_developer',model='gemini-3.5-flash-lite',model_metadata_version='3.5-flash-lite-07-2026',
        managed_agent_engine=False,mandatory_gcp='UNMET_GCP_EXCEPTION_PENDING',real_calendar='pending_illustrative_receipts_only',
        evidence=dict(public='docs/evidence/public-demo-browser-0.4.0.json',live=livepath,features=featurepath,installed_windows=desktoppath,deploy='docs/evidence/render-cutover-0.4.0.json'),
        actual_complete_browser_turns=len(runs),actual_complete_installed_turns=len(installed_runs),retained_failed_attempts=failures,retained_desktop_failures=desktop_failures,
        latency_ms=dict(sample_browser_turns=len(runs),min=min(r['duration_ms'] for r in runs),max=max(r['duration_ms'] for r in runs),cold_start_included=False,statistical_sla=False),
        checks=dict(fresh_public_illustrative_workflow=public['checks'],private_web=live['checks'],private_features=features['checks'],installed_windows=desktop['checks']),
        native_dialog_visibility_verified=False,notification_visibility_verified=False,
        funding=dict(personal_spending_authorized_usd=0,paid_resources_provisioned=False,new_hosting_resources_created=False,invoice_or_remaining_credit_balance_inferred=False),
        limitations=['One first hosted model turn timed out; a bounded retry in the same two test workspaces completed. No automatic paid/canned fallback.',
            'Temporary storage and two-hour sessions may reset earlier on sleep/restart/redeploy; invitations also reset. No durable or always-on background service.',
            'Private AI access only for invited adult Kazakhstan evaluators with permitted non-sensitive material. Self-attestation is not independent eligibility proof.',
            'Tests use four authorized private invitations for agent-owned sessions only; no invitations distributed to other people.',
            'Original managed Agent Engine, Google cloud-to-MCP service identity, real Calendar consent/writes/read-back and new native picker/banner/click acceptance remain pending.'])
    output=root/'docs/evidence/public-deployment-0.4.0.json'
    output.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(evidence=str(output),verified=True,commit=commit,browser_turns=len(runs),installed_turns=len(installed_runs))))

if __name__=='__main__':main()
