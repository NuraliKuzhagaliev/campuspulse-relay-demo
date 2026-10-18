import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";

test("judge compares deadline rescue, chooses availability and reviews fresh approval", async ({
  page,
}) => {
  const measurements: { route: string; milliseconds: number }[] = [];
  page.on("response", async (response) => {
    const route = new URL(response.url()).pathname;
    if (["/api/plan", "/api/rescue", "/api/scenario"].includes(route)) {
      await response.finished();
      const timing = response.request().timing();
      measurements.push({
        route,
        milliseconds: Math.round(timing.responseEnd),
      });
    }
  });
  await page.goto("/");
  await page
    .getByRole("button", { name: /^(Explore illustrative workspace|Enter public demo)$/ })
    .click();
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await page
    .locator(".fact-grid>div")
    .filter({ hasText: "2026-10-21" })
    .getByRole("button", { name: "Use this deadline" })
    .click();
  await page
    .getByRole("button", { name: "Repair my week", exact: true })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Your week is ready" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Judge challenge", exact: true })
    .click();
  for (const [start, end] of [
    ["2026-10-20T16:00:00+05:00", "2026-10-20T17:00:00+05:00"],
    ["2026-10-23T17:00:00+05:00", "2026-10-23T18:00:00+05:00"],
  ]) {
    await page.getByLabel("Candidate start (ISO with offset)").fill(start);
    await page.getByLabel("Candidate end (ISO with offset)").fill(end);
    await page.getByRole("button", { name: "Add permitted option" }).click();
  }
  await page
    .getByRole("button", { name: "Compare permitted remedies", exact: true })
    .click();
  await expect(page.getByText("Total shortage: 120")).toBeVisible();
  await expect(
    page.getByText(/60 minutes missing before deadline/),
  ).toBeVisible();
  await expect(
    page.getByText("Minimum among offered combinations", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Use this availability and revalidate" })
    .first()
    .click();
  await expect(
    page.getByText("Feasible allocation", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Review calendar actions" }).click();
  await expect(
    page.getByRole("button", { name: "Approve illustrative local actions" }),
  ).toBeVisible();
  await fs.writeFile(
    process.env.RELAY_TEST_BASE_URL?.startsWith("https:")?".local/logs/challenge-hosted-metrics.json":".local/logs/challenge-ui-metrics.json",
    JSON.stringify(
      {
        checked_at: new Date().toISOString(),
        mode: process.env.RELAY_TEST_BASE_URL?.startsWith("https:")?"hosted_illustrative":"local_illustrative",
        observations: measurements,
        model_calls: 0,
        p95_reported: false,
      },
      null,
      2,
    ),
  );
});

test("unseen brief, explicit mapping, preflight, languages and responsive challenge", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: /^(Explore illustrative workspace|Enter public demo)$/ })
    .click();
  const name = "judge-brief-" + Date.now() + ".md";
  await page.locator("input[type=file]").setInputFiles({
    name,
    mimeType: "text/markdown",
    buffer: Buffer.from(
      "Assignment: Analysis draft\nCourse: Ethics\nDue: 2026-10-23T18:00:00+05:00\nEffort: 60 minutes\nFilename: ethics-*.md\nFormat: md\nSections: Argument;Limitations\nWords: 3-100\n- [ ] Justify the original reasoning",
    ),
  });
  await expect(
    page.getByRole("button", { name: "Confirm assignment mapping" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Confirm assignment mapping" })
    .click();
  const mapping = page.locator(".mapping-panel");
  await mapping
    .getByRole("combobox", { name: "Assignment", exact: true })
    .selectOption({ label: "Analysis draft · Ethics" });
  await mapping.getByLabel("Course", { exact: true }).fill("Ethics");
  await mapping.getByLabel("Academic term").fill("Fall 2026");
  await mapping.getByLabel("Stable assignment key").fill("analysis-1");
  await mapping
    .getByRole("button", { name: "Confirm mapping", exact: true })
    .click();
  await expect(mapping).toHaveCount(0);
  const preflight = page.locator(".workshop-card").filter({
    has: page.getByRole("heading", { name: "Submission preflight" }),
  });
  await preflight
    .getByRole("combobox", { name: "Assignment", exact: true })
    .selectOption({ label: "Ethics · Analysis draft" });
  await preflight.locator("input[type=file]").setInputFiles({
    name: "wrong.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# Argument\nA reasoned claim."),
  });
  await expect(
    preflight
      .locator(".preflight-result")
      .filter({ hasText: "Sections: Argument;Limitations" }),
  ).toContainText("Missing");
  await expect(
    preflight
      .locator(".preflight-result")
      .filter({ hasText: "Justify the original reasoning" }),
  ).toContainText("Needs review");
  await preflight.locator("input[type=file]").setInputFiles({
    name: "ethics-a.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(
      "# Argument\nA reasoned claim.\n# Limitations\nA stated limitation.",
    ),
  });
  await expect(
    preflight
      .locator(".preflight-result")
      .filter({ hasText: "Sections: Argument;Limitations" }),
  ).toContainText("Verified");
  for (const [language, nav] of [
    ["en", "Judge challenge"],
    ["ru", "Испытание для жюри"],
    ["kk", "Қазылар сынағы"],
  ]) {
    await page.getByTestId("language").selectOption(language);
    for (const [width, height] of [
      [1440, 900],
      [1280, 720],
      [1024, 768],
      [390, 844],
    ]) {
      await page.setViewportSize({ width, height });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await expect(
        page.getByRole("button", { name: nav, exact: true }),
      ).toBeVisible();
    }
    expect(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    ).toEqual([]);
    await page.screenshot({
      path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots"}/challenge-${language}-390.png`,
      fullPage: true,
    });
  }
  await page.getByTestId("language").selectOption("en");
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({
    path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots"}/challenge-1440.png`,
    fullPage: true,
  });
});
