import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AudioPlayer } from '../common/audio';
import { startGame } from './game';

function fire(el: Element, type: string) {
  el.dispatchEvent(new Event(type, { bubbles: true }));
}

describe('startGame', () => {
  let root: HTMLElement;
  let audio: AudioPlayer;
  let onExit: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    document.body.replaceChildren();
    root = document.createElement('div');
    document.body.append(root);
    audio = {
      unlock: vi.fn(),
      play: vi.fn().mockResolvedValue(undefined),
      playToEnd: vi.fn().mockResolvedValue(true),
      preload: vi.fn(),
      stop: vi.fn(),
    } as unknown as AudioPlayer;
    onExit = vi.fn();
    startGame(root, { file: { categories: [], items: [] }, audio, onExit });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('shows the exit button and the help button', () => {
    expect(root.querySelector('.exit-button')?.textContent).toBe('⏏');
    expect(root.querySelector('.help-button')?.textContent).toBe('？');
  });

  it('stops the audio and exits after holding the exit button for 1.5 seconds', () => {
    const exit = root.querySelector('.exit-button');
    if (!exit) throw new Error('no exit button');
    fire(exit, 'pointerdown');
    vi.advanceTimersByTime(1499);
    expect(onExit).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(audio.stop).toHaveBeenCalledTimes(1);
    expect(onExit).toHaveBeenCalledTimes(1);
  });
});
