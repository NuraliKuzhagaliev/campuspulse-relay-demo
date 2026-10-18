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
  gateway = process.env.RELAY_GATEWAY_URL || "http://127.0.0.1:8000",
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
const allowed =
  /^\/api\/(session|state|health|auth\/start|judge\/claim|connections\/calendar-list|connections\/calendar|tasks\/[a-f0-9]+\/settings|events(?:\?after=\d+)?|import-native|plan|scenario|chat|preferences|sync|export|sources\/[a-zA-Z0-9_-]+|conflicts\/[a-f0-9]+\/resolve|packets\/[a-f0-9]+|plans\/[a-f0-9]+\/preview|previews\/[a-f0-9]+\/approve|receipts\/[a-f0-9]+\/(verify|undo))$/;
function sender(event) {
  if (
    !window ||
    event.sender !== window.webContents ||
    event.senderFrame !== window.webContents.mainFrame
  )
    throw new Error("Untrusted native bridge caller.");
}
async function request(apiPath, method = "GET", body) {
  if (!allowed.test(apiPath) || !["GET", "POST"].includes(method))
    throw new Error("Unsupported application request.");
  const response = await session.defaultSession.fetch(gateway + apiPath, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-Relay-CSRF": csrf } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    redirect: "error",
  });
  const value = await response.json();
  if (!response.ok)
    throw new Error(
      (value.error?.code || "REQUEST_FAILED") +
        ": " +
        (value.error?.message || "Gateway request failed."),
    );
  if (apiPath === "/api/session") csrf = value.csrf;
  return value;
}
function validFile(name, size) {
  return (
    /\.(pdf|md|txt|ics)$/i.test(name) && size > 0 && size <= 10 * 1024 * 1024
  );
}
async function selectedFile(file) {
  const stat = await fs.stat(file);
  if (!validFile(file, stat.size))
    throw new Error("Choose PDF, Markdown, TXT or ICS up to 10 MiB.");
  return {
    name: path.basename(file),
    content: (await fs.readFile(file)).toString("base64"),
  };
}
function installBridge() {
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
  ipcMain.handle("relay:import", async (e) => {
    sender(e);
    const result = await dialog.showOpenDialog(window, {
      title: "Import selected academic source",
      properties: ["openFile"],
      filters: [
        { name: "Academic sources", extensions: ["pdf", "md", "txt", "ics"] },
      ],
    });
    if (result.canceled) return null;
    return selectedFile(result.filePaths[0]);
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
    if (Notification.isSupported())
      new Notification({ title, body, silent: true }).show();
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
      ![
        "github.com",
        "calendar.google.com",
        "console.cloud.google.com",
        "accounts.google.com",
      ].includes(u.hostname)
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
    await fs.writeFile(file + ".tmp", json);
    await fs.rename(file + ".tmp", file);
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
      title: "Watch a selected folder (changes require explicit import)",
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
            if (Notification.isSupported())
              new Notification({
                title: "CampusPulse RELAY",
                body: `${chosen.name} changed. Review and import it explicitly.`,
                silent: true,
              }).show();
          } catch {}
        }, 500),
      );
    });
    return { enabled: true, path: selected };
  });
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
  session.defaultSession.setPermissionRequestHandler(
    (_, permission, callback) => callback(permission === "notifications"),
  );
  installBridge();
  await createWindow();
  tray = new Tray(path.join(__dirname, "icon.png"));
  tray.setToolTip("CampusPulse RELAY");
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: "Open CampusPulse RELAY",
        click: () => (window ? window.show() : createWindow()),
      },
      { label: "Quit", click: () => app.quit() },
    ]),
  );
  tray.on("double-click", () => (window ? window.show() : createWindow()));
});
app.on("window-all-closed", () => {
  watcher?.close();
  app.quit();
});
app.on("activate", () => {
  if (!window) createWindow();
});
