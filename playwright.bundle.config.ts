import { defineConfig } from '@playwright/test';
import { resolve } from 'node:path';

// Verify the actual transferred bundle's built UI and backend, not the source dist/.
export default defineConfig({
  testDir: './tests/offline',
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: 'http://127.0.0.1:4177',
    viewport: { width: 1440, height: 1000 },
    serviceWorkers: 'block',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'python -B -m uvicorn backend.app.main:app --host 127.0.0.1 --port 4177',
    cwd: resolve('offline_bundle/BitKaun-linux-x86_64'),
    url: 'http://127.0.0.1:4177/',
    reuseExistingServer: false,
    timeout: 150000,
  },
});
