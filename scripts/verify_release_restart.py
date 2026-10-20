"""Actual local subprocess restarts, not a disruptive restart of public Render."""
import base64,json,os,secrets,subprocess,time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'.local/final-0.5.1/restart'
FOLDER.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,RELAY_MODE='public_demo',RELAY_PUBLIC_AI_ENABLED='false')
for key in ('RELAY_AGENT_RESOURCE','GOOGLE_CLOUD_PROJECT','RELAY_OAUTH_CLIENT_ID','RELAY_OAUTH_CLIENT_SECRET','RELAY_TOKEN_ENCRYPTION_KEY','RELAY_MCP_URL','RELAY_GEMINI_API_KEY','RELAY_INFERENCE_PROVIDER','RELAY_DEPLOYMENT_MODE','GOOGLE_APPLICATION_CREDENTIALS','RELAY_GITHUB_TOKEN'):
    env.pop(key,None)
proof=dict(scope='actual local gateway subprocess restart and empty-store replacement; public Render not restarted',actual_gemini_calls=0,google_calls=0,checks={})
client=httpx.Client(base_url='http://127.0.0.1:8034',timeout=15)
log=(FOLDER/'server.log').open('ab')
process=None

def start(name):
    global process
    env['RELAY_DATA_DIR']=str(FOLDER/name)
    process=subprocess.Popen([str(ROOT/'.local/public-venv/Scripts/python.exe'),'-m','uvicorn','relay.gateway:app','--host','127.0.0.1','--port','8034','--no-access-log'],cwd=ROOT,env=env,stdout=log,stderr=log)
    for _ in range(100):
        if process.poll() is not None:raise RuntimeError('Local test server exited; inspect private log')
        try:
            if client.get('/api/health').status_code==200:return
        except httpx.HTTPError:pass
        time.sleep(.1)
    raise RuntimeError('Local test server did not become ready')

def stop():
    global process
    if process is not None:
        process.terminate();process.wait(timeout=15);process=None

def accept_session(response):
    response.raise_for_status()
    # httpx does not send Secure cookies on HTTP loopback. This explicit header
    # carries ONLY our own test capability to the same local test server.
    token=response.cookies.get('relay_session')
    if token:client.headers['Cookie']='relay_session='+token
    client.headers['X-Relay-CSRF']=response.json()['csrf']
    return response.json()

def post(path,body=None):
    r=client.post('/api'+path,json=body or {});r.raise_for_status();return r.json()

try:
    start('persisted')
    first=accept_session(client.get('/api/session'))
    content=b'Assignment: Restart prism note\nCourse: Synthetic optics\nTerm: Autumn 2026\nAssignment ID: restart-051\nDue: 2026-10-23T18:00:00+05:00\nEffort: 75 minutes\n'
    post('/import-native',dict(name='restart-prism.md',content=base64.b64encode(content).decode()))
    original=client.get('/api/state').json();assert len(original['sources'])==1
    passport=post('/passport/export')['file'];(FOLDER/'restart.relay.json').write_text(json.dumps(passport),encoding='utf-8')
    stop();start('persisted')
    after=client.get('/api/state');after.raise_for_status();after=after.json()
    assert after['workspace_id']==original['workspace_id'] and after['sources'][0]['id']==original['sources'][0]['id']
    proof['checks']['actual_process_restart_with_retained_sqlite_preserves_owned_workspace']=True
    stop();start('empty-store')
    assert client.get('/api/state').status_code==401
    fresh=accept_session(client.get('/api/session'));assert fresh['tenant']!=first['tenant']
    assert client.get('/api/state').json()['sources']==[]
    staged=post('/passport/preview',dict(name='restart.relay.json',content=base64.b64encode(json.dumps(passport).encode()).decode()))
    restored=client.post('/api/passport/'+staged['id']+'/restore',json={});accept_session(restored)
    state=client.get('/api/state').json();assert len(state['sources'])==1 and state['tasks'][0]['minutes']==75
    assert state['receipts']==[] and not state['settings']['calendar_live']
    proof['checks']['actual_empty_datastore_replacement_rejects_old_capability']=True
    proof['checks']['passport_restores_selected_coursework_without_google_or_approval_authority']=True
    proof['passed']=True
finally:
    stop();client.close();log.close()
    (ROOT/'docs/evidence/final-0.5.1-restart.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
