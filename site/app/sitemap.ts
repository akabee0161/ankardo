import type { MetadataRoute } from "next";
import { getAllGames } from "../lib/games";
import { SITE_URL } from "../lib/site";

export const dynamic = "force-static";

// next.config.js の trailingSlash: true に合わせ、末尾スラッシュ付きのURLを載せる。
// /play/<slug>/* のゲーム本体は各ゲームリポジトリの持ち物なので含めない
export default function sitemap(): MetadataRoute.Sitemap {
  const paths = [
    "/",
    "/games/",
    "/about/",
    ...getAllGames().map((game) => `/games/${game.slug}/`),
  ];
  return paths.map((path) => ({ url: `${SITE_URL}${path}` }));
}
