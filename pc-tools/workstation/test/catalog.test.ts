import { describe, expect, it, vi } from "vitest";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
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
  buildLocalizationResetProxy,
  buildMapProofRefreshProxy,
  buildNavGoalPreflightProxy,
  buildNav2LifecycleProxy,
  buildNav2NoMotionProofRefreshProxy,
  buildOperatorReportProxy,
  buildRadarLifecycleProxy,
  buildRadarScanProofRefreshProxy,
  computeRobotProofRefreshTimeoutMs,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "../src/server/catalog";
import { createWorkstationApp, listenFailureHint, robotControlFixedProxyQueryBaseUrl, robotControlReadOnlyQueryBaseUrl, robotControlSummaryQueryBaseUrl, workstationListenAddress } from "../src/server/index";
import type {
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlCameraMjpegStatusResponse,
  RobotControlLiveSummaryResponse,
  RobotControlSummaryResponse,
} from "../src/shared/contracts";
import { WORKSTATION_DEV_API_PROXY_TARGET, WORKSTATION_DEV_PORT, WORKSTATION_NODE_PORT, WORKSTATION_PUBLIC_HOST } from "../src/shared/workstationDefaults";

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

function requestJson(url: string | URL): Promise<{ status: number; body: unknown }> {
  // 用 Node http 调 workstation，避免测试里的 fetch stub 影响客户端请求本身。
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode ?? 0, body: JSON.parse(body) as unknown });
        } catch (error) {
          reject(error);
        }
      });
    }).on("error", reject);
  });
}

function postJson(url: string | URL, body: unknown): Promise<{ status: number; body: unknown }> {
  // POST 也走 Node http；这样 global fetch 只会截获 workstation 内部上游请求。
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const target = new URL(String(url));
    const request = http.request(
      {
        hostname: target.hostname,
        port: target.port,
        path: `${target.pathname}${target.search}`,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
      },
      (res) => {
        let responseBody = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          responseBody += chunk;
        });
        res.on("end", () => {
          try {
            resolve({ status: res.statusCode ?? 0, body: JSON.parse(responseBody) as unknown });
          } catch (error) {
            reject(error);
          }
        });
      },
    );
    request.on("error", reject);
    request.write(payload);
    request.end();
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

function listenRobotApiReadbackByPath(
  handlers: Record<string, { payload: unknown; delay_ms?: number; statusCode?: number }>,
): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  // 真实上位机不同 endpoint 延迟不同；测试用按路径响应来验证只读超时预算不会误判慢端点。
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    const handler = handlers[url] ?? (url === "/api/health"
      ? {
        payload: {
          schema: "trashbot.upper_robot_api.v1.health",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      }
      : undefined);
    if (!handler) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    const delayMs = handler.delay_ms ?? 0;
    const statusCode = handler.statusCode ?? 200;
    setTimeout(() => {
      res.statusCode = statusCode;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
    }, delayMs);
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

function listenSerialRobotApiReadbackByPath(
  handlers: Record<string, { payload: unknown; delay_ms?: number; statusCode?: number }>,
): Promise<{ baseUrl: string; close: () => Promise<void>; requestedUrls: string[] }> {
  // 真实上位机现场表现接近单 worker；这里串行响应，专门防止 summary 再次并发打满慢端点。
  const requestedUrls: string[] = [];
  let responseChain = Promise.resolve();
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    requestedUrls.push(url);
    const handler = handlers[url] ?? (url === "/api/health"
      ? {
        payload: {
          schema: "trashbot.upper_robot_api.v1.health",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      }
      : undefined);
    if (!handler) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    const queuedResponse = responseChain.then(() => new Promise<void>((resolve) => {
      setTimeout(() => {
        res.statusCode = handler.statusCode ?? 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(handler.payload));
        resolve();
      }, handler.delay_ms ?? 0);
    }));
    responseChain = queuedResponse.catch(() => undefined);
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        requestedUrls,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRobotCameraProxyApi(
  handlers: Record<string, { payload: unknown; statusCode?: number; method?: "GET" | "POST" }>,
): Promise<{ baseUrl: string; close: () => Promise<void>; receivedBodies: Record<string, unknown[]> }> {
  // camera proxy 测试需要按固定 POST 路径返回 JSON，验证 workstation 不会退化成任意代理。
  const receivedBodies: Record<string, unknown[]> = {};
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    const handler = handlers[url];
    const expectedMethod = handler?.method ?? "POST";
    if (req.method !== expectedMethod || !handler) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    if (expectedMethod === "GET") {
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
      return;
    }
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      if (!receivedBodies[url]) {
        receivedBodies[url] = [];
      }
      receivedBodies[url].push(body ? JSON.parse(body) : {});
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ ...(handler.payload as Record<string, unknown>), echoed_body: body ? JSON.parse(body) : {} }));
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        receivedBodies,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRobotProofRefreshApi(
  handlers: Record<string, { payload: unknown; statusCode?: number }>,
): Promise<{
  baseUrl: string;
  close: () => Promise<void>;
  receivedBodies: Record<string, unknown[]>;
}> {
  // refresh 代理测试需要检查上游是否只收固定 POST body，而不是浏览器拼接的任意控制参数。
  const receivedBodies: Record<string, unknown[]> = {};
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    const handler = handlers[url];
    if (req.method !== "POST" || !handler) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      if (!receivedBodies[url]) {
        receivedBodies[url] = [];
      }
      receivedBodies[url].push(body ? JSON.parse(body) : {});
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        receivedBodies,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRobotMapLifecycleApi(
  handlers: Record<string, { payload: unknown; statusCode?: number; method: "GET" | "POST" }>,
): Promise<{
  baseUrl: string;
  close: () => Promise<void>;
  receivedBodies: Record<string, unknown[]>;
  receivedGets: string[];
}> {
  // map lifecycle 代理既有 GET 也有 POST；测试要确认它们都只命中固定上位机路径。
  const receivedBodies: Record<string, unknown[]> = {};
  const receivedGets: string[] = [];
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    const handler = handlers[url];
    if (!handler || req.method !== handler.method) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    if (req.method === "GET") {
      receivedGets.push(url);
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
      return;
    }
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      if (!receivedBodies[url]) {
        receivedBodies[url] = [];
      }
      receivedBodies[url].push(body ? JSON.parse(body) : {});
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        receivedBodies,
        receivedGets,
        close: () => new Promise((closeResolve, closeReject) => {
          server.close((error) => (error ? closeReject(error) : closeResolve()));
        }),
      });
    });
  });
}

function listenRobotBaseCommandApi(
  postHandlers: Record<string, { payload: unknown; statusCode?: number }>,
  getHandlers: Record<string, { payload: unknown; statusCode?: number }>,
): Promise<{
  baseUrl: string;
  close: () => Promise<void>;
  receivedBodies: Record<string, unknown[]>;
  receivedGets: string[];
}> {
  // base command 代理测试同时需要固定 POST 和固定 GET-only 证据采集，不能用任意代理模拟。
  const receivedBodies: Record<string, unknown[]> = {};
  const receivedGets: string[] = [];
  const server = http.createServer((req, res) => {
    const url = req.url ?? "/";
    if (req.method === "GET") {
      receivedGets.push(url);
      const handler = getHandlers[url];
      res.statusCode = handler?.statusCode ?? (handler ? 200 : 404);
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler?.payload ?? { error: "not_found" }));
      return;
    }
    const handler = postHandlers[url];
    if (req.method !== "POST" || !handler) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      if (!receivedBodies[url]) {
        receivedBodies[url] = [];
      }
      receivedBodies[url].push(body ? JSON.parse(body) : {});
      res.statusCode = handler.statusCode ?? 200;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(handler.payload));
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        receivedBodies,
        receivedGets,
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
  it("defaults workstation Node API to the public operator port", () => {
    // 现场默认要能从局域网访问；仍允许 HOST/PORT 环境变量在启动前覆盖。
    expect(WORKSTATION_PUBLIC_HOST).toBe("0.0.0.0");
    expect(WORKSTATION_NODE_PORT).toBe(7001);
    expect(workstationListenAddress()).toBe("http://0.0.0.0:7001");
  });

  it("keeps Vite dev defaults off the Node operator port while proxying API to it", () => {
    // 开发热更新页单独占 7002，正式 Node 工作站继续固定在 7001 供局域网访问。
    expect(WORKSTATION_DEV_PORT).toBe(7002);
    expect(WORKSTATION_DEV_PORT).not.toBe(WORKSTATION_NODE_PORT);
    expect(WORKSTATION_DEV_API_PROXY_TARGET).toBe("http://127.0.0.1:7001");
  });

  it("keeps public npm aliases on the same default workstation entrypoints", async () => {
    // public 别名只保留兼容入口，避免以后把 7001/7002 默认值写散后再次漂移。
    const packageJson = JSON.parse(await readFile(path.join(process.cwd(), "package.json"), "utf8")) as {
      scripts: Record<string, string>;
    };

    expect(packageJson.scripts.api).toBe("tsx src/server/index.ts");
    expect(packageJson.scripts["api:public"]).toBe("npm run api");
    expect(packageJson.scripts.dev).toBe("vite");
    expect(packageJson.scripts["dev:public"]).toBe("npm run dev");
  });

  it("defaults Robot Control summary reads to the fixed robot API address", () => {
    // 普通首屏 summary 是只读入口；缺省 query 时必须默认连固定小车，避免现场手填地址。
    expect(robotControlSummaryQueryBaseUrl(undefined)).toBe("http://192.168.1.11:8787");
    expect(robotControlSummaryQueryBaseUrl("")).toBe("http://192.168.1.11:8787");
    expect(robotControlSummaryQueryBaseUrl("http://127.0.0.1:8787")).toBe("http://127.0.0.1:8787");
  });

  it("defaults Robot Control read-only reads to the fixed robot API address", async () => {
    // Nav2/latest、delivery/latest、地图只读画面和自动扫图 latest 都应默认走固定小车，不要求普通用户手填。
    expect(robotControlReadOnlyQueryBaseUrl(undefined)).toBe("http://192.168.1.11:8787");
    expect(robotControlReadOnlyQueryBaseUrl("")).toBe("http://192.168.1.11:8787");
    const requestedUrls: string[] = [];
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      requestedUrls.push(url);
      const pathname = new URL(url).pathname;
      let payload: Record<string, unknown>;
      if (pathname.endsWith("/api/nav2/goal/execution/latest")) {
        payload = { status: "goal_succeeded", feedback_sample_count: 8, robot_control_executed: false };
      } else if (pathname.endsWith("/api/delivery/latest")) {
        payload = { delivery_success: false, latest_result: { missing_required_material: ["operator_observed_motion"] } };
      } else if (pathname.endsWith("/api/radar/status")) {
        payload = {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "scan_once_hz_raw_packet_tf_observed",
          scan_status: "fresh_scan_proof_observed",
          continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
          latest_scan_proof_fresh: true,
          robot_control_executed: false,
        };
      } else if (pathname.endsWith("/api/map/list")) {
        payload = { status: "loaded", maps: [], command_result: { executed: false, ok: true } };
      } else if (pathname.endsWith("/api/free-roam/autonomy/latest")) {
        payload = {
          status: "loaded",
          latest_result: {
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: { state: "locked", reason: "现场安全确认未满足", stop_required: true, gates: [] },
          },
        };
      } else {
        payload = {
          status: "loaded",
          map_name: "default-map-preview",
          map_yaml_name: "default-map-preview.yaml",
          map_image_name: "default-map-preview.pgm",
          width: 1,
          height: 1,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 1, unknown: 0, occupied: 0, other: 0 },
          image_mime_type: "image/png",
          image_data_url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lJK3GQAAAABJRU5ErkJggg==",
          command_result: { executed: false, ok: true },
        };
      }
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    const server = await listen(createWorkstationApp());

    try {
      const nav2 = await requestJson(new URL("/api/robot-control/nav2/goal/execution/latest", server.baseUrl));
      const delivery = await requestJson(new URL("/api/robot-control/delivery/latest", server.baseUrl));
      const radarStatus = await requestJson(new URL("/api/robot-control/radar/status", server.baseUrl));
      const mapList = await requestJson(new URL("/api/robot-control/map/list", server.baseUrl));
      const mapPreview = await requestJson(new URL("/api/robot-control/map/preview", server.baseUrl));
      const freeRoamLatest = await requestJson(new URL("/api/robot-control/free-roam/autonomy/latest", server.baseUrl));

      expect(nav2.status).toBe(200);
      expect(delivery.status).toBe(200);
      expect(radarStatus.status).toBe(200);
      expect(mapList.status).toBe(200);
      expect(mapPreview.status).toBe(200);
      expect(freeRoamLatest.status).toBe(200);
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/nav2/goal/execution/latest");
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/delivery/latest");
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/radar/status");
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/map/list");
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/map/preview");
      expect(requestedUrls).toContain("http://192.168.1.11:8787/api/free-roam/autonomy/latest");
    } finally {
      fetchSpy.mockRestore();
      await server.close();
    }
  });

  it("defaults Robot Control fixed POST proxies to the fixed robot API address", async () => {
    // 普通用户点击自动扫图不应因为 URL 栏缺 baseUrl 而卡住；显式空 baseUrl 仍必须 fail closed。
    expect(robotControlFixedProxyQueryBaseUrl(undefined)).toBe("http://192.168.1.11:8787");
    expect(robotControlFixedProxyQueryBaseUrl("")).toBe("");
    expect(robotControlFixedProxyQueryBaseUrl("http://127.0.0.1:8787")).toBe("http://127.0.0.1:8787");
    const workstation = await listen(createWorkstationApp());
    const originalFetch = globalThis.fetch;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("http://192.168.1.11:8787/api/free-roam/autonomy/start");
      expect(init?.method).toBe("POST");
      expect(JSON.parse(String(init?.body ?? "{}"))).toEqual({
        confirm_operator_safety: true,
        confirm_mapping_active: false,
      });
      return new Response(
        JSON.stringify({
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_start",
          status: "requested",
          command_result: { mode: "free_roam_param_sequence", executed: true, ok: true },
          latest_decision_state: "ready",
          sets_state_machine_parameters: true,
          mapping_active_requested: false,
          mapping_active_applied: false,
          direct_cmd_vel_publish: false,
          motion_unlock_requested: true,
          does_not_set_motion_unlock: false,
          free_move_start_ready: true,
          free_move_blocked_reasons: [],
          mapping_readiness_ready: false,
          mapping_blocked_reasons: ["camera_first_frame_not_observed", "radar_scan_proof_not_fresh"],
          sensor_readiness: {
            ready: true,
            missing: [],
            free_move_ready: true,
            free_move_without_camera_allowed: true,
            motion_without_radar_allowed: true,
            degraded_without_radar: true,
            mapping_readiness: {
              ready: false,
              missing: ["camera_first_frame_not_observed", "radar_scan_proof_not_fresh"],
              requires_camera_first_frame: true,
              requires_fresh_radar_scan: true,
              free_move_allowed_when_mapping_not_ready: true,
            },
          },
          failure_reason: null,
          blocked_reasons: [],
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await postJson(`${workstation.baseUrl}/api/robot-control/free-roam/autonomy/start`, {
        confirm_operator_safety: true,
        confirm_mapping_active: false,
      });
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(response.status).toBe(200);
      const body = response.body as Record<string, any>;
      expect(body.proxy_status).toBe("autonomy_forwarded");
      expect(body.source_base_url).toBe("http://192.168.1.11:8787");
      expect(body.normalized_base_url).toBe("http://192.168.1.11:8787");
      expect(body.blocked_reasons).toEqual([]);
      expect(body.sets_state_machine_parameters).toBe(true);
      expect(body.mapping_active_requested).toBe(false);
      expect(body.mapping_active_applied).toBe(false);
      expect(body.motion_unlock_requested).toBe(true);
      expect(body.free_move_start_ready).toBe(true);
      expect(body.free_move_blocked_reasons).toEqual([]);
      expect(body.mapping_readiness_ready).toBe(false);
      expect(body.mapping_blocked_reasons).toEqual([
        "camera_first_frame_not_observed",
        "radar_scan_proof_not_fresh",
      ]);
      expect(body.sensor_readiness.ready).toBe(true);
      expect(body.sensor_readiness.mapping_readiness.ready).toBe(false);
      expect(body.sensor_readiness.mapping_readiness.missing).toEqual([
        "camera_first_frame_not_observed",
        "radar_scan_proof_not_fresh",
      ]);
      const emptyBaseUrlResponse = await postJson(`${workstation.baseUrl}/api/robot-control/free-roam/autonomy/start?baseUrl=`, {
        confirm_operator_safety: true,
        confirm_mapping_active: false,
      });
      expect(emptyBaseUrlResponse.status).toBe(400);
      const emptyBaseUrlBody = emptyBaseUrlResponse.body as Record<string, any>;
      expect(emptyBaseUrlBody.proxy_status).toBe("autonomy_rejected");
      expect(emptyBaseUrlBody.failure_reason).toBe("baseUrl_not_provided");
      expect(fetchMock).toHaveBeenCalledTimes(1);
    } finally {
      globalThis.fetch = originalFetch;
      await workstation.close();
    }
  });

  it("keeps advanced Nav2 confirmation collapsed into the unified safety checkbox", async () => {
    // 发车前预检对普通和高级入口都只保留一个现场安全确认；底层兼容字段仍由请求体发送。
    const source = await readFile(path.join(process.cwd(), "src/components/RobotControlConsolePanel.vue"), "utf8");

    expect(source).not.toContain("confirmNavigationPreflight");
    expect(source).not.toContain("confirmNavigationExecution");
    expect(source).not.toContain("确认仅做导航目标预检");
    expect(source).not.toContain("确认执行一次受限导航目标");
    expect(source).toContain('name="advancedNavSafetyConfirmed"');
    expect(source).toContain("现场安全确认（全页面一次生效）");
    expect(source).toContain("confirm_navigation_preflight: true");
    expect(source).toContain("confirm_navigation_execution: plainManualSafetyConfirmed.value");
  });

  it("formats public API port conflict with operator next steps", () => {
    // 公网绑定失败是现场访问问题；提示必须给出占用排查和换端口兜底。
    const message = listenFailureHint(
      Object.assign(new Error("listen EADDRINUSE"), { code: "EADDRINUSE" }),
      "0.0.0.0",
      7001,
    );

    expect(message).toContain("0.0.0.0:7001");
    expect(message).toContain("address already in use");
    expect(message).toContain("lsof -nP -iTCP:7001");
    expect(message).toContain("PORT=<free-port> npm run api");
  });

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
    // 任一层缺文件都要进入 blocked_not_proven，不能把缺口误报成 就绪。
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
      latest_map_consumed: false,
      latest_path_generation_attempted: false,
      latest_path_generation_service_available: false,
      latest_path_generation_service_name: "/planner_server/compute_path_to_pose",
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
      expect(summary.current_fact_plain).toContain("画面未显示：页面会自动接入共享 MJPEG 预览");
      expect(summary.current_fact_plain).toContain("未出帧前不当作已经看到画面");
      expect(summary.current_fact_plain).not.toContain("画面未可见");
      expect(summary.current_fact_plain).toContain("地图画面已读到，但图上路线还未显示");
      expect(summary.current_fact_plain).toContain("自动驾驶：图上路线还未准备完成");
      expect(summary.current_fact_plain).toContain("键盘：必须按住 W/A/S/D 或方向键才会连续低速移动");
      expect(summary.current_fact_plain).toContain("发车前：执行图上路线只要求现场安全确认");
      expect(summary.current_fact_plain).not.toContain("marker");
      expect(summary.current_fact_plain).not.toContain("overlay");
      const actionCards = summary.action_status_cards ?? [];
      expect(actionCards.map((card) => card.id)).toEqual([
        "camera_preview",
        "map_preview",
        "radar_map_points",
        "nav2_route",
        "keyboard_control",
        "free_move",
        "mapping_start",
      ]);
      expect(JSON.stringify(actionCards)).not.toContain("marker");
      expect(JSON.stringify(actionCards)).not.toContain("overlay");
      expect(actionCards.find((card) => card.id === "camera_preview")).toMatchObject({
        status: "not_visible",
        evidence: {
          camera_current_frame_visible: false,
          camera_source_first_frame_ready: false,
          camera_blocks_mapping_start: true,
          shared_preview_multi_viewer: true,
          shared_capture: true,
          exclusive_camera_claim: false,
          source_failure_reason: "not_loaded",
          shared_preview_upstream_active: false,
          shared_preview_content_type_loaded: false,
          shared_preview_last_failure_reason: "none",
          shared_preview_last_remote_http_status: "none",
          last_offer_failure_reason: "none",
          last_offer_format_attempts_summary: "none",
          first_frame_probe_read_ok: false,
          visible_content_proven: false,
          shared_preview_client_count: 0,
          shared_preview_cached_frame_loaded: false,
          fixed_shared_preview_endpoint: "/api/robot-control/camera/mjpeg",
          fixed_shared_preview_status_endpoint: "/api/robot-control/camera/mjpeg/status",
          auto_joins_shared_preview: true,
          shared_preview_single_upstream: true,
        },
      });
      expect(actionCards.find((card) => card.id === "map_preview")).toMatchObject({
        status_label: "已显示",
        next_action_plain: "地图画面已显示；继续确认图上路线和小车位置，雷达点另看“地图雷达点”。",
        evidence: {
          map_current_visible: true,
          path_visible_on_map: false,
          path_point_count: 0,
          path_frame_id: "not_loaded",
          robot_pose_visible: false,
          radar_points_visible_on_map: false,
          radar_point_count_on_map: 0,
        },
      });
      const radarActionCard = actionCards.find((card) => card.id === "radar_map_points");
      expect(radarActionCard).toMatchObject({
        status: "not_current",
        wysiwyg_status: "old_or_missing_points_not_drawn",
        evidence: {
          current_on_map: false,
          current_point_count: 0,
          radar_lifecycle_running: false,
          radar_lifecycle_state: "not_loaded",
          map_radar_status: "not_loaded",
          map_radar_point_count: 0,
          map_radar_source_point_count: 0,
          map_radar_blocked_by_lifecycle_not_running: false,
          runtime_scan_status: "not_loaded",
          runtime_scan_fresh: false,
          runtime_scan_point_count: 0,
          runtime_scan_source_point_count: 0,
          runtime_scan_frame_id: "not_loaded",
          runtime_scan_age_s: "not_loaded",
          runtime_scan_source: "not_loaded",
          latest_scan_proof_fresh: false,
          radar_scan_observation_status: "latest_scan_not_fresh",
          radar_scan_observation_missing_reasons: [],
          map_radar_readiness_status: "blocked_latest_scan_not_fresh",
          map_radar_next_action_plain: "先刷新雷达扫描读数，确认拿到新扫描后再刷新地图画面。",
          map_radar_blocked_reason_labels: ["没有可贴图的新雷达点", "小车地图位置未读到"],
          driver_diagnostics_status: "not_loaded",
          driver_diagnostics_next_action_plain: "not_loaded",
          driver_serial_bytes_read_total: "not_loaded",
          driver_serial_packet_count_total: "not_loaded",
          driver_serial_empty_read_count: "not_loaded",
          driver_published_scan_count: "not_loaded",
          radar_start_configured: true,
          fixed_radar_start_endpoint: "/api/robot-control/radar/start",
          fixed_radar_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
          fixed_radar_map_preview_endpoint: "/api/robot-control/map/preview",
          radar_refresh_after_start_required: true,
          radar_map_points_loaded_required: true,
          radar_map_point_count_gt_zero_required: true,
        },
      });
      expect(Array.isArray(radarActionCard?.evidence?.blocked_reasons)).toBe(true);
      expect(actionCards.find((card) => card.id === "nav2_route")).toMatchObject({
        status: "not_ready",
        requires_safety_confirmation: true,
        sends_motion_when_clicked: true,
        evidence: {
          route_ready_on_map: false,
          minimal_precheck_safety_only: true,
          fixed_execute_proxy_endpoint: "/api/robot-control/nav2/goal/execute",
          execute_sends_motion_when_ready: false,
          requires_same_window_wheel_lr_nonzero: true,
          wheel_feedback_status: "not_loaded",
          goal_execution_proven: false,
          goal_execution_hil_pass: false,
          base_command_nonzero_observed: false,
          base_command_nonzero_count: 0,
          base_feedback_sample_count: 0,
          base_feedback_nonzero_sample_count: 0,
          base_feedback_lr_nonzero_proven: false,
          base_feedback_latest_raw_left: "not_loaded",
          base_feedback_latest_raw_right: "not_loaded",
          imu_attitude_delta_observed: false,
          imu_roll_delta: "not_loaded",
          imu_pitch_delta: "not_loaded",
          nav2_stack_running: false,
          nav2_stack_lifecycle_state: "not_loaded",
          planner_server_active: false,
          controller_server_active: false,
          controller_server_requested: false,
          controller_idle_not_blocking: false,
          controller_blocking_current_goal: false,
          controller_idle_reason_plain: "控制服务当前状态未读到。",
          path_generated: false,
          nav2_path_point_count: 0,
          current_blocker_reasons: [
            "planner_server_not_active",
            "nav2_map_not_consumed",
            "path_generation_service_unavailable",
            "path_generation_not_attempted",
          ],
          current_blocker_labels: [
            "planner_server_not_active",
            "地图未被自动驾驶服务消费",
            "路径生成服务不可用",
            "路径生成还没真正开始",
          ],
        },
      });
      expect(Array.isArray(actionCards.find((card) => card.id === "nav2_route")?.evidence?.blockers)).toBe(true);
      expect(actionCards.find((card) => card.id === "keyboard_control")).toMatchObject({
        status_label: "可启用",
        requires_safety_confirmation: true,
        can_start_after_safety_confirm: true,
        sends_motion_when_clicked: false,
        blocks_free_motion: false,
        evidence: {
          hold_to_move_required: true,
          arm_sends_motion: false,
          requires_keydown_for_motion: true,
          pulse_interval_ms: 260,
          pulse_duration_ms: 240,
          manual_command_mode: "ros",
          wheel_feedback_required_in_same_hold_window: true,
          fixed_keyboard_manual_endpoint: "/api/robot-control/base/manual",
          fixed_keyboard_stop_endpoint: "/api/robot-control/base/stop",
          keyboard_start_ready: true,
          keyboard_enabled: false,
          keyboard_armed: false,
          keyboard_sends_motion_while_held: false,
          keyboard_current_direction: "none",
          keyboard_current_hold_pulse_count: 0,
          keyboard_best_continuous_pulse_count: 0,
          keyboard_verified_min_forwarded_pulses: 2,
          keyboard_continuous_pulse_verified: false,
          keyboard_stop_required_after_hold: true,
          keyboard_stop_settled_after_pulse: false,
          keyboard_motion_verified: false,
        },
      });
      expect(actionCards.find((card) => card.id === "keyboard_control")?.evidence?.stop_triggers).toContain("window_blur");
      expect(actionCards.find((card) => card.id === "free_move")).toMatchObject({
        status_label: "可启动",
        requires_safety_confirmation: true,
        can_start_after_safety_confirm: true,
        blocks_free_motion: false,
        evidence: {
          free_move_start_ready: true,
          free_move_safety_only: true,
          stop_fallback_required: true,
          camera_blocks_free_motion: false,
          radar_blocks_free_motion: false,
          fixed_free_roam_start_endpoint: "/api/robot-control/free-roam/autonomy/start",
          fixed_free_roam_stop_endpoint: "/api/robot-control/free-roam/autonomy/stop",
          free_roam_stop_request_pending: false,
          start_will_clear_stop_request: false,
          start_clears_stop_request_not_blocking: false,
          motion_start_blocked_by_stop_request: false,
          fixed_mapping_start_endpoint: "/api/robot-control/map/start",
          fixed_mapping_preview_endpoint: "/api/robot-control/map/preview",
          mapping_start_ready: false,
        },
      });
      expect(actionCards.find((card) => card.id === "free_move")?.evidence?.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
      expect(actionCards.find((card) => card.id === "mapping_start")).toMatchObject({
        status_label: "未就绪",
        requires_safety_confirmation: false,
        can_start_after_safety_confirm: false,
        sends_motion_when_clicked: false,
        blocks_free_motion: false,
        blocks_mapping_start: true,
        evidence: {
          free_move_start_ready: true,
          fixed_mapping_start_endpoint: "/api/robot-control/map/start",
          fixed_mapping_preview_endpoint: "/api/robot-control/map/preview",
          mapping_start_ready: false,
          mapping_start_requires_camera_first_frame: true,
          mapping_start_requires_lidar_fresh: true,
          mapping_camera_first_frame_ready: false,
          mapping_lidar_fresh_ready: false,
          camera_blocks_free_motion: false,
          radar_blocks_free_motion: false,
        },
      });
      expect(actionCards.find((card) => card.id === "mapping_start")?.evidence?.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
      const goalChecklist = summary.goal_checklist ?? [];
      expect(goalChecklist.map((item) => item.id)).toEqual([
        "camera_wysiwyg",
        "map_wysiwyg",
        "radar_map_points_wysiwyg",
        "nav2_route_execution",
        "keyboard_continuous_control",
        "free_move",
        "mapping_start",
      ]);
      expect(JSON.stringify(goalChecklist)).not.toContain("marker");
      expect(JSON.stringify(goalChecklist)).not.toContain("overlay");
      expect(goalChecklist.find((item) => item.id === "map_wysiwyg")).toMatchObject({
        status: "done",
        status_label: "已满足",
        requires_motion: false,
        blocks_goal_completion: false,
      });
      expect(goalChecklist.find((item) => item.id === "keyboard_continuous_control")).toMatchObject({
        status: "needs_safety_confirm",
        status_label: "待安全确认",
        requires_safety_confirmation: true,
        requires_motion: true,
        blocks_goal_completion: true,
      });
      expect(goalChecklist.find((item) => item.id === "free_move")).toMatchObject({
        status: "needs_safety_confirm",
        status_label: "待安全确认",
        requires_safety_confirmation: true,
        requires_motion: true,
        blocks_goal_completion: true,
      });
      expect(goalChecklist.find((item) => item.id === "mapping_start")).toMatchObject({
        status: "not_ready",
        status_label: "未就绪",
        requires_safety_confirmation: false,
        requires_motion: false,
        blocks_goal_completion: true,
      });
      expect(summary.goal_checklist_summary).toMatchObject({
        status: "in_progress",
        status_label: "进行中",
        total_count: 7,
        done_count: 1,
        remaining_count: 6,
        safety_confirm_needed_count: 3,
        motion_needed_count: 3,
        ready_action_count: 2,
        blocked_action_count: 4,
        motion_ready_count: 2,
        sensor_blocker_count: 3,
        first_incomplete_item_id: "camera_wysiwyg",
        first_incomplete_source_card_id: "camera_preview",
        first_motion_item_id: "free_move",
        first_motion_source_card_id: "free_move",
        primary_ready_action_item_id: "free_move",
        primary_ready_action_source_card_id: "free_move",
        safety_precheck_source_card_id: "free_move",
        radar_item_id: "radar_map_points_wysiwyg",
        radar_source_card_id: "radar_map_points",
        nav2_item_id: "nav2_route_execution",
        nav2_source_card_id: "nav2_route",
        mapping_item_id: "mapping_start",
        mapping_source_card_id: "mapping_start",
      });
      expect(summary.goal_summary).toEqual(summary.goal_checklist_summary);
      expect(summary.camera_summary).toEqual(summary.readback_summary.camera);
      expect(summary.map_summary).toEqual(summary.readback_summary.map);
      expect(summary.radar_summary).toEqual(summary.readback_summary.radar);
      expect(summary.nav2_summary).toEqual(summary.readback_summary.nav2);
      expect(summary.keyboard_summary).toEqual(summary.readback_summary.keyboard);
      expect(summary.readback_summary.keyboard_control).toEqual(summary.readback_summary.keyboard);
      expect(summary.readback_summary.keyboard_teleop).toEqual(summary.readback_summary.keyboard);
      expect(summary.keyboard_control_summary).toEqual(summary.readback_summary.keyboard_control);
      expect(summary.keyboard_teleop_summary).toEqual(summary.readback_summary.keyboard_teleop);
      expect(summary.free_roam_summary).toEqual(summary.readback_summary.free_roam);
      expect(summary.camera_summary?.preview_visible_status).toBe(summary.readback_summary.camera.preview_visible_status);
      expect(summary.map_summary?.map_wysiwyg_status_plain).toBe(summary.readback_summary.map.map_wysiwyg_status_plain);
      expect(summary.map_summary?.next_action_plain).toBe(summary.readback_summary.map.path_preview_next_action_plain);
      expect(summary.map_summary?.map_next_action_plain).toBe(summary.readback_summary.map.map_wysiwyg_next_action_plain);
      expect(summary.radar_summary?.radar_overlay_status).toBe(summary.readback_summary.radar.radar_overlay_status);
      expect(summary.nav2_summary?.status).toBe(summary.readback_summary.nav2.status);
      expect(summary.nav2_summary?.next_action_plain).toBe(summary.readback_summary.nav2.next_action_plain);
      expect(summary.keyboard_summary?.start_ready).toBe("true");
      expect(summary.keyboard_control_summary?.start_ready).toBe("true");
      expect(summary.keyboard_teleop_summary?.start_ready).toBe("true");
      expect(summary.keyboard_summary?.next_action_plain).toContain("按住 W/A/S/D");
      expect(summary.keyboard_summary?.wheel_feedback_acceptance_plain).toContain("同一次按住窗口");
      expect(summary.keyboard_summary?.wheel_feedback_acceptance_plain).toContain("wheel L/R 非零");
      expect(summary.keyboard_control_summary?.next_action_plain).toContain("按住 W/A/S/D");
      expect(summary.keyboard_teleop_summary?.next_action_plain).toContain("按住 W/A/S/D");
      expect(summary.free_roam_summary?.motion_start_ready).toBe("true");
      expect(summary.free_roam_summary?.mapping_start_ready).toBe("false");
      expect(summary.free_roam_summary?.motion_next_action_plain).toContain("现场安全确认");
      expect(summary.free_roam_summary?.motion_next_action_plain).toContain("相机和雷达只影响建图");
      expect(summary.goal_checklist_summary?.summary_plain).toContain("本轮目标检查 1/7 项已完成");
      expect(summary.goal_checklist_summary?.summary_plain).toContain("现场可先收口 2 项：自由自助移动、键盘连续手控");
      expect(summary.goal_checklist_summary?.summary_plain).toContain("先做：自由自助移动");
      expect(summary.goal_checklist_summary?.primary_ready_action_next_action_plain).toContain("可先勾选现场安全确认");
      expect(summary.goal_checklist_summary?.primary_ready_action_summary_plain).toContain("可先做：自由自助移动");
      expect(summary.goal_checklist_summary?.move_now_status_plain).toBe("可先动：自由自助移动、键盘连续手控；发车前只需现场安全确认；相机和雷达只影响建图验收。");
      expect(summary.goal_checklist_summary?.mapping_blockers_plain).toBe("建图缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图；这些缺口不阻止先低速自由移动。");
      expect(summary.goal_checklist_summary?.summary_plain).toContain("未就绪项：画面所见即所得、雷达点贴到地图、完整行程执行、传感器就绪后建图");
      expect(summary.goal_checklist_summary?.motion_summary_plain).toContain("可先自由移动");
      expect(summary.goal_checklist_summary?.motion_summary_plain).toContain("键盘或低速手控");
      expect(summary.goal_checklist_summary?.safety_precheck_summary_plain).toContain("发车前预检已精简");
      expect(summary.goal_checklist_summary?.safety_precheck_summary_plain).toContain("只需要现场安全确认");
      expect(summary.goal_checklist_summary?.radar_summary_plain).toContain("雷达点还没有贴到当前地图");
      expect(summary.goal_checklist_summary?.nav2_summary_plain).toContain("完整图上行程还未就绪");
      expect(summary.goal_checklist_summary?.mapping_summary_plain).toContain("建图暂不可启动");
      expect(summary.goal_checklist_summary?.progress_plain).toBe("1/7");
      expect(summary.goal_checklist_summary?.next_action_item_ids).toEqual([
        "camera_wysiwyg",
        "radar_map_points_wysiwyg",
        "nav2_route_execution",
        "keyboard_continuous_control",
        "free_move",
        "mapping_start",
      ]);
      expect(summary.goal_checklist_summary?.ready_action_ids).toEqual([
        "free_move",
        "keyboard_continuous_control",
      ]);
      expect(summary.goal_checklist_summary?.blocked_action_ids).toEqual([
        "camera_wysiwyg",
        "radar_map_points_wysiwyg",
        "nav2_route_execution",
        "mapping_start",
      ]);
      expect(summary.goal_checklist_summary?.next_action_items).toHaveLength(6);
      expect(summary.goal_checklist_summary?.next_action_items.map((item) => item.id)).toEqual([
        "camera_wysiwyg",
        "radar_map_points_wysiwyg",
        "nav2_route_execution",
        "keyboard_continuous_control",
        "free_move",
        "mapping_start",
      ]);
      expect(summary.goal_checklist_summary?.ready_action_items.map((item) => item.id)).toEqual([
        "free_move",
        "keyboard_continuous_control",
      ]);
      expect(summary.goal_checklist_summary?.blocked_action_items.map((item) => item.id)).toEqual([
        "camera_wysiwyg",
        "radar_map_points_wysiwyg",
        "nav2_route_execution",
        "mapping_start",
      ]);
      expect(summary.goal_checklist_summary?.next_action_items[1]).toMatchObject({
        id: "radar_map_points_wysiwyg",
        title: "雷达点贴到地图",
        status_label: "待处理",
        source_card_id: "radar_map_points",
        requires_safety_confirmation: false,
        requires_motion: false,
        blocks_goal_completion: true,
      });
      expect(summary.goal_checklist_summary?.blocked_action_items.find((item) => item.id === "mapping_start")).toMatchObject({
        requires_safety_confirmation: false,
        requires_motion: false,
        blocks_goal_completion: true,
      });
      expect(JSON.stringify(summary.goal_checklist_summary)).not.toContain("raw");
      expect(JSON.stringify(summary.goal_checklist_summary)).not.toContain("marker");
      expect(JSON.stringify(summary.goal_checklist_summary)).not.toContain("overlay");
      expect(summary.readback_summary.map).toMatchObject({
        status: expect.any(String),
        map_once_observed: "true",
        plain_hint: expect.stringContaining("地图画面已读到，但图上路线还未显示"),
        map_current_visible: "true",
        path_current_visible: "false",
        radar_overlay_current_visible: "false",
        map_wysiwyg_status_plain: "地图画面已读到，但图上路线还未显示。",
        map_wysiwyg_next_action_plain: "先准备图上路线，再刷新地图画面。",
        next_action_plain: "先准备图上路线，再刷新地图画面。",
        map_next_action_plain: "先准备图上路线，再刷新地图画面。",
        path_preview_status: "not_observed",
        path_preview_point_count: "0",
        path_preview_frame_id: "not_loaded",
        path_preview_next_action_plain: "先准备图上路线，再刷新地图画面。",
        path_wysiwyg_status_plain: "图上路线未显示；不能把旧路线或空路线当作当前所见。",
        path_wysiwyg_next_action_plain: "先准备图上路线，再刷新地图画面。",
      });
      expect(summary.readback_summary.map.plain_hint).toContain("图上路线未显示；不能把旧路线或空路线当作当前所见");
      expect(summary.readback_summary.map.plain_hint).toContain("下一步：先准备图上路线，再刷新地图画面。");
      expect(summary.readback_summary.radar).toMatchObject({
        status: expect.any(String),
        radar_status_plain: expect.any(String),
        radar_next_action_plain: expect.any(String),
        radar_overlay_point_count: expect.any(String),
        radar_overlay_wysiwyg_status_plain: expect.any(String),
        map_marker_point_count: expect.any(String),
      });
      expect(summary.readback_summary.radar.plain_hint).toContain("下一步：");
      expect(summary.readback_summary.radar.plain_hint).not.toContain("marker");
      expect(summary.readback_summary.radar.plain_hint).not.toContain("overlay");
      expect(summary.readback_summary.localization).toMatchObject({
        status: expect.any(String),
        amcl_pose_observed: "false",
        localization_tf_observed: "false",
        robot_pose_status: "not_observed",
      });
      expect(summary.readback_summary.nav2).toMatchObject({
        status: expect.any(String),
        plain_hint: expect.stringContaining("图上路线还未准备完成。"),
        nav2_stack_running: expect.any(String),
        nav2_stack_lifecycle_state: expect.any(String),
        planner_server_active: "false",
        controller_server_active: expect.any(String),
        controller_server_requested: expect.any(String),
        map_consumed: "false",
        path_generation_attempted: "false",
        path_generation_service_available: "false",
        path_generation_service_name: "/planner_server/compute_path_to_pose",
        path_generated: "false",
        path_generation_succeeded: "false",
        path_point_count: "0",
        path_preview_point_count: "0",
        execution_status_plain: expect.stringContaining("图上路线还未准备完成"),
        next_action_plain: "先按当前根因处理，再准备图上路线并刷新地图画面。",
        route_execution_readiness_plain: expect.stringContaining("图上路线还不可执行"),
        route_execution_precheck_plain: "路线准备完成后，执行只需勾选行程前安全确认。",
        goal_execution_wheel_raw_lr_status_plain: "本轮完整路线执行的轮速 L/R 还未证明。",
        goal_execution_wheel_raw_lr_next_action_plain: "先准备图上路线并执行，再在同窗口确认轮速 L/R 非零。",
        goal_execution_status: expect.any(String),
        goal_execution_proven: expect.any(String),
        goal_execution_hil_pass: expect.any(String),
        goal_execution_result_status: expect.any(String),
        goal_execution_robot_control_executed: expect.any(String),
        goal_execution_feedback_sample_count: expect.any(String),
        goal_execution_goal_frame_id: expect.any(String),
        goal_execution_goal_x: expect.any(String),
        goal_execution_goal_y: expect.any(String),
        goal_execution_generated_at_ms: expect.any(String),
        goal_execution_response_generated_at_ms: expect.any(String),
      });
      expect(summary.readback_summary.nav2.plain_hint).toContain("当前根因：planner_server_not_active、地图未被自动驾驶服务消费、路径生成服务不可用、路径生成还没真正开始。");
      expect(summary.readback_summary.nav2.plain_hint).toContain("下一步：先按当前根因处理，再准备图上路线并刷新地图画面。");
      expect(summary.readback_summary.camera.preview_status).toBe("idle_not_started");
      expect(summary.readback_summary.camera.plain_hint).toContain("画面未显示：页面会自动接入共享 MJPEG 预览");
      expect(summary.readback_summary.camera.plain_hint).toContain("共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看");
      expect(summary.readback_summary.camera.plain_hint).toContain("下一步：打开页面会自动接入共享 MJPEG");
      expect(summary.readback_summary.camera.plain_hint).not.toContain("画面未可见");
      expect(summary.readback_summary.camera.preview_plain_hint).toBe("页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(summary.readback_summary.camera.preview_next_action).toBe("auto_join_shared_mjpeg_preview");
      expect(summary.readback_summary.camera.shared_preview_client_count).toBe("0");
      expect(summary.readback_summary.camera.viewer_count).toBe("0");
      expect(summary.readback_summary.camera.shared_preview_upstream_active).toBe("false");
      expect(summary.readback_summary.camera.upstream_connected).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_content_type_loaded).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_cached_frame_loaded).toBe("false");
      expect(summary.readback_summary.camera.has_recent_frame).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_cached_frame_age_ms).toBe("none");
      expect(summary.readback_summary.camera.shared_preview_access_plain).toBe("共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。");
      expect(summary.readback_summary.camera.shared_preview_realtime_plain).toBe("当前没有实时画面；页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(summary.readback_summary.camera.shared_preview_shared_capture).toBe("true");
      expect(summary.readback_summary.camera.shared_preview_exclusive_camera_claim).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
      expect(summary.readback_summary.camera.shared_preview_multi_viewer_plain).toContain("谁打开页面都接入同一个共享 relay");
      expect(summary.readback_summary.camera.shared_preview_multi_viewer_plain).toContain("当前 0 个页面观看");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("none");
      expect(summary.readback_summary.camera.shared_preview_last_remote_http_status).toBe("none");
      expect(summary.readback_summary.camera.shared_preview_last_failure_at_ms).toBe("none");
      expect(summary.safe_command_boundary.manual_endpoint).toBe("/api/base/manual");
      expect(summary.safe_command_boundary.stop_endpoint).toBe("/api/base/stop");
      expect(summary.safe_command_boundary.cmd_vel_topic).toBe("/cmd_vel");
      expect(summary.safe_command_boundary.nav2_goal).toBe("Nav2 NavigateToPose locked");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(false);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线未就绪");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual(expect.arrayContaining([
        "planner_server_inactive",
        "nav2_map_not_consumed",
        "path_generation_service_unavailable",
        "path_generation_not_attempted",
        "path_generation_not_observed",
        "path_point_count_not_positive",
      ]));
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("not_loaded");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("先恢复规划服务，再生成图上路线");
      expect(summary.safe_command_boundary.nav2_goal_minimal_precheck_plain).toBe("执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。");
      expect(summary.safe_command_boundary.nav2_goal_precheck_plain).toBe("执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。");
      expect(summary.safe_command_boundary.navigation_preflight_plain).toBe("执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。");
      expect(summary.readback_summary.nav2.current_blocker_reasons).toContain("nav2_map_not_consumed");
      expect(summary.readback_summary.nav2.current_blocker_reasons).toContain("path_generation_service_unavailable");
      expect(summary.readback_summary.nav2.current_blocker_reasons).toContain("path_generation_not_attempted");
      expect(summary.readback_summary.nav2.current_blocker_labels).toContain("地图未被自动驾驶服务消费");
      expect(summary.readback_summary.nav2.current_blocker_labels).toContain("路径生成服务不可用");
      expect(summary.safe_command_boundary.nav2_goal_execution_mode_label).toBe("not_loaded");
      expect(summary.safe_command_boundary.manual_motion_entry_status).toBe("controlled_jog_requires_safety_confirmation_only");
      expect(summary.safe_command_boundary.non_stop_requires_operator_report_preflight).toBe(false);
      expect(summary.safe_command_boundary.operator_report_preflight_endpoint).toBe("/api/operator/report");
      expect(summary.safe_command_boundary.operator_report_preflight_required_fields).toEqual([]);
      expect(summary.safe_command_boundary.allowed_directions).toEqual(["forward", "back", "left", "right", "stop"]);
      expect(summary.safe_command_boundary.hil_checklist).toEqual([
        { id: "operator_safety_confirmed", label: "现场安全确认（人在旁边、周围安全、停止手段就绪）" },
      ]);
      expect(summary.safe_command_boundary.hil_checklist.map((item) => item.id)).not.toContain("operator_ready");
      expect(summary.safe_command_boundary.manual_control_enabled).toBe(false);
      expect(summary.safe_command_boundary.keyboard_control).toBe("bounded repeating manual pulse gated");
      expect(summary.safe_command_boundary.keyboard_control_mode).toBe("bounded_repeating_manual_pulse");
      expect(summary.safe_command_boundary.keyboard_manual_command_mode).toBe("ros");
      expect(summary.safe_command_boundary.keyboard_manual_proxy_endpoint).toBe("/api/robot-control/base/manual");
      expect(summary.safe_command_boundary.keyboard_stop_proxy_endpoint).toBe("/api/robot-control/base/stop");
      expect(summary.safe_command_boundary.keyboard_jog_interval_ms).toBe(260);
      expect(summary.safe_command_boundary.keyboard_jog_duration_ms).toBe(240);
      expect(summary.safe_command_boundary.keyboard_stop_triggers).toContain("window_blur");
      expect(summary.safe_command_boundary.keyboard_hold_to_move_plain).toBe("必须按住 W/A/S/D 或方向键才会连续低速移动；只启用键盘但不按方向不会发车。");
      expect(summary.safe_command_boundary.keyboard_stop_triggers_plain).toBe("松开按键、窗口失焦、页面隐藏、切换方向或点击停止都会发送停止请求。");
      expect(summary.safe_command_boundary.keyboard_pulse_timing_plain).toBe("按住时约每 0.26 秒发送一次 0.24 秒低速脉冲。");
      expect(summary.safe_command_boundary.keyboard_reuses_manual_gate).toBe(true);
      expect(summary.safe_command_boundary.keyboard_control_start_ready).toBe(true);
      expect(summary.safe_command_boundary.keyboard_control_status).toBe("start_ready");
      expect(summary.safe_command_boundary.keyboard_control_label).toBe("键盘手控（勾确认后可启用）");
      expect(summary.safe_command_boundary.keyboard_control_next_action).toBe("勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停");
      expect(summary.safe_command_boundary.keyboard_minimal_precheck_plain).toBe("键盘连续手控只复用现场安全确认；启用键盘不发车，只有按住方向键/WASD 才发送低速短脉冲。");
      expect(summary.readback_summary.keyboard.status).toBe("start_ready");
      expect(summary.readback_summary.keyboard.control_mode).toBe("bounded_repeating_manual_pulse");
      expect(summary.readback_summary.keyboard.manual_command_mode).toBe("ros");
      expect(summary.readback_summary.keyboard.start_ready).toBe("true");
      expect(summary.readback_summary.keyboard.continuous_control_ready).toBe("true");
      expect(summary.readback_summary.keyboard.keyboard_control_start_ready).toBe("true");
      expect(summary.readback_summary.keyboard.keyboard_continuous_control_ready).toBe("true");
      expect(summary.readback_summary.keyboard.hold_to_move_required).toBe("true");
      expect(summary.readback_summary.keyboard.keyboard_hold_to_move_required).toBe("true");
      expect(summary.readback_summary.keyboard.enabled).toBe("false");
      expect(summary.readback_summary.keyboard.keyboard_enabled).toBe("false");
      expect(summary.readback_summary.keyboard.keyboard_motion_verified).toBe("false");
      expect(summary.readback_summary.keyboard.keyboard_continuous_pulse_verified).toBe("false");
      expect(summary.readback_summary.keyboard.keyboard_current_hold_pulse_count).toBe("0");
      expect(summary.readback_summary.keyboard.keyboard_best_continuous_pulse_count).toBe("0");
      expect(summary.readback_summary.keyboard.keyboard_verified_min_forwarded_pulses).toBe("2");
      expect(summary.readback_summary.keyboard.keyboard_safety_confirm_required).toBe("true");
      expect(summary.readback_summary.keyboard.minimal_precheck_safety_only).toBe("true");
      expect(summary.readback_summary.keyboard.plain_hint).toBe("可启用键盘；启用本身不发车，必须按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页/换方向或点停止都会停。");
      expect(summary.readback_summary.keyboard.readiness_plain).toBe("可启用键盘；启用本身不发车，按住方向键/WASD 才连续低速移动。");
      expect(summary.readback_summary.keyboard.continuous_control_contract_plain).toBe("按住时约每 0.26 秒发送一次 0.24 秒 ROS 低速脉冲；松开、失焦、切页、换方向或点击停止都会停。");
      expect(summary.readback_summary.keyboard.hold_to_move_plain).toBe(summary.safe_command_boundary.keyboard_hold_to_move_plain);
      expect(summary.readback_summary.keyboard.stop_triggers_plain).toBe(summary.safe_command_boundary.keyboard_stop_triggers_plain);
      expect(summary.readback_summary.keyboard.pulse_timing_plain).toBe(summary.safe_command_boundary.keyboard_pulse_timing_plain);
      expect(summary.readback_summary.keyboard.minimal_precheck_plain).toBe(summary.safe_command_boundary.keyboard_minimal_precheck_plain);
      expect(summary.readback_summary.keyboard.robot_control_executed).toBe("false");
      expect(summary.safe_command_boundary.keyboard_teleop_start_ready).toBe(true);
      expect(summary.safe_command_boundary.keyboard_teleop_status).toBe("start_ready");
      expect(summary.safe_command_boundary.keyboard_teleop_next_action_plain).toBe(summary.safe_command_boundary.keyboard_control_next_action);
      expect(summary.safe_command_boundary.keyboard_control_enabled).toBe(false);
      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("locked");
      expect(summary.safe_command_boundary.free_roam_autonomy_start_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_motion_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_start_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toEqual([
        "camera_first_frame",
        "lidar_fresh",
      ]);
      expect(summary.safe_command_boundary.free_roam_mapping_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_mapping_missing_reasons).toEqual([
        "camera_first_frame",
        "lidar_fresh",
        "mapping_active",
        "fresh_map_preview",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy_label).toBe("自动扫图（未开放）");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).toBe("可先勾选现场安全确认，用键盘或低速手控移动；要启动上车自由移动状态机，先连接状态机并确认停止兜底");
      expect(summary.safe_command_boundary.free_roam_motion_minimal_precheck_plain).toBe("自由移动只要求现场安全确认和停止兜底；相机、雷达、地图记录只影响建图验收。");
      expect(summary.safe_command_boundary.free_roam_mapping_start_plain).toBe("建图启动未就绪；还差：画面首帧、雷达新鲜；同时等待上车自由移动状态机。");
      expect(summary.safe_command_boundary.free_roam_mapping_start_next_action).toBe("先连接上车自由移动状态机；建图启动还差：画面首帧、雷达新鲜。");
      expect(summary.safe_command_boundary.free_roam_mapping_acceptance_plain).toBe("建图验收要求画面首帧、雷达新鲜、地图记录和地图画面就绪；这些缺口不阻止先低速自由移动。");
      expect(summary.safe_command_boundary.free_roam_autonomy_policy.mode).toBe("free_move_requires_safety_confirm_stop_fallback");
      expect(summary.safe_command_boundary.free_roam_autonomy_policy.mapping_mode).toBe("mapping_acceptance_requires_camera_and_fresh_radar");
      expect(summary.safe_command_boundary.free_roam_autonomy_policy.required_gates).toEqual([
        "operator_safety_confirmed",
        "operator_stop_fallback",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy_policy.mapping_start_required_gates).toEqual([
        "camera_first_frame",
        "fresh_radar_scan",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy_policy.mapping_required_gates).toEqual([
        "camera_first_frame",
        "fresh_radar_scan",
        "map_recording_active",
        "fresh_map_preview",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy_gates.map((gate) => gate.id)).toEqual([
        "operator_confirmed",
        "stop_available",
        "motion_hil_unlock",
        "camera_first_frame",
        "lidar_fresh",
      ]);
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
      expect(summary.primary_actions_enabled).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary reads fast endpoints before serial slow aggregate endpoints", async () => {
    // 单 worker 上位机遇到 /api/status 慢聚合时，summary 不能并发排队导致 Nav2/地图/相机等快读端点一起超时。
    const safePayload = (schema: string, status = "loaded", extras: Record<string, unknown> = {}) => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      robot_control_executed: false,
      ...extras,
    });
    const robotApi = await listenSerialRobotApiReadbackByPath({
      "/api/status": {
        delay_ms: 4200,
        payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded", {
          managed_runtime_started: true,
          planner_server_active: true,
          latest_map_consumed: true,
          latest_path_generation_attempted: true,
        }),
      },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_proof", "loaded", { map_once_observed: true }) },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localize_proof", "loaded", { localization_tf_observed: true }) },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "loaded", { lifecycle_running: true, latest_planner_active: true }) },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_proof", "loaded", { path_generated: true, path_point_count: 3 }) },
      "/api/nav2/goal/execution/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution", "loaded") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy", "loaded") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.radar_scan_proof", "loaded") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.radar_raw_packet_proof", "loaded") },
      "/api/base/status": {
        delay_ms: 200,
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "base_ready", {
          wheel_raw_left: 0,
          wheel_raw_right: 0,
        }),
      },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const readStatusById = new Map(summary.read_endpoints.map((endpoint) => [endpoint.id, endpoint.request_status]));
      const requestedUrlIndex = (url: string) => robotApi.requestedUrls.indexOf(url);

      expect(summary.robot_api_connection.status).toBe("degraded");
      expect(readStatusById.get("health")).toBe("loaded");
      expect(summary.robot_api_connection.failed_count).toBe(1);
      expect(summary.robot_api_connection.blocked_reasons).toContain("status:fetch_timeout_2400ms");
      expect(readStatusById.get("map_proof_latest")).toBe("loaded");
      expect(readStatusById.get("nav2_status")).toBe("loaded");
      expect(readStatusById.get("camera_health")).toBe("loaded");
      expect(readStatusById.get("base_status")).toBe("loaded");
      expect(readStatusById.get("status")).toBe("fetch_failed");
      expect(summary.read_endpoints.map((endpoint) => endpoint.endpoint)).toEqual([
        "/api/health",
        "/api/status",
        "/api/map/proof/latest",
        "/api/map/preview",
        "/api/localize/proof/latest",
        "/api/nav2/status",
        "/api/nav2/proof/latest",
        "/api/nav2/goal/execution/latest",
        "/api/operator/report",
        "/api/free-roam/autonomy/latest",
        "/api/camera/health",
        "/api/camera/devices",
        "/api/radar/status",
        "/api/radar/scan-proof/latest",
        "/api/radar/raw-packet-proof/latest",
        "/api/base/feedback-samples/latest",
        "/api/base/status",
      ]);
      expect(requestedUrlIndex("/api/nav2/status")).toBeLessThan(requestedUrlIndex("/api/base/status"));
      expect(requestedUrlIndex("/api/nav2/status")).toBeLessThan(requestedUrlIndex("/api/status"));
      expect(requestedUrlIndex("/api/base/feedback-samples/latest")).toBeLessThan(requestedUrlIndex("/api/status"));
      expect(requestedUrlIndex("/api/base/feedback-samples/latest")).toBeLessThan(requestedUrlIndex("/api/base/status"));
      expect(requestedUrlIndex("/api/base/status")).toBeLessThan(requestedUrlIndex("/api/status"));
    } finally {
      await robotApi.close();
    }
  }, 10000);

  it("Robot Control summary tells users to fix API readback before generating Nav2 route", async () => {
    // 复现 live 7001 场景：小车 base URL 可访问，但 Nav2/地图/定位只读端点读不到。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      robot_control_executed: false,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded") },
      "/api/map/proof/latest": { statusCode: 500, payload: { error: "map_read_failed" } },
      "/api/localize/proof/latest": { statusCode: 500, payload: { error: "localize_read_failed" } },
      "/api/nav2/status": { statusCode: 500, payload: { error: "nav2_status_failed" } },
      "/api/nav2/proof/latest": { statusCode: 500, payload: { error: "nav2_proof_failed" } },
      "/api/nav2/goal/execution/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report", "loaded") },
      "/api/free-roam/autonomy/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "loaded") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(false);
      expect(summary.safe_command_boundary.nav2_goal_blockers).toContain("robot_api_nav2_read_failed");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toContain("robot_api_map_localize_read_failed");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toContain("先确认小车地址和上位机 API 可读");
      expect(summary.readback_summary.nav2.current_blocker_labels).toContain("自动驾驶状态读取失败");
      expect(summary.readback_summary.nav2.current_blocker_labels).toContain("地图/定位读取失败");
      expect(summary.readback_summary.nav2.next_action_plain).toContain("先确认小车地址和上位机 API 可读");
      expect(summary.readback_summary.nav2.route_execution_readiness_plain).toContain("自动驾驶状态读取失败");
      expect(summary.readback_summary.nav2.route_execution_readiness_plain).toContain("地图/定位读取失败");
      expect(summary.current_fact_plain).toContain("先确认小车地址和上位机 API 可读");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary prioritizes stopped Nav2 stack before planner recovery", async () => {
    // 真实车上 `/api/nav2/status` 会只读 o11 lifecycle manager；stopped 时普通首屏应先提示启动服务，不误导成雷达问题。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          lifecycle_running: false,
          lifecycle_state: "stopped",
          lifecycle_manager: {
            schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_manager_status",
            status: "loaded",
            running: false,
            state: "stopped",
            message: "Nav2 lifecycle not running",
            sends_motion_commands: false,
            sends_base_motion_commands: false,
            robot_control_executed: false,
            safe_to_control: false,
            delivery_success: false,
          },
          latest_planner_active: false,
          latest_controller_active: false,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.nav2_stack_running).toBe("false");
      expect(summary.readback_summary.nav2.nav2_stack_lifecycle_state).toBe("stopped");
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("自动驾驶服务未启动");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([
        "nav2_stack_not_running",
        "path_generation_not_observed",
        "path_point_count_not_positive",
      ]);
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("先启动自动驾驶服务（不发车），再生成图上路线");
      expect(summary.safe_command_boundary.nav2_goal_next_action).not.toContain("雷达");
      expect(summary.safe_command_boundary.nav2_goal_next_action).not.toContain("相机");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary reflects camera source first-frame failure in shared preview status", async () => {
    // 只看 summary 的页面也要知道共享画面不是独占，而是相机源没有首帧。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/camera/health": {
        payload: {
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "capture_read_returned_false",
          video_source: "/dev/video1",
          source_usage: { status: "not_in_use", owner_count: 0, owners: [] },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.preview_status).toBe("idle_not_started");
      expect(summary.readback_summary.camera.preview_plain_hint).toBe("不是页面独占：UVC 设备当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summary.readback_summary.camera.preview_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(summary.readback_summary.camera.preview_visible_status).toBe("not_visible_source_first_frame_failed");
      expect(summary.readback_summary.camera.preview_visible_plain).toBe("当前没有实时画面；不是页面独占：UVC 设备当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.camera_wysiwyg_status_plain).toBe("画面未可见：不是页面独占：UVC 设备当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.camera_wysiwyg_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(summary.readback_summary.camera.plain_hint).toContain("画面未显示：不是页面独占");
      expect(summary.readback_summary.camera.plain_hint).toContain("共享预览不是页面独占");
      expect(summary.readback_summary.camera.plain_hint).toContain("下一步：检查 USB、摄像头输入或供电");
      expect(summary.readback_summary.camera.plain_hint).not.toContain("画面未可见");
      expect(summary.current_fact_plain).toContain("画面未显示：不是页面独占：UVC 设备当前没人占用，但 UVC 设备没有输出视频帧");
      expect(summary.current_fact_plain).not.toContain("画面未可见");
      expect(summary.readback_summary.camera.shared_preview_client_count).toBe("0");
      expect(summary.readback_summary.camera.viewer_count).toBe("0");
      expect(summary.readback_summary.camera.shared_preview_upstream_active).toBe("false");
      expect(summary.readback_summary.camera.upstream_connected).toBe("false");
      expect(summary.readback_summary.camera.has_recent_frame).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_exclusive_camera_claim).toBe("false");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summary.readback_summary.camera.shared_preview_last_remote_http_status).toBe("200");
      expect(summary.readback_summary.camera.shared_preview_last_failure_at_ms).toBe("none");
      expect(summary.action_status_cards?.find((card) => card.id === "camera_preview")).toMatchObject({
        evidence: {
          camera_current_frame_visible: false,
          camera_source_first_frame_ready: false,
          camera_blocks_mapping_start: true,
          shared_preview_multi_viewer: true,
          shared_capture: true,
          exclusive_camera_claim: false,
          source_first_frame_failed: true,
          source_diagnosis_status: "uvc_no_frame_not_exclusive",
          source_diagnosis_not_exclusive: true,
          first_frame_probe_read_ok: false,
          visible_content_proven: false,
          shared_preview_client_count: 0,
          shared_preview_cached_frame_loaded: false,
          fixed_shared_preview_endpoint: "/api/robot-control/camera/mjpeg",
          fixed_shared_preview_status_endpoint: "/api/robot-control/camera/mjpeg/status",
          auto_joins_shared_preview: true,
          shared_preview_single_upstream: true,
        },
      });
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps camera status and readiness aligned when relay proves first-frame failure", async () => {
    // live 形态：health 可能慢到超时，但共享 relay 已知道上游无首帧；summary 不能返回 status failed + readiness not_loaded。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/camera/health": {
        delay_ms: 50,
        payload: {
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "ready",
          source_readiness: "source_selected_not_probed",
          source_failure_reason: "",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, {
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: "camera_source_first_frame_failed",
        last_remote_http_status: 200,
        last_failure_at_ms: 1234,
        source_diagnosis_status: "uvc_no_frame_not_exclusive",
        source_diagnosis_plain_hint: "不是页面独占：共享 relay 已证明 UVC 没有输出首帧。",
        source_diagnosis_next_action: "check_usb_camera_input_power_or_known_good_uvc",
        source_diagnosis_not_exclusive: "true",
      }, { readbackTimeoutMs: 1 });

      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summary.readback_summary.camera.preview_plain_hint).toBe("不是页面独占：共享 relay 已证明 UVC 没有输出首帧。");
      expect(summary.readback_summary.camera.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summary.readback_summary.camera.preview_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.source_diagnosis_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(summary.readback_summary.camera.first_frame_probe_status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.first_frame_probe_read_ok).toBe("false");
      expect(summary.readback_summary.camera.first_frame_probe_visible_content_proven).toBe("false");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary uses relay no-frame diagnosis when camera health returns bad JSON", async () => {
    // live 形态：camera health 可能被上游异常内容打成 bad_json，但 relay status 已证明不是页面独占，而是 UVC 没有首帧。
    const server = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end("{not json");
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const robotApi = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
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
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, {
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: "camera_source_first_frame_failed",
        last_remote_http_status: 200,
        last_failure_at_ms: 1234,
        source_diagnosis_status: "uvc_no_frame_not_exclusive",
        source_diagnosis_plain_hint: "不是页面独占：共享 relay 已证明 UVC 没有输出首帧。",
        source_diagnosis_next_action: "check_usb_camera_input_power_or_known_good_uvc",
        source_diagnosis_not_exclusive: "true",
      });

      const cameraHealthReadback = summary.read_endpoints.find((item) => item.id === "camera_health");
      expect(cameraHealthReadback?.request_status).toBe("bad_json");
      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
      expect(summary.readback_summary.camera.first_frame_probe_status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.first_frame_probe_read_ok).toBe("false");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary derives Nav2 execution proof from live execution facts", async () => {
    // 现场上位机 latest 可能不带旧 nav2_goal_execution_proven key；PC 摘要必须从 action 成功和 wheel L/R 非零推导。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              base_command_mode: "pwm",
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: true,
            evidence_ref: "o11-nav2-goal-execution-live-shape",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "ros",
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
            base_command_summary: {
              sample_count: 2,
              nonzero_command_count: 1,
              nonzero_command_observed: true,
              latest_nonzero_command_mode: "ros",
              command_mode_counts: { ros: 2 },
            },
            base_feedback_summary: {
              sample_count: 12,
              nonzero_sample_count: 2,
              wheel_feedback_lr_nonzero_proven: true,
              latest_nonzero_pair: { left_speed: 0.12, right_speed: 0.11 },
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_controller_active: false,
          latest_controller_requested: true,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_result_status).toBe("succeeded");
      expect(summary.readback_summary.nav2.goal_execution_robot_control_executed).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_feedback_sample_count).toBe("8");
      expect(summary.readback_summary.nav2.goal_execution_proven).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_hil_pass).toBe("true");
      expect(summary.readback_summary.nav2.execution_status_plain).toBe("本轮路线执行和执行窗口轮速 L/R 已证明。");
      expect(summary.readback_summary.nav2.next_action_plain).toBe("继续送达确认；送达确认不会发车。");
      expect(summary.readback_summary.nav2.plain_hint).toBe("本轮路线执行和执行窗口轮速 L/R 已证明。下一步：继续送达确认；送达确认不会发车。");
      expect(summary.readback_summary.nav2.plain_hint).not.toContain("wheel raw");
      expect(summary.readback_summary.nav2.route_execution_readiness_plain).toBe("完整路线执行已证明；同窗口轮速 L/R 已非零。");
      expect(summary.readback_summary.nav2.route_execution_precheck_plain).toBe("下一步是送达确认；送达确认不会发车。");
      expect(summary.readback_summary.nav2.goal_execution_base_command_latest_nonzero_mode).toBe("ros");
      expect(summary.readback_summary.nav2.goal_execution_base_command_mode_counts).toBe("{\"ros\":2}");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_lr_nonzero_proven).toBe("true");
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("wheel_lr_nonzero_proven");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("本轮路线和 wheel raw L/R 已证明，继续送达确认");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toBe("本轮路线和执行窗口轮速 L/R 已证明，继续送达确认");
      expect(summary.safe_command_boundary.nav2_goal_execution_mode_label).toBe("下次 ros");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps current Nav2 service state separate from O11 managed execution history", async () => {
    // O11 latest 仍证明上次完整路线执行材料；当前 controller/requested 状态必须优先来自 /api/nav2/status。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          path_generated: true,
          path_point_count: 18,
          base: {
            control_policy: {
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "nav2_no_motion_path_generation_runtime_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          planner_server_active: true,
          controller_server_active: false,
          controller_server_requested: false,
          controller_idle_not_blocking: true,
          controller_blocking_current_goal: false,
          controller_idle_reason_plain: "控制服务当前未被请求，属于等待重跑的空闲读数，不是当前自动驾驶阻塞。",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 18,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_planner_active: true,
          latest_controller_active: false,
          latest_controller_requested: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "pwm",
            managed_runtime: {
              requested: true,
              started: true,
              lifecycle_ready: {
                ok: true,
                states: {
                  planner_server: "active [3] (observed_in_lifecycle_manager_log)",
                  controller_server: "active [3] (observed_in_lifecycle_manager_log)",
                  bt_navigator: "active [3] (observed_in_lifecycle_manager_log)",
                  behavior_server: "active [3] (observed_in_lifecycle_manager_log)",
                },
              },
            },
            base_command_summary: {
              sample_count: 49,
              nonzero_command_count: 49,
              nonzero_command_observed: true,
            },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.planner_server_active).toBe("true");
      expect(summary.readback_summary.nav2.controller_server_requested).toBe("false");
      expect(summary.readback_summary.nav2.controller_server_active).toBe("false");
      expect(summary.readback_summary.nav2.goal_execution_status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_lr_nonzero_proven).toBe("false");
      expect(summary.safe_command_boundary.nav2_goal_blockers).not.toContain("controller_server_inactive");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toContain("ROS");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toContain("执行窗口轮速 L/R");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary infers latest Nav2 command mode for older execution artifacts", async () => {
    // 旧 O11 artifact 已有 base_command_mode 和非零命令数，但没有 latest_nonzero_command_mode；PC 仍要让首屏显示 PWM/T=11。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            evidence_ref: "o11-nav2-goal-execution-old-command-summary",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "pwm",
            base_command_summary: {
              sample_count: 49,
              nonzero_command_count: 49,
              nonzero_command_observed: true,
            },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_planner_active: false,
          latest_controller_active: false,
          latest_controller_requested: true,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.status).toBe("goal_succeeded_wheel_feedback_not_proven");
      expect(summary.readback_summary.nav2.goal_execution_base_command_mode).toBe("pwm");
      expect(summary.readback_summary.nav2.next_execution_base_command_mode).toBe("ros");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_status).toBe("pending_ros_rerun_after_pwm");
      expect(summary.readback_summary.nav2.goal_execution_next_mode_plain).toBe("下次将用 ROS 模式重跑图上路线。");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_plain).toBe("上次 PWM 模式路线返回成功但轮速 L/R 仍未非零，本次切到 ROS 模式复验控制链。");
      expect(summary.readback_summary.nav2.goal_execution_base_command_nonzero_count).toBe("49");
      expect(summary.readback_summary.nav2.goal_execution_base_command_latest_nonzero_mode).toBe("pwm");
      expect(summary.readback_summary.nav2.goal_execution_base_command_mode_counts).toBe("{\"pwm\":49}");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_lr_nonzero_proven).toBe("false");
      expect(summary.readback_summary.nav2.planner_server_active).toBe("false");
      expect(summary.readback_summary.nav2.controller_server_active).toBe("false");
      expect(summary.readback_summary.nav2.controller_server_requested).toBe("true");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(false);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线未就绪");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([
        "planner_server_inactive",
        "controller_server_inactive",
        "path_generation_not_observed",
        "path_point_count_not_positive",
      ]);
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到旧执行运动材料，旧执行主因不是雷达或相机；当前图上路线未就绪，先恢复规划服务和控制服务，再生成图上路线，再勾选行程前安全确认后用 ROS 重跑并复验 wheel raw L/R");
      expect(summary.safe_command_boundary.nav2_goal_next_action).not.toContain("不是雷达、相机或 controller");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary falls back to speed T1 after ROS T13 Nav2 wheel-zero rerun", async () => {
    // Vendor index 明确 T=13 未闭环时要能回退 T=1，不能让自动驾驶无限重复同一个 ROS/T=13 零轮速路径。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            evidence_ref: "o11-nav2-goal-execution-ros-zero-wheel",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "ros",
            base_command_summary: {
              sample_count: 20,
              nonzero_command_count: 19,
              nonzero_command_observed: true,
              latest_nonzero_command_mode: "ros",
              command_mode_counts: { ros: 20 },
            },
            base_feedback_summary: {
              sample_count: 42,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.goal_execution_base_command_mode).toBe("ros");
      expect(summary.readback_summary.nav2.next_execution_base_command_mode).toBe("speed");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_status).toBe("pending_speed_rerun_after_ros");
      expect(summary.readback_summary.nav2.goal_execution_next_mode_plain).toBe("下次将用 SPEED 模式重跑图上路线。");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_plain).toBe("上次 ROS 模式路线返回成功但轮速 L/R 仍未非零，本次切到 SPEED 模式复验控制链。");
      expect(summary.readback_summary.nav2.goal_execution_base_command_latest_nonzero_mode).toBe("ros");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toContain("用 SPEED 重跑并复验 wheel raw L/R");
      expect(summary.safe_command_boundary.nav2_goal_execution_mode_label).toBe("上次 ros，下次 speed");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary does not treat Nav2 action success as route execution when HIL is false", async () => {
    // 真实现场可出现 NavigateToPose succeeded 但 hil_pass=false；PC 不能把它说成完整路线已执行。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              base_command_mode: "pwm",
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "nav2_no_motion_path_generation_runtime_observed",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            evidence_ref: "o11-nav2-goal-execution-hil-false",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.status).toBe("nav2_no_motion_path_generation_runtime_observed");
      expect(summary.readback_summary.nav2.goal_execution_status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_result_status).toBe("succeeded");
      expect(summary.readback_summary.nav2.goal_execution_hil_pass).toBe("false");
      expect(summary.readback_summary.nav2.goal_execution_proven).toBe("false");
      expect(summary.readback_summary.nav2.goal_execution_feedback_sample_count).toBe("8");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps Nav2 IMU motion material visible when wheel HIL is still false", async () => {
    // 现场这类 artifact 代表 Nav2 已经驱动车身产生姿态变化，但不能替代 wheel L/R 非零闭环。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              base_command_mode: "pwm",
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            nav2_goal_execution_proven: false,
            evidence_ref: "o11-nav2-goal-execution-imu-material",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
              imu_attitude_delta_observed: true,
              imu_attitude_delta_summary: {
                max_abs_pitch_delta: 24.210531,
                max_abs_roll_delta: 4.387221,
              },
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_controller_active: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.status).toBe("goal_succeeded_wheel_feedback_not_proven");
      expect(summary.readback_summary.nav2.goal_execution_status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_hil_pass).toBe("false");
      expect(summary.readback_summary.nav2.goal_execution_proven).toBe("false");
      expect(summary.readback_summary.nav2.next_execution_base_command_mode).toBe("ros");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_status).toBe("not_required");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_lr_nonzero_proven).toBe("false");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_imu_attitude_delta_observed).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_left_speed).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_right_speed).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_raw_left).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_raw_right).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_wheel_raw_lr_status_plain).toBe("上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；未看到非零底盘命令，IMU 姿态有变化。");
      expect(summary.readback_summary.nav2.goal_execution_wheel_raw_lr_next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。");
      expect(summary.readback_summary.nav2.controller_server_active).toBe("false");
      expect(summary.readback_summary.nav2.execution_status_plain).toContain("执行窗口轮速 L/R=0/0 未非零");
      expect(summary.readback_summary.nav2.execution_status_plain).toContain("主因不是雷达、相机或控制服务");
      expect(summary.readback_summary.nav2.next_action_plain).toContain("用 ROS 模式重跑图上路线");
      expect(summary.readback_summary.nav2.next_action_plain).toContain("确认轮速 L/R 非零");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或 controller；当前图上路线未就绪，先生成图上路线，再勾选行程前安全确认后用 ROS 重跑并复验 wheel raw L/R");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toBe("上次路线结果成功但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务；当前图上路线未就绪，先生成图上路线，再勾选行程前安全确认后用 ROS 模式重跑并复验执行窗口轮速 L/R");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary accepts lidar extrinsic from Nav2 proof latest when localize proof has no transform", async () => {
    // 真实 timeout fallback 里 Nav2 latest 可能先拿到 /tf_static 外参；PC 不能只看 localize latest。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "blocked_with_root_cause",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "not_proven",
          tf_chain_observed: {
            map_to_odom: true,
            odom_to_base_link: true,
            base_link_to_laser_frame: true,
            map_to_base_link: true,
          },
          base_link_to_laser_frame_transform: {
            parent_frame_id: "base_link",
            child_frame_id: "laser_frame",
            translation: { x: 0, y: 0, z: 0 },
            rotation: { yaw: 0, quaternion: { x: 0, y: 0, z: 0, w: 1 } },
            source: "/tf_static",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            evidence_ref: "o11-nav2-goal-execution-fixture",
            nav2_goal_execution_proven: true,
            goal_accepted: true,
            result_received: true,
            result_status: "succeeded",
            feedback_sample_count: 8,
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
            robot_control_executed: true,
            sends_motion_commands: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.o3_proof_summary.frame_transforms.base_link_to_laser_frame).toEqual({
        parent_frame_id: "base_link",
        child_frame_id: "laser_frame",
        x: 0,
        y: 0,
        yaw: 0,
        source: "/tf_static",
      });
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control first-jog proxy exposes raw during-motion L/R key values", async () => {
    // 只模拟上位机 HTTP contract，验证 PC 代理把 T=1001 during-motion raw L/R 抬给高级诊断。
    const server = http.createServer((req, res) => {
      res.setHeader("Content-Type", "application/json");
      if (req.method === "GET" && req.url === "/api/operator/report") {
        res.end(JSON.stringify({
          latest_result: {
            operator_report_status: "ready_for_review",
            operator_report: {
              evidence_ref: "operator-visual-ready",
              operator_present: true,
              physical_clearance_confirmed: true,
              emergency_stop_ready: true,
              structured_hil_claims: {
                external_video_recorded: true,
                external_video_ref: "video-ref",
                visible_content_proven: false,
                camera_artifacts_ref: "",
              },
            },
          },
        }));
        return;
      }
      if (req.method === "POST" && req.url === "/api/base/manual") {
        res.end(JSON.stringify({
          status: "manual_command_completed",
          manual_command_executed: true,
          auto_stop_executed: true,
          feedback_during_motion_attempted: true,
          serial_motion_transaction: {
            feedback_during_motion: {
              t1001_feedback_frames: [
                { T: 1001, L: 0, R: 0, y: "null" },
                { T: 1001, L: 0.07, R: 0.08, y: "null" },
              ],
            },
            feedback_after_stop: {
              t1001_feedback_frames: [{ T: 1001, L: 0, R: 0, y: "null" }],
            },
          },
          manual_wheel_feedback_summary: {
            lr_nonzero_observed: true,
            nonzero_frame_count: 1,
            latest_nonzero_pair: { left_speed: 0.07, right_speed: 0.08 },
          },
          wheel_feedback_lr_nonzero_proven: true,
          wheel_feedback_nonzero_observed: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        }));
        return;
      }
      res.end(JSON.stringify({ safe_to_control: false, delivery_success: false, primary_actions_enabled: false }));
    });
    const robotApi = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
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
    const app = createWorkstationApp();
    const workstation = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      const listener = app.listen(0, "127.0.0.1", () => {
        const address = listener.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            listener.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/first-jog?baseUrl=${encodeURIComponent(robotApi.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ direction: "forward", speed: 0.08, duration_ms: 500, confirm_hil_checklist: true }),
      });
      const payload = await response.json();
      expect(response.status).toBe(200);
      expect(payload.proxy_status).toBe("command_forwarded");
      expect(payload.remote_motion_key_values.feedback_during_motion_t1001_frame_count).toBe("2");
      expect(payload.remote_motion_key_values.feedback_after_stop_t1001_frame_count).toBe("1");
      expect(payload.remote_motion_key_values.wheel_feedback_latest_raw_left).toBe("0.07");
      expect(payload.remote_motion_key_values.wheel_feedback_latest_raw_right).toBe("0.08");
      expect(payload.remote_motion_key_values.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(payload.safe_to_control).toBe(false);
      expect(payload.delivery_success).toBe(false);
    } finally {
      await workstation.close();
      await robotApi.close();
    }
  });

  it("Robot Control summary does not block on T130 read-only base feedback sends_commands", async () => {
    // T=130 反馈采样会出现 sends_commands=true；只要 motion/control 字段为 false，就不应误判成底盘运动。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
            feedback_readback: {
              sends_commands: true,
              sends_motion_commands: false,
              observed_feedback_types: [1001],
            },
          },
        },
      },
      "/api/base/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          feedback_readback: {
            sends_commands: true,
            sends_motion_commands: false,
            observed_feedback_types: [1001],
          },
        },
      },
      "/api/base/feedback-samples/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
          status: "loaded",
          wheel_feedback_lr_nonzero_proven: true,
          wheel_feedback_nonzero_observed: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
            t1001_observed_count: 3,
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const statusReadback = summary.read_endpoints.find((item) => item.id === "status");
      const baseStatusReadback = summary.read_endpoints.find((item) => item.id === "base_status");
      const feedbackLatestReadback = summary.read_endpoints.find((item) => item.id === "base_feedback_samples_latest");

      expect(statusReadback?.dangerous_true_fields).not.toContain("base.sends_commands");
      expect(statusReadback?.dangerous_true_fields).not.toContain("base.feedback_readback.sends_commands");
      expect(baseStatusReadback?.dangerous_true_fields).not.toContain("feedback_readback.sends_commands");
      expect(feedbackLatestReadback?.dangerous_true_fields).not.toContain("latest_result.sends_commands");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("status.base.sends_commands");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("status.base.feedback_readback.sends_commands");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_status.feedback_readback.sends_commands");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_feedback_samples_latest.latest_result.sends_commands");
      expect(summary.readback_summary.base.latest_t1001_observed_count).toBe("3");
      expect(summary.readback_summary.base.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(summary.readback_summary.base.wheel_feedback_nonzero_observed).toBe("true");
      expect(summary.readback_summary.base.feedback_ack_status).toBe("t1001_observed");
      expect(summary.readback_summary.base.feedback_link_status).toBe("t1001_lr_nonzero_material_observed_not_hil");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary derives latest wheel L/R from nested feedback summary", async () => {
    // 真实上位机 latest 把 wheel raw L/R 放在 nested latest_pair；PC summary 必须提取出来给普通首屏显示。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/base/feedback-samples/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
            t1001_observed_count: 3,
            t1001_feedback_frames: [{ T: 1001, L: 0, R: 0, v: 12.31 }],
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_nonzero_observed: false,
            wheel_feedback_summary: {
              frame_count: 13,
              latest_nonzero_pair: {
                left_speed: 164,
                right_speed: 164,
                source: "vendor_t1001_L_R",
              },
              latest_pair: {
                left_speed: 0,
                right_speed: 0,
                source: "vendor_t1001_L_R",
              },
              lr_nonzero_observed: false,
              matched_frame_count: 13,
              nonzero_frame_count: 0,
              source: "vendor_t1001_L_R",
            },
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const feedbackLatestReadback = summary.read_endpoints.find((item) => item.id === "base_feedback_samples_latest");

      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_left_speed).toBe("0");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_right_speed).toBe("0");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_raw_left).toBe("0");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_raw_right).toBe("0");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_nonzero_left_speed).toBe("164");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_nonzero_right_speed).toBe("164");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_nonzero_frame_count).toBe("0");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_source).toBe("vendor_t1001_L_R");
      expect(summary.readback_summary.base.latest_t1001_observed_count).toBe("3");
      expect(summary.readback_summary.base.wheel_feedback_latest_left_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_right_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_raw_left).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_raw_right).toBe("0");
      expect(summary.readback_summary.base.wheel_left_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_right_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_raw_left).toBe("0");
      expect(summary.readback_summary.base.wheel_raw_right).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_nonzero_left_speed).toBe("164");
      expect(summary.readback_summary.base.wheel_feedback_latest_nonzero_right_speed).toBe("164");
      expect(summary.readback_summary.base.feedback_voltage_v).toBe("12.31");
      expect(summary.readback_summary.base.wheel_feedback_lr_nonzero_proven).toBe("false");
      expect(summary.readback_summary.base.wheel_feedback_nonzero_observed).toBe("false");
      expect(summary.readback_summary.base.feedback_link_status).toBe("t1001_observed_not_motion_proof");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_feedback_samples_latest.latest_result.sends_commands");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps slow feedback samples available for wheel L/R readback", async () => {
    // 现场 /api/base/status 可能被 fresh 串口读数拖慢；latest samples 是只读 artifact，应给 wheel L/R 慢读窗口。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/base/status": {
        delay_ms: 3000,
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/base/feedback-samples/latest": {
        delay_ms: 3000,
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
            t1001_observed_count: 2,
            t1001_feedback_frames: [{ T: 1001, L: 17, R: 19, v: 12.4 }],
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_nonzero_observed: true,
            wheel_feedback_summary: {
              frame_count: 2,
              latest_pair: {
                left_speed: 17,
                right_speed: 19,
                source: "vendor_t1001_L_R",
              },
              latest_nonzero_pair: {
                left_speed: 17,
                right_speed: 19,
                source: "vendor_t1001_L_R",
              },
              lr_nonzero_observed: true,
              matched_frame_count: 2,
              nonzero_frame_count: 2,
              source: "vendor_t1001_L_R",
            },
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const baseStatusReadback = summary.read_endpoints.find((item) => item.id === "base_status");
      const feedbackLatestReadback = summary.read_endpoints.find((item) => item.id === "base_feedback_samples_latest");

      expect(baseStatusReadback?.request_status).toBe("fetch_failed");
      expect(baseStatusReadback?.blocked_reasons).toContain("fetch_timeout_2400ms");
      expect(feedbackLatestReadback?.request_status).toBe("loaded");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_raw_left).toBe("17");
      expect(feedbackLatestReadback?.key_values.wheel_feedback_latest_raw_right).toBe("19");
      expect(summary.readback_summary.base.status).toBe("fetch_failed");
      expect(summary.readback_summary.base.latest_feedback_status).toBe("loaded");
      expect(summary.readback_summary.base.latest_t1001_observed_count).toBe("2");
      expect(summary.readback_summary.base.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(summary.readback_summary.base.wheel_raw_left).toBe("17");
      expect(summary.readback_summary.base.wheel_raw_right).toBe("19");
      expect(summary.readback_summary.base.feedback_link_status).toBe("t1001_lr_nonzero_material_observed_not_hil");
    } finally {
      await robotApi.close();
    }
  }, 12000);

  it("Robot Control summary derives fresh base status T1001 frame count from frames array", async () => {
    // 真实 /api/base/status 会返回 fresh T=1001 frames 数组；即使没有显式 count，也不能退回 stale samples 旧计数。
    const freshFrames = Array.from({ length: 12 }, () => ({ T: 1001, L: 0, R: 0, v: 12.43 }));
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/base/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          feedback_readback: {
            schema: "trashbot.upper_robot_api.v1.base_feedback_request_result",
            t1001_feedback_frames: freshFrames,
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_nonzero_observed: false,
            wheel_feedback_summary: {
              frame_count: 12,
              latest_pair: { left_speed: 0, right_speed: 0, source: "vendor_t1001_L_R" },
              latest_nonzero_pair: null,
              nonzero_frame_count: 0,
              source: "vendor_t1001_L_R",
            },
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
          },
          feedback_samples_latest: {
            freshness: { status: "stale" },
            latest_t1001_observed_count: 3,
            wheel_feedback_summary: {
              frame_count: 3,
              latest_pair: { left_speed: 0, right_speed: 0, source: "vendor_t1001_L_R" },
              latest_nonzero_pair: null,
              nonzero_frame_count: 0,
              source: "vendor_t1001_L_R",
            },
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const baseStatusReadback = summary.read_endpoints.find((item) => item.id === "base_status");

      expect(baseStatusReadback?.key_values.latest_t1001_observed_count).toBe("12");
      expect(baseStatusReadback?.key_values.feedback_samples_freshness_status).toBe("stale");
      expect(baseStatusReadback?.key_values.wheel_feedback_latest_left_speed).toBe("0");
      expect(baseStatusReadback?.key_values.wheel_feedback_latest_right_speed).toBe("0");
      expect(baseStatusReadback?.key_values.wheel_feedback_latest_raw_left).toBe("0");
      expect(baseStatusReadback?.key_values.wheel_feedback_latest_raw_right).toBe("0");
      expect(summary.readback_summary.base.latest_t1001_observed_count).toBe("12");
      expect(summary.readback_summary.base.latest_feedback_status).toBe("fresh_base_status_readback");
      expect(summary.readback_summary.base.wheel_feedback_latest_left_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_right_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_raw_left).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_latest_raw_right).toBe("0");
      expect(summary.readback_summary.base.wheel_left_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_right_speed).toBe("0");
      expect(summary.readback_summary.base.wheel_raw_left).toBe("0");
      expect(summary.readback_summary.base.wheel_raw_right).toBe("0");
      expect(summary.readback_summary.base.feedback_voltage_v).toBe("12.43");
      expect(summary.readback_summary.base.feedback_link_status).toBe("t1001_observed_not_motion_proof");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_status.feedback_readback.sends_commands");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps nested status T130 read errors ahead of direct base status and old samples", async () => {
    // 当前 T=130 读错可能只出现在 /api/status.base；合并时必须按更保守状态显示。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            feedback_ack: {
              t1001_observed: false,
              robot_ack_connected: false,
              reason: "T=1001 not observed after explicit T=130 request",
            },
            feedback_readback: {
              schema: "trashbot.upper_robot_api.v1.base_feedback_request_result",
              serial_read: {
                ok: false,
                error: {
                  type: "SerialException",
                  message: "status nested read failed",
                },
              },
              sends_commands: true,
              sends_motion_commands: false,
              robot_control_executed: false,
            },
          },
        },
      },
      "/api/base/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          feedback_ack: {
            t1001_observed: false,
            robot_ack_connected: false,
            reason: "T=1001 not observed after explicit T=130 request",
          },
          feedback_readback: {
            schema: "trashbot.upper_robot_api.v1.base_feedback_request_result",
            t1001_feedback_frames: [],
            t1001_feedback_status: "not_observed_after_t130",
            serial_read: {
              ok: true,
            },
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
          },
        },
      },
      "/api/base/feedback-samples/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            sends_commands: true,
            sends_motion_commands: false,
            robot_control_executed: false,
            t1001_observed_count: 3,
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_nonzero_observed: true,
            wheel_feedback_summary: {
              frame_count: 3,
              latest_pair: { left_speed: 0, right_speed: 0, source: "vendor_t1001_L_R" },
              latest_nonzero_pair: { left_speed: 164, right_speed: 164, source: "vendor_t1001_L_R" },
              nonzero_frame_count: 2,
              source: "vendor_t1001_L_R",
            },
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const baseStatusReadback = summary.read_endpoints.find((item) => item.id === "base_status");

      expect(baseStatusReadback?.dangerous_true_fields).not.toContain("feedback_readback.sends_commands");
      expect(summary.readback_summary.base.current_feedback_read_status).toBe("read_error");
      expect(summary.readback_summary.base.current_feedback_failure_reason).toContain("status nested read failed");
      expect(summary.readback_summary.base.latest_feedback_status).toBe("current_read_error");
      expect(summary.readback_summary.base.feedback_ack_status).toBe("read_error");
      expect(summary.readback_summary.base.feedback_link_status).toBe("current_t130_read_error");
      expect(summary.readback_summary.base.latest_t1001_observed_count).toBe("0");
      expect(summary.readback_summary.base.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_status.feedback_readback.sends_commands");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary treats structured HIL delivery as operator material only", async () => {
    // /api/operator/report 的 structured_hil_claims 是人工材料索引，不得把 delivery_success claim 当成顶层成功。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "ready",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          evidence_ref: "field-hil-20260611-0605-op",
          operator_report_material_only: true,
          safe_to_control: false,
          hil_pass: false,
          delivery_success: false,
          primary_actions_enabled: false,
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-0605.mp4",
            visible_content_proven: true,
            camera_artifacts_ref: "runtime/camera/latest_metrics.json",
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
            physical_motion_lidar_delta_proven: false,
            scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
            real_route_map_proven: true,
            route_map_ref: "runtime/routes/field-route.csv",
            delivery_success: true,
            site_state: "field_operator_claim_ready_for_review",
          },
          latest_result: {
            status: "loaded",
            operator_report_status: "ready_for_execution",
            structured_hil_claims: {
              delivery_success: true,
            },
            operator_report: {
              operator_present: true,
              physical_clearance_confirmed: true,
              emergency_stop_ready: true,
              evidence_ref: "field-hil-20260611-0605-op",
              structured_hil_claims: {
                external_video_recorded: true,
                external_video_ref: "phone-video-0605.mp4",
                visible_content_proven: true,
                camera_artifacts_ref: "runtime/camera/latest_metrics.json",
                wheel_feedback_lr_nonzero_proven: true,
                wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
                physical_motion_lidar_delta_proven: false,
                scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
                real_route_map_proven: true,
                route_map_ref: "runtime/routes/field-route.csv",
                delivery_success: true,
                site_state: "field_operator_claim_ready_for_review",
              },
            },
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const operatorReadback = summary.read_endpoints.find((item) => item.id === "operator_report_latest");

      expect(operatorReadback?.request_status).toBe("loaded");
      expect(operatorReadback?.dangerous_true_fields).toEqual([]);
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("operator_report_latest.structured_hil_claims.delivery_success");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("operator_report_latest.latest_result.operator_report.structured_hil_claims.delivery_success");
      expect(summary.operator_hil_material_summary.status).toBe("loaded");
      expect(summary.operator_hil_material_summary.report_status).toBe("ready_for_execution");
      expect(summary.operator_hil_material_summary.evidence_ref).toBe("field-hil-20260611-0605-op");
      expect(summary.operator_hil_material_summary.operator_present).toBe("true");
      expect(summary.operator_hil_material_summary.physical_clearance).toBe("true");
      expect(summary.operator_hil_material_summary.emergency_stop).toBe("true");
      expect(summary.operator_hil_material_summary.external_video).toBe("true; ref=phone-video-0605.mp4");
      expect(summary.operator_hil_material_summary.wheel_feedback).toBe("true; ref=runtime/wave_rover_feedback_debug.jsonl");
      expect(summary.operator_hil_material_summary.lidar_delta).toBe("false; ref=runtime/scan_delta/latest_metrics.json");
      expect(summary.operator_hil_material_summary.delivery_claim).toBe("true");
      expect(summary.first_jog_readiness_summary).toEqual({
        status: "ready_for_first_jog",
        basic_safety_ready: true,
        visual_material_ready: true,
        missing_fields: [],
        next_action: "press_try_move",
      });
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
      expect(summary.primary_actions_enabled).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("summarizes first-jog as ready when only visual material is missing", async () => {
    // 最新普通首屏口径：低速试动只需要安全确认；外部视频/可见相机材料只影响后续验收。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          structured_hil_claims: {
            external_video_recorded: false,
            visible_content_proven: false,
            wheel_feedback_lr_nonzero_proven: false,
            physical_motion_lidar_delta_proven: false,
            delivery_success: false,
            site_state: "plain_motion_precheck_ready_for_review",
          },
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.operator_hil_material_summary.operator_present).toBe("true");
      expect(summary.first_jog_readiness_summary).toEqual({
        status: "ready_for_first_jog",
        basic_safety_ready: true,
        visual_material_ready: false,
        missing_fields: [],
        next_action: "press_try_move",
      });
      expect(summary.safe_to_control).toBe(false);
      expect(summary.primary_actions_enabled).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary lifts nested map proof quality into readback summary", async () => {
    // 真实上位机的地图质量可能只在 latest_result.proof 内；PC summary 只能只读透传，不能触发 map refresh。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.status", "ready"),
          map_once_observed: true,
        },
      },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_proof_latest", "map_once_artifact_metadata_observed"),
          latest_result: {
            proof: {
              map_quality_status: "has_usable_map",
              map_metrics: {
                free_cells: 421,
              },
              algorithm_boundary: {
                map_usable_for_navigation: true,
              },
            },
          },
        },
      },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "not_loaded") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_loaded") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_loaded") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "not_loaded") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "not_loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "not_loaded") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "not_loaded") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "not_loaded") },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "not_loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "not_loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.map).toMatchObject({
        status: "map_once_artifact_metadata_observed",
        map_once_observed: "true",
        map_quality_status: "has_usable_map",
        map_free_cell_count: "421",
        map_usable_for_navigation: "true",
      });
      expect(summary.safe_to_control).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary still blocks forged structured HIL claims outside operator report", async () => {
    // 只有 operator_report_latest 端点的结构化 delivery claim 旁路；其它 endpoint 伪造同名字段仍 hard block。
    const robotApi = await listenRobotApiReadback({
      schema: "trashbot.upper_robot_api.v1.status",
      status: "unsafe_non_claim_success",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      structured_hil_claims: {
        delivery_success: true,
      },
      review: {
        delivery_success: true,
      },
      hil_pass: true,
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.console_status).toBe("blocked");
      expect(summary.robot_api_connection.dangerous_true_fields).toEqual(expect.arrayContaining([
        "status.structured_hil_claims.delivery_success",
        "status.review.delivery_success",
        "status.hil_pass",
      ]));
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("operator_report_latest.structured_hil_claims.delivery_success");
      expect(summary.blocked_reasons).toEqual(expect.arrayContaining([
        "dangerous_true_field:status.structured_hil_claims.delivery_success",
        "dangerous_true_field:status.review.delivery_success",
        "dangerous_true_field:status.hil_pass",
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("keeps robot connection readable when optional radar latest endpoints are not installed", async () => {
    // 真实上位机可能只提供 /api/radar/status；独立 latest 404 只能降级雷达证据，不能误判整机离线。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven"),
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 17 },
          ],
          path_preview_point_count: 2,
          path_preview_source_point_count: 18,
          path_preview_frame_id: "map",
        },
      },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { statusCode: 405, payload: { error: "method_not_allowed" } },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_not_running"),
          lifecycle_running: false,
          lifecycle_state: "stopped",
          continuous_scan_status: "lifecycle_not_running",
          continuous_window_observed: false,
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
          latest_t1001_observed_count: 3,
          wheel_feedback_lr_nonzero_proven: false,
        },
      },
      "/api/base/feedback-samples/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded"),
          t1001_observed_count: 3,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.console_status).toBe("loaded_fail_closed_summary");
      expect(summary.robot_api_connection.status).toBe("readable");
      expect(summary.robot_api_connection.blocked_count).toBe(0);
      expect(summary.robot_api_connection.failed_count).toBe(0);
      expect(summary.robot_api_connection.schema_mismatch_count).toBe(0);
      expect(summary.robot_api_connection.blocked_reasons).toEqual([]);
      expect(summary.readback_summary.lidar.latest_scan_proof_status).toBe("missing");
      expect(summary.readback_summary.lidar.latest_raw_packet_proof_status).toBe("missing");
      expect(summary.read_endpoints.find((item) => item.id === "radar_scan_proof_latest")).toEqual(expect.objectContaining({
        http_status: 404,
        request_status: "loaded",
        status: "missing",
        blocked_reasons: [],
      }));
      expect(summary.read_endpoints.find((item) => item.id === "free_roam_autonomy_latest")).toEqual(expect.objectContaining({
        http_status: 405,
        request_status: "loaded",
        status: "missing",
        blocked_reasons: [],
      }));
      expect(summary.readback_summary.free_roam).toEqual({
        status: "missing",
        runtime_status: "not_loaded",
        decision_state: "not_loaded",
        decision_reason: "not_loaded",
        stop_required: "not_loaded",
        stop_request_pending: "false",
        free_roam_stop_request_pending: "false",
        start_will_clear_stop_request: "false",
        start_clears_stop_request_not_blocking: "false",
        motion_start_blocked_by_stop_request: "false",
        stop_request_status_plain: "当前没有外部停止请求；自由移动启动不需要先清除停止请求。",
        artifact_only: "not_loaded",
        cmd_vel_publish_enabled: "not_loaded",
        start_ready: "false",
        free_move_ready: "false",
        free_move_start_ready: "false",
        motion_start_ready: "true",
        free_roam_motion_start_ready: "true",
        free_move_without_camera_allowed: "true",
        motion_without_radar_allowed: "true",
        free_move_minimal_precheck_safety_only: "true",
        free_move_safety_confirm_required: "true",
        free_move_camera_preflight_required: "false",
        free_move_radar_preflight_required: "false",
        motion_ready: "false",
        free_roam_motion_ready: "false",
        mapping_start_ready: "false",
        free_roam_mapping_start_ready: "false",
        mapping_start_requires_camera_first_frame: "true",
        mapping_start_requires_lidar_fresh: "true",
        mapping_start_missing: "camera_first_frame,lidar_fresh",
        mapping_readiness_ready: "false",
        mapping_blocked_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        mapping_missing_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        free_roam_mapping_ready: "false",
        free_roam_mapping_missing_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        mapping_ready: "false",
        mapping_missing: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        free_move_start_status_plain: "上车自由移动状态机未加载；可先用键盘或低速手控移动。",
        motion_runtime_status_plain: "当前未在自由移动运行态；上车自由移动状态机还未就绪。",
        mapping_acceptance_status_plain: "建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面。",
        plain_hint: "可先低速移动；上车自由移动状态机未加载时，先用键盘或低速手控，画面和雷达只影响建图。建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面。下一步：可先勾选现场安全确认，用键盘或低速手控移动；要启动上车自由移动状态机，先连接状态机并确认停止兜底。",
        next_action_plain: "可先勾选现场安全确认，用键盘或低速手控移动；要启动上车自由移动状态机，先连接状态机并确认停止兜底",
        motion_readiness_plain: "可先低速移动；上车自由移动状态机未加载时，先用键盘或低速手控，画面和雷达只影响建图。",
        mapping_start_readiness_plain: "建图启动未就绪；还差：画面首帧、雷达新鲜；同时等待上车自由移动状态机。",
        motion_sensor_dependency_status: "not_required_for_motion",
        motion_sensor_dependency_plain: "自由移动启动只看现场安全确认和停止兜底；相机、雷达和地图记录只影响建图验收。",
        mapping_readiness_plain: "建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面。",
        motion_next_action_plain: "上车自由移动状态机未加载；可先勾选现场安全确认，用键盘或低速手控移动；相机和雷达只影响建图。",
        mapping_start_next_action_plain: "先连接上车自由移动状态机；建图启动还差：画面首帧、雷达新鲜。",
        mapping_next_action_plain: "先连接上车自由移动状态机；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面。",
        runtime_artifact_proven: "not_loaded",
        state_machine_observed: "not_loaded",
        ros2_runtime_proven: "not_loaded",
        gate_count: "0",
      });
    } finally {
      await robotApi.close();
    }
  });

  it("surfaces free-roam autonomy runtime state from latest artifact readback", async () => {
    // 自动扫图 runtime 只读上车端 artifact；PC summary 展示状态机判断，但继续保持自动发车锁定。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          free_roam_runtime_artifact_proven: true,
          free_roam_state_machine_observed: true,
          ros2_runtime_proven: true,
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "turning_for_coverage",
              reason: "地图覆盖暂未增长，原地扫描寻找新方向",
              stop_required: false,
              gates: [
                {
                  id: "operator_confirmed",
                  label: "现场安全确认",
                  state: "ready",
                  evidence: "已勾选现场安全确认",
                  next_action: "继续保持现场可接管",
                },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("start_ready");
      expect(summary.safe_command_boundary.free_roam_autonomy_runtime).toEqual({
        status: "loaded",
        state: "turning_for_coverage",
        reason: "地图覆盖暂未增长，原地扫描寻找新方向",
        stop_required: false,
        artifact_only: true,
        cmd_vel_publish_enabled: false,
      });
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "operator_confirmed",
          state: "ready",
          evidence: "已勾选现场安全确认",
        }),
        expect.objectContaining({
          id: "motion_hil_unlock",
          state: "blocked",
        }),
      ]));
      expect(summary.readback_summary.free_roam).toEqual({
        status: "start_ready",
        runtime_status: "loaded",
        decision_state: "turning_for_coverage",
        decision_reason: "地图覆盖暂未增长，原地扫描寻找新方向",
        stop_required: "false",
        stop_request_pending: "false",
        free_roam_stop_request_pending: "false",
        start_will_clear_stop_request: "false",
        start_clears_stop_request_not_blocking: "false",
        motion_start_blocked_by_stop_request: "false",
        stop_request_status_plain: "当前没有外部停止请求；自由移动启动不需要先清除停止请求。",
        artifact_only: "true",
        cmd_vel_publish_enabled: "false",
        start_ready: "true",
        free_move_ready: "true",
        free_move_start_ready: "true",
        motion_start_ready: "true",
        free_roam_motion_start_ready: "true",
        free_move_without_camera_allowed: "true",
        motion_without_radar_allowed: "true",
        free_move_minimal_precheck_safety_only: "true",
        free_move_safety_confirm_required: "true",
        free_move_camera_preflight_required: "false",
        free_move_radar_preflight_required: "false",
        motion_ready: "false",
        free_roam_motion_ready: "false",
        mapping_start_ready: "false",
        free_roam_mapping_start_ready: "false",
        mapping_start_requires_camera_first_frame: "true",
        mapping_start_requires_lidar_fresh: "true",
        mapping_start_missing: "camera_first_frame,lidar_fresh",
        mapping_readiness_ready: "false",
        mapping_blocked_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        mapping_missing_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        free_roam_mapping_ready: "false",
        free_roam_mapping_missing_reasons: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        mapping_ready: "false",
        mapping_missing: "camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview",
        free_move_start_status_plain: "自由移动可启动；只需现场安全确认和停止兜底。",
        motion_runtime_status_plain: "当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。",
        mapping_acceptance_status_plain: "建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。",
        plain_hint: "可先自由移动；只需要现场安全确认和停止兜底。建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。下一步：勾选现场安全确认后可先自由移动。",
        next_action_plain: "勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面",
        motion_readiness_plain: "可先自由移动；只需要现场安全确认和停止兜底。",
        motion_sensor_dependency_status: "not_required_for_motion",
        motion_sensor_dependency_plain: "自由移动启动只看现场安全确认和停止兜底；相机、雷达和地图记录只影响建图验收。",
        mapping_start_readiness_plain: "建图启动未就绪；还差：画面首帧、雷达新鲜；地图记录和地图画面只影响建图验收。",
        mapping_readiness_plain: "建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。",
        motion_next_action_plain: "勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。",
        mapping_start_next_action_plain: "先补齐建图启动材料：画面首帧、雷达新鲜；低速自由移动不受影响。",
        mapping_next_action_plain: "建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。",
        runtime_artifact_proven: "true",
        state_machine_observed: "true",
        ros2_runtime_proven: "true",
        gate_count: "1",
      });
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("workstation summary route caps slow base readback so the plain first screen stays responsive", async () => {
    // 真实上位机 base/status 可能卡到 8s 以上；summary 首屏要先返回地图/画面/Nav2事实，轮速慢读交给独立刷新入口。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded") },
      "/api/base/status": {
        delay_ms: 4500,
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
          feedback_readback: {
            wheel_feedback_summary: {
              latest_pair: { left_speed: 0.03, right_speed: 0.04 },
              lr_nonzero_observed: true,
            },
          },
        },
      },
      "/api/base/feedback-samples/latest": {
        delay_ms: 4500,
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded"),
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const startedAt = Date.now();
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(robotApi.baseUrl)}`);
      const elapsedMs = Date.now() - startedAt;
      const summary = await response.json() as RobotControlSummaryResponse;

      expect(response.status).toBe(200);
      expect(elapsedMs).toBeLessThan(4000);
      expect(summary.read_endpoints.find((item) => item.id === "base_status")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_2400ms"],
      }));
      expect(summary.read_endpoints.find((item) => item.id === "base_feedback_samples_latest")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_2400ms"],
      }));
      expect(summary.readback_summary.base.wheel_feedback_latest_raw_left).toBe("not_loaded");
      expect(summary.readback_summary.base.current_feedback_read_status).toBe("not_loaded");
      expect(summary.robot_api_connection.blocked_reasons).toContain("base_status:fetch_timeout_2400ms");
      expect(summary.robot_api_connection.blocked_reasons).toContain("base_feedback_samples_latest:fetch_timeout_2400ms");
      expect(summary.robot_api_connection.blocked_reasons).not.toContain("base_status:fetch_timeout_4000ms");
      expect(summary.robot_api_connection.blocked_reasons).not.toContain("base_feedback_samples_latest:fetch_timeout_4000ms");
    } finally {
      await workstation.close();
      await robotApi.close();
    }
  }, 12_000);

  it("workstation live-summary route exposes a flat read-only current card for field curl checks", async () => {
    // 现场只想 curl 当前卡点时，不应要求记住 live_closure_summary 嵌套路径；新端点仍必须复用 summary 的只读聚合。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      robot_control_executed: false,
      evidence_ref: `${status}-proof`,
    });
    const pathPreviewPoints = [
      { x: 0, y: 0, frame_id: "map", source_index: 0 },
      { x: 0.8, y: 0, frame_id: "map", source_index: 1 },
    ];
    const robotApi = await listenSerialRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.status", "ready"),
          nav2_base_command_mode: "ros",
        },
      },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
        },
      },
      "/api/map/preview": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_preview_result", "loaded"),
          path_preview_points: pathPreviewPoints,
          path_preview_frame_id: "map",
        },
      },
      "/api/localize/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed"),
      },
      "/api/nav2/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "path_generated"),
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 2,
          path_preview_points: pathPreviewPoints,
          path_preview_frame_id: "map",
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "path_generated"),
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 2,
          path_preview_points: pathPreviewPoints,
          path_preview_frame_id: "map",
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution_latest", "goal_succeeded"),
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            nav2_goal_execution_proven: true,
            base_command_mode: "ros",
            base_feedback_summary: {
              wheel_feedback_lr_nonzero_proven: false,
              sample_count: 2,
              nonzero_sample_count: 0,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
        },
      },
      "/api/base/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
      },
      "/api/base/feedback-samples/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded"),
      },
      "/api/delivery/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.delivery_latest", "not_submitted"),
      },
      "/api/free-roam/autonomy/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
      },
      "/api/camera/health": {
        payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed"),
      },
      "/api/camera/devices": {
        payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded"),
      },
      "/api/radar/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded"),
      },
      "/api/radar/scan-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded"),
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const summaryResponse = await requestJson(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(robotApi.baseUrl)}`);
      const liveResponse = await requestJson(`${workstation.baseUrl}/api/robot-control/live-summary?baseUrl=${encodeURIComponent(robotApi.baseUrl)}`);
      const summary = summaryResponse.body as RobotControlSummaryResponse;
      const live = liveResponse.body as RobotControlLiveSummaryResponse;

      expect(liveResponse.status).toBe(200);
      expect(live.schema).toBe("trashbot.pc_tools_workstation.robot_control_live_summary.v1");
      expect(live.workstation_endpoint).toBe("/api/robot-control/live-summary");
      expect(live.summary_endpoint).toBe("/api/robot-control/summary");
      expect(live.readback_only).toBe(true);
      expect(live.status).toBe(summary.live_closure_summary?.status);
      expect(live.status).toBe("needs_wheel_rerun");
      expect(summary.status).toBe(live.status);
      expect(summary.live_status).toBe(live.status);
      expect(live.summary_plain).toBe(summary.live_closure_summary?.summary_plain);
      expect(summary.summary_plain).toBe(live.summary_plain);
      expect(live.next_action_plain).toBe(summary.live_closure_summary?.next_action_plain);
      expect(summary.next_action_plain).toBe(live.next_action_plain);
      expect(summary.objective_audit_summary_plain).toBe(summary.live_closure_summary?.objective_audit_summary_plain);
      expect(summary.objective_audit_next_objective_id).toBe(summary.live_closure_summary?.objective_audit_next_objective_id);
      expect(summary.fixed_objective_audit_summary_endpoint).toBe("/api/robot-control/summary");
      expect(summary.objective_audit_sends_motion_when_clicked).toBe(false);
      expect(summary.map_display_primary_tool).toBe("pc_big_map");
      expect(summary.map_display_primary_url).toBe("/map");
      expect(summary.map_display_primary_action_label).toBe("进入地图大屏");
      expect(summary.map_display_default_zoom_percent).toBe("400%");
      expect(summary.map_display_max_zoom_percent).toBe("2400%");
      expect(summary.map_display_wysiwyg_overlays).toEqual(["image", "route", "robot", "radar"]);
      expect(summary.map_display_ros2_companion_tools).toEqual(["rviz2", "foxglove"]);
      expect(summary.map_display_rviz_launch_command).toBe("ros2 launch ros2_trashbot_bringup rviz.launch.py");
      expect(summary.map_display_foxglove_bridge_launch_command).toBe("ros2 launch foxglove_bridge foxglove_bridge_launch.xml");
      expect(summary.map_display_foxglove_websocket_url).toBe("ws://192.168.1.11:8765");
      expect(summary.map_display_ros2_observe_topics).toEqual([
        "/map",
        "/scan",
        "/tf",
        "/plan",
        "/local_plan",
        "/amcl_pose",
        "/global_costmap/costmap",
        "/local_costmap/costmap",
      ]);
      expect(summary.map_display_sends_motion_when_clicked).toBe(false);
      expect(summary.map_display_starts_ros2).toBe(false);
      expect(summary.map_display_starts_rviz2).toBe(false);
      expect(summary.map_display_starts_foxglove).toBe(false);
      expect(summary.map_display_starts_nav2).toBe(false);
      expect(summary.map_display_starts_map_runtime).toBe(false);
      expect(summary.live_wysiwyg_ready).toBe(live.live_wysiwyg_ready);
      expect(summary.live_wysiwyg_missing_surface_ids).toEqual(live.live_wysiwyg_missing_surface_ids);
      expect(summary.live_wysiwyg_needs_refresh).toBe(live.live_wysiwyg_needs_refresh);
      expect(summary.live_wysiwyg_readback_gap_surface_ids).toEqual(live.live_wysiwyg_readback_gap_surface_ids);
      expect(summary.live_wysiwyg_primary_readback_gap_surface_id).toBe(live.live_wysiwyg_primary_readback_gap_surface_id);
      expect(summary.live_wysiwyg_missing_surface_refresh_endpoints).toEqual(live.live_wysiwyg_missing_surface_refresh_endpoints);
      expect(summary.live_wysiwyg_missing_surface_refresh_labels).toEqual(live.live_wysiwyg_missing_surface_refresh_labels);
      expect(summary.live_wysiwyg_primary_refresh_endpoint).toBe(live.live_wysiwyg_primary_refresh_endpoint);
      expect(summary.live_wysiwyg_primary_refresh_label).toBe(live.live_wysiwyg_primary_refresh_label);
      expect(summary.live_wysiwyg_refresh_plan_available).toBe(live.live_wysiwyg_refresh_plan_available);
      expect(summary.live_wysiwyg_refresh_sequence).toEqual(live.live_wysiwyg_refresh_sequence);
      expect(summary.live_wysiwyg_refresh_sequence_labels).toEqual(live.live_wysiwyg_refresh_sequence_labels);
      expect(summary.live_wysiwyg_refresh_sends_motion).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_nav2).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_manual).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_keyboard).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_free_roam).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_radar_lifecycle).toBe(false);
      expect(summary.live_wysiwyg_refresh_starts_map_runtime).toBe(false);
      expect(summary.live_wysiwyg_surface_summaries).toEqual(live.live_wysiwyg_surface_summaries);
      expect(live.nav2_route_ready).toBe(true);
      expect(summary.route_ready).toBe(true);
      expect(summary.nav2_route_ready).toBe(true);
      expect(live.nav2_goal_succeeded).toBe(true);
      expect(summary.nav2_complete).toBe(true);
      expect(summary.nav2_goal_succeeded).toBe(true);
      expect(summary.route_complete).toBe(false);
      expect(summary.trip_complete).toBe(false);
      expect(summary.motion_ready).toBe(true);
      expect(summary.motion_complete).toBe(false);
      expect(live.wheel_lr_nonzero_proven).toBe(false);
      expect(summary.wheel_lr_nonzero).toBe(false);
      expect(summary.wheel_lr_nonzero_proven).toBe(false);
      expect(live.wheel_rerun_ready_for_safety_confirm).toBe(true);
      expect(summary.wheel_rerun_ready_for_safety_confirm).toBe(true);
      expect(live.wheel_rerun_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
      expect(summary.wheel_rerun_start_endpoint).toBe("/api/robot-control/nav2/goal/execute");
      expect(live.wheel_rerun_start_sends_motion).toBe(true);
      expect(summary.wheel_rerun_start_sends_motion).toBe(true);
      expect(live.wheel_rerun_requires_safety_confirm).toBe(true);
      expect(summary.wheel_rerun_requires_safety_confirm).toBe(true);
      expect(live.wheel_rerun_readback_endpoints).toEqual([
        "/api/robot-control/map/preview",
        "/api/robot-control/nav2/goal/execution/latest",
        "/api/robot-control/base/feedback-samples",
        "/api/robot-control/delivery/latest",
        "/api/robot-control/summary",
      ]);
      expect(summary.wheel_rerun_readback_endpoints).toEqual(live.wheel_rerun_readback_endpoints);
      expect(live.wheel_rerun_required_success_markers).toEqual([
        "map_route_visible",
        "nav2_goal_succeeded",
        "same_window_wheel_lr_nonzero",
        "delivery_success",
      ]);
      expect(summary.wheel_rerun_required_success_markers).toEqual(live.wheel_rerun_required_success_markers);
      expect(live.wheel_rerun_current_gap_plain).toContain("当前缺口");
      expect(live.wheel_rerun_no_extra_precheck_plain).toContain("发车前预检只看现场安全确认");
      expect(live.delivery_success).toBe(false);
      expect(summary.route_delivery_success).toBe(false);
      expect(live.delivery_success_required).toBe(true);
      expect(summary.delivery_success_required).toBe(true);
      expect(live.delivery_next_action_plain).toContain("delivery success");
      expect(live.fixed_delivery_latest_endpoint).toBe("/api/robot-control/delivery/latest");
      expect(live.fixed_delivery_complete_endpoint).toBe("/api/robot-control/delivery/complete");
      expect(live.delivery_latest_readback_only).toBe(true);
      expect(live.delivery_complete_sends_motion).toBe(false);
      expect(live.live_wysiwyg_map_visible).toBe(true);
      expect(live.path_current_visible).toBe(true);
      expect(live.live_wysiwyg_camera_visible).toBe(false);
      expect(live.camera_source_diagnosis_status).toBe(summary.live_closure_summary?.camera_source_diagnosis_status);
      expect(live.camera_source_diagnosis_not_exclusive).toBe(summary.live_closure_summary?.camera_source_diagnosis_not_exclusive);
      expect(live.camera_shared_preview_exclusive_camera_claim).toBe(summary.live_closure_summary?.camera_shared_preview_exclusive_camera_claim);
      expect(live.camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.camera_recovery_next_action_plain);
      expect(live.camera_hardware_action_required).toBe(summary.live_closure_summary?.camera_hardware_action_required);
      expect(live.camera_hardware_action_label).toBe(summary.live_closure_summary?.camera_hardware_action_label);
      expect(live.camera_usb_full_speed_detected).toBe(summary.live_closure_summary?.camera_usb_full_speed_detected);
      expect(live.camera_blocks_mapping_start).toBe(summary.live_closure_summary?.camera_blocks_mapping_start);
      expect(live.camera_blocks_free_move).toBe(false);
      expect(live.camera_reprobe_after_hardware_action_required).toBe(summary.live_closure_summary?.camera_reprobe_after_hardware_action_required);
      expect(live.camera_reprobe_sequence).toEqual(summary.live_closure_summary?.camera_reprobe_sequence);
      expect(live.fixed_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
      expect(live.fixed_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
      expect(live.camera_recovery_sends_motion).toBe(false);
      expect(live.camera_recovery_starts_map_runtime).toBe(false);
      expect(live.radar_overlay_status).toBe(summary.live_closure_summary?.radar_overlay_status);
      expect(summary.live_wysiwyg_ready).toBe(summary.live_closure_summary?.live_wysiwyg_ready);
      expect(summary.wysiwyg_ready).toBe(false);
      expect(summary.wysiwyg_complete).toBe(false);
      expect(summary.live_wysiwyg_missing_surface_ids).toEqual(summary.live_closure_summary?.live_wysiwyg_missing_surface_ids);
      expect(summary.live_wysiwyg_refresh_sends_motion).toBe(false);
      expect(summary.camera_current_visible).toBe(summary.live_closure_summary?.camera_current_visible);
      expect(summary.camera_ready).toBe(summary.live_closure_summary?.camera_current_visible);
      expect(summary.camera_first_frame_ready).toBe(summary.live_closure_summary?.camera_current_visible);
      expect(summary.camera_visible).toBe(summary.live_closure_summary?.camera_current_visible);
      expect(summary.live_wysiwyg_camera_visible).toBe(summary.live_closure_summary?.live_wysiwyg_camera_visible);
      expect(summary.camera_needs_usb_fix).toBe(summary.live_closure_summary?.camera_hardware_action_required);
      expect(summary.camera_usb_high_speed).toBe(false);
      expect(summary.camera_usb_speed).toBe(summary.live_closure_summary?.camera_usb_speed);
      expect(summary.camera_source_diagnosis_status).toBe(summary.live_closure_summary?.camera_source_diagnosis_status);
      expect(summary.camera_source_diagnosis_not_exclusive).toBe(summary.live_closure_summary?.camera_source_diagnosis_not_exclusive);
      expect(summary.camera_source_diagnosis_plain_hint).toBe(summary.live_closure_summary?.live_wysiwyg_camera_source_diagnosis_plain_hint);
      expect(summary.camera_recovery_next_action_plain).toBe(summary.live_closure_summary?.camera_recovery_next_action_plain);
      expect(summary.camera_recovery_sends_motion).toBe(false);
      expect(summary.camera_blocks_mapping_start).toBe(summary.live_closure_summary?.camera_blocks_mapping_start);
      expect(summary.camera_blocks_free_move).toBe(false);
      expect(summary.camera_reprobe_after_hardware_action_required).toBe(summary.live_closure_summary?.camera_reprobe_after_hardware_action_required);
      expect(summary.camera_reprobe_sequence).toEqual(summary.live_closure_summary?.camera_reprobe_sequence);
      expect(summary.camera_recovery_starts_map_runtime).toBe(false);
      expect(summary.fixed_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
      expect(summary.fixed_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
      expect(summary.live_wysiwyg_camera_shared_preview_client_count).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_client_count);
      expect(summary.live_wysiwyg_camera_shared_preview_upstream_active).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_upstream_active);
      expect(summary.live_wysiwyg_camera_shared_preview_exclusive_camera_claim).toBe(summary.live_closure_summary?.live_wysiwyg_camera_shared_preview_exclusive_camera_claim);
      expect(summary.map_current_visible).toBe(summary.live_closure_summary?.map_current_visible);
      expect(summary.map_visible).toBe(summary.live_closure_summary?.map_current_visible);
      expect(summary.path_current_visible).toBe(summary.live_closure_summary?.path_current_visible);
      expect(summary.path_visible).toBe(summary.live_closure_summary?.path_current_visible);
      expect(summary.live_wysiwyg_map_visible).toBe(summary.live_closure_summary?.live_wysiwyg_map_visible);
      expect(summary.radar_visible).toBe(summary.live_closure_summary?.radar_map_points_visible);
      expect(summary.radar_points_visible).toBe(summary.live_closure_summary?.radar_map_points_visible);
      expect(summary.radar_ready).toBe(summary.live_closure_summary?.mapping_lidar_fresh_readback_ready);
      expect(summary.radar_fresh).toBe(summary.live_closure_summary?.mapping_lidar_fresh_readback_ready);
      expect(summary.radar_map_ready).toBe(summary.live_closure_summary?.radar_map_points_visible);
      expect(summary.radar_map_points_visible).toBe(summary.live_closure_summary?.radar_map_points_visible);
      expect(summary.radar_overlay_status).toBe(summary.live_closure_summary?.radar_overlay_status);
      expect(live.radar_overlay_current_point_count).toBe(summary.live_closure_summary?.radar_overlay_current_point_count);
      expect(summary.radar_overlay_current_point_count).toBe(summary.live_closure_summary?.radar_overlay_current_point_count);
      expect(live.radar_overlay_source_point_count).toBe(summary.live_closure_summary?.radar_overlay_source_point_count);
      expect(summary.radar_overlay_source_point_count).toBe(summary.live_closure_summary?.radar_overlay_source_point_count);
      expect(live.radar_overlay_primary_blocked_reason).toBe(summary.live_closure_summary?.radar_overlay_primary_blocked_reason);
      expect(summary.radar_overlay_primary_blocked_reason).toBe(summary.live_closure_summary?.radar_overlay_primary_blocked_reason);
      expect(summary.radar_overlay_current_vs_source_plain).toBe(summary.live_closure_summary?.radar_overlay_current_vs_source_plain);
      expect(summary.radar_overlay_refresh_next_action_plain).toBe(summary.live_closure_summary?.radar_overlay_refresh_next_action_plain);
      expect(live.radar_overlay_needs_refresh).toBe(summary.live_closure_summary?.radar_overlay_needs_refresh);
      expect(summary.radar_overlay_needs_refresh).toBe(summary.live_closure_summary?.radar_overlay_needs_refresh);
      expect(live.radar_overlay_blocks_wysiwyg).toBe(summary.live_closure_summary?.radar_overlay_blocks_wysiwyg);
      expect(summary.radar_overlay_blocks_wysiwyg).toBe(summary.live_closure_summary?.radar_overlay_blocks_wysiwyg);
      expect(live.radar_overlay_blocks_free_move).toBe(false);
      expect(summary.radar_overlay_blocks_free_move).toBe(false);
      expect(live.radar_overlay_recovery_sequence).toEqual(summary.live_closure_summary?.radar_overlay_recovery_sequence);
      expect(summary.radar_overlay_recovery_sequence).toEqual(summary.live_closure_summary?.radar_overlay_recovery_sequence);
      expect(live.fixed_radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
      expect(summary.fixed_radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
      expect(live.fixed_radar_overlay_map_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(summary.fixed_radar_overlay_map_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(live.radar_overlay_refresh_sends_motion).toBe(false);
      expect(summary.radar_overlay_refresh_sends_motion).toBe(false);
      expect(live.radar_overlay_refresh_starts_radar_lifecycle).toBe(false);
      expect(summary.radar_overlay_refresh_starts_radar_lifecycle).toBe(false);
      expect(live.mapping_lidar_fresh_readback_ready).toBe(summary.live_closure_summary?.mapping_lidar_fresh_readback_ready);
      expect(live.mapping_lidar_fresh_gate_conflict).toBe(summary.live_closure_summary?.mapping_lidar_fresh_gate_conflict);
      expect(live.mapping_lidar_fresh_gate_status).toBe(summary.live_closure_summary?.mapping_lidar_fresh_gate_status);
      expect(live.mapping_lidar_fresh_refresh_sequence).toEqual(summary.live_closure_summary?.mapping_lidar_fresh_refresh_sequence);
      expect(live.mapping_lidar_fresh_refresh_sends_motion).toBe(false);
      expect(live.mapping_lidar_fresh_refresh_starts_radar_lifecycle).toBe(false);
      expect(live.mapping_lidar_fresh_blocks_free_move).toBe(false);
      expect(live.free_roam_ready).toBe(true);
      expect(summary.free_roam_ready).toBe(true);
      expect(live.free_roam_start_ready).toBe(true);
      expect(summary.free_roam_start_ready).toBe(true);
      expect(summary.free_move_ready).toBe(true);
      expect(live.free_roam_motion_start_ready).toBe(true);
      expect(summary.free_roam_motion_start_ready).toBe(true);
      expect(live.free_roam_motion_ready).toBe(false);
      expect(summary.free_move_running).toBe(false);
      expect(summary.free_move_complete).toBe(false);
      expect(summary.free_roam_motion_ready).toBe(false);
      expect(live.free_move_without_camera_allowed).toBe(true);
      expect(summary.free_move_without_camera_allowed).toBe(true);
      expect(live.free_roam_motion_without_radar_allowed).toBe(true);
      expect(summary.free_roam_motion_without_radar_allowed).toBe(true);
      expect(live.free_roam_mapping_start_ready).toBe(summary.live_closure_summary?.mapping_start_ready);
      expect(summary.mapping_start_ready).toBe(summary.live_closure_summary?.mapping_start_ready);
      expect(summary.mapping_ready).toBe(false);
      expect(summary.mapping_complete).toBe(false);
      expect(summary.free_roam_mapping_start_ready).toBe(summary.live_closure_summary?.mapping_start_ready);
      expect(live.free_roam_mapping_start_missing_reasons).toEqual(summary.live_closure_summary?.mapping_start_missing_reasons);
      expect(summary.mapping_start_missing_reasons).toEqual(summary.live_closure_summary?.mapping_start_missing_reasons);
      expect(summary.free_roam_mapping_start_missing_reasons).toEqual(summary.live_closure_summary?.mapping_start_missing_reasons);
      expect(live.free_roam_mapping_ready).toBe(false);
      expect(summary.free_roam_mapping_ready).toBe(false);
      expect(summary.mapping_acceptance_ready).toBe(false);
      expect(live.free_roam_mapping_missing_reasons).toEqual(summary.live_closure_summary?.mapping_acceptance_missing_reasons);
      expect(summary.free_roam_mapping_missing_reasons).toEqual(summary.live_closure_summary?.mapping_acceptance_missing_reasons);
      expect(summary.mapping_acceptance_missing_reasons).toEqual(summary.live_closure_summary?.mapping_acceptance_missing_reasons);
      expect(summary.mapping_start_requires_camera_first_frame).toBe(true);
      expect(summary.mapping_start_requires_lidar_fresh).toBe(true);
      expect(summary.precheck_ready).toBe(true);
      expect(summary.precheck_complete).toBe(true);
      expect(summary.mapping_unblock_allows_free_move).toBe(true);
      expect(summary.fixed_mapping_start_endpoint).toBe("/api/robot-control/map/start");
      expect(summary.fixed_mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(live.keyboard_ready).toBe(true);
      expect(summary.keyboard_ready).toBe(true);
      expect(summary.keyboard_continuous_ready).toBe(true);
      expect(summary.keyboard_continuous_motion_verified).toBe(false);
      expect(summary.keyboard_wheel_lr_nonzero).toBe(false);
      expect(summary.keyboard_stop_after_release).toBe(false);
      expect(live.keyboard_enable_sends_motion).toBe(false);
      expect(summary.keyboard_enable_sends_motion).toBe(false);
      expect(live.keyboard_hold_to_move_required).toBe(true);
      expect(summary.keyboard_hold_to_move_required).toBe(true);
      expect(summary.keyboard_pulse_interval_ms).toBe(live.keyboard_pulse_interval_ms);
      expect(summary.keyboard_pulse_duration_ms).toBe(live.keyboard_pulse_duration_ms);
      expect(summary.keyboard_stop_triggers).toEqual(live.keyboard_stop_triggers);
      expect(summary.keyboard_acceptance_plain).toBe(live.keyboard_acceptance_plain);
      expect(live.keyboard_manual_endpoint).toBe("/api/robot-control/base/manual");
      expect(live.keyboard_stop_endpoint).toBe("/api/robot-control/base/stop");
      expect(live.keyboard_feedback_readback_endpoint).toBe("/api/robot-control/base/feedback-samples");
      expect(summary.keyboard_summary_endpoint).toBe("/api/robot-control/summary");
      expect(summary.minimal_precheck_safety_only).toBe(true);
      expect(summary.safety_confirm_required_for_motion).toBe(summary.live_closure_summary?.safety_confirm_required_for_motion);
      expect(summary.live_motion_runbook_minimal_precheck_safety_only).toBe(true);
      expect(summary.live_motion_runbook_safety_confirm_required).toBe(summary.live_closure_summary?.live_motion_runbook_safety_confirm_required);
      expect(summary.live_motion_runbook_minimal_precheck_plain).toBe(summary.live_closure_summary?.live_motion_runbook_minimal_precheck_plain);
      expect(summary.live_motion_runbook_items).toEqual(summary.live_closure_summary?.live_motion_runbook_items);
      expect(summary.live_motion_runbook_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_action_ids);
      expect(summary.live_motion_runbook_ready_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_ready_action_ids);
      expect(summary.live_motion_runbook_blocked_action_ids).toEqual(summary.live_closure_summary?.live_motion_runbook_blocked_action_ids);
      expect(summary.live_motion_runbook_primary_action_id).toBe(summary.live_closure_summary?.live_motion_runbook_primary_action_id);
      expect(summary.live_motion_runbook_summary_plain).toBe(summary.live_closure_summary?.live_motion_runbook_summary_plain);
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
      expect(summary.trip_missing_evidence).toEqual(summary.primary_missing_evidence);
      expect(summary.trip_proof_plain).toBe(summary.primary_proof_plain);
      expect(summary.keyboard_start_endpoint).toBe("/api/robot-control/base/manual");
      expect(summary.keyboard_acceptance_endpoints).toEqual([
        "/api/robot-control/base/feedback-samples",
        "/api/robot-control/summary",
      ]);
      expect(summary.keyboard_completed).toBe(false);
      expect(summary.keyboard_proof_status).toBe("ready_to_verify");
      expect(summary.keyboard_missing_evidence).toEqual(["same_hold_window_wheel_lr_nonzero", "stop_after_release"]);
      expect(summary.keyboard_proof_plain).toContain("可验证键盘连续手控");
      expect(summary.free_move_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
      expect(summary.free_move_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
      expect(summary.free_move_acceptance_endpoints).toEqual([
        "/api/robot-control/free-roam/autonomy/latest",
        "/api/robot-control/summary",
      ]);
      expect(summary.free_move_proof_status).toBe("ready_to_verify");
      expect(summary.free_move_missing_evidence).toEqual(["free_roam_latest_motion_ready"]);
      expect(summary.free_move_proof_plain).toContain("可验证自由自助移动");
      expect(summary.mapping_start_endpoint).toBe("/api/robot-control/map/start");
      expect(summary.mapping_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(summary.mapping_acceptance_endpoints).toEqual([
        "/api/robot-control/map/preview",
        "/api/robot-control/summary",
      ]);
      expect(summary.mapping_proof_status).toBe("blocked");
      expect(summary.mapping_missing_evidence).toContain("camera_first_frame");
      expect(summary.mapping_proof_plain).toContain("建图暂不可启动");
      expect(summary.free_move_minimal_precheck_safety_only).toBe(true);
      expect(summary.free_move_safety_confirm_required).toBe(true);
      expect(summary.free_move_camera_preflight_required).toBe(false);
      expect(summary.free_move_radar_preflight_required).toBe(false);
      expect(summary.free_move_blocked_by_camera_wysiwyg).toBe(false);
      expect(summary.free_move_blocked_by_radar_wysiwyg).toBe(false);
      expect(summary.fixed_free_roam_start_endpoint).toBe("/api/robot-control/free-roam/autonomy/start");
      expect(summary.fixed_free_roam_stop_endpoint).toBe("/api/robot-control/free-roam/autonomy/stop");
      expect(live.map_display_engineering_tools_visible_by_default).toBe(false);
      expect(live.map_display_engineering_tools_action_label).toBe("工程观察");
      expect(live.map_display_ordinary_user_tool).toBe("pc_big_map");
      expect(live.map_display_direct_map_keeps_page_fullscreen_without_browser_api).toBe(true);
      expect(live.map_display_direct_map_browser_fullscreen_required).toBe(false);
      expect(live.map_display_rviz_role_plain).toContain("本地工程调试");
      expect(live.map_display_foxglove_role_plain).toContain("远程浏览器大屏观察");
      expect(live.map_display_foxglove_bridge_install_command).toBe("sudo apt install ros-humble-foxglove-bridge");
      expect(live.map_display_engineering_tools_sends_motion).toBe(false);
      expect(live.objective_audit_missing_objective_ids).toContain("motion");
      expect(live.sends_motion_when_clicked).toBe(false);
      expect(live.starts_nav2).toBe(false);
      expect(live.starts_manual).toBe(false);
      expect(live.starts_keyboard).toBe(false);
      expect(live.starts_free_roam).toBe(false);
      expect(live.starts_map_runtime).toBe(false);
      expect(live.submits_delivery).toBe(false);
      expect(live.stops_motion).toBe(false);
      expect(live.publishes_cmd_vel).toBe(false);
      expect(Object.prototype.hasOwnProperty.call(live, "live_closure_summary")).toBe(false);
      expect(robotApi.requestedUrls).not.toContain("/api/nav2/goal/execute");
      expect(robotApi.requestedUrls).not.toContain("/api/base/manual");
      expect(robotApi.requestedUrls).not.toContain("/api/free-roam/autonomy/start");
      expect(robotApi.requestedUrls).not.toContain("/api/map/start");
      expect(robotApi.requestedUrls).not.toContain("/api/delivery/complete");
    } finally {
      await workstation.close();
      await robotApi.close();
    }
  });

  it("Robot Control summary caps slow camera devices readback for a responsive plain first screen", async () => {
    // 板端 camera devices 会做 v4l2 只读枚举；summary 首屏不能为了设备列表卡住地图/路线/雷达状态。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded") },
      "/api/camera/health": {
        payload: {
          ...safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed"),
          source_diagnosis: {
            status: "uvc_no_frame_not_exclusive",
            not_exclusive: true,
            next_action: "check_usb_camera_input_power_or_known_good_uvc",
          },
        },
      },
      "/api/camera/devices": {
        delay_ms: 5200,
        payload: {
          ...safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded"),
          source_candidates: {
            candidates: [
              { path: "/dev/video1", is_video_capture: true, is_uvc_or_usb: true, role: "video_capture" },
            ],
          },
        },
      },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded") },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const cameraDevices = summary.read_endpoints.find((item) => item.id === "camera_devices");

      expect(cameraDevices).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_2400ms"],
      }));
      expect(summary.readback_summary.camera.devices_status).toBe("fetch_failed");
      expect(summary.robot_api_connection.status).toBe("degraded");
      expect(summary.robot_api_connection.blocked_reasons).toContain("camera_devices:fetch_timeout_2400ms");
      expect(summary.robot_api_connection.blocked_reasons).not.toContain("camera_devices:fetch_timeout_4000ms");
      expect(summary.robot_api_connection.blocked_reasons).not.toContain("camera_devices:fetch_timeout_8000ms");
    } finally {
      await robotApi.close();
    }
  }, 10000);

  it("Robot Control summary separates free-roam stop request from lidar mapping readiness", async () => {
    // live 形状：上次 stop 会把 runtime 留在 stopping；PC 仍要说明 start 可在确认后清 stop，不能误说雷达挡住移动。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            snapshot: {
              external_stop_requested: true,
              lidar_age_s: 45136.66,
              lidar_min_distance_m: 0.04,
              mapping_active: false,
              operator_confirmed: false,
              stop_available: true,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                {
                  id: "operator_confirmed",
                  label: "现场安全确认",
                  state: "blocked",
                  evidence: "还未勾选现场安全确认",
                  next_action: "勾选人在旁边、周围安全、停止手段就绪",
                },
                {
                  id: "stop_available",
                  label: "停止兜底",
                  state: "ready",
                  evidence: "停止按钮或上车停止服务可用",
                  next_action: "继续保持现场可接管",
                },
                {
                  id: "lidar_fresh",
                  label: "雷达新鲜",
                  state: "not_proven",
                  evidence: "雷达距离已过期，按无雷达低速自由移动",
                  next_action: "刷新雷达状态；刷新前仅允许现场监看的低速自由移动",
                },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "stopped") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "stale") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded") },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("start_ready");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).toContain("停止请求会在开始自由移动时自动解除，不作为启动阻塞");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).toContain("可先自由移动");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action.match(/勾选现场安全确认/g)?.length).toBe(1);
      expect(summary.safe_command_boundary.free_roam_mapping_missing_reasons).toContain("lidar_fresh");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "external_stop_request",
          scope: "runtime_diagnostic",
          state: "not_proven",
          evidence: "上车自由移动状态机仍处于停止请求",
        }),
        expect.objectContaining({
          id: "lidar_fresh",
          scope: "mapping_acceptance",
          state: "not_proven",
          evidence: "雷达距离已过期，按无雷达低速自由移动",
        }),
        expect.objectContaining({
          id: "mapping_active",
          scope: "mapping_acceptance",
          state: "not_proven",
          next_action: "先启动扫地式建图记录；这不影响现场监看的低速自由移动",
        }),
      ]));
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary tells the operator to rerun ROS Nav2 when PWM success lacks wheel raw L/R", async () => {
    // live 形状：旧 pwm NavigateToPose succeeded，但 wheel raw L/R 同窗口仍是 0/0；PC 要明确下次用 ROS 重跑。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              base_command_mode: "pwm",
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "nav2_path_ready",
          planner_server_active: true,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 35 },
          ],
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "path_ready_with_service_blockers",
          proof_state: "path_ready_with_service_blockers",
          path_generated: true,
          path_point_count: 36,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          planner_server_active: true,
          controller_server_active: false,
          controller_server_requested: false,
          blocked_reasons: ["nav2_lifecycle_not_running"],
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localize_proof_latest",
          status: "loaded",
          amcl_pose: { frame_id: "map", x: 0.01, y: 0.02, yaw: 0 },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            evidence_ref: "o11-nav2-goal-execution-live-pwm-zero-lr",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            publishes_cmd_vel: "nav2_controller_may_publish_cmd_vel_when_goal_is_active",
            base_command_mode: "pwm",
            managed_runtime: {
              requested: true,
              started: true,
              lifecycle_ready: { ok: true },
              cleanup: { ok: true },
            },
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
            base_command_summary: {
              nonzero_command_observed: true,
              nonzero_command_count: 49,
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.readback_summary.nav2.status).toBe("goal_succeeded_wheel_feedback_not_proven");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_left_speed).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_right_speed).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_raw_left).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_base_feedback_latest_raw_right).toBe("0");
      expect(summary.readback_summary.nav2.goal_execution_wheel_raw_lr_status_plain).toBe("上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到 49 次非零底盘命令。");
      expect(summary.readback_summary.nav2.goal_execution_wheel_raw_lr_next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线；执行时会自动启动自动驾驶 runtime，并在同窗口确认轮速 L/R 非零。");
      expect(summary.readback_summary.nav2.goal_execution_readback_publishes_cmd_vel).toBe("nav2_controller_may_publish_cmd_vel_when_goal_is_active");
      expect(summary.readback_summary.nav2.goal_execution_managed_runtime_requested).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_managed_runtime_started).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_managed_runtime_lifecycle_ready_ok).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_managed_runtime_cleanup_ok).toBe("true");
      expect(summary.readback_summary.nav2.execution_status_plain).toContain("执行窗口轮速 L/R=0/0 未非零");
      expect(summary.readback_summary.nav2.next_action_plain).toContain("用 ROS 模式重跑图上路线");
      expect(summary.readback_summary.nav2.plain_hint).toContain("执行窗口轮速 L/R=0/0 未非零");
      expect(summary.readback_summary.nav2.plain_hint).toContain("下一步：勾选行程前安全确认后用 ROS 模式重跑图上路线");
      expect(summary.readback_summary.nav2.plain_hint).not.toContain("wheel raw");
      expect(summary.readback_summary.nav2.route_execution_readiness_plain).toBe("图上路线可重跑复验；上次路线结果成功，但同窗口轮速 L/R=0/0 未非零。");
      expect(summary.readback_summary.nav2.route_execution_precheck_plain).toBe("只需勾选行程前安全确认；相机、雷达和现场报告不作为额外发车前置；执行会用 ROS 模式跑图上路线；执行时会自动启动自动驾驶 runtime。");
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("goal_succeeded_but_wheel_lr_zero");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.safe_command_boundary.nav2_goal_precheck_plain).toBe("执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。");
      expect(summary.safe_command_boundary.navigation_preflight_plain).toBe("执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。");
      expect(summary.safe_command_boundary.nav2_goal_execution_mode_label).toBe("上次 pwm，下次 ros");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到执行运动材料，主因不是雷达、相机或 controller；勾选行程前安全确认后用 ROS 重跑图上路线；执行时会自动启动自动驾驶 runtime，并复验 wheel raw L/R");
      expect(summary.safe_command_boundary.nav2_goal_next_action_plain).toBe("上次路线结果成功但执行窗口轮速 L/R=0/0 未非零；已看到执行运动材料，主因不是雷达、相机或控制服务；勾选行程前安全确认后用 ROS 模式重跑图上路线；执行时会自动启动自动驾驶 runtime，并复验执行窗口轮速 L/R");
      expect(summary.readback_summary.nav2.goal_execution_mode_rerun_status).toBe("pending_ros_rerun_after_pwm");
      expect(summary.action_status_cards?.find((card) => card.id === "nav2_route")).toMatchObject({
        status: "ready_needs_wheel_rerun",
        evidence: {
          route_ready_on_map: true,
          minimal_precheck_safety_only: true,
          fixed_execute_proxy_endpoint: "/api/robot-control/nav2/goal/execute",
          execute_sends_motion_when_ready: true,
          requires_same_window_wheel_lr_nonzero: true,
          wheel_feedback_status: "goal_succeeded_but_wheel_lr_zero",
          last_base_command_mode: "pwm",
          next_base_command_mode: "ros",
          nav2_stack_running: false,
          nav2_stack_lifecycle_state: "stopped",
          planner_server_active: true,
          controller_server_active: false,
          controller_server_requested: false,
          path_generated: true,
          nav2_path_point_count: 36,
          current_blocker_reasons: ["nav2_lifecycle_not_running"],
          current_blocker_labels: ["自动驾驶 lifecycle 未运行"],
          managed_runtime_autostart: true,
          managed_runtime_requested: true,
          managed_runtime_started: true,
          managed_runtime_lifecycle_ready_ok: true,
          managed_runtime_cleanup_ok: true,
          blockers: [],
        },
      });
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary consumes nested nav2 status proof when direct proof latest has no route", async () => {
    // live 上位机会把当前可用路线放进 /api/nav2/status.proof_latest；PC 不能因此误报图上路线 0 点。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          base: {
            control_policy: {
              base_command_mode: "pwm",
              nav2_base_command_mode: "ros",
            },
          },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "not_loaded",
          path_generated: false,
          path_generation_succeeded: false,
          path_point_count: 0,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          lifecycle_running: true,
          lifecycle_state: "running",
          proof_latest: {
            latest_proof_status: "nav2_no_motion_path_generation_runtime_observed",
            latest_map_server_active: true,
            latest_amcl_active: true,
            latest_planner_active: true,
            latest_controller_active: true,
            latest_scan_consumed: true,
            latest_map_consumed: true,
            latest_path_generation_attempted: true,
            latest_path_generation_service_available: true,
            latest_path_generation_service_name: "/compute_path_to_pose",
            latest_path_generation_succeeded: true,
            latest_path_generated: true,
            latest_path_point_count: 18,
            path_preview_points: [
              { x: 0, y: 0, frame_id: "map", source_index: 0 },
              { x: 0.8, y: 0, frame_id: "map", source_index: 17 },
            ],
            path_preview_frame_id: "map",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          latest_result: {
            status: "goal_succeeded",
            result_status: "succeeded",
            hil_pass: false,
            evidence_ref: "o11-nav2-goal-execution-live-status-nested",
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "pwm",
            goal_request: { frame_id: "map", x: 0.8, y: 0 },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
            base_command_summary: {
              nonzero_command_observed: true,
              nonzero_command_count: 49,
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.o3_proof_summary.path_generated).toBe(true);
      expect(summary.o3_proof_summary.path_generation_succeeded).toBe(true);
      expect(summary.o3_proof_summary.path_point_count).toBe(18);
      expect(summary.o3_proof_summary.path_preview_point_count).toBe(2);
      expect(summary.readback_summary.nav2.path_generated).toBe("true");
      expect(summary.readback_summary.nav2.path_generation_succeeded).toBe("true");
      expect(summary.readback_summary.nav2.path_point_count).toBe("18");
      expect(summary.readback_summary.nav2.path_preview_point_count).toBe("2");
      expect(summary.readback_summary.nav2.map_consumed).toBe("true");
      expect(summary.readback_summary.nav2.path_generation_attempted).toBe("true");
      expect(summary.readback_summary.nav2.path_generation_service_available).toBe("true");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线已显示，等待安全确认");
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("goal_succeeded_but_wheel_lr_zero");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到执行运动材料，主因不是雷达、相机或 controller；勾选行程前安全确认后用 ROS 重跑图上路线，并复验 wheel raw L/R");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps generated no-motion Nav2 route executable after managed runtime cleanup", async () => {
    // no-motion proof 生成路线后会清理 managed runtime；goal/execute 会自启 runtime，PC 不应把 lifecycle stopped 当硬挡。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "not_proven",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 18,
          path_preview_point_count: 18,
          path_preview_frame_id: "map",
          amcl_pose_observed: true,
          amcl_pose: { frame_id: "map", source: "/amcl_pose", x: -0.0045, y: 0.0091, yaw: 0.0055 },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          lifecycle_running: false,
          lifecycle_state: "stopped",
          latest_planner_active: true,
          latest_controller_active: false,
          latest_controller_requested: false,
          proof_latest: {
            latest_proof_status: "nav2_no_motion_path_generation_runtime_observed",
            latest_path_generated: true,
            latest_path_generation_succeeded: true,
            latest_path_point_count: 18,
            latest_path_preview_point_count: 18,
            latest_path_preview_frame_id: "map",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.nav2_stack_running).toBe("false");
      expect(summary.readback_summary.nav2.controller_server_active).toBe("false");
      expect(summary.readback_summary.nav2.controller_server_requested).toBe("false");
      expect(summary.o3_proof_summary.path_generated).toBe(true);
      expect(summary.o3_proof_summary.path_point_count).toBe(18);
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线和小车位置已显示，等待安全确认");
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("awaiting_route_execution");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("勾选行程前安全确认后执行图上路线，并在同窗口复验 wheel raw L/R");
    } finally {
      await robotApi.close();
    }
  });

  it("keeps stale radar readback in free-roam mapping gaps even when runtime gate is old-ready", async () => {
    // 自由移动可以启动，但建图验收必须以同轮雷达 freshness 为准，不能被 runtime 旧 gate 覆盖。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "ready",
              reason: "等待启动",
              stop_required: false,
              gates: [
                { id: "operator_confirmed", label: "现场安全确认", state: "ready", evidence: "已勾选现场安全确认", next_action: "继续保持现场可接管" },
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "stop endpoint ready", next_action: "继续保持停止可用" },
                { id: "camera_first_frame", label: "画面首帧", state: "ready", evidence: "画面首帧已读到", next_action: "继续监看画面" },
                { id: "lidar_fresh", label: "雷达新鲜", state: "ready", evidence: "runtime 旧记录显示 fresh", next_action: "继续监看雷达" },
                { id: "obstacle_clear", label: "前方障碍", state: "ready", evidence: "最近障碍 0.04m", next_action: "原地换向避让，不继续直行" },
                { id: "mapping_active", label: "地图记录", state: "ready", evidence: "地图记录已启动", next_action: "继续记录地图" },
                { id: "fresh_map_preview", label: "地图画面", state: "ready", evidence: "地图画面已刷新", next_action: "继续监看地图" },
              ],
            },
          },
        },
      },
      "/api/camera/health": {
        payload: {
          ...safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready"),
          visible_content_proven: true,
        },
      },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "latest_proof_stale_while_lifecycle_running"),
          latest_scan_proof_fresh: false,
          lifecycle_running: true,
          lifecycle_state: "running",
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.free_roam.motion_start_ready).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_start_ready).toBe("true");
      expect(summary.readback_summary.free_roam.motion_ready).toBe("false");
      expect(summary.readback_summary.free_roam.free_move_start_status_plain).toBe("自由移动可启动；只需现场安全确认和停止兜底。");
      expect(summary.readback_summary.free_roam.motion_runtime_status_plain).toBe("当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。");
      expect(summary.readback_summary.free_roam.mapping_readiness_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_blocked_reasons).toBe("lidar_fresh");
      expect(summary.readback_summary.free_roam.mapping_acceptance_status_plain).toContain("不影响先低速自由移动");
      expect(summary.readback_summary.free_roam.mapping_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_missing).toBe("lidar_fresh");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "lidar_fresh",
          state: "not_proven",
          evidence: "雷达最新扫描未刷新",
          next_action: "先刷新雷达；刷新前只能按自由移动记录",
        }),
        expect.objectContaining({
          id: "obstacle_clear",
          state: "not_proven",
          evidence: "雷达未刷新，障碍距离不可用",
          next_action: "先刷新雷达；刷新前不把旧障碍距离贴到地图",
        }),
      ]));
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("uses fresh free-roam runtime scan for mapping lidar readiness when proof latest is stale", async () => {
    // live 形态：free-roam runtime 已从 /scan 读到 0.02s 新鲜距离，但 radar proof latest 还是旧 artifact。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            snapshot: {
              lidar_age_s: 0.02,
              lidar_min_distance_m: 5.44,
              mapping_active: false,
              stop_available: true,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                { id: "operator_confirmed", label: "现场安全确认", state: "blocked", evidence: "还未勾选现场安全确认", next_action: "勾选现场安全确认" },
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "停止按钮可用", next_action: "继续保持现场可接管" },
                { id: "camera_first_frame", label: "画面首帧", state: "not_proven", evidence: "未读到摄像头首帧", next_action: "修复共享预览" },
                { id: "lidar_fresh", label: "雷达新鲜", state: "ready", evidence: "雷达距离 5.44m，延迟 0.02s", next_action: "继续保持雷达运行" },
                { id: "obstacle_clear", label: "前方障碍", state: "ready", evidence: "最近障碍 5.44m", next_action: "继续直行" },
                { id: "mapping_active", label: "地图记录", state: "not_proven", evidence: "地图记录未启动", next_action: "先启动扫地式建图记录" },
                { id: "fresh_map_preview", label: "地图画面", state: "not_proven", evidence: "地图画面未刷新", next_action: "刷新地图画面" },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_not_probed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "latest_proof_incomplete_while_lifecycle_running"),
          latest_scan_proof_fresh: false,
          lifecycle_running: true,
          lifecycle_state: "running",
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "partially_observed"),
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.lidar.runtime_scan_status).toBe("fresh");
      expect(summary.readback_summary.lidar.runtime_lidar_min_distance_m).toBe("5.44");
      expect(summary.readback_summary.lidar.runtime_lidar_age_s).toBe("0.02");
      expect(summary.readback_summary.lidar.runtime_scan_source).toBe("free_roam_runtime_snapshot");
      expect(summary.readback_summary.free_roam.mapping_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_missing).toBe("camera_first_frame,mapping_active,fresh_map_preview");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "lidar_fresh",
          state: "ready",
          evidence: "free-roam runtime /scan 新鲜：距离 5.44m，延迟 0.02s",
          next_action: "proof latest 可能过期；建图按 runtime scan 继续监看，必要时再刷新雷达 proof",
        }),
        expect.objectContaining({
          id: "obstacle_clear",
          state: "ready",
          evidence: "最近障碍 5.44m",
        }),
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("does not call missing safety confirmation an external stop request", async () => {
    // live 形态会在未勾安全确认时给 stop_required=true；这只是安全锁，不是“当前有停止请求”。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            snapshot: {
              external_stop_requested: false,
              mapping_active: false,
              stop_available: true,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "locked",
              reason: "还未勾选现场安全确认",
              stop_required: true,
              gates: [
                { id: "operator_confirmed", label: "现场安全确认", state: "blocked", evidence: "还未勾选现场安全确认", next_action: "勾选现场安全确认" },
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "停止按钮可用", next_action: "继续保持现场可接管" },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "stopped") },
      "/api/radar/scan-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "stale") },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded") },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.free_roam.decision_state).toBe("locked");
      expect(summary.readback_summary.free_roam.decision_reason).toBe("还未勾选现场安全确认");
      expect(summary.readback_summary.free_roam.stop_required).toBe("true");
      expect(summary.readback_summary.free_roam.stop_request_pending).toBe("false");
      expect(summary.readback_summary.free_roam.free_roam_stop_request_pending).toBe("false");
      expect(summary.readback_summary.free_roam.start_will_clear_stop_request).toBe("false");
      expect(summary.readback_summary.free_roam.motion_start_blocked_by_stop_request).toBe("false");
      expect(summary.readback_summary.free_roam.stop_request_status_plain).toBe("当前没有外部停止请求；自由移动启动不需要先清除停止请求。");
      expect(summary.readback_summary.free_roam.motion_readiness_plain).toBe("可先自由移动；只需要现场安全确认和停止兜底。");
      expect(summary.readback_summary.free_roam.free_move_start_status_plain).toBe("自由移动可启动；只需现场安全确认和停止兜底。");
      expect(summary.readback_summary.free_roam.motion_next_action_plain).toBe("勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。");
      expect(summary.readback_summary.free_roam.plain_hint).not.toContain("停止请求");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).not.toContain("停止请求");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).not.toEqual(expect.arrayContaining([
        expect.objectContaining({ id: "external_stop_request" }),
      ]));
    } finally {
      await robotApi.close();
    }
  });

  it("does not treat stale runtime scan as mapping-start lidar readiness when radar lifecycle is stopped", async () => {
    // live 形态：runtime snapshot 仍带着旧 fresh 距离，但 /api/radar/status 已明确雷达 lifecycle 停止。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            snapshot: {
              lidar_age_s: 0.03,
              lidar_min_distance_m: 2.12,
              mapping_active: true,
              stop_available: true,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                { id: "operator_confirmed", label: "现场安全确认", state: "blocked", evidence: "还未勾选现场安全确认", next_action: "勾选现场安全确认" },
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "停止按钮可用", next_action: "继续保持现场可接管" },
                { id: "camera_first_frame", label: "画面首帧", state: "ready", evidence: "画面首帧已读到", next_action: "继续监看画面" },
                { id: "lidar_fresh", label: "雷达新鲜", state: "ready", evidence: "旧 runtime 距离 2.12m，延迟 0.03s", next_action: "继续保持雷达运行" },
                { id: "mapping_active", label: "地图记录", state: "ready", evidence: "地图记录已启动", next_action: "继续记录地图" },
                { id: "fresh_map_preview", label: "地图画面", state: "ready", evidence: "地图画面已刷新", next_action: "继续监看地图" },
              ],
            },
          },
        },
      },
      "/api/camera/health": {
        payload: {
          ...safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready"),
          source_readiness: "first_frame_observed",
          visible_content_proven: true,
        },
      },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_not_running"),
          latest_scan_proof_fresh: false,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          continuous_scan_status: "lifecycle_not_running",
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.lidar.lifecycle_running).toBe("false");
      expect(summary.readback_summary.lidar.runtime_scan_status).toBe("fresh");
      expect(summary.readback_summary.free_roam.mapping_start_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_start_missing).toBe("lidar_fresh");
      expect(summary.readback_summary.free_roam.mapping_start_readiness_plain).toBe("建图启动未就绪；还差：雷达新鲜；地图记录和地图画面只影响建图验收。");
      expect(summary.safe_command_boundary.free_roam_mapping_start_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toEqual(["lidar_fresh"]);
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "lidar_fresh",
          state: "not_proven",
          evidence: "雷达未运行，旧 runtime scan 不能作为建图新鲜扫描",
          next_action: "先启动雷达并等待新扫描，再刷新地图画面确认雷达点",
        }),
      ]));
      expect(summary.action_status_cards?.find((card) => card.id === "mapping_start")).toMatchObject({
        status: "not_ready",
        status_label: "未就绪",
        sends_motion_when_clicked: false,
        blocks_mapping_start: true,
        evidence: {
          mapping_start_ready: false,
          mapping_start_missing_reasons: ["lidar_fresh"],
          mapping_camera_first_frame_ready: true,
          mapping_lidar_fresh_ready: false,
          mapping_lidar_lifecycle_running: false,
          mapping_lidar_lifecycle_state: "stopped",
          mapping_runtime_scan_fresh: true,
          mapping_runtime_scan_diagnostic_only: true,
          mapping_lidar_fresh_blocked_by_lifecycle: true,
          mapping_lidar_next_action_plain: "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。",
        },
      });
      expect(summary.action_status_cards?.find((card) => card.id === "free_move")).toMatchObject({
        status: "start_ready",
        evidence: {
          free_move_start_ready: true,
          radar_blocks_free_motion: false,
        },
      });
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("keeps explicit free-roam mapping gate when map proof looks started", async () => {
    // free-roam runtime 是自助移动状态机的当前事实；它明确说地图记录未启动时，旧 map proof 不能把 gate 改成 就绪。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.status", "ready"),
          managed_runtime_started: true,
        },
      },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
        },
      },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                {
                  id: "mapping_active",
                  label: "地图记录",
                  state: "blocked",
                  evidence: "地图记录未启动",
                  next_action: "先启动扫地式建图记录",
                },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const mappingGate = summary.safe_command_boundary.free_roam_autonomy_gates.find((gate) => gate.id === "mapping_active");

      expect(summary.o3_proof_summary.managed_runtime_started).toBe(true);
      expect(mappingGate).toEqual(expect.objectContaining({
        id: "mapping_active",
        state: "blocked",
        evidence: "地图记录未启动",
        next_action: "先启动扫地式建图记录；这不影响现场监看的低速自由移动",
      }));
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("adds a compatibility free-roam mapping gate when old runtime omits it", async () => {
    // 旧上位机可能没有 mapping_active gate；只有这种情况下才允许 PC 用 map runtime proof 补一行兼容提示。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.status", "ready"),
          managed_runtime_started: true,
        },
      },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
        },
      },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                {
                  id: "operator_confirmed",
                  label: "现场安全确认",
                  state: "blocked",
                  evidence: "还未勾选现场安全确认",
                  next_action: "勾选现场安全确认",
                },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const mappingGate = summary.safe_command_boundary.free_roam_autonomy_gates.find((gate) => gate.id === "mapping_active");

      expect(mappingGate).toEqual(expect.objectContaining({
        id: "mapping_active",
        state: "ready",
        evidence: "当前读回已证明地图记录 runtime 已启动",
        next_action: "继续保持地图记录并监看画面",
      }));
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("keeps free-roam start ready from stop fallback even when lidar freshness is blocked", async () => {
    // 基础自助移动入口不能被雷达新鲜度硬挡；雷达仍作为避障/HIL 风险显示，不升级完整自动扫图就绪。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "ready",
              reason: "停止兜底已就绪，雷达仅作监看",
              stop_required: false,
              gates: [
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "停止入口可用", next_action: "可以低速自助移动" },
                { id: "lidar_fresh", label: "雷达监看", state: "blocked", evidence: "雷达 proof 过期", next_action: "刷新雷达后提升避障证据" },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.free_roam_autonomy_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_motion_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_start_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toEqual([
        "camera_first_frame",
        "lidar_fresh",
      ]);
      expect(summary.safe_command_boundary.free_roam_mapping_ready).toBe(false);
      expect(summary.safe_command_boundary.free_roam_mapping_missing_reasons).toEqual([
        "camera_first_frame",
        "lidar_fresh",
        "mapping_active",
        "fresh_map_preview",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("start_ready");
      expect(summary.safe_command_boundary.free_roam_autonomy_label).toBe("自由移动（勾确认后可启动）");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).toBe("勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面");
      expect(summary.safe_command_boundary.free_roam_mapping_start_plain).toBe("建图启动未就绪；还差：画面首帧、雷达新鲜；地图记录和地图画面只影响建图验收。");
      expect(summary.safe_command_boundary.free_roam_mapping_start_next_action).toBe("先补齐建图启动材料：画面首帧、雷达新鲜；低速自由移动不受影响。");
      expect(summary.readback_summary.free_roam.status).toBe("start_ready");
      expect(summary.current_fact_plain).toContain("建图启动：未就绪；还差：画面首帧、雷达新鲜；地图记录和地图画面只影响建图验收");
      expect(summary.current_fact_plain).toContain("建图验收：未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动");
      expect(summary.current_fact_plain).not.toContain("建图启动：建图启动");
      expect(summary.current_fact_plain).not.toContain("建图验收：建图验收");
      expect(summary.readback_summary.free_roam.next_action_plain).toBe(summary.safe_command_boundary.free_roam_autonomy_next_action);
      expect(summary.readback_summary.free_roam.plain_hint).toBe("可先自由移动；只需要现场安全确认和停止兜底。建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。下一步：勾选现场安全确认后可先自由移动。");
      expect(summary.readback_summary.free_roam.motion_readiness_plain).toBe("可先自由移动；只需要现场安全确认和停止兜底。");
      expect(summary.readback_summary.free_roam.motion_sensor_dependency_status).toBe("not_required_for_motion");
      expect(summary.readback_summary.free_roam.motion_sensor_dependency_plain).toBe("自由移动启动只看现场安全确认和停止兜底；相机、雷达和地图记录只影响建图验收。");
      expect(summary.readback_summary.free_roam.free_move_without_camera_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.motion_without_radar_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_minimal_precheck_safety_only).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_safety_confirm_required).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_camera_preflight_required).toBe("false");
      expect(summary.readback_summary.free_roam.free_move_radar_preflight_required).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_start_requires_camera_first_frame).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_requires_lidar_fresh).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_readiness_plain).toBe("建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。");
      expect(summary.readback_summary.free_roam.motion_next_action_plain).toBe("勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。");
      expect(summary.readback_summary.free_roam.mapping_next_action_plain).toBe("建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates.map((gate) => gate.id)).toEqual([
        "stop_available",
        "motion_hil_unlock",
        "camera_first_frame",
        "lidar_fresh",
        "mapping_active",
        "fresh_map_preview",
      ]);
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "camera_first_frame",
          scope: "mapping_acceptance",
          state: "not_proven",
          evidence: "未读到摄像头首帧证据",
        }),
        expect.objectContaining({ id: "lidar_fresh", state: "blocked" }),
        expect.objectContaining({
          id: "mapping_active",
          scope: "mapping_acceptance",
          state: "not_proven",
        }),
        expect.objectContaining({
          id: "fresh_map_preview",
          scope: "mapping_acceptance",
          state: "not_proven",
          evidence: "地图画面未刷新",
        }),
        expect.objectContaining({
          id: "motion_hil_unlock",
          state: "not_proven",
          evidence: "当前尚未启动自由移动，点击开始后由上车端打开运动双锁",
          next_action: "勾选现场安全确认后点击开始自由移动（低速）",
        }),
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("hides stale obstacle distance when free-roam lidar freshness is expired", async () => {
    // 雷达过期时，旧的最近障碍距离只能作为“需要刷新”的风险，不能继续喂给地图 marker 当实时预览。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "ready",
              reason: "停止兜底已就绪，雷达过期后按无雷达低速自由移动",
              stop_required: false,
              gates: [
                { id: "stop_available", label: "停止兜底", state: "ready", evidence: "停止入口可用", next_action: "可以低速自助移动" },
                { id: "lidar_fresh", label: "雷达监看", state: "not_proven", evidence: "雷达距离已过期，按无雷达低速自由移动", next_action: "刷新雷达状态" },
                { id: "obstacle_clear", label: "前方障碍", state: "not_proven", evidence: "最近障碍 0.04m", next_action: "原地换向避让，不继续直行" },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "stopped") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const obstacleGate = summary.safe_command_boundary.free_roam_autonomy_gates.find((gate) => gate.id === "obstacle_clear");

      expect(summary.safe_command_boundary.free_roam_autonomy_start_ready).toBe(true);
      expect(obstacleGate).toEqual(expect.objectContaining({
        state: "not_proven",
        evidence: "雷达未刷新，障碍距离不可用",
        next_action: "先刷新雷达；刷新前不把旧障碍距离贴到地图",
      }));
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({ id: "lidar_fresh", state: "not_proven" }),
        expect.objectContaining({ id: "stop_available", state: "ready" }),
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("marks free-roam autonomy ready only from an unlocked runtime artifact while keeping PC control flags false", async () => {
    // ready 只说明上车端自由移动状态机已打开运动发布；PC summary 仍不能把自己标成 safe_to_control。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const readyGate = (id: string, label: string) => ({
      id,
      label,
      state: "ready",
      evidence: `${label}已满足`,
      next_action: "继续监看并保持停止兜底",
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: false,
            cmd_vel_publish_enabled: true,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "running",
              reason: "门禁满足，低速直行",
              stop_required: false,
              gates: [
                readyGate("operator_confirmed", "现场安全确认"),
                readyGate("mapping_active", "地图记录"),
                readyGate("camera_first_frame", "画面首帧"),
                readyGate("lidar_fresh", "雷达新鲜"),
                readyGate("fresh_map_preview", "地图新画面"),
                readyGate("obstacle_clear", "前方障碍"),
                readyGate("coverage_target", "覆盖目标"),
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "ready") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("ready");
      expect(summary.safe_command_boundary.free_roam_autonomy_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_motion_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toEqual([]);
      expect(summary.safe_command_boundary.free_roam_mapping_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_missing_reasons).toEqual([]);
      expect(summary.safe_command_boundary.free_roam_autonomy_label).toBe("自动扫图");
      expect(summary.safe_command_boundary.free_roam_autonomy_next_action).toBe("已进入自动扫图条件；继续低速监看地图、雷达和画面");
      expect(summary.safe_command_boundary.free_roam_mapping_start_plain).toBe("建图启动已就绪：画面首帧和雷达新鲜都可用；地图记录和地图画面用于建图验收。");
      expect(summary.safe_command_boundary.free_roam_mapping_start_next_action).toBe("相机和雷达已满足建图启动；勾选现场安全确认后可启动建图记录，再看地图画面完成验收。");
      expect(summary.readback_summary.free_roam.status).toBe("mapping_ready");
      expect(summary.readback_summary.free_roam.next_action_plain).toBe(summary.safe_command_boundary.free_roam_autonomy_next_action);
      expect(summary.readback_summary.free_roam.plain_hint).toBe("自由移动正在运行；相机和雷达不作为继续移动的前置。建图验收已就绪：画面、雷达、地图记录和地图画面都可用。下一步：已进入自动扫图条件；继续低速监看地图、雷达和画面。");
      expect(summary.readback_summary.free_roam.motion_readiness_plain).toBe("自由移动正在运行；相机和雷达不作为继续移动的前置。");
      expect(summary.readback_summary.free_roam.free_move_without_camera_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.motion_without_radar_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_requires_camera_first_frame).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_requires_lidar_fresh).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_readiness_plain).toBe("建图验收已就绪：画面、雷达、地图记录和地图画面都可用。");
      expect(summary.readback_summary.free_roam.motion_next_action_plain).toBe("自由移动运行中；需要收口时点击停止自由移动或红色停止。");
      expect(summary.readback_summary.free_roam.mapping_next_action_plain).toBe("建图验收已就绪；继续低速监看地图、雷达和画面。");
      expect(summary.action_status_cards?.find((card) => card.id === "mapping_start")).toMatchObject({
        status_label: "可启动",
        requires_safety_confirmation: true,
        can_start_after_safety_confirm: true,
        sends_motion_when_clicked: true,
        blocks_mapping_start: false,
      });
      expect(summary.safe_command_boundary.free_roam_autonomy_runtime).toEqual(expect.objectContaining({
        status: "loaded",
        state: "running",
        artifact_only: false,
        cmd_vel_publish_enabled: true,
      }));
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: "motion_hil_unlock",
          state: "ready",
          evidence: "自由移动状态机已打开运动发布",
        }),
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.command_dispatch_enabled).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("labels unlocked free-roam runtime as free movement until mapping acceptance gates are complete", async () => {
    // 车已经由上车端解锁低速运动时，缺摄像头首帧/地图新画面仍不能把本轮说成可验收自动扫图。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const readyGate = (id: string, label: string) => ({
      id,
      label,
      state: "ready",
      evidence: `${label}已满足`,
      next_action: "继续监看并保持停止兜底",
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "ready") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: false,
            cmd_vel_publish_enabled: true,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "running",
              reason: "停止兜底满足，按无画面自由移动",
              stop_required: false,
              gates: [
                readyGate("operator_confirmed", "现场安全确认"),
                readyGate("stop_available", "停止兜底"),
                readyGate("mapping_active", "地图记录"),
                readyGate("lidar_fresh", "雷达新鲜"),
                { id: "camera_first_frame", label: "画面首帧", state: "not_proven", evidence: "摄像头未出首帧", next_action: "先修复共享预览；自由移动可继续监看" },
                { id: "fresh_map_preview", label: "地图新画面", state: "not_proven", evidence: "地图画面未刷新", next_action: "刷新地图画面后再按建图验收" },
              ],
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "lifecycle_running") },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_scan_proof_latest", "scan_observed"),
          latest_scan_proof_fresh: true,
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.safe_command_boundary.free_roam_autonomy).toBe("ready");
      expect(summary.safe_command_boundary.free_roam_autonomy_label).toBe("自由移动（运行中）");
      expect(summary.readback_summary.free_roam.status).toBe("motion_ready");
      expect(summary.readback_summary.free_roam.motion_ready).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_start_missing).toBe("camera_first_frame");
      expect(summary.readback_summary.free_roam.mapping_ready).toBe("false");
      expect(summary.readback_summary.free_roam.mapping_missing).toBe("camera_first_frame,fresh_map_preview");
      expect(summary.readback_summary.free_roam.plain_hint).toBe("自由移动正在运行；相机和雷达不作为继续移动的前置。建图验收未就绪；还差：画面首帧、地图画面；不影响先低速自由移动。");
      expect(summary.readback_summary.free_roam.motion_readiness_plain).toBe("自由移动正在运行；相机和雷达不作为继续移动的前置。");
      expect(summary.readback_summary.free_roam.free_move_without_camera_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.motion_without_radar_allowed).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_requires_camera_first_frame).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_start_requires_lidar_fresh).toBe("true");
      expect(summary.readback_summary.free_roam.mapping_readiness_plain).toBe("建图验收未就绪；还差：画面首帧、地图画面；不影响先低速自由移动。");
      expect(summary.readback_summary.free_roam.motion_next_action_plain).toBe("自由移动运行中；需要收口时点击停止自由移动或红色停止。");
      expect(summary.readback_summary.free_roam.mapping_next_action_plain).toBe("建图验收还差：画面首帧、地图画面；不影响先低速自由移动。");
      expect(summary.safe_command_boundary.free_roam_autonomy_gates).toEqual(expect.arrayContaining([
        expect.objectContaining({ id: "motion_hil_unlock", state: "ready" }),
        expect.objectContaining({ id: "camera_first_frame", state: "not_proven" }),
        expect.objectContaining({ id: "fresh_map_preview", state: "not_proven" }),
      ]));
      expect(summary.safe_to_control).toBe(false);
      expect(summary.safe_command_boundary.command_dispatch_enabled).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("operator report proxy posts only whitelisted material fields to fixed endpoint", async () => {
    // 现场材料提交只能命中 /api/operator/report；delivery_success 只允许作为 structured claim 保留。
    const upstream = await listenRobotProofRefreshApi({
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "operator_report_saved",
          evidence_ref: "field-hil-submit-0620",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          structured_hil_claims: {
            delivery_success: true,
          },
        },
      },
    });
    try {
      const response = await buildOperatorReportProxy(upstream.baseUrl, {
        operator_present: true,
        evidence_ref: "field-hil-submit-0620",
        physical_clearance_confirmed: true,
        emergency_stop_ready: true,
        observed_motion: false,
        observed_stop: true,
        reported_at: "2026-06-11T06:20:00.000Z",
        operator_notes: "no-motion material submit from PC",
        structured_hil_claims: {
          external_video_recorded: true,
          external_video_ref: "phone-video-0620.mp4",
          visible_content_proven: true,
          camera_artifacts_ref: "runtime/camera/latest_metrics.json",
          wheel_feedback_lr_nonzero_proven: false,
          wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
          physical_motion_lidar_delta_proven: false,
          scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
          real_route_map_proven: true,
          route_map_ref: "runtime/routes/field-route.csv",
          delivery_success: true,
          site_state: "field_operator_claim_ready_for_review",
        },
      });

      expect(response.proxy_status).toBe("report_forwarded");
      expect(response.remote_endpoint).toBe("/api/operator/report");
      expect(response.remote_http_status).toBe(200);
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(response.structured_hil_claims.delivery_success).toBe(true);
      expect(response.hard_dangerous_true_fields).toEqual([]);
      expect(upstream.receivedBodies["/api/operator/report"]).toEqual([
        {
          operator_present: true,
          evidence_ref: "field-hil-submit-0620",
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          observed_motion: false,
          observed_stop: true,
          reported_at: "2026-06-11T06:20:00.000Z",
          operator_notes: "no-motion material submit from PC",
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-0620.mp4",
            visible_content_proven: true,
            camera_artifacts_ref: "runtime/camera/latest_metrics.json",
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
            physical_motion_lidar_delta_proven: false,
            scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
            real_route_map_proven: true,
            route_map_ref: "runtime/routes/field-route.csv",
            delivery_success: true,
            site_state: "field_operator_claim_ready_for_review",
          },
        },
      ]);
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/radar/start"]).toBeUndefined();
    } finally {
      await upstream.close();
    }
  });

  it("operator report proxy rejects unknown or dangerous request fields before upstream POST", async () => {
    // 未知字段直接 fail-closed，防止 report 代理被扩展成任意控制字段透传。
    const upstream = await listenRobotProofRefreshApi({
      "/api/operator/report": {
        payload: { schema: "trashbot.upper_robot_api.v1.operator_report", status: "saved" },
      },
    });
    try {
      const topLevelRejected = await buildOperatorReportProxy(upstream.baseUrl, {
        evidence_ref: "field-hil-submit-unknown",
        safe_to_control: true,
      });
      expect(topLevelRejected.proxy_status).toBe("report_rejected");
      expect(topLevelRejected.failure_reason).toContain("request_body_unknown_fields");
      expect(topLevelRejected.rejected_fields).toContain("safe_to_control");
      expect(topLevelRejected.safe_to_control).toBe(false);

      const nestedRejected = await buildOperatorReportProxy(upstream.baseUrl, {
        evidence_ref: "field-hil-submit-nested-unknown",
        structured_hil_claims: {
          delivery_success: true,
          endpoint: "/api/base/manual",
        },
      });
      expect(nestedRejected.proxy_status).toBe("report_rejected");
      expect(nestedRejected.rejected_fields).toContain("structured_hil_claims.endpoint");
      expect(nestedRejected.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/operator/report"]).toBeUndefined();
    } finally {
      await upstream.close();
    }
  });

  it("Robot Control summary preserves radar raw-packet parsed status", async () => {
    // 真实 scan-proof latest 可能顶层 status=loaded，但 key_values.latest_proof_status=raw_packets_parsed；summary 不能把它盖掉。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      evidence_ref: "raw-packet-summary-fixture",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "source_first_frame_failed") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "not_proven") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "partially_observed"),
          lifecycle_running: true,
          lifecycle_state: "running",
          continuous_scan_status: "latest_proof_incomplete_while_lifecycle_running",
          continuous_window_observed: false,
          continuity_window_status: "latest_proof_incomplete_while_lifecycle_running",
          latest_scan_proof_fresh: false,
          driver_diagnostics_status: "serial_open_but_no_bytes",
          driver_diagnostics_next_action_plain: "LiDAR 串口已打开且启动命令已写入，但没有读到任何字节；检查雷达供电、线序、波特率或设备节点。",
          driver_diagnostics_latest: {
            diagnosis_status: "serial_open_but_no_bytes",
            next_action_plain: "LiDAR 串口已打开且启动命令已写入，但没有读到任何字节；检查雷达供电、线序、波特率或设备节点。",
            serial: {
              bytes_read_total: 0,
              packet_count_total: 0,
              empty_read_count: 125,
            },
            runtime: {
              published_scan_count: 0,
            },
          },
          blocked_reasons: [
            "latest_scan_proof_required_observations_missing:scan_once,scan_hz,raw_packet_once,all_required_observations",
          ],
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
          latest_proof_status: "raw_packets_parsed",
          latest_scan_once_observed: false,
          continuous_scan_status: "latest_proof_incomplete_while_lifecycle_running",
          continuous_window_observed: false,
          lifecycle_running: true,
          lifecycle_state: "running",
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/raw-packet-proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result", "loaded") },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.lidar.latest_scan_proof_status).toBe("loaded");
      expect(summary.readback_summary.lidar.latest_scan_proof_result_status).toBe("raw_packets_parsed");
      expect(summary.readback_summary.lidar.raw_packet_once_observed).toBe("true");
      expect(summary.readback_summary.lidar.radar_scan_observation_status).toBe("missing_required_observations");
      expect(summary.readback_summary.lidar.radar_scan_observation_missing_reasons).toBe("scan_once,scan_hz,raw_packet_once");
      expect(summary.readback_summary.lidar.driver_diagnostics_status).toBe("serial_open_but_no_bytes");
      expect(summary.readback_summary.lidar.driver_serial_bytes_read_total).toBe("0");
      expect(summary.readback_summary.lidar.driver_serial_packet_count_total).toBe("0");
      expect(summary.readback_summary.lidar.driver_serial_empty_read_count).toBe("125");
      expect(summary.readback_summary.lidar.driver_published_scan_count).toBe("0");
      expect(summary.readback_summary.radar.driver_diagnostics_status).toBe("serial_open_but_no_bytes");
      expect(summary.readback_summary.radar.driver_diagnostics_next_action_plain).toContain("没有读到任何字节");
      expect(summary.readback_summary.radar.radar_scan_observation_missing_reasons).toBe("scan_once,scan_hz,raw_packet_once");
      expect(summary.readback_summary.radar.radar_status_plain).toContain("扫描材料不完整：没有读到一帧雷达、雷达频率未确认、雷达原始包未确认");
      expect(summary.readback_summary.radar.radar_status_plain).not.toContain("raw_packet_once");
      expect(summary.readback_summary.radar.radar_next_action_plain).toBe("先补齐雷达扫描材料：没有读到一帧雷达、雷达频率未确认、雷达原始包未确认；有新扫描后再刷新地图画面。");
      expect(summary.action_status_cards?.find((card) => card.id === "radar_map_points")?.next_action_plain).toBe("先补齐雷达扫描材料：没有读到一帧雷达、雷达频率未确认、雷达原始包未确认；有新扫描后再刷新地图画面");
      expect(summary.action_status_cards?.find((card) => card.id === "radar_map_points")?.evidence).toMatchObject({
        driver_diagnostics_status: "serial_open_but_no_bytes",
        driver_serial_bytes_read_total: "0",
        driver_serial_packet_count_total: "0",
        driver_serial_empty_read_count: "125",
        driver_published_scan_count: "0",
      });
      expect(summary.goal_checklist_summary?.radar_next_action_plain).toBe("先补齐雷达扫描材料：没有读到一帧雷达、雷达频率未确认、雷达原始包未确认；有新扫描后再刷新地图画面");
      expect(summary.readback_summary.lidar.scan_preview_point_count).toBe("0");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary surfaces running radar lifecycle when latest proof endpoints are missing", async () => {
    // 现场雷达启动成功后可能还没有最新 proof 文件；summary 必须显示“运行但无新 proof”，不能退回 missing。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      evidence_ref: "running-lidar-missing-proof-fixture",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "source_first_frame_failed") },
      "/api/map/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed") },
      "/api/localize/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed") },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "not_proven") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "missing"),
          lifecycle_running: true,
          lifecycle_state: "running",
          continuous_scan_status: "latest_proof_missing_while_lifecycle_running",
          continuous_window_observed: false,
          continuity_window_status: "latest_proof_missing_while_lifecycle_running",
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/scan-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.lidar.status).toBe("latest_proof_missing_while_lifecycle_running");
      expect(summary.readback_summary.lidar.latest_scan_proof_status).toBe("missing");
      expect(summary.readback_summary.lidar.latest_raw_packet_proof_status).toBe("missing");
      expect(summary.readback_summary.lidar.lifecycle_running).toBe("true");
      expect(summary.readback_summary.lidar.continuous_scan_status).toBe("latest_proof_missing_while_lifecycle_running");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps camera diagnosis while capping slow status readback", async () => {
    // status 聚合慢时 summary 先返回分项事实；相机 health 在短预算内仍解析完整诊断。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        delay_ms: 4200,
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "camera_ready_from_status",
          evidence_ref: "status-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          managed_runtime_started: true,
          scan_once_observed: true,
          map_once_observed: true,
          path_generated: true,
          path_point_count: 31,
        },
      },
      "/api/camera/health": {
        delay_ms: 1200,
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_health",
          status: "ready",
          evidence_ref: "camera-health-proof",
          video_source: "/dev/video1",
          video_source_mode: "auto",
          active_peer_count: 0,
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_timeout",
          source_usage: {
            checked: true,
            device: "/dev/video1",
            status: "in_use_by_probe",
            owner_count: 1,
            owners: [
              {
                pid: 1234,
                self: false,
                command: "camera_first_frame_probe.py --device /dev/video1",
              },
            ],
            opens_camera: false,
          },
          current_selection: {
            selected_path: "/dev/video1",
            selected_name: "USB Composite Device: DV20 USB",
            selected_is_uvc_or_usb: true,
            selected_formats_summary: "MJPG@640x480@30；YUYV@640x480@22",
            selected_role: "video_capture",
            selected_sibling_video_nodes_summary: "/dev/video2=metadata",
            selected_sibling_video_node_count: 1,
          },
          shared_preview_contract: "single_shared_capture_for_multiple_clients",
          media_diagnostics: {
            last_offer_error: {
              error: "first_frame_unreadable",
              failure_reason: "first_frame_timeout",
              first_frame_format_attempts: [
                { fourcc: "MJPG", label: "MJPG@640x480@30", status: "first_frame_unreadable", failure_reason: "capture_read_returned_false" },
                { fourcc: "YUYV", label: "YUYV@640x480@22", status: "first_frame_unreadable", failure_reason: "capture_read_returned_false" },
              ],
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/camera/devices": {
        delay_ms: 1200,
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_devices",
          status: "devices_ready",
          evidence_ref: "camera-devices-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/map/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_proof_latest",
          status: "not_loaded",
          evidence_ref: "map-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "localization_reset_observed",
          evidence_ref: "localize-proof",
          amcl_pose_observed: true,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          amcl_pose: { frame_id: "map", x: 0.25, y: 0.75, yaw: 1.57, source: "/amcl_pose" },
          base_link_to_laser_frame_transform: {
            parent_frame_id: "base_link",
            child_frame_id: "laser_frame",
            translation: { x: 0.1, y: 0 },
            rotation: { yaw: 0.05 },
            source: "tf2_echo base_link laser_frame",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "not_loaded",
          evidence_ref: "nav2-status-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "nav2_path_ready",
          evidence_ref: "nav2-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          path_generated: true,
          path_point_count: 31,
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.4, y: 0.1, frame_id: "map", source_index: 12 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 30 },
          ],
          path_preview_point_count: 3,
          path_preview_source_point_count: 31,
          path_preview_frame_id: "map",
        },
      },
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "latest_proof_fresh_while_lifecycle_running",
          continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
          continuous_window_observed: true,
          continuity_window_status: "fresh_window_observed",
          continuity_blocked_reasons: [],
          lifecycle_running: true,
          lifecycle_state: "running",
          latest_scan_proof_fresh: true,
          evidence_ref: "radar-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof_latest",
          status: "scan_once_observed",
          evidence_ref: "radar-scan-proof",
          ranges: [1, 2, null, "bad", 1.5],
          angle_min: 0,
          angle_increment: 1.57079632679,
          frame_id: "laser",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_raw_packet_proof_latest",
          status: "raw_packet_not_proven",
          evidence_ref: "radar-raw-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/base/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_status",
          status: "blocked_by_safety_boundary",
          evidence_ref: "base-status-proof",
          sends_commands: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/base/feedback-samples/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_feedback_samples",
          status: "blocked_by_safety_boundary",
          evidence_ref: "base-feedback-proof",
          latest_result: {
            sends_commands: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);
      const statusReadback = summary.read_endpoints.find((item) => item.id === "status");
      const cameraHealth = summary.read_endpoints.find((item) => item.id === "camera_health");
      const cameraDevices = summary.read_endpoints.find((item) => item.id === "camera_devices");

      expect(statusReadback?.request_status).toBe("fetch_failed");
      expect(statusReadback?.blocked_reasons).toEqual(["fetch_timeout_2400ms"]);
      expect(cameraHealth?.request_status).toBe("loaded");
      expect(cameraDevices?.request_status).toBe("loaded");
      expect(summary.robot_api_connection.failed_count).toBe(1);
      expect(summary.robot_api_connection.blocked_reasons).toContain("status:fetch_timeout_2400ms");
      expect(summary.robot_api_connection.blocked_count).toBeGreaterThanOrEqual(1);
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_status.sends_commands");
      expect(summary.robot_api_connection.dangerous_true_fields).not.toContain("base_feedback_samples_latest.latest_result.sends_commands");
      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.devices_status).toBe("devices_ready");
      expect(summary.readback_summary.camera.video_source).toBe("/dev/video1");
      expect(summary.readback_summary.camera.video_source_mode).toBe("auto");
      expect(summary.readback_summary.camera.selected_path).toBe("/dev/video1");
      expect(summary.readback_summary.camera.selected_name).toBe("USB Composite Device: DV20 USB");
      expect(summary.readback_summary.camera.selected_is_uvc_or_usb).toBe("true");
      expect(summary.readback_summary.camera.selected_formats_summary).toBe("MJPG@640x480@30；YUYV@640x480@22");
      expect(summary.readback_summary.camera.selected_role).toBe("video_capture");
      expect(summary.readback_summary.camera.selected_sibling_video_nodes_summary).toBe("/dev/video2=metadata");
      expect(summary.readback_summary.camera.selected_sibling_video_node_count).toBe("1");
      expect(summary.readback_summary.camera.shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
	      expect(summary.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summary.readback_summary.camera.source_failure_reason).toBe("first_frame_timeout");
      expect(summary.readback_summary.camera.source_usage_status).toBe("in_use_by_probe");
      expect(summary.readback_summary.camera.source_usage_owner_count).toBe("1");
      expect(summary.readback_summary.camera.source_usage_summary).toContain("pid=1234");
      expect(summary.readback_summary.camera.active_peer_count).toBe("0");
      expect(summary.readback_summary.camera.last_offer_error).toBe("first_frame_unreadable");
      expect(summary.readback_summary.camera.last_offer_failure_reason).toBe("first_frame_timeout");
      expect(summary.readback_summary.camera.last_offer_format_attempts_summary).toBe("MJPG@640x480@30 无首帧；YUYV@640x480@22 无首帧");
      expect(summary.readback_summary.lidar.status).toBe("latest_proof_fresh_while_lifecycle_running");
      expect(summary.readback_summary.lidar.continuous_scan_status).toBe("latest_proof_fresh_while_lifecycle_running");
      expect(summary.readback_summary.lidar.lifecycle_running).toBe("true");
      expect(summary.readback_summary.lidar.lifecycle_state).toBe("running");
      expect(summary.readback_summary.lidar.continuous_window_observed).toBe("true");
      expect(summary.readback_summary.lidar.continuity_window_status).toBe("fresh_window_observed");
      expect(summary.readback_summary.lidar.latest_scan_proof_fresh).toBe("true");
      expect(summary.readback_summary.lidar.latest_scan_proof_result_status).toBe("scan_once_observed");
      expect(summary.readback_summary.lidar.raw_packet_once_observed).toBe("not_loaded");
      expect(summary.readback_summary.lidar.scan_preview_point_count).toBe("3");
      expect(summary.readback_summary.lidar.scan_preview_source_point_count).toBe("5");
      expect(summary.readback_summary.lidar.scan_preview_frame_id).toBe("laser");
      expect(summary.readback_summary.map.radar_overlay_status).toBe("loaded");
      expect(summary.readback_summary.map.radar_overlay_plain_hint).toBe("雷达点已按当前扫描和小车地图位置贴到地图。");
	      expect(summary.readback_summary.map.radar_overlay_wysiwyg_status_plain).toBe("雷达点已贴到当前地图：当前显示 3 个点，frame=laser。");
	      expect(summary.readback_summary.map.radar_overlay_wysiwyg_next_action_plain).toBe("继续观察地图雷达层。");
	      expect(summary.readback_summary.map.radar_overlay_next_action).toBe("continue_monitoring_map_radar_overlay");
	      expect(summary.readback_summary.map.radar_overlay_next_action_plain).toBe("继续观察地图雷达层。");
	      expect(summary.action_status_cards?.find((card) => card.id === "radar_map_points")).toMatchObject({
	        status: "current_on_map",
	        status_label: "已贴图",
	        summary_plain: "雷达点已贴到当前地图：当前显示 3 个点，frame=laser",
	        next_action_plain: "继续观察地图雷达层",
	      });
	      expect(summary.goal_checklist?.find((item) => item.id === "radar_map_points_wysiwyg")).toMatchObject({
	        status: "done",
	        status_label: "已满足",
	        next_action_plain: "继续观察地图雷达层",
	        blocks_goal_completion: false,
	      });
	      expect(summary.readback_summary.map.radar_overlay_blocked_reasons).toBe("none");
      expect(summary.readback_summary.map.radar_overlay_blocked_reason_labels).toBe("none");
      expect(summary.readback_summary.map.radar_overlay_point_count).toBe("3");
      expect(summary.readback_summary.map.radar_overlay_source_point_count).toBe("5");
      expect(summary.readback_summary.map.radar_overlay_frame_id).toBe("laser");
      expect(summary.readback_summary.map.radar_overlay_source_frame_id).toBe("laser");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_point_count).toBe("3");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_source_point_count).toBe("5");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_frame_id).toBe("laser");
      expect(summary.readback_summary.map.robot_pose_status).toBe("map_pose_observed");
	      expect(summary.readback_summary.map.radar_overlay_robot_pose_status).toBe("map_pose_observed");
	      expect(summary.readback_summary.map.map_wysiwyg_status_plain).toBe("地图画面未读到；不能把旧图或空白图当作当前所见。");
	      expect(summary.readback_summary.radar.radar_status_plain).toBe("雷达点已贴到当前地图：当前显示 3 个点，frame=laser");
	      expect(summary.readback_summary.radar.radar_next_action_plain).toBe("继续观察地图雷达层");
	      expect(summary.readback_summary.radar.plain_hint).toBe("雷达点已贴到当前地图：当前显示 3 个点，frame=laser。下一步：继续观察地图雷达层。");
	      expect(summary.current_fact_plain).toContain("雷达点已贴到当前地图：当前显示 3 个点，frame=laser");
	      expect(summary.current_fact_plain).not.toContain("先修复雷达扫描观测");
	      expect(summary.action_status_cards?.find((card) => card.id === "map_preview")).toMatchObject({
	        status: "not_visible",
	        status_label: "未显示",
	        wysiwyg_status: "map_not_visible",
	        next_action_plain: "先刷新地图画面",
	      });
	      expect(summary.goal_checklist?.find((item) => item.id === "map_wysiwyg")).toMatchObject({
	        status: "needs_action",
	        status_label: "待处理",
	        blocks_goal_completion: true,
	      });
	      expect(summary.readback_summary.map.plain_hint).toContain("地图画面未读到；不能把旧图或空白图当作当前所见");
      expect(summary.readback_summary.map.plain_hint).toContain("地图雷达点已按当前读数显示：当前显示 3 个点，frame=laser");
      expect(summary.readback_summary.map.plain_hint).not.toContain("雷达 marker");
      expect(summary.readback_summary.map.plain_hint).not.toContain("overlay");
      expect(summary.readback_summary.map.map_wysiwyg_next_action_plain).toBe("先刷新地图画面。");
      expect(summary.readback_summary.map.next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(summary.readback_summary.map.map_next_action_plain).toBe("先刷新地图画面。");
      expect(summary.readback_summary.map.path_preview_status).toBe("path_preview_observed");
      expect(summary.readback_summary.map.path_preview_point_count).toBe("3");
      expect(summary.readback_summary.map.path_preview_frame_id).toBe("map");
      expect(summary.readback_summary.map.path_preview_next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(summary.readback_summary.map.path_wysiwyg_status_plain).toBe("图上路线已显示在当前地图画面。");
      expect(summary.readback_summary.map.path_wysiwyg_next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(summary.o3_proof_summary.path_preview_points).toEqual([
        { x: 0, y: 0, frame_id: "map", source_index: 0 },
        { x: 0.4, y: 0.1, frame_id: "map", source_index: 12 },
        { x: 0.8, y: 0, frame_id: "map", source_index: 30 },
      ]);
      expect(summary.o3_proof_summary.path_preview_point_count).toBe(3);
      expect(summary.o3_proof_summary.path_preview_source_point_count).toBe(31);
      expect(summary.o3_proof_summary.path_preview_frame_id).toBe("map");
      expect(summary.o3_proof_summary.scan_preview_point_count).toBe(3);
      expect(summary.o3_proof_summary.scan_preview_source_point_count).toBe(5);
      expect(summary.o3_proof_summary.scan_preview_frame_id).toBe("laser");
      expect(summary.o3_proof_summary.robot_pose).toEqual({
        x: 0.25,
        y: 0.75,
        yaw: 1.57,
        frame_id: "map",
        source: "/amcl_pose",
      });
      expect(summary.o3_proof_summary.frame_transforms.base_link_to_laser_frame).toEqual({
        parent_frame_id: "base_link",
        child_frame_id: "laser_frame",
        x: 0.1,
        y: 0,
        yaw: 0.05,
        source: "tf2_echo base_link laser_frame",
      });
      expect(summary.o3_proof_summary.scan_preview_points[0]).toEqual(expect.objectContaining({
        range_m: 1,
        angle_rad: 0,
        frame_id: "laser",
        source_index: 0,
      }));
      expect(summary.o3_proof_summary.scan_preview_points[1]?.x_m).toBeCloseTo(0, 5);
      expect(summary.o3_proof_summary.scan_preview_points[1]?.y_m).toBeCloseTo(2, 5);
      expect(summary.readback_summary.base.feedback_link_status).toBe("not_observed");
      expect(summary.o3_proof_summary.path_generated).toBe(true);
    } finally {
      await robotApi.close();
    }
  }, 12_000);

  it("Robot Control summary returns partial readbacks when the HTTP first-screen budget is shorter than slow camera health", async () => {
    // 首屏不能因为 camera health 或 status 慢就让普通页面空白；慢项标 timeout，已读到的自由移动/Nav2/雷达事实先展示。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        delay_ms: 300,
        payload: safePayload("trashbot.upper_robot_api.v1.status", "ready_but_slow"),
      },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
          map_file_observed: true,
          map_metadata_observed: true,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "localization_reset_observed"),
          amcl_pose_observed: true,
          amcl_pose: { frame_id: "map", x: 0.1, y: 0.2, yaw: 0, source: "/amcl_pose" },
        },
      },
      "/api/nav2/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "loaded"),
          planner_server_active: false,
          controller_server_active: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "nav2_path_ready"),
          path_generated: true,
          path_point_count: 3,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution_latest", "not_proven"),
      },
      "/api/operator/report": {
        payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded"),
      },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          free_roam_runtime_artifact_proven: true,
          free_roam_state_machine_observed: true,
          ros2_runtime_proven: true,
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              state: "stopping",
              reason: "停止兜底已就绪，雷达过期后按无雷达低速自由移动",
              stop_required: true,
              start_ready: true,
              motion_start_ready: true,
              mapping_ready: false,
              mapping_missing: ["camera_first_frame", "lidar_fresh"],
            },
          },
        },
      },
      "/api/camera/health": {
        delay_ms: 300,
        payload: safePayload("trashbot.upper_robot_api.v1.camera_health", "source_first_frame_failed"),
      },
      "/api/camera/devices": {
        payload: safePayload("trashbot.upper_robot_api.v1.camera_devices", "devices_ready"),
      },
      "/api/radar/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "stale_window_observed"),
      },
      "/api/radar/scan-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_scan_proof_latest", "scan_stale"),
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_raw_packet_proof_latest", "raw_packet_not_proven"),
      },
      "/api/base/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
      },
      "/api/base/feedback-samples/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples", "loaded"),
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, null, { readbackTimeoutMs: 50 });

      expect(summary.console_status).toBe("loaded_fail_closed_summary");
      expect(summary.robot_api_connection.status).toBe("degraded");
      expect(summary.robot_api_connection.failed_count).toBe(2);
      expect(summary.robot_api_connection.schema_mismatch_count).toBe(0);
      expect(summary.read_endpoints.find((item) => item.id === "status")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_50ms"],
      }));
      expect(summary.read_endpoints.find((item) => item.id === "camera_health")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_50ms"],
      }));
      expect(summary.readback_summary.free_roam.motion_start_ready).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_start_ready).toBe("true");
      expect(summary.readback_summary.free_roam.free_move_start_status_plain).toBe("自由移动可启动；只需现场安全确认和停止兜底。");
      expect(summary.readback_summary.free_roam.plain_hint).not.toContain("停止请求");
      expect(summary.readback_summary.free_roam.motion_runtime_status_plain).toBe("当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。");
      expect(summary.safe_command_boundary.free_roam_motion_start_ready).toBe(true);
      expect(summary.safe_command_boundary.free_roam_mapping_ready).toBe(false);
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([
        "planner_server_inactive",
      ]);
      expect(summary.readback_summary.camera.devices_status).toBe("devices_ready");
      expect(summary.readback_summary.lidar.status).toBe("stale_window_observed");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps camera no-frame diagnosis when camera health times out but shared overlay has source failure", async () => {
    // live 7001 形态：summary 短预算可能让 camera health timeout；PC 仍应用共享预览覆盖诊断解释“不是独占”。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.status", "source_first_frame_failed"),
      },
      "/api/map/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
      },
      "/api/localize/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "blocked_with_root_cause"),
      },
      "/api/nav2/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven"),
      },
      "/api/nav2/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven"),
      },
      "/api/nav2/goal/execution/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution_latest", "not_proven"),
      },
      "/api/operator/report": {
        payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded"),
      },
      "/api/free-roam/autonomy/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
      },
      "/api/camera/health": {
        delay_ms: 300,
        payload: safePayload("trashbot.upper_robot_api.v1.camera_health", "source_first_frame_failed"),
      },
      "/api/camera/devices": {
        payload: safePayload("trashbot.upper_robot_api.v1.camera_devices", "devices_ready"),
      },
      "/api/radar/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded"),
      },
      "/api/radar/scan-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_scan_proof_latest", "scan_stale"),
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_raw_packet_proof_latest", "raw_packet_not_proven"),
      },
      "/api/base/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
      },
      "/api/base/feedback-samples/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples", "loaded"),
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, {
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: "camera_source_first_frame_failed",
        last_remote_http_status: 200,
        last_failure_at_ms: 1782581956648,
        source_diagnosis_status: "uvc_no_frame_not_exclusive",
        source_diagnosis_plain_hint: "不是页面独占：USB Composite Device 当前没人占用，但 UVC 设备没有输出视频帧。",
        source_diagnosis_next_action: "check_usb_camera_input_power_or_known_good_uvc",
        source_diagnosis_not_exclusive: "true",
      }, { readbackTimeoutMs: 50 });

      expect(summary.read_endpoints.find((item) => item.id === "camera_health")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_50ms"],
      }));
      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toBe("不是页面独占：USB Composite Device 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summary.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
      expect(summary.robot_api_connection.status).toBe("degraded");
      expect(summary.safe_to_control).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary does not trust stale positive camera overlay when camera health times out", async () => {
    // 正向“首帧已读到”会放行建图，必须来自当前 health 或 probe；旧 relay overlay 只能作为历史状态。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded"),
      },
      "/api/map/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
      },
      "/api/localize/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "blocked_with_root_cause"),
      },
      "/api/nav2/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven"),
      },
      "/api/nav2/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven"),
      },
      "/api/nav2/goal/execution/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution_latest", "not_proven"),
      },
      "/api/operator/report": {
        payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded"),
      },
      "/api/free-roam/autonomy/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
      },
      "/api/camera/health": {
        delay_ms: 300,
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.camera_health", "ready"),
          source_readiness: "first_frame_observed",
          source_failure_reason: "none",
        },
      },
      "/api/camera/devices": {
        payload: safePayload("trashbot.upper_robot_api.v1.camera_devices", "devices_ready"),
      },
      "/api/radar/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded"),
      },
      "/api/radar/scan-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_scan_proof_latest", "scan_stale"),
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_raw_packet_proof_latest", "raw_packet_not_proven"),
      },
      "/api/base/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
      },
      "/api/base/feedback-samples/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples", "loaded"),
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, {
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: "none",
        last_remote_http_status: 200,
        last_failure_at_ms: null,
        source_diagnosis_status: "first_frame_observed",
        source_diagnosis_plain_hint: "USB Composite Device: DV20 USB 已读到真实首帧，可继续看实时预览。",
        source_diagnosis_next_action: "open_shared_preview",
        source_diagnosis_not_exclusive: "true",
      }, { readbackTimeoutMs: 50 });

      expect(summary.read_endpoints.find((item) => item.id === "camera_health")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_50ms"],
      }));
      expect(summary.readback_summary.camera.status).toBe("fetch_failed");
      expect(summary.readback_summary.camera.source_readiness).not.toBe("first_frame_observed");
      expect(summary.readback_summary.camera.source_diagnosis_status).not.toBe("first_frame_observed");
      expect(summary.readback_summary.camera.camera_wysiwyg_status_plain).toContain("未出帧前不当作画面可见");
      expect(summary.readback_summary.camera.camera_wysiwyg_status_plain).not.toContain("首帧已读到");
      expect(summary.current_fact_plain).not.toContain("首帧已读到");
      expect(summary.action_status_cards?.find((card) => card.id === "camera_preview")).toMatchObject({
        blocks_mapping_start: true,
        evidence: {
          camera_current_frame_visible: false,
          camera_source_first_frame_ready: false,
          camera_source_readiness: "not_loaded",
          camera_blocks_mapping_start: true,
          source_diagnosis_status: "not_loaded",
          first_frame_probe_read_ok: false,
          visible_content_proven: false,
          shared_preview_cached_frame_loaded: false,
        },
      });
      expect(summary.safe_command_boundary.free_roam_mapping_start_missing_reasons).toContain("camera_first_frame");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary treats relay first-frame total timeout as source failure when camera health times out", async () => {
    // live 7001 形态：共享预览最近失败保留原始 first_frame_total_timeout；summary 不能退回 fetch_failed。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      evidence_ref: `${status}-proof`,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded"),
      },
      "/api/map/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
      },
      "/api/localize/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "blocked_with_root_cause"),
      },
      "/api/nav2/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven"),
      },
      "/api/nav2/proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven"),
      },
      "/api/nav2/goal/execution/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.nav2_goal_execution_latest", "not_proven"),
      },
      "/api/operator/report": {
        payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded"),
      },
      "/api/free-roam/autonomy/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
      },
      "/api/camera/health": {
        delay_ms: 300,
        payload: safePayload("trashbot.upper_robot_api.v1.camera_health", "ready"),
      },
      "/api/camera/devices": {
        payload: safePayload("trashbot.upper_robot_api.v1.camera_devices", "devices_ready"),
      },
      "/api/radar/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "loaded"),
      },
      "/api/radar/scan-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_scan_proof_latest", "scan_stale"),
      },
      "/api/radar/raw-packet-proof/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.radar_raw_packet_proof_latest", "raw_packet_not_proven"),
      },
      "/api/base/status": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded"),
      },
      "/api/base/feedback-samples/latest": {
        payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples", "loaded"),
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, null, {
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: "first_frame_total_timeout",
        last_remote_http_status: 502,
        last_failure_at_ms: 1782652235202,
        last_error_payload: {
          failure_reason: "first_frame_total_timeout",
          first_frame_format_attempts: [
            { label: "MJPG@640x480@30", status: "first_frame_unreadable" },
            { label: "YUYV@640x480@22", status: "first_frame_unreadable" },
            { label: "default@current", status: "first_frame_unreadable" },
          ],
        },
        source_diagnosis_status: "uvc_no_frame_not_exclusive",
        source_diagnosis_plain_hint: "不是页面独占：not_loaded 当前没人占用，但 UVC 设备没有输出视频帧。",
        source_diagnosis_next_action: "check_usb_camera_input_power_or_known_good_uvc",
        source_diagnosis_not_exclusive: "true",
      }, { readbackTimeoutMs: 50 });

      expect(summary.read_endpoints.find((item) => item.id === "camera_health")).toEqual(expect.objectContaining({
        request_status: "fetch_failed",
        blocked_reasons: ["fetch_timeout_50ms"],
      }));
      expect(summary.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summary.readback_summary.camera.source_failure_reason).toBe("first_frame_total_timeout");
      expect(summary.readback_summary.camera.shared_preview_last_failure_reason).toBe("first_frame_total_timeout");
      expect(summary.readback_summary.camera.shared_preview_last_remote_http_status).toBe("502");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toBe("不是页面独占：UVC 设备当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.source_diagnosis_plain_hint).not.toContain("not_loaded");
      expect(summary.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
      expect(summary.readback_summary.camera.last_offer_failure_reason).toBe("first_frame_total_timeout");
      expect(summary.readback_summary.camera.last_offer_format_attempts_summary).toBe("MJPG@640x480@30 无首帧；YUYV@640x480@22 无首帧；default@current 无首帧");
      expect(summary.readback_summary.camera.first_frame_probe_status).toBe("source_first_frame_failed");
      expect(summary.readback_summary.camera.first_frame_probe_failure_reason).toBe("first_frame_total_timeout");
      expect(summary.readback_summary.camera.first_frame_probe_read_ok).toBe("false");
      expect(summary.readback_summary.camera.first_frame_probe_visible_content_proven).toBe("false");
      expect(summary.readback_summary.camera.first_frame_probe_fallback_attempts_summary).toBe("MJPG@640x480@30 无首帧；YUYV@640x480@22 无首帧；default@current 无首帧");
      expect(summary.readback_summary.camera.first_frame_probe_checked_at_ms).toBe("1782652235202");
      expect(summary.safe_to_control).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary exposes partial map radar overlay when scan points exist but map pose is missing", async () => {
    // 当前 live 形态会读到局部 scan 点，但没有机器人 map pose；summary 必须把“局部点，不贴地图”结构化暴露。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded") },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "blocked_with_root_cause"),
          amcl_pose_observed: false,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
        },
      },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven") },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": { payload: safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded") },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": { payload: safePayload("trashbot.upper_robot_api.v1.radar_status", "scan_once_hz_raw_packet_tf_observed") },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
          scan_preview_points: [
            { x_m: -0.43, y_m: 0.02, range_m: 0.43, angle_rad: 3.1, frame_id: "laser_frame", source_index: 1 },
            { x_m: -0.43, y_m: -0.02, range_m: 0.43, angle_rad: 3.18, frame_id: "laser_frame", source_index: 5 },
          ],
          scan_preview_point_count: 2,
          scan_preview_source_point_count: 80,
          scan_preview_frame_id: "laser_frame",
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.map.radar_overlay_status).toBe("partial");
      expect(summary.readback_summary.map.radar_overlay_blocked_reasons).toBe("robot_pose_missing_for_map_radar_overlay");
      expect(summary.readback_summary.map.radar_overlay_wysiwyg_status_plain).toBe("雷达材料已读到 80 个来源点，当前可用雷达点 2 个，但地图贴图未完整确认；已有雷达来源点 80 个，但小车地图位置未读到；当前不能把雷达点贴到地图坐标。");
      expect(summary.readback_summary.map.radar_overlay_wysiwyg_next_action_plain).toBe("先刷新定位，再刷新雷达扫描和地图画面。");
      expect(summary.readback_summary.map.radar_overlay_point_count).toBe("2");
      expect(summary.readback_summary.map.radar_overlay_source_point_count).toBe("80");
      expect(summary.readback_summary.map.radar_overlay_frame_id).toBe("laser_frame");
      expect(summary.readback_summary.map.radar_overlay_source_frame_id).toBe("laser_frame");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_point_count).toBe("2");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_source_point_count).toBe("80");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_frame_id).toBe("laser_frame");
      expect(summary.readback_summary.map.robot_pose_status).toBe("not_observed");
      expect(summary.readback_summary.map.radar_overlay_robot_pose_status).toBe("not_observed");
      expect(summary.o3_proof_summary.scan_preview_point_count).toBe(2);
      expect(summary.o3_proof_summary.robot_pose).toBeNull();
      expect(summary.safe_to_control).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary does not count stale stopped radar proof as current map overlay", async () => {
    // live 形态：scan proof 里有旧点，但 runtime /scan 已过期且雷达 lifecycle_state=stopped；地图 overlay 不能继续报 65 个当前点。
    const safePayload = (schema: string, status = "loaded") => ({
      schema,
      status,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
    });
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": { payload: safePayload("trashbot.upper_robot_api.v1.status", "loaded") },
      "/api/map/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.map_lifecycle_proof_latest", "map_once_artifact_metadata_observed"),
          map_once_observed: true,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.localization_proof_latest", "blocked_with_root_cause"),
          amcl_pose_observed: true,
          localization_tf_observed: true,
          amcl_pose: { frame_id: "map", x: 0.2, y: 0.1, yaw: 0, source: "/amcl_pose" },
        },
      },
      "/api/nav2/status": { payload: safePayload("trashbot.upper_robot_api.v1.nav2_lifecycle_status", "not_proven") },
      "/api/nav2/proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.nav2_runtime_proof_latest", "not_proven"),
          path_preview_points: [
            { x: 0, y: 0, frame_id: "map", source_index: 0 },
            { x: 0.8, y: 0, frame_id: "map", source_index: 17 },
          ],
          path_preview_point_count: 2,
          path_preview_source_point_count: 18,
          path_preview_frame_id: "map",
        },
      },
      "/api/operator/report": { payload: safePayload("trashbot.upper_robot_api.v1.operator_report_latest_result", "loaded") },
      "/api/free-roam/autonomy/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.free_roam_autonomy_latest", "loaded"),
          latest_result: {
            snapshot: {
              lidar_age_s: 14392.64,
              lidar_min_distance_m: 0.04,
            },
          },
        },
      },
      "/api/camera/health": { payload: safePayload("trashbot.local_webrtc_camera_smoke.v1", "source_first_frame_failed") },
      "/api/camera/devices": { payload: safePayload("trashbot.local_webrtc_camera_devices.v1", "loaded") },
      "/api/radar/status": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.radar_status", "scan_once_hz_raw_packet_tf_observed"),
          lifecycle_state: "stopped",
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          ...safePayload("trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result", "loaded"),
          scan_preview_points: [
            { x_m: -0.43, y_m: 0.02, range_m: 0.43, angle_rad: 3.1, frame_id: "laser_frame", source_index: 1 },
            { x_m: -0.43, y_m: -0.02, range_m: 0.43, angle_rad: 3.18, frame_id: "laser_frame", source_index: 5 },
          ],
          scan_preview_point_count: 2,
          scan_preview_source_point_count: 65,
          scan_preview_frame_id: "laser_frame",
        },
      },
      "/api/radar/raw-packet-proof/latest": { statusCode: 404, payload: { error: "not_found" } },
      "/api/base/status": { payload: safePayload("trashbot.upper_robot_api.v1.base_status", "loaded") },
      "/api/base/feedback-samples/latest": { payload: safePayload("trashbot.upper_robot_api.v1.base_feedback_samples_latest_result", "loaded") },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.lidar.lifecycle_running).toBe("not_loaded");
      expect(summary.readback_summary.lidar.lifecycle_state).toBe("stopped");
      expect(summary.readback_summary.lidar.runtime_scan_status).toBe("stale");
      expect(summary.o3_proof_summary.scan_preview_point_count).toBe(2);
      expect(summary.readback_summary.map.radar_overlay_status).toBe("not_current");
      expect(summary.readback_summary.map.map_current_visible).toBe("true");
      expect(summary.readback_summary.map.path_current_visible).toBe("true");
      expect(summary.readback_summary.map.radar_overlay_current_visible).toBe("false");
      expect(summary.readback_summary.map.radar_overlay_plain_hint).toContain("已有雷达来源点 65 个");
      expect(summary.readback_summary.map.radar_overlay_plain_hint).toContain("当前不贴到地图");
      expect(summary.readback_summary.map.radar_overlay_wysiwyg_status_plain).toBe("雷达点未贴到当前地图：当前显示 0 个点；旧来源点 65 个只作诊断。已有雷达来源点 65 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。");
      expect(summary.readback_summary.map.radar_overlay_wysiwyg_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(summary.readback_summary.map.radar_overlay_next_action).toBe("start_radar_then_refresh_map_preview");
      expect(summary.readback_summary.map.radar_overlay_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(summary.readback_summary.map.radar_overlay_refresh_required).toBe("true");
      expect(summary.readback_summary.map.radar_overlay_stale_source_points_suppressed).toBe("true");
      expect(summary.readback_summary.map.radar_overlay_primary_blocked_reason).toBe("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(summary.readback_summary.map.radar_overlay_current_vs_source_plain).toBe("地图雷达点：当前 0 个，来源 65 个；旧来源点已抑制，未贴到当前地图；下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(summary.readback_summary.map.radar_overlay_blocked_reasons).toContain("runtime_scan_stale_for_map_radar_overlay");
      expect(summary.readback_summary.map.radar_overlay_blocked_reasons).toContain("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(summary.readback_summary.map.radar_overlay_blocked_reason_labels).toContain("雷达扫描已过期");
      expect(summary.readback_summary.map.radar_overlay_blocked_reason_labels).toContain("雷达未运行");
      expect(summary.readback_summary.map.radar_overlay_point_count).toBe("0");
      expect(summary.readback_summary.map.radar_overlay_source_point_count).toBe("65");
      expect(summary.readback_summary.map.radar_overlay_frame_id).toBe("not_loaded");
      expect(summary.readback_summary.map.radar_overlay_source_frame_id).toBe("laser_frame");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_point_count).toBe("0");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_source_point_count).toBe("65");
      expect(summary.readback_summary.map.radar_overlay_scan_preview_frame_id).toBe("laser_frame");
      expect(summary.readback_summary.map.robot_pose_status).toBe("map_pose_observed");
      expect(summary.readback_summary.map.map_wysiwyg_status_plain).toBe("地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：已有雷达来源点 65 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。");
      expect(summary.readback_summary.map.plain_hint).toContain("地图画面、图上路线和小车位置已显示");
      expect(summary.readback_summary.map.plain_hint).toContain("地图雷达点当前显示 0 个，旧来源点 65 个只作诊断");
      expect(summary.readback_summary.map.plain_hint).toContain("原因：雷达扫描已过期、雷达未运行");
      expect(summary.readback_summary.map.plain_hint).not.toContain("雷达 marker");
      expect(summary.readback_summary.map.plain_hint).not.toContain("overlay");
      expect(summary.readback_summary.map.map_wysiwyg_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(summary.readback_summary.map.next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(summary.readback_summary.map.map_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(summary.action_status_cards?.find((card) => card.id === "map_preview")).toMatchObject({
        status_label: "已显示",
        next_action_plain: "地图画面已显示；继续确认图上路线和小车位置，雷达点另看“地图雷达点”。",
      });
      expect(summary.action_status_cards?.find((card) => card.id === "radar_map_points")?.next_action_plain).toContain("先启动雷达");
      expect(summary.current_fact_plain).toContain("地图画面、图上路线和小车位置已显示");
      expect(summary.current_fact_plain).toContain("雷达未运行或扫描已停；地图雷达点当前显示 0 个，旧来源点 65 个只作诊断");
      expect(summary.current_fact_plain).not.toContain("雷达 marker");
      expect(summary.current_fact_plain.match(/旧来源点 65 个只作诊断/g)?.length).toBe(1);
      expect(summary.readback_summary.map.path_preview_status).toBe("path_preview_observed");
      expect(summary.readback_summary.map.path_preview_point_count).toBe("2");
      expect(summary.readback_summary.map.path_preview_frame_id).toBe("map");
      expect(summary.readback_summary.map.path_preview_next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(summary.readback_summary.map.path_wysiwyg_status_plain).toBe("图上路线已显示在当前地图画面。");
      expect(summary.readback_summary.map.path_wysiwyg_next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary infers UVC sibling node roles from camera devices when health omits them", async () => {
    // live 7001 形态：health 只知道选中了 /dev/video1，devices 只读枚举能补出同一 UVC 的 metadata 兄弟节点。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/camera/health": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_health",
          status: "source_first_frame_failed",
          video_source: "/dev/video1",
          video_source_mode: "auto",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_usage: {
            status: "not_in_use",
            owner_count: 0,
            owners: [],
          },
          current_selection: {
            selected_path: "/dev/video1",
            selected_name: "USB Composite Device: DV20 USB",
            selected_is_uvc_or_usb: true,
            selected_formats_summary: "MJPG@1280x720@30；YUYV@640x480@22",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/camera/devices": {
        payload: {
          schema: "trashbot.local_webrtc_camera_devices.v1",
          status: "loaded",
          source_candidates: {
            candidates: [
              {
                path: "/dev/video0",
                sysfs_name: "cedrus",
                v4l2_name: "cedrus (platform:cedrus)",
                is_uvc_or_usb: false,
                is_video_capture: true,
                is_metadata: false,
                is_decoder: true,
                formats_summary: "not_loaded",
              },
              {
                path: "/dev/video1",
                sysfs_name: "USB Composite Device: DV20 USB",
                v4l2_name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)",
                is_uvc_or_usb: true,
                is_video_capture: true,
                is_metadata: false,
                is_decoder: false,
                formats_summary: "MJPG@1280x720@30；YUYV@640x480@22",
              },
              {
                path: "/dev/video2",
                sysfs_name: "USB Composite Device: DV20 USB",
                v4l2_name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)",
                is_uvc_or_usb: true,
                is_video_capture: false,
                is_metadata: true,
                is_decoder: false,
                formats_summary: "not_loaded",
              },
            ],
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.camera.selected_path).toBe("/dev/video1");
      expect(summary.readback_summary.camera.selected_name).toBe("USB Composite Device: DV20 USB");
      expect(summary.readback_summary.camera.selected_role).toBe("video_capture");
      expect(summary.readback_summary.camera.selected_sibling_video_nodes_summary).toBe("/dev/video2=metadata");
      expect(summary.readback_summary.camera.selected_sibling_video_node_count).toBe("1");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.source_diagnosis_plain_hint).toBe("不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(summary.readback_summary.camera.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summary.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
    } finally {
      await robotApi.close();
    }
  }, 10_000);

  it("Robot Control summary promotes successful camera first-frame probe overlay over stale source failure", async () => {
    // 用户点过只读首帧检查后，summary 必须消费 PC Node 内存 overlay；刷新页面不能继续显示旧无帧结论。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/camera/health": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_health",
          status: "source_first_frame_failed",
          video_source: "/dev/video1",
          source_readiness: "first_frame_failed",
          source_failure_reason: "capture_read_returned_false",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/camera/devices": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_devices",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl, {
        checked_at_ms: 1782500000000,
        proxy_status: "probe_forwarded",
        status: "frame_read",
        failure_reason: "none",
        open_ok: "true",
        read_ok: "true",
        visible_content_proven: "true",
        backend_smoke_status: "not_requested",
        backend_frame_observed: "not_loaded",
        backend_attempts: "0",
        streamon_io_error_observed: "false",
        streamon_io_error_count: "0",
        latest_streamon_io_error: "none",
        fallback_attempts_summary: "none",
      });

      expect(summary.readback_summary.camera.status).toBe("ready");
      expect(summary.readback_summary.camera.source_readiness).toBe("first_frame_observed");
      expect(summary.readback_summary.camera.source_failure_reason).toBe("none");
      expect(summary.readback_summary.camera.first_frame_probe_status).toBe("frame_read");
      expect(summary.readback_summary.camera.first_frame_probe_open_ok).toBe("true");
      expect(summary.readback_summary.camera.first_frame_probe_read_ok).toBe("true");
      expect(summary.readback_summary.camera.first_frame_probe_visible_content_proven).toBe("true");
      expect(summary.readback_summary.camera.preview_plain_hint).toBe("相机源首帧已读到；本页共享实时预览还没显示缓存帧。");
      expect(summary.readback_summary.camera.preview_visible_plain).toBe("当前没有实时画面；相机源首帧已读到；本页共享实时预览还没显示缓存帧。");
      expect(summary.readback_summary.camera.camera_wysiwyg_status_plain).toBe("画面未可见：相机源首帧已读到；本页共享实时预览还没显示缓存帧。");
      expect(summary.readback_summary.camera.plain_hint).toContain("画面未显示：相机源首帧已读到；本页共享实时预览还没显示缓存帧");
      expect(summary.current_fact_plain).toContain("画面未显示：相机源首帧已读到；本页共享实时预览还没显示缓存帧");
      expect(summary.action_status_cards?.find((card) => card.id === "camera_preview")).toMatchObject({
        blocks_mapping_start: false,
        evidence: {
          camera_current_frame_visible: false,
          camera_source_first_frame_ready: true,
          camera_source_readiness: "first_frame_observed",
          camera_blocks_mapping_start: false,
          source_first_frame_failed: false,
          first_frame_probe_read_ok: true,
          visible_content_proven: true,
        },
      });
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary uses Nav2 proof amcl pose when localize latest is stale", async () => {
    // live 上位机可能 localize latest 仍是旧失败 artifact，但 Nav2 proof latest 已经带 /amcl_pose。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "blocked_with_root_cause",
          amcl_pose_observed: false,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "not_proven",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
          path_preview_point_count: 36,
          path_preview_frame_id: "map",
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          amcl_pose_observed: true,
          amcl_pose: { frame_id: "map", source: "/amcl_pose", x: 0.0052, y: 0.0237, yaw: 0.0013 },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest_result",
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-fixture",
          nav2_goal_execution_proven: true,
          goal_accepted: true,
          result_received: true,
          result_status: "succeeded",
          feedback_sample_count: 8,
          goal_frame_id: "map",
          goal_x: 0.8,
          goal_y: 0,
          robot_control_executed: true,
          sends_base_motion_commands: true,
          uses_base_uart: true,
          base_feedback_summary: {
            sample_count: 8,
            nonzero_sample_count: 2,
            wheel_feedback_lr_nonzero_proven: true,
            latest_nonzero_pair: { left_speed: 0.12, right_speed: 0.11 },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.o3_proof_summary.robot_pose).toEqual({
        x: 0.0052,
        y: 0.0237,
        yaw: 0.0013,
        frame_id: "map",
        source: "/amcl_pose",
      });
      expect(summary.readback_summary.localization.robot_pose_status).toBe("map_pose_observed");
      expect(summary.readback_summary.localization.robot_pose_x).toBe("0.0052");
      expect(summary.readback_summary.localization.robot_pose_y).toBe("0.0237");
      expect(summary.o3_proof_summary.path_generated).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal).toBe("Nav2 NavigateToPose locked");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线和小车位置已显示，等待安全确认");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.readback_summary.nav2.goal_execution_status).toBe("goal_succeeded");
      expect(summary.readback_summary.nav2.goal_execution_proven).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_result_status).toBe("succeeded");
      expect(summary.readback_summary.nav2.goal_execution_evidence_ref).toBe("o11-nav2-goal-execution-fixture");
      expect(summary.readback_summary.nav2.goal_execution_robot_control_executed).toBe("true");
      expect(summary.readback_summary.nav2.goal_execution_feedback_sample_count).toBe("8");
      expect(summary.readback_summary.nav2.goal_execution_goal_frame_id).toBe("map");
      expect(summary.readback_summary.nav2.goal_execution_goal_x).toBe("0.8");
      expect(summary.readback_summary.nav2.goal_execution_goal_y).toBe("0");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
      expect(summary.safe_to_control).toBe(false);
      expect(summary.delivery_success).toBe(false);
    } finally {
      await robotApi.close();
    }
  }, 10_000);

  it("keeps Nav2 route ready when only the robot map pose is missing", async () => {
    // 小车地图位置是所见即所得提示；路线点已生成时，summary 不应再把它当作发车硬 blocker。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "ready_for_route",
          map_once_observed: true,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 24,
          path_preview_point_count: 24,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "not_proven",
          amcl_pose_observed: false,
          localization_tf_observed: false,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "path_generated",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 24,
          path_preview_point_count: 24,
          path_preview_frame_id: "map",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "active",
          lifecycle_running: true,
          lifecycle_state: "active",
          latest_planner_active: true,
          latest_controller_active: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.o3_proof_summary.robot_pose).toBeNull();
      expect(summary.readback_summary.localization.robot_pose_status).toBe("not_observed");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线已显示，等待安全确认");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("勾选行程前安全确认后执行图上路线，并在同窗口复验 wheel raw L/R；小车位置未显示时建议先重新定位或刷新地图");
      expect(summary.safe_command_boundary.nav2_goal_next_action).not.toContain("读到小车地图位置");
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary blocks ready Nav2 route when controller is inactive", async () => {
    // 路线、点数和 map pose 都就绪时，controller inactive 仍必须是结构化 blocker，不能只藏在下一步文案里。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "localization_pose_observed",
          amcl_pose_observed: true,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          amcl_pose: { frame_id: "map", source: "/amcl_pose", x: 0.01, y: 0.02, yaw: 0 },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "path_generated",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 12,
          path_preview_point_count: 12,
          path_preview_frame_id: "map",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "not_proven",
          latest_controller_active: false,
          latest_controller_requested: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest_result",
          status: "not_loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.controller_server_active).toBe("false");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(false);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("控制服务未就绪");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual(["controller_server_inactive"]);
      expect(summary.safe_command_boundary.nav2_goal_wheel_feedback_status).toBe("awaiting_route_execution");
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("先恢复控制服务，再勾选行程前安全确认后执行图上路线，并在同窗口复验 wheel raw L/R");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("Robot Control summary keeps ready Nav2 route clickable when managed runtime can start lifecycle", async () => {
    // 上车端 8787 会把 lifecycle blocker 提升到 /api/nav2/status；PC 保留诊断，但 execute 会托管启动 runtime。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.status",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
          status: "path_generated",
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 18,
          path_preview_point_count: 18,
          path_preview_frame_id: "map",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
          status: "path_ready_with_service_blockers",
          proof_state: "path_ready_with_service_blockers",
          path_generated: true,
          path_point_count: 18,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          planner_server_active: true,
          controller_server_active: false,
          controller_server_requested: false,
          blocked_reasons: ["nav2_lifecycle_not_running"],
          next_action: "启动或恢复 Nav2 lifecycle 后再执行图上路线",
          sends_motion_commands: false,
          publishes_cmd_vel: false,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest_result",
          status: "not_loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.nav2.current_blocker_reasons).toBe("nav2_lifecycle_not_running");
      expect(summary.readback_summary.nav2.current_blocker_labels).toBe("自动驾驶 lifecycle 未运行");
      expect(summary.readback_summary.nav2.next_action_plain).toBe("勾选行程前安全确认后执行图上路线；执行时会自动启动自动驾驶 runtime，并在同窗口确认轮速 L/R 非零。");
      expect(summary.readback_summary.nav2.route_execution_precheck_plain).toBe("只需勾选行程前安全确认；相机、雷达和现场报告不作为额外发车前置；执行会用当前模式跑图上路线；执行时会自动启动自动驾驶 runtime。");
      expect(summary.current_fact_plain).toContain("自动驾驶：图上路线已准备，但本轮完整执行和轮速 L/R 还未证明。下一步：勾选行程前安全确认后执行图上路线；执行时会自动启动自动驾驶 runtime");
      expect(summary.safe_command_boundary.nav2_goal_ready).toBe(true);
      expect(summary.safe_command_boundary.nav2_goal_label).toBe("图上路线已显示，等待安全确认");
      expect(summary.safe_command_boundary.nav2_goal_blockers).toEqual([]);
      expect(summary.safe_command_boundary.nav2_goal_next_action).toBe("勾选行程前安全确认后执行图上路线；执行时会自动启动自动驾驶 runtime，并在同窗口复验 wheel raw L/R；小车位置未显示时建议先重新定位或刷新地图");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("workstation proof refresh proxies only allow fixed radar, map, and Nav2 POST bodies", async () => {
    // refresh 代理必须把 body 锁死成 workstation 预设值，且危险 true 字段仍然 fail closed。
    const upstream = await listenRobotProofRefreshApi({
      "/api/radar/scan-proof/refresh": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof_refresh",
          status: "refreshed",
          latest_proof_status: "raw_packets_parsed",
          evidence_ref: "radar-refresh-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_commands: true,
          starts_ros2: true,
          blocked_reasons: [
            "latest_scan_proof_required_observations_missing:scan_once,scan_hz,raw_packet_once,all_required_observations",
            "scan_continuity_not_observed",
          ],
          scan_once_observed: false,
          scan_hz_observed: false,
          raw_packet_once_observed: false,
          tf_observed: true,
          upper_api: {
            radar_status: {
              status: "loaded",
              payload: {
                continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
                continuous_window_observed: true,
                continuity_window_status: "fresh_window_observed",
                continuity_blocked_reasons: [],
                lifecycle_running: true,
                lifecycle_state: "running",
                latest_scan_proof_fresh: true,
                latest_scan_proof_state: "scan_once_hz_raw_packet_tf_observed",
                latest_scan_proof_blocked_reasons: [],
                latest_scan_proof: {
                  scan_once_observed: true,
                  scan_hz_observed: true,
                  raw_packet_once_observed: true,
                  tf_observed: true,
                },
              },
            },
          },
        },
      },
      "/api/map/proof/refresh": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_proof_refresh",
          status: "map_once_artifact_metadata_observed",
          evidence_ref: "map-refresh-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_commands: true,
          starts_ros2: true,
          map_once_observed: true,
          map_file_observed: true,
          map_metadata_observed: true,
        },
      },
      "/api/nav2/proof/refresh": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_refresh",
          status: "blocked_with_root_cause",
          latest_proof_status: "blocked_with_root_cause",
          evidence_ref: "nav2-refresh-proof",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          managed_runtime_started: true,
          initialpose_published: true,
          path_generation_requested: true,
          path_generation_boundary: "path_generation_blocked_by_map_has_no_free_cells",
          path_generated: false,
          path_generation_succeeded: false,
          path_point_count: 0,
          planner_server_active: true,
          root_causes: [{ layer: "map quality", reason: "map_has_no_free_cells_for_nav2_path_proof" }],
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const radarResponse = await fetch(
        `${workstation.baseUrl}/api/robot-control/radar/scan-proof/refresh?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ignored: true }),
        },
      );
      const radarBody = (await radarResponse.json()) as {
        proxy_status: string;
        safe_to_control: boolean;
        blocked_reasons: string[];
        last_result_evidence_ref: string;
        latest_readback_key_values: Record<string, string>;
        latest_proof_status: string;
        scan_once_observed: string;
        scan_hz_observed: string;
        raw_packet_once_observed: string;
        tf_observed: string;
        continuous_scan_status: string;
        lifecycle_running: string;
        lifecycle_state: string;
        continuous_window_observed: string;
        continuity_window_status: string;
        latest_scan_proof_fresh: string;
        hard_dangerous_true_fields: string[];
        non_motion_evidence_actions_observed: string[];
      };
      expect(radarResponse.status).toBe(200);
      expect(radarBody.proxy_status).toBe("refresh_forwarded");
      expect(radarBody.safe_to_control).toBe(false);
      expect(radarBody.blocked_reasons).toEqual([]);
      expect(radarBody.last_result_evidence_ref).toBe("radar-refresh-proof");
      expect(radarBody.hard_dangerous_true_fields).toEqual([]);
      expect(radarBody.non_motion_evidence_actions_observed).toEqual(expect.arrayContaining(["sends_commands", "starts_ros2"]));
      expect(radarBody.latest_readback_key_values.scan_once_observed).toBe("true");
      expect(radarBody.latest_readback_key_values.scan_hz_observed).toBe("true");
      expect(radarBody.latest_readback_key_values.raw_packet_once_observed).toBe("true");
      expect(radarBody.latest_readback_key_values.tf_observed).toBe("true");
      expect(radarBody.latest_readback_key_values.latest_proof_status).toBe("scan_once_hz_raw_packet_tf_observed");
      expect(radarBody.latest_readback_key_values.continuous_scan_status).toBe("latest_proof_fresh_while_lifecycle_running");
      expect(radarBody.latest_readback_key_values.lifecycle_running).toBe("true");
      expect(radarBody.latest_readback_key_values.lifecycle_state).toBe("running");
      expect(radarBody.latest_readback_key_values.continuous_window_observed).toBe("true");
      expect(radarBody.latest_readback_key_values.continuity_window_status).toBe("fresh_window_observed");
      expect(radarBody.latest_readback_key_values.latest_scan_proof_fresh).toBe("true");
      expect(radarBody.scan_once_observed).toBe("true");
      expect(radarBody.scan_hz_observed).toBe("true");
      expect(radarBody.raw_packet_once_observed).toBe("true");
      expect(radarBody.tf_observed).toBe("true");
      expect(radarBody.latest_proof_status).toBe("scan_once_hz_raw_packet_tf_observed");
      expect(radarBody.continuous_scan_status).toBe("latest_proof_fresh_while_lifecycle_running");
      expect(radarBody.lifecycle_running).toBe("true");
      expect(radarBody.lifecycle_state).toBe("running");
      expect(radarBody.continuous_window_observed).toBe("true");
      expect(radarBody.continuity_window_status).toBe("fresh_window_observed");
      expect(radarBody.latest_scan_proof_fresh).toBe("true");
      expect(radarBody.latest_readback_key_values.blocked_reasons).toBeUndefined();
      expect(radarBody.latest_readback_key_values.continuity_blocked_reasons).toBeUndefined();
      expect(upstream.receivedBodies["/api/radar/scan-proof/refresh"]?.[0]).toEqual({
        timeout_s: 12,
      });

      const mapResponse = await fetch(
        `${workstation.baseUrl}/api/robot-control/map/proof/refresh?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ignored: true }),
        },
      );
      const mapBody = (await mapResponse.json()) as {
        proxy_status: string;
        safe_to_control: boolean;
        blocked_reasons: string[];
        latest_readback_key_values: Record<string, string>;
        hard_dangerous_true_fields: string[];
        non_motion_evidence_actions_observed: string[];
      };
      expect(mapResponse.status).toBe(200);
      expect(mapBody.proxy_status).toBe("refresh_forwarded");
      expect(mapBody.safe_to_control).toBe(false);
      expect(mapBody.blocked_reasons).toEqual([]);
      expect(mapBody.hard_dangerous_true_fields).toEqual([]);
      expect(mapBody.non_motion_evidence_actions_observed).toEqual(expect.arrayContaining(["sends_commands", "starts_ros2"]));
      expect(mapBody.latest_readback_key_values.map_once_observed).toBe("true");
      expect(upstream.receivedBodies["/api/map/proof/refresh"]?.[0]).toEqual({ timeout_s: 45 });

      const nav2Response = await fetch(
        `${workstation.baseUrl}/api/robot-control/nav2/proof/refresh?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ path_goal_x: 99, starts_nav2: true }),
        },
      );
      const nav2Body = (await nav2Response.json()) as {
        proxy_status: string;
        safe_to_control: boolean;
        delivery_success: boolean;
        primary_actions_enabled: boolean;
        robot_control_executed: boolean;
        remote_endpoint: string;
        latest_readback_key_values: Record<string, string>;
        hard_dangerous_true_fields: string[];
      };
      expect(nav2Response.status).toBe(200);
      expect(nav2Body.proxy_status).toBe("refresh_forwarded");
      expect(nav2Body.remote_endpoint).toBe("/api/nav2/proof/refresh");
      expect(nav2Body.safe_to_control).toBe(false);
      expect(nav2Body.delivery_success).toBe(false);
      expect(nav2Body.primary_actions_enabled).toBe(false);
      expect(nav2Body.robot_control_executed).toBe(false);
      expect(nav2Body.hard_dangerous_true_fields).toEqual([]);
      expect(nav2Body.latest_readback_key_values.path_generated).toBe("false");
      expect(nav2Body.latest_readback_key_values.path_generation_succeeded).toBe("false");
      expect(nav2Body.latest_readback_key_values.root_causes).toContain("map_has_no_free_cells_for_nav2_path_proof");
      expect(nav2Body.latest_readback_key_values.root_causes).not.toBe("[object Object]");
      expect(upstream.receivedBodies["/api/nav2/proof/refresh"]?.[0]).toEqual({
        timeout_s: 30,
        managed_runtime_opt_in: true,
        managed_timeout_s: 30,
        initialpose_opt_in: true,
        initialpose_x: 0,
        initialpose_y: 0,
        initialpose_yaw: 0,
        path_generation_opt_in: true,
        path_generation_timeout_s: 30,
        path_goal_frame_id: "map",
        path_goal_x: 0.8,
        path_goal_y: 0,
        path_goal_yaw: 0,
      });
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation proof refresh proxies still fail closed on hard dangerous true fields", async () => {
    // 允许的证据动作不能放开控制面，但真正的硬危险字段仍然必须 fail closed。
    const upstream = await listenRobotProofRefreshApi({
      "/api/radar/scan-proof/refresh": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof_refresh",
          status: "scan_once_observed",
          evidence_ref: "radar-refresh-proof",
          safe_to_control: true,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          scan_once_observed: true,
          scan_hz_observed: 10,
          raw_packet_once_observed: true,
          tf_observed: true,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(
        `${workstation.baseUrl}/api/robot-control/radar/scan-proof/refresh?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ignored: true }),
        },
      );
      const body = (await response.json()) as {
        proxy_status: string;
        failure_reason: string;
        blocked_reasons: string[];
        hard_dangerous_true_fields: string[];
        non_motion_evidence_actions_observed: string[];
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("refresh_failed");
      expect(body.failure_reason).toBe("hard_dangerous_true_field:safe_to_control");
      expect(body.blocked_reasons).toContain("hard_dangerous_true_field:safe_to_control");
      expect(body.hard_dangerous_true_fields).toContain("safe_to_control");
      expect(body.non_motion_evidence_actions_observed).toEqual([]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("reads fixed radar latest after refresh when observations are present but fresh lags", async () => {
    // 上车端 artifact 落盘有短暂时序差时，PC 代理只能补读固定 latest GET，不能补发任何运动或 start POST。
    const originalFetch = globalThis.fetch;
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = String(url);
      if (init?.method === "POST" && requestUrl === "http://127.0.0.1:8787/api/radar/scan-proof/refresh") {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            schema: "trashbot.upper_robot_api.v1.radar_scan_proof_refresh",
            status: "refreshed",
            evidence_ref: "radar-refresh-proof",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
            robot_control_executed: false,
            upper_api: {
              radar_status: {
                payload: {
                  continuous_scan_status: "latest_proof_stale_while_lifecycle_running",
                  continuous_window_observed: true,
                  continuity_window_status: "fresh_window_observed",
                  lifecycle_running: true,
                  lifecycle_state: "running",
                  latest_scan_proof_fresh: false,
                  latest_scan_proof_state: "scan_once_hz_raw_packet_tf_observed",
                  latest_scan_proof_blocked_reasons: [],
                  latest_scan_proof: {
                    scan_once_observed: true,
                    scan_hz_observed: true,
                    raw_packet_once_observed: true,
                    tf_observed: true,
                  },
                },
              },
            },
          }),
        } as Response;
      }
      if (init?.method === "GET" && requestUrl === "http://127.0.0.1:8787/api/radar/scan-proof/latest") {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            schema: "trashbot.upper_robot_api.v1.radar_scan_proof_latest",
            status: "scan_once_hz_raw_packet_tf_observed",
            latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
            latest_scan_once_observed: true,
            latest_scan_hz_observed: true,
            latest_raw_packet_once_observed: true,
            latest_tf_observed: true,
            latest_scan_proof_fresh: true,
            continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
            continuous_window_observed: true,
            continuity_window_status: "fresh_window_observed",
            lifecycle_running: true,
            lifecycle_state: "running",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
          }),
        } as Response;
      }
      throw new Error(`unexpected fetch ${init?.method ?? "GET"} ${requestUrl}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildRadarScanProofRefreshProxy("http://127.0.0.1:8787");
      expect(response.proxy_status).toBe("refresh_forwarded");
      expect(response.scan_once_observed).toBe("true");
      expect(response.scan_hz_observed).toBe("true");
      expect(response.raw_packet_once_observed).toBe("true");
      expect(response.tf_observed).toBe("true");
      expect(response.latest_scan_proof_fresh).toBe("true");
      expect(response.continuous_scan_status).toBe("latest_proof_fresh_while_lifecycle_running");
      expect(response.latest_readback_key_values.latest_scan_proof_fresh).toBe("true");
      expect(response.post_refresh_latest_readback_status).toBe("fresh_after_retry");
      expect(response.post_refresh_latest_readback_attempt_count).toBe("1");
      expect(response.robot_control_executed).toBe(false);
      expect(response.safe_to_control).toBe(false);
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(fetchMock.mock.calls.map(([calledUrl, init]) => `${init?.method ?? "GET"} ${String(calledUrl)}`)).toEqual([
        "POST http://127.0.0.1:8787/api/radar/scan-proof/refresh",
        "GET http://127.0.0.1:8787/api/radar/scan-proof/latest",
      ]);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("reads fixed radar latest after refresh when the success response omits scan fields", async () => {
    // 真实上车端可能只返回 refreshed；成功但字段不完整时也要补读 latest，避免按钮回包缺 scan/fresh alias。
    const originalFetch = globalThis.fetch;
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = String(url);
      if (init?.method === "POST" && requestUrl === "http://127.0.0.1:8787/api/radar/scan-proof/refresh") {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            schema: "trashbot.upper_robot_api.v1.radar_scan_proof_refresh",
            status: "refreshed",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
            robot_control_executed: false,
          }),
        } as Response;
      }
      if (init?.method === "GET" && requestUrl === "http://127.0.0.1:8787/api/radar/scan-proof/latest") {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            status: "scan_once_hz_raw_packet_tf_observed",
            latest_scan_once_observed: true,
            latest_scan_hz_observed: true,
            latest_raw_packet_once_observed: true,
            latest_tf_observed: true,
            latest_scan_proof_fresh: true,
            continuous_scan_status: "latest_proof_fresh_while_lifecycle_running",
            lifecycle_running: true,
            lifecycle_state: "running",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
          }),
        } as Response;
      }
      throw new Error(`unexpected fetch ${init?.method ?? "GET"} ${requestUrl}`);
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildRadarScanProofRefreshProxy("http://127.0.0.1:8787");
      expect(response.scan_once_observed).toBe("true");
      expect(response.scan_hz_observed).toBe("true");
      expect(response.raw_packet_once_observed).toBe("true");
      expect(response.tf_observed).toBe("true");
      expect(response.latest_scan_proof_fresh).toBe("true");
      expect(response.post_refresh_latest_readback_status).toBe("fresh_after_retry");
      expect(response.post_refresh_latest_readback_attempt_count).toBe("1");
      expect(response.robot_control_executed).toBe(false);
      expect(fetchMock.mock.calls.map(([calledUrl, init]) => `${init?.method ?? "GET"} ${String(calledUrl)}`)).toEqual([
        "POST http://127.0.0.1:8787/api/radar/scan-proof/refresh",
        "GET http://127.0.0.1:8787/api/radar/scan-proof/latest",
      ]);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("workstation Nav2 no-motion proof refresh fails closed on motion and Nav2 start claims", async () => {
    // Nav2 规划检查不能接受任何启动 Nav2、发布 /cmd_vel 或执行控制的上位机声明。
    const upstream = await listenRobotProofRefreshApi({
      "/api/nav2/proof/refresh": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_refresh",
          status: "unsafe_nav2_claim",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: true,
          starts_nav2: true,
          publishes_cmd_vel: true,
          path_generated: true,
          path_generation_succeeded: true,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(
        `${workstation.baseUrl}/api/robot-control/nav2/proof/refresh?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ignored: true }),
        },
      );
      const body = (await response.json()) as {
        proxy_status: string;
        status: string;
        safe_to_control: boolean;
        delivery_success: boolean;
        primary_actions_enabled: boolean;
        robot_control_executed: boolean;
        hard_dangerous_true_fields: string[];
        blocked_reasons: string[];
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("refresh_failed");
      expect(body.status).toBe("blocked");
      expect(body.safe_to_control).toBe(false);
      expect(body.delivery_success).toBe(false);
      expect(body.primary_actions_enabled).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(body.hard_dangerous_true_fields).toEqual(expect.arrayContaining([
        "robot_control_executed",
        "starts_nav2",
        "publishes_cmd_vel",
      ]));
      expect(body.blocked_reasons).toEqual(expect.arrayContaining([
        "hard_dangerous_true_field:robot_control_executed",
        "hard_dangerous_true_field:starts_nav2",
        "hard_dangerous_true_field:publishes_cmd_vel",
      ]));
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation radar lifecycle proxies use fixed endpoints, empty body, and local URL guard", async () => {
    // radar lifecycle 只能触发 start/stop 两个固定传感器 endpoint，不能透传浏览器 body。
    const directRejected = await buildRadarLifecycleProxy("", "stop");
    expect(directRejected.proxy_status).toBe("lifecycle_rejected");
    expect(directRejected.failure_reason).toBe("baseUrl_not_provided");
    expect(directRejected.safe_to_control).toBe(false);

    const upstream = await listenRobotProofRefreshApi({
      "/api/radar/start": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_lifecycle",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_commands: true,
          sends_motion_commands: false,
          sends_base_motion_commands: false,
          uses_base_uart: false,
          command_result: { mode: "dry_run_stub", executed: false, ok: false },
          failure_reason: "command_not_configured",
          blocked_reasons: ["command_not_configured"],
        },
      },
      "/api/radar/stop": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_lifecycle",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_commands: true,
          sends_motion_commands: false,
          sends_base_motion_commands: false,
          uses_base_uart: false,
          command_result: { mode: "dry_run_stub", executed: false, ok: false },
          failure_reason: "command_not_configured",
          blocked_reasons: ["command_not_configured"],
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const invalidBaseUrlResponse = await fetch(`${workstation.baseUrl}/api/robot-control/radar/stop?baseUrl=${encodeURIComponent("https://192.168.1.11:8787")}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/base/manual" }),
      });
      const invalidBaseUrlBody = (await invalidBaseUrlResponse.json()) as { proxy_status: string; failure_reason: string };
      expect(invalidBaseUrlResponse.status).toBe(400);
      expect(invalidBaseUrlBody.proxy_status).toBe("lifecycle_rejected");
      expect(invalidBaseUrlBody.failure_reason).toBe("baseUrl_protocol_not_allowed");

      const startResponse = await fetch(`${workstation.baseUrl}/api/robot-control/radar/start?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/base/manual", sends_motion_commands: true }),
      });
      const startBody = (await startResponse.json()) as {
        action: string;
        proxy_status: string;
        remote_endpoint: string;
        remote_http_status: number;
        command_result: { mode: string; executed: boolean; ok: boolean };
        sensor_lifecycle_only: boolean;
        map_preview_endpoint: string;
        post_start_map_preview_required: boolean;
        radar_overlay_wysiwyg_status_plain: string;
        radar_overlay_wysiwyg_next_action_plain: string;
        failure_reason: string;
        blocked_reasons: string[];
        hard_dangerous_true_fields: string[];
        robot_control_executed: boolean;
        safe_to_control: boolean;
      };
      expect(startResponse.status).toBe(200);
      expect(startBody.action).toBe("start");
      expect(startBody.proxy_status).toBe("lifecycle_forwarded");
      expect(startBody.remote_endpoint).toBe("/api/radar/start");
      expect(startBody.remote_http_status).toBe(200);
      expect(startBody.command_result).toEqual({ mode: "dry_run_stub", executed: false, ok: false });
      expect(startBody.sensor_lifecycle_only).toBe(true);
      expect(startBody.map_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(startBody.post_start_map_preview_required).toBe(true);
      expect(startBody.radar_overlay_wysiwyg_status_plain).toBe("雷达启动请求已转发；地图上是否显示雷达点必须以后续地图预览的 radar_overlay_status 和点数为准。");
      expect(startBody.radar_overlay_wysiwyg_next_action_plain).toBe("等待新扫描后刷新地图画面，确认 radar_overlay_status=loaded 且 radar_overlay_point_count 大于 0。");
      expect(startBody.failure_reason).toBe("command_not_configured");
      expect(startBody.blocked_reasons).toContain("command_not_configured");
      expect(startBody.hard_dangerous_true_fields).toEqual([]);
      expect(startBody.robot_control_executed).toBe(false);
      expect(startBody.safe_to_control).toBe(false);

      const stopResponse = await fetch(`${workstation.baseUrl}/api/robot-control/radar/stop?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arbitrary_endpoint: "/api/radar/status" }),
      });
      const stopBody = (await stopResponse.json()) as {
        action: string;
        remote_endpoint: string;
        command_result: { mode: string; executed: boolean };
        sensor_lifecycle_only: boolean;
        map_preview_endpoint: string;
        post_start_map_preview_required: boolean;
        radar_overlay_wysiwyg_next_action_plain: string;
      };
      expect(stopResponse.status).toBe(200);
      expect(stopBody.action).toBe("stop");
      expect(stopBody.remote_endpoint).toBe("/api/radar/stop");
      expect(stopBody.command_result.mode).toBe("dry_run_stub");
      expect(stopBody.command_result.executed).toBe(false);
      expect(stopBody.sensor_lifecycle_only).toBe(true);
      expect(stopBody.map_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(stopBody.post_start_map_preview_required).toBe(false);
      expect(stopBody.radar_overlay_wysiwyg_next_action_plain).toBe("刷新地图画面，确认旧雷达点不再贴到当前地图。");
      expect(upstream.receivedBodies["/api/radar/start"]).toEqual([{}]);
      expect(upstream.receivedBodies["/api/radar/stop"]).toEqual([{}]);
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation Nav2 lifecycle proxies use fixed endpoints and reject motion claims", async () => {
    // Nav2 start 可以恢复服务栈，但不能接受目标执行、/cmd_vel 或底盘运动声明。
    const directRejected = await buildNav2LifecycleProxy("", "start");
    expect(directRejected.proxy_status).toBe("lifecycle_rejected");
    expect(directRejected.failure_reason).toBe("baseUrl_not_provided");
    expect(directRejected.safe_to_control).toBe(false);

    const upstream = await listenRobotProofRefreshApi({
      "/api/nav2/start": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle",
          status: "nav2_stack_started",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          starts_nav2: true,
          sends_motion_commands: false,
          sends_base_motion_commands: false,
          publishes_cmd_vel: false,
          command_result: { mode: "configured_command", executed: true, ok: true },
          blocked_reasons: [],
        },
      },
      "/api/nav2/stop": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_lifecycle",
          status: "unsafe_motion_claim",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          starts_nav2: true,
          sends_motion_commands: true,
          publishes_cmd_vel: true,
          command_result: { mode: "configured_command", executed: true, ok: false },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const startResponse = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/start?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/nav2/goal/execute", goal_x: 99, publishes_cmd_vel: true }),
      });
      const startBody = (await startResponse.json()) as {
        action: string;
        proxy_status: string;
        remote_endpoint: string;
        command_result: { mode: string; executed: boolean; ok: boolean };
        hard_dangerous_true_fields: string[];
        robot_control_executed: boolean;
        safe_to_control: boolean;
      };
      expect(startResponse.status).toBe(200);
      expect(startBody.action).toBe("start");
      expect(startBody.proxy_status).toBe("lifecycle_forwarded");
      expect(startBody.remote_endpoint).toBe("/api/nav2/start");
      expect(startBody.command_result).toEqual({ mode: "configured_command", executed: true, ok: true });
      expect(startBody.hard_dangerous_true_fields).toEqual([]);
      expect(startBody.robot_control_executed).toBe(false);
      expect(startBody.safe_to_control).toBe(false);

      const emptyBaseUrlResponse = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/start?baseUrl=`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/nav2/start" }),
      });
      const emptyBaseUrlBody = (await emptyBaseUrlResponse.json()) as { proxy_status: string; failure_reason: string };
      expect(emptyBaseUrlResponse.status).toBe(400);
      expect(emptyBaseUrlBody.proxy_status).toBe("lifecycle_rejected");
      expect(emptyBaseUrlBody.failure_reason).toBe("baseUrl_not_provided");

      const stopResponse = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/stop?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/base/manual" }),
      });
      const stopBody = (await stopResponse.json()) as {
        proxy_status: string;
        status: string;
        failure_reason: string;
        hard_dangerous_true_fields: string[];
        robot_control_executed: boolean;
      };
      expect(stopResponse.status).toBe(502);
      expect(stopBody.proxy_status).toBe("lifecycle_failed");
      expect(stopBody.status).toBe("blocked");
      expect(stopBody.failure_reason).toBe("hard_dangerous_true_field:sends_motion_commands");
      expect(stopBody.hard_dangerous_true_fields).toEqual(expect.arrayContaining(["sends_motion_commands", "publishes_cmd_vel"]));
      expect(stopBody.hard_dangerous_true_fields).not.toContain("starts_nav2");
      expect(stopBody.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/nav2/start"]).toEqual([{}]);
      expect(upstream.receivedBodies["/api/nav2/stop"]).toEqual([{}]);
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation radar lifecycle proxy fails closed on hard dangerous fields but allows sensor sends_commands", async () => {
    // sends_commands=true 可以是传感器 lifecycle 需要；底盘/运动/UART/控制 true 字段仍必须拦截。
    const upstream = await listenRobotProofRefreshApi({
      "/api/radar/stop": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_lifecycle",
          status: "unsafe_claim",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_commands: true,
          sends_motion_commands: true,
          sends_base_motion_commands: true,
          uses_base_uart: true,
          command_result: { mode: "dry_run_stub", executed: false, ok: false },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/radar/stop?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sends_commands: false }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        status: string;
        failure_reason: string;
        hard_dangerous_true_fields: string[];
        blocked_reasons: string[];
        robot_control_executed: boolean;
      };
      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("lifecycle_failed");
      expect(body.status).toBe("blocked");
      expect(body.failure_reason).toBe("hard_dangerous_true_field:sends_motion_commands");
      expect(body.hard_dangerous_true_fields).toEqual(expect.arrayContaining([
        "sends_motion_commands",
        "sends_base_motion_commands",
        "uses_base_uart",
      ]));
      expect(body.hard_dangerous_true_fields).not.toContain("sends_commands");
      expect(body.blocked_reasons).toContain("hard_dangerous_true_field:sends_motion_commands");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/radar/stop"]).toEqual([{}]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation map lifecycle proxies use fixed endpoints and whitelist short request body fields", async () => {
    // lifecycle 代理覆盖 list/save/start/reset 四条固定路径，不接受任意 body 字段或动态 endpoint。
    const upstream = await listenRobotMapLifecycleApi({
      "/api/map/list": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_list_result",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          map_count: 2,
          maps: [
            { name: "floor_1.yaml", quality: { checked: true, ok: true, cell_counts: { free: 0, unknown: 100, occupied: 2 }, has_free_cells: false } },
            { name: "floor_1.pgm" },
          ],
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
        },
      },
      "/api/map/preview": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_preview_result",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          map_name: "floor_1",
          map_yaml_name: "floor_1.yaml",
          map_image_name: "floor_1.pgm",
          width: 1,
          height: 1,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 1, unknown: 0, occupied: 0, other: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_mime_type: "image/png",
          image_data_url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lJK3GQAAAABJRU5ErkJggg==",
          source_image_format: "pgm_p5",
          command_result: { mode: "read_only_local_files", executed: false, ok: true },
        },
      },
      "/api/localize/proof/latest": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.localize_proof",
          status: "amcl_pose_observed",
          safe_to_control: false,
          robot_control_executed: false,
          amcl_pose: { x: 0.4, y: -0.2, yaw: 0.1, frame_id: "map", source: "/amcl_pose" },
        },
      },
      "/api/nav2/status": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "planner_server_active",
          safe_to_control: false,
          robot_control_executed: false,
          path_preview_points: [
            { x: 0.1, y: 0.2, frame_id: "map", source_index: 0 },
            { x: 0.4, y: 0.2, frame_id: "map", source_index: 7 },
          ],
          path_preview_point_count: 2,
          path_preview_source_point_count: 18,
          path_preview_frame_id: "map",
        },
      },
      "/api/nav2/proof/latest": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof",
          status: "path_generated",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/free-roam/autonomy/latest": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_latest",
          status: "loaded",
          safe_to_control: false,
          robot_control_executed: false,
          latest_result: {
            snapshot: {},
          },
        },
      },
      "/api/radar/status": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "fresh",
          safe_to_control: false,
          robot_control_executed: false,
          scan_preview_points: [
            { x_m: 1.2, y_m: 0.3, range_m: 1.24, angle_rad: 0.245, frame_id: "laser_frame", source_index: 7 },
          ],
          scan_preview_source_point_count: 65,
        },
      },
      "/api/radar/scan-proof/latest": {
        method: "GET",
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof",
          status: "scan_once_observed",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/map/save": {
        method: "POST",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_result",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          map_count: 2,
          command_result: { mode: "software_guard_command_not_configured", executed: false, ok: false },
        },
      },
      "/api/map/start": {
        method: "POST",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_result",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          command_result: { mode: "software_guard_command_not_configured", executed: false, ok: false },
        },
      },
      "/api/map/reset": {
        method: "POST",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_result",
          status: "software_guard",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          command_result: { mode: "software_guard_command_not_configured", executed: false, ok: false },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const listResponse = await fetch(`${workstation.baseUrl}/api/robot-control/map/list?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const listBody = (await listResponse.json()) as {
        proxy_status: string;
        remote_endpoint: string;
        remote_method: string;
        map_count: number;
        map_names: string[];
        map_quality_summary: { status: string; no_free_cell_map_count: number };
        map_usable_for_navigation: boolean;
        map_needs_rebuild: boolean;
        robot_control_executed: boolean;
      };
      expect(listResponse.status).toBe(200);
      expect(listBody.proxy_status).toBe("lifecycle_forwarded");
      expect(listBody.remote_endpoint).toBe("/api/map/list");
      expect(listBody.remote_method).toBe("GET");
      expect(listBody.map_count).toBe(2);
      expect(listBody.map_names).toEqual(["floor_1.yaml", "floor_1.pgm"]);
      expect(listBody.map_quality_summary.status).toBe("no_free_cells");
      expect(listBody.map_quality_summary.no_free_cell_map_count).toBe(1);
      expect(listBody.map_usable_for_navigation).toBe(false);
      expect(listBody.map_needs_rebuild).toBe(true);
      expect(listBody.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/map/list"]);

      const previewResponse = await fetch(`${workstation.baseUrl}/api/robot-control/map/preview?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const previewBody = (await previewResponse.json()) as {
        proxy_status: string;
        remote_endpoint: string;
        image_mime_type: string;
        image_data_url: string;
        robot_control_executed: boolean;
        safe_to_control: boolean;
        plain_hint: string;
        map_plain_hint: string;
        map_next_action_plain: string;
        map_wysiwyg_status_plain: string;
        map_wysiwyg_next_action_plain: string;
        robot_pose: { x: number; y: number; yaw: number | null; frame_id: string; source: string } | null;
        robot_pose_status: string;
        path_preview_points: Array<{ x: number; y: number; frame_id: string; source_index: number | null }>;
        path_preview_status: string;
        path_preview_next_action_plain: string;
        next_action_plain: string;
        path_wysiwyg_status_plain: string;
        path_wysiwyg_next_action_plain: string;
        nav2_route_overlay_status: string;
        nav2_route_overlay_point_count: number;
        nav2_route_overlay_next_action_plain: string;
        path_preview_point_count: number;
        path_preview_source_point_count: number | null;
        path_preview_frame_id: string;
        path_preview_source_endpoint_ids: string[];
        radar_overlay: {
          overlay_status: string;
          status: string;
          plain_hint: string;
          next_action: string;
          scan_preview_point_count: number;
          scan_preview_source_point_count: number | null;
          scan_preview_frame_id: string;
          scan_preview_points: Array<{ x_m: number; y_m: number; frame_id: string }>;
          count: number;
          source_count: number | null;
          frame_id: string;
          source_frame_id: string;
          points: Array<{ x_m: number; y_m: number; frame_id: string }>;
          robot_pose: { x: number; y: number; yaw: number | null; frame_id: string; source: string } | null;
          source_endpoint_ids: string[];
          blocked_reasons: string[];
          blocked_reason_labels: string[];
        };
        radar_overlay_point_count: number;
        radar_overlay_current_point_count: number;
        radar_overlay_source_point_count: number | null;
        radar_overlay_refresh_required: boolean;
        radar_overlay_stale_source_points_suppressed: boolean;
        radar_overlay_primary_blocked_reason: string;
        radar_overlay_current_vs_source_plain: string;
        radar_overlay_scan_preview_point_count: number;
        radar_overlay_scan_preview_source_point_count: number | null;
        radar_overlay_frame_id: string;
        radar_overlay_source_frame_id: string;
      };
      expect(previewResponse.status).toBe(200);
      expect(previewBody.proxy_status).toBe("preview_forwarded");
      expect(previewBody.remote_endpoint).toBe("/api/map/preview");
      expect(previewBody.image_mime_type).toBe("image/png");
      expect(previewBody.image_data_url).toContain("data:image/png;base64,");
      expect(previewBody.robot_control_executed).toBe(false);
      expect(previewBody.safe_to_control).toBe(false);
      expect(previewBody.robot_pose).toEqual(expect.objectContaining({ x: 0.4, y: -0.2, frame_id: "map", source: "/amcl_pose" }));
      expect(previewBody.robot_pose_status).toBe("map_pose_observed");
      expect(previewBody.plain_hint).toContain("地图画面、图上路线、小车位置都已按当前读数显示");
      expect(previewBody.plain_hint).toContain("地图雷达点已按当前读数显示：当前显示");
      expect(previewBody.plain_hint).not.toContain("雷达 marker");
      expect(previewBody.plain_hint).not.toContain("overlay");
      expect(previewBody.map_plain_hint).toBe("地图画面、图上路线、小车位置都已按当前读数显示。");
      expect(previewBody.map_plain_hint).not.toContain("雷达 marker");
      expect(previewBody.map_next_action_plain).toBe(previewBody.map_wysiwyg_next_action_plain);
      expect(previewBody.map_wysiwyg_status_plain).toBe("地图画面、图上路线、小车位置和雷达标记都已按当前读数显示。");
      expect(previewBody.map_wysiwyg_next_action_plain).toBe("继续按当前地图画面确认路线和雷达层。");
      expect(previewBody.path_preview_status).toBe("path_preview_observed");
      expect(previewBody.path_preview_next_action_plain).toBe("图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。");
      expect(previewBody.next_action_plain).toBe(previewBody.path_preview_next_action_plain);
      expect(previewBody.path_wysiwyg_status_plain).toBe("图上路线已显示在当前地图画面。");
      expect(previewBody.path_wysiwyg_next_action_plain).toBe(previewBody.path_preview_next_action_plain);
      expect(previewBody.nav2_route_overlay_status).toBe(previewBody.path_preview_status);
      expect(previewBody.nav2_route_overlay_point_count).toBe(previewBody.path_preview_point_count);
      expect(previewBody.nav2_route_overlay_next_action_plain).toBe(previewBody.path_preview_next_action_plain);
      expect(previewBody.path_preview_points).toEqual([
        { x: 0.1, y: 0.2, frame_id: "map", source_index: 0 },
        { x: 0.4, y: 0.2, frame_id: "map", source_index: 7 },
      ]);
      expect(previewBody.path_preview_point_count).toBe(2);
      expect(previewBody.path_preview_source_point_count).toBe(18);
      expect(previewBody.path_preview_frame_id).toBe("map");
      expect(previewBody.path_preview_source_endpoint_ids).toEqual([
        "localize_proof_latest",
        "nav2_status",
        "nav2_proof_latest",
        "free_roam_autonomy_latest",
        "radar_status",
        "radar_scan_proof_latest",
      ]);
      expect(previewBody.radar_overlay.overlay_status).toBe("loaded");
      expect(previewBody.radar_overlay.status).toBe("loaded");
      expect(previewBody.radar_overlay.plain_hint).toBe("雷达点已按当前扫描和小车地图位置贴到地图。");
      expect(previewBody.radar_overlay.next_action).toBe("continue_monitoring_map_radar_overlay");
      expect(previewBody.radar_overlay.scan_preview_point_count).toBe(1);
      expect(previewBody.radar_overlay.scan_preview_source_point_count).toBe(65);
      expect(previewBody.radar_overlay.scan_preview_frame_id).toBe("laser_frame");
      expect(previewBody.radar_overlay.scan_preview_points[0]).toEqual(expect.objectContaining({ x_m: 1.2, y_m: 0.3, frame_id: "laser_frame" }));
      expect(previewBody.radar_overlay.count).toBe(1);
      expect(previewBody.radar_overlay.source_count).toBe(65);
      expect(previewBody.radar_overlay.frame_id).toBe("laser_frame");
      expect(previewBody.radar_overlay.source_frame_id).toBe("laser_frame");
      expect(previewBody.radar_overlay_point_count).toBe(1);
      expect(previewBody.radar_overlay_current_point_count).toBe(1);
      expect(previewBody.radar_overlay_source_point_count).toBe(65);
      expect(previewBody.radar_overlay_refresh_required).toBe(false);
      expect(previewBody.radar_overlay_stale_source_points_suppressed).toBe(false);
      expect(previewBody.radar_overlay_primary_blocked_reason).toBe("none");
      expect(previewBody.radar_overlay_current_vs_source_plain).toBe("地图雷达点：当前 1 个，来源 65 个；下一步：继续观察地图雷达层。");
      expect(previewBody.radar_overlay_scan_preview_point_count).toBe(1);
      expect(previewBody.radar_overlay_scan_preview_source_point_count).toBe(65);
      expect(previewBody.radar_overlay_frame_id).toBe("laser_frame");
      expect(previewBody.radar_overlay_source_frame_id).toBe("laser_frame");
      expect(previewBody.radar_overlay.points).toEqual(previewBody.radar_overlay.scan_preview_points);
      expect(previewBody.radar_overlay.robot_pose).toEqual(expect.objectContaining({ x: 0.4, y: -0.2, frame_id: "map", source: "/amcl_pose" }));
      expect(previewBody.robot_pose).toEqual(previewBody.radar_overlay.robot_pose);
      expect(previewBody.radar_overlay.source_endpoint_ids).toEqual([
        "localize_proof_latest",
        "nav2_status",
        "nav2_proof_latest",
        "free_roam_autonomy_latest",
        "radar_status",
        "radar_scan_proof_latest",
      ]);
      expect(previewBody.radar_overlay.blocked_reasons).toEqual([]);
      expect(previewBody.radar_overlay.blocked_reason_labels).toEqual([]);
      expect(upstream.receivedGets).toEqual(expect.arrayContaining([
        "/api/map/list",
        "/api/map/preview",
        "/api/localize/proof/latest",
        "/api/nav2/status",
        "/api/nav2/proof/latest",
        "/api/free-roam/autonomy/latest",
        "/api/radar/status",
        "/api/radar/scan-proof/latest",
      ]));

      const rejected = await fetch(`${workstation.baseUrl}/api/robot-control/map/save?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ map_name: "floor_1", arbitrary_endpoint: "/api/base/manual" }),
      });
      const rejectedBody = (await rejected.json()) as { proxy_status: string; failure_reason: string };
      expect(rejected.status).toBe(400);
      expect(rejectedBody.proxy_status).toBe("lifecycle_rejected");
      expect(rejectedBody.failure_reason).toContain("request_body_unknown_fields");
      expect(upstream.receivedBodies["/api/map/save"]).toBeUndefined();

      const saveResponse = await fetch(`${workstation.baseUrl}/api/robot-control/map/save?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ map_name: "floor_1", artifact_path: "maps/floor_1.yaml" }),
      });
      const saveBody = (await saveResponse.json()) as {
        proxy_status: string;
        remote_endpoint: string;
        command_result: { mode: string; executed: boolean };
        safe_to_control: boolean;
      };
      expect(saveResponse.status).toBe(200);
      expect(saveBody.proxy_status).toBe("lifecycle_forwarded");
      expect(saveBody.remote_endpoint).toBe("/api/map/save");
      expect(saveBody.command_result.mode).toBe("software_guard_command_not_configured");
      expect(saveBody.command_result.executed).toBe(false);
      expect(saveBody.safe_to_control).toBe(false);
      expect(upstream.receivedBodies["/api/map/save"]).toEqual([
        { map_name: "floor_1", artifact_path: "maps/floor_1.yaml" },
      ]);

      const startResponse = await fetch(`${workstation.baseUrl}/api/robot-control/map/start?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ map_name: "floor_1" }),
      });
      const resetResponse = await fetch(`${workstation.baseUrl}/api/robot-control/map/reset?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artifact_path: "maps/floor_1.yaml" }),
      });
      expect(startResponse.status).toBe(200);
      expect(resetResponse.status).toBe(200);
      expect(upstream.receivedBodies["/api/map/start"]).toEqual([{ map_name: "floor_1" }]);
      expect(upstream.receivedBodies["/api/map/reset"]).toEqual([{ artifact_path: "maps/floor_1.yaml" }]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("map preview radar overlay is partial when scan points exist without map pose", async () => {
    // live 形态：地图图像和雷达点都读到了，但定位只有 TF 信号没有 map-frame pose；不能把雷达点冒充成已贴地图。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/map/preview": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_preview",
          status: "loaded",
          safe_to_control: false,
          robot_control_executed: false,
          map_name: "floor_1",
          map_yaml_name: "floor_1.yaml",
          map_image_name: "floor_1.pgm",
          width: 20,
          height: 10,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 10, unknown: 0, occupied: 0, other: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_mime_type: "image/png",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "pose_signal_observed_without_map_coordinates",
          safe_to_control: false,
          robot_control_executed: false,
          amcl_pose_observed: false,
          localization_tf_observed: true,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "fresh",
          safe_to_control: false,
          robot_control_executed: false,
          scan_preview_points: [
            { x_m: 0.8, y_m: 0.1, range_m: 0.81, angle_rad: 0.12, frame_id: "laser_frame", source_index: 3 },
          ],
          scan_preview_source_point_count: 65,
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof",
          status: "scan_once_observed",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/map/preview?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        image_data_url: string;
        plain_hint: string;
        map_plain_hint: string;
        map_next_action_plain: string;
        map_wysiwyg_status_plain: string;
        map_wysiwyg_next_action_plain: string;
        radar_overlay_status: string;
        radar_overlay_plain_hint: string;
        radar_overlay_wysiwyg_status_plain: string;
        radar_overlay_wysiwyg_next_action_plain: string;
        radar_overlay_next_action: string;
        radar_overlay_next_action_plain: string;
        radar_overlay_count: number;
        radar_overlay_current_point_count: number;
        radar_overlay_source_count: number | null;
        radar_overlay_needs_refresh: boolean;
        radar_overlay_blocks_wysiwyg: boolean;
        radar_overlay_blocks_free_move: boolean;
        radar_overlay_recovery_sequence: string[];
        fixed_radar_overlay_refresh_endpoint: string;
        fixed_radar_overlay_map_preview_endpoint: string;
        radar_overlay_refresh_sends_motion: boolean;
        radar_overlay_refresh_starts_radar_lifecycle: boolean;
        radar_overlay_frame_id: string;
        radar_overlay_source_frame_id: string;
        radar_overlay_points: Array<{ x_m: number; y_m: number; frame_id: string }>;
        radar_overlay: {
          overlay_status: string;
          plain_hint: string;
          wysiwyg_status_plain: string;
          wysiwyg_next_action_plain: string;
          next_action: string;
          next_action_plain: string;
          scan_preview_point_count: number;
          scan_preview_points: Array<{ x_m: number; y_m: number; frame_id: string }>;
          robot_pose: null | { frame_id: string };
          blocked_reasons: string[];
          blocked_reason_labels: string[];
        };
        robot_pose_status: string;
        path_preview_status: string;
        path_preview_next_action_plain: string;
        next_action_plain: string;
        path_wysiwyg_status_plain: string;
        path_wysiwyg_next_action_plain: string;
        nav2_route_overlay_status: string;
        nav2_route_overlay_point_count: number;
        nav2_route_overlay_next_action_plain: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("preview_forwarded");
      expect(body.image_data_url).toContain("data:image/png;base64,");
      expect(body.plain_hint).toContain(body.map_wysiwyg_status_plain.replace(/[。.!?]+$/, ""));
      expect(body.plain_hint).toContain("地图雷达点未完整显示：当前显示 1 个点，来源点 65 个");
      expect(body.plain_hint).toContain("原因：小车地图位置未读到");
      expect(body.plain_hint).not.toContain("雷达 marker");
      expect(body.plain_hint).not.toContain("overlay");
      expect(body.map_plain_hint).toBe(body.map_wysiwyg_status_plain);
      expect(body.map_next_action_plain).toBe(body.map_wysiwyg_next_action_plain);
      expect(body.map_wysiwyg_status_plain).toBe("地图画面已读到，但图上路线还未显示。");
      expect(body.map_wysiwyg_next_action_plain).toBe("先准备图上路线，再刷新地图画面。");
      expect(body.radar_overlay.overlay_status).toBe("partial");
      expect(body.radar_overlay.plain_hint).toContain("小车地图位置未读到");
      expect(body.radar_overlay.wysiwyg_status_plain).toBe("雷达材料已读到 65 个来源点，当前可用雷达点 1 个，但地图贴图未完整确认；已有雷达来源点 65 个，但小车地图位置未读到；当前不能把雷达点贴到地图坐标。");
      expect(body.radar_overlay.wysiwyg_next_action_plain).toBe("先刷新定位，再刷新雷达扫描和地图画面。");
      expect(body.radar_overlay.next_action).toBe("refresh_localization_then_radar_scan");
      expect(body.radar_overlay.next_action_plain).toBe("先刷新定位，再刷新雷达扫描和地图画面。");
      expect(body.radar_overlay.scan_preview_point_count).toBe(1);
      expect(body.radar_overlay.scan_preview_points[0]).toEqual(expect.objectContaining({ x_m: 0.8, y_m: 0.1, frame_id: "laser_frame" }));
      expect(body.radar_overlay_status).toBe(body.radar_overlay.overlay_status);
      expect(body.radar_overlay_plain_hint).toBe(body.radar_overlay.plain_hint);
      expect(body.radar_overlay_wysiwyg_status_plain).toBe(body.radar_overlay.wysiwyg_status_plain);
      expect(body.radar_overlay_wysiwyg_next_action_plain).toBe(body.radar_overlay.wysiwyg_next_action_plain);
      expect(body.radar_overlay_next_action).toBe(body.radar_overlay.next_action);
      expect(body.radar_overlay_next_action_plain).toBe(body.radar_overlay.next_action_plain);
      expect(body.radar_overlay_count).toBe(body.radar_overlay.scan_preview_point_count);
      expect(body.radar_overlay_points[0]).toEqual(expect.objectContaining({ x_m: 0.8, y_m: 0.1, frame_id: "laser_frame" }));
      expect(body.radar_overlay_source_count).toBe(65);
      expect(body.radar_overlay_frame_id).toBe("laser_frame");
      expect(body.radar_overlay.robot_pose).toBeNull();
      expect(body.robot_pose_status).toBe("not_observed");
      expect(body.path_preview_status).toBe("not_observed");
      expect(body.path_preview_next_action_plain).toBe("先准备图上路线，再刷新地图画面。");
      expect(body.next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.path_wysiwyg_status_plain).toBe("图上路线未显示；不能把旧路线或空路线当作当前所见。");
      expect(body.path_wysiwyg_next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.nav2_route_overlay_status).toBe(body.path_preview_status);
      expect(body.nav2_route_overlay_point_count).toBe(0);
      expect(body.nav2_route_overlay_next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.radar_overlay.blocked_reasons).toContain("robot_pose_missing_for_map_radar_overlay");
      expect(body.radar_overlay.blocked_reason_labels).toContain("小车地图位置未读到");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(expect.arrayContaining([
        "/api/map/preview",
        "/api/localize/proof/latest",
        "/api/nav2/status",
        "/api/nav2/proof/latest",
        "/api/radar/status",
        "/api/radar/scan-proof/latest",
      ]));
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("map preview radar overlay does not draw stopped stale radar points", async () => {
    // 地图预览自己也要执行雷达实时性门禁；不能只靠 summary 兜底，否则刷新地图时仍可能把旧点贴到图上。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/map/preview": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_preview",
          status: "loaded",
          safe_to_control: false,
          robot_control_executed: false,
          map_name: "floor_1",
          map_yaml_name: "floor_1.yaml",
          map_image_name: "floor_1.pgm",
          width: 20,
          height: 10,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 10, unknown: 0, occupied: 0, other: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_mime_type: "image/png",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "localization_reset_observed",
          safe_to_control: false,
          robot_control_executed: false,
          robot_pose: { x: 0.4, y: -0.2, yaw: 0.1, frame_id: "map", source: "/amcl_pose" },
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/free-roam/autonomy/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_latest",
          status: "loaded",
          safe_to_control: false,
          robot_control_executed: false,
          latest_result: {
            snapshot: {
              lidar_age_s: 14392.64,
              lidar_min_distance_m: 0.04,
            },
          },
        },
      },
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "scan_once_hz_raw_packet_tf_observed",
          safe_to_control: false,
          robot_control_executed: false,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof",
          status: "scan_once_observed",
          safe_to_control: false,
          robot_control_executed: false,
          scan_preview_points: [
            { x_m: 1.2, y_m: 0.3, range_m: 1.24, angle_rad: 0.2, frame_id: "laser_frame", source_index: 3 },
            { x_m: 0.8, y_m: 0.1, range_m: 0.81, angle_rad: 0.12, frame_id: "laser_frame", source_index: 4 },
          ],
          scan_preview_point_count: 2,
          scan_preview_source_point_count: 65,
          scan_preview_frame_id: "laser_frame",
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/map/preview?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        plain_hint: string;
        map_plain_hint: string;
        map_next_action_plain: string;
        map_wysiwyg_status_plain: string;
        map_wysiwyg_next_action_plain: string;
        radar_overlay_status: string;
        radar_overlay_plain_hint: string;
        radar_overlay_wysiwyg_status_plain: string;
        radar_overlay_wysiwyg_next_action_plain: string;
        radar_overlay_next_action: string;
        radar_overlay_next_action_plain: string;
        radar_overlay_count: number;
        radar_overlay_current_point_count: number;
        radar_overlay_source_count: number | null;
        radar_overlay_needs_refresh: boolean;
        radar_overlay_blocks_wysiwyg: boolean;
        radar_overlay_blocks_free_move: boolean;
        radar_overlay_recovery_sequence: string[];
        fixed_radar_overlay_refresh_endpoint: string;
        fixed_radar_overlay_map_preview_endpoint: string;
        radar_overlay_refresh_sends_motion: boolean;
        radar_overlay_refresh_starts_radar_lifecycle: boolean;
        radar_overlay_frame_id: string;
        radar_overlay_source_frame_id: string;
        radar_overlay_points: Array<{ x_m: number; y_m: number; frame_id: string }>;
        radar_overlay: {
          overlay_status: string;
          status: string;
          plain_hint: string;
          wysiwyg_status_plain: string;
          wysiwyg_next_action_plain: string;
          next_action: string;
          next_action_plain: string;
          scan_preview_point_count: number;
          scan_preview_source_point_count: number | null;
          scan_preview_frame_id: string;
          scan_preview_points: Array<{ x_m: number; y_m: number; frame_id: string }>;
          count: number;
          source_count: number | null;
          frame_id: string;
          source_frame_id: string;
          points: Array<{ x_m: number; y_m: number; frame_id: string }>;
          blocked_reasons: string[];
          blocked_reason_labels: string[];
        };
        robot_pose_status: string;
        path_preview_status: string;
        path_preview_next_action_plain: string;
        next_action_plain: string;
        path_wysiwyg_status_plain: string;
        path_wysiwyg_next_action_plain: string;
        nav2_route_overlay_status: string;
        nav2_route_overlay_point_count: number;
        nav2_route_overlay_next_action_plain: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("preview_forwarded");
      expect(body.plain_hint).toContain(body.map_wysiwyg_status_plain.replace(/[。.!?]+$/, ""));
      expect(body.plain_hint).toContain("地图雷达点当前显示 0 个，旧来源点 65 个只作诊断");
      expect(body.plain_hint).toContain("原因：雷达扫描已过期、雷达未运行");
      expect(body.plain_hint).not.toContain("雷达 marker");
      expect(body.plain_hint).not.toContain("overlay");
      expect(body.map_plain_hint).toBe(body.map_wysiwyg_status_plain);
      expect(body.map_next_action_plain).toBe(body.map_wysiwyg_next_action_plain);
      expect(body.map_wysiwyg_status_plain).toBe("地图画面已读到，但图上路线还未显示。");
      expect(body.map_wysiwyg_next_action_plain).toBe("先准备图上路线，再刷新地图画面。");
      expect(body.radar_overlay.overlay_status).toBe("not_current");
      expect(body.radar_overlay.status).toBe("not_current");
      expect(body.radar_overlay.plain_hint).toContain("已有雷达来源点 65 个");
      expect(body.radar_overlay.plain_hint).toContain("当前不贴到地图");
      expect(body.radar_overlay.wysiwyg_status_plain).toBe("雷达点未贴到当前地图：当前显示 0 个点；旧来源点 65 个只作诊断。已有雷达来源点 65 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。");
      expect(body.radar_overlay.wysiwyg_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_overlay.next_action).toBe("start_radar_then_refresh_map_preview");
      expect(body.radar_overlay.next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_overlay.scan_preview_point_count).toBe(0);
      expect(body.radar_overlay.scan_preview_points).toEqual([]);
      expect(body.radar_overlay.scan_preview_source_point_count).toBe(65);
      expect(body.radar_overlay.scan_preview_frame_id).toBe("laser_frame");
      expect(body.radar_overlay.count).toBe(0);
      expect(body.radar_overlay.points).toEqual([]);
      expect(body.radar_overlay.source_count).toBe(65);
      expect(body.radar_overlay.frame_id).toBe("");
      expect(body.radar_overlay.source_frame_id).toBe("laser_frame");
      expect(body.radar_overlay_status).toBe(body.radar_overlay.overlay_status);
      expect(body.radar_overlay_plain_hint).toBe(body.radar_overlay.plain_hint);
      expect(body.radar_overlay_wysiwyg_status_plain).toBe(body.radar_overlay.wysiwyg_status_plain);
      expect(body.radar_overlay_wysiwyg_next_action_plain).toBe(body.radar_overlay.wysiwyg_next_action_plain);
      expect(body.radar_overlay_next_action).toBe(body.radar_overlay.next_action);
      expect(body.radar_overlay_next_action_plain).toBe(body.radar_overlay.next_action_plain);
      expect(body.radar_overlay_count).toBe(0);
      expect(body.radar_overlay_current_point_count).toBe(0);
      expect(body.radar_overlay_points).toEqual([]);
      expect(body.radar_overlay_source_count).toBe(65);
      expect(body.radar_overlay_needs_refresh).toBe(true);
      expect(body.radar_overlay_blocks_wysiwyg).toBe(true);
      expect(body.radar_overlay_blocks_free_move).toBe(false);
      expect(body.radar_overlay_recovery_sequence).toEqual([
        "/api/robot-control/radar/scan-proof/refresh",
        "/api/robot-control/map/preview",
      ]);
      expect(body.fixed_radar_overlay_refresh_endpoint).toBe("/api/robot-control/radar/scan-proof/refresh");
      expect(body.fixed_radar_overlay_map_preview_endpoint).toBe("/api/robot-control/map/preview");
      expect(body.radar_overlay_refresh_sends_motion).toBe(false);
      expect(body.radar_overlay_refresh_starts_radar_lifecycle).toBe(false);
      expect(body.radar_overlay_frame_id).toBe("");
      expect(body.radar_overlay_source_frame_id).toBe("laser_frame");
      expect(body.radar_overlay.blocked_reasons).toContain("runtime_scan_stale_for_map_radar_overlay");
      expect(body.radar_overlay.blocked_reasons).toContain("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(body.radar_overlay.blocked_reason_labels).toContain("雷达扫描已过期");
      expect(body.radar_overlay.blocked_reason_labels).toContain("雷达未运行");
      expect(body.robot_pose_status).toBe("map_pose_observed");
      expect(body.path_preview_status).toBe("not_observed");
      expect(body.path_preview_next_action_plain).toBe("先准备图上路线，再刷新地图画面。");
      expect(body.next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.path_wysiwyg_status_plain).toBe("图上路线未显示；不能把旧路线或空路线当作当前所见。");
      expect(body.path_wysiwyg_next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.nav2_route_overlay_status).toBe(body.path_preview_status);
      expect(body.nav2_route_overlay_point_count).toBe(0);
      expect(body.nav2_route_overlay_next_action_plain).toBe(body.path_preview_next_action_plain);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(expect.arrayContaining([
        "/api/map/preview",
        "/api/free-roam/autonomy/latest",
        "/api/radar/status",
        "/api/radar/scan-proof/latest",
      ]));
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("map preview radar overlay is not loaded when pose exists but radar has no current points", async () => {
    // 只有 map pose 不能让雷达层变成 partial；没有新雷达点时地图应明确显示 0 个当前雷达点。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/map/preview": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_preview",
          status: "loaded",
          safe_to_control: false,
          robot_control_executed: false,
          map_name: "floor_1",
          map_yaml_name: "floor_1.yaml",
          map_image_name: "floor_1.pgm",
          width: 20,
          height: 10,
          resolution: 0.05,
          origin: [0, 0, 0],
          cell_counts: { free: 10, unknown: 0, occupied: 0, other: 0 },
          has_free_cells: true,
          navigation_quality: "has_free_cells",
          image_mime_type: "image/png",
          image_data_url: "data:image/png;base64,abc",
          source_image_format: "pgm_p5",
        },
      },
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_proof_latest",
          status: "localization_reset_observed",
          safe_to_control: false,
          robot_control_executed: false,
          robot_pose: { x: 0.4, y: -0.2, yaw: 0.1, frame_id: "map", source: "/amcl_pose" },
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof",
          status: "not_proven",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          status: "radar_stopped",
          safe_to_control: false,
          robot_control_executed: false,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          latest_scan_proof_fresh: false,
        },
      },
      "/api/radar/scan-proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_scan_proof",
          status: "not_loaded",
          safe_to_control: false,
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/map/preview?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        radar_overlay_status: string;
        radar_overlay_count: number;
        radar_overlay_source_count: number | null;
        radar_overlay_refresh_required: boolean;
        radar_overlay_stale_source_points_suppressed: boolean;
        radar_overlay_primary_blocked_reason: string;
        radar_overlay_current_vs_source_plain: string;
        radar_overlay_wysiwyg_status_plain: string;
        radar_overlay_next_action_plain: string;
        radar_overlay: {
          overlay_status: string;
          count: number;
          source_count: number | null;
          refresh_required: boolean;
          stale_source_points_suppressed: boolean;
          primary_blocked_reason: string;
          current_vs_source_plain: string;
          blocked_reasons: string[];
          blocked_reason_labels: string[];
        };
        robot_pose_status: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("preview_forwarded");
      expect(body.robot_pose_status).toBe("map_pose_observed");
      expect(body.radar_overlay_status).toBe("not_loaded");
      expect(body.radar_overlay.overlay_status).toBe("not_loaded");
      expect(body.radar_overlay_count).toBe(0);
      expect(body.radar_overlay.count).toBe(0);
      expect(body.radar_overlay_source_count).toBeNull();
      expect(body.radar_overlay.source_count).toBeNull();
      expect(body.radar_overlay_refresh_required).toBe(true);
      expect(body.radar_overlay.refresh_required).toBe(true);
      expect(body.radar_overlay_stale_source_points_suppressed).toBe(false);
      expect(body.radar_overlay.stale_source_points_suppressed).toBe(false);
      expect(body.radar_overlay_primary_blocked_reason).toBe("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(body.radar_overlay.primary_blocked_reason).toBe("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(body.radar_overlay_current_vs_source_plain).toBe("地图雷达点：当前 0 个，来源 not_loaded 个；下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_overlay.current_vs_source_plain).toBe(body.radar_overlay_current_vs_source_plain);
      expect(body.radar_overlay_wysiwyg_status_plain).toContain("当前显示 0 个点");
      expect(body.radar_overlay_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_overlay.blocked_reasons).toContain("scan_preview_points_missing_for_map_radar_overlay");
      expect(body.radar_overlay.blocked_reasons).toContain("radar_lifecycle_not_running_for_map_radar_overlay");
      expect(body.radar_overlay.blocked_reason_labels).toContain("没有可贴图的新雷达点");
      expect(body.radar_overlay.blocked_reason_labels).toContain("雷达未运行");
      expect(body.robot_control_executed).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("radar status proxy exposes top-level lifecycle and map-marker guidance", async () => {
    // 独立雷达状态页只证明雷达本体；地图 marker 所见即所得仍要指向 map preview 的 overlay 计数。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          evidence_ref: "o1-lidar-scan-proof-test",
          latest_evidence_ref: "o1-lidar-scan-proof-test",
          scan_status: "not_proven",
          continuous_scan_status: "lifecycle_not_running",
          continuity_window_status: "lifecycle_not_running",
          continuous_window_observed: false,
          lifecycle_running: false,
          lifecycle_state: "stopped",
          lifecycle_status: "lifecycle_not_running",
          latest_scan_proof_fresh: false,
          scan_point_count: 81,
          latest_scan_age_ms: 12000,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/radar/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        radar_key_values: Record<string, string>;
        continuous_scan_status: string;
        lifecycle_running: string;
        lifecycle_state: string;
        latest_scan_proof_fresh: string;
        scan_point_count: string;
        latest_scan_age_ms: string;
        plain_hint: string;
        next_action_plain: string;
        radar_status_plain: string;
        radar_next_action_plain: string;
        radar_scan_required_observations: string;
        radar_scan_observation_status: string;
        radar_scan_observation_missing_reasons: string;
        radar_scan_ready_for_map_overlay: string;
        radar_overlay_ready_for_map: string;
        radar_map_overlay_readiness_status: string;
        radar_map_overlay_next_action_plain: string;
        radar_overlay_point_count: string;
        radar_overlay_source_point_count: string;
        radar_overlay_wysiwyg_status_plain: string;
        radar_overlay_wysiwyg_next_action_plain: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("status_loaded");
      expect(body.radar_key_values.continuous_scan_status).toBe("lifecycle_not_running");
      expect(body.continuous_scan_status).toBe("lifecycle_not_running");
      expect(body.lifecycle_running).toBe("false");
      expect(body.lifecycle_state).toBe("stopped");
      expect(body.latest_scan_proof_fresh).toBe("false");
      expect(body.scan_point_count).toBe("81");
      expect(body.latest_scan_age_ms).toBe("12000");
      expect(body.plain_hint).toBe("雷达未运行或扫描已停；旧雷达来源点不能当作当前地图雷达点。下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.next_action_plain).toBe(body.radar_next_action_plain);
      expect(body.plain_hint).not.toContain("marker");
      expect(body.plain_hint).not.toContain("overlay");
      expect(body.radar_status_plain).toBe("雷达未运行或扫描已停；旧雷达来源点不能当作当前地图雷达点。");
      expect(body.radar_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_scan_required_observations).toBe("scan_once,scan_hz,raw_packet_once");
      expect(body.radar_scan_observation_status).toBe("missing_required_observations");
      expect(body.radar_scan_observation_missing_reasons).toBe("scan_once,scan_hz,raw_packet_once");
      expect(body.radar_scan_ready_for_map_overlay).toBe("false");
      expect(body.radar_overlay_ready_for_map).toBe("false");
      expect(body.radar_map_overlay_readiness_status).toBe("blocked_radar_lifecycle_not_running");
      expect(body.radar_map_overlay_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.radar_overlay_point_count).toBe("not_loaded");
      expect(body.radar_overlay_source_point_count).toBe("81");
      expect(body.radar_overlay_wysiwyg_status_plain).toBe("雷达 status 不直接绘制地图雷达点；雷达未运行或扫描已停；旧雷达来源点不能当作当前地图雷达点。");
      expect(body.radar_overlay_wysiwyg_next_action_plain).toBe("先启动雷达并等待新扫描，再刷新地图画面确认雷达点。");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/radar/status"]);
      expect(Object.keys(upstream.receivedBodies)).toEqual([]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("radar status proxy names missing scan observations before map overlay can draw", async () => {
    // 现场常见形态是 lifecycle running 但最新 proof 缺 scan/hz/raw packet；PC 必须直接说明缺口。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/radar/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.radar_status",
          evidence_ref: "o1-lidar-scan-proof-running-incomplete",
          latest_evidence_ref: "o1-lidar-scan-proof-running-incomplete",
          scan_status: "not_proven",
          continuous_scan_status: "latest_proof_incomplete_while_lifecycle_running",
          continuity_window_status: "latest_proof_incomplete_while_lifecycle_running",
          continuous_window_observed: false,
          lifecycle_running: true,
          lifecycle_state: "running",
          lifecycle_status: "latest_proof_incomplete_while_lifecycle_running",
          latest_scan_proof_fresh: false,
          scan_once_observed: false,
          scan_hz_observed: false,
          raw_packet_once_observed: false,
          scan_point_count: 0,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/radar/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        radar_scan_observation_status: string;
        radar_scan_observation_missing_reasons: string;
        radar_scan_ready_for_map_overlay: string;
        radar_overlay_ready_for_map: string;
        radar_map_overlay_readiness_status: string;
        radar_map_overlay_next_action_plain: string;
        radar_overlay_wysiwyg_next_action_plain: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.radar_scan_observation_status).toBe("missing_required_observations");
      expect(body.radar_scan_observation_missing_reasons).toBe("scan_once,scan_hz,raw_packet_once");
      expect(body.radar_scan_ready_for_map_overlay).toBe("false");
      expect(body.radar_overlay_ready_for_map).toBe("false");
      expect(body.radar_map_overlay_readiness_status).toBe("blocked_missing_scan_observations");
      expect(body.radar_map_overlay_next_action_plain).toBe("先补齐雷达扫描材料：没有读到一帧雷达、雷达频率未确认、雷达原始包未确认；有新扫描后再刷新地图画面。");
      expect(body.radar_map_overlay_next_action_plain).not.toContain("raw_packet_once");
      expect(body.radar_overlay_wysiwyg_next_action_plain).toBe(body.radar_map_overlay_next_action_plain);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/radar/status"]);
      expect(Object.keys(upstream.receivedBodies)).toEqual([]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation map lifecycle proxy forwards safe executed no-motion helper results", async () => {
    // executed=true 只代表受控 no-motion helper 跑过；只要无危险字段和远端 failure，代理应通过。
    const upstream = await listenRobotMapLifecycleApi({
      "/api/map/save": {
        method: "POST",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_result",
          status: "map_once_artifact_metadata_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_motion_commands: false,
          sends_base_motion_commands: false,
          publishes_cmd_vel: false,
          calls_base_manual: false,
          uses_base_uart: false,
          failure_reason: null,
          command_result: { mode: "map_lifecycle_proof_helper", executed: true, ok: true },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/map/save?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ map_name: "floor_1" }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        status: string;
        command_result: { executed: boolean; ok: boolean };
        blocked_reasons: string[];
        robot_control_executed: boolean;
      };
      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("lifecycle_forwarded");
      expect(body.status).toBe("loaded_fail_closed_summary");
      expect(body.command_result.executed).toBe(true);
      expect(body.command_result.ok).toBe(true);
      expect(body.blocked_reasons).toEqual([]);
      expect(body.robot_control_executed).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation map lifecycle proxy fails closed on dangerous true fields", async () => {
    // 上位机如果声称危险 true，PC 端仍保持 blocked/not_proven 合同。
    const upstream = await listenRobotMapLifecycleApi({
      "/api/map/save": {
        method: "POST",
        payload: {
          schema: "trashbot.upper_robot_api.v1.map_lifecycle_result",
          status: "unexpected_success",
          safe_to_control: true,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          command_result: { mode: "configured_command", executed: true, ok: true },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/map/save?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        status: string;
        hard_dangerous_true_fields: string[];
        blocked_reasons: string[];
        robot_control_executed: boolean;
      };
      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("lifecycle_failed");
      expect(body.status).toBe("blocked");
      expect(body.hard_dangerous_true_fields).toContain("safe_to_control");
      expect(body.blocked_reasons).toEqual(expect.arrayContaining([
        "hard_dangerous_true_field:safe_to_control",
      ]));
      expect(body.robot_control_executed).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("computes refresh timeout budgets from the fixed body and caps them", () => {
    // timeout 由 body 预估时长加余量推导，不再用拍脑袋的固定 15s / 50s。
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 12 },
        timeout_cap_ms: 120_000,
        safety_margin_ms: 78_000,
      }),
    ).toBe(90_000);
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 45 },
        timeout_cap_ms: 120_000,
        safety_margin_ms: 20_000,
      }),
    ).toBe(65_000);
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 30, managed_runtime_opt_in: true, managed_timeout_s: 30, path_generation_timeout_s: 30 },
        timeout_cap_ms: 150_000,
        safety_margin_ms: 60_000,
      }),
    ).toBe(150_000);
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 30, managed_runtime_opt_in: true, managed_timeout_s: 30, path_generation_opt_in: false },
        timeout_cap_ms: 120_000,
        safety_margin_ms: 60_000,
      }),
    ).toBe(120_000);
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 999, runtime_warmup_s: 999 },
        timeout_cap_ms: 60_000,
        safety_margin_ms: 10_000,
      }),
    ).toBe(60_000);
    expect(
      computeRobotProofRefreshTimeoutMs({
        request_body: { timeout_s: 999 },
        timeout_cap_ms: 120_000,
        safety_margin_ms: 20_000,
      }),
    ).toBe(120_000);
  });

  it("reports the computed fetch timeout ms when radar refresh hangs", async () => {
    // 这里不靠真实等待，直接断言 AbortSignal.timeout 接收到的就是计算后的毫秒数。
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout");
    const originalFetch = globalThis.fetch;
    const timeoutError = Object.assign(new Error("timeout"), { name: "TimeoutError" });
    const fetchMock = vi.fn(() => Promise.reject(timeoutError));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildRadarScanProofRefreshProxy("http://127.0.0.1:8787");
      expect(timeoutSpy).toHaveBeenCalledWith(90_000);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(response.proxy_status).toBe("refresh_failed");
      expect(response.failure_reason).toBe("fetch_timeout_90000ms");
      expect(response.blocked_reasons).toContain("fetch_timeout_90000ms");
      expect(response.safe_to_control).toBe(false);
    } finally {
      globalThis.fetch = originalFetch;
      timeoutSpy.mockRestore();
    }
  });

  it("reports the computed fetch timeout ms when map refresh hangs", async () => {
    // map 的 timeout 同样必须按 body 计算，并且封顶前后都能写出准确毫秒数。
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout");
    const originalFetch = globalThis.fetch;
    const timeoutError = Object.assign(new Error("timeout"), { name: "TimeoutError" });
    const fetchMock = vi.fn(() => Promise.reject(timeoutError));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildMapProofRefreshProxy("http://127.0.0.1:8787");
      expect(timeoutSpy).toHaveBeenCalledWith(65_000);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(response.proxy_status).toBe("refresh_failed");
      expect(response.failure_reason).toBe("fetch_timeout_65000ms");
      expect(response.blocked_reasons).toContain("fetch_timeout_65000ms");
      expect(response.safe_to_control).toBe(false);
    } finally {
      globalThis.fetch = originalFetch;
      timeoutSpy.mockRestore();
    }
  });

  it("reports the computed fetch timeout ms when Nav2 no-motion refresh hangs", async () => {
    // Nav2 no-motion 规划检查也使用固定 body 推导 timeout，避免无界等待阻塞工作站。
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout");
    const originalFetch = globalThis.fetch;
    const timeoutError = Object.assign(new Error("timeout"), { name: "TimeoutError" });
    const fetchMock = vi.fn(() => Promise.reject(timeoutError));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildNav2NoMotionProofRefreshProxy("http://127.0.0.1:8787");
      expect(timeoutSpy).toHaveBeenCalledWith(150_000);
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(response.proxy_status).toBe("refresh_failed");
      expect(response.failure_reason).toBe("fetch_timeout_150000ms");
      expect(response.blocked_reasons).toContain("fetch_timeout_150000ms");
      expect(response.safe_to_control).toBe(false);
    } finally {
      globalThis.fetch = originalFetch;
      timeoutSpy.mockRestore();
    }
  });

  it("forwards localization reset with fixed no-motion initialpose body", async () => {
    // localize/reset 是高级诊断固定代理；只能发 AMCL initialpose proof，不开放路径生成或底盘动作。
    const robotApi = await listenRobotProofRefreshApi({
      "/api/localize/reset": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          evidence_ref: "localize-reset-proof",
          initialpose_published: true,
          amcl_pose_observed: true,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          managed_runtime_started: true,
          managed_runtime_cleanup_ok: true,
          localization_reset_observed: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          sends_motion_commands: false,
          publishes_cmd_vel: false,
          calls_base_manual: false,
          uses_base_uart: false,
        },
      },
    });
    try {
      const response = await buildLocalizationResetProxy(robotApi.baseUrl);
      expect(response.proxy_status).toBe("refresh_forwarded");
      expect(response.remote_endpoint).toBe("/api/localize/reset");
      expect(response.last_result_status).toBe("localization_reset_observed");
      expect(response.latest_readback_key_values.initialpose_published).toBe("true");
      expect(response.latest_readback_key_values.amcl_pose_observed).toBe("true");
      expect(response.latest_readback_key_values.managed_runtime_started).toBe("true");
      expect(response.safe_to_control).toBe(false);
      expect(response.robot_control_executed).toBe(false);
      expect(robotApi.receivedBodies["/api/localize/reset"]).toEqual([
        {
          timeout_s: 30,
          managed_runtime_opt_in: true,
          managed_timeout_s: 30,
          initialpose_opt_in: true,
          initialpose_x: 0,
          initialpose_y: 0,
          initialpose_yaw: 0,
          initialpose_frame_id: "map",
          path_generation_opt_in: false,
        },
      ]);
    } finally {
      await robotApi.close();
    }
  });

  it("localization reset proxy rejects missing and unsafe base URLs before fetch", async () => {
    // URL 围栏和其它 Robot Control 代理一致，不能把 reset 入口扩成公网 SSRF。
    const missing = await buildLocalizationResetProxy("");
    expect(missing.proxy_status).toBe("refresh_rejected");
    expect(missing.failure_reason).toBe("baseUrl_not_provided");
    expect(missing.remote_endpoint).toBe("/api/localize/reset");
    expect(missing.safe_to_control).toBe(false);

    const unsafe = await buildLocalizationResetProxy("https://example.com/api?token=secret");
    expect(unsafe.proxy_status).toBe("refresh_rejected");
    expect(unsafe.failure_reason).toBe("baseUrl_protocol_not_allowed");
    expect(unsafe.robot_control_executed).toBe(false);
  });

  it("loads fixed Nav2 latest proof readback after no-motion POST timeout", async () => {
    // 只有 Nav2 no-motion refresh 在 POST 失败后读取固定 latest endpoint，用于表达“请求超时但 latest 已有路径证据”。
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout");
    const originalFetch = globalThis.fetch;
    const timeoutError = Object.assign(new Error("timeout"), { name: "TimeoutError" });
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(timeoutError)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
            status: "nav2_no_motion_path_generation_runtime_observed",
            latest_proof_status: "nav2_no_motion_path_generation_runtime_observed",
            evidence_ref: "nav2-latest-proof",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
            robot_control_executed: false,
            path_generation_requested: true,
            path_generated: true,
            path_generation_succeeded: true,
            path_point_count: 31,
            planner_server_active: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      const response = await buildNav2NoMotionProofRefreshProxy("http://127.0.0.1:8787");
      expect(timeoutSpy).toHaveBeenCalledWith(150_000);
      expect(timeoutSpy).toHaveBeenCalledWith(1500);
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(String(fetchMock.mock.calls[0]?.[0])).toBe("http://127.0.0.1:8787/api/nav2/proof/refresh");
      expect(String(fetchMock.mock.calls[1]?.[0])).toBe("http://127.0.0.1:8787/api/nav2/proof/latest");
      expect(response.proxy_status).toBe("refresh_failed");
      expect(response.status).toBe("blocked");
      expect(response.failure_reason).toBe("fetch_timeout_150000ms");
      expect(response.blocked_reasons).toEqual(["fetch_timeout_150000ms", "post_timeout_latest_readback_loaded"]);
      expect(response.latest_readback_key_values.path_generated).toBe("true");
      expect(response.latest_readback_key_values.path_generation_succeeded).toBe("true");
      expect(response.latest_readback_key_values.path_point_count).toBe("31");
      expect(response.last_result_status).toBe("nav2_no_motion_path_generation_runtime_observed");
      expect(response.last_result_schema).toBe("trashbot.upper_robot_api.v1.nav2_proof_latest");
      expect(response.last_result_evidence_ref).toBe("nav2-latest-proof");
      expect(response.safe_to_control).toBe(false);
      expect(response.delivery_success).toBe(false);
      expect(response.primary_actions_enabled).toBe(false);
      expect(response.robot_control_executed).toBe(false);
    } finally {
      globalThis.fetch = originalFetch;
      timeoutSpy.mockRestore();
    }
  });

  it("Nav2 no-motion proof refresh rejects missing and unsafe base URLs before fetch", async () => {
    // baseUrl 不合法时必须本机拒绝，不能尝试访问任意主机或退化成通用 SSRF 代理。
    const missing = await buildNav2NoMotionProofRefreshProxy("");
    expect(missing.proxy_status).toBe("refresh_rejected");
    expect(missing.failure_reason).toBe("baseUrl_not_provided");
    expect(missing.remote_endpoint).toBe("/api/nav2/proof/refresh");
    expect(missing.safe_to_control).toBe(false);

    const unsafe = await buildNav2NoMotionProofRefreshProxy("https://example.com/api?token=secret");
    expect(unsafe.proxy_status).toBe("refresh_rejected");
    expect(unsafe.failure_reason).toBe("baseUrl_protocol_not_allowed");
    expect(unsafe.robot_control_executed).toBe(false);
  });

  it("Nav2 goal preflight uses minimal safety readbacks and never executes navigation", async () => {
    // 最新普通流程只要求安全确认和定位/路径只读状态；不再把 operator report 材料作为发车前预检。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "blocked_with_root_cause",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          localization_reset_observed: false,
          localization_tf_observed: { map_to_base_link: false },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "nav2_no_motion_path_generation_runtime_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          amcl_pose_observed: true,
          localization_tf_observed: { map_to_odom: true, map_to_base_link: true },
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 23,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "inactive",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          evidence_ref: "field-hil-nav-preflight",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-nav.mp4",
            visible_content_proven: true,
            camera_artifacts_ref: "runtime/camera/latest_metrics.json",
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
            physical_motion_lidar_delta_proven: true,
            scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
            delivery_success: true,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const helperResponse = await buildNavGoalPreflightProxy(upstream.baseUrl, {
        goal_frame_id: "map",
        goal_x: 99,
        goal_y: -99,
        goal_yaw: 9,
        confirm_navigation_preflight: true,
      });
      expect(helperResponse.proxy_status).toBe("preflight_passed");
      expect(helperResponse.preflight_status).toBe("ready_for_navigation_goal_not_executed");
      expect(helperResponse.goal_request.goal_x).toBe(3);
      expect(helperResponse.goal_request.goal_y).toBe(-3);
      expect(helperResponse.goal_request.goal_yaw).toBe(3.1416);
      expect(helperResponse.remote_methods_used).toEqual(["GET"]);
      expect(helperResponse.remote_read_endpoints.map((endpoint) => endpoint.endpoint)).toEqual(expect.arrayContaining([
        "/api/localize/proof/latest",
        "/api/nav2/proof/latest",
        "/api/nav2/status",
      ]));
      expect(helperResponse.remote_read_endpoints.map((endpoint) => endpoint.endpoint)).not.toContain("/api/operator/report");
      expect(JSON.stringify(helperResponse.remote_read_endpoints)).not.toContain("\"payload\"");
      expect(helperResponse.operator_report_preflight.status).toBe("not_required_for_nav2_minimal_safety_precheck");
      expect(helperResponse.operator_report_preflight.report_status).toBe("not_required_for_nav2_minimal_safety_precheck");
      expect(helperResponse.localization_summary.source).toBe("localize_or_nav2_proof_latest");
      expect(helperResponse.localization_summary.map_to_base_link).toBe(true);
      expect(helperResponse.missing_requirements).toEqual([]);
      expect(helperResponse.forbidden_remote_endpoints_not_called).toEqual(["/api/nav2/start", "NavigateToPose", "/cmd_vel", "/api/base/manual"]);
      expect(helperResponse.robot_control_executed).toBe(false);
      expect(helperResponse.safe_to_control).toBe(false);
      expect(helperResponse.delivery_success).toBe(false);

      const routeResponse = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/preflight?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal_x: 0.8, goal_y: 0, goal_yaw: 0, confirm_navigation_preflight: true }),
      });
      const routeBody = (await routeResponse.json()) as { proxy_status: string; robot_control_executed: boolean };
      expect(routeResponse.status).toBe(200);
      expect(routeBody.proxy_status).toBe("preflight_passed");
      expect(routeBody.robot_control_executed).toBe(false);
      expect(JSON.stringify(routeBody)).not.toContain("\"payload\"");
      expect(upstream.receivedBodies["/api/nav2/start"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedBodies["/cmd_vel"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 goal preflight rejects unknown fields but treats localization/path as read-only facts", async () => {
    // 未知字段先本机拒绝；定位/路径不足只进入只读摘要，不再作为普通发车前额外预检。
    const unknown = await buildNavGoalPreflightProxy("http://127.0.0.1:8787", {
      goal_x: 0.8,
      confirm_navigation_preflight: true,
      endpoint: "/api/nav2/start",
    });
    expect(unknown.proxy_status).toBe("preflight_rejected");
    expect(unknown.failure_reason).toContain("request_body_unknown_fields");
    expect(unknown.robot_control_executed).toBe(false);

    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_pending",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "path_not_generated",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          path_generated: false,
          path_generation_succeeded: false,
          path_point_count: 0,
        },
      },
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-nav.mp4",
            visible_content_proven: false,
            wheel_feedback_lr_nonzero_proven: false,
            physical_motion_lidar_delta_proven: false,
            delivery_success: true,
          },
        },
      },
    });
    try {
      const rejected = await buildNavGoalPreflightProxy(upstream.baseUrl, {
        goal_x: 0.8,
        goal_y: 0,
        goal_yaw: 0,
        confirm_navigation_preflight: false,
      });
      expect(rejected.proxy_status).toBe("preflight_rejected");
      expect(rejected.missing_requirements).toEqual(expect.arrayContaining([
        "confirm_navigation_preflight_required",
      ]));
      expect(rejected.missing_requirements).not.toEqual(expect.arrayContaining([
        "localization_runtime_or_reset_not_observed",
        "map_to_base_link_tf_not_observed",
        "path_generation_not_observed",
        "path_point_count_not_positive",
      ]));
      expect(rejected.missing_requirements).not.toContain("operator_report_preflight_required");
      expect(rejected.operator_report_preflight.missing_fields).not.toContain("delivery_success");
      expect(rejected.operator_report_preflight.status).toBe("not_required_for_nav2_minimal_safety_precheck");
      expect(rejected.operator_report_preflight.required_fields).toEqual([]);
      expect(rejected.minimal_precheck_safety_only).toBe(true);
      expect(rejected.camera_preflight_required).toBe(false);
      expect(rejected.radar_preflight_required).toBe(false);
      expect(rejected.operator_report_preflight_required).toBe(false);
      expect(rejected.route_readback_preflight_required).toBe(false);
      expect(rejected.localization_readback_preflight_required).toBe(false);
      expect(rejected.nav2_status_readback_preflight_required).toBe(false);
      expect(rejected.preflight_blocking_requirements).toEqual([
        "confirm_navigation_preflight",
        "goal_limits",
        "hard_dangerous_true_fields",
      ]);
      expect(rejected.operator_precheck_requirements).toEqual(["confirm_navigation_preflight"]);
      expect(rejected.proxy_guard_requirements).toEqual(["goal_limits", "hard_dangerous_true_fields"]);
      expect(rejected.minimal_precheck_plain).toContain("相机、雷达、现场报告、路线读回、定位读回和自动驾驶状态只做显示或复验");
      expect(JSON.stringify(rejected.remote_read_endpoints)).not.toContain("\"payload\"");
      expect(rejected.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/nav2/start"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();

      const accepted = await buildNavGoalPreflightProxy(upstream.baseUrl, {
        goal_x: 0.8,
        goal_y: 0,
        goal_yaw: 0,
        confirm_navigation_preflight: true,
      });
      expect(accepted.proxy_status).toBe("preflight_passed");
      expect(accepted.missing_requirements).toEqual([]);
      expect(accepted.minimal_precheck_safety_only).toBe(true);
      expect(accepted.camera_preflight_required).toBe(false);
      expect(accepted.radar_preflight_required).toBe(false);
      expect(accepted.operator_report_preflight_required).toBe(false);
      expect(accepted.route_readback_preflight_required).toBe(false);
      expect(accepted.localization_readback_preflight_required).toBe(false);
      expect(accepted.nav2_status_readback_preflight_required).toBe(false);
      expect(accepted.operator_precheck_requirements).toEqual(["confirm_navigation_preflight"]);
      expect(accepted.proxy_guard_requirements).toEqual(["goal_limits", "hard_dangerous_true_fields"]);
      expect(accepted.nav2_path_summary.path_generated).toBe(false);
      expect(accepted.nav2_path_summary.path_point_count).toBe(0);
      expect(accepted.robot_control_executed).toBe(false);
    } finally {
      await upstream.close();
    }
  });

  it("Nav2 goal execution reuses minimal PC preflight and forwards with safety confirmation", async () => {
    // 执行入口不能只靠前端禁用按钮；直接 POST 也必须有确认，但缺路径 proof 不再阻断真实 NavigateToPose 请求。
    const upstream = await listenRobotBaseCommandApi({
      "/api/nav2/goal/execute": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_forwarded_by_minimal_preflight",
          robot_control_executed: true,
          goal_request: {
            route_preview: {
              point_count: 3,
              source_point_count: 15,
              frame_id: "map",
              start_x: 0.1,
              start_y: 0.1,
              goal_x: 0.8,
              goal_y: 0,
            },
          },
        },
      },
    }, {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          localization_reset_observed: true,
          localization_tf_observed: { map_to_base_link: true },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "path_not_generated",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          path_generated: false,
          path_generation_succeeded: false,
          path_point_count: 0,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "active",
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execute?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          base_command_mode: "ros",
          route_preview_point_count: 3,
          route_preview_source_point_count: 15,
          route_preview_frame_id: "map",
          route_start_x: 0.1,
          route_start_y: 0.1,
          route_goal_x: 0.8,
          route_goal_y: 0,
          confirm_navigation_execution: true,
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        blocked_reasons: string[];
        minimal_precheck_safety_only: boolean;
        minimal_precheck_plain: string;
        execution_blocking_requirements: string[];
        operator_precheck_requirements: string[];
        proxy_guard_requirements: string[];
        camera_preflight_required: boolean;
        radar_preflight_required: boolean;
        operator_report_preflight_required: boolean;
        route_readback_preflight_required: boolean;
        localization_readback_preflight_required: boolean;
        nav2_status_readback_preflight_required: boolean;
        goal_request: {
          route_preview_point_count: number;
          route_preview_source_point_count: number;
          route_preview_frame_id: string;
          route_start_x: number | null;
          route_start_y: number | null;
          route_goal_x: number | null;
          route_goal_y: number | null;
        };
        goal_execution_key_values: Record<string, string>;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("execution_forwarded");
      expect(body.blocked_reasons).toEqual([]);
      expect(body.minimal_precheck_safety_only).toBe(true);
      expect(body.camera_preflight_required).toBe(false);
      expect(body.radar_preflight_required).toBe(false);
      expect(body.operator_report_preflight_required).toBe(false);
      expect(body.route_readback_preflight_required).toBe(false);
      expect(body.localization_readback_preflight_required).toBe(false);
      expect(body.nav2_status_readback_preflight_required).toBe(false);
      expect(body.execution_blocking_requirements).toEqual([
        "confirm_navigation_execution",
        "goal_limits",
        "hard_dangerous_true_fields",
      ]);
      expect(body.operator_precheck_requirements).toEqual(["confirm_navigation_execution"]);
      expect(body.proxy_guard_requirements).toEqual(["goal_limits", "hard_dangerous_true_fields"]);
      expect(body.minimal_precheck_plain).toContain("路线读回、定位读回和自动驾驶状态只做显示或复验");
      expect(body.goal_request.route_preview_point_count).toBe(3);
      expect(body.goal_request.route_preview_source_point_count).toBe(15);
      expect(body.goal_request.route_preview_frame_id).toBe("map");
      expect(body.goal_request.route_start_x).toBe(0.1);
      expect(body.goal_request.route_start_y).toBe(0.1);
      expect(body.goal_request.route_goal_x).toBe(0.8);
      expect(body.goal_request.route_goal_y).toBe(0);
      expect(body.goal_execution_key_values.status).toBe("goal_forwarded_by_minimal_preflight");
      expect(body.goal_execution_key_values.route_preview_point_count).toBe("3");
      expect(body.goal_execution_key_values.route_preview_source_point_count).toBe("15");
      expect(body.goal_execution_key_values.route_start_x).toBe("0.1");
      expect(body.goal_execution_key_values.route_goal_x).toBe("0.8");
      expect(body.robot_control_executed).toBe(true);
      expect(upstream.receivedGets).toEqual([
        "/api/localize/proof/latest",
        "/api/nav2/proof/latest",
        "/api/nav2/status",
      ]);
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toContainEqual(expect.objectContaining({
        goal_frame_id: "map",
        goal_x: 0.8,
        goal_y: 0,
        goal_yaw: 0,
        base_command_mode: "ros",
        managed_runtime_opt_in: true,
        confirm_navigation_execution: true,
        route_preview: {
          point_count: 3,
          source_point_count: 15,
          frame_id: "map",
          start_x: 0.1,
          start_y: 0.1,
          goal_x: 0.8,
          goal_y: 0,
        },
        route_preview_point_count: 3,
        route_preview_source_point_count: 15,
        route_preview_frame_id: "map",
        route_start_x: 0.1,
        route_start_y: 0.1,
        route_goal_x: 0.8,
        route_goal_y: 0,
      }));
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("defaults Nav2 goal execution to ROS base command mode when the browser omits a mode", async () => {
    // 普通按钮不应该回落到旧 PWM 诊断路径；Node 代理必须把省略模式的请求固定成 ros。
    const upstream = await listenRobotBaseCommandApi({
      "/api/nav2/goal/execute": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_forwarded_by_default_ros_mode",
          robot_control_executed: true,
        },
      },
    }, {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          robot_control_executed: false,
          localization_tf_observed: { map_to_base_link: true },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "path_generated",
          robot_control_executed: false,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "active",
          robot_control_executed: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execute?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          confirm_navigation_execution: true,
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        goal_request: { base_command_mode?: string };
        goal_execution_key_values: Record<string, string>;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("execution_forwarded");
      expect(body.goal_request.base_command_mode).toBe("ros");
      expect(body.goal_execution_key_values.status).toBe("goal_forwarded_by_default_ros_mode");
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toContainEqual(expect.objectContaining({
        base_command_mode: "ros",
        managed_runtime_opt_in: true,
        confirm_navigation_execution: true,
      }));
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("defaults omitted Nav2 goal execution mode from latest rerun recommendation", async () => {
    // 外部脚本可能不带 base_command_mode；如果最近 ROS action 成功但 L/R 仍为 0/0，代理要切到下一推荐模式复验。
    const upstream = await listenRobotBaseCommandApi({
      "/api/nav2/goal/execute": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_forwarded_by_default_speed_mode",
          robot_control_executed: true,
        },
      },
    }, {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          robot_control_executed: false,
          localization_tf_observed: { map_to_base_link: true },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "path_generated",
          robot_control_executed: false,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "active",
          robot_control_executed: false,
        },
      },
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          status: "goal_succeeded",
          result_status: "succeeded",
          robot_control_executed: true,
          base_command_mode: "ros",
          base_command_summary: {
            nonzero_command_count: 20,
            nonzero_command_observed: true,
            latest_nonzero_command_mode: "ros",
          },
          base_feedback_summary: {
            sample_count: 20,
            nonzero_sample_count: 0,
            wheel_feedback_lr_nonzero_proven: false,
            latest_pair: { left_speed: 0, right_speed: 0 },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execute?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          confirm_navigation_execution: true,
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        goal_request: { base_command_mode?: string };
        goal_execution_key_values: Record<string, string>;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("execution_forwarded");
      expect(body.goal_request.base_command_mode).toBe("speed");
      expect(body.goal_execution_key_values.status).toBe("goal_forwarded_by_default_speed_mode");
      expect(upstream.receivedGets).toEqual(expect.arrayContaining([
        "/api/localize/proof/latest",
        "/api/nav2/proof/latest",
        "/api/nav2/status",
        "/api/nav2/goal/execution/latest",
      ]));
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toContainEqual(expect.objectContaining({
        base_command_mode: "speed",
        managed_runtime_opt_in: true,
        confirm_navigation_execution: true,
      }));
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 latest execution proxy reads fixed GET artifact without replaying navigation", async () => {
    // latest 入口只帮 PC 页面找回最近 NavigateToPose artifact ref，不重新发送 Nav2 goal。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest_result",
          status: "not_proven",
          nav2_goal_execution_proven: false,
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          latest_result: {
            status: "goal_succeeded",
            evidence_ref: "o11-nav2-goal-execution-test",
            goal_accepted: true,
            result_received: true,
            result_status: "succeeded",
            goal_request: {
              frame_id: "map",
              x: 0.8,
              y: -0.2,
              yaw: 0.1,
              result_timeout_s: 4,
            },
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            delivery_success: false,
            base_feedback_summary: {
              sample_count: 12,
              nonzero_sample_count: 1,
              wheel_feedback_lr_nonzero_proven: true,
              latest_nonzero_pair: { left_speed: 164, right_speed: 164, raw_left: 164, raw_right: 164 },
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execution/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        goal_execution_key_values: Record<string, string>;
        latest_key_values: Record<string, string>;
        route_execution_readiness_plain: string;
        route_execution_precheck_plain: string;
        goal_execution_wheel_raw_lr_status_plain: string;
        goal_execution_wheel_raw_lr_next_action_plain: string;
        plain_hint: string;
        execution_status_plain: string;
        next_action_plain: string;
        goal_execution_status: string;
        result_status: string;
        nav2_goal_execution_proven: string;
        execution_proof_gap: string;
        goal_execution_robot_control_executed: string;
        goal_execution_feedback_sample_count: string;
        goal_execution_base_feedback_sample_count: string;
        goal_execution_base_feedback_nonzero_sample_count: string;
        goal_execution_base_command_mode: string;
        next_execution_base_command_mode: string;
        goal_execution_base_feedback_latest_raw_left: string;
        goal_execution_base_feedback_latest_raw_right: string;
        hard_dangerous_true_fields: string[];
        robot_control_executed: boolean;
        delivery_success: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.goal_execution_key_values.status).toBe("goal_succeeded");
      expect(body.goal_execution_key_values.evidence_ref).toBe("o11-nav2-goal-execution-test");
      expect(body.goal_execution_key_values.goal_frame_id).toBe("map");
      expect(body.goal_execution_key_values.goal_x).toBe("0.8");
      expect(body.goal_execution_key_values.goal_y).toBe("-0.2");
      expect(body.goal_execution_key_values.goal_yaw).toBe("0.1");
      expect(body.goal_execution_key_values.nav2_goal_execution_proven).toBe("true");
      expect(body.goal_execution_key_values.execution_proof_gap).toBe("none");
      expect(body.goal_execution_key_values.robot_control_executed).toBe("true");
      expect(body.goal_execution_key_values.sends_base_motion_commands).toBe("true");
      expect(body.goal_execution_key_values.uses_base_uart).toBe("true");
      expect(body.goal_execution_key_values.base_feedback_lr_nonzero_proven).toBe("true");
      expect(body.goal_execution_key_values.base_feedback_latest_raw_left).toBe("164");
      expect(body.goal_execution_key_values.base_feedback_latest_raw_right).toBe("164");
      expect(body.goal_execution_key_values.delivery_success).toBe("false");
      expect(body.goal_execution_status).toBe("goal_succeeded");
      expect(body.result_status).toBe("succeeded");
      expect(body.nav2_goal_execution_proven).toBe("true");
      expect(body.execution_proof_gap).toBe("none");
      expect(body.goal_execution_robot_control_executed).toBe("true");
      expect(body.goal_execution_feedback_sample_count).toBe("8");
      expect(body.goal_execution_base_feedback_sample_count).toBe("12");
      expect(body.goal_execution_base_feedback_nonzero_sample_count).toBe("1");
      expect(body.latest_key_values.base_feedback_lr_nonzero_proven).toBe("true");
      expect(body.latest_key_values.next_execution_base_command_mode).toBe("ros");
      expect(body.latest_key_values.goal_execution_wheel_raw_lr_status_plain).toBe("执行窗口轮速 L/R 已非零：L=164，R=164。");
      expect(body.execution_status_plain).toBe("本轮路线执行和执行窗口轮速 L/R 已证明。");
      expect(body.next_action_plain).toBe("继续送达确认；送达确认不会发车。");
      expect(body.route_execution_readiness_plain).toBe("完整路线执行已证明；同窗口轮速 L/R 已非零。");
      expect(body.route_execution_precheck_plain).toBe("下一步是送达确认；送达确认不会发车。");
      expect(body.goal_execution_wheel_raw_lr_status_plain).toBe("执行窗口轮速 L/R 已非零：L=164，R=164。");
      expect(body.goal_execution_wheel_raw_lr_next_action_plain).toBe("继续送达确认；送达确认不会发车。");
      expect(body.plain_hint).toBe(body.execution_status_plain);
      expect(body.goal_execution_base_command_mode).toBe("not_loaded");
      expect(body.next_execution_base_command_mode).toBe("ros");
      expect(body.goal_execution_base_feedback_latest_raw_left).toBe("164");
      expect(body.goal_execution_base_feedback_latest_raw_right).toBe("164");
      expect(body.hard_dangerous_true_fields).toEqual([]);
      expect(body.robot_control_executed).toBe(false);
      expect(body.delivery_success).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/nav2/goal/execution/latest"]);
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 latest execution proxy keeps top-level action success unproven until wheel L/R is nonzero", async () => {
    // 真机 latest artifact 有时没有 latest_result 包装；顶层成功和 IMU 运动迹象仍不能替代 wheel L/R 非零。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_succeeded",
          evidence_ref: "o11-nav2-goal-execution-top-level",
          nav2_goal_execution_proven: false,
          goal_accepted: true,
          result_received: true,
          result_status: "succeeded",
          goal_request: {
            frame_id: "map",
            x: 0.8,
            y: 0,
            yaw: 0,
            result_timeout_s: 4,
          },
          feedback_sample_count: 8,
          robot_control_executed: true,
          sends_base_motion_commands: true,
          uses_base_uart: true,
          delivery_success: false,
          base_feedback_summary: {
            sample_count: 239,
            nonzero_sample_count: 0,
            wheel_feedback_lr_nonzero_proven: false,
            imu_attitude_delta_observed: true,
            imu_attitude_delta_summary: {
              max_abs_pitch_delta: 24.210531,
              max_abs_roll_delta: 4.387221,
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execution/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        goal_execution_key_values: Record<string, string>;
        execution_status_plain: string;
        next_action_plain: string;
        goal_execution_status: string;
        result_status: string;
        nav2_goal_execution_proven: string;
        execution_proof_gap: string;
        goal_execution_hil_pass: string;
        goal_execution_robot_control_executed: string;
        goal_execution_feedback_sample_count: string;
        goal_execution_base_feedback_sample_count: string;
        goal_execution_base_feedback_nonzero_sample_count: string;
        goal_execution_goal_succeeded: string;
        goal_execution_wheel_rerun_needed: string;
        goal_execution_minimal_precheck_safety_only: boolean;
        goal_execution_safety_confirm_required: boolean;
        goal_execution_camera_preflight_required: boolean;
        goal_execution_radar_preflight_required: boolean;
        goal_execution_operator_report_preflight_required: boolean;
        goal_execution_route_wysiwyg_preflight_required: boolean;
        fixed_goal_execution_endpoint: string;
        fixed_goal_execution_latest_endpoint: string;
        goal_execution_base_feedback_latest_raw_left: string;
        goal_execution_base_feedback_latest_raw_right: string;
        robot_control_executed: boolean;
        delivery_success: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.goal_execution_key_values.status).toBe("goal_succeeded");
      expect(body.goal_execution_key_values.nav2_goal_execution_proven).toBe("false");
      expect(body.goal_execution_key_values.execution_proof_gap).toBe("wheel_lr_nonzero_not_proven");
      expect(body.goal_execution_key_values.robot_control_executed).toBe("true");
      expect(body.goal_execution_key_values.sends_base_motion_commands).toBe("true");
      expect(body.goal_execution_key_values.uses_base_uart).toBe("true");
      expect(body.goal_execution_key_values.base_feedback_lr_nonzero_proven).toBe("false");
      expect(body.goal_execution_key_values.base_feedback_imu_attitude_delta_observed).toBe("true");
      expect(body.goal_execution_key_values.feedback_sample_count).toBe("8");
      expect(body.goal_execution_status).toBe("goal_succeeded");
      expect(body.result_status).toBe("succeeded");
      expect(body.nav2_goal_execution_proven).toBe("false");
      expect(body.execution_proof_gap).toBe("wheel_lr_nonzero_not_proven");
      expect(body.goal_execution_hil_pass).toBe("not_loaded");
      expect(body.goal_execution_robot_control_executed).toBe("true");
      expect(body.goal_execution_feedback_sample_count).toBe("8");
      expect(body.goal_execution_base_feedback_sample_count).toBe("239");
      expect(body.goal_execution_base_feedback_nonzero_sample_count).toBe("0");
      expect(body.goal_execution_goal_succeeded).toBe("true");
      expect(body.goal_execution_wheel_rerun_needed).toBe("true");
      expect(body.goal_execution_minimal_precheck_safety_only).toBe(true);
      expect(body.goal_execution_safety_confirm_required).toBe(true);
      expect(body.goal_execution_camera_preflight_required).toBe(false);
      expect(body.goal_execution_radar_preflight_required).toBe(false);
      expect(body.goal_execution_operator_report_preflight_required).toBe(false);
      expect(body.goal_execution_route_wysiwyg_preflight_required).toBe(false);
      expect(body.fixed_goal_execution_endpoint).toBe("/api/robot-control/nav2/goal/execute");
      expect(body.fixed_goal_execution_latest_endpoint).toBe("/api/robot-control/nav2/goal/execution/latest");
      expect(body.execution_status_plain).toBe("上次路线结果成功，但执行窗口轮速 L/R=not_observed/not_observed 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。");
      expect(body.next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。");
      expect(body.goal_execution_base_feedback_latest_raw_left).toBe("not_observed");
      expect(body.goal_execution_base_feedback_latest_raw_right).toBe("not_observed");
      expect(body.robot_control_executed).toBe(false);
      expect(body.delivery_success).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/nav2/goal/execution/latest"]);
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 latest execution proxy derives command mode counts from live nested nonzero command shape", async () => {
    // 现场 latest_result.base_command_summary 可能只给 latest_nonzero_command.command_mode；PC 代理不能把它降成 not_loaded。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest",
          generated_at_ms: 1782567632121,
          latest_result: {
            status: "goal_succeeded",
            evidence_ref: "o11-nav2-goal-execution-live-nested-command",
            nav2_goal_execution_proven: false,
            goal_accepted: true,
            result_received: true,
            result_status: "succeeded",
            robot_control_executed: true,
            sends_base_motion_commands: true,
            uses_base_uart: true,
            base_command_mode: "pwm",
            base_command_summary: {
              sample_count: 50,
              nonzero_command_count: 49,
              nonzero_command_observed: true,
              latest_nonzero_command: {
                command_mode: "pwm",
                vendor_command: { T: 11, L: 164, R: -164 },
              },
            },
            base_feedback_summary: {
              sample_count: 239,
              nonzero_sample_count: 0,
              wheel_feedback_lr_nonzero_proven: false,
              latest_pair: { left_speed: 0, right_speed: 0 },
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execution/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        goal_execution_key_values: Record<string, string>;
        latest_key_values: Record<string, string>;
        route_execution_readiness_plain: string;
        route_execution_precheck_plain: string;
        goal_execution_wheel_raw_lr_status_plain: string;
        goal_execution_wheel_raw_lr_next_action_plain: string;
        plain_hint: string;
        execution_status_plain: string;
        next_action_plain: string;
        base_command_mode: string;
        goal_execution_base_command_mode: string;
        next_execution_base_command_mode: string;
        goal_execution_base_command_nonzero_observed: string;
        goal_execution_base_command_nonzero_count: string;
        goal_execution_base_command_mode_counts: string;
        goal_execution_base_feedback_lr_nonzero_proven: string;
        goal_execution_base_feedback_latest_raw_left: string;
        goal_execution_base_feedback_latest_raw_right: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.goal_execution_key_values.status).toBe("goal_succeeded");
      expect(body.goal_execution_key_values.base_command_mode).toBe("pwm");
      expect(body.goal_execution_key_values.base_command_nonzero_observed).toBe("true");
      expect(body.goal_execution_key_values.base_command_nonzero_count).toBe("49");
      expect(body.goal_execution_key_values.base_command_latest_nonzero_mode).toBe("pwm");
      expect(body.goal_execution_key_values.base_command_mode_counts).toBe("{\"pwm\":49}");
      expect(body.goal_execution_key_values.base_feedback_lr_nonzero_proven).toBe("false");
      expect(body.goal_execution_key_values.base_feedback_latest_left_speed).toBe("0");
      expect(body.goal_execution_key_values.base_feedback_latest_right_speed).toBe("0");
      expect(body.latest_key_values.next_execution_base_command_mode).toBe("ros");
      expect(body.latest_key_values.goal_execution_base_command_nonzero_count).toBe("49");
      expect(body.latest_key_values.goal_execution_base_feedback_lr_nonzero_proven).toBe("false");
      expect(body.latest_key_values.goal_execution_wheel_raw_lr_next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。");
      expect(body.execution_status_plain).toBe("上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令，下一步重点复验执行窗口轮速 L/R。");
      expect(body.plain_hint).toBe(body.execution_status_plain);
      expect(body.next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。");
      expect(body.route_execution_readiness_plain).toBe("图上路线可重跑复验；上次路线结果成功，但同窗口轮速 L/R=0/0 未非零。");
      expect(body.route_execution_precheck_plain).toBe("只需勾选行程前安全确认；相机、雷达和现场报告不作为额外发车前置；执行会用 ROS 模式跑图上路线。");
      expect(body.goal_execution_wheel_raw_lr_status_plain).toBe("上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到 49 次非零底盘命令。");
      expect(body.goal_execution_wheel_raw_lr_next_action_plain).toBe("勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。");
      expect(body.base_command_mode).toBe("pwm");
      expect(body.goal_execution_base_command_mode).toBe("pwm");
      expect(body.next_execution_base_command_mode).toBe("ros");
      expect(body.goal_execution_base_command_nonzero_observed).toBe("true");
      expect(body.goal_execution_base_command_nonzero_count).toBe("49");
      expect(body.goal_execution_base_command_mode_counts).toBe("{\"pwm\":49}");
      expect(body.goal_execution_base_feedback_lr_nonzero_proven).toBe("false");
      expect(body.goal_execution_base_feedback_latest_raw_left).toBe("0");
      expect(body.goal_execution_base_feedback_latest_raw_right).toBe("0");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/nav2/goal/execution/latest"]);
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 latest execution proxy keeps hil_pass false as not proven", async () => {
    // HIL false 是真车未证明的强信号，即使 action succeeded 也不能点亮完整路线。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/nav2/goal/execution/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_latest_result",
          status: "not_proven",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          latest_result: {
            status: "goal_succeeded",
            evidence_ref: "o11-nav2-goal-execution-hil-false",
            goal_accepted: true,
            result_received: true,
            result_status: "succeeded",
            hil_pass: false,
            goal_request: {
              frame_id: "map",
              x: 0.8,
              y: 0,
              yaw: 0,
              result_timeout_s: 4,
            },
            feedback_sample_count: 8,
            robot_control_executed: true,
            sends_motion_commands: true,
            delivery_success: false,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execution/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        goal_execution_key_values: Record<string, string>;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.goal_execution_key_values.status).toBe("goal_succeeded");
      expect(body.goal_execution_key_values.hil_pass).toBe("false");
      expect(body.goal_execution_key_values.nav2_goal_execution_proven).toBe("false");
      expect(body.goal_execution_key_values.feedback_sample_count).toBe("8");
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Nav2 execution proxy allows real base feedback evidence but still blocks delivery success", async () => {
    // O11 真实执行可返回底盘 UART/HIL 证据；delivery_success 仍必须由后续送达 gate 单独确认。
    const preflightGetHandlers = {
      "/api/localize/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.localization_reset_result",
          status: "localization_reset_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          localization_reset_observed: true,
          localization_tf_observed: { map_to_base_link: true },
        },
      },
      "/api/nav2/proof/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_proof_latest",
          status: "nav2_no_motion_path_generation_runtime_observed",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
          path_generated: true,
          path_generation_succeeded: true,
          path_point_count: 36,
        },
      },
      "/api/nav2/status": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_status",
          status: "active",
          robot_control_executed: false,
        },
      },
    };
    const upstream = await listenRobotBaseCommandApi({
      "/api/nav2/goal/execute": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_succeeded",
          goal_accepted: true,
          result_received: true,
          result_status: "succeeded",
          robot_control_executed: true,
          sends_motion_commands: true,
          sends_base_motion_commands: true,
          uses_base_uart: true,
          hil_pass: true,
          nav2_goal_execution_proven: true,
          delivery_success: false,
          base_command_mode: "pwm",
          base_command_summary: {
            sample_count: 2,
            nonzero_command_count: 1,
            nonzero_command_observed: true,
            latest_nonzero_command_mode: "ros",
            command_mode_counts: { ros: 2 },
          },
          base_feedback_summary: {
            sample_count: 2,
            nonzero_sample_count: 1,
            wheel_feedback_lr_nonzero_proven: true,
            latest_nonzero_pair: { left_speed: 90, right_speed: 90 },
          },
        },
      },
    }, preflightGetHandlers);
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/nav2/goal/execute?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          confirm_navigation_execution: true,
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        hard_dangerous_true_fields: string[];
        goal_execution_key_values: Record<string, string>;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("execution_forwarded");
      expect(body.hard_dangerous_true_fields).toEqual([]);
      expect(body.goal_execution_key_values.hil_pass).toBe("true");
      expect(body.goal_execution_key_values.base_command_mode).toBe("pwm");
      expect(body.goal_execution_key_values.base_command_latest_nonzero_mode).toBe("ros");
      expect(body.goal_execution_key_values.base_command_mode_counts).toBe("{\"ros\":2}");
      expect(body.goal_execution_key_values.base_feedback_lr_nonzero_proven).toBe("true");
      expect(body.goal_execution_key_values.base_feedback_latest_left_speed).toBe("90");
      expect(body.goal_execution_key_values.delivery_success).toBe("false");
    } finally {
      await workstation.close();
      await upstream.close();
    }

    const unsafeUpstream = await listenRobotBaseCommandApi({
      "/api/nav2/goal/execute": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.nav2_goal_execution_result",
          status: "goal_succeeded",
          robot_control_executed: true,
          sends_motion_commands: true,
          hil_pass: true,
          delivery_success: true,
        },
      },
    }, preflightGetHandlers);
    const unsafeWorkstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${unsafeWorkstation.baseUrl}/api/robot-control/nav2/goal/execute?baseUrl=${encodeURIComponent(unsafeUpstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_x: 0.8,
          goal_y: 0,
          goal_yaw: 0,
          confirm_navigation_execution: true,
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        hard_dangerous_true_fields: string[];
        failure_reason: string;
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("execution_failed");
      expect(body.hard_dangerous_true_fields).toContain("delivery_success");
      expect(body.failure_reason).toBe("dangerous_true_field:delivery_success");
    } finally {
      await unsafeWorkstation.close();
      await unsafeUpstream.close();
    }
  });

  it("delivery latest proxy reads fixed gate gap without submitting completion", async () => {
    // delivery latest 是只读缺口面板：不提交 operator report，不触发 delivery complete。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/delivery/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.delivery_completion_latest_result",
          delivery_success: false,
          safe_to_control: false,
          primary_actions_enabled: false,
          latest_result: {
            status: "blocked_missing_delivery_material",
            delivery_success: false,
            missing_required_material: JSON.stringify([
              "operator_report_latest_http_200",
              "operator_observed_motion",
              "structured_hil_claims.route_map_ref",
            ]),
            nav2_goal_execution: {
              status: "goal_succeeded",
              result_status: "succeeded",
              feedback_sample_count: 8,
              evidence_ref: "o11-nav2-goal-execution-test",
            },
            operator_report: {
              http_status: 404,
              operator_report_status: null,
              evidence_ref: "delivery-draft-smoke",
              structured_hil_claims: {},
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/delivery/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        delivery_success: boolean;
        delivery_key_values: Record<string, string>;
        missing_required_material: string[];
        delivery_missing_required_material: string[];
        delivery_missing_required_material_count: number;
        delivery_missing_required_material_plain: string;
        delivery_operator_evidence_ref: string;
        delivery_nav2_status: string;
        delivery_nav2_result_status: string;
        delivery_nav2_feedback_sample_count: string;
        delivery_latest_readback_only: boolean;
        delivery_complete_sends_motion: boolean;
        blocked_reasons: string[];
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.delivery_success).toBe(false);
      expect(body.delivery_key_values.status).toBe("blocked_missing_delivery_material");
      expect(body.delivery_key_values.nav2_status).toBe("goal_succeeded");
      expect(body.delivery_key_values.nav2_feedback_sample_count).toBe("8");
      expect(body.delivery_missing_required_material).toEqual([
        "operator_report_latest_http_200",
        "operator_observed_motion",
        "structured_hil_claims.route_map_ref",
      ]);
      expect(body.delivery_missing_required_material_count).toBe(3);
      expect(body.delivery_missing_required_material_plain).toBe("送达还差 3 项：operator_report_latest_http_200、operator_observed_motion、structured_hil_claims.route_map_ref。");
      expect(body.delivery_operator_evidence_ref).toBe("delivery-draft-smoke");
      expect(body.delivery_nav2_status).toBe("goal_succeeded");
      expect(body.delivery_nav2_result_status).toBe("succeeded");
      expect(body.delivery_nav2_feedback_sample_count).toBe("8");
      expect(body.delivery_latest_readback_only).toBe(true);
      expect(body.delivery_complete_sends_motion).toBe(false);
      expect(body.blocked_reasons).toEqual([
        "operator_report_latest_http_200",
        "operator_observed_motion",
        "structured_hil_claims.route_map_ref",
      ]);
      expect(body.missing_required_material).toEqual([
        "operator_report_latest_http_200",
        "operator_observed_motion",
        "structured_hil_claims.route_map_ref",
      ]);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/delivery/latest"]);
      expect(upstream.receivedBodies["/api/delivery/complete"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/operator/report"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("free-roam autonomy latest proxy reads fixed runtime artifact without starting autonomy", async () => {
    // 自动扫图 latest 是只读 runtime artifact：不调用 start/stop，不发送 manual，也不把 PC 顶层安全字段置真。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/free-roam/autonomy/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_latest",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: false,
            cmd_vel_publish_enabled: true,
            map_metrics: {
              free_cells: 421,
              unknown_ratio: 0.9819,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "running",
              reason: "门禁满足，低速直行",
              stop_required: false,
              gates: [
                { id: "operator_confirmed", state: "ready" },
                { id: "lidar_fresh", state: "ready" },
              ],
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/free-roam/autonomy/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        remote_endpoint: string;
        remote_method: string;
        plain_hint: string;
        next_action_plain: string;
        runtime_status: string;
        decision_state: string;
        decision_reason: string;
        stop_request_pending: boolean;
        free_roam_stop_request_pending: boolean;
        start_will_clear_stop_request: boolean;
        start_clears_stop_request_not_blocking: boolean;
        motion_start_blocked_by_stop_request: boolean;
        stop_request_status_plain: string;
        safety_confirmed: boolean;
        free_move_ready: boolean;
        free_move_start_ready: boolean;
        free_roam_motion_start_ready: boolean;
        motion_start_ready: boolean;
        free_roam_motion_ready: boolean;
        motion_ready: boolean;
        free_roam_mapping_ready: boolean;
        mapping_start_ready: boolean;
        mapping_start_missing_reasons: string[];
        free_roam_mapping_missing_reasons: string[];
        mapping_ready: boolean;
        mapping_missing_reasons: string[];
        missing_capabilities: string[];
        mapping_readiness_ready: boolean;
        mapping_blocked_reasons: string[];
        motion_readiness_plain: string;
        free_move_start_status_plain: string;
        motion_runtime_status_plain: string;
        mapping_acceptance_status_plain: string;
        mapping_readiness_plain: string;
        motion_next_action_plain: string;
        mapping_next_action_plain: string;
        latest_key_values: Record<string, string>;
        hard_dangerous_true_fields: string[];
        safe_to_control: boolean;
        delivery_success: boolean;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.remote_endpoint).toBe("/api/free-roam/autonomy/latest");
      expect(body.remote_method).toBe("GET");
      expect(body.plain_hint).toBe("自由移动已启动；继续保持现场可接管，必要时点击停止。建图验收未就绪；还差：画面首帧、地图记录、地图画面；这不阻止先低速自由移动。");
      expect(body.next_action_plain).toBe("继续低速监看；需要停下时点停止。建图验收还差：画面首帧、地图记录、地图画面；不影响先低速自由移动。");
      expect(body.runtime_status).toBe("loaded");
      expect(body.decision_state).toBe("running");
      expect(body.decision_reason).toBe("门禁满足，低速直行");
      expect(body.stop_request_pending).toBe(false);
      expect(body.free_roam_stop_request_pending).toBe(false);
      expect(body.start_will_clear_stop_request).toBe(false);
      expect(body.motion_start_blocked_by_stop_request).toBe(false);
      expect(body.stop_request_status_plain).toBe("当前没有停止请求。");
      expect(body.safety_confirmed).toBe(true);
      expect(body.free_move_ready).toBe(true);
      expect(body.free_move_start_ready).toBe(true);
      expect(body.free_roam_motion_start_ready).toBe(true);
      expect(body.motion_start_ready).toBe(true);
      expect(body.free_roam_motion_ready).toBe(true);
      expect(body.motion_ready).toBe(true);
      expect(body.mapping_start_ready).toBe(false);
      expect(body.mapping_start_missing_reasons).toEqual(["camera_first_frame"]);
      expect(body.free_roam_mapping_ready).toBe(false);
      expect(body.free_roam_mapping_missing_reasons).toEqual(["camera_first_frame", "mapping_active", "fresh_map_preview"]);
      expect(body.mapping_ready).toBe(false);
      expect(body.mapping_missing_reasons).toEqual(["camera_first_frame", "mapping_active", "fresh_map_preview"]);
      expect(body.missing_capabilities).toEqual(["camera_first_frame", "mapping_active", "fresh_map_preview"]);
      expect(body.mapping_readiness_ready).toBe(false);
      expect(body.mapping_blocked_reasons).toEqual(["camera_first_frame", "mapping_active", "fresh_map_preview"]);
      expect(body.motion_readiness_plain).toBe("自由移动正在运行；相机和雷达不作为继续移动的前置。");
      expect(body.free_move_start_status_plain).toBe("自由移动已启动；继续保持现场可接管，必要时点击停止。");
      expect(body.motion_runtime_status_plain).toBe("自由移动正在运行并发布低速运动；继续监看现场，必要时点击停止。");
      expect(body.mapping_acceptance_status_plain).toBe("建图验收未就绪；还差：画面首帧、地图记录、地图画面；这不阻止先低速自由移动。");
      expect(body.mapping_readiness_plain).toBe("建图验收未就绪；还差：画面首帧、地图记录、地图画面；不影响先低速自由移动。");
      expect(body.motion_next_action_plain).toBe("继续低速监看；需要停下时点停止。");
      expect(body.mapping_next_action_plain).toBe("建图验收还差：画面首帧、地图记录、地图画面；不影响先低速自由移动。");
      expect(body.latest_key_values.decision_state).toBe("running");
      expect(body.latest_key_values.decision_reason).toBe("门禁满足，低速直行");
      expect(body.latest_key_values.artifact_only).toBe("false");
      expect(body.latest_key_values.cmd_vel_publish_enabled).toBe("true");
      expect(body.latest_key_values.gate_count).toBe("2");
      expect(body.latest_key_values.runtime_gate_count).toBe("2");
      expect(body.latest_key_values.mapping_gate_count).toBe("4");
      expect(body.latest_key_values.mapping_required_ids).toBe("camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview");
      expect(body.latest_key_values.mapping_missing).toBe("camera_first_frame,mapping_active,fresh_map_preview");
      expect(body.latest_key_values.mapping_ready).toBe("false");
      expect(body.latest_key_values.map_free_cells).toBe("421");
      expect(body.latest_key_values.map_unknown_ratio).toBe("0.9819");
      expect(body.hard_dangerous_true_fields).toEqual([]);
      expect(body.safe_to_control).toBe(false);
      expect(body.delivery_success).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/free-roam/autonomy/latest"]);
      expect(upstream.receivedBodies["/api/free-roam/autonomy/start"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/free-roam/autonomy/stop"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("free-roam autonomy latest explains start-ready while motion runtime is stopped", async () => {
    // live 形态会同时出现 free_move_start_ready=true 和 motion_ready=false；后者只代表尚未运行，不是启动阻塞。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/free-roam/autonomy/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_latest",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "stopping",
              reason: "现场请求停止",
              stop_required: true,
              gates: [
                { id: "operator_confirmed", state: "blocked" },
                { id: "stop_available", state: "ready" },
              ],
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/free-roam/autonomy/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        plain_hint: string;
        next_action_plain: string;
        free_move_ready: boolean;
        free_move_start_ready: boolean;
        free_roam_motion_start_ready: boolean;
        motion_start_ready: boolean;
        free_roam_motion_ready: boolean;
        motion_ready: boolean;
        free_roam_mapping_ready: boolean;
        mapping_start_ready: boolean;
        mapping_start_missing_reasons: string[];
        free_roam_mapping_missing_reasons: string[];
        mapping_ready: boolean;
        mapping_missing_reasons: string[];
        missing_capabilities: string[];
        mapping_readiness_ready: boolean;
        stop_request_pending: boolean;
        free_roam_stop_request_pending: boolean;
        start_will_clear_stop_request: boolean;
        start_clears_stop_request_not_blocking: boolean;
        motion_start_blocked_by_stop_request: boolean;
        stop_request_status_plain: string;
        safety_confirmed: boolean;
        motion_readiness_plain: string;
        free_move_start_status_plain: string;
        motion_runtime_status_plain: string;
        mapping_acceptance_status_plain: string;
        motion_next_action_plain: string;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.plain_hint).toBe("自由移动可启动；点击开始会先清除停止请求，不作为启动阻塞。建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；这不阻止先低速自由移动。");
      expect(body.next_action_plain).toBe("勾选现场安全确认后可先自由移动；开始时会先清除停止请求。建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。");
      expect(body.free_move_ready).toBe(true);
      expect(body.free_move_start_ready).toBe(true);
      expect(body.free_roam_motion_start_ready).toBe(true);
      expect(body.motion_start_ready).toBe(true);
      expect(body.free_roam_motion_ready).toBe(false);
      expect(body.motion_ready).toBe(false);
      expect(body.stop_request_pending).toBe(true);
      expect(body.free_roam_stop_request_pending).toBe(true);
      expect(body.start_will_clear_stop_request).toBe(true);
      expect(body.start_clears_stop_request_not_blocking).toBe(true);
      expect(body.motion_start_blocked_by_stop_request).toBe(false);
      expect(body.stop_request_status_plain).toBe("停止请求会在开始自由移动时自动解除，不作为启动阻塞。");
      expect(body.safety_confirmed).toBe(false);
      expect(body.mapping_start_ready).toBe(false);
      expect(body.mapping_start_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh"]);
      expect(body.free_roam_mapping_ready).toBe(false);
      expect(body.free_roam_mapping_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"]);
      expect(body.mapping_ready).toBe(false);
      expect(body.mapping_missing_reasons).toEqual(["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"]);
      expect(body.missing_capabilities).toEqual(["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"]);
      expect(body.mapping_readiness_ready).toBe(false);
      expect(body.motion_readiness_plain).toBe("可先自由移动；停止请求会在开始时自动解除，不作为启动阻塞。");
      expect(body.free_move_start_status_plain).toBe("自由移动可启动；点击开始会先清除停止请求，不作为启动阻塞。");
      expect(body.motion_runtime_status_plain).toBe("当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。");
      expect(body.mapping_acceptance_status_plain).toContain("这不阻止先低速自由移动");
      expect(body.motion_next_action_plain).toBe("勾选现场安全确认后可先自由移动；开始时会先清除停止请求。");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/free-roam/autonomy/latest"]);
      expect(Object.keys(upstream.receivedBodies)).toEqual([]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("free-roam autonomy latest treats safety-confirmation lock separately from stop request", async () => {
    // stop_required=true 是保守停车要求；未勾安全确认时不能把它解释成外部停止请求。
    const upstream = await listenRobotBaseCommandApi({}, {
      "/api/free-roam/autonomy/latest": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.free_roam_autonomy_latest",
          status: "loaded",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          latest_result: {
            schema: "trashbot.free_roam_autonomy.runtime.v1",
            artifact_only: true,
            cmd_vel_publish_enabled: false,
            snapshot: {
              external_stop_requested: false,
              mapping_active: false,
              stop_available: true,
            },
            decision: {
              schema: "trashbot.free_roam_autonomy.decision.v1",
              state: "locked",
              reason: "还未勾选现场安全确认",
              stop_required: true,
              gates: [
                { id: "operator_confirmed", state: "blocked" },
                { id: "stop_available", state: "ready" },
              ],
            },
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/free-roam/autonomy/latest?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const body = (await response.json()) as {
        proxy_status: string;
        plain_hint: string;
        next_action_plain: string;
        stop_request_pending: boolean;
        free_roam_stop_request_pending: boolean;
        start_will_clear_stop_request: boolean;
        start_clears_stop_request_not_blocking: boolean;
        stop_request_status_plain: string;
        motion_readiness_plain: string;
        free_move_start_status_plain: string;
        motion_next_action_plain: string;
        latest_key_values: Record<string, string>;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("latest_loaded");
      expect(body.stop_request_pending).toBe(false);
      expect(body.free_roam_stop_request_pending).toBe(false);
      expect(body.start_will_clear_stop_request).toBe(false);
      expect(body.start_clears_stop_request_not_blocking).toBe(false);
      expect(body.stop_request_status_plain).toBe("当前没有停止请求。");
      expect(body.motion_readiness_plain).toBe("可先自由移动；只需要现场安全确认和停止兜底。");
      expect(body.free_move_start_status_plain).toBe("自由移动可启动；只需现场安全确认和停止兜底。");
      expect(body.motion_next_action_plain).toBe("勾选现场安全确认后可先自由移动。");
      expect(body.plain_hint).not.toContain("停止请求");
      expect(body.next_action_plain).not.toContain("清除停止请求");
      expect(body.latest_key_values.stop_required).toBe("true");
      expect(body.latest_key_values.external_stop_requested).toBe("false");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/free-roam/autonomy/latest"]);
      expect(Object.keys(upstream.receivedBodies)).toEqual([]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("delivery gap check posts fixed confirm false body and cannot confirm completion", async () => {
    // check 入口只刷新当前缺口：即使浏览器传 confirm=true，也必须固定转发 confirm=false。
    const upstream = await listenRobotBaseCommandApi({
      "/api/delivery/complete": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.delivery_completion_result",
          status: "blocked_missing_delivery_material",
          delivery_success: false,
          safe_to_control: false,
          primary_actions_enabled: false,
          missing_required_material: ["confirm_delivery_completion", "operator_report_ready_for_review"],
          nav2_goal_execution: {
            status: "goal_succeeded",
            result_status: "succeeded",
            feedback_sample_count: 8,
          },
          operator_report: {
            operator_report_status: "unsafe_or_incomplete",
            evidence_ref: "delivery-draft",
          },
        },
      },
    }, {});
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/delivery/check?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm_delivery_completion: true, delivery_success: true }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        delivery_success: boolean;
        request_body: { confirm_delivery_completion?: boolean; delivery_evidence_ref?: string };
        delivery_key_values: Record<string, string>;
        blocked_reasons: string[];
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("check_loaded");
      expect(body.delivery_success).toBe(false);
      expect(body.request_body.confirm_delivery_completion).toBe(false);
      expect(body.request_body.delivery_evidence_ref).toBe("delivery-gap-check-not-confirmed");
      expect(body.delivery_key_values.status).toBe("blocked_missing_delivery_material");
      expect(body.delivery_key_values.operator_report_status).toBe("unsafe_or_incomplete");
      expect(body.blocked_reasons).toEqual(["confirm_delivery_completion", "operator_report_ready_for_review"]);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/delivery/complete"]).toEqual([
        {
          confirm_delivery_completion: false,
          delivery_evidence_ref: "delivery-gap-check-not-confirmed",
          operator_notes: "PC delivery gap check only; confirm_delivery_completion=false so this cannot produce delivery success.",
        },
      ]);
      expect(upstream.receivedBodies["/api/operator/report"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Robot Control summary explains 7071 is not the robot API port", async () => {
    // 现场旧链接或手填 7071 会让所有只读端点 fetch failed；要直说端口漂移，而不是误导成雷达/相机/Nav2 坏了。
    const fetchMock = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("ECONNREFUSED"));
    try {
      const summary = await buildRobotControlSummary("http://192.168.1.11:7071");

      expect(fetchMock).toHaveBeenCalled();
      expect(summary.robot_api_connection.status).toBe("degraded");
      expect(summary.robot_api_connection.loaded_count).toBe(0);
      expect(summary.robot_api_connection.blocked_reasons[0]).toBe("robot_api_port_7071_mismatch_use_8787");
      expect(summary.blocked_reasons[0]).toBe("robot_api_port_7071_mismatch_use_8787");
      expect(summary.live_closure_summary?.robot_api_connection_status).toBe("degraded");
      expect(summary.live_closure_summary?.robot_api_connection_loaded_count).toBe(0);
      expect(summary.live_closure_summary?.robot_api_connection_failed_count).toBeGreaterThan(0);
      expect(summary.live_closure_summary?.robot_api_connection_failed_endpoint_ids).toContain("status");
      expect(summary.live_closure_summary?.robot_api_connection_blocked_reasons[0]).toBe("robot_api_port_7071_mismatch_use_8787");
      expect(summary.live_closure_summary?.robot_api_connection_plain).toContain("小车连接不可用");
      expect(summary.live_closure_summary?.robot_api_connection_next_action_plain).toContain("8787 Robot API 服务");
      expect(summary.live_closure_summary?.robot_api_connection_recovery_endpoints).toEqual([
        "/api/robot-control/summary",
        "/api/robot-control/map/preview",
        "/api/robot-control/radar/status",
        "/api/robot-control/camera/mjpeg/status",
      ]);
      expect(summary.live_closure_summary?.robot_api_connection_sends_motion_when_clicked).toBe(false);
      expect(summary.live_closure_summary?.summary_plain).toContain("先恢复上车连接");
      expect(summary.live_closure_summary?.next_action_plain).toContain("先确认小车电源、网络、8787 Robot API 服务和 SSH 登录状态");
      expect(summary.current_fact_plain).toContain("小车地址端口写错");
      expect(summary.current_fact_plain).toContain("PC 页面是 0.0.0.0:7001");
      expect(summary.current_fact_plain).toContain("Robot API 是 192.168.1.11:8787");
      expect(summary.current_fact_plain).toContain("不要把 Robot API 填成 7071");
      expect(summary.safe_to_control).toBe(false);
      expect(summary.primary_actions_enabled).toBe(false);
      expect(summary.safe_command_boundary.command_dispatch_enabled).toBe(false);
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      fetchMock.mockRestore();
    }
  });

  it("Robot Control summary rejects unsafe URLs and dangerous true fields", async () => {
    // URL 和 payload 任一层不安全都必须 fail-closed，防止控制台被误用为控制代理。
    const missing = await buildRobotControlSummary("");
    expect(missing.console_status).toBe("blocked");
    expect(missing.blocked_reasons).toContain("baseUrl_not_provided");
    expect(missing.current_fact_plain).toBe("当前事实未读到；先填写或确认小车地址。");
    expect(missing.goal_summary).toEqual(missing.goal_checklist_summary);
    expect(missing.camera_summary).toEqual(missing.readback_summary.camera);
    expect(missing.map_summary).toEqual(missing.readback_summary.map);
    expect(missing.radar_summary).toEqual(missing.readback_summary.radar);
    expect(missing.nav2_summary).toEqual(missing.readback_summary.nav2);
    expect(missing.keyboard_summary).toEqual(missing.readback_summary.keyboard);
    expect(missing.readback_summary.keyboard_control).toEqual(missing.readback_summary.keyboard);
    expect(missing.readback_summary.keyboard_teleop).toEqual(missing.readback_summary.keyboard);
    expect(missing.keyboard_control_summary).toEqual(missing.readback_summary.keyboard_control);
    expect(missing.keyboard_teleop_summary).toEqual(missing.readback_summary.keyboard_teleop);
    expect(missing.free_roam_summary).toEqual(missing.readback_summary.free_roam);
    expect(missing.nav2_summary?.next_action_plain).toContain("先准备图上路线");
    expect(missing.goal_summary?.progress_plain).toBe("0/0");
    expect(missing.goal_summary?.ready_action_ids).toEqual([]);
    expect(missing.goal_summary?.blocked_action_ids).toEqual([]);

    const unsafeUrl = await buildRobotControlSummary("https://127.0.0.1:8787?token=secret");
    expect(unsafeUrl.console_status).toBe("blocked");
    expect(unsafeUrl.blocked_reasons).toContain("baseUrl_protocol_not_allowed");
    expect(unsafeUrl.current_fact_plain).toContain("当前事实未读到");
    expect(unsafeUrl.goal_summary).toEqual(unsafeUrl.goal_checklist_summary);
    expect(unsafeUrl.camera_summary).toEqual(unsafeUrl.readback_summary.camera);
    expect(unsafeUrl.map_summary).toEqual(unsafeUrl.readback_summary.map);
    expect(unsafeUrl.radar_summary).toEqual(unsafeUrl.readback_summary.radar);
    expect(unsafeUrl.nav2_summary).toEqual(unsafeUrl.readback_summary.nav2);
    expect(unsafeUrl.keyboard_summary).toEqual(unsafeUrl.readback_summary.keyboard);
    expect(unsafeUrl.readback_summary.keyboard_control).toEqual(unsafeUrl.readback_summary.keyboard);
    expect(unsafeUrl.readback_summary.keyboard_teleop).toEqual(unsafeUrl.readback_summary.keyboard);
    expect(unsafeUrl.keyboard_control_summary).toEqual(unsafeUrl.readback_summary.keyboard_control);
    expect(unsafeUrl.keyboard_teleop_summary).toEqual(unsafeUrl.readback_summary.keyboard_teleop);
    expect(unsafeUrl.free_roam_summary).toEqual(unsafeUrl.readback_summary.free_roam);
    expect(unsafeUrl.goal_summary?.progress_plain).toBe("0/0");

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

  it("workstation camera offer proxy keeps baseUrl guard and returns only safe answer summary", async () => {
    // offer proxy 只允许 camera offer 白名单路径，且响应只保留 answer/peer/status/error 的安全摘要。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/offer": {
        payload: {
          schema: "trashbot.local_webrtc_camera_offer.v1",
          status: "ready",
          peer_id: "peerABC123",
          type: "answer",
          sdp: "v=0\r\ns=remote-answer\r\n",
          safe_to_control: true,
          delivery_success: true,
          primary_actions_enabled: true,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/camera/offer?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ type: "offer", sdp: "v=0\r\ns=local-offer\r\n" }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        answer: { type: string; sdp: string } | null;
        blocked_reasons: string[];
        safe_to_control: boolean;
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("offer_failed");
      expect(body.answer?.type).toBe("answer");
      expect(body.answer?.sdp).toContain("remote-answer");
      expect(body.answer?.sdp.endsWith("\r\n")).toBe(true);
      expect(body.blocked_reasons).toContain("dangerous_true_field:safe_to_control");
      expect(body.safe_to_control).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }

    const server = await listen(createWorkstationApp());
    try {
      const rejected = await fetch(`${server.baseUrl}/api/robot-control/camera/offer?baseUrl=${encodeURIComponent("https://example.com")}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ type: "offer", sdp: "v=0\r\ns=local-offer\r\n" }),
      });
      const rejectedBody = (await rejected.json()) as { failure_reason: string };

      expect(rejected.status).toBe(400);
      expect(rejectedBody.failure_reason).toBe("baseUrl_protocol_not_allowed");
    } finally {
      await server.close();
    }
  });

  it("workstation camera MJPEG proxy forwards only fixed readonly multipart stream", async () => {
    // MJPEG fallback 是固定 GET 只读共享流；多个浏览器不能各自抢一个上游 camera reader。
    let upstreamRequestCount = 0;
    const upstreamControl: { release?: () => void } = {};
    const upstreamServer = http.createServer((req, res) => {
      if (req.method !== "GET" || req.url !== "/api/camera/mjpeg") {
        res.statusCode = 404;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({ error: "not_found" }));
        return;
      }
      upstreamRequestCount += 1;
      res.statusCode = 200;
      res.setHeader("Content-Type", "multipart/x-mixed-replace; boundary=roberframe");
      res.write("--roberframe\r\nContent-Type: image/jpeg\r\nContent-Length: 4\r\n\r\njpeg\r\n");
      upstreamControl.release = () => {
        res.end("--roberframe\r\nContent-Type: image/jpeg\r\nContent-Length: 5\r\n\r\njpeg2\r\n");
      };
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    const openedClients: Array<{ destroy: () => void }> = [];
    try {
      const endpoint = `${workstation.baseUrl}/api/robot-control/camera/mjpeg?baseUrl=${encodeURIComponent(upstream.baseUrl)}`;
      const openMjpegClient = (url: string) => new Promise<{
        statusCode: number | undefined;
        headers: http.IncomingHttpHeaders;
        chunks: string[];
        waitForText: (text: string) => Promise<string>;
        destroy: () => void;
      }>((resolve, reject) => {
        const chunks: string[] = [];
        const request = http.get(url, (response) => {
          response.setEncoding("utf8");
          response.on("data", (chunk) => chunks.push(String(chunk)));
          const waitForText = (text: string) => new Promise<string>((waitResolve, waitReject) => {
            const current = chunks.join("");
            if (current.includes(text)) {
              waitResolve(current);
              return;
            }
            const timeout = setTimeout(() => {
              cleanup();
              waitReject(new Error(`mjpeg_chunk_timeout:${text}`));
            }, 1000);
            const onData = () => {
              const next = chunks.join("");
              if (!next.includes(text)) {
                return;
              }
              cleanup();
              waitResolve(next);
            };
            const onError = (error: Error) => {
              cleanup();
              waitReject(error);
            };
            const cleanup = () => {
              clearTimeout(timeout);
              response.off("data", onData);
              response.off("error", onError);
            };
            response.on("data", onData);
            response.on("error", onError);
          });
          resolve({
            statusCode: response.statusCode,
            headers: response.headers,
            chunks,
            waitForText,
            destroy: () => {
              response.destroy();
              request.destroy();
            },
          });
        });
        request.on("error", reject);
      });
      const response = await openMjpegClient(endpoint);
      openedClients.push(response);
      const secondResponsePromise = openMjpegClient(endpoint);
      await new Promise((resolve) => setTimeout(resolve, 20));

      expect(response.statusCode).toBe(200);
      expect(String(response.headers["content-type"])).toContain("multipart/x-mixed-replace");
      expect(response.headers["x-robber-proxy"]).toBe("camera-mjpeg-shared-readonly");
      expect(response.headers["x-robber-camera-shared-capture"]).toBe("single_shared_capture_for_multiple_clients");
      expect(response.headers["x-robber-camera-exclusive-claim"]).toBe("false");
      expect(upstreamRequestCount).toBe(1);
      const firstText = await response.waitForText("jpeg");
      expect(firstText).toContain("Content-Type: image/jpeg");
      expect(firstText).toContain("jpeg");
      const summaryResponse = await fetch(
        `${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
      );
      const summaryBody = (await summaryResponse.json()) as RobotControlSummaryResponse;
      expect(summaryResponse.status).toBe(200);
      expect(summaryBody.readback_summary.camera.preview_status).toBe("streaming");
      expect(summaryBody.readback_summary.camera.preview_visible_status).toBe("visible_cached_frame");
      expect(summaryBody.readback_summary.camera.preview_visible_plain).toBe("当前有共享实时画面缓存帧；新页面复用同一条上游流。");
      expect(summaryBody.readback_summary.camera.camera_wysiwyg_status_plain).toBe("画面已可见：共享实时画面已有缓存帧，多个页面复用同一条上游流。");
      expect(summaryBody.readback_summary.camera.camera_wysiwyg_next_action_plain).toBe("继续监看共享实时画面。");
      expect(summaryBody.readback_summary.camera.plain_hint).toContain("已经看到画面：共享实时画面已有缓存帧");
      expect(summaryBody.readback_summary.camera.plain_hint).toContain("共享预览不是页面独占");
      expect(summaryBody.readback_summary.camera.plain_hint).toContain("下一步：继续监看共享实时画面");
      expect(Number(summaryBody.readback_summary.camera.shared_preview_client_count)).toBeGreaterThan(0);
      expect(summaryBody.readback_summary.camera.shared_preview_upstream_active).toBe("true");
      expect(summaryBody.readback_summary.camera.shared_preview_content_type_loaded).toBe("true");
      expect(summaryBody.readback_summary.camera.shared_preview_cached_frame_loaded).toBe("true");
      expect(Number(summaryBody.readback_summary.camera.shared_preview_cached_frame_age_ms)).toBeGreaterThanOrEqual(0);
      expect(summaryBody.readback_summary.camera.shared_preview_shared_capture).toBe("true");
      expect(summaryBody.readback_summary.camera.shared_preview_exclusive_camera_claim).toBe("false");
      expect(summaryBody.readback_summary.camera.shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
      expect(summaryBody.readback_summary.camera.shared_preview_multi_viewer_plain).toContain("谁打开页面都接入同一个共享 relay");
      expect(summaryBody.readback_summary.camera.shared_preview_multi_viewer_plain).toContain(`${summaryBody.readback_summary.camera.shared_preview_client_count} 个页面观看`);
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_reason).toBe("none");
      expect(summaryBody.readback_summary.camera.shared_preview_last_remote_http_status).toBe("none");
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_at_ms).toBe("none");
      expect(summaryBody.safe_command_boundary.robot_control_executed).toBe(false);
      expect(upstreamRequestCount).toBe(1);

      const lateResponse = await openMjpegClient(endpoint);
      openedClients.push(lateResponse);
      expect(lateResponse.statusCode).toBe(200);
      expect(String(lateResponse.headers["content-type"])).toContain("multipart/x-mixed-replace");
      expect(lateResponse.headers["x-robber-proxy"]).toBe("camera-mjpeg-shared-readonly");
      expect(lateResponse.headers["x-robber-camera-shared-capture"]).toBe("single_shared_capture_for_multiple_clients");
      expect(lateResponse.headers["x-robber-camera-exclusive-claim"]).toBe("false");
      const lateText = await lateResponse.waitForText("jpeg");
      expect(lateText).toContain("jpeg");
      expect(upstreamRequestCount).toBe(1);
      const statusResponse = await fetch(
        `${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
      );
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;
      expect(statusBody.cached_frame_loaded).toBe(true);
      expect(statusBody.shared_preview_cached_frame_loaded).toBe(true);
      expect(Number(statusBody.cached_frame_age_ms)).toBeGreaterThanOrEqual(0);
      expect(Number(statusBody.shared_preview_cached_frame_age_ms)).toBeGreaterThanOrEqual(0);
      expect(statusBody.shared_preview_client_count).toBe(statusBody.client_count);
      expect(statusBody.viewer_count).toBe(statusBody.client_count);
      expect(statusBody.shared_preview_upstream_active).toBe(statusBody.upstream_active);
      expect(statusBody.upstream_connected).toBe(statusBody.upstream_active);
      expect(statusBody.shared_preview_content_type_loaded).toBe(statusBody.content_type_loaded);
      expect(statusBody.shared_preview_shared_capture).toBe(true);
      expect(statusBody.shared_preview_exclusive_camera_claim).toBe(false);
      expect(statusBody.shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
      expect(statusBody.shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
      expect(statusBody.shared_preview_multi_viewer_plain).toContain("谁打开页面都接入同一个共享 relay");
      expect(statusBody.shared_preview_multi_viewer_plain).toContain(`${statusBody.client_count} 个页面观看`);
      expect(statusBody.has_recent_frame).toBe(statusBody.cached_frame_loaded);
      expect(statusBody.status).toBe(statusBody.preview_status);
      expect(statusBody.plain_hint).toBe(statusBody.preview_plain_hint);
      expect(statusBody.next_action_plain).toBe(statusBody.preview_next_action_plain);
      expect(statusBody.preview_visible_status).toBe("visible_cached_frame");
      expect(statusBody.preview_visible_plain).toBe("当前有共享实时画面缓存帧；新页面复用同一条上游流。");
      expect(statusBody.camera_wysiwyg_status_plain).toBe("画面已可见：共享实时画面已有缓存帧，多个页面复用同一条上游流。");
      expect(statusBody.camera_wysiwyg_next_action_plain).toBe("继续监看共享实时画面。");

      upstreamControl.release?.();
      const secondResponse = await secondResponsePromise;
      openedClients.push(secondResponse);
      expect(secondResponse.statusCode).toBe(200);
      expect(String(secondResponse.headers["content-type"])).toContain("multipart/x-mixed-replace");
      expect(secondResponse.headers["x-robber-proxy"]).toBe("camera-mjpeg-shared-readonly");
      expect(secondResponse.headers["x-robber-camera-shared-capture"]).toBe("single_shared_capture_for_multiple_clients");
      expect(secondResponse.headers["x-robber-camera-exclusive-claim"]).toBe("false");
      const secondText = await secondResponse.waitForText("jpeg2");
      expect(secondText).toContain("jpeg2");
    } finally {
      for (const client of openedClients) {
        client.destroy();
      }
      await workstation.close();
      await upstream.close();
    }
  }, 10_000);

  it("workstation camera MJPEG status is readonly and does not open upstream capture", async () => {
    // status 只允许短读 health 解释源状态；没有页面观看时不能为了查状态去打开 MJPEG 相机流。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.end(JSON.stringify({ method: req.method, url: req.url }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;
      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.shared_preview_client_count).toBe(0);
      expect(statusBody.viewer_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.shared_preview_upstream_active).toBe(false);
      expect(statusBody.upstream_connected).toBe(false);
      expect(statusBody.content_type_loaded).toBe(false);
      expect(statusBody.shared_preview_content_type_loaded).toBe(false);
      expect(statusBody.has_recent_frame).toBe(false);
      expect(statusBody.shared_capture).toBe(true);
      expect(statusBody.shared_preview_shared_capture).toBe(true);
      expect(statusBody.exclusive_camera_claim).toBe(false);
      expect(statusBody.shared_preview_exclusive_camera_claim).toBe(false);
      expect(statusBody.shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
      expect(statusBody.shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
      expect(statusBody.shared_preview_multi_viewer_plain).toContain("当前 0 个页面观看");
      expect(statusBody.last_failure_reason).toBe("");
      expect(statusBody.shared_preview_last_failure_reason).toBe("");
      expect(statusBody.last_remote_http_status).toBe(null);
      expect(statusBody.shared_preview_last_remote_http_status).toBe(null);
      expect(statusBody.last_failure_at_ms).toBe(null);
      expect(statusBody.shared_preview_last_failure_at_ms).toBe(null);
      expect(statusBody.source_diagnosis_status).toBe("not_loaded");
      expect(statusBody.source_diagnosis_plain_hint).toBe("not_loaded");
      expect(statusBody.source_diagnosis_next_action).toBe("not_loaded");
      expect(statusBody.source_diagnosis_next_action_plain).toBe("打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("not_loaded");
      expect(statusBody.status).toBe("idle_not_started");
      expect(statusBody.plain_hint).toBe("页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(statusBody.next_action_plain).toBe("打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。");
      expect(statusBody.preview_status).toBe("idle_not_started");
      expect(statusBody.preview_plain_hint).toBe("页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(statusBody.preview_next_action).toBe("auto_join_shared_mjpeg_preview");
      expect(statusBody.preview_next_action_plain).toBe("打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。");
      expect(statusBody.preview_visible_status).toBe("not_visible_idle");
      expect(statusBody.preview_visible_plain).toBe("当前没有实时画面；页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(statusBody.camera_wysiwyg_status_plain).toBe("画面未可见：页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。");
      expect(statusBody.camera_wysiwyg_next_action_plain).toBe("打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status reports source first-frame failure without opening the stream", async () => {
    // live 7001 形态是 health 已知 source_first_frame_failed，但 relay 刚重启还没有 MJPEG last_failure。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "capture_read_returned_false",
          source_diagnosis: {
            status: "uvc_no_frame_not_exclusive",
            plain_hint: "不是页面独占：not_loaded 当前没人占用，但 UVC 设备没有输出视频帧。",
            next_action: "check_usb_camera_input_power_or_known_good_uvc",
            not_exclusive: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.shared_preview_client_count).toBe(0);
      expect(statusBody.viewer_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.shared_preview_upstream_active).toBe(false);
      expect(statusBody.upstream_connected).toBe(false);
      expect(statusBody.shared_preview_shared_capture).toBe(true);
      expect(statusBody.shared_preview_exclusive_camera_claim).toBe(false);
      expect(statusBody.has_recent_frame).toBe(false);
      expect(statusBody.shared_preview_contract).toBe("single_shared_capture_for_multiple_clients");
      expect(statusBody.shared_preview_multi_viewer_status).toBe("single_upstream_multi_viewer");
      expect(statusBody.shared_preview_multi_viewer_plain).toContain("当前 0 个页面观看");
      expect(statusBody.last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(statusBody.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(statusBody.last_remote_http_status).toBe(200);
      expect(statusBody.shared_preview_last_remote_http_status).toBe(200);
      expect(typeof statusBody.last_failure_at_ms).toBe("number");
      expect(typeof statusBody.shared_preview_last_failure_at_ms).toBe("number");
      expect(statusBody.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(statusBody.source_diagnosis_plain_hint).toBe("不是页面独占：USB 摄像头当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.source_diagnosis_plain_hint).not.toContain("not_loaded");
      expect(statusBody.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.source_diagnosis_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");
      expect(statusBody.source_readiness).toBe("first_frame_failed");
      expect(statusBody.source_failure_reason).toBe("capture_read_returned_false");
      expect(statusBody.preview_status).toBe("source_first_frame_failed");
      expect(statusBody.preview_plain_hint).toBe("不是页面独占：USB 摄像头当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.preview_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.preview_visible_status).toBe("not_visible_source_first_frame_failed");
      expect(statusBody.preview_visible_plain).toBe("当前没有实时画面；不是页面独占：USB 摄像头当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.camera_wysiwyg_status_plain).toBe("画面未可见：不是页面独占：USB 摄像头当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.camera_wysiwyg_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.robot_control_executed).toBe(false);
      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = await summaryResponse.json() as RobotControlSummaryResponse;

      expect(summaryResponse.status).toBe(200);
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summaryBody.readback_summary.camera.shared_preview_last_remote_http_status).toBe("200");
      expect(Number(summaryBody.readback_summary.camera.shared_preview_last_failure_at_ms)).toBeGreaterThan(0);
      expect(summaryBody.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summaryBody.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
      expect(summaryBody.readback_summary.camera.preview_plain_hint).toBe(summaryBody.readback_summary.camera.source_diagnosis_plain_hint);
      expect(summaryBody.readback_summary.camera.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summaryBody.readback_summary.camera.preview_next_action_plain).toBe("检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(summaryBody.safe_command_boundary.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(3);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status derives non-exclusive no-frame diagnosis from source usage", async () => {
    // live 形态可能只在 health 里报告 source_first_frame_failed 和 not_in_use；status 仍要说清不是页面独占。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          video_source: "/dev/video1",
          selected_name: "USB Composite Device: DV20 USB",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_usage: {
            status: "not_in_use",
            owner_count: 0,
            owners: [],
          },
          source_diagnosis: {
            status: "source_first_frame_failed",
            plain_hint: "USB Composite Device: DV20 USB 没有输出首帧；先看占用和格式尝试，再检查 USB/供电。",
            next_action: "inspect_usage_and_format_attempts",
            not_exclusive: false,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(statusBody.last_remote_http_status).toBe(200);
      expect(statusBody.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(statusBody.source_diagnosis_plain_hint).toBe("不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");
      expect(statusBody.source_readiness).toBe("first_frame_failed");
      expect(statusBody.source_failure_reason).toBe("first_frame_total_timeout");
      expect(statusBody.selected_path).toBe("/dev/video1");
      expect(statusBody.selected_name).toBe("USB Composite Device: DV20 USB");
      expect(statusBody.source_usage_status).toBe("not_in_use");
      expect(statusBody.source_usage_owner_count).toBe("0");
      expect(statusBody.preview_status).toBe("source_first_frame_failed");
      expect(statusBody.preview_plain_hint).toBe("不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.robot_control_executed).toBe(false);
      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = await summaryResponse.json() as RobotControlSummaryResponse;
      expect(summaryResponse.status).toBe(200);
      expect(summaryBody.readback_summary.camera.status).toBe("source_first_frame_failed");
      expect(summaryBody.readback_summary.camera.selected_path).toBe("/dev/video1");
      expect(summaryBody.readback_summary.camera.selected_name).toBe("USB Composite Device: DV20 USB");
      expect(summaryBody.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(summaryBody.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summaryBody.readback_summary.camera.source_diagnosis_plain_hint).toContain("不是页面独占");
      expect(summaryBody.readback_summary.camera.source_diagnosis_plain_hint).toContain("UVC 设备没有输出视频帧");
      expect(summaryBody.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
      expect(summaryBody.readback_summary.camera.preview_plain_hint).toBe(summaryBody.readback_summary.camera.source_diagnosis_plain_hint);
      expect(summaryBody.readback_summary.camera.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(summaryBody.safe_command_boundary.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBeGreaterThanOrEqual(2);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status translates UVC transport error diagnosis", async () => {
    let healthRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_diagnosis: {
            status: "uvc_transport_error_not_exclusive",
            plain_hint: "不是页面独占：USB Composite Device: DV20 USB 当前无人占用，但内核日志已有 UVC/USB 传输错误；检查 USB 线、接口、摄像头供电或换 known-good UVC 复测。",
            next_action: "check usb cable port power or known good uvc",
            not_exclusive: true,
          },
          uvc_kernel_diagnostics: {
            status: "uvc_usb_transport_errors_observed",
            transport_error_count: 44,
            latest_transport_error: "[777992.581028] usb 3-1: device descriptor read/all, error -71",
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.preview_status).toBe("source_first_frame_failed");
      expect(statusBody.source_diagnosis_status).toBe("uvc_transport_error_not_exclusive");
      expect(statusBody.source_diagnosis_next_action).toBe("check usb cable port power or known good uvc");
      expect(statusBody.source_diagnosis_next_action_plain).toBe("检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.preview_next_action_plain).toBe("检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.camera_wysiwyg_next_action_plain).toBe("检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status translates full-speed USB diagnosis", async () => {
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_diagnosis: {
            status: "uvc_full_speed_usb_not_exclusive",
            plain_hint: "不是页面独占：USB Composite Device: DV20 USB 当前无人占用，但摄像头挂在 USB 12M full-speed，视频流会 STREAMON I/O error；换高速 USB 口/线、减少转接并确认供电后复测。",
            next_action: "move_camera_to_high_speed_usb_port_or_powered_hub",
            not_exclusive: true,
          },
          uvc_usb_topology: {
            status: "uvc_video_on_full_speed_usb",
            plain_hint: "USB Composite Device: DV20 USB 当前在 USB 12M full-speed 拓扑上，视频流容易 STREAMON I/O error。",
            next_action: "move_camera_to_high_speed_usb_port_or_powered_hub",
            video_usb_speed: "12M",
            kernel_usb_address: "6-1",
            video_interface_count: 2,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.preview_status).toBe("source_first_frame_failed");
      expect(statusBody.source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
      expect(statusBody.source_diagnosis_next_action).toBe("move_camera_to_high_speed_usb_port_or_powered_hub");
      expect(statusBody.source_diagnosis_next_action_plain).toBe("摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。");
      expect(statusBody.preview_next_action_plain).toBe("摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。");
      expect(statusBody.camera_wysiwyg_next_action_plain).toBe("摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。");
      expect(statusBody.uvc_usb_topology_status).toBe("uvc_video_on_full_speed_usb");
      expect(statusBody.uvc_usb_topology_video_usb_speed).toBe("12M");
      expect(statusBody.camera_usb_speed).toBe("12M");
      expect(statusBody.camera_usb_full_speed_detected).toBe(true);
      expect(statusBody.camera_hardware_action_required).toBe(true);
      expect(statusBody.camera_hardware_action_label).toBe("换高速USB后复测");
      expect(statusBody.camera_blocks_mapping_start).toBe(true);
      expect(statusBody.camera_blocks_free_move).toBe(false);
      expect(statusBody.camera_reprobe_after_hardware_action_required).toBe(true);
      expect(statusBody.camera_reprobe_sequence).toEqual([
        "/api/robot-control/camera/first-frame/probe",
        "/api/robot-control/camera/mjpeg/status",
        "/api/robot-control/summary",
      ]);
      expect(statusBody.fixed_camera_probe_endpoint).toBe("/api/robot-control/camera/first-frame/probe");
      expect(statusBody.fixed_camera_mjpeg_status_endpoint).toBe("/api/robot-control/camera/mjpeg/status");
      expect(statusBody.fixed_summary_endpoint).toBe("/api/robot-control/summary");
      expect(statusBody.camera_recovery_sends_motion).toBe(false);
      expect(statusBody.camera_recovery_starts_map_runtime).toBe(false);
      expect(statusBody.camera_status_readback_only).toBe(true);
      expect(statusBody.hard_dangerous_true_fields).toEqual([]);
      expect(statusBody.robot_control_executed).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("Robot Control summary promotes camera device identity from source diagnosis when devices readback is empty", async () => {
    // live 形态：/api/camera/devices 可能只返回空列表，真实设备名在 health.source_diagnosis 里；summary 不能把结构化字段留成 not_loaded。
    const robotApi = await listenRobotApiReadbackByPath({
      "/api/camera/health": {
        payload: {
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          selected_path: "/dev/video1",
          selected_name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)",
          video_source: "/dev/video1",
          source_readiness: "first_frame_failed",
          source_failure_reason: "first_frame_total_timeout",
          source_summary: {
            current_selection: {
              selected_path: "/dev/video1",
              selected_name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)",
              selected_role: "video_capture",
              selected_sibling_video_nodes_summary: "/dev/video2=metadata",
              selected_sibling_video_node_count: 1,
            },
            candidates: [
              { path: "/dev/video0", name: "cedrus (platform:cedrus)", selected_role: "decoder" },
              { path: "/dev/video1", name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)", selected_role: "video_capture" },
              { path: "/dev/video2", name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)", selected_role: "metadata" },
            ],
          },
          media_diagnostics: {
            source_usage: {
              status: "not_in_use",
              owner_count: 0,
              owners: [],
              device: "/dev/video1",
            },
            source_diagnosis: {
              status: "uvc_no_frame_not_exclusive",
              selected_name: "USB Composite Device: DV20 USB  (usb-5310000.usb-1)",
              selected_is_uvc_or_usb: true,
              plain_hint: "不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧。",
              next_action: "check_usb_camera_input_power_or_known_good_uvc",
              not_exclusive: true,
            },
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
      "/api/camera/devices": {
        payload: {
          schema: "trashbot.local_webrtc_camera_devices.v1",
          status: "loaded",
          devices: [],
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        },
      },
    });
    try {
      const summary = await buildRobotControlSummary(robotApi.baseUrl);

      expect(summary.readback_summary.camera.selected_path).toBe("/dev/video1");
      expect(summary.readback_summary.camera.selected_name).toBe("USB Composite Device: DV20 USB");
      expect(summary.readback_summary.camera.selected_is_uvc_or_usb).toBe("true");
      expect(summary.readback_summary.camera.devices_status).toBe("loaded");
      expect(summary.readback_summary.camera.devices_effective_status).toBe("loaded_from_health_source_summary");
      expect(summary.readback_summary.camera.devices_endpoint_count).toBe("0");
      expect(summary.readback_summary.camera.devices_health_candidate_count).toBe("3");
      expect(summary.readback_summary.camera.devices_plain_hint).toContain("相机设备列表返回 0 个设备");
      expect(summary.readback_summary.camera.devices_plain_hint).toContain("相机健康检查已读到 3 个候选");
      expect(summary.readback_summary.camera.source_usage_status).toBe("not_in_use");
      expect(summary.readback_summary.camera.source_usage_owner_count).toBe("0");
      expect(summary.readback_summary.camera.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(summary.readback_summary.camera.camera_wysiwyg_status_plain).toContain("USB Composite Device: DV20 USB");
      expect(summary.safe_command_boundary.robot_control_executed).toBe(false);
    } finally {
      await robotApi.close();
    }
  });

  it("workstation camera MJPEG status treats first-frame total timeout as non-exclusive no-frame material", async () => {
    // live 7001 会出现 first_frame_total_timeout；即使 health 没给现成 diagnosis，PC 也要把它解释成源头无帧而非浏览器独占。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "ready",
          video_source: "/dev/video1",
          selected_name: "USB Composite Device: DV20 USB",
          source_readiness: "source_selected_not_probed",
          source_failure_reason: "first_frame_total_timeout",
          source_usage: {
            status: "not_in_use",
            owner_count: 0,
            owners: [],
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(statusBody.last_remote_http_status).toBe(200);
      expect(statusBody.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(statusBody.source_diagnosis_plain_hint).toBe("不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");
      expect(statusBody.source_readiness).toBe("first_frame_failed");
      expect(statusBody.source_failure_reason).toBe("first_frame_total_timeout");
      expect(statusBody.preview_status).toBe("source_first_frame_failed");
      expect(statusBody.preview_plain_hint).toBe("不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.preview_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("waits for slower camera health before returning MJPEG source diagnosis", async () => {
    // 真实上位机 camera health 偶发超过 2.5s；status 要和 summary 共用宽读取窗口，否则普通首屏会丢掉“不是独占”的诊断。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        setTimeout(() => {
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({
            schema: "trashbot.local_webrtc_camera_smoke.v1",
            status: "source_first_frame_failed",
            source_readiness: "first_frame_failed",
            source_failure_reason: "capture_read_returned_false",
            source_diagnosis: {
              status: "uvc_no_frame_not_exclusive",
              plain_hint: "不是页面独占：慢 health 返回后仍证明 UVC 没有输出视频帧。",
              next_action: "check_usb_camera_input_power_or_known_good_uvc",
              not_exclusive: true,
            },
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
            robot_control_executed: false,
          }));
        }, 2700);
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.last_failure_reason).toBe("camera_source_first_frame_failed");
      expect(statusBody.last_remote_http_status).toBe(200);
      expect(statusBody.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(statusBody.source_diagnosis_plain_hint).toBe("不是页面独占：慢 health 返回后仍证明 UVC 没有输出视频帧。");
      expect(statusBody.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  }, 10_000);

  it("workstation camera MJPEG status reports selected source diagnosis without opening the stream", async () => {
    // live 形态：摄像头已选中且没人占用，但还没读首帧；共享状态要把下一步讲清楚，不应要求用户先打开高级诊断。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_not_probed",
          source_readiness: "source_selected_not_probed",
          source_failure_reason: "",
          source_usage: { status: "not_in_use", owner_count: 0, owners: [] },
          source_diagnosis: {
            status: "source_selected_not_probed",
            plain_hint: "USB Composite Device: DV20 USB 已选中但还没读过首帧；打开共享预览或运行首帧检查。",
            next_action: "open_shared_preview_or_run_first_frame_probe",
            not_exclusive: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.last_failure_reason).toBe("");
      expect(statusBody.last_remote_http_status).toBe(200);
      expect(statusBody.last_failure_at_ms).toBe(null);
      expect(statusBody.source_diagnosis_status).toBe("source_selected_not_probed");
      expect(statusBody.source_diagnosis_plain_hint).toBe("USB Composite Device: DV20 USB 已选中但还没读过首帧；打开共享预览或运行首帧检查。");
      expect(statusBody.source_diagnosis_next_action).toBe("open_shared_preview_or_run_first_frame_probe");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");
      expect(statusBody.source_readiness).toBe("source_selected_not_probed");
      expect(statusBody.source_failure_reason).toBe("none");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status translates open shared preview action after source first-frame is observed", async () => {
    // 源首帧 ready 但页面尚未打开预览时，status 只读接口也要给中文下一步，且不能主动打开 MJPEG 上游。
    let healthRequestCount = 0;
    let mjpegRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "ready",
          source_readiness: "first_frame_observed",
          source_failure_reason: "none",
          source_usage: { status: "not_in_use", owner_count: 0, owners: [] },
          source_diagnosis: {
            status: "first_frame_observed",
            plain_hint: "USB Composite Device: DV20 USB 已读到真实首帧，可继续看实时预览。",
            next_action: "open_shared_preview",
            not_exclusive: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        mjpegRequestCount += 1;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;

      expect(statusResponse.status).toBe(200);
      expect(statusBody.source_diagnosis_status).toBe("first_frame_observed");
      expect(statusBody.source_diagnosis_next_action).toBe("open_shared_preview");
      expect(statusBody.source_diagnosis_next_action_plain).toBe("打开共享实时预览；页面会复用同一条上游流。");
      expect(statusBody.source_readiness).toBe("first_frame_observed");
      expect(statusBody.preview_status).toBe("idle_not_started");
      expect(statusBody.robot_control_executed).toBe(false);
      expect(healthRequestCount).toBe(1);
      expect(mjpegRequestCount).toBe(0);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG status and summary remember the latest upstream failure", async () => {
    // 真实现场若上位机 MJPEG 返回 502，首屏不能退化成“没人观看”；要留下最近失败原因。
    let upstreamRequestCount = 0;
    let healthRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/health") {
        healthRequestCount += 1;
        res.statusCode = 200;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "capture_read_returned_false",
          source_diagnosis: {
            status: "uvc_no_frame_not_exclusive",
            plain_hint: "不是页面独占：USB Composite Device 当前没人占用，但 UVC 设备没有输出视频帧。",
            next_action: "check_usb_camera_input_power_or_known_good_uvc",
            not_exclusive: true,
          },
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          robot_control_executed: false,
        }));
        return;
      }
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        upstreamRequestCount += 1;
        res.statusCode = 502;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          error: "camera_mjpeg_proxy_failed",
          relay: {
            last_failure_reason: "camera_mjpeg_http_status_503",
            last_error_payload: {
              failure_reason: "first_frame_total_timeout",
              first_frame_format_attempts: [
                { label: "MJPG@640x480@15", status: "first_frame_unreadable" },
                { label: "YUYV@640x480@22", status: "first_frame_unreadable" },
                { label: "default@current", status: "first_frame_unreadable" },
              ],
            },
          },
        }));
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const mjpegResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const mjpegBody = await mjpegResponse.json() as { error: string; remote_http_status: number };
      expect(mjpegResponse.status).toBe(502);
      expect(mjpegBody.error).toBe("camera_mjpeg_http_status_503");
      expect(mjpegBody.remote_http_status).toBe(502);

      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.last_failure_reason).toBe("camera_mjpeg_http_status_503");
      expect(statusBody.last_remote_http_status).toBe(502);
      expect(typeof statusBody.last_failure_at_ms).toBe("number");
      expect(statusBody.source_diagnosis_status).toBe("uvc_no_frame_not_exclusive");
      expect(statusBody.source_diagnosis_plain_hint).toBe("不是页面独占：USB Composite Device 当前没人占用，但 UVC 设备没有输出视频帧。");
      expect(statusBody.source_diagnosis_plain_hint).not.toContain("not_loaded");
      expect(statusBody.source_diagnosis_next_action).toBe("check_usb_camera_input_power_or_known_good_uvc");
      expect(statusBody.source_diagnosis_not_exclusive).toBe("true");

      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = await summaryResponse.json() as RobotControlSummaryResponse;
      expect(summaryBody.readback_summary.camera.preview_status).toBe("idle_not_started");
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_mjpeg_http_status_503");
      expect(summaryBody.readback_summary.camera.shared_preview_last_remote_http_status).toBe("502");
      expect(summaryBody.readback_summary.camera.last_offer_format_attempts_summary).toBe("MJPG@640x480@15 无首帧；YUYV@640x480@22 无首帧；default@current 无首帧");
      expect(summaryBody.readback_summary.camera.source_diagnosis_plain_hint).not.toContain("not_loaded");
      expect(Number(summaryBody.readback_summary.camera.shared_preview_last_failure_at_ms)).toBeGreaterThan(0);
      expect(summaryBody.safe_command_boundary.robot_control_executed).toBe(false);
      expect(upstreamRequestCount).toBe(1);
      expect(healthRequestCount).toBeGreaterThanOrEqual(1);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera MJPEG proxy times out hanging upstream without leaving users waiting", async () => {
    // live 相机无帧时上游可能一直不返回 multipart 头；PC 必须快速写明共享预览超时。
    const previousTimeout = process.env.ROBER_CAMERA_MJPEG_UPSTREAM_TIMEOUT_MS;
    process.env.ROBER_CAMERA_MJPEG_UPSTREAM_TIMEOUT_MS = "150";
    let upstreamRequestCount = 0;
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        upstreamRequestCount += 1;
        res.on("close", () => undefined);
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.closeAllConnections?.();
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const mjpegResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const mjpegBody = await mjpegResponse.json() as { error: string; remote_http_status: number | null };
      expect(mjpegResponse.status).toBe(502);
      expect(mjpegBody.error).toBe("camera_mjpeg_upstream_timeout");
      expect(mjpegBody.remote_http_status).toBe(null);

      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;
      expect(statusBody.proxy_status).toBe("status_loaded");
      expect(statusBody.client_count).toBe(0);
      expect(statusBody.upstream_active).toBe(false);
      expect(statusBody.last_failure_reason).toBe("camera_mjpeg_upstream_timeout");
      expect(statusBody.last_remote_http_status).toBe(null);
      expect(typeof statusBody.last_failure_at_ms).toBe("number");

      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = await summaryResponse.json() as RobotControlSummaryResponse;
      expect(summaryBody.readback_summary.camera.shared_preview_last_failure_reason).toBe("camera_mjpeg_upstream_timeout");
      expect(summaryBody.readback_summary.camera.shared_preview_last_remote_http_status).toBe("none");
      expect(summaryBody.safe_command_boundary.robot_control_executed).toBe(false);
      expect(upstreamRequestCount).toBe(1);
    } finally {
      if (previousTimeout === undefined) {
        delete process.env.ROBER_CAMERA_MJPEG_UPSTREAM_TIMEOUT_MS;
      } else {
        process.env.ROBER_CAMERA_MJPEG_UPSTREAM_TIMEOUT_MS = previousTimeout;
      }
      await workstation.close();
      await upstream.close();
    }
  }, 5000);

  it("workstation camera MJPEG proxy normalizes upstream socket read timeout", async () => {
    // 8787 relay 可能把 8088 无帧表现成 aiohttp socket 文本；PC 首屏要继续显示“上游等不到画面”。
    const upstreamServer = http.createServer((req, res) => {
      if (req.method === "GET" && req.url === "/api/camera/mjpeg") {
        res.statusCode = 502;
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
          error: "camera_mjpeg_proxy_failed",
          relay: {
            last_failure_reason: "Timeout on reading data from socket",
          },
        }));
        return;
      }
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: "not_found" }));
    });
    const upstream = await new Promise<{ baseUrl: string; close: () => Promise<void> }>((resolve) => {
      upstreamServer.listen(0, "127.0.0.1", () => {
        const address = upstreamServer.address();
        const port = typeof address === "object" && address ? address.port : 0;
        resolve({
          baseUrl: `http://127.0.0.1:${port}`,
          close: () => new Promise((closeResolve, closeReject) => {
            upstreamServer.close((error) => (error ? closeReject(error) : closeResolve()));
          }),
        });
      });
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const mjpegResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const mjpegBody = await mjpegResponse.json() as { error: string; remote_http_status: number };
      expect(mjpegResponse.status).toBe(502);
      expect(mjpegBody.error).toBe("camera_mjpeg_upstream_timeout");
      expect(mjpegBody.remote_http_status).toBe(502);

      const statusResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/mjpeg/status?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const statusBody = await statusResponse.json() as RobotControlCameraMjpegStatusResponse;
      expect(statusBody.last_failure_reason).toBe("camera_mjpeg_upstream_timeout");
      expect(statusBody.last_remote_http_status).toBe(502);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera first-frame probe uses quick source check without backend smoke", async () => {
    // 普通首屏检查画面不能默认启动 ffmpeg/v4l2 后端矩阵，否则失败时会长时间占住摄像头。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/health": {
        method: "GET",
        payload: {
          schema: "trashbot.local_webrtc_camera_smoke.v1",
          status: "source_not_probed",
          source_readiness: "source_selected_not_probed",
          video_source: "/dev/video1",
          source_usage: { status: "not_in_use", owner_count: 0, owners: [] },
          source_diagnosis: {
            status: "source_selected_not_probed",
            plain_hint: "USB camera 已选中但还没读过首帧。",
            next_action: "open_shared_preview_or_run_first_frame_probe",
            not_exclusive: true,
          },
          safe_to_control: false,
          robot_control_executed: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/camera/first-frame/probe": {
        statusCode: 503,
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe_proxy",
          status: "open_failed",
          probe_payload: {
            schema: "trashbot.camera_first_frame_probe.v1",
            status: "open_failed",
            open_ok: false,
            read_ok: false,
            visible_content_proven: false,
            safe_to_control: false,
            robot_control_executed: false,
            delivery_success: false,
            primary_actions_enabled: false,
          },
          fallback_attempts: [
            {
              status: "open_failed",
              fourcc: "MJPG",
              width: 640,
              height: 480,
              open_ok: false,
              read_ok: false,
              failure_reason: "opencv_capture_not_opened",
            },
          ],
          safe_to_control: false,
          robot_control_executed: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/camera/first-frame/probe?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
      });
      const body = (await response.json()) as {
        proxy_status: string;
        remote_http_status: number;
        status: string;
        failure_reason: string;
        probe_key_values: {
          open_ok: string;
          visible_content_proven: string;
          fallback_attempt_count: string;
          fallback_attempts_summary: string;
        };
        safe_to_control: boolean;
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("probe_failed");
      expect(body.remote_http_status).toBe(503);
      expect(body.failure_reason).toBe("probe_http_status_503");
      expect(body.status).toBe("open_failed");
      expect(body.probe_key_values.open_ok).toBe("false");
      expect(body.probe_key_values.visible_content_proven).toBe("false");
      expect(body.probe_key_values.fallback_attempt_count).toBe("1");
      expect(body.probe_key_values.fallback_attempts_summary).toContain("MJPG@640x480:open_failed/opencv_capture_not_opened");
      expect(body.safe_to_control).toBe(false);
      expect(upstream.receivedBodies["/api/camera/first-frame/probe"]).toEqual([
        {
          include_backend_smoke: false,
          auto_format_fallback: true,
          timeout_s: 3,
          read_call_timeout_s: 4,
        },
      ]);
      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = (await summaryResponse.json()) as {
        readback_summary: {
          camera: {
            source_readiness: string;
            source_failure_reason: string;
            first_frame_probe_status: string;
            first_frame_probe_open_ok: string;
            first_frame_probe_read_ok: string;
            first_frame_probe_visible_content_proven: string;
          };
        };
        safe_to_control: boolean;
      };

      expect(summaryBody.readback_summary.camera.source_readiness).toBe("first_frame_failed");
      expect(summaryBody.readback_summary.camera.source_failure_reason).toBe("probe_http_status_503");
      expect(summaryBody.readback_summary.camera.first_frame_probe_status).toBe("open_failed");
      expect(summaryBody.readback_summary.camera.first_frame_probe_open_ok).toBe("false");
      expect(summaryBody.readback_summary.camera.first_frame_probe_read_ok).toBe("false");
      expect(summaryBody.readback_summary.camera.first_frame_probe_visible_content_proven).toBe("false");
      expect(summaryBody.safe_to_control).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera first-frame probe can request backend smoke for explicit diagnostics", async () => {
    // 用户主动点击检查画面时允许跑 v4l2/ffmpeg 矩阵，帮助确认不是浏览器或页面独占问题。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/first-frame/probe": {
        statusCode: 503,
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe_proxy",
          status: "first_frame_timeout",
          probe_payload: {
            schema: "trashbot.camera_first_frame_probe.v1",
            status: "first_frame_timeout",
            device: "/dev/video1",
            open_ok: true,
            read_ok: false,
            first_frame_timeout: true,
            failure_reason: "deadline_expired",
            visible_content_proven: false,
            backend_smoke: {
              executed: true,
              frame_observed: false,
              status: "backend_no_frame_observed",
              attempts: [
                { name: "v4l2_mjpg_mmap", ok: false, output_bytes: 0 },
                { name: "ffmpeg_mjpg", ok: false, output_bytes: 0 },
              ],
            },
            safe_to_control: false,
            robot_control_executed: false,
            delivery_success: false,
            primary_actions_enabled: false,
          },
          fallback_attempts: [
            {
              status: "first_frame_timeout",
              fourcc: "MJPG",
              width: 640,
              height: 480,
              open_ok: true,
              read_ok: false,
              failure_reason: "deadline_expired",
            },
          ],
          safe_to_control: false,
          robot_control_executed: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
      "/api/camera/health": {
        method: "GET",
        payload: {
          status: "source_first_frame_failed",
          source_readiness: "first_frame_failed",
          source_failure_reason: "deadline_expired",
          current_selection: {
            selected_name: "USB Composite Device: DV20 USB",
            selected_path: "/dev/video1",
            selected_is_uvc_or_usb: true,
          },
          source_diagnosis: {
            status: "uvc_full_speed_usb_not_exclusive",
            plain_hint: "不是页面独占：DV20 USB 当前没人占用，但 UVC 设备没有输出视频帧。",
            next_action: "check_usb_camera_input_power_or_known_good_uvc",
            not_exclusive: true,
          },
          source_usage: {
            status: "free",
            owner_count: 0,
          },
          uvc_usb_topology: {
            status: "uvc_video_on_full_speed_usb",
            video_usb_speed: "12M",
            plain_hint: "摄像头挂在 USB full-speed。",
            next_action: "move_camera_to_high_speed_usb",
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/camera/first-frame/probe?baseUrl=${encodeURIComponent(upstream.baseUrl)}&backendSmoke=1`, {
        method: "POST",
      });
      const body = (await response.json()) as {
        proxy_status: string;
        failure_reason: string;
        camera_first_frame_ready: boolean;
        frame_observed: boolean;
        source_diagnosis_status: string;
        source_diagnosis_not_exclusive: string;
        source_diagnosis_next_action_plain: string;
        camera_usb_speed: string;
        camera_usb_full_speed_detected: boolean;
        camera_hardware_action_required: boolean;
        camera_hardware_action_label: string;
        camera_blocks_mapping_start: boolean;
        camera_blocks_free_move: boolean;
        sends_motion_when_clicked: boolean;
        starts_map_runtime: boolean;
        robot_control_executed: boolean;
        dangerous_true_fields: string[];
        probe_key_values: {
          backend_smoke_status: string;
          backend_frame_observed: string;
          backend_attempts: string;
          failure_reason: string;
        };
        safe_to_control: boolean;
      };

      expect(response.status).toBe(502);
      expect(body.proxy_status).toBe("probe_failed");
      expect(body.failure_reason).toBe("deadline_expired");
      expect(body.probe_key_values.failure_reason).toBe("deadline_expired");
      expect(body.probe_key_values.backend_smoke_status).toBe("backend_no_frame_observed");
      expect(body.probe_key_values.backend_frame_observed).toBe("false");
      expect(body.probe_key_values.backend_attempts).toBe("2");
      expect(body.camera_first_frame_ready).toBe(false);
      expect(body.frame_observed).toBe(false);
      expect(body.source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
      expect(body.source_diagnosis_not_exclusive).toBe("true");
      expect(body.source_diagnosis_next_action_plain).toContain("known-good UVC");
      expect(body.camera_usb_speed).toBe("12M");
      expect(body.camera_usb_full_speed_detected).toBe(true);
      expect(body.camera_hardware_action_required).toBe(true);
      expect(body.camera_hardware_action_label).toBe("换高速USB后复测");
      expect(body.camera_blocks_mapping_start).toBe(true);
      expect(body.camera_blocks_free_move).toBe(false);
      expect(body.sends_motion_when_clicked).toBe(false);
      expect(body.starts_map_runtime).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(body.dangerous_true_fields).toEqual([]);
      expect(body.safe_to_control).toBe(false);
      expect(upstream.receivedBodies["/api/camera/first-frame/probe"]).toEqual([
        {
          include_backend_smoke: true,
          auto_format_fallback: true,
          timeout_s: 3,
          read_call_timeout_s: 4,
        },
      ]);
      const summaryResponse = await fetch(`${workstation.baseUrl}/api/robot-control/summary?baseUrl=${encodeURIComponent(upstream.baseUrl)}`);
      const summaryBody = await summaryResponse.json() as RobotControlSummaryResponse;

      expect(summaryBody.readback_summary.camera.first_frame_probe_status).toBe("first_frame_timeout");
      expect(summaryBody.readback_summary.camera.first_frame_probe_backend_smoke_status).toBe("backend_no_frame_observed");
      expect(summaryBody.readback_summary.camera.first_frame_probe_backend_frame_observed).toBe("false");
      expect(summaryBody.readback_summary.camera.first_frame_probe_backend_attempts).toBe("2");
      expect(summaryBody.readback_summary.camera.source_diagnosis_status).toBe("uvc_full_speed_usb_not_exclusive");
      expect(summaryBody.readback_summary.camera.source_diagnosis_plain_hint).toContain("USB full-speed");
      expect(summaryBody.readback_summary.camera.source_diagnosis_not_exclusive).toBe("true");
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera first-frame probe reports configured proxy timeout without losing robot base url", async () => {
    // PC 代理超时应暴露稳定的现场原因；否则普通首屏会把上车 fallback 矩阵误读成 baseUrl 未加载。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/first-frame/probe": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.camera_first_frame_probe_proxy",
          status: "would_not_return_when_aborted",
          safe_to_control: false,
          robot_control_executed: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout").mockImplementation(() => {
      const controller = new AbortController();
      controller.abort();
      return controller.signal;
    });
    try {
      const quickResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/first-frame/probe?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
      });
      const quickBody = await quickResponse.json() as RobotControlCameraFirstFrameProbeProxyResponse;

      expect(timeoutSpy).toHaveBeenLastCalledWith(60_000);
      expect(quickResponse.status).toBe(502);
      expect(quickBody.proxy_status).toBe("probe_failed");
      expect(quickBody.failure_reason).toBe("fetch_timeout_60000ms");
      expect(quickBody.blocked_reasons).toEqual(["fetch_timeout_60000ms"]);
      expect(quickBody.normalized_base_url).toBe(upstream.baseUrl);
      expect(quickBody.remote_http_status).toBeNull();
      expect(quickBody.robot_control_executed).toBe(false);

      const smokeResponse = await fetch(`${workstation.baseUrl}/api/robot-control/camera/first-frame/probe?baseUrl=${encodeURIComponent(upstream.baseUrl)}&backendSmoke=1`, {
        method: "POST",
      });
      const smokeBody = await smokeResponse.json() as RobotControlCameraFirstFrameProbeProxyResponse;

      expect(timeoutSpy).toHaveBeenLastCalledWith(75_000);
      expect(smokeResponse.status).toBe(502);
      expect(smokeBody.proxy_status).toBe("probe_failed");
      expect(smokeBody.failure_reason).toBe("fetch_timeout_75000ms");
      expect(smokeBody.blocked_reasons).toEqual(["fetch_timeout_75000ms"]);
      expect(smokeBody.normalized_base_url).toBe(upstream.baseUrl);
      expect(smokeBody.remote_http_status).toBeNull();
      expect(smokeBody.robot_control_executed).toBe(false);
    } finally {
      timeoutSpy.mockRestore();
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base manual proxy clamps request and requires confirm_hil_checklist", async () => {
    // 受控点动代理只允许固定 manual endpoint，并且必须经过安全确认 gate 与速度/时长 clamp。
    const upstream = await listenRobotBaseCommandApi({
      "/api/base/manual": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_manual",
          status: "accepted",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    }, {
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          evidence_ref: "field-hil-manual-preflight",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-manual.mp4",
            visible_content_proven: true,
            camera_artifacts_ref: "runtime/camera/latest_metrics.json",
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_ref: "runtime/wave_rover_feedback_debug.jsonl",
            physical_motion_lidar_delta_proven: true,
            scan_delta_ref: "runtime/scan_delta/latest_metrics.json",
            delivery_success: false,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const rejected = await fetch(`${workstation.baseUrl}/api/robot-control/base/manual?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "forward", speed: 9, duration_ms: 9999, confirm_hil_checklist: false }),
      });
      const rejectedBody = (await rejected.json()) as { proxy_status: string; failure_reason: string; safe_to_control: boolean };
      expect(rejected.status).toBe(400);
      expect(rejectedBody.proxy_status).toBe("command_rejected");
      expect(rejectedBody.failure_reason).toBe("confirm_hil_checklist_required");
      expect(rejectedBody.safe_to_control).toBe(false);

      const forwarded = await fetch(`${workstation.baseUrl}/api/robot-control/base/manual?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "forward", speed: 9, duration_ms: 9999, confirm_hil_checklist: true }),
      });
      const forwardedBody = (await forwarded.json()) as {
        proxy_status: string;
        applied_direction: string;
        clamped_speed_mps: number;
        clamped_duration_ms: number;
        operator_report_preflight: { status: string; missing_fields: string[]; evidence_ref: string };
      };
      expect(forwarded.status).toBe(200);
      expect(forwardedBody.proxy_status).toBe("command_forwarded");
      expect(forwardedBody.applied_direction).toBe("forward");
      expect(forwardedBody.clamped_speed_mps).toBe(0.12);
      expect(forwardedBody.clamped_duration_ms).toBe(800);
      expect(forwardedBody.operator_report_preflight.status).toBe("not_required_for_confirmed_manual");
      expect(forwardedBody.operator_report_preflight.missing_fields).toEqual([]);
      expect(forwardedBody.operator_report_preflight.evidence_ref).toBe("not_required_for_confirmed_manual");
      expect(upstream.receivedBodies["/api/base/manual"]).toEqual([
        {
          direction: "forward",
          speed: 0.12,
          duration_ms: 800,
          command_mode: "ros",
          confirm_hil_checklist: true,
        },
      ]);
      expect(upstream.receivedGets).not.toContain("/api/operator/report");
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base manual proxy no longer blocks confirmed low-speed motion on operator report material", async () => {
    // 最新普通首屏口径：勾安全确认即可低速手控；operator report 材料不再阻塞 manual pulse。
    const upstream = await listenRobotBaseCommandApi({
      "/api/base/manual": {
        payload: { schema: "trashbot.upper_robot_api.v1.base_manual", status: "should_not_be_called" },
      },
    }, {
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          evidence_ref: "field-hil-incomplete",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-incomplete.mp4",
            visible_content_proven: true,
            camera_artifacts_ref: "runtime/camera/latest_metrics.json",
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_ref: "",
            physical_motion_lidar_delta_proven: false,
            scan_delta_ref: "",
            delivery_success: true,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/manual?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "forward", speed: 0.08, duration_ms: 500, confirm_hil_checklist: true }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        failure_reason: string;
        operator_report_preflight: { status: string; missing_fields: string[]; failure_reason: string };
        robot_control_executed: boolean;
        safe_to_control: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("command_forwarded");
      expect(body.failure_reason).toBe("");
      expect(body.operator_report_preflight.status).toBe("not_required_for_confirmed_manual");
      expect(body.operator_report_preflight.missing_fields).toEqual([]);
      expect(body.safe_to_control).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).not.toContain("/api/operator/report");
      expect(upstream.receivedBodies["/api/base/manual"]).toEqual([
        {
          direction: "forward",
          speed: 0.08,
          duration_ms: 500,
          command_mode: "ros",
          confirm_hil_checklist: true,
        },
      ]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation first-jog proxy forwards confirmed low-speed motion without visual material", async () => {
    // 勾安全确认即可低速试动；相机/外部视频不再是发车前置。
    const upstream = await listenRobotBaseCommandApi({
      "/api/base/manual": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_manual",
          status: "accepted",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    }, {
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          evidence_ref: "field-hil-first-jog-missing-visual",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          structured_hil_claims: {
            external_video_recorded: false,
            external_video_ref: "",
            visible_content_proven: false,
            camera_artifacts_ref: "",
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_ref: "",
            physical_motion_lidar_delta_proven: false,
            scan_delta_ref: "",
            delivery_success: false,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/first-jog?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "forward", speed: 0.08, duration_ms: 500, confirm_hil_checklist: true }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        failure_reason: string;
        operator_report_preflight: { status: string; required_fields: string[]; missing_fields: string[]; failure_reason: string };
        robot_control_executed: boolean;
        applied_direction: string;
        clamped_speed_mps: number;
        clamped_duration_ms: number;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("command_forwarded");
      expect(body.failure_reason).toBe("");
      expect(body.operator_report_preflight.status).toBe("not_required_for_confirmed_manual");
      expect(body.operator_report_preflight.required_fields).toEqual([]);
      expect(body.operator_report_preflight.missing_fields).toEqual([]);
      expect(body.operator_report_preflight.missing_fields).not.toContain("wheel_feedback_lr_nonzero_proven");
      expect(body.operator_report_preflight.missing_fields).not.toContain("physical_motion_lidar_delta_proven");
      expect(body.robot_control_executed).toBe(false);
      expect(body.applied_direction).toBe("forward");
      expect(body.clamped_speed_mps).toBe(0.08);
      expect(body.clamped_duration_ms).toBe(500);
      expect(upstream.receivedGets).not.toContain("/api/operator/report");
      expect(upstream.receivedBodies["/api/base/manual"]).toEqual([
        {
          direction: "forward",
          speed: 0.08,
          duration_ms: 500,
          command_mode: "ros",
          confirm_hil_checklist: true,
        },
      ]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation first-jog proxy forwards one clamped manual command when visual preflight is present", async () => {
    // first-jog 只解开首次运动证据死锁；仍只转发固定 /api/base/manual 且响应保持 fail-closed 顶层。
    const upstream = await listenRobotBaseCommandApi({
      "/api/base/manual": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_manual",
          status: "accepted",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    }, {
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "loaded",
          operator_present: true,
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          evidence_ref: "field-hil-first-jog-visual",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-first-jog.mp4",
            visible_content_proven: false,
            camera_artifacts_ref: "",
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_ref: "",
            physical_motion_lidar_delta_proven: false,
            scan_delta_ref: "",
            delivery_success: false,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/first-jog?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "left", speed: 9, duration_ms: 9999, confirm_hil_checklist: true }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        applied_direction: string;
        clamped_speed_mps: number;
        clamped_duration_ms: number;
        operator_report_preflight: { status: string; missing_fields: string[]; evidence_ref: string };
        robot_control_executed: boolean;
        safe_to_control: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("command_forwarded");
      expect(body.applied_direction).toBe("left");
      expect(body.clamped_speed_mps).toBe(0.12);
      expect(body.clamped_duration_ms).toBe(800);
      expect(body.operator_report_preflight.status).toBe("not_required_for_confirmed_manual");
      expect(body.operator_report_preflight.missing_fields).toEqual([]);
      expect(body.operator_report_preflight.evidence_ref).toBe("not_required_for_confirmed_manual");
      expect(body.robot_control_executed).toBe(false);
      expect(body.safe_to_control).toBe(false);
      expect(upstream.receivedGets).not.toContain("/api/operator/report");
      expect(upstream.receivedBodies["/api/base/manual"]).toEqual([
        {
          direction: "left",
          speed: 0.12,
          duration_ms: 800,
          command_mode: "ros",
          confirm_hil_checklist: true,
        },
      ]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation operator report route forwards only fixed report endpoint and keeps top-level flags false", async () => {
    // Express route 只把白名单材料提交给上位机 /api/operator/report，不接受 endpoint/method/body 扩展。
    const upstream = await listenRobotProofRefreshApi({
      "/api/operator/report": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.operator_report",
          status: "operator_report_saved",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
          structured_hil_claims: {
            delivery_success: true,
          },
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/operator/report?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operator_present: true,
          evidence_ref: "field-hil-route-submit",
          physical_clearance_confirmed: true,
          emergency_stop_ready: true,
          observed_motion: false,
          observed_stop: true,
          reported_at: "2026-06-11T06:20:00.000Z",
          structured_hil_claims: {
            external_video_recorded: true,
            external_video_ref: "phone-video-route.mp4",
            delivery_success: true,
            site_state: "field_operator_claim_ready_for_review",
          },
        }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        safe_to_control: boolean;
        delivery_success: boolean;
        primary_actions_enabled: boolean;
        robot_control_executed: boolean;
        structured_hil_claims: { delivery_success?: boolean };
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("report_forwarded");
      expect(body.safe_to_control).toBe(false);
      expect(body.delivery_success).toBe(false);
      expect(body.primary_actions_enabled).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(body.structured_hil_claims.delivery_success).toBe(true);
      expect(upstream.receivedBodies["/api/operator/report"]).toHaveLength(1);
      expect(Object.keys(upstream.receivedBodies)).toEqual(["/api/operator/report"]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base feedback samples expose top-level wheel raw aliases without motion", async () => {
    // 只读反馈采样是现场排查 wheel raw 的入口；顶层 alias 必须和 sample_key_values 一致，且不能触发 manual/Nav2。
    const upstream = await listenRobotBaseCommandApi(
      {
        "/api/base/feedback-samples": {
          payload: {
            schema: "trashbot.upper_robot_api.v1.base_feedback_samples_result",
            status: "loaded",
            safe_to_control: false,
            robot_control_executed: false,
            requested_sample_count: 3,
            completed_sample_count: 3,
            t1001_observed_count: 2,
            all_samples_observed_t1001: false,
            partial_samples_observed_t1001: true,
            wheel_feedback_lr_nonzero_proven: false,
            wheel_feedback_nonzero_observed: false,
            observed_feedback_types: [1001],
            sends_motion_commands: false,
            feedback_ack: {
              t1001_observed: true,
            },
            wheel_feedback_summary: {
              nonzero_frame_count: 0,
              source: "vendor_t1001_L_R",
              latest_pair: {
                left_speed: 0,
                right_speed: 0,
              },
            },
          },
        },
      },
      {},
    );
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/feedback-samples?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
      });
      const body = (await response.json()) as {
        proxy_status: string;
        sample_key_values: Record<string, string>;
        wheel_raw_left: string;
        wheel_raw_right: string;
        latest_raw_left: string;
        latest_raw_right: string;
        base_feedback_lr_nonzero_proven: string;
        wheel_feedback_lr_nonzero_proven: string;
        wheel_feedback_source: string;
        wheel_feedback_plain_hint: string;
        wheel_feedback_next_action: string;
        sends_motion_commands: boolean;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("samples_forwarded");
      expect(body.sample_key_values.wheel_feedback_latest_left_speed).toBe("0");
      expect(body.sample_key_values.wheel_feedback_latest_right_speed).toBe("0");
      expect(body.wheel_raw_left).toBe("0");
      expect(body.wheel_raw_right).toBe("0");
      expect(body.latest_raw_left).toBe("0");
      expect(body.latest_raw_right).toBe("0");
      expect(body.base_feedback_lr_nonzero_proven).toBe("false");
      expect(body.wheel_feedback_lr_nonzero_proven).toBe("false");
      expect(body.wheel_feedback_source).toBe("vendor_t1001_L_R");
      expect(body.wheel_feedback_plain_hint).toContain("wheel raw L/R=0/0");
      expect(body.wheel_feedback_plain_hint).toContain("这不是运动命令");
      expect(body.wheel_feedback_next_action).toContain("勾选现场安全确认后低速试动");
      expect(body.sends_motion_commands).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/base/feedback-samples"]).toEqual([{
        sample_count: 3,
        sample_interval_s: 0.15,
        read_timeout_s: 0.25,
        read_window_s: 0.35,
      }]);
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base feedback samples GET returns latest wheel raw JSON without sampling POST", async () => {
    // summary/DOM 暴露的是固定 readback endpoint；现场脚本用 GET 读取时必须拿到 JSON，而不是 SPA HTML。
    const upstream = await listenRobotBaseCommandApi(
      {},
      {
        "/api/base/feedback-samples/latest": {
          payload: {
            schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
            status: "loaded",
            latest_result: {
              schema: "trashbot.upper_robot_api.v1.base_feedback_samples_result",
              status: "loaded",
              safe_to_control: false,
              robot_control_executed: false,
              requested_sample_count: 3,
              completed_sample_count: 3,
              t1001_observed_count: 3,
              all_samples_observed_t1001: true,
              partial_samples_observed_t1001: true,
              wheel_feedback_lr_nonzero_proven: true,
              wheel_feedback_nonzero_observed: true,
              observed_feedback_types: [1001],
              sends_motion_commands: false,
              feedback_ack: {
                t1001_observed: true,
              },
              wheel_feedback_summary: {
                nonzero_frame_count: 2,
                source: "vendor_t1001_L_R",
                latest_pair: {
                  left_speed: 12,
                  right_speed: 13,
                },
              },
            },
            safe_to_control: false,
            sends_motion_commands: false,
            robot_control_executed: false,
            wheel_feedback_lr_nonzero_proven: true,
          },
        },
      },
    );
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/feedback-samples?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "GET",
      });
      const body = (await response.json()) as {
        proxy_status: string;
        remote_endpoint: string;
        sample_key_values: Record<string, string>;
        wheel_raw_left: string;
        wheel_raw_right: string;
        latest_raw_left: string;
        latest_raw_right: string;
        base_feedback_lr_nonzero_proven: string;
        wheel_feedback_lr_nonzero_proven: string;
        sends_motion_commands: boolean;
        robot_control_executed: boolean;
      };

      expect(response.status).toBe(200);
      expect(response.headers.get("content-type")).toContain("application/json");
      expect(body.proxy_status).toBe("samples_forwarded");
      expect(body.remote_endpoint).toBe("/api/base/feedback-samples/latest");
      expect(body.sample_key_values.completed_sample_count).toBe("3");
      expect(body.sample_key_values.t1001_observed_count).toBe("3");
      expect(body.sample_key_values.wheel_feedback_latest_left_speed).toBe("12");
      expect(body.sample_key_values.wheel_feedback_latest_right_speed).toBe("13");
      expect(body.sample_key_values.wheel_feedback_source).toBe("vendor_t1001_L_R");
      expect(body.wheel_raw_left).toBe("12");
      expect(body.wheel_raw_right).toBe("13");
      expect(body.latest_raw_left).toBe("12");
      expect(body.latest_raw_right).toBe("13");
      expect(body.base_feedback_lr_nonzero_proven).toBe("true");
      expect(body.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(body.sends_motion_commands).toBe(false);
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedGets).toEqual(["/api/base/feedback-samples/latest"]);
      expect(upstream.receivedBodies["/api/base/feedback-samples"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedBodies["/api/nav2/goal/execute"]).toBeUndefined();
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base manual proxy captures fixed GET evidence around local checklist reject", async () => {
    // 本地拒绝也要采集 before/after 证据快照；它只读固定 GET，不发送非零运动。
    const upstream = await listenRobotBaseCommandApi(
      {},
      {
        "/api/base/status": {
          payload: {
            schema: "trashbot.upper_robot_api.v1.base_status",
            status: "base_ready",
            safe_to_control: false,
            delivery_success: false,
            primary_actions_enabled: false,
          },
        },
        "/api/base/feedback-samples/latest": {
          payload: {
            schema: "trashbot.upper_robot_api.v1.base_feedback_samples_latest",
            status: "feedback_ready",
            feedback_ack_status: "ack_observed",
            latest_t1001_observed_count: 2,
            wheel_feedback_lr_nonzero_proven: true,
            wheel_feedback_nonzero_observed: true,
          },
        },
        "/api/radar/status": {
          payload: { schema: "trashbot.upper_robot_api.v1.radar_status", status: "radar_ready" },
        },
        "/api/radar/scan-proof/latest": {
          payload: {
            schema: "trashbot.upper_robot_api.v1.radar_scan_proof",
            status: "scan_once_observed",
            scan_once_observed: true,
            tf_observed: true,
          },
        },
      },
    );
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/manual?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ direction: "forward", speed: 0.08, duration_ms: 500, confirm_hil_checklist: false }),
      });
      const body = (await response.json()) as {
        proxy_status: string;
        evidence_capture_status: string;
        evidence_capture_endpoints: Array<{ method: string; endpoint: string; phase: string; request_status: string }>;
        before_readback: Record<string, { key_values: Record<string, string> }>;
        after_readback: Record<string, { key_values: Record<string, string> }>;
        motion_evidence_summary: string;
        motion_evidence_gaps: string[];
        robot_control_executed: boolean;
      };
      expect(response.status).toBe(400);
      expect(body.proxy_status).toBe("command_rejected");
      expect(body.evidence_capture_status).toBe("captured");
      expect(body.evidence_capture_endpoints).toHaveLength(8);
      expect(body.evidence_capture_endpoints.every((endpoint) => endpoint.method === "GET")).toBe(true);
      expect(body.before_readback.base_status?.key_values.status).toBe("base_ready");
      expect(body.after_readback.base_feedback_samples_latest?.key_values.latest_t1001_observed_count).toBe("2");
      expect(body.after_readback.base_feedback_samples_latest?.key_values.wheel_feedback_lr_nonzero_proven).toBe("true");
      expect(body.motion_evidence_summary).toContain("not HIL pass");
      expect(body.motion_evidence_gaps).toEqual(expect.arrayContaining([
        "motion_command_not_forwarded",
        "physical_motion_lidar_delta_not_proven",
      ]));
      expect(body.motion_evidence_gaps).not.toContain("wheel_feedback_lr_nonzero_not_proven");
      expect(body.robot_control_executed).toBe(false);
      expect(upstream.receivedBodies["/api/base/manual"]).toBeUndefined();
      expect(upstream.receivedGets.filter((endpoint) => endpoint === "/api/base/status")).toHaveLength(2);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation base stop proxy stays fail-closed and allows stop without checklist", async () => {
    // stop 是唯一允许在未勾 checklist 时执行的动作，但仍然只能走固定 stop endpoint。
    const upstream = await listenRobotProofRefreshApi({
      "/api/base/stop": {
        payload: {
          schema: "trashbot.upper_robot_api.v1.base_stop",
          status: "stopped",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/base/stop?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ confirm_hil_checklist: false }),
      });
      const body = (await response.json()) as {
        command_kind: string;
        proxy_status: string;
        hil_checklist_gate_status: string;
        safe_to_control: boolean;
        primary_actions_enabled: boolean;
      };
      expect(response.status).toBe(200);
      expect(body.command_kind).toBe("stop");
      expect(body.proxy_status).toBe("command_forwarded");
      expect(body.hil_checklist_gate_status).toBe("stop_allowed_without_checklist");
      expect(body.safe_to_control).toBe(false);
      expect(body.primary_actions_enabled).toBe(false);
      expect(upstream.receivedBodies["/api/base/stop"]).toEqual([{}]);
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera offer proxy normalizes answer SDP line endings without changing semantics", async () => {
    // 真实上位机 answer 需要保留为浏览器可解析的 SDP；这里只做 CRLF 和末尾换行补齐。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/offer": {
        payload: {
          schema: "trashbot.local_webrtc_camera_offer.v1",
          status: "ready",
          peer_id: "peerSDP123",
          type: "answer",
          sdp: "v=0\nm=video 9 UDP/TLS/RTP/SAVPF 96\na=setup:active",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(`${workstation.baseUrl}/api/robot-control/camera/offer?baseUrl=${encodeURIComponent(upstream.baseUrl)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ type: "offer", sdp: "v=0\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\n" }),
      });
      const body = (await response.json()) as { answer: { sdp: string } | null; proxy_status: string };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("offer_forwarded");
      expect(body.answer?.sdp).toBe("v=0\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=setup:active\r\n");
    } finally {
      await workstation.close();
      await upstream.close();
    }
  });

  it("workstation camera close proxy only closes whitelisted peer endpoint and keeps safe flags false", async () => {
    // close proxy 只允许 peer_id 路径白名单，不开放任意 POST 代理或控制类字段透传。
    const upstream = await listenRobotCameraProxyApi({
      "/api/camera/peers/peerABC123/close": {
        payload: {
          schema: "trashbot.local_webrtc_camera_close.v1",
          status: "closed",
          peer_id: "peerABC123",
          safe_to_control: false,
          delivery_success: false,
          primary_actions_enabled: false,
        },
      },
    });
    const workstation = await listen(createWorkstationApp());
    try {
      const response = await fetch(
        `${workstation.baseUrl}/api/robot-control/camera/peers/peerABC123/close?baseUrl=${encodeURIComponent(upstream.baseUrl)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        },
      );
      const body = (await response.json()) as { proxy_status: string; status: string; safe_to_control: boolean };

      expect(response.status).toBe(200);
      expect(body.proxy_status).toBe("peer_closed");
      expect(body.status).toBe("closed");
      expect(body.safe_to_control).toBe(false);
    } finally {
      await workstation.close();
      await upstream.close();
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
