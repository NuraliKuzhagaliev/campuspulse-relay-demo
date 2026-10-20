/** 0.5.2 browser regression. Use an owned isolated HTTPS test server. Zero model calls. */
import fs from "node:fs/promises";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import { chromium, expect as baseExpect } from "@playwright/test";
const expect = baseExpect.configure({ timeout: 20000 }),
  base = process.env.RELAY_CHECK_URL || "https://127.0.0.1:8038",
  proof = {
    scope: "Real local HTTPS UI; no Gemini or Google calls",
    passed: false,
    checks: [],
  },
  browser = await chromium.launch({ headless: true });
const archive = JSON.parse(
  await fs.readFile("public/samples/09-workspace.relay.json", "utf8"),
);
archive.payload.preferences.timezone = "America/New_York";
const canonical = (v) =>
  Array.isArray(v)
    ? v.map(canonical)
    : v && typeof v === "object"
      ? Object.fromEntries(
          Object.keys(v)
            .sort()
            .map((k) => [k, canonical(v[k])]),
        )
      : v;
archive.sha256 = crypto
  .createHash("sha256")
  .update(JSON.stringify(canonical(archive.payload)))
  .digest("hex");
await fs.mkdir(".local/release-0.5.2", { recursive: true });
await fs.writeFile(
  ".local/release-0.5.2/legacy-archive.relay.json",
  JSON.stringify(archive),
);
const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    acceptDownloads: true,
    viewport: { width: 1440, height: 1100 },
  }),
  page = await context.newPage();
async function idle() {
  await expect(page.locator(".working")).toHaveCount(0);
}
async function state() {
  return (await page.request.get(base + "/api/state")).json();
}
try {
  await page.goto(base);
  const entry = page.getByRole("button", {
    name: "Explore illustrative workspace",
    exact: true,
  });
  try {
    await entry.waitFor({ state: "visible", timeout: 3000 });
    await entry.click();
  } catch {}
  const loaded = page.waitForEvent("domcontentloaded");
  await page
    .getByRole("button", { name: "Use my own data", exact: true })
    .click();
  await loaded;
  const planning = page.locator(".planning-context");
  await planning.getByLabel("Range starts", { exact: true }).fill("2026-02-31");
  await planning
    .getByRole("button", { name: "Open calendar: Range starts", exact: true })
    .click();
  await page.locator('.localized-calendar [data-date="2026-10-21"]').click();
  assert(
    await planning
      .getByLabel("Range starts", { exact: true })
      .evaluate((e) => e.validity.valid),
  );
  await planning.getByLabel("Range ends", { exact: true }).fill("2026-10-21");
  await planning
    .getByRole("button", { name: "Open calendar: Range ends", exact: true })
    .click();
  await page.locator('.localized-calendar [data-date="2026-10-21"]').focus();
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Enter");
  await expect(planning.getByLabel("Range ends", { exact: true })).toHaveValue(
    "2026-10-22",
  );
  await planning.getByLabel("Range ends", { exact: true }).fill("2026-10-21");
  await planning
    .getByLabel("Workspace timezone", { exact: true })
    .selectOption("Europe/Moscow");
  await planning
    .getByLabel("Study ends", { exact: true })
    .selectOption("18:30");
  for (const [i, day] of [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ].entries())
    await planning.getByLabel(day, { exact: true }).setChecked(i === 2);
  await planning
    .getByRole("button", { name: "Save planning context", exact: true })
    .click();
  await idle();
  proof.checks.push(
    "invalid date corrected by picker; calendar arrow keys select next day",
  );
  const text =
    "Assignment: Unknown clock brief\nCourse: Clock science\nTerm: Autumn 2026\nAssignment ID: unknown-clock-052\nThe supervisor will announce the deadline. No effort estimate is given.";
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles({
      name: "unknown-clock.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(text),
    });
  await expect(
    page.getByRole("button", { name: "Review extracted fields", exact: true }),
  ).toBeVisible();
  await idle();
  await page
    .getByRole("button", { name: "Review extracted fields", exact: true })
    .click();
  const review = page.getByTestId("review-entity").first();
  await expect(review).toBeVisible();
  await idle();
  await expect(review.getByLabel("Deadline date", { exact: true })).toHaveValue(
    "",
  );
  await expect(review.getByLabel("Deadline time", { exact: true })).toHaveValue(
    "",
  );
  await review
    .getByLabel("I reviewed this assignment and confirm only these fields.")
    .check();
  await review
    .getByRole("button", { name: "Open calendar: Deadline date", exact: true })
    .click();
  await page.locator('.localized-calendar [data-date="2026-10-21"]').click();
  let submitted = 0;
  page.on("request", (r) => {
    if (r.url().endsWith("/confirm")) submitted++;
  });
  await review
    .getByRole("button", { name: "Confirm this assignment", exact: true })
    .click();
  assert.equal(submitted, 0);
  assert(
    !(await review
      .getByLabel("Deadline time", { exact: true })
      .evaluate((e) => e.validity.valid)),
  );
  await review
    .getByRole("button", { name: "Clear deadline", exact: true })
    .click();
  await review
    .getByRole("button", { name: "Confirm this assignment", exact: true })
    .click();
  await expect(review).toHaveCount(0);
  await idle();
  assert.equal((await state()).tasks[0].due, null);
  proof.checks.push(
    "partial date without time cannot confirm; clearing both keeps deadline unknown",
  );
  // A second isolated workspace keeps the complete planning flow separate from the unknown task.
  await context.close();
  const other = await browser.newContext({
    ignoreHTTPSErrors: true,
    acceptDownloads: true,
  });
  const p = await other.newPage();
  await p.goto(base);
  try {
    await p
      .getByRole("button", {
        name: "Explore illustrative workspace",
        exact: true,
      })
      .waitFor({ state: "visible", timeout: 3000 });
    await p
      .getByRole("button", {
        name: "Explore illustrative workspace",
        exact: true,
      })
      .click();
  } catch {}
  const nav = p.waitForEvent("domcontentloaded");
  await p.getByRole("button", { name: "Use my own data", exact: true }).click();
  await nav;
  const c = p.locator(".planning-context");
  await c.getByLabel("Range starts", { exact: true }).fill("2026-10-21");
  await c.getByLabel("Range ends", { exact: true }).fill("2026-10-21");
  await c
    .getByLabel("Workspace timezone", { exact: true })
    .selectOption("Europe/Moscow");
  await c.getByLabel("Study ends", { exact: true }).selectOption("18:30");
  for (const [i, day] of [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ].entries())
    await c.getByLabel(day, { exact: true }).setChecked(i === 2);
  await c
    .getByRole("button", { name: "Save planning context", exact: true })
    .click();
  await expect(p.locator(".working")).toHaveCount(0);
  await p
    .locator("input[type=file]")
    .first()
    .setInputFiles({
      name: "complete-clock.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(
        "Assignment: Complete clock brief\nCourse: Clock science\nTerm: Autumn 2026\nAssignment ID: complete-clock-052\nDue: 2026-10-23T18:00:00+05:00\nEffort: 30 minutes\n- [ ] Explain the clock",
      ),
    });
  await expect(
    p.getByRole("button", { name: "Review extracted fields", exact: true }),
  ).toBeVisible();
  await expect(p.locator(".working")).toHaveCount(0);
  await p
    .getByRole("button", { name: "Review extracted fields", exact: true })
    .click();
  const r = p.getByTestId("review-entity").first();
  await expect(r).toBeVisible();
  await expect(p.locator(".working")).toHaveCount(0);
  await expect(r.getByLabel("Deadline time", { exact: true })).toHaveValue(
    "16:00",
  );
  await r
    .getByLabel("I reviewed this assignment and confirm only these fields.")
    .check();
  await r
    .getByRole("button", { name: "Confirm this assignment", exact: true })
    .click();
  await expect(r).toHaveCount(0);
  await expect(p.locator(".working")).toHaveCount(0);
  await p.getByRole("button", { name: "Repair my week", exact: true }).click();
  await expect(p.locator(".working")).toHaveCount(0);
  let s = await (await p.request.get(base + "/api/state")).json();
  assert(s.plan.feasible && s.plan.blocks.length === 1);
  const baseline = s.plan.id;
  await p.getByRole("button", { name: "Recovery", exact: true }).click();
  await p
    .getByRole("button", { name: "Lose Wednesday afternoon", exact: true })
    .click();
  await expect(p.locator(".working")).toHaveCount(0);
  await p
    .getByRole("button", { name: "Return to baseline", exact: true })
    .click();
  assert.equal(
    (await (await p.request.get(base + "/api/state")).json()).plan.id,
    baseline,
  );
  await p
    .getByRole("button", { name: "Review calendar actions", exact: true })
    .click();
  await expect(
    p.getByRole("button", {
      name: "Approve illustrative local actions",
      exact: true,
    }),
  ).toBeVisible();
  await expect(p.locator(".working")).toHaveCount(0);
  await p
    .getByRole("button", {
      name: "Approve illustrative local actions",
      exact: true,
    })
    .click();
  await expect(p.locator(".working")).toHaveCount(0);
  s = await (await p.request.get(base + "/api/state")).json();
  assert.equal(s.receipts[0].mode, "illustrative");
  assert.equal(s.receipts[0].status, "verified");
  proof.checks.push(
    "Moscow plan, what-if baseline preservation and explicitly illustrative receipt",
  );
  await p.getByRole("button", { name: "Evidence", exact: true }).click();
  await p.getByRole("button", { name: /Progress & continuity/ }).click();
  await p
    .getByRole("button", { name: "Workspace Passport", exact: true })
    .click();
  const passport = p.getByTestId("passport-panel");
  await passport
    .getByLabel("Portable workspace file", { exact: true })
    .setInputFiles(".local/release-0.5.2/legacy-archive.relay.json");
  await expect(
    passport.getByText(/This archive uses America\/New_York/),
  ).toBeVisible();
  await expect(
    passport.getByText(/The restored workspace will use UTC/),
  ).toBeVisible();
  await passport
    .getByRole("button", {
      name: "Import as fresh copy and switch",
      exact: true,
    })
    .click();
  await expect(
    passport.getByRole("button", {
      name: "Import as fresh copy and switch",
      exact: true,
    }),
  ).toHaveCount(0);
  s = await (await p.request.get(base + "/api/state")).json();
  assert.equal(s.settings.timezone, "UTC");
  assert.equal(s.settings.portable_original_timezone, "America/New_York");
  assert.equal(s.settings.calendar_live, false);
  assert.equal(s.receipts.length, 0);
  proof.checks.push(
    "legacy Passport migration disclosed in UI; new UTC copy carries no Google connection or old approvals",
  );
  await other.close();
  proof.passed = true;
} finally {
  await browser.close();
  await fs.writeFile(
    ".local/release-0.5.2/edge-ui.json",
    JSON.stringify(proof, null, 2) + "\n",
  );
}
console.log(JSON.stringify(proof));
