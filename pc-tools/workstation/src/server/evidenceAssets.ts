import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type { EvidenceFixtureRecord, EvidenceToolsResponse } from "../shared/contracts";
import { displayRoot, EVIDENCE_FIXTURE_ROOT } from "./paths";

const CATEGORY_RULES: Array<[string, string]> = [
  // 分类只用于 reviewer 扫描，不参与 pass/fail 或现场证明判定。
  ["wave_rover", "hardware evidence"],
  ["hardware", "hardware evidence"],
  ["cloud", "cloud evidence"],
  ["mobile", "mobile evidence"],
  ["phone", "mobile evidence"],
  ["route", "route evidence"],
  ["elevator", "route evidence"],
  ["field", "field evidence"],
  ["terminal", "terminal evidence"],
];

function classifyAsset(name: string): string {
  // 分组名来自 fixture 目录，不能推断真实硬件或线路状态。
  const normalized = name.toLowerCase();
  return CATEGORY_RULES.find(([needle]) => normalized.includes(needle))?.[1] ?? "general evidence";
}

async function listJsonFixtures(root: string): Promise<string[]> {
  // 缺目录时返回空索引而不是抛 500，调用方继续保留 not_proven 语义。
  try {
    const entries = await fs.readdir(root, { withFileTypes: true });
    const nested = await Promise.all(
      entries.map(async (entry) => {
        const absPath = path.join(root, entry.name);
        if (entry.isDirectory()) {
          return listJsonFixtures(absPath);
        }
        return entry.isFile() && entry.name.endsWith(".json") ? [absPath] : [];
      }),
    );
    return nested.flat().sort((left, right) => left.localeCompare(right));
  } catch {
    return [];
  }
}

async function readableJsonCount(files: string[]): Promise<number> {
  // 读取并解析 JSON 是为了证明 fixture 索引可读，但不把内容搬进 API 响应。
  const results = await Promise.all(
    files.map(async (file) => {
      try {
        JSON.parse(await fs.readFile(file, "utf8"));
        return 1;
      } catch {
        return 0;
      }
    }),
  );
  return results.reduce<number>((sum, value) => sum + value, 0);
}

function groupFromFixture(file: string): string {
  // fixtures 下一级目录是证据主题；根目录散落 JSON 时归入 root。
  const relative = path.relative(EVIDENCE_FIXTURE_ROOT, file).split(path.sep);
  return relative.length > 1 ? (relative[0] ?? "root") : "root";
}

export async function buildEvidenceToolsResponse(): Promise<EvidenceToolsResponse> {
  // Evidence Tools 不再扫描 .py，不读取 docstring，也不保留旧 gate 执行语义。
  const fixtures = await listJsonFixtures(EVIDENCE_FIXTURE_ROOT);
  const groups = fixtures.reduce<Record<string, string[]>>((acc, file) => {
    const group = groupFromFixture(file);
    acc[group] = [...(acc[group] ?? []), displayRoot(file)];
    return acc;
  }, {});

  const assets: EvidenceFixtureRecord[] = Object.entries(groups)
    .map(([group, files]) => ({
      group,
      category: classifyAsset(group),
      fixture_count: files.length,
      fixture_files: files.sort((left, right) => left.localeCompare(right)),
      summary: "JSON fixture index; software proof only; no field success implied.",
    }))
    .sort((left, right) => left.group.localeCompare(right.group));

  const categories = assets.reduce<Record<string, number>>((acc, asset) => {
    // 分类计数帮助 reviewer 扫描 fixture 主题，不代表通过数量。
    acc[asset.category] = (acc[asset.category] ?? 0) + asset.fixture_count;
    return acc;
  }, {});

  return {
    schema: "trashbot.pc_tools_workstation.evidence_tools.v2",
    ...PROOF_FLAGS,
    fixture_root: displayRoot(EVIDENCE_FIXTURE_ROOT),
    total_asset_groups: assets.length,
    total_json_fixtures: await readableJsonCount(fixtures),
    categories,
    assets,
  };
}
