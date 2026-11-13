import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";

// ゲームのリポジトリへ写すプレビュー用ワークフローのひな形（正本）。
// 本番に出てしまう書き方（wrangler deploy、environment、develop 以外での実行、トークンの渡し方）を固定する。
// process.cwd() は site/
const TEMPLATE_PATH = path.join(process.cwd(), "..", ".claude", "skills", "new-game", "preview.yml");

type Step = { uses?: string; run?: string; env?: Record<string, string>; [key: string]: unknown };
type Workflow = {
  on: Record<string, unknown>;
  permissions: Record<string, string>;
  jobs: Record<string, { environment?: unknown; if?: string; steps: Step[] }>;
};

const raw = fs.readFileSync(TEMPLATE_PATH, "utf-8");
const workflow = parse(raw) as Workflow;
const job = workflow.jobs.preview;
const steps = job.steps;

describe("preview.yml（ひな形）", () => {
  it("先頭の行がひな形の版（# template-version: 1）である", () => {
    expect(raw.split("\n")[0]).toBe("# template-version: 1");
  });

  it("トリガーは develop への push と手動実行だけである", () => {
    expect(Object.keys(workflow.on).sort()).toEqual(["push", "workflow_dispatch"]);
    expect((workflow.on.push as { branches: string[] }).branches).toEqual(["develop"]);
  });

  it("権限は contents: read だけである", () => {
    expect(workflow.permissions).toEqual({ contents: "read" });
  });

  it("ジョブは environment を使わず、develop のときだけ動く", () => {
    expect(Object.keys(workflow.jobs)).toEqual(["preview"]);
    expect(job.environment).toBeUndefined();
    expect(job.if).toBe("github.ref == 'refs/heads/develop'");
  });

  it("本番に出すコマンドを実行しない（wrangler deploy・wrangler versions・wrangler-action）", () => {
    for (const step of steps) {
      expect(step.run ?? "").not.toMatch(/wrangler\s+(deploy|versions)/);
      expect(step.uses ?? "").not.toContain("wrangler-action");
    }
  });

  it("wrangler preview --name develop を実行するステップがちょうど 1 つある", () => {
    const previewSteps = steps.filter((s) => /wrangler\s+preview\s+--name\s+develop(\s|$)/.test(s.run ?? ""));
    expect(previewSteps).toHaveLength(1);
  });

  it("すべての uses が 40 桁の SHA で固定されている", () => {
    const uses = steps.map((s) => s.uses).filter((u): u is string => u !== undefined);
    expect(uses.length).toBeGreaterThan(0);
    for (const u of uses) {
      expect(u).toMatch(/@[0-9a-f]{40}$/);
    }
  });

  it("secrets を参照するのは、最後のステップの env だけである", () => {
    const last = steps[steps.length - 1];
    expect(last.run).toContain("wrangler preview");
    expect(JSON.stringify(last.env)).toContain("secrets.CLOUDFLARE_API_TOKEN");
    for (const step of steps.slice(0, -1)) {
      expect(JSON.stringify(step)).not.toContain("secrets.");
    }
    // 最後のステップでも、secrets は env 以外（run など）に書かない
    expect(JSON.stringify({ ...last, env: undefined })).not.toContain("secrets.");
  });
});
