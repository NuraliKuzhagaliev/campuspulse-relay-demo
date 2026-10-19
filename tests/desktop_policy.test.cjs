const { test } = require("node:test");
const assert = require("node:assert/strict");
const { permits, metadata } = require("../desktop/request-policy.cjs");

test("native import and state refresh remain allowed; multipart and invalid IPC remain closed", () => {
  assert(permits("/api/import-native", "POST"));
  assert(permits("/api/state", "GET"));
  assert(permits("/api/events?after=123", "GET"));
  for (const [route, method] of [
    ["/api/import", "POST"],
    ["/api/state", "DELETE"],
    ["/api/import-native?token=secret", "POST"],
    ["/api/../state", "GET"],
    ["https://example.com/api/state", "GET"],
    [null, "GET"],
    ["/api/state", null],
  ])
    assert.equal(permits(route, method), false);
});
test("rejected-request diagnostics redact all input except fixed route/method vocabulary", () => {
  const tokens = ["my-file.md", "private-token", "approval-digest", "secret"];
  const result = JSON.stringify(
    metadata(
      "/api/previews/approval-digest/approve?token=private-token&file=my-file.md#secret",
      "POST",
    ),
  );
  for (const token of tokens) assert(!result.includes(token));
  assert.deepEqual(metadata("/api/import", "POST"), {
    method: "POST",
    path: "/api/import",
  });
  assert.deepEqual(metadata("/api/state", "POST secret"), {
    method: "[invalid]",
    path: "/api/state",
  });
  assert.deepEqual(metadata("https://secret.example/api/state", "GET"), {
    method: "GET",
    path: "[invalid]",
  });
  assert.deepEqual(metadata({ secret: "private-token" }, "GET"), {
    method: "GET",
    path: "[invalid]",
  });
});

test("workshop and conversation contracts use exact narrow methods", () => {
  const id = "a".repeat(24),
    run = "b".repeat(32);
  for (const path of [
    "/api/rescue",
    "/api/preflight",
    "/api/conversation/new",
    `/api/rescues/${run}/choose`,
    `/api/preflights/${id}/recovery`,
    `/api/sources/${id}/mapping`,
    `/api/runs/${run}/cancel`,
  ]) {
    assert(permits(path, "POST"), path);
    assert(!permits(path, "GET"), path);
  }
  for (const path of ["/api/challenge", "/api/conversation", "/api/state"]) {
    assert(permits(path, "GET"));
    assert(!permits(path, "POST"));
  }
  for (const path of [
    "/internal/sync",
    "/api/test/seed",
    "/api/conversation/new?tenant=other",
    "/api/sources/../mapping",
  ])
    assert(!permits(path, "POST"));
});
test("four additions keep exact read/write paths and identifiers; no generic proxy", () => {
  const id = "a".repeat(24);
  for (const p of ["/api/additions", `/api/tasks/${id}/estimate-suggestion`]) {
    assert(permits(p, "GET"));
    assert(!permits(p, "POST"));
  }
  for (const p of [
    `/api/tasks/${id}/progress`,
    `/api/work-sessions/${id}/heartbeat`,
    "/api/progress/preview",
    `/api/progress/${id}/adopt`,
    "/api/clarify",
    `/api/clarify/${id}/answer`,
    `/api/clarify/${id}/cancel`,
    "/api/gates",
    `/api/gates/notifications/${id}/claim`,
    `/api/gates/${id}/observe`,
    `/api/gates/${id}/remove`,
    "/api/gates/conditional-preview",
    "/api/passport/export",
    "/api/passport/preview",
    `/api/passport/${id}/restore`,
  ]) {
    assert(permits(p, "POST"), p);
    assert(!permits(p, "GET"), p);
    assert(!permits(p, "DELETE"), p);
    assert(!permits(p + "?tenant=victim", "POST"), p);
  }
  for (const p of [
    "/api/passport/../../secret",
    "/api/passport/write",
    "/api/gates/https://example.com",
    "/api/progress/arbitrary/adopt",
    "/api/import",
  ])
    assert(!permits(p, "POST"), p);
});
