import { existsSync, readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { loadItems } from './assets';

// 写した直後は素材（public/chiiku/）が無い。実物の一覧を使う確認は、素材が入っているときだけ行う
const REAL_PATH = 'public/chiiku/items.json';
const HAS_REAL = existsSync(REAL_PATH);
const REAL_JSON = HAS_REAL ? readFileSync(REAL_PATH, 'utf-8') : '{}';

function stubFetch(body: string, init: { ok?: boolean; status?: number } = {}) {
  const fn = vi.fn(async () => ({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => JSON.parse(body),
  }));
  vi.stubGlobal('fetch', fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('loadItems', () => {
  it.skipIf(!HAS_REAL)('returns the 21 items and 5 categories of the real items.json', async () => {
    const fetchFn = stubFetch(REAL_JSON);
    const file = await loadItems('/play/game/chiiku/items.json');
    expect(fetchFn).toHaveBeenCalledWith('/play/game/chiiku/items.json');
    expect(file.items).toHaveLength(21);
    expect(file.categories.map((c) => c.key)).toEqual([
      'animal',
      'insect',
      'sea',
      'vegetable',
      'food',
    ]);
    expect(file.items[0]).toEqual({
      id: 'dog',
      category: 'animal',
      label: 'いぬ',
      kana: 'いぬ',
      reading: 'いぬ',
    });
  });

  it.skipIf(!HAS_REAL)('names the broken field: items[3].kana missing', async () => {
    const data = JSON.parse(REAL_JSON);
    data.items[3].kana = undefined; // JSON にすると、この項目は無くなる
    stubFetch(JSON.stringify(data));
    await expect(loadItems('/items.json')).rejects.toThrow('items[3].kana');
  });

  it.skipIf(!HAS_REAL)('names the broken field: category that is not in categories', async () => {
    const data = JSON.parse(REAL_JSON);
    data.items[5].category = 'nope';
    stubFetch(JSON.stringify(data));
    await expect(loadItems('/items.json')).rejects.toThrow('items[5].category');
  });

  it('rejects a file without items', async () => {
    stubFetch(JSON.stringify({ categories: [] }));
    await expect(loadItems('/items.json')).rejects.toThrow('items');
  });

  it('says which url and status failed', async () => {
    stubFetch('{}', { ok: false, status: 404 });
    await expect(loadItems('/missing.json')).rejects.toThrow(
      /404.*\/missing\.json|\/missing\.json.*404/,
    );
  });
});

// CI（deploy.yml の npm test）では、素材の入れ忘れを本番に出す前に止める。
// 写した直後の手元では、素材を入れる前でもテストが通るように、CI のときだけ確かめる
describe('素材（public/chiiku/）', () => {
  it.runIf(process.env.CI === 'true')(
    'CI では入っている（copy-assets.sh を流し忘れていない）',
    () => {
      expect(HAS_REAL, `${REAL_PATH} が無い。copy-assets.sh chiiku を流す`).toBe(true);
    },
  );
});
