import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "このサイトについて",
  description:
    "Ankardo の目的、安全性の方針、掲載しているゲーム、運営者と連絡先について。",
};

const CONTACT_FORM_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLScr21ghCZcOtjrM7LM7QvcnM7hYjWjGE45Gu1TroNXlrFqFPg/viewform";
const GITHUB_URL = "https://github.com/akabee0161";

export default function About() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-extrabold text-neutral-900">このサイトについて</h1>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">Ankardo とは</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          Ankardo は、小さな子供が安心して遊べるゲームを集めたカタログサイトです。ブラウザですぐに遊べるゲームだけを掲載しています。
        </p>
        <p className="mt-3 text-sm leading-relaxed text-neutral-600">
          ゲームは対象年齢・ジャンル・対応デバイスを添えて紹介しています。対象年齢は目安で、遊べる下限を示すものではありません。対応デバイスは、そのゲームが快適に遊べる環境（PC、スマートフォンの縦向き・横向き）を表します。
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">安全性について</h2>
        <ul className="mt-2 list-disc pl-5 text-sm leading-relaxed text-neutral-600">
          <li>広告・課金・アカウント登録はありません。</li>
          <li>
            ゲームの記録（ハイスコアなど）は、お使いの端末の中にのみ保存されます。サーバーへは送信されません。
          </li>
          <li>
            アクセス解析を行う場合も、個人を特定しない集計のみで、Cookie は使いません。
          </li>
        </ul>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">掲載しているゲームについて</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          掲載しているゲームは、すべて運営者本人が制作しています。第三者から募集した作品は掲載していません。
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">運営者と連絡先</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          個人で制作・運営しています。ソースコードは{" "}
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-brand underline"
          >
            GitHub
          </a>
          で公開しています。
        </p>
        <p className="mt-3 text-sm leading-relaxed text-neutral-600">
          ご意見・ご質問・不具合の報告は、
          <a
            href={CONTACT_FORM_URL}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-brand underline"
          >
            お問い合わせフォーム
          </a>
          からお寄せください。
        </p>
      </section>
    </main>
  );
}
