// Keep the native bridge limited to application-relative routes and GET/POST.
const read =
  /^\/api\/(session|state|health|auth\/start|connections\/calendar-list|events(?:\?after=\d+)?|conversation|challenge|export|sources\/[a-zA-Z0-9_-]+|packets\/[a-f0-9]+)$/;
const write =
  /^\/api\/(judge\/claim|connections\/calendar|tasks\/[a-f0-9]+\/settings|import-native|plan|scenario|chat|conversation\/new|runs\/[a-f0-9]+\/cancel|rescue|rescues\/[a-f0-9]+\/choose|preflight|preflights\/[a-f0-9]+\/recovery|sources\/[a-zA-Z0-9_-]+\/mapping|preferences|sync|conflicts\/[a-f0-9]+\/resolve|plans\/[a-f0-9]+\/preview|previews\/[a-f0-9]+\/approve|receipts\/[a-f0-9]+\/(verify|undo))$/;
function permits(apiPath, method) {
  return (
    typeof apiPath === "string" &&
    ((method === "GET" && read.test(apiPath)) ||
      (method === "POST" && write.test(apiPath)))
  );
}
// Never write arbitrary input, URL query values, identifiers, or bodies to logs.
// Unknown path segments are replaced rather than truncated and accidentally leaked.
const safeSegments = new Set(
  "api session state health auth start judge claim connections calendar-list calendar tasks settings events import import-native plan scenario chat conversation new runs cancel rescue rescues choose preflight preflights recovery mapping preferences sync export sources conflicts resolve packets plans preview previews approve receipts verify undo".split(
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
