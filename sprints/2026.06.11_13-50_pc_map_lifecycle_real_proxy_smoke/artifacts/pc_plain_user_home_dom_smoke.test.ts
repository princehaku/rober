import { flushPromises, mount } from "../../../pc-tools/workstation/node_modules/@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../../../pc-tools/workstation/src/App.vue";
import { PROOF_FLAGS } from "../../../pc-tools/workstation/src/shared/contracts";

const ARTIFACT_DIR = dirname(fileURLToPath(import.meta.url));
const FORBIDDEN_TOKENS = [
  "开始建图",
  "保存地图",
  "HIL",
  "proof",
  "Nav2",
  "/cmd_vel",
  "/api/base/manual",
  "task_id",
  "Mock",
  "检查路径",
] as const;

function fixtureFor(url: string): unknown {
  if (url.startsWith("/api/robot-control/summary")) {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_summary.v1",
      robot_api_connection: {
        status: "blocked",
        failed_count: 0,
        blocked_count: 1,
        dangerous_true_fields: [],
      },
      safe_command_boundary: {
        speed_limit_mps: 0.12,
        duration_limit_ms: 800,
      },
      operator_hil_material_summary: {
        status: "not_loaded",
        source_path: "operator_report_latest.structured_hil_claims",
      },
      readback_summary: {
        camera: { status: "not_loaded", devices_status: "not_loaded" },
        lidar: { status: "not_loaded", latest_scan_proof_status: "not_loaded", latest_raw_packet_proof_status: "not_loaded" },
        base: { status: "not_loaded", latest_feedback_status: "not_loaded" },
      },
      o3_proof_summary: {
        proof_status: "not_proven",
        delivery_success: false,
        primary_actions_enabled: false,
        root_causes: [],
        not_proven: ["baseUrl_not_provided"],
      },
      ...PROOF_FLAGS,
    };
  }
  return {
    schema: `trashbot.pc_tools_workstation.dom_stub.${url.replace(/[^a-z0-9]/gi, "_")}.v1`,
    api_routes: [],
    node_route_json_loader: {
      name: "node_route_json_loader",
      implementation: "pc-tools/workstation/src/server/routeDebugLoader.ts",
      accepts_local_json: true,
      executes_control: false,
    },
    route_console_summary: {
      schema: "trashbot.pc_route_debug_console.v1",
      evidence_boundary: "dom_smoke_stub",
      route_progress: null,
      keyframe_preflight: null,
      current_position: null,
      current_checkpoint: null,
      target: null,
      match_status: "not_loaded_pc_only",
      failure: {
        status: "blocked_not_proven",
        blocked_reasons: ["dom_smoke_stub"],
        fail_closed_conditions: [],
      },
      recent_task: null,
      route_elevator_reconciliation: {
        lookup_status: "not_executed_by_workstation",
        evidence_boundary: "dom_smoke_stub",
        delivery_success: false,
        primary_actions_enabled: false,
      },
      not_proven: ["dom_smoke_stub"],
      delivery_success: false,
      primary_actions_enabled: false,
      console_controls: "read_only",
    },
    missing_fields: [],
    blocked_reasons: [],
    input_status: {
      statusJson: "not_provided",
      taskRecord: "not_provided",
      taskRecordDir: "not_provided",
      elevatorRouteReconciliation: "not_provided",
    },
    categories: {},
    assets: [],
    ...PROOF_FLAGS,
  };
}

function visiblePlainHomeText(wrapper: ReturnType<typeof mount>): string {
  return [
    wrapper.find(".topbar").text(),
    wrapper.find(".simple-user-console").text(),
  ].join("\n");
}

describe("pc plain user home DOM smoke artifact", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("keeps the ordinary first screen simple while retaining advanced diagnostics offscreen", async () => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      calls.push(url);
      return {
        ok: true,
        status: 200,
        json: async () => fixtureFor(url),
      };
    }));

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = visiblePlainHomeText(wrapper);
    const diagnosticsText = wrapper.find(".advanced-details").text();
    const cardTitles = wrapper.findAll(".simple-user-console h3").map((node) => node.text());
    const forbiddenTokenPresence = Object.fromEntries(
      FORBIDDEN_TOKENS.map((token) => [token, firstScreenText.includes(token)]),
    );
    const result = {
      schema: "trashbot.pc_workstation.plain_user_home_dom_smoke.v1",
      checked_at: new Date().toISOString(),
      first_screen_title_present: firstScreenText.includes("Rober 小车控制台"),
      simple_user_console_exists: wrapper.find(".simple-user-console").exists(),
      first_screen_card_titles: cardTitles,
      expected_card_titles: ["小车连接", "实时画面", "雷达", "地图", "移动/导航"],
      forbidden_token_presence: forbiddenTokenPresence,
      first_screen_text_sample: firstScreenText.slice(0, 2000),
      advanced_diagnostics_closed_by_default: !wrapper.find(".advanced-details").attributes("open"),
      advanced_entries_retained: {
        start_mapping_advanced: diagnosticsText.includes("开始建图（高级）"),
        save_map: diagnosticsText.includes("保存地图"),
        map_list: diagnosticsText.includes("地图列表"),
        check_path: diagnosticsText.includes("检查路径（高级）"),
      },
      fetch_calls: calls,
    };
    mkdirSync(ARTIFACT_DIR, { recursive: true });
    writeFileSync(resolve(ARTIFACT_DIR, "pc_plain_user_home_dom_smoke.json"), `${JSON.stringify(result, null, 2)}\n`);

    expect(result.first_screen_title_present).toBe(true);
    expect(result.simple_user_console_exists).toBe(true);
    expect(cardTitles).toEqual(result.expected_card_titles);
    expect(Object.values(forbiddenTokenPresence)).toEqual(FORBIDDEN_TOKENS.map(() => false));
    expect(result.advanced_diagnostics_closed_by_default).toBe(true);
  });
});
