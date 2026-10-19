"""Seal a candid local integration delivery. Never upgrades hosting or overwrites sealed versions."""
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1];assert root.drive.lower()=='d:'
read=lambda p:json.loads((root/p).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True,encoding='utf-8').strip()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
version=read('package.json')['version'];assert version=='0.4.0'
revision='0.4.0-local-integration-r1';release=root/'release';sealed=release/'versions'/revision;submission=root/'submission'/revision
assert not sealed.exists() and not submission.exists(),'Preserve sealed delivery; choose a new revision.'
assert not git('status','--porcelain'),'Commit all reviewed source/evidence before packaging.'
commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
remote=git('ls-remote','origin','refs/heads/'+branch).split()[0];assert remote==commit,'Push the reviewed branch before creating a published-source package.'
evaluation=read('docs/evidence/final-verification-0.4.0.json');assert evaluation['python']['failures']==evaluation['python']['errors']==0
assert evaluation['browser']['failed']==0 and all(evaluation['installed_desktop'].values())
webproof=read('docs/evidence/final-web-bundle-0.4.0.json');assert webproof['passed'] and 'relay/gateway.py' in webproof['runtime_files'] and 'dist/index.html' in webproof['runtime_files']
presentation=read('docs/evidence/presentation-0.4.0.json');visual=read('docs/evidence/presentation-0.4.0-visual.json');assert visual['all_12_slides_individually_reviewed']
validation=read(str(Path(presentation['validation']).relative_to(root)));assert validation['packageIntegrity']['status']=='pass' and validation['presentationLayout']['finding_count']==validation['presentationLayout']['warning_count']==0
desktop=read('docs/evidence/four-desktop-0.4.0.json')
for value in desktop['packaged_files']:assert sha(root/value['file'])==value['sha256'],'Packaged files changed after installed verification.'
preserved=[]
for folder in sorted((release/'versions').iterdir()):
    if not (folder/'manifest.json').exists():continue
    old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    for a in old['artifacts']:assert sha(folder/a['relative_path'])==a['sha256'],str(folder/a['relative_path'])
    preserved.append(dict(revision=folder.name,artifacts_hash_verified=len(old['artifacts'])))
source=release/f'source/CampusPulseRELAY-{revision}-source.zip';source.parent.mkdir(parents=True,exist_ok=True);assert not source.exists()
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),commit,'--','.',':(exclude)release/manifest.json'],cwd=root,check=True)
with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as z:
    z.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Version: {version}\nRevision: {revision}\nExact archived source commit: {commit}\nPublished branch: {branch}\nGenerated release manifest/checksums are distributed separately to avoid circular hashes.\nActual public service remains0.2.1 at83552161ec22c7cf44746433425d3b2b99e042c4. New0.4 hosted Gemini cutover and managed GCP/Calendar acceptance are pending.\n')
web=release/f'web/CampusPulseRELAY-{revision}-web-app.zip';web.parent.mkdir(parents=True,exist_ok=True);assert not web.exists()
shutil.copy2(root/'.local/final-integration/CampusPulseRELAY-0.4.0-web-app.zip',web)
private_tokens=[]
for p in (root/'.local/judge-private').glob('ai-*.json'):
    private_tokens += [v['token'].encode() for v in json.loads(p.read_text())['invitations']]
for archive in (source,web):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            clean=name.removeprefix('CampusPulseRELAY/')
            assert not clean.startswith(('.local/','.venv/','node_modules/','inputs/','installed/','submission/'))
            assert not (clean.startswith('.env') and clean!='.env.example')
            data=z.read(name)
            assert not re.search(rb'AIza[0-9A-Za-z_-]{25,}',data),'Potential model credential in '+name
            assert not any(token in data for token in private_tokens),'Private invitation in '+name
        if archive==web:
            for name,expected in webproof['runtime_files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==expected
artifacts=[]
for kind,path in [('windows_installer',release/f'windows/CampusPulse-RELAY-{version}-x64-setup.exe'),('windows_portable',release/f'windows/CampusPulse-RELAY-{version}-x64-portable.exe'),('complete_web_application',web),('source_archive',source),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf']))]:
    artifacts.append(dict(kind=kind,path=str(path),relative_path=path.relative_to(release).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
public=read('docs/evidence/final-public-preserved.json')
manifest=dict(schema_version=5,product='CampusPulse RELAY',version=version,release_revision=revision,status='LOCAL_GEMINI_VERIFIED_HOSTED_CALENDAR_GCP_PENDING',created_at=datetime.now(timezone.utc).isoformat(),project_root=str(root),source_commit=commit,source_commit_semantics='Exact clean pushed source archived; generated manifest/checksums added separately. A subsequent metadata-only commit may contain this manifest.',repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,source_commit=commit,published=True),urls=dict(public_web='https://campuspulse-relay-demo.onrender.com',public_version='0.2.1',local_web='http://127.0.0.1:8000',local_https_staging='https://localhost:8017',managed_agent_api=None),public_deployment=dict(service_id='srv-dbajs73bc2fs73bm9mfg',provider='Render',plan='Free',actual_version='0.2.1',actual_commit=public['health']['deployed_commit'],new_0_4_deployed=False,new_0_4_blocker='Owner must save free Gemini key in existing service private environment, then execute and verify reviewed cutover.'),inference=dict(provider='gemini_developer',model='gemini-3.5-flash-lite',metadata_version='3.5-flash-lite-07-2026',project='gen-lang-client-0595303951',real_local_https_verified=True,hosted_verified=False,full_acceptance='pending'),gcp=dict(status='UNMET_GCP_EXCEPTION_PENDING',reasoning_engine=None,free_trial='closed_prepayment_required_no_visible_credits',credits_provided_by_organizer=False,paid_resources_created=False,personal_spending_authorized_usd=0),real_calendar=dict(status='pending_app_consent_runtime_access_and_exact_ui_approval',external_writes_verified=False),enhancements=evaluation['enhancements'],verification=evaluation,packaged_web_verified_in_minimal_environment=webproof['passed'],windows=dict(installed_version='0.4.0',signature='NotSigned',default_gateway='https://campuspulse-relay-demo.onrender.com',current_public_backend_version='0.2.1',local_gateway_override_required_for_all_0_4_features_until_cutover=True,native_dialogs_substituted_in_automated_contracts=True,new_actual_dialog_banner_click_acceptance='pending_human',preserved_0_3_install='D:\\projects\\CampusPulseRELAY\\installed\\preserved-0.3.0'),presentation=dict(slides=12,editable=True,pdf='rendered_pages_all_pixel_compared',native_powerpoint_opened=False),deadline=dict(reported='2026-10-20 23:59',organizer_timezone_confirmed=False,planning_timezone='Asia/Qyzylorda UTC+05:00',internal_freeze_local='2026-10-20 20:00'),limitations=['Free host may sleep and reset uploads/sessions/SQLite/invitations; no always-on hosted Scheduler or durable hosted persistence.','Private unpaid AI only for invited18+ professional/hackathon evaluators in Kazakhstan with permitted non-sensitive material; attestation is not independent eligibility verification.','All current Calendar receipts are illustrative. Passport copies contain archived untrusted extracts, never authority/credentials or refreshed external observations.','No managed Agent Engine resource or amended replacement criterion verified. No contest entry/message sent.'],preserved_releases=preserved,artifacts=artifacts,instructions=dict(judge='docs/final_judge_guide.md',cutover='docs/final_cutover_plan.md',native='docs/final_native_check.md',requirements='docs/final_integration_ledger.md',funding='docs/cloud_setup.md'))
(release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
checks=''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts)
(release/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
for target in (sealed,submission):
    target.mkdir(parents=True)
    for a in artifacts:
        dest=target/a['relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'release'/a['relative_path'],dest);assert sha(dest)==a['sha256']
    shutil.copy2(release/'manifest.json',target/'manifest.json');(target/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
    for name in ('final_judge_guide.md','final_cutover_plan.md','final_native_check.md','final_integration_ledger.md','organizer_update.md'):
        shutil.copy2(root/'docs'/name,target/name)
    (target/'ENTRY.txt').write_text(f'Repository: https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo/tree/{commit}\nPublic HTTPS: https://campuspulse-relay-demo.onrender.com (actual0.2.1, not0.4 live AI)\nCandidate: {revision}\nOriginal GCP criterion UNMET / GCP_EXCEPTION_PENDING. See manifest and exact pending actions.\n',encoding='utf-8')
    index=dict(source_commit=commit,evaluation=evaluation,web=webproof,presentation=presentation,visual=visual)
    (target/'evidence-index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(version=version,revision=revision,source_commit=commit,artifacts=len(artifacts),preserved_hashes=sum(p['artifacts_hash_verified'] for p in preserved),submission=str(submission),new_public_deployment=False),indent=2))
