"""Publish only deliberately synthetic, permission-free academic examples."""
from pathlib import Path
import json, shutil, zipfile, hashlib, html
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

root=Path(__file__).resolve().parents[1];out=root/'public/samples';out.mkdir(parents=True,exist_ok=True)
files={
 '01-original.md': '# Assignment: Prism calibration\nCourse: Applied Optics\nTerm: Autumn 2026\nAssignment ID: prism-04\nDue: 2026-10-23T18:00:00+05:00\nEffort: 45 minutes\nRubric:\n- [ ] Explain calibration uncertainty\n- [ ] Compare two measurements\nFilename: prism-*.md\nSections: Method; Results; Limitations\nWords: 30-250\n',
 '02-revision.md': '# Assignment: Prism calibration\nCourse: Applied Optics\nTerm: Autumn 2026\nAssignment ID: prism-04\nDue: 2026-10-22T18:00:00+05:00\nEffort: 45 minutes\n- [ ] Explain calibration uncertainty\n- [ ] Compare two measurements\n',
 '03-prose-en.txt': 'In the Applied Acoustics course, Autumn 2026, prepare the Echo mapping report (assignment key echo-09). Submit it on 23 October 2026 at 18:00, timezone Asia/Almaty (UTC+05:00). The estimated effort is 75 minutes. Include Method, Results and Limitations sections. Explain how the microphone was calibrated and compare the two room measurements. Submit a Markdown file named echo-report.md with 40 to 300 words.\n',
 '04-prose-ru.txt': 'По курсу «Экология рек», семестр «Осень 2026», подготовьте отчёт «Карта течений», код river-12. Сдать 23 октября 2026 года в 19:00 по часовому поясу Asia/Almaty (UTC+05:00). Оценка работы — 45 минут. Включите разделы «Метод», «Результаты» и «Ограничения». Объясните выбор точек измерения и сравните два участка реки.\n',
 '05-prose-kk.txt': '«Қолданбалы астрономия» пәнінен, «Күз 2026» семестрінде, «Жұлдыз жарығы» есебін дайындаңыз, тапсырма коды star-21. Тапсыру мерзімі: 2026 жылғы 23 қазан, сағат 20:00, Asia/Almaty уақыт белдеуі (UTC+05:00). Жұмыс ұзақтығы — 75 минут. «Әдіс», «Нәтижелер» және «Шектеулер» бөлімдерін қосыңыз. Екі бақылауды салыстырып, өлшеу қатесін түсіндіріңіз.\n',
 '06-missing-and-ambiguous.md': '# Assignment: Wetland survey\nCourse: Field Biology\nTerm: Autumn 2026\nAssignment ID: wetland-02\nDue: 03/04\nEffort: not specified\n- [ ] Compare water samples\nThe date convention and year are intentionally missing. Ask the teacher; do not invent a deadline or estimate.\n',
 '07-same-title.md': '# Assignment: Lab\nCourse: Botany\nTerm: Autumn 2026\nAssignment ID: bot-lab-3\nDue: 2026-10-23T18:00:00+05:00\nEffort: 45 minutes\n- [ ] Describe leaf structure\n# Assignment: Lab\nCourse: Materials\nTerm: Autumn 2026\nAssignment ID: mat-lab-3\nDue: 2026-10-23T19:00:00+05:00\nEffort: 75 minutes\n- [ ] Compare tensile measurements\n',
 '08-busy.ics': 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//CampusPulse RELAY//Synthetic samples//EN\r\nBEGIN:VEVENT\r\nUID:relay-synthetic-seminar\r\nDTSTAMP:20261019T120000Z\r\nDTSTART:20261020T130000Z\r\nDTEND:20261020T140000Z\r\nSUMMARY:Synthetic seminar\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n',
 '10-prism-draft.md': '# Method\nWe calibrated the instrument against a reference prism, repeated both readings, and recorded uncertainty.\n# Results\nThe first reading was 12.4 degrees and the second was 12.7 degrees. Their difference was 0.3 degrees.\n# Limitations\nThese synthetic observations illustrate structure only. Calibration accuracy and scientific correctness still need human review.\n',
}
for name,text in files.items():(out/name).write_text(text,encoding='utf-8',newline='')
shutil.copyfile(root/'fixtures/workspace-passport-example.relay.json',out/'09-workspace.relay.json')
shutil.copyfile(root/'fixtures/network-security-original.pdf',out/'13-original-brief.pdf')
p=canvas.Canvas(str(out/'11-continued-brief.pdf'),pagesize=A4)
def page(lines):
 p.setFont('Helvetica',12);y=800
 for line in lines:p.drawString(45,y,line);y-=23
page(['SYNTHETIC COURSEWORK - no personal data','Assignment: Polarization memo','Course: Applied Optics','Term: Autumn 2026','Assignment ID: polar-16','The deadline, effort and rubric continue on page 2.']);p.showPage()
page(['Continuation: Polarization memo','Due: 2026-10-23T18:00:00+05:00','Effort: 75 minutes','- [ ] Compare two filters','- [ ] Explain measurement uncertainty','Sections: Method; Results; Limitations','Filename: polarization-*.md']);p.save()
styles=getSampleStyleSheet();doc=SimpleDocTemplate(str(out/'12-table-brief.pdf'),pagesize=A4,rightMargin=30,leftMargin=30)
rows=[['Assignment','Course / term','Deadline (UTC+05:00)','Effort'],['Soil conductivity','Earth Science\nAutumn 2026','23 Oct 2026 18:00','45 minutes'],['Mineral reflection','Earth Science\nAutumn 2026','23 Oct 2026 20:00','75 minutes']]
table=Table(rows,colWidths=[120,120,170,100]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1c4141')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#b9c6ce')),('FONTSIZE',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
doc.build([Paragraph('Synthetic table brief',styles['Title']),Spacer(1,20),table,Spacer(1,22),Paragraph('Assignment keys: soil-31 and mineral-32 respectively. For each report, include Method, Results and Limitations; compare measurements and explain uncertainty. Do not treat these examples as real course requirements.',styles['BodyText'])])
expectations={
 '01-original.md':'1 task prism-04; exact effort45, solver60; due23Oct18:00+05. Import02 next to create one deadline conflict.',
 '02-revision.md':'Same exact course/term/key; revised due22Oct18:00+05; choose the cited revision explicitly. Never silently replace the original.',
 '03-prose-en.txt':'Gemini review: 1 Echo mapping report / Applied Acoustics / Autumn2026 / echo-09; due23Oct18:00+05; effort75, solver90; cited normalized rubric.',
 '04-prose-ru.txt':'Gemini review: 1 Карта течений / Экология рек / Осень2026 / river-12; due23Oct19:00+05; effort45, solver60.',
 '05-prose-kk.txt':'Gemini review: 1 Жұлдыз жарығы / Қолданбалы астрономия / Күз2026 / star-21; due23Oct20:00+05; effort75, solver90.',
 '06-missing-and-ambiguous.md':'1 draft; due/effort unknown. Clarify date convention/year/time/zone and effort in review; no plan claiming complete workload.',
 '07-same-title.md':'2 separate Lab tasks, Botany/bot-lab-3 and Materials/mat-lab-3; effort45/75, solver60/90; mapping one must not merge the other.',
 '08-busy.ics':'1 imported snapshot,20Oct18:00–19:00 Asia/Almaty. Blocks that overlap it must be excluded. No Google consent needed.',
 '09-workspace.relay.json':'Workspace Passport input ONLY. Preview and Restore a fresh copy under Progress/Workspace Passport. Archived claims,45 logged/95 explicitly remaining. Not a Source import.',
 '10-prism-draft.md':'Preflight draft input ONLY for task01. Structural sections and30–250words present; filename matches. Semantic rubric remains human review, no grade/submission claim.',
 '11-continued-brief.pdf':'1 Polarization memo; identity page1; deadline23Oct18:00+05, effort75 and rubric page2. Citations keep original pages.',
 '12-table-brief.pdf':'Gemini review: 2 table entities soil-31/mineral-32, Earth Science/Autumn2026; effort45/75, deadlines18:00/20:00+05. Confirm each separately.',
 '13-original-brief.pdf':'Existing illustrative Network Security lab PDF. Academic term is absent: clarify it explicitly in review. Do not invent the missing term.',
}
guide='''# Try with our sample data / Образцы / Үлгілер

All files are synthetic and permission-free. No real students, personal Calendar data or credentials. Ordinary public link: https://campuspulse-relay-demo.onrender.com/ . No invitations, account or visitor API key.

Reference context: 19–25 October 2026, Asia/Almaty (UTC+05:00), available every day18:00–21:00; optional ICS blocks20October18:00–19:00. Frozen source deadlines remain unchanged. If testing after those deadlines, expect past-deadline unscheduled work, or explicitly enter your own new interpretation; do not claim original dates moved automatically.

English: click Use my own data. Connections → Import a file (or Evidence → Import selected file), maximum2MiB text PDF/MD/TXT/ICS. For prose/tables, confirm permitted free-service processing, then Document review → Propose with Gemini. Review citations, fill missing course/term/key/deadline/effort and Confirm this assignment for EACH entity. Planning context: select the reference dates, timezone and available weekdays/hours. Repair the week → compare a what-if → inspect packet/Preflight/progress. Calendar preview/approval/receipt is explicitly illustrative unless you separately consent to your own Google Calendar. Export/restore a Passport, refresh and verify facts/remaining work. Real Calendar is NOT needed for these examples.

Русский: «Со своими данными» → «Подключения» → «Импортировать файл» (или раздел доказательств). Для обычного текста/таблиц подтвердите условия бесплатной обработки внизу, затем «Разбор документов» → «Предложить через Gemini». Проверьте цитаты, заполните неизвестные поля и подтвердите КАЖДОЕ задание отдельно. В «Период и доступное время» выберите19–25.10.2026, Asia/Almaty и18:00–21:00. Постройте план, сравните сценарий, проверьте пакет/черновик/прогресс. Предпросмотр и квитанции Calendar — учебная имитация без отдельного личного согласия. Passport загружается в отдельной вкладке, черновик — в Preflight.

Қазақша: «Өз деректеріммен» → қосылымдар → файл импорттау. Қарапайым мәтін/кесте үшін төмендегі тегін өңдеу шарттарын растаңыз, одан кейін «Құжаттарды талдау» → «Gemini арқылы ұсыну». Дәйексөздерді тексеріп, белгісіз өрістерді толтырыңыз; ӘР тапсырманы бөлек растаңыз. Жоспарлау кезеңі:19–25.10.2026, Asia/Almaty, күн сайын18:00–21:00. Жоспарды, сценарийді, тапсырма пакетін, Preflight пен прогресті тексеріңіз. Жеке Calendar келісімінсіз күнтізбе әрекеттері оқу үлгісі болып қалады. Passport пен Preflight файлдары дереккөз импортынан бөлек жүктеледі.

Use a fresh own workspace for each numbered scenario, except01→02 (revision/conflict) and01+08+10 (busy time/Preflight). Missing facts require clarification, not guessing. Source text is untrusted evidence, never application instructions. Free hosting storage is temporary: export a Passport; restart/redeploy can reset sessions.

| File | Format / language / bytes | Expected result and purpose |
|---|---|---|
'''
metadata=[]
for name,expected in expectations.items():
 path=out/name;data=path.read_bytes();language='RU' if name.startswith('04') else 'KK' if name.startswith('05') else 'EN / structured'
 guide+=f'| [{name}]({name}) | {path.suffix} / {language} / {len(data)} | {expected} |\n'
 metadata.append(dict(file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),expected=expected))
(out/'README.md').write_text(guide,encoding='utf-8')
(out/'expected-results.json').write_text(json.dumps(dict(reference_week='2026-10-19',timezone='Asia/Almaty',files=metadata),indent=2,ensure_ascii=False),encoding='utf-8')
rows=''.join(f'<tr><td><a href="{html.escape(m["file"])}" download>{html.escape(m["file"])}</a></td><td>{m["bytes"]} bytes</td><td>{html.escape(m["expected"])}</td></tr>' for m in metadata)
page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>RELAY sample documents</title><style>body{font:17px system-ui;line-height:1.6;max-width:1100px;margin:40px auto;padding:20px;color:#173336;background:#f6f7f4}a{color:#214acc}table{border-collapse:collapse;width:100%}td{padding:14px;border-bottom:1px solid #bacbc7;overflow-wrap:anywhere}h1{line-height:1.2}pre{white-space:pre-wrap}tr:nth-child(odd){background:#fff}@media(max-width:700px){td{display:block}}</style><h1>Sample documents · Образцы · Үлгілер</h1><p><a href="/">Open RELAY</a> · <a href="judge_sample_pack.zip" download>Download all samples ZIP</a> · <a href="README.md">Full guide</a></p><p>Synthetic material only. Own data / Со своими данными / Өз деректеріммен. Source import, Passport restore and Preflight draft are separate inputs.</p><table>'+rows+'</table><h2>Step-by-step / Пошагово / Қадамдар</h2><pre>'+html.escape(guide.split('| File |')[0])+'</pre></html>'
(out/'index.html').write_text(page,encoding='utf-8')
with zipfile.ZipFile(out/'judge_sample_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(out.iterdir()):
  if p.name!='judge_sample_pack.zip':z.write(p,p.name)
print(json.dumps(dict(files=len(metadata),zip_bytes=(out/'judge_sample_pack.zip').stat().st_size,public_path='/samples/'),indent=2))
