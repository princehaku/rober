import { afterEach, describe, expect, it, vi } from "vitest";
import { buildMapPreviewProxy, buildRobotControlSummary } from "../src/server/robotControlSummary";

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
    expect(summary.status).toBe("needs_wheel_rerun");
    expect(summary.live_status).toBe("needs_wheel_rerun");
    expect(summary.live_closure_summary?.summary_plain).toBe(
      "当前卡点：图上路线已经有执行成功读数，但同窗口轮速 L/R 还没有非零闭环。",
    );
    expect(summary.summary_plain).toBe(summary.live_closure_summary?.summary_plain);
    expect(summary.live_closure_summary?.summary_plain).not.toContain("wheel raw");
    expect(summary.live_closure_summary?.next_action_plain).toBe(
      "勾现场安全确认后重跑图上路线，并在同一个执行窗口复验轮速 L/R 非零。",
    );
    expect(summary.next_action_plain).toBe(summary.live_closure_summary?.next_action_plain);
    expect(summary.live_closure_summary?.next_action_plain).not.toContain("wheel raw");
    expect(summary.live_closure_summary?.route_ready_on_map).toBe(true);
    expect(summary.route_ready).toBe(true);
    expect(summary.route_ready_on_map).toBe(true);
    expect(summary.live_closure_summary?.nav2_route_ready).toBe(true);
    expect(summary.nav2_route_ready).toBe(true);
    expect(summary.nav2_complete).toBe(true);
    expect(summary.nav2_goal_succeeded).toBe(true);
    expect(summary.nav2_goal_execution_proven).toBe(true);
    expect(summary.trip_execution_ready).toBe(true);
    expect(summary.trip_execution_complete).toBe(false);
    expect(summary.trip_execution_missing_evidence).toEqual(["same_window_wheel_lr_nonzero", "delivery_success"]);
    expect(summary.trip_execution_required_success_markers).toEqual([
      "map_route_visible",
      "nav2_goal_succeeded",
      "same_window_wheel_lr_nonzero",
      "delivery_success",
    ]);
    expect(summary.trip_execution_readback_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.route_complete).toBe(false);
    expect(summary.trip_complete).toBe(false);
    expect(summary.wheel_lr_nonzero).toBe(false);
    expect(summary.wheel_lr_nonzero_proven).toBe(false);
    expect(summary.wheel_feedback_same_window_complete).toBe(false);
    expect(summary.same_window_wheel_lr_nonzero_complete).toBe(false);
    expect(summary.needs_same_window_wheel_rerun).toBe(true);
    expect(summary.live_closure_summary?.camera_current_visible).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_visible).toBe(false);
    expect(summary.live_closure_summary?.map_current_visible).toBe(true);
    expect(summary.live_closure_summary?.path_current_visible).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_map_visible).toBe(true);
    expect(summary.live_closure_summary?.delivery_success_required).toBe(true);
    expect(summary.route_delivery_success).toBe(false);
    expect(summary.delivery_success_current).toBe(false);
    expect(summary.delivery_success_required).toBe(true);
    expect(summary.live_closure_summary?.delivery_next_action_plain).toContain("提交送达确认");
    expect(summary.delivery_next_action_plain).toContain("提交送达确认");
    expect(summary.live_closure_summary?.fixed_delivery_latest_endpoint).toBe("/api/robot-control/delivery/latest");
    expect(summary.fixed_delivery_latest_endpoint).toBe("/api/robot-control/delivery/latest");
    expect(summary.live_closure_summary?.fixed_delivery_complete_endpoint).toBe("/api/robot-control/delivery/complete");
    expect(summary.fixed_delivery_complete_endpoint).toBe("/api/robot-control/delivery/complete");
    expect(summary.live_closure_summary?.delivery_latest_readback_only).toBe(true);
    expect(summary.delivery_latest_readback_only).toBe(true);
    expect(summary.live_closure_summary?.delivery_complete_sends_motion).toBe(false);
    expect(summary.delivery_complete_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.primary_action_id).toBe("run_nav2_route");
    expect(summary.primary_action_id).toBe("run_nav2_route");
    expect(summary.live_closure_summary?.keyboard_continuous_ready).toBe(true);
    expect(summary.keyboard_continuous_ready).toBe(true);
    expect(summary.keyboard_ready).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_motion_verified).toBe(false);
    expect(summary.keyboard_continuous_motion_verified).toBe(false);
    expect(summary.live_closure_summary?.keyboard_continuous_forwarded_pulses).toBe(0);
    expect(summary.keyboard_enable_sends_motion).toBe(false);
    expect(summary.keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.objective_audit_status).toBe("in_progress");
    expect(summary.objective_audit_status).toBe("in_progress");
    expect(summary.live_closure_summary?.objective_audit_total_count).toBe(4);
    expect(summary.objective_audit_total_count).toBe(4);
    expect(summary.live_closure_summary?.objective_audit_done_count).toBeGreaterThanOrEqual(1);
    expect(summary.objective_audit_done_count).toBe(summary.live_closure_summary?.objective_audit_done_count);
    expect(summary.live_closure_summary?.objective_audit_remaining_count).toBeGreaterThan(0);
    expect(summary.objective_audit_remaining_count).toBe(summary.live_closure_summary?.objective_audit_remaining_count);
    expect(summary.objective_audit_next_objective_id).toBe(summary.live_closure_summary?.objective_audit_next_objective_id);
    expect(summary.live_closure_summary?.objective_audit_missing_objective_ids).toContain("motion");
    expect(summary.objective_audit_missing_objective_ids).toContain("motion");
    expect(summary.objective_missing_ids).toEqual(summary.live_closure_summary?.objective_audit_missing_objective_ids);
    expect(summary.objective_next_id).toBe(summary.live_closure_summary?.objective_audit_next_objective_id);
    expect(summary.motion_objective_complete).toBe(false);
    expect(summary.wysiwyg_objective_complete).toBe(false);
    expect(summary.precheck_objective_complete).toBe(true);
    expect(summary.mapping_objective_complete).toBe(false);
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("四项目标完成");
    expect(summary.objective_audit_summary_plain).toContain("四项目标完成");
    expect(summary.live_closure_summary?.fixed_objective_audit_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.fixed_objective_audit_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.objective_audit_sends_motion_when_clicked).toBe(false);
    expect(summary.objective_audit_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.objective_audit_items).toHaveLength(4);
    expect(summary.objective_audit_items).toHaveLength(4);
    const motionObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "motion");
    expect(motionObjective?.completed).toBe(false);
    expect(motionObjective?.actionable).toBe(true);
    expect(summary.motion_ready).toBe(true);
    expect(summary.motion_complete).toBe(false);
    expect(motionObjective?.item_ids).toEqual(["nav2_route_execution", "keyboard_continuous_control", "free_move"]);
    expect(motionObjective?.summary_plain).toContain("图上行程");
    expect(motionObjective?.sends_motion_when_clicked).toBe(false);
    const wysiwygObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "wysiwyg");
    expect(wysiwygObjective?.item_ids).toEqual(["camera_wysiwyg", "map_wysiwyg", "radar_map_points_wysiwyg"]);
    expect(summary.wysiwyg_ready).toBe(false);
    expect(summary.wysiwyg_complete).toBe(false);
    const precheckObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "precheck");
    expect(precheckObjective?.completed).toBe(true);
    expect(summary.precheck_ready).toBe(true);
    expect(summary.precheck_complete).toBe(true);
    const mappingObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "mapping");
    expect(mappingObjective?.summary_plain).not.toContain("camera_first_frame");
    expect(mappingObjective?.next_action_plain).not.toContain("camera_first_frame");
    expect(summary.mapping_ready).toBe(false);
    expect(summary.mapping_complete).toBe(false);
    expect(summary.live_closure_summary?.needs_same_window_wheel_rerun).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_camera_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_radar_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_route_wysiwyg_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.wheel_rerun_command_mode).toBe("ros");
    expect(summary.live_closure_summary?.wheel_rerun_last_base_command_mode).toBe("pwm");
    expect(summary.live_closure_summary?.wheel_rerun_next_base_command_mode).toBe("ros");
    expect(summary.live_closure_summary?.wheel_rerun_feedback_sample_count).toBe("2");
    expect(summary.live_closure_summary?.wheel_rerun_feedback_nonzero_sample_count).toBe("0");
    expect(summary.live_closure_summary?.wheel_rerun_latest_raw_left).toBe("0");
    expect(summary.live_closure_summary?.wheel_rerun_latest_raw_right).toBe("0");
    expect(summary.live_closure_summary?.wheel_rerun_mode_rerun_status).toBe("pending_ros_rerun_after_pwm");
    expect(summary.live_closure_summary?.wheel_rerun_mode_rerun_plain).toContain("PWM 模式");
    expect(summary.live_closure_summary?.wheel_rerun_next_mode_plain).toContain("ROS 模式");
    expect(summary.live_closure_summary?.wheel_rerun_base_command_nonzero_observed).toBe("true");
    expect(summary.live_closure_summary?.wheel_rerun_base_command_nonzero_count).toBe("3");
    expect(summary.live_closure_summary?.wheel_rerun_base_command_latest_nonzero_mode).toBe("pwm");
    expect(summary.live_closure_summary?.wheel_rerun_base_command_mode_counts).toBe("{\"pwm\":3}");
    expect(summary.live_closure_summary?.wheel_rerun_control_diagnosis_plain).toContain("3 次非零底盘命令");
    expect(summary.live_closure_summary?.wheel_rerun_control_diagnosis_plain).toContain("不是雷达、相机或地图所见缺口");
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("轮速 L/R=0/0");
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("样本 2 个");
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("非零样本 0 个");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("先勾现场安全确认");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("确认同窗口 wheel L/R 非零");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("送达确认");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_plain).toContain("goal_succeeded");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_plain).toContain("地图仍显示本轮图上路线");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_plain).toContain("送达确认与本轮行程材料对齐");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.wheel_rerun_ready_for_safety_confirm).toBe(true);
    expect(summary.wheel_rerun_ready_for_safety_confirm).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.wheel_rerun_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.live_closure_summary?.wheel_rerun_start_sends_motion).toBe(true);
    expect(summary.wheel_rerun_start_sends_motion).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_requires_safety_confirm).toBe(true);
    expect(summary.wheel_rerun_requires_safety_confirm).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_readback_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.wheel_rerun_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.wheel_rerun_acceptance_endpoints).toEqual(summary.live_closure_summary?.wheel_rerun_acceptance_endpoints);
    expect(summary.wheel_rerun_readback_endpoints).toEqual(summary.live_closure_summary?.wheel_rerun_readback_endpoints);
    expect(summary.live_closure_summary?.wheel_rerun_required_success_markers).toEqual([
      "map_route_visible",
      "nav2_goal_succeeded",
      "same_window_wheel_lr_nonzero",
      "delivery_success",
    ]);
    expect(summary.wheel_rerun_required_success_markers).toEqual(summary.live_closure_summary?.wheel_rerun_required_success_markers);
    expect(summary.live_closure_summary?.wheel_rerun_current_gap_plain).toContain("当前缺口");
    expect(summary.wheel_rerun_current_gap_plain).toContain("当前缺口");
    expect(summary.wheel_rerun_next_action_plain).toContain("先勾现场安全确认");
    expect(summary.wheel_rerun_acceptance_plain).toContain("同一执行窗口 wheel L/R 非零");
    expect(summary.live_closure_summary?.wheel_rerun_no_extra_precheck_plain).toContain("发车前预检只看现场安全确认");
    expect(summary.wheel_rerun_no_extra_precheck_plain).toContain("发车前预检只看现场安全确认");
    expect(summary.minimal_precheck_safety_only).toBe(true);
    expect(summary.safety_confirm_required_for_motion).toBe(true);
    expect(summary.live_motion_runbook_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_motion_runbook_safety_confirm_required).toBe(true);
    expect(summary.live_motion_runbook_minimal_precheck_plain).toBe(
      "发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。",
    );
    expect(summary.live_closure_summary?.wheel_rerun_delivery_success_required).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_delivery_next_action_plain).toContain("提交送达确认");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_latest_endpoint).toBe("/api/robot-control/nav2/goal/execution/latest");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_delivery_latest_endpoint).toBe("/api/robot-control/delivery/latest");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_delivery_complete_endpoint).toBe("/api/robot-control/delivery/complete");
    expect(summary.live_closure_summary?.wheel_rerun_delivery_complete_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.fixed_wheel_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.map_display_primary_tool).toBe("pc_big_map");
    expect(summary.map_display_primary_tool).toBe("pc_big_map");
    expect(summary.live_closure_summary?.map_display_primary_url).toBe("/map");
    expect(summary.map_display_primary_url).toBe("/map");
    expect(summary.live_closure_summary?.map_display_legacy_url).toBe("?view=map");
    expect(summary.map_display_legacy_url).toBe("?view=map");
    expect(summary.live_closure_summary?.map_display_primary_action_label).toBe("进入地图大屏");
    expect(summary.map_display_primary_action_label).toBe("进入地图大屏");
    expect(summary.live_closure_summary?.map_display_primary_action_opens_new_window).toBe(false);
    expect(summary.map_display_primary_action_opens_new_window).toBe(false);
    expect(summary.live_closure_summary?.map_display_primary_action_opens_current_page).toBe(true);
    expect(summary.map_display_primary_action_opens_current_page).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_default_observer).toBe(true);
    expect(summary.map_display_direct_map_default_observer).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_only).toBe(true);
    expect(summary.map_display_direct_map_only).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_viewport_priority).toBe("fullscreen_map_canvas");
    expect(summary.map_display_direct_map_viewport_priority).toBe("fullscreen_map_canvas");
    expect(summary.live_closure_summary?.map_display_direct_map_canvas_height_mode).toBe("viewport_dominant_full_height");
    expect(summary.map_display_direct_map_canvas_height_mode).toBe("viewport_dominant_full_height");
    expect(summary.live_closure_summary?.map_display_direct_map_keeps_page_fullscreen_without_browser_api).toBe(true);
    expect(summary.map_display_direct_map_keeps_page_fullscreen_without_browser_api).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_browser_fullscreen_required).toBe(false);
    expect(summary.map_display_direct_map_browser_fullscreen_required).toBe(false);
    expect(summary.live_closure_summary?.map_display_direct_map_refreshes_radar_scan_proof_on_enter).toBe(true);
    expect(summary.map_display_direct_map_refreshes_radar_scan_proof_on_enter).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_refreshes_map_preview_on_enter).toBe(true);
    expect(summary.map_display_direct_map_refreshes_map_preview_on_enter).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_refreshes_radar_status_on_enter).toBe(true);
    expect(summary.map_display_direct_map_refreshes_radar_status_on_enter).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_starts_radar_lifecycle_on_enter).toBe(false);
    expect(summary.map_display_direct_map_starts_radar_lifecycle_on_enter).toBe(false);
    expect(summary.live_closure_summary?.map_display_default_zoom_percent).toBe("2400%");
    expect(summary.map_display_default_zoom_percent).toBe("2400%");
    expect(summary.live_closure_summary?.map_display_max_zoom_percent).toBe("4800%");
    expect(summary.map_display_max_zoom_percent).toBe("4800%");
    expect(summary.live_closure_summary?.map_display_too_small_next_action_plain).toContain("进入地图大屏");
    expect(summary.live_closure_summary?.map_display_too_small_next_action_plain).toContain("/map");
    expect(summary.live_closure_summary?.map_display_too_small_next_action_plain).toContain("不需要先开 RViz2");
    expect(summary.map_display_too_small_next_action_plain).toBe(summary.live_closure_summary?.map_display_too_small_next_action_plain);
    expect(summary.live_closure_summary?.map_display_ros2_companion_answer_plain).toContain("RViz2");
    expect(summary.live_closure_summary?.map_display_ros2_companion_answer_plain).toContain("Foxglove bridge");
    expect(summary.live_closure_summary?.map_display_ros2_companion_answer_plain).toContain("PC 大地图");
    expect(summary.map_display_ros2_companion_answer_plain).toBe(summary.live_closure_summary?.map_display_ros2_companion_answer_plain);
    expect(summary.live_closure_summary?.map_display_ros2_companion_plain).toBe(summary.live_closure_summary?.map_display_ros2_companion_answer_plain);
    expect(summary.map_display_ros2_companion_plain).toBe(summary.live_closure_summary?.map_display_ros2_companion_plain);
    expect(summary.live_closure_summary?.map_display_operator_default_surface).toBe("pc_big_map_direct_view");
    expect(summary.map_display_operator_default_surface).toBe("pc_big_map_direct_view");
    expect(summary.live_closure_summary?.map_display_companion_replaces_pc_ui).toBe(false);
    expect(summary.map_display_companion_replaces_pc_ui).toBe(false);
    expect(summary.live_closure_summary?.map_display_wysiwyg_overlays).toEqual(["image", "route", "robot", "radar"]);
    expect(summary.map_display_wysiwyg_overlays).toEqual(["image", "route", "robot", "radar"]);
    expect(summary.live_closure_summary?.map_display_ros2_companion_required).toBe(false);
    expect(summary.map_display_ros2_companion_required).toBe(false);
    expect(summary.live_closure_summary?.map_display_ros2_companion_tools).toEqual(["rviz2", "foxglove"]);
    expect(summary.map_display_ros2_companion_tools).toEqual(["rviz2", "foxglove"]);
    expect(summary.live_closure_summary?.map_display_engineering_tools_visible_by_default).toBe(false);
    expect(summary.map_display_engineering_tools_visible_by_default).toBe(false);
    expect(summary.live_closure_summary?.map_display_engineering_tools_action_label).toBe("工程观察：RViz2 / Foxglove");
    expect(summary.map_display_engineering_tools_action_label).toBe("工程观察：RViz2 / Foxglove");
    expect(summary.live_closure_summary?.map_display_ordinary_user_tool).toBe("pc_big_map");
    expect(summary.map_display_ordinary_user_tool).toBe("pc_big_map");
    expect(summary.live_closure_summary?.map_display_rviz_role_plain).toContain("本地工程调试");
    expect(summary.map_display_rviz_role_plain).toContain("本地工程调试");
    expect(summary.live_closure_summary?.map_display_rviz_launch_command).toBe("ros2 launch ros2_trashbot_bringup rviz.launch.py");
    expect(summary.map_display_rviz_launch_command).toBe("ros2 launch ros2_trashbot_bringup rviz.launch.py");
    expect(summary.live_closure_summary?.map_display_foxglove_role_plain).toContain("远程浏览器大屏观察");
    expect(summary.map_display_foxglove_role_plain).toContain("远程浏览器大屏观察");
    expect(summary.live_closure_summary?.map_display_foxglove_bridge_package).toBe("foxglove_bridge");
    expect(summary.map_display_foxglove_bridge_package).toBe("foxglove_bridge");
    expect(summary.live_closure_summary?.map_display_foxglove_bridge_install_command).toBe("sudo apt install ros-humble-foxglove-bridge");
    expect(summary.map_display_foxglove_bridge_install_command).toBe("sudo apt install ros-humble-foxglove-bridge");
    expect(summary.live_closure_summary?.map_display_foxglove_bridge_launch_command).toBe("ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py");
    expect(summary.map_display_foxglove_bridge_launch_command).toBe("ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py");
    expect(summary.live_closure_summary?.map_display_foxglove_websocket_url).toBe("ws://192.168.1.11:8765");
    expect(summary.map_display_foxglove_websocket_url).toBe("ws://192.168.1.11:8765");
    expect(summary.live_closure_summary?.map_display_foxglove_web_app_url).toBe("https://studio.foxglove.dev");
    expect(summary.map_display_foxglove_web_app_url).toBe("https://studio.foxglove.dev");
    expect(summary.live_closure_summary?.map_display_ros2_observe_topics).toEqual([
      "/map",
      "/scan",
      "/tf",
      "/plan",
      "/local_plan",
      "/amcl_pose",
      "/global_costmap/costmap",
      "/local_costmap/costmap",
    ]);
    expect(summary.map_display_ros2_observe_topics).toEqual(summary.live_closure_summary?.map_display_ros2_observe_topics);
    expect(summary.live_closure_summary?.map_display_ros2_observe_motion_topics).toBe(false);
    expect(summary.map_display_ros2_observe_motion_topics).toBe(false);
    expect(summary.live_closure_summary?.map_display_ros2_observe_control_tools).toBe(false);
    expect(summary.map_display_ros2_observe_control_tools).toBe(false);
    expect(summary.live_closure_summary?.map_display_engineering_tools_sends_motion).toBe(false);
    expect(summary.map_display_engineering_tools_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("普通用户地图：进入 /map 使用 PC 大地图");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("默认 2400% 现场大图");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("适配");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("100% 全图");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("点“细节放大”可查看局部");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("最高 4800%");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("地图太小先点“进入地图大屏”");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("不需要先开 RViz2");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("普通用户仍默认使用 PC 大地图");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("ROS2 配套只作工程观察");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("打开 Foxglove Web");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("ws://192.168.1.11:8765");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("不提供 GoalTool");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("不发送底盘移动命令");
    expect(summary.live_closure_summary?.map_display_companion_plain).not.toContain("/cmd_vel");
    expect(summary.map_display_companion_plain).toBe(summary.live_closure_summary?.map_display_companion_plain);
    expect(summary.live_closure_summary?.map_display_sends_motion_when_clicked).toBe(false);
    expect(summary.map_display_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_ros2).toBe(false);
    expect(summary.map_display_starts_ros2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_rviz2).toBe(false);
    expect(summary.map_display_starts_rviz2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_foxglove).toBe(false);
    expect(summary.map_display_starts_foxglove).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_nav2).toBe(false);
    expect(summary.map_display_starts_nav2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_map_runtime).toBe(false);
    expect(summary.map_display_starts_map_runtime).toBe(false);
    expect(summary.live_closure_summary?.primary_status_item_id).toBe("nav2_route_execution");
    expect(summary.live_closure_summary?.side_blocker_ids).toEqual([
      "camera_wysiwyg",
      "radar_map_points_wysiwyg",
      "mapping_start",
    ]);
    expect(summary.live_closure_summary?.side_blocker_count).toBe(3);
    expect(summary.live_closure_summary?.ready_action_ids).toEqual([
      "nav2_route_execution",
      "keyboard_continuous_control",
      "free_move",
    ]);
    expect(summary.live_closure_summary?.ready_action_count).toBe(3);
    expect(summary.live_closure_summary?.side_gap_summary_plain).toBe(
      "其它缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图；可先做：重跑图上行程并复验轮速、键盘连续手控、自由自助移动。",
    );
    expect(summary.live_closure_summary?.live_wysiwyg_ready).toBe(false);
    expect(summary.live_wysiwyg_ready).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toEqual(["camera", "radar_map_points"]);
    expect(summary.live_wysiwyg_missing_surface_ids).toEqual(["camera", "radar_map_points"]);
    expect(summary.live_wysiwyg_missing_reasons).toEqual(["camera", "radar_map_points"]);
    expect(summary.live_wysiwyg_only_camera_missing).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_needs_refresh).toBe(true);
    expect(summary.live_wysiwyg_needs_refresh).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_readback_gap_surface_ids).toEqual([]);
    expect(summary.live_wysiwyg_readback_gap_surface_ids).toEqual([]);
    expect(summary.live_closure_summary?.live_wysiwyg_primary_readback_gap_surface_id).toBe("none");
    expect(summary.live_wysiwyg_primary_readback_gap_surface_id).toBe("none");
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_endpoints).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/radar/scan-proof/refresh",
    ]);
    expect(summary.live_wysiwyg_missing_surface_refresh_endpoints).toEqual(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_endpoints);
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_labels).toEqual([
      "复测相机首帧",
      "刷新雷达扫描读数",
    ]);
    expect(summary.live_wysiwyg_missing_surface_refresh_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_labels);
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_wysiwyg_primary_refresh_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_label).toBe("复测相机首帧");
    expect(summary.live_wysiwyg_primary_refresh_label).toBe("复测相机首帧");
    expect(summary.live_wysiwyg_refresh_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_probe_failure_reason).toBe("none");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_not_exclusive).toBe("not_loaded");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_client_count).toBe("0");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_upstream_active).toBe("false");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_everyone_can_join).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_current_frame_visible).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_gap_plain).toContain("共享入口可加入");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_status).toBe("needs_probe");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain).toBe("先复测相机首帧并读取共享预览状态；拿到首帧后再刷新当前所见和建图条件。");
    expect(summary.live_closure_summary?.camera_first_frame_probe_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.camera_first_frame_failure_reason).toBe("none");
    expect(summary.live_closure_summary?.camera_source_diagnosis_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.camera_source_diagnosis_not_exclusive).toBe("not_loaded");
    expect(summary.live_closure_summary?.camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.live_closure_summary?.camera_usb_speed).toBe("not_loaded");
    expect(summary.live_closure_summary?.camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain);
    expect(summary.live_closure_summary?.fixed_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.fixed_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.camera_visible).toBe(false);
    expect(summary.camera_current_visible).toBe(false);
    expect(summary.live_wysiwyg_camera_visible).toBe(false);
    expect(summary.map_visible).toBe(true);
    expect(summary.map_current_visible).toBe(true);
    expect(summary.path_visible).toBe(true);
    expect(summary.path_current_visible).toBe(true);
    expect(summary.live_wysiwyg_map_visible).toBe(true);
    expect(summary.camera_source_diagnosis_status).toBe(summary.live_closure_summary?.camera_source_diagnosis_status);
    expect(summary.camera_source_diagnosis_not_exclusive).toBe(summary.live_closure_summary?.camera_source_diagnosis_not_exclusive);
    expect(summary.camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.camera_recovery_next_action_plain);
    expect(summary.camera_recovery_sends_motion).toBe(false);
    expect(summary.fixed_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.fixed_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.live_wysiwyg_camera_source_diagnosis_status).toBe(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_status);
    expect(summary.live_wysiwyg_camera_source_diagnosis_plain_hint).toBe(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_plain_hint);
    expect(summary.live_wysiwyg_camera_source_diagnosis_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_next_action_plain);
    expect(summary.live_wysiwyg_camera_source_diagnosis_not_exclusive).toBe(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_not_exclusive);
    expect(summary.live_wysiwyg_camera_shared_preview_client_count).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_client_count);
    expect(summary.live_wysiwyg_camera_shared_preview_upstream_active).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_upstream_active);
    expect(summary.live_wysiwyg_camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.live_wysiwyg_camera_shared_preview_everyone_can_join).toBe(true);
    expect(summary.live_wysiwyg_camera_shared_preview_current_frame_visible).toBe(false);
    expect(summary.live_wysiwyg_camera_shared_preview_gap_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_gap_plain);
    expect(summary.camera_shared_preview_endpoint).toBe("/api/robot-control/camera/mjpeg");
    expect(summary.camera_shared_preview_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.camera_shared_preview_single_upstream).toBe(true);
    expect(summary.camera_shared_preview_auto_joins).toBe(true);
    expect(summary.camera_shared_preview_everyone_can_join).toBe(true);
    expect(summary.camera_shared_preview_current_frame_visible).toBe(false);
    expect(summary.camera_shared_preview_gap_plain).toContain("不独占摄像头");
    expect(summary.camera_shared_preview_readback_only).toBe(true);
    expect(summary.camera_shared_preview_starts_camera_exclusive_capture).toBe(false);
    expect(summary.camera_shared_preview_sends_motion).toBe(false);
    expect(summary.camera_shared_preview_shared_capture).toBe("true");
    expect(summary.camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.camera_shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
    expect(summary.camera_shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
    expect(summary.camera_shared_preview_multi_viewer_plain).toContain("谁打开页面都接入");
    expect(summary.camera_shared_preview_access_plain).toContain("不是页面独占");
    expect(summary.camera_shared_preview_realtime_plain).toContain("当前没有实时画面");
    expect(summary.camera_wysiwyg_recovery_status).toBe("needs_probe");
    expect(summary.camera_wysiwyg_recovery_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain);
    expect(summary.camera_wysiwyg_recovery_sequence).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence);
    expect(summary.camera_wysiwyg_recovery_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence_labels);
    expect(summary.live_wysiwyg_camera_recovery_status).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_status);
    expect(summary.live_wysiwyg_camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain);
    expect(summary.live_wysiwyg_camera_recovery_sequence).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence);
    expect(summary.live_wysiwyg_camera_recovery_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence_labels);
    expect(summary.live_wysiwyg_camera_recovery_sends_motion).toBe(false);
    expect(summary.camera_wysiwyg_recovery_readback_endpoints).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.camera_wysiwyg_recovery_readback_sequence_labels).toEqual([
      "复测相机首帧",
      "读取共享预览状态",
      "刷新当前卡点",
    ]);
    expect(summary.camera_wysiwyg_recovery_requires_hardware_action).toBe(false);
    expect(summary.camera_wysiwyg_recovery_hardware_action_label).toBe("复测相机首帧");
    expect(summary.camera_wysiwyg_recovery_requires_usb_fix).toBe(false);
    expect(summary.camera_wysiwyg_recovery_blocks_mapping_start).toBe(true);
    expect(summary.camera_wysiwyg_recovery_blocks_free_move).toBe(false);
    expect(summary.camera_wysiwyg_recovery_sends_motion).toBe(false);
    expect(summary.camera_wysiwyg_recovery_starts_map_runtime).toBe(false);
    expect(summary.camera_wysiwyg_recovery_source_diagnosis_status).toBe("not_loaded");
    expect(summary.camera_wysiwyg_recovery_source_not_exclusive).toBe("not_loaded");
    expect(summary.camera_wysiwyg_recovery_shared_preview_single_upstream).toBe(true);
    expect(summary.radar_visible).toBe(false);
    expect(summary.radar_points_visible).toBe(false);
    expect(summary.radar_ready).toBe(false);
    expect(summary.radar_fresh).toBe(false);
    expect(summary.radar_map_ready).toBe(false);
    expect(summary.radar_map_points_visible).toBe(false);
    expect(summary.radar_overlay_status).toBe(summary.live_closure_summary?.radar_overlay_status);
    expect(summary.radar_overlay_current_point_count).toBe(summary.live_closure_summary?.radar_overlay_current_point_count);
    expect(summary.radar_overlay_source_point_count).toBe(summary.live_closure_summary?.radar_overlay_source_point_count);
    expect(summary.radar_overlay_primary_blocked_reason).toBe(summary.live_closure_summary?.radar_overlay_primary_blocked_reason);
    expect(summary.radar_overlay_current_vs_source_plain).toBe(summary.live_closure_summary?.radar_overlay_current_vs_source_plain);
    expect(summary.radar_overlay_refresh_next_action_plain).toBe(summary.live_closure_summary?.radar_overlay_refresh_next_action_plain);
    expect(summary.radar_overlay_needs_refresh).toBe(true);
    expect(summary.radar_overlay_blocks_wysiwyg).toBe(true);
    expect(summary.radar_overlay_blocks_free_move).toBe(false);
    expect(summary.radar_overlay_wysiwyg_complete).toBe(false);
    expect(summary.radar_overlay_readback_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.radar_overlay_status_endpoint).toBe("/api/robot-control/radar/status");
    expect(summary.radar_overlay_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.radar_overlay_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.radar_overlay_recovery_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.fixed_radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.fixed_radar_overlay_map_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.radar_overlay_refresh_sends_motion).toBe(false);
    expect(summary.radar_overlay_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_closure_summary?.camera_recovery_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.camera_recovery_starts_map_runtime).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence_labels).toEqual([
      "复测相机首帧",
      "读取共享预览状态",
      "刷新当前卡点",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_scan_missing_observations).toEqual([]);
    expect(summary.live_closure_summary?.live_wysiwyg_map_radar_blocked_reasons).toEqual([
      "scan_preview_points_missing",
      "robot_pose_missing_for_map_radar_overlay",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_current_point_count).toBe("0");
    expect(summary.live_wysiwyg_radar_map_current_point_count).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_current_point_count);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_source_point_count).toBe("not_loaded");
    expect(summary.live_wysiwyg_radar_map_source_point_count).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_source_point_count);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_stale_source_points_suppressed).toBe(false);
    expect(summary.live_wysiwyg_radar_map_stale_source_points_suppressed).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_stale_source_points_suppressed);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_primary_blocked_reason).toBe("scan_preview_points_missing");
    expect(summary.live_wysiwyg_radar_map_primary_blocked_reason).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_primary_blocked_reason);
    expect(summary.live_wysiwyg_radar_map_overlay_status).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_overlay_status);
    expect(summary.live_wysiwyg_radar_map_current_vs_source_plain).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_current_vs_source_plain);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_next_action_plain).toContain("刷新雷达扫描读数");
    expect(summary.live_wysiwyg_radar_map_refresh_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_next_action_plain);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_wysiwyg_radar_map_refresh_sequence).toEqual(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "读取雷达状态",
      "刷新地图画面",
      "刷新总览",
    ]);
    expect(summary.live_wysiwyg_radar_map_refresh_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence_labels);
    expect(summary.live_closure_summary?.radar_overlay_needs_refresh).toBe(true);
    expect(summary.live_closure_summary?.radar_overlay_blocks_wysiwyg).toBe(true);
    expect(summary.live_closure_summary?.radar_overlay_blocks_free_move).toBe(false);
    expect(summary.live_closure_summary?.radar_overlay_recovery_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.radar_overlay_status).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_overlay_status);
    expect(summary.live_closure_summary?.radar_overlay_current_point_count).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_current_point_count);
    expect(summary.live_closure_summary?.radar_overlay_source_point_count).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_source_point_count);
    expect(summary.live_closure_summary?.radar_overlay_primary_blocked_reason).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_primary_blocked_reason);
    expect(summary.live_closure_summary?.radar_overlay_current_vs_source_plain).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_current_vs_source_plain);
    expect(summary.live_closure_summary?.radar_overlay_refresh_next_action_plain).toBe(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_next_action_plain);
    expect(summary.live_closure_summary?.fixed_radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.live_closure_summary?.fixed_radar_overlay_map_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.live_closure_summary?.radar_overlay_refresh_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.radar_overlay_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_diagnostic_plain).toContain("画面诊断：首帧未证明");
    expect(summary.live_wysiwyg_diagnostic_plain).toBe(summary.live_closure_summary?.live_wysiwyg_diagnostic_plain);
    expect(summary.live_closure_summary?.live_wysiwyg_diagnostic_plain).toContain("还差=地图缺雷达点；小车地图位置未读到");
    expect(summary.live_wysiwyg_camera_diagnostic_plain).toBe(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain);
    expect(summary.live_wysiwyg_radar_diagnostic_plain).toBe(summary.live_closure_summary?.live_wysiwyg_radar_diagnostic_plain);
    expect(summary.live_wysiwyg_map_radar_diagnostic_plain).toBe(summary.live_closure_summary?.live_wysiwyg_map_radar_diagnostic_plain);
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_radar_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.fixed_live_wysiwyg_radar_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.fixed_live_wysiwyg_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_map_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.fixed_live_wysiwyg_map_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_radar_status_endpoint).toBe("/api/robot-control/radar/status");
    expect(summary.fixed_live_wysiwyg_radar_status_endpoint).toBe("/api/robot-control/radar/status");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.fixed_live_wysiwyg_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_plan_available).toBe(true);
    expect(summary.live_wysiwyg_refresh_plan_available).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_wysiwyg_refresh_sequence).toEqual(summary.live_closure_summary?.live_wysiwyg_refresh_sequence);
    expect(summary.live_wysiwyg_focused_refresh_sequence).toEqual(summary.field_acceptance_wysiwyg_refresh_sequence);
    expect(summary.live_wysiwyg_focused_refresh_mode).toBe("all_wysiwyg");
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "读取雷达状态",
      "刷新地图画面",
      "复测相机首帧",
      "读取相机 MJPEG 状态",
      "刷新总览",
    ]);
    expect(summary.live_wysiwyg_refresh_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_refresh_sequence_labels);
    expect(summary.live_wysiwyg_focused_refresh_sequence_labels).toEqual(summary.field_acceptance_wysiwyg_refresh_sequence_labels);
    expect(summary.live_wysiwyg_focused_refresh_sends_motion).toBe(false);
    expect(summary.live_wysiwyg_focused_refreshes_radar_scan_proof).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_radar_status).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_map_preview).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_radar_scan_proof).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_map_preview).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_radar_status).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sends_motion).toBe(false);
    expect(summary.live_wysiwyg_refresh_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_nav2).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_nav2).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_manual).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_manual).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_keyboard).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_keyboard).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_free_roam).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_free_roam).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_map_runtime).toBe(false);
    expect(summary.live_wysiwyg_refresh_starts_map_runtime).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_surface_summaries).toEqual([
      expect.objectContaining({
        id: "camera",
        visible: false,
        readback_gap: false,
        completed: false,
        proof_status: "ready_to_refresh",
        missing_evidence: ["camera_current_frame_visible"],
        proof_plain: "画面未对齐；还差：当前页面画面帧。",
        fixed_refresh_endpoint: "/api/robot-control/camera/first-frame/probe",
        sends_motion_when_clicked: false,
      }),
      expect.objectContaining({
        id: "map",
        visible: true,
        readback_gap: false,
        completed: true,
        proof_status: "completed",
        missing_evidence: [],
        proof_plain: "地图已对齐：当前地图画面已显示。",
        fixed_refresh_endpoint: "/api/robot-control/map/preview",
        sends_motion_when_clicked: false,
      }),
      expect.objectContaining({
        id: "radar_map_points",
        visible: false,
        readback_gap: false,
        completed: false,
        proof_status: "ready_to_refresh",
        missing_evidence: ["scan_preview_points_missing", "robot_pose_missing_for_map_radar_overlay"],
        proof_plain: "雷达点未对齐；还差：地图缺雷达点、小车地图位置未读到。",
        fixed_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
        sends_motion_when_clicked: false,
      }),
    ]);
    expect(summary.live_wysiwyg_surface_summaries).toEqual(summary.live_closure_summary?.live_wysiwyg_surface_summaries);
    expect(summary.live_closure_summary?.keyboard_continuous_minimal_precheck_safety_only).toBe(true);
    expect(summary.keyboard_continuous_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_safety_confirm_required).toBe(true);
    expect(summary.keyboard_continuous_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_enable_sends_motion).toBe(false);
    expect(summary.keyboard_continuous_enable_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.keyboard_continuous_hold_to_move_required).toBe(true);
    expect(summary.keyboard_continuous_hold_to_move_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_pulse_interval_ms).toBe(260);
    expect(summary.keyboard_continuous_pulse_interval_ms).toBe(260);
    expect(summary.live_closure_summary?.keyboard_continuous_pulse_duration_ms).toBe(240);
    expect(summary.keyboard_continuous_pulse_duration_ms).toBe(240);
    expect(summary.live_closure_summary?.keyboard_continuous_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.keyboard_continuous_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.live_closure_summary?.keyboard_continuous_wheel_feedback_acceptance).toBe("same_hold_window_wheel_lr_nonzero");
    expect(summary.keyboard_continuous_wheel_feedback_acceptance).toBe("same_hold_window_wheel_lr_nonzero");
    expect(summary.live_closure_summary?.keyboard_ready).toBe(true);
    expect(summary.live_closure_summary?.keyboard_safety_confirm_required).toBe(true);
    expect(summary.keyboard_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_enable_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.keyboard_hold_to_move_required).toBe(true);
    expect(summary.keyboard_hold_to_move_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_pulse_interval_ms).toBe(260);
    expect(summary.keyboard_pulse_interval_ms).toBe(260);
    expect(summary.live_closure_summary?.keyboard_pulse_duration_ms).toBe(240);
    expect(summary.keyboard_pulse_duration_ms).toBe(240);
    expect(summary.live_closure_summary?.keyboard_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.keyboard_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.live_closure_summary?.keyboard_acceptance_plain).toContain("同一次按住窗口");
    expect(summary.keyboard_acceptance_plain).toContain("同一次按住窗口");
    expect(summary.live_closure_summary?.keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.live_closure_summary?.keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.live_closure_summary?.keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.keyboard_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.keyboard_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.fixed_keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.live_closure_summary?.fixed_keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.live_closure_summary?.fixed_keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.fixed_keyboard_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.fixed_keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.fixed_keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.fixed_keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.fixed_keyboard_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.keyboard_post_hold_readback_endpoints).toEqual([
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
    ]);
    expect(summary.keyboard_post_hold_readback_sequence_labels).toEqual(["复验键盘轮速采样", "刷新总览"]);
    expect(summary.live_closure_summary?.keyboard_continuous_post_hold_feedback_readback_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_post_hold_summary_refresh_required).toBe(true);
    expect(summary.keyboard_post_hold_feedback_readback_required).toBe(true);
    expect(summary.keyboard_post_hold_summary_refresh_required).toBe(true);
    expect(summary.keyboard_continuous_post_hold_feedback_readback_required).toBe(true);
    expect(summary.keyboard_continuous_post_hold_summary_refresh_required).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_action_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
      "start_mapping_when_sensors_ready",
    ]);
    expect(summary.live_motion_runbook_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_action_ids);
    expect(summary.live_closure_summary?.live_motion_runbook_ready_action_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
    ]);
    expect(summary.live_motion_runbook_ready_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_ready_action_ids);
    expect(summary.live_closure_summary?.live_motion_runbook_blocked_action_ids).toEqual([
      "start_mapping_when_sensors_ready",
    ]);
    expect(summary.live_motion_runbook_blocked_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_blocked_action_ids);
    expect(summary.live_closure_summary?.live_motion_runbook_primary_action_id).toBe("run_nav2_route");
    expect(summary.live_motion_runbook_primary_action_id).toBe("run_nav2_route");
    expect(summary.live_closure_summary?.live_motion_runbook_start_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execute",
      "/api/robot-control/base/manual",
      "/api/robot-control/free-roam/autonomy/start",
    ]);
    expect(summary.live_motion_runbook_start_endpoints).toEqual(summary.live_closure_summary?.live_motion_runbook_start_endpoints);
    expect(summary.live_closure_summary?.live_motion_runbook_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
      "/api/robot-control/free-roam/autonomy/latest",
    ]);
    expect(summary.live_motion_runbook_acceptance_endpoints).toEqual(summary.live_closure_summary?.live_motion_runbook_acceptance_endpoints);
    expect(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_motion_runbook_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_safety_confirm_required).toBe(true);
    expect(summary.live_motion_runbook_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_ready_plain).toBe(
      "可先执行：重跑图上行程并复验轮速、键盘连续手控、自由自助移动。",
    );
    expect(summary.live_motion_runbook_ready_plain).toBe(summary.live_closure_summary?.live_motion_runbook_ready_plain);
    expect(summary.live_closure_summary?.live_motion_runbook_blocked_plain).toBe(
      "暂不可执行：传感器就绪后建图。",
    );
    expect(summary.live_motion_runbook_blocked_plain).toBe(summary.live_closure_summary?.live_motion_runbook_blocked_plain);
    expect(summary.live_closure_summary?.live_motion_runbook_primary_action_plain).toBe("重跑图上行程并复验轮速");
    expect(summary.live_motion_runbook_primary_action_plain).toBe("重跑图上行程并复验轮速");
    expect(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_plain).toBe(
      "发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。",
    );
    expect(summary.live_motion_runbook_minimal_precheck_plain).toBe(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_plain);
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "可先执行：重跑图上行程并复验轮速、键盘连续手控、自由自助移动。",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "主推荐：重跑图上行程并复验轮速",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "发车前预检已精简",
    );
    expect(summary.live_motion_runbook_summary_plain).toBe(summary.live_closure_summary?.live_motion_runbook_summary_plain);
    expect(summary.live_motion_runbook_items).toEqual(summary.live_closure_summary?.live_motion_runbook_items);
    expect(summary.field_acceptance_status).toBe("needs_wheel_rerun");
    expect(summary.field_acceptance_next_step_id).toBe("run_nav2_route");
    expect(summary.field_acceptance_next_step_label).toBe("完整行程执行");
    expect(summary.field_acceptance_next_step_display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.field_acceptance_next_step_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.field_acceptance_next_step_sends_motion).toBe(true);
    expect(summary.field_acceptance_next_step_requires_safety_confirm).toBe(true);
    expect(summary.field_acceptance_parallel_status_plain).toContain("只读复验：刷新当前所见");
    expect(summary.field_acceptance_parallel_status_plain).toContain("安全确认后动作：重跑图上行程并复验轮速");
    expect(summary.field_acceptance_parallel_no_motion_action_id).toBe("refresh_current_wysiwyg");
    expect(summary.field_acceptance_parallel_no_motion_action_label).toBe("刷新当前所见");
    expect(summary.field_acceptance_parallel_no_motion_action_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.field_acceptance_parallel_no_motion_action_method).toBe("POST");
    expect(summary.field_acceptance_parallel_no_motion_action_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_wysiwyg_refreshes_radar_scan_proof).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_radar_status).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_map_preview).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.field_acceptance_parallel_safety_action_id).toBe("run_nav2_route");
    expect(summary.field_acceptance_parallel_safety_action_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.field_acceptance_parallel_safety_action_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_parallel_hardware_action_id).toBe("none");
    expect(summary.current_hardware_action_required).toBe(false);
    expect(summary.current_hardware_action_id).toBe("none");
    expect(summary.current_hardware_action_label).toBe("无设备处理动作");
    expect(summary.current_hardware_action_after_readback_sequence).toEqual([]);
    expect(summary.current_hardware_action_blocks_mapping_start).toBe(false);
    expect(summary.current_hardware_action_blocks_free_move).toBe(false);
    expect(summary.current_hardware_action_sends_motion).toBe(false);
    expect(summary.field_acceptance_parallel_mapping_missing_evidence).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.field_acceptance_parallel_free_move_allowed_while_mapping_blocked).toBe(true);
    expect(summary.field_acceptance_parallel_sends_motion_when_clicked).toBe(false);
    expect(summary.field_acceptance_ready_step_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
    ]);
    expect(summary.field_acceptance_blocked_step_ids).toEqual(["start_mapping_when_sensors_ready"]);
    expect(summary.field_acceptance_motion_step_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
      "start_mapping_when_sensors_ready",
    ]);
    expect(summary.field_acceptance_no_motion_step_ids).toEqual([]);
    expect(summary.field_acceptance_safety_confirm_ready_step_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_labels).toEqual([
      "完整行程执行",
      "键盘连续手控",
      "自由自助移动",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_display_labels).toEqual([
      "重跑图上行程并复验轮速",
      "键盘连续手控",
      "自由自助移动",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execute",
      "/api/robot-control/base/manual",
      "/api/robot-control/free-roam/autonomy/start",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_start_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execute",
      "/api/robot-control/base/manual",
      "/api/robot-control/free-roam/autonomy/start",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_stop_endpoints).toEqual([
      "/api/robot-control/base/stop",
      "/api/robot-control/base/stop",
      "/api/robot-control/free-roam/autonomy/stop",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview|/api/robot-control/nav2/goal/execution/latest|/api/robot-control/base/feedback-samples|/api/robot-control/delivery/latest|/api/robot-control/summary",
      "/api/robot-control/base/feedback-samples|/api/robot-control/summary",
      "/api/robot-control/free-roam/autonomy/latest|/api/robot-control/map/preview|/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_safety_confirm_ready_action_minimal_precheck_safety_only).toEqual([true, true, true]);
    expect(summary.field_acceptance_safety_confirm_ready_action_camera_preflight_required).toEqual([false, false, false]);
    expect(summary.field_acceptance_safety_confirm_ready_action_radar_preflight_required).toEqual([false, false, false]);
    expect(summary.field_acceptance_safety_confirm_ready_action_route_wysiwyg_preflight_required).toEqual([false, false, false]);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_id).toBe("run_nav2_route");
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_label).toBe("完整行程执行");
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_minimal_precheck_safety_only).toBe(true);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_camera_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_radar_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_route_wysiwyg_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_requires_safety_confirm).toBe(true);
    expect(summary.field_acceptance_primary_safety_confirm_ready_action_sends_motion).toBe(true);
    expect(summary.current_motion_action_required).toBe(true);
    expect(summary.current_motion_action_id).toBe("run_nav2_route");
    expect(summary.current_motion_action_label).toBe("完整行程执行");
    expect(summary.current_motion_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.current_motion_action_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.current_motion_action_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.current_motion_action_acceptance_endpoints).toEqual(summary.field_acceptance_primary_safety_confirm_ready_action_acceptance_endpoints);
    expect(summary.current_motion_action_readback_endpoints).toEqual(summary.field_acceptance_primary_safety_confirm_ready_action_acceptance_endpoints);
    expect(summary.current_motion_action_required_success_markers).toEqual(["same_window_wheel_lr_nonzero", "delivery_success"]);
    expect(summary.current_motion_action_proof_status).toBe("ready_to_verify");
    expect(summary.current_motion_action_missing_evidence).toEqual(["same_window_wheel_lr_nonzero", "delivery_success"]);
    expect(summary.current_motion_action_proof_plain).toContain("可复验完整行程");
    expect(summary.current_motion_action_requires_safety_confirm).toBe(true);
    expect(summary.current_motion_action_minimal_precheck_safety_only).toBe(true);
    expect(summary.current_motion_action_camera_preflight_required).toBe(false);
    expect(summary.current_motion_action_radar_preflight_required).toBe(false);
    expect(summary.current_motion_action_route_wysiwyg_preflight_required).toBe(false);
    expect(summary.current_motion_action_sends_motion).toBe(true);
    expect(summary.current_motion_action_route_ready_on_map).toBe(summary.nav2_route_acceptance_packet?.route_ready_on_map);
    expect(summary.current_motion_action_nav2_goal_succeeded).toBe(summary.nav2_route_acceptance_packet?.nav2_goal_succeeded);
    expect(summary.current_motion_action_same_window_wheel_lr_nonzero).toBe(summary.nav2_route_acceptance_packet?.same_window_wheel_lr_nonzero);
    expect(summary.current_motion_action_delivery_success).toBe(summary.nav2_route_acceptance_packet?.delivery_success);
    expect(summary.current_motion_action_needs_same_window_wheel_rerun).toBe(summary.nav2_route_acceptance_packet?.needs_same_window_wheel_rerun);
    expect(summary.current_motion_action_delivery_success_required).toBe(summary.nav2_route_acceptance_packet?.delivery_success_required);
    expect(summary.current_motion_action_latest_raw_left).toBe(summary.nav2_route_acceptance_packet?.latest_raw_left);
    expect(summary.current_motion_action_latest_raw_right).toBe(summary.nav2_route_acceptance_packet?.latest_raw_right);
    expect(summary.current_motion_action_feedback_sample_count).toBe(summary.nav2_route_acceptance_packet?.feedback_sample_count);
    expect(summary.current_motion_action_feedback_nonzero_sample_count).toBe(summary.nav2_route_acceptance_packet?.feedback_nonzero_sample_count);
    expect(summary.current_motion_action_current_gap_plain).toBe(summary.nav2_route_acceptance_packet?.current_gap_plain);
    expect(summary.current_motion_action_no_extra_precheck_plain).toBe(summary.nav2_route_acceptance_packet?.no_extra_precheck_plain);
    expect(summary.current_motion_action_delivery_next_action_plain).toBe(summary.nav2_route_acceptance_packet?.delivery_next_action_plain);
    expect(summary.current_wysiwyg_action_required).toBe(true);
    expect(summary.current_wysiwyg_action_id).toBe(summary.field_acceptance_primary_no_motion_readback_action_id);
    expect(summary.current_wysiwyg_action_label).toBe("刷新当前所见");
    expect(summary.current_wysiwyg_action_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.current_wysiwyg_action_method).toBe("POST");
    expect(summary.current_wysiwyg_action_sequence).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence);
    expect(summary.current_wysiwyg_action_sequence_labels).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence_labels);
    expect(summary.current_wysiwyg_action_refreshes_summary).toBe(true);
    expect(summary.current_wysiwyg_action_refreshes_radar_scan_proof).toBe(true);
    expect(summary.current_wysiwyg_action_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.current_wysiwyg_action_refreshes_map_preview).toBe(true);
    expect(summary.current_wysiwyg_action_refreshes_radar_status).toBe(true);
    expect(summary.current_wysiwyg_action_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.current_wysiwyg_action_sends_motion).toBe(false);
    expect(summary.current_wysiwyg_action_starts_radar_lifecycle).toBe(false);
    expect(summary.current_wysiwyg_action_starts_map_runtime).toBe(false);
    expect(summary.current_wysiwyg_action_starts_nav2).toBe(false);
    expect(summary.current_wysiwyg_action_starts_manual).toBe(false);
    expect(summary.current_wysiwyg_action_starts_keyboard).toBe(false);
    expect(summary.current_wysiwyg_action_starts_free_roam).toBe(false);
    expect(summary.current_wysiwyg_action_submits_delivery).toBe(false);
    expect(summary.current_wysiwyg_action_stops_motion).toBe(false);
    expect(summary.current_wysiwyg_action_missing_surface_ids).toEqual(summary.field_acceptance_wysiwyg_missing_surface_ids);
    expect(summary.current_wysiwyg_action_refresh_mode).toBe(summary.field_acceptance_wysiwyg_refresh_mode);
    expect(summary.current_keyboard_action_required).toBe(true);
    expect(summary.current_keyboard_action_ready).toBe(true);
    expect(summary.current_keyboard_action_id).toBe("hold_keyboard");
    expect(summary.current_keyboard_action_label).toBe("键盘连续手控");
    expect(summary.current_keyboard_action_display_label).toBe("键盘连续手控");
    expect(summary.current_keyboard_action_start_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.current_keyboard_action_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.current_keyboard_action_acceptance_endpoints).toEqual([
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
    ]);
    expect(summary.current_keyboard_action_readback_endpoints).toEqual(summary.current_keyboard_action_acceptance_endpoints);
    expect(summary.current_keyboard_action_required_success_markers).toEqual(["same_hold_window_wheel_lr_nonzero", "stop_after_release"]);
    expect(summary.current_keyboard_action_proof_status).toBe("ready_to_verify");
    expect(summary.current_keyboard_action_missing_evidence).toEqual(["same_hold_window_wheel_lr_nonzero", "stop_after_release"]);
    expect(summary.current_keyboard_action_proof_plain).toContain("可验证键盘连续手控");
    expect(summary.current_keyboard_action_requires_safety_confirm).toBe(true);
    expect(summary.current_keyboard_action_minimal_precheck_safety_only).toBe(true);
    expect(summary.current_keyboard_action_enable_sends_motion).toBe(false);
    expect(summary.current_keyboard_action_hold_to_move_required).toBe(true);
    expect(summary.current_keyboard_action_hold_sends_motion).toBe(true);
    expect(summary.current_keyboard_action_pulse_interval_ms).toBe(260);
    expect(summary.current_keyboard_action_pulse_duration_ms).toBe(240);
    expect(summary.current_keyboard_action_stop_triggers).toEqual(["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"]);
    expect(summary.current_keyboard_action_wheel_feedback_acceptance).toBe("same_hold_window_wheel_lr_nonzero");
    expect(summary.current_keyboard_action_post_hold_readback_endpoints).toEqual([
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
    ]);
    expect(summary.current_keyboard_action_post_hold_readback_sequence_labels).toEqual(["复验键盘轮速采样", "刷新总览"]);
    expect(summary.current_keyboard_action_post_hold_feedback_readback_required).toBe(true);
    expect(summary.current_keyboard_action_post_hold_summary_refresh_required).toBe(true);
    expect(summary.current_free_move_action_required).toBe(true);
    expect(summary.current_free_move_action_ready).toBe(true);
    expect(summary.current_free_move_action_id).toBe("start_free_move");
    expect(summary.current_free_move_action_label).toBe("自由自助移动");
    expect(summary.current_free_move_action_display_label).toBe("自由自助移动");
    expect(summary.current_free_move_action_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
    expect(summary.current_free_move_action_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
    expect(summary.current_free_move_action_latest_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.current_free_move_action_readback_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.current_free_move_action_acceptance_endpoints).toEqual([
      "/api/robot-control/free-roam/autonomy/latest",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.current_free_move_action_readback_endpoints).toEqual(summary.current_free_move_action_acceptance_endpoints);
    expect(summary.current_free_move_action_required_success_markers).toEqual(["free_roam_latest_motion_ready"]);
    expect(summary.current_free_move_action_proof_status).toBe("ready_to_verify");
    expect(summary.current_free_move_action_missing_evidence).toEqual(["free_roam_latest_motion_ready"]);
    expect(summary.current_free_move_action_proof_plain).toContain("可验证自由自助移动");
    expect(summary.current_free_move_action_requires_safety_confirm).toBe(true);
    expect(summary.current_free_move_action_minimal_precheck_safety_only).toBe(true);
    expect(summary.current_free_move_action_camera_preflight_required).toBe(false);
    expect(summary.current_free_move_action_radar_preflight_required).toBe(false);
    expect(summary.current_free_move_action_without_camera_allowed).toBe(true);
    expect(summary.current_free_move_action_without_radar_allowed).toBe(true);
    expect(summary.current_free_move_action_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.current_free_move_action_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.current_free_move_action_sends_motion).toBe(true);
    expect(summary.field_acceptance_safety_confirm_ready_actions).toEqual([
      expect.objectContaining({
        id: "run_nav2_route",
        start_endpoint: "/api/robot-control/nav2/goal/execute",
        requires_safety_confirm: true,
        minimal_precheck_safety_only: true,
        sends_motion_when_executed: true,
        camera_preflight_required: false,
        radar_preflight_required: false,
        starts_nav2_when_executed: true,
      }),
      expect.objectContaining({
        id: "hold_keyboard",
        start_endpoint: "/api/robot-control/base/manual",
        requires_safety_confirm: true,
        camera_preflight_required: false,
        radar_preflight_required: false,
        starts_keyboard_when_executed: true,
      }),
      expect.objectContaining({
        id: "start_free_move",
        start_endpoint: "/api/robot-control/free-roam/autonomy/start",
        requires_safety_confirm: true,
        camera_preflight_required: false,
        radar_preflight_required: false,
        starts_free_roam_when_executed: true,
      }),
    ]);
    expect(summary.field_acceptance_hardware_action_ids).toEqual([]);
    expect(summary.field_acceptance_no_motion_readback_action_ids).toEqual([
      "readback_all",
      "refresh_current_wysiwyg",
      "refresh_radar_map_overlay",
    ]);
    expect(summary.field_acceptance_no_motion_readback_action_labels).toEqual([
      "复验全部读数",
      "刷新当前所见",
      "刷新雷达贴图",
    ]);
    expect(summary.field_acceptance_no_motion_readback_action_endpoints).toEqual([
      "/api/robot-control/summary",
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/scan-proof/refresh",
    ]);
    expect(summary.field_acceptance_no_motion_readback_action_methods).toEqual(["GET", "POST", "POST"]);
    expect(summary.field_acceptance_no_motion_readback_action_sequences?.[1]).toBe("/api/robot-control/radar/scan-proof/refresh|/api/robot-control/radar/status|/api/robot-control/map/preview|/api/robot-control/camera/first-frame/probe|/api/robot-control/camera/mjpeg/status|/api/robot-control/summary");
    expect(summary.field_acceptance_no_motion_readback_action_sequence_labels?.[1]).toBe("刷新雷达扫描读数|读取雷达状态|刷新地图画面|复测相机首帧|读取相机 MJPEG 状态|刷新总览");
    expect(summary.field_acceptance_no_motion_readback_action_sequences?.[2]).toBe("/api/robot-control/radar/scan-proof/refresh|/api/robot-control/radar/status|/api/robot-control/map/preview|/api/robot-control/summary");
    expect(summary.field_acceptance_no_motion_readback_action_sequence_labels?.[2]).toBe("刷新雷达扫描读数|读取雷达状态|刷新地图画面|刷新总览");
    expect(summary.field_acceptance_primary_no_motion_readback_action_id).toBe("refresh_current_wysiwyg");
    expect(summary.field_acceptance_primary_no_motion_readback_action_label).toBe("刷新当前所见");
    expect(summary.field_acceptance_primary_no_motion_readback_action_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.field_acceptance_primary_no_motion_readback_action_method).toBe("POST");
    expect(summary.field_acceptance_primary_no_motion_readback_id).toBe(summary.field_acceptance_primary_no_motion_readback_action_id);
    expect(summary.field_acceptance_primary_no_motion_readback_label).toBe(summary.field_acceptance_primary_no_motion_readback_action_label);
    expect(summary.field_acceptance_primary_no_motion_readback_endpoint).toBe(summary.field_acceptance_primary_no_motion_readback_action_endpoint);
    expect(summary.field_acceptance_primary_no_motion_readback_method).toBe(summary.field_acceptance_primary_no_motion_readback_action_method);
    expect(summary.field_acceptance_primary_no_motion_readback_action_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_primary_no_motion_readback_sequence).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence);
    expect(summary.field_acceptance_primary_no_motion_readback_action_sequence_labels).toEqual(["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "复测相机首帧", "读取相机 MJPEG 状态", "刷新总览"]);
    expect(summary.field_acceptance_primary_no_motion_readback_sequence_labels).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence_labels);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_summary).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_radar_scan_proof).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_map_preview).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_radar_status).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_sends_motion).toBe(false);
    expect(summary.field_acceptance_primary_no_motion_readback_sends_motion).toBe(false);
    expect(summary.field_acceptance_no_motion_readback_actions).toEqual([
      expect.objectContaining({
        id: "readback_all",
        endpoint: "/api/robot-control/summary",
        method: "GET",
        sends_motion_when_clicked: false,
        starts_nav2_when_clicked: false,
        starts_manual_when_clicked: false,
        starts_free_roam_when_clicked: false,
        starts_map_runtime_when_clicked: false,
        starts_radar_lifecycle_when_clicked: false,
      }),
      expect.objectContaining({
        id: "refresh_current_wysiwyg",
        endpoint: "/api/robot-control/radar/scan-proof/refresh",
        method: "POST",
        sequence_endpoints: [
          "/api/robot-control/radar/scan-proof/refresh",
          "/api/robot-control/radar/status",
          "/api/robot-control/map/preview",
          "/api/robot-control/camera/first-frame/probe",
          "/api/robot-control/camera/mjpeg/status",
          "/api/robot-control/summary",
        ],
        sequence_labels: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "复测相机首帧", "读取相机 MJPEG 状态", "刷新总览"],
        refreshes_summary: true,
        refreshes_radar_scan_proof: true,
        refreshes_camera_first_frame_probe: true,
        refreshes_map_preview: true,
        refreshes_radar_status: true,
        refreshes_camera_mjpeg_status: true,
        sends_motion_when_clicked: false,
      }),
      expect.objectContaining({
        id: "refresh_radar_map_overlay",
        endpoint: "/api/robot-control/radar/scan-proof/refresh",
        method: "POST",
        sequence_endpoints: [
          "/api/robot-control/radar/scan-proof/refresh",
          "/api/robot-control/radar/status",
          "/api/robot-control/map/preview",
          "/api/robot-control/summary",
        ],
        sequence_labels: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "刷新总览"],
        refreshes_summary: true,
        refreshes_radar_scan_proof: true,
        refreshes_camera_first_frame_probe: false,
        refreshes_map_preview: true,
        refreshes_radar_status: true,
        refreshes_camera_mjpeg_status: false,
        sends_motion_when_clicked: false,
      }),
    ]);
    expect(summary.field_acceptance_remaining_operator_action_summary_plain).toContain("需要现场安全确认的运动验收");
    expect(summary.field_acceptance_remaining_operator_action_summary_plain).toContain("重跑图上行程并复验轮速、键盘连续手控、自由自助移动");
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).toContain("当前没有必须先处理的设备动作");
    expect(summary.field_acceptance_remaining_no_motion_action_summary_plain).toContain("复验全部读数、刷新当前所见、刷新雷达贴图");
    expect(summary.field_acceptance_remaining_no_motion_action_summary_plain).toContain("不启动车辆");
    expect(summary.field_acceptance_remaining_action_summary_plain).toContain("需要现场安全确认的运动验收");
    expect(summary.field_acceptance_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
      "/api/robot-control/free-roam/autonomy/latest",
    ]);
    expect(summary.field_acceptance_safety_confirm_required).toBe(true);
    expect(summary.field_acceptance_minimal_precheck_safety_only).toBe(true);
    expect(summary.field_acceptance_summary_plain).toContain("现场验收包");
    expect(summary.field_acceptance_summary_plain).toContain("四项目标完成");
    expect(summary.field_acceptance_summary_plain).toContain("下一步：");
    expect(summary.field_acceptance_packet).toEqual(expect.objectContaining({
      status: "needs_wheel_rerun",
      next_step_id: "run_nav2_route",
      next_step_start_endpoint: "/api/robot-control/nav2/goal/execute",
      next_step_sends_motion: true,
      next_step_requires_safety_confirm: true,
      safety_confirm_ready_step_ids: ["run_nav2_route", "hold_keyboard", "start_free_move"],
      safety_confirm_ready_action_labels: ["完整行程执行", "键盘连续手控", "自由自助移动"],
      primary_safety_confirm_ready_action_id: "run_nav2_route",
      primary_safety_confirm_ready_action_start_endpoint: "/api/robot-control/nav2/goal/execute",
      primary_safety_confirm_ready_action_requires_safety_confirm: true,
      primary_safety_confirm_ready_action_sends_motion: true,
      no_motion_readback_action_ids: ["readback_all", "refresh_current_wysiwyg", "refresh_radar_map_overlay"],
      no_motion_readback_action_labels: ["复验全部读数", "刷新当前所见", "刷新雷达贴图"],
      no_motion_readback_action_sequences: expect.arrayContaining([
        "/api/robot-control/radar/scan-proof/refresh|/api/robot-control/radar/status|/api/robot-control/map/preview|/api/robot-control/camera/first-frame/probe|/api/robot-control/camera/mjpeg/status|/api/robot-control/summary",
        "/api/robot-control/radar/scan-proof/refresh|/api/robot-control/radar/status|/api/robot-control/map/preview|/api/robot-control/summary",
      ]),
      primary_no_motion_readback_action_id: "refresh_current_wysiwyg",
      primary_no_motion_readback_action_endpoint: "/api/robot-control/radar/scan-proof/refresh",
      primary_no_motion_readback_action_sequence: [
        "/api/robot-control/radar/scan-proof/refresh",
        "/api/robot-control/radar/status",
        "/api/robot-control/map/preview",
        "/api/robot-control/camera/first-frame/probe",
        "/api/robot-control/camera/mjpeg/status",
        "/api/robot-control/summary",
      ],
      primary_no_motion_readback_action_refreshes_map_preview: true,
      primary_no_motion_readback_action_refreshes_radar_status: true,
      primary_no_motion_readback_action_refreshes_camera_first_frame_probe: true,
      primary_no_motion_readback_action_refreshes_camera_mjpeg_status: true,
      primary_no_motion_readback_action_sends_motion: false,
      safety_confirm_required: true,
      minimal_precheck_safety_only: true,
      wysiwyg_missing_surface_ids: expect.arrayContaining(["camera"]),
      mapping_start_ready: false,
      camera_blocks_mapping_start: true,
      camera_blocks_free_move: false,
      sends_motion_when_clicked: false,
      starts_nav2_when_clicked: false,
      starts_manual_when_clicked: false,
      starts_free_roam_when_clicked: false,
      starts_map_runtime_when_clicked: false,
    }));
    expect(summary.field_acceptance_packet?.wysiwyg_refresh_mode).toBe("all_wysiwyg");
    expect(summary.field_acceptance_wysiwyg_refresh_mode).toBe("all_wysiwyg");
    expect(summary.field_acceptance_packet?.steps).toEqual(summary.field_acceptance_steps);
    expect(summary.field_acceptance_steps?.find((item) => item.id === "run_nav2_route")).toEqual(expect.objectContaining({
      ready: true,
      completed: false,
      sends_motion_when_executed: true,
      safety_confirm_required: true,
      missing_evidence: ["same_window_wheel_lr_nonzero", "delivery_success"],
    }));
    expect(summary.field_acceptance_steps?.find((item) => item.id === "start_mapping_when_sensors_ready")).toEqual(expect.objectContaining({
      ready: false,
      sends_motion_when_executed: true,
      missing_evidence: ["camera_first_frame", "lidar_fresh"],
    }));
    expect(summary.nav2_route_acceptance_packet).toEqual(expect.objectContaining({
      action_id: "run_nav2_route",
      label: "完整行程执行",
      status: "needs_wheel_rerun",
      proof_status: "ready_to_verify",
      ready: true,
      completed: false,
      start_endpoint: "/api/robot-control/nav2/goal/execute",
      stop_endpoint: "/api/robot-control/base/stop",
      start_sends_motion: true,
      requires_safety_confirm: true,
      minimal_precheck_safety_only: true,
      camera_preflight_required: false,
      radar_preflight_required: false,
      route_wysiwyg_preflight_required: false,
      blocked_by_camera_wysiwyg: false,
      blocked_by_radar_wysiwyg: false,
      route_ready_on_map: true,
      nav2_goal_succeeded: true,
      same_window_wheel_lr_nonzero: false,
      delivery_success: false,
      needs_same_window_wheel_rerun: true,
      delivery_success_required: true,
      missing_evidence: ["same_window_wheel_lr_nonzero", "delivery_success"],
      required_success_markers: [
        "map_route_visible",
        "nav2_goal_succeeded",
        "same_window_wheel_lr_nonzero",
        "delivery_success",
      ],
      fixed_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest",
      fixed_wheel_readback_endpoint: "/api/robot-control/base/feedback-samples",
      fixed_delivery_latest_endpoint: "/api/robot-control/delivery/latest",
      fixed_delivery_complete_endpoint: "/api/robot-control/delivery/complete",
      delivery_complete_sends_motion: false,
      readback_sends_motion: false,
      readback_starts_nav2: false,
      readback_starts_manual: false,
      readback_starts_keyboard: false,
      readback_starts_free_roam: false,
      readback_starts_map_runtime: false,
      readback_submits_delivery: false,
      readback_stops_motion: false,
      command_mode: "ros",
      next_base_command_mode: "ros",
      latest_raw_left: "0",
      latest_raw_right: "0",
      feedback_sample_count: "2",
      feedback_nonzero_sample_count: "0",
      sends_motion_when_clicked: false,
    }));
    expect(summary.nav2_route_acceptance_packet?.acceptance_endpoints).toEqual(summary.primary_acceptance_endpoints);
    expect(summary.nav2_route_acceptance_packet?.readback_endpoints).toEqual(summary.wheel_rerun_readback_endpoints);
    expect(summary.nav2_route_acceptance_packet?.current_gap_plain).toContain("当前缺口");
    expect(summary.nav2_route_acceptance_packet?.checklist_plain).toContain("先勾现场安全确认");
    expect(summary.nav2_route_acceptance_packet?.acceptance_plain).toContain("送达确认");
    expect(summary.nav2_route_acceptance_packet?.no_extra_precheck_plain).toContain("发车前预检只看现场安全确认");
    expect(summary.primary_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.primary_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.primary_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.primary_sends_motion).toBe(true);
    expect(summary.primary_requires_safety_confirm).toBe(true);
    expect(summary.primary_ready).toBe(true);
    expect(summary.primary_completed).toBe(false);
    expect(summary.primary_proof_status).toBe("ready_to_verify");
    expect(summary.primary_missing_evidence).toEqual(["same_window_wheel_lr_nonzero", "delivery_success"]);
    expect(summary.primary_proof_plain).toContain("可复验完整行程");
    expect(summary.trip_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.trip_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.trip_acceptance_endpoints).toEqual(summary.primary_acceptance_endpoints);
    expect(summary.trip_ready).toBe(true);
    expect(summary.trip_completed).toBe(false);
    expect(summary.trip_proof_status).toBe("ready_to_verify");
    expect(summary.trip_missing_evidence).toEqual(["same_window_wheel_lr_nonzero", "delivery_success"]);
    expect(summary.trip_proof_plain).toBe(summary.primary_proof_plain);
    expect(summary.keyboard_start_endpoint).toBe("/api/robot-control/base/manual");
    expect(summary.keyboard_acceptance_endpoints).toEqual([
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
    ]);
    expect(summary.keyboard_readback_endpoints).toEqual(summary.keyboard_acceptance_endpoints);
    expect(summary.keyboard_required_success_markers).toEqual(["same_hold_window_wheel_lr_nonzero", "stop_after_release"]);
    expect(summary.keyboard_completed).toBe(false);
    expect(summary.keyboard_proof_status).toBe("ready_to_verify");
    expect(summary.keyboard_missing_evidence).toEqual(["same_hold_window_wheel_lr_nonzero", "stop_after_release"]);
    expect(summary.keyboard_proof_plain).toContain("可验证键盘连续手控");
    expect(summary.free_move_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
    expect(summary.free_move_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
    expect(summary.free_move_acceptance_endpoints).toEqual([
      "/api/robot-control/free-roam/autonomy/latest",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.free_move_readback_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.free_move_latest_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.free_move_readback_endpoints).toEqual(summary.free_move_acceptance_endpoints);
    expect(summary.free_move_required_success_marker).toBe("free_roam_latest_motion_ready");
    expect(summary.free_move_required_success_markers).toEqual(["free_roam_latest_motion_ready"]);
    expect(summary.free_move_proof_status).toBe("ready_to_verify");
    expect(summary.free_move_missing_evidence).toEqual(["free_roam_latest_motion_ready"]);
    expect(summary.free_move_proof_plain).toContain("可验证自由自助移动");
    expect(summary.current_free_move_action_start_endpoint).toBe(summary.free_move_start_endpoint);
    expect(summary.current_free_move_action_stop_endpoint).toBe(summary.free_move_stop_endpoint);
    expect(summary.current_free_move_action_acceptance_endpoints).toEqual(summary.free_move_acceptance_endpoints);
    expect(summary.current_free_move_action_readback_endpoint).toBe(summary.free_move_readback_endpoint);
    expect(summary.current_free_move_action_readback_endpoints).toEqual(summary.free_move_readback_endpoints);
    expect(summary.current_free_move_action_required_success_markers).toEqual(summary.free_move_required_success_markers);
    expect(summary.current_free_move_action_missing_evidence).toEqual(summary.free_move_missing_evidence);
    expect(summary.current_free_move_action_proof_status).toBe(summary.free_move_proof_status);
    expect(summary.mapping_start_endpoint).toBe("/api/robot-control/map/start");
    expect(summary.mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.mapping_acceptance_endpoints).toEqual([
      "/api/robot-control/free-roam/autonomy/latest",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.mapping_readback_endpoints).toEqual(summary.mapping_acceptance_endpoints);
    expect(summary.mapping_required_success_markers).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.mapping_proof_status).toBe("blocked");
    expect(summary.mapping_missing_evidence).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.mapping_proof_plain).toContain("建图暂不可启动");
    expect(summary.field_acceptance_missing_evidence_ids).toEqual([
      "same_window_wheel_lr_nonzero",
      "delivery_success",
      "same_hold_window_wheel_lr_nonzero",
      "stop_after_release",
      "free_roam_latest_motion_ready",
      "camera_first_frame",
      "lidar_fresh",
    ]);
    expect(summary.field_acceptance_missing_evidence_labels).toEqual([
      "同窗口 wheel L/R 非零",
      "送达确认",
      "按住同窗口 wheel L/R 非零",
      "松开/失焦后 stop 已落稳",
      "自由移动运行读数",
      "相机首帧",
      "雷达新鲜读数",
    ]);
    expect(summary.field_acceptance_primary_missing_evidence_id).toBe("same_window_wheel_lr_nonzero");
    expect(summary.field_acceptance_primary_missing_evidence_label).toBe("同窗口 wheel L/R 非零");
    expect(summary.field_acceptance_primary_missing_evidence_action_id).toBe("run_nav2_route");
    expect(summary.field_acceptance_primary_missing_evidence_action_label).toBe("完整行程执行");
    expect(summary.field_acceptance_primary_missing_evidence_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.field_acceptance_primary_missing_evidence_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.field_acceptance_primary_missing_evidence_readback_method).toBe("POST");
    expect(summary.field_acceptance_primary_missing_evidence_requires_motion_before_readback).toBe(true);
    expect(summary.field_acceptance_primary_missing_evidence_requires_safety_confirm_before_motion).toBe(true);
    expect(summary.field_acceptance_primary_missing_evidence_blocks_field_acceptance).toBe(true);
    expect(summary.field_acceptance_primary_missing_id).toBe("same_window_wheel_lr_nonzero");
    expect(summary.field_acceptance_primary_missing_label).toBe("同窗口 wheel L/R 非零");
    expect(summary.field_acceptance_primary_missing_action_id).toBe("run_nav2_route");
    expect(summary.field_acceptance_primary_missing_action_label).toBe("完整行程执行");
    expect(summary.field_acceptance_primary_missing_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.field_acceptance_primary_missing_action_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.field_acceptance_primary_missing_action_stop_endpoint).toBe("/api/robot-control/base/stop");
    expect(summary.field_acceptance_primary_missing_action_acceptance_endpoints).toEqual([
      "/api/robot-control/map/preview",
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_primary_missing_action_sends_motion).toBe(true);
    expect(summary.field_acceptance_primary_missing_action_requires_safety_confirm).toBe(true);
    expect(summary.field_acceptance_primary_missing_action_minimal_precheck_safety_only).toBe(true);
    expect(summary.field_acceptance_primary_missing_action_camera_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_missing_action_radar_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_missing_action_operator_report_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_missing_action_route_wysiwyg_preflight_required).toBe(false);
    expect(summary.field_acceptance_primary_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.field_acceptance_primary_readback_method).toBe("POST");
    expect(summary.field_acceptance_primary_requires_motion_before_readback).toBe(true);
    expect(summary.field_acceptance_primary_requires_safety_confirm_before_motion).toBe(true);
    expect(summary.field_acceptance_primary_blocks_field_acceptance).toBe(true);
    const fieldAcceptancePacket = summary.field_acceptance_packet;
    expect(fieldAcceptancePacket).toBeDefined();
    expect(fieldAcceptancePacket?.next_step_display_label).toBe("重跑图上行程并复验轮速");
    expect(fieldAcceptancePacket?.primary_safety_confirm_ready_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(fieldAcceptancePacket?.primary_missing_evidence_action_label).toBe("完整行程执行");
    expect(fieldAcceptancePacket?.primary_missing_evidence_action_display_label).toBe("重跑图上行程并复验轮速");
    expect(fieldAcceptancePacket?.primary_missing_evidence_readback_method).toBe("POST");
    expect(fieldAcceptancePacket?.primary_missing_evidence_requires_motion_before_readback).toBe(true);
    expect(fieldAcceptancePacket?.primary_missing_evidence_requires_safety_confirm_before_motion).toBe(true);
    expect(fieldAcceptancePacket?.primary_missing_evidence_blocks_field_acceptance).toBe(true);
    expect(summary.field_acceptance_missing_evidence_items).toEqual(expect.arrayContaining([
      expect.objectContaining({
        id: "same_window_wheel_lr_nonzero",
        action_id: "run_nav2_route",
        action_display_label: "重跑图上行程并复验轮速",
        readback_endpoint: "/api/robot-control/base/feedback-samples",
        readback_method: "POST",
        requires_motion_before_readback: true,
        requires_safety_confirm_before_motion: true,
        blocks_field_acceptance: true,
      }),
      expect.objectContaining({
        id: "delivery_success",
        action_id: "run_nav2_route",
        readback_endpoint: "/api/robot-control/delivery/latest",
        readback_method: "GET",
        requires_motion_before_readback: true,
      }),
      expect.objectContaining({
        id: "camera_first_frame",
        action_id: "start_mapping_when_sensors_ready",
        readback_endpoint: "/api/robot-control/camera/first-frame/probe",
        readback_method: "POST",
        requires_motion_before_readback: false,
      }),
      expect.objectContaining({
        id: "lidar_fresh",
        action_id: "start_mapping_when_sensors_ready",
        readback_endpoint: "/api/robot-control/radar/scan-proof/refresh",
        readback_method: "POST",
        requires_motion_before_readback: false,
      }),
    ]));
    expect(summary.nav2_route_acceptance_packet?.display_label).toBe("重跑图上行程并复验轮速");
    expect(summary.keyboard_wheel_lr_nonzero).toBe(false);
    expect(summary.keyboard_stop_after_release).toBe(false);
    expect(summary.live_closure_summary?.live_motion_runbook_items).toEqual([
      expect.objectContaining({
        id: "run_nav2_route",
        ready: true,
        completed: false,
        proof_status: "ready_to_verify",
        missing_evidence: ["same_window_wheel_lr_nonzero", "delivery_success"],
        minimal_precheck_safety_only: true,
        safety_confirm_required: true,
        sends_motion_when_executed: true,
        start_endpoint: "/api/robot-control/nav2/goal/execute",
        acceptance_endpoints: [
          "/api/robot-control/map/preview",
          "/api/robot-control/nav2/goal/execution/latest",
          "/api/robot-control/base/feedback-samples",
          "/api/robot-control/delivery/latest",
          "/api/robot-control/summary",
        ],
        proof_plain: "可复验完整行程：勾现场安全确认后执行图上路线，执行后按验收端点读回；还差：同窗口 wheel L/R 非零、送达确认。",
      }),
      expect.objectContaining({
        id: "hold_keyboard",
        ready: true,
        completed: false,
        proof_status: "ready_to_verify",
        missing_evidence: ["same_hold_window_wheel_lr_nonzero", "stop_after_release"],
        start_endpoint: "/api/robot-control/base/manual",
        acceptance_endpoints: [
          "/api/robot-control/base/feedback-samples",
          "/api/robot-control/summary",
        ],
      }),
      expect.objectContaining({
        id: "start_free_move",
        ready: true,
        completed: false,
        proof_status: "ready_to_verify",
        missing_evidence: ["free_roam_latest_motion_ready"],
        start_endpoint: "/api/robot-control/free-roam/autonomy/start",
        acceptance_endpoints: [
          "/api/robot-control/free-roam/autonomy/latest",
          "/api/robot-control/map/preview",
          "/api/robot-control/summary",
        ],
      }),
      expect.objectContaining({
        id: "start_mapping_when_sensors_ready",
        ready: false,
        completed: false,
        proof_status: "blocked",
        missing_evidence: ["camera_first_frame", "lidar_fresh"],
        start_endpoint: "/api/robot-control/map/start",
        acceptance_endpoints: [
          "/api/robot-control/free-roam/autonomy/latest",
          "/api/robot-control/map/preview",
          "/api/robot-control/summary",
        ],
      }),
    ]);
  });

  it("treats camera service self-owner as non-exclusive no-frame usage", async () => {
    // 8088 相机服务自己持有 UVC 是共享预览单上游模型；summary 不能把它说成外部独占。
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
      if (url.pathname === "/api/camera/health") {
        return new Response(JSON.stringify({
          ...basePayload,
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          selected_name: "USB Composite Device: DV20 USB",
          current_selection: {
            selected_name: "USB Composite Device: DV20 USB",
            selected_path: "/dev/video1",
            selected_is_uvc_or_usb: true,
          },
          source_usage: {
            status: "in_use_by_camera_service",
            owner_count: 1,
            owners: [
              {
                pid: 525518,
                command: "python3 scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088",
                self: true,
              },
            ],
          },
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.pathname === "/api/camera/devices") {
        return new Response(JSON.stringify({
          ...basePayload,
          devices: [],
          source_candidates_summary: {
            candidates: [],
          },
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(basePayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });

    expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
    expect(summary.readback_summary.camera.source_usage_status).toBe("in_use_by_camera_service");
    expect(summary.readback_summary.camera.source_usage_owner_count).toBe("1");
    expect(summary.readback_summary.camera.source_usage_scope).toBe("camera_service_self");
    expect(summary.readback_summary.camera.source_usage_not_exclusive).toBe("true");
    expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
    expect(summary.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
    expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toContain("不是页面独占");
    expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toContain("相机服务正在用单上游共享预览读取 USB Composite Device: DV20 USB");
    expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toContain("UVC 设备没有输出视频帧");
    expect(summary.readback_summary.camera.preview_next_action_plain).toContain("检查 USB");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("已排除页面独占");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("诊断=UVC 无首帧");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).not.toContain("uvc_no_frame_not_exclusive");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("UVC 设备没有输出视频帧");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("下一步：检查 USB");
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toContain("camera");
  });

  it("prioritizes full-speed USB camera diagnosis in camera summary", async () => {
    // 现场 dmesg 出现 -71/URB 这类 UVC 传输错误时，普通 summary 要指向 USB 链路而不是泛化无首帧。
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
      if (url.pathname === "/api/camera/health") {
        return new Response(JSON.stringify({
          ...basePayload,
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          current_selection: {
            selected_name: "USB Composite Device: DV20 USB",
            selected_path: "/dev/video1",
            selected_is_uvc_or_usb: true,
          },
          source_usage: {
            status: "not_in_use",
            owner_count: 0,
            other_owner_count: 0,
            owners: [],
          },
          uvc_kernel_diagnostics: {
            status: "uvc_usb_transport_errors_observed",
            plain_hint: "USB Composite Device: DV20 USB 的内核日志出现 UVC/USB 传输错误；优先检查 USB 线、接口、供电或换 known-good UVC。",
            next_action: "check_usb_cable_port_power_or_known_good_uvc",
            transport_error_count: 3,
            latest_transport_error: "uvcvideo 3-1:1.1: Failed to resubmit video URB (-1).",
          },
          uvc_usb_topology: {
            status: "uvc_video_on_full_speed_usb",
            plain_hint: "USB Composite Device: DV20 USB 当前在 USB 12M full-speed 拓扑上，视频流容易 STREAMON I/O error。",
            next_action: "move_camera_to_high_speed_usb_port_or_powered_hub",
            video_usb_speed: "12M",
            kernel_usb_address: "6-1",
            video_interface_count: 2,
          },
          source_diagnosis: {
            status: "uvc_transport_error_not_exclusive",
            plain_hint: "不是页面独占：USB Composite Device: DV20 USB 当前无人占用，但内核日志已有 UVC/USB 传输错误；检查 USB 线、接口、摄像头供电或换 known-good UVC 复测。",
            next_action: "check usb cable port power or known good uvc",
            not_exclusive: true,
            uvc_kernel_diagnostics_status: "uvc_usb_transport_errors_observed",
          },
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(basePayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });

    expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
    expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
    expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toContain("USB 12M full-speed");
    expect(summary.readback_summary.camera.source_diagnosis_next_action_plain).toBe("摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。");
    expect(summary.readback_summary.camera.source_diagnosis_next_action_plain).not.toContain("move camera");
    expect(summary.readback_summary.camera.uvc_kernel_diagnostics_status).toBe("uvc_usb_transport_errors_observed");
    expect(summary.readback_summary.camera.uvc_kernel_diagnostics_transport_error_count).toBe("3");
    expect(summary.readback_summary.camera.uvc_kernel_diagnostics_latest_transport_error).toContain("Failed to resubmit video URB");
    expect(summary.readback_summary.camera.uvc_usb_topology_status).toBe("uvc_video_on_full_speed_usb");
    expect(summary.readback_summary.camera.uvc_usb_topology_video_usb_speed).toBe("12M");
    expect(summary.readback_summary.camera.uvc_usb_topology_kernel_usb_address).toBe("6-1");
    expect(summary.readback_summary.camera.uvc_usb_topology_video_interface_count).toBe("2");
    expect(summary.readback_summary.camera.uvc_usb_topology_next_action).toBe("move_camera_to_high_speed_usb_port_or_powered_hub");
    expect(summary.readback_summary.camera.plain_hint).toContain("USB 12M full-speed");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("诊断=USB full-speed");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).not.toContain("uvc_full_speed_usb_not_exclusive");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("已排除页面独占");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("USB 12M full-speed");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_diagnostic_plain).toContain("下一步：摄像头现在挂在 USB 12M full-speed");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain).toBe(
      "相机不是页面独占；诊断显示 USB full-speed；先换高速USB后复测，再读取共享预览状态。当前硬件提示：摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测。",
    );
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_next_action_plain).toBe(
      "相机不是页面独占；诊断显示 USB full-speed；先换高速USB后复测，再读取共享预览状态。当前硬件提示：摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测。",
    );
    expect(summary.live_closure_summary?.camera_usb_speed).toBe("12M");
    expect(summary.live_closure_summary?.camera_hardware_action_required).toBe(true);
    expect(summary.live_closure_summary?.camera_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.live_closure_summary?.camera_usb_full_speed_detected).toBe(true);
    expect(summary.camera_ready).toBe(false);
    expect(summary.camera_first_frame_ready).toBe(false);
    expect(summary.camera_needs_usb_fix).toBe(true);
    expect(summary.camera_usb_high_speed).toBe(false);
    expect(summary.camera_usb_speed).toBe("12M");
    expect(summary.camera_hardware_action_required).toBe(true);
    expect(summary.camera_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.camera_usb_full_speed_detected).toBe(true);
    expect(summary.current_mapping_action_camera_hardware_action_required).toBe(true);
    expect(summary.current_mapping_action_camera_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.current_mapping_action_camera_usb_full_speed_detected).toBe(true);
    expect(summary.current_mapping_action_camera_usb_speed).toBe("12M");
    expect(summary.current_mapping_action_camera_source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
    expect(summary.current_mapping_action_camera_source_diagnosis_not_exclusive).toBe("true");
    expect(summary.current_mapping_action_camera_recovery_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.current_mapping_action_blocks_free_move).toBe(false);
    expect(summary.camera_source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
    expect(summary.camera_source_diagnosis_not_exclusive).toBe("true");
    expect(summary.camera_source_diagnosis_plain_hint).toContain("USB 12M full-speed");
    expect(summary.camera_source_diagnosis_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.camera_recovery_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.camera_recovery_sends_motion).toBe(false);
    expect(summary.live_wysiwyg_camera_source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
    expect(summary.live_wysiwyg_camera_source_diagnosis_plain_hint).toContain("USB 12M full-speed");
    expect(summary.live_wysiwyg_camera_source_diagnosis_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.live_wysiwyg_camera_source_diagnosis_not_exclusive).toBe("true");
    expect(summary.live_wysiwyg_camera_recovery_status).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_status);
    expect(summary.live_wysiwyg_camera_recovery_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.live_wysiwyg_camera_recovery_sequence).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence);
    expect(summary.live_wysiwyg_camera_recovery_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence_labels);
    expect(summary.live_wysiwyg_camera_recovery_sends_motion).toBe(false);
    expect(summary.camera_wysiwyg_recovery_status).toBe(summary.live_closure_summary?.live_wysiwyg_camera_recovery_status);
    expect(summary.camera_wysiwyg_recovery_next_action_plain).toContain("换高速 USB 口/线或带供电 USB Hub");
    expect(summary.camera_wysiwyg_recovery_readback_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.camera_wysiwyg_recovery_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.camera_wysiwyg_recovery_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.camera_wysiwyg_recovery_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.camera_wysiwyg_recovery_readback_endpoints).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.camera_wysiwyg_recovery_readback_sequence_labels).toEqual([
      "复测相机首帧",
      "读取共享预览状态",
      "刷新当前卡点",
    ]);
    expect(summary.camera_wysiwyg_recovery_requires_hardware_action).toBe(true);
    expect(summary.camera_wysiwyg_recovery_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.camera_wysiwyg_recovery_requires_usb_fix).toBe(true);
    expect(summary.camera_wysiwyg_recovery_blocks_mapping_start).toBe(true);
    expect(summary.camera_wysiwyg_recovery_blocks_free_move).toBe(false);
    expect(summary.camera_wysiwyg_recovery_sends_motion).toBe(false);
    expect(summary.camera_wysiwyg_recovery_starts_map_runtime).toBe(false);
    expect(summary.camera_wysiwyg_recovery_source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
    expect(summary.camera_wysiwyg_recovery_source_not_exclusive).toBe("true");
    expect(summary.camera_wysiwyg_recovery_shared_preview_single_upstream).toBe(true);
    expect(summary.camera_shared_preview_endpoint).toBe("/api/robot-control/camera/mjpeg");
    expect(summary.camera_shared_preview_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.camera_shared_preview_single_upstream).toBe(true);
    expect(summary.camera_shared_preview_auto_joins).toBe(true);
    expect(summary.camera_shared_preview_everyone_can_join).toBe(true);
    expect(summary.camera_shared_preview_current_frame_visible).toBe(false);
    expect(summary.camera_shared_preview_gap_plain).toContain("共享入口可加入");
    expect(summary.camera_shared_preview_readback_only).toBe(true);
    expect(summary.camera_shared_preview_starts_camera_exclusive_capture).toBe(false);
    expect(summary.camera_shared_preview_sends_motion).toBe(false);
    expect(summary.camera_shared_preview_shared_capture).toBe("true");
    expect(summary.camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.camera_shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
    expect(summary.camera_shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
    expect(summary.camera_shared_preview_multi_viewer_plain).toContain("谁打开页面都接入");
    expect(summary.camera_shared_preview_access_plain).toContain("不是页面独占");
    expect(summary.camera_shared_preview_realtime_plain).toContain("当前没有实时画面");
    expect(summary.field_acceptance_hardware_action_ids).toEqual(["camera_usb_recovery"]);
    expect(summary.field_acceptance_hardware_action_labels).toEqual(["换高速USB后复测"]);
    expect(summary.field_acceptance_hardware_action_after_readback_endpoints).toEqual(["/api/robot-control/camera/first-frame/probe"]);
    expect(summary.field_acceptance_hardware_action_after_readback_sequences).toEqual([
      "/api/robot-control/camera/first-frame/probe|/api/robot-control/camera/mjpeg/status|/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_hardware_action_after_readback_sequence_labels).toEqual([
      "复测相机首帧|读取共享预览状态|刷新当前卡点",
    ]);
    expect(summary.field_acceptance_primary_hardware_action_id).toBe("camera_usb_recovery");
    expect(summary.field_acceptance_primary_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.field_acceptance_primary_hardware_action_after_readback_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.field_acceptance_primary_hardware_action_after_readback_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_primary_hardware_action_after_readback_sequence_labels).toEqual([
      "复测相机首帧",
      "读取共享预览状态",
      "刷新当前卡点",
    ]);
    expect(summary.field_acceptance_primary_hardware_action_blocks_mapping_start).toBe(true);
    expect(summary.field_acceptance_primary_hardware_action_blocks_free_move).toBe(false);
    expect(summary.current_hardware_action_required).toBe(true);
    expect(summary.current_hardware_action_id).toBe("camera_usb_recovery");
    expect(summary.current_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.current_hardware_action_plain).toContain("需要设备处理：换高速USB后复测");
    expect(summary.current_hardware_action_after_readback_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.current_hardware_action_after_readback_sequence).toEqual(summary.field_acceptance_primary_hardware_action_after_readback_sequence);
    expect(summary.current_hardware_action_after_readback_sequence_labels).toEqual(summary.field_acceptance_primary_hardware_action_after_readback_sequence_labels);
    expect(summary.current_hardware_action_blocks_mapping_start).toBe(true);
    expect(summary.current_hardware_action_blocks_free_move).toBe(false);
    expect(summary.current_hardware_action_sends_motion).toBe(false);
    expect(summary.field_acceptance_hardware_actions).toEqual([
      expect.objectContaining({
        id: "camera_usb_recovery",
        label: "换高速USB后复测",
        blocks_camera_wysiwyg: true,
        blocks_mapping_start: true,
        blocks_free_move: false,
        after_action_readback_endpoint: "/api/robot-control/camera/first-frame/probe",
        after_action_readback_method: "POST",
        after_action_readback_sequence: [
          "/api/robot-control/camera/first-frame/probe",
          "/api/robot-control/camera/mjpeg/status",
          "/api/robot-control/summary",
        ],
        after_action_readback_sequence_labels: [
          "复测相机首帧",
          "读取共享预览状态",
          "刷新当前卡点",
        ],
        sends_motion_when_clicked: false,
        starts_nav2_when_clicked: false,
        starts_manual_when_clicked: false,
        starts_free_roam_when_clicked: false,
        starts_map_runtime_when_clicked: false,
      }),
    ]);
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).toContain("需要设备处理：换高速USB后复测");
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).toContain("当前设备提示");
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).not.toContain("当前硬件提示");
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).toContain("USB 12M full-speed");
    expect(summary.field_acceptance_remaining_hardware_action_summary_plain).toContain("不阻塞低速自由移动");
    expect(summary.field_acceptance_remaining_action_summary_plain).toContain("相机缺口");
    expect(summary.live_closure_summary?.camera_blocks_mapping_start).toBe(true);
    expect(summary.camera_blocks_mapping_start).toBe(true);
    expect(summary.live_closure_summary?.camera_blocks_free_move).toBe(false);
    expect(summary.camera_blocks_free_move).toBe(false);
    expect(summary.live_closure_summary?.camera_reprobe_after_hardware_action_required).toBe(true);
    expect(summary.camera_reprobe_after_hardware_action_required).toBe(true);
    expect(summary.live_closure_summary?.camera_reprobe_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.camera_reprobe_sequence).toEqual(summary.live_closure_summary?.camera_reprobe_sequence);
    expect(summary.camera_reprobe_sequence_labels).toEqual(summary.live_closure_summary?.live_wysiwyg_camera_recovery_sequence_labels);
    expect(summary.camera_reprobe_sequence_sends_motion).toBe(false);
    expect(summary.camera_hardware_action_next_action_plain).toContain("换高速USB后复测");
    expect(summary.camera_recovery_starts_map_runtime).toBe(false);
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("画面未显示（换高速USB后复测）");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).not.toContain("画面/地图/雷达点");
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toContain("camera");
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toContain("radar_map_points");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_label).toBe("刷新雷达扫描读数");
    const wysiwygObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "wysiwyg");
    expect(wysiwygObjective?.next_action_plain).toBe("下一步：刷新雷达扫描读数。");
    expect(wysiwygObjective?.source_card_id).toBe("radar_map_points");
  });

  it("names the camera WYSIWYG action as USB hardware recovery when radar is already current", async () => {
    // 雷达和地图已经 WYSIWYG 时，剩余相机缺口必须直接告诉现场先换高速 USB，再复测首帧。
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
      if (url.pathname === "/api/camera/health") {
        return new Response(JSON.stringify({
          ...basePayload,
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_usage: {
            status: "not_in_use",
            owner_count: 0,
            owners: [],
          },
          uvc_usb_topology: {
            status: "uvc_video_on_full_speed_usb",
            video_usb_speed: "12M",
            next_action: "move_camera_to_high_speed_usb_port_or_powered_hub",
          },
          source_diagnosis: {
            status: "uvc_full_speed_usb_not_exclusive",
            not_exclusive: true,
          },
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.pathname === "/api/map/preview") {
        return new Response(JSON.stringify({
          ...basePayload,
          map_current_visible: true,
          map_once_observed: true,
          radar_overlay_status: "loaded",
          radar_overlay_point_count: 5,
          radar_overlay_current_point_count: 5,
          radar_overlay_source_point_count: 6,
          radar_overlay_refresh_required: false,
          radar_overlay_blocks_wysiwyg: false,
        }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify(basePayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });

    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toEqual(["camera"]);
    expect(summary.live_closure_summary?.radar_map_points_visible).toBe(true);
    expect(summary.live_closure_summary?.camera_hardware_action_required).toBe(true);
    expect(summary.live_closure_summary?.camera_hardware_action_label).toBe("换高速USB后复测");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_label).toBe("换高速USB后复测相机首帧");
    const wysiwygObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "wysiwyg");
    expect(wysiwygObjective?.next_action_plain).toBe("下一步：换高速USB后复测相机首帧。");
    expect(wysiwygObjective?.source_card_id).toBe("camera_preview");
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
    expect(summary.free_move_start_ready).toBe(true);
    expect(summary.free_move_ready).toBe(true);
    expect(summary.free_move_running).toBe(false);
    expect(summary.free_move_complete).toBe(false);
    expect(summary.free_roam_start_ready).toBe(true);
    expect(summary.free_roam_ready).toBe(true);
    expect(summary.free_roam_motion_start_ready).toBe(true);
    expect(summary.free_roam_motion_ready).toBe(false);
    expect(summary.free_move_without_camera_allowed).toBe(true);
    expect(summary.free_roam_motion_without_radar_allowed).toBe(true);
    expect(summary.live_closure_summary?.free_move_minimal_precheck_safety_only).toBe(true);
    expect(summary.free_move_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.free_move_safety_confirm_required).toBe(true);
    expect(summary.free_move_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.free_move_camera_preflight_required).toBe(false);
    expect(summary.free_move_camera_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.free_move_radar_preflight_required).toBe(false);
    expect(summary.free_move_radar_preflight_required).toBe(false);
    expect(summary.live_closure_summary?.free_move_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.free_move_blocked_by_camera_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.free_move_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.free_move_blocked_by_radar_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.fixed_free_roam_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
    expect(summary.fixed_free_roam_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
    expect(summary.live_closure_summary?.fixed_free_roam_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
    expect(summary.fixed_free_roam_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
    expect(summary.live_closure_summary?.fixed_free_roam_latest_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.fixed_free_roam_latest_endpoint).toBe("/api/robot-control/free-roam/autonomy/latest");
    expect(summary.free_roam_start_endpoint).toBe(summary.free_move_start_endpoint);
    expect(summary.free_roam_stop_endpoint).toBe(summary.free_move_stop_endpoint);
    expect(summary.free_roam_latest_endpoint).toBe(summary.fixed_free_roam_latest_endpoint);
    expect(summary.free_roam_acceptance_endpoints).toEqual(summary.free_move_acceptance_endpoints);
    expect(summary.free_roam_readback_endpoints).toEqual(summary.free_move_readback_endpoints);
    expect(summary.free_roam_required_success_markers).toEqual(summary.free_move_required_success_markers);
    expect(summary.free_roam_missing_evidence).toEqual(summary.free_move_missing_evidence);
    expect(summary.live_closure_summary?.mapping_start_ready).toBe(false);
    expect(summary.mapping_start_ready).toBe(false);
    expect(summary.free_roam_mapping_start_ready).toBe(false);
    expect(summary.live_closure_summary?.mapping_start_requires_camera_first_frame).toBe(true);
    expect(summary.mapping_start_requires_camera_first_frame).toBe(true);
    expect(summary.live_closure_summary?.mapping_start_requires_lidar_fresh).toBe(true);
    expect(summary.mapping_start_requires_lidar_fresh).toBe(true);
    expect(summary.live_closure_summary?.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.mapping_start_missing_evidence).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.mapping_start_only_camera_missing).toBe(false);
    expect(summary.free_roam_mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
    expect(summary.live_closure_summary?.mapping_acceptance_missing_reasons).toEqual([
      "camera_first_frame",
      "lidar_fresh",
      "mapping_active",
      "fresh_map_preview",
    ]);
    expect(summary.mapping_acceptance_ready).toBe(false);
    expect(summary.mapping_acceptance_missing_reasons).toEqual(summary.live_closure_summary?.mapping_acceptance_missing_reasons);
    expect(summary.free_roam_mapping_ready).toBe(false);
    expect(summary.free_roam_mapping_missing_reasons).toEqual(summary.live_closure_summary?.mapping_acceptance_missing_reasons);
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("建图启动还差：画面首帧、雷达新鲜");
    expect(summary.mapping_start_unblock_plain).toContain("建图启动还差：画面首帧、雷达新鲜");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("自由移动仍可先做");
    expect(summary.mapping_start_unblock_plain).toContain("自由移动仍可先做");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("只读复测相机首帧和 MJPEG 状态");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).not.toContain("。；");
    expect(summary.live_closure_summary?.mapping_camera_blocks_start).toBe(true);
    expect(summary.mapping_camera_blocks_start).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_blocks_start).toBe(true);
    expect(summary.mapping_lidar_blocks_start).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_readback_ready).toBe(false);
    expect(summary.mapping_lidar_fresh_readback_ready).toBe(false);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_gate_conflict).toBe(false);
    expect(summary.mapping_lidar_fresh_gate_conflict).toBe(false);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_gate_status).toBe("missing");
    expect(summary.mapping_lidar_fresh_gate_status).toBe("missing");
    expect(summary.live_closure_summary?.mapping_lidar_fresh_next_action_plain).toContain("建图启动仍缺雷达新鲜读数");
    expect(summary.mapping_lidar_fresh_next_action_plain).toContain("建图启动仍缺雷达新鲜读数");
    expect(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.mapping_lidar_fresh_refresh_sequence).toEqual(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sequence);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "读取雷达状态",
      "刷新总览",
    ]);
    expect(summary.mapping_lidar_fresh_refresh_sequence_labels).toEqual(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sequence_labels);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sends_motion).toBe(false);
    expect(summary.mapping_lidar_fresh_refresh_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.mapping_lidar_fresh_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_blocks_free_move).toBe(false);
    expect(summary.mapping_lidar_fresh_blocks_free_move).toBe(false);
    expect(summary.live_closure_summary?.mapping_unblock_allows_free_move).toBe(true);
    expect(summary.mapping_unblock_allows_free_move).toBe(true);
    expect(summary.live_closure_summary?.mapping_unblock_camera_diagnosis_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.mapping_unblock_camera_not_exclusive).toBe("not_loaded");
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_next_action_plain).toBe("先复测相机首帧并读取共享预览状态；拿到首帧后再刷新当前所见和建图条件。");
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_sequence_labels).toEqual([
      "复测相机首帧",
      "读取共享预览状态",
      "刷新当前卡点",
    ]);
    expect(summary.mapping_unblock_camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.mapping_unblock_camera_recovery_next_action_plain);
    expect(summary.mapping_unblock_camera_recovery_sequence).toEqual(summary.live_closure_summary?.mapping_unblock_camera_recovery_sequence);
    expect(summary.mapping_unblock_camera_recovery_sequence_labels).toEqual(summary.live_closure_summary?.mapping_unblock_camera_recovery_sequence_labels);
    expect(summary.mapping_unblock_camera_recovery_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.camera_hardware_action_required).toBe(false);
    expect(summary.live_closure_summary?.camera_hardware_action_label).toBe("复测相机首帧");
    expect(summary.live_closure_summary?.camera_usb_full_speed_detected).toBe(false);
    expect(summary.live_closure_summary?.camera_blocks_mapping_start).toBe(true);
    expect(summary.live_closure_summary?.camera_blocks_free_move).toBe(false);
    expect(summary.live_closure_summary?.camera_reprobe_after_hardware_action_required).toBe(false);
    expect(summary.live_closure_summary?.camera_reprobe_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.fixed_mapping_unblock_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.fixed_mapping_unblock_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.fixed_mapping_unblock_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.fixed_mapping_unblock_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.fixed_mapping_unblock_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.fixed_mapping_unblock_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.mapping_unblock_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.fixed_mapping_start_endpoint).toBe("/api/robot-control/map/start");
    expect(summary.fixed_mapping_start_endpoint).toBe("/api/robot-control/map/start");
    expect(summary.live_closure_summary?.fixed_mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.fixed_mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
  });

  it("suppresses stale lidar_fresh mapping start gap when live radar readback is already fresh", async () => {
    // live 面向现场当前事实：如果雷达扫描和地图贴图已经 fresh/loaded，就不能继续把旧 lidar_fresh gate 当成当前建图缺口。
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
                { id: "lidar_fresh", label: "雷达新鲜", state: "not_proven", evidence: "旧状态机 gate 尚未刷新", next_action: "先刷新雷达" },
              ],
            },
            snapshot: {
              external_stop_requested: false,
              mapping_active: false,
            },
            cmd_vel_publish_enabled: false,
          },
        },
        "/api/map/proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_proof_latest",
          status: "map_once_artifact_metadata_observed",
          map_once_observed: true,
        },
        "/api/map/preview": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.map_preview_result",
          map_available: true,
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
          radar_overlay: {
            overlay_status: "loaded",
            scan_preview_points: [
              { x_m: 0.2, y_m: 0.1, range_m: 0.22, angle_rad: 0.46, frame_id: "laser_frame", source_index: 0 },
            ],
            scan_preview_point_count: 1,
            scan_preview_source_point_count: 1,
            scan_preview_frame_id: "laser_frame",
            robot_pose: { frame_id: "map", x: 1, y: 2, yaw: 0.1, source: "/amcl_pose" },
            blocked_reasons: [],
          },
        },
        "/api/radar/status": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.radar_status",
          continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
          continuity_window_status: "latest_proof_fresh_while_lifecycle_running",
          lifecycle_running: true,
          lifecycle_state: "running",
          latest_scan_proof_fresh: true,
          scan_preview_points: [
            { x_m: 0.2, y_m: 0.1, range_m: 0.22, angle_rad: 0.46, frame_id: "laser_frame", source_index: 0 },
          ],
          scan_preview_point_count: 1,
          scan_preview_source_point_count: 1,
          scan_preview_frame_id: "laser_frame",
        },
        "/api/radar/scan-proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result",
          latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
          latest_scan_proof_fresh: true,
          scan_preview_points: [
            { x_m: 0.2, y_m: 0.1, range_m: 0.22, angle_rad: 0.46, frame_id: "laser_frame", source_index: 0 },
          ],
          scan_preview_point_count: 1,
          scan_preview_source_point_count: 1,
          scan_preview_frame_id: "laser_frame",
          freshness: { status: "fresh", age_seconds: 1 },
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

    expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toContain("lidar_fresh");
    expect(summary.live_closure_summary?.mapping_lidar_fresh_readback_ready).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_gate_conflict).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_gate_status).toBe("readback_ready_boundary_missing");
    expect(summary.live_closure_summary?.mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
    expect(summary.live_closure_summary?.free_roam_mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
    expect(summary.mapping_start_only_camera_missing).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_blocks_start).toBe(false);
    expect(summary.live_closure_summary?.mapping_camera_blocks_start).toBe(true);
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("建图启动还差：画面首帧");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).not.toContain("雷达新鲜");
    expect(summary.live_closure_summary?.radar_map_points_visible).toBe(true);
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("画面未显示");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("图上行程还差路线显示、到点成功、同窗口轮速 L/R 非零、送达确认");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("键盘还差按住读到轮速 L/R 非零、松开后停稳");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("自由移动还差启动读回");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).not.toContain("未完成：行程/键盘/自由移动、");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).not.toContain("画面/地图/雷达点");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).not.toContain("雷达点未贴图");
    expect(summary.field_acceptance_wysiwyg_missing_surface_ids).toEqual(["camera"]);
    expect(summary.field_acceptance_wysiwyg_refresh_mode).toBe("camera_only");
    expect(summary.field_acceptance_packet?.wysiwyg_refresh_mode).toBe("camera_only");
    expect(summary.field_acceptance_wysiwyg_refresh_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_wysiwyg_focused_refresh_sequence).toEqual(summary.field_acceptance_wysiwyg_refresh_sequence);
    expect(summary.live_wysiwyg_focused_refresh_mode).toBe("camera_only");
    expect(summary.field_acceptance_wysiwyg_refresh_sequence_labels).toEqual([
      "复测相机首帧",
      "读取相机 MJPEG 状态",
      "刷新总览",
    ]);
    expect(summary.live_wysiwyg_focused_refresh_sequence_labels).toEqual(summary.field_acceptance_wysiwyg_refresh_sequence_labels);
    expect(summary.live_wysiwyg_focused_refresh_sends_motion).toBe(false);
    expect(summary.live_wysiwyg_focused_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.live_wysiwyg_focused_refreshes_radar_scan_proof).toBe(false);
    expect(summary.live_wysiwyg_focused_refreshes_map_preview).toBe(false);
    expect(summary.live_wysiwyg_focused_refreshes_radar_status).toBe(false);
    expect(summary.field_acceptance_packet?.wysiwyg_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.field_acceptance_packet?.wysiwyg_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.field_acceptance_packet?.wysiwyg_refreshes_radar_scan_proof).toBe(false);
    expect(summary.field_acceptance_packet?.wysiwyg_refreshes_map_preview).toBe(false);
    expect(summary.field_acceptance_packet?.wysiwyg_refreshes_radar_status).toBe(false);
    expect(summary.field_acceptance_wysiwyg_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.field_acceptance_wysiwyg_refreshes_radar_scan_proof).toBe(false);
    expect(summary.field_acceptance_wysiwyg_refreshes_map_preview).toBe(false);
    expect(summary.field_acceptance_wysiwyg_refreshes_radar_status).toBe(false);
    expect(summary.field_acceptance_no_motion_readback_action_ids).toEqual([
      "readback_all",
      "refresh_camera_first_frame",
    ]);
    expect(summary.field_acceptance_no_motion_readback_action_labels).toEqual([
      "复验全部读数",
      "复测相机首帧",
    ]);
    expect(summary.field_acceptance_primary_no_motion_readback_action_id).toBe("refresh_camera_first_frame");
    expect(summary.field_acceptance_primary_no_motion_readback_action_label).toBe("复测相机首帧");
    expect(summary.field_acceptance_primary_no_motion_readback_action_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.field_acceptance_primary_no_motion_readback_id).toBe("refresh_camera_first_frame");
    expect(summary.field_acceptance_primary_no_motion_readback_label).toBe("复测相机首帧");
    expect(summary.field_acceptance_primary_no_motion_readback_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.field_acceptance_primary_no_motion_readback_method).toBe("POST");
    expect(summary.field_acceptance_primary_no_motion_readback_action_sequence).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ]);
    expect(summary.field_acceptance_primary_no_motion_readback_sequence).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence);
    expect(summary.field_acceptance_primary_no_motion_readback_sequence_labels).toEqual(summary.field_acceptance_primary_no_motion_readback_action_sequence_labels);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.field_acceptance_primary_no_motion_readback_action_refreshes_radar_scan_proof).toBe(false);
    expect(summary.field_acceptance_primary_no_motion_readback_action_sends_motion).toBe(false);
    expect(summary.field_acceptance_primary_no_motion_readback_sends_motion).toBe(false);
  });

  it("uses free-roam latest mapping start gaps before stale runtime gate rows", async () => {
    // 上车 latest 已复算建图启动只差相机时，live-summary 不能继续沿用旧 gate 里的 lidar_fresh。
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
            status: "loaded",
            free_roam_motion_start_ready: true,
            free_move_start_ready: true,
            motion_start_ready: true,
            motion_without_radar_allowed: true,
            free_move_without_camera_allowed: true,
            free_roam_mapping_start_ready: false,
            free_roam_mapping_start_missing_reasons: ["camera_first_frame_not_observed"],
            free_roam_mapping_missing_reasons: ["camera_first_frame", "mapping_active", "fresh_map_preview"],
            free_roam_mapping_start_plain: "建图启动未就绪，还差 camera_first_frame_not_observed；低速自由移动不受影响。",
            free_roam_mapping_start_next_action: "先补齐画面首帧；需要移动时可先勾安全确认低速自由移动。",
            decision: {
              state: "stopping",
              reason: "现场请求停止",
              gates: [
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "stop endpoint ready", next_action: "继续监看" },
                { id: "camera_first_frame", label: "画面首帧", state: "not_proven", evidence: "画面首帧未出", next_action: "检查画面" },
                { id: "lidar_fresh", label: "雷达新鲜", state: "not_proven", evidence: "旧 runtime gate 尚未刷新", next_action: "先刷新雷达" },
              ],
            },
            snapshot: {
              external_stop_requested: true,
              mapping_active: false,
            },
            artifact_only: true,
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

    expect(summary.readback_summary.free_roam.mapping_start_missing).toBe("camera_first_frame");
    expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
    expect(summary.live_closure_summary?.mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
    expect(summary.live_closure_summary?.free_roam_mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
    expect(summary.live_closure_summary?.mapping_lidar_blocks_start).toBe(false);
    expect(summary.live_closure_summary?.mapping_lidar_fresh_gate_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.mapping_lidar_fresh_next_action_plain).toContain("建图雷达新鲜读回尚未证明");
    expect(summary.live_closure_summary?.mapping_lidar_fresh_next_action_plain).not.toContain("gate 已满足");
    expect(summary.mapping_lidar_fresh_next_action_plain).toBe(summary.live_closure_summary?.mapping_lidar_fresh_next_action_plain);
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("建图启动还差：画面首帧");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).not.toContain("雷达新鲜");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("建图启动还差画面首帧");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).not.toContain("建图启动还差画面首帧、雷达新鲜");
  });

  it("does not draw stale radar scan proof points as current map overlay", async () => {
    // 地图雷达 overlay 的点来自 scan proof；proof stale 时，即使有旧点数组也不能标成当前 WYSIWYG。
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
        "/api/map/preview": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.map_preview_result",
          status: "loaded",
          map_name: "trashbot_map",
          map_yaml_name: "trashbot_map.yaml",
          map_image_name: "trashbot_map.pgm",
          width: 8,
          height: 8,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 2, unknown: 62, occupied: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
        },
        "/api/radar/status": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.radar_status",
          continuous_scan_status: "latest_proof_stale_while_lifecycle_running",
          continuity_window_status: "latest_proof_stale_while_lifecycle_running",
          lifecycle_running: true,
          lifecycle_state: "running",
          latest_scan_proof_fresh: false,
          scan_proof_latest: {
            latest_scan_once_observed: true,
            latest_scan_hz_observed: true,
            latest_raw_packet_once_observed: true,
            latest_tf_observed: true,
            scan_preview_points: [{ x_m: 0.1, y_m: 0.2, range_m: 0.22, angle_rad: 1.1, frame_id: "laser_frame", source_index: 0 }],
            scan_preview_point_count: 1,
            scan_preview_source_point_count: 3,
            scan_preview_frame_id: "laser_frame",
            freshness: { status: "stale", age_seconds: 1200 },
          },
        },
        "/api/radar/scan-proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result",
          latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
          latest_scan_once_observed: true,
          latest_scan_hz_observed: true,
          latest_raw_packet_once_observed: true,
          latest_tf_observed: true,
          scan_preview_points: [{ x_m: 0.1, y_m: 0.2, range_m: 0.22, angle_rad: 1.1, frame_id: "laser_frame", source_index: 0 }],
          scan_preview_point_count: 1,
          scan_preview_source_point_count: 3,
          scan_preview_frame_id: "laser_frame",
          freshness: { status: "stale", age_seconds: 1200 },
        },
        "/api/nav2/proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          amcl_pose: { frame_id: "map", x: 1, y: 2, yaw: 0 },
          path_preview_points: [
            { x: 1, y: 2, frame_id: "map", source_index: 0 },
            { x: 1.5, y: 2.2, frame_id: "map", source_index: 1 },
          ],
          path_preview_point_count: 2,
          path_preview_frame_id: "map",
        },
      };
      const payload = payloadByPath[url.pathname] ?? basePayload;
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const preview = await buildMapPreviewProxy("http://192.168.1.11:8787");

    expect(preview.proxy_status).toBe("preview_forwarded");
    expect(preview.radar_overlay_status).toBe("not_current");
    expect(preview.radar_overlay_point_count).toBe(0);
    expect(preview.radar_overlay_source_point_count).toBe(3);
    expect(preview.radar_overlay?.blocked_reasons).toContain("runtime_scan_stale_for_map_radar_overlay");
    expect(preview.radar_overlay_wysiwyg_status_plain).toContain("当前不贴到地图");
    expect(preview.radar_overlay_next_action).toBe("refresh_radar_scan_for_map_overlay");
    expect(preview.radar_overlay?.scan_preview_points).toEqual([]);

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });
    expect(summary.readback_summary.map.radar_overlay_status).toBe("not_current");
    expect(summary.readback_summary.map.radar_overlay_point_count).toBe("0");
    expect(summary.readback_summary.map.radar_overlay_source_point_count).toBe("3");
    expect(summary.readback_summary.map.radar_overlay_refresh_required).toBe("true");
    expect(summary.readback_summary.map.radar_overlay_stale_source_points_suppressed).toBe("true");
    expect(summary.readback_summary.map.radar_overlay_primary_blocked_reason).toBe("runtime_scan_stale_for_map_radar_overlay");
    expect(summary.readback_summary.map.radar_overlay_current_vs_source_plain).toBe("地图雷达点：当前 0 个，来源 3 个；旧来源点已抑制，未贴到当前地图；下一步：刷新雷达扫描，再刷新地图画面。");
    expect(summary.readback_summary.map.radar_overlay_blocked_reasons).toContain("runtime_scan_stale_for_map_radar_overlay");
    expect(summary.live_closure_summary?.radar_map_points_visible).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_stale_source_points_suppressed).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_diagnostic_plain).toContain("旧来源点 3 个未贴图");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_diagnostic_plain).toContain("刷新雷达扫描读数，再刷新地图画面");
    expect(summary.live_closure_summary?.live_wysiwyg_map_radar_diagnostic_plain).toContain("旧来源点已抑制");
    expect(summary.live_closure_summary?.live_wysiwyg_map_radar_diagnostic_plain).toContain("不贴到当前地图");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_next_action_plain).toBe("旧雷达来源点 3 个已抑制；先刷新雷达扫描读数，再刷新地图画面，确认同轮雷达点贴图。");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "读取雷达状态",
      "刷新地图画面",
      "刷新总览",
    ]);
  });

  it("uses map preview embedded radar overlay before fallback readback overlay", async () => {
    // 新版上车 map preview 已经把当前地图雷达层随图返回；PC 代理必须优先使用这份画面本体证据。
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
        "/api/map/preview": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.map_preview_result",
          status: "loaded",
          map_name: "trashbot_map",
          width: 8,
          height: 8,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 2, unknown: 62, occupied: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
          radar_overlay: {
            overlay_status: "loaded",
            scan_preview_points: [
              { x_m: 0.2, y_m: 0.1, range_m: 0.22, angle_rad: 0.46, frame_id: "laser_frame", source_index: 0 },
              { x_m: 0.3, y_m: 0.2, range_m: 0.36, angle_rad: 0.58, frame_id: "laser_frame", source_index: 1 },
            ],
            scan_preview_point_count: 2,
            scan_preview_source_point_count: 138,
            scan_preview_frame_id: "laser_frame",
            robot_pose: { frame_id: "map", x: 1, y: 2, yaw: 0.1, source: "/amcl_pose" },
            blocked_reasons: [],
          },
        },
        "/api/radar/status": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.radar_status",
          continuous_scan_status: "latest_proof_stale_while_lifecycle_running",
          continuity_window_status: "latest_proof_stale_while_lifecycle_running",
          lifecycle_running: true,
          lifecycle_state: "running",
          latest_scan_proof_fresh: false,
          scan_proof_latest: {
            scan_preview_points: [{ x_m: 0.1, y_m: 0.2, range_m: 0.22, angle_rad: 1.1, frame_id: "laser_frame", source_index: 0 }],
            scan_preview_point_count: 1,
            scan_preview_source_point_count: 3,
            scan_preview_frame_id: "laser_frame",
            freshness: { status: "stale", age_seconds: 1200 },
          },
        },
        "/api/radar/scan-proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result",
          latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
          scan_preview_points: [{ x_m: 0.1, y_m: 0.2, range_m: 0.22, angle_rad: 1.1, frame_id: "laser_frame", source_index: 0 }],
          scan_preview_point_count: 1,
          scan_preview_source_point_count: 3,
          scan_preview_frame_id: "laser_frame",
          freshness: { status: "stale", age_seconds: 1200 },
        },
        "/api/nav2/proof/latest": {
          ...basePayload,
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          amcl_pose: { frame_id: "map", x: 1, y: 2, yaw: 0 },
          path_preview_points: [
            { x: 1, y: 2, frame_id: "map", source_index: 0 },
            { x: 1.5, y: 2.2, frame_id: "map", source_index: 1 },
          ],
          path_preview_point_count: 2,
          path_preview_frame_id: "map",
        },
      };
      const payload = payloadByPath[url.pathname] ?? basePayload;
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }));

    const preview = await buildMapPreviewProxy("http://192.168.1.11:8787");

    expect(preview.proxy_status).toBe("preview_forwarded");
    expect(preview.radar_overlay_status).toBe("loaded");
    expect(preview.radar_overlay_point_count).toBe(2);
    expect(preview.radar_overlay_source_point_count).toBe(138);
    expect(preview.radar_overlay_refresh_required).toBe(false);
    expect(preview.radar_overlay_primary_blocked_reason).toBe("none");
    expect(preview.radar_overlay?.source_endpoint_ids).toEqual(["map_preview"]);
    expect(preview.radar_overlay_wysiwyg_status_plain).toBe("雷达点已贴到当前地图：当前显示 2 个点，frame=laser_frame。");
    expect(preview.map_wysiwyg_status_plain).toContain("雷达标记都已按当前读数显示");

    const summary = await buildRobotControlSummary("http://192.168.1.11:8787", null, null, {
      readbackTimeoutMs: 100,
    });
    expect(summary.readback_summary.map.radar_overlay_status).toBe("loaded");
    expect(summary.readback_summary.map.radar_overlay_point_count).toBe("2");
    expect(summary.readback_summary.map.radar_overlay_source_point_count).toBe("138");
    expect(summary.readback_summary.map.radar_overlay_refresh_required).toBe("false");
    expect(summary.live_closure_summary?.radar_map_points_visible).toBe(true);
    expect(summary.live_closure_summary?.radar_overlay_needs_refresh).toBe(false);
    expect(summary.live_closure_summary?.radar_overlay_blocks_wysiwyg).toBe(false);
    expect(summary.live_closure_summary?.radar_overlay_blocks_free_move).toBe(false);
    expect(summary.radar_overlay_wysiwyg_complete).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).not.toContain("radar_map_points");
    expect(summary.live_closure_summary?.side_blocker_ids).not.toContain("radar_map_points_wysiwyg");
    expect(summary.live_closure_summary?.side_gap_summary_plain).not.toContain("雷达点贴到地图");
    expect(summary.live_closure_summary?.side_gap_summary_plain).toContain("传感器就绪后建图");
  });
});
