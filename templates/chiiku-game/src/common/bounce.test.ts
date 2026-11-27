import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BOUNCE_MS, WIGGLE_MS, createBouncer } from './bounce';

describe('createBouncer', () => {
  let el: HTMLElement;
  let bouncer: ReturnType<typeof createBouncer>;

  beforeEach(() => {
    vi.useFakeTimers();
    el = document.createElement('div');
    bouncer = createBouncer();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('adds the bounce class and removes it after BOUNCE_MS', () => {
    expect(BOUNCE_MS).toBe(400);
    bouncer.bounce(el);
    expect(el.classList.contains('bounce')).toBe(true);
    vi.advanceTimersByTime(BOUNCE_MS - 1);
    expect(el.classList.contains('bounce')).toBe(true);
    vi.advanceTimersByTime(1);
    expect(el.classList.contains('bounce')).toBe(false);
  });

  it('restarts from the beginning when called again midway', () => {
    bouncer.bounce(el);
    vi.advanceTimersByTime(300);
    bouncer.bounce(el);
    vi.advanceTimersByTime(BOUNCE_MS - 1);
    expect(el.classList.contains('bounce')).toBe(true);
    vi.advanceTimersByTime(1);
    expect(el.classList.contains('bounce')).toBe(false);
  });

  it('keeps separate elements independent', () => {
    const other = document.createElement('div');
    bouncer.bounce(el);
    vi.advanceTimersByTime(200);
    bouncer.bounce(other);
    vi.advanceTimersByTime(200);
    expect(el.classList.contains('bounce')).toBe(false);
    expect(other.classList.contains('bounce')).toBe(true);
  });

  it('uses the given class and duration (the wiggle)', () => {
    expect(WIGGLE_MS).toBe(400);
    const wiggler = createBouncer('wiggle', 100);
    wiggler.bounce(el);
    expect(el.classList.contains('wiggle')).toBe(true);
    expect(el.classList.contains('bounce')).toBe(false);
    vi.advanceTimersByTime(99);
    expect(el.classList.contains('wiggle')).toBe(true);
    vi.advanceTimersByTime(1);
    expect(el.classList.contains('wiggle')).toBe(false);
    wiggler.bounce(el);
    wiggler.clear();
    expect(el.classList.contains('wiggle')).toBe(false);
  });

  it('clear removes the class at once and stops the timers', () => {
    bouncer.bounce(el);
    bouncer.clear();
    expect(el.classList.contains('bounce')).toBe(false);
    // 後から別の用で付けた class を、止めたはずのタイマーが外さない
    el.classList.add('bounce');
    vi.advanceTimersByTime(BOUNCE_MS * 2);
    expect(el.classList.contains('bounce')).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });
});
