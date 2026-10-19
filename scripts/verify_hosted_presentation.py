"""Verify every delivered PDF page and unchanged/changed reviewed slide pixels."""
import json
from pathlib import Path
from PIL import Image,ImageChops
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
meta=json.loads((root/'docs/evidence/presentation-0.4.0.json').read_text())
folder=Path(meta['renders']);assert folder.name=='hosted-r1'
old=root/'.local/presentation-final/integration-r2'
changed={1,6,7,9,11};pages=[];unchanged=[]
pdf=PdfReader(meta['pdf']);assert len(pdf.pages)==12
for n,page in enumerate(pdf.pages,1):
    rendered=Image.open(folder/f'slide-{n:02}.png').convert('RGB')
    embedded=page.images[0].image.convert('RGB')
    assert embedded.size==rendered.size and ImageChops.difference(rendered,embedded).getbbox() is None
    pages.append(dict(page=n,pixel_match=True))
    if n not in changed:
        prior=Image.open(old/f'slide-{n:02}.png').convert('RGB')
        assert ImageChops.difference(prior,rendered).getbbox() is None,n
        unchanged.append(n)
proof=dict(pdf_pages=12,pdf_matches_inspected_slide_renders=pages,changed_slides_individually_reviewed=sorted(changed),unchanged_pixel_identical_to_previously_individually_reviewed_slides=unchanged,all_12_slides_verified=True,native_powerpoint_opened=False)
(root/'docs/evidence/presentation-0.4.0-hosted-visual.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(verified_pages=12,visually_reviewed_changed=sorted(changed),unchanged_pixel_identical=unchanged)))
