import { flushPromises, mount } from "../../../../pc-tools/workstation/node_modules/@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "../../../../pc-tools/workstation/node_modules/vitest/dist/index.js";
import RobotControlConsolePanel from "../../../../pc-tools/workstation/src/components/RobotControlConsolePanel.vue";

const artifactDir = resolve(process.cwd(), "../../sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/dom_smoke");
const summaryArtifact = resolve(process.cwd(), "../../sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/pc_proxy/summary_readback_after_refresh.json");

// 这里只检查 CEO 点名的首屏红线词，避免把高级诊断里的工程词误判成首屏泄漏。
const forbiddenTokens = [
  "HIL",
  "proof",
  "Nav2",
  "/cmd_vel",
  "/api/base/manual",
  "task_id",
  "Mock",
  "检查路径",
] as const;

describe("plain user console DOM smoke", () => {
  it("keeps the default first screen simple", async () => {
    // 使用本轮真实 PC proxy summary 作为后端 fixture，保证 DOM smoke 和本轮证据链一致。
    const summary = JSON.parse(readFileSync(summaryArtifact, "utf8"));
    const mockedFetch = vi.fn(async (url: string) => {
      // 组件初次挂载只需要 summary；其他 endpoint 若被误触发应直接失败，防止 smoke 掩盖额外动作。
      if (url.startsWith("/api/robot-control/summary")) {
        return { ok: true, json: async () => summary.body };
      }
      return { ok: false, status: 404, json: async () => ({ failure_reason: "unexpected_fetch" }) };
    });
    vi.stubGlobal("fetch", mockedFetch);

    const wrapper = mount(RobotControlConsolePanel);
    await flushPromises();
    await wrapper.vm.$nextTick();

    // `.simple-user-console` 是普通用户默认可见范围，工程入口必须留在关闭的 details 内。
    const simpleConsole = wrapper.find(".simple-user-console");
    const titleText = wrapper.find(".section-head h2").text();
    const cardTitles = wrapper.findAll(".robot-console-grid > .snapshot-panel h3").map((node) => node.text());
    const visibleFirstScreenText = [wrapper.find(".section-head").text(), simpleConsole.text()].join("\n");
    const forbiddenTokenPresence = Object.fromEntries(forbiddenTokens.map((token) => [token, visibleFirstScreenText.includes(token)]));
    const advancedDiagnostics = wrapper.find(".robot-console .advanced-details");

    // artifact 只保存短摘要，不复制高级区原文，避免把 debug 文案重新变成验收主证据。
    mkdirSync(artifactDir, { recursive: true });
    writeFileSync(resolve(artifactDir, "pc_plain_user_home_dom_smoke.json"), `${JSON.stringify({
      schema: "trashbot.pc_workstation.plain_user_home_dom_smoke.v1",
      checked_at: new Date().toISOString(),
      simple_user_console_exists: simpleConsole.exists(),
      title_text: titleText,
      first_screen_card_titles: cardTitles,
      expected_card_titles: ["小车连接", "实时画面", "雷达", "地图", "移动/导航"],
      forbidden_token_presence: forbiddenTokenPresence,
      all_forbidden_tokens_absent: Object.values(forbiddenTokenPresence).every((value) => value === false),
      advanced_diagnostics_closed_by_default: advancedDiagnostics.attributes("open") === undefined,
      fetch_calls: mockedFetch.mock.calls.map(([url]) => String(url)),
    }, null, 2)}\n`);

    expect(simpleConsole.exists()).toBe(true);
    expect(titleText).toBe("Rober 小车控制台");
    expect(cardTitles).toEqual(["小车连接", "实时画面", "雷达", "地图", "移动/导航"]);
    for (const token of forbiddenTokens) {
      expect(visibleFirstScreenText).not.toContain(token);
    }
    expect(advancedDiagnostics.attributes("open")).toBeUndefined();
  });
});
