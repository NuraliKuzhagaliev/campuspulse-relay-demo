export const auditTranslations: Record<string, [string, string]> = {
 'The tool-step limit was reached. No final AI answer was produced. Review saved document proposals before retrying.':['Достигнут предел шагов инструментов. Итоговый ответ ИИ не получен. Перед повтором проверьте сохранённые предложения в разделе проверки документа.','Құрал қадамдарының шегіне жетті. ЖИ-дің қорытынды жауабы алынбады. Қайта сұрамас бұрын құжатты тексеру бөліміндегі сақталған ұсыныстарды қарап шығыңыз.'],
 'Connections':['Подключения','Қосылымдар'],
 'Public temporary workspace':['Публичная временная рабочая область','Жалпыға ашық уақытша жұмыс кеңістігі'],
 'Calendar needs reconnection':['Calendar нужно переподключить','Calendar-ды қайта қосу керек'],
 'Calendar needs reconnection. Your documents and progress remain available; no fresh Calendar availability is assumed.':['Calendar нужно переподключить. Документы и прогресс доступны; актуальное свободное время Calendar не предполагается.','Calendar-ды қайта қосу керек. Құжаттар мен прогресс қолжетімді; Calendar-дың өзекті бос уақыты болжанбайды.'],
 'Connected to your selected Calendar. Approved actions affect real events; review the exact preview first.':['Подключён выбранный вами Calendar. Одобренные действия меняют реальные события; сначала проверьте точный предпросмотр.','Таңдалған Calendar қосылған. Расталған әрекеттер нақты оқиғаларды өзгертеді; алдымен дәл алдын ала көріністі тексеріңіз.'],
 'Selected files: PDF, MD, TXT, ICS · up to 2 MiB; text PDFs only.':['Выбранные файлы: PDF, MD, TXT, ICS · до 2 МиБ; только текстовые PDF.','Таңдалған файлдар: PDF, MD, TXT, ICS · 2 МиБ-қа дейін; тек мәтіндік PDF.'],
 'Public AI access needs no sign-in or invitation. Retry the connection; Calendar consent is a separate optional action in Connections.':['Для публичного ИИ не нужны вход или приглашение. Повторите подключение; согласие Calendar — отдельное добровольное действие в разделе «Подключения».','Ашық ЖИ үшін кіру не шақыру қажет емес. Қосылымды қайталаңыз; Calendar келісімі — қосылымдар бөліміндегі бөлек ерікті әрекет.'],
  "This action is unavailable in this workspace. Check the selected resource and access.":
    [
      "Это действие недоступно в текущей области. Проверьте выбранный ресурс и права доступа.",
      "Бұл әрекет осы кеңістікте қолжетімсіз. Таңдалған ресурс пен рұқсаттарды тексеріңіз.",
    ],
  "The selected document has no readable content. Export a non-empty text document and retry.":
    [
      "В выбранном документе нет читаемого текста. Экспортируйте непустой текстовый документ и повторите.",
      "Таңдалған құжатта оқылатын мәтін жоқ. Бос емес мәтіндік құжатты экспорттап, қайталаңыз.",
    ],
  "This local time is ambiguous or invalid. Choose an unambiguous time in the workspace timezone.":
    [
      "Это местное время неоднозначно или недопустимо. Выберите однозначное время в часовом поясе области.",
      "Бұл жергілікті уақыт екіұшты не жарамсыз. Кеңістік уақыт белдеуінде бірмәнді уақытты таңдаңыз.",
    ],
  "Add study availability in Planning context before generating a plan.": [
    "Перед построением плана добавьте доступное время в разделе «Период и доступное время».",
    "Жоспар құрмас бұрын жоспарлау кезеңіне бос оқу уақытын қосыңыз.",
  ],
  "A confirmed deadline and effort estimate are required before planning.": [
    "Перед планированием подтвердите срок и оценку трудозатрат.",
    "Жоспарлау алдында мерзім мен еңбек бағасын растаңыз.",
  ],
  "No academic assignments detected. The document is available for discussion; no tasks or successful academic extraction are claimed.":
    [
      "Учебные задания не обнаружены. Документ доступен для обсуждения; задания и успешное извлечение учебных требований не заявляются.",
      "Оқу тапсырмалары табылмады. Құжатты талқылауға болады; тапсырмалар не оқу талаптарының сәтті алынуы мәлімделмейді.",
    ],
  "Review assignments and availability, then generate a plan. Unknown information stays unknown.":
    [
      "Проверьте задания и доступное время, затем постройте план. Неизвестные сведения остаются неизвестными.",
      "Тапсырмалар мен бос уақытты тексеріп, жоспар құрыңыз. Белгісіз деректер белгісіз болып қалады.",
    ],
  "No requirements assessed. Add and review cited rubric requirements before judging readiness.":
    [
      "Требования не оценены. Добавьте и проверьте критерии с цитатами, прежде чем судить о готовности.",
      "Талаптар бағаланбады. Дайындық туралы қорытынды жасамас бұрын дәйексөзді өлшемдерді қосып тексеріңіз.",
    ],
  "Structural checks only. Semantic correctness still requires review.": [
    "Проверена только структура. Содержательная правильность требует проверки.",
    "Тек құрылым тексерілді. Мазмұн дұрыстығын әлі тексеру керек.",
  ],
  "Choose PDF, Markdown, TXT or ICS up to 2 MiB.": [
    "Выберите PDF, Markdown, TXT или ICS до 2 МиБ.",
    "2 МиБ-қа дейінгі PDF, Markdown, TXT немесе ICS таңдаңыз.",
  ],
  "Previous week": ["Предыдущая неделя", "Алдыңғы апта"],
  "Next week": ["Следующая неделя", "Келесі апта"],
  "Server polling works while the free service is awake. Shared public observations keep their original fetch time. Sleeping or restarting hosting stops polling; no always-on guarantee.":
    [
      "Сервер проверяет изменения, пока бесплатный сервис активен. Общие наблюдения сохраняют исходное время получения. Сон или перезапуск хостинга останавливает проверку; круглосуточная работа не гарантируется.",
      "Тегін сервис белсенді болғанда сервер өзгерістерді тексереді. Ортақ бақылаулар бастапқы алынған уақытын сақтайды. Хостинг ұйқыға кетсе не қайта іске қосылса, тексеру тоқтайды; үздіксіз жұмысқа кепілдік жоқ.",
    ],
  "Create a separate study calendar": [
    "Создать отдельный учебный календарь",
    "Бөлек оқу күнтізбесін жасау",
  ],
  "Disconnect Calendar": ["Отключить Calendar", "Calendar байланысын үзу"],
  "Calendar connection is optional. Consent does not authorize study writes. Create or choose a separate calendar, then review and approve exact actions. Disconnect preserves existing events.":
    [
      "Calendar подключается по желанию. Согласие не разрешает запись учебных блоков. Создайте или выберите отдельный календарь, затем проверьте и одобрите точные действия. Отключение сохраняет существующие события.",
      "Calendar қосылымы міндетті емес. Келісім оқу блоктарын жазуға рұқсат бермейді. Бөлек күнтізбені жасап не таңдап, нақты әрекеттерді тексеріп растаңыз. Байланысты үзу бар оқиғаларды сақтайды.",
    ],
  "Document review": ["Разбор документов", "Құжаттарды талдау"],
  "Review one assignment": [
    "Проверка одного задания",
    "Бір тапсырманы тексеру",
  ],
  "Missing information stays unknown. Any correction is recorded as your interpretation; original quotations stay unchanged.":
    [
      "Недостающие сведения остаются неизвестными. Исправления записываются как ваша интерпретация; исходные цитаты сохраняются.",
      "Жетіспейтін деректер белгісіз болып қалады. Түзетулер сіздің түсіндіруіңіз ретінде жазылады; бастапқы дәйексөздер сақталады.",
    ],
  "Assignment title": ["Название задания", "Тапсырма атауы"],
  Course: ["Курс", "Пән"],
  "Academic term": ["Учебный семестр", "Оқу семестрі"],
  "Assignment key": ["Код задания", "Тапсырма коды"],
  "Exact effort in minutes": [
    "Точная оценка в минутах",
    "Минутпен берілген нақты бағалау",
  ],
  "Deadline in workspace timezone": [
    "Срок в часовом поясе рабочей области",
    "Жұмыс кеңістігінің уақыт белдеуіндегі мерзім",
  ],
  "Rubric items, one per line": [
    "Критерии — по одному на строку",
    "Әр жолға бір бағалау өлшемі",
  ],
  "Citations and proposed interpretations": [
    "Цитаты и предложенные интерпретации",
    "Дәйексөздер мен ұсынылған түсіндірмелер",
  ],
  "I reviewed this assignment and confirm only these fields.": [
    "Я проверил это задание и подтверждаю только эти поля.",
    "Осы тапсырманы тексердім және тек осы өрістерді растаймын.",
  ],
  "Confirm this assignment": [
    "Подтвердить это задание",
    "Осы тапсырманы растау",
  ],
  Confirmed: ["Подтверждено", "Расталды"],
  "Review extracted fields": [
    "Проверить извлечённые поля",
    "Алынған өрістерді тексеру",
  ],
  "Propose with Gemini": ["Предложить через Gemini", "Gemini арқылы ұсыну"],
  "Refresh proposals": ["Обновить предложения", "Ұсыныстарды жаңарту"],
  "Gemini proposals require free-service processing consent below. They do not change coursework until you review and confirm each assignment.":
    [
      "Для предложений Gemini подтвердите условия бесплатной обработки ниже. Задания изменятся только после вашей проверки и подтверждения каждого задания.",
      "Gemini ұсыныстары үшін төмендегі тегін өңдеу шарттарын растаңыз. Әр тапсырманы тексеріп, растағаннан кейін ғана деректер өзгереді.",
    ],
  "PDF, Markdown, TXT and ICS · maximum 2 MiB. Text PDFs only, at most 100 pages and 250,000 extracted characters. No OCR.":
    [
      "PDF, Markdown, TXT и ICS · до 2 МиБ. Только текстовые PDF: до 100 страниц и 250 000 извлечённых символов. OCR недоступен.",
      "PDF, Markdown, TXT және ICS · ең көбі 2 МиБ. Тек мәтіндік PDF: 100 бетке және 250 000 алынған таңбаға дейін. OCR жоқ.",
    ],
  "Planning context": [
    "Период и доступное время",
    "Жоспарлау кезеңі мен бос уақыт",
  ],
  "Save planning context": [
    "Сохранить период и время",
    "Кезең мен уақытты сақтау",
  ],
  "Range starts": ["Начало периода", "Кезеңнің басы"],
  "Range ends": ["Конец периода", "Кезеңнің соңы"],
  "Study starts": ["Начало занятий", "Оқудың басталуы"],
  "Study ends": ["Конец занятий", "Оқудың аяқталуы"],
  "Available weekdays": ["Доступные дни недели", "Қолжетімді апта күндері"],
  Monday: ["Понедельник", "Дүйсенбі"],
  Tuesday: ["Вторник", "Сейсенбі"],
  Wednesday: ["Среда", "Сәрсенбі"],
  Thursday: ["Четверг", "Бейсенбі"],
  Friday: ["Пятница", "Жұма"],
  Saturday: ["Суббота", "Сенбі"],
  Sunday: ["Воскресенье", "Жексенбі"],
  "A finish earlier than the start continues after midnight. Empty weekdays mean no availability. Original source deadlines are never moved.":
    [
      "Если конец раньше начала, занятие продолжается после полуночи. Без выбранных дней свободного времени нет. Сроки источников не переносятся.",
      "Аяқталу уақыты басталуынан ерте болса, оқу түн ортасынан кейін жалғасады. Күндер таңдалмаса, бос уақыт жоқ. Дереккөз мерзімдері өзгермейді.",
    ],
  "Choose your workspace": ["Выбор рабочей области", "Жұмыс кеңістігін таңдау"],
  "Example workspace": ["Область примера", "Үлгі кеңістігі"],
  "Your own documents": ["Ваши документы", "Өз құжаттарыңыз"],
  "The example and your own documents use separate workspaces. Switching preserves both until their temporary sessions expire.":
    [
      "Пример и ваши документы находятся в разных областях. Переключение сохраняет обе до истечения временных сеансов.",
      "Үлгі мен өз құжаттарыңыз бөлек кеңістіктерде. Ауысқанда екеуі де уақытша сеанстар аяқталғанша сақталады.",
    ],
  "Switch workspace": ["Переключить область", "Кеңістікті ауыстыру"],
  "Use my own data": ["Со своими данными", "Өз деректеріммен"],
  "Open example": ["Открыть пример", "Үлгіні ашу"],
  "Sample documents and instructions": [
    "Образцы документов и инструкции",
    "Құжат үлгілері мен нұсқаулық",
  ],
  "Plan scope": ["Охват плана", "Жоспар қамтуы"],
  "confirmed assignments": ["подтверждённых заданий", "расталған тапсырма"],
  "drafts excluded": ["черновиков исключено", "жоба қамтылмады"],
  "This is a partial plan. Review the excluded drafts before treating the whole workload as planned.":
    [
      "Это частичный план. Проверьте исключённые черновики, прежде чем считать всю нагрузку запланированной.",
      "Бұл ішінара жоспар. Барлық жүктеме жоспарланды деп есептемес бұрын қамтылмаған жобаларды тексеріңіз.",
    ],
};
