import { useLocale } from "./i18n";

export const workspaceTimezones = [
  ["Asia/Almaty", "Kazakhstan (UTC+05:00)"],
  ["Europe/Moscow", "Moscow · MSK (UTC+03:00)"],
  ["UTC", "UTC (UTC+00:00)"],
] as const;

export function TimeZoneSelect({
  value,
  onChange,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  const { tr } = useLocale();
  return (
    <select
      aria-label={label}
      value={workspaceTimezones.some(([zone]) => zone === value) ? value : ""}
      onChange={(e) => onChange(e.target.value)}
      required
    >
      {!workspaceTimezones.some(([zone]) => zone === value) && (
        <option value="" disabled>
          {tr("Choose a supported timezone")}
        </option>
      )}
      {workspaceTimezones.map(([zone, name]) => (
        <option key={zone} value={zone}>
          {tr(name)}
        </option>
      ))}
    </select>
  );
}
