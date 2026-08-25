import Link from "next/link";
import type { Game } from "../lib/games";
import { GenreBadge } from "./GenreBadge";
import { MetaBadges } from "./MetaBadges";
import { GameThumbnail } from "./GameThumbnail";

export function GameCard({ game }: { game: Game }) {
  return (
    <Link
      href={`/games/${game.slug}`}
      className="block overflow-hidden rounded-lg border border-neutral-200 bg-white transition hover:shadow-md"
    >
      <div className="h-40 w-full">
        <GameThumbnail genre={game.genre} images={game.images} title={game.title} />
      </div>
      <div className="p-4">
        <div className="mb-2">
          <GenreBadge genre={game.genre} />
        </div>
        <h3 className="text-base font-bold text-neutral-900">{game.title}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-neutral-600">{game.description}</p>
        <div className="mt-3">
          <MetaBadges
            ageRange={game.ageRange}
            players={game.players}
            difficulty={game.difficulty}
            devices={game.devices}
          />
        </div>
      </div>
    </Link>
  );
}
