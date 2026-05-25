import { describe, expect, it } from "vitest";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
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

function expectNoLegacyPythonGateSemantics(value: unknown) {
  // 这些字符串代表旧 Python gate 执行入口，Node/Vue 工作站响应中不应再出现。
  const payload = JSON.stringify(value);
  expect(payload).not.toContain("route_debug_web.py");
  expect(payload).not.toContain("test_route_debug_web.py");
  expect(payload).not.toContain("python -m");
  expect(payload).not.toContain("python3 ");
  expect(payload).not.toContain("route_gate");
  expect(payload).not.toContain("workstation_executes_python_gate");
  expect(payload).not.toContain("/cmd_vel");
  expect(payload).not.toContain("/dev/tty");
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
    expect(response.required_materials.map((material) => material.id)).toEqual([
      "feedback_T1001.log",
      "odom_once.jsonl",
      "imu_once.jsonl",
      "battery_once.jsonl",
      "operator_hil_report",
    ]);
    expect(response.groups.some((group) => group.group === "wave_rover_hil_packet_intake/pass")).toBe(true);
    const intakePass = response.groups.find((group) => group.group === "wave_rover_hil_packet_intake/pass");
    expect(intakePass?.present_materials).toContain("operator_hil_report");
    expect(intakePass?.coverage_counts.present).toBe(5);
    expect(intakePass?.status).toBe("material_coverage_complete_software_proof_only");
    const replayPass = response.groups.find((group) => group.group === "wave_rover_feedback_replay/pass");
    expect(replayPass?.missing_materials).toContain("operator_hil_report");
    expect(replayPass?.status).toBe("material_coverage_partial_software_proof_only");
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
    expect(response.vendor_facts_bounded).toContain("T=1/T=13/T=130/T=131/T=142/T=143 command IDs");
    expect(response.boundary_copy).toContain("coverage is not HIL pass");
    expect(JSON.stringify(response)).not.toContain("HIL pass true");
    expect(JSON.stringify(response)).not.toContain("/dev/tty");
    expectNoLegacyPythonGateSemantics(response);
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

  it("training and proof boundary do not claim real pipelines", async () => {
    // 占位入口必须明确未接真实训练/标注流水线。
    const training = await buildTrainingLabelingResponse();
    const boundary = buildProofBoundary();

    expect(training.entries.every((entry) => entry.real_pipeline_connected === false)).toBe(true);
    expect(boundary.not_proven).toContain("real_training_or_labeling_pipeline");
    expect(boundary.control_policy.workstation_executes_control).toBe(false);
    expect(boundary.control_policy.route_loader_mode).toBe("local_json_readonly");
    expectNoLegacyPythonGateSemantics(boundary);
  });
});
