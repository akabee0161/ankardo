import { GENRES, type GenreKey } from "../lib/genres";

export function GenreBadge({ genre }: { genre: GenreKey }) {
  const info = GENRES[genre];

  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-bold ${info.textClassName} ${info.badgeClassName}`}
    >
      {info.label}
    </span>
  );
}
