// 5 問のあとの「つづける／やめる」の画面。知育ゲームで共通。ゲームごとの決まりを入れない。
// ボタンは絵だけ。どちらも通常のタップ（長押しにしない）。「つづける」を大きく、「やめる」を小さくして、間違えて押しにくくする。

import { assetUrl } from './assets';
import type { AudioPlayer } from './audio';
import { createHelp } from './help';
import { createProgressDots } from './progress';

export type RoundEndOptions = {
  total: number;
  audio: AudioPlayer;
  onContinue: () => void;
  onQuit: () => void;
};

function pictureButton(className: string, glyph: string, label: string): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = className;
  button.setAttribute('aria-label', label);
  button.textContent = glyph;
  return button;
}

export function showRoundEnd(root: HTMLElement, opts: RoundEndOptions): void {
  const { total, audio, onContinue, onQuit } = opts;

  const dots = createProgressDots(total);
  dots.set(total);

  const continueButton = pictureButton('continue-button', '▶', 'つづける');
  const quitButton = pictureButton('quit-button', '🏠', 'やめる');

  // どちらか一方を、最初の 1 回だけ受け付ける（連打・両方押しで、二重に始まらないように）
  let decided = false;
  const decide = (action: () => void) => () => {
    if (decided) return;
    decided = true;
    action();
  };
  continueButton.addEventListener('click', decide(onContinue));
  quitButton.addEventListener('click', decide(onQuit));

  const screen = document.createElement('main');
  screen.className = 'round-end';
  screen.append(dots.el, continueButton, quitButton, createHelp());
  root.replaceChildren(screen);

  // 声が読み込めなくても、画面は使える
  audio.play(assetUrl('voice/again.wav')).catch((error: unknown) => {
    console.error(error);
  });
}
