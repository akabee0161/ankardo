// 押す操作の受け付け。知育ゲームで共通。ゲームごとの決まりを入れない。
//
// 子どもは指をすべらせて触るので、触れた瞬間（pointerdown）に反応する。キーボードは Enter・スペース。
// それに加えて、支援技術（スクリーンリーダーなど）が要素を起動したときは click だけが来るので、それも受け付ける。
// 同じ操作で pointerdown・keydown のあとに続けて来る click では、もう一度呼ばない。

/** click が、直前の pointerdown・keydown と同じ操作の続きかを見分ける間（離した後も、この間は続きとみなす） */
export const CLICK_FOLLOW_MS = 600;

export function attachActivate(el: HTMLElement, onActivate: () => void): void {
  let followed = false;
  let clear: ReturnType<typeof setTimeout> | undefined;

  const handled = () => {
    followed = true;
    clearTimeout(clear);
  };
  const releaseSoon = () => {
    clearTimeout(clear);
    clear = setTimeout(() => {
      followed = false;
    }, CLICK_FOLLOW_MS);
  };

  el.addEventListener('pointerdown', (e) => {
    // PC の右クリック・中クリックでは起動しない（タッチ・ペン・左クリックは button 0）
    if (e.button > 0) return;
    handled();
    onActivate();
    // マウスで押して要素の外で離すと、pointerup は el に届かない。document でも受けて、期限を必ず設ける
    document.addEventListener('pointerup', releaseSoon, { once: true });
    document.addEventListener('pointercancel', releaseSoon, { once: true });
  });
  el.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    // 押しっぱなしの繰り返しでは起動しない
    if (e.repeat) return;
    handled();
    onActivate();
  });
  el.addEventListener('keyup', releaseSoon);
  el.addEventListener('click', () => {
    if (followed) {
      // pointerdown・keydown で処理済みの操作の続き
      followed = false;
      clearTimeout(clear);
      return;
    }
    onActivate();
  });
}
