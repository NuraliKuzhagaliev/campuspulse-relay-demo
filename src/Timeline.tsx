import { useMemo, useState } from "react";
import { CalendarDays, LockKeyhole } from "lucide-react";
import { useLocale, weekRange, weekdayText } from "./i18n";
import type { Plan, Snapshot } from "./types";
const dateKey = (at: number, zone: string) => {
  const p = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(at);
  return ["year", "month", "day"]
    .map((k) => p.find((x) => x.type === k)!.value)
    .join("-");
};
export function dayStart(key: string, zone: string) {
  let lo = Date.parse(key + "T00:00:00Z") - 36 * 3600000,
    hi = lo + 72 * 3600000;
  while (hi - lo > 1) {
    const mid = Math.floor((lo + hi) / 2);
    if (dateKey(mid, zone) < key) lo = mid;
    else hi = mid;
  }
  return hi;
}
const addDate = (key: string, days: number) => {
  const d = new Date(key + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};
export function Timeline({
  data,
  plan,
  onBlock,
  list,
  setList,
}: {
  data: Snapshot;
  plan: Plan | null;
  onBlock: (id: string) => void;
  list: boolean;
  setList: (v: boolean) => void;
}) {
  const { tr, lang, locale } = useLocale();
  const [shift, setShift] = useState(0);
  const zone = data.settings.timezone;
  const days = useMemo(
    () =>
      Array.from({ length: 7 }, (_, i) => {
        const key = addDate(data.settings.anchor, shift + i);
        return {
          key,
          start: dayStart(key, zone),
          end: dayStart(addDate(key, 1), zone),
          date: new Date(key + "T12:00:00Z"),
        };
      }),
    [data.settings.anchor, shift, zone],
  );
  const clock = (value: number | string) =>
    new Intl.DateTimeFormat(locale, {
      timeZone: zone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
      timeZoneName: "shortOffset",
    }).format(new Date(value));
  const blocks = plan?.blocks || [];
  const observed = [
    ...data.settings.windows,
    ...blocks,
    ...(data.calendar_events || []).flatMap((e) =>
      e.start.dateTime && e.end.dateTime
        ? [{ start: e.start.dateTime, end: e.end.dateTime }]
        : [],
    ),
  ];
  const extents = days.flatMap((d) =>
    observed.flatMap((w) => {
      const a = Math.max(Date.parse(w.start), d.start),
        b = Math.min(Date.parse(w.end), d.end);
      return b > a ? [(a - d.start) / 3600000, (b - d.start) / 3600000] : [];
    }),
  );
  const startHour = Math.max(
      0,
      Math.floor(extents.length ? Math.min(...extents) : 9) - 1,
    ),
    endHour = Math.min(
      Math.max(...days.map((d) => (d.end - d.start) / 3600000)),
      Math.ceil(extents.length ? Math.max(...extents) : 20) + 1,
    );
  const pieces = (a: string, b: string, day: (typeof days)[number]) => {
    const start = Math.max(Date.parse(a), day.start + startHour * 3600000),
      end = Math.min(Date.parse(b), day.end, day.start + endHour * 3600000);
    return end > start
      ? {
          top: ((start - day.start) / 3600000 - startHour) * 64,
          height: Math.max(18, ((end - start) / 3600000) * 64 - 3),
        }
      : null;
  };
  const height = (endHour - startHour) * 64;
  return (
    <section className="timeline-card">
      <div className="calendar-toolbar">
        <div className="calendar-range">
          <CalendarDays size={18} />
          <strong>{weekRange(days[0].date, days[6].date, lang)}</strong>
          <span>{zone}</span>
        </div>
        <div className="segmented">
          <button
            onClick={() => setShift(shift - 7)}
            aria-label={tr("Previous week")}
          >
            ←
          </button>
          <button
            onClick={() => setShift(shift + 7)}
            aria-label={tr("Next week")}
          >
            →
          </button>
          <button aria-pressed={!list} onClick={() => setList(false)}>
            {tr("Week")}
          </button>
          <button aria-pressed={list} onClick={() => setList(true)}>
            {tr("List")}
          </button>
        </div>
      </div>
      {list ? (
        <div className="schedule-list">
          {blocks.length ? (
            blocks
              .filter(
                (b) =>
                  Date.parse(b.start) < days[6].end &&
                  Date.parse(b.end) > days[0].start,
              )
              .map((b, i) => (
                <button key={i} onClick={() => onBlock(b.task_id)}>
                  <span>
                    {dateKey(Date.parse(b.start), zone)} · {clock(b.start)}–
                    {clock(b.end)}
                  </span>
                  <strong>
                    {data.tasks.find((t) => t.id === b.task_id)?.title}
                  </strong>
                </button>
              ))
          ) : (
            <p className="empty">{tr("No study blocks generated")}</p>
          )}
        </div>
      ) : (
        <div
          className="calendar-scroll"
          tabIndex={0}
          role="region"
          aria-label={tr("Week")}
        >
          <div
            className="calendar-grid seven-day-grid"
            style={{
              gridTemplateColumns: "56px repeat(7,minmax(125px,1fr))",
              gridTemplateRows: `72px ${height + 1}px`,
            }}
          >
            <div className="time-header">
              <small>{zone}</small>
            </div>
            {days.map((d) => (
              <div className="day-header" key={d.key}>
                <span>{weekdayText(d.date, lang).toUpperCase()}</span>
                <strong>{d.date.getUTCDate()}</strong>
              </div>
            ))}
            <div className="time-labels">
              {Array.from({ length: Math.ceil(height / 64) }, (_, h) => (
                <span key={h} style={{ top: h * 64 + 2 }}>
                  {h + startHour}:00
                </span>
              ))}
            </div>
            {days.map((day) => (
              <div className="day-column" key={day.key}>
                {Array.from(
                  {
                    length: Math.ceil(
                      Math.min(endHour, (day.end - day.start) / 3600000) -
                        startHour,
                    ),
                  },
                  (_, h) => (
                    <div
                      className="hour-line zoned-hour"
                      key={h}
                      style={{ top: h * 64 }}
                    >
                      <small>
                        {clock(day.start + (h + startHour) * 3600000)}
                      </small>
                    </div>
                  ),
                )}
                {data.settings.windows.map((w, i) => {
                  const geometry = pieces(w.start, w.end, day);
                  return (
                    geometry && (
                      <div key={i} className="availability" style={geometry}>
                        <span>{tr("Available")}</span>
                      </div>
                    )
                  );
                })}
                {(data.calendar_events || []).map((e) => {
                  const a = e.start.dateTime,
                    b = e.end.dateTime;
                  if (!a || !b) return null;
                  const geometry = pieces(a, b, day);
                  return (
                    geometry && (
                      <div key={e.id} className="commitment" style={geometry}>
                        <LockKeyhole size={12} />
                        <span>
                          {e.id === "protected-commitment"
                            ? tr("Protected commitment")
                            : e.summary}
                        </span>
                      </div>
                    )
                  );
                })}
                {blocks.map((b, i) => {
                  const geometry = pieces(b.start, b.end, day);
                  if (!geometry) return null;
                  const task = data.tasks.find((t) => t.id === b.task_id);
                  const applied = (data.calendar_events || []).some(
                    (e) =>
                      e.extendedProperties?.private?.relay_task === b.task_id &&
                      e.start.dateTime === b.start &&
                      e.end.dateTime === b.end &&
                      data.receipts.some((r) =>
                        r.outcomes.some(
                          (o) =>
                            o.event_id === e.id &&
                            o.status === "verified" &&
                            o.etag === e.etag,
                        ),
                      ),
                  );
                  return (
                    <button
                      key={i}
                      className={
                        "study-block " +
                        ["blue", "mint", "peach"][
                          Math.max(
                            0,
                            data.tasks.findIndex((t) => t.id === b.task_id),
                          ) % 3
                        ] +
                        (geometry.height < 58 ? " compact" : "") +
                        (applied ? " applied" : "")
                      }
                      style={geometry}
                      onClick={() => onBlock(b.task_id)}
                      title={`${task?.title} · ${clock(b.start)}–${clock(b.end)}`}
                    >
                      <span className="block-time">{clock(b.start)}</span>
                      <strong>{task?.title}</strong>
                      <span className="block-meta">
                        {applied
                          ? tr(
                              data.calendar_mode === "live"
                                ? "Verified in Calendar"
                                : "Verified locally",
                            )
                          : tr("Source linked")}
                      </span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
      <footer className="calendar-footer">
        <span>{tr("Suggested study")}</span>
        <span>{tr("Protected time")}</span>
        <span>{tr("Available window")}</span>
        <small>
          {plan?.invalidated
            ? tr("Outdated plan · repair required")
            : plan
              ? tr("Validated allocation")
              : tr("No study blocks generated")}
        </small>
      </footer>
    </section>
  );
}
