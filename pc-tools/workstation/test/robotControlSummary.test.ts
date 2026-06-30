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
    expect(summary.live_closure_summary?.summary_plain).toBe(
      "当前卡点：图上路线已经有执行成功读数，但同窗口轮速 L/R 还没有非零闭环。",
    );
    expect(summary.live_closure_summary?.summary_plain).not.toContain("wheel raw");
    expect(summary.live_closure_summary?.next_action_plain).toBe(
      "勾现场安全确认后重跑图上路线，并在同一个执行窗口复验轮速 L/R 非零。",
    );
    expect(summary.live_closure_summary?.next_action_plain).not.toContain("wheel raw");
    expect(summary.live_closure_summary?.objective_audit_status).toBe("in_progress");
    expect(summary.live_closure_summary?.objective_audit_total_count).toBe(4);
    expect(summary.live_closure_summary?.objective_audit_done_count).toBeGreaterThanOrEqual(1);
    expect(summary.live_closure_summary?.objective_audit_remaining_count).toBeGreaterThan(0);
    expect(summary.live_closure_summary?.objective_audit_missing_objective_ids).toContain("motion");
    expect(summary.live_closure_summary?.objective_audit_summary_plain).toContain("四项目标完成");
    expect(summary.live_closure_summary?.fixed_objective_audit_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.objective_audit_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.objective_audit_items).toHaveLength(4);
    const motionObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "motion");
    expect(motionObjective?.completed).toBe(false);
    expect(motionObjective?.actionable).toBe(true);
    expect(motionObjective?.item_ids).toEqual(["nav2_route_execution", "keyboard_continuous_control", "free_move"]);
    expect(motionObjective?.summary_plain).toContain("图上行程");
    expect(motionObjective?.sends_motion_when_clicked).toBe(false);
    const wysiwygObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "wysiwyg");
    expect(wysiwygObjective?.item_ids).toEqual(["camera_wysiwyg", "map_wysiwyg", "radar_map_points_wysiwyg"]);
    const mappingObjective = summary.live_closure_summary?.objective_audit_items.find((item) => item.id === "mapping");
    expect(mappingObjective?.summary_plain).not.toContain("camera_first_frame");
    expect(mappingObjective?.next_action_plain).not.toContain("camera_first_frame");
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
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("wheel L/R=0/0");
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("样本 2 个");
    expect(summary.live_closure_summary?.wheel_rerun_readback_plain).toContain("非零样本 0 个");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("先勾现场安全确认");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("确认同窗口 wheel L/R 非零");
    expect(summary.live_closure_summary?.wheel_rerun_checklist_plain).toContain("delivery success");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_plain).toContain("goal_succeeded");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_plain).toContain("delivery success 与本轮行程材料对齐");
    expect(summary.live_closure_summary?.wheel_rerun_acceptance_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
      "/api/robot-control/delivery/latest",
    ]);
    expect(summary.live_closure_summary?.wheel_rerun_delivery_success_required).toBe(true);
    expect(summary.live_closure_summary?.wheel_rerun_delivery_next_action_plain).toContain("提交 delivery success");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_endpoint).toBe("/api/robot-control/nav2/goal/execute");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_latest_endpoint).toBe("/api/robot-control/nav2/goal/execution/latest");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_delivery_latest_endpoint).toBe("/api/robot-control/delivery/latest");
    expect(summary.live_closure_summary?.fixed_wheel_rerun_delivery_complete_endpoint).toBe("/api/robot-control/delivery/complete");
    expect(summary.live_closure_summary?.wheel_rerun_delivery_complete_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.fixed_wheel_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.map_display_primary_tool).toBe("pc_big_map");
    expect(summary.live_closure_summary?.map_display_primary_url).toBe("/map");
    expect(summary.live_closure_summary?.map_display_legacy_url).toBe("?view=map");
    expect(summary.live_closure_summary?.map_display_primary_action_label).toBe("进入地图大屏");
    expect(summary.live_closure_summary?.map_display_primary_action_opens_new_window).toBe(false);
    expect(summary.live_closure_summary?.map_display_primary_action_opens_current_page).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_default_observer).toBe(true);
    expect(summary.live_closure_summary?.map_display_direct_map_only).toBe(true);
    expect(summary.live_closure_summary?.map_display_default_zoom_percent).toBe("100%");
    expect(summary.live_closure_summary?.map_display_max_zoom_percent).toBe("2400%");
    expect(summary.live_closure_summary?.map_display_wysiwyg_overlays).toEqual(["image", "route", "robot", "radar"]);
    expect(summary.live_closure_summary?.map_display_ros2_companion_required).toBe(false);
    expect(summary.live_closure_summary?.map_display_ros2_companion_tools).toEqual(["rviz2", "foxglove"]);
    expect(summary.live_closure_summary?.map_display_rviz_launch_command).toBe("ros2 launch ros2_trashbot_bringup rviz.launch.py");
    expect(summary.live_closure_summary?.map_display_foxglove_bridge_package).toBe("foxglove_bridge");
    expect(summary.live_closure_summary?.map_display_foxglove_bridge_launch_command).toBe("ros2 launch foxglove_bridge foxglove_bridge_launch.xml");
    expect(summary.live_closure_summary?.map_display_foxglove_websocket_url).toBe("ws://192.168.1.11:8765");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("普通用户地图：进入 /map 使用 PC 大地图");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("默认 100% 整图铺满大画布");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("细节放大最高 2400%");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("ROS2 配套只作工程观察");
    expect(summary.live_closure_summary?.map_display_companion_plain).toContain("ws://192.168.1.11:8765");
    expect(summary.live_closure_summary?.map_display_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_ros2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_rviz2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_foxglove).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_nav2).toBe(false);
    expect(summary.live_closure_summary?.map_display_starts_map_runtime).toBe(false);
    expect(summary.live_closure_summary?.primary_status_item_id).toBe("nav2_route_execution");
    expect(summary.live_closure_summary?.side_blocker_ids).toEqual([
      "camera_wysiwyg",
      "radar_map_points_wysiwyg",
      "mapping_start",
    ]);
    expect(summary.live_closure_summary?.side_blocker_count).toBe(3);
    expect(summary.live_closure_summary?.ready_action_ids).toEqual([
      "free_move",
      "keyboard_continuous_control",
      "nav2_route_execution",
    ]);
    expect(summary.live_closure_summary?.ready_action_count).toBe(3);
    expect(summary.live_closure_summary?.side_gap_summary_plain).toBe(
      "其它缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图；可先做：自由自助移动、键盘连续手控、完整行程执行。",
    );
    expect(summary.live_closure_summary?.live_wysiwyg_ready).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toEqual(["camera", "radar_map_points"]);
    expect(summary.live_closure_summary?.live_wysiwyg_needs_refresh).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_readback_gap_surface_ids).toEqual([]);
    expect(summary.live_closure_summary?.live_wysiwyg_primary_readback_gap_surface_id).toBe("none");
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_endpoints).toEqual([
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/radar/scan-proof/refresh",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_refresh_labels).toEqual([
      "复测相机首帧",
      "刷新雷达扫描读数",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.live_wysiwyg_primary_refresh_label).toBe("复测相机首帧");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_probe_failure_reason).toBe("none");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_status).toBe("not_loaded");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_not_exclusive).toBe("not_loaded");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_client_count).toBe("0");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_upstream_active).toBe("false");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_exclusive_camera_claim).toBe("false");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_status).toBe("needs_probe");
    expect(summary.live_closure_summary?.live_wysiwyg_camera_recovery_next_action_plain).toBe("先复测相机首帧并读取共享预览状态；拿到首帧后再刷新当前所见和建图条件。");
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
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_source_point_count).toBe("not_loaded");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_stale_source_points_suppressed).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_primary_blocked_reason).toBe("scan_preview_points_missing");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_next_action_plain).toContain("刷新雷达扫描读数");
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/map/preview",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "刷新地图画面",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_diagnostic_plain).toContain("画面诊断：首帧未证明");
    expect(summary.live_closure_summary?.live_wysiwyg_diagnostic_plain).toContain("还差=地图缺雷达点；小车地图位置未读到");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_radar_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_map_preview_endpoint).toBe("/api/robot-control/map/preview");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_radar_status_endpoint).toBe("/api/robot-control/radar/status");
    expect(summary.live_closure_summary?.fixed_live_wysiwyg_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_plan_available).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sequence).toEqual([
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/map/preview",
      "/api/robot-control/radar/status",
      "/api/robot-control/camera/mjpeg/status",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "复测相机首帧",
      "刷新地图画面",
      "读取雷达状态",
      "读取相机 MJPEG 状态",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_radar_scan_proof).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_camera_first_frame_probe).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_map_preview).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_radar_status).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refreshes_camera_mjpeg_status).toBe(true);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_nav2).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_manual).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_keyboard).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_free_roam).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_radar_lifecycle).toBe(false);
    expect(summary.live_closure_summary?.live_wysiwyg_refresh_starts_map_runtime).toBe(false);
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
    expect(summary.live_closure_summary?.fixed_keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
    expect(summary.live_closure_summary?.fixed_keyboard_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.keyboard_continuous_post_hold_feedback_readback_required).toBe(true);
    expect(summary.live_closure_summary?.keyboard_continuous_post_hold_summary_refresh_required).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_action_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
      "start_mapping_when_sensors_ready",
    ]);
    expect(summary.live_closure_summary?.live_motion_runbook_ready_action_ids).toEqual([
      "run_nav2_route",
      "hold_keyboard",
      "start_free_move",
    ]);
    expect(summary.live_closure_summary?.live_motion_runbook_blocked_action_ids).toEqual([
      "start_mapping_when_sensors_ready",
    ]);
    expect(summary.live_closure_summary?.live_motion_runbook_primary_action_id).toBe("run_nav2_route");
    expect(summary.live_closure_summary?.live_motion_runbook_start_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execute",
      "/api/robot-control/base/manual",
      "/api/robot-control/free-roam/autonomy/start",
    ]);
    expect(summary.live_closure_summary?.live_motion_runbook_acceptance_endpoints).toEqual([
      "/api/robot-control/nav2/goal/execution/latest",
      "/api/robot-control/base/feedback-samples",
      "/api/robot-control/summary",
      "/api/robot-control/delivery/latest",
      "/api/robot-control/free-roam/autonomy/latest",
      "/api/robot-control/map/preview",
    ]);
    expect(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_safety_only).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_safety_confirm_required).toBe(true);
    expect(summary.live_closure_summary?.live_motion_runbook_ready_plain).toBe(
      "可先执行：完整行程执行、键盘连续手控、自由自助移动。",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_blocked_plain).toBe(
      "暂不可执行：传感器就绪后建图。",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_primary_action_plain).toBe("完整行程执行");
    expect(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_plain).toBe(
      "发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "可先执行：完整行程执行、键盘连续手控、自由自助移动。",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "主推荐：完整行程执行",
    );
    expect(summary.live_closure_summary?.live_motion_runbook_summary_plain).toContain(
      "发车前预检已精简",
    );
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
          "/api/robot-control/nav2/goal/execution/latest",
          "/api/robot-control/base/feedback-samples",
          "/api/robot-control/summary",
          "/api/robot-control/delivery/latest",
        ],
        proof_plain: "可复验完整行程：勾现场安全确认后执行图上路线，执行后按验收端点读回；还差：同窗口 wheel L/R 非零、delivery success。",
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
    expect(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids).toContain("camera");
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
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("建图启动还差：画面首帧、雷达新鲜");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("自由移动仍可先做");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).toContain("只读复测相机首帧和 MJPEG 状态");
    expect(summary.live_closure_summary?.mapping_start_unblock_plain).not.toContain("。；");
    expect(summary.live_closure_summary?.mapping_camera_blocks_start).toBe(true);
    expect(summary.live_closure_summary?.mapping_lidar_blocks_start).toBe(true);
    expect(summary.live_closure_summary?.mapping_unblock_allows_free_move).toBe(true);
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
    expect(summary.live_closure_summary?.fixed_mapping_unblock_summary_endpoint).toBe("/api/robot-control/summary");
    expect(summary.live_closure_summary?.mapping_unblock_camera_recovery_sends_motion).toBe(false);
    expect(summary.live_closure_summary?.fixed_mapping_unblock_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
    expect(summary.live_closure_summary?.fixed_mapping_unblock_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
    expect(summary.live_closure_summary?.mapping_unblock_sends_motion_when_clicked).toBe(false);
    expect(summary.live_closure_summary?.fixed_mapping_start_endpoint).toBe("/api/robot-control/map/start");
    expect(summary.live_closure_summary?.fixed_mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
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
      "/api/robot-control/map/preview",
    ]);
    expect(summary.live_closure_summary?.live_wysiwyg_radar_map_refresh_sequence_labels).toEqual([
      "刷新雷达扫描读数",
      "刷新地图画面",
    ]);
  });
});
