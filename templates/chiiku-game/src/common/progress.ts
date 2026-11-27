// 問題を出すゲームの「1 回 5 問」の区切りと、進み具合を見せる点の並び。知育ゲームで共通。ゲームごとの決まりを入れない。
// 点は点数ではなく、正解した問題の数を見せる飾り。間違えても減らさない。記録は残さない。

export const ROUND_SIZE = 5;

export type ProgressDots = {
  el: HTMLElement;
  /** 先頭から n 個を灯す（0..total に丸める） */
  set(done: number): void;
};

export function createProgressDots(total: number): ProgressDots {
  const el = document.createElement('div');
  el.className = 'progress';
  el.setAttribute('role', 'img');
  const dots = Array.from({ length: total }, () => {
    const dot = document.createElement('span');
    dot.className = 'dot';
    el.append(dot);
    return dot;
  });

  const set = (done: number) => {
    const n = Math.max(0, Math.min(total, Math.floor(done)));
    dots.forEach((dot, i) => {
      dot.classList.toggle('on', i < n);
    });
    el.setAttribute('aria-label', `${total} もん中 ${n} もん`);
  };
  set(0);

  return { el, set };
}
