import {
  useLayoutEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { CalendarDays, ChevronLeft, ChevronRight, X } from "lucide-react";
import {
  useLocale,
  calendarMonthName,
  calendarDateLabel,
  weekdayText,
} from "./i18n";

const iso = (date: Date) => date.toISOString().slice(0, 10);
function parse(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(value + "T12:00:00Z");
  return Number.isFinite(date.getTime()) && iso(date) === value ? date : null;
}

/** The app locale owns this calendar; native browser/Windows date pickers are not used. */
export function LocalizedDateInput({
  label,
  value,
  onChange,
  required = false,
  timezone = "UTC",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  timezone?: string;
}) {
  const { tr, lang } = useLocale();
  const today = () => {
    const parts = new Intl.DateTimeFormat("en-CA", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: timezone,
    }).formatToParts(new Date());
    const part = (kind: string) => parts.find((p) => p.type === kind)!.value;
    return parse(`${part("year")}-${part("month")}-${part("day")}`)!;
  };
  const id = useId(),
    dialog = useRef<HTMLDialogElement>(null),
    opener = useRef<HTMLButtonElement>(null),
    input = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const wasOpen = useRef(false);
  const pendingFocus = useRef<string | null>(null);
  const [cursor, setCursor] = useState(() => parse(value) || today());
  const [focusDate, setFocusDate] = useState(value);
  const year = cursor.getUTCFullYear(),
    month = cursor.getUTCMonth();
  // Explicit dictionaries also work in browsers/Electron builds lacking Kazakh ICU data.
  const heading = `${calendarMonthName(month, lang)} ${year}`;
  const first = new Date(Date.UTC(year, month, 1, 12));
  const leading = (first.getUTCDay() + 6) % 7;
  const days = Array.from(
    { length: 42 },
    (_, index) => new Date(Date.UTC(year, month, index - leading + 1, 12)),
  );
  useLayoutEffect(() => {
    if (open) {
      dialog.current?.showModal();
      wasOpen.current = true;
      dialog.current
        ?.querySelector<HTMLButtonElement>('.date-picker-grid [tabindex="0"]')
        ?.focus();
    } else if (wasOpen.current) {
      opener.current?.focus();
      wasOpen.current = false;
    }
  }, [open]);
  useLayoutEffect(() => {
    if (open && pendingFocus.current) {
      dialog.current
        ?.querySelector<HTMLButtonElement>(
          `[data-date="${pendingFocus.current}"]`,
        )
        ?.focus();
      pendingFocus.current = null;
    }
  }, [open, focusDate, month, year]);
  useLayoutEffect(() => {
    input.current?.setCustomValidity(
      !value || parse(value) ? "" : tr("Enter a valid date as YYYY-MM-DD."),
    );
  }, [value, tr]);
  function close() {
    dialog.current?.close();
    setOpen(false);
  }
  function moveMonth(delta: number) {
    const next = new Date(Date.UTC(year, month + delta, 1, 12));
    setCursor(next);
    setFocusDate(iso(next));
  }
  function choose(date: Date) {
    onChange(iso(date));
    close();
  }
  function arrow(event: KeyboardEvent, date: Date) {
    const shift = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[
      event.key
    ];
    if (shift === undefined) return;
    event.preventDefault();
    const next = new Date(date);
    next.setUTCDate(next.getUTCDate() + shift);
    const nextValue = iso(next);
    pendingFocus.current = nextValue;
    setCursor(next);
    setFocusDate(nextValue);
  }
  return (
    <div className="localized-date-field">
      <label htmlFor={id}>{label}</label>
      <div className="date-input-row">
        <input
          ref={input}
          id={id}
          type="text"
          inputMode="numeric"
          value={value}
          required={required}
          pattern="[0-9]{4}-[0-9]{2}-[0-9]{2}"
          placeholder={tr("YYYY-MM-DD")}
          maxLength={10}
          onChange={(e) => onChange(e.target.value)}
          onInvalid={(e) =>
            e.currentTarget.setCustomValidity(
              value
                ? tr("Enter a valid date as YYYY-MM-DD.")
                : tr("Choose date"),
            )
          }
          onBlur={(e) =>
            e.target.setCustomValidity(
              !value || parse(value)
                ? ""
                : tr("Enter a valid date as YYYY-MM-DD."),
            )
          }
          onInput={(e) => e.currentTarget.setCustomValidity("")}
        />
        <button
          ref={opener}
          type="button"
          className="date-open icon-button"
          aria-label={`${tr("Open calendar")}: ${label}`}
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => {
            const date = parse(value) || today();
            setCursor(date);
            setFocusDate(iso(date));
            setOpen(true);
          }}
        >
          <CalendarDays size={19} />
        </button>
      </div>
      {open && (
        <dialog
          ref={dialog}
          className="localized-calendar"
          aria-label={`${tr("Choose date")}: ${label}`}
          onCancel={(e) => {
            e.preventDefault();
            close();
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              const r = e.currentTarget.getBoundingClientRect();
              if (
                e.clientX < r.left ||
                e.clientX > r.right ||
                e.clientY < r.top ||
                e.clientY > r.bottom
              )
                close();
            }
          }}
        >
          <div className="date-picker-heading">
            <button
              type="button"
              className="icon-button"
              aria-label={tr("Previous month")}
              onClick={() => moveMonth(-1)}
            >
              <ChevronLeft size={19} />
            </button>
            <strong aria-live="polite" data-testid="date-month-heading">
              {heading}
            </strong>
            <button
              type="button"
              className="icon-button"
              aria-label={tr("Next month")}
              onClick={() => moveMonth(1)}
            >
              <ChevronRight size={19} />
            </button>
            <button
              type="button"
              className="icon-button"
              aria-label={tr("Close calendar")}
              onClick={close}
            >
              <X size={19} />
            </button>
          </div>
          <div className="date-picker-month-controls">
            <select
              aria-label={tr("Month")}
              value={month}
              onChange={(e) => {
                const date = new Date(Date.UTC(year, +e.target.value, 1, 12));
                setCursor(date);
                setFocusDate(iso(date));
              }}
            >
              {Array.from({ length: 12 }, (_, m) => (
                <option key={m} value={m}>
                  {calendarMonthName(m, lang)}
                </option>
              ))}
            </select>
            <select
              aria-label={tr("Year")}
              value={year}
              onChange={(e) => {
                const date = new Date(Date.UTC(+e.target.value, month, 1, 12));
                setCursor(date);
                setFocusDate(iso(date));
              }}
            >
              {Array.from(
                { length: Math.max(2100, year) - Math.min(1900, year) + 1 },
                (_, i) => Math.min(1900, year) + i,
              ).map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </div>
          <div role="grid" aria-label={heading} className="date-picker-grid">
            <div role="row" className="date-picker-grid-row">
              {Array.from({ length: 7 }, (_, d) => (
                <span key={d} role="columnheader">
                  {weekdayText(new Date(Date.UTC(2026, 0, 5 + d)), lang)}
                </span>
              ))}
            </div>
            {Array.from({ length: 6 }, (_, row) => (
              <div key={row} role="row" className="date-picker-grid-row">
                {days.slice(row * 7, row * 7 + 7).map((date) => (
                  <div
                    key={iso(date)}
                    role="gridcell"
                    aria-selected={iso(date) === value}
                  >
                    <button
                      type="button"
                      data-date={iso(date)}
                      aria-label={calendarDateLabel(date, lang)}
                      className={`${date.getUTCMonth() !== month ? "outside-month" : ""} ${iso(date) === value ? "selected-date" : ""}`}
                      tabIndex={
                        iso(date) === (focusDate || iso(first)) ? 0 : -1
                      }
                      onKeyDown={(e) => arrow(e, date)}
                      onClick={() => choose(date)}
                    >
                      {date.getUTCDate()}
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="date-picker-footer">
            <button
              type="button"
              className="secondary"
              onClick={() => choose(today())}
            >
              {tr("Today")}
            </button>
            {!required && (
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  onChange("");
                  close();
                }}
              >
                {tr("Clear date")}
              </button>
            )}
          </div>
          <p className="date-picker-format-hint">
            {tr(
              "Date format: YYYY-MM-DD. Use arrow keys to move between days.",
            )}
          </p>
        </dialog>
      )}
    </div>
  );
}

export function HalfHourSelect({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
      >
        {Array.from(
          { length: 48 },
          (_, i) =>
            `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`,
        ).map((time) => (
          <option key={time}>{time}</option>
        ))}
      </select>
    </div>
  );
}
