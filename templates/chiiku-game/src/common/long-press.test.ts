import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { attachLongPress } from './long-press';

function fire(el: Element, type: string) {
  el.dispatchEvent(new Event(type, { bubbles: true }));
}

describe('attachLongPress', () => {
  let el: HTMLElement;
  let onFire: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    el = document.createElement('button');
    onFire = vi.fn();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('fires after 1500ms', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1499);
    expect(onFire).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('short tap does not exit', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(800);
    fire(el, 'pointerup');
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('pointerleave cancels', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    fire(el, 'pointerleave');
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('pointercancel cancels', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    fire(el, 'pointercancel');
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('fires only once for one press', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(10000);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('a second press after a cancelled one counts from zero', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    fire(el, 'pointerup');
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    expect(onFire).not.toHaveBeenCalled();
    vi.advanceTimersByTime(500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('a second finger pressing again does not restart or double the count', () => {
    attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('the returned function detaches it', () => {
    const detach = attachLongPress(el, 1500, onFire);
    detach();
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('detaching during a press cancels it', () => {
    const detach = attachLongPress(el, 1500, onFire);
    fire(el, 'pointerdown');
    vi.advanceTimersByTime(1000);
    detach();
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });
});

function firePointer(el: Element, type: string, init: Record<string, unknown>) {
  el.dispatchEvent(Object.assign(new Event(type, { bubbles: true }), init));
}

describe('attachLongPress with several fingers and moves', () => {
  let el: HTMLElement;
  let onFire: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    el = document.createElement('button');
    el.getBoundingClientRect = () =>
      ({ left: 0, top: 0, right: 100, bottom: 100, width: 100, height: 100 }) as DOMRect;
    onFire = vi.fn();
    attachLongPress(el, 1500, onFire);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('a second finger lifting does not cancel the first finger that is holding', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    vi.advanceTimersByTime(1000);
    firePointer(el, 'pointerdown', { pointerId: 2 });
    vi.advanceTimersByTime(100);
    firePointer(el, 'pointerup', { pointerId: 2 });
    vi.advanceTimersByTime(400);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('the finger that started the press cancels it when it lifts', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    firePointer(el, 'pointerdown', { pointerId: 2 });
    vi.advanceTimersByTime(1000);
    firePointer(el, 'pointerup', { pointerId: 1 });
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('a second finger leaving or being cancelled does not cancel the first', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    firePointer(el, 'pointerdown', { pointerId: 2 });
    firePointer(el, 'pointerleave', { pointerId: 2 });
    firePointer(el, 'pointercancel', { pointerId: 2 });
    vi.advanceTimersByTime(1500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('moving outside the button cancels it (touch keeps the pointer captured, so no pointerleave)', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    vi.advanceTimersByTime(1000);
    firePointer(el, 'pointermove', { pointerId: 1, clientX: 140, clientY: 50 });
    vi.advanceTimersByTime(5000);
    expect(onFire).not.toHaveBeenCalled();
  });

  it('a small move inside the button keeps the press', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    vi.advanceTimersByTime(1000);
    firePointer(el, 'pointermove', { pointerId: 1, clientX: 60, clientY: 40 });
    vi.advanceTimersByTime(500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('another finger moving outside does not cancel the first', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    firePointer(el, 'pointermove', { pointerId: 2, clientX: 500, clientY: 500 });
    vi.advanceTimersByTime(1500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });

  it('a move event without coordinates does not cancel', () => {
    firePointer(el, 'pointerdown', { pointerId: 1 });
    firePointer(el, 'pointermove', { pointerId: 1 });
    vi.advanceTimersByTime(1500);
    expect(onFire).toHaveBeenCalledTimes(1);
  });
});
