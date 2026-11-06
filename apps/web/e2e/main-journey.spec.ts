import { expect, test, type Page } from "@playwright/test";

/** Today's date in Kenya, as the API and M-Pesa see it. */
function kenyanToday(): { day: number; month: number; year: number } {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Nairobi",
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).formatToParts(new Date());
  const value = (type: string) =>
    Number(parts.find((part) => part.type === type)?.value);
  return { day: value("day"), month: value("month"), year: value("year") };
}

/** An invented M-Pesa message dated today, with a code no earlier run used. */
function inventedMessage(): { text: string; year: number } {
  const { day, month, year } = kenyanToday();
  const code = `UK${Date.now().toString(36).toUpperCase()}`
    .slice(0, 10)
    .padEnd(10, "X");
  const text =
    `${code} Confirmed. Ksh150.00 sent to JANE WANJIKU 0712345678 on ` +
    `${day}/${month}/${year % 100} at 6:00 AM. New M-PESA balance is ` +
    `Ksh2,339.58. Transaction cost, Ksh7.00.`;
  return { text, year };
}

/** A link in the bottom navigation. */
function nav(page: Page, name: string) {
  return page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name });
}

/** The home page does not refresh on its own yet, so reload until the worker is done. */
async function waitUntilRead(page: Page) {
  await expect(async () => {
    await page.reload();
    await expect(page.getByText("Needs a look")).toBeVisible({
      timeout: 1_000,
    });
  }).toPass({ timeout: 60_000, intervals: [2_000] });
}

test("sign up, record a payment, confirm it, export the year and delete the account", async ({
  page,
}) => {
  const email = `e2e-${Date.now()}@example.com`;
  const password = "journey-test-password-2026";
  const message = inventedMessage();

  await test.step("sign up", async () => {
    await page.goto("/signup");
    await page.getByLabel("Your name").fill("Journey Test");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(
      page.getByRole("heading", { name: "Hello, Journey Test" }),
    ).toBeVisible();
  });

  await test.step("paste an M-Pesa message and wait for it to be read", async () => {
    await page.getByRole("button", { name: "Paste M-Pesa message" }).click();
    await page.getByLabel("M-Pesa message").fill(message.text);
    await page.getByRole("button", { name: "Save message" }).click();
    await expect(page.getByText("Saved.")).toBeVisible();
    await waitUntilRead(page);
  });

  await test.step("confirm it with a category", async () => {
    await nav(page, "To check").click();
    await expect(page.getByText("KSh 150.00")).toBeVisible();
    await expect(page.getByText("JANE WANJIKU")).toBeVisible();
    await page.getByRole("button", { name: "Change" }).click();
    await page
      .getByLabel("What it was for")
      .selectOption({ label: "Family support given" });
    await page.getByRole("button", { name: "Save and confirm" }).click();
    await expect(page.getByText("KSh 150.00")).toBeHidden();
  });

  await test.step("see it in the ledger", async () => {
    await nav(page, "Ledger").click();
    const row = page.getByRole("listitem").filter({ hasText: "JANE WANJIKU" });
    await expect(row).toContainText("Family support given");
    await expect(row).toContainText("−KSh 150.00");
  });

  await test.step("download the year's workbook", async () => {
    await page.getByLabel("Year").selectOption(String(message.year));
    const downloading = page.waitForEvent("download");
    await page
      .getByRole("link", { name: `Download ${message.year} (Excel)` })
      .click();
    const download = await downloading;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
    const stream = await download.createReadStream();
    const [first] = await stream.toArray();
    // An .xlsx file is a zip archive, which starts with "PK".
    expect((first as Buffer).subarray(0, 2).toString()).toBe("PK");
  });

  await test.step("delete the account", async () => {
    await page.getByRole("link", { name: "Account", exact: true }).click();
    await page.getByLabel(`Type ${email} to confirm`).fill(email);
    await page.getByRole("button", { name: "Delete my account" }).click();
    await expect(page).toHaveURL(/\/signup$/);
  });

  await test.step("the deleted account cannot sign in", async () => {
    await page.goto("/signin");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    // Not getByRole("alert"): Next.js adds a hidden alert region that announces page changes.
    await expect(
      page.getByText("The email or password is wrong."),
    ).toBeVisible();
  });
});
