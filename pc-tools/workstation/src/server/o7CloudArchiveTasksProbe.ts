import { PROOF_FLAGS } from "../shared/contracts";
import type { O7CloudArchiveTasksProbeResponse } from "../shared/contracts";

const EXPECTED_SCHEMA = "trashbot.o7.cloud_archive_tasks.v1";
const PROBE_SCHEMA = "trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1";
const REMOTE_ENDPOINT = "/api/o7/cloud-archive/tasks" as const;

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "real_command_api_connected",
  "real_robot_ack_connected",
  "real_cloud_archive_connected",
  "real_realtime_api_connected",
  "real_annotation_api_connected",
  "real_voice_api_connected",
  "real_asr_tts_runtime_connected",
  "asr_stream_connected",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "playback_available",
  "submit_enabled",
  "rollback_enabled",
  "dataset_export_available",
  "robot_control_executed",
  "success_claim_allowed",
]);

function failClosed(
  reason: string,
  baseUrl: string,
  extras: Partial<O7CloudArchiveTasksProbeResponse> = {},
): O7CloudArchiveTasksProbeResponse {
  // probe 失败也必须返回完整 fail-closed 契约，UI 不能把 HTTP 错误解释成云 archive 在线。
  return {
    schema: PROBE_SCHEMA,
    probe_status: "fail_closed",
    source_base_url: baseUrl || "not_provided",
    remote_endpoint: REMOTE_ENDPOINT,
    remote_schema: extras.remote_schema ?? "not_loaded",
    archive_status: extras.archive_status ?? "not_loaded",
    task_count: extras.task_count ?? 0,
    selected_task_id: extras.selected_task_id ?? null,
    latest_task_id: extras.latest_task_id ?? null,
    inspector_statuses: extras.inspector_statuses ?? {
      route_replay: "blocked_not_proven",
      labeling_queue: "blocked_not_proven",
      voice_asr_tts: "blocked_not_proven",
      safe_command: "blocked_not_proven",
    },
    route_replay_summary: extras.route_replay_summary ?? "status=blocked_not_loaded; frame_count=0; sample_refs=[]; playback_available=false",
    labeling_queue_summary: extras.labeling_queue_summary ?? "status=blocked_not_loaded; review_item_count=0; label_schema=not_loaded; submit_enabled=false",
    voice_asr_tts_summary: extras.voice_asr_tts_summary ?? "status=blocked_not_loaded; asr_event_count=0; tts_draft_count=0; tts_send_enabled=false",
    safe_command_summary: extras.safe_command_summary ?? "status=blocked_not_loaded; command_count=0; manual=blocked_not_loaded; navigate=blocked_not_loaded; ack=blocked_not_loaded; command_dispatch_enabled=false; robot_control_executed=false",
    key_false_fields: extras.key_false_fields ?? defaultFalseFields(),
    dangerous_true_fields: extras.dangerous_true_fields ?? [],
    blocked_reasons: extras.blocked_reasons ?? [reason],
    not_proven: extras.not_proven ?? ["cloud_archive_tasks_probe_not_proven"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  };
}

function normalizeLoopbackBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // 只允许 PC 后端探测本机回环 HTTP URL，避免把诊断入口变成外网代理。
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
  // 远端响应必须是 object；其他 JSON 形态都按 schema 错误处理。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function stringArray(value: unknown): string[] {
  // 只展示远端已经脱敏的 blocked/not_proven 文本，坏类型收敛为空数组。
  return Array.isArray(value) ? value.map(String) : [];
}

function limitedStringArray(value: unknown, limit = 3): string[] {
  // probe 摘要只需要看数据形状，数组全部限量，避免把远端 payload 原样透传给 UI。
  return stringArray(value).slice(0, limit).map((item) => item.replace(/\s+/g, " ").slice(0, 96));
}

function numberField(record: Record<string, unknown> | null, key: string): number {
  // 数量字段只接受 number；字符串数字不自动提升，避免坏 contract 被误读为有效统计。
  const value = record?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function stringField(record: Record<string, unknown> | null, key: string, fallback: string): string {
  // 摘要字段统一收敛成短文本，防止远端塞入对象或长文本污染 operator 视图。
  const value = record?.[key];
  return typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 96) : fallback;
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 递归扫描危险开关；只要任一为 true，probe 结果必须 fail closed。
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

function defaultFalseFields(): string[] {
  // 这些 false 字段覆盖 archive、回放、标注、语音和手控/寻路最容易误读的能力。
  return [
    "real_cloud_archive_connected=false",
    "playback_available=false",
    "submit_enabled=false",
    "tts_send_enabled=false",
    "command_dispatch_enabled=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "robot_control_executed=false",
  ];
}

function boolField(record: Record<string, unknown> | null, key: string): boolean {
  // 缺失字段按 false 展示，避免旧 contract 被前端推断成能力打开。
  return record?.[key] === true;
}

function keyFalseFields(remote: Record<string, unknown>): string[] {
  const route = asRecord(remote.route_replay_inspector);
  const labeling = asRecord(remote.labeling_queue_inspector);
  const voice = asRecord(remote.voice_asr_tts_inspector);
  const safeCommand = asRecord(remote.safe_command_inspector);
  const cursor = asRecord(route?.cursor_initial_state);
  return [
    `real_cloud_archive_connected=${String(remote.real_cloud_archive_connected === true)}`,
    `real_realtime_api_connected=${String(remote.real_realtime_api_connected === true)}`,
    `real_annotation_api_connected=${String(remote.real_annotation_api_connected === true)}`,
    `real_voice_api_connected=${String(remote.real_voice_api_connected === true)}`,
    `real_command_api_connected=${String(remote.real_command_api_connected === true || boolField(safeCommand, "real_command_api_connected"))}`,
    `real_robot_ack_connected=${String(remote.real_robot_ack_connected === true || boolField(safeCommand, "real_robot_ack_connected"))}`,
    `playback_available=${String(remote.playback_available === true || boolField(route, "playback_available") || boolField(cursor, "safe_to_play"))}`,
    `submit_enabled=${String(remote.submit_enabled === true || boolField(labeling, "submit_enabled"))}`,
    `tts_send_enabled=${String(remote.tts_send_enabled === true || boolField(voice, "tts_send_enabled"))}`,
    `command_dispatch_enabled=${String(boolField(safeCommand, "command_dispatch_enabled"))}`,
    `safe_to_control=${String(remote.safe_to_control === true || boolField(safeCommand, "safe_to_control"))}`,
    `delivery_success=${String(remote.delivery_success === true || boolField(safeCommand, "delivery_success"))}`,
    `primary_actions_enabled=${String(remote.primary_actions_enabled === true || boolField(safeCommand, "primary_actions_enabled"))}`,
    `robot_control_executed=${String(remote.robot_control_executed === true || boolField(safeCommand, "robot_control_executed"))}`,
  ];
}

function taskId(value: unknown): string | null {
  const task = asRecord(value);
  // 只读取任务摘要中的 id，不展开轨迹或事件 payload。
  return task ? String(task.task_id ?? task.id ?? "unknown") : null;
}

function inspectorStatuses(remote: Record<string, unknown>): O7CloudArchiveTasksProbeResponse["inspector_statuses"] {
  // inspector status 给 UI 一个低噪声诊断视图，不传输样本帧或标注内容。
  return {
    route_replay: String(asRecord(remote.route_replay_inspector)?.status ?? "blocked_not_proven"),
    labeling_queue: String(asRecord(remote.labeling_queue_inspector)?.status ?? "blocked_not_proven"),
    voice_asr_tts: String(asRecord(remote.voice_asr_tts_inspector)?.status ?? "blocked_not_proven"),
    safe_command: String(asRecord(remote.safe_command_inspector)?.status ?? "blocked_not_proven"),
  };
}

function inspectorSummaries(remote: Record<string, unknown>): Pick<
  O7CloudArchiveTasksProbeResponse,
  "route_replay_summary" | "labeling_queue_summary" | "voice_asr_tts_summary" | "safe_command_summary"
> {
  const safeSummaries = asRecord(remote.safe_summaries);
  const trajectory = asRecord(safeSummaries?.trajectory);
  const labels = asRecord(safeSummaries?.labels);
  const voiceSummary = asRecord(safeSummaries?.voice);
  const commandSummary = asRecord(safeSummaries?.commands);
  const route = asRecord(remote.route_replay_inspector);
  const labeling = asRecord(remote.labeling_queue_inspector);
  const voice = asRecord(remote.voice_asr_tts_inspector);
  const safeCommand = asRecord(remote.safe_command_inspector);
  const labelSchema = asRecord(labeling?.label_schema);
  const ttsDraft = asRecord(voice?.tts_draft);
  const manual = asRecord(safeCommand?.manual_turn_envelope);
  const navigate = asRecord(safeCommand?.navigate_goal_envelope);
  const ack = asRecord(safeCommand?.robot_ack_blocked_summary);
  const firstFrame = asRecord(Array.isArray(route?.sample_frames) ? route.sample_frames[0] : null);

  // 四个 summary 只由远端 safe_summaries 和 inspector 白名单字段拼接，不能透传完整 JSON。
  return {
    route_replay_summary: [
      `status=${stringField(route, "status", "blocked_not_proven")}`,
      `frame_count=${numberField(route, "frame_count") || numberField(trajectory, "frame_count")}`,
      `sample_refs=[${limitedStringArray(trajectory?.sample_refs).join(",")}]`,
      `first_frame=${stringField(firstFrame, "state", "not_loaded")}:${stringField(firstFrame, "evidence_ref", "not_loaded")}`,
      "playback_available=false",
    ].join("; "),
    labeling_queue_summary: [
      `status=${stringField(labeling, "status", "blocked_not_proven")}`,
      `review_item_count=${numberField(labeling, "review_item_count") || numberField(labels, "label_count")}`,
      `label_schema=${stringField(labelSchema, "schema_ref", "not_loaded")}@${stringField(labelSchema, "version", "not_loaded")}`,
      `allowed_label_types=[${limitedStringArray(labeling?.allowed_label_types, 5).join(",")}]`,
      "submit_enabled=false",
    ].join("; "),
    voice_asr_tts_summary: [
      `status=${stringField(voice, "status", "blocked_not_proven")}`,
      `asr_event_count=${numberField(voice, "asr_event_count") || numberField(voiceSummary, "asr_event_count")}`,
      `tts_draft_count=${numberField(voiceSummary, "tts_draft_count")}`,
      `tts_text_length=${numberField(ttsDraft, "text_length")}`,
      "tts_send_enabled=false",
    ].join("; "),
    safe_command_summary: [
      `status=${stringField(safeCommand, "status", "blocked_not_proven")}`,
      `command_count=${numberField(safeCommand, "command_count") || numberField(commandSummary, "command_count")}`,
      `manual=${stringField(manual, "status", "blocked_not_proven")}`,
      `navigate=${stringField(navigate, "status", "blocked_not_proven")}`,
      `ack=${stringField(ack, "ack_status", "blocked_not_proven")}`,
      "command_dispatch_enabled=false",
      "robot_control_executed=false",
    ].join("; "),
  };
}

export async function buildO7CloudArchiveTasksProbe(baseUrl: string): Promise<O7CloudArchiveTasksProbeResponse> {
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
    const taskList = asRecord(remote.task_list);
    const summaries = inspectorSummaries(remote);
    if (remoteSchema !== EXPECTED_SCHEMA) {
      return failClosed("remote_schema_mismatch", normalized.normalized, { remote_schema: remoteSchema, key_false_fields: falseFields });
    }
    if (dangerous.length > 0) {
      return failClosed("remote_dangerous_true_field", normalized.normalized, {
        remote_schema: remoteSchema,
        archive_status: String(remote.archive_status ?? "not_loaded"),
        task_count: typeof taskList?.total_tasks === "number" ? taskList.total_tasks : 0,
        selected_task_id: taskId(remote.selected_task),
        latest_task_id: taskId(remote.latest_task),
        inspector_statuses: inspectorStatuses(remote),
        ...summaries,
        key_false_fields: falseFields,
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
      archive_status: String(remote.archive_status ?? "blocked_not_proven"),
      task_count: typeof taskList?.total_tasks === "number" ? taskList.total_tasks : 0,
      selected_task_id: taskId(remote.selected_task),
      latest_task_id: taskId(remote.latest_task),
      inspector_statuses: inspectorStatuses(remote),
      ...summaries,
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
