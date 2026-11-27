import type { ItemsFile } from '../common/assets';
import type { AudioPlayer } from '../common/audio';
import { createExitButton } from '../common/exit-button';
import { createHelp } from '../common/help';

export type GameDeps = {
  file: ItemsFile;
  audio: AudioPlayer;
  /** ゲームを終えるとき（⏏ の長押し）。タイトル画面に戻る */
  onExit: () => void;
};

export function startGame(root: HTMLElement, deps: GameDeps): void {
  const { audio, onExit } = deps;

  const screen = document.createElement('main');
  screen.className = 'play-screen';
  screen.append(
    createExitButton(() => {
      audio.stop();
      onExit();
    }),
    createHelp(),
  );
  // ここに遊びを書く（素材は deps.file、声は audio.play(`${import.meta.env.BASE_URL}chiiku/voice/<id>.wav`)）
  root.replaceChildren(screen);
}
