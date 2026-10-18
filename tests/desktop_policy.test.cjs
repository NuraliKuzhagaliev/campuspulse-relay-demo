const { test } = require("node:test");
const assert = require("node:assert/strict");
const { permits, metadata } = require("../desktop/request-policy.cjs");

test("native import and state refresh remain allowed; multipart and invalid IPC remain closed", () => {
  assert(permits("/api/import-native", "POST"));
  assert(permits("/api/state", "GET"));
  assert(permits("/api/events?after=123", "GET"));
  for (const [route, method] of [["/api/import", "POST"], ["/api/state", "DELETE"], ["/api/import-native?token=secret", "POST"], ["/api/../state", "GET"], ["https://example.com/api/state", "GET"], [null, "GET"], ["/api/state", null]])
    assert.equal(permits(route, method), false);
});
test("rejected-request diagnostics redact all input except fixed route/method vocabulary", () => {
  const tokens = ["my-file.md", "private-token", "approval-digest", "secret"];
  const result = JSON.stringify(metadata("/api/previews/approval-digest/approve?token=private-token&file=my-file.md#secret", "POST"));
  for (const token of tokens) assert(!result.includes(token));
  assert.deepEqual(metadata("/api/import", "POST"), {method:"POST",path:"/api/import"});
  assert.deepEqual(metadata("/api/state", "POST secret"), {method:"[invalid]",path:"/api/state"});
  assert.deepEqual(metadata("https://secret.example/api/state", "GET"), {method:"GET",path:"[invalid]"});
  assert.deepEqual(metadata({ secret: "private-token" }, "GET"), {method:"GET",path:"[invalid]"});
});
