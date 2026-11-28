import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CLICK_FOLLOW_MS, attachActivate } from './activate';

function pointer(el: Element, type: string, button = 0) {
  const e = new Event(type, { bubbles: true }) as Event & { button: number };
  e.button = button;
  el.dispatchEvent(e);
}
function key(el: Element, type: string, k: string, repeat = false) {
  const e = new KeyboardEvent(type, { key: k, repeat, bubbles: true, cancelable: true });
  el.dispatchEvent(e);
  return e;
}

describe('attachActivate', () => {
  let el: HTMLButtonElement;
  let fn: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    document.body.replaceChildren();
    el = document.createElement('button');
    // 実際の画面と同じく、要素は document の中に置く（pointerup が document まで届く）
    document.body.append(el);
    fn = vi.fn();
    attachActivate(el, fn);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('fires on pointerdown, and not again on the click that follows', () => {
    pointer(el, 'pointerdown');
    expect(fn).toHaveBeenCalledTimes(1);
    pointer(el, 'pointerup');
    el.click();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('ignores right and middle buttons', () => {
    pointer(el, 'pointerdown', 2);
    pointer(el, 'pointerdown', 1);
    expect(fn).not.toHaveBeenCalled();
  });

  it('fires on Enter and Space, not on key repeat, and not again on the click that follows', () => {
    const e = key(el, 'keydown', 'Enter');
    expect(e.defaultPrevented).toBe(true);
    key(el, 'keydown', 'Enter', true);
    expect(fn).toHaveBeenCalledTimes(1);
    key(el, 'keyup', 'Enter');
    el.click();
    expect(fn).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(CLICK_FOLLOW_MS);
    key(el, 'keydown', ' ');
    el.click();
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('ignores other keys', () => {
    key(el, 'keydown', 'a');
    expect(fn).not.toHaveBeenCalled();
  });

  it('fires on a click that came alone (assistive technology)', () => {
    el.click();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('still fires on a lone click after a mouse press released outside the element', () => {
    pointer(el, 'pointerdown');
    pointer(document.body, 'pointerup'); // 要素の外で離した（el の pointerup は来ない）
    vi.advanceTimersByTime(CLICK_FOLLOW_MS);
    el.click();
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('still fires on a lone click after a touch that slid away (no click followed)', () => {
    pointer(el, 'pointerdown');
    pointer(el, 'pointerup'); // 指がすべって、click は来なかった
    vi.advanceTimersByTime(CLICK_FOLLOW_MS);
    el.click();
    expect(fn).toHaveBeenCalledTimes(2);
  });
});
