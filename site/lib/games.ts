import fs from "node:fs";
import path from "node:path";
import { GENRES, type GenreKey } from "./genres";
import { DEVICES, type DeviceKey } from "./devices";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  genre: GenreKey;
  devices: DeviceKey[];
  ageRange: string;
  players: string;
  difficulty: string;
  controls?: string[];
  images?: string[];
  featured?: boolean;
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

export function validateGame(data: unknown, file: string): Game {
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
  if (
    typeof genre !== "string" ||
    !Object.prototype.hasOwnProperty.call(GENRES, genre)
  ) {
    throw new Error(
      `content/games/${file}: "genre" が不正です(値: ${JSON.stringify(
        genre
      )})。GENRES(site/lib/genres.ts)のいずれかのキーを指定してください`
    );
  }

  const devices = record.devices;
  if (!Array.isArray(devices) || devices.length === 0) {
    throw new Error(
      `content/games/${file}: "devices" は1つ以上の要素を持つ配列である必要があります`
    );
  }

  for (const device of devices) {
    if (
      typeof device !== "string" ||
      !Object.prototype.hasOwnProperty.call(DEVICES, device)
    ) {
      throw new Error(
        `content/games/${file}: "devices" に不正な値が含まれています(値: ${JSON.stringify(
          device
        )})。DEVICES(site/lib/devices.ts)のいずれかのキーを指定してください`
      );
    }
  }

  if (new Set(devices).size !== devices.length) {
    throw new Error(
      `content/games/${file}: "devices" に重複した値が含まれています`
    );
  }

  const controls = record.controls;
  if (controls !== undefined) {
    if (
      !Array.isArray(controls) ||
      controls.length === 0 ||
      !controls.every(
        (control) => typeof control === "string" && control.trim() !== ""
      )
    ) {
      throw new Error(
        `content/games/${file}: "controls" は空でない文字列の配列である必要があります`
      );
    }
  }

  const images = record.images;
  if (images !== undefined) {
    if (
      !Array.isArray(images) ||
      !images.every((image) => typeof image === "string" && image.trim() !== "")
    ) {
      throw new Error(
        `content/games/${file}: "images" は空でない文字列の配列である必要があります`
      );
    }
  }

  const featured = record.featured;
  if (featured !== undefined && typeof featured !== "boolean") {
    throw new Error(
      `content/games/${file}: "featured" はboolean型である必要があります`
    );
  }

  return record as Game;
}

function parseGameJson(raw: string, file: string): unknown {
  try {
    return JSON.parse(raw);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`content/games/${file}: JSONの構文が不正です`);
    }
    throw error;
  }
}

export function getAllGames(): Game[] {
  const files = fs.readdirSync(GAMES_DIR).filter((f) => f.endsWith(".json"));
  const games = files.map((file) => {
    const raw = fs.readFileSync(path.join(GAMES_DIR, file), "utf-8");
    return validateGame(parseGameJson(raw, file), file);
  });
  return games.sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getGame(slug: string): Game | undefined {
  return getAllGames().find((game) => game.slug === slug);
}

export function getFeaturedGames(limit = 3): Game[] {
  const games = getAllGames();
  const featured = games.filter((game) => game.featured);
  return (featured.length > 0 ? featured : games).slice(0, limit);
}
