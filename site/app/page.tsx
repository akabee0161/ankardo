import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>Ankardo</h1>
      <p>子供向けインディーゲームのカタログサイトです。</p>
      <Link href="/games">ゲーム一覧を見る</Link>
    </main>
  );
}
