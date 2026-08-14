import { GENRES, type GenreKey } from "../lib/genres";

export function GameThumbnail({
  genre,
  images,
  title,
}: {
  genre: GenreKey;
  images?: string[];
  title: string;
}) {
  const firstImage = images?.[0];

  if (firstImage) {
    return <img src={firstImage} alt={title} className="h-full w-full object-cover" />;
  }

  return (
    <div
      className={`flex h-full w-full items-center justify-center text-4xl font-bold text-neutral-400 ${GENRES[genre].placeholderClassName}`}
    >
      {title.charAt(0)}
    </div>
  );
}
