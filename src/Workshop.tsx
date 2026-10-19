import { useRef, useState } from "react";
import { api } from "./api";
import { useLocale, label } from "./i18n";
import type { Plan, Snapshot, Task, Fact } from "./types";

type Remedy = {
  id: string;
  added_capacity_minutes: number;
  accepted_blocks_moved: number;
  additions: { start: string; end: string }[];
  plan: Plan;
};
type Rescue = {
  id: string;
  minimum_proven: boolean;
  no_allowed_remedy: boolean;
  combinations_checked: number;
  bottlenecks: {
    total_shortage_minutes: number;
    deadlines: { deadline: string; missing_minutes: number }[];
  };
  remedies: Remedy[];
};
type Preflight = {
  assessment_status?:string;
  id: string;
  task_id: string;
  missing_count: number;
  draft: { filename: string; words: number };
  results: {
    requirement: Fact;
    status: string;
    observed: Record<string, unknown>;
  }[];
};

export function Workshop({
  data,
  refresh,
  openSource,
  onPlan,
  work,
  busy,
}: {
  data: Snapshot;
  refresh: () => Promise<unknown>;
  openSource: (id: string, page?: number) => Promise<void>;
  onPlan: (p: Plan, proposal?: boolean) => void;
  work: (label: string, fn: () => Promise<void>) => Promise<void>;
  busy: boolean;
}) {
  const { tr, locale, lang } = useLocale();
  const [taskId, setTaskId] = useState(data.tasks[0]?.id || "");
  const [target, setTarget] = useState("");
  const [course, setCourse] = useState(""),
    [term, setTerm] = useState(""),
    [assignmentKey, setKey] = useState("");
  const [additions, setAdditions] = useState<{ start: string; end: string }[]>(
    [],
  );
  const [start, setStart] = useState(""),
    [end, setEnd] = useState("");
  const [loseWednesday, setLoseWednesday] = useState(true);
  const [rescue, setRescue] = useState<Rescue | null>(null);
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [extra, setExtra] = useState(60),
    [exception, setException] = useState("");
  const [draft, setDraft] = useState<{ name: string; content: string } | null>(
    null,
  );
  const draftInput = useRef<HTMLInputElement>(null);
  const task = data.tasks.find((t) => t.id === taskId);
  async function selectedDraft(file?: File) {
    await work("Checking selected draft", async () => {
      let selected;
      if (file) {
        if (file.size > 2 * 1024 * 1024)
          throw new Error("UNSUPPORTED_INPUT: Draft exceeds the upload limit.");
        const bytes = new Uint8Array(await file.arrayBuffer());
        let binary = "";
        for (let i = 0; i < bytes.length; i += 8192)
          binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
        selected = { name: file.name, content: btoa(binary) };
      } else selected = await window.relay?.importFile();
      if (!selected || !task) return;
      setDraft(selected);
      setPreflight(
        await api<Preflight>("/preflight", "POST", {
          ...selected,
          task_id: task.id,
        }),
      );
    });
  }
  const unresolved = data.tasks.filter(
    (t) => t.identity?.status === "unresolved",
  );
  return (
    <section className="workshop" aria-label={tr("Judge challenge")}>
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            {tr("Your document. Your constraints.")}
          </span>
          <h2>{tr("Judge challenge")}</h2>
        </div>
      </div>
      <p>
        {tr(
          "Import your own permitted course brief in Evidence. Confirm its course and term, inspect exact quotes, then repair the week. This visitor owns the evidence below.",
        )}
      </p>
      <ol className="challenge-steps">
        <li>{tr("Import and confirm evidence")}</li>
        <li>{tr("Compare recovery")}</li>
        <li>{tr("Review a fresh approval")}</li>
        <li>{tr("Inspect read-back")}</li>
      </ol>
      {unresolved.length > 0 && (
        <div className="mapping-panel">
          <h3>{tr("Confirm assignment mapping")}</h3>
          <p>
            {tr(
              "Missing course or term creates a separate draft. Link it only when you know it is the same assignment.",
            )}
          </p>
          <label>
            {tr("Assignment")}
            <select value={taskId} onChange={(e) => setTaskId(e.target.value)}>
              {data.tasks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title} · {t.course}
                </option>
              ))}
            </select>
          </label>
          <label>
            {tr("Existing assignment")}
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">{tr("Create a separate assignment")}</option>
              {data.tasks
                .filter((t) => t.identity?.status === "confirmed")
                .map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.course} · {t.title} · {t.identity.term}
                  </option>
                ))}
            </select>
          </label>
          {!target && (
            <div className="input-grid">
              <label>
                {tr("Course")}
                <input
                  value={course}
                  onChange={(e) => setCourse(e.target.value)}
                  maxLength={180}
                />
              </label>
              <label>
                {tr("Academic term")}
                <input
                  value={term}
                  onChange={(e) => setTerm(e.target.value)}
                  maxLength={100}
                />
              </label>
              <label>
                {tr("Stable assignment key")}
                <input
                  value={assignmentKey}
                  onChange={(e) => setKey(e.target.value)}
                  maxLength={180}
                />
              </label>
            </div>
          )}
          <button
            className="secondary"
            disabled={
              busy ||
              !task ||
              (!target &&
                (!course.trim() || !term.trim() || !assignmentKey.trim()))
            }
            onClick={() =>
              void work("Confirming mapping", async () => {
                await api(
                  "/sources/" + task!.source_ids[0] + "/mapping",
                  "POST",
                  {
                    section_key: task!.section_key,
                    course,
                    term,
                    assignment_key: assignmentKey,
                    target_id: target || null,
                  },
                );
                await refresh();
                setTarget("");
              })
            }
          >
            {tr("Confirm mapping")}
          </button>
        </div>
      )}
      <div className="workshop-card">
        <h3>{tr("Minimal rescue")}</h3>
        <p>
          {tr(
            "Offer up to five availability additions you permit. Compare combinations without changing deadlines, protected commitments or required effort.",
          )}
        </p>
        <label className="check">
          <input
            type="checkbox"
            checked={loseWednesday}
            onChange={(e) => setLoseWednesday(e.target.checked)}
          />
          {tr("Lose Wednesday afternoon")}
        </label>
        <div className="input-grid">
          <label>
            {tr("Candidate start (ISO with offset)")}
            <input
              value={start}
              onChange={(e) => setStart(e.target.value)}
              placeholder="2026-10-20T16:00:00+05:00"
            />
          </label>
          <label>
            {tr("Candidate end (ISO with offset)")}
            <input
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              placeholder="2026-10-20T18:00:00+05:00"
            />
          </label>
        </div>
        <button
          className="text-button"
          disabled={!start || !end || additions.length >= 5}
          onClick={() => {
            setAdditions([...additions, { start, end }]);
            setStart("");
            setEnd("");
            setRescue(null);
          }}
        >
          {tr("Add permitted option")}
        </button>
        <ul>
          {additions.map((w, i) => (
            <li key={i}>
              <code>
                {w.start} → {w.end}
              </code>
              <button
                className="text-button"
                onClick={() => {
                  setAdditions(additions.filter((_, j) => i !== j));
                  setRescue(null);
                }}
              >
                {tr("Remove")}
              </button>
            </li>
          ))}
        </ul>
        <button
          className="secondary"
          disabled={busy || !data.plan || data.plan.invalidated}
          onClick={() =>
            void work("Comparing permitted remedies", async () =>
              setRescue(
                await api<Rescue>("/rescue", "POST", {
                  scenario: loseWednesday ? { remove_weekday: 2 } : null,
                  additions,
                }),
              ),
            )
          }
        >
          {tr("Compare permitted remedies")}
        </button>
        {rescue && (
          <div role="status">
            <p>
              <strong>
                {tr("Total shortage")}:{" "}
                {rescue.bottlenecks.total_shortage_minutes} {tr("minutes")}
              </strong>
            </p>
            {rescue.bottlenecks.deadlines
              .filter((d) => d.missing_minutes > 0)
              .map((d) => (
                <p key={d.deadline}>
                  {new Date(d.deadline).toLocaleString(locale)}:{" "}
                  {d.missing_minutes} {tr("minutes missing before deadline")}
                </p>
              ))}
            <p>
              {tr(
                rescue.minimum_proven
                  ? "Minimum among offered combinations"
                  : "Best found among offered alternatives",
              )}{" "}
              · {rescue.combinations_checked} {tr("combinations checked")}
            </p>
            {rescue.no_allowed_remedy && (
              <p>
                {tr(
                  "No offered combination restores feasibility. Offer time before the bottleneck deadline.",
                )}
              </p>
            )}
            {rescue.remedies.map((r, i) => (
              <div className="remedy" key={r.id}>
                <h4>
                  {tr("Option")} {i + 1} · +{r.added_capacity_minutes}{" "}
                  {tr("minutes")}
                </h4>
                <p>
                  {r.accepted_blocks_moved} {tr("accepted blocks would move")}
                </p>
                {r.additions.map((w) => (
                  <p key={w.start}>
                    {new Date(w.start).toLocaleString(locale)} →{" "}
                    {new Date(w.end).toLocaleString(locale)}
                  </p>
                ))}
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void work("Revalidating chosen remedy", async () => {
                      const p = await api<Plan>(
                        "/rescues/" + rescue.id + "/choose",
                        "POST",
                        { remedy_id: r.id },
                      );
                      setRescue(null);
                      await refresh();
                      onPlan(p, false);
                    })
                  }
                >
                  {tr("Use this availability and revalidate")}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="workshop-card">
        <h3>{tr("Submission preflight")}</h3>
        <p>
          {tr(
            "Checks structure against cited requirements. Headings and images do not prove correctness. No grade prediction or submission.",
          )}
        </p>
        <label>
          {tr("Assignment")}
          <select
            value={taskId}
            onChange={(e) => {
              setTaskId(e.target.value);
              setPreflight(null);
              setDraft(null);
            }}
          >
            {data.tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.course} · {t.title}
              </option>
            ))}
          </select>
        </label>
        <button
          className="secondary"
          disabled={busy || !task}
          onClick={() =>
            window.relay ? void selectedDraft() : draftInput.current?.click()
          }
        >
          {tr("Select draft deliverable")}
        </button>
        <input
          hidden
          type="file"
          accept=".pdf,.md,.txt"
          ref={draftInput}
          onChange={(e) => {
            if (e.target.files?.[0]) void selectedDraft(e.target.files[0]);
            e.target.value = "";
          }}
        />
        {preflight && (
          <div>
            <p role="status">{tr(preflight.assessment_status==='not_assessed'?'No requirements assessed. Add and review cited rubric requirements before judging readiness.':'Structural checks only. Semantic correctness still requires review.')}</p>
            <p>
              <strong>{preflight.draft.filename}</strong> ·{" "}
              {preflight.draft.words} {tr("extracted words")}
            </p>
            {!preflight.results.length && (
              <p>
                {tr(
                  "No checkable submission requirements were found. Select a rubric with explicit requirements.",
                )}
              </p>
            )}
            {preflight.results.map((r, i) => (
              <div className="preflight-result" key={i}>
                <strong>{label(r.status, lang)}</strong>
                <blockquote>{r.requirement.quote}</blockquote>
                <button
                  className="text-button"
                  onClick={() =>
                    void openSource(r.requirement.source_id, r.requirement.page)
                  }
                >
                  {tr("Original requirement")} · {tr("Page")}{" "}
                  {r.requirement.page}
                </button>
                <details>
                  <summary>{tr("Observed metadata")}</summary>
                  <pre>{JSON.stringify(r.observed, null, 2)}</pre>
                </details>
              </div>
            ))}
            <label>
              {tr("Approved filename exception (requires review)")}
              <input
                value={exception}
                onChange={(e) => setException(e.target.value)}
                maxLength={500}
              />
            </label>
            <button
              className="text-button"
              disabled={busy || !draft || !exception.trim()}
              onClick={() =>
                void work("Checking selected draft", async () => {
                  const exceptions = Object.fromEntries(
                    preflight.results
                      .filter((r) =>
                        r.requirement.quote
                          .toLowerCase()
                          .startsWith("filename:"),
                      )
                      .map((r) => [r.requirement.id, exception]),
                  );
                  setPreflight(
                    await api<Preflight>("/preflight", "POST", {
                      ...draft,
                      task_id: preflight.task_id,
                      exceptions,
                    }),
                  );
                })
              }
            >
              {tr("Recheck with declared exception")}
            </button>
            {!!preflight.missing_count && (
              <div>
                <label>
                  {tr("Additional effort assumption (minutes)")}
                  <input
                    type="number"
                    min={30}
                    max={600}
                    step={30}
                    value={extra}
                    onChange={(e) => setExtra(Number(e.target.value))}
                  />
                </label>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void work("Comparing preflight recovery", async () =>
                      onPlan(
                        await api<Plan>(
                          "/preflights/" + preflight.id + "/recovery",
                          "POST",
                          { extra_minutes: extra },
                        ),
                        true,
                      ),
                    )
                  }
                >
                  {tr("Propose recovery for missing work")}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="workshop-card">
        <h3>{tr("Challenge evidence")}</h3>
        <p>
          {tr(
            "Live, illustrative and recorded evidence remain distinct. Calendar read-back here uses the local adapter until real consent is verified.",
          )}
        </p>
        <p>
          {tr("Observed source versions")}: {data.sources.length} ·{" "}
          {tr("Current tasks")}: {data.tasks.length} ·{" "}
          {tr("Read-back receipts")}: {data.receipts.length}
        </p>
        <ul>
          {data.sources.map((s) => (
            <li key={s.id}>
              <button
                className="text-button"
                onClick={() => void openSource(s.id)}
              >
                {s.title}
              </button>{" "}
              <code>{s.version.slice(0, 8)}</code> ·{" "}
              {s.mode === "live_github"
                ? tr("Live GitHub observation")
                : tr("Illustrative or uploaded evidence")}
            </li>
          ))}
        </ul>
        <p>
          {tr(
            "Inspect relevant tool calls in Activity. Review plan changes in Recovery and approve only its fresh exact preview.",
          )}
        </p>
      </div>
    </section>
  );
}
