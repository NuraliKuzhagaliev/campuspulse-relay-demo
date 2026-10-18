import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/browser",
  timeout: 45000,
  workers: 1,
  reporter: [
    ["list"],
    ["json", { outputFile: ".local/logs/playwright-results.json" }],
  ],
  use: {
    baseURL: process.env.RELAY_TEST_BASE_URL || "http://127.0.0.1:8000",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir: ".local/browser-results",
});
