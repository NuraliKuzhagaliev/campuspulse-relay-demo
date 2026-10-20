import { useState } from "react";
import { api } from "./api";
import { useLocale, errorMessage } from "./i18n";
import type { Snapshot } from "./types";

export function LiveAccess({
  data,
  consent,
  onConsent,
}: {
  data: Snapshot;
  consent: boolean;
  onConsent: (value: boolean) => void;
}) {
  const { tr, lang } = useLocale();
  const [invitation, setInvitation] = useState("");
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState("");
  if (data.agent.provider !== "gemini_developer") return null;
  return (
    <aside className="live-access" aria-label={tr("Gemini access and privacy")}>
      <p>
        <strong>{tr("Gemini Developer API · server-side MCP")}</strong> ·{" "}
        {tr("Managed GCP criterion unmet · optional integration disabled")}
      </p>
      <p className="fine-print">
        {tr(
          "Free Gemini: use permitted non-sensitive documents only. Inputs may be used for product improvement and human review.",
        )}
      </p>
      {data.agent.public_access ? (
        <p>
          {tr(
            "Public Gemini access · no invitation, account or API key needed",
          )}
        </p>
      ) : null}
      {data.agent.public_access ||
      data.settings.ai_access ||
      data.settings.mode === "judge" ? (
        <label className="processing-consent">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => onConsent(e.target.checked)}
          />
          {tr(
            data.agent.public_access
              ? "I am 18 or older, evaluating this hackathon application in a supported region outside the EEA, UK and Switzerland, and will send only permitted non-sensitive material."
              : "I am an evaluator aged 18 or older, currently in Kazakhstan, and will send only permitted, non-sensitive material.",
          )}
        </label>
      ) : (
        <details>
          <summary>{tr("Use a private AI invitation")}</summary>
          <p className="fine-print">
            {tr(
              "Live AI requires a private invitation. Calendar actions here are illustrative.",
            )}
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setPending(true);
              setFailure("");
              try {
                await api("/judge/claim", "POST", {
                  invitation: invitation.trim(),
                });
                setInvitation("");
                location.reload();
              } catch (error) {
                setFailure(errorMessage(String(error), lang));
                setPending(false);
              }
            }}
          >
            <label>
              {tr("Owner-issued one-use judge invitation")}
              <input
                type="password"
                autoComplete="off"
                spellCheck={false}
                maxLength={100}
                value={invitation}
                onChange={(e) => setInvitation(e.target.value)}
              />
            </label>
            <button
              className="secondary"
              disabled={pending || invitation.trim().length < 40}
            >
              {tr("Open isolated demo")}
            </button>
          </form>
          {failure ? <p role="alert">{failure}</p> : null}
        </details>
      )}
      <p className="fine-print">
        {tr(
          "AI access grants no Google Calendar permission. Export a Workspace Passport before this temporary session resets.",
        )}
      </p>
    </aside>
  );
}
