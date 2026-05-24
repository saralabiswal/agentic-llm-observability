/**
 * Frontend build, test, or HTML shell configuration for the React app.
 *
 * Author: Sarala Biswal
 */
import { expect, test } from "@playwright/test";

const pages = [
  { nav: "About", heading: "Manage agentic LLM cost and quality in production" },
  { nav: "Quote Agentic Flow", heading: "Quote-to-Cash Agentic Flow" },
  { nav: "Cost Impact", heading: "Cost impact from the agent run" },
  { nav: "Quality Evidence", heading: "Quality and grounding evidence" },
  { nav: "Latency SLOs", heading: "Latency SLOs and percentile view" },
  { nav: "Prompt Governance", heading: "Prompt governance and versions" },
  { nav: "Drift & Alerts", heading: "Drift and alert history" },
  { nav: "Architecture", heading: "How observability plugs in" },
  { nav: "Settings", heading: "Provider and model policy" },
  { nav: "Developer Corner", heading: "Actual prompts behind the Quote-to-Cash agents" },
];

test("all dashboard pages render in the dark shell", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  for (const item of pages) {
    await page.getByRole("button", { name: new RegExp(item.nav) }).click();
    await expect(page.getByText(item.heading).first()).toBeVisible({ timeout: 10_000 });
    const bodyBackground = await page.locator("body").evaluate((node) => getComputedStyle(node).backgroundColor);
    expect(bodyBackground).not.toBe("rgb(255, 255, 255)");
    await expect(page.locator(".chart-card, .architecture-svg, .about-flow-card, .settings-panel, .prompt-panel, .ops-panel, .developer-prompt-panel").first()).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(/"[^"]+":/)).toHaveCount(0);
  }
});

test("developer corner shows actual agent prompt previews", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  await page.getByRole("button", { name: /Developer Corner/ }).click();
  await expect(page.getByText("Actual prompts behind the Quote-to-Cash agents")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("button", { name: /Margin Risk Agent/ })).toBeVisible();
  await page.getByRole("button", { name: /Margin Risk Agent/ }).click();
  await expect(page.getByText("Agent: Margin Risk Agent")).toBeVisible();
  await expect(page.getByText("Prompt: v2.2.margin_risk")).toBeVisible();
  await expect(page.getByText("Policy source")).toBeVisible();
  await expect(page.getByText("Gross Margin Protection Policy")).toBeVisible();
  await expect(page.getByText("Task context: Assess expected margin")).toBeVisible();
  await expect(page.getByText("input_tokens")).toBeVisible();
});

test("topbar refresh action is available", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  await page.getByTitle("Refresh dashboard data").click();
  await expect(page.getByText(/Updated/).first()).toBeVisible();
});

test("settings model selection drives cost impact routing", async ({ page }) => {
  let optimizeTarget = "";
  await page.route("**/costs/summary**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        total_cost_usd: "0.001000",
        total_calls: 5,
        avg_cost_per_call: "0.000200",
        cost_by_model: { "gpt-4o-mini": "0.001000" },
        cost_by_usecase: { quote_to_cash_revenue_command_center: "0.001000" },
        top_cost_driver: "quote_to_cash_revenue_command_center",
        projected_monthly_usd: "0.001000",
        budget_burn_rate_pct: 0.01,
      },
    });
  });
  await page.route("**/costs/timeline**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: [{ date: "2026-05-24", total_cost: "0.001000" }],
    });
  });
  await page.route("**/costs/by-model**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: [{ model: "gpt-4o-mini", provider: "openai", total_cost: "0.001000", call_count: 5, avg_cost: "0.000200" }],
    });
  });
  await page.route("**/costs/optimize**", async (route) => {
    optimizeTarget = new URL(route.request().url()).searchParams.get("target_model") ?? "";
    await route.fulfill({
      contentType: "application/json",
      json: [
        {
          use_case: "quote_to_cash_revenue_command_center",
          current_model: "gpt-4o-mini",
          current_cost_usd: "0.001000",
          recommended_model: "qwen2.5:7b",
          recommended_cost_usd: "0.000240",
          quality_delta_pct: -3.4,
          cost_savings_pct: 76,
          monthly_savings_usd: "0.000760",
          rationale: "Route selected Quote-to-Cash runs through qwen2.5:7b.",
        },
      ],
    });
  });

  await page.goto("http://localhost:5173/");
  await page.getByRole("button", { name: /Settings/ }).click();
  await expect(page.getByRole("radio", { name: /Local LLM/ })).toBeVisible();
  await expect(page.getByRole("radio", { name: /AWS Bedrock/ })).toBeVisible();
  await expect(page.getByRole("radio", { name: /Azure OpenAI/ })).toBeVisible();
  await page.getByRole("radio", { name: /AWS Bedrock/ }).click();
  await expect(page.getByText("cost planning only")).toBeVisible();
  await page.getByRole("radio", { name: /Qwen 2.5/ }).click();
  await page.getByRole("button", { name: /Quote Agentic Flow/ }).click();
  await expect(page.getByLabel("Runtime Path")).toContainText("Local LLM - Qwen 2.5");
  await expect(page.getByLabel("Runtime Path")).toContainText("Managed in Settings");
  await page.getByRole("button", { name: /Cost Impact/ }).click();

  await expect(page.getByText("Settings runtime: Qwen 2.5")).toBeVisible();
  await expect(page.getByText("No better routing policy found")).toBeVisible();
  await expect(page.getByText("AWS Bedrock: Claude 3.5 Haiku")).toBeVisible();
  await expect(page.getByText("cost planning only")).toBeVisible();
  expect(optimizeTarget).toBe("qwen2.5:7b");
});

test("revenue command center runs quote analysis and shows trace", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  await page.getByRole("button", { name: /Quote Agentic Flow/ }).click();
  await expect(page.getByText("Quote-to-Cash Agentic Flow").first()).toBeVisible();
  await page.getByRole("button", { name: /Run Agent Flow/ }).click();
  await expect(page.getByText("Latest Observability Trace")).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText("Margin Risk", { exact: true })).toBeVisible();
  await expect(page.getByText("Customer-facing quote note")).toBeVisible();
  await expect(page.getByText("Continue observability flow")).toBeVisible();
  await page.getByRole("button", { name: /^Cost$/ }).click();
  await expect(page.getByText("Cost impact from the agent run")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Business flow", { exact: true })).toBeVisible();
  await expect(page.getByText("Projection model:")).toBeVisible();
  await expect(page.getByText("Settings Cost Change")).toBeVisible();
  await expect(page.getByText("Quote-to-Cash Agentic Flow").first()).toBeVisible();
  await expect(page.locator(".stat-session-row").filter({ hasText: "Session runs" }).locator("strong")).toHaveText("1");
});
