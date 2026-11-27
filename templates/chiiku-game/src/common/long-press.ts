// 長押しの検出。ゲームを終えるボタンに使う（子どもが間違えて押しても出ないように）。
// 知育ゲームで共通。ゲームごとの決まりを入れない。

/**
 * pointerdown から ms 続いたら 1 回だけ onFire を呼ぶ。
 * 押し始めた指が、離れる・要素から出る・取り消されるときは、途中で止める。
 * 押している間にもう 1 本の指が触れても、数え直さず、2 回目も呼ばない。2 本目の指の動きでは止めない。
 * 返り値の関数で外す（押している途中なら取り消す）。
 */
export function attachLongPress(el: HTMLElement, ms: number, onFire: () => void): () => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let held = false;
  // 押し始めた指の ID。テストなど pointerId の無いイベントでは undefined どうしで一致する
  let pressId: number | undefined;

  const idOf = (e: Event) => (e as PointerEvent).pointerId;

  const cancel = () => {
    held = false;
    pressId = undefined;
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  };
  const down = (e: Event) => {
    if (held) return;
    held = true;
    pressId = idOf(e);
    timer = setTimeout(() => {
      timer = null;
      onFire();
    }, ms);
  };
  const end = (e: Event) => {
    if (held && idOf(e) === pressId) cancel();
  };
  // タッチでは、指は押した要素に捕まえられたままになり、外へ出ても pointerleave が来ない。
  // 動いた位置が要素の外なら、取り消す
  const move = (e: Event) => {
    if (!held || idOf(e) !== pressId) return;
    const { clientX, clientY } = e as PointerEvent;
    if (typeof clientX !== 'number' || typeof clientY !== 'number') return;
    const r = el.getBoundingClientRect();
    if (clientX < r.left || clientX > r.right || clientY < r.top || clientY > r.bottom) cancel();
  };
  // 長押しで出る「コピー・保存」のメニュー（Android など）を出さない
  const noMenu = (e: Event) => e.preventDefault();

  el.addEventListener('pointerdown', down);
  el.addEventListener('pointerup', end);
  el.addEventListener('pointerleave', end);
  el.addEventListener('pointercancel', end);
  el.addEventListener('pointermove', move);
  el.addEventListener('contextmenu', noMenu);

  return () => {
    cancel();
    el.removeEventListener('pointerdown', down);
    el.removeEventListener('pointerup', end);
    el.removeEventListener('pointerleave', end);
    el.removeEventListener('pointercancel', end);
    el.removeEventListener('pointermove', move);
    el.removeEventListener('contextmenu', noMenu);
  };
}
