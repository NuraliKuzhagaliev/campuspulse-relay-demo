const native = {
  en: {
    importTitle: "Import selected academic source",
    filter: "Academic sources",
    chooseFile: "Choose PDF, Markdown, TXT or ICS up to 10 MiB.",
    watchTitle: "Select folder for opt-in, non-recursive source watching",
    chooseFolder: "Choose an existing folder on D:.",
    changed: (name) => `${name} changed. Review and import it explicitly.`,
    open: "Open CampusPulse RELAY",
    quit: "Quit",
  },
  ru: {
    importTitle: "Импорт выбранного учебного источника",
    filter: "Учебные источники",
    chooseFile: "Выберите PDF, Markdown, TXT или ICS до 10 МиБ.",
    watchTitle: "Выберите папку для явного наблюдения без вложенных папок",
    chooseFolder: "Выберите существующую папку на D:.",
    changed: (name) =>
      `${name}: файл изменён. Проверьте и импортируйте его явно.`,
    open: "Открыть CampusPulse RELAY",
    quit: "Выйти",
  },
  kk: {
    importTitle: "Таңдалған оқу дереккөзін импорттау",
    filter: "Оқу дереккөздері",
    chooseFile: "10 МиБ-қа дейінгі PDF, Markdown, TXT немесе ICS таңдаңыз.",
    watchTitle: "Ішкі қалталарсыз ерікті бақылау үшін қалтаны таңдаңыз",
    chooseFolder: "D: дискісіндегі бар қалтаны таңдаңыз.",
    changed: (name) =>
      `${name}: файл өзгерді. Оны тексеріп, нақты импорттаңыз.`,
    open: "CampusPulse RELAY ашу",
    quit: "Шығу",
  },
};
module.exports = native;
