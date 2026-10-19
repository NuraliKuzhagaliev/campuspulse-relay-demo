import { useEffect, useState } from "react";
import { api } from "./api";
import { useLocale } from "./i18n";
import type { Snapshot } from "./types";
type Field = {
  field: string;
  value: string | number | string[] | null;
  page: number;
  quote: string;
  validation_status: string;
  assumptions: string;
};
type Entity = {
  defaults?: Record<string, string | number | string[] | null>;
  id: string;
  entity_id: string;
  fields: Field[];
  applied?: boolean;
};
type Proposal = {
  id: string;
  source_id: string;
  source_version: string;
  entities: Entity[];
};
type Work = (label: string, fn: () => Promise<void>) => Promise<void>;
const local = (value: string, zone: string) => {
  const parts = new Intl.DateTimeFormat("sv-SE", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(value));
  return parts.replace(" ", "T");
};
function ReviewEntity({
  proposal,
  entity,
  data,
  work,
  done,
}: {
  proposal: Proposal;
  entity: Entity;
  data: Snapshot;
  work: Work;
  done: () => Promise<void>;
}) {
  const { tr } = useLocale();
  const first = (key: string) =>
    entity.defaults?.[key] ??
    entity.fields.find((f) => f.field === key && f.value !== null)?.value;
  const [values, setValues] = useState(() =>
    Object.fromEntries(
      ["title", "course", "term", "assignment_key", "minutes"].map((k) => [
        k,
        String(first(k) ?? ""),
      ]),
    ),
  );
  const due = first("due");
  const [date, setDate] = useState(
    typeof due === "string" && due.includes("T")
      ? local(due, data.settings.timezone)
      : "",
  );
  const [rubric, setRubric] = useState(
    entity.fields
      .filter((f) => f.field === "rubric")
      .flatMap((f) =>
        Array.isArray(f.value) ? f.value : [String(f.value ?? "")],
      )
      .join("\n"),
  );
  const [checked, setChecked] = useState(false);
  return (
    <form
      className="panel review-entity"
      data-testid="review-entity"
      onSubmit={(e) => {
        e.preventDefault();
        void work(tr("Confirm this assignment"), async () => {
          await api(
            `/extraction-proposals/${proposal.id}/${entity.id}/confirm`,
            "POST",
            {
              source_version: proposal.source_version,
              confirmed: checked,
              due_local: date || null,
              values: {
                ...values,
                minutes: values.minutes ? Number(values.minutes) : null,
                due: null,
                rubric: rubric.split("\n").filter(Boolean),
              },
            },
          );
          await done();
        });
      }}
    >
      <h3>{tr("Review one assignment")}</h3>
      <p>
        {tr(
          "Missing information stays unknown. Any correction is recorded as your interpretation; original quotations stay unchanged.",
        )}
      </p>
      <div className="review-fields">
        {(
          ["title", "course", "term", "assignment_key", "minutes"] as const
        ).map((key) => (
          <label key={key}>
            {tr(
              {
                title: "Assignment title",
                course: "Course",
                term: "Academic term",
                assignment_key: "Assignment key",
                minutes: "Exact effort in minutes",
              }[key],
            )}
            <input
              required={key !== "minutes"}
              type={key === "minutes" ? "number" : "text"}
              min={key === "minutes" ? 1 : undefined}
              max={key === "minutes" ? 10080 : undefined}
              maxLength={180}
              value={values[key]}
              onChange={(e) => setValues({ ...values, [key]: e.target.value })}
            />
          </label>
        ))}
        <label>
          {tr("Deadline in workspace timezone")} · {data.settings.timezone}
          <input
            type="datetime-local"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <label>
          {tr("Rubric items, one per line")}
          <textarea
            value={rubric}
            onChange={(e) => setRubric(e.target.value)}
          />
        </label>
      </div>
      <details>
        <summary>{tr("Citations and proposed interpretations")}</summary>
        {entity.fields.map((f, i) => (
          <div className="review-quote" key={i}>
            <strong>
              {f.field} · p.{f.page} · {f.validation_status}
            </strong>
            <blockquote>{f.quote}</blockquote>
            <p>
              {Array.isArray(f.value)
                ? f.value.join("; ")
                : String(f.value ?? "—")}
            </p>
            {f.assumptions && <p>{f.assumptions}</p>}
          </div>
        ))}
      </details>
      <label className="review-consent">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => setChecked(e.target.checked)}
        />
        {tr("I reviewed this assignment and confirm only these fields.")}
      </label>
      <button className="primary" disabled={!checked || entity.applied}>
        {entity.applied ? tr("Confirmed") : tr("Confirm this assignment")}
      </button>
    </form>
  );
}
export function DocumentReview({
  data,
  work,
  refresh,
  onExtract,
}: {
  data: Snapshot;
  work: Work;
  refresh: () => Promise<unknown>;
  onExtract: (id: string) => void;
}) {
  const { tr } = useLocale();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const load = async () =>
    setProposals(
      (await api<{ proposals: Proposal[] }>("/extraction-proposals")).proposals,
    );
  useEffect(() => {
    void load().catch(() => {});
  }, [data.workspace_id, data.events.length]);
  const done = async () => {
    await load();
    await refresh();
  };
  return (
    <section className="document-review" aria-label={tr("Document review")}>
      <h2>{tr("Document review")}</h2>
      <p>
        {tr(
          "PDF, Markdown, TXT and ICS · maximum 2 MiB. Text PDFs only, at most 100 pages and 250,000 extracted characters. No OCR.",
        )}
      </p>
      {data.sources.map((s) => (
        <div className="panel review-source" key={s.id}>
          <strong>{s.title}</strong>
          {s.import_notice ===
            "no_academic_assignments_detected_document_available_for_discussion" && (
            <p>
              {tr(
                "No academic assignments detected. The document is available for discussion; no tasks or successful academic extraction are claimed.",
              )}
            </p>
          )}
          <button
            className="secondary"
            onClick={() =>
              void work(tr("Review extracted fields"), async () => {
                await api(`/sources/${s.id}/review`, "POST");
                await load();
              })
            }
          >
            {tr("Review extracted fields")}
          </button>
          <button className="secondary" onClick={() => onExtract(s.id)}>
            {tr("Propose with Gemini")}
          </button>
        </div>
      ))}
      <p>
        {tr(
          "Gemini proposals require free-service processing consent below. They do not change coursework until you review and confirm each assignment.",
        )}
      </p>
      <button
        className="text-button"
        onClick={() => void work(tr("Refresh proposals"), load)}
      >
        {tr("Refresh proposals")}
      </button>
      {proposals.flatMap((p) =>
        p.entities
          .filter((e) => !e.applied)
          .map((e) => (
            <ReviewEntity
              key={p.id + e.id}
              proposal={p}
              entity={e}
              data={data}
              work={work}
              done={done}
            />
          )),
      )}
    </section>
  );
}

export function PlanningContext({
  data,
  work,
  refresh,
}: {
  data: Snapshot;
  work: Work;
  refresh: () => Promise<unknown>;
}) {
  const { tr } = useLocale();
  const [zone, setZone] = useState(data.settings.timezone);
  const [start, setStart] = useState(data.settings.anchor);
  const [end, setEnd] = useState(() => {
    const d = new Date(data.settings.anchor + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + 6);
    return d.toISOString().slice(0, 10);
  });
  const [a, setA] = useState("18:00"),
    [b, setB] = useState("20:00"),
    [days, setDays] = useState([0, 1, 2, 3, 4]);
  return (
    <details
      className="panel planning-context"
      open={!data.settings.windows.length}
    >
      <summary>{tr("Planning context")}</summary>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void work(tr("Save planning context"), async () => {
            await api("/planning-context", "POST", {
              timezone: zone,
              start_date: start,
              end_date: end,
              start_time: a,
              end_time: b,
              weekdays: days,
            });
            await refresh();
          });
        }}
      >
        <div className="review-fields">
          <label>
            {tr("Workspace timezone")}
            <input
              aria-label={tr("Workspace timezone")}
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              list="planning-zones"
            />
            <datalist id="planning-zones">
              {[
                "Asia/Almaty",
                "Asia/Qyzylorda",
                "Europe/London",
                "Europe/Berlin",
                "America/New_York",
                "UTC",
              ].map((z) => (
                <option key={z}>{z}</option>
              ))}
            </datalist>
          </label>
          <label>
            {tr("Range starts")}
            <input
              type="date"
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            {tr("Range ends")}
            <input
              type="date"
              required
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
          <label>
            {tr("Study starts")}
            <input
              type="time"
              required
              step={1800}
              value={a}
              onChange={(e) => setA(e.target.value)}
            />
          </label>
          <label>
            {tr("Study ends")}
            <input
              type="time"
              required
              step={1800}
              value={b}
              onChange={(e) => setB(e.target.value)}
            />
          </label>
        </div>
        <fieldset>
          <legend>{tr("Available weekdays")}</legend>
          {[
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
          ].map((name, i) => (
            <label key={i}>
              <input
                type="checkbox"
                checked={days.includes(i)}
                onChange={(e) =>
                  setDays(
                    e.target.checked
                      ? [...days, i]
                      : days.filter((d) => d !== i),
                  )
                }
              />
              {tr(name)}
            </label>
          ))}
        </fieldset>
        <p>
          {tr(
            "A finish earlier than the start continues after midnight. Empty weekdays mean no availability. Original source deadlines are never moved.",
          )}
        </p>
        <button className="secondary">{tr("Save planning context")}</button>
      </form>
    </details>
  );
}
