// 共通素材の一覧（public/chiiku/items.json）を読む。知育ゲームで共通。ゲームごとの決まりを入れない。

export type Category = { key: string; label: string };

export type Item = {
  id: string;
  category: string;
  /** ふつうの書き方（「トマト」） */
  label: string;
  /** ひらがな（「とまと」）。字を出すゲームはこちらを使う */
  kana: string;
  /** 読み上げの文 */
  reading: string;
};

export type ItemsFile = { categories: Category[]; items: Item[] };

function fail(where: string, why: string): never {
  throw new Error(`items.json: ${where}: ${why}`);
}

function nonEmptyString(value: unknown, where: string): string {
  if (typeof value !== 'string' || value === '') {
    fail(where, `空でない文字列でない（${JSON.stringify(value)}）`);
  }
  return value;
}

/** 形が違えば、どの項目が違うかを示す Error を投げる。 */
export function parseItems(data: unknown): ItemsFile {
  if (typeof data !== 'object' || data === null) {
    fail('(全体)', 'オブジェクトでない');
  }
  const raw = data as { categories?: unknown; items?: unknown };

  if (!Array.isArray(raw.categories)) {
    fail('categories', '配列でない');
  }
  const categories: Category[] = raw.categories.map((c: unknown, i: number) => {
    if (typeof c !== 'object' || c === null) {
      fail(`categories[${i}]`, 'オブジェクトでない');
    }
    const entry = c as Record<string, unknown>;
    return {
      key: nonEmptyString(entry.key, `categories[${i}].key`),
      label: nonEmptyString(entry.label, `categories[${i}].label`),
    };
  });
  const keys = new Set(categories.map((c) => c.key));

  if (!Array.isArray(raw.items)) {
    fail('items', '配列でない');
  }
  const seen = new Set<string>();
  const items: Item[] = raw.items.map((v: unknown, i: number) => {
    if (typeof v !== 'object' || v === null) {
      fail(`items[${i}]`, 'オブジェクトでない');
    }
    const entry = v as Record<string, unknown>;
    const item: Item = {
      id: nonEmptyString(entry.id, `items[${i}].id`),
      category: nonEmptyString(entry.category, `items[${i}].category`),
      label: nonEmptyString(entry.label, `items[${i}].label`),
      kana: nonEmptyString(entry.kana, `items[${i}].kana`),
      reading: nonEmptyString(entry.reading, `items[${i}].reading`),
    };
    if (!keys.has(item.category)) {
      fail(`items[${i}].category`, `'${item.category}' が categories に無い`);
    }
    if (seen.has(item.id)) {
      fail(`items[${i}].id`, `'${item.id}' が重複している`);
    }
    seen.add(item.id);
    return item;
  });

  return { categories, items };
}

export async function loadItems(url: string): Promise<ItemsFile> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${url}: 読み込めない（HTTP ${res.status}）`);
  }
  return parseItems(await res.json());
}
