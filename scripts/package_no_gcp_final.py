"""Seal an honest primary-route candidate, preserving every prior release."""
import hashlib,json,re,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REVISION='0.5.1-final-r1'

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def sha(path):
    with path.open('rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()

def main():
    assert ROOT.drive.lower()=='d:'
    release=ROOT/'release';sealed=release/'versions'/REVISION;submission=ROOT/'submission'/REVISION
    assert not sealed.exists() and not submission.exists(),'Preserve sealed releases.'
    assert not git('status','--porcelain'),'Commit and publish reviewed source/evidence first.'
    source_commit=git('rev-parse','HEAD');branch=git('branch','--show-current')
    for ref in ('main',branch):assert git('ls-remote','origin','refs/heads/'+ref).split()[0]==source_commit
    acceptance=read('docs/evidence/final-0.5.1-acceptance.json');runtime=acceptance['deployed_commit']
    # Additional synthetic acceptance fixtures are documentation inputs, never
    # consumed by the app as runtime goldens. All executable runtime is equal.
    assert not git('diff',runtime,source_commit,'--','relay','src','desktop/main.cjs','desktop/preload.cjs','desktop/request-policy.cjs','desktop/locales.cjs','infra','public','package-lock.json','requirements.cloud.txt','requirements.public.txt','requirements.public.lock.txt','vite.config.ts','tsconfig.json','index.html')
    previous_package=json.loads(git('show',runtime+':package.json'))
    current_package=read('package.json')
    for key in ('version','main','dependencies','devDependencies','scripts'):
        assert previous_package[key]==current_package[key],key
    assert read('docs/evidence/final-0.5.1-windows-D-install-fix.json')['passed']
    assert read('docs/evidence/public-deployment-0.5.1.json')['verified']
    for name in ['final-0.5.1-hosted-ui.json','final-0.5.1-mcp.json','final-0.5.1-100-simulated-r3.json','final-0.5.1-recovery.json','final-0.5.1-restart.json','final-0.5.1-public-samples.json','final-0.5.1-hosted-github.json','final-0.5.1-windows-package.json']:
        assert read('docs/evidence/'+name)['passed'],name
    live=read(acceptance['documents']['evidence']);assert live['passed'] and len(live['cases'])==5 and len(live['runs'])==6
    assert acceptance['managed_gcp']['enabled'] is False and acceptance['funding']['personal_spending_authorized_usd']==0
    presentation=read('docs/evidence/presentation-0.5.1.json');assert read('docs/evidence/presentation-0.5.1-visual.json')['all_12_slides_verified']
    assert read('docs/evidence/final-web-bundle-0.5.1.json')['passed']
    preserved=[]
    for folder in sorted((release/'versions').iterdir()):
        if not (folder/'manifest.json').exists():continue
        previous=json.loads((folder/'manifest.json').read_text(encoding='utf-8-sig'))
        for item in previous['artifacts']:assert sha(folder/item['relative_path'])==item['sha256'],str(folder/item['relative_path'])
        preserved.append(dict(revision=folder.name,verified_artifacts=len(previous['artifacts'])))
    source=release/f'source/CampusPulseRELAY-{REVISION}-source.zip';assert not source.exists()
    subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/','--output='+str(source),source_commit,'--','.',':(exclude)release/manifest.json'],cwd=ROOT,check=True)
    with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',f'Primary-route candidate {REVISION}\nArchived clean pushed source:{source_commit}\nActual public runtime:{runtime}\nWeb and Electron executable runtime files match the public commit; later changes include a corrected D-only NSIS installer, owner helpers, verification, documentation, packaging and supplemental synthetic inputs.\nNON_GCP_READY={acceptance["NON_GCP_READY"]}. Real Calendar and native remaining gates are explicit. Original managed-GCP criterion unmet, optional integration disabled. No personal charges.\n')
    web=release/f'web/CampusPulseRELAY-{REVISION}-web-app.zip';assert not web.exists()
    shutil.copy2(ROOT/'.local/final-integration/CampusPulseRELAY-0.5.1-web-app.zip',web)
    for package in (source,web):
        with zipfile.ZipFile(package) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                clean=name.removeprefix('CampusPulseRELAY/')
                assert not clean.startswith(('.local/','.venv/','node_modules/','inputs/','installed/','submission/'))
                assert not(clean.startswith('.env') and clean!='.env.example')
                assert not re.search(rb'(?:AIza[0-9A-Za-z_-]{25,}|github_pat_[0-9A-Za-z_]{40,}|ghp_[0-9A-Za-z]{30,}|GOCSPX-[0-9A-Za-z_-]{20,})',archive.read(name)),'Potential secret; contents withheld'
    evidence=release/f'evidence/CampusPulseRELAY-{REVISION}-evidence.zip';evidence.parent.mkdir(parents=True,exist_ok=True);assert not evidence.exists()
    with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as archive:
        for pattern in ('docs/evidence/final-0.5.1-*.json','docs/evidence/public-deployment-0.5.1.json','docs/evidence/presentation-0.5.1*.json'):
            for path in sorted(ROOT.glob(pattern)):archive.write(path,path.relative_to(ROOT).as_posix())
        archive.write(ROOT/acceptance['documents']['evidence'],acceptance['documents']['evidence'])
        for name in ['README.md','REQUIREMENTS.md','BLOCKERS.md','docs/final_integration_ledger.md','docs/final_judge_guide.md','docs/remaining_actions_0.5.1.md','docs/independent_tester_calendar_ru.txt','docs/independent_website_test_ru.txt','scripts/calendar-owner-replay.js']:
            archive.write(ROOT/name,name)
    artifacts=[]
    def add(kind,path):
        assert path.resolve().is_relative_to(release.resolve())
        artifacts.append(dict(kind=kind,path=str(path),relative_path=path.relative_to(release).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    for kind,path in [('windows_installer',release/'windows/CampusPulse-RELAY-0.5.1-x64-setup.exe'),('windows_portable',release/'windows/CampusPulse-RELAY-0.5.1-x64-portable.exe'),('complete_local_illustrative_web',web),('source_archive',source),('editable_presentation',Path(presentation['pptx'])),('presentation_pdf',Path(presentation['pdf'])),('acceptance_evidence',evidence),('synthetic_uncertainty_addendum',release/'samples/CampusPulseRELAY-0.5.1-uncertainty-addendum.zip')]:add(kind,path)
    for name in ('Install-D.cmd','Launch-Portable-D.cmd'):
        shutil.copy2(ROOT/'desktop'/name,release/'windows'/name);add('D_drive_wrapper',release/'windows'/name)
    samples=release/'samples'/'0.5.1';samples.mkdir(parents=True,exist_ok=True)
    for name in ('judge_sample_pack.zip','README.md','expected-results.json'):
        target=samples/name;assert not target.exists();shutil.copy2(ROOT/'public/samples'/name,target);add('public_13_file_sample_package',target)
    manifest=dict(schema_version=8,product='CampusPulse RELAY',version='0.5.1',release_revision=REVISION,status='PUBLIC_PRIMARY_ROUTE_VERIFIED_OWNER_CALENDAR_NATIVE_GATES_PENDING',created_at=datetime.now(timezone.utc).isoformat(),source_commit=source_commit,deployed_commit=runtime,source_commit_semantics='Exact clean pushed archived source; manifest may be committed later. Web/Electron runtime unchanged since deployed commit; Windows NSIS installer and owner launch helpers corrected separately.',project_root=str(ROOT),repository=dict(url='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',branch=branch,default_branch='main',published=True),urls=dict(public_web=acceptance['public_url'],samples=acceptance['samples']['url'],managed_agent_api=None),public_deployment=read('docs/evidence/public-deployment-0.5.1.json'),acceptance=acceptance,core_enhancements='F1-F5 locally implemented; real Calendar and full enhancement-level Gemini acceptance remain separate',windows=acceptance['windows'],managed_gcp=acceptance['managed_gcp'],funding=acceptance['funding'],limitations=acceptance['limitations'],artifacts=artifacts,preserved_releases=preserved)
    checks=''.join(a['sha256']+'  '+a['relative_path']+'\n' for a in artifacts)
    for target in (release,sealed,submission):
        target.mkdir(parents=True,exist_ok=True)
        if target!=release:
            for item in artifacts:
                path=target/item['relative_path'];path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item['path'],path)
        (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');(target/'SHA256SUMS.txt').write_text(checks,encoding='ascii')
        for item in artifacts:assert sha(target/item['relative_path'])==item['sha256']
    print(json.dumps(dict(revision=REVISION,source_commit=source_commit,runtime=runtime,artifacts=len(artifacts),all_artifact_copies_verified=3*len(artifacts),preserved_releases=len(preserved),preserved_artifacts=sum(v['verified_artifacts'] for v in preserved),NON_GCP_READY=acceptance['NON_GCP_READY'])))

if __name__=='__main__':main()
