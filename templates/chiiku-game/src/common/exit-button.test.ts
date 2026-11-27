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

  it('is a labelled button with the exit glyph', () => {
    expect(button.tagName).toBe('BUTTON');
    expect(button.type).toBe('button');
    expect(button.className).toBe('exit-button');
    expect(button.textContent).toBe('⏏');
    expect(button.getAttribute('aria-label')).toBe('おわる（ながおし）');
  });
});
