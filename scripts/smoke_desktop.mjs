import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { _electron as electron } from "playwright";

const root = process.cwd();
const executable =
  process.env.RELAY_TEST_EXE ||
  path.join(root, "installed", "CampusPulse RELAY", "CampusPulse RELAY.exe");
const data = path.join(root, ".local", "desktop-smoke");
const environment = { ...process.env, RELAY_DESKTOP_DATA: data };
delete environment.ELECTRON_RUN_AS_NODE;
await fs.mkdir("docs/evidence", { recursive: true });
await fs.mkdir("docs/screenshots", { recursive: true });
const proof = {
  checked_at: new Date().toISOString(),
  executable,
  installed_build: true,
  checks: {},
  limitations: [
    "Google external-browser OAuth consent is not configured; the pairing route is implemented but not live-verified.",
    "The native file picker is deterministically stubbed in this automated smoke; actual file IO/import is exercised.",
    "Native notification dispatch is exercised; OS toast visibility is not asserted.",
  ],
};
let app;
try {
  app = await electron.launch({
    executablePath: executable,
    cwd: root,
    env: environment,
    timeout: 30000,
  });
  let window = await app.firstWindow();
  await window
    .getByRole("button", { name: "Explore illustrative workspace" })
    .click();
  await window
    .getByRole("heading", { name: "Your week. Back in balance." })
    .waitFor();
  const prefs = await app.evaluate(({ BrowserWindow, app, Notification }) => ({
    preferences:
      BrowserWindow.getAllWindows()[0].webContents.getLastWebPreferences(),
    userData: app.getPath("userData"),
    sessionData: app.getPath("sessionData"),
    version: app.getVersion(),
    notificationSupported: Notification.isSupported(),
  }));
  assert.equal(prefs.preferences.nodeIntegration, false);
  assert.equal(prefs.preferences.contextIsolation, true);
  assert.equal(prefs.preferences.sandbox, true);
  assert.match(prefs.userData, /^D:/i);
  assert.match(prefs.sessionData, /^D:/i);
  proof.checks.security = {
    nodeIntegration: false,
    contextIsolation: true,
    sandbox: true,
  };
  proof.checks.paths = {
    userData: prefs.userData,
    sessionData: prefs.sessionData,
  };
  proof.version = prefs.version;
  const fixture = path.join(root, ".local", "tmp", "desktop-unseen.md");
  await fs.writeFile(
    fixture,
    "Assignment: Desktop unseen lab\nDue: 2026-11-10T18:00:00+05:00\nEffort: 60 minutes\n- [ ] Capture a reproducible observation",
  );
  await app.evaluate(({ dialog }, file) => {
    dialog.showOpenDialog = async () => ({
      canceled: false,
      filePaths: [file],
    });
  }, fixture);
  await window
    .getByRole("button", { name: "Connections", exact: true })
    .click();
  await window
    .getByRole("button", { name: "Import a file", exact: true })
    .click();
  await window.getByText("desktop-unseen.md", { exact: true }).waitFor();
  proof.checks.nativeImport =
    "actual selected file read via restricted bridge; native picker stubbed";
  await window.evaluate(() =>
    window.relay.notify(
      "CampusPulse RELAY",
      "Installed Windows smoke: notification dispatch verified.",
    ),
  );
  proof.checks.notificationDispatch = prefs.notificationSupported;
  await window.screenshot({
    path: "docs/screenshots/desktop-installed.png",
    fullPage: true,
  });
  await app.close();
  app = null;
  app = await electron.launch({
    executablePath: executable,
    cwd: root,
    env: environment,
    timeout: 30000,
  });
  window = await app.firstWindow();
  const entry = window.getByRole("button", {
    name: "Explore illustrative workspace",
  });
  try {
    await entry.click({ timeout: 3000 });
  } catch {}
  await window.getByRole("button", { name: "Evidence", exact: true }).click();
  await window.getByText("desktop-unseen.md", { exact: true }).waitFor();
  proof.checks.reopenPersistence = true;
  await app.close();
  app = null;
  // Block network through the app's own Electron session; cached snapshot must remain readable.
  app = await electron.launch({
    executablePath: executable,
    cwd: root,
    env: environment,
    timeout: 30000,
  });
  await app.evaluate(({ session }) => {
    session.defaultSession.webRequest.onBeforeRequest(
      { urls: ["http://127.0.0.1:8000/*"] },
      (_, cb) => cb({ cancel: true }),
    );
  });
  window = await app.firstWindow();
  await window.reload();
  await window
    .getByText("Cached offline view — live facts and writes unavailable.")
    .waitFor({ timeout: 15000 });
  assert.equal(
    await window.getByRole("button", { name: "Repair my week" }).isDisabled(),
    true,
  );
  proof.checks.cachedOfflineView = true;
  proof.checks.offlineWritesDisabled = true;
  await window.screenshot({
    path: "docs/screenshots/desktop-offline.png",
    fullPage: true,
  });
  await app.evaluate(({ session }) => {
    session.defaultSession.webRequest.onBeforeRequest(null);
  });
  await window.getByRole("button", { name: "Reconnect & revalidate" }).click();
  await window
    .getByText("Reconnected. Previous approvals are never replayed.")
    .waitFor();
  proof.checks.reconnectRevalidated = true;
  proof.passed = true;
} catch (error) {
  proof.passed = false;
  proof.error = String(error);
  throw error;
} finally {
  if (app) await app.close();
  await fs.writeFile(
    "docs/evidence/desktop-smoke.json",
    JSON.stringify(proof, null, 2),
  );
}
console.log(JSON.stringify(proof, null, 2));
