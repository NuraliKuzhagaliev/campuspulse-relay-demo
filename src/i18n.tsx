import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { translations, type Language } from "./translations";

export const locales = { en: "en-GB", ru: "ru-RU", kk: "kk-KZ" } as const;
const weekdays = {
  en: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
  ru: ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
  kk: ["Жс", "Дс", "Сс", "Ср", "Бс", "Жм", "Сб"],
};
const months = {
  en: [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ],
  ru: [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
  ],
  kk: [
    "қаңтар",
    "ақпан",
    "наурыз",
    "сәуір",
    "мамыр",
    "маусым",
    "шілде",
    "тамыз",
    "қыркүйек",
    "қазан",
    "қараша",
    "желтоқсан",
  ],
};
export function weekdayText(date: Date, language: Language) {
  return weekdays[language][date.getUTCDay()];
}
const standaloneRussianMonths = [
  "январь",
  "февраль",
  "март",
  "апрель",
  "май",
  "июнь",
  "июль",
  "август",
  "сентябрь",
  "октябрь",
  "ноябрь",
  "декабрь",
];
export function calendarMonthName(month: number, language: Language) {
  return language === "ru"
    ? standaloneRussianMonths[month]
    : months[language][month];
}
export function calendarDateLabel(date: Date, language: Language) {
  const day = translate(
    [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ][date.getUTCDay()],
    language,
  );
  return `${day}, ${date.getUTCDate()} ${months[language][date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}
export function weekRange(start: Date, end: Date, language: Language) {
  if (start.getUTCMonth() === end.getUTCMonth())
    return `${start.getUTCDate()}–${end.getUTCDate()} ${months[language][start.getUTCMonth()]}`;
  return `${start.getUTCDate()} ${months[language][start.getUTCMonth()]} – ${end.getUTCDate()} ${months[language][end.getUTCMonth()]}`;
}
export function deadlineText(
  value: string,
  language: Language,
  timezone: string,
) {
  const date = new Date(value);
  const key = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    timeZone: timezone,
  }).format(date);
  const day = weekdays[language][weekdays.en.indexOf(key)];
  const clock = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone: timezone,
  }).format(date);
  return `${day} ${clock}`;
}
const canonical = new Map<string, string>();
for (const [key, values] of Object.entries(translations)) {
  canonical.set(key, key);
  for (const value of values) canonical.set(value, key);
}
export function translate(
  text: string,
  language: Language,
  values: Record<string, string | number> = {},
): string {
  const key = canonical.get(text) || text;
  const row = translations[key as keyof typeof translations];
  const result =
    language === "en" || !row ? key : row[language === "ru" ? 0 : 1];
  return result.replace(/\{(\w+)\}/g, (match, name) =>
    String(values[name] ?? match),
  );
}
const labelKeys: Record<string, string> = {
  illustrative: "Illustrative",
  complete: "Complete",
  cancelled: "Cancelled",
  needs_review: "Needs review",
  missing: "Missing",
  run_partial: "Partial",
  run_unknown: "Unknown",
  run_cancelled: "Cancelled",
  selected_upload: "Selected upload",
  imported_snapshot: "Imported snapshot",
  implemented_local: "Locally implemented",
  live: "Live",
  judge: "Judge demo",
  personal: "Personal workspace",
  explicit: "Explicit",
  observed: "Observed",
  unknown: "Unknown",
  confirmed: "Confirmed",
  conflict: "Conflicting",
  planned: "Planned",
  worked_on: "Worked on",
  self_reported: "Self-reported",
  externally_observed: "Externally observed",
  run_started: "Run started",
  run_queued: "Question queued",
  queued: "Question queued",
  quota_wait: "Waiting for API quota",
  run_completed: "Run completed",
  run_failed: "Run failed",
  tool_started: "Tool started",
  tool_finished: "Tool finished",
  tool_failed: "Tool failed",
  model_call_reserved: "Model allowance reserved",
  model_usage: "Observed model usage",
  get_progress_summary: "Read work progress",
  recommend_clarification: "Compare clarification impact",
  observe_handoff_gate: "Observe handoff gate",
  source_conflict: "Source conflict",
  plan_validated: "Plan validated",
  approval_required: "Approval required",
  action_applied: "Action applied",
  action_verified: "Action verified",
  decision_summary: "Decision summary",
  verified: "Verified",
  partial: "Partial",
  deleted: "Deleted",
  preserved: "Preserved",
  pending: "Pending",
  skipped: "Skipped",
  mismatch: "Mismatch",
  not_found: "Not found",
  failed: "Failed",
  OPTIMAL: "Optimal",
  FEASIBLE: "Feasible",
  INFEASIBLE: "Infeasible",
  UNKNOWN: "Unknown",
  MODEL_INVALID: "Invalid model",
  create: "Create",
  keep: "Keep",
  delete: "Remove",
  minutes: "Estimated effort",
  due: "Confirmed deadline",
  completion: "Progress",
  supports: "Supports",
  retained: "Retained",
  removed: "Removed",
  unchanged: "Unchanged",
  live_github: "Live GitHub",
  list_course_sources: "List course sources",
  read_course_source: "Read course source",
  get_assignment_repo_status: "Check repository status",
  read_assignment_repo_file: "Read repository file",
  get_calendar_window: "Read calendar window",
  get_workspace_plan_inputs: "Read planning inputs",
  preview_study_blocks: "Preview study blocks",
  apply_approved_study_blocks: "Apply approved blocks",
  verify_study_blocks: "Verify study blocks",
  undo_owned_study_blocks: "Undo owned blocks",
  build_next_action_packet: "Build study packet",
  save_validated_plan: "Save validated plan",
  build_recovery_plan: "Build recovery plan",
  compare_plan_scenarios: "Compare plan scenarios",
};
export function label(value: string, language: Language) {
  return translate(labelKeys[value] || value, language);
}
const patterns: [RegExp, string, string[]][] = [
  [
    /^(\d+) minutes remain unscheduled\.$/,
    "{count} minutes remain unscheduled.",
    ["count"],
  ],
  [
    /^(\d+) minutes remain unscheduled before its hard deadline\.$/,
    "{count} minutes remain unscheduled before its hard deadline.",
    ["count"],
  ],
  [/^(\d+) events observed\.$/, "{count} events observed.", ["count"]],
  [/^(\d+) minutes estimated$/, "{count} minutes estimated", ["count"]],
  [
    /^(\d+) selected-folder file change\(s\) detected\. Use Import to review and upload explicitly\.$/,
    "{count} selected-folder file change(s) detected. Use Import to review and upload explicitly.",
    ["count"],
  ],
  [
    /^Open the cited requirement and draft: (.*)$/s,
    "Open the cited requirement and draft: {requirement}",
    ["requirement"],
  ],
  [/^Study · (.*)$/s, "Study · {title}", ["title"]],
  [/^Calling (.*)\.$/, "Calling {tool}.", ["tool"]],
];
export function operational(
  value: string | undefined,
  language: Language,
): string {
  if (!value) return "";
  if (canonical.has(value)) return translate(value, language);
  for (const [pattern, key, names] of patterns) {
    const match = value.match(pattern);
    if (match)
      return translate(
        key,
        language,
        Object.fromEntries(names.map((name, i) => [name, match[i + 1]])),
      );
  }
  return label(value, language); // Original source text and unknown external diagnostics remain verbatim.
}
export function eventSummary(
  event: { type: string; summary?: string; code?: string },
  language: Language,
) {
  if (event.type === "action_applied") return event.summary || ""; // Exact event title is observed data.
  return event.code
    ? errorMessage(`${event.code}: ${event.summary || ""}`, language)
    : operational(event.summary, language);
}
const errorKeys: Record<string, string> = {
  STALE_REVISION:
    "This workspace changed elsewhere. Refresh, review the latest values and retry.",
  IDEMPOTENCY_CONFLICT:
    "This workspace changed elsewhere. Refresh, review the latest values and retry.",
  PASSPORT_INVALID:
    "The portable file is invalid or unsupported. Your current workspace is unchanged.",
  PASSPORT_VERSION:
    "The portable file is invalid or unsupported. Your current workspace is unchanged.",
  PASSPORT_REFERENCES:
    "The portable file is invalid or unsupported. Your current workspace is unchanged.",
  PASSPORT_CHECKSUM:
    "The portable file is invalid or unsupported. Your current workspace is unchanged.",
  PASSPORT_TOO_LARGE:
    "The portable file exceeds 2 MiB. Select fewer sources; nothing was truncated.",
  LEGACY_SNAPSHOT_MISSING_EXTRACTS:
    "Legacy snapshots omit source pages. Re-import original documents; this file cannot restore cited coursework.",
  SESSION_ACTIVE:
    "This timer was changed or stopped elsewhere. Refresh and recover the recorded duration.",
  SESSION_CLOSED:
    "This timer was changed or stopped elsewhere. Refresh and recover the recorded duration.",
  USE_PROGRESS:
    "This workspace changed elsewhere. Refresh, review the latest values and retry.",
  PR_NOT_FOUND:
    "The external service could not be reached. Reconnect and retry; no success is assumed.",
  BUSY: "A bounded comparison is already running. Cancel it or retry when it settles.",
  CANCELLED: "Comparison cancelled. The accepted plan is unchanged.",
  FEATURE_PENDING:
    "Sign in or reconnect the required service, then retry. Cloud acceptance remains pending.",
  PROCESSING_CONSENT_REQUIRED:
    "Confirm adult access and permitted non-sensitive processing before using free Gemini.",
  AUTH_REQUIRED:
    "The workspace or integration session expired. Start a workspace or reconnect that integration. Restore coursework from a saved Passport; previous approvals are never replayed.",
  UNSUPPORTED_TIMEZONE:
    "Choose Kazakhstan (UTC+05:00), Moscow (UTC+03:00), or UTC.",
  TOOL_INPUT_INVALID:
    "The tool input was rejected. Review the source and the indicated fields; no rejected proposal was applied.",
  TOOL_EXECUTION_FAILED:
    "The tool could not complete. Inspect the operation before retrying; no success is assumed.",
  ACCESS_DENIED:
    "This action is unavailable in this workspace. Check the selected resource and access.",
  EMPTY_CONTENT:
    "The selected document has no readable content. Export a non-empty text document and retry.",
  AMBIGUOUS_TIME:
    "This local time is ambiguous or invalid. Choose an unambiguous time in the workspace timezone.",
  AVAILABILITY_REQUIRED:
    "Add study availability in Planning context before generating a plan.",
  UPSTREAM_RATE_LIMITED:
    "The service request allowance is exhausted. Wait for its reset before retrying.",
  UPSTREAM_UNAVAILABLE:
    "The external service could not be reached. Reconnect and retry; no success is assumed.",
  AGENT_STEP_LIMIT:
    "The tool-step limit was reached. No final AI answer was produced. Review saved document proposals before retrying.",
  PARSE_FAILED:
    "The source or structured input could not be read. Check its format, dates and required fields.",
  UNSUPPORTED_INPUT:
    "Choose a supported text PDF, Markdown, TXT or ICS within the displayed limits.",
  INFEASIBLE:
    "The work does not fit before its deadlines. Review availability and effort explicitly.",
  SOURCE_CONFLICT:
    "Evidence or an event changed. Review the current sources before planning or approving.",
  STALE_PLAN:
    "The plan or approval is outdated. Refresh, repair and review a new exact preview.",
  APPROVAL_REQUIRED:
    "Review and approve the exact current preview before any calendar changes.",
  PARTIAL_APPLY:
    "Some operations need reconciliation. Inspect the receipt before retrying.",
  REQUEST_FAILED:
    "The action could not be completed. Check the connection and retry.",
};
export function errorMessage(raw: string, language: Language) {
  const code = Object.keys(errorKeys).find((key) => raw.includes(key));
  const exact = [...canonical.keys()]
    .filter((text) => text.length > 20 && raw.includes(text))
    .sort((a, b) => b.length - a.length)[0];
  return (
    translate(
      exact || (code ? errorKeys[code] : errorKeys.REQUEST_FAILED),
      language,
    ) + (code ? ` (${code})` : "")
  );
}
export function formatDuration(minutes: number, language: Language): string {
  const hours = Math.floor(minutes / 60),
    remainder = minutes % 60;
  const unit =
    language === "en"
      ? ["h", "m"]
      : language === "ru"
        ? ["ч", "мин"]
        : ["сағ", "мин"];
  return hours
    ? `${hours}${language === "en" ? "" : " "}${unit[0]}${remainder ? ` ${remainder}${language === "en" ? "" : " "}${unit[1]}` : ""}`
    : `${minutes}${language === "en" ? "" : " "}${unit[1]}`;
}
type LocaleValue = {
  lang: Language;
  setLang: (language: Language) => void;
  locale: string;
  tr: (text: string, values?: Record<string, string | number>) => string;
};
const Context = createContext<LocaleValue | null>(null);
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>(() => {
    const saved = localStorage.getItem("relay.language");
    return saved === "ru" || saved === "kk" ? saved : "en";
  });
  useEffect(() => {
    document.documentElement.lang = lang;
    localStorage.setItem("relay.language", lang);
    void window.relay?.setLanguage?.(lang).catch(() => undefined);
  }, [lang]);
  return (
    <Context.Provider
      value={{
        lang,
        setLang,
        locale: locales[lang],
        tr: (text, values) => translate(text, lang, values),
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useLocale() {
  const value = useContext(Context);
  if (!value) throw new Error("LocaleProvider is required.");
  return value;
}
