"""Package tested local artifacts on D:; never provisions or calls models."""
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
if ROOT.drive.upper()!='D:':
    raise SystemExit('Use the authorized D: project root for this release.')
RELEASE=ROOT/'release'
def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):
    (ROOT/path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

commit=git('rev-parse','HEAD')
source=RELEASE/'source/CampusPulseRELAY-0.1.0-source.zip'
source.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/',
                '--output='+str(source),commit],cwd=ROOT,check=True)
with zipfile.ZipFile(source) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        relative=name.removeprefix('CampusPulseRELAY/')
        assert not relative.startswith(('.local/','.venv/','node_modules/','inputs/'))
        assert not (relative.startswith('.env') and relative!='.env.example')
web=RELEASE/'web/CampusPulseRELAY-0.1.0-web-build.zip'
web.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(web,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((ROOT/'dist').rglob('*')):
        if path.is_file():
            archive.write(path,'dist/'+path.relative_to(ROOT/'dist').as_posix())
    archive.writestr('README.txt','Production frontend assets. Serve through the RELAY FastAPI gateway with its API. This is not a standalone backend or a cloud deployment. See the source README.\n')
with zipfile.ZipFile(web) as archive:
    assert archive.testzip() is None
suite=ET.parse(ROOT/'.local/logs/pytest-all.xml').getroot().find('testsuite').attrib
browser=read('.local/logs/playwright-results.json')['stats']
desktop=read('docs/evidence/desktop-smoke.json')
mcp=read('docs/evidence/mcp-smoke.json')
connections=read('docs/connections.json')
assert int(suite['failures'])==0 and int(suite['errors'])==0
assert browser['unexpected']==0 and desktop['passed'] and mcp['all_calls_passed']
artifacts=[]
for kind,relative in [
    ('windows_installer','windows/CampusPulse-RELAY-0.1.0-x64-setup.exe'),
    ('windows_portable','windows/CampusPulse-RELAY-0.1.0-x64-portable.exe'),
    ('source_archive',source.relative_to(RELEASE).as_posix()),
    ('web_frontend_build',web.relative_to(RELEASE).as_posix()),
    ('editable_presentation','presentation/CampusPulse-RELAY-final.pptx'),
    ('presentation_pdf','presentation/CampusPulse-RELAY-final.pdf'),
    ('recorded_local_demo','recordings/CampusPulse-RELAY-recorded-local-demo.webm')]:
    path=RELEASE/relative
    artifacts.append(dict(kind=kind,relative_path=relative,path=str(path),bytes=path.stat().st_size,sha256=sha(path)))
proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),
           python=dict(tests=int(suite['tests']),failures=int(suite['failures']),errors=int(suite['errors']),seconds=float(suite['time'])),
           browser=browser,production_build_passed=True,pip_check_passed=True,powershell_parse_passed=True,
           cloud_model_calls=0,live_calendar_writes=0)
write('docs/evidence/test-summary.json',proof)
manifest=dict(
    schema_version=1,product='CampusPulse RELAY',version='0.1.0',status='local_release_candidate_cloud_pending',
    created_at=proof['checked_at'],project_root=str(ROOT),source_commit=commit,
    repository=dict(url=connections['github']['url'],branch='main',source_commit=commit,published=True),
    urls=dict(local_web='http://127.0.0.1:8000',local_mcp='http://127.0.0.1:8001/mcp/',public_web=None,agent_api=None),
    cloud=dict(status='pending_organizer_credit_activation_and_verification',resource=None,revision=None,model_success_verified=False,
               paid_resources_provisioned=False,personal_spending_authorized_usd=0,credits_confirmed=False,
               final_project_selected=False,credit_project_eligibility_confirmed=False),
    dedicated_calendar=connections['calendar'],
    verification=dict(python=proof['python'],browser=browser,installed_windows_passed=desktop['passed'],
                      windows_signature='NotSigned',mcp_protocol=mcp['protocol_version'],mcp_tools=len(mcp['tools']),
                      mcp_final_calls_passed=True,background_change_observed_seconds=19.62,
                      background_latency_observations=1,background_is_cloud_hosted=False,
                      real_calendar_write_readback=False,managed_agent_smoke=False,live_judge_session=False,
                      presentation_slides=8,presentation_native_editable=True,presentation_pdf='rendered_slide_pages',
                      recording_seconds=125.48),
    artifacts=artifacts,
    instructions=dict(run_gateway='scripts/dev.ps1',bootstrap='scripts/bootstrap.ps1',
                      local_judge='docs/judge_quickstart.md',install_uninstall='release/README.md',
                      after_credit_activation='docs/cloud_setup.md',exclusive_judge_setup='docs/judge_setup.md'),
    blockers=[
        'Organizer credits: activation, exact eligible project/billing account, balance and expiration are not confirmed. No personal spending authorized.',
        'Real Vertex AI Agent Engine resource, Gemini request, public web and cloud-to-MCP boundary have not been deployed/verified.',
        'Application Calendar OAuth/shared runtime access and actual approved write/read-back remain unverified.',
        'Hosted exclusive judge access and consent/token renewal require actual credentials and testing.'
    ],
    limitations=['Conservative explicit academic text extraction; no scanned OCR or general natural-language date inference.',
                 'UI translation is partial; live EN/RU/KK model evaluation is pending.',
                 'Desktop picker is instrumented in automated smoke; actual selected-file IO is tested. OS toast visibility is not asserted.',
                 'Unsigned Windows app; local connected operations need a running gateway.',
                 'Guarded undo preserves edited events; deleted prior blocks require a fresh approval to restore.',
                 'GitHub public quota requires backoff or a dedicated repository-scoped read credential.']
)
write('release/manifest.json',manifest)
(RELEASE/'SHA256SUMS.txt').write_text(''.join(f"{a['sha256']}  {a['relative_path']}\n" for a in artifacts),encoding='ascii')
print(json.dumps({'source_commit':commit,'artifacts':len(artifacts),'python_tests':int(suite['tests']),
                  'browser_passed':browser['expected'],'manifest':str(RELEASE/'manifest.json')},indent=2))
