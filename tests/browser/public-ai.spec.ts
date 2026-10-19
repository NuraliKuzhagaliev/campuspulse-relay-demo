import { test, expect } from "@playwright/test";

test("public queue UI resumes after refresh without duplicate submission; localized states and cancellation", async ({
  page,
}) => {
  // Deliberately simulated UI responses. This test makes zero provider calls.
  let posts = 0,
    active = false,
    complete = false;
  let reset = false;
  const run = "a".repeat(32),
    conversation = "b".repeat(32);
  await page.route("**/api/state", async (route) => {
    const response = await route.fetch(),
      state = await response.json();
    Object.assign(state.agent, {
      configured: true,
      public_access: true,
      provider: "gemini_developer",
    });
    state.demo={public:true,session_seconds:7200,storage:'temporary'};
    if(reset) state.workspace_id='demo-reset-ui-only';
    await route.fulfill({ response, json: state });
  });
  await page.route('**/api/demo/reset',route=>{
    reset=true;
    return route.fulfill({json:{csrf:'ui-reset-only'}});
  });
  await page.route("**/api/conversation", (route) =>
    route.fulfill({
      json: { id: conversation, turns: [], active_run: active ? run : null },
    }),
  );
  const waiting = () => ({
    status: "queued",
    run_id: run,
    conversation_id: conversation,
    position: 7,
    poll_after_ms: 100,
    quota: { wait_seconds: 60 },
  });
  await page.route("**/api/chat", (route) => {
    posts++;
    active = true;
    return route.fulfill({ status: 202, json: waiting() });
  });
  await page.route("**/api/runs/" + run, (route) =>
    route.fulfill({
      json: complete
        ? {
            status: "complete",
            text: "SIMULATED UI RESULT ONLY",
            run_id: run,
            conversation_id: conversation,
          }
        : waiting(),
    }),
  );
  await page.route("**/api/runs/" + run + "/cancel", (route) => {
    active = false;
    return route.fulfill({
      json: { status: "cancelled", remote_compute_stopped: true },
    });
  });
  await page.goto("/");
  await expect(page.locator(".live-access input[type=checkbox]")).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Explore illustrative workspace",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Use a private AI invitation", { exact: true }),
  ).toHaveCount(0);
  await page.locator(".live-access input[type=checkbox]").check();
  await page
    .locator('.assistant input[maxlength="6000"]')
    .fill("Simulated queue UI check");
  await page.locator(".assistant > form button").click();
  await expect(page.getByTestId("ai-queue")).toContainText("Queue position");
  await page.reload();
  await expect(page.getByTestId("ai-queue")).toBeVisible();
  await expect(
    page.locator(".live-access input[type=checkbox]"),
  ).not.toBeChecked();
  expect(posts).toBe(1);
  for (const [lang, text] of [
    ["ru", "Вопрос в очереди"],
    ["kk", "Сұрақ кезекте"],
    ["en", "Question queued"],
  ]) {
    await page.getByTestId("language").selectOption(lang);
    await expect(page.getByTestId("ai-queue")).toContainText(text);
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
  }
  complete = true;
  await expect(page.locator(".answer pre")).toHaveText(
    "SIMULATED UI RESULT ONLY",
  );
  await expect(page.getByTestId("ai-queue")).toHaveCount(0);
  expect(posts).toBe(1);
  complete = false;
  await page.locator(".live-access input[type=checkbox]").check();
  await page
    .locator('.assistant input[maxlength="6000"]')
    .fill("Cancel simulated queued request");
  await page.locator(".assistant > form button").click();
  await expect(page.getByTestId("ai-queue")).toBeVisible();
  await page.getByRole("button", { name: "Stop waiting", exact: true }).click();
  await expect(page.getByTestId("ai-queue")).toHaveCount(0);
  const response=page.waitForResponse('**/api/demo/reset');
  await page.getByRole('button',{name:'Start a fresh demo',exact:true}).click();
  await response;
  await expect(page.locator('.working')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Explore illustrative workspace',exact:true})).toHaveCount(0);
  await expect(page.locator('.live-access input[type=checkbox]')).toBeVisible();
});
