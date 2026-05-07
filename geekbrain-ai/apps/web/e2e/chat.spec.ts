import { test, expect } from "@playwright/test";

test.describe("GeekBrain AI Chat Interface", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders chat thread with welcome message", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Hello");
    await expect(page.locator('[aria-label="Message input"]')).toBeVisible();
    await expect(page.locator('[aria-label="Send message"]')).toBeVisible();
  });

  test("can type a message in the composer", async ({ page }) => {
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What services does GeekBrain run?");
    await expect(input).toHaveValue("What services does GeekBrain run?");
  });

  test("send button is visible when not running", async ({ page }) => {
    await expect(page.locator('[aria-label="Send message"]')).toBeVisible();
  });
});

test.describe("L1: Knowledge Base Retrieval", () => {
  test("answers question about company services", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What services does GeekBrain run?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText(/PaymentGW|OrderSvc|AuthSvc/i);
  });

  test("answers question about deployment policy", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What is the deployment policy?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText(/deploy/i);
  });
});

test.describe("L2: Conflict Resolution", () => {
  test("resolves API rate limit conflict in favor of v2", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What is the API rate limit?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText("1000");
  });
});

test.describe("L3: Tool Use - Database & Metrics", () => {
  test("answers cost question using database tool", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What is the total cost of PaymentGW in Q1 2026?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText(/16[,.]?500/);
  });

  test("answers current metrics question using API tool", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What is the current p99 latency of PaymentGW?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText(/\d+\s*ms/i);
  });

  test("reports NotificationSvc degraded status", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');
    await input.fill("What is the current status of NotificationSvc?");
    await page.locator('[aria-label="Send message"]').click();

    const assistantMessage = page.locator('[data-role="assistant"]');
    await expect(assistantMessage).toBeVisible({ timeout: 20_000 });
    await expect(assistantMessage).toContainText(/degraded|alert|high.latency/i);
  });
});

test.describe("L4: Conversation Memory", () => {
  test("resolves follow-up question using context from prior turn", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('[aria-label="Message input"]');

    await input.fill("Tell me about PaymentGW");
    await page.locator('[aria-label="Send message"]').click();

    const firstResponse = page.locator('[data-role="assistant"]').first();
    await expect(firstResponse).toBeVisible({ timeout: 20_000 });

    await input.fill("What incidents did it have in Q1?");
    await page.locator('[aria-label="Send message"]').click();

    const secondResponse = page.locator('[data-role="assistant"]').nth(1);
    await expect(secondResponse).toBeVisible({ timeout: 20_000 });
    await expect(secondResponse).toContainText(/INC-001|INC-003|INC-005|incident/i);
  });
});
