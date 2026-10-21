import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './app/tests/e2e',
  fullyParallel: false,
  use: { trace: 'retain-on-failure' },
  projects: [
    {
      name: 'production-chromium',
      use: { ...devices['Desktop Chrome'], baseURL: 'http://127.0.0.1:4173' },
    },
    {
      name: 'development-chromium',
      use: { ...devices['Desktop Chrome'], baseURL: 'http://127.0.0.1:5173' },
    },
  ],
  webServer: [
    {
      command: 'npm run preview -- --port 4173 --strictPort',
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: false,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
    },
  ],
});
