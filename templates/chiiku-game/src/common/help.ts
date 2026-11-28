// 「？」ボタンと、保護者向けの注意。タイトル画面とゲーム画面の右上に置く。
// 子どもが触っても遊びが止まらないよう、押すとその場に説明が出るだけで、閉じるボタンでしか閉じない。

const NOTICE = [
  '【保護者の方へ】',
  '音が鳴らないときは、本体の消音ボタンがONになっていないか確かめてください。ONのときは、OFFにしてください。',
  '音量も確かめてください。',
];

/** 画面に置く入れ物。画面を置き換える側が、開いたままの説明を閉じるために `closeIfOpen` を呼ぶ */
export type Help = HTMLElement & { closeIfOpen(): void };

export function createHelp(): Help {
  // closeIfOpen は、下で入れる（それまでは型だけ Help にしておく）
  const wrap = document.createElement('div') as unknown as Help;
  wrap.className = 'help';
  // 触れたことが、後ろの遊び（声を鳴らす処理）へ伝わらないように
  wrap.addEventListener('pointerdown', (e) => e.stopPropagation());

  const open = document.createElement('button');
  open.type = 'button';
  open.className = 'help-button';
  open.setAttribute('aria-label', 'ほごしゃの方へ');
  open.textContent = '？';

  const dialog = document.createElement('div');
  dialog.className = 'help-dialog';
  dialog.setAttribute('role', 'dialog');
  dialog.setAttribute('aria-modal', 'true');
  dialog.setAttribute('aria-label', '保護者の方へ');
  dialog.hidden = true;

  const panel = document.createElement('div');
  panel.className = 'help-panel';
  for (const line of NOTICE) {
    const p = document.createElement('p');
    p.textContent = line;
    panel.append(p);
  }
  const closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.className = 'help-close';
  closeButton.textContent = 'とじる';
  panel.append(closeButton);
  dialog.append(panel);

  const onKey = (e: KeyboardEvent) => {
    // 開いたまま画面が置き換わった（長押しの終了など）。後の画面の Tab を奪わないように、ここで外す
    if (!wrap.isConnected) {
      close();
      return;
    }
    if (e.key === 'Escape') close();
    // 説明の中で動けるのは「とじる」だけ。Tab・Shift+Tab で、後ろ（ブラウザの画面の外）へ出さない
    if (e.key === 'Tab') {
      e.preventDefault();
      closeButton.focus();
    }
  };
  // 説明を開いている間、後ろの画面は Tab で動けず、Enter も効かないようにする（後ろの絵の声が鳴らないように）
  let behind: Element[] = [];
  function close(refocus = true) {
    dialog.hidden = true;
    for (const el of behind) el.removeAttribute('inert');
    behind = [];
    open.removeAttribute('inert');
    document.removeEventListener('keydown', onKey);
    if (refocus) open.focus();
  }
  // 説明を開いたまま、画面が置き換わるとき（区切りの画面など）に呼ぶ。開いていなければ何もしない。
  // 置き換わった後も画面が使い回されるので、閉じておかないと、戻ったときに説明が開いたまま出る
  wrap.closeIfOpen = () => {
    if (!dialog.hidden) close(false);
  };
  open.addEventListener('click', () => {
    dialog.hidden = false;
    behind = [...(wrap.parentElement?.children ?? [])].filter((el) => el !== wrap);
    for (const el of behind) el.setAttribute('inert', '');
    open.setAttribute('inert', ''); // 「？」は説明と同じ入れ物の中にあるので、自分で外す
    document.addEventListener('keydown', onKey);
    closeButton.focus();
  });
  closeButton.addEventListener('click', () => close());

  wrap.append(open, dialog);
  return wrap;
}
