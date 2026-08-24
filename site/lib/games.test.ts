import { describe, expect, it } from "vitest";
import { validateGame } from "./games";

const VALID_GAME = {
  slug: "sample",
  title: "サンプルゲーム",
  description: "テスト用のゲーム。",
  playUrl: "/play/sample/",
  genre: "action",
  ageRange: "5〜8歳",
  players: "ひとり用",
  difficulty: "やさしめ",
};

describe("validateGame", () => {
  it("必須フィールドが揃っていれば通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });

  it("JSONオブジェクトでなければエラーになる", () => {
    expect(() => validateGame(null, "sample.json")).toThrow(
      /JSONオブジェクトではありません/
    );
    expect(() => validateGame("文字列", "sample.json")).toThrow(
      /JSONオブジェクトではありません/
    );
  });

  it("必須の文字列フィールドが欠けていればエラーになる", () => {
    const { title, ...withoutTitle } = VALID_GAME;
    expect(() => validateGame(withoutTitle, "sample.json")).toThrow(/"title"/);
  });

  it("必須の文字列フィールドが空文字ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, description: "   " }, "sample.json")
    ).toThrow(/"description"/);
  });

  it("genre が GENRES に無い値ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, genre: "cooking" }, "sample.json")
    ).toThrow(/"genre"/);
  });

  it("images が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, images: "/a.png" }, "sample.json")
    ).toThrow(/"images"/);
  });

  it("images に空文字が含まれていればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, images: ["/a.png", ""] }, "sample.json")
    ).toThrow(/"images"/);
  });

  it("images が未設定でも通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });
});
