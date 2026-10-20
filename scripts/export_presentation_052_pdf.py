"""PDF pages embed the actual final-PPTX renders, with working demo links."""
from pathlib import Path
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
folder,output=map(Path,sys.argv[1:]);assert folder.drive.lower()==output.drive.lower()=='d:'
assert not output.exists(),'Preserve previous PDFs; choose a new revision.'
pages=sorted(folder.glob('slide-*.png'));assert len(pages)==14
pdf=canvas.Canvas(str(output),pagesize=(960,540),pageCompression=1)
pdf.setTitle('CampusPulse RELAY 0.5.2');pdf.setAuthor('CampusPulse RELAY');pdf.setSubject('Product briefing with original logo and actual dated evidence')
for index,image in enumerate(pages,1):
 pdf.drawImage(ImageReader(str(image)),0,0,width=960,height=540)
 if index==14:
  pdf.linkURL('https://campuspulse-relay-demo.onrender.com/',(50.4,156,914.4,198),relative=0,thickness=0)
  pdf.linkURL('https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',(50.4,42.6,914.4,73.8),relative=0,thickness=0)
 pdf.showPage()
pdf.save()
print('Exported 14 high-resolution rendered pages with two working link annotations.')
