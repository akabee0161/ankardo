import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EXIT_HOLD_MS, createExitButton } from './exit-button';

function fire(el: Element, type: string) {
  el.dispatchEvent(new Event(type, { bubbles: true }));
}

describe('createExitButton', () => {
  let onExit: ReturnType<typeof vi.fn>;
  let button: HTMLButtonElement;

  beforeEach(() => {
    vi.useFakeTimers();
    onExit = vi.fn();
    button = createExitButton(onExit);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('holds for 1.5 seconds', () => {
    expect(EXIT_HOLD_MS).toBe(1500);
  });

  it('calls onExit once after EXIT_HOLD_MS of holding', () => {
    fire(button, 'pointerdown');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 1);
    expect(onExit).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onExit).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(5000);
    expect(onExit).toHaveBeenCalledTimes(1);
  });

  it('does not call onExit when released at 1499ms', () => {
    fire(button, 'pointerdown');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 1);
    fire(button, 'pointerup');
    vi.advanceTimersByTime(5000);
    expect(onExit).not.toHaveBeenCalled();
  });

  it('exits after holding Enter or Space for EXIT_HOLD_MS (key repeats do not restart it)', () => {
    const key = (type: string, k: string, repeat = false) =>
      button.dispatchEvent(
        new KeyboardEvent(type, { key: k, repeat, bubbles: true, cancelable: true }),
      );
    key('keydown', 'Enter');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 1);
    key('keydown', 'Enter', true);
    expect(onExit).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onExit).toHaveBeenCalledTimes(1);
    key('keyup', 'Enter');
    key('keydown', ' ');
    vi.advanceTimersByTime(EXIT_HOLD_MS);
    expect(onExit).toHaveBeenCalledTimes(2);
  });

  it('still exits when another key (Shift) is released while Enter is held', () => {
    const key = (type: string, k: string) =>
      button.dispatchEvent(new KeyboardEvent(type, { key: k, bubbles: true, cancelable: true }));
    key('keydown', 'Enter');
    vi.advanceTimersByTime(500);
    key('keyup', 'Shift');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 500);
    expect(onExit).toHaveBeenCalledTimes(1);
  });

  it('does not exit by keyboard on a short press, when focus leaves, or on other keys', () => {
    const key = (type: string, k: string) =>
      button.dispatchEvent(new KeyboardEvent(type, { key: k, bubbles: true, cancelable: true }));
    key('keydown', 'Enter');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 1);
    key('keyup', 'Enter');
    key('keydown', ' ');
    vi.advanceTimersByTime(EXIT_HOLD_MS - 1);
    button.dispatchEvent(new Event('blur'));
    key('keydown', 'a');
    vi.advanceTimersByTime(EXIT_HOLD_MS * 3);
    expect(onExit).not.toHaveBeenCalled();
  });

  it('is a labelled button with the exit glyph', () => {
    expect(button.tagName).toBe('BUTTON');
    expect(button.type).toBe('button');
    expect(button.className).toBe('exit-button');
    expect(button.textContent).toBe('⏏');
    expect(button.getAttribute('aria-label')).toBe('おわる（ながおし）');
  });
});
