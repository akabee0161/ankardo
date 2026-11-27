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
  return button;
}
