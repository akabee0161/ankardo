import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AudioPlayer } from './audio';
import { showRoundEnd } from './round-end';

describe('showRoundEnd', () => {
  let root: HTMLElement;
  let audio: AudioPlayer;
  let onContinue: ReturnType<typeof vi.fn>;
  let onQuit: ReturnType<typeof vi.fn>;

  const show = () => showRoundEnd(root, { total: 5, audio, onContinue, onQuit });
  const button = (selector: string): HTMLButtonElement => {
    const el = root.querySelector<HTMLButtonElement>(selector);
    if (!el) throw new Error(`${selector} が無い`);
    return el;
  };

  beforeEach(() => {
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
    onContinue = vi.fn();
    onQuit = vi.fn();
  });

  it('shows the continue and quit buttons with pictures only', () => {
    show();
    expect(root.querySelector('main.round-end')).not.toBeNull();
    expect(button('.continue-button').textContent).toBe('▶');
    expect(button('.continue-button').getAttribute('aria-label')).toBe('つづける');
    expect(button('.quit-button').textContent).toBe('🏠');
    expect(button('.quit-button').getAttribute('aria-label')).toBe('やめる');
    expect(root.querySelector('.help-button')).not.toBeNull();
  });

  it('lights all the dots', () => {
    show();
    expect(root.querySelectorAll('.dot')).toHaveLength(5);
    expect(root.querySelectorAll('.dot.on')).toHaveLength(5);
  });

  it('asks "もういっかい やる？" by voice when it appears', () => {
    show();
    expect(audio.play).toHaveBeenCalledWith('/chiiku/voice/again.wav');
  });

  it('still shows the screen when the voice cannot be played', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    audio.play = vi.fn().mockRejectedValue(new Error('404'));
    show();
    await Promise.resolve();
    expect(button('.continue-button')).toBeTruthy();
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it('continues once, however many times continue is pressed', () => {
    show();
    const c = button('.continue-button');
    c.click();
    c.click();
    expect(onContinue).toHaveBeenCalledTimes(1);
    expect(onQuit).not.toHaveBeenCalled();
  });

  it('quits once, however many times quit is pressed', () => {
    show();
    const q = button('.quit-button');
    q.click();
    q.click();
    expect(onQuit).toHaveBeenCalledTimes(1);
    expect(onContinue).not.toHaveBeenCalled();
  });

  it('does not let continue and quit both fire', () => {
    show();
    button('.continue-button').click();
    button('.quit-button').click();
    expect(onContinue).toHaveBeenCalledTimes(1);
    expect(onQuit).not.toHaveBeenCalled();
  });
});
