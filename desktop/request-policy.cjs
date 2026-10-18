// Keep the native bridge limited to application-relative routes and GET/POST.
const allowed =
  /^\/api\/(session|state|health|auth\/start|judge\/claim|connections\/calendar-list|connections\/calendar|tasks\/[a-f0-9]+\/settings|events(?:\?after=\d+)?|import-native|plan|scenario|chat|preferences|sync|export|sources\/[a-zA-Z0-9_-]+|conflicts\/[a-f0-9]+\/resolve|packets\/[a-f0-9]+|plans\/[a-f0-9]+\/preview|previews\/[a-f0-9]+\/approve|receipts\/[a-f0-9]+\/(verify|undo))$/;
function permits(apiPath, method) {
  return (
    typeof apiPath === "string" &&
    allowed.test(apiPath) &&
    ["GET", "POST"].includes(method)
  );
}
// Never write arbitrary input, URL query values, identifiers, or bodies to logs.
// Unknown path segments are replaced rather than truncated and accidentally leaked.
const safeSegments = new Set(
  "api session state health auth start judge claim connections calendar-list calendar tasks settings events import import-native plan scenario chat preferences sync export sources conflicts resolve packets plans preview previews approve receipts verify undo".split(
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
