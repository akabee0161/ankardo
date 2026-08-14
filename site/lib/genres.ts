export type GenreKey =
  | "action"
  | "puzzle"
  | "adventure"
  | "rhythm"
  | "racing"
  | "shooting"
  | "simulation";

export type GenreInfo = {
  label: string;
  badgeClassName: string;
  placeholderClassName: string;
  textClassName: string;
};

export const GENRES: Record<GenreKey, GenreInfo> = {
  action: {
    label: "アクション",
    badgeClassName: "bg-genre-action",
    placeholderClassName: "bg-genre-action/15",
    // #ff7a45 は白文字だと2.59:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
  puzzle: {
    label: "パズル",
    badgeClassName: "bg-genre-puzzle",
    placeholderClassName: "bg-genre-puzzle/15",
    // #2f80ed は白文字だと3.87:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
  adventure: {
    label: "アドベンチャー",
    badgeClassName: "bg-genre-adventure",
    placeholderClassName: "bg-genre-adventure/15",
    // #43a047 は白文字だと3.30:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
  rhythm: {
    label: "リズム/音楽",
    badgeClassName: "bg-genre-rhythm",
    placeholderClassName: "bg-genre-rhythm/15",
    // #ec407a は白文字だと3.76:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
  racing: {
    label: "レース",
    badgeClassName: "bg-genre-racing",
    placeholderClassName: "bg-genre-racing/15",
    // #ffc107 は白文字だと1.63:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
  shooting: {
    label: "シューティング",
    badgeClassName: "bg-genre-shooting",
    placeholderClassName: "bg-genre-shooting/15",
    // #7c4dff は濃色文字だと3.72:1でAA未達のため白文字にする(白文字は4.81:1でAA達成)
    textClassName: "text-white",
  },
  simulation: {
    label: "育成/シミュレーション",
    badgeClassName: "bg-genre-simulation",
    placeholderClassName: "bg-genre-simulation/15",
    // #26c6da は白文字だと2.06:1でAA未達のため濃色文字にする
    textClassName: "text-neutral-900",
  },
};
