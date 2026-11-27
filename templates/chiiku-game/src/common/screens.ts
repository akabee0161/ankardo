import { createHelp } from './help';

// タイトル画面。知育ゲームで共通。ゲームごとの決まりを入れない。
// 字が読めない子ども向けなので、ボタンは絵（▶）だけ。字は親のための題とクレジットだけ。

export type TitleOptions = {
  title: string;
  /** タイトル画面の下に小さく出すクレジット（1 行ずつ） */
  credits: string[];
  /** 最初のタッチの中で、onStart の前に呼ぶ（音の解禁など）。ここで失敗しても、はじめる */
  unlock?: () => unknown;
  onStart: () => void;
};

export function showTitle(root: HTMLElement, opts: TitleOptions): void {
  root.replaceChildren();

  const screen = document.createElement('main');
  screen.className = 'title-screen';

  const heading = document.createElement('h1');
  heading.className = 'title-name';
  heading.textContent = opts.title;

  const start = document.createElement('button');
  start.type = 'button';
  start.className = 'start-button';
  start.setAttribute('aria-label', 'はじめる');
  start.textContent = '▶';

  const credits = document.createElement('div');
  credits.className = 'credits';
  for (const line of opts.credits) {
    const p = document.createElement('p');
    p.textContent = line;
    credits.append(p);
  }

  let started = false;
  start.addEventListener('click', () => {
    if (started) return;
    started = true;
    // unlock は必ず、このタッチの処理の中（await の前）で呼ぶ
    try {
      const result = opts.unlock?.();
      if (result instanceof Promise) result.catch(() => {});
    } catch {
      // 音が使えなくても、遊びは始められる
    }
    opts.onStart();
  });

  screen.append(heading, start, credits, createHelp());
  root.append(screen);
}
