import { test, expect, type Page } from '@playwright/test';

// Isolated UI state fixtures. The real endpoint is checked in tests/offline/runtime.spec.ts.
const complete = {
  status: 'SUCCESS', ledger_records: 1, network_records: 1, matched_records: 1,
  newly_indexed_records: 1, unmatched_ledger: 0, unmatched_network: 0, correlation_rate: 1,
  timing_issue_count: 0, conflicting_records: 0, scenario_results: [],
};

async function openUpload(page: Page) {
  await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1'));
  await page.route('**/cases/active', route => route.fulfill({ json: { status: 'success', case_name: null } }));
  await page.goto('/terminal');
  await expect(page.locator('.pacman-splash')).toBeVisible();
  await page.keyboard.press('Escape');
  const terminal = page.getByRole('textbox', { name: 'BitKaun terminal command' });
  await terminal.fill('upload');
  await terminal.press('Enter');
}

async function selectFiles(page: Page) {
  await page.locator('input[type="file"]').nth(0).setInputFiles({ name: 'ledger.csv', mimeType: 'text/csv', buffer: Buffer.from('txid,timestamp\n1,2026-09-06 10:00:00') });
  await page.locator('input[type="file"]').nth(1).setInputFiles({ name: 'network.csv', mimeType: 'text/csv', buffer: Buffer.from('txid,relay_timestamp\n1,2026-09-06 09:59:59') });
}

test('initial upload and failed request both show evidence fields and Not estimated', async ({ page }) => {
  await openUpload(page);
  const panel = page.getByRole('region', { name: 'Evidence & Correlation Analysis' });
  await expect(panel.getByRole('heading', { name: 'Evidence & Correlation Analysis' })).toBeVisible();
  for (const field of ['Match Method', 'Timing Status', 'Observations', 'Reasons']) {
    await expect(panel.getByText(field, { exact: true })).toBeVisible();
  }
  await expect(panel.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
  await expect(panel.getByRole('status')).toContainText('Upload both files');
  await selectFiles(page);
  await page.route('**/api/ingest/correlate', route => route.fulfill({ status: 503, json: { detail: 'Backend unavailable for test' } }));
  await page.getByRole('button', { name: /MERGE DUAL STREAMS & RUN V8 ML INFERENCE/ }).click();
  await expect(panel.getByRole('status')).toContainText('Correlation could not complete');
  await expect(panel.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
});

for (const variant of ['omitted', 'empty', 'null'] as const) {
  test(`completed upload with ${variant} evidence keeps the section visible`, async ({ page }) => {
    await openUpload(page);
    await selectFiles(page);
    const response = variant === 'omitted' ? complete : { ...complete, correlation_evidence: variant === 'empty' ? [] : null };
    await page.route('**/api/ingest/correlate', route => route.fulfill({ json: response }));
    await page.getByRole('button', { name: /MERGE DUAL STREAMS & RUN V8 ML INFERENCE/ }).click();
    const panel = page.getByRole('region', { name: 'Evidence & Correlation Analysis' });
    await expect(page.getByText('EXACT-ID MATCH COVERAGE', { exact: true })).toBeVisible();
    await expect(panel.getByRole('heading', { name: 'Evidence & Correlation Analysis' })).toBeVisible();
    await expect(panel.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
    await expect(panel.getByRole('status')).toContainText(variant === 'empty' ? 'No correlation evidence was returned' : 'does not include correlation evidence');
    await expect(panel.locator('details')).toHaveCount(0);
  });
}

test('pending request shows loading state; first response record opens with actual evidence', async ({ page }) => {
  await openUpload(page);
  await selectFiles(page);
  let release!: () => void;
  const wait = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/ingest/correlate', async route => {
    await wait;
    await route.fulfill({ json: { ...complete, correlation_evidence: [{
      transaction_hash: 'actual-test-id', match_method: 'EXACT_TRANSACTION_ID', match_status: 'MATCHED',
      ledger_timestamp: '2026-09-06T10:00:00Z', timing_delta_seconds: -2, timing_status: 'CLOCK_ORDER_ISSUE',
      correlation_confidence: null, attribution_status: 'RELAY_OBSERVED_ORIGIN_UNVERIFIED',
      observations: [{ relay_timestamp: '2026-09-06T10:00:02Z', relay_ip: '192.0.2.10', asn: 'AS64500', node_type: 'residential' }],
      reasons: ['Clock ordering requires investigation.'],
    }] } });
  });
  await page.getByRole('button', { name: /MERGE DUAL STREAMS & RUN V8 ML INFERENCE/ }).click();
  const panel = page.getByRole('region', { name: 'Evidence & Correlation Analysis' });
  try {
    await expect(panel).toHaveAttribute('aria-busy', 'true');
    await expect(panel.getByRole('status')).toContainText('Correlating the uploaded streams');
    await expect(panel.locator('.correlation-confidence')).toHaveText('Correlation confidence: Not estimated');
  } finally { release(); }
  const first = panel.locator('details').first();
  await expect(first).toHaveAttribute('open', '');
  await expect(first.getByText('EXACT TRANSACTION ID', { exact: true })).toBeVisible();
  await expect(first.getByText('CLOCK ORDER ISSUE', { exact: true })).toBeVisible();
  await expect(first.getByText('-2s (signed)', { exact: true })).toBeVisible();
  await expect(first.getByText(/192\.0\.2\.10/)).toBeVisible();
  await expect(first.getByText('Clock ordering requires investigation.', { exact: true })).toBeVisible();
  await first.locator('summary').click();
  await expect(first).not.toHaveAttribute('open', '');
  await expect(panel.locator('.correlation-confidence')).toBeVisible();
  await expect(panel.locator('.correlation-confidence')).not.toContainText('%');
});
