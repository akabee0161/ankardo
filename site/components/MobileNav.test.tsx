/**
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MobileNav } from "./MobileNav";

// next/link はクリック時に App Router のコンテキストを要求する。
// テストでは素の <a> に差し替えて、コンテキストなしでもクリックできるようにする。
vi.mock("next/link", () => ({
  default: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

// jsdom は matchMedia を実装していないため、既定のモックを用意する。
// デフォルトでは常に matches: false（デスクトップ幅ではない）として扱う。
beforeEach(() => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  );
});

afterEach(() => {
  cleanup();
  document.body.style.overflow = "";
  vi.unstubAllGlobals();
});

describe("MobileNav", () => {
  it("初期状態ではメニューが閉じている", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("ボタンを押すとメニューが開く", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));

    expect(screen.getByRole("link", { name: "ゲーム一覧" })).not.toBeNull();
    expect(screen.getByRole("link", { name: "このサイトについて" })).not.toBeNull();
    expect(
      screen.getByRole("button", { name: "メニューを閉じる" }).getAttribute("aria-expanded")
    ).toBe("true");
  });

  it("開いている間は背後のスクロールを止める", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    expect(document.body.style.overflow).toBe("hidden");

    fireEvent.click(screen.getByRole("button", { name: "メニューを閉じる" }));
    expect(document.body.style.overflow).toBe("");
  });

  it("Escキーで閉じる", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    fireEvent.keyDown(document, { key: "Escape" });

    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("閉じたときフォーカスがボタンに戻る", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    fireEvent.click(button);
    fireEvent.keyDown(document, { key: "Escape" });

    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "メニューを開く" })
    );
  });

  it("メニュー内のリンクを押すと閉じる", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    fireEvent.click(screen.getByRole("link", { name: "ゲーム一覧" }));

    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("aria-controls がメニューの id と一致する", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    const controls = button.getAttribute("aria-controls");
    fireEvent.click(button);

    expect(document.getElementById(controls)).not.toBeNull();
  });

  it("開いている間にビューポートが640px以上になるとメニューを閉じてスクロールロックを解除する", () => {
    let changeHandler: (() => void) | undefined;
    const mql = {
      matches: false,
      addEventListener: (_event: string, handler: () => void) => {
        changeHandler = handler;
      },
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation(() => mql)
    );

    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    expect(document.body.style.overflow).toBe("hidden");

    mql.matches = true;
    act(() => {
      changeHandler?.();
    });

    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
    expect(document.body.style.overflow).toBe("");
  });
});
