/** Editable Russian product briefing. Actual evidence only; preserves all prior decks. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=process.cwd(),runtime='C:/Users/nural/.cache/codex-runtimes/codex-primary-runtime/dependencies',skill='C:/Users/nural/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.22136/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';process.env.RUNTIME_NODE=runtime+'/node/bin/node.exe';process.env.RUNTIME_PYTHON=runtime+'/python/python.exe';
const require=createRequire(import.meta.url),{Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(require.resolve('@oai/artifact-tool',{paths:[process.env.RUNTIME_NODE_MODULES]})).href);
const revision=process.env.RELAY_DECK_REVISION||'design-r1';if(!/^design-r\d+$/.test(revision))throw new Error('Use a new design-rN revision');
const output=path.join(root,'release/presentation'),build=path.join(root,'.local/presentation-final/0.5.2-'+revision),stem='CampusPulse-RELAY-0.5.2-'+revision;
await fs.mkdir(output,{recursive:true});await fs.mkdir(build,{recursive:true});
const capture=JSON.parse(await fs.readFile('docs/evidence/presentation-captures-0.5.2.json','utf8'));if(!capture.passed)throw new Error('Complete genuine synthetic capture flow first.');
const deck=Presentation.create({slideSize:{width:1600,height:900}});
const C={white:'#FFFFFF',ink:'#11223A',navy:'#101C34',blue:'#268EF0',mint:'#76DDBD',pale:'#EAF8F2',muted:'#607085',light:'#B9C9D8',line:'#DFE7ED',amber:'#C9872C'};
const repo='https://github.com/NuraliKuzhagaliev/campuspulse-relay-demo',url='https://campuspulse-relay-demo.onrender.com/';
function text(s,value,x,y,w,h,size=30,color=C.ink,bold=false,align='left'){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=value;q.text.style={typeface:'Arial',fontSize:size,color,bold,insets:0,autoFit:'none',wrap:'square',alignment:align};return q;
}
function link(s,label,uri,x,y,w,h,size=30,color=C.blue){const q=text(s,'',x,y,w,h,size,color,true);q.text=[{run:label,link:{uri,isExternal:true}}];return q;}
function slide(title,{dark=false,bg,notes='',sources=[]}={}){
 const s=deck.slides.add();s.background.fill=bg||(dark?C.navy:C.white);const n=deck.slides.items.length;
 text(s,title,80,74,1440,140,56,dark?C.white:C.ink,true);
 text(s,'CampusPulse RELAY 0.5.2',80,852,1120,24,18,dark?C.light:C.muted);
 text(s,String(n).padStart(2,'0'),1450,852,70,24,18,dark?C.light:C.muted,false,'right');
 s.speakerNotes.text=notes+'\n\nИсточники: '+sources.map(p=>p.startsWith('https:')?p:repo+'/blob/main/'+p).join('\n');return s;
}
async function image(s,name,x,y,w,h,{crop,fit='contain',alt=name}={}){const file=name.startsWith('docs/')||name.startsWith('assets/')?name:'docs/images/presentation-0.5.2/'+name+'.png';s.images.add({blob:new Uint8Array(await fs.readFile(file)),contentType:file.endsWith('.jpg')?'image/jpeg':'image/png',alt,fit,position:{left:x,top:y,width:w,height:h},...(crop?{crop}:{})});}
function table(s,values,widths,{x=80,y=235,w=1440,h=470,dark=false,size=28}={}){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});t.styleOptions={headerRow:false,bandedRows:false};t.borders.assign({fill:dark?'#24364D':C.line,width:0.5,style:'solid'});
 for(let r=0;r<values.length;r++){t.rows[r].height=h/values.length;for(let c=0;c<values[r].length;c++){const q=t.getCell(r,c);q.fill=dark?C.navy:C.white;q.text.style={typeface:'Arial',fontSize:r===0?22:size,bold:r===0||c===0,color:r===0?(dark?C.mint:C.muted):(dark?C.white:C.ink),insets:{left:18,right:18,top:16,bottom:10},verticalAlignment:'middle',wrap:'square'};}}
 return t;
}
// 01: minimal cover, original owner artwork preserved.
{
 const s=deck.slides.add();s.background.fill=C.white;
 text(s,'GDG ASTANA    TOPIC 2: CAMPUSPULSE AI',80,85,1250,36,24,C.muted,true);
 text(s,'CampusPulse\nRELAY',80,235,860,240,108,C.ink,true);
 text(s,'Учебная неделя\nс опорой на источники',86,540,830,130,43,C.ink);
 text(s,'Web и Windows 0.5.2',86,765,1000,42,28,C.muted);
 await image(s,'assets/branding/CampusPulse_RELAY_app_icon_logo_2K_20261020200832.jpg',955,200,565,565,{alt:'Оригинальный логотип CampusPulse RELAY, предоставленный владельцем'});
 s.speakerNotes.text='CampusPulse RELAY помогает студенту сопоставить документы, подтвердить факты и получить план на доступное время. Показываем текущую публичную версию 0.5.2. Основная архитектура использует Render и Gemini Developer API. Источник бренда: оригинальный JPG пользователя; пропорции и рисунок сохранены. Состояние выпуска: '+repo+'/blob/main/STATUS.md';
}
// 02: the specific source conflict, not invented user research.
{
 const s=slide('Один срок меняется. План требует пересмотра',{notes:'Это синтетический сценарий продукта, а не результат опроса или измеренный эффект на успеваемость. На снимке текущая 0.5.2 сохраняет две версии источника. Студент выбирает интерпретацию сам.',sources:['docs/evidence/presentation-captures-0.5.2.json','relay/evidence.py']});
 text(s,'Две версии\nисточника',80,257,500,150,60,C.blue,true);
 text(s,'RELAY сохраняет обе цитаты\nи показывает противоречие.',80,453,470,120,33,C.ink);
 text(s,'Выбор срока остаётся\nявным решением студента.',80,625,470,100,30,C.muted);
 await image(s,'conflict',610,254,910,490,{alt:'Настоящий снимок конфликта источников в синтетическом примере 0.5.2'});
}
// 03: hero product view.
{
 const s=slide('План учитывает доступное время',{dark:true,notes:'Синтетический пример: 540 минут требуемой работы и 540 минут доступной ёмкости после защищённого окна. Это детерминированный план OR-Tools, не ответ модели и не прогноз оценки. Скриншот получен на реальном публичном 0.5.2.',sources:['docs/evidence/presentation-captures-0.5.2.json','relay/scheduler.py']});
 await image(s,'week',80,236,1080,563,{alt:'Недельный календарь с выделенными учебными блоками и защищённым обязательством'});
 text(s,'540',1210,245,310,125,106,C.mint,true);text(s,'минут работы\nв этом примере',1215,386,300,96,30,C.white);
 text(s,'Занятость\nДедлайны\nЗависимости',1215,570,300,170,34,C.light);
}
// 04: exact source interpretation review.
{
 const s=slide('Каждое задание подтверждает студент',{notes:'Новый синтетический документ Urban sound map: 53 минуты, срок 23 октября в19:00 UTC+5. На экране детерминированная проверка извлечённых полей. Это не новый ответ Gemini. Студент сопоставляет поля с оригиналом и подтверждает каждое задание. Неизвестные данные остаются неизвестными.',sources:['docs/evidence/presentation-captures-0.5.2.json','tests/test_timezone_release.py']});
 text(s,'53 мин',80,277,390,100,76,C.blue,true);text(s,'точная оценка\nиз нового документа',84,410,370,100,31,C.muted);
 text(s,'Цитата и версия\nостаются доступны\nпосле подтверждения.',84,606,370,135,30,C.ink);
 await image(s,'assignment-review',485,240,1035,580,{alt:'Форма проверки одного задания, точных 53 минут и срока с явным подтверждением'});
}
// 05: actual baseline and what-if summaries.
{
 const s=slide('What-if сохраняет исходный план',{bg:C.pale,notes:'Сравнение сценариев не принимает изменение автоматически. Слева текущий baseline, справа результат потери среды из синтетического примера. Minimal Rescue сравнивает только дополнительно разрешённые окна. Source estimate and solver allocation remain separate.',sources:['docs/evidence/public-edges-0.5.2.json','docs/evidence/presentation-captures-0.5.2.json']});
 text(s,'Базовый план',80,236,680,48,34,C.ink,true);text(s,'Сценарий: нет среды',840,236,680,48,34,C.ink,true);
 await image(s,'plan-summary',80,320,680,310);await image(s,'what-if',840,320,680,310);
 text(s,'Дефицит времени виден до применения изменений',80,682,1440,72,40,C.ink,true);
 text(s,'Minimal Rescue использует только разрешённую студентом дополнительную доступность.',80,776,1430,46,26,C.muted);
}
// 06: required editable feature evidence table.
{
 const s=slide('Пять основных улучшений',{notes:'F1–F5 реализованы локально и сохранены в 0.5.2. Их полная реальная приёмка с Calendar и Gemini отслеживается отдельно. Source references prove source text, not semantic correctness. No stress/grade outcome measured.',sources:['REQUIREMENTS.md','README.md','docs/final_integration_ledger.md']});
 table(s,[['','Улучшение','Что видит студент'],['F1','Evidence / Conflict Inbox','Цитаты, страницы, версии и явный выбор спорного факта'],['F2','Feasibility / What-if','План по ограничениям и видимый дефицит времени'],['F3','Change Radar','Наблюдение разрешённых GitHub-источников и изменений'],['F4','Approved Actions','Точный preview, отдельное одобрение и квитанция чтения'],['F5','Next Action Packets','Конкретный шаг, связанный с исходным критерием']],[100,390,950],{y:240,h:480,size:27});
 text(s,'Локально реализованы. Реальная приёмка Calendar и Gemini отмечается отдельно.',80,765,1430,65,26,C.muted);
}
// 07: honest dated real-model evidence, not a fresh cosmetic-run claim.
{
 const s=slide('Gemini использует настоящие MCP-инструменты',{dark:true,notes:'Реальная серия на runtime7e4098d от20.10.2026: пять собственных документов, шесть ходов, пять complete и один partial. Partial сохраняет отвергнутый вызов TOOL_INPUT_INVALID / extra_forbidden, даже когда модель затем исправила предложение. Это не статистическая гарантия и не новый AI-тест0.5.2. Публичная0.5.2 сохраняет этот путь обработки. Названия инструментов отражают реальные функции MCP.',sources:['docs/evidence/audit-live-mvgqi7ei.json','docs/evidence/final-0.5.1-partial-diagnosis.json','docs/evidence/public-deployment-0.5.2.json']});
 text(s,'6',80,235,400,230,200,C.mint,true);text(s,'реальных ходов\nна пяти документах',88,505,500,110,38,C.white);
 text(s,'read_course_source\npropose_academic_extraction\nsave_validated_plan',700,260,820,155,29,C.light);
 text(s,'5 complete',700,485,760,80,60,C.mint,true);text(s,'1 partial',700,594,760,80,60,'#F1C27D',true);
 text(s,'Серия на 0.5.1 от 20.10.2026. Частичный исход остаётся в истории.',80,778,1440,50,26,C.light);
}
// 08: continuity features and actual newly recorded 45/95.
{
 const s=slide('Прогресс и продолжение работы',{notes:'В отдельном синтетическом сеансе текущей версии записаны45 минут работы и95 минут явно оставшейся работы. Эти величины независимы. Время не доказывает обучение или завершение. Passport восстанавливает выбранные источники и прогресс как новую копию без ключей и полномочий одобрения. Clarify First сравнивает последствия неизвестных данных. Handoff Radar наблюдает PR. Submission Preflight проверяет наблюдаемую структуру черновика, не выставляет оценку.',sources:['docs/evidence/presentation-captures-0.5.2.json','relay/progress.py','relay/passport.py','src/Continuity.tsx']});
 await image(s,'progress-numbers',80,236,1440,118,{alt:'Настоящий сохранённый UI: исходная оценка 180, учтено45, явно осталось95 минут'});
 text(s,'Время и остаток\nучитываются отдельно',80,420,650,120,43,C.ink,true);
 text(s,'Workspace Passport',840,420,680,52,34,C.blue,true);text(s,'Перенос выбранных источников\nи прогресса как новой копии.',840,495,650,95,31,C.ink);
 text(s,'Clarify First',80,651,650,44,31,C.blue,true);text(s,'Влияние неизвестных данных на план.',80,712,650,86,28,C.muted);
 text(s,'Handoff Radar',840,651,680,44,31,C.blue,true);text(s,'Наблюдение PR без автоматического\nпризнания задания выполненным.',840,712,650,86,28,C.muted);
 text(s,'Submission Preflight проверяет структуру черновика по требованиям.',80,808,1440,34,24,C.muted);
}
// 09: new locale-specific app calendars, Russian browser.
{
 const s=slide('Интерфейс EN / RU / KZ',{dark:true,notes:'Настоящие календари публичной0.5.2 при русском языке браузера. Стандартный внутренний код казахского языка остаётся kk. Доступны только Asia/Almaty, Europe/Moscow и UTC. Сервер отклоняет произвольный пояс. Системный диалог выбора файла сохраняет язык операционной системы.',sources:['docs/evidence/public-locale-0.5.2.json','docs/evidence/presentation-captures-0.5.2.json','relay/timezones.py']});
 for(const [i,lang] of ['en','ru','kk'].entries()){text(s,['EN','RU','KZ'][i],100+i*500,217,400,44,32,C.mint,true,'center');await image(s,'date-'+lang,100+i*500,285,400,470);}
 text(s,'Казахстан UTC+5        Москва UTC+3        UTC',80,790,1440,44,30,C.white,false,'center');
}
// 10: owner approval path, with explicitly illustrative screenshot.
{
 const s=slide('Calendar: действие подтверждает владелец',{notes:'На снимке настоящий иллюстративный предпросмотр одного синтетического события. Его не одобряли и не записывали в Google. Историческое согласие Google и восстановление цели были реальными. Приёмка реальной записи, read-back, повтора без дублей, отмены и отзыва доступа остаётся открытой. Каждый посетитель подключает свой календарь. Согласие Google не одобряет события. Защищённая отмена требует отдельного решения владельца.',sources:['docs/independent_tester_calendar_ru.txt','BLOCKERS.md','docs/evidence/presentation-captures-0.5.2.json']});
 await image(s,'calendar-single-preview',80,235,530,550,{alt:'Настоящий иллюстративный предпросмотр одного события, без Google-записи и approval digest'});
 const items=[['01','Добровольное согласие Google'],['02','Свой отдельный календарь'],['03','Точный preview и одобрение'],['04','Запись и повторное чтение'],['05','Отдельная отмена теста']];items.forEach(([n,label],i)=>{text(s,n,700,245+i*98,80,54,30,C.blue,true);text(s,label,805,245+i*98,715,70,32,C.ink);});
 text(s,'На снимке имитация. Приёмка реальных событий Calendar ожидается.',80,789,1440,44,26,C.muted);
}
// 11: architecture as a required editable factual table, not decorative shapes.
{
 const s=slide('Рабочая архитектура 0.5.2',{dark:true,notes:'Основной маршрут: публичный Render Free, серверный Gemini Developer API, подписанные защищённые MCP-инструменты, собственные данные пространства и разрешённые GitHub-источники. Gateway хранит сеансы, CSRF, SQLite, очередь и добровольное подключение Calendar. OR-Tools строит детерминированный план. Изменения Calendar требуют явного одобрения и исключены из набора инструментов модели. Внутренние ключи остаются на сервере.',sources:['README.md','relay/gateway.py','relay/public_ai.py','relay/mcp_server.py','infra/Dockerfile.alternative']});
 table(s,[['Граница','Компоненты','Назначение'],['Пользователь','React / Windows Electron','Изолированный сеанс и явные действия'],['Приложение','Render Free / FastAPI','Данные, операции и справедливая очередь'],['AI','Gemini Developer API','Серверный ключ и многоходовый диалог'],['Инструменты','Защищённый MCP / OR-Tools','Источники, GitHub и проверенный план'],['Calendar','Отдельный Google OAuth','Свой календарь, одобрение и read-back']],[280,500,660],{dark:true,y:230,h:490,size:26});
 text(s,'Публичный вход без приглашений и пользовательских API-ключей',80,776,1440,54,30,C.mint,true);
}
// 12: counts are scoped, never a model success percentage.
{
 const s=slide('Проверки с сохранёнными доказательствами',{notes:'0.5.2:252 Python-теста и3подтеста,8проверок IPC,9сочетаний языка и ширины,4дополнительных сценария и2чистых HTTPS-сеанса. В100-сессионном тесте провайдер имитирован, реальных Gemini-вызовов ноль.16файлов Windows совпадают с исходниками, ProductVersion0.5.2.0. Это не подтверждает физическую установку, диалоги Open/Save или нажатие уведомления.13исходных файлов выпуска имеют подтверждённый SHA-256. Предыдущие релизы сохранены.',sources:['docs/evidence/locale-release-0.5.2.json','docs/evidence/public-locale-0.5.2.json','docs/evidence/public-edges-0.5.2.json','docs/evidence/locale-release-0.5.2-100-simulated.json','docs/evidence/windows-package-0.5.2.json','docs/evidence/release-distribution-0.5.2.json']});
 for(const [i,[n,label]] of [['252','Python-теста\nи 3 подтеста'],['9','сочетаний языка\nи размера экрана'],['100','сеансов в тесте\nс имитацией провайдера']].entries()){text(s,n,80+i*500,250,440,150,118,i===1?C.blue:C.ink,true);text(s,label,85+i*500,433,425,115,31,C.muted);}
 text(s,'8 проверок узкого IPC',80,640,680,60,37,C.ink,true);text(s,'2 чистых публичных сеанса',840,640,680,60,37,C.ink,true);
 text(s,'16 файлов Windows совпадают с исходниками. Физическая установка проверяется отдельно.',80,746,1440,75,26,C.muted);
}
// 13: actual acceptance boundaries, visibly on slide.
{
 const s=slide('Границы подтверждённого результата',{notes:'NON_GCP_READY=false. Официального разрешения заменить обязательный managed GCP не установлено. Физическая приёмка текущей Windows-версии и реальные операции Calendar требуют участия владельца. Прежнее согласие и цель были реальными, но временный сеанс может истечь. Бесплатные квоты конечны, хранилище может сброситься. Личных расходов, платного fallback или активации billing не было.',sources:['BLOCKERS.md','STATUS.md','release/manifest.json','docs/remaining_actions_0.5.2.md']});
 table(s,[['Область','Фактический статус'],['Публичный web 0.5.2','Render live, собственные документы, проверенные ссылки Windows'],['Gemini / MCP / GitHub','Реальные проходы сохранены вместе с partial и ошибками'],['Google Calendar','Согласие и цель проверялись. Приёмка событий ещё ожидается'],['Windows 0.5.2','Сборка проверена. Native Open/Save и notification click ожидаются'],['Managed GCP / Agent Engine','Отключён. Исходный обязательный критерий не выполнен']],[450,990],{y:230,h:485,size:26});
 text(s,'NON_GCP_READY = false',80,759,760,52,32,C.amber,true);text(s,'Бесплатные квоты и временное хранилище',840,763,680,60,26,C.muted);
}
// 14: direct ordinary URL and repository links. No invite/schedule.
{
 const s=deck.slides.add();s.background.fill=C.navy;
 text(s,'CampusPulse RELAY',80,85,1050,55,35,C.mint,true);
 text(s,'Свой документ.\nСвоя учебная неделя.',80,252,1300,210,86,C.white,true);
 link(s,'campuspulse-relay-demo.onrender.com',url,84,570,1440,70,44,C.mint);
 text(s,'Публичный вход без регистрации и собственного ключа',84,672,1440,58,32,C.light);
 link(s,'Исходники, образцы, README и Windows',repo,84,777,1440,52,28,C.light);
 s.speakerNotes.text='Демонстрация для жюри: обычнаяHTTPSссылка, собственныйсинтетическийдокумент, цитаты, подтверждение, план, what-if, вопросGemini иPassport. Calendarвладелец подключаетдобровольно. ManagedGCPостаетсяотдельным невыполненнымкритерием. Документыдлябесплатнойобработки должнысоответствоватьпоказаннымусловиям. Не обещаемнеограниченныебесплатныезапросы. Links: '+url+' '+repo;
}
// Inspect and finalize the actual editable PPTX before rendering the exported file.
await fs.writeFile(path.join(build,'inspection.ndjson'),(await deck.inspect({kind:'slide,textbox,image,table',maxChars:400000})).ndjson);
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const finalPptx=path.join(output,stem+'.pptx');
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:finalPptx,pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-heading-fit','--validate-bullet-geometry','--require-native-table-slide','6','--require-native-table-slide','11','--require-native-table-slide','13'],explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[6,11,13],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const finalDeck=await PresentationFile.importPptx(await FileBlob.load(finalPptx));
for(const [i,s] of finalDeck.slides.items.entries()){const png=await finalDeck.export({slide:s,format:'png',scale:1.5});await fs.writeFile(path.join(build,'slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));console.log(JSON.stringify({rendered_slide:i+1}));}
// Bundled PDF exporter currently fails resolving #standard-fonts/Helvetica.
// The alternative PDF embeds the actual validated-PPTX renders, never substitutes illustrations.
const pdfResult=spawnSync(path.join(root,'.venv/Scripts/python.exe'),['scripts/export_presentation_052_pdf.py',build,path.join(output,stem+'.pdf')],{cwd:root,env:process.env,encoding:'utf8'});if(pdfResult.status!==0)throw new Error(pdfResult.stderr);console.log(pdfResult.stdout.trim());
const proof={version:'0.5.2',revision,slides:14,language:'Russian',pptx:finalPptx,pdf:path.join(output,stem+'.pdf'),pdf_kind:'High-resolution actual slide render pages; editable text and native tables are in PPTX',renders:build,editable_text:true,native_tables:[6,11,13],original_logo_preserved:true,native_powerpoint_opened:false,source_runtime_commit:capture.deployed_commit,public_capture_evidence:'docs/evidence/presentation-captures-0.5.2.json',model_calls_for_presentation:0,google_writes_for_presentation:0,NON_GCP_READY:false,visual_review_pending:true};
await fs.writeFile(path.join(build,'result.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
