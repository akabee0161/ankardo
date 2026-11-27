import { describe, expect, it } from 'vitest';
import { ROUND_SIZE, createProgressDots } from './progress';

const on = (el: HTMLElement) => el.querySelectorAll('.dot.on').length;

describe('createProgressDots', () => {
  it('has a round of 5', () => {
    expect(ROUND_SIZE).toBe(5);
  });

  it('shows total dots, none lit at first', () => {
    const { el } = createProgressDots(5);
    expect(el.classList.contains('progress')).toBe(true);
    expect(el.querySelectorAll('.dot')).toHaveLength(5);
    expect(on(el)).toBe(0);
  });

  it('lights the first n dots', () => {
    const dots = createProgressDots(5);
    dots.set(2);
    expect(on(dots.el)).toBe(2);
    expect(dots.el.querySelectorAll('.dot')[1]?.classList.contains('on')).toBe(true);
    expect(dots.el.querySelectorAll('.dot')[2]?.classList.contains('on')).toBe(false);
    dots.set(0);
    expect(on(dots.el)).toBe(0);
  });

  it('clamps the number to 0..total', () => {
    const dots = createProgressDots(5);
    dots.set(9);
    expect(on(dots.el)).toBe(5);
    dots.set(-1);
    expect(on(dots.el)).toBe(0);
  });

  it('tells a screen reader how far the round is', () => {
    const dots = createProgressDots(5);
    dots.set(2);
    expect(dots.el.getAttribute('role')).toBe('img');
    expect(dots.el.getAttribute('aria-label')).toBe('5 もん中 2 もん');
  });
});
