import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import { PROOF_FLAGS } from "../src/shared/contracts";

const fixtures: Record<string, unknown> = {
  "/api/health": {
    schema: "trashbot.pc_tools_workstation.health.v1",
    version: "0.2.0",
    mode: "pc_only_readonly_workstation",
    api_routes: [],
    ...PROOF_FLAGS,
  },
  "/api/route/debug-summary": {
    schema: "trashbot.pc_tools_workstation.route_debug_summary.v2",
    route_root: "pc-tools/route",
    node_route_json_loader: {
      name: "node_route_json_loader",
      implementation: "pc-tools/workstation/src/server/routeDebugLoader.ts",
      accepts_local_json: true,
      executes_control: false,
    },
    route_console_summary: {
      schema: "trashbot.pc_route_debug_console.v1",
      evidence_boundary: "software_proof_docker_pc_route_debug_console_gate",
      route_progress: null,
      keyframe_preflight: null,
      current_position: null,
      current_checkpoint: null,
      target: null,
      match_status: "not_loaded_pc_only",
      failure: {
        status: "blocked_not_proven",
        blocked_reasons: ["status_json_not_provided"],
        fail_closed_conditions: ["bad_json", "success_or_control_claim"],
      },
      recent_task: null,
      route_elevator_reconciliation: {
        lookup_status: "not_executed_by_workstation",
        evidence_boundary: "software_proof_docker_pc_route_elevator_console_integration_gate",
        delivery_success: false,
        primary_actions_enabled: false,
      },
      not_proven: ["real_ros2_runtime", "delivery_success"],
      delivery_success: false,
      primary_actions_enabled: false,
      console_controls: "read_only",
    },
    missing_fields: ["real_nav2_runtime"],
    blocked_reasons: ["status_json_not_provided"],
    input_status: {
      statusJson: "not_provided",
      taskRecord: "not_provided",
      taskRecordDir: "not_provided",
      elevatorRouteReconciliation: "not_provided",
    },
    ...PROOF_FLAGS,
  },
  "/api/tools/evidence": {
    schema: "trashbot.pc_tools_workstation.evidence_tools.v2",
    fixture_root: "pc-tools/evidence/fixtures",
    total_asset_groups: 1,
    total_json_fixtures: 2,
    categories: { "route evidence": 2 },
    assets: [
      {
        group: "route_task_completion_signal",
        category: "route evidence",
        fixture_count: 2,
        fixture_files: [
          "pc-tools/evidence/fixtures/route_task_completion_signal/pass/input.json",
          "pc-tools/evidence/fixtures/route_task_completion_signal/fail/input.json",
        ],
        summary: "JSON fixture index; software proof only; no field success implied.",
      },
    ],
    ...PROOF_FLAGS,
  },
  "/api/tools/training-labeling": {
    schema: "trashbot.pc_tools_workstation.training_labeling.v1",
    entries: [{ name: "training", path: "pc-tools/training", status: "placeholder_not_connected", real_pipeline_connected: false }],
    ...PROOF_FLAGS,
  },
  "/api/proof-boundary": {
    schema: "trashbot.pc_tools_workstation.proof_boundary.v2",
    can_prove: ["Node/Vue workstation can index local JSON fixtures under pc-tools/evidence/fixtures"],
    not_proven: ["real_ros2_runtime", "delivery_success"],
    enforced_fields: PROOF_FLAGS,
    control_policy: {
      workstation_executes_control: false,
      route_loader_mode: "local_json_readonly",
      recovery_path: "Load local JSON proof files in the Node workstation.",
    },
    ...PROOF_FLAGS,
  },
};

describe("App", () => {
  it("renders fail-closed Node route loader and evidence fixture index", async () => {
    // UI 测试只使用 API fixture，确保页面不自己发明机器人状态或旧执行入口。
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => ({
        ok: true,
        json: async () => fixtures[url],
      })),
    );

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("node_route_json_loader");
    expect(wrapper.text()).toContain("pc-tools/workstation/src/server/routeDebugLoader.ts");
    expect(wrapper.text()).toContain("safe_to_control=false");
    expect(wrapper.text()).toContain("delivery_success=false");
    expect(wrapper.text()).toContain("pc_only=true");
    expect(wrapper.text()).toContain("console_controls");
    expect(wrapper.text()).toContain("read_only");
    expect(wrapper.text()).toContain("status_json_not_provided");
    expect(wrapper.text()).not.toContain("route_debug_web.py");
    expect(wrapper.text()).not.toContain("python -m");
    expect(wrapper.text()).not.toContain("workstation_executes_python_gate");
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toContain("/dev/tty");
  });
});
