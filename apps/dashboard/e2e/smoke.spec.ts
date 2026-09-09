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

test("home page renders completely", async ({ page }) => {
  await gotoHome(page);
  await Promise.all([
    expect(page.getByTestId(TEST_IDS.dashboardHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.volcanoesHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.inferenceButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.signalField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.myProfileButton)).toBeVisible(),
  ]);
  await expect(page.getByTestId(TEST_IDS.inferenceButton)).toBeDisabled();
  const signal = page.getByTestId(TEST_IDS.signalField);
  await expect(signal).toHaveValue("deformation");
  await signal.selectOption("seismic");
  await expect(signal).toHaveValue("seismic");
  const map = page.getByTestId(TEST_IDS.homeMap);
  await expect(map).toBeVisible();
  await expect(map.locator("canvas")).toBeVisible();
  const marker = map.locator(".maplibregl-marker").first();
  if ((await map.locator(".maplibregl-marker").count()) === 0) {
    return;
  }
  await expect(marker).toBeVisible();
  await marker.click();
  const popup = page.getByTestId(TEST_IDS.volcanoPopup);
  await expect(popup).toBeVisible();
  await expect(popup.getByText(/interferograms/i)).toBeVisible();
});

test("admin page renders completely", async ({ page }) => {
  await gotoAdmin(page);
  await Promise.all([
    expect(page.getByTestId(TEST_IDS.adminHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.modelsHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.ingestButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.refineButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.trainButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.batchButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.promoteButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.refreshButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.maxSamplesField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.signalField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.sourceField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.stageField)).toBeVisible(),
  ]);
  const maxSamples = page.getByTestId(TEST_IDS.maxSamplesField);
  await maxSamples.fill("10");
  await expect(maxSamples).toHaveValue("10");
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

test("unauthenticated visit to home stays in browser", async ({ browser }) => {
  const context = await browser.newContext({ storageState: undefined });
  const page = await context.newPage();
  await page.goto(routes.base.home);
  await expect(page).toHaveURL((url) => url.pathname === routes.base.home);
  await expect(page.getByTestId(TEST_IDS.homeScreen)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.dashboardHeading)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.openAdminLink)).toHaveCount(0);
  await expect(page.getByTestId(TEST_IDS.myProfileButton)).toHaveCount(0);
  await expect(page.getByTestId(TEST_IDS.createProfileLink)).toBeVisible();
  await page.getByTestId(TEST_IDS.createProfileLink).click();
  await expect(page).toHaveURL((url) => url.pathname === routes.auth.login);
  await context.close();
});

test("unauthenticated visit to admin returns to login", async ({ browser }) => {
  const context = await browser.newContext({ storageState: undefined });
  const page = await context.newPage();
  await page.goto(routes.admin.root);
  await expect(page).toHaveURL((url) => url.pathname === routes.auth.login);
  await context.close();
});
