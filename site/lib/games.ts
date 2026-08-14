import fs from "node:fs";
import path from "node:path";
import { GENRES, type GenreKey } from "./genres";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  genre: GenreKey;
  ageRange: string;
  players: string;
  difficulty: string;
  images?: string[];
};

const GAMES_DIR = path.join(process.cwd(), "content", "games");

const REQUIRED_STRING_FIELDS = [
  "slug",
  "title",
  "description",
  "playUrl",
  "ageRange",
  "players",
  "difficulty",
] as const;

function validateGame(data: unknown, file: string): Game {
  if (typeof data !== "object" || data === null) {
    throw new Error(`content/games/${file}: JSONオブジェクトではありません`);
  }

  const record = data as Record<string, unknown>;

  for (const field of REQUIRED_STRING_FIELDS) {
    const value = record[field];
    if (typeof value !== "string" || value.trim() === "") {
      throw new Error(
        `content/games/${file}: "${field}" は空でない文字列である必要があります`
      );
    }
  }

  const genre = record.genre;
  if (typeof genre !== "string" || !(genre in GENRES)) {
    throw new Error(
      `content/games/${file}: "genre" が不正です(値: ${JSON.stringify(
        genre
      )})。GENRES(site/lib/genres.ts)のいずれかのキーを指定してください`
    );
  }

  return record as Game;
}

export function getAllGames(): Game[] {
  const files = fs.readdirSync(GAMES_DIR).filter((f) => f.endsWith(".json"));
  const games = files.map((file) => {
    const raw = fs.readFileSync(path.join(GAMES_DIR, file), "utf-8");
    return validateGame(JSON.parse(raw), file);
  });
  return games.sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getGame(slug: string): Game | undefined {
  return getAllGames().find((game) => game.slug === slug);
}
