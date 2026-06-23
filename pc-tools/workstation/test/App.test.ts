import { flushPromises, mount } from "@vue/test-utils";
import type { VueWrapper } from "@vue/test-utils";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import TrainingLabelingPanel from "../src/components/TrainingLabelingPanel.vue";
import { PROOF_FLAGS, type RobotControlSummaryResponse } from "../src/shared/contracts";

const SPRINT_ARTIFACT_DIR = resolve(
  process.cwd(),
  "../../sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts",
);

const DEFAULT_FIRST_SCREEN_FORBIDDEN_TOKENS = [
  "检查路径",
  "现场材料",
  "HIL",
  "Nav2",
  "proof",
  "key values",
  "/cmd_vel",
  "/api/base/manual",
  "可点动",
  "task_id",
  "O6",
  "O7",
  "Mock",
  "field manifest",
] as const;

const SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS = [
  "检查路径",
  "现场材料",
  "HIL",
  "Nav2",
  "proof",
  "key values",
  "/cmd_vel",
  "/api/base/manual",
  "task_id",
  "O6",
  "O7",
  "Mock",
  "field manifest",
] as const;

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
  "/api/hardware/wave-rover/material-coverage": {
    schema: "trashbot.pc_tools_workstation.hardware_materials.v1",
    fixture_root: "pc-tools/evidence/fixtures",
    vendor_sources: [
      {
        path: "docs/vendor/VENDOR_INDEX.md",
        fact_ids: ["vendor_index_source_of_truth", "orange_pi_uart_not_proven", "hardware_boundary"],
      },
      {
        path: "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        fact_ids: ["rpi_default_serial_example", "json_line_send", "readline_receive"],
      },
      {
        path: "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
        fact_ids: ["cmd_config_movement_ids", "feedback_interval_config_reference"],
      },
      {
        path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        fact_ids: ["cmd_id_definitions", "feedback_base_info_id"],
      },
      {
        path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
        fact_ids: ["newline_json_dispatch", "command_handler_dispatch"],
      },
      {
        path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
        fact_ids: ["t1001_feedback_fields", "module_type_conditional_fields"],
      },
    ],
    hardware_claim_level: "software_material_coverage",
    serial_reference: {
      vendor_rpi_default_device: "/dev/ttyAMA0",
      vendor_rpi_alternate_device: "/dev/serial0",
      baudrate: 115200,
      orange_pi_device_status: "not_proven",
    },
    command_facts: [
      {
        t: 1,
        name: "CMD_SPEED_CTRL",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 11,
        name: "CMD_PWM_INPUT",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 13,
        name: "CMD_ROS_CTRL",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 130,
        name: "CMD_BASE_FEEDBACK",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 131,
        name: "CMD_BASE_FEEDBACK_FLOW",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 142,
        name: "CMD_FEEDBACK_FLOW_INTERVAL",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
      {
        t: 143,
        name: "CMD_UART_ECHO_MODE",
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
        hardware_verified: false,
      },
    ],
    feedback_schema: {
      T1001: {
        base_fields: ["L", "R", "r", "p", "y", "v"],
        module_conditional_fields: ["moduleType=1 adds x/z/b/s/e/t and overwrites y with arm lastY"],
        source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
      },
    },
    required_materials: [
      {
        id: "feedback_T1001.log",
        required_path: "feedback_T1001.log",
        description: "WAVE ROVER T=1001 base feedback log material.",
      },
      {
        id: "odom_once.jsonl",
        required_path: "odom_once.jsonl",
        description: "One odom sample material exported as JSONL.",
      },
      {
        id: "imu_once.jsonl",
        required_path: "imu_once.jsonl",
        description: "One IMU sample material exported as JSONL.",
      },
      {
        id: "battery_once.jsonl",
        required_path: "battery_once.jsonl",
        description: "One battery sample material exported as JSONL.",
      },
      {
        id: "operator_hil_report",
        required_path: "operator_hil_report or operator_hil_report.json",
        description: "Operator HIL report material; file presence is not HIL pass.",
      },
    ],
    fixture_groups: [
      {
        group: "wave_rover_hil_packet_intake/pass",
        fixture_relative_path: "pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/pass",
        present_materials: [
          "feedback_T1001.log",
          "odom_once.jsonl",
          "imu_once.jsonl",
          "battery_once.jsonl",
          "operator_hil_report",
        ],
        missing_materials: [],
        coverage_counts: { present: 5, missing: 0, required: 5 },
        status: "material_coverage_complete_software_proof_only",
      },
      {
        group: "wave_rover_feedback_replay/pass",
        fixture_relative_path: "pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass",
        present_materials: ["feedback_T1001.log", "odom_once.jsonl", "imu_once.jsonl", "battery_once.jsonl"],
        missing_materials: ["operator_hil_report"],
        coverage_counts: { present: 4, missing: 1, required: 5 },
        status: "material_coverage_partial_software_proof_only",
      },
    ],
    groups: [
      {
        group: "wave_rover_hil_packet_intake/pass",
        fixture_relative_path: "pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/pass",
        present_materials: [
          "feedback_T1001.log",
          "odom_once.jsonl",
          "imu_once.jsonl",
          "battery_once.jsonl",
          "operator_hil_report",
        ],
        missing_materials: [],
        coverage_counts: { present: 5, missing: 0, required: 5 },
        status: "material_coverage_complete_software_proof_only",
      },
      {
        group: "wave_rover_feedback_replay/pass",
        fixture_relative_path: "pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass",
        present_materials: ["feedback_T1001.log", "odom_once.jsonl", "imu_once.jsonl", "battery_once.jsonl"],
        missing_materials: ["operator_hil_report"],
        coverage_counts: { present: 4, missing: 1, required: 5 },
        status: "material_coverage_partial_software_proof_only",
      },
    ],
    coverage_summary: {
      groups_total: 2,
      groups_complete: 1,
      groups_partial: 1,
      groups_missing: 0,
      required_per_group: 5,
    },
    vendor_facts_bounded: [
      "UART newline-delimited JSON",
      "FEEDBACK_BASE_INFO=1001",
      "json_cmd.h defines T=1/T=11/T=13/T=130/T=131/T=142/T=143 command IDs",
      "ugv_advance.h baseInfoFeedback() assembles T=1001 fields L/R/r/p/y/v",
    ],
    gaps: [
      {
        group: "wave_rover_feedback_replay/pass",
        fixture_relative_path: "pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass",
        missing_material: "operator_hil_report",
        recovery_hint: "补齐 operator_hil_report 后仍需人工复核，coverage 也不会升级为 HIL pass。",
      },
    ],
    fail_closed_tokens: [
      "hil_pass=false",
      "hardware_connected=false",
      "serial_path_not_proven",
      "baudrate_link_not_proven",
      "wheel_direction_not_proven",
      "cmd_ros_ctrl_not_proven_on_chassis",
      "feedback_frequency_not_proven",
      "imu_calibration_not_proven",
      "battery_calibration_not_proven",
      "delivery_success_not_proven",
    ],
    not_proven_tokens: [
      "hil_pass=false",
      "hardware_connected=false",
      "serial_path_not_proven",
      "baudrate_link_not_proven",
      "wheel_direction_not_proven",
      "cmd_ros_ctrl_not_proven_on_chassis",
      "feedback_frequency_not_proven",
      "imu_calibration_not_proven",
      "battery_calibration_not_proven",
      "delivery_success_not_proven",
    ],
    not_proven_boundaries: [
      "real_wave_rover_power_on_not_proven",
      "real_uart_link_not_proven",
      "real_hil_pass_not_proven",
      "lidar_tof_material_not_proven",
      "delivery_success_not_proven",
      "pr5_resolved_not_proven",
    ],
    boundary_copy:
      "coverage is not HIL pass; complete material coverage is still software_proof/not_proven and keeps hardware_connected=false, safe_to_control=false, delivery_success=false.",
    ...PROOF_FLAGS,
  },
  "/api/robot-control/summary": {
    schema: "trashbot.pc_tools_workstation.robot_control_summary.v1",
    console_status: "blocked",
    source_base_url: "http://127.0.0.1:8787",
    normalized_base_url: "http://127.0.0.1:8787",
    proxy_policy: {
      vue_direct_robot_api_access: false,
      node_proxy_only: true,
      allowed_methods: ["GET", "POST"],
      allowed_endpoint_class: "status_latest_readback_plus_fixed_control_and_report_proxies",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: 1781040814776,
    read_endpoints: [
      {
        id: "status",
        endpoint: "/api/status",
        http_status: 200,
        request_status: "loaded",
        schema: "trashbot.upper_robot_api.v1.status",
        status: "blocked_not_proven",
        evidence_ref: "robot-api-status-proof",
        key_values: {
          safe_to_control: "false",
          delivery_success: "false",
          primary_actions_enabled: "false",
          path_generated: "false",
        },
        blocked_reasons: [],
        dangerous_true_fields: [],
      },
    ],
    o3_proof_summary: {
      managed_runtime_started: true,
      scan_once_observed: true,
      map_once_observed: true,
      amcl_pose_observed: false,
      localization_tf_observed: false,
      planner_server_active: false,
      path_generation_requested: true,
      path_generation_succeeded: false,
      path_generated: false,
      path_point_count: 0,
      root_causes: ["planner_server_not_active"],
      not_proven: ["path_generated", "delivery_success"],
    },
    robot_api_connection: {
      status: "blocked",
      loaded_count: 1,
      blocked_count: 0,
      failed_count: 0,
      schema_mismatch_count: 0,
      dangerous_true_fields: [],
      blocked_reasons: ["dangerous actions locked by V1 boundary"],
      last_refresh_ms: 1781040814776,
    },
    readback_summary: {
      camera: {
        status: "camera_health_not_proven",
        devices_status: "camera_devices_not_proven",
        preview_status: "idle_not_started",
        video_source: "/dev/video1",
        video_source_mode: "auto",
        selected_path: "/dev/video1",
        source_readiness: "source_selected_not_probed",
        source_failure_reason: "none",
        active_peer_count: "0",
        last_offer_error: "none",
        last_offer_failure_reason: "none",
      },
      lidar: {
        status: "radar_status_not_proven",
        latest_scan_proof_status: "scan_once_observed",
        latest_raw_packet_proof_status: "raw_packet_not_proven",
        continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
        lifecycle_running: "true",
        lifecycle_state: "running",
        continuous_window_observed: "true",
        continuity_window_status: "fresh_window_observed",
        latest_scan_proof_fresh: "true",
      },
      base: {
        status: "base_status_not_proven",
        latest_feedback_status: "feedback_samples_not_proven",
        feedback_ack_status: "blocked_no_ack",
      },
    },
    operator_hil_material_summary: {
      status: "loaded",
      source_endpoint_id: "operator_report_latest",
      source_path: "operator_report_latest.structured_hil_claims",
      report_status: "ready_for_review",
      evidence_ref: "field-hil-20260611-0605-op",
      operator_present: "true",
      physical_clearance: "true",
      emergency_stop: "true",
      external_video: "true; ref=phone-video-0605.mp4",
      camera_visible: "true; ref=runtime/camera/latest_metrics.json",
      wheel_feedback: "true; ref=runtime/wave_rover_feedback_debug.jsonl",
      lidar_delta: "false; ref=runtime/scan_delta/latest_metrics.json",
      route_map: "true; ref=runtime/routes/field-route.csv",
      delivery_claim: "true",
      site_state: "field_operator_claim_ready_for_review",
    },
    first_jog_readiness_summary: {
      status: "ready_for_first_jog",
      basic_safety_ready: true,
      visual_material_ready: true,
      missing_fields: [],
      next_action: "press_try_move",
    },
    safe_command_boundary: {
      manual_endpoint: "/api/base/manual",
      stop_endpoint: "/api/base/stop",
      cmd_vel_topic: "/cmd_vel",
      nav2_goal: "Nav2 NavigateToPose locked",
      map_start: "map start locked",
      radar_start: "radar start locked",
      keyboard_control: "keyboard control locked",
      map_click_goal: "map click goal locked",
      locked_reason: "requires safety lock, checklist, operator report materials, robot ACK, timeout/cancel/stop/recovery evidence before enablement",
      manual_motion_entry_status: "controlled_jog_requires_hil_checklist_and_operator_report",
      manual_motion_entry_label: "受控点动（需现场确认）",
      allowed_directions: ["forward", "back", "left", "right", "stop"],
      non_stop_requires_confirm_hil_checklist: true,
      non_stop_requires_operator_report_preflight: true,
      operator_report_preflight_endpoint: "/api/operator/report",
      operator_report_preflight_required_fields: [
        "operator_present",
        "physical_clearance_confirmed",
        "emergency_stop_ready",
        "external_video_recorded",
        "external_video_ref",
        "visible_content_proven",
        "camera_artifacts_ref",
        "wheel_feedback_lr_nonzero_proven",
        "wheel_feedback_ref",
        "physical_motion_lidar_delta_proven",
        "scan_delta_ref",
      ],
      speed_limit_mps: 0.12,
      duration_limit_ms: 800,
      hil_checklist: [
        { id: "operator_ready", label: "现场有人扶控并准备急停" },
        { id: "clearance_confirmed", label: "已确认小车周围无人和障碍" },
        { id: "low_speed_only", label: "本轮仅做低速短时点动" },
        { id: "not_autonomy_mode", label: "本轮不是自动导航任务" },
      ],
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      robot_control_executed: false,
    },
    blocked_reasons: ["dangerous actions locked by V1 boundary"],
    not_proven: ["O7", "path_generated", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/robot-control/operator/report": {
    schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
    proxy_status: "report_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/operator/report",
    remote_method: "POST",
    remote_http_status: 200,
    status: "loaded_fail_closed_summary",
    request_body: {
      operator_present: true,
      evidence_ref: "field-hil-ui-submit",
      physical_clearance_confirmed: true,
      emergency_stop_ready: true,
      observed_motion: false,
      observed_stop: true,
      reported_at: "2026-06-11T06:20:00.000Z",
      structured_hil_claims: {
        external_video_recorded: true,
        external_video_ref: "phone-video-ui.mp4",
        delivery_success: true,
        site_state: "field_operator_claim_ready_for_review",
      },
    },
    structured_hil_claims: {
      external_video_recorded: true,
      external_video_ref: "phone-video-ui.mp4",
      delivery_success: true,
      site_state: "field_operator_claim_ready_for_review",
    },
    rejected_fields: [],
    ignored_fields: [],
    failure_reason: "",
    blocked_reasons: [],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
    ...PROOF_FLAGS,
  },
    "/api/robot-control/radar/scan-proof/refresh": {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      robot_control_executed: false,
      refresh_kind: "radar_scan_proof_refresh",
      proxy_status: "refresh_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/radar/scan-proof/refresh",
    remote_http_status: 200,
    status: "loaded_fail_closed_summary",
    last_result_status: "scan_once_observed",
    last_result_schema: "trashbot.upper_robot_api.v1.radar_scan_proof_refresh",
    last_result_evidence_ref: "radar-scan-refresh-proof",
    last_refreshed_at_ms: 1781040815776,
      latest_readback_key_values: {
        status: "scan_once_observed",
        evidence_ref: "radar-scan-refresh-proof",
        scan_once_observed: "true",
        scan_hz_observed: "10",
        raw_packet_once_observed: "true",
        tf_observed: "true",
        continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
        lifecycle_running: "true",
        lifecycle_state: "running",
        continuous_window_observed: "true",
        continuity_window_status: "fresh_window_observed",
        latest_scan_proof_fresh: "true",
      },
      failure_reason: "",
      blocked_reasons: [],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: ["sends_commands", "starts_ros2"],
      ...PROOF_FLAGS,
    },
    "/api/robot-control/radar/start": {
      schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
      action: "start",
      proxy_status: "lifecycle_forwarded",
      source_base_url: "http://192.168.1.11:8787",
      normalized_base_url: "http://192.168.1.11:8787",
      remote_endpoint: "/api/radar/start",
      remote_method: "POST",
      remote_http_status: 200,
      status: "loaded_fail_closed_summary",
      command_result: { mode: "dry_run_stub", executed: false, ok: false },
      failure_reason: "command_not_configured",
      blocked_reasons: ["command_not_configured"],
      hard_dangerous_true_fields: [],
      robot_control_executed: false,
      ...PROOF_FLAGS,
    },
    "/api/robot-control/radar/stop": {
      schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
      action: "stop",
      proxy_status: "lifecycle_forwarded",
      source_base_url: "http://192.168.1.11:8787",
      normalized_base_url: "http://192.168.1.11:8787",
      remote_endpoint: "/api/radar/stop",
      remote_method: "POST",
      remote_http_status: 200,
      status: "loaded_fail_closed_summary",
      command_result: { mode: "dry_run_stub", executed: false, ok: false },
      failure_reason: "command_not_configured",
      blocked_reasons: ["command_not_configured"],
      hard_dangerous_true_fields: [],
      robot_control_executed: false,
      ...PROOF_FLAGS,
    },
    "/api/robot-control/map/proof/refresh": {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      robot_control_executed: false,
    refresh_kind: "map_proof_refresh",
    proxy_status: "refresh_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/map/proof/refresh",
    remote_http_status: 200,
    status: "loaded_fail_closed_summary",
    last_result_status: "map_once_observed",
    last_result_schema: "trashbot.upper_robot_api.v1.map_proof_refresh",
    last_result_evidence_ref: "map-refresh-proof",
    last_refreshed_at_ms: 1781040816776,
      latest_readback_key_values: {
        status: "map_once_observed",
        evidence_ref: "map-refresh-proof",
        map_once_observed: "true",
        map_file_observed: "true",
        map_metadata_observed: "true",
      },
      failure_reason: "",
      blocked_reasons: [],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: ["sends_commands", "starts_ros2"],
      ...PROOF_FLAGS,
    },
    "/api/robot-control/nav2/proof/refresh": {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      robot_control_executed: false,
      refresh_kind: "nav2_no_motion_proof_refresh",
      proxy_status: "refresh_failed",
      source_base_url: "http://192.168.1.11:8787",
      normalized_base_url: "http://192.168.1.11:8787",
      remote_endpoint: "/api/nav2/proof/refresh",
      remote_http_status: null,
      status: "blocked",
      last_result_status: "nav2_no_motion_path_generation_runtime_observed",
      last_result_schema: "trashbot.upper_robot_api.v1.nav2_proof_refresh",
      last_result_evidence_ref: "nav2-refresh-proof",
      last_refreshed_at_ms: 1781040817776,
      latest_readback_key_values: {
        status: "nav2_no_motion_path_generation_runtime_observed",
        latest_proof_status: "nav2_no_motion_path_generation_runtime_observed",
        path_generation_requested: "true",
        path_generation_succeeded: "true",
        path_generated: "true",
        path_point_count: "17",
        planner_server_active: "true",
      },
      failure_reason: "fetch_timeout_90000ms",
      blocked_reasons: ["fetch_timeout_90000ms", "post_timeout_latest_readback_loaded"],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      ...PROOF_FLAGS,
    },
    "/api/robot-control/nav2/goal/preflight": {
      schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_preflight.v1",
      proxy_status: "preflight_rejected",
      preflight_status: "preflight_rejected",
      source_base_url: "http://192.168.1.11:8787",
      normalized_base_url: "http://192.168.1.11:8787",
      workstation_endpoint: "/api/robot-control/nav2/goal/preflight",
      remote_methods_used: ["GET"],
      remote_read_endpoints: [
        {
          id: "localize_proof_latest",
          endpoint: "/api/localize/proof/latest",
          http_status: 200,
          request_status: "loaded",
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          evidence_ref: "localize-reset-proof",
          key_values: {
            localization_reset_observed: "true",
            localization_tf_observed: "{\"map_to_base_link\":true}",
          },
          blocked_reasons: [],
          dangerous_true_fields: [],
        },
        {
          id: "nav2_proof_latest",
          endpoint: "/api/nav2/proof/latest",
          http_status: 200,
          request_status: "loaded",
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "nav2_no_motion_path_generation_runtime_observed",
          evidence_ref: "nav2-latest-proof",
          key_values: {
            path_generated: "true",
            path_generation_succeeded: "true",
            path_point_count: "17",
          },
          blocked_reasons: [],
          dangerous_true_fields: [],
        },
      ],
      forbidden_remote_endpoints_not_called: ["/api/nav2/start", "NavigateToPose", "/cmd_vel", "/api/base/manual"],
      goal_request: {
        goal_frame_id: "map",
        goal_x: 0.8,
        goal_y: 0,
        goal_yaw: 0,
        confirm_navigation_preflight: true,
      },
      goal_limits: {
        frame_id: "map",
        x_min_m: -3,
        x_max_m: 3,
        y_min_m: -3,
        y_max_m: 3,
        yaw_min_rad: -3.1416,
        yaw_max_rad: 3.1416,
      },
      operator_report_preflight: {
        status: "blocked",
        source_endpoint: "/api/operator/report",
        request_status: "loaded",
        http_status: 200,
        report_status: "ready_for_review",
        evidence_ref: "field-hil-20260611-0605-op",
        required_fields: ["scan_delta_ref"],
        missing_fields: ["physical_motion_lidar_delta_proven"],
        material_summary: {
          status: "loaded",
          source_endpoint_id: "operator_report_latest",
          source_path: "operator_report_latest.structured_hil_claims",
          report_status: "ready_for_review",
          evidence_ref: "field-hil-20260611-0605-op",
          operator_present: "true",
          physical_clearance: "true",
          emergency_stop: "true",
          external_video: "true; ref=phone-video-0605.mp4",
          camera_visible: "true; ref=runtime/camera/latest_metrics.json",
          wheel_feedback: "true; ref=runtime/wave_rover_feedback_debug.jsonl",
          lidar_delta: "false; ref=runtime/scan_delta/latest_metrics.json",
          route_map: "true; ref=runtime/routes/field-route.csv",
          delivery_claim: "true",
          site_state: "field_operator_claim_ready_for_review",
        },
        failure_reason: "operator_report_preflight_required",
        hard_dangerous_true_fields: [],
      },
      localization_summary: {
        request_status: "loaded",
        status: "localization_reset_observed",
        localization_reset_observed: true,
        nav2_no_motion_localization_runtime_observed: false,
        map_to_base_link: true,
      },
      nav2_path_summary: {
        request_status: "loaded",
        status: "nav2_no_motion_path_generation_runtime_observed",
        path_generated: true,
        path_generation_succeeded: true,
        path_point_count: 17,
      },
      nav2_status_summary: {
        request_status: "loaded",
        status: "inactive",
      },
      missing_requirements: ["operator_report_preflight_required"],
      failure_reason: "operator_report_preflight_required",
      blocked_reasons: ["operator_report_preflight_required"],
      hard_dangerous_true_fields: [],
      robot_control_executed: false,
      ...PROOF_FLAGS,
    },
    "/api/robot-control/localize/reset": {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      robot_control_executed: false,
      refresh_kind: "localization_reset",
      proxy_status: "refresh_forwarded",
      source_base_url: "http://192.168.1.11:8787",
      normalized_base_url: "http://192.168.1.11:8787",
      remote_endpoint: "/api/localize/reset",
      remote_http_status: 200,
      status: "loaded_fail_closed_summary",
      last_result_status: "localization_reset_observed",
      last_result_schema: "trashbot.upper_robot_api.v1.localization_reset_result",
      last_result_evidence_ref: "localize-reset-proof",
      last_refreshed_at_ms: 1781040818776,
      latest_readback_key_values: {
        status: "localization_reset_observed",
        initialpose_published: "true",
        amcl_pose_observed: "true",
        localization_tf_observed: "{\"map_to_odom\":true,\"map_to_base_link\":true}",
        managed_runtime_started: "true",
        managed_runtime_cleanup_ok: "true",
        localization_reset_observed: "true",
      },
      failure_reason: "",
      blocked_reasons: [],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      ...PROOF_FLAGS,
    },
  "/api/robot-control/map/list": {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    action: "list",
    proxy_status: "lifecycle_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/map/list",
    remote_method: "GET",
    remote_http_status: 200,
    status: "loaded_fail_closed_summary",
    map_count: 2,
    map_names: ["floor_1.yaml", "floor_1.pgm"],
    map_quality_summary: {
      status: "no_free_cells",
      message: "当前地图没有可通行区域，需要重新建图。",
      checked_yaml_count: 1,
      usable_map_count: 0,
      no_free_cell_map_count: 1,
      analysis_failed_count: 0,
    },
    map_usable_for_navigation: false,
    map_needs_rebuild: true,
    command_result: { mode: "read_only_local_files", executed: false, ok: true },
    request_body: {},
    failure_reason: "",
    blocked_reasons: [],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
    ...PROOF_FLAGS,
  },
  "/api/robot-control/map/save": {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    action: "save",
    proxy_status: "lifecycle_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/map/save",
    remote_method: "POST",
    remote_http_status: 200,
    status: "loaded_fail_closed_summary",
    map_count: 2,
    map_names: [],
    map_quality_summary: {
      status: "not_loaded",
      message: "地图质量还没有读取。",
      checked_yaml_count: 0,
      usable_map_count: 0,
      no_free_cell_map_count: 0,
      analysis_failed_count: 0,
    },
    map_usable_for_navigation: false,
    map_needs_rebuild: false,
    command_result: { mode: "software_guard_command_not_configured", executed: false, ok: false },
    request_body: {},
    failure_reason: "",
    blocked_reasons: [],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
    ...PROOF_FLAGS,
  },
  "/api/robot-control/camera/offer": {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
    proxy_status: "offer_forwarded",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/camera/offer",
    remote_http_status: 200,
    status: "ready",
    peer_id: "peer-preview-001",
    answer: {
      type: "answer",
      sdp: "v=0\r\ns=remote-answer\r\n",
    },
    error: "",
    failure_reason: "",
    blocked_reasons: [],
    ...PROOF_FLAGS,
  },
  "/api/robot-control/camera/peers/peer-preview-001/close": {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1",
    proxy_status: "peer_closed",
    source_base_url: "http://192.168.1.11:8787",
    normalized_base_url: "http://192.168.1.11:8787",
    remote_endpoint: "/api/camera/peers/{peer_id}/close",
    remote_http_status: 200,
    peer_id: "peer-preview-001",
    status: "closed",
    error: "",
    failure_reason: "",
    blocked_reasons: [],
    ...PROOF_FLAGS,
  },
  "/api/tools/training-labeling": {
    schema: "trashbot.pc_tools_workstation.training_labeling.v2",
    roots: { dataset: "pc-tools/training", labeling: "pc-tools/labeling" },
    real_pipeline_connected: false,
    workspaces: [
      {
        name: "dataset",
        root: "pc-tools/training",
        status: "empty_not_connected",
        real_pipeline_connected: false,
        asset_counts: {
          total_assets: 0,
          structured_files: 0,
          manifest_candidates: 0,
          images: 0,
          annotations: 0,
          ignored_python_files: 0,
        },
        manifest_candidates: [],
        image_files: [],
        annotation_files: [],
        missing_requirements: [
          "asset_files",
          "manifest_candidate",
          "image_files",
          "annotation_files",
          "real_pipeline_connection",
        ],
        next_actions: [
          "Place dataset or annotation assets under this workspace for read-only inventory.",
          "Add a manifest candidate and paired images/annotations before readiness can improve.",
          "Keep real_pipeline_connected=false until a backend asset contract exists.",
        ],
      },
      {
        name: "labeling",
        root: "pc-tools/labeling",
        status: "empty_not_connected",
        real_pipeline_connected: false,
        asset_counts: {
          total_assets: 0,
          structured_files: 0,
          manifest_candidates: 0,
          images: 0,
          annotations: 0,
          ignored_python_files: 0,
        },
        manifest_candidates: [],
        image_files: [],
        annotation_files: [],
        missing_requirements: [
          "asset_files",
          "manifest_candidate",
          "image_files",
          "annotation_files",
          "real_pipeline_connection",
        ],
        next_actions: [
          "Place dataset or annotation assets under this workspace for read-only inventory.",
          "Add a manifest candidate and paired images/annotations before readiness can improve.",
          "Keep real_pipeline_connected=false until a backend asset contract exists.",
        ],
      },
    ],
    missing_requirements: [
      "asset_files",
      "manifest_candidate",
      "image_files",
      "annotation_files",
      "real_pipeline_connection",
    ],
    next_actions: [
      "Place dataset or annotation assets under this workspace for read-only inventory.",
      "Add a manifest candidate and paired images/annotations before readiness can improve.",
      "Keep real_pipeline_connected=false until a backend asset contract exists.",
    ],
    boundary_copy:
      "Dataset and labeling inventory is read-only software proof; it does not run pipelines, transfer data, write files, or prove a real pipeline.",
    ...PROOF_FLAGS,
  },
  "/api/o7/operator-console": {
    schema: "trashbot.o7.operator_console.v1",
    contract_source: "cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py",
    workstation_endpoint: "/api/o7/operator-console",
    cloud_api_status: "draft_blocked_not_proven",
    robot_connection: "not_connected_by_pc",
    realtime_stream_status: "blocked_not_proven",
    operator_mode: "observe_only",
    board_media_preflight_required: true,
    board_media_preflight_schema: "trashbot.o7_board_media_preflight.v1",
    board_media_preflight_state: "blocked",
    board_media_preflight_summary: {
      schema: "trashbot.o7_board_media_preflight.v1",
      schema_version: 1,
      evidence_boundary: "software_proof_o7_board_media_preflight_contract",
      source: "operator_media_preflight",
      overall_state: "blocked",
      safe_to_control: false,
      primary_actions_enabled: false,
      device_probe_allowed: false,
      device_probe_attempted: false,
      software_proof_only: true,
      blocked_reasons: ["board_media_preflight_not_collected_by_pc", "rtc_signaling_stun_turn_not_proven"],
      not_proven: [
        "real_rtc_session",
        "real_camera_video_source",
        "real_audio_capture",
        "real_audio_playback",
        "real_asr_stream",
        "real_tts_playback",
      ],
      next_required_evidence: [
        "orange_pi_camera_device_enumeration",
        "rtc_signaling_stun_turn_trace",
        "on_robot_media_smoke_with_no_chassis_motion",
      ],
    },
    realtime_map_snapshot: {
      schema: "trashbot.o7.realtime_map_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      map_ref: {
        value: "not_connected",
        status: "not_proven",
        evidence_ref: "missing_cloud_realtime_map_ref",
      },
      map_frame: {
        value: "map",
        status: "contract_placeholder_not_tf",
        frame_source: "cloud_contract_draft",
      },
      robot_pose: {
        x_m: null,
        y_m: null,
        yaw_rad: null,
        pose_source: "not_connected",
        status: "not_proven",
      },
      pose_freshness: {
        last_update_ms: null,
        age_ms: null,
        latency_lt_2s_proven: false,
        status: "blocked_no_realtime_stream",
      },
      route_membership: {
        route_id: "not_connected",
        on_route: false,
        in_elevator_zone: false,
        status: "not_proven",
        reason: "cloud_realtime_map_pose_stream_not_connected",
      },
      blocked_reasons: ["cloud_realtime_api_draft", "ros2_tf_forwarding_not_proven"],
      not_proven: ["real_ros2_tf", "real_robot_pose", "robot_position_latency_lt_2s"],
    },
    elevator_state_snapshot: {
      schema: "trashbot.o7.elevator_state_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      state_chain: [
        {
          state: "not_connected",
          status: "not_proven",
          evidence_ref: "missing_cloud_elevator_state_chain",
        },
      ],
      current_state: "not_connected",
      current_floor_evidence: {
        floor_label: "not_connected",
        confidence: null,
        evidence_ref: "missing_floor_evidence",
        status: "not_proven",
      },
      target_floor: {
        floor_label: "not_connected",
        confirmation_status: "not_proven",
      },
      human_takeover: {
        required: true,
        reason: "real_elevator_state_chain_not_proven",
        operator_action: "keep_observe_only_until_cloud_archive_and_field_evidence_exist",
      },
      blocked_reasons: ["elevator_event_archive_not_connected", "floor_recognition_not_proven"],
      not_proven: ["real_elevator_state_chain", "real_human_takeover_reason"],
    },
    route_replay_snapshot: {
      schema: "trashbot.o7.route_replay_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      playback_available: false,
      real_archive_connected: false,
      task_selector: {
        source_contract: "history.route_replay.v1",
        status: "blocked_no_cloud_task_archive",
        available_task_count: 0,
        selected_task_id: "not_connected",
        task_list_ref: "missing_o6_cloud_task_archive",
        selection_required: true,
      },
      selected_task: {
        task_id: "not_connected",
        robot_id: "not_connected",
        route_id: "not_connected",
        started_at_ms: null,
        completed_at_ms: null,
        status: "not_proven",
        evidence_ref: "missing_selected_task_record",
      },
      trajectory: {
        frame_count: 0,
        sample_frames: [],
        frame_schema: "pending_cloud_trajectory_frame_v1",
        map_frame: "not_connected",
        status: "blocked_no_trajectory_api",
      },
      playback_cursor: {
        frame_index: null,
        timestamp_ms: null,
        playing: false,
        speed: 0,
        status: "blocked_not_available",
      },
      keyframes: {
        count: 0,
        sample_refs: [],
        status: "blocked_no_keyframe_archive",
      },
      evidence_refs: {
        task_archive: "missing_o6_cloud_task_archive",
        trajectory_api: "missing_trajectory_api",
        keyframe_archive: "missing_keyframe_archive",
        state_transition_archive: "missing_state_transition_archive",
      },
      state_transitions: {
        count: 0,
        sample: [],
        status: "blocked_no_state_transition_archive",
        gaps: ["cloud_task_archive_not_connected", "state_transition_timeline_not_backfilled"],
      },
      blocked_reasons: ["o6_cloud_task_archive_not_connected", "trajectory_frames_not_available"],
      not_proven: ["real_history_task_list", "real_trajectory_frames", "real_state_transition_timeline"],
      next_required_evidence: [
        "o6_cloud_task_archive_query_contract",
        "trajectory_frame_schema_with_map_frame_and_timestamp",
        "pc_playback_cursor_bound_to_cloud_frames_without_robot_control",
      ],
    },
    labeling_queue_snapshot: {
      schema: "trashbot.o7.labeling_queue_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      submit_enabled: false,
      rollback_enabled: false,
      real_annotation_api_connected: false,
      dataset_export_available: false,
      review_queue: {
        source_contract: "labeling.review_queue.v1",
        status: "blocked_no_annotation_api",
        available_item_count: 0,
        assigned_operator: "not_connected",
        queue_ref: "missing_o6_annotation_review_queue",
        selection_required: true,
      },
      selected_item: {
        item_id: "not_connected",
        task_id: "not_connected",
        frame_id: "not_connected",
        media_ref: "missing_review_item_media_ref",
        evidence_ref: "missing_selected_labeling_item_record",
        status: "not_proven",
      },
      label_schema: {
        schema_ref: "missing_label_schema",
        version: "not_connected",
        status: "blocked_no_label_schema_api",
        required_fields: [],
      },
      allowed_label_types: [
        { type: "elevator_door_state", status: "contract_placeholder_not_api", values: ["open", "closed", "unknown"] },
        { type: "floor_label", status: "contract_placeholder_not_api", values: [] },
        { type: "obstacle_type", status: "contract_placeholder_not_api", values: ["none", "person", "unknown"] },
      ],
      draft_labels: {
        count: 0,
        items: [],
        status: "blocked_no_selected_item",
        autosave_available: false,
      },
      submit_audit: {
        status: "blocked_not_available",
        endpoint: "POST /api/o6/annotations (future, disabled)",
        last_submit_id: "not_connected",
        idempotency_key_required: true,
        audit_ref: "missing_submit_audit_log",
      },
      rollback_audit: {
        status: "blocked_not_available",
        endpoint: "POST /api/o6/annotations/rollback (future, disabled)",
        last_rollback_id: "not_connected",
        requires_reason: true,
        audit_ref: "missing_rollback_audit_log",
      },
      dataset_export: {
        status: "blocked_not_available",
        export_ref: "missing_training_dataset_export",
        supported_formats: [],
        gaps: ["o6_annotation_api_not_connected", "dataset_manifest_export_not_available"],
      },
      blocked_reasons: ["o6_annotation_api_not_connected", "label_schema_not_available"],
      not_proven: ["real_labeling_review_queue", "real_annotation_submit", "real_training_dataset_export"],
      next_required_evidence: ["o6_annotation_review_queue_query_contract", "dataset_export_manifest_contract"],
    },
    voice_asr_tts_snapshot: {
      schema: "trashbot.o7.voice_asr_tts_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      asr_stream_connected: false,
      tts_send_enabled: false,
      speaker_dispatch_enabled: false,
      real_voice_api_connected: false,
      real_asr_tts_runtime_connected: false,
      media_preflight_dependency: {
        required: true,
        source_schema: "trashbot.o7_board_media_preflight.v1",
        status: "blocked",
        dependency_ref: "board_media_preflight_summary",
      },
      asr_stream: {
        source_contract: "voice.asr_tts_operator.v1",
        status: "blocked_no_voice_api",
        connection_state: "not_connected",
        last_event_at_ms: null,
        partial_slot: {
          text: "",
          status: "empty_not_connected",
          evidence_ref: "missing_asr_partial_transcript_trace",
        },
        final_slot: {
          text: "",
          status: "empty_not_connected",
          evidence_ref: "missing_asr_final_transcript_trace",
        },
      },
      tts_draft: {
        text: "",
        status: "draft_disabled",
        max_chars: 0,
        language: "zh-CN",
        voice_profile: "not_connected",
        confirmation_required: true,
      },
      speaker_dispatch: {
        status: "blocked_not_available",
        endpoint: "POST /api/o7/operator/voice/tts (future, disabled)",
        sends_to_robot: false,
        idempotency_key_required: true,
        timeout_ms: null,
        recovery_path: "Keep observe_only mode until voice evidence exists.",
      },
      command_ack_audit: {
        ack_status: "blocked_no_ack_contract",
        last_command_id: "not_connected",
        audit_ref: "missing_voice_command_audit_log",
        speaker_ack_ref: "missing_speaker_dispatch_ack",
        failure_event_ref: "missing_speaker_failure_event",
      },
      blocked_reasons: ["voice_api_not_connected", "asr_event_stream_not_connected", "speaker_dispatch_ack_not_proven"],
      not_proven: ["real_asr_stream", "real_asr_partial_transcript", "real_tts_playback", "real_speaker_dispatch_ack"],
      next_required_evidence: [
        "voice_asr_tts_cloud_api_contract",
        "asr_stream_connection_trace_with_partial_and_final_events",
        "tts_command_ack_and_audit_log_sample",
      ],
    },
    safe_command_snapshot: {
      schema: "trashbot.o7.safe_command_snapshot.v1",
      schema_version: 1,
      source: "software_proof",
      snapshot_status: "blocked_not_proven",
      safe_to_control: false,
      primary_actions_enabled: false,
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      real_command_api_connected: false,
      real_robot_ack_connected: false,
      manual_turn_envelope: {
        source_contract: "operator.safe_command_preview.v1",
        status: "blocked_not_proven",
        sends_to_robot: false,
        accepted_input_slots: ["ui_turn_left", "ui_turn_right", "keyboard_arrow_keys_disabled"],
        requested_direction: "not_connected",
        velocity_limited: true,
        steering_limited: true,
        evidence_ref: "missing_manual_turn_command_envelope_trace",
      },
      velocity_limits: {
        max_linear_mps: null,
        max_angular_radps: null,
        source: "not_connected",
        status: "blocked_no_robot_hil_limits",
        hardware_verified: false,
      },
      steering_limits: {
        max_steering_angle_rad: null,
        max_turn_rate_radps: null,
        source: "not_connected",
        status: "blocked_no_robot_hil_limits",
        hardware_verified: false,
      },
      navigate_goal_envelope: {
        source_contract: "operator.safe_command_preview.v1",
        status: "blocked_not_proven",
        sends_to_robot: false,
        goal_source: "map_click_disabled",
        requires_map_goal_slot: true,
        evidence_ref: "missing_navigate_goal_command_envelope_trace",
      },
      map_goal_slot: {
        map_frame: "map",
        x_m: null,
        y_m: null,
        yaw_rad: null,
        status: "empty_not_connected",
        evidence_ref: "missing_map_goal_selection_trace",
      },
      cloud_command_endpoint: {
        manual_turn: "POST /api/o7/operator/commands/manual-turn (future, disabled)",
        navigate_goal: "POST /api/o7/operator/commands/navigate-goal (future, disabled)",
        status: "future_disabled",
        sends_to_robot: false,
      },
      idempotency_key_requirement: {
        required: true,
        header: "Idempotency-Key",
        status: "required_not_connected",
        replay_policy: "reject_duplicate_future_contract",
      },
      confirmation_policy: {
        manual_turn_requires_confirmation: true,
        navigate_goal_requires_confirmation: true,
        keyboard_control_requires_hold: true,
        status: "blocked_no_confirmation_ui",
      },
      robot_ack_status: {
        ack_status: "blocked_no_robot_ack_contract",
        last_command_id: "not_connected",
        ack_ref: "missing_robot_command_ack",
        timeout_ms: null,
        cancel_ack_ref: "missing_robot_cancel_ack",
        stop_ack_ref: "missing_robot_stop_ack",
        recovery_ref: "missing_robot_recovery_event",
      },
      evidence_gaps: {
        timeout: "missing_command_timeout_policy_and_trace",
        cancel: "missing_cancel_command_ack_trace",
        stop: "missing_stop_command_ack_trace",
        recovery: "missing_robot_recovery_event_trace",
      },
      blocked_reasons: ["safe_command_api_not_connected", "robot_ack_timeout_cancel_stop_recovery_not_proven"],
      not_proven: [
        "real_manual_turn_control",
        "real_velocity_control",
        "real_keyboard_control",
        "real_navigate_goal_dispatch",
        "real_robot_command_ack",
        "real_timeout_cancel_stop_recovery",
      ],
      next_required_evidence: [
        "cloud_safe_command_api_contract_with_bearer_auth",
        "idempotency_key_replay_rejection_trace",
        "cancel_stop_recovery_ack_trace",
      ],
    },
    manual_control_policy: {
      pc_direct_robot_connection: false,
      cloud_mediated_only: true,
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      real_command_api_connected: false,
      real_robot_ack_connected: false,
      confirmation_required_before_future_dispatch: true,
      success_claim_allowed: false,
    },
    kr_views: [
      {
        id: "O7-KR1",
        title: "实时地图与机器人位置",
        status: "blocked",
        cloud_contract: "realtime.map_pose.v1",
        pc_surface: "Map/Pose panel",
        current_view: ["pose=not_proven"],
        blocked_by: ["cloud realtime stream not connected"],
        next_required_contract: "Cloud must expose robot pose snapshots.",
      },
      {
        id: "O7-KR2",
        title: "电梯状态展示",
        status: "blocked",
        cloud_contract: "realtime.elevator_state.v1",
        pc_surface: "Elevator state panel",
        current_view: ["floor_evidence=not_proven"],
        blocked_by: ["elevator event archive not connected"],
        next_required_contract: "Cloud must expose elevator state chain.",
      },
      {
        id: "O7-KR3",
        title: "历史路线回放",
        status: "draft",
        cloud_contract: "history.route_replay.v1",
        pc_surface: "Route replay panel",
        current_view: ["playback=blocked"],
        blocked_by: ["cloud task archive query not connected"],
        next_required_contract: "Cloud must expose trajectory frames.",
      },
      {
        id: "O7-KR4",
        title: "数据标注/打标界面",
        status: "draft",
        cloud_contract: "labeling.review_queue.v1",
        pc_surface: "Labeling queue panel",
        current_view: ["submit=blocked"],
        blocked_by: ["annotation API not connected"],
        next_required_contract: "Cloud must expose label schema.",
      },
      {
        id: "O7-KR5",
        title: "实时 ASR 监听 + TTS 发言控制",
        status: "blocked",
        cloud_contract: "voice.asr_tts_operator.v1",
        pc_surface: "Voice monitor panel",
        current_view: ["asr_stream=blocked"],
        blocked_by: ["ASR event stream not connected"],
        next_required_contract: "Cloud must expose ASR transcript events.",
      },
      {
        id: "O7-KR6",
        title: "手动转向控制 + 自动寻路下发",
        status: "blocked",
        cloud_contract: "operator.safe_command_preview.v1",
        pc_surface: "Safe command preview panel",
        current_view: ["manual_control=blocked"],
        blocked_by: ["safe command dispatch disabled"],
        next_required_contract: "Cloud must expose safe command API.",
      },
    ],
    command_previews: [
      {
        id: "manual_turn_preview",
        label: "Manual turn envelope",
        status: "blocked_not_proven",
        requires_confirmation: true,
        sends_to_robot: false,
        cloud_endpoint: "POST /api/o7/operator/commands/manual-turn (future, disabled)",
        recovery_path: "Require ACK before enabling.",
      },
    ],
    blocked_reasons: ["pc_must_not_direct_connect_robot", "manual_or_navigation_dispatch_disabled"],
    not_proven: [
      "real_o7_realtime_cloud_stream",
      "real_annotation_submit_api",
      "real_voice_api_connected",
      "real_asr_stream",
      "real_operator_safe_command_dispatch",
      "delivery_success",
    ],
    recovery_paths: ["Connect O6 cloud archive and realtime stream before replacing draft values."],
    ...PROOF_FLAGS,
  },
  "/api/o7/previews/acceptance": {
    schema: "trashbot.o7.previews_acceptance.v1",
    ...PROOF_FLAGS,
    guard_endpoint: "/api/o7/previews/acceptance",
    evidence_boundary: "software_proof_o7_previews_acceptance_guard",
    acceptance_verdict: "blocked_not_proven_guard_ok",
    not_real_capability_proof: true,
    reads_hardware: false,
    sends_commands: false,
    connects_cloud_production: false,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    covered_surface_ids: [
      "cloud_operator_console_probe",
      "cloud_archive_tasks_probe",
      "rtc_signaling_contract_probe",
      "realtime_elevator_probe",
      "route_replay_player",
      "realtime_map_pose_preview",
      "elevator_state_timeline_preview",
      "route_replay_trajectory_minimap",
      "labeling_review_panel",
      "local_draft_annotation_editor",
      "voice_monitor_panel",
      "local_tts_draft_editor",
      "safe_command_review_panel",
      "local_safe_command_draft_editor",
    ],
    surfaces: [
      {
        id: "cloud_operator_console_probe",
        source_endpoint: "/api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>",
        ui_surface: "Cloud operator console probe",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["production_cloud_probe_forbidden"],
        not_proven: ["real_robot_status_or_ack"],
      },
      {
        id: "cloud_archive_tasks_probe",
        source_endpoint: "/api/o7/cloud-archive/tasks-probe?baseUrl=<local-loopback-url>",
        ui_surface: "Cloud archive tasks probe",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["production_archive_store_forbidden"],
        not_proven: ["real_route_replay_archive"],
      },
      {
        id: "rtc_signaling_contract_probe",
        source_endpoint: "/api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>",
        ui_surface: "RTC signaling contract probe",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["local_http_contract_probe_only", "webrtc_media_transport_not_connected"],
        not_proven: ["real_rtc_signaling_session", "real_webrtc_media_transport", "real_rtc_video", "real_ros2_tf"],
      },
      {
        id: "realtime_elevator_probe",
        source_endpoint: "/api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>",
        ui_surface: "Realtime/elevator cloud probe",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["production_realtime_stream_forbidden"],
        not_proven: ["real_rtc_video"],
      },
      {
        id: "route_replay_player",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local route replay player",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["local_cursor_only"],
        not_proven: ["real_robot_motion"],
      },
      {
        id: "realtime_map_pose_preview",
        source_endpoint: "/api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>",
        ui_surface: "Realtime map pose preview",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["real_ros2_tf_connected_false"],
        not_proven: ["real_realtime_map_pose"],
      },
      {
        id: "elevator_state_timeline_preview",
        source_endpoint: "/api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>",
        ui_surface: "Elevator state timeline preview",
        evidence_boundary: "local_http_contract_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["real_elevator_state_chain_connected_false"],
        not_proven: ["real_elevator_state_chain"],
      },
      {
        id: "route_replay_trajectory_minimap",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Route replay trajectory minimap",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["playback_available_false"],
        not_proven: ["real_map_overlay"],
      },
      {
        id: "labeling_review_panel",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Debug fallback: archive fixture labeling review panel",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["submit_enabled_false"],
        not_proven: ["real_annotation_api"],
      },
      {
        id: "local_draft_annotation_editor",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local draft annotation editor",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["submit_enabled_false", "real_annotation_api_connected_false"],
        not_proven: ["real_draft_autosave"],
      },
      {
        id: "voice_monitor_panel",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local voice ASR/TTS monitor panel",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["tts_send_enabled_false"],
        not_proven: ["real_asr_tts_runtime"],
      },
      {
        id: "local_tts_draft_editor",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local TTS draft editor",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["tts_send_enabled_false", "real_voice_api_connected_false"],
        not_proven: ["real_tts_send"],
      },
      {
        id: "safe_command_review_panel",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local safe command review panel",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["command_dispatch_enabled_false"],
        not_proven: ["real_robot_ack"],
      },
      {
        id: "local_safe_command_draft_editor",
        source_endpoint: "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
        ui_surface: "Local safe command draft editor",
        evidence_boundary: "local_fixture_cursor_only",
        software_proof_available: true,
        acceptance_status: "blocked_not_proven",
        blocked_reasons: ["command_dispatch_enabled_false", "robot_control_executed_false"],
        not_proven: ["real_manual_control", "real_robot_ack"],
      },
    ],
    fail_closed_checks: [],
    fixed_false_fields: {
      reads_hardware: false,
      sends_commands: false,
      connects_cloud_production: false,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      playback_available: false,
      submit_enabled: false,
      tts_send_enabled: false,
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      robot_control_executed: false,
      real_realtime_api_connected: false,
      real_ros2_tf_connected: false,
      real_cloud_archive_connected: false,
      real_annotation_api_connected: false,
      real_voice_api_connected: false,
      real_command_api_connected: false,
      real_robot_ack_connected: false,
      real_asr_tts_runtime_connected: false,
      real_cloud_operator_console_connected: false,
      manual_turn_sends_to_robot: false,
      navigate_goal_sends_to_robot: false,
    },
    blocked: ["production_cloud_connection_blocked_by_design", "robot_command_dispatch_blocked_by_design"],
    not_proven: ["real_rtc_video_connected", "real_manual_control_or_navigate_goal", "real_hardware_hil"],
    software_proof_only: ["local_loopback_http_contract_shapes", "local_browser_cursor_panels"],
    remaining_real_capability_gaps: [
      "rtc_signaling_contract_probe_does_not_prove_real_rtc_video_or_media_transport",
      "connect_real_rtc_video_and_realtime_pose_stream",
      "connect_real_route_replay_archive",
      "connect_real_annotation_voice_command_apis",
    ],
  },
  "/api/o7/cloud-operator-console-probe": {
    schema: "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1",
    probe_status: "loaded_fail_closed_contract",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint: "/api/o7/operator-console",
    remote_schema: "trashbot.o7.operator_console.v1",
    cloud_api_status: "draft_blocked_not_proven",
    operator_mode: "observe_only",
    kr_ids: ["O7-KR1", "O7-KR2", "O7-KR3", "O7-KR4", "O7-KR5", "O7-KR6"],
    key_false_fields: [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "command_dispatch_enabled=false",
      "manual_control_enabled=false",
      "navigate_goal_enabled=false",
      "keyboard_control_enabled=false",
      "real_command_api_connected=false",
      "real_robot_ack_connected=false",
      "tts_send_enabled=false",
      "submit_enabled=false",
      "playback_available=false",
    ],
    blocked_reasons: ["cloud_realtime_api_draft", "manual_or_navigation_dispatch_disabled"],
    not_proven: ["real_o7_realtime_cloud_stream", "real_robot_command_ack"],
    fail_closed_reason: "none_remote_contract_is_still_observe_only",
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  },
  "/api/o7/cloud-archive/tasks-probe": {
    schema: "trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1",
    probe_status: "loaded_fail_closed_contract",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint: "/api/o7/cloud-archive/tasks",
    remote_schema: "trashbot.o7.cloud_archive_tasks.v1",
    archive_status: "blocked_not_proven",
    task_count: 0,
    selected_task_id: null,
    latest_task_id: null,
    inspector_statuses: {
      route_replay: "blocked_not_proven",
      labeling_queue: "blocked_not_proven",
      voice_asr_tts: "blocked_not_proven",
      safe_command: "blocked_not_proven",
    },
    route_replay_summary: "status=fixture_inspector_ready; frame_count=2; sample_refs=[frame_ref_000,frame_ref_001]; first_frame=departed:frame_ref_000; playback_available=false",
    labeling_queue_summary: "status=fixture_labeling_ready; review_item_count=2; label_schema=label_schema_ref@fixture-v1; allowed_label_types=[floor_label,obstacle_type]; submit_enabled=false",
    voice_asr_tts_summary: "status=fixture_voice_ready; asr_event_count=2; tts_draft_count=1; tts_text_length=14; tts_send_enabled=false",
    safe_command_summary: "status=fixture_command_ready; command_count=2; manual=fixture_summary_only; navigate=fixture_summary_only; ack=blocked_not_proven; command_dispatch_enabled=false; robot_control_executed=false",
    key_false_fields: [
      "real_cloud_archive_connected=false",
      "playback_available=false",
      "submit_enabled=false",
      "tts_send_enabled=false",
      "command_dispatch_enabled=false",
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
    ],
    dangerous_true_fields: [],
    blocked_reasons: ["real_cloud_archive_store_not_connected", "robot_control_disabled"],
    not_proven: ["real_o7_cloud_archive_task_api", "real_o7_trajectory_playback"],
    fail_closed_reason: "none_remote_contract_is_still_blocked_not_proven",
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  },
  "/api/o7/realtime-elevator-preview": {
    schema: "trashbot.o7.realtime_elevator_preview.v1",
    schema_version: 1,
    preview_status: "fixture_preview_ready",
    input_status: { fixture_json: "fixtures/realtime.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.realtime_elevator_fixture.v1",
    real_realtime_api_connected: false,
    real_ros2_tf_connected: false,
    real_elevator_state_chain_connected: false,
    latency_lt_2s_proven: false,
    robot_control_executed: false,
    session: {
      session_id: "fixture_session",
      source: "local_json_fixture",
      evidence_ref: "fixture_evidence",
      audit_refs: ["audit_realtime"],
      status: "fixture_summary_only",
    },
    map_summary: { map_ref: "map_fixture", map_frame: "map", source: "local_json_fixture", status: "fixture_summary_only" },
    robot_pose_summary: { x_m: 1.2, y_m: 2.4, yaw_rad: 0.3, pose_source: "fixture", status: "fixture_summary_only" },
    pose_freshness_summary: { timestamp_ms: 1000, age_ms: 5000, latency_lt_2s_proven: false, status: "fixture_summary_only" },
    route_membership_summary: {
      route_id: "route_a",
      requested_status: "fixture_requested",
      requested_on_route: "true_rejected_to_false",
      requested_in_elevator_zone: "true_rejected_to_false",
      on_route: false,
      in_elevator_zone: false,
      status: "blocked_not_proven",
    },
    elevator_state_chain_summary: {
      current_state: "waiting",
      sample_limit: 5,
      count: 1,
      sample: [{ state: "waiting", status: "fixture_only", timestamp_ms: 1000, evidence_ref: "elevator_state_ref" }],
      status: "fixture_summary_only",
    },
    current_floor_evidence_summary: { floor_label: "1F", confidence: 0.5, evidence_ref: "floor_ref", status: "fixture_summary_only" },
    target_floor_summary: { floor_label: "2F", confirmation_status: "not_proven", evidence_ref: "target_ref", status: "fixture_summary_only" },
    human_takeover_summary: {
      required: true,
      reason: "fixture_only_not_proven",
      operator_action: "observe_only",
      evidence_ref: "takeover_ref",
      status: "blocked_not_proven",
    },
    evidence_refs: {
      fixture_ref: "fixture_ref",
      session_evidence_ref: "fixture_evidence",
      audit_refs: ["audit_realtime"],
      elevator_state_refs: ["elevator_state_ref"],
      floor_evidence_ref: "floor_ref",
      target_floor_evidence_ref: "target_ref",
      human_takeover_evidence_ref: "takeover_ref",
    },
    blocked_reasons: ["real_realtime_api_not_connected", "ros2_tf_not_proven"],
    not_proven: ["real_o7_realtime_cloud_stream", "real_o7_ros2_tf_forwarding", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/o7/route-replay-preview": {
    schema: "trashbot.o7.route_replay_preview.v1",
    schema_version: 1,
    preview_status: "fixture_preview_ready",
    input_status: { fixture_json: "fixtures/route.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.route_replay_fixture.v1",
    real_cloud_archive_connected: false,
    robot_control_executed: false,
    task: { task_id: "task_fixture", robot_id: "robot_fixture", route_id: "route_fixture", evidence_ref: "task_ref" },
    route_metadata: { map_frame: "map", frame_schema: "fixture_trajectory_frame_summary_v1", source: "local_json_fixture" },
    trajectory: {
      frame_count: 1,
      sample_frames: [
        {
          frame_index: 0,
          timestamp_ms: 1000,
          pose: { x_m: 0, y_m: 0, yaw_rad: 0 },
          velocity: { linear_mps: 0, angular_radps: 0 },
          state: "idle",
          evidence_ref: "frame_ref",
        },
      ],
      status: "fixture_summary_only",
    },
    playback_cursor_initial_state: { frame_index: 0, timestamp_ms: 1000, playing: false, speed: 0, safe_to_play: false, status: "preview_cursor_only" },
    keyframes: { count: 1, sample_refs: ["keyframe_ref"], status: "fixture_refs_only" },
    evidence_refs: { fixture_ref: "fixture_ref", task_evidence_ref: "task_ref", keyframe_refs: ["keyframe_ref"] },
    state_transitions: { count: 1, sample: [{ from: "idle", to: "waiting", timestamp_ms: 1000, evidence_ref: "transition_ref" }], gaps: [], status: "fixture_summary_only" },
    blocked_reasons: ["real_cloud_archive_not_connected"],
    not_proven: ["real_o7_route_replay_archive", "real_o7_trajectory_playback", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/o7/labeling-preview": {
    schema: "trashbot.o7.labeling_preview.v1",
    schema_version: 1,
    preview_status: "fixture_preview_ready",
    input_status: { fixture_json: "fixtures/labeling.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.labeling_fixture.v1",
    real_annotation_api_connected: false,
    submit_enabled: false,
    rollback_enabled: false,
    dataset_export_available: false,
    robot_control_executed: false,
    queue: { queue_id: "queue_fixture", source: "local_json_fixture", review_item_count: 1, status: "fixture_summary_only" },
    review_items: {
      sample_limit: 3,
      sample: [{ item_id: "item_1", task_id: "task_1", frame_id: "frame_1", media_ref: "media_ref", evidence_ref: "item_ref", current_labels: { count: 0, sample: [] } }],
      status: "fixture_summary_only",
    },
    label_schema: { schema_ref: "schema_ref", version: "v1", required_fields: ["label_type"], allowed_fields: ["value"], status: "fixture_schema_summary_only" },
    allowed_label_types: ["elevator_door_state"],
    draft_labels: { count: 1, sample: [{ item_id: "item_1", label_type: "floor_label", value: "2F", status: "draft", evidence_ref: "draft_ref" }], autosave_available: false, status: "fixture_draft_slots_only" },
    dataset_export: { status: "fixture_gap_summary_only", export_ref: "export_missing", supported_formats: ["jsonl"], gaps: ["real_export_not_connected"] },
    evidence_refs: { fixture_ref: "fixture_ref", queue_evidence_ref: "queue_ref", item_evidence_refs: ["item_ref"] },
    blocked_reasons: ["real_annotation_api_not_connected"],
    not_proven: ["real_o7_annotation_submit", "real_o7_dataset_export", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/o7/field-evidence-consumer-ingest": {
    schema: "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1",
    ingest_status: "fixture_consumer_ready_not_proven",
    manifest_input_status: {
      manifest_json: "file:field-evidence-manifest.json",
      status: "loaded",
      failure_reason: "",
    },
    route_replay_input_status: {
      fixture_json: "file:route-replay.json",
      status: "loaded",
      failure_reason: "",
    },
    labeling_input_status: {
      fixture_json: "file:labeling.json",
      status: "loaded",
      failure_reason: "",
    },
    source_manifest_schema: "trashbot.field_evidence_manifest.v1",
    manifest: {
      schema: "trashbot.field_evidence_manifest.v1",
      run_id: "field_evidence_20260609T101500Z",
      source: "local_fixture",
      mode: "local",
      artifact_status: "gated",
      artifact_health: {
        status: "gated",
        required_count: 5,
        present_count: 5,
        missing_count: 0,
        blocked_count: 0,
        empty_count: 0,
        present_artifacts: ["map_yaml", "route_csv", "keyframes", "rosbag", "replay_jsonl"],
        missing_artifacts: [],
        blocked_artifacts: [],
        summary: "all_required_artifacts_present",
      },
      manifest_gate: {
        schema: "trashbot.field_evidence_manifest.v1",
        status: "gated",
        gate_pass: true,
        blocked_reason: "preflight_ready_not_delivery_proof",
        source: "local_fixture",
      },
      status: "field_evidence_manifest_ready_not_delivery_proof",
      gate_pass: true,
      blocked_reason: "preflight_ready_not_delivery_proof",
      not_proven: true,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      artifact_root: "file:field_evidence_fixture",
      preflight_status: "ready_for_live_route_capture_not_proven",
      artifacts: {
        map_yaml: {
          required: true,
          present: true,
          path: "file:map.yaml",
          size_bytes: 24,
          mtime_utc: "2026-06-09T10:15:00Z",
          sha256: "manifest-map-sha",
          reason: null,
        },
        route_csv: {
          required: true,
          present: true,
          path: "file:route.csv",
          size_bytes: 18,
          mtime_utc: "2026-06-09T10:15:00Z",
          sha256: "manifest-route-sha",
          reason: null,
        },
        keyframes: {
          required: true,
          present: true,
          path: "file:keyframes",
          size_bytes: 128,
          mtime_utc: "2026-06-09T10:15:00Z",
          sha256: "manifest-keyframes-sha",
          reason: null,
          file_count: 2,
        },
        rosbag: {
          required: true,
          present: true,
          path: "file:route_bag",
          size_bytes: 256,
          mtime_utc: "2026-06-09T10:15:00Z",
          sha256: "manifest-rosbag-sha",
          reason: null,
        },
        replay_jsonl: {
          required: true,
          present: true,
          path: "file:fixed_route_replay.jsonl",
          size_bytes: 96,
          mtime_utc: "2026-06-09T10:15:00Z",
          sha256: "manifest-replay-sha",
          reason: null,
        },
      },
    },
    route_replay_preview: {
      schema: "trashbot.o7.route_replay_preview.v1",
      schema_version: 1,
      preview_status: "fixture_preview_ready",
      input_status: { fixture_json: "file:route-replay.json", status: "loaded", failure_reason: "" },
      source_fixture_schema: "trashbot.o7.route_replay_fixture.v1",
      real_cloud_archive_connected: false,
      robot_control_executed: false,
      task: {
        task_id: "field-evidence-task-001",
        robot_id: "robot-fixture-01",
        route_id: "route-field-evidence",
        evidence_ref: "file:route-evidence.json",
      },
      route_metadata: { map_frame: "map", frame_schema: "fixture_trajectory_frame_summary_v1", source: "local_json_fixture" },
      trajectory: {
        frame_count: 2,
        sample_frames: [
          {
            frame_index: 0,
            timestamp_ms: 1000,
            pose: { x_m: 0.2, y_m: 0.1, yaw_rad: 0 },
            velocity: { linear_mps: 0.1, angular_radps: 0.01 },
            state: "departed",
            evidence_ref: "file:frame-000.jpg",
          },
          {
            frame_index: 1,
            timestamp_ms: 1100,
            pose: { x_m: 0.4, y_m: 0.3, yaw_rad: 0.1 },
            velocity: { linear_mps: 0.2, angular_radps: 0.02 },
            state: "arrived",
            evidence_ref: "file:frame-001.jpg",
          },
        ],
        status: "fixture_summary_only",
      },
      playback_cursor_initial_state: { frame_index: 0, timestamp_ms: 1000, playing: false, speed: 0, safe_to_play: false, status: "preview_cursor_only" },
      keyframes: { count: 2, sample_refs: ["file:keyframe-000.jpg", "keyframe-001.jpg"], status: "fixture_refs_only" },
      evidence_refs: { fixture_ref: "file:route-replay.json", task_evidence_ref: "file:route-evidence.json", keyframe_refs: ["file:keyframe-000.jpg", "keyframe-001.jpg"] },
      state_transitions: {
        count: 1,
        sample: [{ from: "queued", to: "departed", timestamp_ms: 900, evidence_ref: "file:transition-000.json" }],
        gaps: ["not_o6_cloud_archive", "robot_control_disabled", "delivery_success_not_proven"],
        status: "fixture_summary_only",
      },
      blocked_reasons: ["not_o6_cloud_archive", "robot_control_disabled", "delivery_success_not_proven"],
      not_proven: ["real_o6_route_replay_archive", "real_route_replay_playback", "delivery_success"],
    },
    labeling_preview: {
      schema: "trashbot.o7.labeling_preview.v1",
      schema_version: 1,
      preview_status: "fixture_preview_ready",
      input_status: { fixture_json: "file:labeling.json", status: "loaded", failure_reason: "" },
      source_fixture_schema: "trashbot.o7.labeling_fixture.v1",
      real_annotation_api_connected: false,
      submit_enabled: false,
      rollback_enabled: false,
      dataset_export_available: false,
      robot_control_executed: false,
      queue: { queue_id: "field-evidence-queue-001", source: "local_json_fixture", review_item_count: 2, status: "fixture_summary_only" },
      review_items: {
        sample_limit: 3,
        sample: [
          {
            item_id: "label-item-001",
            task_id: "field-evidence-task-001",
            frame_id: "frame-000",
            media_ref: "file:frame-000.jpg",
            evidence_ref: "file:review-000.json",
            current_labels: { count: 1, sample: [{ label_type: "floor_label", value: "F3", status: "fixture_existing", evidence_ref: "file:label-000.json" }] },
          },
        ],
        status: "fixture_summary_only",
      },
      label_schema: {
        schema_ref: "file:label-schema.json",
        version: "fixture-v1",
        required_fields: ["label_type", "value", "evidence_ref"],
        allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref"],
        status: "fixture_schema_summary_only",
      },
      allowed_label_types: ["floor_label", "obstacle_type"],
      draft_labels: {
        count: 1,
        sample: [
          { item_id: "label-item-001", label_type: "floor_label", value: "F3", status: "draft_slot", evidence_ref: "file:draft-000.json" },
        ],
        autosave_available: false,
        status: "fixture_draft_slots_only",
      },
      dataset_export: {
        status: "fixture_gap_summary_only",
        export_ref: "file:dataset-export.json",
        supported_formats: ["jsonl"],
        gaps: ["real_annotation_api_not_connected", "dataset_manifest_export_not_available"],
      },
      evidence_refs: {
        fixture_ref: "file:labeling.json",
        queue_evidence_ref: "file:labeling-queue.json",
        item_evidence_refs: ["file:review-000.json"],
      },
      blocked_reasons: ["real_annotation_api_not_connected", "dataset_export_disabled"],
      not_proven: ["real_o7_annotation_submit", "real_o7_dataset_export", "delivery_success"],
    },
    consumer_entry: {
      primary_path: "/api/o7/field-evidence-consumer-ingest",
      route_replay_path: "/api/o7/route-replay-preview",
      labeling_path: "/api/o7/labeling-preview",
      fallback_mode: "local_mock",
      blocked_reason: "preflight_ready_not_delivery_proof",
    },
    blocked_reasons: ["preflight_ready_not_delivery_proof", "not_o6_cloud_archive", "real_annotation_api_not_connected"],
    not_proven: [
      "field_evidence_manifest_not_delivery_proof",
      "real_o7_route_replay_archive",
      "real_o7_annotation_submit",
      "delivery_success",
    ],
    next_required_evidence: [
      "field_evidence_manifest_artifacts_complete_and_preflight_ready",
      "real_o7_route_replay_archive",
      "real_o7_annotation_submit",
    ],
    ...PROOF_FLAGS,
  },
  "/api/o7/voice-preview": {
    schema: "trashbot.o7.voice_preview.v1",
    schema_version: 1,
    preview_status: "fixture_preview_ready",
    input_status: { fixture_json: "fixtures/voice.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.voice_fixture.v1",
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    robot_control_executed: false,
    voice_session: { session_id: "voice_fixture", source: "local_json_fixture", evidence_ref: "voice_ref", audit_refs: ["voice_audit"], status: "fixture_summary_only" },
    asr_events: {
      event_count: 1,
      sample_limit: 3,
      sample: [{ event_type: "partial", timestamp_ms: 1000, transcript: "fixture transcript", confidence: 0.5, evidence_ref: "asr_ref" }],
      latest_partial: { text: "fixture", timestamp_ms: 1000, confidence: 0.5, evidence_ref: "partial_ref", status: "fixture_summary_only" },
      latest_final: { text: "", timestamp_ms: null, confidence: null, evidence_ref: "final_ref", status: "empty_not_proven" },
      status: "fixture_summary_only",
    },
    tts_draft_summary: { text: "hello", text_length: 5, voice_profile: "fixture_voice", language: "zh-CN", confirmation_required: true, status: "fixture_draft_only" },
    speaker_dispatch_summary: { sends_to_robot: false, speaker_dispatch_enabled: false, ack_status: "blocked_not_proven", speaker_ack_ref: "ack_ref", failure_event_ref: "failure_ref", failure_refs: ["failure_ref"], status: "blocked_not_proven" },
    media_preflight_dependency: { required: true, source_schema: "trashbot.o7_board_media_preflight.v1", status: "blocked", dependency_ref: "board_media_preflight_summary", gaps: ["media_smoke_missing"] },
    evidence_refs: { fixture_ref: "fixture_ref", session_evidence_ref: "voice_ref", asr_event_refs: ["asr_ref"], tts_evidence_ref: "tts_ref", audit_refs: ["voice_audit"] },
    blocked_reasons: ["real_voice_api_not_connected"],
    not_proven: ["real_o7_voice_api", "real_o7_asr_tts_runtime", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/o7/safe-command-preview": {
    schema: "trashbot.o7.safe_command_preview.v1",
    schema_version: 1,
    preview_status: "fixture_preview_ready",
    input_status: { fixture_json: "fixtures/safe-command.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.safe_command_fixture.v1",
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    robot_control_executed: false,
    command_session: { command_session_id: "command_fixture", source: "local_json_fixture", evidence_ref: "command_ref", audit_refs: ["command_audit"], status: "fixture_summary_only" },
    manual_turn_envelope_summary: { sends_to_robot: false, requested_direction: "left", velocity_limited: true, steering_limited: true, evidence_ref: "manual_ref", status: "fixture_summary_only" },
    navigate_goal_envelope_summary: { sends_to_robot: false, goal_source: "fixture", map_frame: "map", x_m: 1, y_m: 2, yaw_rad: 0, evidence_ref: "goal_ref", status: "fixture_summary_only" },
    velocity_limits: { max_linear_mps: 0.1, max_angular_radps: 0.2, source: "fixture", hardware_verified: false, status: "fixture_limit_summary_only" },
    steering_limits: { max_steering_angle_rad: 0.3, max_turn_rate_radps: 0.2, source: "fixture", hardware_verified: false, status: "fixture_limit_summary_only" },
    map_goal_slot: { map_frame: "map", x_m: 1, y_m: 2, yaw_rad: 0, status: "fixture_slot_summary_only", evidence_ref: "slot_ref" },
    idempotency_key_requirement: { required: true, key_ref: "key_ref", header: "Idempotency-Key", status: "fixture_requirement_summary_only" },
    confirmation_policy: { manual_turn_requires_confirmation: true, navigate_goal_requires_confirmation: true, keyboard_control_requires_hold: true, status: "fixture_policy_summary_only" },
    robot_ack_summary: { ack_status: "blocked_not_proven", last_command_id: "command_fixture", ack_ref: "ack_ref", timeout_ms: null, cancel_ack_ref: "cancel_ref", stop_ack_ref: "stop_ref", recovery_ref: "recovery_ref", status: "blocked_not_proven" },
    evidence_gaps: ["real_robot_ack_missing", "hil_safety_missing"],
    evidence_refs: {
      fixture_ref: "fixture_ref",
      session_evidence_ref: "command_ref",
      ack_ref: "ack_ref",
      cancel_ack_ref: "cancel_ref",
      stop_ack_ref: "stop_ref",
      recovery_ref: "recovery_ref",
      audit_refs: ["command_audit"],
    },
    blocked_reasons: ["real_command_api_not_connected", "real_robot_ack_not_connected"],
    not_proven: ["real_o7_safe_command_api", "real_robot_command_ack", "real_hil_safety"],
    ...PROOF_FLAGS,
  },
  "/api/o7/cloud-archive/tasks": {
    schema: "trashbot.o7.cloud_archive_tasks.v1",
    schema_version: 1,
    archive_status: "fixture_archive_ready",
    input_status: { archive_json: "fixtures/archive.json", status: "loaded", failure_reason: "" },
    source_fixture_schema: "trashbot.o7.cloud_archive_fixture.v1",
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    robot_control_executed: false,
    task_list: {
      source: "local_json_fixture",
      total_tasks: 2,
      tasks: [
        {
          task_id: "task_archive_001",
          robot_id: "robot_fixture",
          route_id: "route_fixture",
          status: "archived_fixture_only",
          started_at_ms: 1000,
          updated_at_ms: 1500,
          evidence_ref: "task_ref_001",
        },
        {
          task_id: "task_archive_002",
          robot_id: "robot_fixture",
          route_id: "route_fixture",
          status: "needs_review_fixture_only",
          started_at_ms: 2000,
          updated_at_ms: 2600,
          evidence_ref: "task_ref_002",
        },
      ],
      status: "fixture_summary_only",
    },
    selected_task: {
      task_id: "task_archive_002",
      robot_id: "robot_fixture",
      route_id: "route_fixture",
      status: "needs_review_fixture_only",
      started_at_ms: 2000,
      updated_at_ms: 2600,
      evidence_ref: "task_ref_002",
    },
    latest_task: {
      task_id: "task_archive_002",
      robot_id: "robot_fixture",
      route_id: "route_fixture",
      status: "needs_review_fixture_only",
      started_at_ms: 2000,
      updated_at_ms: 2600,
      evidence_ref: "task_ref_002",
    },
    safe_summaries: {
      trajectory: { frame_count: 3, sample_refs: ["frame_ref"], status: "fixture_summary_only" },
      events: { event_count: 2, sample_types: ["arrived_at_elevator"], status: "fixture_summary_only" },
      labels: { label_count: 2, sample_types: ["floor_label"], real_annotation_api_connected: false, status: "fixture_summary_only" },
      voice: { asr_event_count: 1, tts_draft_count: 1, real_voice_api_connected: false, status: "fixture_summary_only" },
      commands: {
        command_count: 2,
        sample_kinds: ["manual_turn", "navigate_goal"],
        real_command_api_connected: false,
        robot_control_executed: false,
        status: "fixture_summary_only",
      },
    },
    route_replay_inspector: {
      status: "fixture_inspector_ready",
      selected_task_id: "task_archive_002",
      map_frame: "map",
      frame_count: 3,
      sample_frames: [
        {
          frame_index: 0,
          timestamp_ms: 2000,
          x_m: 1.25,
          y_m: -0.5,
          yaw_rad: 1.57,
          speed_mps: 0.12,
          state: "departed",
          evidence_ref: "frame_ref_000",
        },
        {
          frame_index: 1,
          timestamp_ms: 2100,
          x_m: 1.35,
          y_m: -0.45,
          yaw_rad: 1.6,
          speed_mps: 0.13,
          state: "arrived_at_elevator",
          evidence_ref: "frame_ref_001",
        },
      ],
      event_timeline: [
        {
          event_type: "arrived_at_elevator",
          state: "door_open_wait",
          timestamp_ms: 2150,
          evidence_ref: "event_ref_001",
        },
      ],
      keyframe_refs: ["keyframe_ref_001", "keyframe_ref_002"],
      cursor_initial_state: {
        playing: false,
        safe_to_play: false,
        speed: 0,
        frame_index: 0,
      },
      blocked_reasons: ["real_cloud_archive_not_connected", "safe_route_playback_not_enabled"],
      not_proven: ["real_o7_history_route_replay", "safe_route_playback"],
    },
    labeling_queue_inspector: {
      status: "fixture_labeling_ready",
      selected_task_id: "task_archive_002",
      review_item_count: 2,
      sample_review_items: [
        {
          item_id: "review_item_001",
          task_id: "task_archive_002",
          frame_id: "frame_001",
          media_ref: "frame_media_001.jpg",
          evidence_ref: "review_item_001.json",
          current_labels: {
            count: 1,
            sample: [
              {
                label_type: "floor_label",
                value: "F3",
                status: "fixture_existing",
                evidence_ref: "label_floor_001.json",
              },
            ],
          },
        },
        {
          item_id: "review_item_002",
          task_id: "task_archive_002",
          frame_id: "frame_002",
          media_ref: "frame_media_002.jpg",
          evidence_ref: "review_item_002.json",
          current_labels: {
            count: 1,
            sample: [
              {
                label_type: "elevator_door_state",
                value: "open",
                status: "fixture_existing",
                evidence_ref: "label_door_002.json",
              },
            ],
          },
        },
      ],
      label_schema: {
        schema_ref: "label_schema_v1.json",
        version: "fixture-v1",
        required_fields: ["label_type", "value", "evidence_ref"],
        allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref"],
      },
      allowed_label_types: ["floor_label", "elevator_door_state", "obstacle_type"],
      draft_labels: {
        count: 1,
        sample: [
          {
            label_type: "obstacle_type",
            value: "cart",
            status: "draft_fixture",
            evidence_ref: "draft_label_001.json",
          },
        ],
        autosave_available: false,
      },
      dataset_export: {
        available: false,
        status: "fixture_summary_only",
        export_ref: "dataset_export_fixture.json",
        supported_formats: ["jsonl", "coco"],
        gaps: ["real_annotation_api_not_connected", "operator_review_not_complete"],
      },
      submit_enabled: false,
      rollback_enabled: false,
      dataset_export_available: false,
      real_annotation_api_connected: false,
      blocked_reasons: ["real_annotation_api_not_connected", "annotation_submit_disabled"],
      not_proven: ["real_o7_annotation_api", "real_o7_annotation_submit"],
    },
    voice_asr_tts_inspector: {
      status: "fixture_voice_ready",
      selected_task_id: "task_archive_002",
      voice_session: {
        session_id: "voice_session_archive_002",
        source: "local_json_fixture",
        evidence_ref: "voice_session_002.json",
        audit_refs: ["voice_audit_001.json"],
        status: "fixture_summary_only",
      },
      asr_event_count: 2,
      sample_asr_events: [
        {
          event_type: "partial",
          timestamp_ms: 2300,
          transcript: "请去三楼",
          confidence: 0.62,
          evidence_ref: "asr_partial_001.json",
        },
        {
          event_type: "final",
          timestamp_ms: 2400,
          transcript: "请去三楼电梯口",
          confidence: 0.9,
          evidence_ref: "asr_final_001.json",
        },
      ],
      latest_partial: {
        text: "请去三楼",
        timestamp_ms: 2300,
        confidence: 0.62,
        evidence_ref: "asr_partial_001.json",
        status: "fixture_summary_only",
      },
      latest_final: {
        text: "请去三楼电梯口",
        timestamp_ms: 2400,
        confidence: 0.9,
        evidence_ref: "asr_final_001.json",
        status: "fixture_summary_only",
      },
      tts_draft: {
        text: "我会等待人工确认后再播报。",
        text_length: 13,
        voice_profile: "operator-default",
        language: "zh-CN",
        confirmation_required: true,
        status: "fixture_draft_only",
      },
      speaker_dispatch: {
        sends_to_robot: false,
        speaker_dispatch_enabled: false,
        ack_status: "not_proven",
        speaker_ack_ref: "speaker_ack_missing.json",
        failure_event_ref: "speaker_failure_missing.json",
        failure_refs: ["speaker_gap_001.json"],
        status: "blocked_not_proven",
      },
      media_preflight_dependency: {
        required: true,
        source_schema: "trashbot.o7_board_media_preflight.v1",
        status: "blocked",
        dependency_ref: "board_media_preflight_summary",
        gaps: ["audio_input_not_checked", "speaker_output_not_checked"],
      },
      asr_stream_connected: false,
      tts_send_enabled: false,
      speaker_dispatch_enabled: false,
      real_voice_api_connected: false,
      real_asr_tts_runtime_connected: false,
      blocked_reasons: ["real_voice_api_not_connected", "tts_send_disabled"],
      not_proven: ["real_o7_voice_api", "real_speaker_dispatch_ack"],
    },
    safe_command_inspector: {
      status: "fixture_command_ready",
      selected_task_id: "task_archive_002",
      command_session: {
        command_session_id: "archive_command_session_002",
        source: "local_json_fixture",
        evidence_ref: "command_session_002.json",
        audit_refs: ["command_audit_001.json"],
        status: "fixture_summary_only",
      },
      command_count: 2,
      sample_commands: [
        {
          command_id: "command_archive_000",
          command_type: "manual_turn",
          status: "draft_fixture_only",
          envelope_ref: "manual_turn_envelope.json",
          idempotency_key_ref: "idempotency_key_000.json",
          evidence_ref: "command_evidence_000.json",
        },
        {
          command_id: "command_archive_001",
          command_type: "navigate_goal",
          status: "draft_fixture_only",
          envelope_ref: "navigate_goal_envelope.json",
          idempotency_key_ref: "idempotency_key_001.json",
          evidence_ref: "command_evidence_001.json",
        },
      ],
      manual_turn_envelope: {
        sends_to_robot: false,
        requested_direction: "left",
        velocity_limited: true,
        steering_limited: true,
        evidence_ref: "manual_turn_envelope.json",
        status: "fixture_summary_only",
      },
      navigate_goal_envelope: {
        sends_to_robot: false,
        goal_source: "fixture_map_goal_slot",
        map_frame: "map",
        x_m: 1.25,
        y_m: -0.5,
        yaw_rad: 1.57,
        evidence_ref: "navigate_goal_envelope.json",
        status: "fixture_summary_only",
      },
      velocity_limits: {
        max_linear_mps: 0.2,
        max_angular_radps: 0.4,
        source: "fixture_limit_not_hil",
        hardware_verified: false,
        status: "fixture_limit_summary_only",
      },
      steering_limits: {
        max_steering_angle_rad: 0.35,
        max_turn_rate_radps: 0.45,
        source: "fixture_limit_not_hil",
        hardware_verified: false,
        status: "fixture_limit_summary_only",
      },
      map_goal_slot: {
        map_frame: "map",
        x_m: 1.25,
        y_m: -0.5,
        yaw_rad: 1.57,
        status: "fixture_slot_summary_only",
        evidence_ref: "map_goal_slot.json",
      },
      idempotency_key_requirement: {
        required: true,
        key_ref: "idempotency_policy.json",
        header: "Idempotency-Key",
        status: "fixture_requirement_summary_only",
      },
      confirmation_policy: {
        manual_turn_requires_confirmation: true,
        navigate_goal_requires_confirmation: true,
        keyboard_control_requires_hold: true,
        status: "fixture_policy_summary_only",
      },
      robot_ack_blocked_summary: {
        ack_status: "blocked_not_proven",
        last_command_id: "command_archive_001",
        ack_ref: "missing_robot_command_ack",
        timeout_ms: null,
        cancel_ack_ref: "missing_robot_cancel_ack",
        stop_ack_ref: "missing_robot_stop_ack",
        recovery_ref: "missing_robot_recovery_event",
        status: "blocked_not_proven",
      },
      evidence_gaps: ["robot_ack_timeout_trace_missing", "cancel_ack_trace_missing", "stop_ack_trace_missing", "recovery_event_trace_missing"],
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      real_command_api_connected: false,
      real_robot_ack_connected: false,
      robot_control_executed: false,
      safe_to_control: false,
      primary_actions_enabled: false,
      delivery_success: false,
      blocked_reasons: ["real_command_api_not_connected", "robot_ack_not_proven"],
      not_proven: ["real_o7_safe_command_api", "real_robot_command_ack", "real_timeout_cancel_stop_recovery"],
    },
    fixed_false_fields: {
      real_cloud_archive_connected: false,
      real_realtime_api_connected: false,
      real_annotation_api_connected: false,
      real_voice_api_connected: false,
      real_command_api_connected: false,
      real_robot_ack_connected: false,
      real_asr_tts_runtime_connected: false,
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      asr_stream_connected: false,
      tts_send_enabled: false,
      speaker_dispatch_enabled: false,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
    },
    blocked_reasons: ["real_cloud_archive_not_connected", "robot_control_disabled"],
    not_proven: ["real_o7_cloud_archive_task_api", "real_o7_command_api", "delivery_success"],
    ...PROOF_FLAGS,
  },
  "/api/o7/consumer-read/tasks": {
    schema: "trashbot.pc_tools_workstation.o7_consumer_task_list.v1",
    list_status: "loaded_fail_closed_summary",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint: "/api/o6/consumer/tasks?view=summary&limit=50",
    remote_schema: "trashbot.o6.consumer_read.v1",
    query_strategy: {
      view: "summary",
      include: [],
      limit: 50,
      primary_path: true,
      fail_closed_visible: true,
    },
    task_list: [
      {
        task_id: "task-consumer-001",
        robot_id: "robot_fixture",
        started_at_ms: 1000,
        finished_at_ms: 2000,
        task_status_summary: "completed_mock",
        latest_event_at_ms: 1900,
        trajectory_frame_count: 3,
        event_count: 2,
        evidence_count: 1,
        labeling_status: "partial",
        inference_status: "present",
        tunnel_status_summary: "online",
        selected: true,
      },
    ],
    blocked_reasons: [],
    not_proven: ["proof_status=not_proven", "safe_to_control=false"],
    fail_closed_reason: "none",
    local_loopback_only: true,
    connects_cloud_production: false,
    robot_control_executed: false,
    ...PROOF_FLAGS,
  },
  "/api/o7/consumer-read/tasks/task-consumer-001": {
    schema: "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1",
    detail_status: "loaded_fail_closed_summary",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint:
      "/api/o6/consumer/tasks/task-consumer-001?view=default&include=trajectory,events,evidence,labeling,inference,tunnel",
    remote_schema: "trashbot.o6.consumer_read.v1",
    requested_task_id: "task-consumer-001",
    query_strategy: {
      view: "default",
      include: ["trajectory", "events", "evidence", "labeling", "inference", "tunnel"],
      primary_path: true,
      fail_closed_visible: true,
    },
    field_evidence: {
      source_contract: "trashbot.field_evidence_manifest.v1",
      input_status: "loaded",
      artifact_status: "gated",
      manifest_gate: {
        schema: "trashbot.field_evidence_manifest.v1",
        status: "gated",
        gate_pass: true,
        blocked_reason: "preflight_ready_not_delivery_proof",
        source: "local_fixture",
      },
      blocked_reason: "preflight_ready_not_delivery_proof",
      not_proven: true,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    },
    task_summary: {
      task_id: "task-consumer-001",
      robot_id: "robot_fixture",
      task_status_summary: "completed_mock",
      started_at_ms: 1000,
      finished_at_ms: 2000,
    },
    trajectory: {
      status: "loaded_not_proven",
      frame_count: 3,
      sample_frames: [
        {
          frame_index: 0,
          timestamp_ms: 1000,
          pose: { x_m: 0.2, y_m: 0.1, yaw_rad: 0 },
          velocity: { linear_mps: 0.1 },
          state: "consumer_departed",
          evidence_ref: "consumer-frame-000.jpg",
        },
        {
          frame_index: 1,
          timestamp_ms: 1200,
          pose: { x_m: 0.4, y_m: 0.3, yaw_rad: 0.1 },
          velocity: { linear_mps: 0.2 },
          state: "consumer_en_route",
          evidence_ref: "consumer-frame-001.jpg",
        },
      ],
    },
    events: {
      status: "loaded_not_proven",
      count: 2,
      sample_events: [{ event_type: "route.frame", state: "consumer_en_route", timestamp_ms: 1200, evidence_ref: "consumer-event-001.json" }],
    },
    evidence: {
      status: "loaded_not_proven",
      count: 1,
      sample_evidence: [{ evidence_type: "snapshot", state: "consumer_en_route", timestamp_ms: 1200, evidence_ref: "consumer-evidence-001.jpg" }],
    },
    labeling: {
      status: "partial",
      label_count: 1,
      sample_items: [{ item_id: "label-1", frame_id: "frame-001", status: "pending", evidence_ref: "consumer-label-001.json" }],
    },
    inference: {
      status: "present",
      count: 1,
      sample_results: [{ result_type: "floor_recognition", status: "not_proven", timestamp_ms: 1200, evidence_ref: "consumer-inference-001.json" }],
    },
    tunnel_status: {
      status: "loaded_not_proven",
      latest_known_status: "online",
      temporal_alignment: "latest_known_robot_snapshot_not_task_aligned",
    },
    blocked_reasons: [],
    not_proven: ["proof_status=not_proven", "robot_control_executed=false"],
    fail_closed_reason: "none",
    local_loopback_only: true,
    connects_cloud_production: false,
    robot_control_executed: false,
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
  "/api/o7/realtime-elevator-probe": {
    schema: "trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1",
    probe_status: "loaded_fail_closed_contract",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint: "/api/o7/realtime-elevator/snapshot",
    remote_schema: "trashbot.o7.realtime_elevator_snapshot.v1",
    realtime_status: "blocked_not_proven",
    snapshot_status: "blocked_not_proven",
    map_ref_summary: "id=not_connected, status=blocked_not_proven, evidence_ref=missing_real_map_artifact",
    map_frame_summary: "frame_id=map, source=contract_placeholder_not_tf, status=blocked_not_proven",
    robot_pose_summary:
      "x_m=1.25, y_m=-0.75, yaw_rad=1.57, pose_source=fixture_pose_slot_not_tf, timestamp_ms=2000, evidence_ref=pose-slot.json, real_ros2_tf_connected=false",
    pose_freshness_summary: "age_ms=not_loaded, latency_lt_2s_proven=false, status=blocked_not_proven",
    probe_observed_at_ms: 7000,
    remote_pose_timestamp_ms: 2000,
    remote_pose_age_ms: 5000,
    freshness_gate_status: "pc_only_freshness_observed_not_latency_proof:blocked_not_proven",
    latency_lt_2s_proven: false,
    route_membership_false_fields: ["route_membership.on_route=false", "route_membership.in_elevator_zone=false"],
    elevator_status: "current_state=waiting_operator, sample_count=6, status=blocked_not_proven",
    elevator_state_samples_summary: [
      "#1, state=waiting_operator, status=fixture_summary_only, timestamp_ms=2000, evidence_ref=state-001.json",
      "#2, state=door_open_observed, status=fixture_summary_only, timestamp_ms=2100, evidence_ref=state-002.json",
    ],
    current_floor_evidence_summary:
      "floor_label=not_connected, confidence=not_loaded, floor_recognition_proven=false, status=blocked_not_proven",
    human_takeover_summary:
      "required=true, human_takeover_proven=false, reason=real_elevator_state_chain_not_proven, status=blocked_not_proven",
    key_false_fields: [
      "real_realtime_api_connected=false",
      "real_ros2_tf_connected=false",
      "latency_lt_2s_proven=false",
      "route_membership.on_route=false",
      "route_membership.in_elevator_zone=false",
      "real_elevator_state_chain_connected=false",
      "floor_recognition_proven=false",
      "human_takeover_proven=false",
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
    ],
    dangerous_true_fields: [],
    blocked_reasons: ["real_realtime_api_not_connected", "ros2_tf_forwarding_not_proven"],
    not_proven: ["real_o7_realtime_cloud_stream", "real_current_floor_recognition"],
    fail_closed_reason: "none_remote_contract_is_still_blocked_not_proven",
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  },
  "/api/o7/rtc-signaling-contract-probe": {
    schema: "trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1",
    probe_status: "loaded_fail_closed_contract",
    source_base_url: "http://127.0.0.1:8088",
    remote_endpoint: "/api/o7/rtc-signaling/contract",
    remote_schema: "trashbot.o7.rtc_signaling_contract.v1",
    contract_status: "static_fail_closed_contract",
    key_false_fields: [
      "network_probe_executed=false",
      "webrtc_session_created=false",
      "media_transport_connected=false",
      "video_track_received=false",
      "realtime_pose_stream_connected=false",
      "real_ros2_tf_connected=false",
      "safe_to_control=false",
      "sends_commands=false",
      "reads_hardware=false",
      "robot_control_executed=false",
      "delivery_success=false",
    ],
    protocol_surface_keys: [
      "credential_handling",
      "elevator_realtime_events",
      "failure_timeout_semantics",
      "ice_candidates",
      "media_tracks",
      "observability_evidence_refs",
      "offer_answer",
      "pose_realtime_events",
      "session_identity",
      "signaling_endpoint",
    ],
    required_evidence_refs: [
      "signaling_trace_ref",
      "ice_connectivity_trace_ref",
      "first_video_frame_ref",
      "robot_side_signaling_client_trace",
      "ros2_tf_bridge_trace",
    ],
    blocked_reasons: ["rtc_signaling_endpoint_not_implemented", "video_track_not_received"],
    not_proven: ["real_rtc_signaling_session", "real_webrtc_media_transport", "real_ros2_tf_connected"],
    dangerous_true_fields: [],
    fail_closed_reason: "none_remote_contract_is_still_static_fail_closed",
    local_loopback_only: true,
    network_probe_executed: false,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  },
  "/api/o7/live-endpoints/manifest": {
    schema: "trashbot.o7.live_endpoints_manifest.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    manifest_status: "readiness_manifest_ready",
    endpoint: "/api/o7/live-endpoints/manifest",
    env_only: true,
    network_probe_executed: false,
    sends_commands: false,
    safe_to_control: false,
    connects_cloud_production: false,
    robot_control_executed: false,
    reads_hardware: false,
    token_values_exposed: false,
    url_query_hash_credentials_exposed: false,
    summary: {
      configured: 1,
      not_configured: 4,
      blocked: 1,
      token_present: 1,
      token_absent: 5,
    },
    capabilities: [
      {
        id: "rtc_realtime_pose_elevator",
        kr_ids: ["O7-KR1", "O7-KR2"],
        title: "RTC/realtime pose/elevator state API",
        env: { url: "O7_RTC_REALTIME_URL", token: "O7_RTC_REALTIME_TOKEN" },
        status: "configured",
        proof_status: "not_proven",
        url: {
          configured: true,
          display_url: "wss://relay.example.test/o7/realtime",
          protocol: "wss",
          host: "relay.example.test",
          path: "/o7/realtime",
          unsafe_reason: "",
        },
        token: { env: "O7_RTC_REALTIME_TOKEN", status: "present" },
        missing: [],
        blocked_reasons: [],
        required_live_evidence: ["rtc_signaling_trace", "realtime_pose_latency_trace"],
        remaining_real_capability_gaps: ["real_rtc_video_connected", "real_ros2_tf_forwarding"],
      },
      {
        id: "cloud_archive",
        kr_ids: ["O7-KR3"],
        title: "Cloud archive API",
        env: { url: "O7_CLOUD_ARCHIVE_URL", token: "O7_CLOUD_ARCHIVE_TOKEN" },
        status: "not_configured",
        proof_status: "not_proven",
        url: {
          configured: false,
          display_url: "not_configured",
          protocol: "",
          host: "",
          path: "",
          unsafe_reason: "",
        },
        token: { env: "O7_CLOUD_ARCHIVE_TOKEN", status: "absent" },
        missing: ["url", "token"],
        blocked_reasons: [],
        required_live_evidence: ["cloud_archive_task_query_trace"],
        remaining_real_capability_gaps: ["real_cloud_archive_connected"],
      },
      {
        id: "route_replay_source",
        kr_ids: ["O7-KR3"],
        title: "Route replay data source API",
        env: { url: "O7_ROUTE_REPLAY_URL", token: "O7_ROUTE_REPLAY_TOKEN" },
        status: "blocked",
        proof_status: "not_proven",
        url: {
          configured: false,
          display_url: "blocked_unsafe_url",
          protocol: "https",
          host: "replay.example.test",
          path: "/api",
          unsafe_reason: "url_must_not_include_credentials_query_or_hash",
        },
        token: { env: "O7_ROUTE_REPLAY_TOKEN", status: "absent" },
        missing: ["token"],
        blocked_reasons: ["O7_ROUTE_REPLAY_URL:url_must_not_include_credentials_query_or_hash"],
        required_live_evidence: ["route_replay_frame_page_trace"],
        remaining_real_capability_gaps: ["real_route_replay_frames"],
      },
      {
        id: "annotation_submit_api",
        kr_ids: ["O7-KR4"],
        title: "Annotation submit API",
        env: { url: "O7_ANNOTATION_API_URL", token: "O7_ANNOTATION_API_TOKEN" },
        status: "not_configured",
        proof_status: "not_proven",
        url: {
          configured: false,
          display_url: "not_configured",
          protocol: "",
          host: "",
          path: "",
          unsafe_reason: "",
        },
        token: { env: "O7_ANNOTATION_API_TOKEN", status: "absent" },
        missing: ["url", "token"],
        blocked_reasons: [],
        required_live_evidence: ["annotation_submit_audit_trace"],
        remaining_real_capability_gaps: ["real_annotation_submit"],
      },
      {
        id: "voice_asr_tts_api",
        kr_ids: ["O7-KR5"],
        title: "Voice ASR/TTS API",
        env: { url: "O7_VOICE_API_URL", token: "O7_VOICE_API_TOKEN" },
        status: "not_configured",
        proof_status: "not_proven",
        url: {
          configured: false,
          display_url: "not_configured",
          protocol: "",
          host: "",
          path: "",
          unsafe_reason: "",
        },
        token: { env: "O7_VOICE_API_TOKEN", status: "absent" },
        missing: ["url", "token"],
        blocked_reasons: [],
        required_live_evidence: ["asr_stream_partial_final_trace"],
        remaining_real_capability_gaps: ["real_voice_api_connected"],
      },
      {
        id: "safe_command_api",
        kr_ids: ["O7-KR6"],
        title: "Safe command API",
        env: { url: "O7_SAFE_COMMAND_API_URL", token: "O7_SAFE_COMMAND_TOKEN" },
        status: "not_configured",
        proof_status: "not_proven",
        url: {
          configured: false,
          display_url: "not_configured",
          protocol: "",
          host: "",
          path: "",
          unsafe_reason: "",
        },
        token: { env: "O7_SAFE_COMMAND_TOKEN", status: "absent" },
        missing: ["url", "token"],
        blocked_reasons: [],
        required_live_evidence: ["idempotent_command_api_trace"],
        remaining_real_capability_gaps: ["real_robot_ack_connected"],
      },
    ],
    required_live_evidence: [
      "rtc_signaling_trace",
      "realtime_pose_latency_trace",
      "cloud_archive_task_query_trace",
      "route_replay_frame_page_trace",
      "annotation_submit_audit_trace",
      "asr_stream_partial_final_trace",
      "idempotent_command_api_trace",
    ],
    remaining_real_capability_gaps: [
      "real_rtc_video_connected",
      "real_ros2_tf_forwarding",
      "real_cloud_archive_connected",
      "real_route_replay_frames",
      "real_annotation_submit",
      "real_voice_api_connected",
      "real_robot_ack_connected",
    ],
    blocked_reasons: ["O7_ROUTE_REPLAY_URL:url_must_not_include_credentials_query_or_hash"],
    not_proven: ["real_rtc_video_connected", "real_robot_ack_connected"],
  },
};

function cloneFixture<T>(value: T): T {
  // fixture 需要在单测内局部改写；深拷贝可以避免跨用例串改共享常量。
  return JSON.parse(JSON.stringify(value)) as T;
}

function stubWorkstationFetch(fixtureOverrides: Record<string, unknown> = {}) {
  // 测试桩允许 route debug 带 query，确保表单路径仍走同一个只读 API。
  const localFixtures = { ...fixtures, ...fixtureOverrides };
  const mockedFetch = vi.fn(async (url: string, options?: RequestInit) => {
    let fixtureKey = url;
    if (url.startsWith("/api/route/debug-summary")) {
      fixtureKey = "/api/route/debug-summary";
    } else if (url.startsWith("/api/robot-control/summary")) {
      fixtureKey = "/api/robot-control/summary";
    } else if (url.startsWith("/api/robot-control/base/first-jog")) {
      fixtureKey = "/api/robot-control/base/first-jog";
    } else if (url.startsWith("/api/robot-control/base/manual")) {
      fixtureKey = "/api/robot-control/base/manual";
    } else if (url.startsWith("/api/robot-control/base/stop")) {
      fixtureKey = "/api/robot-control/base/stop";
    } else if (url.startsWith("/api/robot-control/base/feedback-samples")) {
      fixtureKey = "/api/robot-control/base/feedback-samples";
    } else if (url.startsWith("/api/robot-control/radar/scan-proof/refresh")) {
      fixtureKey = "/api/robot-control/radar/scan-proof/refresh";
    } else if (url.startsWith("/api/robot-control/radar/start")) {
      fixtureKey = "/api/robot-control/radar/start";
    } else if (url.startsWith("/api/robot-control/radar/stop")) {
      fixtureKey = "/api/robot-control/radar/stop";
    } else if (url.startsWith("/api/robot-control/map/proof/refresh")) {
      fixtureKey = "/api/robot-control/map/proof/refresh";
    } else if (url.startsWith("/api/robot-control/nav2/proof/refresh")) {
      fixtureKey = "/api/robot-control/nav2/proof/refresh";
    } else if (url.startsWith("/api/robot-control/nav2/goal/preflight")) {
      fixtureKey = "/api/robot-control/nav2/goal/preflight";
    } else if (url.startsWith("/api/robot-control/nav2/goal/execute")) {
      fixtureKey = "/api/robot-control/nav2/goal/execute";
    } else if (url.startsWith("/api/robot-control/nav2/goal/execution/latest")) {
      fixtureKey = "/api/robot-control/nav2/goal/execution/latest";
    } else if (url.startsWith("/api/robot-control/delivery/latest")) {
      fixtureKey = "/api/robot-control/delivery/latest";
    } else if (url.startsWith("/api/robot-control/delivery/check")) {
      fixtureKey = "/api/robot-control/delivery/check";
    } else if (url.startsWith("/api/robot-control/delivery/complete")) {
      fixtureKey = "/api/robot-control/delivery/complete";
    } else if (url.startsWith("/api/robot-control/localize/reset")) {
      fixtureKey = "/api/robot-control/localize/reset";
    } else if (url.startsWith("/api/robot-control/map/list")) {
      fixtureKey = "/api/robot-control/map/list";
    } else if (url.startsWith("/api/robot-control/map/save")) {
      fixtureKey = "/api/robot-control/map/save";
    } else if (url.startsWith("/api/robot-control/operator/report")) {
      fixtureKey = "/api/robot-control/operator/report";
    } else if (url.startsWith("/api/robot-control/camera/first-frame/probe")) {
      fixtureKey = "/api/robot-control/camera/first-frame/probe";
    } else if (url.startsWith("/api/robot-control/camera/offer")) {
      fixtureKey = "/api/robot-control/camera/offer";
    } else if (url.startsWith("/api/robot-control/camera/peers/peer-preview-001/close")) {
      fixtureKey = "/api/robot-control/camera/peers/peer-preview-001/close";
    } else if (url.startsWith("/api/o7/consumer-read/tasks/")) {
      fixtureKey = "/api/o7/consumer-read/tasks/task-consumer-001";
    } else if (url.startsWith("/api/o7/consumer-read/tasks")) {
      fixtureKey = "/api/o7/consumer-read/tasks";
    } else if (url.startsWith("/api/o7/realtime-elevator-preview")) {
      fixtureKey = "/api/o7/realtime-elevator-preview";
    } else if (url.startsWith("/api/o7/route-replay-preview")) {
      fixtureKey = "/api/o7/route-replay-preview";
    } else if (url.startsWith("/api/o7/labeling-preview")) {
      fixtureKey = "/api/o7/labeling-preview";
    } else if (url.startsWith("/api/o7/field-evidence-consumer-ingest")) {
      fixtureKey = "/api/o7/field-evidence-consumer-ingest";
    } else if (url.startsWith("/api/o7/voice-preview")) {
      fixtureKey = "/api/o7/voice-preview";
    } else if (url.startsWith("/api/o7/safe-command-preview")) {
      fixtureKey = "/api/o7/safe-command-preview";
    } else if (url.startsWith("/api/o7/previews/acceptance")) {
      fixtureKey = "/api/o7/previews/acceptance";
    } else if (url.startsWith("/api/o7/live-endpoints/manifest")) {
      fixtureKey = "/api/o7/live-endpoints/manifest";
    } else if (url.startsWith("/api/o7/cloud-archive/tasks-probe")) {
      fixtureKey = "/api/o7/cloud-archive/tasks-probe";
    } else if (url.startsWith("/api/o7/cloud-archive/tasks")) {
      fixtureKey = "/api/o7/cloud-archive/tasks";
    } else if (url.startsWith("/api/o7/cloud-operator-console-probe")) {
      fixtureKey = "/api/o7/cloud-operator-console-probe";
    } else if (url.startsWith("/api/o7/rtc-signaling-contract-probe")) {
      fixtureKey = "/api/o7/rtc-signaling-contract-probe";
    } else if (url.startsWith("/api/o7/realtime-elevator-probe")) {
      fixtureKey = "/api/o7/realtime-elevator-probe";
    }
    if (options?.method === "POST" && fixtureKey === "/api/robot-control/camera/offer") {
      const body = JSON.parse(String(options.body ?? "{}")) as { type?: string; sdp?: string };
      if (body.type !== "offer" || !body.sdp) {
        return {
          ok: false,
          status: 400,
          json: async () => ({
            schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
            proxy_status: "offer_rejected",
            failure_reason: "invalid_offer_request",
            ...PROOF_FLAGS,
          }),
        };
      }
    }
    return {
      ok: true,
      json: async () => localFixtures[fixtureKey],
    };
  });
  vi.stubGlobal("fetch", mockedFetch);
  return mockedFetch;
}

function writePlainHomeSmokeArtifact(firstScreenText: string, advancedText: string, advancedDetailsClosed: boolean): void {
  // 该 artifact 只证明默认 DOM 文案收敛，不把折叠区的诊断能力解释成已联调。
  mkdirSync(SPRINT_ARTIFACT_DIR, { recursive: true });
  const forbiddenTokenPresence = Object.fromEntries(
    DEFAULT_FIRST_SCREEN_FORBIDDEN_TOKENS.map((token) => [token, firstScreenText.includes(token)]),
  );
  writeFileSync(
    resolve(SPRINT_ARTIFACT_DIR, "pc_plain_user_home_dom_smoke.json"),
    `${JSON.stringify(
      {
        schema: "trashbot.pc_workstation.plain_user_home_dom_smoke.v1",
        checked_at: new Date().toISOString(),
        first_screen_card_titles: ["小车连接", "实时画面", "雷达", "地图", "移动/导航"],
        simple_user_console_forbidden_token_presence: Object.fromEntries(
          SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS.map((token) => [token, firstScreenText.includes(token)]),
        ),
        forbidden_token_presence: forbiddenTokenPresence,
        advanced_diagnostics_closed_by_default: true,
        advanced_entries_retained: {
          check_path: advancedText.includes("检查路径（高级）"),
          nav_goal_preflight: advancedText.includes("导航目标预检（高级）"),
          hil_materials: advancedText.includes("现场 HIL 材料"),
          proof_readback: advancedText.includes("latest readback key values"),
          advanced_details_closed: advancedDetailsClosed,
        },
      },
      null,
      2,
    )}\n`,
  );
}

function writeCameraFrameQualityArtifact(payload: Record<string, unknown>): void {
  // 该 artifact 只记录前端本地 video/canvas 诊断，不包含真实图像内容或截图落盘。
  mkdirSync(SPRINT_ARTIFACT_DIR, { recursive: true });
  writeFileSync(
    resolve(SPRINT_ARTIFACT_DIR, "camera_frame_quality_dom_smoke.json"),
    `${JSON.stringify(payload, null, 2)}\n`,
  );
}

function visiblePlainHomeText(wrapper: VueWrapper): string {
  // Vue Test Utils 会把关闭的 details 文本也算进 wrapper.text()；这里显式拼默认可见首屏。
  return [
    wrapper.find(".topbar").text(),
    wrapper.find(".simple-user-console").text(),
  ].join("\n");
}

describe("App", () => {
  afterEach(() => {
    // 清理全局 fetch，避免后续用例误用上一轮 API fixture。
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders fail-closed Node route loader and evidence fixture index", async () => {
    // UI 测试只使用 API fixture，确保页面不自己发明机器人状态或旧执行入口。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).toContain("node_route_json_loader");
    expect(advancedToolsText).toContain("pc-tools/workstation/src/server/routeDebugLoader.ts");
    expect(advancedToolsText).toContain("console_controls");
    expect(advancedToolsText).toContain("read_only");
    expect(advancedToolsText).toContain("not_loaded_pc_only");
    expect(advancedToolsText).toContain("blocked_not_proven");
    expect(advancedToolsText).toContain("status_json_not_provided");
    expect(advancedToolsText).not.toContain("route_debug_web.py");
    expect(advancedToolsText).not.toContain("python -m");
    expect(advancedToolsText).not.toContain("workstation_executes_python_gate");
    expect(advancedToolsText).not.toContain("/cmd_vel");
    expect(advancedToolsText).not.toContain("/dev/tty");
  });

  it("submits route inputs through the workstation API query contract", async () => {
    // 组件只更新表单状态，query 拼接必须由 src/client/workstationApi.ts 集中完成。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const routeInputs = wrapper.findAll("form.route-inputs input");
    expect(routeInputs).toHaveLength(4);
    await routeInputs[0]!.setValue("C:\\tmp\\status proof.json");
    await wrapper.find("form.route-inputs").trigger("submit");
    await flushPromises();

    const routeCall = mockedFetch.mock.calls
      .map(([url]) => String(url))
      .find((url) => url.startsWith("/api/route/debug-summary?"));
    expect(routeCall).toBeTruthy();
    const parsed = new URL(routeCall ?? "", "http://workstation.local");
    expect(parsed.searchParams.get("statusJson")).toBe("C:\\tmp\\status proof.json");
    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).not.toContain("/cmd_vel");
    expect(advancedToolsText).not.toContain("/dev/tty");
  });

  it("renders Robot Control V1 by default with Robot API proxy and locked command boundary", async () => {
    // 首屏默认就是 Robot Control；测试只验证 Node proxy 摘要和 locked UI，不触发任何真实控制 endpoint。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenCards = wrapper.findAll(".robot-console-grid > .snapshot-panel");
    expect(firstScreenCards).toHaveLength(5);
    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("Rober 小车控制台");
    expect(firstScreenText).toContain("连接小车、查看画面和地图，必要时一键停止。");
    expect(firstScreenText).toContain("小车连接");
    expect(firstScreenText).toContain("实时画面");
    expect(firstScreenText).toContain("雷达");
    expect(firstScreenText).toContain("雷达已运行");
    expect(firstScreenText).toContain("地图");
    expect(firstScreenText).toContain("移动/导航");
    expect(firstScreenText).toContain("已连接");
    expect(firstScreenText).toContain("部分项目未通过，可展开高级诊断。");
    expect(firstScreenText).toContain("未打开");
    expect(firstScreenText).toContain("未刷新");
    expect(firstScreenText).toContain("地图列表");
    expect(firstScreenText).toContain("重新建图");
    expect(firstScreenText).toContain("保存地图");
    expect(firstScreenText).toContain("待试动");
    expect(firstScreenText).toContain("现场画面已记录；可以试动一下。");
    expect(firstScreenText).toContain("重新定位");
    expect(firstScreenText).toContain("移动前检查");
    expect(firstScreenText).toContain("启用键盘");
    expect(wrapper.find('[data-testid="keyboard-control-stop"]').text()).toBe("键盘停止（随时可点）");
    expect(firstScreenText).toContain("W/A/S/D 或方向键");
    expect(firstScreenText).toContain("当前方向：未按键");
    expect(firstScreenText).toContain("本轮进度");
    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去行程卡点");
    expect(wrapper.find('[data-testid="plain-goal-progress-refresh"]').text()).toBe("刷新进度（只读）");
    expect(wrapper.find('[data-testid="plain-goal-progress-next-action"]').text()).toContain("下一步：先处理行程执行。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toBe("当前状态：轮速记录已完成；行程执行待完成；送达确认待完成；键盘手控未满足。");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toBe("当前读数：轮速已完成；行程未完成；送达未完成；键盘未满足。");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toBe("验收卡点：还没读到行程成功结果。");
    expect(firstScreenText).toContain("去轮速");
    expect(firstScreenText).toContain("去行程");
    expect(firstScreenText).toContain("去送达");
    expect(firstScreenText).toContain("去键盘");
    expect(firstScreenText).toContain("轮速记录");
    expect(firstScreenText).toContain("点“试动一下”后读取轮速。");
    expect(firstScreenText).toContain("雷达移动记录还没拿到：试动时需要雷达看到前后变化，之后键盘手控才会解锁。");
    expect(firstScreenText).toContain("行程操作");
    expect(firstScreenText).toContain("先勾选行程前确认，再检查或执行。");
    expect(firstScreenText).toContain("先勾选确认");
    expect(firstScreenText).toContain("读取行程结果（只读）");
    expect(firstScreenText).toContain("行程执行");
    expect(firstScreenText).toContain("送达确认");
    expect(firstScreenText).toContain("键盘手控");
    expect(firstScreenText).toContain("先补齐键盘手控条件，再启用键盘。还差：键盘入口、移动前检查、雷达移动记录。");
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先复查入口，不发车）");
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').text()).toBe("启用键盘（先复查入口）");
    expect(wrapper.find('[data-testid="plain-keyboard-next-action"]').text()).toContain("下一步：复查手控条件。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("先补齐键盘手控条件。还差：键盘入口、移动前检查、雷达移动记录。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("下一步：复查手控条件。");
    expect(firstScreenText).toContain("最终确认");
    expect(firstScreenText).toContain("待行程");
    expect(firstScreenText).toContain("先完成本轮行程，再做最终确认。");
    expect(firstScreenText).toContain("还差 9 项：本轮行程、送达材料、人在旁边可接管、周围安全、停止手段就绪、已观察到到达/移动、已观察到停止、视频和行程材料已核对、确认已投放/送达。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="plain-goal-progress-refresh"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid^="plain-goal-progress-go-"]')).toHaveLength(4);
    expect(wrapper.find('[data-testid="plain-trip-run"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-wheel-record"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("低速试动读轮速");
    expect(wrapper.find('[data-testid="plain-wheel-readback-refresh"]').text()).toBe("刷新当前轮速（只读）");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').text()).toBe("保存轮速记录（先试动）");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-delivery-final-confirm"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="plain-trip-run"]').attributes("tabindex")).toBe("-1");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').attributes("tabindex")).toBe("-1");
    expect(wrapper.find('[data-testid="plain-delivery-status"]').attributes("tabindex")).toBe("-1");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find(".simple-user-console [data-testid='keyboard-control-panel']").exists()).toBe(true);
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find(".simple-user-console .motion-pad").exists()).toBe(false);
    expect(firstScreenText).toContain("任务收口");
    expect(wrapper.find('[data-testid="plain-delivery-latest"]').text()).toBe("刷新送达状态（只读）");
    expect(wrapper.find('[data-testid="plain-delivery-gap-check"]').text()).toBe("复查送达条件（不确认）");
    expect(firstScreenText).toContain("停止");
    expect(firstScreenText).not.toContain("目标收口进度");
    expect(firstScreenText).not.toContain("普通用户入口");
    expect(firstScreenText).not.toContain("http://192.168.1.11:8787");
    expect(wrapper.find(".robot-console > .section-head").exists()).toBe(false);
    expect(wrapper.find(".simple-user-console input[name='robotApiBaseUrl']").exists()).toBe(false);
    const robotBaseUrlInput = wrapper.find('input[name="robotApiBaseUrl"]');
    const defaultRobotBaseUrlButton = wrapper.find('[data-testid="robot-api-default"]');
    const defaultRobotBaseUrlAdvancedButton = wrapper.find('[data-testid="robot-api-default-advanced"]');
    expect((robotBaseUrlInput.element as HTMLInputElement).value).toBe("http://192.168.1.11:8787");
    expect(defaultRobotBaseUrlButton.text()).toBe("恢复默认");
    expect(defaultRobotBaseUrlButton.attributes("disabled")).toBeDefined();
    expect(defaultRobotBaseUrlAdvancedButton.text()).toBe("恢复默认地址");
    expect(defaultRobotBaseUrlAdvancedButton.attributes("disabled")).toBeDefined();
    await robotBaseUrlInput.setValue("");
    await wrapper.vm.$nextTick();
    expect(defaultRobotBaseUrlButton.attributes("disabled")).toBeUndefined();
    expect(defaultRobotBaseUrlAdvancedButton.attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="robot-api-default-summary"]').text()).toBe("已改为高级地址");
    const fetchCallsBeforeDefaultRestore = mockedFetch.mock.calls.length;
    await defaultRobotBaseUrlButton.trigger("click");
    await wrapper.vm.$nextTick();
    expect((robotBaseUrlInput.element as HTMLInputElement).value).toBe("http://192.168.1.11:8787");
    expect(wrapper.find('[data-testid="robot-api-default-summary"]').text()).toBe("已使用默认地址");
    expect(mockedFetch.mock.calls).toHaveLength(fetchCallsBeforeDefaultRestore);
    expect(
      mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787")),
    ).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execution/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    const simpleUserConsoleText = wrapper.find(".simple-user-console").text();
    for (const token of SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS) {
      expect(simpleUserConsoleText).not.toContain(token);
    }
    const firstScreenForbiddenTokens = [
      ...DEFAULT_FIRST_SCREEN_FORBIDDEN_TOKENS,
      "路线",
      "预览",
      "证据",
      "硬件",
      "数据",
      "安全边界",
      "开始建图",
      "重置地图",
      "启动雷达",
      "停止雷达",
      "structured_hil_claims",
      "现场确认",
      "低速短时点动",
      "外部视频",
      "轮速反馈",
      "视频材料",
      "速度",
      "时长",
      "readback",
      "raw",
      "source",
      "status key",
      "safe_to_control",
      "delivery_success",
      "safe_to_control",
      "/dev/ttyS5",
      "自动导航",
      "最近证据",
      "task_id",
      "O6 consumer base URL",
      "peer_id",
      "ice_connection_state",
      "scan_once_observed",
      "map_once_observed",
      "未检查",
      "路径可生成",
      "导航目标",
      "path_generation_succeeded",
      "path_point_count",
      "目标 x",
      "导航目标预检",
    ];
    for (const token of firstScreenForbiddenTokens) {
      expect(firstScreenText).not.toContain(token);
    }
    expect(wrapper.text()).not.toContain("source=software_proof");
    expect(wrapper.text()).not.toContain("proof_status=not_proven");
    expect(wrapper.find(".shell > .tabs").exists()).toBe(false);
    expect(wrapper.find(".advanced-tools-details > summary").text()).toContain("高级工具");
    expect(wrapper.find(".advanced-tools-details").attributes("open")).toBeUndefined();
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("路线");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("控制台");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("预览");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("证据");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("硬件");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("数据");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).toContain("安全边界");
    expect(wrapper.find(".advanced-tools-details .tabs").text()).not.toContain("机器人");
    const diagnostics = wrapper.find(".robot-console .advanced-details");
    expect(diagnostics.find("summary").text()).toContain("高级诊断");
    expect(diagnostics.attributes("open")).toBeUndefined();
    const goalClosureText = wrapper.find('[data-testid="goal-closure-checklist"]').text();
    expect(goalClosureText).toContain("wheel raw L/R 非零");
    expect(goalClosureText).toContain("完整 Nav2 路线执行");
    expect(goalClosureText).toContain("delivery success");
    expect(goalClosureText).toContain("PC 键盘连续手控");
    expect(goalClosureText).not.toContain("/cmd_vel");
    const keyboardClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItem?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItem?.text()).toContain("键盘合同未从 summary 读到");
    expect(diagnostics.text()).toContain("task_id");
    expect(diagnostics.text()).toContain("Robot API status");
    expect(diagnostics.text()).toContain("Node server only; Vue direct access=false");
    expect(diagnostics.text()).toContain("path_generated");
    expect(diagnostics.text()).toContain("planner_server_not_active");
    expect(diagnostics.text()).toContain("safe_to_control=false");
    expect(diagnostics.text()).toContain("delivery_success=false");
    expect(diagnostics.text()).toContain("primary_actions_enabled=false");
    expect(diagnostics.text()).toContain("现场 HIL 材料");
    expect(diagnostics.text()).toContain("operator_report_latest.structured_hil_claims");
    expect(diagnostics.text()).toContain("phone-video-0605.mp4");
    expect(diagnostics.text()).toContain("轮速反馈");
    expect(diagnostics.text()).toContain("field_operator_claim_ready_for_review");
    expect(diagnostics.text()).toContain("提交现场材料（高级）");
    expect(diagnostics.text()).toContain("operator report preflight");
    expect(diagnostics.text()).toContain("latest submit");
    expect(diagnostics.text()).toContain("/api/operator/report");
    expect(diagnostics.text()).toContain("现场点动设置 / 控制边界");
    expect(diagnostics.text()).toContain("Nav2 规划详情");
    expect(diagnostics.text()).toContain("检查路径（高级）");
    expect(diagnostics.text()).toContain("导航目标预检（高级）");
    expect(diagnostics.text()).toContain("确认仅做导航目标预检");
    expect(diagnostics.text()).toContain("启动雷达（高级）");
    expect(diagnostics.text()).toContain("停止雷达（高级）");
    expect(diagnostics.text()).toContain("latest_proof_fresh_while_lifecycle_running");
    expect(diagnostics.text()).toContain("lifecycle=true/running");
    expect(diagnostics.text()).toContain("window=true/fresh_window_observed");
    expect(diagnostics.text()).toContain("前进");
    expect(diagnostics.text()).toContain("速度上限");
    expect(diagnostics.text()).toContain("现场有人扶控并准备急停");
    writePlainHomeSmokeArtifact(firstScreenText, diagnostics.text(), diagnostics.attributes("open") === undefined);
  });

  it("shows a plain timeout hint when the robot API does not respond", async () => {
    // 真实现场可能出现上位机 HTTP 全部 timeout；普通首屏要给可执行排查动作，不暴露 endpoint 细节或发控制命令。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.robot_api_connection = {
      status: "degraded",
      loaded_count: 0,
      blocked_count: 0,
      failed_count: 12,
      schema_mismatch_count: 0,
      dangerous_true_fields: [],
      blocked_reasons: [
        "status:fetch_timeout_5000ms",
        "base_status:fetch_timeout_5000ms",
        "delivery_latest:fetch_timeout_5000ms",
      ],
      last_refresh_ms: 1782141632169,
    };
    const mockedFetch = stubWorkstationFetch({ "/api/robot-control/summary": summaryFixture });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("小车连接");
    expect(firstScreenText).toContain("有异常");
    expect(firstScreenText).toContain("上位机没回应；检查小车电源、网络和上位机服务后再点连接/刷新。");
    expect(firstScreenText).not.toContain("fetch_timeout");
    expect(firstScreenText).not.toContain("/api/base");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("refreshes plain goal progress with read-only endpoints only", async () => {
    // 普通首屏的进度刷新只重读摘要、底盘反馈、最近行程和送达状态；不能借刷新触发运动或送达确认。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=not_loaded";
    summaryFixture.readback_summary.base.latest_feedback_status = "stale";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/feedback-samples": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
        proxy_status: "samples_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/feedback-samples",
        remote_http_status: 200,
        status: "loaded",
        sample_key_values: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_result",
          requested_sample_count: "3",
          completed_sample_count: "3",
          t1001_observed_count: "3",
          all_samples_observed_t1001: "true",
          partial_samples_observed_t1001: "false",
          feedback_ack_t1001_observed: "true",
          wheel_feedback_lr_nonzero_proven: "false",
          wheel_feedback_nonzero_observed: "false",
          wheel_feedback_nonzero_frame_count: "0",
          wheel_feedback_latest_left_speed: "0",
          wheel_feedback_latest_right_speed: "0",
          wheel_feedback_source: "vendor_t1001_L_R",
          observed_feedback_types: "[1001]",
          sends_motion_commands: "false",
          robot_control_executed: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        sends_motion_commands: false,
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const callsBeforeClick = mockedFetch.mock.calls.length;
    const summaryCallsBeforeClick = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/summary?"),
    ).length;
    const navLatestCallsBeforeClick = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/nav2/goal/execution/latest?"),
    ).length;
    const deliveryLatestCallsBeforeClick = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/delivery/latest?"),
    ).length;
    const baseFeedbackSamplesCallsBeforeClick = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/base/feedback-samples?"),
    ).length;

    const refreshButton = wrapper.find('[data-testid="plain-goal-progress-refresh"]');
    expect(refreshButton.exists()).toBe(true);
    expect(refreshButton.text()).toBe("刷新进度（只读）");
    expect(refreshButton.attributes("disabled")).toBeUndefined();
    await refreshButton.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const callsAfterClick = mockedFetch.mock.calls.slice(callsBeforeClick).map(([url]) => String(url));
    expect(callsAfterClick).toHaveLength(4);
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary?")).length,
    ).toBe(summaryCallsBeforeClick + 1);
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/feedback-samples?")).length,
    ).toBe(baseFeedbackSamplesCallsBeforeClick + 1);
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execution/latest?")).length,
    ).toBe(navLatestCallsBeforeClick + 1);
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?")).length,
    ).toBe(deliveryLatestCallsBeforeClick + 1);
    expect(callsAfterClick.some((url) => url.startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(callsAfterClick.some((url) => url.startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(callsAfterClick.some((url) => url.startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(callsAfterClick.some((url) => url.includes("/cmd_vel"))).toBe(false);
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("当前轮速 L/R=0/0，已读到 3 帧，仍需试动读到非零。");
    expect(wrapper.find('[data-testid="plain-wheel-readback-summary"]').text()).not.toContain("历史轮速样本已过期");

    const wheelRefreshCallsBeforeClick = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/base/feedback-samples?"),
    ).length;
    await wrapper.find('[data-testid="plain-wheel-readback-refresh"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/feedback-samples?")).length,
    ).toBe(wheelRefreshCallsBeforeClick + 1);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
  });

  it("shows current wheel L/R and frame count in plain goal progress from summary", async () => {
    // 本轮进度要直接解释当前 wheel L/R=0/0，避免用户误以为只要有反馈帧就算完成。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.readback_summary.base.latest_t1001_observed_count = "12";
    summaryFixture.readback_summary.base.wheel_feedback_latest_left_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_latest_right_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_lr_nonzero_proven = "false";
    summaryFixture.readback_summary.base.wheel_feedback_nonzero_observed = "false";
    summaryFixture.readback_summary.base.feedback_voltage_v = "12.43";
    summaryFixture.readback_summary.base.latest_feedback_status = "stale";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=not_loaded";
    const mockedFetch = stubWorkstationFetch({ "/api/robot-control/summary": summaryFixture });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const plainProgress = wrapper.find('[data-testid="plain-goal-progress"]').text();
    expect(plainProgress).toContain("轮速记录");
    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去轮速记录卡点");
    expect(wrapper.find('[data-testid="plain-goal-progress-next-action"]').text()).toContain("下一步：先处理轮速记录。当前轮速 L/R=0/0");
    expect(plainProgress).toContain("当前轮速 L/R=0/0，已读到 12 帧，反馈电压约 12.43V，下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toBe("验收卡点：轮速 L/R=0/0，检查电机使能、供电、模式和现场空间后重试。");
    expect(wrapper.find('[data-testid="plain-wheel-readback-summary"]').text()).toContain("历史轮速样本已过期，以当前读回为准");
    expect(wrapper.find('[data-testid="plain-wheel-next-action"]').text()).toContain("下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。");
    expect(wrapper.find('[data-testid="plain-wheel-zero-check-summary"]').text()).toContain("轮速卡点：请确认电机使能、供电、模式和现场空间后再重试。");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("先查卡点再重试读非零 L/R");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').text()).toBe("保存轮速记录（先试动）");
    const callsBeforeZeroCheck = mockedFetch.mock.calls.length;
    await wrapper.find('[data-testid="plain-wheel-zero-check"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-wheel-zero-check"]').text()).toBe("轮速卡点已检查");
    expect(wrapper.find('[data-testid="plain-wheel-zero-check-summary"]').text()).toContain("轮速卡点已检查：电机使能、供电、模式和现场空间已确认；下一步低速重试读非零 L/R。");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("检查后重试读非零 L/R");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeZeroCheck);
    expect(visiblePlainHomeText(wrapper)).not.toContain("raw");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("shows historical wheel material separately from current zero readback", async () => {
    // 已保存的 during-motion 轮速材料不能被当前停车 0/0 读回抹掉，但 UI 必须讲清来源。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=pc-first-jog-wheel-lr-history";
    summaryFixture.readback_summary.base.latest_t1001_observed_count = "13";
    summaryFixture.readback_summary.base.wheel_feedback_latest_left_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_latest_right_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_lr_nonzero_proven = "false";
    summaryFixture.readback_summary.base.wheel_feedback_nonzero_observed = "false";
    stubWorkstationFetch({ "/api/robot-control/summary": summaryFixture });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const wheelClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("wheel raw L/R 非零"));
    expect(wheelClosureItem?.attributes("data-ready")).toBe("true");
    expect(wheelClosureItem?.text()).toContain("已有历史非零材料；当前只读 L/R=0/0，本轮复验需低速重试");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("轮速有历史材料，当前 L/R=0/0");
    expect(wrapper.find('[data-testid="plain-goal-progress-next-action"]').text()).toContain("下一步：先处理行程执行。");
  });

  it("shows restore-first-jog as the next wheel step when delivery draft replaced basic safety", async () => {
    // 送达草稿覆盖 basic safety 后，进度区应先引导恢复确认，再让现场试动读非零。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.readback_summary.base.latest_t1001_observed_count = "13";
    summaryFixture.readback_summary.base.wheel_feedback_latest_left_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_latest_right_speed = "0";
    summaryFixture.operator_hil_material_summary.operator_present = "false";
    summaryFixture.operator_hil_material_summary.physical_clearance = "false";
    summaryFixture.operator_hil_material_summary.emergency_stop = "false";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=not_loaded";
    summaryFixture.first_jog_readiness_summary = {
      status: "blocked_missing_basic_safety",
      basic_safety_ready: false,
      visual_material_ready: true,
      missing_fields: ["operator_present", "physical_clearance_confirmed", "emergency_stop_ready"],
      next_action: "complete_basic_safety_check",
    };
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({ "/api/robot-control/summary": summaryFixture });
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("当前轮速 L/R=0/0，已读到 13 帧，先点恢复试动确认，再试动读非零。");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toBe("验收卡点：送达草稿覆盖了试动确认，先恢复试动确认，再低速试动读非零 L/R。");
    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去恢复确认");
    expect(wrapper.find('[data-testid="plain-goal-progress-go-wheel"]').text()).toBe("去恢复");
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').text()).toBe("启用键盘（先恢复确认）");
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先恢复确认，不发车）");
    expect(wrapper.find('[data-testid="plain-keyboard-next-action"]').text()).toContain("下一步：恢复试动确认（不会发车）。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("还差：移动前检查、恢复试动确认、轮速记录、雷达移动记录。");
    const callsBeforeFocus = mockedFetch.mock.calls.length;
    await wrapper.find('[data-testid="plain-goal-progress-primary-action"]').trigger("click");
    expect(focusSpy).toHaveBeenCalled();
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeFocus);
    expect(wrapper.find('[data-testid="plain-first-jog-restore"]').attributes("disabled")).toBeUndefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("focuses plain goal progress targets without calling robot APIs", async () => {
    // 进度快捷按钮只是把用户带到对应普通面板；不替用户执行行程、确认送达或发送手控。
    const mockedFetch = stubWorkstationFetch();
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const callsBeforeClick = mockedFetch.mock.calls.length;
    const focusCallsBeforeClick = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-goal-progress-primary-action"]').trigger("click");
    const targets = ["wheel", "trip", "delivery", "keyboard"];
    for (const target of targets) {
      await wrapper.find(`[data-testid="plain-goal-progress-go-${target}"]`).trigger("click");
    }
    expect(wrapper.find('[data-testid="plain-goal-progress-go-wheel"]').text()).toBe("去轮速");
    expect(wrapper.find('[data-testid="plain-goal-progress-go-trip"]').text()).toBe("去行程");
    expect(wrapper.find('[data-testid="plain-goal-progress-go-delivery"]').text()).toBe("去送达");
    expect(wrapper.find('[data-testid="plain-goal-progress-go-keyboard"]').text()).toBe("去键盘");

    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去行程卡点");
    expect(focusSpy.mock.calls.length).toBe(focusCallsBeforeClick + 5);
    expect(mockedFetch.mock.calls.length).toBe(callsBeforeClick);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("runs plain trip preflight and execution only after the safety checkbox is checked", async () => {
    // 普通首屏可以触发固定行程代理，但必须先显式勾选；测试不触发任何底盘手控或 cmd_vel endpoint。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execute": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_proxy.v1",
        proxy_status: "execution_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execute",
        remote_endpoint: "/api/nav2/goal/execute",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_request: {
          goal_frame_id: "map",
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          result_timeout_s: 8,
          confirm_navigation_execution: true,
        },
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "plain-trip-execution-fixture",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
      },
    });
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const tripPanel = wrapper.find('[data-testid="plain-trip-run"]');
    expect(tripPanel.exists()).toBe(true);
    expect(tripPanel.text()).toContain("行程操作");
    expect(tripPanel.text()).toContain("待确认");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').attributes("disabled")).toBeDefined();

    await wrapper.find('input[name="plainTripSafetyConfirmed"]').setValue(true);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("检查行程");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("执行行程");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="plain-trip-execute"]').attributes("disabled")).toBeUndefined();

    await wrapper.find('[data-testid="plain-trip-preflight"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const preflightCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/preflight?"));
    expect(preflightCall).toBeTruthy();
    expect(JSON.parse(String((preflightCall?.[1] as RequestInit | undefined)?.body ?? "{}"))).toEqual({
      goal_frame_id: "map",
      goal_x: 0.8,
      goal_y: 0,
      goal_yaw: 0,
      confirm_navigation_preflight: true,
    });

    const focusCallsBeforeExecute = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-trip-execute"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const executeCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"));
    expect(executeCall).toBeTruthy();
    expect(JSON.parse(String((executeCall?.[1] as RequestInit | undefined)?.body ?? "{}"))).toEqual({
      goal_frame_id: "map",
      goal_x: 0.8,
      goal_y: 0,
      goal_yaw: 0,
      result_timeout_s: 8,
      confirm_navigation_execution: true,
    });
    expect((wrapper.find('input[name="deliveryOperatorRouteMapRef"]').element as HTMLInputElement).value).toBe("plain-trip-execution-fixture");
    expect((wrapper.find('input[name="deliveryEvidenceRef"]').element as HTMLInputElement).value).toBe("delivery-confirmation-plain-trip-execution-fixture");
    expect(visiblePlainHomeText(wrapper)).toContain("最近行程成功，反馈 8 次；送达仍需现场确认。");
    expect(wrapper.find('[data-testid="plain-trip-evidence-summary"]').text()).toContain("最近行程成功，反馈 8 次；送达仍需现场确认。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("最近行程成功，反馈 8 次；送达仍需现场确认。");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("行程已完成");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("行程已完成");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-trip-latest"]').text()).toBe("重新读取行程（只读）");
    expect(visiblePlainHomeText(wrapper)).toContain("行程材料已在，点准备送达材料补画面。");
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforeExecute);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-delivery-status"]').element);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(visiblePlainHomeText(wrapper)).not.toContain("Nav2");
    expect(visiblePlainHomeText(wrapper)).not.toContain("proof");
    expect(visiblePlainHomeText(wrapper)).not.toContain("/cmd_vel");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("shows stale latest Nav2 success age on the plain first screen without sending commands", async () => {
    // latest 只读结果可能很旧；普通首屏必须讲清年龄，不能把它冒充成本轮新路线证明。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-stale-fixture",
          generated_at_ms: "1782099547218",
          response_generated_at_ms: "1782150147954",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const staleSummary = "最近行程成功，反馈 8 次，约 14 小时前；这条记录较旧，如需本轮复验，请重新执行行程；送达仍需现场确认。";
    expect(wrapper.find('[data-testid="plain-trip-evidence-summary"]').text()).toContain(staleSummary);
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("最近行程记录较旧，需要重新执行本轮行程。");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("最近行程成功，反馈 8 次，约 14 小时前；这条记录较旧，如需本轮复验，请重新执行行程；送达未完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("行程执行待完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去行程卡点");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("先勾选确认");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("keeps a fresh Nav2 success without feedback samples out of the complete route gate", async () => {
    // 完整路线执行必须有 goal_succeeded 和执行反馈样本；空 success 摘要不能放行送达确认。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-no-feedback-fixture",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
          result_status: "succeeded",
          feedback_sample_count: "0",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="plain-trip-evidence-summary"]').text()).toContain("最近行程成功，未读到反馈样本，刚刚；需重新读取或执行完整行程。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("行程执行待完成");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("最近行程缺少反馈样本，需要重新读取或执行完整行程。");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toContain("验收卡点：行程成功但缺少反馈样本，需要重新读取或执行完整行程。");
    expect(wrapper.find('[data-testid="plain-delivery-next-action"]').text()).toContain("下一步：重新读取或执行完整行程。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("本轮行程");
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-no-feedback-fixture");
    await wrapper.find('input[name="deliveryEvidenceRef"]').setValue("delivery-confirmation-o11-nav2-goal-execution-no-feedback-fixture");
    await wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 1 项：本轮行程。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先重新行程）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("turns camera source first-frame failure into a plain first-screen hint", async () => {
    // 首屏可以提示用户检查摄像头/视频线，但不能把 source_readiness 或 first_frame_timeout 露出来。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as RobotControlSummaryResponse;
    summaryFixture.readback_summary.camera.status = "source_first_frame_failed";
    summaryFixture.readback_summary.camera.source_readiness = "first_frame_failed";
    summaryFixture.readback_summary.camera.source_failure_reason = "first_frame_timeout";
    summaryFixture.readback_summary.camera.last_offer_error = "first_frame_unreadable";
    summaryFixture.readback_summary.camera.last_offer_failure_reason = "first_frame_timeout";
    stubWorkstationFetch({ "/api/robot-control/summary": summaryFixture });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("实时画面");
    expect(firstScreenText).toContain("失败");
    expect(firstScreenText).toContain("相机没有出画面，检查摄像头/视频线。");
    expect(firstScreenText).not.toContain("source_readiness");
    expect(firstScreenText).not.toContain("first_frame_timeout");
    expect(firstScreenText).not.toContain("/dev/video1");
    for (const token of SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS) {
      expect(wrapper.find(".simple-user-console").text()).not.toContain(token);
    }
  });

  it("submits operator report material from advanced diagnostics without leaking it to the first screen", async () => {
    // 表单只在高级诊断里出现；提交走固定 workstation proxy，不把 delivery claim 升成顶层成功。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).not.toContain("提交现场材料");
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await wrapper.find('input[name="operatorReportEvidenceRef"]').setValue("field-hil-ui-submit");
    await wrapper.find('input[name="operatorReportSiteState"]').setValue("field_operator_claim_ready_for_review");
    await wrapper.find('input[name="operatorReportExternalVideoRef"]').setValue("phone-video-ui.mp4");
    await wrapper.find('input[name="operatorReportCameraArtifactsRef"]').setValue("runtime/camera/latest_metrics.json");
    await wrapper.find('input[name="operatorReportWheelFeedbackRef"]').setValue("runtime/wave_rover_feedback_debug.jsonl");
    const reportForm = wrapper.findAll("form").find((form) => form.text().includes("提交现场材料"));
    expect(reportForm).toBeTruthy();
    const claimChecks = reportForm?.findAll(".compact-checklist input[type='checkbox']") ?? [];
    await claimChecks[0]?.setValue(true);
    await claimChecks[1]?.setValue(true);
    await claimChecks[2]?.setValue(true);
    await claimChecks[5]?.setValue(true);
    await claimChecks[6]?.setValue(true);
    await claimChecks[10]?.setValue(true);

    await reportForm?.trigger("submit");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const [url, options] = reportCall ?? ["", {} as RequestInit];
    const parsed = new URL(String(url), "http://workstation.local");
    const body = JSON.parse(String((options as RequestInit).body ?? "{}")) as Record<string, unknown>;
    expect(parsed.searchParams.get("baseUrl")).toBe("http://192.168.1.11:8787");
    expect((options as RequestInit).method).toBe("POST");
    expect(body.delivery_success).toBeUndefined();
    expect(body.safe_to_control).toBeUndefined();
    expect(body.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      visible_content_proven: true,
      delivery_success: true,
      external_video_ref: "phone-video-ui.mp4",
    }));
    expect(wrapper.find("details").text()).toContain("report_forwarded");
    expect(wrapper.find("details").text()).toContain("phone-video-ui.mp4");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("delivery_success");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("外部视频");
  });

  it("keeps non-stop motion disabled when operator material is incomplete but still allows stop", async () => {
    // 非 stop 点动必须等 checklist 和现场材料都齐；材料缺项时只能保留 stop 作为 fail-safe。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.external_video = "not_loaded";
    summaryFixture.operator_hil_material_summary.camera_visible = "not_loaded";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "not_loaded";
    summaryFixture.operator_hil_material_summary.lidar_delta = "false; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.first_jog_readiness_summary = {
      status: "blocked_missing_visual_material",
      basic_safety_ready: true,
      visual_material_ready: false,
      missing_fields: ["external_video_or_visible_camera"],
      next_action: "record_visual_material",
    };
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
      "/api/robot-control/base/stop": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "stop",
        proxy_status: "command_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/stop",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        requested_direction: "stop",
        applied_direction: "stop",
        requested_speed_mps: 0,
        clamped_speed_mps: 0,
        requested_duration_ms: 0,
        clamped_duration_ms: 0,
        confirm_hil_checklist: false,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "stop_allowed_without_checklist",
        checklist_missing: [],
        operator_report_preflight: {
          status: "not_required_for_stop",
          source_endpoint: "/api/operator/report",
          request_status: "not_required",
          http_status: null,
          report_status: "not_required_for_stop",
          evidence_ref: "not_required_for_stop",
          required_fields: [],
          missing_fields: [],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "blocked",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: [],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "stop command evidence snapshot blocked in fixture",
        motion_evidence_gaps: ["stop_command_not_motion_proof"],
        failure_reason: "",
        blocked_reasons: [],
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    const diagnostics = wrapper.find(".robot-console .advanced-details");
    expect(diagnostics.text()).toContain("材料未满足，本机不会发送点动");
    expect(diagnostics.text()).toContain("external_video_recorded");
    expect(diagnostics.text()).toContain("visible_content_proven");
    expect(diagnostics.text()).toContain("wheel_feedback_lr_nonzero_proven");
    expect(diagnostics.text()).toContain("physical_motion_lidar_delta_proven");
    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("待记录");
    expect(firstScreenText).toContain("先记录现场画面，再试动一下；需要时可直接停止。");
    expect(firstScreenText).not.toContain("现场材料");
    expect(firstScreenText).not.toContain("external_video_recorded");
    expect(firstScreenText).not.toContain("physical_motion_lidar_delta_proven");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("先记录画面再试动");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-wheel-save"]').text()).toBe("保存轮速记录（先记录画面）");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').attributes("disabled")).toBeDefined();

    const motionButtons = wrapper.findAll(".motion-pad button");
    const forwardButton = motionButtons.find((button) => button.text() === "前进");
    const stopButton = motionButtons.find((button) => button.text() === "停止");
    expect(forwardButton?.attributes("disabled")).toBeDefined();
    expect(stopButton?.attributes("disabled")).toBeUndefined();

    await forwardButton?.trigger("click");
    await flushPromises();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(wrapper.find(".robot-console .advanced-details").text()).not.toContain("blocked_keyboard_manual_gate");

    const blockedArmButton = wrapper.find('[data-testid="keyboard-control-arm"]');
    expect(blockedArmButton.attributes("disabled")).toBeDefined();
    await blockedArmButton.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const blockedKeyboardPanel = wrapper.find('[data-testid="keyboard-control-panel"]');
    await blockedKeyboardPanel.trigger("keydown", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(wrapper.find(".robot-console .advanced-details").text()).not.toContain("blocked_keyboard_manual_gate");
    const feedbackCallsBeforeKeyboardRecheck = mockedFetch.mock.calls.filter(([url]) =>
      String(url).startsWith("/api/robot-control/base/feedback-samples?"),
    ).length;
    await wrapper.find('[data-testid="keyboard-control-recheck"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(
      mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/feedback-samples?")).length,
    ).toBe(feedbackCallsBeforeKeyboardRecheck + 1);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);

    await stopButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const stopCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/base/stop?"));
    expect(stopCall).toBeTruthy();
    expect((stopCall?.[1] as RequestInit | undefined)?.method).toBe("POST");
  });

  it("points the keyboard arm button at wheel proof once earlier plain gates are ready", async () => {
    // 前置普通 gate 已满足时，键盘入口应把 operator 引向当前真实卡点：轮速非零证据。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_review";
    summaryFixture.operator_hil_material_summary.operator_present = "true";
    summaryFixture.operator_hil_material_summary.physical_clearance = "true";
    summaryFixture.operator_hil_material_summary.emergency_stop = "true";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=phone-video-0605.mp4";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=runtime/camera/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=runtime/wave_rover_feedback_debug.jsonl";
    summaryFixture.operator_hil_material_summary.lidar_delta = "false; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    const armButton = wrapper.find('[data-testid="keyboard-control-arm"]');
    expect(armButton.text()).toBe("启用键盘（先补轮速）");
    expect(armButton.attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先补轮速，不发车）");
    expect(visiblePlainHomeText(wrapper)).toContain("下一步：读取并保存轮速记录。");

    await armButton.trigger("click");
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("points the keyboard arm button at lidar motion once wheel proof is ready", async () => {
    // 轮速补齐后，键盘 gate 的下一块真实材料通常是 LiDAR 位移记录。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_review";
    summaryFixture.operator_hil_material_summary.operator_present = "true";
    summaryFixture.operator_hil_material_summary.physical_clearance = "true";
    summaryFixture.operator_hil_material_summary.emergency_stop = "true";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=phone-video-0605.mp4";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=runtime/camera/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=runtime/wave_rover_feedback_debug.jsonl";
    summaryFixture.operator_hil_material_summary.lidar_delta = "false; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    const armButton = wrapper.find('[data-testid="keyboard-control-arm"]');
    expect(armButton.text()).toBe("启用键盘（先补雷达）");
    expect(armButton.attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先补雷达，不发车）");
    expect(visiblePlainHomeText(wrapper)).toContain("下一步：试动读取雷达移动记录。");

    await armButton.trigger("click");
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("keeps keyboard disabled when summary lacks the bounded pulse contract even after manual gate is ready", async () => {
    // 连续键盘手控不能只靠材料 gate 放开；后端 summary 必须显式声明 bounded pulse 合同。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_execution";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=phone-video-0605.mp4";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=runtime/camera/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=runtime/wave_rover_feedback_debug.jsonl";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=runtime/scan_delta/latest_metrics.json";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("键盘合同未从 summary 读到");
    expect(visiblePlainHomeText(wrapper)).toContain("先补齐键盘手控条件，再启用键盘。还差：键盘入口。");
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先复查入口，不发车）");
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').text()).toBe("启用键盘（先复查入口）");
    expect(wrapper.find('[data-testid="plain-keyboard-next-action"]').text()).toContain("下一步：复查手控条件。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("先补齐键盘手控条件。还差：键盘入口。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("下一步：复查手控条件。");
    const keyboardClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItem?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItem?.text()).toContain("键盘合同未从 summary 读到");

    const armButton = wrapper.find('[data-testid="keyboard-control-arm"]');
    expect(armButton.attributes("disabled")).toBeDefined();
    await armButton.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const keyboardPanel = wrapper.find('[data-testid="keyboard-control-panel"]');
    await keyboardPanel.trigger("keydown", { key: "w" });
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("submits a plain motion precheck without unlocking non-stop motion", async () => {
    // 普通首屏只能提交基础现场确认；视频、轮速和 LiDAR delta 材料不能被它伪造成已满足。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.external_video = "not_loaded";
    summaryFixture.operator_hil_material_summary.camera_visible = "not_loaded";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "not_loaded";
    summaryFixture.operator_hil_material_summary.lidar_delta = "not_loaded";
    summaryFixture.first_jog_readiness_summary = {
      status: "blocked_missing_visual_material",
      basic_safety_ready: true,
      visual_material_ready: false,
      missing_fields: ["external_video_or_visible_camera"],
      next_action: "record_visual_material",
    };
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: { wheel_feedback_lr_nonzero_proven: true, delivery_success: false },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const plainPrecheckButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "移动前检查");
    expect(plainPrecheckButton).toBeTruthy();
    await plainPrecheckButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const [url, options] = reportCall ?? ["", {} as RequestInit];
    const parsed = new URL(String(url), "http://workstation.local");
    const body = JSON.parse(String((options as RequestInit).body ?? "{}")) as Record<string, any>;
    expect(parsed.searchParams.get("baseUrl")).toBe("http://192.168.1.11:8787");
    expect((options as RequestInit).method).toBe("POST");
    expect(body.operator_present).toBe(true);
    expect(body.physical_clearance_confirmed).toBe(true);
    expect(body.emergency_stop_ready).toBe(true);
    expect(body.observed_motion).toBe(false);
    expect(body.observed_stop).toBe(true);
    expect(String(body.evidence_ref)).toMatch(/^plain-motion-precheck-/);
    expect(body.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: false,
      visible_content_proven: false,
      wheel_feedback_lr_nonzero_proven: false,
      physical_motion_lidar_delta_proven: false,
      delivery_success: false,
      site_state: "plain_motion_precheck_ready_for_review",
    }));
    expect(body.safe_to_control).toBeUndefined();
    expect(body.delivery_success).toBeUndefined();

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("已记录");
    expect(firstScreenText).toContain("移动前检查已记录；还需要现场画面。");
    expect(firstScreenText).not.toContain("operator_report");
    expect(firstScreenText).not.toContain("structured_hil_claims");
    expect(firstScreenText).not.toContain("external_video_recorded");
    expect(mockedFetch.mock.calls.some(([callUrl]) => String(callUrl).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("shows raw wheel L/R from base feedback samples without treating T1001 count as nonzero proof", async () => {
    // T=1001 计数只是反馈链路；UI 必须直接显示 L/R=0/0 和 nonzero=false。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=not_loaded";
    summaryFixture.readback_summary.base.feedback_voltage_v = "12.43";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/feedback-samples": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
        proxy_status: "samples_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/feedback-samples",
        remote_http_status: 200,
        status: "loaded",
        sample_key_values: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_result",
          requested_sample_count: "3",
          completed_sample_count: "3",
          t1001_observed_count: "3",
          all_samples_observed_t1001: "true",
          partial_samples_observed_t1001: "false",
          feedback_ack_t1001_observed: "true",
          wheel_feedback_lr_nonzero_proven: "false",
          wheel_feedback_nonzero_observed: "false",
          wheel_feedback_nonzero_frame_count: "0",
          wheel_feedback_latest_left_speed: "0",
          wheel_feedback_latest_right_speed: "0",
          wheel_feedback_source: "vendor_t1001_L_R",
          observed_feedback_types: "[1001]",
          sends_motion_commands: "false",
          robot_control_executed: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        sends_motion_commands: false,
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const feedbackButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "采集底盘反馈（高级）");
    expect(feedbackButton).toBeTruthy();
    await feedbackButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const diagnosticsText = wrapper.find(".robot-console .advanced-details").text();
    expect(diagnosticsText).toContain("base feedback raw L/R");
    expect(diagnosticsText).toContain("latest_L=0");
    expect(diagnosticsText).toContain("latest_R=0");
    expect(diagnosticsText).toContain("nonzero_frames=0");
    expect(diagnosticsText).toContain("proven=false");
    expect(diagnosticsText).toContain("source=vendor_t1001_L_R");
    expect(diagnosticsText).toContain("wheel raw L/R progress");
    expect(diagnosticsText).toContain("static T1001 feedback only");
    expect(diagnosticsText).toContain("next=restore first-jog materials then run wheel nonzero trial");
    expect(visiblePlainHomeText(wrapper)).toContain("已读到底盘反馈，但当前轮速是 L/R=0/0；反馈电压约 12.43V；这还不是非零证据；若试动后仍为 0/0，检查电机使能、供电、模式和现场空间。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("当前轮速 L/R=0/0，已读到 3 帧，反馈电压约 12.43V，下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。");
    expect(wrapper.find('[data-testid="plain-wheel-next-action"]').text()).toContain("下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/feedback-samples?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("does not close wheel raw L/R from static nonzero base feedback samples", async () => {
    // 只读 samples 可能读到非零 L/R，但它不是试动窗口材料，不能点亮保存或目标收口。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.wheel_feedback = "false; ref=not_loaded";
    summaryFixture.readback_summary.base.wheel_feedback_latest_left_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_latest_right_speed = "0";
    summaryFixture.readback_summary.base.wheel_feedback_lr_nonzero_proven = "false";
    summaryFixture.readback_summary.base.wheel_feedback_nonzero_observed = "false";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/feedback-samples": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
        proxy_status: "samples_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/feedback-samples",
        remote_http_status: 200,
        status: "loaded",
        requested_sample_count: 3,
        sample_interval_s: 0.08,
        read_timeout_s: 0.8,
        read_window_s: 1.0,
        sample_key_values: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_result",
          requested_sample_count: "3",
          completed_sample_count: "3",
          t1001_observed_count: "3",
          all_samples_observed_t1001: "true",
          partial_samples_observed_t1001: "false",
          feedback_ack_t1001_observed: "true",
          wheel_feedback_lr_nonzero_proven: "true",
          wheel_feedback_nonzero_observed: "true",
          wheel_feedback_nonzero_frame_count: "2",
          wheel_feedback_latest_left_speed: "0.08",
          wheel_feedback_latest_right_speed: "0.08",
          wheel_feedback_source: "vendor_t1001_L_R",
          observed_feedback_types: "[1001]",
          sends_motion_commands: "false",
          robot_control_executed: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        sends_motion_commands: false,
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    await wrapper.find('[data-testid="plain-wheel-readback-refresh"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="plain-wheel-readback-summary"]').text()).toContain("只读轮速已出现非零：L/R=0.08/0.08；仍以试动窗口保存为准。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("轮速记录待完成");
    const wheelClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("wheel raw L/R 非零"));
    expect(wheelClosureItem?.attributes("data-ready")).toBe("false");
    expect(wheelClosureItem?.text()).toContain("只读采样读到非零 L/R=0.08/0.08；仍需低速试动窗口保存");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').attributes("disabled")).toBeDefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("restores first-jog material from existing visual refs without sending motion", async () => {
    // 送达草稿可能覆盖 latest report；恢复按钮只补 first-jog 前置材料，不触发试动。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "unsafe_or_incomplete";
    summaryFixture.operator_hil_material_summary.evidence_ref = "delivery-draft-fixture";
    summaryFixture.operator_hil_material_summary.operator_present = "false";
    summaryFixture.operator_hil_material_summary.physical_clearance = "false";
    summaryFixture.operator_hil_material_summary.emergency_stop = "false";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=pc-first-jog-wheel-before-restore";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=scan-delta-before-restore";
    summaryFixture.operator_hil_material_summary.route_map = "true; ref=o11-nav2-goal-execution-before-restore";
    summaryFixture.operator_hil_material_summary.delivery_claim = "false";
    summaryFixture.operator_hil_material_summary.site_state = "delivery_material_draft_not_operator_confirmed";
    summaryFixture.first_jog_readiness_summary = {
      status: "blocked_missing_basic_safety",
      basic_safety_ready: false,
      visual_material_ready: true,
      missing_fields: ["operator_present", "physical_clearance_confirmed", "emergency_stop_ready"],
      next_action: "complete_basic_safety_check",
    };
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: { delivery_success: false },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    expect(visiblePlainHomeText(wrapper)).toContain("已有现场画面；请恢复试动确认后再试动，恢复确认不会发车。");
    expect(visiblePlainHomeText(wrapper)).toContain("试动按钮已锁定：请先点恢复试动确认（不会发车）。");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("先点“恢复试动确认”（不会发车），再试动读取轮速。");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("恢复试动确认");
    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("first-jog material restore");
    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("latest-only operator report is delivery_material_draft_not_operator_confirmed");
    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("action=restore first-jog confirmation");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("先恢复确认再试动");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-wheel-save"]').text()).toBe("保存轮速记录（先恢复确认）");
    expect(wrapper.find('[data-testid="plain-wheel-save"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').text()).toBe("启用键盘（先恢复确认）");
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件（先恢复确认，不发车）");
    expect(wrapper.find('[data-testid="plain-keyboard-next-action"]').text()).toContain("下一步：恢复试动确认（不会发车）。");
    const firstJogButtonBeforeRestore = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "试动一下");
    expect(firstJogButtonBeforeRestore).toBeTruthy();
    expect(firstJogButtonBeforeRestore?.attributes("disabled")).toBeDefined();

    const restoreButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "恢复试动确认");
    expect(restoreButton).toBeTruthy();
    expect(restoreButton?.attributes("disabled")).toBeUndefined();
    const callsBeforeRestore = mockedFetch.mock.calls.length;
    await restoreButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody).toEqual(expect.objectContaining({
      operator_present: true,
      physical_clearance_confirmed: true,
      emergency_stop_ready: true,
      observed_motion: false,
      observed_stop: true,
    }));
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg",
      visible_content_proven: true,
      camera_artifacts_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_restore.jpg",
      wheel_feedback_lr_nonzero_proven: true,
      wheel_feedback_ref: "pc-first-jog-wheel-before-restore",
      physical_motion_lidar_delta_proven: true,
      scan_delta_ref: "scan-delta-before-restore",
      real_route_map_proven: true,
      route_map_ref: "o11-nav2-goal-execution-before-restore",
      delivery_success: false,
      site_state: "plain_first_jog_material_restored_for_trial",
    }));
    const firstJogButtonAfterRestore = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "试动一下");
    expect(firstJogButtonAfterRestore?.attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("开始低速试动读非零 L/R");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').attributes("disabled")).toBeUndefined();
    expect(focusSpy).toHaveBeenCalled();
    expect(visiblePlainHomeText(wrapper)).not.toContain("试动按钮已锁定");
    expect(mockedFetch.mock.calls.length).toBeGreaterThan(callsBeforeRestore);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/first-jog?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("records a plain video reference and sends first-jog through the fixed proxy only", async () => {
    // 普通首屏可以走 first-jog 入口，但不会伪造轮速/LiDAR，也不会退回旧 manual 代理。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.external_video = "not_loaded";
    summaryFixture.operator_hil_material_summary.camera_visible = "not_loaded";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "not_loaded";
    summaryFixture.operator_hil_material_summary.lidar_delta = "not_loaded";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/first-jog": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "manual",
        proxy_status: "command_rejected",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/manual",
        remote_http_status: null,
        status: "blocked",
        requested_direction: "forward",
        applied_direction: "forward",
        requested_speed_mps: 0.08,
        clamped_speed_mps: 0.08,
        requested_duration_ms: 500,
        clamped_duration_ms: 500,
        confirm_hil_checklist: true,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "manual_allowed",
        checklist_missing: [],
        operator_report_preflight: {
          status: "blocked",
          source_endpoint: "/api/operator/report",
          request_status: "loaded",
          http_status: 200,
          report_status: "ready_for_review",
          evidence_ref: "plain-first-jog-video-fixture",
          required_fields: ["operator_present", "physical_clearance_confirmed", "emergency_stop_ready", "external_video_or_visible_camera"],
          missing_fields: ["external_video_or_visible_camera"],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "first_jog_preflight_required",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "blocked",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: ["first_jog_preflight_required"],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "first-jog rejected before remote manual",
        motion_evidence_gaps: [
          "motion_command_not_forwarded",
          "wheel_feedback_lr_nonzero_not_proven",
          "physical_motion_lidar_delta_not_proven",
        ],
        failure_reason: "first_jog_preflight_required",
        blocked_reasons: ["first_jog_preflight_required"],
        hard_dangerous_true_fields: [],
      },
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const firstScreen = wrapper.find(".simple-user-console");
    expect(firstScreen.text()).toContain("现场画面记录");
    expect(firstScreen.text()).toContain("记录画面");
    expect(firstScreen.text()).toContain("试动一下");
    for (const token of SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS) {
      expect(firstScreen.text()).not.toContain(token);
    }

    await wrapper.find('input[name="plainExternalVideoRef"]').setValue("phone-video-plain-001.mp4");
    const recordButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "记录画面");
    await recordButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody.operator_present).toBe(true);
    expect(reportBody.physical_clearance_confirmed).toBe(true);
    expect(reportBody.emergency_stop_ready).toBe(true);
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "phone-video-plain-001.mp4",
      visible_content_proven: false,
      wheel_feedback_lr_nonzero_proven: false,
      physical_motion_lidar_delta_proven: false,
      delivery_success: false,
      site_state: "plain_first_jog_visual_ready_for_review",
    }));
    expect(reportBody.safe_to_control).toBeUndefined();
    expect(reportBody.delivery_success).toBeUndefined();

    const firstJogButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "试动一下");
    await firstJogButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstJogCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/base/first-jog?"));
    expect(firstJogCall).toBeTruthy();
    const [firstJogUrl, firstJogOptions] = firstJogCall ?? ["", {} as RequestInit];
    const parsed = new URL(String(firstJogUrl), "http://workstation.local");
    const firstJogBody = JSON.parse(String((firstJogOptions as RequestInit).body ?? "{}")) as Record<string, unknown>;
    expect(parsed.searchParams.get("baseUrl")).toBe("http://192.168.1.11:8787");
    expect((firstJogOptions as RequestInit).method).toBe("POST");
    expect(firstJogBody).toEqual({
      direction: "forward",
      speed: 0.08,
      duration_ms: 500,
      confirm_hil_checklist: true,
    });
    expect(mockedFetch.mock.calls.some(([callUrl]) => String(callUrl).startsWith("/api/robot-control/base/feedback-samples?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([callUrl]) => String(callUrl).startsWith("/api/robot-control/base/manual?"))).toBe(false);

    const firstScreenAfter = visiblePlainHomeText(wrapper);
    expect(firstScreenAfter).toContain("未试动");
    expect(firstScreenAfter).toContain("还需要先记录现场画面，小车没有移动。");
    expect(firstScreenAfter).not.toContain("first_jog_preflight_required");
    expect(firstScreenAfter).not.toContain("external_video_or_visible_camera");
    expect(firstScreenAfter).not.toContain("physical_motion_lidar_delta_proven");
  });

  it("summarizes first-jog wheel evidence on the plain first screen after a forwarded trial", async () => {
    // 普通首屏要把试动后的 wheel raw L/R 结果翻译成短摘要，不要求用户进高级诊断翻 key。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as RobotControlSummaryResponse;
    summaryFixture.operator_hil_material_summary.lidar_delta = "false; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.route_map = "true; ref=o11-nav2-goal-execution-before-wheel-save";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/first-jog": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "manual",
        proxy_status: "command_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/manual",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        requested_direction: "forward",
        applied_direction: "forward",
        requested_speed_mps: 0.08,
        clamped_speed_mps: 0.08,
        requested_duration_ms: 500,
        clamped_duration_ms: 500,
        confirm_hil_checklist: true,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "manual_allowed",
        checklist_missing: [],
        operator_report_preflight: {
          status: "loaded",
          source_endpoint: "/api/operator/report",
          request_status: "loaded",
          http_status: 200,
          report_status: "ready_for_execution",
          evidence_ref: "plain-first-jog-video-fixture",
          required_fields: [],
          missing_fields: [],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "captured",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: [],
        before_readback: {},
        after_readback: {
          radar_status: {
            phase: "after",
            id: "radar_status",
            endpoint: "/api/radar/status",
            method: "GET",
            request_status: "loaded",
            http_status: 200,
            status: "scan_delta_observed",
            schema: "trashbot.upper_robot_api.v1.radar_status",
            key_values: {
              physical_motion_lidar_delta_proven: "true",
              scan_delta_ref: "first-jog-scan-delta-fixture",
              evidence_ref: "radar-status-fixture",
            },
            failure_reason: "",
          },
        },
        motion_evidence_summary: "first-jog fixture captured during-motion T1001 wheel feedback",
        motion_evidence_gaps: [],
        remote_motion_key_values: {
          wheel_feedback_lr_nonzero_proven: "true",
          wheel_feedback_nonzero_observed: "true",
          wheel_feedback_nonzero_frame_count: "2",
          wheel_feedback_latest_left_speed: "0.08",
          wheel_feedback_latest_right_speed: "0.08",
          wheel_feedback_latest_raw_left: "0.08",
          wheel_feedback_latest_raw_right: "0.08",
          feedback_during_motion_t1001_frame_count: "3",
          feedback_after_stop_t1001_frame_count: "1",
          feedback_during_motion_attempted: "true",
          feedback_after_stop_attempted: "true",
          physical_motion_lidar_delta_proven: "true",
          scan_delta_ref: "first-jog-scan-delta-fixture",
          manual_command_executed: "true",
          auto_stop_executed: "true",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
      },
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    const firstJogButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "试动一下");
    expect(firstJogButton).toBeTruthy();
    expect(firstJogButton?.attributes("disabled")).toBeUndefined();
    await firstJogButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([callUrl]) => String(callUrl).startsWith("/api/robot-control/base/feedback-samples?"))).toBe(true);
    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("已试动");
    expect(firstScreenText).toContain("轮速证据已拿到：L/R=0.08/0.08，运动帧=3。");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("可保存");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("已拿到非零 L/R 和雷达移动记录，先保存。");
    expect(wrapper.find('[data-testid="plain-lidar-motion-record-summary"]').text()).toContain("雷达移动记录已拿到：保存轮速记录时会一起保存。");
    for (const token of SIMPLE_USER_CONSOLE_FORBIDDEN_TOKENS) {
      expect(firstScreenText).not.toContain(token);
    }
    const saveWheelButton = wrapper.find('[data-testid="plain-wheel-save"]');
    expect(saveWheelButton.text()).toBe("保存轮速记录");
    expect(saveWheelButton.attributes("disabled")).toBeUndefined();
    expect(focusSpy).toHaveBeenCalled();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    const focusCallsBeforeSave = focusSpy.mock.calls.length;
    await saveWheelButton.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody).toEqual(expect.objectContaining({
      operator_present: true,
      physical_clearance_confirmed: true,
      emergency_stop_ready: true,
      observed_motion: true,
      observed_stop: true,
    }));
    expect(String(reportBody.evidence_ref)).toMatch(/^pc-first-jog-wheel-lr-/);
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      wheel_feedback_lr_nonzero_proven: true,
      physical_motion_lidar_delta_proven: true,
      scan_delta_ref: "first-jog-scan-delta-fixture",
      real_route_map_proven: true,
      route_map_ref: "o11-nav2-goal-execution-before-wheel-save",
      delivery_success: false,
      site_state: "plain_first_jog_wheel_lr_nonzero_observed",
    }));
    expect(String(reportBody.structured_hil_claims.wheel_feedback_ref)).toMatch(/^pc-first-jog-wheel-lr-/);
    expect(visiblePlainHomeText(wrapper)).toContain("轮速和雷达记录已保存；键盘手控材料可复用。");
    expect(visiblePlainHomeText(wrapper)).toContain("轮速和雷达移动证据已保存；后续手控材料可复用。");
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforeSave);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-trip-run"]').element);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/first-jog?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
  });

  it("explains plain first-jog wheel retry when motion frames keep L/R at zero", async () => {
    // 真实现场曾读到 during-motion T1001 但 L/R=0/0；普通首屏要给出下一步排查，而不是只说失败。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/base/first-jog": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "manual",
        proxy_status: "command_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/manual",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        requested_direction: "forward",
        applied_direction: "forward",
        requested_speed_mps: 0.08,
        clamped_speed_mps: 0.08,
        requested_duration_ms: 500,
        clamped_duration_ms: 500,
        confirm_hil_checklist: true,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "manual_allowed",
        checklist_missing: [],
        operator_report_preflight: {
          status: "loaded",
          source_endpoint: "/api/operator/report",
          request_status: "loaded",
          http_status: 200,
          report_status: "ready_for_execution",
          evidence_ref: "plain-first-jog-video-fixture",
          required_fields: [],
          missing_fields: [],
          material_summary: (fixtures["/api/robot-control/summary"] as RobotControlSummaryResponse).operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "captured",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: [],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "first-jog fixture captured during-motion T1001 wheel feedback at zero",
        motion_evidence_gaps: ["wheel_feedback_lr_nonzero_not_proven"],
        remote_motion_key_values: {
          wheel_feedback_lr_nonzero_proven: "false",
          wheel_feedback_nonzero_observed: "false",
          wheel_feedback_nonzero_frame_count: "0",
          wheel_feedback_latest_left_speed: "0",
          wheel_feedback_latest_right_speed: "0",
          wheel_feedback_latest_raw_left: "0",
          wheel_feedback_latest_raw_right: "0",
          feedback_during_motion_t1001_frame_count: "4",
          feedback_after_stop_t1001_frame_count: "1",
          feedback_during_motion_attempted: "true",
          feedback_after_stop_attempted: "true",
          manual_command_executed: "true",
          auto_stop_executed: "true",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
      },
      "/api/robot-control/base/manual": {
        proxy_status: "should_not_be_called",
      },
      "/api/robot-control/operator/report": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstJogButton = wrapper.findAll(".robot-console-grid button").find((button) => button.text() === "试动一下");
    expect(firstJogButton?.attributes("disabled")).toBeUndefined();
    await firstJogButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("已试动，但轮速还是 0/0：检查电机使能、供电、模式和现场空间后重试。运动帧=4。");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("待重试");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("已试动但 L/R=0/0，检查电机使能、供电、模式和现场空间后重试。");
    expect(wrapper.find('[data-testid="plain-wheel-next-action"]').text()).toContain("下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。");
    expect(wrapper.find('[data-testid="plain-wheel-zero-check-summary"]').text()).toContain("轮速卡点：请确认电机使能、供电、模式和现场空间后再重试。");
    const retryWheelButton = wrapper.find('[data-testid="plain-wheel-trial"]');
    expect(retryWheelButton.text()).toBe("先查卡点再重试读非零 L/R");
    expect(retryWheelButton.attributes("disabled")).toBeUndefined();
    const callsBeforeZeroCheck = mockedFetch.mock.calls.length;
    await wrapper.find('[data-testid="plain-wheel-zero-check"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-wheel-zero-check"]').text()).toBe("轮速卡点已检查");
    expect(wrapper.find('[data-testid="plain-wheel-record"]').text()).toContain("轮速卡点已检查；请低速重试读取非零 L/R。");
    expect(wrapper.find('[data-testid="plain-wheel-zero-check-summary"]').text()).toContain("轮速卡点已检查：电机使能、供电、模式和现场空间已确认；下一步低速重试读非零 L/R。");
    expect(wrapper.find('[data-testid="plain-wheel-trial"]').text()).toBe("检查后重试读非零 L/R");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeZeroCheck);
    const firstJogCallsBeforeRetry = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/first-jog?")).length;
    await wrapper.find('[data-testid="plain-wheel-trial"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/first-jog?")).length).toBe(firstJogCallsBeforeRetry + 1);
    const saveWheelButton = wrapper.find('[data-testid="plain-wheel-save"]');
    expect(saveWheelButton.text()).toBe("保存轮速记录（等非零 L/R）");
    expect(saveWheelButton.attributes("disabled")).toBeDefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("prefills delivery video ref from fixed camera first-frame probe without submitting delivery", async () => {
    // 送达材料的画面 ref 可以从固定 camera probe 样张预填，但不能自动提交送达 claim。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/camera/first-frame/probe": {
        schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
        proxy_status: "probe_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/camera/first-frame/probe",
        remote_http_status: 200,
        status: "visible_content_candidate",
        probe_key_values: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe",
          device: "/dev/video1",
          requested_fourcc: "MJPG",
          open_ok: "true",
          read_ok: "true",
          first_frame_timeout: "false",
          failure_reason: "",
          visible_content_proven: "false",
          visible_content_candidate: "true",
          sample_path: "/root/rober/onboard/runtime/camera/first_frame_probe_fixture.jpg",
          sample_write_ok: "true",
          elapsed_ms: "120",
          mean_luma: "42.0",
          max_luma: "220",
          dynamic_range_luma: "180",
          non_black_ratio: "0.8",
          backend_smoke_status: "not_requested",
          backend_frame_observed: "false",
          backend_attempts: "0",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": {
        proxy_status: "should_not_be_called",
      },
      "/api/robot-control/delivery/complete": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const fillVideoButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "使用最近画面 ref");
    expect(fillVideoButton).toBeTruthy();
    await fillVideoButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect((wrapper.find('input[name="deliveryOperatorVideoRef"]').element as HTMLInputElement).value).toBe(
      "/root/rober/onboard/runtime/camera/first_frame_probe_fixture.jpg",
    );
    const probeCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/camera/first-frame/probe?"));
    expect(probeCall).toBeTruthy();
    expect((probeCall?.[1] as RequestInit | undefined)?.method).toBe("POST");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(visiblePlainHomeText(wrapper)).not.toContain("送达视频 ref");
  });

  it("prefills delivery route and visual refs with one advanced action without submitting claims", async () => {
    // 一键预填只拉取固定 latest/probe 证据，不能替 operator 提交 observed motion 或 delivery success。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fixture",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/camera/first-frame/probe": {
        schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
        proxy_status: "probe_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/camera/first-frame/probe",
        remote_http_status: 200,
        status: "frame_read",
        probe_key_values: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe",
          device: "/dev/video1",
          requested_fourcc: "MJPG",
          open_ok: "true",
          read_ok: "true",
          first_frame_timeout: "false",
          failure_reason: "",
          visible_content_proven: "true",
          visible_content_candidate: "true",
          sample_path: "/root/rober/onboard/runtime/camera/first_frame_probe_prefill.jpg",
          sample_write_ok: "true",
          elapsed_ms: "120",
          mean_luma: "42.0",
          max_luma: "220",
          dynamic_range_luma: "180",
          non_black_ratio: "0.8",
          backend_smoke_status: "not_requested",
          backend_frame_observed: "false",
          backend_attempts: "0",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          operator_report_status: "not_loaded",
        },
        failure_reason: "",
        blocked_reasons: ["operator_report_latest_http_200"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const prefillButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "预填送达材料（高级）");
    expect(prefillButton).toBeTruthy();
    await prefillButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect((wrapper.find('input[name="deliveryOperatorRouteMapRef"]').element as HTMLInputElement).value).toBe("o11-nav2-goal-execution-fixture");
    expect((wrapper.find('input[name="deliveryEvidenceRef"]').element as HTMLInputElement).value).toBe("delivery-confirmation-o11-nav2-goal-execution-fixture");
    expect((wrapper.find('input[name="deliveryOperatorEvidenceRef"]').element as HTMLInputElement).value).toBe("operator-o11-nav2-goal-execution-fixture");
    expect((wrapper.find('input[name="deliveryOperatorVideoRef"]').element as HTMLInputElement).value).toBe(
      "/root/rober/onboard/runtime/camera/first_frame_probe_prefill.jpg",
    );
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execution/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/camera/first-frame/probe?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
  });

  it("submits delivery draft material without motion or delivery confirmation while preserving existing safety material", async () => {
    // 草稿只保存 refs；允许保留已有 basic safety，但不能升级成 observed motion/stop 或 delivery_success。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=pc-first-jog-wheel-lr-fixture";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=scan-delta-fixture";
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: { delivery_success: false },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          operator_report_status: "unsafe_or_incomplete",
        },
        failure_reason: "",
        blocked_reasons: ["operator_report_ready_for_review", "operator_observed_motion", "structured_hil_claims.delivery_success"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1",
        proxy_status: "completion_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: true,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/complete",
        remote_endpoint: "/api/delivery/complete",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        delivery_key_values: { status: "delivery_complete", delivery_success: "true" },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await wrapper.find('input[name="deliveryOperatorEvidenceRef"]').setValue("delivery-draft-fixture");
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/first_frame_probe_prefill.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-fixture");

    const draftButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "提交送达草稿（高级）");
    expect(draftButton).toBeTruthy();
    await draftButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody.evidence_ref).toBe("delivery-draft-fixture");
    expect(reportBody.operator_present).toBe(true);
    expect(reportBody.physical_clearance_confirmed).toBe(true);
    expect(reportBody.emergency_stop_ready).toBe(true);
    expect(reportBody.observed_motion).toBe(false);
    expect(reportBody.observed_stop).toBe(false);
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_prefill.jpg",
      visible_content_proven: true,
      camera_artifacts_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_prefill.jpg",
      wheel_feedback_lr_nonzero_proven: true,
      wheel_feedback_ref: "pc-first-jog-wheel-lr-fixture",
      physical_motion_lidar_delta_proven: true,
      scan_delta_ref: "scan-delta-fixture",
      real_route_map_proven: true,
      route_map_ref: "o11-nav2-goal-execution-fixture",
      delivery_success: false,
      site_state: "delivery_material_draft_not_operator_confirmed",
    }));
    expect(reportBody.delivery_success).toBeUndefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
  });

  it("keeps final delivery confirmation disabled until every operator checklist item is checked", async () => {
    // 最终送达确认不能再靠一个总开关；缺任一现场确认项都不能写 delivery_success。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/operator/report": {
        proxy_status: "should_not_be_called",
      },
      "/api/robot-control/delivery/complete": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-fixture");
    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(true);
    await wrapper.vm.$nextTick();

    const confirmButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "提交送达材料并确认（高级）");
    expect(confirmButton).toBeTruthy();
    expect(confirmButton?.attributes("disabled")).toBeDefined();
    await confirmButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
  });

  it("submits final delivery operator material only after the explicit checklist is complete", async () => {
    // 全项确认后才提交 operator report，并把 delivery complete 交给后端 gate 合成最终结论。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_execution";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=pc-first-jog-wheel-lr-final";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=scan-delta-final";
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fixture",
          generated_at_ms: "1782150147000",
          response_generated_at_ms: "1782150147954",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: { delivery_success: true },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1",
        proxy_status: "completion_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: true,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/complete",
        remote_endpoint: "/api/delivery/complete",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        delivery_key_values: { status: "delivery_complete", delivery_success: "true" },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: true,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: { status: "delivery_complete", delivery_success: "true" },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    await wrapper.find('input[name="deliveryOperatorEvidenceRef"]').setValue("delivery-operator-fixture");
    await wrapper.find('input[name="deliveryEvidenceRef"]').setValue("delivery-confirmation-fixture");
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-fixture");
    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').setValue(true);
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await wrapper.vm.$nextTick();

    const confirmButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "提交送达材料并确认（高级）");
    expect(confirmButton).toBeTruthy();
    expect(confirmButton?.attributes("disabled")).toBeUndefined();
    const confirmForm = wrapper.findAll("form").find((form) => form.text().includes("送达最终确认"));
    expect(confirmForm).toBeTruthy();
    await confirmForm?.trigger("submit");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody).toEqual(expect.objectContaining({
      operator_present: true,
      evidence_ref: "delivery-operator-fixture",
      physical_clearance_confirmed: true,
      emergency_stop_ready: true,
      observed_motion: true,
      observed_stop: true,
    }));
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg",
      visible_content_proven: true,
      camera_artifacts_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg",
      wheel_feedback_lr_nonzero_proven: true,
      wheel_feedback_ref: "pc-first-jog-wheel-lr-final",
      physical_motion_lidar_delta_proven: true,
      scan_delta_ref: "scan-delta-final",
      real_route_map_proven: true,
      route_map_ref: "o11-nav2-goal-execution-fixture",
      delivery_success: true,
      site_state: "operator_confirmed_delivery_complete",
    }));
    const completeCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"));
    expect(completeCall).toBeTruthy();
    const completeBody = JSON.parse(String((completeCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(completeBody).toEqual(expect.objectContaining({
      confirm_delivery_completion: true,
      delivery_evidence_ref: "delivery-confirmation-fixture",
    }));
    expect(wrapper.find('[data-testid="plain-delivery-submit-result"]').text()).toContain("送达提交已通过：上位机已确认送达完成。");
    expect(focusSpy).toHaveBeenCalled();
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="keyboard-control-arm"]').element);
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').text()).toBe("启用键盘（按键才动）");
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toContain("未启用");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("focuses keyboard recheck after delivery success when keyboard gate is still blocked", async () => {
    // 送达完成后若键盘条件还没齐，只把焦点带到复查按钮；不能自动启用键盘或发送手控。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        proxy_status: "latest_loaded",
        status: "loaded_fail_closed_summary",
        delivery_success: false,
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-keyboard-blocked",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": {
        proxy_status: "report_forwarded",
        status: "loaded_fail_closed_summary",
        delivery_success: false,
        structured_hil_claims: { delivery_success: true },
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": {
        proxy_status: "completion_forwarded",
        status: "loaded_fail_closed_summary",
        delivery_success: true,
        delivery_key_values: { status: "delivery_complete", delivery_success: "true" },
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        proxy_status: "latest_loaded",
        status: "loaded_fail_closed_summary",
        delivery_success: true,
        delivery_key_values: { status: "delivery_complete", delivery_success: "true" },
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    await wrapper.find('input[name="deliveryOperatorEvidenceRef"]').setValue("delivery-operator-keyboard-blocked");
    await wrapper.find('input[name="deliveryEvidenceRef"]').setValue("delivery-confirmation-keyboard-blocked");
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/keyboard_blocked.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-keyboard-blocked");
    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').setValue(true);
    await wrapper.vm.$nextTick();

    const confirmForm = wrapper.findAll("form").find((form) => form.text().includes("送达最终确认"));
    expect(confirmForm).toBeTruthy();
    await confirmForm?.trigger("submit");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="plain-delivery-submit-result"]').text()).toContain("送达提交已通过：上位机已确认送达完成。");
    expect(focusSpy).toHaveBeenCalled();
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="keyboard-control-recheck"]').element);
    expect(wrapper.find('[data-testid="keyboard-control-arm"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).not.toContain("手控中");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("treats stale delivery success as history instead of current completion", async () => {
    // 旧 delivery_success 只能提示历史记录，不能让本轮进度或最终确认直接变成完成。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fresh-delivery-stale-fixture",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: true,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "delivery_complete",
          delivery_success: "true",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          generated_at_ms: "1782099547218",
          response_generated_at_ms: "1782150147954",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const deliveryStatus = wrapper.find('[data-testid="plain-delivery-status"]');
    expect(deliveryStatus.text()).toContain("需复验");
    expect(deliveryStatus.text()).toContain("读到旧送达成功记录；本轮仍需重新确认送达。");
    expect(wrapper.find('[data-testid="plain-delivery-final-confirm"]').text()).toContain("旧送达成功记录不能用于本轮，仍需重新确认送达。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("送达确认待完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("送达有旧成功记录");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toContain("验收卡点：送达成功记录较旧，需要本轮重新确认送达。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("blocks delivery success when latest route material belongs to an older Nav2 run", async () => {
    // delivery/latest 可能刚刷新但携带旧 route/map ref；本轮收口必须要求它匹配当前 Nav2 evidence。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fresh-fixture",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "proven",
        safe_to_control: false,
        delivery_success: true,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "delivery_success_confirmed",
        delivery_key_values: {
          status: "delivery_complete",
          delivery_success: "true",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
        },
        delivery_material_refs: {
          operator_evidence_ref: "delivery-old-operator-fixture",
          external_video_ref: "/root/rober/onboard/runtime/camera/old_delivery_frame.jpg",
          camera_artifacts_ref: "/root/rober/onboard/runtime/camera/old_delivery_frame.jpg",
          route_map_ref: "o11-nav2-goal-execution-old-fixture",
          site_state: "operator_confirmed_delivery_complete",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
      "/api/robot-control/nav2/goal/execute": { proxy_status: "should_not_be_called" },
      "/api/robot-control/base/manual": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="plain-delivery-status"]').text()).toContain("读到送达成功记录，但行程材料不是本轮记录");
    expect(wrapper.find('[data-testid="plain-delivery-final-confirm"]').text()).toContain("送达成功记录的行程材料不是本轮记录");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("送达确认待完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("送达成功材料非本轮");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toContain("验收卡点：送达成功记录的行程材料不是本轮记录");
    const deliveryClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("delivery success"));
    expect(deliveryClosureItem?.attributes("data-ready")).toBe("false");
    expect(deliveryClosureItem?.text()).toContain("行程材料不是本轮记录");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();

    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("shows a plain delivery submit failure summary when the completion gate blocks", async () => {
    // 红色确认提交失败后，普通首屏必须直接显示 gate 缺口，不能只回到“可提交”。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fixture",
          generated_at_ms: "1782150147000",
          response_generated_at_ms: "1782150147954",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: { delivery_success: true },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1",
        proxy_status: "completion_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/complete",
        remote_endpoint: "/api/delivery/complete",
        remote_http_status: 200,
        status: "blocked_missing_delivery_material",
        request_body: {},
        delivery_key_values: { status: "blocked_missing_delivery_material", delivery_success: "false" },
        failure_reason: "",
        blocked_reasons: ["operator_observed_stop", "structured_hil_claims.delivery_success"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "blocked_missing_delivery_material",
        delivery_key_values: { status: "blocked_missing_delivery_material", delivery_success: "false" },
        failure_reason: "",
        blocked_reasons: ["operator_observed_stop", "structured_hil_claims.delivery_success"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="deliveryOperatorVideoRef"]').setValue("/root/rober/onboard/runtime/camera/first_frame_probe_final.jpg");
    await wrapper.find('input[name="deliveryOperatorRouteMapRef"]').setValue("o11-nav2-goal-execution-fixture");
    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').setValue(true);
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-submit-result"]').text()).toContain("送达提交未通过：还差：已观察到停止、确认已投放/送达。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（不发车）");
  });

  it("recomputes delivery gap through the fixed check endpoint without confirming completion", async () => {
    // 复算缺口只调用 delivery/check；它固定 confirm=false，不能走 delivery/complete 确认路径。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/delivery/check": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_gap_check_proxy.v1",
        proxy_status: "check_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/check",
        remote_endpoint: "/api/delivery/complete",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {
          confirm_delivery_completion: false,
          delivery_evidence_ref: "delivery-gap-check-not-confirmed",
        },
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          operator_report_status: "unsafe_or_incomplete",
        },
        failure_reason: "",
        blocked_reasons: [
          "confirm_delivery_completion",
          "operator_report_ready_for_review",
          "operator_observed_motion",
          "operator_observed_stop",
          "structured_hil_claims.delivery_success",
        ],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          operator_report_status: "unsafe_or_incomplete",
        },
        failure_reason: "",
        blocked_reasons: [
          "confirm_delivery_completion",
          "operator_report_ready_for_review",
          "operator_observed_motion",
          "operator_observed_stop",
          "structured_hil_claims.delivery_success",
        ],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");

    const checkButton = wrapper.findAll(".advanced-details button").find((button) => button.text() === "复算送达缺口（高级）");
    expect(checkButton).toBeTruthy();
    await checkButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const checkCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/delivery/check?"));
    expect(checkCall).toBeTruthy();
    expect((checkCall?.[1] as RequestInit | undefined)?.method).toBe("POST");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    const diagnosticsText = wrapper.find(".robot-console .advanced-details").text();
    expect(diagnosticsText).toContain("delivery check status");
    expect(diagnosticsText).toContain("check_loaded");
    expect(diagnosticsText).toContain("operator_report_ready_for_review");
    const closureCheckText = wrapper.find('[data-testid="delivery-closure-check"]').text();
    expect(closureCheckText).toContain("送达收口检查");
    expect(closureCheckText).toContain("当前 gate 缺项");
    expect(closureCheckText).toContain("已满足：Nav2 路线执行成功");
    expect(closureCheckText).toContain("未满足：现场报告 ready_for_review");
    expect(closureCheckText).toContain("未满足：现场观察到运动/到达");
    expect(closureCheckText).toContain("未满足：现场观察到停止");
    expect(closureCheckText).toContain("未满足：确认已投放/送达");
  });

  it("enables non-stop motion only after complete operator material and still uses the fixed workstation proxy", async () => {
    // 材料齐全时，前端只放开固定 proxy 点动；普通用户首屏仍不出现工程词。
    vi.useFakeTimers();
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_execution";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=phone-video-0605.mp4";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=runtime/camera/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=runtime/wave_rover_feedback_debug.jsonl";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "manual",
        proxy_status: "command_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/manual",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        requested_direction: "forward",
        applied_direction: "forward",
        requested_speed_mps: 0.08,
        clamped_speed_mps: 0.08,
        requested_duration_ms: 500,
        clamped_duration_ms: 500,
        confirm_hil_checklist: true,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "manual_allowed",
        checklist_missing: [],
        operator_report_preflight: {
          status: "loaded",
          source_endpoint: "/api/operator/report",
          request_status: "loaded",
          http_status: 200,
          report_status: "ready_for_execution",
          evidence_ref: "field-hil-20260611-0605-op",
          required_fields: [],
          missing_fields: [],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "captured",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: [],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "manual command evidence captured in fixture",
        motion_evidence_gaps: [],
        failure_reason: "",
        blocked_reasons: [],
      },
      "/api/robot-control/base/stop": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "stop",
        proxy_status: "command_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/stop",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        requested_direction: "stop",
        applied_direction: "stop",
        requested_speed_mps: 0,
        clamped_speed_mps: 0,
        requested_duration_ms: 0,
        clamped_duration_ms: 0,
        confirm_hil_checklist: false,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "stop_allowed_without_checklist",
        checklist_missing: [],
        operator_report_preflight: {
          status: "not_required_for_stop",
          source_endpoint: "/api/operator/report",
          request_status: "not_required",
          http_status: null,
          report_status: "not_required_for_stop",
          evidence_ref: "not_required_for_stop",
          required_fields: [],
          missing_fields: [],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "blocked",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: [],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "keyboard release stop fixture",
        motion_evidence_gaps: ["stop_command_not_motion_proof"],
        failure_reason: "",
        blocked_reasons: [],
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    const forwardButton = wrapper.findAll(".motion-pad button").find((button) => button.text() === "前进");
    expect(forwardButton?.attributes("disabled")).toBeUndefined();
    expect(wrapper.find(".robot-console .advanced-details").text().replace(/\s+/g, "")).toContain("materialmissingfieldsnone");

    await forwardButton?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const manualCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/base/manual?"));
    expect(manualCall).toBeTruthy();
    const [manualUrl, manualOptions] = manualCall ?? ["", {} as RequestInit];
    const parsed = new URL(String(manualUrl), "http://workstation.local");
    const manualBody = JSON.parse(String((manualOptions as RequestInit).body ?? "{}")) as Record<string, unknown>;
    expect(parsed.searchParams.get("baseUrl")).toBe("http://192.168.1.11:8787");
    expect((manualOptions as RequestInit).method).toBe("POST");
    expect(manualBody).toEqual(expect.objectContaining({
      direction: "forward",
      confirm_hil_checklist: true,
    }));
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("NavigateToPose"))).toBe(false);

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("待命");
    expect(firstScreenText).toContain("已完成移动前检查；需要时可直接停止。");
    for (const token of DEFAULT_FIRST_SCREEN_FORBIDDEN_TOKENS) {
      expect(firstScreenText).not.toContain(token);
    }
    expect(firstScreenText).not.toContain("HIL");
    expect(firstScreenText).not.toContain("proof");
    expect(firstScreenText).not.toContain("cmd_vel");
    expect(firstScreenText).not.toContain("base_manual");
    expect(firstScreenText).not.toContain("task_id");

    const manualCallsBeforeKeyboard = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?")).length;
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?")).length).toBe(manualCallsBeforeKeyboard);

    const armButton = wrapper.find('[data-testid="keyboard-control-arm"]');
    expect(armButton.attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="keyboard-control-recheck"]').text()).toBe("复查手控条件");
    expect(armButton.text()).toBe("启用键盘（按键才动）");
    expect(visiblePlainHomeText(wrapper)).toContain("可手控");
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("未启用，先点启用键盘。");
    expect(wrapper.find('[data-testid="keyboard-control-panel"]').text()).not.toContain("还差：");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text().replace(/\s+/g, "")).toContain("键盘手控待验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控待验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("键盘待验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toContain("验收卡点：还没读到行程成功结果。");
    const keyboardClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItem?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItem?.text()).toContain("键盘入口已就绪，仍需按住方向键连续验证，最佳连续 0/2 次");
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    const manualCallsBeforeKeyboardRecheck = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?")).length;
    await wrapper.find('[data-testid="keyboard-control-recheck"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(focusSpy).toHaveBeenCalled();
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="keyboard-control-arm"]').element);
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?")).length).toBe(manualCallsBeforeKeyboardRecheck);
    await armButton.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).toContain("已启用");
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("等待按键，按住才会动。");
    const keyboardPanel = wrapper.find('[data-testid="keyboard-control-panel"]');
    await keyboardPanel.trigger("keydown", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).toContain("手控中");
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("正在前进，松开即停；本次按住 1/2 次。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控待验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("键盘待验证");
    const keyboardClosureItemAfterFirstPulse = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItemAfterFirstPulse?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItemAfterFirstPulse?.text()).toContain("本次按住 1/2 次");
    await keyboardPanel.trigger("keyup", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="keyboard-current-direction"]').text()).toBe("当前方向：未按键");
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("已停止，按住方向键可继续点动。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控待验证");
    const keyboardClosureItemAfterSplitPulse = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItemAfterSplitPulse?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItemAfterSplitPulse?.text()).toContain("最佳连续 1/2 次");

    await keyboardPanel.trigger("keydown", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("正在前进，松开即停；本次按住 1/2 次。");
    const keyboardClosureItemAfterSecondSessionFirstPulse = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItemAfterSecondSessionFirstPulse?.attributes("data-ready")).toBe("false");

    await vi.advanceTimersByTimeAsync(260);
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控已验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("键盘已验证");
    const keyboardClosureItemAfterKey = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItemAfterKey?.attributes("data-ready")).toBe("true");
    expect(keyboardClosureItemAfterKey?.text()).toContain("已连续转发键盘方向输入，已连续 2/2 次");
    expect(wrapper.find('[data-testid="keyboard-current-direction"]').text()).toBe("当前方向：前进");
    const manualCallsAfterKeyboard = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?")).length;
    expect(manualCallsAfterKeyboard).toBeGreaterThan(manualCallsBeforeKeyboard);
    const keyboardManualCalls = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?"));
    const keyboardManualCall = keyboardManualCalls[keyboardManualCalls.length - 1];
    const keyboardBody = JSON.parse(String((keyboardManualCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, unknown>;
    expect(keyboardBody).toEqual(expect.objectContaining({
      direction: "forward",
      duration_ms: 240,
      confirm_hil_checklist: true,
    }));
    await keyboardPanel.trigger("keyup", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="keyboard-current-direction"]').text()).toBe("当前方向：未按键");
    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("已停止，按住方向键可继续点动。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控已验证");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/stop?"))).toBe(true);
    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("keyboard continuous control");
    expect(wrapper.find(".robot-console .advanced-details").text()).toContain("pulse_ms=240");
  });

  it("does not verify keyboard control when the manual pulse is rejected", async () => {
    // 键盘验收必须来自固定 manual proxy 成功转发；单纯按键或失败响应不能算已验证。
    const summaryFixture = cloneFixture(fixtures["/api/robot-control/summary"]) as Record<string, any>;
    summaryFixture.operator_hil_material_summary.report_status = "ready_for_execution";
    summaryFixture.operator_hil_material_summary.external_video = "true; ref=phone-video-0605.mp4";
    summaryFixture.operator_hil_material_summary.camera_visible = "true; ref=runtime/camera/latest_metrics.json";
    summaryFixture.operator_hil_material_summary.wheel_feedback = "true; ref=runtime/wave_rover_feedback_debug.jsonl";
    summaryFixture.operator_hil_material_summary.lidar_delta = "true; ref=runtime/scan_delta/latest_metrics.json";
    summaryFixture.safe_command_boundary.keyboard_control_mode = "bounded_repeating_manual_pulse";
    summaryFixture.safe_command_boundary.keyboard_reuses_manual_gate = true;
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/summary": summaryFixture,
      "/api/robot-control/base/manual": {
        schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
        command_kind: "manual",
        proxy_status: "command_rejected",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        robot_control_executed: false,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/base/manual",
        remote_http_status: 400,
        status: "blocked",
        requested_direction: "forward",
        applied_direction: "forward",
        requested_speed_mps: 0.08,
        clamped_speed_mps: 0.08,
        requested_duration_ms: 240,
        clamped_duration_ms: 240,
        confirm_hil_checklist: true,
        non_stop_requires_confirm_hil_checklist: true,
        hil_checklist_gate_status: "manual_blocked_by_remote",
        checklist_missing: [],
        operator_report_preflight: {
          status: "loaded",
          source_endpoint: "/api/operator/report",
          request_status: "loaded",
          http_status: 200,
          report_status: "ready_for_execution",
          evidence_ref: "field-hil-keyboard-rejected",
          required_fields: [],
          missing_fields: [],
          material_summary: summaryFixture.operator_hil_material_summary,
          failure_reason: "",
          hard_dangerous_true_fields: [],
        },
        request_contract: {
          max_speed_mps: 0.12,
          max_duration_ms: 800,
          allowed_directions: ["forward", "back", "left", "right", "stop"],
        },
        evidence_capture_status: "blocked",
        evidence_capture_endpoints: [],
        evidence_capture_blocked_reasons: ["remote_manual_rejected"],
        before_readback: {},
        after_readback: {},
        motion_evidence_summary: "keyboard manual pulse rejected fixture",
        motion_evidence_gaps: ["motion_command_not_forwarded"],
        failure_reason: "remote_manual_rejected",
        blocked_reasons: ["remote_manual_rejected"],
      },
      "/api/robot-control/base/stop": {
        proxy_status: "should_not_be_called",
      },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    const checklistInputs = wrapper.findAll(".checklist-box input[type='checkbox']");
    for (const checkbox of checklistInputs) {
      await checkbox.setValue(true);
    }
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('[data-testid="keyboard-control-arm"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const keyboardPanel = wrapper.find('[data-testid="keyboard-control-panel"]');
    await keyboardPanel.trigger("keydown", { key: "w" });
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="keyboard-live-status"]').text()).toBe("键盘手控请求未成功，未记为已验证。");
    expect(wrapper.find('[data-testid="keyboard-current-direction"]').text()).toBe("当前方向：未按键");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("键盘手控待验证");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("键盘待验证");
    const keyboardClosureItem = wrapper.findAll('[data-testid="goal-closure-checklist"] li')
      .find((item) => item.text().includes("PC 键盘连续手控"));
    expect(keyboardClosureItem?.attributes("data-ready")).toBe("false");
    expect(keyboardClosureItem?.text()).toContain("键盘入口已就绪，仍需按住方向键连续验证，最佳连续 0/2 次");
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toHaveLength(1);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/stop?"))).toBe(false);
  });

  it("refreshes radar and map proof through fixed POST proxies and auto refreshes the summary", async () => {
    // 刷新与 lifecycle 按钮都只打 workstation 固定代理，动作结束后还要自动回刷 summary。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = visiblePlainHomeText(wrapper);
    expect(firstScreenText).toContain("刷新雷达");
    expect(firstScreenText).toContain("刷新地图");
    expect(firstScreenText).toContain("地图列表");
    expect(firstScreenText).toContain("重新建图");
    expect(firstScreenText).toContain("保存地图");
    expect(firstScreenText).toContain("停止");
    expect(firstScreenText).not.toContain("启动雷达");
    expect(firstScreenText).not.toContain("停止雷达");
    expect(firstScreenText).toContain("雷达已运行");
    expect(firstScreenText).toContain("未刷新");
    expect(firstScreenText).toContain("未读取");
    for (const token of DEFAULT_FIRST_SCREEN_FORBIDDEN_TOKENS) {
      expect(firstScreenText).not.toContain(token);
    }
    expect(firstScreenText).not.toContain("raw");
    expect(firstScreenText).not.toContain("scan_once_observed");
    expect(firstScreenText).not.toContain("map_once_observed");
    expect(firstScreenText).not.toContain("path_generation_succeeded");
    expect(firstScreenText).toContain("移动前检查");
    expect(firstScreenText).toContain("重新定位");
    expect(firstScreenText).not.toContain("定位重置");
    expect(firstScreenText).not.toContain("AMCL");
    expect(firstScreenText).not.toContain("Start");
    expect(firstScreenText).not.toContain("Reset");

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await flushPromises();

    const summaryCallsBefore = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;

    await wrapper.findAll("button").find((button) => button.text() === "刷新雷达")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(visiblePlainHomeText(wrapper)).toContain("雷达已运行");
    expect(visiblePlainHomeText(wrapper)).not.toContain("scan 可见");
    expect(visiblePlainHomeText(wrapper)).not.toContain("tf 可见");
    expect(wrapper.find("details").text()).toContain("scan_once_observed");
    expect(wrapper.find("details").text()).toContain("scan_hz_observed");
    expect(wrapper.find("details").text()).toContain("tf_observed");
    expect(wrapper.find("details").text()).toContain("continuous_scan_status");
    expect(wrapper.find("details").text()).toContain("lifecycle_running");
    expect(wrapper.find("details").text()).toContain("continuous_window_observed");
    expect(wrapper.find("details").text()).toContain("non-motion evidence actions");
    expect(wrapper.find("details").text()).toContain("sends_commands");
    expect(wrapper.find("details").text()).toContain("starts_ros2");
    expect(wrapper.find("details").text()).toContain("last refreshed time");
    expect(wrapper.find("details").text()).toContain("latest readback key values");
    expect(wrapper.find("details").text()).toContain("blocked reasons");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/radar/scan-proof/refresh") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterRadar = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterRadar).toBeGreaterThan(summaryCallsBefore);

    expect(wrapper.find("details").text()).toContain("启动雷达（高级）");
    expect(wrapper.find("details").text()).toContain("停止雷达（高级）");
    await wrapper.find("details").element.setAttribute("open", "");
    await wrapper.vm.$nextTick();
    await wrapper.findAll("button").find((button) => button.text() === "启动雷达（高级）")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).not.toContain("启动雷达");
    expect(wrapper.find("details").text()).toContain("start:lifecycle_forwarded");
    expect(wrapper.find("details").text()).toContain("/api/radar/start");
    expect(wrapper.find("details").text()).toContain("dry_run_stub");
    expect(wrapper.find("details").text()).toContain("executed=false");
    expect(wrapper.find("details").text()).toContain("command_not_configured");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/radar/start") && options?.method === "POST")).toBe(true);

    await wrapper.findAll("button").find((button) => button.text() === "停止雷达（高级）")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(wrapper.find("details").text()).toContain("stop:lifecycle_forwarded");
    expect(wrapper.find("details").text()).toContain("/api/radar/stop");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/radar/stop") && options?.method === "POST")).toBe(true);

    await wrapper.findAll("button").find((button) => button.text() === "刷新地图")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(visiblePlainHomeText(wrapper)).toContain("已刷新");
    expect(visiblePlainHomeText(wrapper)).not.toContain("map 可见");
    expect(visiblePlainHomeText(wrapper)).not.toContain("evidence 可见");
    expect(wrapper.find("details").text()).toContain("map_once_observed");
    expect(wrapper.find("details").text()).toContain("map_file_observed");
    expect(wrapper.find("details").text()).toContain("map_metadata_observed");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/proof/refresh") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterMap = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterMap).toBeGreaterThan(summaryCallsAfterRadar);

    await wrapper.findAll("button").find((button) => button.text() === "检查路径（高级）")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(visiblePlainHomeText(wrapper)).not.toContain("路径可生成");
    expect(visiblePlainHomeText(wrapper)).not.toContain("检查已返回；不会发车。");
    expect(visiblePlainHomeText(wrapper)).not.toContain("检查路径");
    expect(visiblePlainHomeText(wrapper)).not.toContain("path_generation_succeeded");
    expect(wrapper.find("details").text()).toContain("/api/nav2/proof/refresh");
    expect(wrapper.find("details").text()).toContain("nav2_no_motion_path_generation_runtime_observed");
    expect(wrapper.find("details").text()).toContain("post_timeout_latest_readback_loaded");
    expect(wrapper.find("details").text()).toContain("path_generation_succeeded");
    expect(wrapper.find("details").text()).toContain("path_point_count");
    expect(wrapper.find("details").text()).toContain("no Nav2 start/stop; no NavigateToPose; no /cmd_vel; no /api/base/manual");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/nav2/proof/refresh") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterNav2 = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterNav2).toBeGreaterThan(summaryCallsAfterMap);

    await wrapper.find("details").element.setAttribute("open", "");
    await wrapper.vm.$nextTick();
    await wrapper.find("input[name='navGoalX']").setValue("99");
    await wrapper.find("input[name='confirmNavigationPreflight']").setValue(true);
    const navGoalPreflightForm = wrapper.findAll("form").find((form) => form.text().includes("导航目标预检"));
    expect(navGoalPreflightForm).toBeTruthy();
    await navGoalPreflightForm?.trigger("submit");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).not.toContain("导航目标预检");
    expect(wrapper.find("details").text()).toContain("preflight_rejected");
    expect(wrapper.find("details").text()).toContain("operator_report_preflight_required");
    expect(wrapper.find("details").text()).toContain("/api/localize/proof/latest");
    expect(wrapper.find("details").text()).toContain("/api/nav2/proof/latest");
    expect(wrapper.find("details").text()).toContain("/api/operator/report");
    expect(wrapper.find("details").text()).toContain("robot_control_executed=false");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/nav2/goal/preflight") && options?.method === "POST")).toBe(true);
    const navGoalCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/preflight"));
    expect(JSON.parse(String(navGoalCall?.[1]?.body ?? "{}"))).toEqual({
      goal_frame_id: "map",
      goal_x: 99,
      goal_y: 0,
      goal_yaw: 0,
      confirm_navigation_preflight: true,
    });
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/nav2/start"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/base/manual"))).toBe(false);

    expect(wrapper.find("details").text()).toContain("定位重置（高级）");
    await wrapper.findAll("button").find((button) => button.text() === "重新定位")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).toContain("已定位");
    expect(visiblePlainHomeText(wrapper)).toContain("定位已返回；需要时可直接停止。");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("定位重置");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("initialpose");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("AMCL");
    expect(wrapper.find("details").text()).toContain("/api/localize/reset");
    expect(wrapper.find("details").text()).toContain("localization_reset_observed");
    expect(wrapper.find("details").text()).toContain("initialpose_published");
    expect(wrapper.find("details").text()).toContain("amcl_pose_observed");
    expect(wrapper.find("details").text()).toContain("managed_runtime_started");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/localize/reset") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterLocalize = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterLocalize).toBeGreaterThan(summaryCallsAfterNav2);

    await wrapper.findAll("button").find((button) => button.text() === "地图列表")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("当前地图不可导航，需要重新建图");
    expect(wrapper.find("details").text()).toContain("lifecycle action");
    expect(wrapper.find("details").text()).toContain("/api/map/list");
    expect(wrapper.find("details").text()).toContain("floor_1.yaml");
    expect(wrapper.find("details").text()).toContain("status=no_free_cells");
    expect(wrapper.find("details").text()).toContain("no_free=1");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/list") && !options)).toBe(true);

    await wrapper.find("details").element.setAttribute("open", "");
    await wrapper.vm.$nextTick();
    await wrapper.findAll("button").find((button) => button.text() === "保存地图")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("保存地图已返回");
    expect(wrapper.find("details").text()).toContain("command_result");
    expect(wrapper.find("details").text()).toContain("executed=false");
    expect(wrapper.find("details").text()).toContain("software_guard_command_not_configured");
    expect(wrapper.find("details").text()).toContain("开始建图（高级）");
    expect(wrapper.find("details").text()).toContain("Reset（受控/高级，禁用）");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/save") && options?.method === "POST")).toBe(true);

    await wrapper.findAll("button").find((button) => button.text() === "开始建图（高级）")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/start") && options?.method === "POST")).toBe(true);
  });

  it("refreshes plain delivery status without submitting delivery completion", async () => {
    // 普通首屏收口按钮只能读取/复算状态；不能提交 operator report 或 delivery complete。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          operator_report_status: "ready_for_review",
        },
        failure_reason: "",
        blocked_reasons: ["operator_observed_motion", "structured_hil_claims.delivery_success"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/check": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_gap_check_proxy.v1",
        proxy_status: "check_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/check",
        remote_endpoint: "/api/delivery/complete",
        remote_http_status: 400,
        status: "blocked",
        request_body: {
          confirm_delivery_completion: false,
          delivery_evidence_ref: "delivery-gap-check-not-confirmed",
        },
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
        },
        failure_reason: "delivery_material_incomplete",
        blocked_reasons: ["operator_observed_motion", "structured_hil_claims.delivery_success"],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-plain-fixture",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/camera/first-frame/probe": {
        schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
        proxy_status: "probe_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/camera/first-frame/probe",
        remote_http_status: 200,
        status: "frame_read",
        probe_key_values: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe",
          device: "/dev/video1",
          requested_fourcc: "MJPG",
          open_ok: "true",
          read_ok: "true",
          first_frame_timeout: "false",
          failure_reason: "",
          visible_content_proven: "true",
          visible_content_candidate: "true",
          sample_path: "/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg",
          sample_write_ok: "true",
          elapsed_ms: "120",
          mean_luma: "42.0",
          max_luma: "220",
          dynamic_range_luma: "180",
          non_black_ratio: "0.8",
          backend_smoke_status: "not_requested",
          backend_frame_observed: "false",
          backend_attempts: "0",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": {
        schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
        proxy_status: "report_forwarded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        remote_endpoint: "/api/operator/report",
        remote_method: "POST",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        request_body: {},
        structured_hil_claims: {
          external_video_recorded: true,
          external_video_ref: "/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg",
          real_route_map_proven: true,
          route_map_ref: "o11-nav2-goal-execution-plain-fixture",
          delivery_success: false,
          site_state: "delivery_material_draft_not_operator_confirmed",
        },
        rejected_fields: [],
        ignored_fields: [],
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const deliveryStatus = wrapper.find('[data-testid="plain-delivery-status"]');
    expect(deliveryStatus.exists()).toBe(true);
    expect(deliveryStatus.text()).toContain("任务收口");
    expect(deliveryStatus.text()).toContain("待确认");
    expect(deliveryStatus.text()).toContain("行程已完成");
    expect(wrapper.find('[data-testid="plain-delivery-gate-missing"]').text()).toContain("上位机还差：已观察到到达/移动、确认已投放/送达。");
    expect(wrapper.find('[data-testid="plain-delivery-next-action"]').text()).toContain("下一步：更新行程材料。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("还差：已观察到到达/移动、确认已投放/送达。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("下一步：更新行程材料。");
    expect(deliveryStatus.text()).toContain("最终确认");
    expect(deliveryStatus.text()).toContain("待材料");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 9 项：本轮行程材料、送达材料");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先更新行程材料）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-delivery-gap-check"]').text()).toBe("复查送达条件（还差 2 项，不确认）");
    expect(wrapper.find('[data-testid="plain-delivery-mark-safety"]').text()).toBe("下一步：勾选安全三项");
    expect(wrapper.find('[data-testid="plain-delivery-mark-arrived-stopped"]').text()).toBe("下一步：确认到达停稳");
    expect(wrapper.find('[data-testid="plain-delivery-mark-refs-verified"]').text()).toBe("下一步：核对材料");
    expect(wrapper.find('[data-testid="plain-delivery-mark-success"]').text()).toBe("下一步：确认投放/送达");
    expect(wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').text()).toBe("全部已确认");
    expect(visiblePlainHomeText(wrapper)).not.toContain("delivery_success");
    expect(visiblePlainHomeText(wrapper)).not.toContain("/api/delivery");

    const latestCallsBefore = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?")).length;
    await wrapper.find('[data-testid="plain-delivery-latest"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/delivery/latest?")).length).toBeGreaterThan(latestCallsBefore);

    await wrapper.find('[data-testid="plain-delivery-gap-check"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const checkCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/delivery/check?"));
    expect(checkCall).toBeTruthy();
    expect((checkCall?.[1] as RequestInit | undefined)?.method).toBe("POST");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);

    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    const focusCallsBeforePrefill = focusSpy.mock.calls.length;
    await wrapper.findAll(".simple-user-console button").find((button) => button.text() === "准备送达材料")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(deliveryStatus.text()).toContain("已预填");
    expect(deliveryStatus.text()).toContain("视频和行程材料已预填");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 7 项");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("确认已投放/送达");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先勾选安全）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/camera/first-frame/probe?"))).toBe(true);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(wrapper.find('[data-testid="plain-delivery-draft-save"]').text()).toBe("保存送达草稿（不确认）");
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforePrefill);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-delivery-draft-save"]').element);

    const checkCallsBeforeDraftSave = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/delivery/check?")).length;
    const focusCallsBeforeDraftSave = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-delivery-draft-save"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCall).toBeTruthy();
    const reportBody = JSON.parse(String((reportCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(reportBody.observed_motion).toBe(false);
    expect(reportBody.observed_stop).toBe(false);
    expect(reportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg",
      real_route_map_proven: true,
      route_map_ref: "o11-nav2-goal-execution-plain-fixture",
      delivery_success: false,
      site_state: "delivery_material_draft_not_operator_confirmed",
    }));
    expect(deliveryStatus.text()).toContain("已保存");
    expect(deliveryStatus.text()).toContain("请完成下方最终确认");
    expect(deliveryStatus.text()).toContain("送达材料已保存；现场逐项确认后再提交。");
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforeDraftSave);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-delivery-final-confirm"]').element);
    expect(mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/delivery/check?")).length).toBe(checkCallsBeforeDraftSave + 1);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);

    const callsBeforeAllConfirmedShortcut = mockedFetch.mock.calls.length;
    const focusCallsBeforeAllConfirmedShortcut = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect((wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmClearance"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmEstop"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').text()).toBe("全部确认已勾选");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（不发车）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeUndefined();
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeAllConfirmedShortcut);
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforeAllConfirmedShortcut);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').element);

    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(false);
    await wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').setValue(false);
    await wrapper.vm.$nextTick();

    const callsBeforeSafetyShortcut = mockedFetch.mock.calls.length;
    await wrapper.find('[data-testid="plain-delivery-mark-safety"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect((wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmClearance"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmEstop"]').element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 4 项");
    expect(wrapper.find('[data-testid="plain-delivery-mark-safety"]').text()).toBe("安全三项已勾选");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeSafetyShortcut);

    await wrapper.find('[data-testid="plain-delivery-mark-arrived-stopped"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect((wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 2 项");
    expect(wrapper.find('[data-testid="plain-delivery-mark-arrived-stopped"]').text()).toBe("已确认到达停稳");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeSafetyShortcut);

    await wrapper.find('[data-testid="plain-delivery-mark-refs-verified"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect((wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 1 项");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("确认已投放/送达");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先确认投放）");
    expect(wrapper.find('[data-testid="plain-delivery-mark-refs-verified"]').text()).toBe("材料已核对");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeSafetyShortcut);

    const focusCallsBeforeSuccessShortcut = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-delivery-mark-success"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect((wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("全部确认项已勾选，可以提交。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（不发车）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeUndefined();
    expect(wrapper.find('[data-testid="plain-delivery-mark-success"]').text()).toBe("已确认投放/送达");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeSafetyShortcut);
    expect(focusSpy.mock.calls.length).toBeGreaterThan(focusCallsBeforeSuccessShortcut);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').element);

    await wrapper.find('input[name="deliveryOperatorConfirmOperatorPresent"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmClearance"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmEstop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedMotion"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmObservedStop"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmRefsVerified"]').setValue(true);
    await wrapper.find('input[name="deliveryOperatorConfirmDeliverySuccess"]').setValue(true);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("全部确认项已勾选，可以提交。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（不发车）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeUndefined();

    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const reportCalls = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/operator/report?"));
    expect(reportCalls).toHaveLength(2);
    const finalReportBody = JSON.parse(String((reportCalls[1]?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, any>;
    expect(finalReportBody).toEqual(expect.objectContaining({
      operator_present: true,
      physical_clearance_confirmed: true,
      emergency_stop_ready: true,
      observed_motion: true,
      observed_stop: true,
    }));
    expect(finalReportBody.structured_hil_claims).toEqual(expect.objectContaining({
      external_video_recorded: true,
      external_video_ref: "/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg",
      visible_content_proven: true,
      camera_artifacts_ref: "/root/rober/onboard/runtime/camera/plain_delivery_frame.jpg",
      route_map_ref: "o11-nav2-goal-execution-plain-fixture",
      delivery_success: true,
      site_state: "operator_confirmed_delivery_complete",
    }));
    const completeCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"));
    expect(completeCall).toBeTruthy();
    const completeBody = JSON.parse(String((completeCall?.[1] as RequestInit | undefined)?.body ?? "{}")) as Record<string, unknown>;
    expect(completeBody).toEqual(expect.objectContaining({ confirm_delivery_completion: true }));
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/nav2/goal/execute?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
  });

  it("prefills plain delivery material refs from latest delivery readback without submitting", async () => {
    // 页面刷新后若上位机 latest 已有送达草稿材料，PC 只恢复 ref，不能替现场确认送达。
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          generated_at_ms: "1782103344406",
          response_generated_at_ms: "1782150442201",
          operator_report_status: "unsafe_or_incomplete",
        },
        delivery_material_refs: {
          operator_evidence_ref: "delivery-draft-smoke-1782102952",
          external_video_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg",
          camera_artifacts_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg",
          route_map_ref: "o11-nav2-goal-execution-1782099547218",
          site_state: "delivery_material_draft_not_operator_confirmed",
        },
        failure_reason: "",
        blocked_reasons: [
          "confirm_delivery_completion",
          "operator_report_ready_for_review",
          "operator_observed_motion",
          "operator_observed_stop",
          "structured_hil_claims.delivery_success",
        ],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const deliveryStatus = wrapper.find('[data-testid="plain-delivery-status"]');
    expect(deliveryStatus.text()).toContain("已保存");
    expect(deliveryStatus.text()).toContain("送达材料草稿已保存，约 13 小时前；这份草稿较旧，如本轮已重新到达，请重新准备材料或重新确认；请完成下方最终确认。");
    expect(deliveryStatus.text()).toContain("旧行程记录不能用于本轮送达，先重新执行本轮行程。");
    expect(wrapper.find('[data-testid="plain-goal-progress-primary-action"]').text()).toBe("去行程卡点");
    const callsBeforeFocus = mockedFetch.mock.calls.length;
    const focusCallsBeforeDeliveryClick = focusSpy.mock.calls.length;
    await wrapper.find('[data-testid="plain-goal-progress-primary-action"]').trigger("click");
    expect(focusSpy.mock.calls.length).toBe(focusCallsBeforeDeliveryClick + 1);
    expect(focusSpy.mock.contexts[focusSpy.mock.contexts.length - 1]).toBe(wrapper.find('[data-testid="plain-trip-run"]').element);
    expect(mockedFetch.mock.calls.length).toBe(callsBeforeFocus);
    expect(wrapper.find('[data-testid="plain-delivery-gate-missing"]').text()).toContain("上位机还差：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达。");
    expect(wrapper.find('[data-testid="plain-delivery-gap-check"]').text()).toBe("复查送达条件（还差 5 项，不确认）");
    expect(wrapper.find('[data-testid="plain-delivery-next-action"]').text()).toContain("下一步：重新执行本轮行程。");
    expect(wrapper.find('[data-testid="plain-trip-evidence-summary"]').text()).toContain("最近行程成功，反馈 8 次，约 13 小时前；这条记录较旧，如需本轮复验，请重新执行行程；送达仍需现场确认。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("最近行程记录较旧，需要重新执行本轮行程。");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-preflight"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-trip-execute"]').text()).toBe("先勾选确认");
    expect(wrapper.find('[data-testid="plain-trip-execute"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="plain-trip-latest"]').text()).toBe("读取行程结果（只读）");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("还差：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达。");
    expect(wrapper.find('[data-testid="plain-goal-progress"]').text()).toContain("下一步：重新执行本轮行程。");
    expect(wrapper.find('[data-testid="plain-goal-progress-state-summary"]').text()).toContain("行程执行待完成；送达确认待完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-evidence-summary"]').text()).toContain("最近行程成功，反馈 8 次，约 13 小时前；这条记录较旧，如需本轮复验，请重新执行行程；送达未完成");
    expect(wrapper.find('[data-testid="plain-goal-progress-blocker-summary"]').text()).toContain("验收卡点：行程成功记录较旧，需要重新执行本轮行程。");
    expect((wrapper.find('input[name="deliveryOperatorEvidenceRef"]').element as HTMLInputElement).value).toBe("delivery-draft-smoke-1782102952");
    expect((wrapper.find('input[name="deliveryOperatorVideoRef"]').element as HTMLInputElement).value).toBe("/root/rober/onboard/runtime/camera/first_frame_probe_1782102949377.jpg");
    expect((wrapper.find('input[name="deliveryOperatorRouteMapRef"]').element as HTMLInputElement).value).toBe("o11-nav2-goal-execution-1782099547218");
    expect((wrapper.find('input[name="deliveryEvidenceRef"]').element as HTMLInputElement).value).toBe("delivery-confirmation-o11-nav2-goal-execution-1782099547218");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("本轮行程");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先重新行程）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    await wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 1 项：本轮行程。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先重新行程）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(visiblePlainHomeText(wrapper)).not.toContain("o11-nav2-goal-execution-1782099547218");
    expect(visiblePlainHomeText(wrapper)).not.toContain("structured_hil_claims");
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/base/manual?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).includes("/cmd_vel"))).toBe(false);
  });

  it("blocks final delivery when a restored draft route ref does not match the fresh Nav2 result", async () => {
    // 旧草稿不能混用到新一轮行程；必须先更新 route/map ref，再允许现场最终确认。
    const mockedFetch = stubWorkstationFetch({
      "/api/robot-control/nav2/goal/execution/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        remote_endpoint: "/api/nav2/goal/execution/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        goal_execution_key_values: {
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fresh-fixture",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
          result_status: "succeeded",
          feedback_sample_count: "8",
          delivery_success: "false",
        },
        failure_reason: "",
        blocked_reasons: [],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/delivery/latest": {
        schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
        proxy_status: "latest_loaded",
        source: "software_proof",
        proof_status: "not_proven",
        safe_to_control: false,
        delivery_success: false,
        primary_actions_enabled: false,
        pc_only: true,
        source_base_url: "http://192.168.1.11:8787",
        normalized_base_url: "http://192.168.1.11:8787",
        workstation_endpoint: "/api/robot-control/delivery/latest",
        remote_endpoint: "/api/delivery/latest",
        remote_http_status: 200,
        status: "loaded_fail_closed_summary",
        delivery_key_values: {
          status: "blocked_missing_delivery_material",
          delivery_success: "false",
          nav2_status: "goal_succeeded",
          nav2_feedback_sample_count: "8",
          generated_at_ms: "1782150441201",
          response_generated_at_ms: "1782150442201",
          operator_report_status: "unsafe_or_incomplete",
        },
        delivery_material_refs: {
          operator_evidence_ref: "delivery-draft-old-fixture",
          external_video_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_old.jpg",
          camera_artifacts_ref: "/root/rober/onboard/runtime/camera/first_frame_probe_old.jpg",
          route_map_ref: "o11-nav2-goal-execution-old-fixture",
          site_state: "delivery_material_draft_not_operator_confirmed",
        },
        failure_reason: "",
        blocked_reasons: [
          "confirm_delivery_completion",
          "operator_report_ready_for_review",
          "operator_observed_motion",
          "operator_observed_stop",
          "structured_hil_claims.delivery_success",
        ],
        hard_dangerous_true_fields: [],
        robot_control_executed: false,
      },
      "/api/robot-control/operator/report": { proxy_status: "should_not_be_called" },
      "/api/robot-control/delivery/complete": { proxy_status: "should_not_be_called" },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect((wrapper.find('input[name="deliveryOperatorRouteMapRef"]').element as HTMLInputElement).value).toBe("o11-nav2-goal-execution-old-fixture");
    expect(wrapper.find('[data-testid="plain-delivery-next-action"]').text()).toContain("下一步：更新行程材料。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("本轮行程材料");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（先更新行程材料）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();

    await wrapper.find('[data-testid="plain-delivery-mark-all-confirmed"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("还差 1 项：本轮行程材料。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeDefined();
    await wrapper.find('[data-testid="plain-delivery-confirm-submit"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);

    await wrapper.find('[data-testid="plain-delivery-prefill-material"]').trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect((wrapper.find('input[name="deliveryOperatorRouteMapRef"]').element as HTMLInputElement).value).toBe("o11-nav2-goal-execution-fresh-fixture");
    expect((wrapper.find('input[name="deliveryEvidenceRef"]').element as HTMLInputElement).value).toBe("delivery-confirmation-o11-nav2-goal-execution-fresh-fixture");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-missing"]').text()).toContain("全部确认项已勾选，可以提交。");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').text()).toBe("确认送达（不发车）");
    expect(wrapper.find('[data-testid="plain-delivery-confirm-submit"]').attributes("disabled")).toBeUndefined();
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/operator/report?"))).toBe(false);
    expect(mockedFetch.mock.calls.some(([url]) => String(url).startsWith("/api/robot-control/delivery/complete?"))).toBe(false);
  });

  it("starts and stops Camera Preview through workstation camera proxy while keeping control locked", async () => {
    // WebRTC UI 测试只验证本机代理和前端状态机，不连接真实浏览器媒体栈或机器人。
    vi.useFakeTimers();
    const mockedFetch = stubWorkstationFetch();
    const visibleFrameData = new Uint8ClampedArray(32 * 24 * 4);
    for (let index = 0; index < visibleFrameData.length; index += 4) {
      visibleFrameData[index] = 220;
      visibleFrameData[index + 1] = 200;
      visibleFrameData[index + 2] = 180;
      visibleFrameData[index + 3] = 255;
    }
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation((contextId: string) => {
      if (contextId !== "2d") {
        return null;
      }
      return {
        drawImage: () => undefined,
        getImageData: () => ({ data: visibleFrameData }),
      } as unknown as CanvasRenderingContext2D;
    });
    class FakeMediaStream {
      tracks: Array<{ kind: string; readyState: string; stop: () => void }>;

      constructor(tracks: Array<{ kind: string; readyState: string; stop: () => void }>) {
        this.tracks = tracks;
      }

      getTracks() {
        return this.tracks;
      }
    }

    class FakePeerConnection {
      iceConnectionState = "new";
      iceGatheringState = "complete";
      localDescription: { type: "offer"; sdp: string } | null = null;
      remoteDescription: { type: "answer"; sdp: string } | null = null;
      oniceconnectionstatechange: (() => void) | null = null;
      ontrack: ((
        event: {
          track: { kind: string; readyState: string; stop: () => void; onended: (() => void) | null };
          streams: FakeMediaStream[];
        },
      ) => void) | null =
        null;

      addTransceiver() {
        return undefined;
      }

      async createOffer() {
        return { type: "offer" as const, sdp: "v=0\r\ns=local-offer\r\n" };
      }

      async setLocalDescription(description: { type: "offer"; sdp: string }) {
        this.localDescription = description;
      }

      async setRemoteDescription(description: { type: "answer"; sdp: string }) {
        // fake stream 模拟真实浏览器 RTCTrackEvent.streams[0]，覆盖 video.srcObject 绑定路径。
        const videoTrack = {
          kind: "video",
          readyState: "live",
          stop: () => undefined,
          onended: null,
        };
        this.remoteDescription = description;
        this.iceConnectionState = "connected";
        this.oniceconnectionstatechange?.();
        this.ontrack?.({
          track: videoTrack,
          streams: [new FakeMediaStream([videoTrack])],
        });
      }

      getReceivers() {
        return [];
      }

      close() {
        this.iceConnectionState = "closed";
        this.oniceconnectionstatechange?.();
      }
    }

    vi.stubGlobal("MediaStream", FakeMediaStream as unknown as typeof MediaStream);
    vi.stubGlobal("RTCPeerConnection", FakePeerConnection as unknown as typeof RTCPeerConnection);
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const robotBaseUrlInput = wrapper.find('input[name="robotApiBaseUrl"]');
    await robotBaseUrlInput.setValue("http://192.168.1.11:8787");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "打开画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();
    const previewVideoElement = wrapper.find('[data-testid="robot-camera-preview-video"]').element as HTMLVideoElement;
    Object.defineProperty(previewVideoElement, "videoWidth", { configurable: true, value: 640 });
    Object.defineProperty(previewVideoElement, "videoHeight", { configurable: true, value: 480 });
    Object.defineProperty(previewVideoElement, "readyState", { configurable: true, value: 4 });
    previewVideoElement.dispatchEvent(new Event("loadeddata"));
    previewVideoElement.dispatchEvent(new Event("playing"));
    await vi.advanceTimersByTimeAsync(1100);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("画面可见");
    expect(wrapper.find(".robot-console-grid").text()).toContain("画面可见。");
    expect(wrapper.find("details").text()).toContain("preview_status");
    expect(wrapper.find("details").text()).toContain("streaming");
    expect(wrapper.find("details").text()).toContain("peer-preview-001");
    expect(wrapper.find("details").text()).toContain("ice_connection_state");
    expect(wrapper.find("details").text()).toContain("connected");
    expect(wrapper.find("details").text()).toContain("video_track_state");
    expect(wrapper.find("details").text()).toContain("live");
    expect(wrapper.find("details").text()).toContain("video_element_src_object");
    expect(wrapper.find("details").text().replace(/\s+/g, "")).toContain("video_element_src_objecttrue");
    expect(wrapper.find("details").text()).toContain("sample_status");
    expect(wrapper.find("details").text()).toContain("visible_content_observed");
    expect(wrapper.find("details").text()).toContain("mean_luma");
    expect(wrapper.find("details").text()).toContain("non_black_ratio_ge16");
    expect(previewVideoElement.srcObject).not.toBeNull();
    expect(wrapper.find("details").text()).toContain("safe_to_control=false");
    expect(wrapper.find("details").text()).toContain("Node server only; Vue direct access=false");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/camera/offer") && options?.method === "POST")).toBe(true);
    writeCameraFrameQualityArtifact({
      schema: "trashbot.pc_workstation.camera_frame_quality_dom_smoke.v1",
      checked_at: new Date().toISOString(),
      plain_status: "画面可见",
      preview_status: "streaming",
      sample_status: "visible_content_observed",
      mean_luma: 202,
      max_luma: 202,
      non_black_ratio_ge16: 1,
      video_size: "640x480",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      robot_control_executed: false,
    });

    await wrapper.findAll("button").find((button) => button.text() === "关闭画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("未打开");
    expect(wrapper.find("details").text()).toContain("stopped_by_user");
    expect(wrapper.find("details").text()).toContain("peer_closed:closed");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).includes("/api/robot-control/camera/peers/peer-preview-001/close") && options?.method === "POST")).toBe(true);
  });

  it("marks near-black preview as 画面偏暗 instead of optimistic 已打开", async () => {
    // 只要本地像素采样接近纯黑，就必须给普通用户更真实的“画面偏暗”而不是“已打开”。
    vi.useFakeTimers();
    const mockedFetch = stubWorkstationFetch();
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(() => ({
      drawImage: () => undefined,
      getImageData: () => ({ data: new Uint8ClampedArray(32 * 24 * 4) }),
    }) as unknown as CanvasRenderingContext2D);
    class FakeMediaStream {
      tracks: Array<{ kind: string; readyState: string; stop: () => void }>;

      constructor(tracks: Array<{ kind: string; readyState: string; stop: () => void }>) {
        this.tracks = tracks;
      }

      getTracks() {
        return this.tracks;
      }
    }

    class FakePeerConnection {
      iceConnectionState = "new";
      iceGatheringState = "complete";
      localDescription: { type: "offer"; sdp: string } | null = null;
      remoteDescription: { type: "answer"; sdp: string } | null = null;
      oniceconnectionstatechange: (() => void) | null = null;
      ontrack: ((
        event: {
          track: { kind: string; readyState: string; stop: () => void; onended: (() => void) | null };
          streams: FakeMediaStream[];
        },
      ) => void) | null = null;

      addTransceiver() {
        return undefined;
      }

      async createOffer() {
        return { type: "offer" as const, sdp: "v=0\r\ns=local-offer\r\n" };
      }

      async setLocalDescription(description: { type: "offer"; sdp: string }) {
        this.localDescription = description;
      }

      async setRemoteDescription(description: { type: "answer"; sdp: string }) {
        const videoTrack = {
          kind: "video",
          readyState: "live",
          stop: () => undefined,
          onended: null,
        };
        this.remoteDescription = description;
        this.iceConnectionState = "connected";
        this.oniceconnectionstatechange?.();
        this.ontrack?.({
          track: videoTrack,
          streams: [new FakeMediaStream([videoTrack])],
        });
      }

      getReceivers() {
        return [];
      }

      close() {
        this.iceConnectionState = "closed";
        this.oniceconnectionstatechange?.();
      }
    }

    vi.stubGlobal("MediaStream", FakeMediaStream as unknown as typeof MediaStream);
    vi.stubGlobal("RTCPeerConnection", FakePeerConnection as unknown as typeof RTCPeerConnection);
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await flushPromises();
    await wrapper.findAll("button").find((button) => button.text() === "打开画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const previewVideoElement = wrapper.find('[data-testid="robot-camera-preview-video"]').element as HTMLVideoElement;
    Object.defineProperty(previewVideoElement, "videoWidth", { configurable: true, value: 640 });
    Object.defineProperty(previewVideoElement, "videoHeight", { configurable: true, value: 480 });
    Object.defineProperty(previewVideoElement, "readyState", { configurable: true, value: 4 });
    previewVideoElement.dispatchEvent(new Event("loadeddata"));
    previewVideoElement.dispatchEvent(new Event("playing"));
    await vi.advanceTimersByTimeAsync(1100);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("画面偏暗");
    expect(wrapper.find(".robot-console-grid").text()).toContain("画面太暗，先检查镜头/光线。");
    expect(wrapper.find("details").text()).toContain("near_black");
    expect(wrapper.find("details").text()).toContain("max_luma");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/camera/offer") && options?.method === "POST")).toBe(true);
  });

  it("keeps failure status after Start Preview fails instead of collapsing to stopped_by_user", async () => {
    // Start 失败后仍要保留失败态，避免 operator 只看到 stopped_by_user 而丢失归因。
    const mockedFetch = vi.fn(async (url: string) => {
      if (url.startsWith("/api/robot-control/camera/offer")) {
        return {
          ok: false,
          status: 502,
          json: async () => ({
            schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
            proxy_status: "offer_failed",
            source_base_url: "http://192.168.1.11:8787",
            normalized_base_url: "http://192.168.1.11:8787",
            remote_endpoint: "/api/camera/offer",
            remote_http_status: 502,
            status: "blocked",
            peer_id: "",
            answer: null,
            error: "",
            failure_reason: "remote_answer_missing",
            blocked_reasons: ["remote_answer_missing"],
            ...PROOF_FLAGS,
          }),
        };
      }
      if (url.startsWith("/api/robot-control/camera/peers/")) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtures["/api/robot-control/camera/peers/peer-preview-001/close"],
        };
      }
      const fixtureKey = url.startsWith("/api/route/debug-summary")
        ? "/api/route/debug-summary"
        : url.startsWith("/api/robot-control/summary")
          ? "/api/robot-control/summary"
          : url.startsWith("/api/o7/consumer-read/tasks/")
            ? "/api/o7/consumer-read/tasks/task-consumer-001"
            : url.startsWith("/api/o7/consumer-read/tasks")
              ? "/api/o7/consumer-read/tasks"
              : url;
      return {
        ok: true,
        status: 200,
        json: async () => fixtures[fixtureKey],
      };
    });
    vi.stubGlobal("fetch", mockedFetch);
    vi.stubGlobal("RTCPeerConnection", class {
      iceConnectionState = "new";
      iceGatheringState = "complete";
      localDescription = { type: "offer" as const, sdp: "v=0\r\ns=local-offer\r\n" };
      addTransceiver() { return undefined; }
      async createOffer() { return this.localDescription; }
      async setLocalDescription() { return undefined; }
      getReceivers() { return []; }
      close() { this.iceConnectionState = "closed"; }
    } as unknown as typeof RTCPeerConnection);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "打开画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("失败");
    expect(wrapper.find("details").text()).toContain("start_failed");
    expect(wrapper.find("details").text()).toContain("remote_answer_missing");
    expect(wrapper.find("details").text()).not.toContain("preview_statusstopped_by_user");
  });

  it("renders hardware material coverage with fail-closed copy", async () => {
    // Hardware Materials tab 使用 API 返回的 coverage，不把材料存在渲染成 HIL pass。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "硬件")?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("WAVE ROVER Material Coverage");
    expect(wrapper.text()).toContain("coverage is not HIL pass");
    expect(wrapper.text()).toContain("wave_rover_hil_packet_intake/pass");
    expect(wrapper.text()).toContain("feedback_T1001.log");
    expect(wrapper.text()).toContain("operator_hil_report");
    expect(wrapper.text()).toContain("hil_pass=false");
    expect(wrapper.text()).toContain("serial_path_not_proven");
    expect(wrapper.text()).toContain("Coverage gaps");
    expect(wrapper.text()).toContain("missing operator_hil_report");
    expect(wrapper.text()).toContain("not_proven boundaries");
    expect(wrapper.text()).toContain("real_uart_link_not_proven");
    expect(wrapper.text()).toContain("lidar_tof_material_not_proven");
    expect(wrapper.text()).toContain("UART newline-delimited JSON");
    expect(wrapper.text()).toContain("complete file/material coverage");
    expect(wrapper.text()).toContain("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h");
    expect(wrapper.text()).toContain("vendor_rpi_default_device");
    expect(wrapper.text()).toContain("/dev/ttyAMA0");
    expect(wrapper.text()).toContain("orange_pi_device_status");
    expect(wrapper.text()).toContain("CMD_ROS_CTRL");
    expect(wrapper.text()).toContain("hardware_verified=false");
    expect(wrapper.text()).toContain("moduleType=1");
    expect(wrapper.text()).toContain("primary_actions_enabled");
    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).not.toContain("/cmd_vel");
    expect(advancedToolsText).not.toContain("/dev/ttyUSB");
    expect(wrapper.text()).not.toMatch(/hardware connected|ready to control/i);
    expect(wrapper.text()).not.toContain("hil_pass=true");
  });

  it("renders dataset inventory without pipeline control semantics", () => {
    // Training/Labeling 面板只展示 API 清单；这里直接挂组件，避免其它 tab 的硬件参考干扰边界检查。
    const wrapper = mount(TrainingLabelingPanel, {
      props: {
        trainingLabeling: fixtures["/api/tools/training-labeling"] as never,
      },
    });
    const text = wrapper.text().toLowerCase();

    expect(wrapper.text()).toContain("Dataset/Labeling Assets");
    expect(wrapper.text()).toContain("empty_not_connected");
    expect(wrapper.text()).toContain("real_pipeline_connected");
    expect(wrapper.text()).toContain("primary_actions_enabled");
    expect(wrapper.findAll("button")).toHaveLength(0);
    expect(text).not.toContain("start ");
    expect(text).not.toContain("upload");
    expect(text).not.toContain("execute");
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toContain("/dev/tty");
  });

  it("renders O7 operator console as cloud-contract observe-only surface", async () => {
    // O7 tab 必须展示六个 KR 的契约缺口，不能出现真实控制按钮或成功外推。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "控制台")?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("O7 Operator Console");
    expect(wrapper.text()).toContain("draft_blocked_not_proven");
    expect(wrapper.text()).toContain("cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py");
    expect(wrapper.text()).toContain("observe_only");
    expect(wrapper.text()).toContain("not_connected_by_pc");
    expect(wrapper.text()).toContain("Board media preflight");
    expect(wrapper.text()).toContain("trashbot.o7_board_media_preflight.v1");
    expect(wrapper.text()).toContain("safe_to_controlfalse");
    expect(wrapper.text()).toContain("primary_actions_enabledfalse");
    expect(wrapper.text()).toContain("device_probe_attemptedfalse");
    expect(wrapper.text()).toContain("real_camera_video_source");
    expect(wrapper.text()).toContain("real_tts_playback");
    expect(wrapper.text()).toContain("on_robot_media_smoke_with_no_chassis_motion");
    expect(wrapper.text()).toContain("Realtime map snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.realtime_map_snapshot.v1");
    expect(wrapper.text()).toContain("contract_placeholder_not_tf");
    expect(wrapper.text()).toContain("latency_lt_2s_proven=false");
    expect(wrapper.text()).toContain("ros2_tf_forwarding_not_proven");
    expect(wrapper.text()).toContain("Elevator state snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.elevator_state_snapshot.v1");
    expect(wrapper.text()).toContain("not_connected:not_proven");
    expect(wrapper.text()).toContain("real_elevator_state_chain_not_proven");
    expect(wrapper.text()).toContain("floor_recognition_not_proven");
    expect(wrapper.text()).toContain("Route replay snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.route_replay_snapshot.v1");
    expect(wrapper.text()).toContain("blocked_no_cloud_task_archive");
    expect(wrapper.text()).toContain("frame_count=0");
    expect(wrapper.text()).toContain("blocked_not_available");
    expect(wrapper.text()).toContain("missing_keyframe_archive");
    expect(wrapper.text()).toContain("state_transition_timeline_not_backfilled");
    expect(wrapper.text()).toContain("o6_cloud_task_archive_query_contract");
    expect(wrapper.text()).toContain("Labeling queue snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.labeling_queue_snapshot.v1");
    expect(wrapper.text()).toContain("blocked_no_annotation_api");
    expect(wrapper.text()).toContain("missing_review_item_media_ref");
    expect(wrapper.text()).toContain("blocked_no_label_schema_api");
    expect(wrapper.text()).toContain("submit enabledfalse");
    expect(wrapper.text()).toContain("rollback enabledfalse");
    expect(wrapper.text()).toContain("annotation APIfalse");
    expect(wrapper.text()).toContain("missing_submit_audit_log");
    expect(wrapper.text()).toContain("missing_rollback_audit_log");
    expect(wrapper.text()).toContain("available=false");
    expect(wrapper.text()).toContain("missing_training_dataset_export");
    expect(wrapper.text()).toContain("dataset_manifest_export_not_available");
    expect(wrapper.text()).toContain("o6_annotation_review_queue_query_contract");
    expect(wrapper.text()).toContain("dataset_export_manifest_contract");
    expect(wrapper.text()).toContain("Voice ASR/TTS snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.voice_asr_tts_snapshot.v1");
    expect(wrapper.text()).toContain("connected=false");
    expect(wrapper.text()).toContain("blocked_no_voice_api");
    expect(wrapper.text()).toContain("missing_asr_partial_transcript_trace");
    expect(wrapper.text()).toContain("missing_asr_final_transcript_trace");
    expect(wrapper.text()).toContain("draft_disabled");
    expect(wrapper.text()).toContain("not_connected");
    expect(wrapper.text()).toContain("TTS send enabledfalse");
    expect(wrapper.text()).toContain("enabled=false");
    expect(wrapper.text()).toContain("blocked_no_ack_contract");
    expect(wrapper.text()).toContain("missing_voice_command_audit_log");
    expect(wrapper.text()).toContain("missing_speaker_dispatch_ack");
    expect(wrapper.text()).toContain("voice_api_not_connected");
    expect(wrapper.text()).toContain("real_speaker_dispatch_ack");
    expect(wrapper.text()).toContain("voice_asr_tts_cloud_api_contract");
    expect(wrapper.text()).toContain("Safe command snapshot");
    expect(wrapper.text()).toContain("trashbot.o7.safe_command_snapshot.v1");
    expect(wrapper.text()).toContain("command dispatchfalse");
    expect(wrapper.text()).toContain("manual controlfalse");
    expect(wrapper.text()).toContain("navigate goalfalse");
    expect(wrapper.text()).toContain("keyboard controlfalse");
    expect(wrapper.text()).toContain("command APIfalse");
    expect(wrapper.text()).toContain("robot ACKfalse");
    expect(wrapper.text()).toContain("keyboard_arrow_keys_disabled");
    expect(wrapper.text()).toContain("blocked_no_robot_hil_limits");
    expect(wrapper.text()).toContain("map_click_disabled");
    expect(wrapper.text()).toContain("empty_not_connected");
    expect(wrapper.text()).toContain("future_disabled");
    expect(wrapper.text()).toContain("Idempotency-Key");
    expect(wrapper.text()).toContain("required_not_connected");
    expect(wrapper.text()).toContain("blocked_no_confirmation_ui");
    expect(wrapper.text()).toContain("blocked_no_robot_ack_contract");
    expect(wrapper.text()).toContain("missing_robot_command_ack");
    expect(wrapper.text()).toContain("missing_command_timeout_policy_and_trace");
    expect(wrapper.text()).toContain("missing_cancel_command_ack_trace");
    expect(wrapper.text()).toContain("missing_stop_command_ack_trace");
    expect(wrapper.text()).toContain("missing_robot_recovery_event_trace");
    expect(wrapper.text()).toContain("safe_command_api_not_connected");
    expect(wrapper.text()).toContain("real_manual_turn_control");
    expect(wrapper.text()).toContain("real_navigate_goal_dispatch");
    expect(wrapper.text()).toContain("cloud_safe_command_api_contract_with_bearer_auth");
    expect(wrapper.text()).toContain("cancel_stop_recovery_ack_trace");
    expect(wrapper.text()).toContain("O7-KR1");
    expect(wrapper.text()).toContain("O7-KR6");
    expect(wrapper.text()).toContain("operator.safe_command_preview.v1");
    expect(wrapper.text()).toContain("sends_to_robot=false");
    expect(wrapper.text()).toContain("pc_must_not_direct_connect_robot");
    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).not.toContain("/cmd_vel");
    expect(wrapper.findAll("button").map((button) => button.text())).not.toContain("Manual turn envelope");
    expect(wrapper.text()).not.toMatch(/ready[_ ]?to[_ ]?control/i);
    expect(wrapper.text()).not.toMatch(/success[_ -]?claim[_ -]?allowed=true/i);
    expect(wrapper.text()).not.toMatch(/\bpass=true\b/i);
    expect(wrapper.text()).not.toMatch(/\bpassed=true\b/i);
    expect(advancedToolsText).not.toContain("/dev/ttyUSB");
    expect(advancedToolsText).not.toContain("/dev/ttyACM");
    expect(wrapper.text()).not.toMatch(/success[_ ]?claim[_ ]?allowed true/i);
    expect(wrapper.text()).not.toMatch(/submit enabledtrue/i);
    expect(wrapper.text()).not.toMatch(/rollback enabledtrue/i);
    expect(wrapper.text()).not.toMatch(/tts send enabledtrue/i);
    expect(wrapper.text()).not.toMatch(/manual controltrue/i);
    expect(wrapper.text()).not.toMatch(/navigate goaltrue/i);
    expect(wrapper.text()).not.toMatch(/keyboard controltrue/i);
  });

  it("loads O7 fixture previews through PC-only read-only API clients", async () => {
    // O7 Previews tab 不自动读本地路径；operator 必须显式点击 Load preview。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "预览")?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("O7 Fixture Previews");
    expect(wrapper.text()).toContain("O7 previews acceptance guard");
    expect(wrapper.text()).toContain("O7 real capability gap summary");
    expect(wrapper.text()).toContain("O7 live endpoints manifest");
    expect(wrapper.text()).toContain("network_probe_executed=false");
    expect(wrapper.text()).toContain("O7-KR1 realtime map/pose");
    expect(wrapper.text()).toContain("O7-KR6 command");
    expect(wrapper.text()).toContain("matched surface count=0");
    expect(wrapper.text()).toContain("ready_for_real_operation=false");
    expect(wrapper.text()).toContain("Remaining real capability gaps");
    expect(wrapper.text()).toContain("not_loaded");
    expect(wrapper.text()).toContain("Key guard false fields");
    expect(wrapper.text()).toContain("safe_to_control=false");
    expect(wrapper.text()).toContain("sends_commands=false");
    expect(wrapper.text()).toContain("connects_cloud_production=false");
    expect(wrapper.text()).toContain("robot_control_executed=false");
    expect(wrapper.text()).toContain("o7_previews_acceptance_guard_not_loaded");
    expect(wrapper.text()).toContain("Cloud operator console probe");
    expect(wrapper.text()).toContain("Cloud archive tasks probe");
    expect(wrapper.text()).toContain("RTC signaling contract probe");
    expect(wrapper.text()).toContain("Realtime/elevator cloud probe");
    expect(wrapper.text()).toContain("Local field evidence manifest JSON");
    expect(wrapper.text()).toContain("Cloud Archive Tasks");
    expect(wrapper.text()).toContain("fixture_json_not_provided");
    expect(wrapper.text()).toContain("archive_json_not_provided");
    expect(wrapper.text()).toContain("cloud_operator_console_probe_not_loaded");
    expect(wrapper.text()).toContain("cloud_archive_tasks_probe_not_loaded");
    expect(wrapper.text()).toContain("rtc_signaling_contract_probe_not_loaded");
    expect(wrapper.text()).toContain("realtime_elevator_probe_not_loaded");
    expect(wrapper.text()).toContain("Debug fallback: archive fixture labeling review panel");
    expect(wrapper.findAll("button").find((button) => button.text() === "Next item")?.attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Local voice ASR/TTS monitor panel");
    expect(wrapper.findAll("button").find((button) => button.text() === "Next ASR event")?.attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Local TTS draft editor");
    expect(wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("Local safe command review panel");
    expect(wrapper.findAll("button").find((button) => button.text() === "Next command")?.attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("real realtime API");
    expect(wrapper.text()).toContain("robot ACK");
    expect(wrapper.text()).toContain("HIL/hardware safety");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/realtime-elevator-preview");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/previews/acceptance");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/live-endpoints/manifest");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/realtime-elevator-probe");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/rtc-signaling-contract-probe");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/cloud-archive/tasks");

    expect(wrapper.findAll("input").length).toBeGreaterThanOrEqual(21);
    await wrapper.find('input[aria-label="Cloud operator console probe base URL"]').setValue("http://127.0.0.1:8088");
    await wrapper.find('input[aria-label="Cloud archive tasks probe base URL"]').setValue("http://127.0.0.1:8088");
    await wrapper.find('input[aria-label="O7 consumer read base URL"]').setValue("http://127.0.0.1:8088");
    await wrapper.find('input[aria-label="O7 consumer selected task ID"]').setValue("task-consumer-001");
    await wrapper
      .find('input[aria-label="O7 consumer local field evidence manifest JSON"]')
      .setValue("fixtures/field-evidence-manifest.json");
    await wrapper.find('input[aria-label="Realtime elevator cloud probe base URL"]').setValue("http://127.0.0.1:8088");
    await wrapper.find('input[aria-label="RTC signaling contract probe base URL"]').setValue("http://127.0.0.1:8088");
    await wrapper.find('input[aria-label="Cloud archive fixture JSON path"]').setValue("fixtures/archive.json");
    await wrapper.find('input[aria-label="Realtime/Elevator fixture JSON path"]').setValue("fixtures/realtime.json");
    await wrapper.find('input[aria-label="Route Replay fixture JSON path"]').setValue("fixtures/route.json");
    await wrapper.find('input[aria-label="Labeling fixture JSON path"]').setValue("fixtures/labeling.json");
    await wrapper.find('input[aria-label="Voice fixture JSON path"]').setValue("fixtures/voice.json");
    await wrapper.find('input[aria-label="Safe Command fixture JSON path"]').setValue("fixtures/safe-command.json");

    const callsBeforeManifest = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Load live endpoints manifest")?.trigger("click");
    await flushPromises();
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeManifest + 1);

    const callsBeforeAcceptanceGuard = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Load previews acceptance guard")?.trigger("click");
    await flushPromises();
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeAcceptanceGuard + 1);

    await wrapper.findAll("button").find((button) => button.text() === "Probe cloud operator console")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Probe cloud archive tasks")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Probe RTC signaling contract")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Probe realtime/elevator snapshot")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Load consumer task list")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Load consumer task detail")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Load archive tasks")?.trigger("click");
    await flushPromises();

    for (const label of [
      "Load Realtime/Elevator preview",
      "Load Route Replay preview",
      "Load Labeling preview",
      "Load Voice preview",
      "Load Safe Command preview",
    ]) {
      await wrapper.findAll("button").find((button) => button.text() === label)?.trigger("click");
      await flushPromises();
    }

    const previewCalls = mockedFetch.mock.calls.map(([url]) => String(url)).filter((url) => url.startsWith("/api/o7/"));
    expect(previewCalls).toContain("/api/o7/live-endpoints/manifest");
    expect(previewCalls).toContain("/api/o7/previews/acceptance");
    expect(previewCalls).toContain("/api/o7/cloud-operator-console-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/consumer-read/tasks?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain(
      "/api/o7/consumer-read/tasks/task-consumer-001?baseUrl=http%3A%2F%2F127.0.0.1%3A8088&fieldEvidenceManifestJson=fixtures%2Ffield-evidence-manifest.json",
    );
    expect(previewCalls).toContain("/api/o7/cloud-archive/tasks-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/rtc-signaling-contract-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/realtime-elevator-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/cloud-archive/tasks?archiveJson=fixtures%2Farchive.json");
    expect(previewCalls).toContain("/api/o7/realtime-elevator-preview?fixtureJson=fixtures%2Frealtime.json");
    expect(previewCalls).toContain("/api/o7/route-replay-preview?fixtureJson=fixtures%2Froute.json");
    expect(previewCalls.some((url) => url.includes("/api/o7/labeling-preview"))).toBe(true);
    expect(previewCalls).toContain("/api/o7/voice-preview?fixtureJson=fixtures%2Fvoice.json");
    expect(previewCalls).toContain("/api/o7/safe-command-preview?fixtureJson=fixtures%2Fsafe-command.json");
    expect(wrapper.text()).toContain("trashbot.o7.realtime_elevator_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.route_replay_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.labeling_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.voice_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.safe_command_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.cloud_archive_tasks.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_consumer_task_list.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_consumer_task_detail.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1");
    expect(wrapper.text()).toContain("trashbot.o7.rtc_signaling_contract.v1");
    expect(wrapper.text()).toContain("static_fail_closed_contract");
    expect(wrapper.text()).toContain("webrtc_session_created=false");
    expect(wrapper.text()).toContain("first_video_frame_ref");
    expect(wrapper.text()).toContain("trashbot.o7.previews_acceptance.v1");
    expect(wrapper.text()).toContain("trashbot.o7.live_endpoints_manifest.v1");
    expect(wrapper.text()).toContain("readiness_manifest_ready");
    expect(wrapper.text()).toContain("configured=1");
    expect(wrapper.text()).toContain("blocked=1");
    expect(wrapper.text()).toContain("token_present=1");
    expect(wrapper.text()).toContain("O7-KR1+O7-KR2 rtc_realtime_pose_elevator · status=configured");
    expect(wrapper.text()).toContain("wss://relay.example.test/o7/realtime");
    expect(wrapper.text()).toContain("token=present");
    expect(wrapper.text()).toContain("O7-KR3 route_replay_source · status=blocked");
    expect(wrapper.text()).toContain("blocked_unsafe_url");
    expect(wrapper.text()).toContain("O7_ROUTE_REPLAY_URL:url_must_not_include_credentials_query_or_hash");
    expect(wrapper.text()).toContain("token_values_exposed=false");
    expect(wrapper.text()).toContain("url_query_hash_credentials_exposed=false");
    expect(wrapper.text()).toContain("task-consumer-001");
    expect(wrapper.text()).toContain("local_consumer_detail_cursor_ready");
    expect(wrapper.text()).toContain("readonly_consumer_detail_trajectory_ready");
    expect(wrapper.text()).toContain("consumer-frame-000.jpg");
    expect(wrapper.text()).toContain("consumer_en_route");
    expect(wrapper.text()).toContain("consumer-event-001.json");
    expect(wrapper.text()).toContain("consumer-evidence-001.jpg");
    expect(wrapper.text()).toContain("consumer-inference-001.json");
    expect(wrapper.text()).toContain("latest_known_robot_snapshot_not_task_aligned");
    expect(wrapper.text()).toContain("idempotent_command_api_trace");
    expect(wrapper.text()).toContain("real_robot_ack_connected");
    expect(wrapper.text()).toContain("software_proof_o7_previews_acceptance_guard");
    expect(wrapper.text()).toContain("O7 real capability gap summary");
    expect(wrapper.text()).toContain("O7-KR1 realtime map/pose");
    expect(wrapper.text()).toContain("O7-KR2 elevator state");
    expect(wrapper.text()).toContain("O7-KR3 route replay");
    expect(wrapper.text()).toContain("O7-KR4 labeling");
    expect(wrapper.text()).toContain("O7-KR5 ASR/TTS");
    expect(wrapper.text()).toContain("O7-KR6 command");
    expect(wrapper.text()).toContain(
      "O7-KR1 realtime map/pose · matched surface count=2 · surfaces=realtime_elevator_probe, realtime_map_pose_preview",
    );
    expect(wrapper.text()).toContain(
      "O7-KR2 elevator state · matched surface count=2 · surfaces=realtime_elevator_probe, elevator_state_timeline_preview",
    );
    expect(wrapper.text()).toContain(
      "O7-KR3 route replay · matched surface count=2 · surfaces=route_replay_player, route_replay_trajectory_minimap",
    );
    expect(wrapper.text()).toContain(
      "O7-KR4 labeling · matched surface count=2 · surfaces=labeling_review_panel, local_draft_annotation_editor",
    );
    expect(wrapper.text()).toContain(
      "O7-KR5 ASR/TTS · matched surface count=2 · surfaces=voice_monitor_panel, local_tts_draft_editor",
    );
    expect(wrapper.text()).toContain(
      "O7-KR6 command · matched surface count=2 · surfaces=safe_command_review_panel, local_safe_command_draft_editor",
    );
    expect(wrapper.text()).toContain("ready_for_real_operation=false");
    expect(wrapper.text()).toContain("production_realtime_stream_forbidden");
    expect(wrapper.text()).toContain("real_realtime_map_pose");
    expect(wrapper.text()).toContain("rtc_signaling_contract_probe_does_not_prove_real_rtc_video_or_media_transport");
    expect(wrapper.text()).toContain("connect_real_rtc_video_and_realtime_pose_stream");
    expect(wrapper.text()).toContain("connect_real_route_replay_archive");
    expect(wrapper.text()).toContain("connect_real_annotation_voice_command_apis");
    expect(wrapper.text()).toContain("safe_to_control=false");
    expect(wrapper.text()).toContain("sends_commands=false");
    expect(wrapper.text()).toContain("connects_cloud_production=false");
    expect(wrapper.text()).toContain("robot_control_executed=false");
    expect(wrapper.text()).toContain("cloud_operator_console_probe");
    expect(wrapper.text()).toContain("rtc_signaling_contract_probe");
    expect(wrapper.text()).toContain("route_replay_player");
    expect(wrapper.text()).toContain("realtime_map_pose_preview");
    expect(wrapper.text()).toContain("elevator_state_timeline_preview");
    expect(wrapper.text()).toContain("route_replay_trajectory_minimap");
    expect(wrapper.text()).toContain("local_draft_annotation_editor");
    expect(wrapper.text()).toContain("voice_monitor_panel");
    expect(wrapper.text()).toContain("local_tts_draft_editor");
    expect(wrapper.text()).toContain("local_safe_command_draft_editor");
    expect(wrapper.text()).toContain("Realtime map pose preview");
    expect(wrapper.text()).toContain("Elevator state timeline preview");
    expect(wrapper.text()).toContain("Route replay trajectory minimap");
    expect(wrapper.text()).toContain("local_loopback_http_contract_shapes");
    expect(wrapper.text()).toContain("production_cloud_connection_blocked_by_design");
    expect(wrapper.text()).toContain("real_rtc_video_connected");
    expect(wrapper.text()).toContain("trashbot.o7.realtime_elevator_snapshot.v1");
    expect(wrapper.text()).toContain("loaded_fail_closed_contract");
    expect(wrapper.text()).toContain("none_remote_contract_is_still_observe_only");
    expect(wrapper.text()).toContain("none_remote_contract_is_still_blocked_not_proven");
    expect(wrapper.text()).toContain("Dangerous true fields");
    expect(wrapper.text()).toContain("Inspector summaries");
    expect(wrapper.text()).toContain("route_replay_summary=status=fixture_inspector_ready; frame_count=2");
    expect(wrapper.text()).toContain("playback_available=false");
    expect(wrapper.text()).toContain("labeling_queue_summary=status=fixture_labeling_ready; review_item_count=2");
    expect(wrapper.text()).toContain("submit_enabled=false");
    expect(wrapper.text()).toContain("voice_asr_tts_summary=status=fixture_voice_ready; asr_event_count=2");
    expect(wrapper.text()).toContain("tts_send_enabled=false");
    expect(wrapper.text()).toContain("safe_command_summary=status=fixture_command_ready; command_count=2");
    expect(wrapper.text()).toContain("command_dispatch_enabled=false");
    expect(wrapper.text()).toContain("robot_control_executed=false");
    expect(wrapper.text()).toContain("local loopback only");
    expect(wrapper.text()).toContain("robot pose");
    expect(wrapper.text()).toContain("x_m=1.25");
    expect(wrapper.text()).toContain("pose_source=fixture_pose_slot_not_tf");
    expect(wrapper.text()).toContain("real_ros2_tf_connected=false");
    expect(wrapper.text()).toContain("probe observed at ms");
    expect(wrapper.text()).toContain("remote pose timestamp ms");
    expect(wrapper.text()).toContain("remote pose age ms");
    expect(wrapper.text()).toContain("freshness gate status");
    expect(wrapper.text()).toContain("pc_only_freshness_observed_not_latency_proof:blocked_not_proven");
    expect(wrapper.text()).toContain("remote_pose_timestamp_ms");
    expect(wrapper.text()).toContain("remote_pose_age_ms");
    expect(wrapper.text()).toContain("freshness_gate_status");
    expect(wrapper.text()).toContain("Realtime map pose preview");
    expect(wrapper.find('svg[aria-label="Realtime map pose preview"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("readonly_probe_summary_pose_ready");
    expect(wrapper.text()).toContain("pose_marker");
    expect(wrapper.text()).toContain("x_m=1.25; y_m=-0.75; yaw_rad=1.57");
    expect(wrapper.text()).toContain("map_frame/ref");
    expect(wrapper.text()).toContain("latency_lt_2s_provenfalse");
    expect(wrapper.text()).toContain("real_ros2_tf_connectedfalse");
    expect(wrapper.text()).toContain("real_realtime_api_connectedfalse");
    expect(wrapper.text()).toContain("Elevator state samples");
    expect(wrapper.text()).toContain("Elevator state timeline preview");
    expect(wrapper.text()).toContain("sample_index=0");
    expect(wrapper.text()).toContain("sample_index=1");
    expect(wrapper.text()).toContain("state=waiting_operator");
    expect(wrapper.text()).toContain("evidence_ref=state-001.json");
    expect(wrapper.text()).toContain("real_elevator_state_chain_connectedfalse");
    expect(wrapper.text()).toContain("floor_recognition_provenfalse");
    expect(wrapper.text()).toContain("human_takeover_provenfalse");
    expect(wrapper.text()).toContain("Route membership false fields");
    expect(wrapper.text()).toContain("route_membership.in_elevator_zone=false");
    expect(wrapper.text()).toContain("task_archive_002");
    expect(wrapper.text()).toContain("needs_review_fixture_only");
    expect(wrapper.text()).toContain("fixture_inspector_ready");
    expect(wrapper.text()).toContain("Local route replay player");
    expect(wrapper.text()).toContain("local_fixture_cursor_only");
    expect(wrapper.text()).toContain("local_fixture_cursor_ready");
    expect(wrapper.text()).toContain("Route replay trajectory minimap");
    expect(wrapper.find('svg[aria-label="Route replay trajectory minimap"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("readonly_fixture_trajectory_ready");
    expect(wrapper.text()).toContain("trajectory_points");
    expect(wrapper.text()).toContain("current_marker");
    expect(wrapper.text()).toContain("frame_index=0");
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.text()).toContain("frame_ref_000");
    expect(wrapper.text()).toContain("keyframe_ref_001");
    expect(wrapper.text()).toContain("playing=false");
    expect(wrapper.text()).toContain("safe_to_play=false");

    const callsBeforeLocalCursor = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Next frame")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("2 / 2");
    expect(wrapper.text()).toContain("frame_ref_001");
    expect(wrapper.text()).toContain("frame_index=1");
    await wrapper.findAll("button").find((button) => button.text() === "Reset cursor")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalCursor);
    expect(wrapper.text()).toContain("Consumer-detail labeling queue primary path");
    expect(wrapper.text()).toContain("consumer-detail labeling primary path");
    expect(wrapper.text()).toContain("consumer_detail_labeling_queue_ready");
    expect(wrapper.text()).toContain("submit_enabled=false");
    expect(wrapper.text()).toContain("export_enabled=false");
    expect(wrapper.text()).toContain("rollback_enabled=false");
    expect(wrapper.text()).toContain("real_annotation_api_connected=false");
    expect(wrapper.text()).toContain("dataset_export_available=false");
    expect(wrapper.text()).toContain("consumer-detail labeling primary path uses task detail labels plus evidence/events/trajectory checks");
    expect(wrapper.text()).toContain("Labeling queue inspector debug fallback");
    expect(wrapper.text()).toContain("Debug fallback: archive fixture labeling review panel");
    expect(wrapper.text()).toContain("local_fixture_item_cursor_only");
    expect(wrapper.text()).toContain("local_fixture_item_cursor_ready");
    expect(wrapper.text()).toContain("draft_labels.autosave_available=false");
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.findAll("button").find((button) => button.text() === "Next item")?.attributes("disabled")).toBeUndefined();
    expect(wrapper.text()).toContain("review_item_001");
    expect(wrapper.text()).toContain("frame_media_001.jpg");
    expect(wrapper.text()).not.toContain("review_item_002frame_002");

    const callsBeforeLabelingCursor = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Next item")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("2 / 2");
    expect(wrapper.text()).toContain("review_item_002");
    expect(wrapper.text()).toContain("frame_media_002.jpg");
    await wrapper.findAll("button").find((button) => button.text() === "Reset item")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLabelingCursor);
    expect(wrapper.text()).toContain("Local draft annotation editor");
    expect(wrapper.text()).toContain("browser_memory_only");
    expect(wrapper.text()).toContain("local_memory_draft_ready");
    expect(wrapper.text()).toContain("local_memory_draft_valid");
    expect(wrapper.text()).toContain("autosave_availablefalse");
    expect(wrapper.text()).toContain("cloud_write_executedfalse");

    const callsBeforeLocalDraftEdit = mockedFetch.mock.calls.length;
    await wrapper.find('select[aria-label="Local draft annotation label type"]').setValue("obstacle_type");
    await wrapper.find('input[aria-label="Local draft annotation confidence"]').setValue("0.72");
    await wrapper.find('textarea[aria-label="Local draft annotation note"]').setValue("local draft note for review item 001");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("obstacle_type");
    expect(wrapper.text()).toContain("0.72");
    expect(wrapper.text()).toContain("note_chars=36");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalDraftEdit);

    await wrapper.find('input[aria-label="Local draft annotation confidence"]').setValue("1.25");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_invalid_confidence");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalDraftEdit);

    await wrapper.findAll("button").find((button) => button.text() === "Next item")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("2 / 2");
    expect(wrapper.text()).toContain("review_item_002");
    expect(wrapper.text()).toContain("0.5");
    expect(wrapper.text()).not.toContain("local draft note for review item 001");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalDraftEdit);

    await wrapper.findAll("button").find((button) => button.text() === "Reset draft")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("local_memory_draft_valid");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalDraftEdit);

    await wrapper.findAll("button").find((button) => button.text() === "Reset item")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.text()).toContain("blocked_invalid_confidence");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalDraftEdit);
    expect(wrapper.text()).toContain("floor_label");
    expect(wrapper.text()).toContain("draft_label_001.json");
    expect(wrapper.text()).toContain("operator_review_not_complete");
    expect(wrapper.text()).toContain("draft_labels.autosave_available=false");
    expect(wrapper.text()).toContain("dataset_export.available=false");
    expect(wrapper.text()).toContain("Voice ASR/TTS inspector");
    expect(wrapper.text()).toContain("Local voice ASR/TTS monitor panel");
    expect(wrapper.text()).toContain("local_fixture_voice_monitor_only");
    expect(wrapper.text()).toContain("local_fixture_voice_monitor_ready");
    expect(wrapper.text()).toContain("ASR event sample");
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.text()).toContain("asr_partial_001.json");
    expect(wrapper.text()).toContain("请去三楼电梯口");
    expect(wrapper.text()).toContain("我会等待人工确认后再播报。");
    expect(wrapper.text()).toContain("tts_draft.confirmation_required");
    expect(wrapper.text()).toContain("confirmation_required");
    expect(wrapper.text()).toContain("Local TTS draft editor");
    expect(wrapper.text()).toContain("browser_memory_only");
    expect(wrapper.text()).toContain("local_tts_draft_ready");
    expect(wrapper.text()).toContain("local_tts_draft_valid");
    expect(wrapper.text()).toContain("latest_final_chars=");
    expect(wrapper.text()).toContain("draft text length");
    expect(wrapper.text()).toContain("playback_availablefalse");
    expect(wrapper.text()).toContain("cloud_write_executedfalse");
    expect(wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").attributes("disabled")).toBeUndefined();
    expect(wrapper.text()).toContain("speaker_ack_missing.json");
    expect(wrapper.text()).toContain("audio_input_not_checked");
    expect(wrapper.text()).toContain("speaker_dispatch.sends_to_robot=false");
    expect(wrapper.text()).toContain("real_asr_tts_runtime_connected=false");

    const callsBeforeLocalTtsDraftEdit = mockedFetch.mock.calls.length;
    await wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").setValue("请乘客确认后我再播报。");
    await wrapper.find("input[aria-label=\"Local TTS voice profile\"]").setValue("operator-soft");
    await wrapper.find("input[aria-label=\"Local TTS language\"]").setValue("zh-CN");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("operator-soft");
    expect(wrapper.text()).toContain("local_tts_draft_valid");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.find('input[aria-label="Cloud archive fixture JSON path"]').setValue("fixtures/archive-other.json");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("operator-default");
    expect(wrapper.text()).not.toContain("operator-soft");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").setValue("");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_tts_text_empty");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").setValue("请".repeat(121));
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_tts_text_too_long");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.find("textarea[aria-label=\"Local TTS draft text\"]").setValue("请确认我再播报。");
    await wrapper.find("input[aria-label=\"Local TTS voice profile\"]").setValue("");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_voice_profile_empty");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.find("input[aria-label=\"Local TTS voice profile\"]").setValue("operator-soft");
    await wrapper.find("input[aria-label=\"Local TTS language\"]").setValue("");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_language_empty");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    await wrapper.findAll("button").find((button) => button.text() === "Reset TTS draft")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("operator-default");
    expect(wrapper.text()).toContain("local_tts_draft_valid");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalTtsDraftEdit);

    const callsBeforeVoiceCursor = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Next ASR event")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("2 / 2");
    expect(wrapper.text()).toContain("asr_final_001.json");
    await wrapper.findAll("button").find((button) => button.text() === "Reset ASR cursor")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeVoiceCursor);
    expect(wrapper.text()).toContain("asr_stream_connected=false");
    expect(wrapper.text()).toContain("tts_send_enabled=false");
    expect(wrapper.text()).toContain("speaker_dispatch_enabled=false");
    expect(wrapper.text()).toContain("real_voice_api_connected=false");
    expect(wrapper.text()).toContain("real_asr_tts_runtime_connected=false");
    expect(wrapper.text()).toContain("speaker_dispatch.sends_to_robot=false");
    expect(wrapper.text()).toContain("Safe command inspector");
    expect(wrapper.text()).toContain("Local safe command review panel");
    expect(wrapper.text()).toContain("local_fixture_command_cursor_only");
    expect(wrapper.text()).toContain("local_fixture_safe_command_review_ready");
    expect(wrapper.text()).toContain("archive_command_session_002");
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.text()).toContain("command_archive_000");
    expect(wrapper.text()).toContain("command_archive_001");
    expect(wrapper.text()).toContain("manual_turn_envelope.json");
    expect(wrapper.text()).toContain("navigate_goal_envelope.json");
    expect(wrapper.text()).toContain("idempotency_policy.json");
    expect(wrapper.text()).toContain("robot_ack_timeout_trace_missing");
    expect(wrapper.text()).toContain("cancel_ack_trace_missing");
    expect(wrapper.text()).toContain("stop_ack_trace_missing");
    expect(wrapper.text()).toContain("recovery_event_trace_missing");
    expect(wrapper.text()).toContain("keyboard_control_enabled=false");
    expect(wrapper.text()).toContain("manual_turn_envelope.sends_to_robot=false");
    expect(wrapper.text()).toContain("navigate_goal_envelope.sends_to_robot=false");

    expect(wrapper.text()).toContain("Local safe command draft editor");
    expect(wrapper.text()).toContain("local_browser_memory_only");
    expect(wrapper.text()).toContain("local_safe_command_draft_valid");
    expect(wrapper.text()).toContain("confirmation_required");
    expect(wrapper.text()).toContain("command_dispatch_enabled");
    expect(wrapper.text()).toContain("cloud_write_executed");

    const callsBeforeLocalSafeCommandDraftEdit = mockedFetch.mock.calls.length;
    await wrapper.find("input[aria-label=\"Local safe command manual direction\"]").setValue("sideways");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_manual_direction_not_allowed");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    await wrapper.find("input[aria-label=\"Local safe command idempotency draft ref\"]").setValue("");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_idempotency_key_missing");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    await wrapper.find("input[aria-label=\"Local safe command idempotency draft ref\"]").setValue("draft-ref-custom");
    await wrapper.find("select[aria-label=\"Local safe command mode\"]").setValue("navigate_goal");
    await wrapper.find("input[aria-label=\"Local safe command target x\"]").setValue("abc");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("blocked_invalid_navigate_goal");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    await wrapper.find("input[aria-label=\"Local safe command target x\"]").setValue("1.25");
    await wrapper.find("input[aria-label=\"Local safe command target y\"]").setValue("-0.5");
    await wrapper.find("input[aria-label=\"Local safe command target yaw\"]").setValue("1.57");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("local_safe_command_draft_valid");
    expect(wrapper.text()).toContain("x=1.25; y=-0.5; yaw=1.57");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    await wrapper.findAll("button").find((button) => button.text() === "Reset command draft")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("idempotency_key_000.json");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    await wrapper.find("input[aria-label=\"Local safe command idempotency draft ref\"]").setValue("draft-ref-custom");
    await wrapper.find('input[aria-label="Cloud archive fixture JSON path"]').setValue("fixtures/archive-third.json");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).not.toContain("draft-ref-custom");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalSafeCommandDraftEdit);

    const callsBeforeSafeCommandCursor = mockedFetch.mock.calls.length;
    await wrapper.findAll("button").find((button) => button.text() === "Next command")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("2 / 2");
    expect(wrapper.text()).toContain("command_evidence_001.json");
    await wrapper.findAll("button").find((button) => button.text() === "Reset command cursor")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(wrapper.text()).toContain("command_evidence_000.json");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeSafeCommandCursor);

    expect(wrapper.text()).toContain("arrived_at_elevator");
    expect(wrapper.text()).toContain("navigate_goal");
    expect(wrapper.text()).toContain("real_realtime_api_connected=false");
    expect(wrapper.text()).toContain("real_ros2_tf_connected=false");
    expect(wrapper.text()).toContain("real_cloud_archive_connected=false");
    expect(wrapper.text()).toContain("real_annotation_api_connected=false");
    expect(wrapper.text()).toContain("real_voice_api_connected=false");
    expect(wrapper.text()).toContain("real_command_api_connected=false");
    expect(wrapper.text()).toContain("robot_control_executed=false");
    expect(wrapper.text()).toContain("submit_enabled=false");
    expect(wrapper.text()).toContain("tts_send_enabled=false");
    expect(wrapper.text()).toContain("command_dispatch_enabled=false");
    expect(wrapper.text()).toContain("real_robot_ack_connected=false");
    expect(wrapper.text()).toContain("real_o7_realtime_cloud_stream");
    expect(wrapper.text()).toContain("real_o7_annotation_submit");
    expect(wrapper.text()).toContain("real_o7_voice_api");
    expect(wrapper.text()).toContain("real_hil_safety");
    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toMatch(
      /\bSend\b|\bSpeak\b|\bDispatch\b|\bRun\b|\bSubmit\b|\bControl\b|\bPlay\b|\bPause\b|\bExport\b|\bStop\b|\bCancel\b|\bRecovery\b/,
    );
  });

  it("loads field evidence consumer ingest from manifest and route/labeling fixtures", async () => {
    // 新入口必须把 manifest、route replay 和 labeling 绑成同一条只读消费链。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "预览")?.trigger("click");
    await wrapper.vm.$nextTick();

    await wrapper.find('input[aria-label="Field evidence manifest JSON path"]').setValue("fixtures/field-evidence-manifest.json");
    await wrapper.find('input[aria-label="Route replay fixture JSON path"]').setValue("fixtures/field-route-replay.json");
    await wrapper.find('input[aria-label="Labeling fixture JSON path"]').setValue("fixtures/field-labeling.json");
    await wrapper.findAll("button").find((button) => button.text() === "Load field evidence consumer ingest")?.trigger("click");
    await flushPromises();

    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toContain(
      "/api/o7/field-evidence-consumer-ingest?manifestJson=fixtures%2Ffield-evidence-manifest.json&routeReplayFixtureJson=fixtures%2Ffield-route-replay.json&labelingFixtureJson=fixtures%2Ffield-labeling.json",
    );
    expect(wrapper.text()).toContain("Field evidence consumer ingest");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1");
    expect(wrapper.text()).toContain("fixture_consumer_ready_not_proven");
    expect(wrapper.text()).toContain("trashbot.field_evidence_manifest.v1");
    expect(wrapper.text()).toContain("field_evidence_20260609T101500Z");
    expect(wrapper.text()).toContain("field_evidence_fixture");
    expect(wrapper.text()).toContain("preflight_ready_not_delivery_proof");
    expect(wrapper.text()).toContain("route_replay_preview");
    expect(wrapper.text()).toContain("labeling_preview");
    expect(wrapper.text()).toContain("field-evidence-task-001");
    expect(wrapper.text()).toContain("field-evidence-queue-001");
    expect(wrapper.text()).toContain("label-schema.json");
    expect(wrapper.text()).toContain("field_evidence_manifest_not_delivery_proof");
    expect(wrapper.text()).toContain("real_o7_route_replay_archive");
    expect(wrapper.text()).toContain("real_o7_annotation_submit");
    expect(wrapper.text()).toContain("field_evidence_manifest_artifacts_complete_and_preflight_ready");
    expect(wrapper.text()).toContain("safe_to_controlfalse");
    expect(wrapper.text()).toContain("delivery_successfalse");
    const advancedToolsText = wrapper.find(".advanced-tools-details").text();
    expect(advancedToolsText).not.toContain("/cmd_vel");
  });

  it("blocks consumer-detail labeling queue primary path when labeling samples are missing", async () => {
    // 这个用例只验证 consumer-detail 标注主路径的 fail-closed 分支，不依赖 archive fallback。
    const consumerTaskListFixture = fixtures["/api/o7/consumer-read/tasks"] as Record<string, unknown>;
    const blockedFixtures: Record<string, unknown> = {
      ...fixtures,
      "/api/o7/consumer-read/tasks": {
        ...consumerTaskListFixture,
        task_list: [
          {
            task_id: "task-consumer-labeling-blocked",
            robot_id: "robot_fixture",
            started_at_ms: 1000,
            finished_at_ms: 2000,
            task_status_summary: "completed_mock",
            latest_event_at_ms: 1900,
            trajectory_frame_count: 2,
            event_count: 1,
            evidence_count: 1,
            labeling_status: "partial",
            inference_status: "present",
            tunnel_status_summary: "online",
            selected: true,
          },
        ],
      },
      "/api/o7/consumer-read/tasks/task-consumer-labeling-blocked": {
        schema: "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1",
        detail_status: "loaded_fail_closed_summary",
        source_base_url: "http://127.0.0.1:8088",
        remote_endpoint:
          "/api/o6/consumer/tasks/task-consumer-labeling-blocked?view=default&include=trajectory,events,evidence,labeling,inference,tunnel",
        remote_schema: "trashbot.o6.consumer_read.v1",
        requested_task_id: "task-consumer-labeling-blocked",
        query_strategy: {
          view: "default",
          include: ["trajectory", "events", "evidence", "labeling", "inference", "tunnel"],
          primary_path: true,
          fail_closed_visible: true,
        },
        field_evidence: {
          source_contract: "trashbot.field_evidence_manifest.v1",
          input_status: "loaded",
          artifact_status: "gated",
          manifest_gate: {
            schema: "trashbot.field_evidence_manifest.v1",
            status: "gated",
            gate_pass: true,
            blocked_reason: "preflight_ready_not_delivery_proof",
            source: "local_fixture",
          },
          blocked_reason: "preflight_ready_not_delivery_proof",
          not_proven: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
        task_summary: {
          task_id: "task-consumer-labeling-blocked",
          robot_id: "robot_fixture",
          task_status_summary: "completed_mock",
          started_at_ms: 1000,
          finished_at_ms: 2000,
        },
        trajectory: {
          status: "loaded_not_proven",
          frame_count: 2,
          sample_frames: [
            {
              frame_index: 0,
              timestamp_ms: 1000,
              pose: { x_m: 0.2, y_m: 0.1, yaw_rad: 0 },
              velocity: { linear_mps: 0.1 },
              state: "consumer_departed",
              evidence_ref: "consumer-frame-000.jpg",
            },
          ],
        },
        events: {
          status: "loaded_not_proven",
          count: 1,
          sample_events: [{ event_type: "route.frame", state: "consumer_en_route", timestamp_ms: 1200, evidence_ref: "consumer-event-001.json" }],
        },
        evidence: {
          status: "loaded_not_proven",
          count: 1,
          sample_evidence: [{ evidence_type: "snapshot", state: "consumer_en_route", timestamp_ms: 1200, evidence_ref: "consumer-evidence-001.jpg" }],
        },
        labeling: {
          status: "pending",
          label_count: 0,
          sample_items: [],
        },
        inference: {
          status: "present",
          count: 1,
          sample_results: [{ result_type: "floor_recognition", status: "not_proven", timestamp_ms: 1200, evidence_ref: "consumer-inference-001.json" }],
        },
        tunnel_status: {
          status: "loaded_not_proven",
          latest_known_status: "online",
          temporal_alignment: "latest_known_robot_snapshot_not_task_aligned",
        },
        blocked_reasons: [],
        not_proven: ["proof_status=not_proven", "robot_control_executed=false"],
        fail_closed_reason: "none",
        local_loopback_only: true,
        connects_cloud_production: false,
        robot_control_executed: false,
        ...PROOF_FLAGS,
      },
    };

    const mockedFetch = vi.fn(async (url: string) => {
      const fixtureKey = url.startsWith("/api/route/debug-summary")
        ? "/api/route/debug-summary"
        : url.startsWith("/api/o7/consumer-read/tasks/")
          ? "/api/o7/consumer-read/tasks/task-consumer-labeling-blocked"
          : url.startsWith("/api/o7/consumer-read/tasks")
            ? "/api/o7/consumer-read/tasks"
            : url;
      return {
        ok: true,
        json: async () => blockedFixtures[fixtureKey],
      };
    });
    vi.stubGlobal("fetch", mockedFetch);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "预览")?.trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.findAll("button").find((button) => button.text() === "Load consumer task list")?.trigger("click");
    await flushPromises();
    await wrapper.findAll("button").find((button) => button.text() === "Load consumer task detail")?.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Consumer-detail labeling queue primary path");
    expect(wrapper.text()).toContain("blocked_not_proven");
    expect(wrapper.text()).toContain("labeling_missing");
    expect(wrapper.text()).toContain("submit_enabled=false");
    expect(wrapper.text()).toContain("export_enabled=false");
    expect(wrapper.text()).toContain("rollback_enabled=false");
    expect(wrapper.text()).toContain("real_annotation_api_connected=false");
    expect(wrapper.text()).toContain("dataset_export_available=false");
    expect(wrapper.text()).not.toContain("consumer_detail_labeling_queue_ready");
  });
});
