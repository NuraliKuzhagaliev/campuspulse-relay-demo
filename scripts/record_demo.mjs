import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";
const root = process.cwd();
await fs.mkdir("release/recordings", { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: {
    dir: path.join(root, ".local/demo-video"),
    size: { width: 1440, height: 900 },
  },
});
const page = await context.newPage();
const pause = (ms) => page.waitForTimeout(ms);
await page.goto("http://127.0.0.1:8000");
await page.evaluate(() => {
  const tag = document.createElement("div");
  tag.textContent =
    "RECORDED BACKUP · local illustrative Calendar · cloud not connected";
  Object.assign(tag.style, {
    position: "fixed",
    bottom: "8px",
    right: "12px",
    zIndex: "99999",
    background: "#10243a",
    color: "#bde9d6",
    padding: "9px 12px",
    borderRadius: "7px",
    font: "12px Arial",
  });
  document.body.append(tag);
});
await pause(8000);
await page
  .getByRole("button", { name: "Explore illustrative workspace" })
  .click();
await pause(9000);
await page.getByRole("button", { name: "Evidence", exact: true }).click();
await pause(12000);
await page
  .locator(".fact-grid>div")
  .filter({ hasText: "2026-10-22" })
  .getByRole("button", { name: "Page 1" })
  .click();
await pause(12000);
await page.getByRole("button", { name: "Close dialog" }).click();
await page
  .locator(".fact-grid>div")
  .filter({ hasText: "2026-10-21" })
  .getByRole("button", { name: "Use this deadline" })
  .click();
await pause(5000);
await page.getByRole("button", { name: "Repair my week" }).click();
await page
  .getByText("Your week is ready for review. No external changes made.")
  .waitFor();
await page.getByRole("button", { name: "My week", exact: true }).click();
await pause(12000);
await page.locator(".study-block").first().click();
await pause(10000);
await page.getByRole("button", { name: "Close dialog" }).click();
await page.getByRole("button", { name: "Recovery", exact: true }).click();
await page.getByRole("button", { name: "Lose Wednesday afternoon" }).click();
await pause(13000);
await page.getByRole("button", { name: "Return to baseline" }).click();
await page.getByRole("button", { name: "Review calendar actions" }).click();
await pause(12000);
await page
  .getByRole("button", { name: "Approve illustrative local actions" })
  .click();
await page.getByRole("heading", { name: "Read-back completed" }).waitFor();
await pause(12000);
await page.getByRole("button", { name: "Connections", exact: true }).click();
await page.getByRole("button", { name: "Fetch live course source" }).click();
await pause(9000);
await page.getByRole("button", { name: "Evidence", exact: true }).click();
await pause(10000);
const video = page.video();
await context.close();
await browser.close();
const file = await video.path();
const target = path.join(
  root,
  "release/recordings/CampusPulse-RELAY-recorded-local-demo.webm",
);
await fs.copyFile(file, target);
await fs.writeFile(
  "docs/evidence/recording.json",
  JSON.stringify(
    {
      path: target,
      recorded: true,
      mode: "local illustrative Calendar; live GitHub fetch attempted, inspect the visible result for availability/quota",
      cloud_proof: false,
      script: "scripts/record_demo.mjs",
      duration_target_seconds: 134,
      duration_is_target_only: true,
    },
    null,
    2,
  ),
);
console.log(target);
