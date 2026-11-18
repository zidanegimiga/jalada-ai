import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/** WCAG 2.2 at levels A and AA. */
const STANDARD = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

const SIGNED_OUT = ["/signup", "/signin"];
// /ask shows the conversation where the assistant is on, and a notice where it is not.
const SIGNED_IN = ["/", "/review", "/ledger", "/ask", "/account", "/design"];

/** The smallest a thumb target may be, in CSS pixels. WCAG asks for 24; phones need 44. */
const TAP = 44;

/** Each rule axe finds broken on the page, with the elements that break it. */
async function axeProblems(page: Page): Promise<string[]> {
  const { violations } = await new AxeBuilder({ page })
    .withTags(STANDARD)
    .analyze();
  return violations.map(
    (v) =>
      `${v.id}: ${v.help}\n` +
      v.nodes
        .map((n) => `  ${n.target.join(" ")}: ${n.failureSummary ?? ""}`)
        .join("\n"),
  );
}

/**
 * Links, buttons and fields smaller than a thumb. Links inside a sentence are left out,
 * as WCAG allows, and so are visually hidden inputs behind a label.
 */
async function smallTargets(page: Page): Promise<string[]> {
  return page.$$eval(
    "a, button, input, select, textarea, summary",
    (elements, tap) =>
      elements.flatMap((element) => {
        const box = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        const hidden = box.width <= 1 || style.visibility === "hidden";
        const inSentence =
          element.tagName === "A" && style.display === "inline";
        if (hidden || inSentence || (box.width >= tap && box.height >= tap)) {
          return [];
        }
        const name = (element.textContent ?? "").trim() || element.outerHTML;
        return [`${name.slice(0, 60)}: ${box.width}x${box.height}`];
      }),
    TAP,
  );
}

/** An invented M-Pesa message with a code no earlier run used, so To check has a card. */
function inventedMessage(): string {
  const today = new Date();
  const code = `UA${Date.now().toString(36).toUpperCase()}`
    .slice(0, 10)
    .padEnd(10, "X");
  return (
    `${code} Confirmed. Ksh150.00 sent to JANE WANJIKU 0712345678 on ` +
    `${today.getDate()}/${today.getMonth() + 1}/${today.getFullYear() % 100} ` +
    `at 6:00 AM. New M-PESA balance is Ksh2,339.58. Transaction cost, Ksh7.00.`
  );
}

/** Opens each page in the light and dark themes and collects what is wrong. */
async function checkPages(page: Page, paths: string[]) {
  for (const scheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme: scheme });
    for (const path of paths) {
      await test.step(`${path} (${scheme})`, async () => {
        await page.goto(path);
        await page.waitForLoadState("networkidle");
        expect
          .soft(await axeProblems(page), `axe on ${path}, ${scheme} theme`)
          .toEqual([]);
        if (scheme === "light") {
          expect
            .soft(await smallTargets(page), `tap targets on ${path}`)
            .toEqual([]);
        }
      });
    }
  }
}

test("every page meets WCAG 2.2 AA, with thumb-sized targets", async ({
  page,
}) => {
  await checkPages(page, SIGNED_OUT);

  await page.goto("/signup");
  await page.getByLabel("Your name").fill("Access Test");
  await page.getByLabel("Email").fill(`a11y-${Date.now()}@example.com`);
  await page.getByLabel("Password").fill(crypto.randomUUID());
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(
    page.getByRole("heading", { name: "Hello, Access" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Paste M-Pesa message" }).click();
  await page.getByLabel("M-Pesa message").fill(inventedMessage());
  await page.getByRole("button", { name: "Save message" }).click();
  await expect(page.getByText("Needs a look")).toBeVisible({ timeout: 60_000 });

  await checkPages(page, SIGNED_IN);
});
