from pathlib import Path
import os,json
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
root=Path(__file__).resolve().parents[1]
stem=os.environ.get('RELAY_PRESENTATION_STEM','CampusPulse-RELAY-'+json.loads((root/'package.json').read_text(encoding='utf-8'))['version'])
output=root/'release/presentation'/f'{stem}.pdf'
pdf=canvas.Canvas(str(output),pagesize=(960,540))
pdf.setTitle('CampusPulse RELAY - release briefing')
pdf.setAuthor('CampusPulse RELAY')
for i in range(1,int(os.environ.get('RELAY_PRESENTATION_SLIDES','8'))+1):
    image=root/f'.local/presentation-build/slide-{i:02}.png'
    pdf.drawImage(ImageReader(str(image)),0,0,width=960,height=540)
    pdf.showPage()
pdf.save()
