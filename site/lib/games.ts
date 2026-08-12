import fs from "node:fs";
import path from "node:path";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  screenshot?: string;
};

const GAMES_DIR = path.join(process.cwd(), "content", "games");

export function getAllGames(): Game[] {
  const files = fs.readdirSync(GAMES_DIR).filter((f) => f.endsWith(".json"));
  const games = files.map((file) => {
    const raw = fs.readFileSync(path.join(GAMES_DIR, file), "utf-8");
    return JSON.parse(raw) as Game;
  });
  return games.sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getGame(slug: string): Game | undefined {
  return getAllGames().find((game) => game.slug === slug);
}
