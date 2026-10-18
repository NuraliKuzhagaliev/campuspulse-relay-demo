"""Record the verified 0.2.x release without rewriting preserved release artifacts."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
assert ROOT.drive.upper()=='D:'
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

version=read('package.json')['version']
assert version=='0.2.1','Use an explicit release-specific recorder for later versions.'
release=ROOT/'release'
if (release/'versions'/version/'manifest.json').exists():
    old=read(f'release/versions/{version}/manifest.json')
    for a in old['artifacts']:
        assert sha(release/'versions'/version/a['relative_path'])==a['sha256']
    raise SystemExit('This version is already preserved. Use a new version/revision instead of overwriting its artifacts.')
source_commit=git('rev-parse','HEAD')
deployment=read(f'docs/evidence/public-deployment-{version}.json')
browser=read(f'docs/evidence/public-demo-browser-{version}.json')
desktop=read(f'docs/evidence/desktop-contract-{version}.json')
imports=read(f'docs/evidence/desktop-import-regression-{version}.json')
evaluation=read('docs/evidence/continuation-evaluation.json')
presentation=read(f'docs/evidence/presentation-{version}.json')
assert deployment['verified'] and deployment['service_plan']=='free' and deployment['status']=='live'
assert browser['passed'] and browser['deployed_commit']==deployment['deployed_commit']
assert desktop['passed'] and desktop['version']==version and all(f['matches_current_source'] for f in desktop['packaged_files'])
assert imports['passed'] and all(f['matches_current_source'] for f in imports['packaged_files'])
assert evaluation['python']['tests']=='78' and evaluation['python']['failures']=='0' and evaluation['python']['errors']=='0'
assert presentation['public_demo_verified'] and presentation['slides']==10
runtime_paths=['relay','src','desktop','package.json','package-lock.json','infra','requirements.public.txt','requirements.public.lock.txt']
assert not git('diff','--name-only',deployment['deployed_commit'],source_commit,'--',*runtime_paths),'Runtime changed after the verified deployed commit.'

preserved=[]
for old_version in ['0.1.0','0.1.1','0.1.1-public-demo','0.2.0']:
    folder=release/'versions'/old_version;old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    for artifact in old['artifacts']:assert sha(folder/artifact['relative_path'])==artifact['sha256']
    preserved.append(dict(version=old_version,directory=str(folder),artifacts_hash_verified=len(old['artifacts'])))

archive=release/f'source/CampusPulseRELAY-{version}-source.zip';archive.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(archive),source_commit,'--','.',':(exclude)release/manifest.json'],cwd=ROOT,check=True)
with zipfile.ZipFile(archive,'a',zipfile.ZIP_DEFLATED) as z:
    z.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Source archive commit: {source_commit}\nPublic runtime commit: {deployment["deployed_commit"]}\nGenerated manifest is distributed alongside this archive to avoid circular hashing. Prior artifacts are retained separately.\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert not any(n.startswith(('CampusPulseRELAY/.local/','CampusPulseRELAY/.venv/','CampusPulseRELAY/node_modules/','CampusPulseRELAY/inputs/')) for n in z.namelist())
web=release/f'web/CampusPulseRELAY-{version}-web-build.zip';web.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(web,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted((ROOT/'dist').rglob('*')):
        if path.is_file():z.write(path,'dist/'+path.relative_to(ROOT/'dist').as_posix())
    z.writestr('README.txt','Serve these frontend files through the FastAPI gateway. The complete Python source/requirements and Docker deployment are in the source archive. This ZIP alone is not a backend.\n')

artifacts=[]
for kind,path in [('windows_installer',release/f'windows/CampusPulse-RELAY-{version}-x64-setup.exe'),('windows_portable',release/f'windows/CampusPulse-RELAY-{version}-x64-portable.exe'),('source_archive',archive),('web_frontend_build',web),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf']))]:
    artifacts.append(dict(kind=kind,path=str(path),relative_path=path.relative_to(release).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))

manifest=dict(schema_version=3,product='CampusPulse RELAY',version=version,created_at=datetime.now(timezone.utc).isoformat(),
    status='public_illustrative_release_verified_mandatory_gcp_pending',project_root=str(ROOT),source_commit=source_commit,
    source_commit_semantics='Source archive includes final evidence/authoring scripts; public runtime is pinned separately. Runtime paths match that deployed commit. No paid GCP deployment is claimed.',
    repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch='main',source_commit=source_commit,published=True),
    urls=dict(public_web=deployment['public_url'],local_web='http://127.0.0.1:8000',local_mcp='http://127.0.0.1:8001/mcp/',agent_api=None),
    public_demo_deployment=deployment,cloud=dict(provider='GCP',status='pending_organizer_credit_activation_and_verification',resource=None,revision=None,model_success_verified=False,paid_resources_provisioned=False,personal_spending_authorized_usd=0,credits_confirmed=False,public_illustrative_hosting_satisfies_mandatory_gate=False),
    enhancements=dict(**{f'F{i}':'locally_implemented' for i in range(1,6)},D1='locally_and_publicly_verified_illustrative',D2='locally_and_publicly_verified_structural_only',D3='public_illustrative_judge_verified_live_gcp_pending',real_calendar_acceptance='pending',real_gemini_acceptance='pending'),
    languages=dict(operational_ui=['en','ru','kk'],browser_verified=True,original_evidence_preserved=True,live_model_acceptance='pending'),
    verification=dict(python=evaluation['python'],browser_scenarios=10,public_workflow_passed=True,hosted_challenge_scenarios=2,native_policy_tests=3,installed_windows_contract=desktop['checks'],installed_import_regression=True,packaged_files_match=True,windows_signature='NotSigned',native_human_proof_release='0.1.1',native_picker_reobserved_in_0_2_0=False,native_banner_reobserved_in_0_2_0=False,native_click_focus_verified=False,mcp_tools=13,real_github_read=browser['checks']['hosted_github_read'],paid_model_calls=0,real_calendar_writes=0,presentation_slides=10,presentation_pdf='rendered slide pages',presentation_pptx='native editable'),
    preserved_releases=preserved,artifacts=artifacts,
    blockers=['Organizer credits: eligible project, billing account, balance and expiration unconfirmed; no personal spending authorized.','Real Gemini/Agent Engine resource and managed end-to-end path, cloud-to-MCP renewal/restart, real Calendar consent/write/read-back/revocation and isolated unseen-document live judge acceptance remain pending.','Real prose/table model extraction and confirmation UX acceptance pending; local cited proposal contract is not live evidence.','Windows native notification click/focus unverified; 0.1.1 human picker/banner proof retained separately.'],
    limitations=['Free single-instance Render demo: temporary SQLite and two-hour visitor capability sessions, with earlier reset on hosting inactivity/restarts/redeploys. No durable or multi-instance public persistence claimed.','Public imports 2 MiB / 12 sources including examples; manual GitHub observations cached five minutes with original provenance. Actual anonymous provider 429 and recovery are recorded.','Deterministic parser requires structured facts. Missing identity/course/term stays unresolved; scans have no OCR. Semantic draft correctness and grades are not inferred.','Unsigned Windows app requires the running local gateway for connected operations. Automated import checks substitute the native picker; new real native interaction is not claimed.','Prior 0.1.0 local recording is a preserved historical backup and was not re-recorded for this release.'],
    instructions=dict(judge='docs/judge_quickstart.md',evaluation='docs/evaluation_results.md',defects='docs/defect_ledger.md',contracts='docs/contract_inventory.md',after_credits='docs/live_acceptance_batch.md'))
(release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(release/'SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts),encoding='ascii')
target=release/'versions'/version;target.mkdir(exist_ok=True)
import shutil
for a in artifacts:
    dst=target/a['relative_path'];dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(dst)==a['sha256'],'Never overwrite an already preserved release.'
    else:shutil.copy2(release/a['relative_path'],dst)
if not (target/'manifest.json').exists():shutil.copy2(release/'manifest.json',target/'manifest.json')
print(json.dumps(dict(version=version,artifacts=len(artifacts),source_commit=source_commit,deployed_commit=deployment['deployed_commit'],preserved=preserved),indent=2))
