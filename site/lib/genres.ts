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
};

export const GENRES: Record<GenreKey, GenreInfo> = {
  action: {
    label: "アクション",
    badgeClassName: "bg-genre-action",
    placeholderClassName: "bg-genre-action/15",
  },
  puzzle: {
    label: "パズル",
    badgeClassName: "bg-genre-puzzle",
    placeholderClassName: "bg-genre-puzzle/15",
  },
  adventure: {
    label: "アドベンチャー",
    badgeClassName: "bg-genre-adventure",
    placeholderClassName: "bg-genre-adventure/15",
  },
  rhythm: {
    label: "リズム/音楽",
    badgeClassName: "bg-genre-rhythm",
    placeholderClassName: "bg-genre-rhythm/15",
  },
  racing: {
    label: "レース",
    badgeClassName: "bg-genre-racing",
    placeholderClassName: "bg-genre-racing/15",
  },
  shooting: {
    label: "シューティング",
    badgeClassName: "bg-genre-shooting",
    placeholderClassName: "bg-genre-shooting/15",
  },
  simulation: {
    label: "育成/シミュレーション",
    badgeClassName: "bg-genre-simulation",
    placeholderClassName: "bg-genre-simulation/15",
  },
};
