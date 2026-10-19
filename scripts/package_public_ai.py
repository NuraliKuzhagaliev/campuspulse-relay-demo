"""Seal 0.4.1 without replacing any prior revision or publishing private content."""
import hashlib,json,re,shutil,subprocess,zipfile
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];assert root.drive.lower()=='d:'
read=lambda n:json.loads((root/n).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True,encoding='utf-8').strip()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
revision='0.4.1-public-ai-r2';release=root/'release';sealed=release/'versions'/revision;submission=root/'submission'/revision
assert not sealed.exists() and not submission.exists()
assert not git('status','--porcelain'),'Commit and push the reviewed source/evidence first.'
commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
assert git('ls-remote','origin','refs/heads/main').split()[0]==commit
assert git('ls-remote','origin','refs/heads/'+branch).split()[0]==commit
proof=read('docs/evidence/public-deployment-0.4.1.json');deployed=proof['deployed_commit']
assert proof['verified'] and proof['real_gemini_verified'] and proof['plan']=='Free'
assert not git('diff',deployed,commit,'--','relay','src','infra','requirements.cloud.txt','package.json','package-lock.json','fixtures','public','tsconfig.json','vite.config.ts','index.html','.dockerignore')
live=read(proof['evidence']['real_public']);load=read(proof['evidence']['simulated_100']);desktop=read(proof['evidence']['installed'])
assert live['verified'] and live['actual_complete_real_gemini_turns']==2 and load['passed'] and load['sessions']==100 and load['actual_gemini_calls']==0 and load['checks']['plan_isolation_100']
assert desktop['passed'] and read(proof['evidence']['workflow'])['passed'] and read(proof['evidence']['preserved_native'])['passed']
for f in desktop['packaged_files']:assert sha(root/f['file'])==f['sha256']
presentation=read('docs/evidence/presentation-0.4.1.json');visual=read('docs/evidence/presentation-0.4.1-visual.json');assert visual['all_12_slides_verified']
validation=json.loads(Path(presentation['validation']).read_text());assert validation['packageIntegrity']['status']=='pass' and validation['presentationLayout']['finding_count']==0
assert visual['layout_warning_review']['accepted']
webproof=read('docs/evidence/final-web-bundle-0.4.1.json');assert webproof['passed']
preserved=[]
for folder in sorted((release/'versions').iterdir()):
    if not (folder/'manifest.json').exists():continue
    old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
    for item in old['artifacts']:assert sha(folder/item['relative_path'])==item['sha256']
    preserved.append(dict(revision=folder.name,artifacts_hash_verified=len(old['artifacts'])))
source=release/f'source/CampusPulseRELAY-{revision}-source.zip';assert not source.exists()
source.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),commit,'--','.',':(exclude)release/manifest.json'],cwd=root,check=True)
with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as z:
    z.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Version:0.4.1\nRevision:{revision}\nExact clean pushed source:{commit}\nActual deployed web runtime:{deployed}\nDeployed frontend/backend/runtime files match archived source. Later changes are verification, documentation, packaging and presentation sources. Manifest/checksums distributed separately to avoid circular hashes.\nPublic automatic anonymous Gemini/MCP verified. Original managed GCP unmet; optional real Calendar and new human native observations pending.\n')
web=release/f'web/CampusPulseRELAY-{revision}-web-app.zip';assert not web.exists();web.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'.local/final-integration/CampusPulseRELAY-0.4.1-web-app.zip',web)
for package in (source,web):
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        for name in z.namelist():
            clean=name.removeprefix('CampusPulseRELAY/')
            assert not clean.startswith(('.local/','.venv/','node_modules/','inputs/','installed/','submission/'))
            assert not (clean.startswith('.env') and clean!='.env.example')
            assert not re.search(rb'AIza[0-9A-Za-z_-]{25,}',z.read(name)),'Potential credential in archive'
        if package==web:
            for name,h in webproof['runtime_files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
artifacts=[]
for name in ('Install-D.cmd','Launch-Portable-D.cmd'):shutil.copy2(root/'desktop'/name,release/'windows'/name)
for kind,p in [('windows_installer',release/'windows/CampusPulse-RELAY-0.4.1-x64-setup.exe'),('windows_portable',release/'windows/CampusPulse-RELAY-0.4.1-x64-portable.exe'),('complete_local_illustrative_web_application',web),('source_archive',source),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf'])),('D_drive_launch_wrapper',release/'windows/Install-D.cmd'),('D_drive_launch_wrapper',release/'windows/Launch-Portable-D.cmd')]:
    artifacts.append(dict(kind=kind,path=str(p),relative_path=p.relative_to(release).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema_version=6,product='CampusPulse RELAY',version='0.4.1',release_revision=revision,status='PUBLIC_ANONYMOUS_GEMINI_MCP_VERIFIED_MANAGED_GCP_CALENDAR_NATIVE_PENDING',created_at=datetime.now(timezone.utc).isoformat(),project_root=str(root),source_commit=commit,source_commit_semantics='Exact clean pushed source archive. Deployed runtime commit is recorded separately and runtime files are identical. Manifest metadata may be committed subsequently.',repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,default_branch='main',source_commit=commit,published=True),urls=dict(public_web=proof['public_url'],public_version='0.4.1',local_web='http://127.0.0.1:8000',managed_agent_api=None),public_deployment=proof,verification=dict(python_tests_passed=132,python_subtests_passed=3,ipc_policy_tests_passed=6,public_live=live,simulated_provider_100=load,installed=desktop,web_bundle=webproof['checks'],managed_gcp='UNMET_GCP_EXCEPTION_PENDING',real_calendar='pending_optional_separate_consent',new_native_visibility_click='pending_human',original_native_45_95=read(proof['evidence']['preserved_native'])),inference=dict(provider='gemini_developer',model='gemini-3.5-flash-lite',route='alternative_hosted',actual_public_complete_turns=2,public_access='automatic_anonymous_isolated_queue',personal_invitations_required=False,user_registration_required=False,user_api_key_required=False,managed_agent_engine=False,full_enhancement_acceptance='pending'),queue=dict(one_outstanding_per_workspace=True,workers=2,per_model_call_fair_quota_tickets=True,observed_project_limits=dict(rpm=15,tpm=250000,rpd=500),remaining_balance_claimed=False,daily_reset='midnight America/Los_Angeles',provider_429_authoritative=True),core_enhancements='F1-F5 locally implemented; real Calendar/full enhancement-level Gemini acceptance pending',windows=dict(version='0.4.1',unsigned=True,installed_dir=str(root/'installed/CampusPulse RELAY'),current_package_source_match=True,zero_model_public_IPC_checks=True,original_45_95_preserved=True,old_install_backup=str(root/'installed/preserved-0.4.0-hosted-r1')),presentation=dict(slides=12,editable=True,pdf_all_pages_pixel_match=True,native_powerpoint_opened=False,one_visual_style_warning_reviewed=True),funding=dict(personal_spending_authorized_usd=0,paid_upgrade=False,new_infrastructure=False,organizer_credits_expected=False),limitations=['Free temporary storage can reset uploads/sessions/history/queue on restart/redeploy and the host can sleep. No durable or always-on guarantee.','Free Gemini requires adult eligible professional/hackathon evaluation and permitted non-sensitive input. Region/age statement is self-attestation.','First public batch retained one Google504 and one complete turn. The next pair completed. A later plan-harness precondition failure was corrected and non-model checks repeated without additional model calls. No statistical success/SLA claim.','100-session provider is simulated, with seeded plan isolation fixtures; zero real Gemini calls in that load test.','Actual new native Open/Save/cancel/banner/click needs human observation; installed contracts do not replace that.','Public AI grants no personal Calendar permission. Current public Calendar receipts are illustrative.','Original managed Agent Engine deployment/cloud-to-MCP acceptance remains unmet; no payment authorized.','New public evidence contains only metadata/hashes. Full answers/documents/citations/cookies/content screenshots remain privately on D:.'],artifacts=artifacts,preserved_releases=preserved)
manifest['verification']['targeted_browser_tests_passed']=6
manifest['presentation']['reused_reviewed_revision']='0.4.1-public-ai-r1'
manifest['windows']['prior_r1_installation_backup']=str(root/'installed/preserved-0.4.1-public-ai-r1')
manifest['limitations'].append('Current GitHub anonymous upstream quota returned429. Useful error is verified; the earlier actual hosted live read remains preserved, and no fresh read is claimed for the quota-limited r2 check.')
checks=''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts)
(release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');(release/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
for target in (sealed,submission):
    target.mkdir(parents=True)
    for a in artifacts:
        dst=target/a['relative_path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(release/a['relative_path'],dst);assert sha(dst)==a['sha256']
    shutil.copy2(release/'manifest.json',target/'manifest.json');(target/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
    for name in ('final_judge_guide.md','remaining_actions_0.4.1.md','final_integration_ledger.md','public_ai_access.md'):shutil.copy2(root/'docs'/name,target/name)
    (target/'ENTRY.txt').write_text(f'Public HTTPS:{proof["public_url"]}\nNo invitation, registration, Google login or visitor API key. Automatic isolated temporary workspace, real queued Gemini/MCP.\nRuntime:{deployed}\nArchived source:{commit}\nOriginal managed GCP unmet. Real Calendar optional/pending. New actual native picker/banner/click pending. No personal payment or contest submission.\n',encoding='utf-8')
    (target/'evidence-index.json').write_text(json.dumps(dict(deployment=proof,live=live,simulated_load=load,presentation=presentation,visual=visual),indent=2)+'\n')
print(json.dumps(dict(revision=revision,archived_source_commit=commit,deployed_commit=deployed,artifacts=len(artifacts),preserved_hashes=sum(p['artifacts_hash_verified'] for p in preserved),submission=str(submission))))
