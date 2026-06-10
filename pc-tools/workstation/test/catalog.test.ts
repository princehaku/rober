import { describe, expect, it } from "vitest";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import {
  buildO7CloudArchiveTasksProbe,
  buildO7CloudArchiveTasks,
  buildO7LiveEndpointsManifest,
  buildO7ConsumerTaskDetail,
  buildO7ConsumerTaskList,
  buildO7CloudOperatorConsoleProbe,
  buildO7RealtimeElevatorProbe,
  buildO7RtcSignalingContractProbe,
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildRobotControlSummary,
  buildO7OperatorConsoleAcceptanceResponse,
  buildO7OperatorConsoleResponse,
  buildO7PreviewsAcceptanceResponse,
  buildO7FieldEvidenceConsumerIngest,
  buildO7LabelingPreview,
  buildO7RealtimeElevatorPreview,
  buildO7RouteReplayPreview,
  buildO7SafeCommandPreview,
  buildO7VoicePreview,
  buildProofBoundary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "../src/server/catalog";
import { createWorkstationApp } from "../src/server/index";

function sampleStatus(evidenceRef: string) {
  // 样例只提供 Node loader 生成 safe summary 所需字段，不模拟真实 Nav2 或现场成功。
  return {
    state: "waiting_visual_gate",
    route_contract_version: "fixed_route.v1",
    route_file: "/tmp/private/fixed_route.yaml",
    route_file_basename: "fixed_route.yaml",
    route_id: "fixed_route",
    checkpoint: 1,
    current_index: 1,
    total: 3,
    evidence_ref: evidenceRef,
    route_progress: {
      route_id: "fixed_route",
      route_file_basename: "fixed_route.yaml",
      checkpoint_id: "fixed_route:001",
      evidence_ref: evidenceRef,
      checkpoint: 1,
      current_index: 1,
      total_checkpoints: 3,
      target: { x: 1.2, y: 0.4, qw: 1.0 },
      route_contract_version: "fixed_route.v1",
      source: "fixed_route",
      failure_code: "CHECKPOINT_MISSING",
    },
    keyframe_preflight: {
      enabled: true,
      route_visual_ready: false,
      total_checkpoints: 3,
      loaded_keyframes: [{ index: 0 }],
      missing_keyframes: [{ index: 1, reason: "missing" }],
      invalid_keyframes: [],
    },
    visual_gate_status: "keyframe_preflight_failed",
    failure_code: "CHECKPOINT_MISSING",
    failure_reason: "missing keyframes",
    last_nav_result: "not_started",
  };
}

function sampleReconciliation(evidenceRef: string) {
  // reconciliation 只走软件证明白名单，且显式关闭交付成功和主动作。
  return {
    schema: "trashbot.elevator_route_evidence_reconciliation.v1",
    source: "software_proof",
    evidence_boundary: "software_proof_docker_elevator_route_evidence_reconciliation_gate",
    evidence_ref: evidenceRef,
    phone_safe_summary: {
      schema: "trashbot.elevator_route_evidence_reconciliation_summary.v1",
      source: "software_proof",
      evidence_boundary: "software_proof_docker_elevator_route_evidence_reconciliation_gate",
      status: "reconciled_not_proven",
      reconciliation_verdict: "reconciled_not_proven",
      same_evidence_ref_required: true,
      same_evidence_ref_status: "matched_same_evidence_ref",
      evidence_ref: evidenceRef,
      source_states: {
        elevator_status: "ready_for_operator_review_not_proven",
        route_completion_verdict: "completed_not_proven",
      },
      missing_materials_count: 0,
      mismatch_reasons_count: 0,
      operator_next_steps: ["Keep this as software proof only."],
      not_proven: ["real_elevator_door_state", "real_nav2_fixed_route_run", "delivery_success"],
      safe_copy: "Elevator-route reconciliation metadata only; delivery_success=false.",
      delivery_success: false,
      primary_actions_enabled: false,
    },
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function sampleRouteReplayFixture(evidenceRef: string) {
  // route replay fixture 只模拟本地安全 JSON，不代表 O6 云归档或真实机器人运动。
  return {
    schema: "trashbot.o7.route_replay_fixture.v1",
    task_id: "task-fixture-001",
    robot_id: "robot-fixture-01",
    route_id: "route-alpha",
    map_frame: "map",
    evidence_ref: evidenceRef,
    trajectory_frames: [
      {
        frame_index: 0,
        timestamp_ms: 1000,
        pose: { x_m: 1.1, y_m: 2.2, yaw_rad: 0.1 },
        velocity: { linear_mps: 0.2, angular_radps: 0.01 },
        state: "departed",
        evidence_ref: path.join(path.dirname(evidenceRef), "frame-000.jpg"),
      },
      {
        frame_index: 1,
        timestamp_ms: 1100,
        pose: { x_m: 1.2, y_m: 2.3, yaw_rad: 0.2 },
        velocity: { linear_mps: 0.3, angular_radps: 0.02 },
        state: "en_route",
        evidence_ref: "frame-001.jpg",
      },
      {
        frame_index: 2,
        timestamp_ms: 1200,
        pose: { x_m: 1.3, y_m: 2.4, yaw_rad: 0.3 },
        velocity: { linear_mps: 0.4, angular_radps: 0.03 },
        state: "observe",
        evidence_ref: "frame-002.jpg",
      },
      {
        frame_index: 3,
        timestamp_ms: 1300,
        pose: { x_m: 1.4, y_m: 2.5, yaw_rad: 0.4 },
        velocity: { linear_mps: 0.5, angular_radps: 0.04 },
        state: "extra_sample_not_returned",
        evidence_ref: "frame-003.jpg",
      },
    ],
    keyframe_refs: [
      path.join(path.dirname(evidenceRef), "keyframe-000.jpg"),
      "keyframe-001.jpg",
    ],
    state_transitions: [
      { from: "queued", to: "departed", timestamp_ms: 900, evidence_ref: "transition-queued.json" },
      { from_state: "departed", to_state: "en_route", timestamp_ms: 1000, evidence_ref: "transition-en-route.json" },
    ],
  };
}

function sampleLabelingFixture(evidenceRef: string) {
  // labeling fixture 只表达待标注队列和导出缺口，不模拟真实提交或训练集导出。
  return {
    schema: "trashbot.o7.labeling_fixture.v1",
    queue_id: "queue-fixture-001",
    evidence_ref: evidenceRef,
    review_items: [
      {
        item_id: "item-001",
        task_id: "task-001",
        frame_id: "frame-001",
        media_ref: path.join(path.dirname(evidenceRef), "frame-001.jpg"),
        evidence_ref: path.join(path.dirname(evidenceRef), "item-001.json"),
        current_labels: [
          { label_type: "elevator_door_state", value: "open", status: "fixture_existing", evidence_ref: "label-001.json" },
        ],
      },
      {
        item_id: "item-002",
        task_id: "task-001",
        frame_id: "frame-002",
        media_ref: "frame-002.jpg",
        evidence_ref: "item-002.json",
        current_labels: [],
      },
      {
        item_id: "item-003",
        task_id: "task-002",
        frame_id: "frame-003",
        media_ref: "frame-003.jpg",
        evidence_ref: "item-003.json",
        current_labels: [{ type: "obstacle_type", label: "box", status: "fixture_existing" }],
      },
      {
        item_id: "item-004",
        task_id: "task-002",
        frame_id: "frame-004",
        media_ref: "frame-004.jpg",
        evidence_ref: "item-004.json",
        current_labels: [],
      },
    ],
    label_schema: {
      schema_ref: "label-schema-o7-kr4.json",
      version: "fixture-v1",
      required_fields: ["label_type", "value", "evidence_ref"],
      allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref"],
    },
    allowed_label_types: ["elevator_door_state", "floor_label", "obstacle_type"],
    draft_labels: [
      { item_id: "item-001", label_type: "floor_label", value: "F3", status: "draft_slot", evidence_ref: "draft-001.json" },
      { item_id: "item-002", label_type: "obstacle_type", value: "cart", status: "draft_slot", evidence_ref: "draft-002.json" },
    ],
    dataset_export: {
      status: "blocked_not_available",
      export_ref: "dataset-export-missing.json",
      supported_formats: ["coco", "jsonl"],
      gaps: ["operator_review_not_complete"],
    },
  };
}

function sampleFieldEvidenceManifest(root: string, evidenceRef: string) {
  // manifest fixture 只表达现场材料 gate 和安全边界，不证明真实路线或交付成功。
  return {
    schema: "trashbot.field_evidence_manifest.v1",
    run_id: "field_evidence_20260609T101500Z",
    generated_at: "2026-06-09T10:15:00Z",
    source: "local_fixture",
    mode: "local",
    artifact_root: root,
    preflight_json: "preflight.json",
    preflight_status: "ready_for_live_route_capture_not_proven",
    preflight: {
      schema: "trashbot.field_route_preflight.v1",
      status: "ready_for_live_route_capture_not_proven",
      dry_run: false,
      blocked_reason: null,
      mode: "local",
      read_ok: true,
    },
    gate_pass: true,
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
    blocked_reason: "preflight_ready_not_delivery_proof",
    not_proven: true,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    artifacts: {
      map_yaml: {
        required: true,
        present: true,
        path: path.join(root, "map.yaml"),
        size_bytes: 24,
        mtime_utc: "2026-06-09T10:15:00Z",
        sha256: "map-sha",
        reason: null,
      },
      route_csv: {
        required: true,
        present: true,
        path: path.join(root, "route.csv"),
        size_bytes: 18,
        mtime_utc: "2026-06-09T10:15:00Z",
        sha256: "route-sha",
        reason: null,
      },
      keyframes: {
        required: true,
        present: true,
        path: path.join(root, "keyframes"),
        size_bytes: 128,
        mtime_utc: "2026-06-09T10:15:00Z",
        sha256: "keyframes-sha",
        reason: null,
        file_count: 2,
      },
      rosbag: {
        required: true,
        present: true,
        path: path.join(root, "route_bag"),
        size_bytes: 256,
        mtime_utc: "2026-06-09T10:15:00Z",
        sha256: "rosbag-sha",
        reason: null,
      },
      replay_jsonl: {
        required: true,
        present: true,
        path: evidenceRef,
        size_bytes: 96,
        mtime_utc: "2026-06-09T10:15:00Z",
        sha256: "replay-sha",
        reason: null,
      },
    },
  };
}

function sampleVoiceFixture(evidenceRef: string) {
  // voice fixture 只表达本地 ASR/TTS 槽位和缺口，不模拟真实语音 API、播放或 ACK 成功。
  return {
    schema: "trashbot.o7.voice_fixture.v1",
    session_id: "voice-session-001",
    evidence_ref: evidenceRef,
    asr_events: [
      {
        event_type: "partial",
        timestamp_ms: 1000,
        transcript: "去三楼",
        confidence: 0.61,
        evidence_ref: path.join(path.dirname(evidenceRef), "asr-partial-001.json"),
      },
      {
        event_type: "partial",
        timestamp_ms: 1200,
        transcript: "去三楼电梯口",
        confidence: 0.72,
        evidence_ref: "asr-partial-002.json",
      },
      {
        event_type: "final",
        timestamp_ms: 1500,
        transcript: "请去三楼电梯口",
        confidence: 0.88,
        evidence_ref: "asr-final-001.json",
      },
      {
        event_type: "partial",
        timestamp_ms: 1700,
        transcript: "下一句不会进入 sample",
        confidence: 0.55,
        evidence_ref: "asr-partial-003.json",
      },
    ],
    tts_draft: {
      text: "我会等待人工确认后再播报。",
      language: "zh-CN",
      voice_profile: "operator-default",
      evidence_ref: path.join(path.dirname(evidenceRef), "tts-draft.json"),
    },
    voice_profile: {
      name: "fallback-profile",
      language: "zh-CN",
    },
    speaker_ack: {
      ack_status: "not_proven",
      speaker_ack_ref: "speaker-ack-missing.json",
      failure_event_ref: "speaker-failure-missing.json",
      failure_refs: ["speaker-timeout.json", path.join(path.dirname(evidenceRef), "speaker-device-missing.json")],
    },
    media_preflight: {
      status: "blocked",
      gaps: ["audio_input_not_checked"],
    },
    audit_refs: ["voice-audit-001.json", path.join(path.dirname(evidenceRef), "voice-audit-002.json")],
  };
}

function sampleSafeCommandFixture(evidenceRef: string) {
  // safe command fixture 只表达手控/寻路 envelope 槽位，不模拟真实 command API 或机器人 ACK。
  return {
    schema: "trashbot.o7.safe_command_fixture.v1",
    command_session_id: "safe-command-session-001",
    evidence_ref: evidenceRef,
    manual_turn_envelope: {
      requested_direction: "left",
      evidence_ref: path.join(path.dirname(evidenceRef), "manual-turn-envelope.json"),
    },
    navigate_goal_envelope: {
      goal_source: "fixture_map_goal_slot",
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      evidence_ref: "navigate-goal-envelope.json",
    },
    velocity_limits: {
      max_linear_mps: 0.2,
      max_angular_radps: 0.4,
      source: "fixture_limit_not_hil",
    },
    steering_limits: {
      max_steering_angle_rad: 0.35,
      max_turn_rate_radps: 0.45,
      source: "fixture_limit_not_hil",
    },
    map_goal_slot: {
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      evidence_ref: path.join(path.dirname(evidenceRef), "map-goal-slot.json"),
    },
    idempotency_key_requirement: {
      key_ref: "idempotency-policy.json",
    },
    confirmation_policy: {
      status: "fixture_policy_summary_only",
    },
    robot_ack_status: {
      ack_status: "blocked_not_proven",
      last_command_id: "cmd-preview-001",
      ack_ref: "ack-missing.json",
      timeout_ms: 1500,
      cancel_ack_ref: "cancel-missing.json",
      stop_ack_ref: "stop-missing.json",
      recovery_ref: "recovery-missing.json",
    },
    evidence_gaps: ["operator_confirmation_ui_not_connected"],
    audit_refs: ["safe-command-audit-001.json", path.join(path.dirname(evidenceRef), "safe-command-audit-002.json")],
  };
}

function sampleCloudArchiveFixture(evidenceRef: string) {
  // cloud archive fixture 汇总 KR3-KR6 数据槽位，但仍只是本地只读 software proof。
  return {
    schema: "trashbot.o7.cloud_archive_fixture.v1",
    selected_task_id: "task-archive-002",
    tasks: [
      {
        task_id: "task-archive-001",
        robot_id: "robot-fixture-01",
        route_id: "route-alpha",
        status: "archived_fixture_only",
        started_at_ms: 1000,
        updated_at_ms: 1500,
        evidence_ref: path.join(path.dirname(evidenceRef), "task-archive-001.json"),
        trajectory_frames: [
          { evidence_ref: path.join(path.dirname(evidenceRef), "frame-001.jpg") },
          { evidence_ref: "frame-002.jpg" },
        ],
        events: [{ event_type: "departed" }, { state: "elevator_wait" }],
        labels: [{ label_type: "floor_label" }],
        asr_events: [{ event_type: "partial" }],
        tts_drafts: [{ text: "fixture" }],
        commands: [{ command_type: "navigate_goal" }],
      },
      {
        task_id: "task-archive-002",
        robot_id: "robot-fixture-01",
        route_id: "route-beta",
        status: "needs_review_fixture_only",
        started_at_ms: 2000,
        updated_at_ms: 2600,
        evidence_ref: evidenceRef,
        map_frame: "map",
        trajectory_frames: [
          {
            frame_index: 10,
            timestamp_ms: 2100,
            pose: { x_m: 1.25, y_m: -0.5, yaw_rad: 1.57 },
            velocity: { linear_mps: 0.12 },
            state: "departed",
            evidence_ref: path.join(path.dirname(evidenceRef), "frame-101.jpg"),
          },
          {
            frame_index: 11,
            timestamp_ms: 2200,
            x_m: 1.35,
            y_m: -0.45,
            yaw_rad: 1.6,
            speed_mps: 0.13,
            state: "elevator_wait",
            evidence_ref: "frame-102.jpg",
          },
          { frame_index: 12, timestamp_ms: 2300, x_m: 1.4, y_m: -0.4, yaw_rad: 1.62, speed_mps: 0.1, state: "sample_3", evidence_ref: "frame-103.jpg" },
          { frame_index: 13, timestamp_ms: 2400, x_m: 1.5, y_m: -0.3, yaw_rad: 1.7, speed_mps: 0.09, state: "sample_4", evidence_ref: "frame-104.jpg" },
          { frame_index: 14, timestamp_ms: 2500, x_m: 1.6, y_m: -0.2, yaw_rad: 1.8, speed_mps: 0.08, state: "sample_5", evidence_ref: "frame-105.jpg" },
          { frame_index: 15, timestamp_ms: 2600, x_m: 1.7, y_m: -0.1, yaw_rad: 1.9, speed_mps: 0.07, state: "sample_not_returned", evidence_ref: "frame-106.jpg" },
        ],
        events: [
          { event_type: "arrived_at_elevator", timestamp_ms: 2250, evidence_ref: path.join(path.dirname(evidenceRef), "event-001.json") },
          { state: "door_open_wait", timestamp_ms: 2350, evidence_ref: "event-002.json" },
        ],
        keyframe_refs: [
          path.join(path.dirname(evidenceRef), "keyframe-001.jpg"),
          "keyframe-002.jpg",
          "keyframe-003.jpg",
          "keyframe-004.jpg",
          "keyframe-005.jpg",
          "keyframe-not-returned.jpg",
        ],
        labels: [
          {
            item_id: "label-item-001",
            frame_id: "frame-101",
            media_ref: path.join(path.dirname(evidenceRef), "frame-101.jpg"),
            label_type: "floor_label",
            value: "F3",
            status: "fixture_existing",
            evidence_ref: path.join(path.dirname(evidenceRef), "label-001.json"),
          },
          { type: "obstacle_type", label: "box", status: "fixture_existing", evidence_ref: "label-002.json" },
        ],
        review_items: [
          {
            item_id: "review-001",
            task_id: "task-archive-002",
            frame_id: "frame-101",
            media_ref: path.join(path.dirname(evidenceRef), "frame-101.jpg"),
            evidence_ref: path.join(path.dirname(evidenceRef), "review-001.json"),
            current_labels: [
              { label_type: "elevator_door_state", value: "open", status: "fixture_existing", evidence_ref: "label-door.json" },
              { label_type: "floor_label", value: "F3", status: "fixture_existing", evidence_ref: "label-floor.json" },
              { label_type: "obstacle_type", value: "none", status: "fixture_existing", evidence_ref: "label-obstacle.json" },
              { label_type: "extra_not_returned", value: "ignored", status: "fixture_existing", evidence_ref: "label-extra.json" },
            ],
          },
          { item_id: "review-002", task_id: "task-archive-002", frame_id: "frame-102", media_ref: "frame-102.jpg", evidence_ref: "review-002.json", current_labels: [] },
          { item_id: "review-003", task_id: "task-archive-002", frame_id: "frame-103", media_ref: "frame-103.jpg", evidence_ref: "review-003.json", current_labels: [] },
          { item_id: "review-004", task_id: "task-archive-002", frame_id: "frame-104", media_ref: "frame-104.jpg", evidence_ref: "review-004.json", current_labels: [] },
          { item_id: "review-005", task_id: "task-archive-002", frame_id: "frame-105", media_ref: "frame-105.jpg", evidence_ref: "review-005.json", current_labels: [] },
          { item_id: "review-not-returned", task_id: "task-archive-002", frame_id: "frame-106", media_ref: "frame-106.jpg", evidence_ref: "review-006.json", current_labels: [] },
        ],
        label_schema: {
          schema_ref: path.join(path.dirname(evidenceRef), "label-schema.json"),
          version: "fixture-v2",
          required_fields: ["label_type", "value", "evidence_ref", "status", "reviewer", "extra_not_returned"],
          allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref", "extra_not_returned"],
        },
        allowed_label_types: ["elevator_door_state", "floor_label", "obstacle_type", "trash_type", "blocked_reason", "extra_not_returned"],
        draft_labels: [
          { label_type: "floor_label", value: "F3", status: "draft_fixture", evidence_ref: path.join(path.dirname(evidenceRef), "draft-001.json") },
          { label_type: "obstacle_type", value: "cart", status: "draft_fixture", evidence_ref: "draft-002.json" },
          { label_type: "trash_type", value: "paper", status: "draft_fixture", evidence_ref: "draft-003.json" },
          { label_type: "blocked_reason", value: "blurred", status: "draft_fixture", evidence_ref: "draft-004.json" },
          { label_type: "elevator_door_state", value: "closed", status: "draft_fixture", evidence_ref: "draft-005.json" },
          { label_type: "extra_not_returned", value: "ignored", status: "draft_fixture", evidence_ref: "draft-006.json" },
        ],
        dataset_export: {
          status: "blocked_not_available",
          export_ref: path.join(path.dirname(evidenceRef), "dataset-export.json"),
          supported_formats: ["jsonl", "coco", "yolo", "csv", "parquet", "extra_not_returned"],
          gaps: ["real_annotation_api_not_connected", "operator_review_not_complete", "training_split_not_defined", "extra_not_returned"],
        },
        voice_session: {
          session_id: "voice-session-archive-002",
          evidence_ref: path.join(path.dirname(evidenceRef), "voice-session.json"),
          audit_refs: ["voice-audit-001.json", path.join(path.dirname(evidenceRef), "voice-audit-002.json")],
        },
        asr_events: [
          {
            event_type: "partial",
            timestamp_ms: 2310,
            transcript: "请去 /tmp/private/raw-audio.wav",
            confidence: 0.51,
            evidence_ref: path.join(path.dirname(evidenceRef), "asr-partial-001.json"),
          },
          { event_type: "partial", timestamp_ms: 2320, transcript: "请去三楼", confidence: 0.64, evidence_ref: "asr-partial-002.json" },
          { event_type: "final", timestamp_ms: 2330, transcript: "请去三楼电梯口", confidence: 0.88, evidence_ref: "asr-final-001.json" },
          { event_type: "partial", timestamp_ms: 2340, transcript: "等待人工确认", confidence: 0.7, evidence_ref: "asr-partial-003.json" },
          { event_type: "noise", timestamp_ms: 2350, transcript: "环境音", confidence: 0.2, evidence_ref: "asr-noise-001.json" },
          { event_type: "partial", timestamp_ms: 2360, transcript: "不会进入 sample", confidence: 0.55, evidence_ref: "asr-not-returned.json" },
        ],
        tts_drafts: [
          {
            text: "我会等待人工确认后再播报 /tmp/private/tts.txt",
            language: "zh-CN",
            voice_profile: "operator-default",
            evidence_ref: path.join(path.dirname(evidenceRef), "tts-draft-001.json"),
          },
          { text: "draft two" },
        ],
        voice_profile: { name: "fallback-profile", language: "zh-CN" },
        speaker_ack: {
          ack_status: "not_proven",
          speaker_ack_ref: "speaker-ack-missing.json",
          failure_event_ref: path.join(path.dirname(evidenceRef), "speaker-failure.json"),
          failure_refs: [
            "speaker-timeout.json",
            path.join(path.dirname(evidenceRef), "speaker-device-missing.json"),
            "speaker-gap-003.json",
            "speaker-gap-004.json",
            "speaker-gap-005.json",
            "speaker-gap-not-returned.json",
          ],
        },
        media_preflight: {
          status: "blocked",
          dependency_ref: path.join(path.dirname(evidenceRef), "media-preflight.json"),
          gaps: ["audio_input_not_checked", "speaker_output_not_checked"],
        },
        command_session: {
          command_session_id: "archive-command-session-002",
          evidence_ref: path.join(path.dirname(evidenceRef), "command-session.json"),
          audit_refs: ["command-audit-001.json", path.join(path.dirname(evidenceRef), "command-audit-002.json")],
        },
        commands: [
          {
            command_id: "cmd-archive-001",
            kind: "manual_turn",
            status: "queued_fixture_only",
            envelope_ref: path.join(path.dirname(evidenceRef), "manual-turn-envelope.json"),
            idempotency_key_ref: "idem-manual-001.json",
            evidence_ref: "command-manual-001.json",
          },
          {
            command_id: "cmd-archive-002",
            command_type: "navigate_goal",
            status: "draft_fixture_only",
            envelope_ref: "navigate-goal-envelope.json",
            idempotency_key_ref: "idem-nav-001.json",
            evidence_ref: path.join(path.dirname(evidenceRef), "command-nav-001.json"),
          },
        ],
        manual_turn_envelope: {
          requested_direction: "left",
          evidence_ref: path.join(path.dirname(evidenceRef), "manual-turn-envelope.json"),
        },
        navigate_goal_envelope: {
          goal_source: "fixture_map_goal_slot",
          map_frame: "map",
          x_m: 1.25,
          y_m: -0.5,
          yaw_rad: 1.57,
          evidence_ref: "navigate-goal-envelope.json",
        },
        velocity_limits: {
          max_linear_mps: 0.2,
          max_angular_radps: 0.4,
          source: "fixture_limit_not_hil",
        },
        steering_limits: {
          max_steering_angle_rad: 0.35,
          max_turn_rate_radps: 0.45,
          source: "fixture_limit_not_hil",
        },
        map_goal_slot: {
          map_frame: "map",
          x_m: 1.25,
          y_m: -0.5,
          yaw_rad: 1.57,
          evidence_ref: path.join(path.dirname(evidenceRef), "map-goal-slot.json"),
        },
        idempotency_key_requirement: {
          key_ref: "idempotency-policy.json",
        },
        confirmation_policy: {
          status: "fixture_policy_summary_only",
        },
        command_ack: {
          ack_status: "blocked_not_proven",
          last_command_id: "cmd-archive-002",
          ack_ref: "ack-missing.json",
          timeout_ms: 1500,
          cancel_ack_ref: "cancel-missing.json",
          stop_ack_ref: "stop-missing.json",
          recovery_ref: "recovery-missing.json",
        },
        command_evidence_gaps: ["operator_confirmation_ui_not_connected"],
      },
    ],
  };
}

function listen(app: ReturnType<typeof createWorkstationApp>): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // HTTP endpoint 测试用真实 Express app，但只监听随机本地端口，不连接任何外部服务。
  const server = http.createServer(app);
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenJson(payload: unknown): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // probe 测试用最小本机 JSON 服务模拟 relay snapshot，不连接外网或真实机器人。
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    if (req.url === "/api/o7/realtime-elevator/snapshot") {
      res.end(JSON.stringify(payload));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ error: "not_found" }));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRobotApiReadback(payload: unknown): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // Robot Control 测试用任意 GET readback 服务；只返回 JSON，不实现 POST 或运动控制。
  const server = http.createServer((_req, res) => {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(payload));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenCloudArchive(payload: unknown): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // cloud archive probe 测试用本机 HTTP 服务，只返回给定 contract，不连接 relay、云或机器人。
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    if (req.url === "/api/o7/cloud-archive/tasks") {
      res.end(JSON.stringify(payload));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ error: "not_found" }));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenConsumerRead(listPayload: unknown, detailPayload: unknown): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // consumer read adapter 测试只模拟本机 O6 list/detail 合同，不连接真实 relay、云或机器人。
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    if (req.url === "/api/o6/consumer/tasks?view=summary&limit=50") {
      res.end(JSON.stringify(listPayload));
      return;
    }
    if (req.url?.startsWith("/api/o6/consumer/tasks/") && req.url.includes("?view=default&include=")) {
      res.end(JSON.stringify(detailPayload));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ error: "not_found" }));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRtcContract(payload: unknown): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // RTC contract probe 测试只模拟本机 relay 合同入口，不创建 WebRTC、视频或 ROS2 /tf 连接。
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    if (req.url === "/api/o7/rtc-signaling/contract") {
      res.end(JSON.stringify(payload));
      return;
    }
    res.statusCode = 404;
    res.end(JSON.stringify({ error: "not_found" }));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function sampleRealtimeElevatorFixture(evidenceRef: string) {
  // realtime/elevator fixture 只表达 PC 预览槽位，不模拟真实实时 API、ROS2 /tf 或电梯状态链。
  return {
    schema: "trashbot.o7.realtime_elevator_fixture.v1",
    session_id: "realtime-elevator-session-001",
    map_ref: path.join(path.dirname(evidenceRef), "map-alpha.yaml"),
    map_frame: "map",
    robot_pose: {
      x_m: 1.25,
      y_m: -0.75,
      yaw_rad: 1.57,
      pose_source: "fixture_pose_slot_not_tf",
    },
    pose_freshness: {
      timestamp_ms: 2000,
      age_ms: 350,
    },
    route_membership: {
      route_id: "route-alpha",
      on_route: false,
      in_elevator_zone: false,
      status: "fixture_request_only",
    },
    elevator_state_chain: [
      {
        state: "waiting",
        status: "fixture_summary_only",
        timestamp_ms: 1000,
        evidence_ref: path.join(path.dirname(evidenceRef), "elevator-waiting.json"),
      },
      {
        state: "entering",
        status: "fixture_summary_only",
        timestamp_ms: 1400,
        evidence_ref: "elevator-entering.json",
      },
      {
        state: "moving",
        status: "fixture_summary_only",
        timestamp_ms: 1800,
        evidence_ref: "elevator-moving.json",
      },
      {
        state: "exiting",
        status: "fixture_summary_only",
        timestamp_ms: 2200,
        evidence_ref: "elevator-exiting.json",
      },
      {
        state: "handoff",
        status: "fixture_summary_only",
        timestamp_ms: 2600,
        evidence_ref: "elevator-handoff.json",
      },
      {
        state: "extra_sample_not_returned",
        status: "fixture_summary_only",
        timestamp_ms: 3000,
        evidence_ref: "elevator-extra.json",
      },
    ],
    current_floor_evidence: {
      floor_label: "F2",
      confidence: 0.62,
      evidence_ref: path.join(path.dirname(evidenceRef), "current-floor.json"),
    },
    target_floor: {
      floor_label: "F3",
      confirmation_status: "operator_selected_not_proven",
      evidence_ref: "target-floor.json",
    },
    human_takeover: {
      reason: "fixture_requires_operator_review",
      operator_action: "confirm_target_floor_before_real_dispatch",
      evidence_ref: "human-takeover.json",
    },
    evidence_ref: evidenceRef,
    audit_refs: ["realtime-audit-001.json", path.join(path.dirname(evidenceRef), "realtime-audit-002.json")],
  };
}

function expectNoLegacyPythonGateSemantics(value: unknown, allowVendorSerialReference = false) {
  // 这些字符串代表旧 Python gate 执行入口，Node/Vue 工作站响应中不应再出现。
  const payload = JSON.stringify(value);
  expect(payload).not.toContain("route_debug_web.py");
  expect(payload).not.toContain("test_route_debug_web.py");
  expect(payload).not.toContain("python -m");
  expect(payload).not.toContain("python3 ");
  expect(payload).not.toContain("route_gate");
  expect(payload).not.toContain("workstation_executes_python_gate");
  expect(payload).not.toContain("/cmd_vel");
  if (!allowVendorSerialReference) {
    expect(payload).not.toContain("/dev/tty");
  }
  expect(payload).not.toContain("/dev/ttyUSB");
  expect(payload).not.toContain("/dev/ttyACM");
}

describe("workstation fail-closed API contracts", () => {
  it("health exposes software-proof fields only", () => {
    // health 在线不等于机器人在线，因此必须覆盖全部 fail-closed 字段。
    const health = buildHealth();

    expect(health.source).toBe("software_proof");
    expect(health.proof_status).toBe("not_proven");
    expect(health.safe_to_control).toBe(false);
    expect(health.delivery_success).toBe(false);
    expect(health.primary_actions_enabled).toBe(false);
    expect(health.pc_only).toBe(true);
  });

  it("indexes JSON fixtures without requiring Python files", async () => {
    // Evidence index 只能证明 JSON fixture 可读，不再依赖 .py 文件存在。
    const response = await buildEvidenceToolsResponse();

    expect(response.schema).toBe("trashbot.pc_tools_workstation.evidence_tools.v2");
    expect(response.fixture_root).toBe("pc-tools/evidence/fixtures");
    expect(response.total_asset_groups).toBeGreaterThan(0);
    expect(response.total_json_fixtures).toBeGreaterThan(0);
    expect(response.assets.some((asset) => asset.group === "wave_rover_hil_packet_intake")).toBe(true);
    expect(response.assets.every((asset) => asset.fixture_files.every((file) => file.endsWith(".json")))).toBe(true);
    expect(response.primary_actions_enabled).toBe(false);
    expectNoLegacyPythonGateSemantics(response);
  });

  it("summarizes WAVE ROVER material coverage without HIL pass claims", async () => {
    // Material coverage 扫描 log/jsonl/report 文件名，但所有顶层 proof flags 仍 fail-closed。
    const response = await buildHardwareMaterialsResponse();

    expect(response.schema).toBe("trashbot.pc_tools_workstation.hardware_materials.v1");
    expect(response.fixture_root).toBe("pc-tools/evidence/fixtures");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.hardware_claim_level).toBe("software_material_coverage");
    expect(response.vendor_sources).toEqual(
      expect.arrayContaining([
        { path: "docs/vendor/VENDOR_INDEX.md", fact_ids: expect.arrayContaining(["vendor_index_source_of_truth"]) },
        { path: "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py", fact_ids: expect.arrayContaining(["json_line_send"]) },
        { path: "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml", fact_ids: expect.arrayContaining(["cmd_config_movement_ids"]) },
        { path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", fact_ids: expect.arrayContaining(["cmd_id_definitions"]) },
        { path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h", fact_ids: expect.arrayContaining(["newline_json_dispatch"]) },
        { path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h", fact_ids: expect.arrayContaining(["t1001_feedback_fields"]) },
      ]),
    );
    expect(response.serial_reference).toEqual({
      vendor_rpi_default_device: "/dev/ttyAMA0",
      vendor_rpi_alternate_device: "/dev/serial0",
      baudrate: 115200,
      orange_pi_device_status: "not_proven",
    });
    expect(response.command_facts).toEqual(
      expect.arrayContaining([
        { t: 1, name: "CMD_SPEED_CTRL", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 11, name: "CMD_PWM_INPUT", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 13, name: "CMD_ROS_CTRL", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 130, name: "CMD_BASE_FEEDBACK", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 131, name: "CMD_BASE_FEEDBACK_FLOW", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 142, name: "CMD_FEEDBACK_FLOW_INTERVAL", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
        { t: 143, name: "CMD_UART_ECHO_MODE", source_path: "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", hardware_verified: false },
      ]),
    );
    expect(response.command_facts.every((fact) => fact.hardware_verified === false)).toBe(true);
    expect(response.feedback_schema.T1001.base_fields).toEqual(["L", "R", "r", "p", "y", "v"]);
    expect(response.feedback_schema.T1001.module_conditional_fields.join(" ")).toContain("moduleType=1");
    expect(response.feedback_schema.T1001.source_path).toBe("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h");
    expect(response.required_materials.map((material) => material.id)).toEqual([
      "feedback_T1001.log",
      "odom_once.jsonl",
      "imu_once.jsonl",
      "battery_once.jsonl",
      "operator_hil_report",
    ]);
    expect(response.fixture_groups).toEqual(response.groups);
    expect(response.fixture_groups.some((group) => group.group === "wave_rover_hil_packet_intake/pass")).toBe(true);
    const intakePass = response.fixture_groups.find((group) => group.group === "wave_rover_hil_packet_intake/pass");
    expect(intakePass?.present_materials).toContain("operator_hil_report");
    expect(intakePass?.coverage_counts.present).toBe(5);
    expect(intakePass?.status).toBe("material_coverage_complete_software_proof_only");
    expect(response.proof_status).toBe("not_proven");
    const replayPass = response.fixture_groups.find((group) => group.group === "wave_rover_feedback_replay/pass");
    expect(replayPass?.missing_materials).toContain("operator_hil_report");
    expect(replayPass?.status).toBe("material_coverage_partial_software_proof_only");
    expect(response.gaps).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          group: "wave_rover_feedback_replay/pass",
          missing_material: "operator_hil_report",
        }),
      ]),
    );
    expect(response.not_proven_boundaries).toEqual(
      expect.arrayContaining([
        "real_wave_rover_power_on_not_proven",
        "real_uart_link_not_proven",
        "real_hil_pass_not_proven",
        "lidar_tof_material_not_proven",
        "delivery_success_not_proven",
      ]),
    );
    expect(response.fail_closed_tokens).toEqual(
      expect.arrayContaining([
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
      ]),
    );
    expect(response.vendor_facts_bounded).toContain("UART newline-delimited JSON");
    expect(response.vendor_facts_bounded).toContain("json_cmd.h defines T=1/T=11/T=13/T=130/T=131/T=142/T=143 command IDs");
    expect(response.vendor_facts_bounded).toContain("ugv_advance.h baseInfoFeedback() assembles T=1001 fields L/R/r/p/y/v");
    expect(response.boundary_copy).toContain("coverage is not HIL pass");
    expect(JSON.stringify(response)).not.toContain("hardware_connected=true");
    expect(JSON.stringify(response)).not.toContain("hil_pass=true");
    expect(JSON.stringify(response)).not.toContain("hil_verified");
    expect(JSON.stringify(response)).not.toMatch(/hardware connected|ready to control/i);
    expect(JSON.stringify(response)).not.toContain("HIL pass true");
    expectNoLegacyPythonGateSemantics(response, true);
  });

  it("route debug summary uses Node JSON loader and fails closed without input", async () => {
    // 缺少 status JSON 时页面仍可用，但摘要必须保持 blocked/not_proven。
    const response = await buildRouteDebugSummary();

    expect(response.schema).toBe("trashbot.pc_tools_workstation.route_debug_summary.v2");
    expect(response.route_root).toBe("pc-tools/route");
    expect(response.node_route_json_loader.name).toBe("node_route_json_loader");
    expect(response.node_route_json_loader.executes_control).toBe(false);
    expect(response.route_console_summary.console_controls).toBe("read_only");
    expect(response.route_console_summary.failure.status).toBe("blocked_not_proven");
    expect(response.route_console_summary.failure.fail_closed_conditions).toContain("bad_json");
    expect(response.blocked_reasons).toContain("status_json_not_provided");
    expect(response.missing_fields).toContain("real_nav2_runtime");
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expectNoLegacyPythonGateSemantics(response);
  });

  it("loads sample status task and reconciliation JSON as safe summary", async () => {
    // 正常读取也只能得到 software_proof/not_proven，不能打开控制或交付成功。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-route-json-"));
    const evidenceRef = path.join(root, "same-evidence.json");
    const statusPath = path.join(root, "status.json");
    const taskDir = path.join(root, "tasks");
    const reconciliationPath = path.join(root, "reconciliation.json");
    await mkdir(taskDir);
    await writeFile(statusPath, JSON.stringify(sampleStatus(evidenceRef)), "utf8");
    await writeFile(path.join(taskDir, "wrong.json"), JSON.stringify({ evidence_ref: "/tmp/other" }), "utf8");
    await writeFile(path.join(taskDir, "match.json"), JSON.stringify({ task_id: "matched", route_progress: { evidence_ref: evidenceRef } }), "utf8");
    await writeFile(reconciliationPath, JSON.stringify(sampleReconciliation(evidenceRef)), "utf8");

    const response = await buildRouteDebugSummary({
      statusJson: statusPath,
      taskRecordDir: taskDir,
      elevatorRouteReconciliation: reconciliationPath,
    });

    expect(response.route_console_summary.route_progress?.checkpoint_id).toBe("fixed_route:001");
    expect(response.route_console_summary.keyframe_preflight?.visual_gate_status).toBe("keyframe_preflight_failed");
    expect(response.route_console_summary.recent_task?.task_id).toBe("matched");
    expect(response.route_console_summary.route_elevator_reconciliation.lookup_status).toBe("found");
    expect(response.route_console_summary.route_elevator_reconciliation.source_ref).toBe("file:reconciliation.json");
    expect(response.route_console_summary.delivery_success).toBe(false);
    expect(response.route_console_summary.primary_actions_enabled).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(JSON.stringify(response)).not.toContain(root);
    expectNoLegacyPythonGateSemantics(response);
  });

  it("bad JSON fails closed without success claims", async () => {
    // 坏 JSON 不能让 API 500，也不能让 UI 推断 route 可用。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-route-bad-json-"));
    const statusPath = path.join(root, "bad.json");
    await writeFile(statusPath, "{not json", "utf8");

    const response = await buildRouteDebugSummary({ statusJson: statusPath });

    expect(response.route_console_summary.failure.status).toBe("blocked_not_proven");
    expect(response.blocked_reasons).toContain("status_json_read_error");
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expectNoLegacyPythonGateSemantics(response);
  });

  it("rejects unsafe copy success or control claims and evidence mismatch", async () => {
    // 输入夹带控制、成功或错配 evidence_ref 时只能返回 blocked 摘要。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-route-blocked-"));
    const statusPath = path.join(root, "status.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const mismatchPath = path.join(root, "mismatch.json");
    const controlTaskPath = path.join(root, "task.json");
    await writeFile(statusPath, JSON.stringify(sampleStatus("expected-ref")), "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.wrong.v1" }), "utf8");
    const unsafe = sampleReconciliation("expected-ref");
    unsafe.phone_safe_summary.operator_next_steps = ["Read /dev/ttyUSB0 then publish forbidden topic"];
    await writeFile(unsafePath, JSON.stringify(unsafe), "utf8");
    const success = sampleReconciliation("other-ref");
    success.phone_safe_summary.safe_copy = "delivery success completed";
    await writeFile(successPath, JSON.stringify(success), "utf8");
    await writeFile(mismatchPath, JSON.stringify(sampleReconciliation("other-ref")), "utf8");
    await writeFile(controlTaskPath, JSON.stringify({ task_id: "bad", primary_actions_enabled: true }), "utf8");

    const unsafeResponse = await buildRouteDebugSummary({ statusJson: statusPath, elevatorRouteReconciliation: unsafePath });
    const successResponse = await buildRouteDebugSummary({ statusJson: statusPath, elevatorRouteReconciliation: successPath });
    const unsupportedResponse = await buildRouteDebugSummary({ statusJson: statusPath, elevatorRouteReconciliation: unsupportedPath });
    const mismatchResponse = await buildRouteDebugSummary({ statusJson: statusPath, elevatorRouteReconciliation: mismatchPath });
    const controlResponse = await buildRouteDebugSummary({ statusJson: statusPath, taskRecord: controlTaskPath });

    expect(unsafeResponse.route_console_summary.route_elevator_reconciliation.lookup_status).toBe("unsafe_copy");
    expect(successResponse.route_console_summary.route_elevator_reconciliation.lookup_status).toBe("success_claim");
    expect(unsupportedResponse.route_console_summary.route_elevator_reconciliation.lookup_status).toBe("unsupported_schema");
    expect(mismatchResponse.route_console_summary.route_elevator_reconciliation.lookup_status).toBe("evidence_ref_mismatch");
    expect(controlResponse.route_console_summary.failure.blocked_reasons).toContain("task_record_control_claim");
    expect(successResponse.delivery_success).toBe(false);
    expect(successResponse.primary_actions_enabled).toBe(false);
    expectNoLegacyPythonGateSemantics(unsafeResponse);
    expectNoLegacyPythonGateSemantics(successResponse);
  });

  it("training and labeling empty workspaces fail closed", async () => {
    // 空目录必须展示 empty_not_connected，不能伪造成可训练或可标注。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-empty-assets-"));
    const trainingRoot = path.join(root, "training");
    const labelingRoot = path.join(root, "labeling");
    await mkdir(trainingRoot);
    await mkdir(labelingRoot);

    const training = await buildTrainingLabelingResponse({ trainingRoot, labelingRoot });

    expect(training.schema).toBe("trashbot.pc_tools_workstation.training_labeling.v2");
    expect(training.real_pipeline_connected).toBe(false);
    expect(training.proof_status).toBe("not_proven");
    expect(training.primary_actions_enabled).toBe(false);
    expect(training.workspaces).toHaveLength(2);
    expect(training.workspaces.every((workspace) => workspace.status === "empty_not_connected")).toBe(true);
    expect(training.workspaces.every((workspace) => workspace.asset_counts.total_assets === 0)).toBe(true);
    expect(training.missing_requirements).toEqual(
      expect.arrayContaining(["asset_files", "manifest_candidate", "image_files", "annotation_files", "real_pipeline_connection"]),
    );
    expectNoLegacyPythonGateSemantics(training);
  });

  it("training and labeling fixture inventory counts manifests images and annotations", async () => {
    // 临时 fixture 只验证本地资产扫描计数，不读取内容、不写输出、不接真实流水线。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-assets-"));
    const trainingRoot = path.join(root, "training");
    const labelingRoot = path.join(root, "labeling");
    await mkdir(path.join(trainingRoot, "images"), { recursive: true });
    await mkdir(path.join(labelingRoot, "labels"), { recursive: true });
    await writeFile(path.join(trainingRoot, "dataset_manifest.yaml"), "name: sample\n", "utf8");
    await writeFile(path.join(trainingRoot, "images", "frame001.jpg"), "", "utf8");
    await writeFile(path.join(trainingRoot, "labels.json"), "[]", "utf8");
    await writeFile(path.join(trainingRoot, "legacy.py"), "print('ignored')\n", "utf8");
    await writeFile(path.join(labelingRoot, "annotations.jsonl"), "{}\n", "utf8");
    await writeFile(path.join(labelingRoot, "labels", "frame001.txt"), "0 0.5 0.5 0.1 0.1\n", "utf8");
    await writeFile(path.join(labelingRoot, "frame001.png"), "", "utf8");

    const response = await buildTrainingLabelingResponse({ trainingRoot, labelingRoot });
    const dataset = response.workspaces.find((workspace) => workspace.name === "dataset");
    const labeling = response.workspaces.find((workspace) => workspace.name === "labeling");

    expect(dataset?.status).toBe("assets_present_not_connected");
    expect(dataset?.asset_counts).toMatchObject({
      total_assets: 3,
      structured_files: 2,
      manifest_candidates: 2,
      images: 1,
      annotations: 1,
      ignored_python_files: 1,
    });
    expect(labeling?.status).toBe("assets_present_not_connected");
    expect(labeling?.asset_counts).toMatchObject({
      total_assets: 3,
      structured_files: 1,
      manifest_candidates: 1,
      images: 1,
      annotations: 2,
      ignored_python_files: 0,
    });
    expect(response.real_pipeline_connected).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(JSON.stringify(response)).not.toContain("legacy.py");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("training and proof boundary do not claim real pipelines", async () => {
    // 资产入口必须明确未接真实训练/标注流水线。
    const training = await buildTrainingLabelingResponse();
    const boundary = buildProofBoundary();

    expect(training.real_pipeline_connected).toBe(false);
    expect(training.workspaces.every((workspace) => workspace.real_pipeline_connected === false)).toBe(true);
    expect(training.workspaces.every((workspace) => workspace.status.endsWith("_not_connected"))).toBe(true);
    expect(boundary.not_proven).toContain("real_training_or_labeling_pipeline");
    expect(boundary.control_policy.workstation_executes_control).toBe(false);
    expect(boundary.control_policy.route_loader_mode).toBe("local_json_readonly");
    expectNoLegacyPythonGateSemantics(training);
    expectNoLegacyPythonGateSemantics(boundary);
  });

  it("O7 operator console exposes six cloud-contract driven KR views without dispatch", () => {
    // O7 console 只证明契约视图可渲染，不证明实时流、语音、手控或寻路可用。
    const response = buildO7OperatorConsoleResponse();

    expect(response.schema).toBe("trashbot.o7.operator_console.v1");
    expect(response.contract_source).toBe("cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py");
    expect(response.cloud_api_status).toBe("draft_blocked_not_proven");
    expect(response.operator_mode).toBe("observe_only");
    expect(response.robot_connection).toBe("not_connected_by_pc");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.manual_control_policy.pc_direct_robot_connection).toBe(false);
    expect(response.manual_control_policy.cloud_mediated_only).toBe(true);
    expect(response.manual_control_policy.command_dispatch_enabled).toBe(false);
    expect(response.board_media_preflight_required).toBe(true);
    expect(response.board_media_preflight_schema).toBe("trashbot.o7_board_media_preflight.v1");
    expect(response.board_media_preflight_state).toBe("blocked");
    expect(response.board_media_preflight_summary.safe_to_control).toBe(false);
    expect(response.board_media_preflight_summary.primary_actions_enabled).toBe(false);
    expect(response.board_media_preflight_summary.device_probe_attempted).toBe(false);
    expect(response.board_media_preflight_summary.blocked_reasons).toContain("board_media_preflight_not_collected_by_pc");
    expect(response.board_media_preflight_summary.not_proven).toEqual(
      expect.arrayContaining([
        "real_rtc_session",
        "real_camera_video_source",
        "real_audio_capture",
        "real_audio_playback",
        "real_asr_stream",
        "real_tts_playback",
      ]),
    );
    expect(response.board_media_preflight_summary.next_required_evidence).toContain(
      "on_robot_media_smoke_with_no_chassis_motion",
    );
    expect(response.realtime_map_snapshot.schema).toBe("trashbot.o7.realtime_map_snapshot.v1");
    expect(response.realtime_map_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.realtime_map_snapshot.map_ref.status).toBe("not_proven");
    expect(response.realtime_map_snapshot.map_frame.status).toBe("contract_placeholder_not_tf");
    expect(response.realtime_map_snapshot.pose_freshness.latency_lt_2s_proven).toBe(false);
    expect(response.realtime_map_snapshot.route_membership.on_route).toBe(false);
    expect(response.realtime_map_snapshot.route_membership.in_elevator_zone).toBe(false);
    expect(response.realtime_map_snapshot.blocked_reasons).toContain("ros2_tf_forwarding_not_proven");
    expect(response.realtime_map_snapshot.not_proven).toContain("robot_position_latency_lt_2s");
    expect(response.elevator_state_snapshot.schema).toBe("trashbot.o7.elevator_state_snapshot.v1");
    expect(response.elevator_state_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.elevator_state_snapshot.current_state).toBe("not_connected");
    expect(response.elevator_state_snapshot.current_floor_evidence.status).toBe("not_proven");
    expect(response.elevator_state_snapshot.target_floor.confirmation_status).toBe("not_proven");
    expect(response.elevator_state_snapshot.human_takeover.required).toBe(true);
    expect(response.elevator_state_snapshot.human_takeover.reason).toBe("real_elevator_state_chain_not_proven");
    expect(response.elevator_state_snapshot.blocked_reasons).toContain("floor_recognition_not_proven");
    expect(response.elevator_state_snapshot.not_proven).toContain("real_human_takeover_reason");
    expect(response.route_replay_snapshot.schema).toBe("trashbot.o7.route_replay_snapshot.v1");
    expect(response.route_replay_snapshot.source).toBe("software_proof");
    expect(response.route_replay_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.route_replay_snapshot.safe_to_control).toBe(false);
    expect(response.route_replay_snapshot.primary_actions_enabled).toBe(false);
    expect(response.route_replay_snapshot.playback_available).toBe(false);
    expect(response.route_replay_snapshot.real_archive_connected).toBe(false);
    expect(response.route_replay_snapshot.task_selector.source_contract).toBe("history.route_replay.v1");
    expect(response.route_replay_snapshot.task_selector.status).toBe("blocked_no_cloud_task_archive");
    expect(response.route_replay_snapshot.task_selector.available_task_count).toBe(0);
    expect(response.route_replay_snapshot.task_selector.selected_task_id).toBe("not_connected");
    expect(response.route_replay_snapshot.selected_task.status).toBe("not_proven");
    expect(response.route_replay_snapshot.selected_task.evidence_ref).toBe("missing_selected_task_record");
    expect(response.route_replay_snapshot.trajectory.frame_count).toBe(0);
    expect(response.route_replay_snapshot.trajectory.sample_frames).toEqual([]);
    expect(response.route_replay_snapshot.playback_cursor.status).toBe("blocked_not_available");
    expect(response.route_replay_snapshot.keyframes.status).toBe("blocked_no_keyframe_archive");
    expect(response.route_replay_snapshot.evidence_refs.task_archive).toBe("missing_o6_cloud_task_archive");
    expect(response.route_replay_snapshot.evidence_refs.keyframe_archive).toBe("missing_keyframe_archive");
    expect(response.route_replay_snapshot.state_transitions.gaps).toContain("state_transition_timeline_not_backfilled");
    expect(response.route_replay_snapshot.blocked_reasons).toContain("o6_cloud_task_archive_not_connected");
    expect(response.route_replay_snapshot.not_proven).toContain("real_trajectory_frames");
    expect(response.route_replay_snapshot.next_required_evidence).toContain("o6_cloud_task_archive_query_contract");
    expect(response.labeling_queue_snapshot.schema).toBe("trashbot.o7.labeling_queue_snapshot.v1");
    expect(response.labeling_queue_snapshot.source).toBe("software_proof");
    expect(response.labeling_queue_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.labeling_queue_snapshot.safe_to_control).toBe(false);
    expect(response.labeling_queue_snapshot.primary_actions_enabled).toBe(false);
    expect(response.labeling_queue_snapshot.submit_enabled).toBe(false);
    expect(response.labeling_queue_snapshot.rollback_enabled).toBe(false);
    expect(response.labeling_queue_snapshot.real_annotation_api_connected).toBe(false);
    expect(response.labeling_queue_snapshot.dataset_export_available).toBe(false);
    expect(response.labeling_queue_snapshot.review_queue.source_contract).toBe("labeling.review_queue.v1");
    expect(response.labeling_queue_snapshot.review_queue.status).toBe("blocked_no_annotation_api");
    expect(response.labeling_queue_snapshot.review_queue.available_item_count).toBe(0);
    expect(response.labeling_queue_snapshot.selected_item.media_ref).toBe("missing_review_item_media_ref");
    expect(response.labeling_queue_snapshot.selected_item.status).toBe("not_proven");
    expect(response.labeling_queue_snapshot.label_schema.status).toBe("blocked_no_label_schema_api");
    expect(response.labeling_queue_snapshot.allowed_label_types.map((labelType) => labelType.type)).toEqual([
      "elevator_door_state",
      "floor_label",
      "obstacle_type",
    ]);
    expect(response.labeling_queue_snapshot.draft_labels.count).toBe(0);
    expect(response.labeling_queue_snapshot.draft_labels.autosave_available).toBe(false);
    expect(response.labeling_queue_snapshot.submit_audit.audit_ref).toBe("missing_submit_audit_log");
    expect(response.labeling_queue_snapshot.rollback_audit.audit_ref).toBe("missing_rollback_audit_log");
    expect(response.labeling_queue_snapshot.dataset_export.export_ref).toBe("missing_training_dataset_export");
    expect(response.labeling_queue_snapshot.dataset_export.gaps).toContain("dataset_manifest_export_not_available");
    expect(response.labeling_queue_snapshot.blocked_reasons).toContain("o6_annotation_api_not_connected");
    expect(response.labeling_queue_snapshot.not_proven).toContain("real_training_dataset_export");
    expect(response.labeling_queue_snapshot.next_required_evidence).toContain("dataset_export_manifest_contract");
    expect(response.voice_asr_tts_snapshot.schema).toBe("trashbot.o7.voice_asr_tts_snapshot.v1");
    expect(response.voice_asr_tts_snapshot.source).toBe("software_proof");
    expect(response.voice_asr_tts_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.voice_asr_tts_snapshot.safe_to_control).toBe(false);
    expect(response.voice_asr_tts_snapshot.primary_actions_enabled).toBe(false);
    expect(response.voice_asr_tts_snapshot.asr_stream_connected).toBe(false);
    expect(response.voice_asr_tts_snapshot.tts_send_enabled).toBe(false);
    expect(response.voice_asr_tts_snapshot.speaker_dispatch_enabled).toBe(false);
    expect(response.voice_asr_tts_snapshot.real_voice_api_connected).toBe(false);
    expect(response.voice_asr_tts_snapshot.real_asr_tts_runtime_connected).toBe(false);
    expect(response.voice_asr_tts_snapshot.media_preflight_dependency.status).toBe("blocked");
    expect(response.voice_asr_tts_snapshot.asr_stream.status).toBe("blocked_no_voice_api");
    expect(response.voice_asr_tts_snapshot.asr_stream.partial_slot.evidence_ref).toBe(
      "missing_asr_partial_transcript_trace",
    );
    expect(response.voice_asr_tts_snapshot.asr_stream.final_slot.evidence_ref).toBe(
      "missing_asr_final_transcript_trace",
    );
    expect(response.voice_asr_tts_snapshot.tts_draft.status).toBe("draft_disabled");
    expect(response.voice_asr_tts_snapshot.tts_draft.voice_profile).toBe("not_connected");
    expect(response.voice_asr_tts_snapshot.speaker_dispatch.sends_to_robot).toBe(false);
    expect(response.voice_asr_tts_snapshot.command_ack_audit.ack_status).toBe("blocked_no_ack_contract");
    expect(response.voice_asr_tts_snapshot.command_ack_audit.audit_ref).toBe("missing_voice_command_audit_log");
    expect(response.voice_asr_tts_snapshot.command_ack_audit.speaker_ack_ref).toBe("missing_speaker_dispatch_ack");
    expect(response.voice_asr_tts_snapshot.blocked_reasons).toContain("voice_api_not_connected");
    expect(response.voice_asr_tts_snapshot.not_proven).toContain("real_asr_partial_transcript");
    expect(response.voice_asr_tts_snapshot.not_proven).toContain("real_speaker_dispatch_ack");
    expect(response.voice_asr_tts_snapshot.next_required_evidence).toContain("voice_asr_tts_cloud_api_contract");
    expect(response.safe_command_snapshot.schema).toBe("trashbot.o7.safe_command_snapshot.v1");
    expect(response.safe_command_snapshot.source).toBe("software_proof");
    expect(response.safe_command_snapshot.snapshot_status).toBe("blocked_not_proven");
    expect(response.safe_command_snapshot.safe_to_control).toBe(false);
    expect(response.safe_command_snapshot.primary_actions_enabled).toBe(false);
    expect(response.safe_command_snapshot.command_dispatch_enabled).toBe(false);
    expect(response.safe_command_snapshot.manual_control_enabled).toBe(false);
    expect(response.safe_command_snapshot.navigate_goal_enabled).toBe(false);
    expect(response.safe_command_snapshot.keyboard_control_enabled).toBe(false);
    expect(response.safe_command_snapshot.real_command_api_connected).toBe(false);
    expect(response.safe_command_snapshot.real_robot_ack_connected).toBe(false);
    expect(response.safe_command_snapshot.manual_turn_envelope.sends_to_robot).toBe(false);
    expect(response.safe_command_snapshot.manual_turn_envelope.accepted_input_slots).toContain(
      "keyboard_arrow_keys_disabled",
    );
    expect(response.safe_command_snapshot.velocity_limits.hardware_verified).toBe(false);
    expect(response.safe_command_snapshot.velocity_limits.status).toBe("blocked_no_robot_hil_limits");
    expect(response.safe_command_snapshot.steering_limits.hardware_verified).toBe(false);
    expect(response.safe_command_snapshot.navigate_goal_envelope.goal_source).toBe("map_click_disabled");
    expect(response.safe_command_snapshot.map_goal_slot.status).toBe("empty_not_connected");
    expect(response.safe_command_snapshot.cloud_command_endpoint.status).toBe("future_disabled");
    expect(response.safe_command_snapshot.cloud_command_endpoint.sends_to_robot).toBe(false);
    expect(response.safe_command_snapshot.idempotency_key_requirement.required).toBe(true);
    expect(response.safe_command_snapshot.idempotency_key_requirement.header).toBe("Idempotency-Key");
    expect(response.safe_command_snapshot.confirmation_policy.manual_turn_requires_confirmation).toBe(true);
    expect(response.safe_command_snapshot.confirmation_policy.navigate_goal_requires_confirmation).toBe(true);
    expect(response.safe_command_snapshot.robot_ack_status.ack_status).toBe("blocked_no_robot_ack_contract");
    expect(response.safe_command_snapshot.robot_ack_status.ack_ref).toBe("missing_robot_command_ack");
    expect(response.safe_command_snapshot.evidence_gaps.timeout).toBe("missing_command_timeout_policy_and_trace");
    expect(response.safe_command_snapshot.evidence_gaps.cancel).toBe("missing_cancel_command_ack_trace");
    expect(response.safe_command_snapshot.evidence_gaps.stop).toBe("missing_stop_command_ack_trace");
    expect(response.safe_command_snapshot.evidence_gaps.recovery).toBe("missing_robot_recovery_event_trace");
    expect(response.safe_command_snapshot.blocked_reasons).toContain("safe_command_api_not_connected");
    expect(response.safe_command_snapshot.blocked_reasons).toContain(
      "robot_ack_timeout_cancel_stop_recovery_not_proven",
    );
    expect(response.safe_command_snapshot.not_proven).toContain("real_manual_turn_control");
    expect(response.safe_command_snapshot.not_proven).toContain("real_navigate_goal_dispatch");
    expect(response.safe_command_snapshot.not_proven).toContain("real_timeout_cancel_stop_recovery");
    expect(response.safe_command_snapshot.next_required_evidence).toContain(
      "cloud_safe_command_api_contract_with_bearer_auth",
    );
    expect(response.safe_command_snapshot.next_required_evidence).toContain("cancel_stop_recovery_ack_trace");
    expect(response.kr_views.map((kr) => kr.id)).toEqual(["O7-KR1", "O7-KR2", "O7-KR3", "O7-KR4", "O7-KR5", "O7-KR6"]);
    expect(response.kr_views.every((kr) => ["draft", "blocked", "not_proven"].includes(kr.status))).toBe(true);
    expect(response.command_previews.every((command) => command.sends_to_robot === false)).toBe(true);
    expect(response.command_previews.every((command) => command.requires_confirmation === true)).toBe(true);
    expect(response.blocked_reasons).toContain("pc_must_not_direct_connect_robot");
    expect(response.blocked_reasons).toContain("route_replay_snapshot_blocked");
    expect(response.blocked_reasons).toContain("labeling_queue_snapshot_blocked");
    expect(response.blocked_reasons).toContain("voice_asr_tts_snapshot_blocked");
    expect(response.blocked_reasons).toContain("safe_command_snapshot_blocked");
    expect(response.blocked_reasons).toContain("o6_annotation_api_not_connected");
    expect(response.not_proven).toContain("real_voice_api_connected");
    expect(response.not_proven).toContain("real_asr_partial_transcript");
    expect(response.not_proven).toContain("real_keyboard_control");
    expect(response.not_proven).toContain("real_robot_command_ack");
    expect(response.not_proven).toContain("real_operator_safe_command_dispatch");
    expect(response.not_proven).toContain("real_route_replay_trajectory_frames");
    expect(response.not_proven).toContain("real_annotation_rollback");
    expect(response.not_proven).toContain("real_training_dataset_export");
    expect(JSON.stringify(response)).not.toContain("delivery_success=true");
    expect(JSON.stringify(response)).not.toContain("playback_available=true");
    expect(JSON.stringify(response)).not.toContain("real_archive_connected=true");
    expect(JSON.stringify(response)).not.toContain("submit_enabled=true");
    expect(JSON.stringify(response)).not.toContain("rollback_enabled=true");
    expect(JSON.stringify(response)).not.toContain("real_annotation_api_connected=true");
    expect(JSON.stringify(response)).not.toContain("dataset_export_available=true");
    expect(JSON.stringify(response)).not.toContain("asr_stream_connected=true");
    expect(JSON.stringify(response)).not.toContain("tts_send_enabled=true");
    expect(JSON.stringify(response)).not.toContain("speaker_dispatch_enabled=true");
    expect(JSON.stringify(response)).not.toContain("real_voice_api_connected=true");
    expect(JSON.stringify(response)).not.toContain("real_asr_tts_runtime_connected=true");
    expect(JSON.stringify(response)).not.toContain("manual_control_enabled=true");
    expect(JSON.stringify(response)).not.toContain("navigate_goal_enabled=true");
    expect(JSON.stringify(response)).not.toContain("keyboard_control_enabled=true");
    expect(JSON.stringify(response)).not.toContain("real_command_api_connected=true");
    expect(JSON.stringify(response)).not.toContain("real_robot_ack_connected=true");
    expect(JSON.stringify(response)).not.toContain("success_claim_allowed=true");
    expect(JSON.stringify(response)).not.toContain("command_dispatch_enabled=true");
    expect(JSON.stringify(response)).not.toContain("/cmd_vel");
    expect(JSON.stringify(response)).not.toContain("/dev/ttyUSB");
    expect(JSON.stringify(response)).not.toMatch(/ready[_ ]?to[_ ]?control/i);
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 realtime elevator preview summarizes a safe local fixture without realtime tf elevator or control claims", async () => {
    // KR1/KR2 preview 只把本地 map/pose/elevator 槽位压成摘要，真实实时链路仍全部关闭。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-realtime-elevator-"));
    const evidenceRef = path.join(root, "realtime-elevator-evidence.json");
    const fixturePath = path.join(root, "realtime-elevator-fixture.json");
    await writeFile(fixturePath, JSON.stringify(sampleRealtimeElevatorFixture(evidenceRef)), "utf8");

    const response = await buildO7RealtimeElevatorPreview({ fixtureJson: fixturePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.realtime_elevator_preview.v1");
    expect(response.preview_status).toBe("fixture_preview_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.fixture_json).toBe("file:realtime-elevator-fixture.json");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.real_realtime_api_connected).toBe(false);
    expect(response.real_ros2_tf_connected).toBe(false);
    expect(response.real_elevator_state_chain_connected).toBe(false);
    expect(response.latency_lt_2s_proven).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.source_fixture_schema).toBe("trashbot.o7.realtime_elevator_fixture.v1");
    expect(response.session).toEqual({
      session_id: "realtime-elevator-session-001",
      source: "local_json_fixture",
      evidence_ref: "file:realtime-elevator-evidence.json",
      audit_refs: ["realtime-audit-001.json", "file:realtime-audit-002.json"],
      status: "fixture_summary_only",
    });
    expect(response.map_summary).toEqual({
      map_ref: "file:map-alpha.yaml",
      map_frame: "map",
      source: "local_json_fixture",
      status: "fixture_summary_only",
    });
    expect(response.robot_pose_summary).toEqual({
      x_m: 1.25,
      y_m: -0.75,
      yaw_rad: 1.57,
      pose_source: "fixture_pose_slot_not_tf",
      status: "fixture_summary_only",
    });
    expect(response.pose_freshness_summary).toEqual({
      timestamp_ms: 2000,
      age_ms: 350,
      latency_lt_2s_proven: false,
      status: "fixture_summary_only",
    });
    expect(response.route_membership_summary).toMatchObject({
      route_id: "route-alpha",
      requested_status: "fixture_request_only",
      requested_on_route: "requested_false_not_proven",
      requested_in_elevator_zone: "requested_false_not_proven",
      on_route: false,
      in_elevator_zone: false,
      status: "blocked_not_proven",
    });
    expect(response.elevator_state_chain_summary.count).toBe(6);
    expect(response.elevator_state_chain_summary.sample_limit).toBe(5);
    expect(response.elevator_state_chain_summary.sample).toHaveLength(5);
    expect(response.elevator_state_chain_summary.sample[0]).toEqual({
      state: "waiting",
      status: "fixture_summary_only",
      timestamp_ms: 1000,
      evidence_ref: "file:elevator-waiting.json",
    });
    expect(response.current_floor_evidence_summary).toEqual({
      floor_label: "F2",
      confidence: 0.62,
      evidence_ref: "file:current-floor.json",
      status: "fixture_summary_only",
    });
    expect(response.target_floor_summary).toEqual({
      floor_label: "F3",
      confirmation_status: "operator_selected_not_proven",
      evidence_ref: "target-floor.json",
      status: "fixture_summary_only",
    });
    expect(response.human_takeover_summary).toEqual({
      required: true,
      reason: "fixture_requires_operator_review",
      operator_action: "confirm_target_floor_before_real_dispatch",
      evidence_ref: "human-takeover.json",
      status: "blocked_not_proven",
    });
    expect(response.evidence_refs.elevator_state_refs).toEqual([
      "file:elevator-waiting.json",
      "elevator-entering.json",
      "elevator-moving.json",
      "elevator-exiting.json",
      "elevator-handoff.json",
      "elevator-extra.json",
    ]);
    expect(response.blocked_reasons).toContain("real_realtime_api_not_connected");
    expect(response.blocked_reasons).toContain("route_membership_forced_false");
    expect(response.blocked_reasons).toContain("real_elevator_state_chain_not_connected");
    expect(response.not_proven).toContain("real_ros2_tf_forwarding");
    expect(response.not_proven).toContain("real_current_floor_recognition");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("real_realtime_api_connected=true");
    expect(payload).not.toContain("real_ros2_tf_connected=true");
    expect(payload).not.toContain("latency_lt_2s_proven=true");
    expect(payload).not.toContain("on_route=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 realtime elevator preview fails closed for missing bad unsupported unsafe and real capability claims", async () => {
    // KR1/KR2 fixture 不能自证实时连接、/tf、低延迟、路线成员、电梯到达、楼层或人工接管通过。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-realtime-elevator-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    const realtimePath = path.join(root, "realtime.json");
    const tfPath = path.join(root, "tf.json");
    const latencyPath = path.join(root, "latency.json");
    const routePath = path.join(root, "route.json");
    const elevatorZonePath = path.join(root, "elevator-zone.json");
    const elevatorStatePath = path.join(root, "elevator-state.json");
    const arrivalPath = path.join(root, "arrival.json");
    const floorPath = path.join(root, "floor.json");
    const takeoverPath = path.join(root, "takeover.json");
    const robotControlPath = path.join(root, "robot-control.json");
    const fixture = sampleRealtimeElevatorFixture("safe-ref");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...fixture, evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...fixture, note: "delivery success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...fixture, safe_to_control: true }), "utf8");
    await writeFile(realtimePath, JSON.stringify({ ...fixture, real_realtime_api_connected: true }), "utf8");
    await writeFile(tfPath, JSON.stringify({ ...fixture, real_ros2_tf_connected: true }), "utf8");
    await writeFile(latencyPath, JSON.stringify({ ...fixture, latency_lt_2s_proven: true }), "utf8");
    await writeFile(routePath, JSON.stringify({ ...fixture, route_membership: { on_route: true } }), "utf8");
    await writeFile(elevatorZonePath, JSON.stringify({ ...fixture, route_membership: { in_elevator_zone: true } }), "utf8");
    await writeFile(elevatorStatePath, JSON.stringify({ ...fixture, real_elevator_state_chain_connected: true }), "utf8");
    await writeFile(arrivalPath, JSON.stringify({ ...fixture, elevator_arrival_proven: true }), "utf8");
    await writeFile(floorPath, JSON.stringify({ ...fixture, floor_recognition_proven: true }), "utf8");
    await writeFile(takeoverPath, JSON.stringify({ ...fixture, human_takeover_proven: true }), "utf8");
    await writeFile(robotControlPath, JSON.stringify({ ...fixture, robot_control_executed: true }), "utf8");

    const missing = await buildO7RealtimeElevatorPreview({ fixtureJson: path.join(root, "missing.json") });
    const badJson = await buildO7RealtimeElevatorPreview({ fixtureJson: badJsonPath });
    const unsupported = await buildO7RealtimeElevatorPreview({ fixtureJson: unsupportedPath });
    const unsafe = await buildO7RealtimeElevatorPreview({ fixtureJson: unsafePath });
    const success = await buildO7RealtimeElevatorPreview({ fixtureJson: successPath });
    const control = await buildO7RealtimeElevatorPreview({ fixtureJson: controlPath });
    const realtime = await buildO7RealtimeElevatorPreview({ fixtureJson: realtimePath });
    const tf = await buildO7RealtimeElevatorPreview({ fixtureJson: tfPath });
    const latency = await buildO7RealtimeElevatorPreview({ fixtureJson: latencyPath });
    const route = await buildO7RealtimeElevatorPreview({ fixtureJson: routePath });
    const elevatorZone = await buildO7RealtimeElevatorPreview({ fixtureJson: elevatorZonePath });
    const elevatorState = await buildO7RealtimeElevatorPreview({ fixtureJson: elevatorStatePath });
    const arrival = await buildO7RealtimeElevatorPreview({ fixtureJson: arrivalPath });
    const floor = await buildO7RealtimeElevatorPreview({ fixtureJson: floorPath });
    const takeover = await buildO7RealtimeElevatorPreview({ fixtureJson: takeoverPath });
    const robotControl = await buildO7RealtimeElevatorPreview({ fixtureJson: robotControlPath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    expect(realtime.input_status.status).toBe("real_realtime_api_claim");
    expect(tf.input_status.status).toBe("ros2_tf_connected_claim");
    expect(latency.input_status.status).toBe("latency_lt_2s_claim");
    expect(route.input_status.status).toBe("route_membership_true_claim");
    expect(elevatorZone.input_status.status).toBe("in_elevator_zone_true_claim");
    expect(elevatorState.input_status.status).toBe("real_elevator_state_claim");
    expect(arrival.input_status.status).toBe("elevator_arrival_claim");
    expect(floor.input_status.status).toBe("floor_recognition_proven_claim");
    expect(takeover.input_status.status).toBe("human_takeover_proven_claim");
    expect(robotControl.input_status.status).toBe("robot_control_executed_claim");
    for (const response of [
      missing,
      badJson,
      unsupported,
      unsafe,
      success,
      control,
      realtime,
      tf,
      latency,
      route,
      elevatorZone,
      elevatorState,
      arrival,
      floor,
      takeover,
      robotControl,
    ]) {
      expect(response.schema).toBe("trashbot.o7.realtime_elevator_preview.v1");
      expect(response.preview_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.real_realtime_api_connected).toBe(false);
      expect(response.real_ros2_tf_connected).toBe(false);
      expect(response.real_elevator_state_chain_connected).toBe(false);
      expect(response.latency_lt_2s_proven).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.route_membership_summary.on_route).toBe(false);
      expect(response.route_membership_summary.in_elevator_zone).toBe(false);
      expect(response.elevator_state_chain_summary.sample).toEqual([]);
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 route replay preview summarizes a safe local fixture without control or success claims", async () => {
    // preview adapter 前进一步只消费本地 fixture 摘要，不连接云端、不播放、不控制机器人。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-replay-"));
    const evidenceRef = path.join(root, "task-evidence.json");
    const fixturePath = path.join(root, "fixture.json");
    await writeFile(fixturePath, JSON.stringify(sampleRouteReplayFixture(evidenceRef)), "utf8");

    const response = await buildO7RouteReplayPreview({ fixtureJson: fixturePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.route_replay_preview.v1");
    expect(response.preview_status).toBe("fixture_preview_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.fixture_json).toBe("file:fixture.json");
    expect(response.source).toBe("software_proof");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.real_cloud_archive_connected).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.task).toMatchObject({
      task_id: "task-fixture-001",
      robot_id: "robot-fixture-01",
      route_id: "route-alpha",
      evidence_ref: "file:task-evidence.json",
    });
    expect(response.route_metadata.map_frame).toBe("map");
    expect(response.route_metadata.source).toBe("local_json_fixture");
    expect(response.trajectory.frame_count).toBe(4);
    expect(response.trajectory.sample_frames).toHaveLength(3);
    expect(response.trajectory.sample_frames[0]).toEqual({
      frame_index: 0,
      timestamp_ms: 1000,
      pose: { x_m: 1.1, y_m: 2.2, yaw_rad: 0.1 },
      velocity: { linear_mps: 0.2, angular_radps: 0.01 },
      state: "departed",
      evidence_ref: "file:frame-000.jpg",
    });
    expect(response.playback_cursor_initial_state).toEqual({
      frame_index: 0,
      timestamp_ms: 1000,
      playing: false,
      speed: 0,
      safe_to_play: false,
      status: "preview_cursor_only",
    });
    expect(response.keyframes.count).toBe(2);
    expect(response.keyframes.sample_refs).toEqual(["file:keyframe-000.jpg", "keyframe-001.jpg"]);
    expect(response.evidence_refs.fixture_ref).toBe("file:fixture.json");
    expect(response.evidence_refs.task_evidence_ref).toBe("file:task-evidence.json");
    expect(response.state_transitions.count).toBe(2);
    expect(response.state_transitions.sample).toEqual([
      { from: "queued", to: "departed", timestamp_ms: 900, evidence_ref: "transition-queued.json" },
      { from: "departed", to: "en_route", timestamp_ms: 1000, evidence_ref: "transition-en-route.json" },
    ]);
    expect(response.state_transitions.gaps).toEqual(
      expect.arrayContaining(["not_o6_cloud_archive", "not_real_route_playback", "robot_control_disabled"]),
    );
    expect(response.not_proven).toContain("real_route_replay_playback");
    expect(response.not_proven).toContain("delivery_success");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("safe_to_control=true");
    expect(payload).not.toContain("delivery_success=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 route replay preview fails closed for missing bad unsupported unsafe success and control fixtures", async () => {
    // 所有不可信输入都返回同一 schema 和固定 false 开关，避免 UI 猜测可回放。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-replay-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...sampleRouteReplayFixture("safe-ref"), evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...sampleRouteReplayFixture("safe-ref"), note: "delivery success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...sampleRouteReplayFixture("safe-ref"), safe_to_control: true }), "utf8");

    const missing = await buildO7RouteReplayPreview({ fixtureJson: path.join(root, "missing.json") });
    const badJson = await buildO7RouteReplayPreview({ fixtureJson: badJsonPath });
    const unsupported = await buildO7RouteReplayPreview({ fixtureJson: unsupportedPath });
    const unsafe = await buildO7RouteReplayPreview({ fixtureJson: unsafePath });
    const success = await buildO7RouteReplayPreview({ fixtureJson: successPath });
    const control = await buildO7RouteReplayPreview({ fixtureJson: controlPath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    for (const response of [missing, badJson, unsupported, unsafe, success, control]) {
      expect(response.schema).toBe("trashbot.o7.route_replay_preview.v1");
      expect(response.preview_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.real_cloud_archive_connected).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.trajectory.frame_count).toBe(0);
      expect(response.playback_cursor_initial_state.safe_to_play).toBe(false);
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 labeling preview summarizes a safe local fixture without submit rollback export or control claims", async () => {
    // labeling preview 前进一步只展示待标注数据摘要，真实 annotation API 和导出仍关闭。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-labeling-"));
    const evidenceRef = path.join(root, "queue-evidence.json");
    const fixturePath = path.join(root, "labeling-fixture.json");
    await writeFile(fixturePath, JSON.stringify(sampleLabelingFixture(evidenceRef)), "utf8");

    const response = await buildO7LabelingPreview({ fixtureJson: fixturePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.labeling_preview.v1");
    expect(response.preview_status).toBe("fixture_preview_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.fixture_json).toBe("file:labeling-fixture.json");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.real_annotation_api_connected).toBe(false);
    expect(response.submit_enabled).toBe(false);
    expect(response.rollback_enabled).toBe(false);
    expect(response.dataset_export_available).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.source_fixture_schema).toBe("trashbot.o7.labeling_fixture.v1");
    expect(response.queue).toEqual({
      queue_id: "queue-fixture-001",
      source: "local_json_fixture",
      review_item_count: 4,
      status: "fixture_summary_only",
    });
    expect(response.review_items.sample_limit).toBe(3);
    expect(response.review_items.sample).toHaveLength(3);
    expect(response.review_items.sample[0]).toEqual({
      item_id: "item-001",
      task_id: "task-001",
      frame_id: "frame-001",
      media_ref: "file:frame-001.jpg",
      evidence_ref: "file:item-001.json",
      current_labels: {
        count: 1,
        sample: [
          {
            label_type: "elevator_door_state",
            value: "open",
            status: "fixture_existing",
            evidence_ref: "label-001.json",
          },
        ],
      },
    });
    expect(response.label_schema).toMatchObject({
      schema_ref: "label-schema-o7-kr4.json",
      version: "fixture-v1",
      required_fields: ["label_type", "value", "evidence_ref"],
      allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref"],
      status: "fixture_schema_summary_only",
    });
    expect(response.allowed_label_types).toEqual(["elevator_door_state", "floor_label", "obstacle_type"]);
    expect(response.draft_labels.count).toBe(2);
    expect(response.draft_labels.autosave_available).toBe(false);
    expect(response.draft_labels.sample[0]).toEqual({
      item_id: "item-001",
      label_type: "floor_label",
      value: "F3",
      status: "draft_slot",
      evidence_ref: "draft-001.json",
    });
    expect(response.dataset_export.status).toBe("fixture_gap_summary_only");
    expect(response.dataset_export.export_ref).toBe("dataset-export-missing.json");
    expect(response.dataset_export.supported_formats).toEqual(["coco", "jsonl"]);
    expect(response.dataset_export.gaps).toEqual(
      expect.arrayContaining([
        "operator_review_not_complete",
        "real_annotation_api_not_connected",
        "dataset_manifest_export_not_available",
      ]),
    );
    expect(response.evidence_refs.fixture_ref).toBe("file:labeling-fixture.json");
    expect(response.evidence_refs.queue_evidence_ref).toBe("file:queue-evidence.json");
    expect(response.evidence_refs.item_evidence_refs).toEqual([
      "file:item-001.json",
      "item-002.json",
      "item-003.json",
      "item-004.json",
    ]);
    expect(response.blocked_reasons).toContain("dataset_export_disabled");
    expect(response.not_proven).toContain("real_annotation_submit");
    expect(response.not_proven).toContain("real_training_dataset_export");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("submit_enabled=true");
    expect(payload).not.toContain("rollback_enabled=true");
    expect(payload).not.toContain("dataset_export_available=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 labeling preview fails closed for missing bad unsupported unsafe and action availability claims", async () => {
    // 标注 fixture 不能自证提交、回滚、导出或控制可用，所有危险输入统一 blocked。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-labeling-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    const submitPath = path.join(root, "submit.json");
    const rollbackPath = path.join(root, "rollback.json");
    const exportPath = path.join(root, "export.json");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), note: "labeling success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), safe_to_control: true }), "utf8");
    await writeFile(submitPath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), submit_enabled: true }), "utf8");
    await writeFile(rollbackPath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), rollback_enabled: true }), "utf8");
    await writeFile(exportPath, JSON.stringify({ ...sampleLabelingFixture("safe-ref"), dataset_export_available: true }), "utf8");

    const missing = await buildO7LabelingPreview({ fixtureJson: path.join(root, "missing.json") });
    const badJson = await buildO7LabelingPreview({ fixtureJson: badJsonPath });
    const unsupported = await buildO7LabelingPreview({ fixtureJson: unsupportedPath });
    const unsafe = await buildO7LabelingPreview({ fixtureJson: unsafePath });
    const success = await buildO7LabelingPreview({ fixtureJson: successPath });
    const control = await buildO7LabelingPreview({ fixtureJson: controlPath });
    const submit = await buildO7LabelingPreview({ fixtureJson: submitPath });
    const rollback = await buildO7LabelingPreview({ fixtureJson: rollbackPath });
    const datasetExport = await buildO7LabelingPreview({ fixtureJson: exportPath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    expect(submit.input_status.status).toBe("submit_claim");
    expect(rollback.input_status.status).toBe("rollback_claim");
    expect(datasetExport.input_status.status).toBe("export_claim");
    for (const response of [missing, badJson, unsupported, unsafe, success, control, submit, rollback, datasetExport]) {
      expect(response.schema).toBe("trashbot.o7.labeling_preview.v1");
      expect(response.preview_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.real_annotation_api_connected).toBe(false);
      expect(response.submit_enabled).toBe(false);
      expect(response.rollback_enabled).toBe(false);
      expect(response.dataset_export_available).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.queue.review_item_count).toBe(0);
      expect(response.review_items.sample).toEqual([]);
      expect(response.draft_labels.autosave_available).toBe(false);
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 field evidence consumer ingest composes manifest route replay and labeling fixtures", async () => {
    // 主入口必须把三类 local fixture 拼成同一份只读消费摘要，且保留控制关闭边界。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-field-ingest-"));
    const evidenceRef = path.join(root, "manifest-evidence.json");
    const manifestPath = path.join(root, "field-evidence-manifest.json");
    const routeReplayPath = path.join(root, "route-replay.json");
    const labelingPath = path.join(root, "labeling.json");
    await writeFile(manifestPath, JSON.stringify(sampleFieldEvidenceManifest(root, evidenceRef)), "utf8");
    await writeFile(routeReplayPath, JSON.stringify(sampleRouteReplayFixture(evidenceRef)), "utf8");
    await writeFile(labelingPath, JSON.stringify(sampleLabelingFixture(evidenceRef)), "utf8");

    const response = await buildO7FieldEvidenceConsumerIngest({
      manifestJson: manifestPath,
      routeReplayFixtureJson: routeReplayPath,
      labelingFixtureJson: labelingPath,
    });

    expect(response.schema).toBe("trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1");
    expect(response.ingest_status).toBe("fixture_consumer_ready_not_proven");
    expect(response.manifest_input_status.status).toBe("loaded");
    expect(response.manifest_input_status.manifest_json).toBe("file:field-evidence-manifest.json");
    expect(response.route_replay_input_status.status).toBe("loaded");
    expect(response.route_replay_input_status.fixture_json).toBe("file:route-replay.json");
    expect(response.labeling_input_status.status).toBe("loaded");
    expect(response.labeling_input_status.fixture_json).toBe("file:labeling.json");
    expect(response.source_manifest_schema).toBe("trashbot.field_evidence_manifest.v1");
    expect(response.manifest.schema).toBe("trashbot.field_evidence_manifest.v1");
    expect(response.manifest.run_id).toBe("field_evidence_20260609T101500Z");
    expect(response.manifest.source).toBe("local_fixture");
    expect(response.manifest.mode).toBe("local");
    expect(response.manifest.status).toBe("field_evidence_manifest_ready_not_delivery_proof");
    expect(response.manifest.gate_pass).toBe(true);
    expect(response.manifest.not_proven).toBe(true);
    expect(response.manifest.delivery_success).toBe(false);
    expect(response.manifest.primary_actions_enabled).toBe(false);
    expect(response.route_replay_preview.preview_status).toBe("fixture_preview_ready");
    expect(response.route_replay_preview.task.task_id).toBe("task-fixture-001");
    expect(response.labeling_preview.preview_status).toBe("fixture_preview_ready");
    expect(response.labeling_preview.queue.queue_id).toBe("queue-fixture-001");
    expect(response.consumer_entry.fallback_mode).toBe("local_mock");
    expect(response.consumer_entry.primary_path).toBe("/api/o7/field-evidence-consumer-ingest");
    expect(response.consumer_entry.route_replay_path).toBe("/api/o7/route-replay-preview");
    expect(response.consumer_entry.labeling_path).toBe("/api/o7/labeling-preview");
    expect(response.consumer_entry.blocked_reason).toBe("");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.blocked_reasons).toEqual(expect.arrayContaining(["preflight_ready_not_delivery_proof"]));
    expect(response.not_proven).toEqual(
      expect.arrayContaining([
        "field_evidence_manifest_not_delivery_proof",
        "real_o6_cloud_archive",
        "real_route_replay_playback",
        "real_robot_control",
        "real_o6_annotation_api",
        "real_labeling_review_queue",
        "real_label_schema_api",
        "real_review_item_media",
        "real_draft_label_autosave",
        "real_annotation_submit",
        "real_annotation_rollback",
        "real_training_dataset_export",
      ]),
    );
    expect(response.next_required_evidence).toEqual(
      expect.arrayContaining([
        "real_o6_cloud_archive",
        "real_route_replay_playback",
        "real_robot_control",
        "real_o6_annotation_api",
        "real_labeling_review_queue",
        "real_label_schema_api",
        "real_review_item_media",
        "real_draft_label_autosave",
        "real_annotation_submit",
        "real_annotation_rollback",
        "real_training_dataset_export",
      ]),
    );
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 field evidence consumer ingest fails closed when local fixture paths are missing", async () => {
    // 任一层缺文件都要进入 blocked_not_proven，不能把缺口误报成 ready。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-field-ingest-missing-"));
    const manifestPath = path.join(root, "missing-manifest.json");
    const routeReplayPath = path.join(root, "missing-route-replay.json");
    const labelingPath = path.join(root, "missing-labeling.json");

    const response = await buildO7FieldEvidenceConsumerIngest({
      manifestJson: manifestPath,
      routeReplayFixtureJson: routeReplayPath,
      labelingFixtureJson: labelingPath,
    });

    expect(response.schema).toBe("trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1");
    expect(response.ingest_status).toBe("blocked_not_proven");
    expect(response.manifest_input_status.status).toBe("missing");
    expect(response.route_replay_input_status.status).toBe("missing");
    expect(response.labeling_input_status.status).toBe("missing");
    expect(response.source_manifest_schema).toBe("not_loaded");
    expect(response.manifest.status).toBe("manifest_not_loaded");
    expect(response.manifest.gate_pass).toBe(false);
    expect(response.manifest.not_proven).toBe(true);
    expect(response.route_replay_preview.preview_status).toBe("blocked_not_proven");
    expect(response.labeling_preview.preview_status).toBe("blocked_not_proven");
    expect(response.consumer_entry.fallback_mode).toBe("blocked_not_proven");
    expect(response.consumer_entry.blocked_reason).toBe("manifest_not_loaded");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.blocked_reasons).toEqual(expect.arrayContaining(["fixture_json_missing", "manifest_not_loaded"]));
    expect(response.not_proven).toEqual(expect.arrayContaining(["field_evidence_manifest_not_delivery_proof", "real_o6_cloud_archive", "real_o6_annotation_api"]));
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 voice preview summarizes a safe local fixture without ASR TTS speaker or control claims", async () => {
    // voice preview 前进一步只展示 ASR/TTS 摘要，真实语音 API、喇叭播放和 ACK 仍关闭。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-voice-"));
    const evidenceRef = path.join(root, "voice-evidence.json");
    const fixturePath = path.join(root, "voice-fixture.json");
    await writeFile(fixturePath, JSON.stringify(sampleVoiceFixture(evidenceRef)), "utf8");

    const response = await buildO7VoicePreview({ fixtureJson: fixturePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.voice_preview.v1");
    expect(response.preview_status).toBe("fixture_preview_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.fixture_json).toBe("file:voice-fixture.json");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.real_voice_api_connected).toBe(false);
    expect(response.real_asr_tts_runtime_connected).toBe(false);
    expect(response.asr_stream_connected).toBe(false);
    expect(response.tts_send_enabled).toBe(false);
    expect(response.speaker_dispatch_enabled).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.source_fixture_schema).toBe("trashbot.o7.voice_fixture.v1");
    expect(response.voice_session).toEqual({
      session_id: "voice-session-001",
      source: "local_json_fixture",
      evidence_ref: "file:voice-evidence.json",
      audit_refs: ["voice-audit-001.json", "file:voice-audit-002.json"],
      status: "fixture_summary_only",
    });
    expect(response.asr_events.event_count).toBe(4);
    expect(response.asr_events.sample_limit).toBe(3);
    expect(response.asr_events.sample).toHaveLength(3);
    expect(response.asr_events.sample[0]).toEqual({
      event_type: "partial",
      timestamp_ms: 1000,
      transcript: "去三楼",
      confidence: 0.61,
      evidence_ref: "file:asr-partial-001.json",
    });
    expect(response.asr_events.latest_partial).toMatchObject({
      text: "下一句不会进入 sample",
      timestamp_ms: 1700,
      confidence: 0.55,
      evidence_ref: "asr-partial-003.json",
      status: "fixture_summary_only",
    });
    expect(response.asr_events.latest_final).toMatchObject({
      text: "请去三楼电梯口",
      timestamp_ms: 1500,
      confidence: 0.88,
      evidence_ref: "asr-final-001.json",
      status: "fixture_summary_only",
    });
    expect(response.tts_draft_summary).toEqual({
      text: "我会等待人工确认后再播报。",
      text_length: 13,
      voice_profile: "operator-default",
      language: "zh-CN",
      confirmation_required: true,
      status: "fixture_draft_only",
    });
    expect(response.speaker_dispatch_summary).toMatchObject({
      sends_to_robot: false,
      speaker_dispatch_enabled: false,
      ack_status: "not_proven",
      speaker_ack_ref: "speaker-ack-missing.json",
      failure_event_ref: "speaker-failure-missing.json",
      failure_refs: ["speaker-timeout.json", "file:speaker-device-missing.json"],
      status: "blocked_not_proven",
    });
    expect(response.media_preflight_dependency).toMatchObject({
      required: true,
      source_schema: "trashbot.o7_board_media_preflight.v1",
      status: "blocked",
      dependency_ref: "board_media_preflight_summary",
    });
    expect(response.media_preflight_dependency.gaps).toEqual(
      expect.arrayContaining(["audio_input_not_checked", "real_audio_playback_not_proven"]),
    );
    expect(response.evidence_refs.fixture_ref).toBe("file:voice-fixture.json");
    expect(response.evidence_refs.session_evidence_ref).toBe("file:voice-evidence.json");
    expect(response.evidence_refs.asr_event_refs).toEqual([
      "file:asr-partial-001.json",
      "asr-partial-002.json",
      "asr-final-001.json",
      "asr-partial-003.json",
    ]);
    expect(response.evidence_refs.tts_evidence_ref).toBe("file:tts-draft.json");
    expect(response.blocked_reasons).toContain("tts_send_disabled");
    expect(response.not_proven).toContain("real_asr_stream");
    expect(response.not_proven).toContain("real_speaker_dispatch_ack");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("asr_stream_connected=true");
    expect(payload).not.toContain("tts_send_enabled=true");
    expect(payload).not.toContain("speaker_dispatch_enabled=true");
    expect(payload).not.toContain("real_voice_api_connected=true");
    expect(payload).not.toContain("real_asr_tts_runtime_connected=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 voice preview fails closed for missing bad unsupported unsafe and voice availability claims", async () => {
    // 本地 fixture 不能自证 ASR 连接、TTS 可发送、喇叭可调度、真实 runtime 或 ACK 成功。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-voice-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    const asrPath = path.join(root, "asr.json");
    const ttsPath = path.join(root, "tts.json");
    const speakerPath = path.join(root, "speaker.json");
    const realVoicePath = path.join(root, "real-voice.json");
    const ackSuccessPath = path.join(root, "ack-success.json");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), note: "voice success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), safe_to_control: true }), "utf8");
    await writeFile(asrPath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), asr_stream_connected: true }), "utf8");
    await writeFile(ttsPath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), tts_send_enabled: true }), "utf8");
    await writeFile(speakerPath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), speaker_dispatch_enabled: true }), "utf8");
    await writeFile(realVoicePath, JSON.stringify({ ...sampleVoiceFixture("safe-ref"), real_voice_api_connected: true }), "utf8");
    await writeFile(
      ackSuccessPath,
      JSON.stringify({ ...sampleVoiceFixture("safe-ref"), speaker_ack: { ack_status: "success" } }),
      "utf8",
    );

    const missing = await buildO7VoicePreview({ fixtureJson: path.join(root, "missing.json") });
    const badJson = await buildO7VoicePreview({ fixtureJson: badJsonPath });
    const unsupported = await buildO7VoicePreview({ fixtureJson: unsupportedPath });
    const unsafe = await buildO7VoicePreview({ fixtureJson: unsafePath });
    const success = await buildO7VoicePreview({ fixtureJson: successPath });
    const control = await buildO7VoicePreview({ fixtureJson: controlPath });
    const asr = await buildO7VoicePreview({ fixtureJson: asrPath });
    const tts = await buildO7VoicePreview({ fixtureJson: ttsPath });
    const speaker = await buildO7VoicePreview({ fixtureJson: speakerPath });
    const realVoice = await buildO7VoicePreview({ fixtureJson: realVoicePath });
    const ackSuccess = await buildO7VoicePreview({ fixtureJson: ackSuccessPath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    expect(asr.input_status.status).toBe("asr_connected_claim");
    expect(tts.input_status.status).toBe("tts_send_claim");
    expect(speaker.input_status.status).toBe("speaker_dispatch_claim");
    expect(realVoice.input_status.status).toBe("real_voice_claim");
    expect(ackSuccess.input_status.status).toBe("speaker_ack_success_claim");
    for (const response of [missing, badJson, unsupported, unsafe, success, control, asr, tts, speaker, realVoice, ackSuccess]) {
      expect(response.schema).toBe("trashbot.o7.voice_preview.v1");
      expect(response.preview_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.real_voice_api_connected).toBe(false);
      expect(response.real_asr_tts_runtime_connected).toBe(false);
      expect(response.asr_stream_connected).toBe(false);
      expect(response.tts_send_enabled).toBe(false);
      expect(response.speaker_dispatch_enabled).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.asr_events.event_count).toBe(0);
      expect(response.tts_draft_summary.confirmation_required).toBe(true);
      expect(response.speaker_dispatch_summary.sends_to_robot).toBe(false);
      expect(response.media_preflight_dependency.status).toBe("blocked");
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 safe command preview summarizes a safe local fixture without dispatch ack or control claims", async () => {
    // safe command preview 只展示手控/寻路 envelope 摘要，真实发送、ACK、键盘控制和 HIL 都关闭。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-safe-command-"));
    const evidenceRef = path.join(root, "safe-command-evidence.json");
    const fixturePath = path.join(root, "safe-command-fixture.json");
    await writeFile(fixturePath, JSON.stringify(sampleSafeCommandFixture(evidenceRef)), "utf8");

    const response = await buildO7SafeCommandPreview({ fixtureJson: fixturePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.safe_command_preview.v1");
    expect(response.preview_status).toBe("fixture_preview_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.fixture_json).toBe("file:safe-command-fixture.json");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.command_dispatch_enabled).toBe(false);
    expect(response.manual_control_enabled).toBe(false);
    expect(response.navigate_goal_enabled).toBe(false);
    expect(response.keyboard_control_enabled).toBe(false);
    expect(response.real_command_api_connected).toBe(false);
    expect(response.real_robot_ack_connected).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.source_fixture_schema).toBe("trashbot.o7.safe_command_fixture.v1");
    expect(response.command_session).toEqual({
      command_session_id: "safe-command-session-001",
      source: "local_json_fixture",
      evidence_ref: "file:safe-command-evidence.json",
      audit_refs: ["safe-command-audit-001.json", "file:safe-command-audit-002.json"],
      status: "fixture_summary_only",
    });
    expect(response.manual_turn_envelope_summary).toEqual({
      sends_to_robot: false,
      requested_direction: "left",
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: "file:manual-turn-envelope.json",
      status: "fixture_summary_only",
    });
    expect(response.navigate_goal_envelope_summary).toEqual({
      sends_to_robot: false,
      goal_source: "fixture_map_goal_slot",
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      evidence_ref: "navigate-goal-envelope.json",
      status: "fixture_summary_only",
    });
    expect(response.velocity_limits).toEqual({
      max_linear_mps: 0.2,
      max_angular_radps: 0.4,
      source: "fixture_limit_not_hil",
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    });
    expect(response.steering_limits).toMatchObject({
      max_steering_angle_rad: 0.35,
      max_turn_rate_radps: 0.45,
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    });
    expect(response.map_goal_slot).toEqual({
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      status: "fixture_slot_summary_only",
      evidence_ref: "file:map-goal-slot.json",
    });
    expect(response.idempotency_key_requirement).toEqual({
      required: true,
      key_ref: "idempotency-policy.json",
      header: "Idempotency-Key",
      status: "fixture_requirement_summary_only",
    });
    expect(response.confirmation_policy.manual_turn_requires_confirmation).toBe(true);
    expect(response.confirmation_policy.navigate_goal_requires_confirmation).toBe(true);
    expect(response.confirmation_policy.keyboard_control_requires_hold).toBe(true);
    expect(response.robot_ack_summary).toEqual({
      ack_status: "blocked_not_proven",
      last_command_id: "cmd-preview-001",
      ack_ref: "ack-missing.json",
      timeout_ms: 1500,
      cancel_ack_ref: "cancel-missing.json",
      stop_ack_ref: "stop-missing.json",
      recovery_ref: "recovery-missing.json",
      status: "blocked_not_proven",
    });
    expect(response.evidence_gaps).toEqual(
      expect.arrayContaining([
        "operator_confirmation_ui_not_connected",
        "robot_ack_timeout_trace_missing",
        "cancel_ack_trace_missing",
        "stop_ack_trace_missing",
        "recovery_event_trace_missing",
      ]),
    );
    expect(response.evidence_refs.fixture_ref).toBe("file:safe-command-fixture.json");
    expect(response.evidence_refs.session_evidence_ref).toBe("file:safe-command-evidence.json");
    expect(response.evidence_refs.ack_ref).toBe("ack-missing.json");
    expect(response.blocked_reasons).toContain("command_dispatch_disabled");
    expect(response.not_proven).toContain("real_robot_command_ack");
    expect(response.not_proven).toContain("real_velocity_limit_hil");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("command_dispatch_enabled=true");
    expect(payload).not.toContain("manual_control_enabled=true");
    expect(payload).not.toContain("navigate_goal_enabled=true");
    expect(payload).not.toContain("keyboard_control_enabled=true");
    expect(payload).not.toContain("real_command_api_connected=true");
    expect(payload).not.toContain("real_robot_ack_connected=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 safe command preview fails closed for unsafe control dispatch ack and hardware claims", async () => {
    // 本地 safe command fixture 不能自证控制开关、真实 ACK、执行成功或 HIL/硬件验证。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-safe-command-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    const dispatchPath = path.join(root, "dispatch.json");
    const manualPath = path.join(root, "manual.json");
    const navigatePath = path.join(root, "navigate.json");
    const keyboardPath = path.join(root, "keyboard.json");
    const realApiPath = path.join(root, "real-api.json");
    const realAckPath = path.join(root, "real-ack.json");
    const executedPath = path.join(root, "executed.json");
    const ackSuccessPath = path.join(root, "ack-success.json");
    const hardwarePath = path.join(root, "hardware.json");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), note: "command success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), safe_to_control: true }), "utf8");
    await writeFile(dispatchPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), command_dispatch_enabled: true }), "utf8");
    await writeFile(manualPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), manual_control_enabled: true }), "utf8");
    await writeFile(navigatePath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), navigate_goal_enabled: true }), "utf8");
    await writeFile(keyboardPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), keyboard_control_enabled: true }), "utf8");
    await writeFile(realApiPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), real_command_api_connected: true }), "utf8");
    await writeFile(realAckPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), real_robot_ack_connected: true }), "utf8");
    await writeFile(executedPath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), robot_control_executed: true }), "utf8");
    await writeFile(
      ackSuccessPath,
      JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), robot_ack_status: { ack_status: "success" } }),
      "utf8",
    );
    await writeFile(hardwarePath, JSON.stringify({ ...sampleSafeCommandFixture("safe-ref"), hardware_verified: true }), "utf8");

    const missing = await buildO7SafeCommandPreview({ fixtureJson: path.join(root, "missing.json") });
    const badJson = await buildO7SafeCommandPreview({ fixtureJson: badJsonPath });
    const unsupported = await buildO7SafeCommandPreview({ fixtureJson: unsupportedPath });
    const unsafe = await buildO7SafeCommandPreview({ fixtureJson: unsafePath });
    const success = await buildO7SafeCommandPreview({ fixtureJson: successPath });
    const control = await buildO7SafeCommandPreview({ fixtureJson: controlPath });
    const dispatch = await buildO7SafeCommandPreview({ fixtureJson: dispatchPath });
    const manual = await buildO7SafeCommandPreview({ fixtureJson: manualPath });
    const navigate = await buildO7SafeCommandPreview({ fixtureJson: navigatePath });
    const keyboard = await buildO7SafeCommandPreview({ fixtureJson: keyboardPath });
    const realApi = await buildO7SafeCommandPreview({ fixtureJson: realApiPath });
    const realAck = await buildO7SafeCommandPreview({ fixtureJson: realAckPath });
    const executed = await buildO7SafeCommandPreview({ fixtureJson: executedPath });
    const ackSuccess = await buildO7SafeCommandPreview({ fixtureJson: ackSuccessPath });
    const hardware = await buildO7SafeCommandPreview({ fixtureJson: hardwarePath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    expect(dispatch.input_status.status).toBe("dispatch_enabled_claim");
    expect(manual.input_status.status).toBe("manual_enabled_claim");
    expect(navigate.input_status.status).toBe("navigate_enabled_claim");
    expect(keyboard.input_status.status).toBe("keyboard_enabled_claim");
    expect(realApi.input_status.status).toBe("real_command_api_claim");
    expect(realAck.input_status.status).toBe("real_robot_ack_claim");
    expect(executed.input_status.status).toBe("robot_control_executed_claim");
    expect(ackSuccess.input_status.status).toBe("ack_success_claim");
    expect(hardware.input_status.status).toBe("hardware_verified_claim");
    for (const response of [
      missing,
      badJson,
      unsupported,
      unsafe,
      success,
      control,
      dispatch,
      manual,
      navigate,
      keyboard,
      realApi,
      realAck,
      executed,
      ackSuccess,
      hardware,
    ]) {
      expect(response.schema).toBe("trashbot.o7.safe_command_preview.v1");
      expect(response.preview_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.command_dispatch_enabled).toBe(false);
      expect(response.manual_control_enabled).toBe(false);
      expect(response.navigate_goal_enabled).toBe(false);
      expect(response.keyboard_control_enabled).toBe(false);
      expect(response.real_command_api_connected).toBe(false);
      expect(response.real_robot_ack_connected).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.manual_turn_envelope_summary.sends_to_robot).toBe(false);
      expect(response.navigate_goal_envelope_summary.sends_to_robot).toBe(false);
      expect(response.velocity_limits.hardware_verified).toBe(false);
      expect(response.steering_limits.hardware_verified).toBe(false);
      expect(response.robot_ack_summary.ack_status).toBe("blocked_not_proven");
      expect(response.confirmation_policy.manual_turn_requires_confirmation).toBe(true);
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 cloud archive tasks summarizes local archive fixture without real API or control claims", async () => {
    // archive task API 是 KR3-KR6 的统一数据源雏形，不是 O6 真实云归档连接。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-cloud-archive-"));
    const evidenceRef = path.join(root, "task-archive-002.json");
    const archivePath = path.join(root, "archive.json");
    await writeFile(archivePath, JSON.stringify(sampleCloudArchiveFixture(evidenceRef)), "utf8");

    const response = await buildO7CloudArchiveTasks({ archiveJson: archivePath });
    const payload = JSON.stringify(response);

    expect(response.schema).toBe("trashbot.o7.cloud_archive_tasks.v1");
    expect(response.archive_status).toBe("fixture_archive_ready");
    expect(response.input_status.status).toBe("loaded");
    expect(response.input_status.archive_json).toBe("file:archive.json");
    expect(response.source_fixture_schema).toBe("trashbot.o7.cloud_archive_fixture.v1");
    expect(response.source).toBe("software_proof");
    expect(response.proof_status).toBe("not_proven");
    expect(response.safe_to_control).toBe(false);
    expect(response.delivery_success).toBe(false);
    expect(response.primary_actions_enabled).toBe(false);
    expect(response.pc_only).toBe(true);
    expect(response.real_cloud_archive_connected).toBe(false);
    expect(response.real_realtime_api_connected).toBe(false);
    expect(response.real_annotation_api_connected).toBe(false);
    expect(response.real_voice_api_connected).toBe(false);
    expect(response.real_command_api_connected).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.fixed_false_fields).toEqual({
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
    });
    expect(response.task_list.total_tasks).toBe(2);
    expect(response.task_list.tasks.map((task) => task.task_id)).toEqual(["task-archive-001", "task-archive-002"]);
    expect(response.selected_task).toMatchObject({
      task_id: "task-archive-002",
      robot_id: "robot-fixture-01",
      route_id: "route-beta",
      status: "needs_review_fixture_only",
      evidence_ref: "file:task-archive-002.json",
    });
    expect(response.latest_task?.task_id).toBe("task-archive-002");
    expect(response.safe_summaries.trajectory).toEqual({
      frame_count: 6,
      sample_refs: ["file:frame-101.jpg", "frame-102.jpg", "frame-103.jpg", "frame-104.jpg", "frame-105.jpg"],
      status: "fixture_summary_only",
    });
    expect(response.safe_summaries.events.sample_types).toEqual(["arrived_at_elevator", "door_open_wait"]);
    expect(response.route_replay_inspector).toMatchObject({
      status: "fixture_inspector_ready",
      selected_task_id: "task-archive-002",
      map_frame: "map",
      frame_count: 6,
      cursor_initial_state: {
        playing: false,
        safe_to_play: false,
        speed: 0,
        frame_index: 10,
      },
    });
    expect(response.route_replay_inspector.sample_frames).toHaveLength(5);
    expect(response.route_replay_inspector.sample_frames[0]).toEqual({
      frame_index: 10,
      timestamp_ms: 2100,
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      speed_mps: 0.12,
      state: "departed",
      evidence_ref: "file:frame-101.jpg",
    });
    expect(response.route_replay_inspector.sample_frames[4]?.frame_index).toBe(14);
    expect(response.route_replay_inspector.sample_frames).not.toContainEqual(
      expect.objectContaining({ frame_index: 15 }),
    );
    expect(response.route_replay_inspector.event_timeline).toEqual([
      {
        event_type: "arrived_at_elevator",
        state: "state_missing",
        timestamp_ms: 2250,
        evidence_ref: "file:event-001.json",
      },
      {
        event_type: "event_type_missing",
        state: "door_open_wait",
        timestamp_ms: 2350,
        evidence_ref: "event-002.json",
      },
    ]);
    expect(response.route_replay_inspector.keyframe_refs).toEqual([
      "file:keyframe-001.jpg",
      "keyframe-002.jpg",
      "keyframe-003.jpg",
      "keyframe-004.jpg",
      "keyframe-005.jpg",
    ]);
    expect(response.safe_summaries.labels).toMatchObject({
      label_count: 2,
      sample_types: ["floor_label", "obstacle_type"],
      real_annotation_api_connected: false,
    });
    expect(response.labeling_queue_inspector).toMatchObject({
      status: "fixture_labeling_ready",
      selected_task_id: "task-archive-002",
      review_item_count: 6,
      submit_enabled: false,
      rollback_enabled: false,
      dataset_export_available: false,
      real_annotation_api_connected: false,
    });
    expect(response.labeling_queue_inspector.sample_review_items).toHaveLength(5);
    expect(response.labeling_queue_inspector.sample_review_items[0]).toEqual({
      item_id: "review-001",
      task_id: "task-archive-002",
      frame_id: "frame-101",
      media_ref: "file:frame-101.jpg",
      evidence_ref: "file:review-001.json",
      current_labels: {
        count: 4,
        sample: [
          { label_type: "elevator_door_state", value: "open", status: "fixture_existing", evidence_ref: "label-door.json" },
          { label_type: "floor_label", value: "F3", status: "fixture_existing", evidence_ref: "label-floor.json" },
          { label_type: "obstacle_type", value: "none", status: "fixture_existing", evidence_ref: "label-obstacle.json" },
        ],
      },
    });
    expect(response.labeling_queue_inspector.sample_review_items.map((item) => item.item_id)).not.toContain("review-not-returned");
    expect(response.labeling_queue_inspector.label_schema).toEqual({
      schema_ref: "file:label-schema.json",
      version: "fixture-v2",
      required_fields: ["label_type", "value", "evidence_ref", "status", "reviewer"],
      allowed_fields: ["label_type", "value", "confidence", "notes", "evidence_ref"],
    });
    expect(response.labeling_queue_inspector.allowed_label_types).toEqual([
      "elevator_door_state",
      "floor_label",
      "obstacle_type",
      "trash_type",
      "blocked_reason",
    ]);
    expect(response.labeling_queue_inspector.draft_labels).toMatchObject({
      count: 6,
      autosave_available: false,
    });
    expect(response.labeling_queue_inspector.draft_labels.sample).toHaveLength(5);
    expect(response.labeling_queue_inspector.draft_labels.sample[0]).toEqual({
      label_type: "floor_label",
      value: "F3",
      status: "draft_fixture",
      evidence_ref: "file:draft-001.json",
    });
    expect(response.labeling_queue_inspector.dataset_export).toEqual({
      available: false,
      status: "fixture_summary_only",
      export_ref: "file:dataset-export.json",
      supported_formats: ["jsonl", "coco", "yolo", "csv", "parquet"],
      gaps: ["real_annotation_api_not_connected", "operator_review_not_complete", "training_split_not_defined", "extra_not_returned"],
    });
    expect(response.labeling_queue_inspector.blocked_reasons).toContain("annotation_submit_disabled");
    expect(response.labeling_queue_inspector.not_proven).toContain("real_o7_annotation_submit");
    expect(response.safe_summaries.voice).toMatchObject({
      asr_event_count: 6,
      tts_draft_count: 2,
      real_voice_api_connected: false,
    });
    expect(response.voice_asr_tts_inspector).toMatchObject({
      status: "fixture_voice_ready",
      selected_task_id: "task-archive-002",
      asr_event_count: 6,
      asr_stream_connected: false,
      tts_send_enabled: false,
      speaker_dispatch_enabled: false,
      real_voice_api_connected: false,
      real_asr_tts_runtime_connected: false,
    });
    expect(response.voice_asr_tts_inspector.voice_session).toEqual({
      session_id: "voice-session-archive-002",
      source: "local_json_fixture",
      evidence_ref: "file:voice-session.json",
      audit_refs: ["voice-audit-001.json", "file:voice-audit-002.json"],
      status: "fixture_summary_only",
    });
    expect(response.voice_asr_tts_inspector.sample_asr_events).toHaveLength(5);
    expect(response.voice_asr_tts_inspector.sample_asr_events[0]).toEqual({
      event_type: "partial",
      timestamp_ms: 2310,
      transcript: "请去 [REDACTED_LOCAL_PATH]",
      confidence: 0.51,
      evidence_ref: "file:asr-partial-001.json",
    });
    expect(response.voice_asr_tts_inspector.sample_asr_events.map((event) => event.evidence_ref)).not.toContain(
      "asr-not-returned.json",
    );
    expect(response.voice_asr_tts_inspector.latest_partial).toEqual({
      text: "不会进入 sample",
      timestamp_ms: 2360,
      confidence: 0.55,
      evidence_ref: "asr-not-returned.json",
      status: "fixture_summary_only",
    });
    expect(response.voice_asr_tts_inspector.latest_final).toEqual({
      text: "请去三楼电梯口",
      timestamp_ms: 2330,
      confidence: 0.88,
      evidence_ref: "asr-final-001.json",
      status: "fixture_summary_only",
    });
    expect(response.voice_asr_tts_inspector.tts_draft).toEqual({
      text: "我会等待人工确认后再播报 [REDACTED_LOCAL_PATH]",
      text_length: 34,
      voice_profile: "operator-default",
      language: "zh-CN",
      confirmation_required: true,
      status: "fixture_draft_only",
    });
    expect(response.voice_asr_tts_inspector.speaker_dispatch).toEqual({
      sends_to_robot: false,
      speaker_dispatch_enabled: false,
      ack_status: "not_proven",
      speaker_ack_ref: "speaker-ack-missing.json",
      failure_event_ref: "file:speaker-failure.json",
      failure_refs: [
        "speaker-timeout.json",
        "file:speaker-device-missing.json",
        "speaker-gap-003.json",
        "speaker-gap-004.json",
        "speaker-gap-005.json",
      ],
      status: "blocked_not_proven",
    });
    expect(response.voice_asr_tts_inspector.media_preflight_dependency).toMatchObject({
      required: true,
      source_schema: "trashbot.o7_board_media_preflight.v1",
      status: "blocked",
      dependency_ref: "file:media-preflight.json",
      gaps: expect.arrayContaining(["audio_input_not_checked", "real_audio_input_not_proven"]),
    });
    expect(response.voice_asr_tts_inspector.blocked_reasons).toContain("tts_send_disabled");
    expect(response.voice_asr_tts_inspector.not_proven).toContain("real_speaker_dispatch_ack");
    expect(response.safe_summaries.commands).toMatchObject({
      command_count: 2,
      sample_kinds: ["manual_turn", "navigate_goal"],
      real_command_api_connected: false,
      robot_control_executed: false,
    });
    expect(response.safe_command_inspector).toMatchObject({
      status: "fixture_command_ready",
      selected_task_id: "task-archive-002",
      command_count: 2,
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
    });
    expect(response.safe_command_inspector.command_session).toEqual({
      command_session_id: "archive-command-session-002",
      source: "local_json_fixture",
      evidence_ref: "file:command-session.json",
      audit_refs: ["command-audit-001.json", "file:command-audit-002.json"],
      status: "fixture_summary_only",
    });
    expect(response.safe_command_inspector.sample_commands).toEqual([
      {
        command_id: "cmd-archive-001",
        command_type: "manual_turn",
        status: "queued_fixture_only",
        envelope_ref: "file:manual-turn-envelope.json",
        idempotency_key_ref: "idem-manual-001.json",
        evidence_ref: "command-manual-001.json",
      },
      {
        command_id: "cmd-archive-002",
        command_type: "navigate_goal",
        status: "draft_fixture_only",
        envelope_ref: "navigate-goal-envelope.json",
        idempotency_key_ref: "idem-nav-001.json",
        evidence_ref: "file:command-nav-001.json",
      },
    ]);
    expect(response.safe_command_inspector.manual_turn_envelope).toEqual({
      sends_to_robot: false,
      requested_direction: "left",
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: "file:manual-turn-envelope.json",
      status: "fixture_summary_only",
    });
    expect(response.safe_command_inspector.navigate_goal_envelope).toMatchObject({
      sends_to_robot: false,
      goal_source: "fixture_map_goal_slot",
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      evidence_ref: "navigate-goal-envelope.json",
    });
    expect(response.safe_command_inspector.velocity_limits).toEqual({
      max_linear_mps: 0.2,
      max_angular_radps: 0.4,
      source: "fixture_limit_not_hil",
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    });
    expect(response.safe_command_inspector.steering_limits).toEqual({
      max_steering_angle_rad: 0.35,
      max_turn_rate_radps: 0.45,
      source: "fixture_limit_not_hil",
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    });
    expect(response.safe_command_inspector.map_goal_slot).toEqual({
      map_frame: "map",
      x_m: 1.25,
      y_m: -0.5,
      yaw_rad: 1.57,
      status: "fixture_slot_summary_only",
      evidence_ref: "file:map-goal-slot.json",
    });
    expect(response.safe_command_inspector.idempotency_key_requirement).toEqual({
      required: true,
      key_ref: "idempotency-policy.json",
      header: "Idempotency-Key",
      status: "fixture_requirement_summary_only",
    });
    expect(response.safe_command_inspector.confirmation_policy).toEqual({
      manual_turn_requires_confirmation: true,
      navigate_goal_requires_confirmation: true,
      keyboard_control_requires_hold: true,
      status: "fixture_policy_summary_only",
    });
    expect(response.safe_command_inspector.robot_ack_blocked_summary).toEqual({
      ack_status: "blocked_not_proven",
      last_command_id: "cmd-archive-002",
      ack_ref: "ack-missing.json",
      timeout_ms: 1500,
      cancel_ack_ref: "cancel-missing.json",
      stop_ack_ref: "stop-missing.json",
      recovery_ref: "recovery-missing.json",
      status: "blocked_not_proven",
    });
    expect(response.safe_command_inspector.evidence_gaps).toEqual(expect.arrayContaining([
      "operator_confirmation_ui_not_connected",
      "robot_ack_timeout_trace_missing",
      "cancel_ack_trace_missing",
      "stop_ack_trace_missing",
      "recovery_event_trace_missing",
    ]));
    expect(response.safe_command_inspector.not_proven).toContain("real_timeout_cancel_stop_recovery");
    expect(response.blocked_reasons).toContain("real_cloud_archive_not_connected");
    expect(response.blocked_reasons).toContain("robot_control_disabled");
    expect(response.not_proven).toContain("real_o7_cloud_archive_task_api");
    expect(response.not_proven).toContain("real_o7_command_api");
    expect(payload).not.toContain(root);
    expect(payload).not.toContain("/cmd_vel");
    expect(payload).not.toContain("/dev/ttyUSB");
    expect(payload).not.toContain("real_cloud_archive_connected=true");
    expect(payload).not.toContain("delivery_success=true");
    expectNoLegacyPythonGateSemantics(response);
  });

  it("O7 cloud archive tasks fails closed for missing bad unsupported unsafe real API success and control claims", async () => {
    // archive fixture 不能自证云端、实时、标注、语音、命令 API 或真实控制已经接通。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-cloud-archive-blocked-"));
    const badJsonPath = path.join(root, "bad.json");
    const unsupportedPath = path.join(root, "unsupported.json");
    const unsafePath = path.join(root, "unsafe.json");
    const successPath = path.join(root, "success.json");
    const controlPath = path.join(root, "control.json");
    const realApiPath = path.join(root, "real-api.json");
    const fixture = sampleCloudArchiveFixture("safe-ref");
    await writeFile(badJsonPath, "{bad", "utf8");
    await writeFile(unsupportedPath, JSON.stringify({ schema: "trashbot.other.v1" }), "utf8");
    await writeFile(unsafePath, JSON.stringify({ ...fixture, evidence_ref: "/dev/ttyUSB0" }), "utf8");
    await writeFile(successPath, JSON.stringify({ ...fixture, note: "cloud archive connected and delivery success completed" }), "utf8");
    await writeFile(controlPath, JSON.stringify({ ...fixture, safe_to_control: true }), "utf8");
    await writeFile(realApiPath, JSON.stringify({ ...fixture, real_cloud_archive_connected: true }), "utf8");

    const missing = await buildO7CloudArchiveTasks({ archiveJson: path.join(root, "missing.json") });
    const badJson = await buildO7CloudArchiveTasks({ archiveJson: badJsonPath });
    const unsupported = await buildO7CloudArchiveTasks({ archiveJson: unsupportedPath });
    const unsafe = await buildO7CloudArchiveTasks({ archiveJson: unsafePath });
    const success = await buildO7CloudArchiveTasks({ archiveJson: successPath });
    const control = await buildO7CloudArchiveTasks({ archiveJson: controlPath });
    const realApi = await buildO7CloudArchiveTasks({ archiveJson: realApiPath });

    expect(missing.input_status.status).toBe("missing");
    expect(badJson.input_status.status).toBe("bad_json");
    expect(unsupported.input_status.status).toBe("unsupported_schema");
    expect(unsafe.input_status.status).toBe("unsafe_copy");
    expect(success.input_status.status).toBe("success_claim");
    expect(control.input_status.status).toBe("control_claim");
    expect(realApi.input_status.status).toBe("real_api_claim");
    for (const response of [missing, badJson, unsupported, unsafe, success, control, realApi]) {
      expect(response.schema).toBe("trashbot.o7.cloud_archive_tasks.v1");
      expect(response.archive_status).toBe("blocked_not_proven");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.real_cloud_archive_connected).toBe(false);
      expect(response.real_realtime_api_connected).toBe(false);
      expect(response.real_annotation_api_connected).toBe(false);
      expect(response.real_voice_api_connected).toBe(false);
      expect(response.real_command_api_connected).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.task_list.tasks).toEqual([]);
      expect(response.route_replay_inspector.status).toBe("blocked_not_proven");
      expect(response.route_replay_inspector.sample_frames).toEqual([]);
      expect(response.route_replay_inspector.event_timeline).toEqual([]);
      expect(response.route_replay_inspector.keyframe_refs).toEqual([]);
      expect(response.route_replay_inspector.cursor_initial_state).toEqual({
        playing: false,
        safe_to_play: false,
        speed: 0,
        frame_index: null,
      });
      expect(response.labeling_queue_inspector.status).toBe("blocked_not_proven");
      expect(response.labeling_queue_inspector.sample_review_items).toEqual([]);
      expect(response.labeling_queue_inspector.draft_labels.sample).toEqual([]);
      expect(response.labeling_queue_inspector.submit_enabled).toBe(false);
      expect(response.labeling_queue_inspector.rollback_enabled).toBe(false);
      expect(response.labeling_queue_inspector.dataset_export_available).toBe(false);
      expect(response.labeling_queue_inspector.real_annotation_api_connected).toBe(false);
      expect(response.voice_asr_tts_inspector.status).toBe("blocked_not_proven");
      expect(response.voice_asr_tts_inspector.sample_asr_events).toEqual([]);
      expect(response.voice_asr_tts_inspector.asr_event_count).toBe(0);
      expect(response.voice_asr_tts_inspector.asr_stream_connected).toBe(false);
      expect(response.voice_asr_tts_inspector.tts_send_enabled).toBe(false);
      expect(response.voice_asr_tts_inspector.speaker_dispatch_enabled).toBe(false);
      expect(response.voice_asr_tts_inspector.real_voice_api_connected).toBe(false);
      expect(response.voice_asr_tts_inspector.real_asr_tts_runtime_connected).toBe(false);
      expect(response.voice_asr_tts_inspector.speaker_dispatch.sends_to_robot).toBe(false);
      expect(response.safe_command_inspector.status).toBe("blocked_not_proven");
      expect(response.safe_command_inspector.sample_commands).toEqual([]);
      expect(response.safe_command_inspector.command_dispatch_enabled).toBe(false);
      expect(response.safe_command_inspector.manual_control_enabled).toBe(false);
      expect(response.safe_command_inspector.navigate_goal_enabled).toBe(false);
      expect(response.safe_command_inspector.keyboard_control_enabled).toBe(false);
      expect(response.safe_command_inspector.real_command_api_connected).toBe(false);
      expect(response.safe_command_inspector.real_robot_ack_connected).toBe(false);
      expect(response.safe_command_inspector.robot_control_executed).toBe(false);
      expect(response.safe_command_inspector.safe_to_control).toBe(false);
      expect(response.safe_command_inspector.primary_actions_enabled).toBe(false);
      expect(response.safe_command_inspector.delivery_success).toBe(false);
      expect(response.safe_summaries.commands.robot_control_executed).toBe(false);
      expect(response.blocked_reasons.length).toBeGreaterThan(0);
      expectNoLegacyPythonGateSemantics(response);
    }
  });

  it("O7 cloud archive tasks derives minimal labeling queue from labels only", async () => {
    // 旧 archive 只有 labels[] 时也要给 KR4 一个可检查 item/draft 摘要，而不是只返回 label count。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-cloud-labels-only-"));
    const archivePath = path.join(root, "archive-labels-only.json");
    await writeFile(archivePath, JSON.stringify({
      schema: "trashbot.o7.cloud_archive_fixture.v1",
      selected_task_id: "task-labels-only",
      tasks: [
        {
          task_id: "task-labels-only",
          robot_id: "robot-fixture-01",
          route_id: "route-labels",
          status: "labels_only_fixture",
          labels: [
            {
              frame_id: "frame-a",
              media_ref: path.join(root, "frame-a.jpg"),
              label_type: "floor_label",
              value: "F2",
              status: "fixture_existing",
              evidence_ref: path.join(root, "label-a.json"),
            },
            { type: "obstacle_type", label: "cart", status: "fixture_existing", evidence_ref: "label-b.json" },
          ],
          asr_events: [{ type: "final", text: "到达电梯口", timestamp_ms: 100, confidence: 0.8 }],
          tts_draft: { text: "单对象草稿只读摘要", voice_profile: "single-profile", language: "zh-CN" },
        },
      ],
    }), "utf8");

    const response = await buildO7CloudArchiveTasks({ archiveJson: archivePath });

    expect(response.labeling_queue_inspector.status).toBe("fixture_labeling_ready");
    expect(response.labeling_queue_inspector.review_item_count).toBe(2);
    expect(response.labeling_queue_inspector.sample_review_items[0]).toMatchObject({
      item_id: "label_item_1",
      task_id: "task-labels-only",
      frame_id: "frame-a",
      media_ref: "file:frame-a.jpg",
      evidence_ref: "file:label-a.json",
      current_labels: {
        count: 1,
        sample: [
          { label_type: "floor_label", value: "F2", status: "fixture_existing", evidence_ref: "file:label-a.json" },
        ],
      },
    });
    expect(response.labeling_queue_inspector.allowed_label_types).toEqual(["floor_label", "obstacle_type"]);
    expect(response.labeling_queue_inspector.draft_labels.count).toBe(2);
    expect(response.labeling_queue_inspector.draft_labels.autosave_available).toBe(false);
    expect(response.voice_asr_tts_inspector.status).toBe("fixture_voice_ready");
    expect(response.voice_asr_tts_inspector.tts_draft.voice_profile).toBe("single-profile");
    expect(response.voice_asr_tts_inspector.latest_final.text).toBe("到达电梯口");
    expect(JSON.stringify(response)).not.toContain(root);
  });

  it("O7 cloud archive tasks endpoint returns read-only local fixture summary", async () => {
    // endpoint 通过 Express 路由验证 query 参数，不启动生产云端或任何控制链路。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-cloud-archive-http-"));
    const archivePath = path.join(root, "archive-http.json");
    await writeFile(archivePath, JSON.stringify(sampleCloudArchiveFixture(path.join(root, "task-archive-002.json"))), "utf8");
    const server = await listen(createWorkstationApp());

    try {
      const url = new URL("/api/o7/cloud-archive/tasks", server.baseUrl);
      url.searchParams.set("archiveJson", archivePath);
      const response = await fetch(url);
      const body = (await response.json()) as Awaited<ReturnType<typeof buildO7CloudArchiveTasks>>;

      expect(response.status).toBe(200);
      expect(body.schema).toBe("trashbot.o7.cloud_archive_tasks.v1");
      expect(body.input_status.status).toBe("loaded");
      expect(body.selected_task?.task_id).toBe("task-archive-002");
      expect(body.real_cloud_archive_connected).toBe(false);
      expect(body.real_annotation_api_connected).toBe(false);
      expect(body.real_voice_api_connected).toBe(false);
      expect(body.real_command_api_connected).toBe(false);
      expect(body.robot_control_executed).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer read adapters use O6 list/detail primary path with fixed strategy", async () => {
    // adapter 只验证 O7 PC 对 O6 consumer read 的主入口拼接，不证明真实云、真实控制或真实交付。
    const listPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_list: {
        tasks: [
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
      },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      field_evidence_manifest: sampleFieldEvidenceManifest("/tmp/consumer-task-001", "consumer-field-evidence-001"),
      task_summary: {
        task_id: "task-consumer-001",
        robot_id: "robot_fixture",
        task_status_summary: "completed_mock",
        started_at_ms: 1000,
        finished_at_ms: 2000,
      },
      trajectory: { status: "loaded_not_proven", frame_count: 3, frames: [{ frame_index: 0, x_m: 1.0 }] },
      events: { status: "loaded_not_proven", count: 2, items: [{ event_type: "route.frame" }] },
      evidence: { status: "loaded_not_proven", count: 1, items: [{ evidence_type: "snapshot" }] },
      labeling: { status: "partial", label_count: 1, items: [{ item_id: "label-1" }] },
      inference: { status: "present", count: 1, items: [{ result_type: "floor_recognition" }] },
      tunnel_status: {
        status: "loaded_not_proven",
        latest_known_status: "online",
        temporal_alignment: "latest_known_robot_snapshot_not_task_aligned",
      },
      blocked_reasons: [],
      not_proven: ["robot_control_executed=false"],
    };
    const server = await listenConsumerRead(listPayload, detailPayload);

    try {
      const list = await buildO7ConsumerTaskList(server.baseUrl);
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-001");

      expect(list.schema).toBe("trashbot.pc_tools_workstation.o7_consumer_task_list.v1");
      expect(list.remote_endpoint).toBe("/api/o6/consumer/tasks?view=summary&limit=50");
      expect(list.query_strategy.view).toBe("summary");
      expect(list.query_strategy.include).toEqual([]);
      expect(list.task_list[0]).toMatchObject({
        task_id: "task-consumer-001",
        labeling_status: "partial",
        inference_status: "present",
        tunnel_status_summary: "online",
      });
      expect(list.safe_to_control).toBe(false);

      expect(detail.schema).toBe("trashbot.pc_tools_workstation.o7_consumer_task_detail.v1");
      expect(detail.remote_endpoint).toBe(
        "/api/o6/consumer/tasks/task-consumer-001?view=default&include=trajectory,events,evidence,labeling,inference,tunnel",
      );
      expect(detail.query_strategy.include).toEqual([
        "trajectory",
        "events",
        "evidence",
        "labeling",
        "inference",
        "tunnel",
      ]);
      expect(detail.field_evidence.source_contract).toBe("trashbot.field_evidence_manifest.v1");
      expect(detail.field_evidence.input_status).toBe("loaded");
      expect(detail.field_evidence.artifact_status).toBe("gated");
      expect(detail.field_evidence.manifest_gate.status).toBe("gated");
      expect(detail.field_evidence.not_proven).toBe(true);
      expect(detail.field_evidence.safe_to_control).toBe(false);
      expect(detail.task_summary?.task_id).toBe("task-consumer-001");
      expect(detail.trajectory.frame_count).toBe(3);
      expect(detail.tunnel_status.temporal_alignment).toBe("latest_known_robot_snapshot_not_task_aligned");
      expect(detail.connects_cloud_production).toBe(false);
      expect(detail.robot_control_executed).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer detail accepts existing field evidence ingest contract and reuses manifest gate", async () => {
    // 兼容已有 ingest contract，避免 O6 detail 已接入旧摘要时还需要前端重新 join 本地 fixture。
    const listPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_list: { tasks: [{ task_id: "task-consumer-ingest-001", robot_id: "robot_fixture" }] },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      field_evidence_consumer_ingest: {
        schema: "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1",
        manifest: sampleFieldEvidenceManifest("/tmp/consumer-task-ingest-001", "consumer-field-evidence-002"),
      },
      task_summary: { task_id: "task-consumer-ingest-001", robot_id: "robot_fixture", task_status_summary: "completed_mock" },
      trajectory: { status: "loaded_not_proven", frame_count: 0, frames: [] },
      events: { status: "loaded_not_proven", count: 0, items: [] },
      evidence: { status: "loaded_not_proven", count: 0, items: [] },
      labeling: { status: "pending", label_count: 0, items: [] },
      inference: { status: "absent", count: 0, items: [] },
      tunnel_status: { status: "blocked_not_proven", latest_known_status: "blocked_not_proven" },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const server = await listenConsumerRead(listPayload, detailPayload);

    try {
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-ingest-001");

      expect(detail.detail_status).toBe("loaded_fail_closed_summary");
      expect(detail.field_evidence.source_contract).toBe(
        "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1",
      );
      expect(detail.field_evidence.input_status).toBe("loaded");
      expect(detail.field_evidence.manifest_gate.status).toBe("gated");
      expect(detail.field_evidence.artifact_status).toBe("gated");
      expect(detail.field_evidence.delivery_success).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer detail fills missing field evidence from valid local manifest without replacing remote detail sections", async () => {
    // 本地 manifest 只补 field_evidence，trajectory/events/evidence/labeling/inference/tunnel 仍来自 O6 detail。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-consumer-local-manifest-"));
    const manifestPath = path.join(root, "field-evidence-manifest.json");
    await writeFile(
      manifestPath,
      JSON.stringify(sampleFieldEvidenceManifest("/tmp/consumer-task-local-001", "consumer-field-evidence-local")),
      "utf8",
    );
    const listPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_list: { tasks: [{ task_id: "task-consumer-local-001", robot_id: "robot_fixture" }] },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_summary: {
        task_id: "task-consumer-local-001",
        robot_id: "robot_fixture",
        task_status_summary: "completed_mock",
      },
      trajectory: { status: "remote_trajectory_loaded", frame_count: 7, frames: [{ frame_index: 6, x_m: 4.2 }] },
      events: { status: "remote_events_loaded", count: 2, items: [{ event_type: "remote_event" }] },
      evidence: { status: "remote_evidence_loaded", count: 1, items: [{ evidence_type: "remote_snapshot" }] },
      labeling: { status: "remote_labeling_loaded", label_count: 1, items: [{ item_id: "remote_label" }] },
      inference: { status: "remote_inference_loaded", count: 1, items: [{ result_type: "remote_inference" }] },
      tunnel_status: {
        status: "remote_tunnel_loaded",
        latest_known_status: "online",
        temporal_alignment: "latest_known_robot_snapshot_not_task_aligned",
      },
      blocked_reasons: [],
      not_proven: ["robot_control_executed=false"],
    };
    const server = await listenConsumerRead(listPayload, detailPayload);

    try {
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-local-001", manifestPath);

      expect(detail.detail_status).toBe("loaded_fail_closed_summary");
      expect(detail.field_evidence.source_contract).toBe("trashbot.field_evidence_manifest.v1");
      expect(detail.field_evidence.input_status).toBe("loaded");
      expect(detail.field_evidence.manifest_gate.status).toBe("gated");
      expect(detail.trajectory.status).toBe("remote_trajectory_loaded");
      expect(detail.trajectory.frame_count).toBe(7);
      expect(detail.events.sample_events[0]?.event_type).toBe("remote_event");
      expect(detail.evidence.sample_evidence[0]?.evidence_type).toBe("remote_snapshot");
      expect(detail.labeling.sample_items[0]?.item_id).toBe("remote_label");
      expect(detail.inference.sample_results[0]?.result_type).toBe("remote_inference");
      expect(detail.tunnel_status.status).toBe("remote_tunnel_loaded");
      expect(detail.safe_to_control).toBe(false);
      expect(detail.primary_actions_enabled).toBe(false);
      expect(detail.delivery_success).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer detail prefers valid remote field evidence over a provided local manifest", async () => {
    // 远端已有合法 field evidence 时，本地 query 不能覆盖 O6 detail 给出的证据合同。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-consumer-remote-priority-"));
    const localManifestPath = path.join(root, "local-field-evidence.json");
    await writeFile(
      localManifestPath,
      JSON.stringify(sampleFieldEvidenceManifest("/tmp/local-manifest", "local-field-evidence")),
      "utf8",
    );
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      field_evidence_manifest: sampleFieldEvidenceManifest("/tmp/remote-manifest", "remote-field-evidence"),
      task_summary: { task_id: "task-consumer-remote-priority", robot_id: "robot_fixture", task_status_summary: "completed_mock" },
      trajectory: { status: "loaded_not_proven", frame_count: 0, frames: [] },
      events: { status: "loaded_not_proven", count: 0, items: [] },
      evidence: { status: "loaded_not_proven", count: 0, items: [] },
      labeling: { status: "pending", label_count: 0, items: [] },
      inference: { status: "absent", count: 0, items: [] },
      tunnel_status: { status: "blocked_not_proven", latest_known_status: "blocked_not_proven" },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const server = await listenConsumerRead(
      { schema: "trashbot.o6.consumer_read.v1", task_list: { tasks: [] }, blocked_reasons: [], not_proven: [] },
      detailPayload,
    );

    try {
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-remote-priority", localManifestPath);

      expect(detail.detail_status).toBe("loaded_fail_closed_summary");
      expect(detail.field_evidence.manifest_gate.blocked_reason).toBe("preflight_ready_not_delivery_proof");
      expect(detail.field_evidence.source_contract).toBe("trashbot.field_evidence_manifest.v1");
      expect(detail.field_evidence.input_status).toBe("loaded");
    } finally {
      await server.close();
    }
  });

  it("O7 consumer detail fails closed when remote field evidence and local manifest are missing", async () => {
    // 远端缺 field evidence 时必须要求本地 manifest；未提供 query 仍不能继续给出“可读成功”摘要。
    const listPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_list: { tasks: [{ task_id: "task-consumer-missing-field-evidence", robot_id: "robot_fixture" }] },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_summary: {
        task_id: "task-consumer-missing-field-evidence",
        robot_id: "robot_fixture",
        task_status_summary: "completed_mock",
      },
      trajectory: { status: "loaded_not_proven", frame_count: 0, frames: [] },
      events: { status: "loaded_not_proven", count: 0, items: [] },
      evidence: { status: "loaded_not_proven", count: 0, items: [] },
      labeling: { status: "pending", label_count: 0, items: [] },
      inference: { status: "absent", count: 0, items: [] },
      tunnel_status: { status: "blocked_not_proven", latest_known_status: "blocked_not_proven" },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const server = await listenConsumerRead(listPayload, detailPayload);

    try {
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-missing-field-evidence");

      expect(detail.detail_status).toBe("fail_closed");
      expect(detail.fail_closed_reason).toBe("field_evidence_manifest_json_not_provided");
      expect(detail.field_evidence.input_status).toBe("not_provided");
      expect(detail.field_evidence.artifact_status).toBe("blocked");
      expect(detail.safe_to_control).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer detail fails closed for unsafe local manifest when remote field evidence is missing", async () => {
    // 本地 manifest 出现控制/成功 true 声明时必须 fail-closed，不能补齐 field_evidence。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-consumer-unsafe-manifest-"));
    const manifestPath = path.join(root, "unsafe-field-evidence.json");
    await writeFile(
      manifestPath,
      JSON.stringify({
        ...sampleFieldEvidenceManifest("/tmp/unsafe-manifest", "unsafe-field-evidence"),
        safe_to_control: true,
      }),
      "utf8",
    );
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_summary: { task_id: "task-consumer-unsafe-local", robot_id: "robot_fixture", task_status_summary: "completed_mock" },
      trajectory: { status: "loaded_not_proven", frame_count: 0, frames: [] },
      events: { status: "loaded_not_proven", count: 0, items: [] },
      evidence: { status: "loaded_not_proven", count: 0, items: [] },
      labeling: { status: "pending", label_count: 0, items: [] },
      inference: { status: "absent", count: 0, items: [] },
      tunnel_status: { status: "blocked_not_proven", latest_known_status: "blocked_not_proven" },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const server = await listenConsumerRead(
      { schema: "trashbot.o6.consumer_read.v1", task_list: { tasks: [] }, blocked_reasons: [], not_proven: [] },
      detailPayload,
    );

    try {
      const detail = await buildO7ConsumerTaskDetail(server.baseUrl, "task-consumer-unsafe-local", manifestPath);

      expect(detail.detail_status).toBe("fail_closed");
      expect(detail.fail_closed_reason).toBe("field_evidence_manifest_json_success_claim");
      expect(detail.field_evidence.input_status).toBe("unsafe_claim");
      expect(detail.safe_to_control).toBe(false);
      expect(detail.primary_actions_enabled).toBe(false);
      expect(detail.delivery_success).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 consumer read HTTP endpoints expose workstation adapter contract", async () => {
    // Express 路由测试确认 PC 端入口已经挂到 workstation，而不是让浏览器直接打 relay。
    const listPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      task_list: { tasks: [{ task_id: "task-consumer-001", robot_id: "robot_fixture" }] },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const detailPayload = {
      schema: "trashbot.o6.consumer_read.v1",
      field_evidence_manifest: sampleFieldEvidenceManifest("/tmp/consumer-task-001", "consumer-field-evidence-001"),
      task_summary: { task_id: "task-consumer-001", robot_id: "robot_fixture", task_status_summary: "completed_mock" },
      trajectory: { status: "loaded_not_proven", frame_count: 0, frames: [] },
      events: { status: "loaded_not_proven", count: 0, items: [] },
      evidence: { status: "loaded_not_proven", count: 0, items: [] },
      labeling: { status: "pending", label_count: 0, items: [] },
      inference: { status: "absent", count: 0, items: [] },
      tunnel_status: { status: "blocked_not_proven", latest_known_status: "blocked_not_proven" },
      blocked_reasons: [],
      not_proven: ["proof_status=not_proven"],
    };
    const upstream = await listenConsumerRead(listPayload, detailPayload);
    const workstation = await listen(createWorkstationApp());

    try {
      const listUrl = new URL("/api/o7/consumer-read/tasks", workstation.baseUrl);
      listUrl.searchParams.set("baseUrl", upstream.baseUrl);
      const listResponse = await fetch(listUrl);
      const listBody = (await listResponse.json()) as Awaited<ReturnType<typeof buildO7ConsumerTaskList>>;

      const detailUrl = new URL("/api/o7/consumer-read/tasks/task-consumer-001", workstation.baseUrl);
      detailUrl.searchParams.set("baseUrl", upstream.baseUrl);
      const detailResponse = await fetch(detailUrl);
      const detailBody = (await detailResponse.json()) as Awaited<ReturnType<typeof buildO7ConsumerTaskDetail>>;

      expect(listResponse.status).toBe(200);
      expect(listBody.schema).toBe("trashbot.pc_tools_workstation.o7_consumer_task_list.v1");
      expect(listBody.task_list[0]?.task_id).toBe("task-consumer-001");
      expect(detailResponse.status).toBe(200);
      expect(detailBody.schema).toBe("trashbot.pc_tools_workstation.o7_consumer_task_detail.v1");
      expect(detailBody.requested_task_id).toBe("task-consumer-001");
      expect(detailBody.query_strategy.include).toEqual([
        "trajectory",
        "events",
        "evidence",
        "labeling",
        "inference",
        "tunnel",
      ]);
    } finally {
      await upstream.close();
      await workstation.close();
    }
  });

  it("Robot Control summary proxies Robot API readback endpoints and keeps commands locked", async () => {
    // Robot API fixture server 只返回只读 JSON；测试不调用 /api/base/manual 或任何 POST endpoint。
    const robotApi = await listenRobotApiReadback({
      schema: "trashbot.upper_robot_api.v1.status",
      status: "blocked_with_root_cause",
      evidence_ref: "robot-control-test-proof",
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
      root_causes: [{ layer: "Nav2", reason: "planner_server_not_active" }],
      not_proven: ["path_generated", "delivery_success"],
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      publishes_cmd_vel: false,
      calls_base_manual: false,
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.schema).toBe("trashbot.pc_tools_workstation.robot_control_summary.v1");
      expect(summary.proxy_policy.node_proxy_only).toBe(true);
      expect(summary.proxy_policy.vue_direct_robot_api_access).toBe(false);
      expect(summary.robot_api_connection.loaded_count).toBeGreaterThan(0);
      expect(summary.read_endpoints.some((endpoint) => endpoint.endpoint === "/api/status")).toBe(true);
      expect(summary.read_endpoints.some((endpoint) => endpoint.endpoint === "/api/base/status")).toBe(true);
      expect(summary.o3_proof_summary.path_generated).toBe(false);
      expect(summary.o3_proof_summary.path_generation_succeeded).toBe(false);
      expect(summary.safe_command_boundary.manual_endpoint).toBe("/api/base/manual");
      expect(summary.safe_command_boundary.cmd_vel_topic).toBe("/cmd_vel");
      expect(summary.safe_command_boundary.manual_control_enabled).toBe(false);
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
      expect(summary.primary_actions_enabled).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary rejects unsafe URLs and dangerous true fields", async () => {
    // URL 和 payload 任一层不安全都必须 fail-closed，防止控制台被误用为控制代理。
    const missing = await buildRobotControlSummary("");
    expect(missing.console_status).toBe("blocked");
    expect(missing.blocked_reasons).toContain("baseUrl_not_provided");

    const unsafeUrl = await buildRobotControlSummary("https://127.0.0.1:8787?token=secret");
    expect(unsafeUrl.console_status).toBe("blocked");
    expect(unsafeUrl.blocked_reasons).toContain("baseUrl_protocol_not_allowed");

    const robotApi = await listenRobotApiReadback({
      schema: "trashbot.upper_robot_api.v1.status",
      status: "unsafe_control_claim",
      safe_to_control: true,
      delivery_success: false,
      primary_actions_enabled: false,
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      expect(summary.console_status).toBe("blocked");
      expect(summary.robot_api_connection.dangerous_true_fields.some((field) => field.includes("safe_to_control"))).toBe(true);
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("O7 operator console acceptance guard summarizes fail-closed snapshots", () => {
    // Acceptance guard 从 source builder 派生，复核六个 KR snapshot 和禁用入口仍然关闸。
    const acceptance = buildO7OperatorConsoleAcceptanceResponse();

    expect(acceptance.schema).toBe("trashbot.o7.operator_console_acceptance.v1");
    expect(acceptance.source_response_schema).toBe("trashbot.o7.operator_console.v1");
    expect(acceptance.source_endpoint).toBe("/api/o7/operator-console");
    expect(acceptance.guard_endpoint).toBe("/api/o7/operator-console/acceptance");
    expect(acceptance.evidence_boundary).toBe("software_proof_o7_operator_console_acceptance_guard");
    expect(acceptance.safe_to_control).toBe(false);
    expect(acceptance.primary_actions_enabled).toBe(false);
    expect(acceptance.delivery_success).toBe(false);
    expect(acceptance.reads_hardware).toBe(false);
    expect(acceptance.sends_commands).toBe(false);
    expect(acceptance.connects_cloud_production).toBe(false);
    expect(acceptance.six_kr_snapshots_present).toBe(true);
    expect(acceptance.snapshot_schema_keys).toEqual([
      "board_media_preflight_summary",
      "realtime_map_snapshot",
      "elevator_state_snapshot",
      "route_replay_snapshot",
      "labeling_queue_snapshot",
      "voice_asr_tts_snapshot",
      "safe_command_snapshot",
    ]);
    expect(Object.values(acceptance.snapshot_schemas)).toEqual(
      expect.arrayContaining([
        "trashbot.o7_board_media_preflight.v1",
        "trashbot.o7.realtime_map_snapshot.v1",
        "trashbot.o7.elevator_state_snapshot.v1",
        "trashbot.o7.route_replay_snapshot.v1",
        "trashbot.o7.labeling_queue_snapshot.v1",
        "trashbot.o7.voice_asr_tts_snapshot.v1",
        "trashbot.o7.safe_command_snapshot.v1",
      ]),
    );
    expect(acceptance.fail_closed_checks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "top_level_safe_to_control", actual: false }),
        expect.objectContaining({ id: "top_level_primary_actions_enabled", actual: false }),
        expect.objectContaining({ id: "top_level_delivery_success", actual: false }),
      ]),
    );
    expect(acceptance.disabled_entry_checks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "safe_command_command_dispatch_enabled", actual: false }),
        expect.objectContaining({ id: "safe_command_manual_control_enabled", actual: false }),
        expect.objectContaining({ id: "safe_command_navigate_goal_enabled", actual: false }),
        expect.objectContaining({ id: "safe_command_keyboard_control_enabled", actual: false }),
        expect.objectContaining({ id: "voice_tts_send_enabled", actual: false }),
        expect.objectContaining({ id: "labeling_submit_enabled", actual: false }),
        expect.objectContaining({ id: "route_replay_playback_available", actual: false }),
      ]),
    );
    expect(acceptance.dangerous_marker_scan.markers_absent).toBe(true);
    expect(acceptance.dangerous_marker_scan.matched_marker_ids).toEqual([]);
    expect(acceptance.acceptance_verdict).toBe("blocked_not_proven_guard_ok");
    expect(acceptance.not_real_capability_proof).toBe(true);
    expect(acceptance.remaining_gaps).toContain("real_safe_command_dispatch_not_proven");
    expect(JSON.stringify(acceptance)).not.toContain("/cmd_vel");
    expect(JSON.stringify(acceptance)).not.toContain("/dev/ttyUSB");
    expect(JSON.stringify(acceptance)).not.toContain("/dev/ttyACM");
    expect(JSON.stringify(acceptance)).not.toMatch(/ready[_ -]?to[_ -]?control/i);
    expect(JSON.stringify(acceptance)).not.toContain("delivery_success=true");
    expect(JSON.stringify(acceptance)).not.toContain("command_dispatch_enabled=true");
  });

  it("O7 previews acceptance guard summarizes PC-only preview readiness boundaries", async () => {
    // Previews guard 不读取 fixture、不探测云端；这里只验证静态合同与 Express 路由保持一致。
    const acceptance = buildO7PreviewsAcceptanceResponse();

    expect(acceptance.schema).toBe("trashbot.o7.previews_acceptance.v1");
    expect(acceptance.guard_endpoint).toBe("/api/o7/previews/acceptance");
    expect(acceptance.evidence_boundary).toBe("software_proof_o7_previews_acceptance_guard");
    expect(acceptance.acceptance_verdict).toBe("blocked_not_proven_guard_ok");
    expect(acceptance.not_real_capability_proof).toBe(true);
    expect(acceptance.reads_hardware).toBe(false);
    expect(acceptance.sends_commands).toBe(false);
    expect(acceptance.connects_cloud_production).toBe(false);
    expect(acceptance.safe_to_control).toBe(false);
    expect(acceptance.delivery_success).toBe(false);
    expect(acceptance.primary_actions_enabled).toBe(false);
    expect(acceptance.covered_surface_ids).toEqual([
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
    ]);
    expect(acceptance.surfaces).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "rtc_signaling_contract_probe",
          source_endpoint: "/api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>",
          ui_surface: "RTC signaling contract probe",
          evidence_boundary: "local_http_contract_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining([
            "real_rtc_signaling_session_not_created",
            "webrtc_media_transport_not_connected",
            "ros2_tf_not_connected",
          ]),
          not_proven: expect.arrayContaining([
            "real_rtc_signaling_session",
            "real_webrtc_media_transport",
            "real_rtc_video",
            "real_realtime_pose_stream",
            "real_ros2_tf",
          ]),
        }),
        expect.objectContaining({
          id: "realtime_map_pose_preview",
          evidence_boundary: "local_http_contract_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["real_ros2_tf_connected_false"]),
          not_proven: expect.arrayContaining(["real_realtime_map_pose"]),
        }),
        expect.objectContaining({
          id: "elevator_state_timeline_preview",
          evidence_boundary: "local_http_contract_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["real_elevator_state_chain_connected_false"]),
          not_proven: expect.arrayContaining(["real_elevator_state_chain"]),
        }),
        expect.objectContaining({
          id: "route_replay_trajectory_minimap",
          evidence_boundary: "local_fixture_cursor_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["playback_available_false"]),
          not_proven: expect.arrayContaining(["real_map_overlay"]),
        }),
        expect.objectContaining({
          id: "local_draft_annotation_editor",
          evidence_boundary: "local_fixture_cursor_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["submit_enabled_false", "real_annotation_api_connected_false"]),
          not_proven: expect.arrayContaining(["real_draft_autosave"]),
        }),
        expect.objectContaining({
          id: "local_tts_draft_editor",
          evidence_boundary: "local_fixture_cursor_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["tts_send_enabled_false", "real_voice_api_connected_false"]),
          not_proven: expect.arrayContaining(["real_tts_send"]),
        }),
        expect.objectContaining({
          id: "local_safe_command_draft_editor",
          evidence_boundary: "local_fixture_cursor_only",
          acceptance_status: "blocked_not_proven",
          blocked_reasons: expect.arrayContaining(["command_dispatch_enabled_false", "robot_control_executed_false"]),
          not_proven: expect.arrayContaining(["real_robot_ack"]),
        }),
      ]),
    );
    expect(acceptance.fixed_false_fields).toMatchObject({
      playback_available: false,
      submit_enabled: false,
      tts_send_enabled: false,
      command_dispatch_enabled: false,
      manual_control_enabled: false,
      navigate_goal_enabled: false,
      keyboard_control_enabled: false,
      robot_control_executed: false,
      real_realtime_api_connected: false,
      real_cloud_archive_connected: false,
      real_robot_ack_connected: false,
    });
    expect(acceptance.fail_closed_checks.every((check) => check.actual === false)).toBe(true);
    expect(acceptance.not_proven).toEqual(
      expect.arrayContaining(["real_rtc_video_connected", "real_manual_control_or_navigate_goal", "real_hardware_hil"]),
    );
    expect(acceptance.remaining_real_capability_gaps).toEqual(
      expect.arrayContaining(["rtc_signaling_contract_probe_does_not_prove_real_rtc_video_or_media_transport"]),
    );

    const server = await listen(createWorkstationApp());
    try {
      const response = await fetch(new URL("/api/o7/previews/acceptance", server.baseUrl));
      const body = (await response.json()) as ReturnType<typeof buildO7PreviewsAcceptanceResponse>;

      expect(response.status).toBe(200);
      expect(body.schema).toBe("trashbot.o7.previews_acceptance.v1");
      expect(body.covered_surface_ids).toEqual(acceptance.covered_surface_ids);
      expect(body.fixed_false_fields.command_dispatch_enabled).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 live endpoints manifest reads env only and redacts URLs and tokens", async () => {
    // manifest 只读取环境变量并输出脱敏 readiness，不探测网络、不暴露 token 值。
    const empty = buildO7LiveEndpointsManifest({});

    expect(empty.schema).toBe("trashbot.o7.live_endpoints_manifest.v1");
    expect(empty.endpoint).toBe("/api/o7/live-endpoints/manifest");
    expect(empty.env_only).toBe(true);
    expect(empty.network_probe_executed).toBe(false);
    expect(empty.sends_commands).toBe(false);
    expect(empty.safe_to_control).toBe(false);
    expect(empty.connects_cloud_production).toBe(false);
    expect(empty.robot_control_executed).toBe(false);
    expect(empty.reads_hardware).toBe(false);
    expect(empty.token_values_exposed).toBe(false);
    expect(empty.url_query_hash_credentials_exposed).toBe(false);
    expect(empty.summary).toMatchObject({ configured: 0, not_configured: 6, blocked: 0, token_present: 0, token_absent: 6 });
    expect(empty.capabilities.every((capability) => capability.status === "not_configured")).toBe(true);
    expect(empty.capabilities.every((capability) => capability.proof_status === "not_proven")).toBe(true);
    expect(empty.capabilities.map((capability) => capability.id)).toEqual([
      "rtc_realtime_pose_elevator",
      "cloud_archive",
      "route_replay_source",
      "annotation_submit_api",
      "voice_asr_tts_api",
      "safe_command_api",
    ]);
    expect(JSON.stringify(empty)).not.toContain("secret");

    const configured = buildO7LiveEndpointsManifest({
      O7_RTC_REALTIME_URL: "wss://relay.example.test/o7/realtime",
      O7_RTC_REALTIME_TOKEN: "secret-rtc-token",
      O7_CLOUD_ARCHIVE_URL: "https://archive.example.test/api/o7/tasks",
      O7_CLOUD_ARCHIVE_TOKEN: "secret-archive-token",
      O7_ROUTE_REPLAY_URL: "https://user:pass@replay.example.test/api?token=leak#frag",
      O7_ANNOTATION_API_URL: "https://annotation.example.test/api/o7/labels?token=leak",
      O7_VOICE_API_URL: "ftp://voice.example.test/api",
      O7_SAFE_COMMAND_API_URL: "https://command.example.test/api/o7/commands",
    });

    expect(configured.summary).toMatchObject({ configured: 3, not_configured: 0, blocked: 3, token_present: 2, token_absent: 4 });
    expect(configured.capabilities[0]?.url.display_url).toBe("wss://relay.example.test/o7/realtime");
    expect(configured.capabilities[0]?.token.status).toBe("present");
    expect(configured.capabilities[0]?.url.display_url).not.toContain("secret-rtc-token");
    expect(configured.capabilities[2]?.status).toBe("blocked");
    expect(configured.capabilities[2]?.url.display_url).toBe("blocked_unsafe_url");
    expect(configured.capabilities[2]?.blocked_reasons).toContain(
      "O7_ROUTE_REPLAY_URL:url_must_not_include_credentials_query_or_hash",
    );
    expect(configured.capabilities[3]?.blocked_reasons).toContain(
      "O7_ANNOTATION_API_URL:url_must_not_include_credentials_query_or_hash",
    );
    expect(configured.capabilities[4]?.blocked_reasons).toContain("O7_VOICE_API_URL:protocol_not_allowed");
    expect(JSON.stringify(configured)).not.toContain("secret-rtc-token");
    expect(JSON.stringify(configured)).not.toContain("user:pass");
    expect(JSON.stringify(configured)).not.toContain("token=leak");
    expect(configured.required_live_evidence).toEqual(expect.arrayContaining(["rtc_signaling_trace", "idempotent_command_api_trace"]));
    expect(configured.remaining_real_capability_gaps).toEqual(
      expect.arrayContaining(["real_rtc_video_connected", "real_robot_ack_connected"]),
    );

    const server = await listen(createWorkstationApp());
    try {
      const response = await fetch(new URL("/api/o7/live-endpoints/manifest", server.baseUrl));
      const body = (await response.json()) as ReturnType<typeof buildO7LiveEndpointsManifest>;

      expect(response.status).toBe(200);
      expect(body.schema).toBe("trashbot.o7.live_endpoints_manifest.v1");
      expect(body.network_probe_executed).toBe(false);
      expect(body.sends_commands).toBe(false);
    } finally {
      await server.close();
    }
  });

  it("O7 cloud operator console probe only accepts loopback and keeps dangerous fields closed", async () => {
    // probe 通过真实 PC 后端拉本机 operator-console，验证 SSRF 围栏和 fail-closed 扫描。
    const server = await listen(createWorkstationApp());
    try {
      const probe = await buildO7CloudOperatorConsoleProbe(server.baseUrl);

      expect(probe.schema).toBe("trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1");
      expect(probe.probe_status).toBe("loaded_fail_closed_contract");
      expect(probe.source_base_url).toBe(server.baseUrl);
      expect(probe.remote_schema).toBe("trashbot.o7.operator_console.v1");
      expect(probe.cloud_api_status).toBe("draft_blocked_not_proven");
      expect(probe.operator_mode).toBe("observe_only");
      expect(probe.kr_ids).toEqual(["O7-KR1", "O7-KR2", "O7-KR3", "O7-KR4", "O7-KR5", "O7-KR6"]);
      expect(probe.key_false_fields).toEqual(expect.arrayContaining(["safe_to_control=false", "delivery_success=false"]));
      expect(probe.sends_commands).toBe(false);
      expect(probe.connects_cloud_production).toBe(false);
      expect(probe.reads_hardware).toBe(false);
    } finally {
      await server.close();
    }

    const blocked = await buildO7CloudOperatorConsoleProbe("https://example.com");
    expect(blocked.probe_status).toBe("fail_closed");
    expect(blocked.fail_closed_reason).toBe("baseUrl_protocol_not_allowed");
    expect(blocked.safe_to_control).toBe(false);
    expect(blocked.primary_actions_enabled).toBe(false);
  });

  it("O7 cloud archive tasks probe only accepts loopback and keeps dangerous fields closed", async () => {
    // probe 只拉本机 HTTP contract，不接受公网 URL，也不把 archive contract 解读成可回放/可标注/可控制。
    const server = await listen(createWorkstationApp());
    try {
      const probe = await buildO7CloudArchiveTasksProbe(server.baseUrl);

      expect(probe.schema).toBe("trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1");
      expect(probe.probe_status).toBe("loaded_fail_closed_contract");
      expect(probe.source_base_url).toBe(server.baseUrl);
      expect(probe.remote_schema).toBe("trashbot.o7.cloud_archive_tasks.v1");
      expect(probe.archive_status).toBe("blocked_not_proven");
      expect(probe.task_count).toBe(0);
      expect(probe.selected_task_id).toBeNull();
      expect(probe.latest_task_id).toBeNull();
      expect(probe.inspector_statuses.route_replay).toBe("blocked_not_proven");
      expect(probe.key_false_fields).toEqual(expect.arrayContaining([
        "real_cloud_archive_connected=false",
        "playback_available=false",
        "submit_enabled=false",
        "tts_send_enabled=false",
        "command_dispatch_enabled=false",
      ]));
      expect(probe.dangerous_true_fields).toEqual([]);
      expect(probe.sends_commands).toBe(false);
      expect(probe.connects_cloud_production).toBe(false);
      expect(probe.reads_hardware).toBe(false);
    } finally {
      await server.close();
    }

    const blocked = await buildO7CloudArchiveTasksProbe("https://example.com");
    expect(blocked.probe_status).toBe("fail_closed");
    expect(blocked.fail_closed_reason).toBe("baseUrl_protocol_not_allowed");
    expect(blocked.safe_to_control).toBe(false);
    expect(blocked.primary_actions_enabled).toBe(false);
  });

  it("O7 cloud archive tasks probe extracts fixture-backed inspector summaries without opening actions", async () => {
    // probe 摘要只读白名单字段，既能看到 KR3-KR6 数据形状，也保持全部操作入口关闭。
    const root = await mkdtemp(path.join(os.tmpdir(), "rober-o7-archive-probe-summary-"));
    const archivePath = path.join(root, "archive-probe.json");
    await writeFile(archivePath, JSON.stringify(sampleCloudArchiveFixture(path.join(root, "task-archive-002.json"))), "utf8");
    const archive = await buildO7CloudArchiveTasks({ archiveJson: archivePath });
    const server = await listenCloudArchive(archive);

    try {
      const probe = await buildO7CloudArchiveTasksProbe(server.baseUrl);

      expect(probe.probe_status).toBe("loaded_fail_closed_contract");
      expect(probe.task_count).toBe(2);
      expect(probe.selected_task_id).toBe("task-archive-002");
      expect(probe.inspector_statuses).toMatchObject({
        route_replay: "fixture_inspector_ready",
        labeling_queue: "fixture_labeling_ready",
        voice_asr_tts: "fixture_voice_ready",
        safe_command: "fixture_command_ready",
      });
      expect(probe.route_replay_summary).toContain("frame_count=6");
      expect(probe.route_replay_summary).toContain("sample_refs=[file:frame-101.jpg,frame-102.jpg,frame-103.jpg]");
      expect(probe.route_replay_summary).toContain("first_frame=departed:file:frame-101.jpg");
      expect(probe.route_replay_summary).toContain("playback_available=false");
      expect(probe.labeling_queue_summary).toContain("review_item_count=6");
      expect(probe.labeling_queue_summary).toContain("label_schema=file:label-schema.json@fixture-v2");
      expect(probe.labeling_queue_summary).toContain("allowed_label_types=[elevator_door_state,floor_label,obstacle_type,trash_type,blocked_reason]");
      expect(probe.labeling_queue_summary).toContain("submit_enabled=false");
      expect(probe.voice_asr_tts_summary).toContain("asr_event_count=6");
      expect(probe.voice_asr_tts_summary).toContain("tts_draft_count=2");
      expect(probe.voice_asr_tts_summary).toContain("tts_text_length=34");
      expect(probe.voice_asr_tts_summary).toContain("tts_send_enabled=false");
      expect(probe.safe_command_summary).toContain("command_count=2");
      expect(probe.safe_command_summary).toContain("manual=fixture_summary_only");
      expect(probe.safe_command_summary).toContain("navigate=fixture_summary_only");
      expect(probe.safe_command_summary).toContain("ack=blocked_not_proven");
      expect(probe.safe_command_summary).toContain("command_dispatch_enabled=false");
      expect(probe.safe_command_summary).toContain("robot_control_executed=false");
      expect(JSON.stringify(probe)).not.toContain(root);
    } finally {
      await server.close();
    }
  });

  it("O7 cloud archive tasks probe still fails closed when fixture-backed response exposes a dangerous true", async () => {
    // 任一远端危险开关为 true 时，即便 summary 可提取，也必须整体 fail_closed。
    const server = await listenCloudArchive({
      schema: "trashbot.o7.cloud_archive_tasks.v1",
      archive_status: "fixture_summary_ready",
      task_list: { total_tasks: 1 },
      selected_task: { task_id: "unsafe-task" },
      latest_task: { task_id: "unsafe-task" },
      safe_summaries: {
        trajectory: { frame_count: 1, sample_refs: ["frame-unsafe.jpg"], status: "fixture_summary_only" },
      },
      route_replay_inspector: {
        status: "fixture_inspector_ready",
        frame_count: 1,
        sample_frames: [{ state: "unsafe", evidence_ref: "frame-unsafe.jpg" }],
        playback_available: true,
      },
      labeling_queue_inspector: { status: "blocked_not_proven", submit_enabled: false },
      voice_asr_tts_inspector: { status: "blocked_not_proven", tts_send_enabled: false },
      safe_command_inspector: { status: "blocked_not_proven", command_dispatch_enabled: false, robot_control_executed: false },
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    });

    try {
      const probe = await buildO7CloudArchiveTasksProbe(server.baseUrl);

      expect(probe.probe_status).toBe("fail_closed");
      expect(probe.fail_closed_reason).toBe("remote_dangerous_true_field");
      expect(probe.dangerous_true_fields).toContain("route_replay_inspector.playback_available");
      expect(probe.blocked_reasons).toContain("dangerous_true:route_replay_inspector.playback_available");
      expect(probe.safe_to_control).toBe(false);
      expect(probe.primary_actions_enabled).toBe(false);
      expect(probe.route_replay_summary).toContain("playback_available=false");
    } finally {
      await server.close();
    }
  });

  it("O7 RTC signaling contract probe only accepts loopback and keeps RTC fields closed", async () => {
    // probe 只拉本机 HTTP 合同入口，不能把协议清单解读成 WebRTC、视频或 ROS2 /tf 已打通。
    const server = await listenRtcContract({
      schema: "trashbot.o7.rtc_signaling_contract.v1",
      schema_version: 1,
      source: "software_proof",
      proof_status: "not_proven",
      endpoint: "/api/o7/rtc-signaling/contract",
      contract_status: "static_fail_closed_contract",
      network_probe_executed: false,
      webrtc_session_created: false,
      media_transport_connected: false,
      video_track_received: false,
      realtime_pose_stream_connected: false,
      real_ros2_tf_connected: false,
      safe_to_control: false,
      sends_commands: false,
      reads_hardware: false,
      robot_control_executed: false,
      delivery_success: false,
      protocol_surfaces: {
        signaling_endpoint: { required: true, method: "POST", path_template: "/api/o7/rtc/signaling/sessions" },
        session_identity: { required: true, session_id_required: true, idempotency_key_required: true },
        offer_answer: { required: true, forbidden_in_this_endpoint: true },
        ice_candidates: { required: true, timeout_semantics_required: true },
        media_tracks: { required: true, video: { required: true, received: false }, audio: { required: false, received: false } },
        pose_realtime_events: { required: true, event_schema: "trashbot.o7.realtime_pose_event.v1" },
        elevator_realtime_events: { required: true, event_schema: "trashbot.o7.elevator_realtime_event.v1" },
        credential_handling: {
          required: true,
          credential_transport_policy: "bearer_header_redacted",
          credential_values_exposed: false,
        },
        observability_evidence_refs: {
          required: true,
          required_refs: ["signaling_trace_ref", "ice_connectivity_trace_ref", "first_video_frame_ref"],
        },
        failure_timeout_semantics: { required: true, required_states: ["signaling_timeout", "ice_failed"] },
        forbidden_actions: {
          command_dispatch: false,
          manual_control: false,
          navigate_goal: false,
          keyboard_control: false,
          hardware_probe: false,
          network_probe_from_contract_endpoint: false,
        },
      },
      blocked_reasons: ["rtc_signaling_endpoint_not_implemented", "video_track_not_received"],
      not_proven: ["real_rtc_signaling_session", "real_webrtc_media_transport", "real_ros2_tf_connected"],
      next_required_evidence: ["robot_side_signaling_client_trace", "pose_event_stream_trace", "ros2_tf_bridge_trace"],
    });

    try {
      const probe = await buildO7RtcSignalingContractProbe(server.baseUrl);

      expect(probe.schema).toBe("trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1");
      expect(probe.probe_status).toBe("loaded_fail_closed_contract");
      expect(probe.source_base_url).toBe(server.baseUrl);
      expect(probe.remote_schema).toBe("trashbot.o7.rtc_signaling_contract.v1");
      expect(probe.contract_status).toBe("static_fail_closed_contract");
      expect(probe.key_false_fields).toEqual(expect.arrayContaining([
        "network_probe_executed=false",
        "webrtc_session_created=false",
        "video_track_received=false",
        "real_ros2_tf_connected=false",
        "sends_commands=false",
        "reads_hardware=false",
      ]));
      expect(probe.protocol_surface_keys).toEqual(expect.arrayContaining([
        "credential_handling",
        "media_tracks",
        "offer_answer",
        "pose_realtime_events",
        "signaling_endpoint",
      ]));
      expect(probe.required_evidence_refs).toEqual(expect.arrayContaining([
        "signaling_trace_ref",
        "first_video_frame_ref",
        "robot_side_signaling_client_trace",
        "ros2_tf_bridge_trace",
      ]));
      expect(probe.dangerous_true_fields).toEqual([]);
      expect(probe.network_probe_executed).toBe(false);
      expect(probe.sends_commands).toBe(false);
      expect(probe.connects_cloud_production).toBe(false);
      expect(probe.reads_hardware).toBe(false);
      expect(JSON.stringify(probe)).not.toContain("bearer_header_redacted");
    } finally {
      await server.close();
    }

    const blocked = await buildO7RtcSignalingContractProbe("http://example.com");
    expect(blocked.probe_status).toBe("fail_closed");
    expect(blocked.fail_closed_reason).toBe("baseUrl_must_be_local_loopback");
    expect(blocked.network_probe_executed).toBe(false);
    expect(blocked.safe_to_control).toBe(false);

    const dangerousServer = await listenRtcContract({
      schema: "trashbot.o7.rtc_signaling_contract.v1",
      contract_status: "unsafe_contract",
      network_probe_executed: true,
      protocol_surfaces: {
        forbidden_actions: { command_dispatch: true },
      },
      blocked_reasons: [],
      not_proven: [],
    });
    try {
      const dangerous = await buildO7RtcSignalingContractProbe(dangerousServer.baseUrl);

      expect(dangerous.probe_status).toBe("fail_closed");
      expect(dangerous.fail_closed_reason).toBe("remote_dangerous_true_field");
      expect(dangerous.dangerous_true_fields).toEqual(expect.arrayContaining([
        "network_probe_executed",
        "protocol_surfaces.forbidden_actions.command_dispatch",
      ]));
      expect(dangerous.blocked_reasons).toContain("dangerous_true:network_probe_executed");
      expect(dangerous.safe_to_control).toBe(false);
      expect(dangerous.sends_commands).toBe(false);
    } finally {
      await dangerousServer.close();
    }
  });

  it("O7 realtime elevator probe only accepts loopback and keeps realtime elevator fields closed", async () => {
    // probe 只拉本机 snapshot contract，并把 map/pose/elevator 摘要保持在 fail-closed 诊断层。
    const server = await listenJson({
      schema: "trashbot.o7.realtime_elevator_snapshot.v1",
      realtime_status: "blocked_not_proven",
      snapshot_status: "blocked_not_proven",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      real_realtime_api_connected: false,
      real_ros2_tf_connected: false,
      latency_lt_2s_proven: false,
      real_elevator_state_chain_connected: false,
      floor_recognition_proven: false,
      human_takeover_proven: false,
      map_ref: { id: "not_connected", status: "blocked_not_proven", evidence_ref: "missing_real_map_artifact" },
      map_frame: { frame_id: "map", source: "contract_placeholder_not_tf", status: "blocked_not_proven" },
      robot_pose: {
        x_m: 1.25,
        y_m: -0.75,
        yaw_rad: 1.57,
        pose_source: "fixture_pose_slot_not_tf",
        timestamp_ms: 2000,
        evidence_ref: "pose-slot.json",
      },
      pose_freshness: { age_ms: null, latency_lt_2s_proven: false, status: "blocked_not_proven" },
      route_membership: { route_id: "not_connected", on_route: false, in_elevator_zone: false, status: "blocked_not_proven" },
      elevator_state_chain: {
        current_state: "waiting_operator",
        sample_count: 6,
        samples: [
          { state: "waiting_operator", status: "fixture_summary_only", timestamp_ms: 2000, evidence_ref: "state-001.json" },
          { state: "door_open_observed", status: "fixture_summary_only", timestamp_ms: 2100, evidence_ref: "state-002.json" },
          { state: "entering_elevator", status: "fixture_summary_only", timestamp_ms: 2200, evidence_ref: "state-003.json" },
          { state: "riding", status: "fixture_summary_only", timestamp_ms: 2300, evidence_ref: "state-004.json" },
          { state: "exiting_elevator", status: "fixture_summary_only", timestamp_ms: 2400, evidence_ref: "state-005.json" },
          { state: "extra_not_returned", status: "fixture_summary_only", timestamp_ms: 2500, evidence_ref: "state-006.json" },
        ],
        status: "blocked_not_proven",
      },
      current_floor_evidence: {
        floor_label: "not_connected",
        confidence: null,
        floor_recognition_proven: false,
        status: "blocked_not_proven",
      },
      human_takeover: {
        required: true,
        human_takeover_proven: false,
        reason: "real_elevator_state_chain_not_proven",
        status: "blocked_not_proven",
      },
      blocked_reasons: ["real_realtime_api_not_connected", "ros2_tf_forwarding_not_proven"],
      not_proven: ["real_o7_realtime_cloud_stream", "real_current_floor_recognition"],
    });
    try {
      const probe = await buildO7RealtimeElevatorProbe(server.baseUrl);

      expect(probe.schema).toBe("trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1");
      expect(probe.probe_status).toBe("loaded_fail_closed_contract");
      expect(probe.source_base_url).toBe(server.baseUrl);
      expect(probe.remote_schema).toBe("trashbot.o7.realtime_elevator_snapshot.v1");
      expect(probe.realtime_status).toBe("blocked_not_proven");
      expect(probe.snapshot_status).toBe("blocked_not_proven");
      expect(probe.map_frame_summary).toContain("frame_id=map");
      expect(probe.robot_pose_summary).toContain("x_m=1.25");
      expect(probe.robot_pose_summary).toContain("y_m=-0.75");
      expect(probe.robot_pose_summary).toContain("yaw_rad=1.57");
      expect(probe.robot_pose_summary).toContain("pose_source=fixture_pose_slot_not_tf");
      expect(probe.robot_pose_summary).toContain("timestamp_ms=2000");
      expect(probe.robot_pose_summary).toContain("evidence_ref=pose-slot.json");
      expect(probe.robot_pose_summary).toContain("real_ros2_tf_connected=false");
      expect(probe.pose_freshness_summary).toContain("latency_lt_2s_proven=false");
      expect(probe.probe_observed_at_ms).toEqual(expect.any(Number));
      expect(probe.remote_pose_timestamp_ms).toBe(2000);
      expect(probe.remote_pose_age_ms).toEqual(expect.any(Number));
      expect(probe.freshness_gate_status).toBe("pc_only_freshness_observed_not_latency_proof:blocked_not_proven");
      expect(probe.latency_lt_2s_proven).toBe(false);
      expect(probe.route_membership_false_fields).toEqual([
        "route_membership.on_route=false",
        "route_membership.in_elevator_zone=false",
      ]);
      expect(probe.elevator_status).toContain("current_state=waiting_operator");
      expect(probe.elevator_status).toContain("sample_count=6");
      expect(probe.elevator_state_samples_summary).toHaveLength(5);
      expect(probe.elevator_state_samples_summary[0]).toContain("state=waiting_operator");
      expect(probe.elevator_state_samples_summary[0]).toContain("timestamp_ms=2000");
      expect(probe.elevator_state_samples_summary[0]).toContain("evidence_ref=state-001.json");
      expect(probe.elevator_state_samples_summary.join("\n")).not.toContain("extra_not_returned");
      expect(probe.current_floor_evidence_summary).toContain("floor_recognition_proven=false");
      expect(probe.human_takeover_summary).toContain("human_takeover_proven=false");
      expect(probe.key_false_fields).toEqual(expect.arrayContaining([
        "real_realtime_api_connected=false",
        "real_ros2_tf_connected=false",
        "route_membership.on_route=false",
        "route_membership.in_elevator_zone=false",
        "safe_to_control=false",
      ]));
      expect(probe.dangerous_true_fields).toEqual([]);
      expect(probe.sends_commands).toBe(false);
      expect(probe.connects_cloud_production).toBe(false);
      expect(probe.reads_hardware).toBe(false);
    } finally {
      await server.close();
    }

    const blocked = await buildO7RealtimeElevatorProbe("https://example.com");
    expect(blocked.probe_status).toBe("fail_closed");
    expect(blocked.fail_closed_reason).toBe("baseUrl_protocol_not_allowed");
    expect(blocked.safe_to_control).toBe(false);
    expect(blocked.primary_actions_enabled).toBe(false);
    expect(blocked.robot_pose_summary).toContain("real_ros2_tf_connected=false");
    expect(blocked.elevator_state_samples_summary).toEqual([]);

    const dangerousServer = await listenJson({
      schema: "trashbot.o7.realtime_elevator_snapshot.v1",
      real_ros2_tf_connected: true,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      map_frame: { frame_id: "map", source: "contract_placeholder_not_tf", status: "blocked_not_proven" },
      robot_pose: { x_m: 1, y_m: 2, yaw_rad: 3, pose_source: "unsafe_remote_claim", timestamp_ms: 4 },
      elevator_state_chain: {
        current_state: "unsafe_tf_claim",
        sample_count: 1,
        samples: [{ state: "unsafe_tf_claim", status: "blocked_not_proven", timestamp_ms: 4, evidence_ref: "unsafe.json" }],
        status: "blocked_not_proven",
      },
      blocked_reasons: [],
      not_proven: [],
    });
    try {
      const dangerous = await buildO7RealtimeElevatorProbe(dangerousServer.baseUrl);

      expect(dangerous.probe_status).toBe("fail_closed");
      expect(dangerous.fail_closed_reason).toBe("remote_dangerous_true_field");
      expect(dangerous.dangerous_true_fields).toContain("real_ros2_tf_connected");
      expect(dangerous.robot_pose_summary).toContain("x_m=1");
      expect(dangerous.robot_pose_summary).toContain("real_ros2_tf_connected=false");
      expect(dangerous.elevator_state_samples_summary).toHaveLength(1);
      expect(dangerous.safe_to_control).toBe(false);
      expect(dangerous.primary_actions_enabled).toBe(false);
    } finally {
      await dangerousServer.close();
    }
  });
});
