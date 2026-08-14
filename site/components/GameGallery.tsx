"use client";

import { useState } from "react";
import { GENRES, type GenreKey } from "../lib/genres";

export function GameGallery({
  genre,
  images,
  title,
}: {
  genre: GenreKey;
  images?: string[];
  title: string;
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!images || images.length === 0) {
    return (
      <div
        className={`flex h-48 w-full items-center justify-center rounded-lg text-6xl font-bold text-neutral-400 sm:h-72 ${GENRES[genre].placeholderClassName}`}
      >
        {title.charAt(0)}
      </div>
    );
  }

  return (
    <div>
      <div className="h-48 w-full overflow-hidden rounded-lg sm:h-72">
        <img src={images[selectedIndex]} alt={title} className="h-full w-full object-cover" />
      </div>
      {images.length > 1 && (
        <div className="mt-2 flex gap-2">
          {images.map((image, index) => (
            <button
              key={image}
              type="button"
              onClick={() => setSelectedIndex(index)}
              className={`h-16 w-16 overflow-hidden rounded-md border-2 ${
                index === selectedIndex ? "border-neutral-900" : "border-transparent opacity-60"
              }`}
            >
              <img src={image} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
