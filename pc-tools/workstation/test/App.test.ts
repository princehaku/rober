import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import TrainingLabelingPanel from "../src/components/TrainingLabelingPanel.vue";
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
      allowed_endpoint_class: "status_latest_readback_plus_fixed_manual_stop",
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
      },
      lidar: {
        status: "radar_status_not_proven",
        latest_scan_proof_status: "scan_once_observed",
        latest_raw_packet_proof_status: "raw_packet_not_proven",
      },
      base: {
        status: "base_status_not_proven",
        latest_feedback_status: "feedback_samples_not_proven",
        feedback_ack_status: "blocked_no_ack",
      },
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
      locked_reason: "requires safety lock, HIL gate, robot ACK, timeout/cancel/stop/recovery evidence before enablement",
      manual_motion_entry_status: "controlled_jog_requires_hil_checklist",
      manual_motion_entry_label: "受控点动（需现场确认）",
      allowed_directions: ["forward", "back", "left", "right", "stop"],
      non_stop_requires_confirm_hil_checklist: true,
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
      failure_reason: "fetch_timeout_46000ms",
      blocked_reasons: ["fetch_timeout_46000ms", "post_timeout_latest_readback_loaded"],
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

function stubWorkstationFetch() {
  // 测试桩允许 route debug 带 query，确保表单路径仍走同一个只读 API。
  const mockedFetch = vi.fn(async (url: string, options?: RequestInit) => {
    let fixtureKey = url;
    if (url.startsWith("/api/route/debug-summary")) {
      fixtureKey = "/api/route/debug-summary";
    } else if (url.startsWith("/api/robot-control/summary")) {
      fixtureKey = "/api/robot-control/summary";
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
    } else if (url.startsWith("/api/robot-control/map/list")) {
      fixtureKey = "/api/robot-control/map/list";
    } else if (url.startsWith("/api/robot-control/map/save")) {
      fixtureKey = "/api/robot-control/map/save";
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
      json: async () => fixtures[fixtureKey],
    };
  });
  vi.stubGlobal("fetch", mockedFetch);
  return mockedFetch;
}

describe("App", () => {
  afterEach(() => {
    // 清理全局 fetch，避免后续用例误用上一轮 API fixture。
    vi.unstubAllGlobals();
  });

  it("renders fail-closed Node route loader and evidence fixture index", async () => {
    // UI 测试只使用 API fixture，确保页面不自己发明机器人状态或旧执行入口。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "路线")?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("node_route_json_loader");
    expect(wrapper.text()).toContain("pc-tools/workstation/src/server/routeDebugLoader.ts");
    expect(wrapper.text()).toContain("console_controls");
    expect(wrapper.text()).toContain("read_only");
    expect(wrapper.text()).toContain("not_loaded_pc_only");
    expect(wrapper.text()).toContain("blocked_not_proven");
    expect(wrapper.text()).toContain("status_json_not_provided");
    expect(wrapper.text()).not.toContain("route_debug_web.py");
    expect(wrapper.text()).not.toContain("python -m");
    expect(wrapper.text()).not.toContain("workstation_executes_python_gate");
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toContain("/dev/tty");
  });

  it("submits route inputs through the workstation API query contract", async () => {
    // 组件只更新表单状态，query 拼接必须由 src/client/workstationApi.ts 集中完成。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "路线")?.trigger("click");
    await wrapper.vm.$nextTick();

    await wrapper.find("input").setValue("C:\\tmp\\status proof.json");
    await wrapper.find("form.route-inputs").trigger("submit");
    await flushPromises();

    const routeCall = mockedFetch.mock.calls
      .map(([url]) => String(url))
      .find((url) => url.startsWith("/api/route/debug-summary?"));
    expect(routeCall).toBeTruthy();
    const parsed = new URL(routeCall ?? "", "http://workstation.local");
    expect(parsed.searchParams.get("statusJson")).toBe("C:\\tmp\\status proof.json");
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toContain("/dev/tty");
  });

  it("renders Robot Control V1 by default with Robot API proxy and locked command boundary", async () => {
    // 首屏默认就是 Robot Control；测试只验证 Node proxy 摘要和 locked UI，不触发任何真实控制 endpoint。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = wrapper.find(".robot-console-grid").text();
    expect(firstScreenText).toContain("小车连接");
    expect(firstScreenText).toContain("实时画面");
    expect(firstScreenText).toContain("雷达");
    expect(firstScreenText).toContain("地图");
    expect(firstScreenText).toContain("移动/导航");
    expect(firstScreenText).toContain("未连接");
    expect(firstScreenText).toContain("未打开");
    expect(firstScreenText).toContain("未刷新");
    expect(firstScreenText).toContain("检查路径");
    expect(firstScreenText).toContain("路径未证明");
    expect(firstScreenText).toContain("自动导航（未开放）");
    expect(firstScreenText).toContain("停止");
    expect(firstScreenText).toContain("最近证据：还没有请求。");
    expect(firstScreenText).not.toContain("启动雷达");
    expect(firstScreenText).not.toContain("停止雷达");
    expect(firstScreenText).not.toContain("前进");
    expect(firstScreenText).not.toContain("现场有人扶控并准备急停");
    expect(firstScreenText).not.toContain("HIL");
    expect(firstScreenText).not.toContain("raw");
    expect(firstScreenText).not.toContain("速度上限");
    expect(firstScreenText).not.toContain("时长上限");
    expect(firstScreenText).not.toContain("保存地图");
    expect(firstScreenText).not.toContain("task_id selector");
    expect(firstScreenText).not.toContain("O6 consumer base URL");
    expect(firstScreenText).not.toContain("peer_id");
    expect(firstScreenText).not.toContain("ice_connection_state");
    expect(firstScreenText).not.toContain("scan_once_observed");
    expect(firstScreenText).not.toContain("map_once_observed");
    expect(firstScreenText).not.toContain("path_generation_succeeded");
    expect(firstScreenText).not.toContain("path_point_count");
    expect(wrapper.text()).not.toContain("source=software_proof");
    expect(wrapper.text()).not.toContain("proof_status=not_proven");
    expect(firstScreenText).not.toContain("/cmd_vel");
    expect(wrapper.find(".tabs").text()).toContain("机器人");
    expect(wrapper.find("details summary").text()).toContain("高级诊断");
    expect(wrapper.find("details").text()).toContain("task_id");
    expect(wrapper.find("details").text()).toContain("Robot API status");
    expect(wrapper.find("details").text()).toContain("Node server only; Vue direct access=false");
    expect(wrapper.find("details").text()).toContain("path_generated");
    expect(wrapper.find("details").text()).toContain("planner_server_not_active");
    expect(wrapper.find("details").text()).toContain("safe_to_control=false");
    expect(wrapper.find("details").text()).toContain("delivery_success=false");
    expect(wrapper.find("details").text()).toContain("primary_actions_enabled=false");
    expect(wrapper.find("details").text()).toContain("现场点动设置 / 控制边界");
    expect(wrapper.find("details").text()).toContain("Nav2 规划详情");
    expect(wrapper.find("details").text()).toContain("启动雷达（高级）");
    expect(wrapper.find("details").text()).toContain("停止雷达（高级）");
    expect(wrapper.find("details").text()).toContain("前进");
    expect(wrapper.find("details").text()).toContain("速度上限");
    expect(wrapper.find("details").text()).toContain("现场有人扶控并准备急停");
  });

  it("refreshes radar and map proof through fixed POST proxies and auto refreshes the summary", async () => {
    // 刷新与 lifecycle 按钮都只打 workstation 固定代理，动作结束后还要自动回刷 summary。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const firstScreenText = wrapper.find(".robot-console-grid").text();
    expect(firstScreenText).toContain("刷新雷达");
    expect(firstScreenText).toContain("刷新地图");
    expect(firstScreenText).toContain("查看地图列表");
    expect(firstScreenText).toContain("检查路径");
    expect(firstScreenText).not.toContain("保存地图");
    expect(firstScreenText).not.toContain("启动雷达");
    expect(firstScreenText).not.toContain("停止雷达");
    expect(firstScreenText).toContain("未刷新");
    expect(firstScreenText).toContain("未读取");
    expect(firstScreenText).toContain("路径未证明");
    expect(firstScreenText).not.toContain("raw");
    expect(firstScreenText).not.toContain("HIL");
    expect(firstScreenText).not.toContain("scan_once_observed");
    expect(firstScreenText).not.toContain("map_once_observed");
    expect(firstScreenText).not.toContain("path_generation_succeeded");
    expect(firstScreenText).not.toContain("Start");
    expect(firstScreenText).not.toContain("Reset");

    await wrapper.find('input[name="robotApiBaseUrl"]').setValue("http://192.168.1.11:8787");
    await flushPromises();

    const summaryCallsBefore = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;

    await wrapper.findAll("button").find((button) => button.text() === "刷新雷达")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("已刷新");
    expect(wrapper.find(".robot-console-grid").text()).toContain("scan 可见");
    expect(wrapper.find(".robot-console-grid").text()).toContain("tf 可见");
    expect(wrapper.find("details").text()).toContain("scan_once_observed");
    expect(wrapper.find("details").text()).toContain("scan_hz_observed");
    expect(wrapper.find("details").text()).toContain("tf_observed");
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
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("启动雷达");
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

    expect(wrapper.find(".robot-console-grid").text()).toContain("已刷新");
    expect(wrapper.find(".robot-console-grid").text()).toContain("map 可见");
    expect(wrapper.find(".robot-console-grid").text()).toContain("evidence 可见");
    expect(wrapper.find("details").text()).toContain("map_once_observed");
    expect(wrapper.find("details").text()).toContain("map_file_observed");
    expect(wrapper.find("details").text()).toContain("map_metadata_observed");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/proof/refresh") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterMap = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterMap).toBeGreaterThan(summaryCallsAfterRadar);

    await wrapper.findAll("button").find((button) => button.text() === "检查路径")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("路径可生成");
    expect(wrapper.find(".robot-console-grid").text()).toContain("刷新请求超时，但 latest 已有 no-motion 路径证据；不会自动发车。");
    expect(wrapper.find(".robot-console-grid").text()).not.toContain("path_generation_succeeded");
    expect(wrapper.find("details").text()).toContain("/api/nav2/proof/refresh");
    expect(wrapper.find("details").text()).toContain("nav2_no_motion_path_generation_runtime_observed");
    expect(wrapper.find("details").text()).toContain("post_timeout_latest_readback_loaded");
    expect(wrapper.find("details").text()).toContain("path_generation_succeeded");
    expect(wrapper.find("details").text()).toContain("path_point_count");
    expect(wrapper.find("details").text()).toContain("no Nav2 start/stop; no NavigateToPose; no /cmd_vel; no /api/base/manual");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/nav2/proof/refresh") && options?.method === "POST")).toBe(true);
    const summaryCallsAfterNav2 = mockedFetch.mock.calls.filter(([url]) => String(url).startsWith("/api/robot-control/summary")).length;
    expect(summaryCallsAfterNav2).toBeGreaterThan(summaryCallsAfterMap);

    await wrapper.findAll("button").find((button) => button.text() === "查看地图列表")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("地图列表 2 个候选");
    expect(wrapper.find("details").text()).toContain("lifecycle action");
    expect(wrapper.find("details").text()).toContain("/api/map/list");
    expect(wrapper.find("details").text()).toContain("floor_1.yaml");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/list") && !options)).toBe(true);

    await wrapper.find("details").element.setAttribute("open", "");
    await wrapper.vm.$nextTick();
    await wrapper.findAll("button").find((button) => button.text() === "保存地图")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).not.toContain("保存请求已返回");
    expect(wrapper.find("details").text()).toContain("command_result");
    expect(wrapper.find("details").text()).toContain("executed=false");
    expect(wrapper.find("details").text()).toContain("software_guard_command_not_configured");
    expect(wrapper.find("details").text()).toContain("Start（受控/高级，禁用）");
    expect(wrapper.find("details").text()).toContain("Reset（受控/高级，禁用）");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/map/save") && options?.method === "POST")).toBe(true);
  });

  it("starts and stops Camera Preview through workstation camera proxy while keeping control locked", async () => {
    // WebRTC UI 测试只验证本机代理和前端状态机，不连接真实浏览器媒体栈或机器人。
    const mockedFetch = stubWorkstationFetch();
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
      localDescription: { type: "offer"; sdp: string } | null = null;
      remoteDescription: { type: "answer"; sdp: string } | null = null;
      oniceconnectionstatechange: (() => void) | null = null;
      ontrack: ((event: { track: { kind: string; readyState: string; stop: () => void; onended: (() => void) | null } }) => void) | null =
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
        this.remoteDescription = description;
        this.iceConnectionState = "connected";
        this.oniceconnectionstatechange?.();
        this.ontrack?.({
          track: {
            kind: "video",
            readyState: "live",
            stop: () => undefined,
            onended: null,
          },
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

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const robotBaseUrlInput = wrapper.find('input[name="robotApiBaseUrl"]');
    await robotBaseUrlInput.setValue("http://192.168.1.11:8787");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "打开画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("已打开");
    expect(wrapper.find(".robot-console-grid").text()).toContain("画面已打开");
    expect(wrapper.find("details").text()).toContain("preview_status");
    expect(wrapper.find("details").text()).toContain("streaming");
    expect(wrapper.find("details").text()).toContain("peer-preview-001");
    expect(wrapper.find("details").text()).toContain("ice_connection_state");
    expect(wrapper.find("details").text()).toContain("connected");
    expect(wrapper.find("details").text()).toContain("video_track_state");
    expect(wrapper.find("details").text()).toContain("live");
    expect(wrapper.find("details").text()).toContain("safe_to_control=false");
    expect(wrapper.find("details").text()).toContain("Node server only; Vue direct access=false");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).startsWith("/api/robot-control/camera/offer") && options?.method === "POST")).toBe(true);

    await wrapper.findAll("button").find((button) => button.text() === "关闭画面")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".robot-console-grid").text()).toContain("未打开");
    expect(wrapper.find("details").text()).toContain("stopped_by_user");
    expect(wrapper.find("details").text()).toContain("peer_closed:closed");
    expect(mockedFetch.mock.calls.some(([url, options]) => String(url).includes("/api/robot-control/camera/peers/peer-preview-001/close") && options?.method === "POST")).toBe(true);
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
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.text()).not.toContain("/dev/ttyUSB");
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
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.findAll("button").map((button) => button.text())).not.toContain("Manual turn envelope");
    expect(wrapper.text()).not.toMatch(/ready[_ ]?to[_ ]?control/i);
    expect(wrapper.text()).not.toMatch(/success[_ -]?claim[_ -]?allowed=true/i);
    expect(wrapper.text()).not.toMatch(/\bpass=true\b/i);
    expect(wrapper.text()).not.toMatch(/\bpassed=true\b/i);
    expect(wrapper.text()).not.toContain("/dev/ttyUSB");
    expect(wrapper.text()).not.toContain("/dev/ttyACM");
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
    expect(wrapper.text()).not.toContain("/cmd_vel");
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
    expect(wrapper.text()).not.toContain("/cmd_vel");
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
