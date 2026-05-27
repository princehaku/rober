import path from "node:path";
import { buildO7CloudArchiveTasks } from "./o7CloudArchiveTasks";
import type { O7CloudArchiveTasksResponse } from "../shared/contracts";

const DEMO_ARCHIVE_JSON = path.resolve(process.cwd(), "fixtures/o7/demo_archive.json");

export function o7DemoArchiveFixturePath(): string {
  // 固定 demo 路径避免前端传任意本机文件；真实数据仍走显式 archiveJson 输入。
  return DEMO_ARCHIVE_JSON;
}

export async function buildO7DemoArchive(): Promise<O7CloudArchiveTasksResponse> {
  // demo 复用 archive adapter 的安全扫描与 fixed false 字段，不另开一套控制语义。
  return buildO7CloudArchiveTasks({ archiveJson: o7DemoArchiveFixturePath() });
}
