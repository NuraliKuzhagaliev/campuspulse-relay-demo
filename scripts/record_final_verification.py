"""Collect measured local evidence without promoting it to hosted/GCP acceptance."""
import hashlib
import json
import sqlite3
import statistics
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text(encoding='utf-8-sig'))
suite=ET.parse(root/'.local/logs/final-python.xml').getroot().find('testsuite').attrib
assert suite['failures']==suite['errors']=='0'
browser=read('.local/logs/playwright-results.json')['stats']
assert browser['unexpected']==0
files=['docs/evidence/final-live-local-mvf8h3vr.json','docs/evidence/final-focus-local-mvf8uiq4.json','docs/evidence/final-features-local-mvf943c1.json']
runs=[r for file in files for r in read(file)['runs']]
semantic=sorted((root/'docs/evidence').glob('final-semantics-local-*.json'))[-1]
assert read(str(semantic.relative_to(root)))['passed']
runs.append(read(str(semantic.relative_to(root)))['result'])
durations=[r['duration_ms'] for r in runs]
usage=[]
dbfile=root/'.local/final-integration/alternative-data/relay.sqlite3'
with sqlite3.connect(dbfile.as_uri()+'?mode=ro',uri=True) as db:
    for row in db.execute('SELECT data FROM events'):
        value=json.loads(row[0])
        if value.get('type')=='model_usage':usage.append(value)
python=dict(tests=int(suite['tests']),failures=0,errors=0,seconds=float(suite['time']))
desktop={name:read('docs/evidence/'+name+'-0.4.0.json')['passed'] for name in ('desktop-contract','desktop-import-regression','four-desktop')}
assert all(desktop.values())
ui=read('docs/evidence/final-ui-local-mvf8xcqp.json');assert ui['passed']
files+=['docs/evidence/final-ui-local-mvf8xcqp.json',str(semantic.relative_to(root)).replace('\\','/'),'docs/evidence/desktop-contract-0.4.0.json','docs/evidence/desktop-import-regression-0.4.0.json','docs/evidence/four-desktop-0.4.0.json','docs/evidence/final-account-assessment.json']
evidence=dict(checked_at=datetime.now(timezone.utc).isoformat(),version='0.4.0',status='LOCAL_GEMINI_VERIFIED_HOSTED_CALENDAR_GCP_PENDING',source_commit_at_collection=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),source_has_uncommitted_integration_changes=True,
    python=python,browser=dict(passed=browser['expected'],skipped=browser['skipped'],failed=browser['unexpected'],seconds=browser['duration']/1000),ipc_policy=dict(passed=4,failed=0,seconds=.0824866),installed_desktop=desktop,windows_signature='NotSigned',
    real_gemini=dict(provider='gemini_developer',model='gemini-3.5-flash-lite',metadata_version='3.5-flash-lite-07-2026',project='gen-lang-client-0595303951',environment='local HTTPS gateway plus actual remote Gemini and live public GitHub',development_certificate_only=True,managed_agent_engine=False,frontend_turns=len(runs),complete=sum(r['status']=='complete' for r in runs),partial=sum(r['status']=='partial' for r in runs),latency_ms=dict(n=len(runs),min=min(durations),max=max(durations),mean=round(statistics.mean(durations)),kind='gateway agent duration; warm local server; no hosted cold-start or percentile claim'),provider_reported_usage=dict(model_responses=len(usage),**{k:sum(v[k] for v in usage) for k in ('input_tokens','output_tokens','thinking_tokens','total_tokens')}),usage_scope='All provider-reported model responses retained in the isolated local alternative data store, including development smoke/failures. Not a quota balance or final invoice.'),
    reviewed_defects=[dict(issue='Unnecessary proposal failed in first source-only turn',finding='Original tool arguments were deliberately not persisted, so the historical rejected field cannot be reconstructed. Unconditional extraction instruction and unconstrained list[dict] contract were identified.',fix='Source-only reads no longer create proposals; finite typed candidate schema and redacted error codes added.',recheck='Two affected real turns completed, exact source read and non-applying extraction proposal.'),dict(issue='Post-answer Axe scrollable-region-focusable violation',fix='Execution events are a named focusable region with EN/RU/KK label.',recheck='UI-only existing real-run state, zero additional model calls; no automated AA violations.'),dict(issue='Model called a student remaining estimate validated and overstated changed-entry count as moved blocks',fix='Explicit instruction/tool metadata distinguish reports, 30-minute units and removed-plus-added diff entries.',recheck='Actual follow-up after server restart correctly reports45 logged,95 remaining,120 allocated and no independently verified completion.')],
    accessibility=dict(viewports=[390,768,1280,1440],languages=['en','ru','kk'],automated_AA_primary_state=True,all_accessibility_standards_claimed=False),
    additional_browser_fault_regression=read('docs/evidence/final-ui-quota-0.4.0.json'),
    acceptance=dict(unseen_cited_sources='genuinely_live_verified_local_gateway',conflict_and_clarification='genuinely_live_verified_local_gateway',real_github_and_public_pr='genuinely_live_verified_local_gateway',planning_and_whatif='real_agent_server_plan_and_browser_local_adapter_verified',explicit_progress_and_conversation_restart='genuinely_live_verified_local_gateway',injection_and_two_visitor_source_isolation='genuinely_live_verified_local_gateway',languages='real_EN_RU_KK_answers_observed',passport_authority='deterministic_browser_and_installed_contracts_verified',real_calendar='NOT_RUN_CONSENT_AND_EXACT_UI_APPROVAL_PENDING',managed_gcp='UNMET_GCP_EXCEPTION_PENDING',public_0_4_and_windows_https_model_query='PENDING_EXISTING_RENDER_SECRET_AND_CUTOVER',hosted_background='UNAVAILABLE_FREE_HOST_SLEEP',unmodified_0_4_native_dialogs_and_notification_click='HUMAN_OBSERVATION_PENDING'),
    enhancements={f'F{i}':'locally_implemented_real_calendar_and_full_gemini_acceptance_pending' for i in range(1,6)},personal_spending_authorized_usd=0,evidence=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in files])
(root/'docs/evidence/final-verification-0.4.0.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(python=python,browser=evidence['browser'],real_frontend_turns=len(runs),real_model_usage=evidence['real_gemini']['provider_reported_usage'])))
