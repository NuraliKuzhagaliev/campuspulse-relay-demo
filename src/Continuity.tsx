import { useEffect, useRef, useState } from "react";
import { api, setCsrf } from "./api";
import { useLocale, errorMessage, label } from "./i18n";
import type { Snapshot, Task, Plan } from "./types";

type Log = {
  id: string;
  task_id: string;
  duration_minutes: number;
  revision: number;
  origin: string;
  created_at: string;
  corrections: { duration_minutes: number; reason: string }[];
};
type Session = {
  id: string;
  task_id: string;
  status: string;
  revision: number;
  active_seconds: number;
  started_at: string;
};
type Gate = {
  id: string;
  task_id: string;
  repo: string;
  number: number;
  status: string;
  eta?: string;
  archived?: boolean;
  downstream_task_ids: string[];
  last_error?: { code: string };
  observation?: {
    url: string;
    state: string;
    merged: boolean;
    merged_at: string | null;
    head_sha: string;
    merge_sha: string;
    observed_at: string;
    last_checked_at: string;
  };
};
type AdditionState = {
  revision: number;
  logs: Log[];
  sessions: Session[];
  gates: Gate[];
  notifications: { id: string; task_id: string }[];
};
type Runner = (fn: () => Promise<void>) => Promise<void>;
const requestId = () => crypto.randomUUID().replaceAll("-", "");
const fileValue = async (file: File) => {
  if (file.size > 2 * 1024 * 1024)
    throw new Error("PASSPORT_TOO_LARGE: Portable workspace limit is 2 MiB.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  let text = "";
  for (let i = 0; i < bytes.length; i += 8192)
    text += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return { name: file.name, content: btoa(text) };
};

export function Continuity({
  data,
  refresh,
  task,
  compact = false,
}: {
  data: Snapshot;
  refresh: () => Promise<unknown>;
  task?: Task;
  compact?: boolean;
}) {
  const { tr, lang } = useLocale();
  const [open, setOpen] = useState(compact),
    [tab, setTab] = useState("progress");
  const [state, setState] = useState<AdditionState | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const lock = useRef(false),
    generation = useRef(0),
    notified = useRef(new Set<string>());
  async function load() {
    setState(await api<AdditionState>("/additions"));
  }
  useEffect(() => {
    if (!open) return;
    let current = true;
    api<AdditionState>("/additions")
      .then((s) => {
        if (current) setState(s);
      })
      .catch((e) => {
        if (current) setError((e as Error).message);
      });
    return () => {
      current = false;
      generation.current++;
    };
  }, [open, data.additions_revision]);
  useEffect(() => {
    for (const n of state?.notifications || []) {
      if (notified.current.has(n.id)) continue;
      notified.current.add(n.id);
      if (window.relay)
        void api<{ claimed: boolean }>(
          "/gates/notifications/" + n.id + "/claim",
          "POST",
        )
          .then((r) =>
            r.claimed
              ? window.relay?.notify(
                  tr("Handoff condition observed"),
                  data.tasks.find((t) => t.id === n.task_id)?.title ||
                    tr("Handoff Radar"),
                )
              : undefined,
          )
          .catch(() => undefined);
    }
  }, [state?.notifications, data.tasks, tr]);
  const run: Runner = async (fn) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await fn();
      await load();
      await refresh();
    } catch (e) {
      setError((e as Error).message);
      await load().catch(() => undefined);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  return (
    <section className="continuity" aria-label={tr("Progress & continuity")}>
      {!compact && (
        <button
          className="continuity-toggle"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          <span>
            <span className="eyebrow">{tr("KEEP THE THREAD")}</span>
            <strong>{tr("Progress & continuity")}</strong>
          </span>
          <span aria-hidden="true">{open ? "−" : "+"}</span>
        </button>
      )}
      {open && (
        <>
          <p className="fine-print">
            {tr(
              "Your work, decisions and handoffs. Deterministic services; no model or live Calendar connection.",
            )}
          </p>
          {data.settings.portable_origin && (
            <p className="offline-banner">
              {tr(
                "Restored copy: included text is an archived untrusted extract. Original files and upstream observations have not been reverified. Reconnect and recompute before operational use.",
              )}
            </p>
          )}
          {!compact && (
            <nav
              className="continuity-tabs"
              aria-label={tr("Progress & continuity")}
            >
              {[
                ["progress", "Progress & Remaining Work"],
                ["clarify", "Clarify First"],
                ["handoff", "Handoff Radar"],
                ["passport", "Workspace Passport"],
              ].map(([id, title]) => (
                <button
                  key={id}
                  className={tab === id ? "selected" : ""}
                  aria-pressed={tab === id}
                  onClick={() => setTab(id)}
                >
                  {tr(title)}
                </button>
              ))}
            </nav>
          )}
          {error && (
            <div className="error-banner" role="alert">
              {errorMessage(error, lang)}
              <details>
                <summary>{tr("Original diagnostic")}</summary>
                <pre>{error}</pre>
              </details>
              <button className="text-button" onClick={() => void run(load)}>
                {tr("Refresh and retry")}
              </button>
            </div>
          )}
          <div aria-live="polite" className="fine-print">
            {busy ? tr("Working on your request…") : ""}
          </div>
          {state && (tab === "progress" || compact) && (
            <ProgressPanel
              data={data}
              initialTask={task}
              state={state}
              run={run}
              busy={busy}
              reload={load}
            />
          )}
          {state && tab === "clarify" && !compact && (
            <ClarifyPanel data={data} state={state} run={run} busy={busy} />
          )}
          {state && tab === "handoff" && !compact && (
            <HandoffPanel data={data} state={state} run={run} busy={busy} />
          )}
          {tab === "passport" && !compact && (
            <PassportPanel
              data={data}
              run={run}
              busy={busy}
              refresh={refresh}
            />
          )}
        </>
      )}
    </section>
  );
}

function FuturePlan({
  plan,
  state,
  run,
  onAdopt,
}: {
  plan: Plan;
  state: AdditionState;
  run: Runner;
  onAdopt: () => void;
}) {
  const { tr } = useLocale();
  const p = plan as Plan & {
    block_diff?: { added: unknown[]; removed: unknown[] };
    historical_blocks?: unknown[];
  };
  return (
    <div className="decision-result">
      <h4>{tr("Review future-plan change")}</h4>
      <p>
        {tr("Future minutes: {count}", { count: plan.required_minutes })} ·{" "}
        {tr("Unscheduled minutes: {count}", {
          count: plan.unscheduled_minutes,
        })}
      </p>
      <p>
        {tr("Changed blocks: {removed} removed, {added} added", {
          removed: p.block_diff?.removed.length || 0,
          added: p.block_diff?.added.length || 0,
        })}
      </p>
      <p className="fine-print">
        {tr(
          "History stays recorded. Only eligible future work is recomputed. Calendar approval remains separate.",
        )}
      </p>
      <details>
        <summary>{tr("Inspect changed blocks")}</summary>
        <pre>{JSON.stringify(p.block_diff || plan.blocks, null, 2)}</pre>
      </details>
      <button
        className="primary"
        onClick={() =>
          void run(async () => {
            await api("/progress/" + plan.id + "/adopt", "POST", {
              expected_revision: state.revision,
            });
            onAdopt();
          })
        }
      >
        {tr("Adopt this future plan")}
      </button>
    </div>
  );
}

function ProgressPanel({
  data,
  initialTask,
  state,
  run,
  busy,
  reload,
}: {
  data: Snapshot;
  initialTask?: Task;
  state: AdditionState;
  run: Runner;
  busy: boolean;
  reload: () => Promise<void>;
}) {
  const { tr, locale } = useLocale();
  const [tid, setTid] = useState(initialTask?.id || data.tasks[0]?.id || "");
  const task = data.tasks.find((t) => t.id === tid);
  const logs = state.logs.filter((l) => l.task_id === tid);
  const active = state.sessions.find(
    (s) => s.task_id === tid && ["running", "interrupted"].includes(s.status),
  );
  const [duration, setDuration] = useState(45),
    [remaining, setRemaining] = useState(90),
    [category, setCategory] = useState(""),
    [interruptions, setInterruptions] = useState(""),
    [evidence, setEvidence] = useState("");
  const [proposal, setProposal] = useState<Plan | null>(null),
    [suggestion, setSuggestion] = useState<{
      sample_count: number;
      suggested_minutes: number | null;
      status: string;
      samples: unknown[];
    } | null>(null);
  const [owned, setOwned] = useState<string | null>(null),
    [interrupted, setInterrupted] = useState(false),
    [correction, setCorrection] = useState(""),
    [reason, setReason] = useState("");
  const timer = useRef<{ revision: number; tick: number } | null>(null),
    heartbeatBusy = useRef(false);
  useEffect(() => {
    setProposal(null);
    setSuggestion(null);
  }, [data.workspace_fingerprint]);
  useEffect(() => {
    if (!owned) return;
    const interrupt = () => {
      if (document.hidden) {
        setInterrupted(true);
        setOwned(null);
      }
    };
    document.addEventListener("visibilitychange", interrupt);
    const interval = window.setInterval(async () => {
      if (heartbeatBusy.current || !timer.current) return;
      heartbeatBusy.current = true;
      const tick = performance.now();
      try {
        const s = await api<Session>(
          "/work-sessions/" + owned + "/heartbeat",
          "POST",
          {
            delta_ms: tick - timer.current.tick,
            session_revision: timer.current.revision,
          },
        );
        timer.current = { revision: s.revision, tick };
        if (s.status !== "running") {
          setInterrupted(true);
          setOwned(null);
        }
        await reload();
      } catch {
        setInterrupted(true);
        setOwned(null);
      } finally {
        heartbeatBusy.current = false;
      }
    }, 10000);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", interrupt);
    };
  }, [owned]);
  if (!task) return null;
  const original = data.sources
    .flatMap((s) => s.facts)
    .filter((f) => f.task_id === tid && f.field === "minutes");
  async function mutate(action: string, values: Record<string, unknown> = {}) {
    return api<{ session?: Session }>("/tasks/" + tid + "/progress", "POST", {
      action,
      request_id: requestId(),
      expected_revision: state.revision,
      ...values,
    });
  }
  return (
    <div className="feature-panel" data-testid="progress-panel">
      <h3>{tr("Progress & Remaining Work")}</h3>
      {!initialTask && (
        <label>
          {tr("Coursework")}
          <select
            value={tid}
            onChange={(e) => {
              setTid(e.target.value);
              setProposal(null);
              setSuggestion(null);
            }}
          >
            {data.tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.course} · {t.title}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="effort-comparison">
        <div>
          <span>{tr("Source-stated effort")}</span>
          <strong>
            {original
              .map((f) => f.value)
              .filter((v, i, a) => a.indexOf(v) === i)
              .join(" / ") || tr("Unknown")}
          </strong>
        </div>
        <div>
          <span>{tr("Actual logged minutes")}</span>
          <strong>
            {new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(
              logs.reduce((sum, l) => sum + l.duration_minutes, 0),
            )}
          </strong>
        </div>
        <div>
          <span>{tr("Explicit remaining minutes")}</span>
          <strong>{task.progress?.remaining_minutes ?? tr("Unknown")}</strong>
        </div>
      </div>
      {task.progress?.remaining_minutes != null &&
        task.progress.remaining_minutes > 0 && (
          <p className="fine-print">
            {tr("Solver allocation rounds up to {count} minutes.", {
              count: Math.ceil(task.progress.remaining_minutes / 30) * 30,
            })}
          </p>
        )}
      <p className="fine-print">
        {tr(
          "The timer measures elapsed active session time. It does not prove attention, learning, completion or submission.",
        )}
      </p>
      <div className="feature-form">
        <label>
          {tr("Comparable task category")}
          <input
            value={category}
            maxLength={80}
            onChange={(e) => setCategory(e.target.value)}
          />
        </label>
        {!active ? (
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                const r = await mutate("start", { category });
                if (r.session) {
                  timer.current = {
                    revision: r.session.revision,
                    tick: performance.now(),
                  };
                  setOwned(r.session.id);
                  setInterrupted(false);
                }
              })
            }
          >
            {tr("Start work")}
          </button>
        ) : (
          <div className="decision-result">
            <strong>
              {owned && !interrupted
                ? tr("Session running")
                : tr("Interrupted session: confirm actual duration")}
            </strong>
            <p>
              {tr("Recorded active minutes: {count}", {
                count: Math.round(active.active_seconds / 6) / 10,
              })}
            </p>
            <p className="fine-print">
              {tr(
                "Reload, sleep or closing the app never confirms absent time. Review and correct the duration below.",
              )}
            </p>
          </div>
        )}
        <label>
          {tr("Actual minutes to record")}
          <input
            type="number"
            min={0.01}
            max={1440}
            step="0.01"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </label>
        <label>
          {tr("Interruptions or checklist outcomes (optional)")}
          <input
            value={interruptions}
            maxLength={500}
            onChange={(e) => setInterruptions(e.target.value)}
          />
        </label>
        <label>
          {tr("Evidence reference (optional)")}
          <select
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
          >
            <option value="">{tr("No evidence selected")}</option>
            {data.sources
              .flatMap((s) => s.facts)
              .filter((f) => f.task_id === tid)
              .map((f) => (
                <option key={f.id} value={f.id}>
                  {f.quote.slice(0, 100)}
                </option>
              ))}
          </select>
        </label>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await mutate(active ? "stop" : "log", {
                duration_minutes: duration,
                category,
                interruptions,
                evidence_id: evidence || null,
                ...(active ? { session_id: active.id } : {}),
              });
              setOwned(null);
              setProposal(null);
            })
          }
        >
          {active ? tr("Pause and confirm work log") : tr("Log work manually")}
        </button>
      </div>
      <h4>{tr("What remains?")}</h4>
      <p className="fine-print">
        {tr(
          "Logged time is never subtracted automatically. State remaining work or keep it unknown.",
        )}
      </p>
      <div className="feature-form">
        <label>
          {tr("Remaining minutes")}
          <input
            type="number"
            min={0.01}
            max={10080}
            step="0.01"
            value={remaining}
            onChange={(e) => setRemaining(Number(e.target.value))}
          />
        </label>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await mutate("remaining", { remaining_minutes: remaining });
              setProposal(null);
            })
          }
        >
          {tr("Save remaining estimate")}
        </button>
        <button
          className="text-button"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await mutate("unknown");
              setProposal(null);
            })
          }
        >
          {tr("Still unknown")}
        </button>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await mutate("complete");
              setProposal(null);
            })
          }
        >
          {tr("Confirm completed · student report")}
        </button>
      </div>
      <button
        className="primary"
        disabled={busy}
        onClick={() =>
          void run(async () =>
            setProposal(await api<Plan>("/progress/preview", "POST")),
          )
        }
      >
        {tr("Preview future plan")}
      </button>
      {proposal && (
        <FuturePlan
          plan={proposal}
          state={state}
          run={run}
          onAdopt={() => setProposal(null)}
        />
      )}
      <details>
        <summary>{tr("Progress history and corrections")}</summary>
        {logs.map((l) => (
          <article className="history-entry" key={l.id}>
            <strong>
              {l.duration_minutes} {tr("minutes")}
            </strong>
            <time>{new Date(l.created_at).toLocaleString(locale)}</time>
            <span>
              {tr(
                l.origin === "student_manual"
                  ? "Manual student report"
                  : "Student-confirmed timer",
              )}
            </span>
            {l.corrections.map((c, i) => (
              <p key={i}>
                {tr("Previous duration: {count}", {
                  count: c.duration_minutes,
                })}{" "}
                · {c.reason}
              </p>
            ))}
            <button
              className="text-button"
              onClick={() => {
                setCorrection(l.id);
                setDuration(l.duration_minutes);
              }}
            >
              {tr("Correct this log")}
            </button>
          </article>
        ))}
        {correction && (
          <div className="feature-form">
            <label>
              {tr("Correction reason")}
              <input
                value={reason}
                maxLength={500}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <button
              disabled={busy}
              className="secondary"
              onClick={() =>
                void run(async () => {
                  const log = logs.find((l) => l.id === correction);
                  if (!log) return;
                  await mutate("correct", {
                    log_id: log.id,
                    log_revision: log.revision,
                    duration_minutes: duration,
                    reason,
                  });
                  setCorrection("");
                })
              }
            >
              {tr("Save correction using actual minutes above")}
            </button>
          </div>
        )}
        <pre>{JSON.stringify(task.progress, null, 2)}</pre>
      </details>
      <details>
        <summary>{tr("Estimate suggestion from comparable history")}</summary>
        <p className="fine-print">
          {tr(
            "At least five completed tasks in this workspace with the same course/category and an estimate frozen before starting. Corrected logs use a median ratio capped at 0.5–2 and round up to 30 minutes. Imported history is excluded.",
          )}
        </p>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () =>
              setSuggestion(
                await api("/tasks/" + tid + "/estimate-suggestion"),
              ),
            )
          }
        >
          {tr("Check eligible history")}
        </button>
        {suggestion && (
          <div>
            <p>
              {tr("Eligible samples: {count}", {
                count: suggestion.sample_count,
              })}
            </p>
            {suggestion.suggested_minutes ? (
              <>
                <p>
                  {tr("Suggested minutes: {count}", {
                    count: suggestion.suggested_minutes,
                  })}
                </p>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      await mutate("remaining", {
                        remaining_minutes: suggestion.suggested_minutes,
                      });
                    })
                  }
                >
                  {tr("Use as my remaining estimate")}
                </button>
              </>
            ) : (
              <p>
                {tr(
                  "Insufficient comparable history. No personalized forecast is offered.",
                )}
              </p>
            )}
            <pre>{JSON.stringify(suggestion.samples, null, 2)}</pre>
          </div>
        )}
      </details>
    </div>
  );
}

type Candidate = {
  id: string;
  task_id: string | null;
  kind: string;
  impact_known: boolean;
  feasibility_changing: boolean;
  minutes_affected: number;
  blocks_affected: number;
  choices: {
    value: string | number | boolean | { start: string; end: string };
    quote?: string;
    page?: number;
    source_id?: string;
  }[];
};
type Clarification = {
  id: string;
  status: string;
  tested?: number;
  possible_in_selected_set?: number;
  candidates: Candidate[];
  branches: unknown[];
  gaps: unknown[];
  sources: unknown;
  duration_ms: number;
};
function ClarifyPanel({
  data,
  state,
  run,
  busy,
}: {
  data: Snapshot;
  state: AdditionState;
  run: Runner;
  busy: boolean;
}) {
  const { tr } = useLocale();
  const [result, setResult] = useState<Clarification | null>(null),
    [task, setTask] = useState(data.tasks[0]?.id || ""),
    [low, setLow] = useState(60),
    [high, setHigh] = useState(120),
    [include, setInclude] = useState(false);
  const job = useRef("");
  const cancelled = useRef(false);
  const [offeredStart, setOfferedStart] = useState(""),
    [offeredEnd, setOfferedEnd] = useState("");
  const lead = result?.candidates[0];
  useEffect(() => setResult(null), [data.workspace_fingerprint]);
  return (
    <div className="feature-panel" data-testid="clarify-panel">
      <h3>{tr("Clarify First")}</h3>
      <p>
        {tr(
          "Which unanswered question changes this schedule most? Compare cited alternatives and your explicitly offered bounds.",
        )}
      </p>
      <details>
        <summary>{tr("Offer effort bounds for a missing estimate")}</summary>
        <label>
          <input
            type="checkbox"
            checked={include}
            onChange={(e) => setInclude(e.target.checked)}
          />
          {tr("Include my two effort bounds")}
        </label>
        <div className="feature-form">
          <label>
            {tr("Coursework")}
            <select value={task} onChange={(e) => setTask(e.target.value)}>
              {data.tasks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.course} · {t.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            {tr("Lower offered minutes")}
            <input
              type="number"
              min={1}
              max={10080}
              value={low}
              onChange={(e) => setLow(Number(e.target.value))}
            />
          </label>
          <label>
            {tr("Upper offered minutes")}
            <input
              type="number"
              min={1}
              max={10080}
              value={high}
              onChange={(e) => setHigh(Number(e.target.value))}
            />
          </label>
        </div>
      </details>
      <details>
        <summary>{tr("Offer an availability question")}</summary>
        <div className="feature-form">
          <label>
            {tr("Candidate start (ISO with offset)")}
            <input
              value={offeredStart}
              maxLength={80}
              onChange={(e) => setOfferedStart(e.target.value)}
            />
          </label>
          <label>
            {tr("Candidate end (ISO with offset)")}
            <input
              value={offeredEnd}
              maxLength={80}
              onChange={(e) => setOfferedEnd(e.target.value)}
            />
          </label>
        </div>
        <p className="fine-print">
          {tr(
            "Compare this explicitly offered window with not adding it. Nothing changes until you choose.",
          )}
        </p>
      </details>
      <div className="row">
        <button
          className="primary"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              job.current = requestId();
              cancelled.current = false;
              const comparison = await api<Clarification>("/clarify", "POST", {
                request_id: job.current,
                bounds: include ? [{ task_id: task, values: [low, high] }] : [],
                offered_windows:
                  offeredStart && offeredEnd
                    ? [{ start: offeredStart, end: offeredEnd }]
                    : [],
              });
              if (!cancelled.current) setResult(comparison);
            })
          }
        >
          {tr("Compare schedule impact")}
        </button>
        {busy && job.current && (
          <button
            className="secondary"
            onClick={() => {
              cancelled.current = true;
              setResult(null);
              void api("/clarify/" + job.current + "/cancel", "POST").catch(
                () => undefined,
              );
            }}
          >
            {tr("Cancel comparison")}
          </button>
        )}
      </div>
      {result && (
        <div className="decision-result" aria-live="polite">
          <p>
            {tr("Branches tested: {tested} of {total}", {
              tested: result.tested || 0,
              total: result.possible_in_selected_set || 0,
            })}{" "}
            ·{" "}
            {tr(
              result.status === "complete"
                ? "Evaluated selected alternatives"
                : "Partial or unsupported analysis",
            )}
          </p>
          {lead ? (
            <>
              <h4>
                {data.tasks.find((t) => t.id === lead.task_id)?.title ||
                  tr("Offered availability window")}
              </h4>
              <p>
                {tr(
                  lead.feasibility_changing
                    ? "This answer changes feasibility in evaluated branches."
                    : lead.impact_known
                      ? "Observed schedule impact among evaluated branches."
                      : "Impact is unknown; unresolved inputs remain.",
                )}
              </p>
              <p>
                {tr("Affected minutes: {minutes}; changed blocks: {blocks}", {
                  minutes: lead.minutes_affected,
                  blocks: lead.blocks_affected,
                })}
              </p>
              <div className="clarify-options">
                {lead.choices.map((c, i) => (
                  <button
                    className="secondary"
                    key={i}
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await api("/clarify/" + result.id + "/answer", "POST", {
                          candidate_id: lead.id,
                          choice: i,
                          request_id: requestId(),
                          expected_revision: state.revision,
                        });
                        setResult(null);
                      })
                    }
                  >
                    <strong>
                      {typeof c.value === "object"
                        ? `${c.value.start} → ${c.value.end}`
                        : typeof c.value === "boolean"
                          ? tr("Do not add this window")
                          : String(c.value)}
                    </strong>
                    {c.quote && <blockquote>{c.quote}</blockquote>}
                    {c.page && (
                      <span>{tr("Page {count}", { count: c.page })}</span>
                    )}
                    <span>
                      {tr(
                        c.quote
                          ? "Choose cited evidence"
                          : "Accept my assumption",
                      )}
                    </span>
                  </button>
                ))}
              </div>
              <button
                className="text-button"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    await api("/clarify/" + result.id + "/answer", "POST", {
                      candidate_id: lead.id,
                      choice: null,
                      request_id: requestId(),
                      expected_revision: state.revision,
                    });
                    setResult(null);
                  })
                }
              >
                {tr("I don't know · keep the gap")}
              </button>
            </>
          ) : (
            <p>
              {tr(
                "No supported alternatives. Supply bounds or review unresolved source details.",
              )}
            </p>
          )}
          <p className="fine-print">
            {tr(
              "At most three binary uncertainties and eight joint branches, one second per solve, eight seconds overall. Unchanged sampled branches do not prove irrelevance; unknown is not infeasible.",
            )}
          </p>
          <details>
            <summary>{tr("Inspect all evaluated branches")}</summary>
            <pre>
              {JSON.stringify(
                {
                  candidates: result.candidates,
                  branches: result.branches,
                  gaps: result.gaps,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

function HandoffPanel({
  data,
  state,
  run,
  busy,
}: {
  data: Snapshot;
  state: AdditionState;
  run: Runner;
  busy: boolean;
}) {
  const { tr, locale } = useLocale();
  const [tid, setTid] = useState(data.tasks[0]?.id || ""),
    [repo, setRepo] = useState(data.settings.github_repo),
    [number, setNumber] = useState(1),
    [eta, setEta] = useState(""),
    [proposal, setProposal] = useState<Plan | null>(null),
    [conditional, setConditional] = useState<Plan | null>(null);
  const statuses: Record<string, string> = {
    unknown: "Unknown · revalidation needed",
    waiting: "Waiting · no assumed release time",
    condition_observed: "Condition observed · PR merged",
    stale: "Stale observation",
    unavailable: "Unavailable · previous observation retained",
    disabled: "Disabled by student",
  };
  useEffect(() => {
    setProposal(null);
    setConditional(null);
  }, [data.workspace_fingerprint]);
  return (
    <div className="feature-panel" data-testid="handoff-panel">
      <h3>{tr("Handoff Radar")}</h3>
      <p>
        {tr(
          "Link a public pull request that must be merged before this coursework begins. Closed alone does not mean merged.",
        )}
      </p>
      <div className="feature-form">
        <label>
          {tr("Coursework")}
          <select value={tid} onChange={(e) => setTid(e.target.value)}>
            {data.tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.course} · {t.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          {tr("Allowlisted owner/repository")}
          <input
            value={repo}
            maxLength={201}
            onChange={(e) => setRepo(e.target.value)}
          />
        </label>
        <label>
          {tr("Pull-request number")}
          <input
            type="number"
            min={1}
            max={100000000}
            value={number}
            onChange={(e) => setNumber(Number(e.target.value))}
          />
        </label>
        <label>
          {tr("Optional student ETA (ISO with offset)")}
          <input
            value={eta}
            maxLength={80}
            onChange={(e) => setEta(e.target.value)}
          />
        </label>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await api("/gates", "POST", {
                task_id: tid,
                repo,
                number,
                eta: eta || null,
                request_id: requestId(),
                expected_revision: state.revision,
              });
              setProposal(null);
            })
          }
        >
          {tr("Link PR-merged prerequisite")}
        </button>
      </div>
      <ul className="gate-list">
        {state.gates.map((g) => (
          <li key={g.id}>
            <div className="gate-chain">
              <strong>
                {g.repo} #{g.number}
              </strong>
              <span aria-hidden="true">→</span>
              <strong>
                {data.tasks.find((t) => t.id === g.task_id)?.title}
              </strong>
            </div>
            <p className="status-pill">
              {tr(statuses[g.status] || statuses.unknown)}
            </p>
            <p>
              {tr("Impacted coursework: {count}", {
                count: g.downstream_task_ids.length,
              })}
            </p>
            <p className="fine-print">
              {tr(
                "Latest safe handoff: unknown. No teammate finish time is assumed.",
              )}
            </p>
            {g.observation && (
              <details>
                <summary>{tr("Inspect GitHub observation")}</summary>
                <a href={g.observation.url} target="_blank" rel="noreferrer">
                  {g.observation.url}
                </a>
                <p>
                  {tr("Observed at")}{" "}
                  {new Date(g.observation.observed_at).toLocaleString(locale)}
                </p>
                <p>
                  {tr("Last checked at")}{" "}
                  {new Date(g.observation.last_checked_at).toLocaleString(
                    locale,
                  )}
                </p>
                <pre>{JSON.stringify(g.observation, null, 2)}</pre>
              </details>
            )}
            {g.last_error && (
              <p className="warning-text">{g.last_error.code}</p>
            )}
            <button
              className="secondary"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await api("/gates/" + g.id + "/observe", "POST");
                  setProposal(null);
                })
              }
            >
              {tr("Observe public PR")}
            </button>
            {g.status !== "disabled" && (
              <button
                className="text-button"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    await api("/gates/" + g.id + "/remove", "POST", {
                      request_id: requestId(),
                      expected_revision: state.revision,
                    });
                    setProposal(null);
                  })
                }
              >
                {tr("Remove this gate")}
              </button>
            )}
          </li>
        ))}
      </ul>
      <div className="row">
        <button
          className="primary"
          disabled={busy}
          onClick={() =>
            void run(async () =>
              setProposal(await api("/progress/preview", "POST")),
            )
          }
        >
          {tr("Preview observed handoff plan")}
        </button>
        <button
          className="secondary"
          disabled={busy}
          onClick={() =>
            void run(async () =>
              setConditional(await api("/gates/conditional-preview", "POST")),
            )
          }
        >
          {tr("Compare my conditional ETA")}
        </button>
      </div>
      {conditional && (
        <div className="decision-result">
          <strong>{tr("Conditional scenario · student ETA")}</strong>
          <p>
            {tr("Unscheduled minutes: {count}", {
              count: conditional.unscheduled_minutes,
            })}
          </p>
          <p className="fine-print">
            {tr(
              "This assumes your ETA. It is not an observed handoff and cannot authorize Calendar actions.",
            )}
          </p>
        </div>
      )}
      {proposal && (
        <FuturePlan
          plan={proposal}
          state={state}
          run={run}
          onAdopt={() => setProposal(null)}
        />
      )}
    </div>
  );
}

function PassportPanel({
  data,
  run,
  busy,
  refresh,
}: {
  data: Snapshot;
  run: Runner;
  busy: boolean;
  refresh: () => Promise<unknown>;
}) {
  const { tr } = useLocale();
  const [selected, setSelected] = useState(data.sources.map((s) => s.id)),
    [saved, setSaved] = useState<{
      file: unknown;
      preview: {
        bytes: number;
        sources: number;
        assignments: number;
        logs: number;
        gates: number;
      };
    } | null>(null),
    [staged, setStaged] = useState<{
      id: string;
      original_timezone?: string;
      restored_timezone?: string;
      sources: number;
      assignments: number;
      logs: number;
      gates: number;
      bytes: number;
    } | null>(null);
  const input = useRef<HTMLInputElement>(null);
  async function choose(file?: File) {
    await run(async () => {
      const chosen = file
        ? await fileValue(file)
        : await window.relay?.importFile("passport");
      if (!chosen) return;
      setStaged(await api("/passport/preview", "POST", chosen));
    });
  }
  async function download() {
    if (!saved) return;
    const text = JSON.stringify(saved.file);
    if (window.relay) {
      await window.relay.savePassport(saved.file);
      return;
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(
      new Blob([text], { type: "application/json" }),
    );
    a.download = "CampusPulse-RELAY.relay.json";
    a.click();
    window.setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  return (
    <div className="feature-panel" data-testid="passport-panel">
      <h3>{tr("Workspace Passport")}</h3>
      <p>
        {tr(
          "Manual file transfer between web and Windows. This is not automatic sync or permanent hosted storage.",
        )}
      </p>
      <p className="fine-print">
        {tr(
          "The file includes selected course extracts and personal progress. Keep it private and save it on D:. No credentials, approvals, writable Calendar connections or operation journals are included.",
        )}
      </p>
      <details>
        <summary>{tr("Select included sources")}</summary>
        {data.sources.map((s) => (
          <label className="check-row" key={s.id}>
            <input
              type="checkbox"
              checked={selected.includes(s.id)}
              onChange={(e) => {
                setSelected(
                  e.target.checked
                    ? [...selected, s.id]
                    : selected.filter((x) => x !== s.id),
                );
                setSaved(null);
              }}
            />
            {s.title}
          </label>
        ))}
      </details>
      <button
        className="primary"
        disabled={busy || !selected.length}
        onClick={() =>
          void run(async () =>
            setSaved(
              await api("/passport/export", "POST", { source_ids: selected }),
            ),
          )
        }
      >
        {tr("Preview portable workspace")}
      </button>
      {saved && (
        <div className="decision-result">
          <h4>{tr("Save portable workspace")}</h4>
          <p>
            {tr(
              "Sources: {sources}; assignments: {tasks}; work logs: {logs}; gates: {gates}",
              {
                sources: saved.preview.sources,
                tasks: saved.preview.assignments,
                logs: saved.preview.logs,
                gates: saved.preview.gates,
              },
            )}
          </p>
          <p>
            {tr("File size: {count} bytes", { count: saved.preview.bytes })}
          </p>
          <p>
            {tr(
              "Extracted copies included; original files are absent. Observations become archived claims. A checksum does not prove authenticity.",
            )}
          </p>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void run(download)}
          >
            {tr("Download .relay.json")}
          </button>
        </div>
      )}
      <hr />
      <h4>{tr("Restore portable workspace")}</h4>
      <input
        ref={input}
        hidden
        className="file-input"
        type="file"
        accept=".json"
        aria-label={tr("Portable workspace file")}
        onChange={(e) => {
          void choose(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <button
        className="secondary"
        disabled={busy}
        onClick={() => (window.relay ? void choose() : input.current?.click())}
      >
        {tr("Choose portable workspace")}
      </button>
      {staged && (
        <div className="decision-result">
          <h4>{tr("Review restore preview")}</h4>
          {staged.original_timezone !== staged.restored_timezone && (
            <p role="status">
              {tr(
                "This archive uses {original}. The restored workspace will use {target}; original evidence and absolute timestamps stay unchanged.",
                {
                  original: staged.original_timezone || "",
                  target: staged.restored_timezone || "",
                },
              )}
            </p>
          )}
          <p>
            {tr(
              "Sources: {sources}; assignments: {tasks}; work logs: {logs}; gates: {gates}",
              {
                sources: staged.sources,
                tasks: staged.assignments,
                logs: staged.logs,
                gates: staged.gates,
              },
            )}
          </p>
          <p>
            {tr(
              "A fresh isolated copy will open. Your current workspace stays intact. All plans and external observations require revalidation; no external action is authorized.",
            )}
          </p>
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                const session = await api<{ csrf: string; tenant: string }>(
                  "/passport/" + staged.id + "/restore",
                  "POST",
                );
                setCsrf(session.csrf);
                setStaged(null);
                await refresh();
              })
            }
          >
            {tr("Import as fresh copy and switch")}
          </button>
          <button className="text-button" onClick={() => setStaged(null)}>
            {tr("Cancel restore")}
          </button>
        </div>
      )}
    </div>
  );
}
