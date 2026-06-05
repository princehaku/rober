#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCHEMA = "trashbot.pc_tools_workstation.o7_direct_upper_browser_workflow.v1";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const runtimeRoot = path.join(workstationRoot, ".workstation-runtime");
const baseUrl = process.env.ROBER_WORKSTATION_BROWSER_URL || "http://127.0.0.1:8788/";
const outputPath = process.env.ROBER_O7_DIRECT_UPPER_BROWSER_EVIDENCE
  || path.join(runtimeRoot, "o7-direct-upper-browser-workflow.json");
const screenshotPath = process.env.ROBER_O7_DIRECT_UPPER_BROWSER_SCREENSHOT
  || path.join(runtimeRoot, "o7-direct-upper-browser-workflow.png");

function nowIso() {
  return new Date().toISOString();
}

function failClosedBase(blockedReason) {
  return {
    schema: SCHEMA,
    status: "fail_closed",
    executed_at: nowIso(),
    base_url: baseUrl,
    browser_plugin: "not_available",
    browser_engine: "chromium",
    page_identity: { url: "not_loaded", title: "not_loaded" },
    actions: [],
    network_calls: [],
    console_messages: [],
    screenshot_path: screenshotPath,
    blocked_reason: blockedReason,
    evidence_type: "browser_workflow_button_level",
    not_proven: ["pc_wasd_control", "hil_pass", "amcl", "nav2_consumption", "delivery_success"],
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

async function writeEvidence(result) {
  // 浏览器证据固定落 runtime 文件，便于 sprint 留档引用；它不改变任何机器人状态。
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ ...result, report_path: outputPath })}\n`);
}

function textSnippet(value) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, 900);
}

async function loadPlaywright() {
  // Playwright 是本项目 devDependency；缺依赖时输出 fail-closed JSON，而不是假装有浏览器证据。
  try {
    return await import("playwright");
  } catch {
    return null;
  }
}

async function main() {
  const playwright = await loadPlaywright();
  if (!playwright) {
    await writeEvidence(failClosedBase("playwright_dependency_unavailable"));
    process.exitCode = 1;
    return;
  }

  const consoleMessages = [];
  const networkCalls = [];
  const actions = [];
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  page.on("console", (message) => {
    // 只保留 console 摘要，避免把页面长对象或 SDP 一类调试文本写进证据。
    if (["error", "warning"].includes(message.type())) {
      consoleMessages.push(`${message.type()}:${message.text()}`.slice(0, 500));
    }
  });
  page.on("response", (response) => {
    const url = response.url();
    if (url.includes("/api/o7/direct-upper/")) {
      networkCalls.push({
        url,
        status: response.status(),
        method: response.request().method(),
      });
    }
  });

  try {
    await page.goto(baseUrl, { waitUntil: "networkidle", timeout: 30000 });
    await page.getByRole("heading", { name: "Rober 控制台" }).waitFor({ timeout: 15000 });
    await page.getByLabel("operator evidence ref").fill("o10-browser-button-workflow");
    await page.getByLabel("operator confirmation").check();

    const buttonFlow = [
      { label: "Refresh scan proof", expect: "/api/radar/scan-proof/refresh" },
      { label: "Read scan latest", expect: "/api/radar/scan-proof/latest" },
      { label: "Read map proof latest", expect: "/api/map/proof/latest" },
      { label: "Localize reset", expect: "/api/localize/reset" },
    ];

    for (const item of buttonFlow) {
      // 每个动作都从真实按钮触发，随后用 lock-message 证明 UI 收到反馈并保持 fail-closed。
      await page.getByRole("button", { name: item.label }).click({ timeout: 10000 });
      await page.getByText(item.expect, { exact: false }).waitFor({ timeout: 70000 });
      const statusText = await page.locator(".lock-message").innerText({ timeout: 5000 });
      actions.push({
        label: item.label,
        expected_remote_path: item.expect,
        status_text: textSnippet(statusText),
        safe_to_control_visible: statusText.includes("safe_to_control=false"),
        fail_closed_or_not_proven_visible: /失败|not_proven|仍锁定/.test(statusText),
      });
    }

    const bodyText = await page.locator("body").innerText();
    await page.screenshot({ path: screenshotPath, fullPage: true });
    const result = {
      schema: SCHEMA,
      status: actions.every((item) => item.safe_to_control_visible && item.fail_closed_or_not_proven_visible) ? "ok" : "fail_closed",
      executed_at: nowIso(),
      base_url: baseUrl,
      browser_plugin: "not_available",
      browser_engine: "chromium",
      page_identity: { url: page.url(), title: await page.title() },
      page_not_blank: bodyText.includes("Rober 控制台") && bodyText.includes("PC 本机 8787 接口"),
      framework_overlay_observed: /vite|webpack|next\.js/i.test(bodyText) && /error/i.test(bodyText),
      actions,
      network_calls: networkCalls,
      console_messages: consoleMessages,
      screenshot_path: screenshotPath,
      covered_entries: ["scan_proof_refresh", "scan_proof_latest", "map_proof_latest", "localize_reset"],
      evidence_type: "browser_workflow_button_level",
      not_proven: ["pc_wasd_control", "hil_pass", "amcl", "nav2_consumption", "delivery_success"],
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    };
    await writeEvidence(result);
    process.exitCode = result.status === "ok" ? 0 : 1;
  } catch (error) {
    await writeEvidence({
      ...failClosedBase(error instanceof Error ? error.message : "browser_workflow_failed"),
      page_identity: { url: page.url(), title: await page.title().catch(() => "not_loaded") },
      actions,
      network_calls: networkCalls,
      console_messages: consoleMessages,
    });
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

await main();
