import { useState } from "react";
import { api } from "./api";
import { useLocale } from "./i18n";

export function CalendarRecovery({
  onRecovered,
}: {
  onRecovered: () => Promise<void>;
}) {
  const { tr } = useLocale();
  const [id, setId] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  return (
    <details>
      <summary>{tr("Reconnect an existing app-created calendar")}</summary>
      <p>
        {tr(
          "After a workspace expires, connect Google again in this browser. Enter your existing app-created Calendar ID to verify it without creating another calendar. This does not select it or authorize event writes.",
        )}
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setPending(true);
          setMessage("");
          try {
            await api("/connections/calendar/recover", "POST", {
              calendar_id: id.trim(),
            });
            await onRecovered();
            setMessage(
              tr(
                "Calendar verified. Select it from the authorized list before preparing a preview.",
              ),
            );
            setId("");
          } catch (error) {
            setMessage(String((error as Error).message));
          } finally {
            setPending(false);
          }
        }}
      >
        <label>
          {tr("Existing app-created Calendar ID")}
          <input
            value={id}
            onChange={(e) => setId(e.target.value)}
            maxLength={240}
            required
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button className="secondary" disabled={pending || !id.trim()}>
          {tr("Verify existing calendar")}
        </button>
      </form>
      {message ? <p role="status">{message}</p> : null}
    </details>
  );
}
