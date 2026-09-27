import { describe, expect, it } from "vitest";
import sitemap from "./sitemap";
import { getAllGames } from "../lib/games";

describe("sitemap", () => {
  const urls = sitemap().map((entry) => entry.url);

  it("固定ページを末尾スラッシュ付きの絶対URLで含む", () => {
    expect(urls).toEqual(
      expect.arrayContaining([
        "https://ankardo.com/",
        "https://ankardo.com/games/",
        "https://ankardo.com/about/",
      ]),
    );
  });

  it("全ゲームの詳細ページを含む", () => {
    for (const game of getAllGames()) {
      expect(urls).toContain(`https://ankardo.com/games/${game.slug}/`);
    }
  });

  it("URLが重複しない", () => {
    expect(new Set(urls).size).toBe(urls.length);
  });
});
