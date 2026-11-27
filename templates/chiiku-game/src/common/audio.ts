// 声・鳴き声を Web Audio で鳴らす。知育ゲームで共通。ゲームごとの決まりを入れない。
//
// ブラウザは画面に触れるまで音を出せない（特に iOS Safari）。最初のタッチ（「はじめる」）の中で
// unlock() を呼ぶと、AudioContext が使えるようになる。

export interface AudioPlayer {
  /** 最初のタッチの処理の中で呼ぶ。AudioContext を動かし、無音を 1 回鳴らして音を解禁する */
  unlock(): Promise<void>;
  /** 鳴っている音を止めてから鳴らす。読み込みが遅くても、後から叩いた方を優先する */
  play(url: string): Promise<void>;
  /** 声を先に読み込んで、デコードしておく（鳴らさない）。最初のタッチで待たせないために、画面に出す前後に呼ぶ。失敗は握りつぶし、タップのときにやり直す */
  preload(urls: string[]): void;
  /** 鳴っている音と、読み込み中で鳴らしていない音を止める */
  stop(): void;
}

type SourceLike = {
  buffer: unknown;
  onended: (() => void) | null;
  connect(destination: unknown): unknown;
  start(when?: number): void;
  stop(): void;
};

type ContextLike = {
  readonly state: string;
  readonly destination: unknown;
  resume(): Promise<void>;
  createBufferSource(): SourceLike;
  createBuffer(channels: number, length: number, sampleRate: number): unknown;
  decodeAudioData(data: ArrayBuffer): Promise<unknown>;
};

type FetchLike = (
  url: string,
) => Promise<{ ok: boolean; status: number; arrayBuffer(): Promise<ArrayBuffer> }>;

export type AudioDeps = { context?: ContextLike; fetchFn?: FetchLike };

function defaultContext(): ContextLike {
  const w = window as unknown as {
    AudioContext?: new () => ContextLike;
    webkitAudioContext?: new () => ContextLike;
  };
  const Ctor = w.AudioContext ?? w.webkitAudioContext;
  if (!Ctor) {
    throw new Error('このブラウザは Web Audio に対応していない');
  }
  return new Ctor();
}

export function createAudio(deps: AudioDeps = {}): AudioPlayer {
  let context: ContextLike | undefined = deps.context;
  const fetchFn: FetchLike = deps.fetchFn ?? ((url) => fetch(url));
  const decoded = new Map<string, Promise<unknown>>();
  let playing: SourceLike | null = null;
  // play() ごとに増やす。読み込みの間に別の play()・stop() が来たら、古い方は鳴らさない
  let ticket = 0;

  const ctx = (): ContextLike => {
    context ??= defaultContext();
    return context;
  };

  const stopPlaying = () => {
    if (!playing) return;
    const source = playing;
    playing = null;
    source.onended = null;
    try {
      source.stop();
    } catch {
      // 鳴り終わった音を止めても例外になるブラウザがある。無視してよい
    }
  };

  const load = (url: string): Promise<unknown> => {
    let pending = decoded.get(url);
    if (!pending) {
      pending = (async () => {
        const res = await fetchFn(url);
        if (!res.ok) {
          throw new Error(`${url}: 読み込めない（HTTP ${res.status}）`);
        }
        return ctx().decodeAudioData(await res.arrayBuffer());
      })();
      decoded.set(url, pending);
      // 失敗したものは覚えない（次のタッチでやり直せるように）
      pending.catch(() => decoded.delete(url));
    }
    return pending;
  };

  return {
    unlock() {
      // await の前に全部呼ぶ。await の後ろだと、タッチの処理の外になり、iOS が音を許さないことがある
      // iOS Safari の Web Audio は、消音スイッチで消える。これは利用者の意思なので、変えない
      // （鳴らないときは、「？」の保護者向けの案内で消音ボタンを確かめてもらう）
      const c = ctx();
      const resumed = c.resume();
      const silent = c.createBufferSource();
      silent.buffer = c.createBuffer(1, 1, 22050);
      silent.connect(c.destination);
      silent.start(0);
      return resumed;
    },

    async play(url) {
      const mine = ++ticket;
      stopPlaying();
      const c = ctx();
      // suspended（最初のタッチの前）と、iOS が電話・画面ロックで止めた interrupted は、タップで動かし直す
      if (c.state !== 'running') {
        void c.resume().catch(() => {});
      }
      const buffer = await load(url);
      if (mine !== ticket) return;
      const source = c.createBufferSource();
      source.buffer = buffer;
      source.connect(c.destination);
      source.onended = () => {
        if (playing === source) playing = null;
      };
      playing = source;
      source.start(0);
    },

    preload(urls) {
      for (const url of urls) {
        load(url).catch(() => {
          // 先読みの失敗は、タップのときにもう一度読むので、ここでは何もしない（load が失敗を覚えない）
        });
      }
    },

    stop() {
      ticket++;
      stopPlaying();
    },
  };
}
