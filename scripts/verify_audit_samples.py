"""Verify the actual public sample index, 13 files and ZIP, without model calls."""
import hashlib,json,zipfile,io,sys
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relay.domain import now
ROOT=Path(__file__).resolve().parents[1];BASE='https://campuspulse-relay-demo.onrender.com'
def main():
    proof=dict(checked_at=now(),url=BASE+'/samples/',provider_calls=0,google_writes=0,files=[])
    with httpx.Client(timeout=40,follow_redirects=False) as client:
        health=client.get(BASE+'/api/health');health.raise_for_status();proof['deployed_commit']=health.json()['deployed_commit']
        index=client.get(BASE+'/samples/');index.raise_for_status();assert 'judge_sample_pack.zip' in index.text
        metadata=client.get(BASE+'/samples/expected-results.json');metadata.raise_for_status();assert metadata.json()==json.loads((ROOT/'public/samples/expected-results.json').read_text(encoding='utf-8'))
        expected=metadata.json();assert len(expected['files'])==13
        package=client.get(BASE+'/samples/judge_sample_pack.zip');package.raise_for_status();assert package.content==(ROOT/'public/samples/judge_sample_pack.zip').read_bytes()
        with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():assert not name.startswith(('/','\\')) and '..' not in Path(name).parts
            for item in expected['files']:
                response=client.get(BASE+'/samples/'+item['file']);response.raise_for_status();actual=hashlib.sha256(response.content).hexdigest()
                assert actual==item['sha256'] and len(response.content)==item['bytes']
                assert hashlib.sha256(archive.read(item['file'])).hexdigest()==actual
                proof['files'].append(dict(file=item['file'],bytes=len(response.content),sha256=actual,content_type=response.headers.get('content-type'),zip_hash_matches=True))
        guide=client.get(BASE+'/samples/README.md');guide.raise_for_status();assert all(s in guide.text for s in ['English','Русский','Қазақша'])
        privacy=client.get(BASE+'/samples/privacy.html');privacy.raise_for_status()
        proof.update(sample_zip_sha256=hashlib.sha256(package.content).hexdigest(),sample_zip_bytes=len(package.content),trilingual_guide=True,privacy_page=True,passed=True)
    (ROOT/'docs/evidence/audit-public-samples.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,files=len(proof['files']),deployed_commit=proof['deployed_commit'])))
if __name__=='__main__':main()
