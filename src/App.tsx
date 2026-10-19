import { useEffect, useRef, useState, type ReactNode } from "react";
import { LiveAccess } from "./LiveAccess";
import {
  Activity,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  Check,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Command,
  Download,
  FileText,
  FolderOpen,
  GitBranch,
  Globe2,
  Link2,
  LoaderCircle,
  LockKeyhole,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Undo2,
  Upload,
  WifiOff,
  X,
  Zap,
} from "lucide-react";
import { api, setCsrf } from "./api";
import { importSelectedSource } from "./imports";
import { Workshop } from "./Workshop";
import { Continuity } from "./Continuity";
import { DocumentReview, PlanningContext } from "./DocumentReview";
import { Timeline } from "./Timeline";
import { version as releaseVersion } from "../package.json";
import {
  useLocale,
  operational,
  eventSummary,
  weekdayText,
  weekRange,
  deadlineText,
  label,
  errorMessage,
  formatDuration,
} from "./i18n";
import type {
  Snapshot,
  Fact,
  Source,
  Task,
  Plan,
  RunEvent,
  Preview,
  Packet,
  Block,
} from "./types";

const langs = {
  en: {
    week: "My week",
    evidence: "Evidence",
    recovery: "Recovery",
    activity: "Activity",
    connections: "Connections",
    challenge: "Judge challenge",
    headline: "Your week.",
    balance: "Back in balance.",
    repair: "Repair my week",
    sub: "See what changed. Know what to do next.",
    conflict: "A deadline changed. Let’s check the evidence.",
    review: "Review evidence",
    timeline: "A little structure. A lot more clarity.",
    study: "Study window",
    next: "Your next moves",
    assistant: "Ask RELAY",
    placeholder: "What changed in my week?",
    inspector: "Execution inspector",
    offline: "Cached offline view — live facts and writes unavailable.",
  },
  ru: {
    week: "Моя неделя",
    evidence: "Источники",
    recovery: "Новый план",
    activity: "Действия",
    connections: "Подключения",
    challenge: "Испытание для жюри",
    headline: "Ваша неделя.",
    balance: "Снова в балансе.",
    repair: "Перестроить неделю",
    sub: "Что изменилось. Что делать дальше.",
    conflict: "Срок изменился. Проверим источники.",
    review: "Проверить источники",
    timeline: "Ясный план на вашу неделю.",
    study: "Время для учёбы",
    next: "Следующие шаги",
    assistant: "Спросить RELAY",
    placeholder: "Что изменилось в моей неделе?",
    inspector: "Инспектор выполнения",
    offline: "Сохранённый план — нет свежих данных и внешних действий.",
  },
  kk: {
    week: "Менің аптам",
    evidence: "Дереккөздер",
    recovery: "Жаңа жоспар",
    activity: "Әрекеттер",
    connections: "Қосылымдар",
    challenge: "Қазылар сынағы",
    headline: "Сіздің аптаңыз.",
    balance: "Қайта теңгерімде.",
    repair: "Аптаны қайта жоспарлау",
    sub: "Не өзгерді. Әрі қарай не істеу керек.",
    conflict: "Мерзім өзгерді. Дереккөздерді тексерейік.",
    review: "Дереккөздерді қарау",
    timeline: "Аптаңызға арналған түсінікті жоспар.",
    study: "Оқу уақыты",
    next: "Келесі қадамдар",
    assistant: "RELAY-ден сұрау",
    placeholder: "Менің аптамда не өзгерді?",
    inspector: "Орындалу инспекторы",
    offline: "Сақталған жоспар — жаңа деректер мен сыртқы әрекеттер жоқ.",
  },
};
type View =
  | "week"
  | "evidence"
  | "recovery"
  | "activity"
  | "connections"
  | "challenge";
type Lang = keyof typeof langs;
const CONTACTING_AGENT = "Contacting remote agent";
type ChatReply = {
  text: string;
  status: string;
  reason?: string;
  code?: string;
  run_id?: string;
  conversation_id?: string;
  position?: number;
  poll_after_ms?: number;
  quota?: { wait_seconds: number; reason?: string; reset_at?: number };
};
const icons = {
  week: CalendarDays,
  evidence: BookOpen,
  recovery: Zap,
  activity: Activity,
  connections: Link2,
  challenge: ShieldCheck,
};

const shortHash = (s: string) => s.slice(0, 8);
function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const { tr, lang, locale } = useLocale();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = ref.current;
    el?.showModal();
    return () => el?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className={wide ? "modal wide" : "modal"}
      onCancel={onClose}
    >
      <header className="modal-head">
        <div>
          <span className="eyebrow">CAMPUSPULSE RELAY</span>
          <h2>{title}</h2>
        </div>
        <button
          className="icon-button"
          aria-label={tr("Close dialog")}
          onClick={onClose}
        >
          <X size={21} />
        </button>
      </header>
      {children}
    </dialog>
  );
}
function StatusPill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <span className={`pill ${tone}`}>
      <i />
      {children}
    </span>
  );
}
function SourceFact({
  fact,
  source,
  onOpen,
}: {
  fact: Fact;
  source?: Source;
  onOpen: (id: string, page?: number) => void;
}) {
  const { tr, lang, locale } = useLocale();
  return (
    <div className="fact">
      <div className="between">
        <span className="eyebrow">{source?.title || fact.source_id}</span>
        <span className="mono">v.{shortHash(fact.source_version)}</span>
      </div>
      <p className="fact-date">
        {fact.value
          ? String(fact.value).replace("T", " · ")
          : tr("Unknown / needs clarification")}
      </p>
      <blockquote>{fact.quote}</blockquote>
      <button
        className="text-button"
        onClick={() => onOpen(fact.source_id, fact.page)}
      >
        <FileText size={14} />
        {tr("Page")} {fact.page}
        <ArrowUpRight size={14} />
      </button>
      <small>
        {tr("Original evidence ·")} {fact.timezone} · {label(fact.kind, lang)}
      </small>
    </div>
  );
}
function RunRail({
  events,
  resource,
  close,
}: {
  events: RunEvent[];
  resource: string | null;
  close: () => void;
}) {
  const { tr, lang, locale } = useLocale();
  const recent = events.slice(-9).reverse();
  return (
    <aside className="run-rail">
      <div className="between">
        <span className="eyebrow light">
          <Radio size={14} />
          {tr("EXECUTION")}
        </span>
        <button
          className="icon-button light"
          aria-label={tr("Close inspector")}
          onClick={close}
        >
          <PanelRightClose size={17} />
        </button>
      </div>
      <h2>
        {tr("Clarity at")}
        <br />
        {tr("every step.")}
      </h2>
      <p className="rail-intro">
        {tr("Actual operations, observations")}
        <br />
        {tr("and outcomes from this workspace.")}
      </p>
      <div className="resource-state">
        <span className="status-dot" />
        {resource?.startsWith("gemini-developer:")
          ? tr("Gemini · alternative host")
          : resource
            ? tr("Managed resource configured")
            : tr("Agent Engine not connected")}
      </div>
      <div
        className="run-events"
        role="region"
        aria-label={tr("Execution events")}
        tabIndex={0}
        aria-live="polite"
      >
        {recent.map((e) => (
          <div className="run-event" key={e.sequence}>
            <span
              className={`event-dot ${e.type.includes("failed") ? "failed" : ""}`}
            >
              {e.type.includes("failed") ? (
                <X size={11} />
              ) : e.type.includes("started") ? (
                <ArrowRight size={11} />
              ) : (
                <Check size={11} />
              )}
            </span>
            <span className="event-type">{label(e.tool || e.type, lang)}</span>
            <p>{eventSummary(e, lang)}</p>
            <small>
              {new Date(e.timestamp).toLocaleTimeString(locale, {
                hour: "2-digit",
                minute: "2-digit",
              })}
              {e.duration_ms !== undefined
                ? ` · ${tr("{value} ms", { value: e.duration_ms })}`
                : ""}
              {e.mode ? ` · ${label(e.mode, lang)}` : ""}
            </small>
          </div>
        ))}
      </div>
      <div className="rail-foot">
        <ShieldCheck size={17} />
        <p>
          {tr("Plans are proposals.")}
          <br />
          <strong>{tr("You approve every external write.")}</strong>
        </p>
      </div>
    </aside>
  );
}

export default function App() {
  const [calendars, setCalendars] = useState<
    { id: string; name: string; role: string; primary: boolean }[]
  >([]);
  const { lang, setLang, tr, locale } = useLocale();
  const duration = (minutes: number) => formatDuration(minutes, lang);
  const t = langs[lang];
  const [data, setData] = useState<Snapshot | null>(null),
    [view, setView] = useState<View>("week"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(""),
    [offline, setOffline] = useState(false),
    [rail, setRail] = useState(true),
    [list, setList] = useState(false),
    [entry, setEntry] = useState(false),
    [commands, setCommands] = useState(false);
  const [source, setSource] = useState<Source | null>(null),
    [page, setPage] = useState(1),
    [packet, setPacket] = useState<Packet | null>(null),
    [preview, setPreview] = useState<Preview | null>(null),
    [scenario, setScenario] = useState<Plan | null>(null),
    [prompt, setPrompt] = useState(""),
    [answer, setAnswer] = useState(""),
    [notice, setNotice] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const [processingWorkspace, setProcessingWorkspace] = useState<string | null>(
    null,
  );
  const [queuedQuestion, setQueuedQuestion] = useState<ChatReply | null>(null);
  const processingConsent =
    !!data?.workspace_id && processingWorkspace === data.workspace_id;
  const ready = useRef(false);
  const workLock = useRef(false);
  const workGeneration = useRef(0);
  const chatGeneration = useRef(0);
  const conversationId = useRef<string | null>(null);
  const tenantRef = useRef<string | null>(
    localStorage.getItem("relay.lastTenant"),
  );
  const eventCursor = useRef(0);
  async function refresh() {
    const s = await api<Snapshot>("/state");
    if (
      s.workspace_id &&
      tenantRef.current &&
      s.workspace_id !== tenantRef.current
    ) {
      setSource(null);
      setPacket(null);
      setPreview(null);
      setScenario(null);
      setAnswer("");
      setQueuedQuestion(null);
      chatGeneration.current++;
      setPrompt("");
      setNotice("");
      setCalendars([]);
      conversationId.current = null;
    }
    setData(s);
    eventCursor.current = s.events.at(-1)?.sequence || 0;
    setOffline(false);
    tenantRef.current = s.workspace_id || tenantRef.current;
    localStorage.setItem("relay.lastTenant", tenantRef.current || "");
    if (s.demo?.public) {
      localStorage.setItem("relay.publicDemo", "1");
      localStorage.removeItem("relay.snapshot.v1:" + tenantRef.current);
    } else
      localStorage.setItem(
        "relay.snapshot.v1:" + tenantRef.current,
        JSON.stringify(s),
      );
    if (window.relay) await window.relay.saveSnapshot(s);
    return s;
  }
  async function work(
    label: string,
    fn: () => Promise<void>,
    allowOffline = false,
  ) {
    if (offline && !allowOffline) {
      setError(t.offline);
      return;
    }
    if (workLock.current) return;
    workLock.current = true;
    const generation = ++workGeneration.current;
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      if (generation === workGeneration.current) {
        workLock.current = false;
        setBusy("");
      }
    }
  }
  async function followQuestion(initial: ChatReply, generation: number) {
    let result = initial;
    while (
      ["queued", "running", "quota_wait", "cancel_requested"].includes(
        result.status,
      )
    ) {
      if (generation !== chatGeneration.current) return;
      setQueuedQuestion(result);
      await new Promise((resolve) =>
        setTimeout(resolve, result.poll_after_ms || 3000),
      );
      if (generation !== chatGeneration.current) return;
      result = await api<ChatReply>("/runs/" + result.run_id);
    }
    if (generation !== chatGeneration.current) return;
    setQueuedQuestion(null);
    setAnswer(
      result.text ||
        (result.code
          ? errorMessage(result.code, lang)
          : tr("No usable final answer. Review the outcome before retrying.")),
    );
    setNotice(tr("Agent outcome") + ": " + label(result.status, lang));
    await refresh();
  }
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const session = await api<{ csrf: string; tenant: string }>("/session");
        setCsrf(session.csrf);
        tenantRef.current = session.tenant;
        if (cancelled) return;
        const initial = await refresh();
        ready.current = true;
        if (
          initial.settings.mode === "illustrative" &&
          !sessionStorage.getItem("relay.entered") &&
          !initial.agent.public_access
        )
          setEntry(true);
        if (initial.agent.public_access) {
          const c = await api<{
            id: string;
            active_run?: string;
            turns: { assistant: string }[];
          }>("/conversation");
          if (cancelled) return;
          conversationId.current = c.id;
          if (c.active_run) {
            const run = await api<ChatReply>("/runs/" + c.active_run);
            const generation = ++chatGeneration.current;
            void work(CONTACTING_AGENT, () => followQuestion(run, generation));
          } else if (c.turns.at(-1)?.assistant)
            setAnswer(c.turns.at(-1)!.assistant);
        }
      } catch (e) {
        const authFailed =
          (e as { status?: number }).status === 401 ||
          String(e).includes("AUTH_REQUIRED");
        const cached =
          authFailed || localStorage.getItem("relay.publicDemo") === "1"
            ? null
            : window.relay
              ? await window.relay.loadSnapshot(tenantRef.current)
              : JSON.parse(
                  localStorage.getItem(
                    "relay.snapshot.v1:" + tenantRef.current,
                  ) || "null",
                );
        if (cached) {
          setData(cached);
          setOffline(true);
        }
        setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
      chatGeneration.current++;
    };
  }, []);
  useEffect(() => {
    let polling = false,
      retired = false;
    const timer = setInterval(
      async () => {
        if (!ready.current || document.hidden || offline || polling || retired)
          return;
        polling = true;
        const requestedTenant = tenantRef.current;
        try {
          const events = await api<{
            workspace_id?: string;
            events: RunEvent[];
          }>("/events?after=" + eventCursor.current);
          if (retired || requestedTenant !== tenantRef.current) return;
          if (
            events.workspace_id &&
            events.workspace_id !== tenantRef.current
          ) {
            const session = await api<{ csrf: string }>("/session");
            setCsrf(session.csrf);
            await refresh();
            return;
          }
          if (events.events.length) {
            eventCursor.current = Math.max(
              eventCursor.current,
              events.events.at(-1)!.sequence,
            );
            setData((d) =>
              d
                ? {
                    ...d,
                    events: Array.from(
                      new Map(
                        [...d.events, ...events.events].map((e) => [
                          e.sequence,
                          e,
                        ]),
                      ).values(),
                    )
                      .sort((a, b) => a.sequence - b.sequence)
                      .slice(-500),
                  }
                : d,
            );
          }
        } catch {
          if (!retired && requestedTenant === tenantRef.current)
            setOffline(true);
        } finally {
          polling = false;
        }
      },
      busy ? 1000 : 3000,
    );
    return () => {
      retired = true;
      clearInterval(timer);
    };
  }, [offline, busy]);
  useEffect(() => {
    function key(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommands((v) => !v);
      }
    }
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);
  useEffect(() => {
    if (!window.relay) return;
    return window.relay.onFiles((files) => {
      setNotice(
        `${files.length} selected-folder file change(s) detected. Use Import to review and upload explicitly.`,
      );
    });
  }, []);
  async function openSource(id: string, p = 1) {
    await work("Opening evidence", async () => {
      setSource(await api<Source>("/sources/" + id));
      setPage(p);
    });
  }
  async function openPacket(id: string) {
    await work("Opening study packet", async () =>
      setPacket(await api<Packet>("/packets/" + id)),
    );
  }
  async function repair() {
    await work(t.repair, async () => {
      const p = await api<Plan>("/plan", "POST");
      setScenario(null);
      await refresh();
      setNotice(
        p.feasible
          ? "Your week is ready for review. No external changes made."
          : `${p.unscheduled_minutes} minutes remain unscheduled.`,
      );
      if (window.relay)
        await window.relay.notify(
          "CampusPulse RELAY",
          p.feasible
            ? "Your recovery plan is ready to review."
            : "Your plan needs more available time.",
        );
    });
  }
  async function importFile(file?: File) {
    await work("Importing selected file", async () => {
      if (!(await importSelectedSource(file))) return;
      await refresh();
      setView("evidence");
      setNotice(
        "Source imported. Review facts and explicit gaps before planning.",
      );
    });
  }
  async function connectGoogle() {
    setBusy("Complete Google consent in your system browser");
    setError("");
    try {
      if (window.relay) {
        await window.relay.connectGoogle();
        location.reload();
      } else {
        const result = await api<{ url: string }>("/auth/start");
        location.assign(result.url);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function ask(message = prompt) {
    if (!message.trim()) return;
    const generation = ++chatGeneration.current;
    await work(CONTACTING_AGENT, async () => {
      if (!conversationId.current)
        conversationId.current = (
          await api<{ id: string }>("/conversation")
        ).id;
      const r = await api<ChatReply>("/chat", "POST", {
        message,
        language: lang,
        conversation_id: conversationId.current,
        request_id: crypto.randomUUID().replaceAll("-", ""),
        adult_confirmed: processingConsent,
        permitted_processing: processingConsent,
        processing_region: processingConsent
          ? data?.agent.public_access
            ? "supported_non_eea"
            : "KZ"
          : null,
      });
      if (generation !== chatGeneration.current) return;
      setPrompt("");
      await followQuestion(r, generation);
    });
  }
  if (!data)
    return (
      <main className="boot">
        <div className="brand-symbol">
          R<span>/</span>
        </div>
        <h1>CampusPulse RELAY</h1>
        <select
          data-testid="boot-language"
          aria-label={tr("Language")}
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
        >
          <option value="en">English</option>
          <option value="ru">Русский</option>
          <option value="kk">Қазақша</option>
        </select>
        {error ? (
          <>
            <p role="alert">{errorMessage(error, lang)}</p>
            <details className="diagnostic">
              <summary>{tr("Original diagnostic")}</summary>
              <code>{error}</code>
            </details>
            <button className="primary" onClick={() => location.reload()}>
              <RefreshCw size={16} />
              {tr("Retry connection")}
            </button>
            <p>{tr('Public AI access needs no sign-in or invitation. Retry the connection; Calendar consent is a separate optional action in Connections.')}</p>
            <p>
              {tr(
                "Start the local gateway with scripts/dev.ps1, or configure the deployed gateway.",
              )}
            </p>
          </>
        ) : (
          <>
            <LoaderCircle className="spin" />
            <p>{tr("Opening your workspace…")}</p>
          </>
        )}
      </main>
    );
  const unresolved = data.conflicts.filter((c) => c.status === "unresolved");
  const activePlan = scenario || data.plan;
  const current = activePlan && !activePlan.invalidated;
  const sourceById = (id: string) => data.sources.find((s) => s.id === id);
  const external = (url: string) =>
    window.relay
      ? window.relay.openExternal(url)
      : window.open(url, "_blank", "noopener,noreferrer");
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        {tr("Skip to main content")}
      </a>
      <nav className="side-nav" aria-label={tr("Main navigation")}>
        <button
          className="brand-symbol"
          title="CampusPulse RELAY"
          onClick={() => setView("week")}
        >
          R<span>/</span>
        </button>
        <div className="nav-items">
          {(Object.keys(icons) as View[]).map((v) => {
            const Icon = icons[v];
            return (
              <button
                key={v}
                className={view === v ? "nav-item selected" : "nav-item"}
                onClick={() => setView(v)}
                aria-label={t[v]}
                aria-current={view === v ? "page" : undefined}
              >
                <Icon size={21} />
                <span>{t[v]}</span>
                {v === "evidence" && unresolved.length ? (
                  <b>{unresolved.length}</b>
                ) : null}
              </button>
            );
          })}
        </div>
        <button
          className="nav-item command-button"
          onClick={() => setCommands(true)}
        >
          <Command size={19} />
          <span>⌘ / Ctrl K</span>
        </button>
        <div className="nav-foot">
          RELAY<span>{releaseVersion}</span>
        </div>
      </nav>
      <div className="workspace">
        <header className="topbar">
          <div className="wordmark">
            CampusPulse <strong>RELAY</strong>
            <span className="top-divider" />
            <span className="workspace-label">{tr("Academic workspace")}</span>
          </div>
          <div className="top-right">
            <StatusPill
              tone={
                offline
                  ? "warning"
                  : data.settings.mode === "illustrative"
                    ? "warning"
                    : "success"
              }
            >
              {offline
                ? tr("Offline snapshot")
                : data.settings.mode === "judge_ai"
                  ? tr("Private AI workspace · Calendar simulated")
                  : data.settings.mode === "illustrative"
                    ? tr("Illustrative workspace")
                    : data.settings.mode === "judge"
                      ? tr("Exclusive judge demo")
                      : tr("Connected workspace")}
            </StatusPill>
            <select
              aria-label={tr("Language")}
              data-testid="language"
              value={lang}
              onChange={(e) => setLang(e.target.value as Lang)}
            >
              <option value="en">EN</option>
              <option value="ru">RU</option>
              <option value="kk">KK</option>
            </select>
            <button
              className="avatar"
              onClick={() => setView("connections")}
              aria-label={tr("Workspace connections")}
            >
              CP
            </button>
          </div>
        </header>
        {offline ? (
          <div className="offline-banner">
            <WifiOff size={16} />
            {t.offline}
            <button
              onClick={() => {
                setOffline(false);
                void work(
                  "Revalidating",
                  async () => {
                    await api("/session").then((s) =>
                      setCsrf((s as { csrf: string }).csrf),
                    );
                    await refresh();
                    setNotice(
                      "Reconnected. Previous approvals are never replayed.",
                    );
                  },
                  true,
                );
              }}
            >
              {tr("Reconnect & revalidate")}
            </button>
          </div>
        ) : null}
        {data.demo?.public ? (
          <aside
            className="public-demo-banner"
            aria-label={tr("Public illustrative demo")}
          >
            <div>
              <strong>{tr("Public temporary workspace")}</strong>
              <p>
                {tr(
                  "Private browser workspace · expires after 2 hours. Hosting inactivity, restarts or redeploys can reset it sooner. Use sample documents.",
                )}
              </p>
              <small>
                {data.agent.provider === "gemini_developer"
                  ? tr(
                      "Alternative Gemini is configured; Agent Engine and real Calendar acceptance remain pending.",
                    )
                  : tr(
                      "Calendar actions are simulated. Gemini/Agent Engine and real Google Calendar remain pending.",
                    )}
              </small>
            </div>
            <button
              className="secondary"
              disabled={!!busy}
              onClick={() =>
                void work("Starting a fresh demo", async () => {
                  const old = tenantRef.current;
                  const session = await api<{ csrf: string }>("/session");
                  setCsrf(session.csrf);
                  const next = await api<{ csrf: string }>(
                    "/demo/reset",
                    "POST",
                  );
                  setCsrf(next.csrf);
                  localStorage.removeItem("relay.snapshot.v1:" + old);
                  setSource(null);
                  setPacket(null);
                  setPreview(null);
                  setScenario(null);
                  setAnswer("");
                  setPrompt("");
                  setNotice("");
                  setCalendars([]);
                  conversationId.current = null;
                  const fresh = await refresh();
                  setView("week");
                  setEntry(!fresh.agent.public_access);
                })
              }
            >
              {tr("Start a fresh demo")}
            </button>
          </aside>
        ) : null}
        <div className="content-wrap">
          <main id="main" className="main-content">
            {data.calendar_error&&<div className="offline-banner" role="status"><p>{tr('Calendar needs reconnection. Your documents and progress remain available; no fresh Calendar availability is assumed.')}</p><button className="secondary" onClick={()=>setView('connections')}>{tr('Connections')}</button></div>}
            <p className="fine-print">{tr('Selected files: PDF, MD, TXT, ICS · up to 2 MiB; text PDFs only.')}</p>
            {data.demo?.public && (
              <section
                className="panel workspace-choice"
                aria-label={tr("Choose your workspace")}
              >
                <strong>
                  {data.settings.mode === "illustrative"
                    ? tr("Example workspace")
                    : tr("Your own documents")}
                </strong>
                <p>
                  {tr(
                    "The example and your own documents use separate workspaces. Switching preserves both until their temporary sessions expire.",
                  )}
                </p>
                {(["own", "example"] as const).map((kind) => (
                  <button
                    key={kind}
                    className="secondary"
                    disabled={!!busy}
                    onClick={() =>
                      void work(tr("Switch workspace"), async () => {
                        const next = await api<{ csrf: string }>(
                          "/workspace/switch",
                          "POST",
                          { kind },
                        );
                        setCsrf(next.csrf);
                        sessionStorage.setItem("relay.entered", "1");
                        location.reload();
                      })
                    }
                  >
                    {tr(kind === "own" ? "Use my own data" : "Open example")}
                  </button>
                ))}
                <a href={window.relay ? "https://campuspulse-relay-demo.onrender.com/samples/" : "/samples/"} target="_blank" rel="noreferrer" onClick={window.relay ? (e)=>{e.preventDefault();void external("https://campuspulse-relay-demo.onrender.com/samples/");} : undefined}>
                  {tr("Sample documents and instructions")}
                </a>
              </section>
            )}
            {(view === "week" || view === "recovery") && (
              <PlanningContext
                key={"context:" + data.workspace_id}
                data={data}
                work={work}
                refresh={refresh}
              />
            )}
            {data.plan?.scope && (
              <p className="scope-notice" role="status">
                {tr("Plan scope")}: {data.plan.scope.included.length}{" "}
                {tr("confirmed assignments")}; {data.plan.scope.excluded.length}{" "}
                {tr("drafts excluded")}.{" "}
                {!data.plan.scope.complete &&
                  tr(
                    "This is a partial plan. Review the excluded drafts before treating the whole workload as planned.",
                  )}
              </p>
            )}
            {view === "evidence" && (
              <DocumentReview
                key={"review:" + data.workspace_id}
                data={data}
                refresh={refresh}
                work={work}
                busy={!!busy}
                onExtract={(id) =>
                  void ask(
                    `Read source ${id} completely, including continuation chunks/pages. Extract its academic assignments using propose_academic_extraction. Group each assignment under a distinct entity_id (use existing section_key if it matches). Cite exact page quotes for title, course, term, assignment_key, due, minutes, rubric and normalized submission_requirement where present. Keep missing or ambiguous fields unknown. Do not save a plan or apply facts. Tell me which fields need clarification; I will review each proposal in Document review.`,
                  )
                }
              />
            )}
            {data.settings.mode === "judge" && (
              <div className="offline-banner">
                <ShieldCheck size={18} />
                {tr(
                  "Dedicated judge workspace. Upload permitted demo coursework. Calendar changes are real, require approval, and stay in your exclusive demo calendar.",
                )}
              </div>
            )}
            <section className="hero">
              <div>
                <div className="eyebrow">
                  <span className="pulse-dot" /> {tr("MONDAY START ·")}{" "}
                  {data.settings.timezone}
                </div>
                <h1>
                  {view === "week" ? (
                    <>
                      {t.headline}
                      <br />
                      <span>{t.balance}</span>
                    </>
                  ) : (
                    t[view]
                  )}
                </h1>
                <p>
                  {view === "week"
                    ? t.sub
                    : view === "evidence"
                      ? tr(
                          "Every deadline deserves a source. Every conflict deserves a choice.",
                        )
                      : view === "recovery"
                        ? tr(
                            "Make room for what matters, within the time you actually have.",
                          )
                        : view === "activity"
                          ? tr(
                              "An honest record of what was called, observed and applied.",
                            )
                          : tr(
                              "Choose exactly what RELAY can read and change.",
                            )}
                </p>
              </div>
              <div className="hero-actions">
                <button
                  className="primary"
                  disabled={!!busy || offline}
                  onClick={repair}
                >
                  {busy === t.repair ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Sparkles size={17} />
                  )}{" "}
                  {t.repair}
                  <ArrowRight size={17} />
                </button>
                <span className="hero-note">
                  <ShieldCheck size={13} />
                  {tr("Nothing changes without your approval")}
                </span>
              </div>
            </section>
            {error ? (
              <div className="error-banner" role="alert">
                <TriangleAlert size={18} />
                <div>
                  <strong>{tr("We couldn’t complete that action.")}</strong>
                  <p>{errorMessage(error, lang)}</p>
                  <details className="diagnostic">
                    <summary>{tr("Original diagnostic")}</summary>
                    <code>{error}</code>
                  </details>
                </div>
                <button
                  className="icon-button"
                  aria-label={tr("Dismiss error")}
                  onClick={() => setError("")}
                >
                  <X size={17} />
                </button>
              </div>
            ) : null}
            {notice ? (
              <div className="notice" role="status">
                <Check size={16} />
                {operational(notice, lang)}
                <button
                  aria-label={tr("Dismiss notification")}
                  onClick={() => setNotice("")}
                >
                  <X size={14} />
                </button>
              </div>
            ) : null}
            {view === "week" ? (
              <>
                {unresolved.length ? (
                  <button
                    className="conflict-banner"
                    onClick={() => setView("evidence")}
                  >
                    <span className="warning-icon">
                      <GitBranch size={22} />
                    </span>
                    <span>
                      <strong>{t.conflict}</strong>
                      <small>
                        {
                          data.tasks.find(
                            (task) => task.id === unresolved[0].task_id,
                          )?.title
                        }{" "}
                        {tr("· two sources disagree · your choice is needed")}
                      </small>
                    </span>
                    <span className="review-link">
                      {t.review}
                      <ArrowUpRight size={16} />
                    </span>
                  </button>
                ) : (
                  <div className="all-clear">
                    <ShieldCheck size={17} />
                    {tr("Evidence checked.")}{" "}
                    {data.conflicts.length
                      ? tr("Your deadline choice is recorded.")
                      : tr("No deadline conflicts detected.")}
                    <button onClick={() => setView("evidence")}>
                      {tr("View sources")} <ArrowUpRight size={14} />
                    </button>
                  </div>
                )}
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">{tr("THE WEEK AHEAD")}</span>
                    <h2>{t.timeline}</h2>
                  </div>
                  <button
                    className="text-button"
                    onClick={() =>
                      void work("Refreshing sources", async () => {
                        await refresh();
                        setNotice(
                          "Workspace reloaded. Use Change radar to fetch the live repository.",
                        );
                      })
                    }
                  >
                    <RefreshCw size={15} />
                    {tr("Refresh")}
                  </button>
                </div>
                <Timeline
                  data={data}
                  plan={data.plan}
                  onBlock={openPacket}
                  list={list}
                  setList={setList}
                />
                <div className="capacity-strip">
                  <div className="capacity-icon">
                    <Clock3 size={22} />
                  </div>
                  <div>
                    <strong>
                      {data.plan
                        ? tr("{work} of work · {capacity} available", {
                            work: duration(data.plan.required_minutes),
                            capacity: duration(data.plan.capacity_minutes),
                          })
                        : data.tasks.length
                          ? tr("{work} known estimated work", {
                              work: duration(
                                data.tasks.reduce(
                                  (sum, t) => sum + (t.minutes || 0),
                                  0,
                                ),
                              ),
                            }) +
                            (data.tasks.some((t) => !t.minutes)
                              ? tr(" · some effort unknown")
                              : "")
                          : tr("Your week starts with a source.")}
                    </strong>
                    <p>
                      {data.plan
                        ? data.plan.feasible
                          ? tr(
                              "Every hard deadline checked. Effort remains an estimate.",
                            )
                          : tr(
                              "{count} minutes don’t fit. Review explicit alternatives.",
                              { count: data.plan.unscheduled_minutes },
                            )
                        : tr(
                            data.conflicts.some(
                              (c) => c.status === "unresolved",
                            )
                              ? "Resolve the conflicting deadline to calculate a feasible plan."
                              : "Review assignments and availability, then generate a plan. Unknown information stays unknown.",
                          )}
                    </p>
                  </div>
                  <div className="capacity-value">
                    {data.plan
                      ? duration(Math.max(0, data.plan.slack_minutes))
                      : "—"}
                    <span>{tr("capacity buffer")}</span>
                  </div>
                </div>
                <div className="section-heading next-heading">
                  <h2>{t.next}</h2>
                  <button
                    className="text-button"
                    onClick={() => input.current?.click()}
                  >
                    <Plus size={16} />
                    {tr("Import a source")}
                  </button>
                </div>
                <div className="task-grid">
                  {data.tasks.map((task, i) => (
                    <button
                      className={`task-card card-${i % 3}`}
                      key={task.id}
                      onClick={() => openPacket(task.id)}
                    >
                      <span className="eyebrow">{task.course}</span>
                      <h3>
                        {task.title}
                        <ArrowUpRight size={17} />
                      </h3>
                      <div className="task-details">
                        <span>
                          <Clock3 size={14} />
                          {task.minutes
                            ? duration(task.minutes)
                            : tr("Effort unknown")}
                        </span>
                        <span className={!task.due ? "missing" : ""}>
                          {task.due
                            ? deadlineText(
                                task.due,
                                lang,
                                data.settings.timezone,
                              )
                            : tr("Deadline needs your choice")}
                        </span>
                      </div>
                      <footer>
                        <Link2 size={12} />
                        {tr("{count} evidence sources", {
                          count: task.source_ids.length,
                        })}
                        <span>{label(task.completion, lang)}</span>
                      </footer>
                    </button>
                  ))}
                </div>
              </>
            ) : null}
            {view === "evidence" ? (
              <div className="evidence-view">
                {data.conflicts.map((c) => (
                  <section className="conflict-card" key={c.id}>
                    <div className="between">
                      <h2>
                        {
                          data.tasks.find((task) => task.id === c.task_id)
                            ?.title
                        }
                      </h2>
                      <StatusPill
                        tone={c.status === "resolved" ? "success" : "warning"}
                      >
                        {c.status === "resolved"
                          ? tr("Choice recorded")
                          : tr("Conflicting deadlines")}
                      </StatusPill>
                    </div>
                    <p>
                      {tr(
                        "Both passages are preserved. A newer fetch alone does not establish authority.",
                      )}
                    </p>
                    <div className="fact-grid">
                      {c.facts.map((f) => (
                        <div key={f.id}>
                          <SourceFact
                            fact={f}
                            source={sourceById(f.source_id)}
                            onOpen={openSource}
                          />
                          <button
                            className={
                              c.resolution?.fact_id === f.id
                                ? "secondary chosen"
                                : "secondary"
                            }
                            disabled={!!busy || offline}
                            onClick={() =>
                              void work(
                                "Recording deadline choice",
                                async () => {
                                  await api(
                                    "/conflicts/" + c.id + "/resolve",
                                    "POST",
                                    { fact_id: f.id },
                                  );
                                  await refresh();
                                  setNotice(
                                    "Explicit deadline choice saved with this evidence version.",
                                  );
                                },
                              )
                            }
                          >
                            {c.resolution?.fact_id === f.id ? (
                              <Check size={16} />
                            ) : null}
                            {c.resolution?.fact_id === f.id
                              ? tr("Selected deadline")
                              : tr("Use this deadline")}
                          </button>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
                <div className="section-heading">
                  <h2>
                    {tr("Source library")}{" "}
                    <span className="count">{data.sources.length}</span>
                  </h2>
                  <button
                    className="secondary"
                    onClick={() =>
                      window.relay ? importFile() : input.current?.click()
                    }
                  >
                    <Upload size={16} />
                    {tr("Import selected file")}
                  </button>
                </div>
                <div className="source-list">
                  {data.sources.map((s) => (
                    <button key={s.id} onClick={() => openSource(s.id)}>
                      <span className="source-icon">
                        <FileText size={22} />
                      </span>
                      <span>
                        <strong>{s.title}</strong>
                        <small>
                          {label(s.mode, lang)} · {s.facts.length}{" "}
                          {tr("evidence facts · version")}{" "}
                          {shortHash(s.version)}
                        </small>
                      </span>
                      <ArrowUpRight size={18} />
                    </button>
                  ))}
                </div>
                <p className="fine-print">
                  {data.demo?.public
                    ? tr(
                        "Public demo imports: text PDF, Markdown, TXT or ICS up to 2 MiB. At most 12 sources including examples. Original quotations stay unchanged.",
                      )
                    : tr(
                        "PDF, Markdown, TXT and ICS · maximum 2 MiB. Text PDFs only, at most 100 pages and 250,000 extracted characters. No OCR.",
                      )}
                </p>
              </div>
            ) : null}
            {view === "recovery" ? (
              <>
                <div className="recovery-tools">
                  <button
                    className="secondary"
                    disabled={!data.plan || !!busy}
                    onClick={() =>
                      void work("Comparing scenario", async () =>
                        setScenario(
                          await api<Plan>("/scenario", "POST", {
                            remove_weekday: 2,
                          }),
                        ),
                      )
                    }
                  >
                    <ArrowDown size={16} />
                    {tr("Lose Wednesday afternoon")}
                  </button>
                  <button
                    className="secondary"
                    disabled={!data.plan || !!busy}
                    onClick={() =>
                      void work("Comparing scenario", async () =>
                        setScenario(
                          await api<Plan>("/scenario", "POST", {
                            task_id: data.tasks[0].id,
                            extra_minutes: 60,
                          }),
                        ),
                      )
                    }
                  >
                    <Plus size={16} />
                    {tr("One hour more effort")}
                  </button>
                  {scenario ? (
                    <button
                      className="text-button"
                      onClick={() => setScenario(null)}
                    >
                      {tr("Return to baseline")}
                      <X size={15} />
                    </button>
                  ) : null}
                </div>
                {activePlan ? (
                  <>
                    <div
                      className={
                        activePlan.feasible
                          ? "plan-summary"
                          : "plan-summary overloaded"
                      }
                    >
                      <StatusPill
                        tone={activePlan.feasible ? "success" : "warning"}
                      >
                        {scenario
                          ? tr("What-if · baseline unchanged")
                          : activePlan.invalidated
                            ? tr("Outdated plan")
                            : activePlan.feasible
                              ? tr("Feasible allocation")
                              : tr("More time is needed")}
                      </StatusPill>
                      <h2>
                        {activePlan.feasible
                          ? tr("A week that fits.")
                          : tr("This week needs an explicit tradeoff.")}
                      </h2>
                      <div className="plan-stats">
                        <p>
                          <strong>
                            {duration(activePlan.required_minutes)}
                          </strong>
                          <span>{tr("estimated work")}</span>
                        </p>
                        <p>
                          <strong>
                            {duration(activePlan.capacity_minutes)}
                          </strong>
                          <span>{tr("available capacity")}</span>
                        </p>
                        <p>
                          <strong>
                            {duration(activePlan.unscheduled_minutes)}
                          </strong>
                          <span>{tr("unscheduled")}</span>
                        </p>
                        <p>
                          <strong>
                            {label(activePlan.solver_status, lang)}
                          </strong>
                          <span>{tr("solver result")}</span>
                        </p>
                      </div>
                      {Object.entries(activePlan.unscheduled_by_task).map(
                        ([id, m]) => (
                          <p key={id}>
                            {data.tasks.find((t) => t.id === id)?.title}: {m}{" "}
                            {tr(
                              "minutes remain unscheduled before its hard deadline.",
                            )}
                          </p>
                        ),
                      )}
                      <p>
                        {activePlan.feasible
                          ? tr(
                              "Hard constraints validated. No calibrated probability or grade prediction is implied.",
                            )
                          : tr(
                              "Add availability before the affected deadline, revise the effort estimate explicitly, or request an instructor-approved extension. RELAY never changes the real deadline.",
                            )}
                      </p>
                    </div>
                    <Timeline
                      data={data}
                      plan={activePlan}
                      list={list}
                      setList={setList}
                      onBlock={openPacket}
                    />
                    <div className="approval-cta">
                      <div>
                        <h3>{tr("Ready to make space?")}</h3>
                        <p>
                          {tr(
                            "Review the exact events and destination before approving.",
                          )}
                        </p>
                      </div>
                      <button
                        className="primary"
                        disabled={
                          !activePlan.feasible ||
                          !current ||
                          !!scenario ||
                          !!busy ||
                          offline
                        }
                        onClick={() =>
                          void work("Preparing exact preview", async () =>
                            setPreview(
                              await api<Preview>(
                                "/plans/" + activePlan.id + "/preview",
                                "POST",
                              ),
                            ),
                          )
                        }
                      >
                        <ShieldCheck size={17} />
                        {tr("Review calendar actions")}
                        <ArrowRight size={17} />
                      </button>
                    </div>
                    <div className="assumptions">
                      <h3>{tr("Assumptions stay visible")}</h3>
                      {activePlan.assumptions.map((a) => (
                        <p key={a}>
                          <Check size={14} />
                          {operational(a, lang)}
                        </p>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="empty panel">
                    <Zap size={32} />
                    <h2>{tr("Start with the evidence.")}</h2>
                    <p>
                      {tr(
                        "Resolve the deadline conflict, then repair your week to compare scenarios.",
                      )}
                    </p>
                    <button
                      className="secondary"
                      onClick={() => setView("evidence")}
                    >
                      {tr("Review evidence")}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                )}
              </>
            ) : null}
            {view === "activity" ? (
              <>
                <div className="section-heading">
                  <h2>{tr("Verified receipts")}</h2>
                  <StatusPill>
                    {data.receipts.length} {tr("receipts")}
                  </StatusPill>
                </div>
                {data.receipts.length ? (
                  data.receipts.map((r) => (
                    <section className="receipt panel" key={r.id}>
                      <div className="between">
                        <h3>
                          <CheckCheck size={20} />
                          {r.status === "verified"
                            ? tr("Read-back completed")
                            : tr("Partial apply — inspect outcomes")}
                        </h3>
                        <StatusPill
                          tone={r.mode === "live" ? "success" : "warning"}
                        >
                          {r.mode === "live"
                            ? tr("Live Calendar")
                            : tr("Illustrative local calendar")}
                        </StatusPill>
                      </div>
                      <p className="mono">{r.calendar_id}</p>
                      {r.outcomes.map((o) => (
                        <div className="receipt-line" key={o.event_id}>
                          <span>{label(o.status, lang)}</span>
                          <code>{o.event_id.slice(0, 16)}</code>
                          {o.url ? (
                            <button
                              className="text-button"
                              onClick={() => external(o.url!)}
                            >
                              {tr("Open Calendar")}
                              <ArrowUpRight size={13} />
                            </button>
                          ) : null}
                          {o.error ? (
                            <small>
                              {errorMessage(
                                o.error.code + ": " + o.error.message,
                                lang,
                              )}
                            </small>
                          ) : null}
                        </div>
                      ))}
                      <div className="row">
                        <button
                          className="secondary"
                          onClick={() =>
                            void work("Verifying events", async () => {
                              const value = await api(
                                "/receipts/" + r.id + "/verify",
                                "POST",
                              );
                              setAnswer(JSON.stringify(value, null, 2));
                            })
                          }
                        >
                          <RefreshCw size={15} />
                          {tr("Verify again")}
                        </button>
                        <button
                          className="text-button"
                          onClick={() =>
                            void work("Guarded undo", async () => {
                              const value = await api(
                                "/receipts/" + r.id + "/undo",
                                "POST",
                              );
                              setAnswer(JSON.stringify(value, null, 2));
                              await refresh();
                            })
                          }
                        >
                          <Undo2 size={15} />
                          {tr("Undo unchanged owned events")}
                        </button>
                      </div>
                    </section>
                  ))
                ) : (
                  <div className="empty panel">
                    <ShieldCheck size={28} />
                    <h3>{tr("No actions applied yet.")}</h3>
                    <p>
                      {tr(
                        "A receipt appears after you review and approve concrete calendar events.",
                      )}
                    </p>
                  </div>
                )}
                <div className="section-heading">
                  <h2>{tr("Execution journal")}</h2>
                  <small>
                    {tr(
                      "Durable, ordered events · reconnect uses sequence IDs",
                    )}
                  </small>
                </div>
                <div className="journal">
                  {data.events
                    .slice()
                    .reverse()
                    .map((e) => (
                      <div key={e.sequence}>
                        <code>#{e.sequence}</code>
                        <span className="journal-icon">
                          {e.type.includes("failed") ? (
                            <TriangleAlert size={16} />
                          ) : (
                            <Activity size={16} />
                          )}
                        </span>
                        <div>
                          <strong>{label(e.tool || e.type, lang)}</strong>
                          <p>{eventSummary(e, lang)}</p>
                        </div>
                        <small>
                          {e.duration_ms !== undefined
                            ? tr("{value} ms", { value: e.duration_ms })
                            : "—"}
                        </small>
                      </div>
                    ))}
                </div>
              </>
            ) : null}
            {view === "connections" ? (
              <>
                <div className="connection-grid">
                  <section className="panel connection-card">
                    <span className="connection-icon">
                      <Sparkles size={24} />
                    </span>
                    <StatusPill
                      tone={data.agent.configured ? "neutral" : "warning"}
                    >
                      {data.agent.configured
                        ? tr("Configured · unverified")
                        : tr("Authentication required")}
                    </StatusPill>
                    <h2>
                      {data.agent.provider === "gemini_developer"
                        ? tr("Gemini · alternative host")
                        : tr("Gemini + Agent Engine")}
                    </h2>
                    <p>
                      {data.agent.provider === "gemini_developer"
                        ? tr(
                            "Alternative Gemini is configured; Agent Engine and real Calendar acceptance remain pending.",
                          )
                        : tr(
                            "The managed reasoningEngine is the actual agent query path. Its live deployment is not verified yet.",
                          )}
                    </p>
                    <code>
                      {data.agent.resource ||
                        tr("No managed resource connected")}
                    </code>
                    <button
                      className="secondary"
                      onClick={() =>
                        external(
                          "https://console.cloud.google.com/vertex-ai/agents",
                        )
                      }
                    >
                      {tr("Open Google Cloud")}
                      <ArrowUpRight size={16} />
                    </button>
                  </section>
                  <section className="panel connection-card">
                    <span className="connection-icon">
                      <GitBranch size={24} />
                    </span>
                    <StatusPill tone="neutral">
                      {tr("Public GitHub source")}
                    </StatusPill>
                    <h2>{tr("Course repository")}</h2>
                    <p>{data.settings.github_repo}</p>
                    <button
                      className="secondary"
                      disabled={!!busy || offline}
                      onClick={() =>
                        void work("Reading live repository", async () => {
                          const r = await api<{
                            changed: boolean;
                            commit: string;
                          }>("/sync", "POST");
                          await refresh();
                          setNotice(
                            r.changed
                              ? "Live source version imported. Review its impact."
                              : "No meaningful source change; no duplicate impact run.",
                          );
                        })
                      }
                    >
                      <RefreshCw size={16} />
                      {tr("Fetch live course source")}
                    </button>
                    <label className="toggle-row">
                      <input
                        type="checkbox"
                        checked={data.settings.watch_enabled}
                        onChange={(e) =>
                          void work("Updating radar", async () => {
                            await api("/preferences", "POST", {
                              watch_enabled: e.target.checked,
                            });
                            await refresh();
                          })
                        }
                      />
                      {tr("Poll every {count} seconds", {
                        count: data.settings.poll_seconds || 300,
                      })}
                    </label>
                    <small>
                      {data.demo?.public
                        ? tr(
                            "Server polling works while the free service is awake. Shared public observations keep their original fetch time. Sleeping or restarting hosting stops polling; no always-on guarantee.",
                          )
                        : tr(
                            "Local server polling continues without a chat prompt. Hosted scheduled execution requires GCP deployment.",
                          )}
                    </small>
                  </section>
                  <section className="panel connection-card">
                    <span className="connection-icon">
                      <CalendarDays size={24} />
                    </span>
                    <StatusPill
                      tone={data.settings.calendar_live&&data.calendar_mode!=='unavailable' ? "success" : "warning"}
                    >
                      {data.calendar_mode==='unavailable'?tr('Calendar needs reconnection'):data.settings.calendar_live
                        ? tr("Live connection")
                        : tr("Illustrative local adapter")}
                    </StatusPill>
                    <h2>{tr("Study calendar")}</h2>
                    <button
                      className="text-button"
                      disabled={
                        !!data.demo?.public &&
                        !data.agent.configured
                      }
                      onClick={() => void connectGoogle()}
                    >
                      {tr("Connect Google in system browser")}
                      <ArrowUpRight size={14} />
                    </button>
                    {data.settings.calendar_live?<p>{tr('Connected to your selected Calendar. Approved actions affect real events; review the exact preview first.')}</p>:data.demo?.public ? (
                      <p>
                        {tr(
                          "Real Google consent and Calendar writes are pending. Review and approve simulated actions in Recovery.",
                        )}
                      </p>
                    ) : (
                      <p>
                        {tr(
                          "Writes are confined to a selected, authorized calendar. A service identity needs explicit sharing or consent.",
                        )}
                      </p>
                    )}
                    <code>
                      {data.settings.calendar_id ||
                        tr("No authorized calendar selected")}
                    </code>
                    <button
                      className="text-button"
                      disabled={
                        !!data.demo?.public &&
                        !data.agent.configured
                      }
                      onClick={() =>
                        void work("Listing authorized calendars", async () =>
                          setCalendars(
                            (
                              await api<{
                                calendars: {
                                  id: string;
                                  name: string;
                                  role: string;
                                  primary: boolean;
                                }[];
                              }>("/connections/calendar-list")
                            ).calendars,
                          ),
                        )
                      }
                    >
                      {tr("Choose an authorized calendar")}
                      <ChevronRight size={14} />
                    </button>
                    {calendars.map((c) => (
                      <button
                        key={c.id}
                        className="secondary"
                        onClick={() =>
                          void work(
                            "Connecting selected calendar",
                            async () => {
                              await api("/connections/calendar", "POST", {
                                calendar_id: c.id,
                              });
                              setCalendars([]);
                              await refresh();
                            },
                          )
                        }
                      >
                        {c.name}
                        {c.primary ? tr(" · primary") : ""}
                      </button>
                    ))}
                    <button
                      className="secondary"
                      disabled={
                        !!data.demo?.public &&
                        !data.agent.configured
                      }
                      onClick={() =>
                        void work(
                          tr("Create a separate study calendar"),
                          async () => {
                            await api("/connections/calendar/create", "POST");
                            setCalendars(
                              (
                                await api<{
                                  calendars: {
                                    id: string;
                                    name: string;
                                    role: string;
                                    primary: boolean;
                                  }[];
                                }>("/connections/calendar-list")
                              ).calendars,
                            );
                          },
                        )
                      }
                    >
                      {tr("Create a separate study calendar")}
                    </button>
                    <button
                      className="text-button"
                      disabled={!data.settings.calendar_live}
                      onClick={() =>
                        void work(tr("Disconnect Calendar"), async () => {
                          await api("/connections/disconnect", "POST");
                          setCalendars([]);
                          await refresh();
                        })
                      }
                    >
                      {tr("Disconnect Calendar")}
                    </button>
                    <p>
                      {tr(
                        "Calendar connection is optional. Consent does not authorize study writes. Create or choose a separate calendar, then review and approve exact actions. Disconnect preserves existing events.",
                      )}
                    </p>
                    <button
                      className="secondary"
                      onClick={() => external("https://calendar.google.com")}
                    >
                      {tr("Open Google Calendar")}
                      <ArrowUpRight size={16} />
                    </button>
                  </section>
                  <section className="panel connection-card">
                    <span className="connection-icon">
                      <FolderOpen size={24} />
                    </span>
                    <StatusPill>
                      {window.relay ? tr("Windows desktop") : tr("Web client")}
                    </StatusPill>
                    <h2>{tr("Your files. Your choice.")}</h2>
                    <p>
                      {tr(
                        "Import only selected files. No arbitrary drive indexing. Offline snapshots never execute writes.",
                      )}
                    </p>
                    <p>
                      {tr(
                        "PDF, Markdown, TXT and ICS · maximum 2 MiB. Text PDFs only, at most 100 pages and 250,000 extracted characters. No OCR.",
                      )}
                    </p>
                    <button
                      className="secondary"
                      onClick={() =>
                        window.relay ? importFile() : input.current?.click()
                      }
                    >
                      <Upload size={16} />
                      {tr("Import a file")}
                    </button>
                    {window.relay ? (
                      <button
                        className="text-button"
                        onClick={() =>
                          void work("Select folder", async () => {
                            const r = await window.relay!.watchFolder();
                            setNotice(
                              r.enabled
                                ? "Folder watch enabled. Changes will be offered for explicit import."
                                : "Folder watch disabled.",
                            );
                          })
                        }
                      >
                        {tr("Select a folder to watch")}
                        <FolderOpen size={15} />
                      </button>
                    ) : null}
                    {window.relay ? (
                      <button
                        className="secondary"
                        onClick={() =>
                          void work("Send test notification", async () => {
                            await window.relay?.notify(
                              tr("RELAY notification check"),
                              tr(
                                "This is a local notification test. No cloud calls or calendar writes were made.",
                              ),
                            );
                            setNotice(
                              "Notification requested. Check the Windows banner or Notification Center; dispatch alone does not prove visibility.",
                            );
                          })
                        }
                      >
                        {tr("Send test notification")}
                      </button>
                    ) : null}
                  </section>
                </div>
                <div className="settings-row panel">
                  <Globe2 size={20} />
                  <div>
                    <h3>{tr("Workspace timezone")}</h3>
                    <p>{tr("Original evidence timestamps are preserved.")}</p>
                  </div>
                  <input
                    aria-label={tr("Workspace timezone")}
                    defaultValue={data.settings.timezone}
                    onBlur={(e) => {
                      if (e.target.value !== data.settings.timezone)
                        void work("Setting timezone", async () => {
                          await api("/preferences", "POST", {
                            timezone: e.target.value,
                          });
                          await refresh();
                        });
                    }}
                  />
                </div>
                <div className="settings-row panel">
                  <Download size={20} />
                  <div>
                    <h3>{tr("Export your workspace")}</h3>
                    <p>
                      {tr(
                        "JSON snapshot with provenance, plans and receipts. No credentials.",
                      )}
                    </p>
                  </div>
                  <button
                    className="secondary"
                    onClick={() => {
                      const blob = new Blob([JSON.stringify(data, null, 2)], {
                        type: "application/json",
                      });
                      const a = document.createElement("a");
                      a.href = URL.createObjectURL(blob);
                      a.download = "CampusPulse-RELAY-workspace.json";
                      a.click();
                      URL.revokeObjectURL(a.href);
                    }}
                  >
                    {tr("Export JSON")}
                  </button>
                </div>
              </>
            ) : null}
            {view === "challenge" ? (
              <Workshop
                key={data.workspace_id}
                data={data}
                refresh={refresh}
                openSource={openSource}
                onPlan={(p, proposed) => {
                  setScenario(proposed ? p : null);
                  setView("recovery");
                }}
                work={work}
                busy={!!busy || offline}
              />
            ) : null}
            {view === "evidence" &&
            data.tasks.some((t) => t.identity?.status === "unresolved") ? (
              <div className="offline-banner">
                <span>
                  {tr(
                    "Course or term is unresolved. Confirm the assignment mapping before planning.",
                  )}
                </span>
                <button
                  className="secondary"
                  onClick={() => setView("challenge")}
                >
                  {tr("Confirm assignment mapping")}
                </button>
              </div>
            ) : null}
            {view === "recovery" ? (
              <button
                className="secondary"
                onClick={() => setView("challenge")}
              >
                {tr("Compare permitted remedies")}
              </button>
            ) : null}
            {(view === "week" ||
              view === "evidence" ||
              view === "connections") && (
              <Continuity
                key={data.workspace_id}
                data={data}
                refresh={refresh}
              />
            )}
            <p className="fine-print local-acceptance">
              {tr(
                "Five enhancements locally implemented · real Calendar and Gemini acceptance pending.",
              )}
            </p>
            <section className="assistant">
              {!entry ? (
                <LiveAccess
                  key={data.workspace_id}
                  data={data}
                  consent={processingConsent}
                  onConsent={(value) =>
                    setProcessingWorkspace(
                      value ? data.workspace_id || null : null,
                    )
                  }
                />
              ) : null}
              <div className="assistant-label">
                <Sparkles size={17} />
                <strong>{t.assistant}</strong>
                <span>
                  {data.agent.provider === "gemini_developer"
                    ? tr("Gemini · alternative host")
                    : data.agent.configured
                      ? tr("Managed Gemini agent")
                      : tr("Connect Agent Engine for live AI")}
                </span>
              </div>
              <button
                className="text-button"
                disabled={!!busy}
                onClick={() =>
                  void work("Starting a new conversation", async () => {
                    conversationId.current = (
                      await api<{ id: string }>("/conversation/new", "POST")
                    ).id;
                    setAnswer("");
                    setPrompt("");
                    setNotice(
                      tr(
                        "New conversation started. Previous context is not reused.",
                      ),
                    );
                  })
                }
              >
                {tr("New conversation")}
              </button>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void ask();
                }}
              >
                <input
                  aria-label={tr("Message RELAY")}
                  placeholder={t.placeholder}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  maxLength={6000}
                />
                <button
                  aria-label={tr("Send to agent")}
                  disabled={!!busy || offline || !prompt.trim()}
                >
                  <Send size={18} />
                </button>
              </form>
              {queuedQuestion ? (
                <div
                  className="queue-status"
                  role="status"
                  aria-live="polite"
                  data-testid="ai-queue"
                >
                  <strong>
                    {tr(
                      queuedQuestion.status === "queued"
                        ? "Question queued"
                        : queuedQuestion.status === "quota_wait"
                          ? "Waiting for API quota"
                          : "Gemini is working",
                    )}
                  </strong>
                  {queuedQuestion.position ? (
                    <p>
                      {tr("Queue position")} {queuedQuestion.position}
                    </p>
                  ) : null}
                  {queuedQuestion.quota?.wait_seconds ? (
                    <p>
                      {tr(
                        "Shared API quota is temporarily full. Your question stays queued; no paid fallback is used.",
                      )}
                    </p>
                  ) : null}
                  <p className="fine-print">
                    {tr(
                      "One question per workspace at a time. Refresh resumes this question without sending it again.",
                    )}
                  </p>
                  {!busy ? (
                    <button
                      className="secondary"
                      onClick={() => {
                        const generation = ++chatGeneration.current;
                        void work(CONTACTING_AGENT, () =>
                          followQuestion(queuedQuestion, generation),
                        );
                      }}
                    >
                      {tr("Resume queued question")}
                    </button>
                  ) : null}
                </div>
              ) : null}
              {answer ? (
                <div className="answer">
                  <button
                    aria-label={tr("Dismiss agent response")}
                    className="icon-button"
                    onClick={() => setAnswer("")}
                  >
                    <X size={16} />
                  </button>
                  <pre>{answer}</pre>
                </div>
              ) : null}
            </section>
            <footer className="page-footer">
              <span>{tr("See what changed. Know what to do next.")}</span>
              <span>
                {data.settings.mode === "illustrative"
                  ? tr("Illustrative course content · local Calendar adapter")
                  : ""}{" "}
                · {tr("View generated")}{" "}
                {new Date(
                  data.snapshot_generated_at || data.last_sync || "",
                ).toLocaleTimeString(locale)}
              </span>
            </footer>
            <input
              hidden
              ref={input}
              type="file"
              accept=".pdf,.md,.txt,.ics"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void importFile(f);
                e.target.value = "";
              }}
            />
          </main>
          {rail ? (
            <RunRail
              events={data.events}
              resource={data.agent.resource}
              close={() => setRail(false)}
            />
          ) : (
            <button
              className="rail-open icon-button"
              aria-label={tr("Open inspector")}
              onClick={() => setRail(true)}
            >
              <PanelRightOpen size={20} />
            </button>
          )}
        </div>
      </div>
      {busy ? (
        <div className="working" role="status">
          <LoaderCircle size={16} className="spin" />
          {operational(busy, lang)}
          {busy === CONTACTING_AGENT ? (
            <button
              onClick={() =>
                void (async () => {
                  chatGeneration.current++;
                  workGeneration.current++;
                  workLock.current = false;
                  setBusy("");
                  setQueuedQuestion(null);
                  setNotice(
                    tr(
                      "Stopped waiting. Remote compute may continue; inspect events and receipts before retrying.",
                    ),
                  );
                  try {
                    const c = await api<{ active_run?: string }>(
                      "/conversation",
                    );
                    if (c.active_run)
                      await api("/runs/" + c.active_run + "/cancel", "POST");
                  } catch (e) {
                    setError((e as Error).message);
                  }
                })()
              }
            >
              {tr("Stop waiting")}
            </button>
          ) : null}
        </div>
      ) : null}
      {source ? (
        <Modal title={source.title} onClose={() => setSource(null)} wide>
          <div className="source-meta">
            <StatusPill
              tone={source.mode === "live_github" ? "success" : "warning"}
            >
              {label(source.mode, lang)}
            </StatusPill>
            <code>{source.content_hash}</code>
            <p>
              {tr("Fetched")} {source.fetched_at} {tr("· version")}{" "}
              {source.version}
            </p>
            {source.remote?.url ? (
              <button
                className="text-button"
                onClick={() => external(source.remote!.url)}
              >
                {tr("Open original commit")}
                <ArrowUpRight size={14} />
              </button>
            ) : null}
          </div>
          <div className="page-tabs">
            {source.pages?.map((p) => (
              <button
                className={page === p.page ? "active" : ""}
                key={p.page}
                onClick={() => setPage(p.page)}
              >
                {tr("Page")} {p.page}
              </button>
            ))}
          </div>
          <pre className="source-text">
            {source.pages?.find((p) => p.page === page)?.text ||
              tr("Page unavailable")}
          </pre>
          <p className="fine-print">
            {tr(
              "Source material is untrusted data. Its text cannot authorize calendar writes or override application instructions.",
            )}
          </p>
        </Modal>
      ) : null}
      {packet ? (
        <Modal title={packet.task.title} onClose={() => setPacket(null)} wide>
          <div className="packet-summary">
            <StatusPill>{label(packet.completion_origin, lang)}</StatusPill>
            <span>{operational(packet.duration_assumption, lang)}</span>
          </div>
          <div className="next-action">
            <span className="eyebrow">{tr("ONE SMALL NEXT ACTION")}</span>
            <h3>{operational(packet.next_action, lang)}</h3>
          </div>
          <h3>{tr("Deliverable checklist")}</h3>
          {packet.task.user_overrides ? (
            <p className="fine-print">
              {tr("Explicit inputs from you:")}{" "}
              {Object.entries(packet.task.user_overrides)
                .map(
                  ([key, value]) =>
                    `${label(key, lang)}: ${key === "completion" ? label(String(value), lang) : value}`,
                )
                .join(" · ")}
              {tr(". Original source quotes are preserved below.")}
            </p>
          ) : null}
          {packet.checklist.length ? (
            <ul className="checklist" id="packet-checklist" tabIndex={-1}>
              {packet.checklist.map((r) => (
                <li key={r}>
                  <span className="empty-checkbox" />
                  {r}
                </li>
              ))}
            </ul>
          ) : (
            <p className="warning-text">
              {tr(
                "Rubric is missing. Define requirements before calling this complete.",
              )}
            </p>
          )}
          <form
            className="packet-edit"
            onSubmit={(e) => {
              e.preventDefault();
              const form = new FormData(e.currentTarget);
              void work("Saving your explicit task assumptions", async () => {
                const values: Record<string, unknown> = {};
                if (form.get("minutes"))
                  values.minutes = Number(form.get("minutes"));
                if (form.get("due")) values.due = String(form.get("due"));
                setPacket(
                  await api<Packet>(
                    "/tasks/" + packet.task.id + "/settings",
                    "POST",
                    values,
                  ),
                );
                await refresh();
                setNotice(
                  "Your explicit inputs were recorded. Repair the plan before applying actions.",
                );
              });
            }}
          >
            <label>
              {tr("Estimated effort (minutes)")}
              <input
                name="minutes"
                type="number"
                min="30"
                max="10080"
                step="30"
                defaultValue={packet.task.minutes || ""}
              />
            </label>
            <label>
              {tr("Confirmed deadline (ISO with UTC offset)")}
              <input
                name="due"
                placeholder="2026-10-23T18:00:00+05:00"
                defaultValue={packet.task.due || ""}
              />
            </label>
            <button className="secondary" type="submit">
              {tr("Save explicit inputs")}
            </button>
          </form>
          {data && (
            <Continuity
              key={data.workspace_id + packet.task.id}
              data={data}
              refresh={refresh}
              task={
                data.tasks.find((t) => t.id === packet.task.id) || packet.task
              }
              compact
            />
          )}
          <h3>{tr("Follow the evidence")}</h3>
          <div className="evidence-chain">
            <button
              onClick={() => {
                setPacket(null);
                void openSource(packet.task.source_ids[0]);
              }}
            >
              {tr("Source")}
            </button>
            <ArrowRight size={16} />
            <button
              onClick={() =>
                document.getElementById("packet-checklist")?.focus()
              }
            >
              {tr("Requirement")}
            </button>
            <ArrowRight size={16} />
            <button
              onClick={() =>
                document
                  .querySelector<HTMLInputElement>(".packet-edit input")
                  ?.focus()
              }
            >
              {tr("Task")}
            </button>
            <ArrowRight size={16} />
            <button
              onClick={() => {
                setPacket(null);
                setView("week");
                setList(true);
              }}
            >
              {tr("Study block")}
            </button>
            <ArrowRight size={16} />
            <button
              onClick={() => {
                setPacket(null);
                setView("activity");
              }}
            >
              {tr("Observation")}
            </button>
          </div>
          <div className="packet-facts">
            {packet.facts.map((f) => (
              <button
                key={f.id}
                onClick={() => {
                  setPacket(null);
                  void openSource(f.source_id, f.page);
                }}
              >
                <Link2 size={15} />
                <span>
                  {f.quote}
                  <small>
                    {sourceById(f.source_id)?.title} {tr("· page")} {f.page} ·{" "}
                    {shortHash(f.source_version)}
                  </small>
                </span>
                <ArrowUpRight size={15} />
              </button>
            ))}
          </div>
          <p className="fine-print">
            {tr(
              "Planned work and self-reported progress are distinct from externally observed completion. Closing an issue does not prove full learning or final submission.",
            )}
          </p>
        </Modal>
      ) : null}
      {preview ? (
        <Modal
          title={tr("Review. Approve. Verify.")}
          onClose={() => setPreview(null)}
          wide
        >
          <StatusPill tone={preview.mode === "live" ? "success" : "warning"}>
            {preview.mode === "live"
              ? tr("Real Google Calendar")
              : tr("Illustrative local calendar — no external writes")}
          </StatusPill>
          <div className="approval-target">
            <small>{tr("EXACT DESTINATION")}</small>
            <strong>{preview.calendar_id}</strong>
            <p>
              {tr("Plan")} {preview.plan_id} {tr("· expires")}{" "}
              {new Date(preview.expires_at).toLocaleTimeString(locale)}
            </p>
          </div>
          <p className="fine-print">
            {tr("Event titles are shown exactly as they will be written.")}
          </p>
          <div className="preview-list">
            {preview.actions.map((a) => (
              <div key={a.event.id}>
                <Plus size={16} />
                <span>
                  <strong>{a.event.summary}</strong>
                  <small>
                    {new Date(a.event.start.dateTime).toLocaleString(locale)} →{" "}
                    {new Date(a.event.end.dateTime).toLocaleTimeString(locale)}
                  </small>
                </span>
                <code>
                  {{
                    create: tr("Add"),
                    keep: tr("Keep"),
                    delete: tr("Remove"),
                  }[a.operation] || a.operation}
                </code>
              </div>
            ))}
          </div>
          <p className="fine-print">
            {tr(
              "No invitations or outgoing messages. The backend rechecks evidence and Calendar freshness, applies this exact digest once, and reads each event back.",
            )}
          </p>
          <code className="digest">SHA256 {preview.digest}</code>
          <button
            className="primary full"
            disabled={!!busy || offline}
            onClick={() =>
              void work("Applying and verifying approved events", async () => {
                const r = await api<{ status: string }>(
                  "/previews/" + preview.id + "/approve",
                  "POST",
                  { digest: preview.digest },
                );
                setPreview(null);
                await refresh();
                setView("activity");
                setNotice(
                  r.status === "verified"
                    ? "Read-back verified. Inspect the receipt and integration mode."
                    : "Partial apply. Inspect every operation before retrying.",
                );
              })
            }
          >
            <ShieldCheck size={18} />
            {preview.mode === "live"
              ? tr("Approve exact Calendar actions")
              : tr("Approve illustrative local actions")}
          </button>
        </Modal>
      ) : null}
      {entry ? (
        <Modal
          title={tr("Every change has a way forward.")}
          onClose={() => {
            setEntry(false);
            sessionStorage.setItem("relay.entered", "1");
          }}
        >
          <select
            data-testid="entry-language"
            aria-label={tr("Language")}
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
          >
            <option value="en">English</option>
            <option value="ru">Русский</option>
            <option value="kk">Қазақша</option>
          </select>
          <p className="entry-description">
            {tr(
              "An evidence-linked recovery plan for the week you actually have.",
            )}
          </p>
          <div className="entry-loop">
            <FileText />
            <ArrowRight size={17} />
            <CalendarDays />
            <ArrowRight size={17} />
            <ShieldCheck />
          </div>
          <button
            className="primary full"
            onClick={() => {
              setEntry(false);
              sessionStorage.setItem("relay.entered", "1");
            }}
          >
            {data.demo?.public
              ? tr("Enter public demo")
              : tr("Explore illustrative workspace")}
            <ArrowRight size={18} />
          </button>
          {!data.demo?.public ? (
            <button
              className="secondary full"
              onClick={() => {
                setEntry(false);
                setView("connections");
                sessionStorage.setItem("relay.entered", "1");
              }}
            >
              <Link2 size={17} />
              {tr("Connect my workspace")}
            </button>
          ) : (
            <p className="fine-print">
              {tr(
                "Private browser workspace · expires after 2 hours. Hosting inactivity, restarts or redeploys can reset it sooner. Use sample documents.",
              )}
            </p>
          )}
          <div className="demo-disclosure">
            <Radio size={18} />
            <p>
              <strong>
                {data.demo?.public
                  ? tr("Public demo · mandatory GCP acceptance pending")
                  : tr("Live demo: cloud setup required")}
              </strong>
              {data.agent.provider === "gemini_developer"
                ? tr(
                    "Alternative Gemini is configured; Agent Engine and real Calendar acceptance remain pending.",
                  )
                : data.demo?.public
                  ? tr(
                      "Illustrative course data. Calendar actions are simulated. GitHub reads are real. Gemini/Agent Engine and real Calendar acceptance remain pending.",
                    )
                  : tr(
                      "Course examples are illustrative. The local Calendar is simulated. GitHub public reads are real. No Gemini success or cloud deployment is claimed.",
                    )}
            </p>
          </div>
          <LiveAccess
            key={data.workspace_id}
            data={data}
            consent={processingConsent}
            onConsent={(value) =>
              setProcessingWorkspace(value ? data.workspace_id || null : null)
            }
          />
        </Modal>
      ) : null}
      {commands ? (
        <Modal
          title={tr("What would you like to do?")}
          onClose={() => setCommands(false)}
        >
          <div className="command-list">
            {(Object.keys(icons) as View[]).map((v) => {
              const Icon = icons[v];
              return (
                <button
                  key={v}
                  onClick={() => {
                    setView(v);
                    setCommands(false);
                  }}
                >
                  <Icon size={18} />
                  {t[v]}
                  <ArrowRight size={15} />
                </button>
              );
            })}
            <button
              onClick={() => {
                setCommands(false);
                void repair();
              }}
            >
              <Sparkles size={18} />
              {t.repair}
              <ArrowRight size={15} />
            </button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
