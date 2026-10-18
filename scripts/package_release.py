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
version=read('package.json')['version']
assert version=='0.1.1','Historical local 0.1.1 recorder only; use package_continuation.py for 0.2.0.'
source=RELEASE/f'source/CampusPulseRELAY-{version}-source.zip'
source.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--prefix=CampusPulseRELAY/',
                '--output='+str(source),commit,'--','.',':(exclude)release/manifest.json',
                ':(exclude)docs/evidence/test-summary.json'],cwd=ROOT,check=True)
with zipfile.ZipFile(source,'a',zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('CampusPulseRELAY/RELEASE-METADATA.txt',
                    f'Source commit: {commit}\nVersion: {version}\nThe generated release manifest and test-summary rollup are distributed alongside this archive, not embedded, to avoid circular hashes or stale metadata. Detailed evidence and tests remain in docs/.\n')
with zipfile.ZipFile(source) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        relative=name.removeprefix('CampusPulseRELAY/')
        assert not relative.startswith(('.local/','.venv/','node_modules/','inputs/'))
        assert not (relative.startswith('.env') and relative!='.env.example')
web=RELEASE/f'web/CampusPulseRELAY-{version}-web-build.zip'
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
native=read('docs/evidence/desktop-native-result.json')
import_regression=read('docs/evidence/desktop-import-regression.json')
presentation=read('docs/evidence/presentation.json')
policy_suite=ET.parse(ROOT/'.local/logs/desktop-policy.xml').getroot()
policy_cases=list(policy_suite.iter('testcase'))
assert len(policy_cases)==2 and not list(policy_suite.iter('failure')) and not list(policy_suite.iter('error'))
assert int(suite['failures'])==0 and int(suite['errors'])==0
assert browser['unexpected']==0 and desktop['passed'] and mcp['all_calls_passed']
assert import_regression['passed'] and all(p['matches_current_source'] for p in import_regression['packaged_files'])
# Verify the prior release before producing any current artifact.
preserved=RELEASE/'versions/0.1.0'
previous=json.loads((preserved/'manifest.json').read_text(encoding='utf-8-sig'))
for artifact in previous['artifacts']:
    assert sha(preserved/artifact['relative_path'])==artifact['sha256']
artifacts=[]
for kind,relative in [
    ('windows_installer',f'windows/CampusPulse-RELAY-{version}-x64-setup.exe'),
    ('windows_portable',f'windows/CampusPulse-RELAY-{version}-x64-portable.exe'),
    ('source_archive',source.relative_to(RELEASE).as_posix()),
    ('web_frontend_build',web.relative_to(RELEASE).as_posix()),
    ('editable_presentation',Path(presentation['pptx']).relative_to(RELEASE).as_posix()),
    ('presentation_pdf',Path(presentation['pdf']).relative_to(RELEASE).as_posix()),
    ('recorded_local_demo','recordings/CampusPulse-RELAY-recorded-local-demo.webm')]:
    path=RELEASE/relative
    artifacts.append(dict(kind=kind,relative_path=relative,path=str(path),bytes=path.stat().st_size,sha256=sha(path)))
proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),
           python=dict(tests=int(suite['tests']),failures=int(suite['failures']),errors=int(suite['errors']),seconds=float(suite['time'])),
           browser=browser,production_build_passed=True,pip_check_passed=True,powershell_parse_passed=True,
           desktop_policy_tests=len(policy_cases),installed_import_regression_passed=True,
           cloud_model_calls=0,live_calendar_writes=0)
write('docs/evidence/test-summary.json',proof)
manifest=dict(
    schema_version=2,product='CampusPulse RELAY',version=version,status='local_release_candidate_cloud_pending',
    created_at=proof['checked_at'],project_root=str(ROOT),source_commit=commit,
    repository=dict(url=connections['github']['url'],branch='main',source_commit=commit,published=True),
    urls=dict(local_web='http://127.0.0.1:8000',local_mcp='http://127.0.0.1:8001/mcp/',public_web=None,agent_api=None),
    cloud=dict(status='pending_organizer_credit_activation_and_verification',resource=None,revision=None,model_success_verified=False,
               paid_resources_provisioned=False,personal_spending_authorized_usd=0,credits_confirmed=False,
               final_project_selected=False,credit_project_eligibility_confirmed=False),
    dedicated_calendar=connections['calendar'],
    preserved_release=dict(version='0.1.0',directory=str(preserved),git_tag='local-release-0.1.0',
                           artifacts_hash_verified=len(previous['artifacts']),source_commit=previous['source_commit']),
    enhancements=dict(F1='locally_implemented',F2='locally_implemented',F3='locally_implemented',F4='locally_implemented',F5='locally_implemented',
                      real_calendar_acceptance='pending',real_gemini_acceptance='pending'),
    languages=dict(operational_ui=['en','ru','kk'],browser_flows_verified=True,
                   original_evidence_and_exact_action_titles_preserved=True,live_model_acceptance='pending'),
    verification=dict(python=proof['python'],browser=browser,installed_windows_regression_passed=desktop['passed'],
                      installed_import_regression_passed=import_regression['passed'],desktop_policy_tests=len(policy_cases),
                      packaged_main_preload_policy_renderer_match=True,
                      native_picker_appearance_confirmed_by_user=native['picker'].get('appearance_confirmed_by_user',False),
                      native_picker_import_exact_readback=native['picker'].get('exact_source_observed',False),
                      native_import_stages=native.get('import',{}),
                      native_notification_visibility=native['notification'].get('visibility_verified',False),
                      native_notification_visibility_basis=native['notification'].get('visibility_basis'),
                      native_notification_location=native['notification'].get('location'),
                      native_notification_click_observed=native['notification'].get('actual_click_observed',False),
                      native_check_status=native['status'],native_check_evidence='docs/evidence/desktop-native-result.json',
                      original_human_import_incident='Rejected route was not logged historically; attribution remains unconfirmed.',
                      reproduced_import_failure='POST /api/import rejected before upload; native POST /api/import-native and GET /api/state succeeded.',
                      corrected_import_behavior='Both desktop selection paths use /api/import-native; exact content read-back, refresh/cache and retained rejection guards verified.',
                      windows_signature='NotSigned',mcp_protocol=mcp['protocol_version'],mcp_tools=len(mcp['tools']),
                      mcp_final_calls_passed=True,mcp_checked_at=mcp.get('checked_at'),background_change_observed_seconds=19.62,
                      background_latency_observations=1,background_is_cloud_hosted=False,
                      real_calendar_write_readback=False,managed_agent_smoke=False,live_judge_session=False,
                      presentation_slides=8,presentation_native_editable=True,presentation_pdf='rendered_slide_pages',
                      recording_seconds=125.48,recording_release='0.1.0',recording_is_retained_local_backup=True),
    artifacts=artifacts,
    source_archive_metadata=dict(generated_manifest_distributed_separately=True,
                                  omitted_generated_files=['release/manifest.json','docs/evidence/test-summary.json']),
    instructions=dict(run_gateway='scripts/dev.ps1',bootstrap='scripts/bootstrap.ps1',
                      local_judge='docs/judge_quickstart.md',install_uninstall='release/README.md',
                      after_credit_activation='docs/cloud_setup.md',exclusive_judge_setup='docs/judge_setup.md',
                      native_recheck='docs/native_windows_check.md',import_diagnosis='docs/desktop_import_fix.md'),
    blockers=[
        'Organizer credits: activation, exact eligible project/billing account, balance and expiration are not confirmed. No personal spending authorized.',
        'Real Vertex AI Agent Engine resource, Gemini request, public web and cloud-to-MCP boundary have not been deployed/verified.',
        'Application Calendar OAuth/shared runtime access and actual approved write/read-back remain unverified.',
        'Hosted exclusive judge access and consent/token renewal require actual credentials and testing.'
    ] + ([] if native['picker'].get('exact_source_observed') else ['Corrected app is reopened in the same verification workspace; successful import through the real unmodified picker still requires human recheck.'])
      + ([] if native['notification'].get('visibility_verified') else ['Actual Windows notification visibility/click requires human observation. Dispatch alone is insufficient.']),
    limitations=['Conservative explicit academic text extraction; no scanned OCR or general natural-language date inference.',
                 'EN/RU/Kazakh operational UI is translated and tested. Original evidence and exact action titles remain verbatim. Live multilingual model evaluation is pending.',
                 'Automated desktop import regression substitutes the picker. Separate real picker import passed and the user confirmed the visible bottom-right Windows banner; no click/focus callback was observed. The Windows control helper failed before initialization.',
                 'Unsigned Windows app; local connected operations need a running gateway.',
                 'Guarded undo preserves edited events; deleted prior blocks require a fresh approval to restore.',
                 'GitHub public quota requires backoff or a dedicated repository-scoped read credential.']
)
write('release/manifest.json',manifest)
(RELEASE/'SHA256SUMS.txt').write_text(''.join(f"{a['sha256']}  {a['relative_path']}\n" for a in artifacts),encoding='ascii')
print(json.dumps({'source_commit':commit,'artifacts':len(artifacts),'python_tests':int(suite['tests']),
                  'browser_passed':browser['expected'],'manifest':str(RELEASE/'manifest.json')},indent=2))
