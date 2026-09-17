import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import os from "node:os";

// 运行实际 Vue DOM 与生产代理的离线测试，证据来自断言通过后的观测。
const workspace = fileURLToPath(new URL("../", import.meta.url));
const outputIndex = process.argv.indexOf("--output");
const output = resolve((outputIndex >= 0 ? process.argv[outputIndex + 1] : undefined) || "../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-pc-performance.json");
const temporary = `${output}.observations.tmp`;
mkdirSync(dirname(output), { recursive: true });
try {
  // 子进程使用当前 Node，不依赖平台 shell 或系统 npm 命令别名。
  execFileSync(process.execPath, ["node_modules/vitest/vitest.mjs", "run", "test/controlStatusPerformance.test.ts"], {
    cwd: workspace,
    env: { ...process.env, ROBER_PC_PERFORMANCE_OUTPUT: temporary },
    stdio: "inherit",
  });
  const after = JSON.parse(readFileSync(temporary, "utf8"));
  // 基线为改动前真实执行两个 builder 的 fake-fetch 计数，明确排除实机含义。
  const baseline = JSON.parse(readFileSync(new URL("../../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-pc-baseline.json", import.meta.url), "utf8"));
  // 保存锁定依赖的实际运行版本，让其他主机能复现同一套软件证据。
  const packages = Object.fromEntries(["vue", "vitest", "vite", "jsdom"].map((name) => [name,
    JSON.parse(readFileSync(resolve(workspace, "node_modules", name, "package.json"), "utf8")).version,
  ]));
  const result = {
    schema: "trashbot.pc_control_status_performance.v1",
    captured_at: new Date().toISOString(),
    environment: { node: process.version, platform: process.platform, arch: process.arch, os: os.release(), packages },
    injection: "jsdom Vue mount + deferred fake fetch + fake WebRTC; zero hardware/network",
    evidence_boundary: "software_mock_only; structural counts; no physical latency or CPU claim",
    baseline, after,
  };
  let artifact = result;
  // 计划中的统一出口必须重跑手机场景，避免把历史 JSON 拼装为本轮证据。
  if (basename(output) === "ui-performance.json") {
    execFileSync(process.execPath, ["--test", resolve(workspace, "../../mobile/web/test_mobile_performance.mjs")], {
      cwd: workspace,
      stdio: "inherit",
    });
    // 手机测试只在固定 sprint 写入结果，任意 --output 仍读取同一真实执行产物。
    const mobile = JSON.parse(readFileSync(new URL("../../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-mobile-performance.json", import.meta.url), "utf8"));
    artifact = {
      schema: "trashbot.control_status_ui_performance.v1",
      captured_at: new Date().toISOString(),
      // 两端分别保留环境、基线和观测范围，禁止合并成不明来源的延迟数值。
      pc: result,
      mobile,
      evidence_boundary: "software_mock_only; structural counts; no physical latency or CPU claim",
      // 聚合成功仅表示两个离线验收进程都通过，不提高实机证明等级。
      hardware_or_deployment_executed: false,
    };
  }
  // 两端断言通过后才写统一产物；独立 ui-pc 输出仍仅包含 PC 结构。
  writeFileSync(output, `${JSON.stringify(artifact, null, 2)}\n`);
  console.log(`UI performance evidence: ${output}`);
} finally {
  rmSync(temporary, { force: true });
}
