import { test, expect } from "@playwright/test";

test("expired identity exposes one-use judge entry without loading a cached workspace", async ({ page }) => {
  await page.route("**/api/session", route => route.fulfill({status: 401, contentType: "application/json", body: JSON.stringify({error: {code: "AUTH_REQUIRED", message: "Sign in or use an invitation."}})}));
  await page.route("**/api/judge/claim", route => route.fulfill({status: 403, contentType: "application/json", body: JSON.stringify({error: {code: "ACCESS_DENIED", message: "Invitation is invalid, expired or already used."}})}));
  await page.goto("/");
  const field=page.getByLabel("Owner-issued one-use judge invitation");
  await expect(field).toBeVisible();
  await field.fill("short");
  await expect(page.getByRole("button",{name:"Open isolated demo"})).toBeDisabled();
  await field.fill("a".repeat(43));
  await page.getByRole("button",{name:"Open isolated demo"}).click();
  await expect(page.getByRole("alert")).toContainText("already used");
  await expect(page.getByRole("heading",{name:"Evidence"})).toHaveCount(0);
});

test("evidence → feasible plan → what-if → approval → verified receipt", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Explore illustrative workspace" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your week. Back in balance." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Repair my week" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Resolve the deadline conflict",
  );
  await page.getByRole("button", { name: "Dismiss error" }).click();
  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await expect(
    page.getByText("two sources disagree", { exact: false }),
  ).toHaveCount(0);
  await expect(
    page.getByText("2026-10-21 · 18:00:00+05:00", { exact: true }),
  ).toBeVisible();
  const earlier = page
    .locator(".fact-grid>div")
    .filter({ hasText: "2026-10-21" });
  await earlier.getByRole("button", { name: "Use this deadline" }).click();
  await expect(
    page.getByText("Choice recorded", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Repair my week" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Your week is ready" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "My week", exact: true }).click();
  await expect(page.locator(".study-block").first()).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/week-1440.png",
    fullPage: true,
  });
  await page.locator(".study-block").first().click();
  await expect(
    page.getByRole("heading", { name: "Deliverable checklist" }),
  ).toBeVisible();
  await expect(page.getByText("planned", { exact: true }).last()).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Recovery", exact: true }).click();
  await page.getByRole("button", { name: "Lose Wednesday afternoon" }).click();
  await expect(
    page.getByText("What-if · baseline unchanged", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".plan-stats")).toContainText("2h");
  await expect(
    page.getByRole("button", { name: "Review calendar actions" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Return to baseline" }).click();
  await page.getByRole("button", { name: "Review calendar actions" }).click();
  await expect(
    page.getByText("Illustrative local calendar — no external writes"),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Approve illustrative local actions" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Read-back completed" }),
  ).toBeVisible();
  await expect(
    page.getByText("Illustrative local calendar", { exact: true }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/receipt-1440.png",
    fullPage: true,
  });
});

test("unseen file with missing deadline stays partial, sources navigate", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Explore illustrative workspace" })
    .click();
  await page
    .locator("input[type=file]")
    .setInputFiles({
      name: "unseen-assignment.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(
        "Assignment: Independent unseen essay\nCourse: Ethics\nDue: 03/04\nEffort: 60 minutes\n- [ ] Explain a counterargument",
      ),
    });
  await expect(
    page.getByText("unseen-assignment.md", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button")
    .filter({ hasText: "unseen-assignment.md" })
    .click();
  await expect(page.locator(".source-text")).toContainText("Due: 03/04");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "My week", exact: true }).click();
  await page
    .getByRole("button")
    .filter({ hasText: "Independent unseen essay" })
    .click();
  await expect(page.getByText("60 minutes estimated")).toBeVisible();
  await expect(
    page
      .locator(".packet-facts")
      .getByRole("button")
      .filter({ hasText: "Due: 03/04" }),
  ).toBeVisible();
});

test("responsive layouts, keyboard palette, languages and honest disconnected AI", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Explore illustrative workspace" })
    .click();
  for (const viewport of [
    { width: 1280, height: 720 },
    { width: 1024, height: 768 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await expect(
      page.getByRole("heading", { name: "Your week. Back in balance." }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `docs/screenshots/week-${viewport.width}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.keyboard.press("Control+k");
  await expect(
    page.getByRole("heading", { name: "What would you like to do?" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByLabel("Language", { exact: true }).selectOption("ru");
  await expect(
    page.getByRole("heading", { name: "Ваша неделя. Снова в балансе." }),
  ).toBeVisible();
  await page.getByLabel("Language", { exact: true }).selectOption("kk");
  await expect(
    page.getByRole("heading", { name: "Сіздің аптаңыз. Қайта теңгерімде." }),
  ).toBeVisible();
  await page.getByLabel("Language", { exact: true }).selectOption("en");
  await page
    .getByRole("textbox", { name: "Message RELAY" })
    .fill("Can you summarize my course?");
  await page.getByRole("button", { name: "Send to agent" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "real Gemini Agent Engine is not connected",
  );
});
