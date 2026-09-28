import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/offline',
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: 'http://127.0.0.1:4176',
    viewport: { width: 1440, height: 1000 },
    serviceWorkers: 'block',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'python -B -m uvicorn backend.app.main:app --host 127.0.0.1 --port 4176',
    url: 'http://127.0.0.1:4176/',
    reuseExistingServer: false,
    timeout: 150000,
  },
});
