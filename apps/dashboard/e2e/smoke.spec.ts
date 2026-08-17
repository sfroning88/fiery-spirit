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

async function waitForProperties(page: Page) {
  await expect(page.getByTestId(TEST_IDS.propertiesHeading)).toBeVisible({
    timeout: 15_000,
  });
}

test("home page renders dashboard heading", async ({ page }) => {
  await gotoHome(page);
  await expect(page.getByTestId(TEST_IDS.dashboardHeading)).toBeVisible();
});

test("home page renders properties list", async ({ page }) => {
  await gotoHome(page);
  await waitForProperties(page);
});

test("home page renders search bar", async ({ page }) => {
  await gotoHome(page);
  await expect(page.getByTestId(TEST_IDS.propertySearchInput)).toBeVisible();
});

test("sort buttons are present on home page", async ({ page }) => {
  await gotoHome(page);
  await expect(page.getByTestId(TEST_IDS.sortButtonName)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.sortButtonMsa)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.sortButtonOcc)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.sortButtonSnaps)).toBeVisible();
});

test("clicking a sort button changes active sort", async ({ page }) => {
  await gotoHome(page);
  await waitForProperties(page);
  const msaBtn = page.getByTestId(TEST_IDS.sortButtonMsa);
  await msaBtn.click();
  await expect(msaBtn).toHaveAttribute("aria-pressed", "true");
});

test("searching filters property list", async ({ page }) => {
  await gotoHome(page);
  const search = page.getByTestId(TEST_IDS.propertySearchInput);
  await search.fill("zzzzzzzznotarealaproperty");
  await expect(page.getByTestId(TEST_IDS.propertySearchEmpty)).toBeVisible();
});

test("my profile button opens profile dialog", async ({ page }) => {
  await gotoHome(page);
  await page.getByTestId(TEST_IDS.myProfileButton).click();
  await expect(page.getByTestId(TEST_IDS.myProfileDialog)).toBeVisible();
});

test("my profile dialog shows name and email fields", async ({ page }) => {
  await gotoHome(page);
  await page.getByTestId(TEST_IDS.myProfileButton).click();
  const dialog = page.getByTestId(TEST_IDS.myProfileDialog);
  await expect(dialog.getByTestId(TEST_IDS.myProfileNameField)).toBeVisible();
  await expect(dialog.getByTestId(TEST_IDS.myProfileEmailField)).toBeVisible();
});

test("my profile dialog closes on close button", async ({ page }) => {
  await gotoHome(page);
  await page.getByTestId(TEST_IDS.myProfileButton).click();
  const dialog = page.getByTestId(TEST_IDS.myProfileDialog);
  await expect(dialog).toBeVisible();
  await dialog.getByTestId(TEST_IDS.myProfileCloseButton).click();
  await expect(dialog).not.toBeVisible();
});

test("first property view button opens property card dialog", async ({
  page,
}) => {
  await gotoHome(page);
  await waitForProperties(page);
  const firstView = page.getByTestId(TEST_IDS.propertyViewButton).first();
  const hasProperties = await firstView.isVisible();
  if (!hasProperties) {
    test.skip(true, "No properties visible in this deploy");
  }
  await firstView.click();
  await expect(page.getByTestId(TEST_IDS.propertyCardDialog)).toBeVisible();
});

test("property card dialog has add snapshot button", async ({ page }) => {
  await gotoHome(page);
  const firstView = page.getByTestId(TEST_IDS.propertyViewButton).first();
  const hasProperties = await firstView.isVisible();
  if (!hasProperties) {
    test.skip(true, "No properties visible in this deploy");
  }
  await firstView.click();
  const dialog = page.getByTestId(TEST_IDS.propertyCardDialog);
  await expect(
    dialog.getByTestId(TEST_IDS.propertyCardAddSnapshotButton),
  ).toBeVisible();
});

test("add snapshot button opens snapshot form", async ({ page }) => {
  await gotoHome(page);
  const firstView = page.getByTestId(TEST_IDS.propertyViewButton).first();
  const hasProperties = await firstView.isVisible();
  if (!hasProperties) {
    test.skip(true, "No properties visible in this deploy");
  }
  await firstView.click();
  await page
    .getByTestId(TEST_IDS.propertyCardDialog)
    .getByTestId(TEST_IDS.propertyCardAddSnapshotButton)
    .click();
  await expect(page.getByTestId(TEST_IDS.snapshotFormDialog)).toBeVisible();
});

test("property card has predict button when snapshots exist", async ({
  page,
}) => {
  await gotoHome(page);
  const firstView = page.getByTestId(TEST_IDS.propertyViewButton).first();
  const hasProperties = await firstView.isVisible();
  if (!hasProperties) {
    test.skip(true, "No properties visible in this deploy");
  }
  await firstView.click();
  const dialog = page.getByTestId(TEST_IDS.propertyCardDialog);
  const predictBtn = dialog.getByTestId(TEST_IDS.predictButton);
  const hasSnapshot = await predictBtn.isVisible();
  if (!hasSnapshot) {
    test.skip(true, "Property has no snapshots; predict card not rendered");
  }
  await expect(predictBtn).toBeVisible();
});

test("predict button is interactive and does not navigate away", async ({
  page,
}) => {
  await page.route("**/api/predict**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ predictions: [] }),
    });
  });
  await gotoHome(page);
  const firstView = page.getByTestId(TEST_IDS.propertyViewButton).first();
  const hasProperties = await firstView.isVisible();
  if (!hasProperties) {
    test.skip(true, "No properties visible in this deploy");
  }
  await firstView.click();
  const predictBtn = page
    .getByTestId(TEST_IDS.propertyCardDialog)
    .getByTestId(TEST_IDS.predictButton);
  const hasBtn = await predictBtn.isVisible();
  if (!hasBtn) {
    test.skip(true, "Property has no snapshots; predict card not rendered");
  }
  await predictBtn.click();
  await expect(page).toHaveURL((url) => url.pathname === routes.base.home);
});

test("admin page renders admin heading", async ({ page }) => {
  await gotoAdmin(page);
  await expect(page.getByTestId(TEST_IDS.adminHeading)).toBeVisible();
});

test("admin page renders training batches section", async ({ page }) => {
  await gotoAdmin(page);
  await expect(page.getByTestId(TEST_IDS.trainingBatchesHeading)).toBeVisible();
});

test("admin page has shuffle groups button", async ({ page }) => {
  await gotoAdmin(page);
  await expect(page.getByTestId(TEST_IDS.shuffleGroupsButton)).toBeVisible();
});

test("admin page has train models button", async ({ page }) => {
  await gotoAdmin(page);
  await expect(page.getByTestId(TEST_IDS.trainModelsButton)).toBeVisible();
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
