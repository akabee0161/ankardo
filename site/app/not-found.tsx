import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ページが見つかりません",
};

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col items-center px-4 py-16 text-center">
      <h1 className="text-3xl font-extrabold text-neutral-900">
        ページが見つかりません
      </h1>
      <p className="mt-3 text-sm text-neutral-600">
        お探しのページは存在しないか、移動した可能性があります。
      </p>
      <Link
        href="/"
        className="mt-8 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
      >
        トップページに戻る
      </Link>
    </main>
  );
}
