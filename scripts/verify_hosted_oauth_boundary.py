"""Actual hosted OAuth configuration/browser binding; zero Google requests/consent."""
import json,os
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import httpx
BASE='https://campuspulse-relay-demo.onrender.com'
def main():
    with httpx.Client(base_url=BASE,timeout=40,follow_redirects=False) as owner:
        health=owner.get('/api/health').raise_for_status().json()
        if os.getenv('RELAY_EXPECTED_DEPLOY_COMMIT'):assert health['deployed_commit']==os.environ['RELAY_EXPECTED_DEPLOY_COMMIT']
        owner.get('/api/session').raise_for_status()
        status=owner.get('/api/connections/status').raise_for_status().json();assert status['configured'] and not status['connected']
        start=owner.get('/api/auth/start').raise_for_status().json();assert start['url']==BASE+'/connect'
        redirect=owner.get('/connect');assert redirect.status_code==307
        target=urlparse(redirect.headers['location']);query=parse_qs(target.query)
        assert target.hostname=='accounts.google.com' and query['redirect_uri']==[BASE+'/auth/callback']
        assert set(query['scope'][0].split())=={'openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/calendar.app.created'}
        assert query['code_challenge_method']==['S256']
        binding=owner.cookies.get('relay_oauth_state');state=query['state'][0];assert binding and binding!=state
        cookie=redirect.headers['set-cookie'];assert all(s in cookie for s in ['HttpOnly','Secure','SameSite=lax','Max-Age=900'])
        with httpx.Client(base_url=BASE,timeout=30,follow_redirects=False) as foreign:
            foreign.cookies.set('relay_oauth_state',state)
            result=foreign.get('/auth/callback',params={'state':state,'code':'SIMULATED_INVALID_CODE'},headers={'Accept':'application/json'})
            assert result.status_code==403 and result.json()['error']['code']=='ACCESS_DENIED'
        proof=dict(checked_at=datetime.now(timezone.utc).isoformat(),deployed_commit=health['deployed_commit'],passed=True,
            configuration_including_encryption_key_valid=True,exact_https_callback=True,minimum_scopes=True,pkce_s256=True,
            private_browser_binding_independent_from_url_state=True,copied_url_cannot_reconstruct_cookie=True,web_cookie_ttl_seconds=900,
            google_api_calls=0,real_consent=False,real_calendar_writes=0,limitation='Hosted boundary only. Actual owner consent/token exchange and event acceptance remain pending.')
    Path('docs/evidence/audit-hosted-oauth-boundary.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
if __name__=='__main__':main()
