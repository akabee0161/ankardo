import { describe, expect, it } from "vitest";
import robots from "./robots";

describe("robots", () => {
  it("全クローラーに全パスを許可し、サイトマップの場所を示す", () => {
    expect(robots()).toEqual({
      rules: { userAgent: "*", allow: "/" },
      sitemap: "https://ankardo.com/sitemap.xml",
    });
  });
});
