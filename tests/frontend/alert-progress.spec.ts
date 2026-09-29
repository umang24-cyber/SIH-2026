import { test, expect } from '@playwright/test';

test('alerts shows actual scan progress while waiting, then stops polling on completion', async ({ page }) => {
  await page.route('**/cases/active', route => route.fulfill({ json: { status: 'success', case_name: null } }));
  await page.addInitScript(() => sessionStorage.setItem('bitkaun-opening-seen', '1'));
  let finish!: () => void;
  const waiting = new Promise<void>(resolve => { finish = resolve; });
  await page.route('**/alerts?*', async route => {
    await waiting;
    await route.fulfill({ json: { total_alerts: 0, alerts: [] } });
  });
  let polls = 0;
  await page.route('**/alerts/scan-status', route => {
    polls++;
    return route.fulfill({ json: { state: 'running', phase: 'features', processed: 120, total: 1000, elapsed_seconds: 4.5 } });
  });
  await page.goto('/terminal');
  await expect(page.locator('.pacman-splash')).toBeVisible();
  await page.keyboard.press('Escape');
  const command = page.getByRole('textbox', { name: 'BitKaun terminal command' });
  await command.fill('alerts --limit 10');
  await command.press('Enter');
  try {
    await expect(page.getByRole('status').filter({ hasText: 'Alert scan:' })).toContainText('120 / 1,000 scenarios');
    await expect(page.getByRole('status').filter({ hasText: 'Alert scan:' })).toContainText('4.5s elapsed');
    expect(polls).toBeGreaterThan(0);
  } finally { finish(); }
  await expect(page.getByRole('status').filter({ hasText: 'Alert scan:' })).toHaveCount(0);
});
