import Link from "next/link";
import { getAllGames } from "../../lib/games";

export default function GamesList() {
  const games = getAllGames();

  return (
    <main>
      <h1>ゲーム一覧</h1>
      <ul>
        {games.map((game) => (
          <li key={game.slug}>
            <Link href={`/games/${game.slug}`}>{game.title}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
