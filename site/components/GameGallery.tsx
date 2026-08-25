"use client";

import { useRef, useState } from "react";
import type { TouchEvent } from "react";
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
  const touchStartXRef = useRef<number | null>(null);

  if (!images || images.length === 0) {
    return (
      <div
        className={`flex aspect-video w-full items-center justify-center rounded-lg text-6xl font-bold text-neutral-400 ${GENRES[genre].placeholderClassName}`}
      >
        {title.charAt(0)}
      </div>
    );
  }

  function handleTouchStart(event: TouchEvent<HTMLDivElement>) {
    touchStartXRef.current = event.changedTouches[0]?.clientX ?? null;
  }

  function handleTouchEnd(event: TouchEvent<HTMLDivElement>) {
    const startX = touchStartXRef.current;
    touchStartXRef.current = null;
    if (startX === null || images.length <= 1) {
      return;
    }

    const endX = event.changedTouches[0]?.clientX;
    if (endX === undefined) {
      return;
    }

    const deltaX = endX - startX;
    const SWIPE_THRESHOLD = 50;
    if (Math.abs(deltaX) < SWIPE_THRESHOLD) {
      return;
    }

    if (deltaX < 0) {
      // 左スワイプ: 次の画像へ(最後の画像なら何もしない)
      setSelectedIndex((current) => Math.min(current + 1, images.length - 1));
    } else {
      // 右スワイプ: 前の画像へ(最初の画像なら何もしない)
      setSelectedIndex((current) => Math.max(current - 1, 0));
    }
  }

  return (
    <div>
      <div
        className="aspect-video w-full overflow-hidden rounded-lg"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <img src={images[selectedIndex]} alt={title} className="h-full w-full object-cover" />
      </div>
      {images.length > 1 && (
        <div className="mt-2 flex gap-2">
          {images.map((image, index) => (
            <button
              key={image}
              type="button"
              onClick={() => setSelectedIndex(index)}
              aria-label={`${title} スクリーンショット ${index + 1}`}
              aria-pressed={index === selectedIndex}
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
