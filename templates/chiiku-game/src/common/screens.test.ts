import { beforeEach, describe, expect, it, vi } from 'vitest';
import { showTitle } from './screens';

describe('showTitle', () => {
  let root: HTMLElement;

  beforeEach(() => {
    root = document.createElement('div');
  });

  it('shows one big start button that has only a picture, and the credits', () => {
    showTitle(root, {
      title: 'ゲームの題',
      credits: ['VOICEVOX:ずんだもん'],
      onStart: () => {},
    });
    const buttons = root.querySelectorAll('.start-button');
    expect(buttons).toHaveLength(1);
    expect(buttons[0]?.textContent?.trim()).toBe('▶');
    expect(buttons[0]?.getAttribute('aria-label')).toBe('はじめる');
    expect(root.textContent).toContain('ゲームの題');
    expect(root.textContent).toContain('VOICEVOX:ずんだもん');
  });

  it('unlock is called inside the start tap, before onStart', () => {
    const order: string[] = [];
    showTitle(root, {
      title: 't',
      credits: [],
      unlock: () => order.push('unlock'),
      onStart: () => order.push('start'),
    });
    root.querySelector('button')?.click();
    // click() が返った時点で両方が済んでいる = タッチの処理の中で呼んでいる
    expect(order).toEqual(['unlock', 'start']);
  });

  it('starts even when unlock throws', () => {
    const onStart = vi.fn();
    showTitle(root, {
      title: 't',
      credits: [],
      unlock: () => {
        throw new Error('boom');
      },
      onStart,
    });
    root.querySelector('button')?.click();
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it('does not start twice when the button is tapped twice', () => {
    const onStart = vi.fn();
    showTitle(root, { title: 't', credits: [], onStart });
    const button = root.querySelector('button');
    button?.click();
    button?.click();
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it('shows no credit line when there are no credits', () => {
    showTitle(root, { title: 't', credits: [], onStart: () => {} });
    expect(root.querySelector('.credits')?.children.length ?? 0).toBe(0);
  });

  it('has the ? button for parents, and tapping it does not start the game', () => {
    const onStart = vi.fn();
    showTitle(root, { title: 't', credits: [], onStart });
    root.querySelector<HTMLElement>('.help-button')?.click();
    expect(root.querySelector<HTMLElement>('.help-dialog')?.hidden).toBe(false);
    expect(onStart).not.toHaveBeenCalled();
  });
});
