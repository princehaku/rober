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
    manual_control_policy: {
      pc_direct_robot_connection: false,
      cloud_mediated_only: true,
      command_dispatch_enabled: false,
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
      "real_operator_safe_command_dispatch",
      "delivery_success",
    ],
    recovery_paths: ["Connect O6 cloud archive and realtime stream before replacing draft values."],
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

function stubWorkstationFetch() {
  // 测试桩允许 route debug 带 query，确保表单路径仍走同一个只读 API。
  const mockedFetch = vi.fn(async (url: string) => {
    const fixtureKey = url.startsWith("/api/route/debug-summary") ? "/api/route/debug-summary" : url;
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

  it("submits route inputs through the workstation API query contract", async () => {
    // 组件只更新表单状态，query 拼接必须由 src/client/workstationApi.ts 集中完成。
    const mockedFetch = stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
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

  it("renders hardware material coverage with fail-closed copy", async () => {
    // Hardware Materials tab 使用 API 返回的 coverage，不把材料存在渲染成 HIL pass。
    stubWorkstationFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.findAll("button").find((button) => button.text() === "Hardware Materials")?.trigger("click");
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

    await wrapper.findAll("button").find((button) => button.text() === "O7 Console")?.trigger("click");
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
    expect(wrapper.text()).toContain("O7-KR1");
    expect(wrapper.text()).toContain("O7-KR6");
    expect(wrapper.text()).toContain("operator.safe_command_preview.v1");
    expect(wrapper.text()).toContain("sends_to_robot=false");
    expect(wrapper.text()).toContain("pc_must_not_direct_connect_robot");
    expect(wrapper.text()).not.toContain("/cmd_vel");
    expect(wrapper.findAll("button").map((button) => button.text())).not.toContain("Manual turn envelope");
    expect(wrapper.text()).not.toMatch(/ready[_ ]?to[_ ]?control/i);
    expect(wrapper.text()).not.toMatch(/success[_ ]?claim[_ ]?allowed true/i);
    expect(wrapper.text()).not.toMatch(/submit enabledtrue/i);
    expect(wrapper.text()).not.toMatch(/rollback enabledtrue/i);
  });
});
