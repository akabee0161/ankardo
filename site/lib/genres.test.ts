import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { GENRES, type GenreKey } from "./genres";

const css = fs.readFileSync(path.join(process.cwd(), "app", "globals.css"), "utf-8");

describe("GENRES", () => {
  const keys = Object.keys(GENRES) as GenreKey[];

  it("全ジャンルに、globals.css の色(--color-genre-<キー>)がある(忘れると、バッジとカードの色が付かない)", () => {
    for (const key of keys) {
      expect(css, `--color-genre-${key}`).toMatch(new RegExp(`--color-genre-${key}:\\s*#[0-9a-fA-F]{6};`));
    }
  });

  it("バッジ・プレースホルダ・文字の class が、キーと同じ名前の色を使う", () => {
    for (const key of keys) {
      expect(GENRES[key].badgeClassName).toBe(`bg-genre-${key}`);
      expect(GENRES[key].placeholderClassName).toBe(`bg-genre-${key}/15`);
    }
  });

  it("文字の色は、白か濃色のどちらかで、ジャンルの色に対して AA(4.5:1)を満たす", () => {
    const hex = (key: string) => {
      const m = css.match(new RegExp(`--color-genre-${key}:\\s*#([0-9a-fA-F]{6});`));
      if (!m?.[1]) throw new Error(`--color-genre-${key} が無い`);
      return [0, 2, 4].map((i) => Number.parseInt((m[1] as string).slice(i, i + 2), 16));
    };
    const lin = (c: number) => {
      const s = c / 255;
      return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    };
    const lum = ([r, g, b]: number[]) => 0.2126 * lin(r as number) + 0.7152 * lin(g as number) + 0.0722 * lin(b as number);
    const contrast = (a: number, b: number) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const WHITE = 1;
    const NEUTRAL_900 = lum([0x17, 0x17, 0x17]); // Tailwind の neutral-900（#171717）
    for (const key of keys) {
      const bg = lum(hex(key));
      const text = GENRES[key].textClassName;
      expect(["text-white", "text-neutral-900"], key).toContain(text);
      const ratio = contrast(bg, text === "text-white" ? WHITE : NEUTRAL_900);
      expect(ratio, `${key} の文字の対比 ${ratio.toFixed(2)}:1`).toBeGreaterThanOrEqual(4.5);
    }
  });
});
