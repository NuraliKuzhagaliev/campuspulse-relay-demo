import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import ts from "typescript";
import { translations } from "../../src/translations";
import {
  translate,
  operational,
  errorMessage,
  weekdayText,
  weekRange,
  eventSummary,
} from "../../src/i18n";

test("operational catalog preserves placeholders and covers rendered static copy", () => {
  const names = (text: string) =>
    [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const [key, pair] of Object.entries(translations)) {
    for (const value of pair) {
      expect(value.trim(), key).not.toBe("");
      expect(names(value), key).toEqual(names(key));
    }
    expect(translate(key, "en")).toBe(key);
  }
  const source = fs.readFileSync("src/App.tsx", "utf8");
  const sf = ts.createSourceFile(
    "App.tsx",
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const permitted = new Set([
    "R",
    "/",
    "CP",
    "CAMPUSPULSE RELAY",
    "RELAY",
    "CampusPulse",
    "CampusPulse RELAY",
    "0.1",
    "0.2",
    "SHA256",
    "EN",
    "RU",
    "KK",
    "English",
    "Русский",
    "Қазақша",
    "⌘ / Ctrl K",
    "v.",
    ":",
    ":00",
    "·",
    "–",
    "→",
    "#",
  ]);
  const raw: string[] = [];
  function visit(n: ts.Node) {
    if (
      ts.isJsxText(n) &&
      n.text.trim() &&
      !permitted.has(n.text.replace(/\s+/g, " ").trim())
    )
      raw.push(n.text.trim());
    if (
      ts.isCallExpression(n) &&
      n.expression.getText(sf) === "tr" &&
      n.arguments[0] &&
      ts.isStringLiteral(n.arguments[0])
    )
      expect(
        Object.hasOwn(translations, n.arguments[0].text),
        n.arguments[0].text,
      ).toBe(true);
    if (
      ts.isStringLiteral(n) &&
      Object.hasOwn(translations, n.text) &&
      n.pos > source.indexOf("type View =")
    ) {
      let rendered = false;
      for (let parent = n.parent; parent; parent = parent.parent) {
        if (ts.isArrowFunction(parent) || ts.isFunctionExpression(parent))
          break;
        if (
          ts.isCallExpression(parent) &&
          ["tr", "operational", "label", "errorMessage"].includes(
            parent.expression.getText(sf),
          )
        )
          break;
        if (ts.isJsxAttribute(parent)) {
          rendered = ["title", "aria-label", "placeholder"].includes(
            parent.name.getText(sf),
          );
          break;
        }
        if (ts.isJsxExpression(parent)) {
          rendered =
            !ts.isJsxAttribute(parent.parent) ||
            ["title", "aria-label", "placeholder"].includes(
              parent.parent.name.getText(sf),
            );
          break;
        }
      }
      if (rendered) raw.push(n.text);
    }
    ts.forEachChild(n, visit);
  }
  visit(sf);
  expect(raw).toEqual([]);
  expect(weekdayText(new Date("2026-10-19T12:00:00Z"), "kk")).toBe("Дс");
  expect(
    weekRange(
      new Date("2026-10-19T12:00:00Z"),
      new Date("2026-10-23T12:00:00Z"),
      "kk",
    ),
  ).toBe("19–23 қазан");
  expect(
    eventSummary(
      { type: "action_applied", summary: "Study · Original title" },
      "ru",
    ),
  ).toBe("Study · Original title");
  expect(operational("120 minutes remain unscheduled.", "kk")).toContain("120");
  expect(
    operational(
      "Open the cited requirement and draft: Keep this original rubric",
      "ru",
    ),
  ).toContain("Keep this original rubric");
  expect(
    errorMessage("UPSTREAM_RATE_LIMITED: unknown provider diagnostic", "kk"),
  ).toContain("шегі таусылды");
});

for (const lang of ["ru", "kk"] as const) {
  const copy = {
    ru: {
      enter: "Открыть учебный пример",
      evidence: "Источники",
      recovery: "Новый план",
      activity: "Действия",
      connections: "Подключения",
      choose: "Использовать этот срок",
      close: "Закрыть диалог",
      page: "Страница 1",
      repair: "Перестроить неделю",
      review: "Проверить изменения календаря",
      approve: "Одобрить локальные учебные изменения",
      receipt: "Повторное чтение выполнено",
      lose: "Убрать вторую половину среды",
      back: "Вернуться к исходному плану",
      sourceLabel: "Исходные данные",
      send: "Отправить агенту",
      message: "Сообщение RELAY",
      rate: "Лимит запросов",
      fetch: "Получить актуальный источник курса",
      packet: "Список результатов",
      save: "Сохранить заданные данные",
      native: "Пять улучшений реализованы локально",
      planned: "Запланировано",
      language: "Язык",
    },
    kk: {
      enter: "Көрнекі кеңістікті ашу",
      evidence: "Дереккөздер",
      recovery: "Жаңа жоспар",
      activity: "Әрекеттер",
      connections: "Қосылымдар",
      choose: "Осы мерзімді қолдану",
      close: "Терезені жабу",
      page: "Бет 1",
      repair: "Аптаны қайта жоспарлау",
      review: "Күнтізбе өзгерістерін қарау",
      approve: "Жергілікті үлгі өзгерістерді мақұлдау",
      receipt: "Қайта оқу аяқталды",
      lose: "Сәрсенбінің түстен кейінгі уақытын алып тастау",
      back: "Бастапқы жоспарға оралу",
      sourceLabel: "Бастапқы дерек",
      send: "Агентке жіберу",
      message: "RELAY-ге хабарлама",
      rate: "сұрауларының шегі",
      fetch: "Курстың нақты дереккөзін алу",
      packet: "Нәтижелер тізімі",
      save: "Нақты деректерді сақтау",
      native: "Бес жетілдіру жергілікті іске асырылды",
      planned: "Жоспарланған",
      language: "Тіл",
    },
  }[lang];
  test(`${lang}: conflict, original quote, packet, what-if, exact approval, errors and persistence`, async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByTestId("entry-language").selectOption(lang);
    await page.getByRole("button", { name: copy.enter, exact: true }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", lang);
    await expect(page.getByTestId("language")).toHaveAttribute(
      "aria-label",
      copy.language,
    );
    await expect(page.locator(".local-acceptance")).toContainText(copy.native);
    for (const view of [copy.evidence, copy.connections]) {
      await page.getByRole("button", { name: view, exact: true }).click();
      const result = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect(
        result.violations.map((v) => ({
          id: v.id,
          nodes: v.nodes.map((n) => n.target),
        })),
      ).toEqual([]);
      await page.setViewportSize({ width: 390, height: 844 });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.screenshot({
        path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots"}/${lang}-${view === copy.evidence ? "evidence" : "connections"}-390.png`,
        fullPage: true,
      });
      await page.setViewportSize({ width: 1280, height: 720 });
    }
    await page
      .getByRole("button", { name: copy.evidence, exact: true })
      .click();
    await page
      .getByRole("button", { name: copy.page, exact: true })
      .first()
      .click();
    await expect(page.locator(".source-text")).toContainText(
      "Due: 2026-10-22T18:00:00+05:00",
    );
    await page.getByRole("button", { name: copy.close, exact: true }).click();
    await page
      .getByRole("button", { name: copy.choose, exact: true })
      .nth(1)
      .click();
    await page.getByRole("button", { name: copy.repair, exact: true }).click();
    await page
      .getByRole("button", { name: copy.recovery, exact: true })
      .click();
    await page.locator(".study-block").first().click();
    await expect(
      page.getByRole("heading", { name: copy.packet, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: copy.save, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".packet-facts")).toContainText(
      "Explain the threat model",
    );
    await page.getByRole("button", { name: copy.close, exact: true }).click();
    const scenarioResponse = page.waitForResponse((r) =>
      r.url().endsWith("/api/scenario"),
    );
    await page.getByRole("button", { name: copy.lose, exact: true }).click();
    expect((await (await scenarioResponse).json()).unscheduled_minutes).toBe(
      120,
    );
    await expect(
      page.locator(".plan-stats p").nth(2).locator("strong"),
    ).toHaveText(lang === "ru" ? "2 ч" : "2 сағ");
    await page.getByRole("button", { name: copy.back, exact: true }).click();
    await page.getByRole("button", { name: copy.review, exact: true }).click();
    await expect(page.locator(".approval-target")).toContainText(
      "local-illustrative-calendar",
    );
    await page.screenshot({
      path: `${process.env.RELAY_SCREENSHOT_DIR||"docs/screenshots"}/${lang}-approval-1280.png`,
      fullPage: true,
    });
    await page.getByRole("button", { name: copy.approve, exact: true }).click();
    await expect(
      page.getByRole("heading", { name: copy.receipt, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".journal")).not.toContainText(
      "All actions verified.",
    );
    await page
      .getByRole("textbox", { name: copy.message, exact: true })
      .fill(
        lang === "ru"
          ? "Что изменилось в моём плане?"
          : "Жоспарымда не өзгерді?",
      );
    const sent = page.waitForRequest((r) => r.url().endsWith("/api/chat"));
    await page.getByRole("button", { name: copy.send, exact: true }).click();
    expect((await sent).postDataJSON().language).toBe(lang);
    await expect(page.getByRole("alert")).toContainText("AUTH_REQUIRED");
    await page
      .getByRole("button", { name: copy.connections, exact: true })
      .click();
    await page.route("**/api/sync", (route) =>
      route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "UPSTREAM_RATE_LIMITED",
            message: "Untranslated provider diagnostic for preserved detail",
          },
        }),
      }),
    );
    await page.getByRole("button", { name: copy.fetch, exact: true }).click();
    await expect(page.getByRole("alert")).toContainText(copy.rate);
    await page.reload();
    await expect(page.getByTestId("language")).toHaveValue(lang);
    await expect(page.locator("html")).toHaveAttribute("lang", lang);
  });
}
