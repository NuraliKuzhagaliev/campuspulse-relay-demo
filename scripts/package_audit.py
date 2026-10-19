"""Seal a factual audit candidate without weakening its unverified acceptance gates."""
import hashlib,json,re,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REVISION='0.5.0-audit-r1'
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert ROOT.drive.lower()=='d:'
    release=ROOT/'release';sealed=release/'versions'/REVISION;submission=ROOT/'submission'/REVISION
    assert not sealed.exists() and not submission.exists(),'Never overwrite a sealed revision.'
    assert not git('status','--porcelain'),'Commit and push reviewed source/evidence first.'
    commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
    for ref in ('main',branch):assert git('ls-remote','origin','refs/heads/'+ref).split()[0]==commit
    acceptance=read('docs/evidence/non-gcp-0.5.0.json');deployed=acceptance['deployed_commit']
    deployment=read('docs/evidence/public-deployment-0.5.0.json')
    assert deployment['verified'] and deployment['deployed_commit']==deployed and deployment['plan']=='Free'
    runtime_paths=['relay','src','desktop','infra','requirements.cloud.txt','requirements.public.txt','requirements.public.lock.txt','package.json','package-lock.json','fixtures','public','tsconfig.json','vite.config.ts','index.html','.dockerignore','.gitattributes']
    assert not git('diff',deployed,commit,'--',*runtime_paths),'Archive must match the deployed runtime source.'
    live=read(acceptance['documents']['evidence']);assert live['passed'] and len(live['cases'])==5 and len(live['runs'])==6
    load=read('docs/evidence/audit-100-simulated.json');assert load['passed'] and load['sessions']==100 and load['actual_gemini_calls']==0
    samples=read('docs/evidence/audit-public-samples.json');assert samples['passed'] and len(samples['files'])==13 and samples['deployed_commit']==deployed
    desktop=read('docs/evidence/audit-desktop-0.5.0.json');assert desktop['passed']
    for item in desktop['packaged_files']:assert sha(ROOT/item['file'])==item['sha256']
    assert read('docs/evidence/preserved-native-0.5.0.json')['passed']
    webproof=read('docs/evidence/final-web-bundle-0.5.0.json');assert webproof['passed']
    presentation=read('docs/evidence/presentation-0.5.0.json');visual=read('docs/evidence/presentation-0.5.0-visual.json')
    assert visual['all_12_slides_verified'] and presentation['NON_GCP_READY']==acceptance['NON_GCP_READY']
    validation=json.loads(Path(presentation['validation']).read_text(encoding='utf-8'))
    assert validation['packageIntegrity']['status']=='pass' and validation['presentationLayout']['finding_count']==0
    preserved=[]
    for folder in sorted((release/'versions').iterdir()):
        if not (folder/'manifest.json').exists():continue
        old=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
        for item in old['artifacts']:assert sha(folder/item['relative_path'])==item['sha256'],str(folder/item['relative_path'])
        preserved.append(dict(revision=folder.name,artifacts_hash_verified=len(old['artifacts'])))
    source=release/f'source/CampusPulseRELAY-{REVISION}-source.zip';assert not source.exists();source.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),commit,'--','.',':(exclude)release/manifest.json'],cwd=ROOT,check=True)
    with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as z:
        z.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Audit candidate {REVISION}\nExact clean pushed archived source:{commit}\nActual public runtime:{deployed}\nDeployed runtime source matches archived runtime files. Later source changes contain documentation/verification/presentation/packaging only. Manifest/checksums are separate to avoid circular hashes.\nNON_GCP_READY={acceptance["NON_GCP_READY"]}\nReal Calendar/native remaining gates and managed GCP acceptance remain explicit. No personal spending.\n')
    web=release/f'web/CampusPulseRELAY-{REVISION}-web-app.zip';assert not web.exists();web.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'.local/final-integration/CampusPulseRELAY-0.5.0-web-app.zip',web)
    for package in (source,web):
        with zipfile.ZipFile(package) as z:
            assert z.testzip() is None
            for name in z.namelist():
                clean=name.removeprefix('CampusPulseRELAY/')
                assert not clean.startswith(('.local/','.venv/','node_modules/','inputs/','installed/','submission/'))
                assert not(clean.startswith('.env') and clean!='.env.example')
                assert not re.search(rb'(?:AIza[0-9A-Za-z_-]{25,}|github_pat_[0-9A-Za-z_]{40,}|ghp_[0-9A-Za-z]{30,})',z.read(name)),'Potential secret in archive'
            if package==web:
                for name,h in webproof['runtime_files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
    for name in ('Install-D.cmd','Launch-Portable-D.cmd'):shutil.copy2(ROOT/'desktop'/name,release/'windows'/name)
    artifacts=[]
    for kind,p in [('windows_installer',release/'windows/CampusPulse-RELAY-0.5.0-x64-setup.exe'),('windows_portable',release/'windows/CampusPulse-RELAY-0.5.0-x64-portable.exe'),('complete_local_illustrative_web_application',web),('source_archive',source),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf'])),('D_drive_launch_wrapper',release/'windows/Install-D.cmd'),('D_drive_launch_wrapper',release/'windows/Launch-Portable-D.cmd')]:
        artifacts.append(dict(kind=kind,path=str(p),relative_path=p.relative_to(release).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    for name in ('judge_sample_pack.zip','README.md','expected-results.json'):
        dst=release/'samples'/name;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copy2(ROOT/'public/samples'/name,dst)
        artifacts.append(dict(kind='public_sample_package',path=str(dst),relative_path=dst.relative_to(release).as_posix(),bytes=dst.stat().st_size,sha256=sha(dst)))
    manifest=dict(schema_version=7,product='CampusPulse RELAY',version='0.5.0',release_revision=REVISION,status='AUDIT_CANDIDATE_REAL_PUBLIC_GEMINI_VERIFIED_CALENDAR_NATIVE_GCP_GATES_PENDING',created_at=datetime.now(timezone.utc).isoformat(),
        project_root=str(ROOT),source_commit=commit,source_commit_semantics='Exact clean pushed archived source; manifest metadata may be published subsequently. Runtime commit is separate and runtime source matches.',
        repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,default_branch='main',source_commit=commit,published=True),
        urls=dict(public_web=acceptance['public_url'],samples=acceptance['samples']['url'],managed_agent_api=None),public_deployment=deployment,acceptance=acceptance,
        verification=dict(real_document_batch=live,provider_simulated_100=load,installed=desktop,web_bundle=webproof,presentation=visual),
        core_enhancements='F1-F5 locally implemented; real Calendar and full enhancement-level Gemini acceptance pending',
        windows=dict(version='0.5.0',unsigned=True,original_45_95_preserved=True,native_observed_build_evidence='docs/evidence/audit-native-observation-0.5.0.json',full_native_acceptance=False),
        funding=dict(personal_spending_authorized_usd=0,paid_upgrade=False,managed_resources_created=False,organizer_activation_project_coverage_pending=True),
        presentation=dict(slides=12,editable=True,pdf_all_pages_pixel_match=True,native_powerpoint_opened=False),limitations=acceptance['limitations'],artifacts=artifacts,preserved_releases=preserved)
    checks=''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts)
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');(release/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
    for target in (sealed,submission):
        target.mkdir(parents=True)
        for a in artifacts:
            dst=target/a['relative_path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(release/a['relative_path'],dst);assert sha(dst)==a['sha256']
        shutil.copy2(release/'manifest.json',target/'manifest.json');(target/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
        for name in ('final_judge_guide.md','remaining_actions_0.5.0.md','final_integration_ledger.md','audit_U1_U16.md','calendar_acceptance_0_5.md','organizer_window_runbook.md'):
            shutil.copy2(ROOT/'docs'/name,target/name)
        (target/'ENTRY.txt').write_text(f'Public HTTPS:{acceptance["public_url"]}\nAutomatic isolated temporary workspace; no invitation/registration/Google login/visitor key for real Gemini/MCP.\nRuntime:{deployed}\nArchived source:{commit}\nNON_GCP_READY=false: actual Calendar and remaining Windows acceptance pending. Managed GCP not yet deployed. No personal payment or contest submission.\n',encoding='utf-8')
        (target/'evidence-index.json').write_text(json.dumps(dict(acceptance=acceptance,deployment=deployment,real_documents=acceptance['documents']['evidence'],simulated_100='docs/evidence/audit-100-simulated.json',presentation=presentation),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(revision=REVISION,archived_source_commit=commit,deployed_commit=deployed,artifacts=len(artifacts),preserved_releases=len(preserved),preserved_hashes=sum(x['artifacts_hash_verified'] for x in preserved),submission=str(submission))))
if __name__=='__main__':main()
