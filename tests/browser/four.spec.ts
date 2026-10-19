import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";
import { translate } from "../../src/i18n";
import { translations } from "../../src/translations";
import ts from "typescript";

test("four additions: cited clarification, explicit work, gate failure, passport fresh-copy restore", async ({
  page,
}) => {
  const timings: { route: string; ms: number }[] = [];
  page.on("response", async (response) => {
    const route = new URL(response.url()).pathname;
    if (
      [
        "/api/clarify",
        "/api/progress/preview",
        "/api/passport/export",
        "/api/passport/preview",
      ].includes(route)
    ) {
      await response.finished();
      timings.push({
        route,
        ms: Math.round(response.request().timing().responseEnd),
      });
    }
  });
  await page.goto("/");
  await page
    .getByRole("button", {
      name: /^(Explore illustrative workspace|Enter public demo)$/,
    })
    .click();
  await page
    .getByRole("button", { name: "Progress & continuity", exact: false })
    .click();
  // Independent academic imports with identical titles must remain separate.
  await page
    .getByRole("button", { name: "Progress & continuity", exact: false })
    .click();
  for (const course of ["History", "Ethics"]) {
    await page
      .locator("input[type=file]")
      .first()
      .setInputFiles({
        name: course.toLowerCase() + "-lab.md",
        mimeType: "text/markdown",
        buffer: Buffer.from(
          "Assignment: Lab 1\nCourse: " +
            course +
            "\nTerm: 2026 Autumn\nAssignment ID: lab-1\nDue: 2026-10-23T18:00:00+05:00\nEffort: 30 minutes\n- [ ] Explain the result",
        ),
      });
    await expect(
      page.getByText(course.toLowerCase() + "-lab.md", { exact: true }),
    ).toBeVisible();
  }
  await page.getByRole("button", { name: "My week", exact: true }).click();
  await expect(
    page.locator(".task-card").filter({ hasText: "Lab 1" }),
  ).toHaveCount(2);
  await page
    .getByRole("button", { name: "Progress & continuity", exact: false })
    .click();
  const features = page.locator(".continuity").first();
  await features
    .getByRole("button", { name: "Clarify First", exact: true })
    .click();
  await features
    .getByRole("button", { name: "Compare schedule impact", exact: true })
    .click();
  await expect(features.getByText("Branches tested: 2 of 2")).toBeVisible();
  await features
    .getByRole("button", { name: /Choose cited evidence/ })
    .first()
    .click();
  await expect(features.locator(".decision-result")).toHaveCount(0);
  await features
    .getByRole("button", { name: "Progress & Remaining Work", exact: true })
    .click();
  const panel = features.getByTestId("progress-panel");
  await panel
    .getByRole("combobox", { name: "Coursework", exact: true })
    .selectOption({ label: "Web Engineering · Web project" });
  await panel
    .getByLabel("Actual minutes to record", { exact: true })
    .fill("45");
  await panel
    .getByRole("button", { name: "Log work manually", exact: true })
    .click();
  await expect(panel.locator(".effort-comparison")).toContainText("45");
  await expect(panel.locator(".effort-comparison")).toContainText("Unknown");
  await panel.getByLabel("Remaining minutes", { exact: true }).fill("90");
  await panel
    .getByRole("button", { name: "Save remaining estimate", exact: true })
    .click();
  await expect(panel.locator(".effort-comparison")).toContainText("90");
  await panel
    .getByRole("button", { name: "Preview future plan", exact: true })
    .click();
  await expect(panel.getByText("Future minutes: 570")).toBeVisible();
  await panel
    .getByRole("button", { name: "Adopt this future plan", exact: true })
    .click();
  await features
    .getByRole("button", { name: "Handoff Radar", exact: true })
    .click();
  await features
    .getByRole("button", { name: "Link PR-merged prerequisite", exact: true })
    .click();
  await expect(
    features.getByText("Unknown · revalidation needed", { exact: true }),
  ).toBeVisible();
  // Deliberately simulate only the transport failure; live observation has a separate proof.
  await page.route("**/api/gates/*/observe", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "Deterministic browser transport failure",
        },
      }),
    }),
  );
  await features
    .getByRole("button", { name: "Observe public PR", exact: true })
    .click();
  await expect(features.getByRole("alert")).toContainText("external service");
  await page.unroute("**/api/gates/*/observe");
  await features
    .getByRole("button", { name: "Workspace Passport", exact: true })
    .click();
  await features
    .getByRole("button", { name: "Preview portable workspace", exact: true })
    .click();
  await expect(
    features.getByText(/Sources: 6; assignments: 5; work logs: 1; gates: 1/),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await features
    .getByRole("button", { name: "Download .relay.json", exact: true })
    .click();
  const download = await downloadPromise;
  const file =
    "D:/projects/CampusPulseRELAY/.local/four-additions/browser-workspace.relay.json";
  await fs.mkdir("D:/projects/CampusPulseRELAY/.local/four-additions", {
    recursive: true,
  });
  await download.saveAs(file);
  await features.getByLabel("Portable workspace file").setInputFiles(file);
  await expect(
    features.getByRole("heading", { name: "Review restore preview" }),
  ).toBeVisible();
  await features
    .getByRole("button", {
      name: "Import as fresh copy and switch",
      exact: true,
    })
    .click();
  await page.reload();
  await page
    .getByRole("button", { name: "Progress & continuity", exact: false })
    .click();
  await page
    .getByTestId("progress-panel")
    .getByRole("combobox", { name: "Coursework", exact: true })
    .selectOption({ label: "Web Engineering · Web project" });
  await expect(page.locator(".effort-comparison")).toContainText("45");
  await expect(page.locator(".effort-comparison")).toContainText("90");
  await expect(
    page.getByRole("heading", { name: "Your week. Back in balance." }),
  ).toBeVisible();
  await fs.writeFile(
    `docs/evidence/four-browser-timing-${process.env.RELAY_TEST_BASE_URL?.includes("8014") ? "public-mode" : "local"}.json`,
    JSON.stringify(
      {
        environment: process.env.RELAY_TEST_BASE_URL || "localhost",
        kind: "local_deterministic",
        samples: timings,
        no_p95_claim: true,
      },
      null,
      2,
    ),
  );
});

test("four addition controls: EN RU KK at 390 768 1280 1440, keyboard and automated AA", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", {
      name: /^(Explore illustrative workspace|Enter public demo)$/,
    })
    .click();
  await page
    .getByRole("button", { name: "Progress & continuity", exact: false })
    .click();
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const lang of ["en", "ru", "kk"] as const) {
    await page.locator("header select").selectOption(lang);
    for (const width of [390, 768, 1280, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const tab of [
        "Progress & Remaining Work",
        "Clarify First",
        "Handoff Radar",
        "Workspace Passport",
      ]) {
        const control = page
          .locator(".continuity")
          .getByRole("button", { name: translate(tab, lang), exact: true });
        await control.click();
        await expect(
          page
            .locator(".continuity")
            .getByRole("heading", { name: translate(tab, lang), exact: true }),
        ).toBeVisible();
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
        await control.focus();
        await expect(control).toBeFocused();
        await fs.mkdir(process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots/four-additions", { recursive: true });
        await page.screenshot({
          path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots/four-additions"}/${lang}-${width}-${tab.split(" ")[0].toLowerCase()}.png`,
          fullPage: true,
        });
      }
      await fs.mkdir(process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots/four-additions", { recursive: true });
      await page.screenshot({
        path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots/four-additions"}/${lang}-${width}.png`,
        fullPage: true,
      });
    }
  }
  await page.locator("header select").selectOption("en");
  for (const tab of [
    "Progress & Remaining Work",
    "Clarify First",
    "Handoff Radar",
    "Workspace Passport",
  ]) {
    await page
      .locator(".continuity")
      .getByRole("button", { name: tab, exact: true })
      .click();
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(
      result.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      })),
    ).toEqual([]);
  }
});

test("new feature operational strings have complete RU KK catalogs", async () => {
  const source = await fs.readFile("src/Continuity.tsx", "utf8");
  const parsed = ts.createSourceFile(
    "Continuity.tsx",
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const visit = (node: ts.Node) => {
    if (
      ts.isCallExpression(node) &&
      node.expression.getText(parsed) === "tr" &&
      node.arguments[0] &&
      ts.isStringLiteral(node.arguments[0])
    )
      expect(
        Object.hasOwn(translations, node.arguments[0].text),
        node.arguments[0].text,
      ).toBe(true);
    ts.forEachChild(node, visit);
  };
  visit(parsed);
});
