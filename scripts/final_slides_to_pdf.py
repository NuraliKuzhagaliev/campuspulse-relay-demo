"""Package verified presentation renders as PDF pages; never draw substitute evidence."""
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
folder,output=map(Path,sys.argv[1:])
assert folder.drive.lower()==output.drive.lower()=='d:'
if output.exists():raise SystemExit('Preserve existing presentation outputs; use a new revision.')
pdf=canvas.Canvas(str(output),pagesize=(960,540))
pdf.setTitle('CampusPulse RELAY 0.4.0 integration evidence')
for image in sorted(folder.glob('slide-*.png')):
    pdf.drawImage(ImageReader(str(image)),0,0,width=960,height=540)
    pdf.showPage()
pdf.save()
