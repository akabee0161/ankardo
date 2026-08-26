export type NavLink = {
  href: string;
  label: string;
};

export const NAV_LINKS: NavLink[] = [
  { href: "/games", label: "ゲーム一覧" },
  { href: "/about", label: "このサイトについて" },
];

export const FOOTER_LINKS: NavLink[] = [
  { href: "/", label: "トップ" },
  ...NAV_LINKS,
];
