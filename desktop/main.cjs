const {
  app,
  BrowserWindow,
  ipcMain,
  dialog,
  shell,
  Notification,
  Tray,
  Menu,
  nativeImage,
  session,
} = require("electron");
const fs = require("node:fs/promises");
const { watch } = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const native = require("./locales.cjs");
const requestPolicy = require("./request-policy.cjs");
let language = "en";
const words = () => native[language];
const activeNotifications = new Map();
if (process.platform === "win32")
  app.setAppUserModelId("dev.campuspulse.relay");
// Never default project data/caches to the system drive. Portable and installed builds use D:.
const dataRoot =
  process.env.RELAY_DESKTOP_DATA ||
  "D:\\projects\\CampusPulseRELAY\\.local\\desktop";
if (!/^[dD]:[\\/]/.test(dataRoot))
  throw new Error("CampusPulse RELAY desktop data must be on D:.");
app.setPath("userData", dataRoot);
app.setPath("sessionData", path.join(dataRoot, "session"));
app.setPath("logs", path.join(dataRoot, "logs"));
app.setPath("crashDumps", path.join(dataRoot, "crash-dumps"));
app.commandLine.appendSwitch("disk-cache-dir", path.join(dataRoot, "cache"));
app.commandLine.appendSwitch("disable-http-cache");
let window,
  tray,
  watcher,
  gateway = process.env.RELAY_GATEWAY_URL || "https://campuspulse-relay-demo.onrender.com",
  csrf = "";
const trustedOrigin = new URL(gateway).origin;
if (
  !(
    trustedOrigin === "http://127.0.0.1:8000" ||
    new URL(gateway).protocol === "https:"
  )
)
  throw new Error(
    "Gateway must use HTTPS or the explicit local development endpoint.",
  );
let pendingImportId = null;
let refreshedImportId = null;
let auditQueue = Promise.resolve();
function audit(stage, fields = {}) {
  // Callers pass only fixed stage names, random correlation IDs and sanitized
  // route metadata. No document bytes, file paths, tokens or approval payloads.
  auditQueue = auditQueue
    .then(async () => {
      await fs.mkdir(path.join(dataRoot, "logs"), { recursive: true });
      await fs.appendFile(
        path.join(dataRoot, "logs/desktop-trace.jsonl"),
        JSON.stringify({
          stage,
          ...fields,
          at: new Date().toISOString(),
        }) + "\n",
      );
    })
    .catch(() => undefined); // Diagnostics must never break local import.
  return auditQueue;
}
function sender(event) {
  if (
    !window ||
    event.sender !== window.webContents ||
    event.senderFrame !== window.webContents.mainFrame
  )
    throw new Error("Untrusted native bridge caller.");
}
async function request(apiPath, method = "GET", body) {
  const route = requestPolicy.metadata(apiPath, method);
  if (!requestPolicy.permits(apiPath, method)) {
    await audit("request-rejected", route);
    throw new Error("Unsupported application request.");
  }
  const isImport = apiPath === "/api/import-native" && method === "POST";
  const isRefresh =
    apiPath === "/api/state" && method === "GET" && pendingImportId;
  const importId = isImport
    ? pendingImportId || crypto.randomBytes(8).toString("hex")
    : isRefresh || null;
  if (importId)
    await audit(isImport ? "import-request-started" : "state-refresh-started", {
      id: importId,
      ...route,
    });
  let response, value;
  try {
    response = await session.defaultSession.fetch(gateway + apiPath, {
      method,
      signal: AbortSignal.timeout(110000),
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(csrf ? { "X-Relay-CSRF": csrf } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      redirect: "error",
    });
    value = await response.json();
  } catch (error) {
    if (importId)
      await audit(isImport ? "import-request-failed" : "state-refresh-failed", {
        id: importId,
        ...route,
      });
    throw error;
  }
  if (!response.ok) {
    if (importId)
      await audit(isImport ? "import-request-failed" : "state-refresh-failed", {
        id: importId,
        ...route,
        status: response.status,
      });
    throw new Error(
      (value.error?.code || "REQUEST_FAILED") +
        ": " +
        (value.error?.message || "Gateway request failed."),
    );
  }
  if (isImport) {
    pendingImportId = importId;
    await audit("import-request-completed", {
      id: importId,
      ...route,
      status: response.status,
    });
  } else if (isRefresh) {
    refreshedImportId = importId;
    pendingImportId = null;
    await audit("state-refresh-completed", {
      id: importId,
      ...route,
      status: response.status,
    });
  }
  if (
    apiPath === "/api/session" ||
    apiPath === "/api/demo/reset" ||
    /^\/api\/passport\/[a-f0-9]+\/restore$/.test(apiPath)
  )
    csrf = value.csrf;
  return value;
}
function validFile(name, size) {
  return (
    /\.(pdf|md|txt|ics)$/i.test(name) && size > 0 && size <= 2 * 1024 * 1024
  );
}
async function selectedFile(file, importId, kind) {
  if (importId) await audit("file-read-started", { id: importId });
  try {
    const stat = await fs.stat(file);
    if (
      kind === "passport"
        ? !(
            /\.json$/i.test(file) &&
            stat.size > 0 &&
            stat.size <= 2 * 1024 * 1024
          )
        : !validFile(file, stat.size)
    )
      throw new Error(
        kind === "passport" ? words().choosePassport : words().chooseFile,
      );
    const value = {
      name: path.basename(file),
      content: (await fs.readFile(file)).toString("base64"),
    };
    if (importId) await audit("file-read-completed", { id: importId });
    return value;
  } catch (error) {
    if (importId) await audit("file-read-failed", { id: importId });
    throw error;
  }
}
function installBridge() {
  ipcMain.handle("relay:passport-save", async (e, value) => {
    sender(e);
    const text = JSON.stringify(value);
    if (
      !value ||
      value.format !== "campuspulse-relay-workspace" ||
      value.version !== 1 ||
      Buffer.byteLength(text) > 2 * 1024 * 1024
    )
      throw new Error(words().choosePassport);
    const folder = path.join(dataRoot, "downloads");
    await fs.mkdir(folder, { recursive: true });
    const result = await dialog.showSaveDialog(window, {
      title: words().passportSave,
      defaultPath: path.join(folder, "CampusPulse-RELAY.relay.json"),
      filters: [{ name: words().passportFilter, extensions: ["json"] }],
    });
    if (result.canceled) return { saved: false };
    if (
      !/^[dD]:[\\/]/.test(path.resolve(result.filePath)) ||
      !result.filePath.toLowerCase().endsWith(".json")
    )
      throw new Error(words().passportDrive);
    const actualParent = await fs.realpath(path.dirname(result.filePath));
    if (!/^[dD]:[\\/]/.test(actualParent))
      throw new Error(words().passportDrive);
    const existing = await fs.lstat(result.filePath).catch((error) => {
      if (error.code === "ENOENT") return null;
      throw error;
    });
    if (existing?.isSymbolicLink()) throw new Error(words().passportDrive);
    const temporary = path.join(
      actualParent,
      ".relay-" + crypto.randomBytes(12).toString("hex") + ".tmp",
    );
    try {
      await fs.writeFile(temporary, text, { encoding: "utf8", flag: "wx" });
      await fs.rename(temporary, result.filePath);
    } finally {
      await fs.unlink(temporary).catch(() => undefined);
    }
    return { saved: true };
  });
  ipcMain.handle("relay:request", async (e, p, m, b) => {
    sender(e);
    return request(p, m, b);
  });
  ipcMain.handle("relay:connect", async (e) => {
    sender(e);
    const response = await session.defaultSession.fetch(
      gateway + "/api/auth/start?desktop=true",
    );
    const pairing = await response.json();
    if (!response.ok)
      throw new Error(pairing.error?.message || "OAuth is not configured.");
    const link = new URL(pairing.url);
    if (link.origin !== trustedOrigin || link.pathname !== "/connect")
      throw new Error("Untrusted authentication destination.");
    await shell.openExternal(link.href);
    for (let i = 0; i < 200; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      const response = await session.defaultSession.fetch(
        gateway + "/api/auth/poll",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pairing_id: pairing.pairing_id,
            secret: pairing.secret,
          }),
          credentials: "include",
        },
      );
      const value = await response.json();
      if (!response.ok)
        throw new Error(value.error?.message || "Pairing failed.");
      if (value.csrf) {
        csrf = value.csrf;
        return;
      }
    }
    throw new Error("Pairing timed out. Start again.");
  });
  ipcMain.handle("relay:import", async (e, kind) => {
    sender(e);
    if (kind !== undefined && kind !== "passport")
      throw new Error("Unsupported picker purpose.");
    const pickerId = crypto.randomBytes(8).toString("hex");
    pendingImportId = null;
    const logPicker = async (event) => {
      await fs.mkdir(path.join(dataRoot, "logs"), { recursive: true });
      await fs.appendFile(
        path.join(dataRoot, "logs/native-picker.jsonl"),
        JSON.stringify({
          id: pickerId,
          event,
          language,
          at: new Date().toISOString(),
        }) + "\n",
      );
    };
    await logPicker("opened");
    await audit("picker-opened", { id: pickerId });
    const result = await dialog.showOpenDialog(window, {
      title: kind === "passport" ? words().passportTitle : words().importTitle,
      properties: ["openFile"],
      filters: [
        {
          name: kind === "passport" ? words().passportFilter : words().filter,
          extensions:
            kind === "passport" ? ["json"] : ["pdf", "md", "txt", "ics"],
        },
      ],
    });
    await logPicker(result.canceled ? "canceled" : "selected");
    await audit(result.canceled ? "picker-canceled" : "picker-selected", {
      id: pickerId,
    });
    if (result.canceled) return null;
    const selected = await selectedFile(result.filePaths[0], pickerId, kind);
    pendingImportId = pickerId;
    return selected;
  });
  ipcMain.handle("relay:locale", async (e, next) => {
    sender(e);
    if (!Object.hasOwn(native, next))
      throw new Error("Unsupported UI language.");
    language = next;
    await fs.mkdir(dataRoot, { recursive: true });
    await fs.writeFile(
      path.join(dataRoot, "ui-language.json"),
      JSON.stringify({ language }),
    );
    updateTrayMenu();
  });
  ipcMain.handle("relay:notify", async (e, title, body) => {
    sender(e);
    if (
      typeof title !== "string" ||
      typeof body !== "string" ||
      title.length > 100 ||
      body.length > 500
    )
      throw new Error("Invalid notification.");
    return showNativeNotification(title, body, "ui-request");
  });
  ipcMain.handle("relay:external", async (e, url) => {
    sender(e);
    let u;
    try {
      u = new URL(url);
    } catch {
      throw new Error("Invalid link.");
    }
    if (
      u.protocol !== "https:" ||
      !([
        "github.com",
        "calendar.google.com",
        "console.cloud.google.com",
        "accounts.google.com",
      ].includes(u.hostname) || (u.origin === "https://campuspulse-relay-demo.onrender.com" && u.pathname.startsWith("/samples/") && !u.search && !u.hash && !u.username && !u.password))
    )
      throw new Error("Only approved service HTTPS links can open externally.");
    await shell.openExternal(u.href);
  });
  ipcMain.handle("relay:cache-save", async (e, data) => {
    sender(e);
    const json = JSON.stringify(data);
    if (json.length > 3 * 1024 * 1024)
      throw new Error("Snapshot exceeds cache limit.");
    await fs.mkdir(dataRoot, { recursive: true });
    if (!data.workspace_id) throw new Error("Snapshot identity is missing.");
    const tag = crypto
      .createHash("sha256")
      .update(data.workspace_id)
      .digest("hex");
    await fs.writeFile(
      path.join(dataRoot, "last-workspace.json"),
      JSON.stringify({ tenant: data.workspace_id }),
    );
    const file = path.join(dataRoot, "snapshot-" + tag + ".json");
    try {
      await fs.writeFile(file + ".tmp", json);
      await fs.rename(file + ".tmp", file);
      if (refreshedImportId)
        await audit("snapshot-save-completed", { id: refreshedImportId });
    } catch (error) {
      if (refreshedImportId)
        await audit("snapshot-save-failed", { id: refreshedImportId });
      throw error;
    } finally {
      refreshedImportId = null;
    }
  });
  ipcMain.handle("relay:cache-load", async (e, tenant) => {
    sender(e);
    try {
      if (!tenant)
        tenant = JSON.parse(
          await fs.readFile(path.join(dataRoot, "last-workspace.json"), "utf8"),
        ).tenant;
      if (typeof tenant !== "string" || tenant.length > 200) return null;
      const tag = crypto.createHash("sha256").update(tenant).digest("hex");
      return JSON.parse(
        await fs.readFile(
          path.join(dataRoot, "snapshot-" + tag + ".json"),
          "utf8",
        ),
      );
    } catch {
      return null;
    }
  });
  ipcMain.handle("relay:version", (e) => {
    sender(e);
    return app.getVersion();
  });
  ipcMain.handle("relay:watch", async (e) => {
    sender(e);
    if (watcher) {
      watcher.close();
      watcher = null;
      return { enabled: false };
    }
    const result = await dialog.showOpenDialog(window, {
      title: words().watchTitle,
      properties: ["openDirectory"],
    });
    if (result.canceled) return { enabled: false };
    const selected = result.filePaths[0];
    const seen = new Map();
    const pending = new Map();
    let count = 0;
    watcher = watch(selected, { recursive: false }, (_, name) => {
      if (!name || !validFile(String(name), 1) || count >= 200) return;
      const file = path.join(selected, String(name));
      if (pending.has(file)) clearTimeout(pending.get(file));
      pending.set(
        file,
        setTimeout(async () => {
          pending.delete(file);
          try {
            const chosen = await selectedFile(file);
            const hash = crypto
              .createHash("sha256")
              .update(chosen.content)
              .digest("hex");
            if (seen.get(file) === hash) return;
            seen.set(file, hash);
            count++;
            window?.webContents.send("relay:files", [
              { name: chosen.name, content: "" },
            ]);
            showNativeNotification(
              "CampusPulse RELAY",
              words().changed(chosen.name),
              "folder-change",
            );
          } catch {}
        }, 500),
      );
    });
    return { enabled: true, path: selected };
  });
}
function updateTrayMenu() {
  if (!tray) return;
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: words().open,
        click: () => (window ? window.show() : createWindow()),
      },
      { label: words().quit, click: () => app.quit() },
    ]),
  );
}
function showNativeNotification(title, body, kind) {
  const id = crypto.randomBytes(8).toString("hex");
  const record = (event) => {
    void fs
      .mkdir(path.join(dataRoot, "logs"), { recursive: true })
      .then(() =>
        fs.appendFile(
          path.join(dataRoot, "logs/native-notifications.jsonl"),
          JSON.stringify({
            id,
            event,
            kind,
            language,
            at: new Date().toISOString(),
          }) + "\n",
        ),
      )
      .catch(() => undefined);
  };
  if (!Notification.isSupported()) {
    record("unsupported");
    return { id, supported: false, dispatched: false };
  }
  const notification = new Notification({ title, body, silent: true });
  activeNotifications.set(id, notification);
  notification.on("show", () => record("os-show-event"));
  notification.on("failed", () => {
    record("failed");
    activeNotifications.delete(id);
  });
  notification.on("click", () => {
    record("clicked");
    window?.show();
    window?.focus();
  });
  notification.on("close", () => {
    record("closed");
    activeNotifications.delete(id);
  });
  record("dispatch-requested");
  notification.show();
  return { id, supported: true, dispatched: true };
}
async function createWindow() {
  window = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 720,
    minHeight: 600,
    title: "CampusPulse RELAY",
    backgroundColor: "#F5F4EF",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      devTools: !app.isPackaged,
    },
  });
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  window.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("file://")) e.preventDefault();
  });
  const dist = path.join(__dirname, "..", "dist", "index.html");
  await window.loadFile(dist);
  window.on("closed", () => {
    window = null;
  });
}
app.whenReady().then(async () => {
  await fs.mkdir(dataRoot, { recursive: true });
  try {
    const saved = JSON.parse(
      await fs.readFile(path.join(dataRoot, "ui-language.json"), "utf8"),
    );
    if (Object.hasOwn(native, saved.language)) language = saved.language;
  } catch {}
  session.defaultSession.setPermissionRequestHandler(
    (_, permission, callback) => callback(permission === "notifications"),
  );
  installBridge();
  await createWindow();
  tray = new Tray(path.join(__dirname, "icon.png"));
  tray.setToolTip("CampusPulse RELAY");
  updateTrayMenu();
  tray.on("double-click", () => (window ? window.show() : createWindow()));
});
app.on("window-all-closed", () => {
  watcher?.close();
  app.quit();
});
app.on("activate", () => {
  if (!window) createWindow();
});
