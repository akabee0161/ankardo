// 触った絵がはねる動き。知育ゲームで共通。ゲームごとの決まりを入れない。
// 動きそのものは common.css の .bounce（@keyframes bounce）。ここは class の付け外しだけを行う。

export const BOUNCE_MS = 400;

export function createBouncer(): { bounce(el: HTMLElement): void; clear(): void } {
  const timers = new Map<HTMLElement, ReturnType<typeof setTimeout>>();

  return {
    /** 続けて呼ぶと、はねを最初からやり直す */
    bounce(el) {
      clearTimeout(timers.get(el));
      el.classList.remove('bounce');
      // class を付け直しても動きが再開するように、レイアウトを一度確定させる
      void el.offsetWidth;
      el.classList.add('bounce');
      timers.set(
        el,
        setTimeout(() => {
          el.classList.remove('bounce');
          timers.delete(el);
        }, BOUNCE_MS),
      );
    },
    /** 全部のタイマーを止め、class を外す（画面を描き直すときなど） */
    clear() {
      for (const [el, timer] of timers) {
        clearTimeout(timer);
        el.classList.remove('bounce');
      }
      timers.clear();
    },
  };
}
