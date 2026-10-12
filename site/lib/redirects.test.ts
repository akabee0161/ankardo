import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { getAllGames } from "./games";

// public/_redirects は Cloudflare Workers Assets が読む転送ルール。
// 書式: [source] [destination] [code]
function readRules(): string[][] {
  const raw = fs.readFileSync(path.join(process.cwd(), "public", "_redirects"), "utf-8");
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "" && !line.startsWith("#"))
    .map((line) => line.split(/\s+/));
}

describe("_redirects", () => {
  const rules = readRules();

  it("末尾スラッシュなしの固定ページを 301 でスラッシュ付きへ転送する", () => {
    for (const page of ["/games", "/about"]) {
      expect(rules).toContainEqual([page, `${page}/`, "301"]);
    }
  });

  it("全ゲームの詳細ページを 301 でスラッシュ付きへ転送する", () => {
    for (const game of getAllGames()) {
      const source = `/games/${game.slug}`;
      expect(rules).toContainEqual([source, `${source}/`, "301"]);
    }
  });

  it("プレースホルダやワイルドカードを使わない(/games/ 配下の .txt などまで転送してしまうため)", () => {
    for (const [source] of rules) {
      expect(source).not.toMatch(/[:*]/);
    }
  });
});
