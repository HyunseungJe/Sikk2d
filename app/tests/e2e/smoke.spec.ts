import { test, expect } from '@playwright/test';

test('built shell starts PixiJS and survives resizing without browser errors', async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sikk2d' })).toBeVisible();
  const stage = page.getByTestId('pixi-stage');
  await expect(stage).toHaveAttribute('data-status', 'ready');
  await expect(stage.locator('canvas')).toHaveCount(1);
  await expect(stage.locator('canvas')).toBeVisible();
  expect(
    await stage
      .locator('canvas')
      .evaluate(
        (canvas: HTMLCanvasElement) => canvas.width > 0 && canvas.height > 0,
      ),
  ).toBe(true);
  await expect(page.getByRole('region', { name: '타임라인' })).toBeVisible();
  await expect(page.getByLabel('프레임 눈금').locator('span')).toHaveCount(24);
  await page.screenshot({ path: testInfo.outputPath('shell.png') });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(stage.locator('canvas')).toBeVisible();
  await page.reload();
  await expect(stage).toHaveAttribute('data-status', 'ready');
  expect(errors).toEqual([]);
});
