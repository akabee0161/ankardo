import { loadItems } from './common/assets';
import { createAudio } from './common/audio';
import './common/common.css';
import { showTitle } from './common/screens';
import { startGame } from './game/game';
import './style.css';

// 画面の下に出すクレジット。ankardo の shared-assets/chiiku/CREDITS.md に従う。
// 鳴き声を入れたゲーム（copy-assets.sh に --no-cry を付けない）は、public/chiiku/CREDITS.md の 3 行にする
const CREDITS = ['VOICEVOX:ずんだもん'];

const root = document.getElementById('app');
if (!root) {
  throw new Error('#app が無い');
}
const app: HTMLElement = root;

async function main() {
  // 素材の一覧が読めて、形が合っていなければ、下の catch で知らせる
  const file = await loadItems(`${import.meta.env.BASE_URL}chiiku/items.json`);
  const audio = createAudio();

  const showHome = () =>
    showTitle(app, {
      title: '__TITLE__',
      credits: CREDITS,
      unlock: () => audio.unlock(),
      onStart: () => startGame(app, { file, audio, onExit: showHome }),
    });
  showHome();
}

main().catch((error: unknown) => {
  console.error(error);
  app.textContent = '読み込めませんでした。もう一度ひらいてください。';
});
