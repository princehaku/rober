import { PROOF_FLAGS } from "../shared/contracts";
import type { O7RealtimeElevatorProbeResponse } from "../shared/contracts";

const EXPECTED_SCHEMA = "trashbot.o7.realtime_elevator_snapshot.v1";
const PROBE_SCHEMA = "trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1";
const REMOTE_ENDPOINT = "/api/o7/realtime-elevator/snapshot" as const;
const ELEVATOR_SAMPLE_LIMIT = 5;

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "real_realtime_api_connected",
  "real_ros2_tf_connected",
  "latency_lt_2s_proven",
  "on_route",
  "in_elevator_zone",
  "real_elevator_state_chain_connected",
  "floor_recognition_proven",
  "human_takeover_proven",
  "robot_control_executed",
  "success_claim_allowed",
]);

function defaultFalseFields(): string[] {
  // 默认 false 字段覆盖 KR1/KR2 的真实实时、/tf、路线、电梯、楼层和控制能力。
  return [
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
  ];
}

function failClosed(
  reason: string,
  baseUrl: string,
  extras: Partial<O7RealtimeElevatorProbeResponse> = {},
): O7RealtimeElevatorProbeResponse {
  // probe 失败时仍返回完整结构，UI 只能展示 blocked，而不能推断实时地图或电梯已接通。
  return {
    schema: PROBE_SCHEMA,
    probe_status: "fail_closed",
    source_base_url: baseUrl || "not_provided",
    remote_endpoint: REMOTE_ENDPOINT,
    remote_schema: extras.remote_schema ?? "not_loaded",
    realtime_status: extras.realtime_status ?? "not_loaded",
    snapshot_status: extras.snapshot_status ?? "not_loaded",
    map_ref_summary: extras.map_ref_summary ?? "not_loaded",
    map_frame_summary: extras.map_frame_summary ?? "not_loaded",
    robot_pose_summary: extras.robot_pose_summary ?? "x_m=not_loaded, y_m=not_loaded, yaw_rad=not_loaded, pose_source=not_loaded, timestamp_ms=not_loaded, evidence_ref=not_loaded, real_ros2_tf_connected=false",
    pose_freshness_summary: extras.pose_freshness_summary ?? "blocked_not_proven",
    route_membership_false_fields: extras.route_membership_false_fields ?? [
      "route_membership.on_route=false",
      "route_membership.in_elevator_zone=false",
    ],
    elevator_status: extras.elevator_status ?? "blocked_not_proven",
    elevator_state_samples_summary: extras.elevator_state_samples_summary ?? [],
    current_floor_evidence_summary: extras.current_floor_evidence_summary ?? "blocked_not_proven",
    human_takeover_summary: extras.human_takeover_summary ?? "blocked_not_proven",
    key_false_fields: extras.key_false_fields ?? defaultFalseFields(),
    dangerous_true_fields: extras.dangerous_true_fields ?? [],
    blocked_reasons: extras.blocked_reasons ?? [reason],
    not_proven: extras.not_proven ?? ["realtime_elevator_probe_not_proven"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  };
}

function normalizeLoopbackBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // 只允许本机 HTTP 回环，避免诊断 probe 被滥用成 SSRF 或生产云探测代理。
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "baseUrl_not_provided" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "baseUrl_invalid_url" };
  }
  if (parsed.protocol !== "http:") {
    return { ok: false, reason: "baseUrl_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "baseUrl_must_not_include_credentials_query_or_hash" };
  }
  if (!["127.0.0.1", "localhost", "[::1]"].includes(parsed.host.replace(/:\d+$/, "")) && parsed.hostname !== "::1") {
    return { ok: false, reason: "baseUrl_must_be_local_loopback" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed.toString().replace(/\/$/, "") };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // 远端 snapshot 必须是 object；其他 JSON 形态不能进入 UI 摘要。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function stringArray(value: unknown): string[] {
  // blocked/not_proven 只展示字符串化后的短文本，坏类型收敛为空数组。
  return Array.isArray(value) ? value.map(String) : [];
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 任一危险字段为 true 都说明远端 contract 不再 fail-closed，probe 必须降级。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`));
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    const current = DANGEROUS_TRUE_FIELDS.has(key) && nested === true ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath));
  });
}

function boolField(record: Record<string, unknown> | null, key: string): boolean {
  // 缺失按 false 展示，旧 contract 不能被 UI 推断成已经接通。
  return record?.[key] === true;
}

function keyFalseFields(remote: Record<string, unknown>): string[] {
  const route = asRecord(remote.route_membership);
  const poseFreshness = asRecord(remote.pose_freshness);
  const floor = asRecord(remote.current_floor_evidence);
  const humanTakeover = asRecord(remote.human_takeover);
  return [
    `real_realtime_api_connected=${String(remote.real_realtime_api_connected === true)}`,
    `real_ros2_tf_connected=${String(remote.real_ros2_tf_connected === true)}`,
    `latency_lt_2s_proven=${String(remote.latency_lt_2s_proven === true || boolField(poseFreshness, "latency_lt_2s_proven"))}`,
    `route_membership.on_route=${String(boolField(route, "on_route"))}`,
    `route_membership.in_elevator_zone=${String(boolField(route, "in_elevator_zone"))}`,
    `real_elevator_state_chain_connected=${String(remote.real_elevator_state_chain_connected === true)}`,
    `floor_recognition_proven=${String(remote.floor_recognition_proven === true || boolField(floor, "floor_recognition_proven"))}`,
    `human_takeover_proven=${String(remote.human_takeover_proven === true || boolField(humanTakeover, "human_takeover_proven"))}`,
    `safe_to_control=${String(remote.safe_to_control === true)}`,
    `delivery_success=${String(remote.delivery_success === true)}`,
    `primary_actions_enabled=${String(remote.primary_actions_enabled === true)}`,
    `robot_control_executed=${String(remote.robot_control_executed === true)}`,
  ];
}

function summary(record: Record<string, unknown> | null, keys: string[]): string {
  // 摘要只输出少量标量字段，避免把远端 snapshot 原样透传到 UI。
  if (!record) {
    return "not_loaded";
  }
  return keys.map((key) => `${key}=${String(record[key] ?? "not_loaded")}`).join(", ");
}

function scalarSummary(record: Record<string, unknown>, key: string, fallback = "not_loaded"): string {
  // 只允许标量值进入摘要，object/array 会被压成 fallback，防止透传远端嵌套 payload。
  const value = record[key];
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean" || value === null) {
    return String(value ?? fallback);
  }
  return fallback;
}

function robotPoseSummary(remote: Record<string, unknown>): string {
  // 位姿摘要明确保留 real_ros2_tf_connected=false，fixture 位姿不能被 UI 解释成真实 /tf。
  const pose = asRecord(remote.robot_pose);
  if (!pose) {
    return "x_m=not_loaded, y_m=not_loaded, yaw_rad=not_loaded, pose_source=not_loaded, timestamp_ms=not_loaded, evidence_ref=not_loaded, real_ros2_tf_connected=false";
  }
  return [
    `x_m=${scalarSummary(pose, "x_m")}`,
    `y_m=${scalarSummary(pose, "y_m")}`,
    `yaw_rad=${scalarSummary(pose, "yaw_rad")}`,
    `pose_source=${scalarSummary(pose, "pose_source", scalarSummary(pose, "source"))}`,
    `timestamp_ms=${scalarSummary(pose, "timestamp_ms")}`,
    `evidence_ref=${scalarSummary(pose, "evidence_ref")}`,
    `real_ros2_tf_connected=false`,
  ].join(", ");
}

function elevatorStateSamplesSummary(elevator: Record<string, unknown> | null): string[] {
  // 状态链 sample 只保留 state/status/timestamp/evidence_ref，最多 5 条，不展开完整 remote JSON。
  const samples = Array.isArray(elevator?.samples) ? elevator.samples : [];
  return samples.slice(0, ELEVATOR_SAMPLE_LIMIT).map((sample, index) => {
    const record = asRecord(sample) ?? {};
    return [
      `#${index + 1}`,
      `state=${scalarSummary(record, "state", scalarSummary(record, "current_state"))}`,
      `status=${scalarSummary(record, "status")}`,
      `timestamp_ms=${scalarSummary(record, "timestamp_ms", scalarSummary(record, "t_ms"))}`,
      `evidence_ref=${scalarSummary(record, "evidence_ref")}`,
    ].join(", ");
  });
}

export async function buildO7RealtimeElevatorProbe(baseUrl: string): Promise<O7RealtimeElevatorProbeResponse> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosed(normalized.reason, baseUrl);
  }

  try {
    const response = await fetch(`${normalized.normalized}${REMOTE_ENDPOINT}`, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(2000),
    });
    if (!response.ok) {
      return failClosed(`remote_http_${response.status}`, normalized.normalized);
    }
    const remote = asRecord(await response.json());
    if (!remote) {
      return failClosed("remote_json_not_object", normalized.normalized);
    }
    const remoteSchema = String(remote.schema ?? "not_loaded");
    const falseFields = keyFalseFields(remote);
    const dangerous = scanDangerousTrueFields(remote);
    const route = asRecord(remote.route_membership);
    const elevator = asRecord(remote.elevator_state_chain);
    const floor = asRecord(remote.current_floor_evidence);
    const humanTakeover = asRecord(remote.human_takeover);
    const extras: Partial<O7RealtimeElevatorProbeResponse> = {
      remote_schema: remoteSchema,
      realtime_status: String(remote.realtime_status ?? "not_loaded"),
      snapshot_status: String(remote.snapshot_status ?? "not_loaded"),
      map_ref_summary: summary(asRecord(remote.map_ref), ["id", "status", "evidence_ref"]),
      map_frame_summary: summary(asRecord(remote.map_frame), ["frame_id", "source", "status"]),
      robot_pose_summary: robotPoseSummary(remote),
      pose_freshness_summary: summary(asRecord(remote.pose_freshness), ["age_ms", "latency_lt_2s_proven", "status"]),
      route_membership_false_fields: [
        `route_membership.on_route=${String(boolField(route, "on_route"))}`,
        `route_membership.in_elevator_zone=${String(boolField(route, "in_elevator_zone"))}`,
      ],
      elevator_status: summary(elevator, ["current_state", "sample_count", "status"]),
      elevator_state_samples_summary: elevatorStateSamplesSummary(elevator),
      current_floor_evidence_summary: summary(floor, ["floor_label", "confidence", "floor_recognition_proven", "status"]),
      human_takeover_summary: summary(humanTakeover, ["required", "human_takeover_proven", "reason", "status"]),
      key_false_fields: falseFields,
    };
    if (remoteSchema !== EXPECTED_SCHEMA) {
      return failClosed("remote_schema_mismatch", normalized.normalized, extras);
    }
    if (dangerous.length > 0) {
      return failClosed("remote_dangerous_true_field", normalized.normalized, {
        ...extras,
        dangerous_true_fields: dangerous,
        blocked_reasons: dangerous.map((field) => `dangerous_true:${field}`),
      });
    }
    return {
      schema: PROBE_SCHEMA,
      probe_status: "loaded_fail_closed_contract",
      source_base_url: normalized.normalized,
      remote_endpoint: REMOTE_ENDPOINT,
      remote_schema: remoteSchema,
      realtime_status: String(remote.realtime_status ?? "blocked_not_proven"),
      snapshot_status: String(remote.snapshot_status ?? "blocked_not_proven"),
      map_ref_summary: extras.map_ref_summary ?? "not_loaded",
      map_frame_summary: extras.map_frame_summary ?? "not_loaded",
      robot_pose_summary: extras.robot_pose_summary ?? robotPoseSummary(remote),
      pose_freshness_summary: extras.pose_freshness_summary ?? "blocked_not_proven",
      route_membership_false_fields: extras.route_membership_false_fields ?? [],
      elevator_status: extras.elevator_status ?? "blocked_not_proven",
      elevator_state_samples_summary: extras.elevator_state_samples_summary ?? [],
      current_floor_evidence_summary: extras.current_floor_evidence_summary ?? "blocked_not_proven",
      human_takeover_summary: extras.human_takeover_summary ?? "blocked_not_proven",
      key_false_fields: falseFields,
      dangerous_true_fields: [],
      blocked_reasons: stringArray(remote.blocked_reasons),
      not_proven: stringArray(remote.not_proven),
      fail_closed_reason: "none_remote_contract_is_still_blocked_not_proven",
      local_loopback_only: true,
      connects_cloud_production: false,
      sends_commands: false,
      reads_hardware: false,
      ...PROOF_FLAGS,
    };
  } catch {
    return failClosed("remote_fetch_failed", normalized.normalized);
  }
}
