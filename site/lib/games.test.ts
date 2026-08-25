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
  devices: ["pc"],
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

  it("devices が未設定ならエラーになる", () => {
    const { devices, ...withoutDevices } = VALID_GAME;
    expect(() => validateGame(withoutDevices, "sample.json")).toThrow(
      /"devices"/
    );
  });

  it("devices が空配列ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: [] }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: "pc" }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices に DEVICES に無い値が含まれていればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: ["pc", "vr"] }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices に重複があればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: ["pc", "pc"] }, "sample.json")
    ).toThrow(/重複/);
  });

  it("devices に複数の有効な値を指定できる", () => {
    const game = { ...VALID_GAME, devices: ["pc", "mobile-landscape"] };
    expect(validateGame(game, "sample.json")).toEqual(game);
  });

  it("controls が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, controls: "タップでジャンプ" }, "sample.json")
    ).toThrow(/"controls"/);
  });

  it("controls に空文字が含まれていればエラーになる", () => {
    expect(() =>
      validateGame(
        { ...VALID_GAME, controls: ["タップでジャンプ", ""] },
        "sample.json"
      )
    ).toThrow(/"controls"/);
  });

  it("controls が未設定でも通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });

  it("controls に文字列の配列を指定できる", () => {
    const game = { ...VALID_GAME, controls: ["タップでジャンプ"] };
    expect(validateGame(game, "sample.json")).toEqual(game);
  });
});
