// Keep the native bridge limited to application-relative routes and GET/POST.
const read =
  /^\/api\/(session|state|health|auth\/start|connections\/calendar-list|events(?:\?after=\d+)?|conversation|runs\/[a-f0-9]{32}|challenge|additions|tasks\/[a-f0-9]+\/estimate-suggestion|export|sources\/[a-zA-Z0-9_-]+|packets\/[a-f0-9]+)$/;
const write =
  /^\/api\/(demo\/reset|judge\/claim|connections\/calendar|tasks\/[a-f0-9]+\/settings|import-native|tasks\/[a-f0-9]+\/progress|work-sessions\/[a-f0-9]+\/heartbeat|progress\/preview|progress\/[a-f0-9]+\/adopt|clarify|clarify\/[a-f0-9]+\/(cancel|answer)|gates|gates\/notifications\/[a-f0-9]+\/claim|gates\/conditional-preview|gates\/[a-f0-9]+\/(observe|remove)|passport\/(export|preview)|passport\/[a-f0-9]+\/restore|plan|scenario|chat|conversation\/new|runs\/[a-f0-9]+\/cancel|rescue|rescues\/[a-f0-9]+\/choose|preflight|preflights\/[a-f0-9]+\/recovery|sources\/[a-zA-Z0-9_-]+\/mapping|preferences|sync|conflicts\/[a-f0-9]+\/resolve|plans\/[a-f0-9]+\/preview|previews\/[a-f0-9]+\/approve|receipts\/[a-f0-9]+\/(verify|undo))$/;
function permits(apiPath, method) {
  if (typeof apiPath !== "string" || apiPath.length > 2000) return false;
  if (method === "GET" && apiPath === "/api/extraction-proposals") return true;
  if (method === "GET" && apiPath === "/api/connections/status") return true;
  if (method === "POST" && apiPath === "/api/connections/disconnect")
    return true;
  if (method === "POST" && apiPath === "/api/connections/calendar/create")
    return true;
  if (method === "POST" && apiPath === "/api/connections/calendar/recover")
    return true;
  if (
    method === "POST" &&
    /^\/api\/sources\/[A-Za-z0-9_-]+\/review$/.test(apiPath)
  )
    return true;
  if (
    method === "POST" &&
    (["/api/workspace/switch", "/api/planning-context"].includes(apiPath) ||
      /^\/api\/extraction-proposals\/[a-f0-9]{24}\/[a-f0-9]{24}\/confirm$/.test(
        apiPath,
      ))
  )
    return true;
  return (
    typeof apiPath === "string" &&
    ((method === "GET" && read.test(apiPath)) ||
      (method === "POST" && write.test(apiPath)))
  );
}
// Never write arbitrary input, URL query values, identifiers, or bodies to logs.
// Unknown path segments are replaced rather than truncated and accidentally leaked.
const safeSegments = new Set(
  "api demo reset additions progress work-sessions heartbeat estimate-suggestion adopt clarify answer gates notifications conditional-preview observe remove passport restore session state health auth start judge claim connections calendar-list calendar tasks settings events import import-native plan scenario chat conversation new runs cancel rescue rescues choose preflight preflights recovery mapping preferences sync export sources conflicts resolve packets plans preview previews approve receipts verify undo".split(
    " ",
  ),
);
function metadata(apiPath, method) {
  const safeMethod = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
  ].includes(method)
    ? method
    : "[invalid]";
  let safePath = "[invalid]";
  if (
    typeof apiPath === "string" &&
    apiPath.startsWith("/api/") &&
    apiPath.length <= 2000
  ) {
    const pathname = apiPath.split(/[?#]/, 1)[0];
    safePath = pathname
      .split("/")
      .map((segment) =>
        segment === "" ? "" : safeSegments.has(segment) ? segment : ":redacted",
      )
      .join("/");
    if (apiPath.includes("?")) safePath += "?[redacted]";
    if (apiPath.includes("#")) safePath += "#[redacted]";
  }
  return { method: safeMethod, path: safePath };
}
module.exports = { permits, metadata };
