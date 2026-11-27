import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { createHelp } from './help';

describe('createHelp', () => {
  let help: HTMLElement;
  const button = () => help.querySelector<HTMLButtonElement>('.help-button');
  const dialog = () => help.querySelector<HTMLElement>('.help-dialog');
  const close = () => help.querySelector<HTMLButtonElement>('.help-close');

  beforeEach(() => {
    document.body.replaceChildren();
    help = createHelp();
    document.body.append(help);
  });

  afterEach(() => {
    // 開いたままのテストが、document のキー入力の待ち受けを残さないように
    if (dialog()?.hidden === false) close()?.click();
  });

  it('shows only a small ? button at first, and the notice is hidden', () => {
    expect(button()?.textContent?.trim()).toBe('？');
    expect(button()?.getAttribute('aria-label')).toBe('ほごしゃの方へ');
    expect(dialog()?.hidden).toBe(true);
  });

  it('opens the notice for parents when ? is tapped, including the silent switch', () => {
    button()?.click();
    expect(dialog()?.hidden).toBe(false);
    expect(dialog()?.textContent).toContain('保護者の方へ');
    expect(dialog()?.textContent).toContain('消音ボタン');
  });

  it('closes only with the close button or Escape', () => {
    button()?.click();
    dialog()?.dispatchEvent(new Event('click', { bubbles: true })); // 背景のタッチでは閉じない
    expect(dialog()?.hidden).toBe(false);
    close()?.click();
    expect(dialog()?.hidden).toBe(true);
    button()?.click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(dialog()?.hidden).toBe(true);
  });

  it('does not play a voice or send the tap to the game behind it', () => {
    let reached = false;
    document.body.addEventListener('pointerdown', () => {
      reached = true;
    });
    button()?.dispatchEvent(new Event('pointerdown', { bubbles: true }));
    expect(reached).toBe(false);
  });

  it('makes the screen behind it unreachable by Tab while open, and brings it back when closed', () => {
    const behind = document.createElement('button');
    document.body.append(behind);
    button()?.click();
    expect(behind.hasAttribute('inert')).toBe(true);
    expect(help.hasAttribute('inert')).toBe(false); // 説明の中は、Tab で動ける
    close()?.click();
    expect(behind.hasAttribute('inert')).toBe(false);
  });

  it('puts the focus on the close button when opened', () => {
    button()?.click();
    expect(document.activeElement).toBe(close());
  });

  it('names the dialog, so assistive technology can tell what it is for', () => {
    expect(dialog()?.getAttribute('aria-label')).toBe('保護者の方へ');
  });

  it('takes the ? button out of the tab order while open, and puts it back when closed', () => {
    button()?.click();
    expect(button()?.hasAttribute('inert')).toBe(true);
    close()?.click();
    expect(button()?.hasAttribute('inert')).toBe(false);
  });

  it('keeps Tab and Shift+Tab on the close button while open', () => {
    button()?.click();
    for (const shiftKey of [false, true]) {
      const e = new KeyboardEvent('keydown', { key: 'Tab', shiftKey, cancelable: true });
      document.dispatchEvent(e);
      expect(e.defaultPrevented).toBe(true);
      expect(document.activeElement).toBe(close());
    }
  });

  it('leaves Tab alone when closed', () => {
    const e = new KeyboardEvent('keydown', { key: 'Tab', cancelable: true });
    document.dispatchEvent(e);
    expect(e.defaultPrevented).toBe(false);
  });
});
