import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/frontend',
  fullyParallel: true,
  workers: 2,
  timeout: 45000,
  use: {
    baseURL: 'http://127.0.0.1:4175',
    viewport: { width: 1440, height: 1000 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run preview -- --host 127.0.0.1 --port 4175 --strictPort',
    url: 'http://127.0.0.1:4175',
    reuseExistingServer: false,
  },
});
