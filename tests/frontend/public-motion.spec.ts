import { test, expect } from '@playwright/test';

test('entry, pouring, coin flight and settlement share the actual landing artwork', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.clock.install();
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Enter BitKaun' })).toBeFocused();
  await page.evaluate(() => document.fonts.ready);
  await page.clock.pauseAt(new Date(Date.now() + 1000));
  await page.screenshot({ path: testInfo.outputPath('entry-wordmark.png') });
  await page.getByRole('button', { name: 'Enter BitKaun' }).click();
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-running/);
  await page.getByRole('button', { name: 'Mute sound and music' }).click();
  await page.clock.runFor(1500);
  await expect(page.locator('.landing-canvas')).toHaveAttribute('data-landing-phase', 'pour');
  await expect(page.locator('.landing-intro-bottle')).toBeVisible();
  expect(await page.locator('.landing-art-liquid').evaluateAll(elements => elements.some(element => !!element.textContent?.trim()))).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('pour-and-flip.png') });
  await page.clock.runFor(700);
  await page.screenshot({ path: testInfo.outputPath('coin-apex.png') });
  await page.clock.runFor(2400);
  await expect(page.locator('.landing-canvas')).toHaveAttribute('data-landing-phase', 'leaves');
  await page.screenshot({ path: testInfo.outputPath('botanical-reveal.png') });
  await page.clock.runFor(1400);
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-ready/);
  await expect(page.locator('.landing-intro-bottle')).toHaveCount(0);
  await expect(page.locator('.landing-art-wine')).not.toHaveAttribute('style', /transform/);
  await expect(page.locator('.landing-art-bitcoin')).not.toHaveAttribute('style', /transform/);
  await expect(page.getByRole('heading', { name: /Follow the flow/ })).toBeFocused();
  await expect(page.getByRole('button', { name: 'Rotate or flick the Bitcoin' })).toBeEnabled();
  await page.screenshot({ path: testInfo.outputPath('landing-settled.png') });
  expect(errors).toEqual([]);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Enter BitKaun' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Replay opening' }).click();
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-running/);
  await page.keyboard.press('Escape');
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-ready/);
});

test('the supplied music resumes after paper transitions and pauses in the terminal', async ({ page }) => {
  await page.addInitScript(() => {
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { (window as any).__backgroundMusic = this; return play.call(this); };
  });
  await page.route('**/cases/active', route => route.fulfill({ json: { status: 'success', case_name: null } }));
  await page.route('**/api/observatory/**', route => route.fulfill({ json: {
    schema_version: '1.0', status: 'unavailable', data: null, message: 'No benchmark needed for this audio-navigation test.',
    meta: { sources: [], scope: 'test', model_version: null, dataset_version: null, synthetic: true, generated_at: '2026-09-27T00:00:00Z', notes: [] },
  } }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Enter BitKaun' }).click();
  await page.getByRole('button', { name: 'Skip opening' }).click();
  await expect(page.locator('.public-audio')).toHaveAttribute('data-active-sequences', '0');
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'playing', { timeout: 20000 });
  await expect.poll(() => page.evaluate(() => (window as any).__backgroundMusic?.currentTime || 0)).toBeGreaterThan(0);
  const time = await page.evaluate(() => (window as any).__backgroundMusic.currentTime);
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await expect(page.locator('.book-turning')).toBeVisible();
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'paused');
  await page.keyboard.press('Escape');
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'playing');
  expect(await page.evaluate(() => (window as any).__backgroundMusic.currentTime)).toBeGreaterThanOrEqual(time);
  await page.getByRole('button', { name: 'Mute sound and music' }).click();
  await expect.poll(() => page.evaluate(() => (window as any).__backgroundMusic.paused)).toBe(true);
  await page.getByRole('button', { name: 'Unmute sound and music' }).click();
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'playing');
  await page.getByRole('link', { name: 'BitKaun home', exact: true }).click();
  await page.getByRole('link', { name: /03.*observatory.*Analytics/i }).click();
  await expect(page.locator('.newspaper-entrance')).toBeVisible();
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'paused');
  await page.keyboard.press('Escape');
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'playing');
  expect(await page.evaluate(() => (window as any).__backgroundMusic.currentTime)).toBeGreaterThanOrEqual(time);
  await page.getByRole('navigation', { name: 'Observatory navigation' }).getByRole('button', { name: 'Terminal', exact: true }).click();
  await expect(page).toHaveURL('/terminal');
  await expect(page.locator('.public-audio')).toHaveCount(0);
  expect(await page.evaluate(() => (window as any).__backgroundMusic.paused)).toBe(true);
  await page.keyboard.press('Escape');
  await page.getByRole('link', { name: '[home]', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Enter BitKaun' })).toHaveCount(0);
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'playing');
});

test('mobile pour stays in the viewport and interrupted intros clean up', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.clock.install();
  await page.goto('/');
  await page.clock.pauseAt(new Date(Date.now() + 1000));
  await page.getByRole('button', { name: 'Enter BitKaun' }).click();
  await page.getByRole('button', { name: 'Mute sound and music' }).click();
  await page.clock.runFor(2000);
  const wine = await page.locator('.landing-art-wine').boundingBox();
  const coin = await page.locator('.landing-art-bitcoin').boundingBox();
  expect(wine!.x).toBeGreaterThanOrEqual(0);
  expect(wine!.x + wine!.width).toBeLessThanOrEqual(390);
  expect(coin!.y).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: testInfo.outputPath('mobile-pour.png') });
  await page.setViewportSize({ width: 844, height: 390 });
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-ready/);
  await expect(page.locator('.landing-pour-stream')).toHaveCount(0);
  await expect(page.locator('.public-audio')).toHaveAttribute('data-active-sequences', '0');
});

test('reduced motion skips choreography and the intro can be skipped without enabling audio', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.keyboard.press('Escape');
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-ready/);
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'locked');
  await page.getByRole('button', { name: 'Replay opening' }).click();
  await expect(page.locator('.landing-canvas')).toHaveClass(/intro-ready/);
  await expect(page.locator('.landing-intro-bottle')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'REDUCED MOTION', exact: true })).toBeDisabled();
});

test('a missing music file leaves navigation and sound controls usable', async ({ page }) => {
  await page.route('**/audio/lounge.mp3', route => route.fulfill({ status: 404, body: 'Missing track' }));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Enter BitKaun' }).click();
  await expect(page.locator('.public-audio')).toHaveAttribute('data-music-state', 'unavailable');
  await page.getByRole('button', { name: 'Mute sound and music' }).click();
  await expect(page.getByRole('button', { name: 'Unmute sound and music' })).toBeVisible();
  await page.getByRole('link', { name: 'Read the field guide' }).click();
  await expect(page.locator('.docs-prose')).toBeVisible();
});
