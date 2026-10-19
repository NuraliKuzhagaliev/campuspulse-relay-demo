"""Reproduce the reported import defects without model/network calls."""
import json
from pathlib import Path
from relay.evidence import read_upload, extract_facts
from relay.extraction import extraction_proposal
from relay.domain import now
if Path('docs/evidence/audit-u-before.json').exists():
    raise SystemExit('The original baseline evidence is sealed. Do not overwrite it with a changed implementation.')

def source(text):
    return read_upload('audit.txt', text.encode()) | {'id':'audit','version':'v1'}

cases={
 'ru': 'Задание: Анализ спектра\nКурс: Оптика\nСеместр: Осень 2026\nСрок: 2026-10-23T18:00:00+05:00\nОценка: 45 минут',
 'kk': 'Тапсырма: Спектрді талдау\nКурс: Оптика\nСеместр: Күз 2026\nМерзімі: 2026-10-23T18:00:00+05:00\nҰзақтығы: 45 минут',
 'indented': '  **Assignment:** Spectrum\n  **Course:** Optics\n  **Term:** Autumn 2026\n  **Due:** 2026-10-23T18:00:00+05:00\n  **Effort:** 45 minutes',
 '45_minutes': 'Assignment: Spectrum\nCourse: Optics\nTerm: Autumn 2026\nDue: 2026-10-23T18:00:00+05:00\nEffort: 45 minutes',
}
out={'at':now(),'network_calls':0,'baseline_commit':'12a9eb04b89721108d4b67ce5df0be2f767e0b0e','cases':{}}
for key,text in cases.items():
    facts,tasks=extract_facts(source(text))
    out['cases'][key]={'draft_count':len(tasks),'effort':tasks[0]['minutes'] if tasks else None,'fact_count':len(facts)}
s=source('Assignment: Spectrum\nCourse: Optics\nTerm: Autumn 2026')
s['pages'].append({'page':2,'text':'Due: 2026-10-23T18:00:00+05:00\nEffort: 60 minutes'})
f,t=extract_facts(s);out['cases']['continued_page']={'due':t[0]['due'],'minutes':t[0]['minutes']}
for value in [None,42,False]:
    try: extraction_proposal(s,[dict(field='due',value=value,page=1,quote='Spectrum')]); result='accepted'
    except Exception as exc: result=type(exc).__name__
    out['cases']['due_'+str(value)]={'result':result}
try:read_upload('empty.txt',b' \n\t');out['cases']['whitespace']={'result':'accepted'}
except Exception as exc:out['cases']['whitespace']={'result':type(exc).__name__}
path=Path('docs/evidence/audit-u-before.json');path.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
