/**
 * @vitest-environment jsdom
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { GenreFilter } from "./GenreFilter";
import type { Game } from "../lib/games";

// next/link はクリック時に App Router のコンテキストを要求する。
// テストでは素の <a> に差し替えて、コンテキストなしでもクリックできるようにする。
vi.mock("next/link", () => ({
  default: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

afterEach(() => {
  cleanup();
});

function makeGame(overrides: Partial<Game>): Game {
  return {
    slug: "sample",
    title: "サンプルゲーム",
    description: "テスト用のゲーム。",
    playUrl: "/play/sample/",
    genre: "action",
    ageRange: "5〜8歳",
    players: "ひとり用",
    difficulty: "やさしめ",
    devices: ["pc"],
    ...overrides,
  };
}

const GAMES: Game[] = [
  makeGame({ slug: "action-game", title: "アクションゲーム", genre: "action" }),
  makeGame({ slug: "puzzle-game", title: "パズルゲーム", genre: "puzzle" }),
  makeGame({ slug: "adventure-game", title: "アドベンチャーゲーム", genre: "adventure" }),
];

describe("GenreFilter", () => {
  it("初期状態ではすべてのゲームが表示される", () => {
    render(<GenreFilter games={GAMES} />);

    expect(screen.getByText("アクションゲーム")).not.toBeNull();
    expect(screen.getByText("パズルゲーム")).not.toBeNull();
    expect(screen.getByText("アドベンチャーゲーム")).not.toBeNull();
  });

  it("実際にゲームが存在するジャンルのみタブとして表示される", () => {
    render(<GenreFilter games={GAMES} />);

    expect(screen.getByRole("button", { name: "すべて" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "アクション" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "パズル" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "アドベンチャー" })).not.toBeNull();
    // GENRESには定義されているがどのゲームも使っていないジャンルは出さない
    expect(screen.queryByRole("button", { name: "レース" })).toBeNull();
  });

  it("ジャンルタブを押すとそのジャンルのゲームだけ表示される", () => {
    render(<GenreFilter games={GAMES} />);

    fireEvent.click(screen.getByRole("button", { name: "パズル" }));

    expect(screen.getByText("パズルゲーム")).not.toBeNull();
    expect(screen.queryByText("アクションゲーム")).toBeNull();
    expect(screen.queryByText("アドベンチャーゲーム")).toBeNull();
  });

  it("「すべて」タブを押すと全件表示に戻る", () => {
    render(<GenreFilter games={GAMES} />);

    fireEvent.click(screen.getByRole("button", { name: "パズル" }));
    fireEvent.click(screen.getByRole("button", { name: "すべて" }));

    expect(screen.getByText("アクションゲーム")).not.toBeNull();
    expect(screen.getByText("パズルゲーム")).not.toBeNull();
    expect(screen.getByText("アドベンチャーゲーム")).not.toBeNull();
  });

  it("選択中のタブは aria-pressed が true になる", () => {
    render(<GenreFilter games={GAMES} />);

    const allTab = screen.getByRole("button", { name: "すべて" });
    const puzzleTab = screen.getByRole("button", { name: "パズル" });

    expect(allTab.getAttribute("aria-pressed")).toBe("true");
    expect(puzzleTab.getAttribute("aria-pressed")).toBe("false");

    fireEvent.click(puzzleTab);

    expect(allTab.getAttribute("aria-pressed")).toBe("false");
    expect(puzzleTab.getAttribute("aria-pressed")).toBe("true");
  });
});
