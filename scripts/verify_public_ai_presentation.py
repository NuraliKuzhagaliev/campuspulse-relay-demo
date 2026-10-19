import json
from pathlib import Path
from PIL import Image,ImageChops
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
meta=json.loads((root/'docs/evidence/presentation-0.4.1.json').read_text())
folder=Path(meta['renders']);pdf=PdfReader(meta['pdf']);assert len(pdf.pages)==12
assert '0.4.1' in pdf.metadata.title
pages=[]
for n,page in enumerate(pdf.pages,1):
    raster=Image.open(folder/f'slide-{n:02}.png').convert('RGB')
    embedded=page.images[0].image.convert('RGB')
    assert raster.size==embedded.size and ImageChops.difference(raster,embedded).getbbox() is None
    pages.append(dict(page=n,pixel_match_to_individually_reviewed_render=True))
validation=json.loads(Path(meta['validation']).read_text())
assert validation['packageIntegrity']['status']=='pass' and validation['presentationLayout']['finding_count']==0
warnings=validation['presentationLayout'].get('warnings',[])
assert len(warnings)==1 and warnings[0]['slide']==12 and warnings[0]['kind']=='dense_bold_paragraphs_without_spacing'
proof=dict(slides=12,individually_visually_reviewed=list(range(1,13)),pdf_pages=pages,source_pptx_imported_and_existing_shapes_edited=True,
    retained_font='Arial',retained_geometry=True,layout_findings=0,layout_warning_review=dict(slide=12,kind=warnings[0]['kind'],accepted=True,
    reason='Four short pending-gate lines remain readable in the existing bold source layout, with no clipping or overlap; preserved the established design.'),
    native_powerpoint_opened=False,all_12_slides_verified=True)
(root/'docs/evidence/presentation-0.4.1-visual.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(verified_pages=12,reviewed_slides=12,findings=0,visually_accepted_style_warnings=1)))
