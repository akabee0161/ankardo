import { afterEach, describe, expect, it, vi } from 'vitest';
import type { AudioPlayer } from './audio';
import { playCorrect, playWrong } from './feedback';

type FakeAudio = AudioPlayer & {
  play: ReturnType<typeof vi.fn>;
  playToEnd: ReturnType<typeof vi.fn>;
};

function fakeAudio(overrides: Record<string, unknown> = {}): FakeAudio {
  return {
    unlock: vi.fn(),
    play: vi.fn().mockResolvedValue(undefined),
    playToEnd: vi.fn().mockResolvedValue(true),
    preload: vi.fn(),
    stop: vi.fn(),
    ...overrides,
  } as unknown as FakeAudio;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('playCorrect', () => {
  it('plays the chime, then the voice, and returns true', async () => {
    const audio = fakeAudio();
    await expect(playCorrect(audio, '/v/ok-dog.wav')).resolves.toBe(true);
    expect(audio.playToEnd.mock.calls.map((c) => c[0])).toEqual([
      '/chiiku/sfx/correct.wav',
      '/v/ok-dog.wav',
    ]);
  });

  it('does not play the voice when the chime was cut off, and returns false', async () => {
    const audio = fakeAudio({ playToEnd: vi.fn().mockResolvedValueOnce(false) });
    await expect(playCorrect(audio, '/v/ok-dog.wav')).resolves.toBe(false);
    expect(audio.playToEnd).toHaveBeenCalledTimes(1);
  });

  it('plays the voice even if the chime cannot be read', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    const audio = fakeAudio({
      playToEnd: vi.fn().mockRejectedValueOnce(new Error('404')).mockResolvedValueOnce(true),
    });
    await expect(playCorrect(audio, '/v/ok-dog.wav')).resolves.toBe(true);
    expect(audio.playToEnd).toHaveBeenCalledTimes(2);
    expect(error).toHaveBeenCalled();
  });

  it('returns true when only the voice cannot be read (the game goes on)', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    const audio = fakeAudio({
      playToEnd: vi.fn().mockResolvedValueOnce(true).mockRejectedValueOnce(new Error('404')),
    });
    await expect(playCorrect(audio, '/v/ok-dog.wav')).resolves.toBe(true);
    expect(error).toHaveBeenCalled();
  });

  it('returns false when the voice was cut off', async () => {
    const audio = fakeAudio({
      playToEnd: vi.fn().mockResolvedValueOnce(true).mockResolvedValueOnce(false),
    });
    await expect(playCorrect(audio, '/v/ok-dog.wav')).resolves.toBe(false);
  });
});

describe('playWrong', () => {
  it('plays the soft sound', () => {
    const audio = fakeAudio();
    playWrong(audio);
    expect(audio.play).toHaveBeenCalledWith('/chiiku/sfx/wrong.wav');
  });

  it('does not throw when the sound cannot be read', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    const audio = fakeAudio({ play: vi.fn().mockRejectedValue(new Error('404')) });
    expect(() => playWrong(audio)).not.toThrow();
    await Promise.resolve();
    await Promise.resolve();
    expect(error).toHaveBeenCalled();
  });
});
