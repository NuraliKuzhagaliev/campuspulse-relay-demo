"""Seal the actual hosted alternative result; preserve every earlier sealed revision."""
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
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
revision='0.4.0-hosted-r1';release=root/'release';sealed=release/'versions'/revision;submission=root/'submission'/revision
assert not sealed.exists() and not submission.exists(),'Choose a new revision; never overwrite a sealed package.'
assert not git('status','--porcelain'),'Commit reviewed source/evidence before packaging.'
commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
assert git('ls-remote','origin','refs/heads/'+branch).split()[0]==commit,'Push the exact archived source first.'
proof=read('docs/evidence/public-deployment-0.4.0.json');assert proof['verified'] and proof['real_gemini_verified']
deployed=proof['deployed_commit']
assert not git('diff',deployed,commit,'--','relay','src','infra','requirements.cloud.txt','package.json','package-lock.json','fixtures','public','tsconfig.json','vite.config.ts','index.html','.dockerignore'),'Deployed web runtime differs; verify new deployment first.'
desktop=read(proof['evidence']['installed_windows']);assert desktop['passed'] and desktop['checks']['native_reset_rotates_workspace_and_csrf']
for item in desktop['packaged_files']:assert sha(root/item['file'])==item['sha256']
assert read('docs/evidence/desktop-import-regression-0.4.0-hosted-r1.json')['passed']
assert read('docs/evidence/final-preserved-native-after-hosted.json')['passed']
regressions=read('docs/evidence/hosted-regressions-0.4.0.json');assert regressions['passed']
webproof=read('docs/evidence/final-web-bundle-0.4.0.json');assert webproof['passed']
presentation=read('docs/evidence/presentation-0.4.0.json');visual=read('docs/evidence/presentation-0.4.0-hosted-visual.json');assert visual['all_12_slides_verified'] and presentation['hosted_gemini_verified']
validation=json.loads(Path(presentation['validation']).read_text());assert validation['packageIntegrity']['status']=='pass' and validation['presentationLayout']['finding_count']==validation['presentationLayout']['warning_count']==0
preserved=[]
for folder in sorted((release/'versions').iterdir()):
    if not (folder/'manifest.json').exists():continue
    old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    for item in old['artifacts']:assert sha(folder/item['relative_path'])==item['sha256']
    preserved.append(dict(revision=folder.name,artifacts_hash_verified=len(old['artifacts'])))
source=release/f'source/CampusPulseRELAY-{revision}-source.zip';source.parent.mkdir(parents=True,exist_ok=True);assert not source.exists()
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),commit,'--','.',':(exclude)release/manifest.json'],cwd=root,check=True)
with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Version:0.4.0\nRevision:{revision}\nExact archived source:{commit}\nActual deployed web runtime:{deployed}\nNew source contains desktop-only IPC reset/CSRF repair, owner-clock tool/tests and actual hosted evidence/docs. Deployed frontend/backend sources are identical.\nOriginal managed GCP UNMET/EXCEPTION_PENDING. Real Calendar and native visibility/click remain pending.\nManifest/checksums distributed separately to avoid circular hashes.\n')
web=release/f'web/CampusPulseRELAY-{revision}-web-app.zip';web.parent.mkdir(parents=True,exist_ok=True);assert not web.exists()
shutil.copy2(root/'.local/final-integration/CampusPulseRELAY-0.4.0-web-app.zip',web)
private_tokens=[]
for path in (root/'.local/judge-private').glob('ai-*.json'):
    private_tokens += [value['token'].encode() for value in json.loads(path.read_text())['invitations']]
for package in (source,web):
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            clean=name.removeprefix('CampusPulseRELAY/')
            assert not clean.startswith(('.local/','.venv/','node_modules/','inputs/','installed/','submission/'))
            assert not (clean.startswith('.env') and clean!='.env.example')
            data=archive.read(name)
            assert not re.search(rb'AIza[0-9A-Za-z_-]{25,}',data),'Potential model credential: '+name
            assert not any(token in data for token in private_tokens),'Private invitation: '+name
        if package==web:
            for name,expected in webproof['runtime_files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==expected
artifacts=[]
for name in ('Install-D.cmd','Launch-Portable-D.cmd'):shutil.copy2(root/'desktop'/name,release/'windows'/name)
for kind,path in [('windows_installer',release/'windows/CampusPulse-RELAY-0.4.0-x64-setup.exe'),('windows_portable',release/'windows/CampusPulse-RELAY-0.4.0-x64-portable.exe'),('complete_web_application',web),('source_archive',source),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf'])),('D_drive_launch_wrapper',release/'windows/Install-D.cmd'),('D_drive_launch_wrapper',release/'windows/Launch-Portable-D.cmd')]:
    artifacts.append(dict(kind=kind,path=str(path),relative_path=path.relative_to(release).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
manifest=read('release/versions/0.4.0-local-integration-r1/manifest.json')
manifest['preserved_local_verification']=manifest.pop('verification')
manifest.update(release_revision=revision,status='HOSTED_ALTERNATIVE_GEMINI_VERIFIED_GCP_CALENDAR_NATIVE_PENDING',created_at=datetime.now(timezone.utc).isoformat(),source_commit=commit,source_commit_semantics='Exact clean pushed source archive. Deployed web runtime commit is separate and web runtime files are unchanged. New desktop reset/CSRF and owner-clock fixes plus docs/tests are included. Manifest metadata may be committed subsequently.',
    repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,source_commit=commit,published=True),
    urls=dict(public_web=proof['public_url'],public_version='0.4.0',local_web='http://127.0.0.1:8000',managed_agent_api=None),
    public_deployment=dict(provider='Render',plan='Free',service_id=proof['service_id'],deploy_id=proof['deploy_id'],actual_version='0.4.0',actual_commit=deployed,new_0_4_deployed=True,verified=True,real_gemini_verified=True,web_runtime_identical_to_archived_source=True),
    verification=dict(hosted_evidence='docs/evidence/public-deployment-0.4.0.json',regressions=regressions,actual_current_installed_package_source_match=True,preserved_local_baseline='preserved_local_verification',managed_gcp='UNMET_GCP_EXCEPTION_PENDING',real_calendar='pending',new_native_visibility_click='pending_human'),hosted_verification=proof,artifacts=artifacts,preserved_releases=preserved,
    additional_regressions=dict(owner_clock_tests_passed=2,ipc_policy_tests_passed=5,installed_reset_rotation=True,import_both_paths=True,preserved_native_45_95=True),
    presentation=dict(slides=12,editable=True,pdf='all12_pages_pixel_match_verified_renders',native_powerpoint_opened=False))
manifest['inference'].update(hosted_verified=True,full_acceptance='pending_original_managed_and_real_calendar_gates')
manifest['windows'].update(current_public_backend_version='0.4.0',local_gateway_override_required_for_all_0_4_features_until_cutover=False,actual_public_gemini_query_verified=True,reset_exact_route_csrf_fixed=True,pre_hosted_install_backup=str(root/'installed/preserved-0.4.0-local-integration-r1'))
manifest['limitations'].append('One first hosted Gemini request timed out; a bounded repeat completed. Initial installed reset failed after successful import/chat and was repaired/reinstalled/rechecked. Original failure evidence retained; no statistical success/SLA claim.')
(release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
checks=''.join(item['sha256']+'  '+item['relative_path']+'\n' for item in artifacts)
(release/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
for target in (sealed,submission):
    target.mkdir(parents=True)
    for item in artifacts:
        destination=target/item['relative_path'];destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(release/item['relative_path'],destination);assert sha(destination)==item['sha256']
    shutil.copy2(release/'manifest.json',target/'manifest.json');(target/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
    for name in ('final_judge_guide.md','final_native_check.md','final_integration_ledger.md','organizer_update.md'):
        shutil.copy2(root/'docs'/name,target/name)
    (target/'ENTRY.txt').write_text(f'Public HTTPS:{proof["public_url"]}\nWeb/runtime version0.4.0 deployed:{deployed}\nExact source archive:{commit}\nOriginal GCP UNMET/EXCEPTION_PENDING. Real Calendar pending. New native picker/banner/click pending.\nNo entry submitted by Codex. Temporary storage; private AI evaluation access required.\n',encoding='utf-8')
    (target/'evidence-index.json').write_text(json.dumps(dict(source_commit=commit,hosted=proof,presentation=presentation,visual=visual),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(revision=revision,source_commit=commit,deployed_commit=deployed,artifacts=len(artifacts),preserved_hashes=sum(p['artifacts_hash_verified'] for p in preserved),submission=str(submission)),indent=2))
