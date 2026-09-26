import { test, expect } from '@playwright/test';

const slugs = ['introduction', 'setup', 'quickstart', 'commands', 'cli', 'ingestion', 'graphs', 'ml', 'cases', 'architecture', 'api', 'data-models', 'troubleshooting', 'faq', 'deadlock'];

// Opening choreography is exercised separately in public-motion.spec.ts.
test.beforeEach(async ({ page }) => { await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1')); });

test('landing has readable editorial typography, interactive art, and working docs entry', async ({ page }, testInfo) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Follow the flow.');
  await expect(page.locator('.landing-hero h1')).toHaveCSS('font-family', /Newsreader/);
  await expect(page.locator('.landing-deck')).toHaveCSS('font-family', /DM Sans/);
  await expect(page.getByRole('button', { name: 'Rotate or flick the Bitcoin' })).toBeVisible();
  await page.getByRole('button', { name: 'Pause motion' }).click();
  await expect(page.getByRole('button', { name: 'Resume motion' })).toHaveAttribute('aria-pressed', 'true');
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: testInfo.outputPath('landing-desktop.png'), fullPage: true });
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await expect(page).toHaveURL(/\/docs\/introduction$/);
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Investigate Bitcoin transaction flows');
});

test('all fifteen pages render offline content and valid local anchors without backend calls', async ({ page }) => {
  const errors: string[] = [];
  const backendCalls: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (/\/(cases|health|alerts|api)\//.test(new URL(request.url()).pathname) && request.resourceType() === 'fetch') backendCalls.push(request.url()); });
  for (const slug of slugs) {
    await page.goto(`/docs/${slug}`);
    await expect(page.locator('.docs-prose')).toBeVisible();
    expect(await page.locator('.docs-prose').innerText()).not.toContain('Frontend content integration notes');
    const broken = await page.locator('a[href^="#"]').evaluateAll(links => links.map(link => link.getAttribute('href')!.slice(1)).filter(id => id && !document.getElementById(decodeURIComponent(id))));
    expect(broken, slug).toEqual([]);
    await expect(page.locator('.docs-sidebar a[aria-current="page"]')).toHaveAttribute('href', `/docs/${slug}`);
  }
  expect(errors).toEqual([]);
  expect(backendCalls).toEqual([]);
});

test('search supports command text, keyboard selection, no-results, and Escape', async ({ page }) => {
  await page.goto('/docs/introduction');
  await expect(page.locator('.docs-prose')).toBeVisible();
  await page.keyboard.press('Control+k');
  const search = page.getByRole('textbox', { name: 'Search documentation' });
  await expect(search).toBeFocused();
  await search.fill('alerts --limit');
  await expect(page.locator('.docs-search-result').first()).toContainText('Web terminal commands');
  await search.press('Enter');
  await expect(page).toHaveURL(/\/docs\/commands#investigation-commands$/);
  await expect(page.getByRole('dialog', { name: 'Search the field guide' })).not.toBeVisible();
  await page.getByRole('button', { name: 'Search the field guide', exact: true }).click();
  await search.fill('zzzzunfindableexample');
  await expect(page.getByRole('status')).toContainText('No results');
  await search.press('Escape');
  await expect(page.getByRole('button', { name: 'Search the field guide', exact: true })).toBeFocused();
});

test('setup preserves code, copies it, and restores direct heading links on refresh', async ({ page, context }, testInfo) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/docs/setup#install-backend-dependencies');
  await expect(page.locator('#install-backend-dependencies')).toBeInViewport();
  const block = page.locator('.docs-code-block').filter({ hasText: 'python -m pip install --upgrade pip' });
  await block.getByRole('button', { name: /Copy/ }).click();
  await expect(block).toContainText('Copied');
  expect((await page.evaluate(() => navigator.clipboard.readText())).replace(/\r\n/g, '\n')).toBe('python -m pip install --upgrade pip\npython -m pip install -r backend/requirements.txt');
  await page.reload();
  await expect(page.locator('#install-backend-dependencies')).toBeInViewport();
  await page.goto('/docs/introduction');
  await expect(page.locator('.docs-prose')).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: testInfo.outputPath('docs-desktop.png'), fullPage: true });
});

test('terminal draft and command output survive consulting the guide', async ({ page }) => {
  await page.route('**/cases/active', route => route.fulfill({ json: { status: 'success', case_name: null } }));
  await page.goto('/');
  await page.locator('.landing-actions').getByRole('button', { name: 'Open Terminal' }).click();
  await expect(page.locator('.pacman-splash')).toBeVisible();
  await page.keyboard.press('Escape');
  const input = page.getByRole('textbox', { name: 'BitKaun terminal command' });
  await expect(input).toBeAttached();
  await input.fill('sound off');
  await input.press('Enter');
  await input.fill('inspect my-unfinished-id');
  await expect(page.locator('.terminal-body')).toContainText('Audio synthesizer: MUTED');
  await page.getByRole('link', { name: '[field guide]', exact: true }).click();
  await page.getByRole('button', { name: 'Search the field guide', exact: true }).click();
  await page.getByRole('textbox', { name: 'Search documentation' }).fill('graph');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Open Terminal', exact: true }).click();
  await expect(input).toHaveValue('inspect my-unfinished-id');
  await expect(page.locator('.pacman-splash')).toHaveCount(0);
  await expect(page.locator('.terminal-body')).toContainText('Audio synthesizer: MUTED');
  await expect(page.locator('.terminal-body')).toContainText('sound off');
});

test('mobile navigation, search, and wide tables fit the viewport', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.getByRole('button', { name: /^reduced motion$/i })).toBeDisabled();
  expect(await page.locator('.landing-canvas').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('landing-mobile.png'), fullPage: true });
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await page.getByRole('button', { name: 'Open chapter navigation' }).click();
  const menu = page.getByRole('dialog', { name: 'Documentation navigation' });
  await menu.getByRole('link', { name: 'Web terminal commands' }).click();
  await expect(menu).not.toBeVisible();
  await expect(page).toHaveURL(/\/docs\/commands$/);
  expect(await page.locator('.docs-shell').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  const table = page.locator('.docs-table-scroll').first();
  expect(await table.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
  await page.getByRole('button', { name: 'Search the field guide', exact: true }).click();
  await page.getByRole('textbox', { name: 'Search documentation' }).fill('PowerShell');
  await expect(page.locator('.docs-search-result').first()).toBeVisible();
  await page.keyboard.press('Escape');
  await page.goto('/docs/introduction');
  await expect(page.locator('.docs-prose')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('docs-mobile.png'), fullPage: true });
});

test('Back and Forward recover an interrupted terminal entry', async ({ page }) => {
  await page.route('**/cases/active', route => route.fulfill({ json: { status: 'success' } }));
  await page.goto('/docs/introduction');
  await page.getByRole('button', { name: 'Open Terminal', exact: true }).click();
  await page.goBack();
  await expect(page.locator('.docs-prose')).toBeVisible();
  await page.goForward();
  await expect(page.locator('.pacman-splash')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('textbox', { name: 'BitKaun terminal command' })).toBeAttached();
});

test('missing chapters offer a working route home', async ({ page }) => {
  await page.goto('/docs/not-a-chapter');
  await expect(page.getByRole('heading', { name: 'A small detour.' })).toBeVisible();
  await page.getByRole('link', { name: 'Back to the introduction' }).click();
  await expect(page).toHaveURL(/\/docs\/introduction$/);
  await page.reload();
  await expect(page.locator('.docs-prose')).toBeVisible();
});

test('Docs opens as a book page with the guide underneath and a skippable turn', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await expect(page.locator('.book-turning')).toBeVisible();
  await expect(page.locator('.docs-prose')).toBeVisible();
  await expect(page.locator('.book-cover-front')).toHaveAttribute('inert', '');
  await page.screenshot({ path: testInfo.outputPath('book-page-turn.png') });
  await page.getByRole('button', { name: 'Skip page turn' }).click();
  await expect(page.locator('.book-stage')).toHaveCount(0);
  await expect(page.locator('.docs-article-header h1')).toBeFocused();
  await page.goto('/');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await expect(page).toHaveURL(/\/docs\/introduction$/);
  await expect(page.locator('.book-stage')).toHaveCount(0);
});
