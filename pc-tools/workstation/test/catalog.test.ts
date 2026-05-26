import { describe, expect, it } from "vitest";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildO7OperatorConsoleAcceptanceResponse,
  buildO7OperatorConsoleResponse,
  buildO7LabelingPreview,
  buildO7RouteReplayPreview,
  buildO7SafeCommandPreview,
  buildO7VoicePreview,
  buildProofBoundary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "../src/server/catalog";

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
});
