"use client";

import { useState } from "react";
import { GENRES, type GenreKey } from "../lib/genres";
import type { Game } from "../lib/games";
import { GameCard } from "./GameCard";

const TAB_BASE_CLASS =
  "rounded-full px-4 py-1.5 text-sm font-bold transition";
const TAB_SELECTED_CLASS = "bg-neutral-900 text-white";
const TAB_UNSELECTED_CLASS = "bg-neutral-100 text-neutral-600 hover:bg-neutral-200";

export function GenreFilter({ games }: { games: Game[] }) {
  const [selected, setSelected] = useState<GenreKey | "all">("all");

  const availableGenres = (Object.keys(GENRES) as GenreKey[]).filter((genre) =>
    games.some((game) => game.genre === genre)
  );

  const filtered = selected === "all" ? games : games.filter((game) => game.genre === selected);

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          aria-pressed={selected === "all"}
          className={`${TAB_BASE_CLASS} ${selected === "all" ? TAB_SELECTED_CLASS : TAB_UNSELECTED_CLASS}`}
          onClick={() => setSelected("all")}
        >
          すべて
        </button>
        {availableGenres.map((genre) => (
          <button
            key={genre}
            type="button"
            aria-pressed={selected === genre}
            className={`${TAB_BASE_CLASS} ${selected === genre ? TAB_SELECTED_CLASS : TAB_UNSELECTED_CLASS}`}
            onClick={() => setSelected(genre)}
          >
            {GENRES[genre].label}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((game) => (
          <GameCard key={game.slug} game={game} />
        ))}
      </div>
    </div>
  );
}
