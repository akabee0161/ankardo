import { notFound } from "next/navigation";
import { getAllGames, getGame } from "../../../lib/games";

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
    <main>
      <h1>{game.title}</h1>
      <p>{game.description}</p>
      <a href={game.playUrl}>プレイする</a>
    </main>
  );
}
