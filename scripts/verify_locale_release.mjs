/** 0.5.2 browser regression. Use an owned isolated HTTPS test server. Zero model calls. */
import fs from "node:fs/promises";
import assert from "node:assert/strict";
import { chromium, expect as baseExpect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { buildSync } from "esbuild";
const expect = baseExpect.configure({ timeout: 20000 }),
  base = process.env.RELAY_CHECK_URL || "https://127.0.0.1:8038",
  folder = ".local/release-0.5.2";
const code = buildSync({
  entryPoints: ["src/translations.ts"],
  bundle: true,
  write: false,
  format: "esm",
  platform: "node",
}).outputFiles[0].text;
const { translations } = await import(
  "data:text/javascript;base64," + Buffer.from(code).toString("base64")
);
const tr = (key, lang) =>
  lang === "en" ? key : translations[key]?.[lang === "ru" ? 0 : 1] || key;
const proof = {
  version: "0.5.2",
  url: base,
  browser_locale: "ru-RU",
  model_calls: 0,
  calendar_writes: 0,
  states: [],
  checks: [],
  passed: false,
};
await fs.mkdir(folder, { recursive: true });
const browser = await chromium.launch({ headless: true });
async function state(page) {
  return (await page.request.get(base + "/api/state")).json();
}
async function own() {
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    locale: "ru-RU",
    viewport: { width: 1440, height: 1100 },
  });
  const page = await context.newPage();
  await page.goto(base);
  const enter = page.getByRole("button", {
    name: "Explore illustrative workspace",
    exact: true,
  });
  try {
    await enter.waitFor({ state: "visible", timeout: 4000 });
    await enter.click();
  } catch {}
  await expect(page.getByTestId("language")).toBeVisible();
  const navigated = page.waitForEvent("domcontentloaded");
  await page
    .getByRole("button", { name: "Use my own data", exact: true })
    .click();
  await navigated;
  await expect(page.locator(".planning-context")).toBeVisible();
  return { page, context };
}
try {
  for (const lang of ["en", "ru", "kk"]) {
    const { page, context } = await own();
    await page.getByTestId("language").selectOption(lang);
    assert.deepEqual(
      await page.getByTestId("language").locator("option").allTextContents(),
      ["EN", "RU", "KZ"],
    );
    const planning = page.locator(".planning-context");
    const zone = planning.getByRole("combobox", {
      name: tr("Workspace timezone", lang),
      exact: true,
    });
    assert.deepEqual(
      await zone
        .locator("option")
        .evaluateAll((items) => items.map((o) => o.value)),
      ["Asia/Almaty", "Europe/Moscow", "UTC"],
    );
    await zone.selectOption("Europe/Moscow");
    await planning
      .getByLabel(tr("Range starts", lang), { exact: true })
      .fill("2026-10-21");
    await planning
      .getByLabel(tr("Range ends", lang), { exact: true })
      .fill("2026-10-21");
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({ width, height: 1100 });
      await planning
        .getByRole("button", {
          name: tr("Open calendar", lang) + ": " + tr("Range starts", lang),
          exact: true,
        })
        .click();
      const dialog = page.locator(".localized-calendar");
      await expect(dialog).toBeVisible();
      const geometry = await dialog.evaluate((d) => {
        const box = d.getBoundingClientRect(),
          cells = [...d.querySelectorAll("[data-date]")].map((e) =>
            e.getBoundingClientRect(),
          );
        return {
          columns: new Set(cells.map((c) => Math.round(c.left))).size,
          rows: new Set(cells.map((c) => Math.round(c.top))).size,
          no_internal_overflow: d.scrollWidth <= d.clientWidth + 1,
          all_cells_fit: cells.every(
            (c) => c.left >= box.left && c.right <= box.right && c.width >= 30,
          ),
          height: box.height,
        };
      });
      assert.equal(geometry.columns, 7);
      assert.equal(geometry.rows, 6);
      assert(
        geometry.no_internal_overflow &&
          geometry.all_cells_fit &&
          geometry.height < 700,
        JSON.stringify(geometry),
      );
      const heading = await dialog
        .getByTestId("date-month-heading")
        .innerText();
      assert(
        heading
          .toLowerCase()
          .includes({ en: "october", ru: "октябрь", kk: "қазан" }[lang]),
        heading,
      );
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.equal(
        results.violations.length,
        0,
        JSON.stringify(
          results.violations.map((x) => ({
            id: x.id,
            targets: x.nodes.map((n) => n.target),
          })),
        ),
      );
      assert(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      );
      await page.screenshot({
        path: `${folder}/${lang}-${width}-calendar.png`,
      });
      if (width === 1440 && process.env.RELAY_SAVE_DOC_SCREENSHOTS === "true") {
        await fs.mkdir("docs/images", { recursive: true });
        await dialog.screenshot({
          path: `docs/images/calendar-${lang}-0.5.2.png`,
        });
      }
      proof.states.push({
        lang,
        visible_language_label: lang === "kk" ? "KZ" : lang.toUpperCase(),
        width,
        heading,
        geometry,
        AA_violations: 0,
        no_overflow: true,
      });
      await dialog.locator('[data-date="2026-10-21"]').click();
      await expect(
        planning.getByLabel(tr("Range starts", lang), { exact: true }),
      ).toHaveValue("2026-10-21");
    }
    await page.setViewportSize({ width: 1440, height: 1100 });
    const opener = planning.getByRole("button", {
      name: tr("Open calendar", lang) + ": " + tr("Range ends", lang),
      exact: true,
    });
    await opener.click();
    await page.keyboard.press("Escape");
    await expect(page.locator(".localized-calendar")).toHaveCount(0);
    await expect(opener).toBeFocused();
    await planning
      .getByLabel(tr("Study starts", lang), { exact: true })
      .selectOption("18:00");
    await planning
      .getByLabel(tr("Study ends", lang), { exact: true })
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
      await planning
        .getByLabel(tr(day, lang), { exact: true })
        .setChecked(i === 2);
    let received = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/planning-context") &&
        r.request().method() === "POST",
    );
    await planning
      .getByRole("button", {
        name: tr("Save planning context", lang),
        exact: true,
      })
      .click();
    assert.equal((await received).status(), 200);
    let value = await state(page);
    assert.equal(value.settings.timezone, "Europe/Moscow");
    assert.equal(value.settings.windows.length, 1);
    assert(value.settings.windows[0].start.endsWith("+03:00"));
    await page.reload();
    await expect(page.getByTestId("language")).toHaveValue(lang);
    await planning.locator("summary").click();
    await expect(
      planning.getByLabel(tr("Range ends", lang), { exact: true }),
    ).toHaveValue("2026-10-21");
    await expect(
      planning.getByLabel(tr("Study ends", lang), { exact: true }),
    ).toHaveValue("18:30");
    await expect(
      planning.getByLabel(tr("Wednesday", lang), { exact: true }),
    ).toBeChecked();
    await expect(
      planning.getByLabel(tr("Monday", lang), { exact: true }),
    ).not.toBeChecked();
    await page
      .getByRole("button", { name: tr("Connections", lang), exact: true })
      .click();
    const connectedZone = page
      .locator(".settings-row")
      .getByRole("combobox", {
        name: tr("Workspace timezone", lang),
        exact: true,
      });
    assert.equal(await connectedZone.locator("option").count(), 3);
    received = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/preferences") && r.request().method() === "POST",
    );
    await connectedZone.selectOption("UTC");
    assert.equal((await received).status(), 200);
    assert.equal((await state(page)).settings.timezone, "UTC");
    await expect(page.locator(".working")).toHaveCount(0);
    const text = `Assignment: Synthetic ${lang} clock check\nCourse: Time lab\nTerm: Autumn 2026\nAssignment ID: timezone-${lang}-052\nDue: 2026-10-23T18:00:00+05:00\nEffort: 30 minutes\nRubric:\n- [ ] Explain the clock evidence`;
    await page
      .locator("input[type=file]")
      .first()
      .setInputFiles({
        name: `clock-${lang}.md`,
        mimeType: "text/markdown",
        buffer: Buffer.from(text),
      });
    await expect(
      page.getByText(`clock-${lang}.md`, { exact: true }).first(),
    ).toBeVisible();
    await expect(page.locator(".working")).toHaveCount(0);
    await page
      .getByRole("button", {
        name: tr("Review extracted fields", lang),
        exact: true,
      })
      .click();
    const review = page.getByTestId("review-entity").first();
    await expect(review).toBeVisible();
    await expect(
      review.getByLabel(tr("Deadline date", lang), { exact: true }),
    ).toHaveValue("2026-10-23");
    await expect(
      review.getByLabel(tr("Deadline time", lang), { exact: true }),
    ).toHaveValue("13:00");
    await review
      .getByRole("button", {
        name: tr("Open calendar", lang) + ": " + tr("Deadline date", lang),
        exact: true,
      })
      .click();
    await expect(page.locator(".localized-calendar")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator(".working")).toHaveCount(0);
    await review
      .getByLabel(
        tr("I reviewed this assignment and confirm only these fields.", lang),
      )
      .check();
    received = page.waitForResponse(
      (r) => r.url().endsWith("/confirm") && r.request().method() === "POST",
    );
    await review
      .getByRole("button", {
        name: tr("Confirm this assignment", lang),
        exact: true,
      })
      .click();
    assert.equal((await received).status(), 200);
    await expect(review).toHaveCount(0);
    value = await state(page);
    assert.equal(value.tasks.length, 1);
    assert.equal(value.tasks[0].minutes, 30);
    assert.equal(
      new Date(value.tasks[0].due).toISOString(),
      "2026-10-23T13:00:00.000Z",
    );
    const source = await (
      await page.request.get(base + "/api/sources/" + value.sources[0].id)
    ).json();
    assert.equal(source.pages[0].text, text);
    proof.checks.push({
      lang,
      timezone_controls_exactly_three: true,
      saved_context_survives_refresh: true,
      connections_timezone_saved: true,
      review_calendar_localized: true,
      confirmed_deadline_instant_preserved: true,
      source_quote_unchanged: true,
      keyboard_escape_focus: true,
    });
    await context.close();
  }
  proof.passed = true;
} finally {
  await browser.close();
  await fs.writeFile(
    folder + "/locale-ui.json",
    JSON.stringify(proof, null, 2) + "\n",
  );
}
console.log(
  JSON.stringify({
    passed: proof.passed,
    states: proof.states.length,
    full_language_flows: proof.checks.length,
    model_calls: 0,
  }),
);
