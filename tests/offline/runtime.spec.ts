import { test, expect } from '@playwright/test';

test('built UI, actual Observatory and documentation work with only the local origin permitted', async ({ page, context, baseURL }) => {
  const externalRequests: string[] = [];
  const assetFailures: string[] = [];
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (['http:', 'https:'].includes(url.protocol) && url.origin !== baseURL) {
      externalRequests.push(url.href);
      await route.abort('blockedbyclient');
    } else await route.continue();
  });
  page.on('response', response => {
    if (response.status() >= 400 && ['script', 'stylesheet', 'font', 'image'].includes(response.request().resourceType())) {
      assetFailures.push(`${response.status()} ${response.url()}`);
    }
  });
  await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1'));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Follow the flow.');
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator('.landing-hero h1')).toHaveCSS('font-family', /Newsreader/);

  await page.goto('/docs/faq');
  await expect(page.getByRole('link', { name: 'Offline Linux delivery' })).toHaveAttribute('href', '/source/docs/OFFLINE_LINUX.md');
  const source = await context.request.get('/source/docs/OFFLINE_LINUX.md');
  expect(source.ok()).toBeTruthy();
  expect(await source.text()).toContain('Linux offline delivery');

  await page.goto('/docs');
  await expect(page.getByRole('heading', { name: 'BitKaun API Reference' })).toBeVisible();
  await expect(page.getByRole('status')).toContainText('endpoints in local schema');
  await page.getByLabel('Filter endpoints').fill('/api/observatory/');
  await expect(page.getByRole('status')).toContainText('6 endpoints');

  await page.goto('/analytics');
  const totals = (await (await context.request.get('/api/observatory/dataset')).json()).data.totals;
  const metrics = (await (await context.request.get('/api/observatory/overview')).json()).data.headline_metrics;
  const precision = metrics.find((metric: { id: string }) => metric.id === 'precision').value;
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeVisible();
  await expect(page.locator('.obs-at-a-glance')).toContainText(totals.transactions.toLocaleString('en-US'), { timeout: 45000 });
  await expect(page.locator('.obs-metric').filter({ has: page.getByText('PRECISION', { exact: true }) })).toContainText(`${(precision * 100).toFixed(2)}%`);
  await expect(page.getByRole('list', { name: 'Feature importance', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Typology attribution', exact: true }).click();
  await expect(page.getByRole('list', { name: 'Feature importance', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeVisible();

  expect(assetFailures).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test('real dual-stream upload shows evidence and unknown confidence without internet', async ({ page, context, baseURL }, testInfo) => {
  const external: string[] = [];
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (['http:', 'https:'].includes(url.protocol) && url.origin !== baseURL) {
      external.push(url.href);
      await route.abort('blockedbyclient');
    } else await route.continue();
  });
  await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1'));
  await page.goto('/terminal');
  await expect(page.locator('.pacman-splash')).toBeVisible();
  await page.keyboard.press('Escape');
  const terminal = page.getByRole('textbox', { name: 'BitKaun terminal command' });
  await terminal.fill('upload');
  await terminal.press('Enter');
  const evidence = page.getByRole('region', { name: 'Evidence & Correlation Analysis' });
  await expect(evidence.getByRole('heading', { name: 'Evidence & Correlation Analysis' })).toBeVisible();
  await expect(evidence.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
  await expect(evidence.getByText('Match Method', { exact: true })).toBeVisible();
  await expect(evidence.getByText('Timing Status', { exact: true })).toBeVisible();
  await expect(evidence.getByText('Observations', { exact: true })).toBeVisible();
  await expect(evidence.getByText('Reasons', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /Load Sample Dual-Stream Pair/ }).click();
  await expect(page.getByText('sample_blockchain_ledger.csv', { exact: true })).toBeVisible();
  const response = page.waitForResponse(r => r.url().endsWith('/api/ingest/correlate') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /MERGE DUAL STREAMS & RUN V8 ML INFERENCE/ }).click();
  expect((await response).ok()).toBeTruthy();
  await expect(page.getByText('EXACT-ID MATCH COVERAGE', { exact: true })).toBeVisible();
  await expect(evidence).toBeVisible();
  await expect(evidence.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
  await expect(evidence.locator('details').first()).toHaveAttribute('open', '');
  await expect(evidence.locator('details').first().getByText('EXACT TRANSACTION ID', { exact: true })).toBeVisible();
  await expect(evidence.locator('details').first().getByRole('heading', { name: 'Observations' })).toBeVisible();
  await expect(evidence.locator('details').first().getByRole('heading', { name: 'Reasons' })).toBeVisible();
  await expect(evidence.locator('details').first().getByText(/Exact original transaction ID appears/)).toBeVisible();
  await expect(evidence.locator('details').first().getByText(/RELAY OBSERVED ORIGIN UNVERIFIED/)).toBeVisible();
  await evidence.screenshot({ path: testInfo.outputPath('upload-evidence-visible.png') });
  expect(external).toEqual([]);
});
