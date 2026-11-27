// 正解のほめ方（音 → 声）と、間違いのやさしい音。知育ゲームで共通。ゲームごとの決まりを入れない。
// 音の素材は ankardo の共通素材（public/chiiku/sfx/）。

import { assetUrl } from './assets';
import type { AudioPlayer } from './audio';

/**
 * 正解の音を鳴らし、終わったら voiceUrl の声を鳴らす。
 * 最後まで鳴ったら true。途中で切られた（⏏・別の音）ら false で、そこで止める（呼んだ側は次へ進まない）。
 * 読み込めない音は console.error に出して飛ばし、遊びは続ける。
 */
export async function playCorrect(audio: AudioPlayer, voiceUrl: string): Promise<boolean> {
  for (const url of [assetUrl('sfx/correct.wav'), voiceUrl]) {
    try {
      if (!(await audio.playToEnd(url))) return false;
    } catch (error) {
      console.error(error);
    }
  }
  return true;
}

/** 間違いのやさしい音。鳴らせなくても、遊びは続ける */
export function playWrong(audio: AudioPlayer): void {
  audio.play(assetUrl('sfx/wrong.wav')).catch((error: unknown) => {
    console.error(error);
  });
}
