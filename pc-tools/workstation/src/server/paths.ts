import path from "node:path";

// 路径模块集中管理仓库根和 pc-tools 目录，避免 server 各层各自推断。
export const REPO_ROOT = path.resolve(process.cwd(), "../..");
export const EVIDENCE_ROOT = path.join(REPO_ROOT, "pc-tools", "evidence");
export const EVIDENCE_FIXTURE_ROOT = path.join(EVIDENCE_ROOT, "fixtures");
export const ROUTE_ROOT = path.join(REPO_ROOT, "pc-tools", "route");

export function displayRoot(absPath: string): string {
  // API 只暴露仓库内相对路径，避免把本机盘符或用户目录泄露到 UI。
  return path.relative(REPO_ROOT, absPath).split(path.sep).join("/");
}
