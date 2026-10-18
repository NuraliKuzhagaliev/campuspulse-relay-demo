from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
root=Path(__file__).resolve().parents[1]
output=root/'release/presentation/CampusPulse-RELAY-final.pdf'
pdf=canvas.Canvas(str(output),pagesize=(960,540))
pdf.setTitle('CampusPulse RELAY - release briefing')
pdf.setAuthor('CampusPulse RELAY')
for i in range(1,9):
    image=root/f'.local/presentation-build/slide-{i:02}.png'
    pdf.drawImage(ImageReader(str(image)),0,0,width=960,height=540)
    pdf.showPage()
pdf.save()
