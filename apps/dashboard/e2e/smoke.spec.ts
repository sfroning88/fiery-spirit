import { test, expect, type Page } from "@playwright/test";
import { TEST_IDS } from "@/lib/test-ids";
import { routes } from "@lib/routes";

async function gotoHome(page: Page) {
  await page.goto(routes.base.home);
  await expect(page.getByTestId(TEST_IDS.homeScreen)).toBeVisible();
}

async function gotoAdmin(page: Page) {
  await page.goto(routes.admin.root);
  await expect(page.getByTestId(TEST_IDS.adminScreen)).toBeVisible();
}

test("home page renders dashboard heading", async ({ page }) => {
  await gotoHome(page);
  await expect(page.getByTestId(TEST_IDS.dashboardHeading)).toBeVisible();
});

test("admin page renders admin heading", async ({ page }) => {
  await gotoAdmin(page);
  await expect(page.getByTestId(TEST_IDS.adminHeading)).toBeVisible();
});

test("admin page back to dashboard link navigates to home", async ({
  page,
}) => {
  await gotoAdmin(page);
  await page.getByTestId(TEST_IDS.backToDashboardLink).click();
  await expect(page).toHaveURL((url) => url.pathname === routes.base.home);
});

test("home page open admin link navigates to admin", async ({ page }) => {
  await gotoHome(page);
  const adminLink = page.getByTestId(TEST_IDS.openAdminLink);
  const isAdmin = await adminLink.isVisible();
  if (!isAdmin) {
    test.skip(true, "Playwright user is not a platform admin");
  }
  await adminLink.click();
  await expect(page).toHaveURL((url) => url.pathname === routes.admin.root);
});

test("unauthenticated visit to home redirects to login", async ({
  browser,
}) => {
  const context = await browser.newContext({ storageState: undefined });
  const page = await context.newPage();
  await page.goto(routes.base.home);
  await expect(page).toHaveURL((url) => url.pathname === routes.auth.login);
  await context.close();
});
