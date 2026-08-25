import { notFound } from "next/navigation";
import { getAllGames, getGame } from "../../../lib/games";
import { GenreBadge } from "../../../components/GenreBadge";
import { MetaBadges } from "../../../components/MetaBadges";
import { GameGallery } from "../../../components/GameGallery";

export function generateStaticParams() {
  return getAllGames().map((game) => ({ slug: game.slug }));
}

export default async function GameDetail({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const game = getGame(slug);

  if (!game) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <GameGallery genre={game.genre} images={game.images} title={game.title} />
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <GenreBadge genre={game.genre} />
        <MetaBadges
          ageRange={game.ageRange}
          players={game.players}
          difficulty={game.difficulty}
          devices={game.devices}
        />
      </div>
      <h1 className="mt-3 text-2xl font-extrabold text-neutral-900">{game.title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-neutral-600">{game.description}</p>
      <a
        href={game.playUrl}
        className="mt-6 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
      >
        ▶ プレイする
      </a>
      {game.controls && game.controls.length > 0 && (
        <section className="mt-8">
          <h2 className="text-base font-bold text-neutral-900">あそびかた</h2>
          <ul className="mt-2 list-disc pl-5 text-sm leading-relaxed text-neutral-600">
            {game.controls.map((control) => (
              <li key={control}>{control}</li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
