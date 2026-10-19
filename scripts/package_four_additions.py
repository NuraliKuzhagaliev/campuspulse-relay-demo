"""Seal the reviewable local 0.3.0 candidate; never overwrite prior versions."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
assert ROOT.drive.upper()=='D:'
read=lambda name:json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()

version=read('package.json')['version'];assert version=='0.3.0'
revision='0.3.0-r1'
release=ROOT/'release';target=release/'versions'/revision
if target.exists():raise SystemExit('This candidate version is already preserved. Use a later version; never overwrite sealed artifacts.')
assert not git('status','--porcelain'),'Commit the concrete reviewed source/evidence before sealing its archive.'
commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
evaluation=read('docs/evidence/four-evaluation-0.3.0.json')
web_proof=read('docs/evidence/four-web-bundle.json');assert web_proof['passed']
assert evaluation['python']['tests']=='111' and evaluation['python']['errors']=='0' and evaluation['python']['failures']=='0'
assert evaluation['browser']['passed']==13 and evaluation['local_public_mode']['passed']==4
assert evaluation['mcp']['tools']==14 and evaluation['mcp']['passed']
desktop=read('docs/evidence/four-desktop-0.3.0.json');assert desktop['passed'] and all(f['matches_source'] for f in desktop['packaged_files'])
assert read('docs/evidence/desktop-contract-0.3.0.json')['passed'] and read('docs/evidence/desktop-import-regression-0.3.0.json')['passed']
for record in desktop['packaged_files']:assert sha(ROOT/record['file'])==record['sha256'],'Packaged runtime changed after installed verification.'

preserved=[]
for old_version in ['0.1.0','0.1.1','0.1.1-public-demo','0.2.0','0.2.1','0.3.0']:
    folder=release/'versions'/old_version;old=read(str(folder.relative_to(ROOT)/'manifest.json'))
    for artifact in old['artifacts']:assert sha(folder/artifact['relative_path'])==artifact['sha256']
    preserved.append(dict(version=old_version,directory=str(folder),artifacts_hash_verified=len(old['artifacts'])))

source=release/f'source/CampusPulseRELAY-{revision}-source.zip';source.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),commit,'--','.',':(exclude)release/manifest.json'],cwd=ROOT,check=True)
with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as z:
    z.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Revision: {revision}\nLocal source commit: {commit}\nBranch: {branch}\nNot pushed/published. Public remains0.2.1 at83552161ec22c7cf44746433425d3b2b99e042c4.\nGenerated manifest is separate to avoid circular hashing. Unmodified native passport dialogs remain a human acceptance gate.\n')
with zipfile.ZipFile(source) as z:
    assert z.testzip() is None
    assert not any(n.startswith(tuple('CampusPulseRELAY/'+p for p in ('.local/','.venv/','node_modules/','inputs/','installed/'))) for n in z.namelist())
    assert not any(n.endswith('/.env') for n in z.namelist())

web=release/f'web/CampusPulseRELAY-{revision}-web-app.zip';web.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(web,'w',zipfile.ZIP_DEFLATED) as z:
    for folder in ('dist','relay','fixtures'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':z.write(path,path.relative_to(ROOT).as_posix())
    for filename in ('requirements.public.txt','requirements.public.lock.txt','scripts/run-web-bundle.ps1','LICENSE','docs/workspace_passport.md','docs/four_additions_acceptance.md'):
        z.write(ROOT/filename,filename)
    z.writestr('README.txt',f'CampusPulse RELAY{version} complete local web application: built React frontend + actual Python backend.\nExtract on D:. Run .\\scripts\\run-web-bundle.ps1 (Python3.13 installed). It creates dependencies/temp/cache/data on D: and serves localhost8000.\nSource revision {commit}. No cloud/model/Calendar credentials required for the illustrative flow. Source archive contains full development/public deployment infrastructure; no public replacement is authorized by this package.\n')
with zipfile.ZipFile(web) as z:
    assert z.testzip() is None and 'relay/gateway.py' in z.namelist() and 'dist/index.html' in z.namelist()
    for filename,expected in web_proof['runtime_files'].items():assert hashlib.sha256(z.read(filename)).hexdigest()==expected,'Web runtime changed after isolated bundle acceptance.'

artifacts=[]
for kind,path in [('windows_installer',release/f'windows/CampusPulse-RELAY-{version}-x64-setup.exe'),('windows_portable',release/f'windows/CampusPulse-RELAY-{version}-x64-portable.exe'),('complete_web_application',web),('source_archive',source)]:
    artifacts.append(dict(kind=kind,path=str(path),relative_path=path.relative_to(release).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
public=read('docs/evidence/public-deployment-0.2.1.json')
manifest=dict(schema_version=4,product='CampusPulse RELAY',version=version,release_revision=revision,created_at=datetime.now(timezone.utc).isoformat(),status='local_reviewable_candidate_native_human_gate_pending_not_published',project_root=str(ROOT),source_commit=commit,source_commit_semantics='Local committed source, verification and docs are archived. Final generated manifest is distributed separately. No public/cloud deployment of0.3.0.',repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,source_commit=commit,published=False),urls=dict(local_web='http://127.0.0.1:8000',public_web=public['public_url'],public_version='0.2.1',agent_api=None),public_demo_deployment=public,public_deployment_replaced=False,cloud=dict(provider='GCP',status='deferred_pending_organizer_credit_eligibility_balance_expiration',model_calls=0,real_calendar_writes=0,new_resources_provisioned=0,personal_spending_authorized_usd=0),enhancements=dict(**{f'F{i}':'locally_implemented' for i in range(1,6)},A1='implemented_local_and_installed_contracts_verified',A2='implemented_local_browser_verified',A3='implemented_live_public_read_and_signed_local_MCP_verified',A4='implemented_cross_device_contracts_verified_unmodified_native_dialog_gate_pending',D1_D2_D3='preserved',real_gemini_acceptance='pending',real_calendar_acceptance='pending'),languages=dict(operational_ui=['en','ru','kk'],viewport_widths=[390,768,1280,1440],model_acceptance='pending'),verification=evaluation,preserved_releases=preserved,artifacts=artifacts,preserved_presentation=dict(version='0.2.1',pptx=str(release/'presentation/CampusPulse-RELAY-0.2.1-quality-verified.pptx'),pdf=str(release/'presentation/CampusPulse-RELAY-0.2.1-quality-verified.pdf'),regenerated=False,scope='Verified prior public release; not a claim that0.3.0 is public or GCP complete'),blockers=['True unmodified Windows passport Open/Save/cancel/restore/restart interaction pending human after supported helper initialization failure.','Firestore addition transactions fail closed until separately verified.','Mandatory actual Gemini/Agent Engine/cloud-to-MCP auth/Calendar consent-write-readback/authenticated hosted unseen-document judge acceptance deferred.','Organizer eligible project/billing/credit balance/expiration unconfirmed; no uncovered personal spend authorized.','0.3.0 is not published or deployed; public remains the preserved0.2.1 revision.'],limitations=['Manual unencrypted portable extracts are archived untrusted copies, not original binary/upstream verification. Calendar busy details, approvals, journals and accepted plans are excluded; re-import/reconnect/recompute.','Timers/logs/completion are personal reports; positive remaining rounds up to30 minutes. Suggestions require five eligible pre-start frozen samples and remain a heuristic.','Clarification evaluates a bounded selected set; unknown is not infeasible. Waiting PR gates have no assumed release time; latest safe handoff unknown.','Unsigned desktop requires a running local gateway. Real new banner/click visibility not claimed. Public storage remains temporary; this candidate has local public-mode tests, not hosted0.3.0 HTTPS acceptance.'],instructions=dict(acceptance='docs/four_additions_acceptance.md',design_and_demo='docs/four_additions_design.md',passport='docs/workspace_passport.md',native_human='docs/native_passport_check.md',later_cloud='docs/live_acceptance_batch.md'))
(release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(release/'SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts),encoding='ascii')
target.mkdir(parents=True)
for a in artifacts:
    dst=target/a['relative_path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(release/a['relative_path'],dst);assert sha(dst)==a['sha256']
shutil.copy2(release/'manifest.json',target/'manifest.json');shutil.copy2(release/'SHA256SUMS.txt',target/'SHA256SUMS.txt')
print(json.dumps(dict(version=version,source_commit=commit,published=False,artifacts=len(artifacts),preserved_artifact_hashes=sum(p['artifacts_hash_verified'] for p in preserved),native_human_pending=True),indent=2))
