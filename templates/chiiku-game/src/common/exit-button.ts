// ゲームを終えるボタン（⏏）。長押しで押し、タイトル画面に戻る（子どもが間違えて出ないように）。
// 知育ゲームで共通。ゲームごとの決まりを入れない。

import { attachLongPress } from './long-press';

export const EXIT_HOLD_MS = 1500;

/**
 * 画面を描き直しても同じボタンを使い回せる（長押しの途中で消えないように）。
 * 見た目は common.css の .exit-button。置き場所（左上）もそこで決める。
 */
export function createExitButton(onExit: () => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'exit-button';
  button.setAttribute('aria-label', 'おわる（ながおし）');
  button.textContent = '⏏';
  attachLongPress(button, EXIT_HOLD_MS, onExit);

  // キーボード: Enter・スペースを EXIT_HOLD_MS 押し続けたら終える。離す・フォーカスが外れると取り消す
  let keyTimer: ReturnType<typeof setTimeout> | undefined;
  const cancelKey = () => {
    clearTimeout(keyTimer);
    keyTimer = undefined;
  };
  button.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    ev.preventDefault();
    if (ev.repeat || keyTimer !== undefined) return;
    keyTimer = setTimeout(() => {
      keyTimer = undefined;
      onExit();
    }, EXIT_HOLD_MS);
  });
  button.addEventListener('keyup', cancelKey);
  button.addEventListener('blur', cancelKey);
  return button;
}
