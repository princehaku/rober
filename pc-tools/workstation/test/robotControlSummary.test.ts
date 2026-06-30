import { afterEach, describe, expect, it, vi } from "vitest";
import { buildRobotControlSummary } from "../src/server/robotControlSummary";

describe("robotControlSummary", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("explains when the PC page port is used as the robot API port", async () => {
    // 现场最容易把 7001 当小车 API；所有只读请求失败时必须先暴露端口口径，而不是误判成相机/雷达/Nav2 坏了。
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new Error("connect ECONNREFUSED 192.168.1.11:7001");
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:7001", null, null, {
      readbackTimeoutMs: 1,
    });

    expect(summary.robot_api_connection.loaded_count).toBe(0);
    expect(summary.robot_api_connection.failed_count).toBeGreaterThan(0);
    expect(summary.robot_api_connection.blocked_reasons).toContain("robot_api_port_7001_mismatch_use_8787");
    expect(summary.blocked_reasons).toContain("robot_api_port_7001_mismatch_use_8787");
    expect(summary.current_fact_plain).toContain("7001 是 PC 页面服务端口");
    expect(summary.current_fact_plain).toContain("192.168.1.11:8787");
  });

  it("exposes minimal precheck fields for same-window wheel rerun", async () => {
    // API 读数也要声明轮速复验只需要安全确认，不能让脚本误把相机/雷达 WYSIWYG 当成额外发车预检。
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input));
      const basePayload = {
        schema: "trashbot.upper_robot_api.v1.readback",
        status: "loaded",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        robot_control_executed: false,
      };
      const payloadByPath: Record<string, Record<string, unknown>> = {
        "/api/status": {
          ...basePayload,
          nav2_base_command_mode: "ros",
        },
        "/api/map/proof/latest": {
          ...basePayload,
          map_once_observed: true,
        },
        "/api/nav2/status": {
          ...basePayload,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          planner_server_active: false,
          controller_server_active: false,
          controller_server_requested: false,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 2,
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 1 },
          ],
          path_preview_frame_id: "map",
        },
        "/api/nav2/proof/latest": {
          ...basePayload,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 2,
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 1 },
          ],
          path_preview_frame_id: "map",
        },
        "/api/nav2/goal/execution/latest": {
          ...basePayload,
          status: "goal_succeeded",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            nav2_goal_execution_proven: true,
            base_command_mode: "pwm",
            base_command_summary: {
              nonzero_command_observed: true,
              nonzero_command_count: 3,
            },
            base_feedback_summary: {
              wheel_feedback_lr_nonzero_proven: false,
              sample_count: 2,
              nonzero_sample_count: 0,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
        },
      };
      const payload = payloadByPath[url.pathname] ?? basePayload;
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });

    expect(summary.live_closure_summary?.status).toBe("needs_wheel_rerun");
    expect(summary.live_closure_summary?.needs_same_window_wheel_rerun).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_camera_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_radar_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_route_wysiwyg_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_command_mode).toBe("ros");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.live_closure_summary?.keyboard_continuous_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_enable_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.keyboard_continuous_hold_to_move_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_pulse_interval_ms).toBe(260);
    expect(summary.live_closure_summary?.keyboard_continuous_pulse_duration_ms).toBe(240);
    expect(summary.live_closure_summary?.keyboard_continuous_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.live_closure_summary?.keyboard_continuous_wheel_feedback_acceptance).toBe("same_hold_window_wheel_lr_nonzero");
    expect(summary.live_closure_summary?.fixed_keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.live_closure_summary?.fixed_keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
  });

  it("separates free movement from mapping sensor readiness in live closure", async () => {
    // 自由移动只要安全确认和停止兜底；相机/雷达缺口只能阻塞建图启动，不能冒充移动前置。
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input));
      const basePayload = {
        schema: "trashbot.upper_robot_api.v1.readback",
        status: "loaded",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        robot_control_executed: false,
      };
      const payloadByPath: Record<string, Record<string, unknown>> = {
        "/api/free-roam/autonomy/latest": {
          ...basePayload,
          latest_result: {
            decision: {
              state: "ready",
              reason: "operator_can_start_low_speed_free_move",
              gates: [
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "stop endpoint ready", next_action: "继续监看" },
                { id: "camera_first_frame", label: "画面首帧", state: "not_proven", evidence: "画面首帧未出", next_action: "检查画面" },
                { id: "lidar_fresh", label: "雷达新鲜", state: "not_proven", evidence: "雷达最新扫描未刷新", next_action: "先刷新雷达" },
              ],
            },
            snapshot: {
              external_stop_requested: false,
              mapping_active: false,
            },
            cmd_vel_publish_enabled: false,
          },
        },
      };
      const payload = payloadByPath[url.pathname] ?? basePayload;
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });

    expect(summary.live_closure_summary?.free_move_start_ready).toBe(true);
    expect(summary.live_closure_summary?.free_move_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.free_move_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.free_move_camera_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.free_move_radar_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.free_move_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.free_move_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.fixed_free_roam_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
    expect(summary.live_closure_summary?.fixed_free_roam_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
    expect(summary.live_closure_summary?.mapping_start_ready).toBe(false);
    expect(summary.live_closure_summary?.mapping_start_requires_camera_first_frame).toBe(true);
    expect(summary.live_closure_summary?.mapping_start_requires_lidar_fresh).toBe(true);
    expect(summary.live_closure_summary?.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.live_closure_summary?.mapping_acceptance_missing_reasons).toEqual([
      "camera_first_frame",
      "lidar_fresh",
      "mapping_active",
      "fresh_map_preview",
    ]);
    expect(summary.live_closure_summary?.fixed_mapping_start_endpoint).toBe("/api/robot-control/map/start");
    expect(summary.live_closure_summary?.fixed_mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
  });
});
