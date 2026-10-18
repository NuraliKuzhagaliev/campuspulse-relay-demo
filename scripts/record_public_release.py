"""Record verified public hosting alongside the preserved local release artifacts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
assert ROOT.drive.upper()=='D:'
assert json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version']=='0.1.1','Historical 0.1.1 recorder only; use package_continuation.py for 0.2.0.'
def read(relative):return json.loads((ROOT/relative).read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

deployment=read('docs/evidence/public-deployment.json')
browser=read('docs/evidence/public-demo-browser.json')
presentation=read('docs/evidence/public-presentation.json')
assert deployment['verified'] and browser['passed']
assert deployment['deployed_commit']==browser['deployed_commit']
assert deployment['status']=='live' and deployment['service_plan']=='free'
assert not deployment['google_runtime_enabled'] and not deployment['real_calendar_enabled']
assert presentation['public_demo_verified'] and presentation['public_url']==deployment['public_url']

manifest=read('release/manifest.json')
preserved=[]
for version in ['0.1.0','0.1.1']:
    folder=ROOT/'release/versions'/version
    old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    for artifact in old['artifacts']:
        assert sha(folder/artifact['relative_path'])==artifact['sha256']
    preserved.append(dict(version=version,directory=str(folder),git_tag='local-release-'+version,
                          artifacts_hash_verified=len(old['artifacts']),source_archive_commit=old['source_commit']))

manifest['status']='public_illustrative_demo_verified_mandatory_gcp_pending'
manifest['updated_at']=datetime.now(timezone.utc).isoformat()
manifest['source_commit_semantics']='Preserved local 0.1.1 source archive; public_demo_deployment.deployed_commit identifies the hosted source.'
manifest['repository']['public_demo_deployed_commit']=deployment['deployed_commit']
manifest['urls']['public_web']=deployment['public_url']
manifest['cloud']['provider']='GCP'
manifest['cloud']['public_illustrative_hosting_satisfies_mandatory_gate']=False
manifest['public_demo_deployment']=deployment
manifest['preserved_releases']=preserved
manifest['verification']['installed_source_comparison_commit']=manifest['source_commit']
manifest['verification']['windows_artifacts_unchanged']=True
manifest['verification']['public_https_browser_acceptance_passed']=True
manifest['verification']['public_browser_evidence']='docs/evidence/public-demo-browser.json'
manifest['verification']['current_python_tests']=61
manifest['verification']['public_http_security_tests']=5
manifest['verification']['existing_browser_scenarios_preserved']=8
manifest['verification']['public_demo_workflows']=list(browser['checks'])
manifest['verification']['public_backend_github_read']=browser['checks']['hosted_github_read']
manifest['verification']['public_presentation_slides']=8
manifest['verification']['public_presentation_validation']='docs/evidence/public-presentation-validation.json'
manifest['instructions']['public_demo']='docs/public_demo_hosting.md'
manifest['instructions']['public_verification']='node scripts/verify_public_demo.mjs '+deployment['public_url']
manifest['blockers']=[
    'Organizer credits: exact eligible GCP project/billing account, balance and expiration remain unconfirmed. No uncovered personal spending authorized.',
    'Actual Gemini/Vertex AI Agent Engine resource, managed API, cloud-to-MCP authentication/renewal/restart remain unverified.',
    'Real Google consent, approved Calendar write/read-back and revocation remain unverified.',
    'Managed judge session with real Calendar access and an unseen document remains unverified; public anonymous-demo isolation is separately verified.'
]
public_limit='Public Render demo uses temporary storage and two-hour isolated sessions, with earlier reset possible on idle spin-down/restarts/redeploys. Public uploads: 2 MiB, 12 sources including examples. GitHub observations may be reused for five minutes. No durable public persistence or managed AI is claimed.'
if public_limit not in manifest['limitations']:manifest['limitations'].append(public_limit)
manifest['artifacts']=[a for a in manifest['artifacts'] if not a['kind'].startswith('public_demo_presentation')]
for kind,key in [('public_demo_presentation_editable','pptx'),('public_demo_presentation_pdf','pdf')]:
    target=Path(presentation[key]);relative=target.relative_to(ROOT/'release').as_posix()
    manifest['artifacts'].append(dict(kind=kind,relative_path=relative,path=str(target),bytes=target.stat().st_size,sha256=sha(target)))
for artifact in manifest['artifacts']:
    assert sha(ROOT/'release'/artifact['relative_path'])==artifact['sha256']
(ROOT/'release/manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(ROOT/'release/SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in manifest['artifacts']),encoding='ascii')
print(json.dumps(dict(url=deployment['public_url'],deployed_commit=deployment['deployed_commit'],artifacts=len(manifest['artifacts']),preserved_versions=['0.1.0','0.1.1']),indent=2))
