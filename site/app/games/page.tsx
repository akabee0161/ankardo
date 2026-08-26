import type { Metadata } from "next";
import { getAllGames } from "../../lib/games";
import { GenreFilter } from "../../components/GenreFilter";

export const metadata: Metadata = {
  title: "ゲーム一覧",
  description: "Ankardo に掲載しているゲームの一覧。",
};

export default function GamesList() {
  const games = getAllGames();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-neutral-900">ゲーム一覧</h1>
      <GenreFilter games={games} />
    </main>
  );
}
