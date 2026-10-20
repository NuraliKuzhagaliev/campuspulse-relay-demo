# Own uncertainty checks / Проверка неизвестных и противоречий / Белгісіздік пен қайшылықты тексеру

These synthetic documents were written for the 0.5.1 public UI acceptance, not embedded as expected answers in application code. No AI call was used in these deterministic uncertainty checks. The separate five-prose/PDF batch uses real Gemini/MCP.

EN: Import unknown-en/ru/kk independently. Review and confirm while leaving effort and deadline blank. Refresh: both must remain unknown. In a separate own workspace import conflict-a and conflict-b, confirm each, inspect two quoted deadlines, explicitly choose one and refresh: both source facts remain, the choice persists.

RU: unknown-en/ru/kk проверяются по отдельности: подтвердите задание с пустыми сроком и длительностью. После обновления значения должны остаться неизвестными. В отдельном пространстве импортируйте conflict-a и conflict-b, подтвердите каждое, сравните цитаты и выберите срок. Обе цитаты должны сохраниться после обновления.

KK: unknown-en/ru/kk файлдарын жеке тексеріңіз. Мерзім мен ұзақтықты бос қалдырып, тапсырманы растаңыз. Бетті жаңартқаннан кейін олар белгісіз болып қалуы керек. Бөлек кеңістікте conflict-a және conflict-b файлдарын импорттап, әрқайсын растаңыз, дәйексөздерді салыстырып, мерзімді таңдаңыз. Жаңартудан кейін екі дерек те сақталуы керек.

Expected: one task per independent missing-data input, due=null/minutes=null. Conflicting pair: one canonical assignment, two source versions with distinct due facts, explicit resolution, exact45minutes/solver60. No calendar approval or Google connection needed. Original13-file public pack remains at https://campuspulse-relay-demo.onrender.com/samples/ .
