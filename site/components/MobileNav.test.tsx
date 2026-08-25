/**
 * @vitest-environment jsdom
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MobileNav } from "./MobileNav";

// next/link はクリック時に App Router のコンテキストを要求する。
// テストでは素の <a> に差し替えて、コンテキストなしでもクリックできるようにする。
vi.mock("next/link", () => ({
  default: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

afterEach(() => {
  cleanup();
  document.body.style.overflow = "";
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
});
