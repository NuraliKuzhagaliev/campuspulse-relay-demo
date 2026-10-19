"""Create a complete illustrative web application ZIP, then stage it for minimal-runtime verification."""
import json
import zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text())['version']
output=root/f'.local/final-integration/CampusPulseRELAY-{version}-web-app.zip'
stage=root/'.local/final-integration/web-bundle'
assert not stage.exists(),'Preserve an existing verification extraction; choose a new path.'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for folder in ('dist','relay','fixtures'):
        for p in sorted((root/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':z.write(p,p.relative_to(root).as_posix())
    for name in ('requirements.public.txt','requirements.public.lock.txt','scripts/run-web-bundle.ps1','LICENSE','docs/workspace_passport.md','docs/final_judge_guide.md'):
        z.write(root/name,name)
    z.writestr('README.txt','CampusPulse RELAY '+version+' complete React + Python illustrative web application.\nExtract on D:, run scripts/run-web-bundle.ps1 using Python3.13. All environment/cache/data paths stay on D:. No Google account or key needed for illustrative file import, planning or local-adapter Calendar receipts.\nReal Gemini requires the separately configured full server source/dependency/deployment route. Managed GCP and real Calendar acceptance remain pending.\n')
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    z.extractall(stage)
print(json.dumps(dict(zip=str(output),stage=str(stage))))
