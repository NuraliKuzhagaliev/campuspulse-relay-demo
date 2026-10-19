"""Independent prose fixtures frozen after parser changes, before genuine UI runs."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];folder=root/'.local/audit-holdouts';folder.mkdir(parents=True,exist_ok=True)
target=folder/'frozen.json'
if target.exists():raise SystemExit('Holdouts already frozen. Do not tailor them to an observed provider response.')
texts={
 'holdout-en.txt': 'Research Methods, Autumn term 2026. Assessment M26 is the Measurement log: submit it by 22 October 2026 at 17:30 in Asia/Almaty (UTC+05:00). Reserve 45 minutes. Explain instrument drift; include Method and Observations sections. A second task, assessment N13, is the Noise comparison memo, due 23 October 2026 at 19:00 in the same timezone. Allow 75 minutes for it. Include Comparison and Limits sections and compare two microphone readings.\n',
 'holdout-ru.txt': 'Инженерная физика, семестр «Осень 2026». Задание TH-62: отчёт «Тепловой баланс». Сдать 23 октября 2026 года в 18:30, часовой пояс Asia/Qyzylorda (UTC+05:00). На работу отводится полтора часа. Обязательны разделы «Метод», «Наблюдения» и «Ограничения». Сравните температуру двух образцов и объясните погрешность измерений.\n',
 'holdout-kk.txt': '«Жер бедері» пәні, «Күз 2026» семестрі. GEO-8 тапсырмасы: «Жартас қабаты» есебі. Тапсыру мерзімі — 2026 жылғы 23 қазан, сағат 20:30, Asia/Almaty уақыт белдеуі (UTC+05:00). Жұмысқа 45 минут бөлінеді. «Әдіс», «Бақылау» және «Шектеулер» бөлімдері қажет. Екі үлгіні салыстырып, өлшеу қатесін түсіндіріңіз.\n',
}
expected={
 'holdout-en.txt':[dict(key='M26',minutes=45,due='2026-10-22T17:30:00+05:00'),dict(key='N13',minutes=75,due='2026-10-23T19:00:00+05:00')],
 'holdout-ru.txt':[dict(key='TH-62',minutes=90,due='2026-10-23T18:30:00+05:00')],
 'holdout-kk.txt':[dict(key='GEO-8',minutes=45,due='2026-10-23T20:30:00+05:00')],
}
files=[]
for name,text in texts.items():
    path=folder/name;path.write_text(text,encoding='utf-8');files.append(dict(file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),expected=expected[name]))
target.write_text(json.dumps(dict(frozen_at=datetime.now(timezone.utc).isoformat(),independent_of_model_outcomes=True,files=files),indent=2),encoding='utf-8');print(json.dumps({'frozen_holdouts':len(files),'model_calls':0}))
