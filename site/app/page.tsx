import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col items-center px-4 py-16 text-center">
      <h1 className="text-3xl font-extrabold text-neutral-900">Ankardo</h1>
      <p className="mt-3 text-sm text-neutral-600">
        子供向けインディーゲームのカタログサイトです。
      </p>
      <Link
        href="/games"
        className="mt-8 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
      >
        ゲーム一覧を見る
      </Link>
    </main>
  );
}
