import { test, expect, type Page } from '@playwright/test';

// Deliberately small test data: changes in backend values must reach the UI unchanged.
const meta = { sources: ['test/report.json'], scope: 'saved_test_benchmark', model_version: 'v8', dataset_version: 'test-dataset', synthetic: true, generated_at: '2026-09-27T00:00:00Z', notes: ['Test provenance note.'] };
const envelope = (data: unknown) => ({ schema_version: '1.0', status: 'available', meta, data, message: null });
const metrics = [
  { id: 'precision', label: 'PRECISION', value: .8123, unit: 'ratio' },
  { id: 'recall', label: 'RECALL', value: .9234, unit: 'ratio' },
  { id: 'f1', label: 'F1', value: .865, unit: 'ratio' },
  { id: 'roc_auc', label: 'ROC AUC', value: .9456, unit: 'ratio' },
];
const diagram = {
  id: 'test-pipeline', label: 'From source to evidence', kind: 'architecture', description: 'Illustrative test architecture.',
  nodes: [{ id: 'ledger', label: 'Blockchain transactions', description: 'Ledger inputs are joined by transaction ID.' }, { id: 'binary', label: 'Binary model', description: 'Risk ranks the scenario.' }, { id: 'alert', label: 'Alert dossier', description: 'Human investigation follows.' }],
  edges: [{ id: 'ledger-binary', source: 'ledger', target: 'binary', label: 'Scenario features' }, { id: 'binary-alert', source: 'binary', target: 'alert', label: 'Risk threshold' }],
};
const item = { id: 'normal', label: 'Normal', count: 17 };

async function mockObservatory(page: Page) {
  await page.route('**/api/observatory/**', async route => {
    const url = new URL(route.request().url());
    const endpoint = url.pathname.split('/').pop();
    let data: unknown;
    if (endpoint === 'overview') data = { title: 'BitKaun Observatory', evaluation_date: '2026-09-08T02:05:00Z', features: 46, headline_metrics: [...metrics].reverse() };
    if (endpoint === 'dataset') data = {
      totals: { transactions: 12345, scenarios: 77, unique_wallets: 4567, first_timestamp: '2024-01-01T00:00:00Z', last_timestamp: '2024-03-01T00:00:00Z' },
      bucket: url.searchParams.get('bucket'), timezone: 'UTC', splits: [{ id: 'train', label: 'Train', scenarios: 60, transactions: 10000 }, { id: 'test', label: 'Test', scenarios: 17, transactions: 2345 }],
      timeline: [{ timestamp: '2024-01-01T00:00:00Z', transactions: 123, output_volume_btc: 1.23456789 }, { timestamp: '2024-02-01T00:00:00Z', transactions: 0, output_volume_btc: 0 }, { timestamp: '2024-03-01T00:00:00Z', transactions: url.searchParams.get('bucket') === 'day' ? 789 : 456, output_volume_btc: 9.87654321 }],
      scenario_class_distribution: [item], scenario_binary_distribution: [{ id: 'licit', label: 'Licit', count: 60 }, { id: 'illicit', label: 'Illicit', count: 17 }],
      transaction_class_distribution: [item], infrastructure_distribution: [{ ...item, label: 'Residential' }], country_distribution: [{ ...item, label: 'IN' }], script_distribution: [{ ...item, label: 'P2PKH' }],
    };
    if (endpoint === 'performance') data = {
      evaluation_date: '2026-09-08T02:05:00Z', evaluation_type: 'Saved test evaluation', scoring_unit: 'scenario', threshold: .5,
      binary: { sample_count: 17, metrics, confusion_matrix: null, per_class: [] },
      typology: { sample_count: 8, metrics: [{ id: 'macro_f1', label: 'MACRO F1', value: .72, unit: 'ratio' }], confusion_matrix: null, per_class: [] },
      diagnostics: [{ id: 'calibration', label: 'Calibration', metrics: [{ id: 'ece', label: 'ECE', value: .015, unit: 'ratio' }], note: 'Lower is better.' }],
      limitations: ['Synthetic benchmark only.'], formal_decision: null, curves_available: false, curves_unavailable_reason: 'No saved curve coordinates.',
    };
    if (endpoint === 'features') data = {
      model: url.searchParams.get('model'), feature_count: 46, description: 'Normalized gain, not SHAP.', local_shap_unavailable_reason: 'No local SHAP example.',
      features: [{ id: 'test', label: url.searchParams.get('model') === 'typology' ? 'Typology signal' : 'Binary signal', group: 'financial', importance: .321 }],
      groups: [{ id: 'financial', label: 'Financial', group: 'financial', importance: .7 }],
    };
    if (endpoint === 'pipeline') data = diagram;
    if (endpoint === 'patterns') data = { patterns: ['Peeling chain', 'Layering', 'Mixing', 'Ransomware collection'].map((label, index) => ({ ...diagram, id: `pattern-${index}`, label, kind: 'illustration' })) };
    await route.fulfill({ json: envelope(data) });
  });
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1'));
  await mockObservatory(page);
});

test('live-shaped data drives the edition, selectors, and UTC timeline', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/analytics');
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeVisible();
  await expect(page.locator('.obs-metric').filter({ has: page.getByText('PRECISION', { exact: true }) })).toContainText('81.23%');
  await expect(page.locator('.obs-at-a-glance')).toContainText('12,345');
  await expect(page.locator('#performance')).toContainText('8 Sept 2026');
  await expect(page.locator('#performance')).toContainText('No saved curve coordinates.');
  await expect(page.locator('.obs-confusion')).toHaveCount(0);
  await page.getByLabel('Timeline period').selectOption('day');
  await expect(page.locator('.obs-chart-readout')).toContainText('789');
  await page.getByLabel('Timeline measure').selectOption('volume');
  await expect(page.locator('.obs-chart-readout')).toContainText('9.87654321');
  await page.getByLabel('Explore a time bucket').fill('0');
  await expect(page.locator('.obs-chart-readout')).toContainText('1 Jan 2024');
  await expect(page.locator('.obs-chart-readout')).toContainText('1.23456789');
  await page.getByLabel('Dataset breakdown').selectOption('script_distribution');
  await expect(page.getByRole('list', { name: 'Dataset secondary distribution' })).toContainText('P2PKH');
  await page.getByRole('button', { name: 'Typology attribution', exact: true }).click();
  await expect(page.getByRole('list', { name: 'Feature importance', exact: true })).toContainText('Typology signal');
  await page.getByLabel('Number of features').selectOption('46');
  await expect(page.getByRole('list', { name: 'Feature importance', exact: true })).toContainText('32.1%');
  await page.locator('.obs-shell').evaluate(element => { element.scrollTop = 0; });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: testInfo.outputPath('observatory-desktop.png') });
});

test('flowchart preserves directions and supports keyboard stage and edge selection', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/analytics');
  const pipeline = page.locator('#pipeline');
  await pipeline.getByRole('button', { name: 'Binary model', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(pipeline.locator('.obs-diagram-detail')).toContainText('Risk ranks the scenario.');
  await pipeline.getByRole('button', { name: 'Risk threshold: Binary model to Alert dossier' }).focus();
  await page.keyboard.press('Space');
  await expect(pipeline.locator('.obs-diagram-detail')).toContainText('Binary model → Alert dossier');
  await pipeline.getByRole('button', { name: 'Zoom in diagram' }).click();
  await expect(pipeline.getByRole('button', { name: 'Reset diagram zoom' })).toHaveText('125%');
  await pipeline.getByRole('button', { name: 'Reset diagram zoom' }).click();
  await expect(pipeline.getByRole('button', { name: 'Reset diagram zoom' })).toHaveText('100%');
});

test('an unavailable section retries independently while network errors stay readable', async ({ page }) => {
  let requests = 0;
  await page.route('**/api/observatory/dataset?*', async route => {
    requests++;
    if (requests === 1) await route.fulfill({ json: { ...envelope(null), status: 'unavailable', message: 'Dataset artifact temporarily missing.' } });
    else await route.fallback();
  });
  await page.route('**/api/observatory/features?*', route => route.fulfill({ status: 503, body: 'Offline' }));
  await page.goto('/analytics');
  await expect(page.locator('#dataset')).toContainText('Dataset artifact temporarily missing.');
  await expect(page.locator('.obs-metrics')).toContainText('81.23%');
  await expect(page.locator('#features')).toContainText('HTTP 503');
  await page.locator('#dataset').getByRole('button', { name: 'Retry this section' }).click();
  await expect(page.locator('.obs-at-a-glance')).toContainText('12,345');
});

test('newspaper opening is 3D, skippable and transfers focus to the edition', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.clock.install();
  await page.goto('/');
  await page.clock.pauseAt(new Date(Date.now() + 1000));
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page).toHaveURL(/\/analytics$/);
  await expect(page.locator('.newspaper-canvas canvas')).toBeVisible();
  await expect(page.locator('.obs-shell')).toHaveAttribute('inert', '');
  await page.getByRole('button', { name: 'Skip opening' }).click();
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeFocused();
  await expect(page.locator('.obs-shell')).not.toHaveAttribute('inert', '');
  expect(errors).toEqual([]);
});

test('opening completes naturally and interrupted navigation leaves no overlay', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page.locator('.newspaper-entrance')).toBeVisible();
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0, { timeout: 6000 });
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeFocused();
  await page.goBack();
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page.locator('.newspaper-entrance')).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL('/');
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0);
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeVisible();
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0);
});

test('mobile edition fits, reduced motion skips the entrance, and direct refresh works', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page).toHaveURL('/analytics');
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0);
  await expect(page.locator('.obs-at-a-glance')).toContainText('12,345');
  expect(await page.locator('.obs-shell').evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('observatory-mobile.png') });
  await page.getByRole('navigation', { name: 'Edition sections' }).getByRole('link', { name: /How it works/ }).click();
  await expect(page.locator('#pipeline h2')).toBeInViewport();
  const viewport = page.locator('#pipeline .obs-diagram-viewport');
  expect(await viewport.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
  await page.reload();
  await expect(page.locator('.obs-at-a-glance')).toContainText('12,345');
  await page.getByRole('navigation', { name: 'Observatory navigation' }).getByRole('link', { name: 'Home', exact: true }).click();
  await expect(page).toHaveURL('/');
});

test('unavailable WebGL falls back to the readable edition', async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (...args: Parameters<typeof original>) {
      if (String(args[0]).includes('webgl')) return null;
      return original.apply(this, args);
    } as typeof original;
  });
  await page.goto('/');
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page.getByRole('heading', { name: 'The Observatory', exact: true })).toBeVisible();
  await expect(page.locator('.newspaper-entrance')).toHaveCount(0);
  await expect(page.locator('.obs-shell')).not.toHaveAttribute('inert', '');
});

test('data reveals wait for the newspaper and settle to exact values', async ({ page }) => {
  await page.clock.install();
  await page.goto('/');
  await page.clock.pauseAt(new Date(Date.now() + 1000));
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page.locator('.newspaper-entrance')).toBeVisible();
  await expect(page.locator('.obs-metrics .scramble-number').first()).toHaveAttribute('data-reveal', 'waiting');
  await page.getByRole('button', { name: 'Skip opening' }).click();
  await expect(page.locator('.obs-metrics .scramble-number').first()).toHaveAttribute('data-reveal', 'playing');
  await page.clock.runFor(750);
  await expect(page.locator('.obs-metrics .scramble-number').first()).toHaveAttribute('data-reveal', 'done');
  await expect(page.locator('.obs-metrics .scramble-number').first().locator('[aria-hidden=true]')).toHaveText('0.9456');
  await page.locator('#features').scrollIntoViewIfNeeded();
  await page.clock.runFor(100);
  await expect(page.locator('#features .obs-bars').first()).toHaveAttribute('data-reveal', 'playing');
  await page.clock.runFor(1500);
  await expect(page.locator('#features .obs-bars').first()).toHaveAttribute('data-reveal', 'done');
  await page.locator('#pipeline').scrollIntoViewIfNeeded();
  await expect(page.locator('#pipeline .obs-diagram')).toHaveAttribute('data-reveal', 'playing');
  await page.clock.runFor(1800);
  await expect(page.locator('#pipeline .obs-diagram')).toHaveAttribute('data-reveal', 'done');
});
