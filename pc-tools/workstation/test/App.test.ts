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
        command_count: 1,
        sample_kinds: ["navigate_goal"],
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
      command_count: 1,
      sample_commands: [
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
    pose_freshness_summary: "age_ms=not_loaded, latency_lt_2s_proven=false, status=blocked_not_proven",
    route_membership_false_fields: ["route_membership.on_route=false", "route_membership.in_elevator_zone=false"],
    elevator_status: "current_state=not_connected, sample_count=0, status=blocked_not_proven",
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
};

function stubWorkstationFetch() {
  // 测试桩允许 route debug 带 query，确保表单路径仍走同一个只读 API。
  const mockedFetch = vi.fn(async (url: string) => {
    const fixtureKey = url.startsWith("/api/route/debug-summary")
      ? "/api/route/debug-summary"
      : url.startsWith("/api/o7/realtime-elevator-preview")
        ? "/api/o7/realtime-elevator-preview"
        : url.startsWith("/api/o7/route-replay-preview")
          ? "/api/o7/route-replay-preview"
          : url.startsWith("/api/o7/labeling-preview")
            ? "/api/o7/labeling-preview"
            : url.startsWith("/api/o7/voice-preview")
              ? "/api/o7/voice-preview"
              : url.startsWith("/api/o7/safe-command-preview")
                ? "/api/o7/safe-command-preview"
                : url.startsWith("/api/o7/cloud-archive/tasks-probe")
                  ? "/api/o7/cloud-archive/tasks-probe"
                  : url.startsWith("/api/o7/cloud-archive/tasks")
                ? "/api/o7/cloud-archive/tasks"
                : url.startsWith("/api/o7/cloud-operator-console-probe")
                  ? "/api/o7/cloud-operator-console-probe"
                  : url.startsWith("/api/o7/realtime-elevator-probe")
                    ? "/api/o7/realtime-elevator-probe"
                    : url;
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

    await wrapper.findAll("button").find((button) => button.text() === "O7 Previews")?.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("O7 Fixture Previews");
    expect(wrapper.text()).toContain("Cloud operator console probe");
    expect(wrapper.text()).toContain("Cloud archive tasks probe");
    expect(wrapper.text()).toContain("Realtime/elevator cloud probe");
    expect(wrapper.text()).toContain("Cloud Archive Tasks");
    expect(wrapper.text()).toContain("fixture_json_not_provided");
    expect(wrapper.text()).toContain("archive_json_not_provided");
    expect(wrapper.text()).toContain("cloud_operator_console_probe_not_loaded");
    expect(wrapper.text()).toContain("cloud_archive_tasks_probe_not_loaded");
    expect(wrapper.text()).toContain("realtime_elevator_probe_not_loaded");
    expect(wrapper.text()).toContain("real realtime API");
    expect(wrapper.text()).toContain("robot ACK");
    expect(wrapper.text()).toContain("HIL/hardware safety");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/realtime-elevator-preview");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/realtime-elevator-probe");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/cloud-archive/tasks");

    const inputs = wrapper.findAll("input");
    expect(inputs).toHaveLength(10);
    await inputs[0]!.setValue("http://127.0.0.1:8088");
    await inputs[1]!.setValue("http://127.0.0.1:8088");
    await inputs[2]!.setValue("http://127.0.0.1:8088");
    await inputs[3]!.setValue("fixtures/archive.json");
    await inputs[5]!.setValue("fixtures/realtime.json");
    await inputs[6]!.setValue("fixtures/route.json");
    await inputs[7]!.setValue("fixtures/labeling.json");
    await inputs[8]!.setValue("fixtures/voice.json");
    await inputs[9]!.setValue("fixtures/safe-command.json");

    await wrapper.findAll("button").find((button) => button.text() === "Probe cloud operator console")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Probe cloud archive tasks")?.trigger("click");
    await flushPromises();

    await wrapper.findAll("button").find((button) => button.text() === "Probe realtime/elevator snapshot")?.trigger("click");
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
    expect(previewCalls).toContain("/api/o7/cloud-operator-console-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/cloud-archive/tasks-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/realtime-elevator-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A8088");
    expect(previewCalls).toContain("/api/o7/cloud-archive/tasks?archiveJson=fixtures%2Farchive.json");
    expect(previewCalls).toContain("/api/o7/realtime-elevator-preview?fixtureJson=fixtures%2Frealtime.json");
    expect(previewCalls).toContain("/api/o7/route-replay-preview?fixtureJson=fixtures%2Froute.json");
    expect(previewCalls).toContain("/api/o7/labeling-preview?fixtureJson=fixtures%2Flabeling.json");
    expect(previewCalls).toContain("/api/o7/voice-preview?fixtureJson=fixtures%2Fvoice.json");
    expect(previewCalls).toContain("/api/o7/safe-command-preview?fixtureJson=fixtures%2Fsafe-command.json");
    expect(wrapper.text()).toContain("trashbot.o7.realtime_elevator_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.route_replay_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.labeling_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.voice_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.safe_command_preview.v1");
    expect(wrapper.text()).toContain("trashbot.o7.cloud_archive_tasks.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1");
    expect(wrapper.text()).toContain("trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1");
    expect(wrapper.text()).toContain("trashbot.o7.realtime_elevator_snapshot.v1");
    expect(wrapper.text()).toContain("loaded_fail_closed_contract");
    expect(wrapper.text()).toContain("none_remote_contract_is_still_observe_only");
    expect(wrapper.text()).toContain("none_remote_contract_is_still_blocked_not_proven");
    expect(wrapper.text()).toContain("Dangerous true fields");
    expect(wrapper.text()).toContain("local loopback only");
    expect(wrapper.text()).toContain("Route membership false fields");
    expect(wrapper.text()).toContain("route_membership.in_elevator_zone=false");
    expect(wrapper.text()).toContain("task_archive_002");
    expect(wrapper.text()).toContain("needs_review_fixture_only");
    expect(wrapper.text()).toContain("fixture_inspector_ready");
    expect(wrapper.text()).toContain("Local route replay player");
    expect(wrapper.text()).toContain("local_fixture_cursor_only");
    expect(wrapper.text()).toContain("local_fixture_cursor_ready");
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
    await wrapper.findAll("button").find((button) => button.text() === "Reset cursor")?.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain("1 / 2");
    expect(mockedFetch.mock.calls).toHaveLength(callsBeforeLocalCursor);
    expect(wrapper.text()).toContain("Labeling queue inspector");
    expect(wrapper.text()).toContain("review_item_001");
    expect(wrapper.text()).toContain("frame_media_001.jpg");
    expect(wrapper.text()).toContain("floor_label");
    expect(wrapper.text()).toContain("draft_label_001.json");
    expect(wrapper.text()).toContain("operator_review_not_complete");
    expect(wrapper.text()).toContain("draft_labels.autosave_available=false");
    expect(wrapper.text()).toContain("dataset_export.available=false");
    expect(wrapper.text()).toContain("Voice ASR/TTS inspector");
    expect(wrapper.text()).toContain("ASR event sample");
    expect(wrapper.text()).toContain("请去三楼电梯口");
    expect(wrapper.text()).toContain("我会等待人工确认后再播报。");
    expect(wrapper.text()).toContain("speaker_ack_missing.json");
    expect(wrapper.text()).toContain("audio_input_not_checked");
    expect(wrapper.text()).toContain("speaker_dispatch.sends_to_robot=false");
    expect(wrapper.text()).toContain("real_asr_tts_runtime_connected=false");
    expect(wrapper.text()).toContain("Safe command inspector");
    expect(wrapper.text()).toContain("archive_command_session_002");
    expect(wrapper.text()).toContain("command_archive_001");
    expect(wrapper.text()).toContain("manual_turn_envelope.json");
    expect(wrapper.text()).toContain("navigate_goal_envelope.json");
    expect(wrapper.text()).toContain("idempotency_policy.json");
    expect(wrapper.text()).toContain("robot_ack_timeout_trace_missing");
    expect(wrapper.text()).toContain("cancel_ack_trace_missing");
    expect(wrapper.text()).toContain("stop_ack_trace_missing");
    expect(wrapper.text()).toContain("recovery_event_trace_missing");
    expect(wrapper.text()).toContain("keyboard_control_enabled=false");
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
});
