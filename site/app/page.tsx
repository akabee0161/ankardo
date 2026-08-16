import Link from "next/link";
import { getFeaturedGames } from "../lib/games";
import { GameCard } from "../components/GameCard";
import { GENRES, type GenreKey } from "../lib/genres";

export default function Home() {
  const featuredGames = getFeaturedGames();

  return (
    <main>
      <section
        className="px-4 py-16 text-center text-white"
        style={{
          background:
            "linear-gradient(120deg, var(--color-genre-action), var(--color-genre-puzzle), var(--color-genre-adventure), var(--color-genre-rhythm), var(--color-genre-racing), var(--color-genre-shooting), var(--color-genre-simulation))",
        }}
      >
        <h1 className="text-3xl font-extrabold drop-shadow-sm sm:text-4xl">
          見つけよう、きみだけのすきなゲーム
        </h1>
        <p className="mt-3 text-sm font-medium drop-shadow-sm sm:text-base">
          年齢・ジャンルで選べる、子供向けインディーゲームカタログ
        </p>
      </section>

      {featuredGames.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 py-10">
          <h2 className="mb-4 text-xl font-bold text-neutral-900">ピックアップゲーム</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {featuredGames.map((game) => (
              <GameCard key={game.slug} game={game} />
            ))}
          </div>
        </section>
      )}

      <section className="mx-auto max-w-5xl px-4 py-10">
        <h2 className="mb-4 text-xl font-bold text-neutral-900">ジャンルから探す</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {(Object.keys(GENRES) as GenreKey[]).map((key) => {
            const info = GENRES[key];
            return (
              <Link
                key={key}
                href="/games"
                className={`flex h-16 items-center justify-center rounded-lg text-sm font-bold ${info.textClassName} ${info.badgeClassName}`}
              >
                {info.label}
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-4 pb-16 text-center">
        <p className="text-sm text-neutral-600">
          対象年齢やジャンルでゲームを選べるので、お子さまに合った一本を見つけやすくしています。
        </p>
        <Link
          href="/games"
          className="mt-6 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
        >
          ゲーム一覧を見る
        </Link>
      </section>
    </main>
  );
}
