import { describe, expect, it } from 'vitest';
import { FPS, FRAME_COUNT, FRAME_LABELS } from './timeline';

describe('timeline shell', () => {
  it('shows 24 output frames at the planned 12 FPS', () => {
    expect(FRAME_COUNT / FPS).toBe(2);
    expect(FRAME_LABELS).toHaveLength(24);
    expect(FRAME_LABELS[0]).toBe(0);
    expect(FRAME_LABELS.at(-1)).toBe(23);
  });
});
