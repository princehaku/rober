import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7ConsumerTaskDetailResponse,
  O7ConsumerTaskListItem,
  O7ConsumerTaskListResponse,
} from "../shared/contracts";

type JsonRecord = Record<string, unknown>;

const LIST_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_list.v1" as const;
const DETAIL_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1" as const;
const REMOTE_LIST_ENDPOINT = "/api/o6/consumer/tasks" as const;
const REMOTE_DETAIL_ENDPOINT_PREFIX = "/api/o6/consumer/tasks/" as const;
const DEFAULT_BASE_URL = "http://127.0.0.1:8088" as const;
const DEFAULT_LIST_VIEW = "summary" as const;
const DEFAULT_DETAIL_VIEW = "default" as const;
const DEFAULT_DETAIL_INCLUDE = ["trajectory", "events", "evidence", "labeling", "inference", "tunnel"] as const;

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "connects_cloud_production",
  "robot_control_executed",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "submit_enabled",
  "rollback_enabled",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "real_cloud_db_connected",
  "real_oss_connected",
]);

function asRecord(value: unknown): JsonRecord | null {
  // 远端 consumer read 必须返回 object；其他 JSON 形态全部按 fail-closed 处理。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : null;
}

function asString(value: unknown, fallback = "blocked_not_proven"): string {
  // 所有展示字符串都收敛成短文本，避免坏 payload 直接透传到 UI。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 160) : fallback;
}

function asNumber(value: unknown): number | null {
  // 数值字段只接受有限数字，字符串数字不自动提升，避免误判远端 contract。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asBoolean(value: unknown): boolean {
  // 布尔默认 false，防止缺字段被 UI 推断成可控制或已完成。
  return value === true;
}

function limitedArray(value: unknown, limit = 5): unknown[] {
  // 详情摘要只保留少量样本，避免把完整 timeline 原样灌进 PC 页面。
  return Array.isArray(value) ? value.slice(0, limit) : [];
}

function stringList(value: unknown, limit = 12): string[] {
  // blocked/not_proven 等字段仅保留短文本列表，减小噪声并避免坏对象透传。
  return Array.isArray(value) ? value.map((item) => asString(item, "blocked_not_proven")).slice(0, limit) : [];
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 只要 consumer read 中出现危险 true 字段，就直接阻断 O7 的“主入口”成功态。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`));
  }
  return Object.entries(value as JsonRecord).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    const current = DANGEROUS_TRUE_FIELDS.has(key) && nested === true ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath));
  });
}

function normalizeLoopbackBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // workstation 只允许探测本机回环 HTTP relay，避免把 PC adapter 变成任意外网代理。
  const trimmed = baseUrl.trim() || DEFAULT_BASE_URL;
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
  if (!["127.0.0.1", "localhost"].includes(parsed.hostname) && parsed.hostname !== "::1") {
    return { ok: false, reason: "baseUrl_must_be_local_loopback" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed.toString().replace(/\/$/, "") };
}

function fixedFalseFields() {
  // 这些固定 false 字段是 O7 页面判断“只读软件证明边界”的主锚点。
  return {
    safe_to_control: false as const,
    connects_cloud_production: false as const,
    robot_control_executed: false as const,
    delivery_success: false as const,
    primary_actions_enabled: false as const,
  };
}

function failClosedList(reason: string, baseUrl: string): O7ConsumerTaskListResponse {
  // 列表失败时仍返回完整 contract，让 UI 能明确看到主路径被关闸的原因。
  return {
    schema: LIST_SCHEMA,
    list_status: "fail_closed",
    source_base_url: baseUrl || DEFAULT_BASE_URL,
    remote_endpoint: REMOTE_LIST_ENDPOINT,
    remote_schema: "not_loaded",
    query_strategy: {
      view: DEFAULT_LIST_VIEW,
      include: [],
      limit: 50,
      primary_path: true,
      fail_closed_visible: true,
    },
    task_list: [],
    blocked_reasons: [reason],
    not_proven: ["o7_consumer_task_list_not_proven"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function failClosedDetail(reason: string, baseUrl: string, taskId: string): O7ConsumerTaskDetailResponse {
  // 详情失败时也保留固定 include 策略，便于 reviewer 核对 FP3 的默认请求行为。
  return {
    schema: DETAIL_SCHEMA,
    detail_status: "fail_closed",
    source_base_url: baseUrl || DEFAULT_BASE_URL,
    remote_endpoint: `${REMOTE_DETAIL_ENDPOINT_PREFIX}${taskId || "<task_id>"}`,
    remote_schema: "not_loaded",
    requested_task_id: taskId || "not_provided",
    query_strategy: {
      view: DEFAULT_DETAIL_VIEW,
      include: [...DEFAULT_DETAIL_INCLUDE],
      primary_path: true,
      fail_closed_visible: true,
    },
    task_summary: null,
    trajectory: { status: "blocked_not_proven", frame_count: 0, sample_frames: [] },
    events: { status: "blocked_not_proven", count: 0, sample_events: [] },
    evidence: { status: "blocked_not_proven", count: 0, sample_evidence: [] },
    labeling: { status: "blocked_not_proven", label_count: 0, sample_items: [] },
    inference: { status: "blocked_not_proven", count: 0, sample_results: [] },
    tunnel_status: {
      status: "blocked_not_proven",
      latest_known_status: "blocked_not_proven",
      temporal_alignment: "latest_known_robot_snapshot_not_task_aligned",
    },
    blocked_reasons: [reason],
    not_proven: ["o7_consumer_task_detail_not_proven"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function mapTaskItem(value: unknown): O7ConsumerTaskListItem {
  const record = asRecord(value);
  // 任务卡片只映射 O7 文档已经确认的字段，不把其余 payload 当成 UI 事实。
  return {
    task_id: asString(record?.task_id, "unknown_task"),
    robot_id: asString(record?.robot_id, "unknown_robot"),
    started_at_ms: asNumber(record?.started_at_ms),
    finished_at_ms: asNumber(record?.finished_at_ms),
    task_status_summary: asString(record?.task_status_summary),
    latest_event_at_ms: asNumber(record?.latest_event_at_ms),
    trajectory_frame_count: asNumber(record?.trajectory_frame_count) ?? 0,
    event_count: asNumber(record?.event_count) ?? 0,
    evidence_count: asNumber(record?.evidence_count) ?? 0,
    labeling_status: asString(record?.labeling_status, "pending"),
    inference_status: asString(record?.inference_status, "absent"),
    tunnel_status_summary: asString(record?.tunnel_status_summary, "blocked_not_proven"),
    selected: asBoolean(record?.selected),
  };
}

function sampleObjectArray(value: unknown, limit = 5): JsonRecord[] {
  // 详情样本数组只保留 object 项，并截断为少量条目供 reviewer 目视复核。
  return limitedArray(value, limit).map((item) => asRecord(item)).filter((item): item is JsonRecord => Boolean(item));
}

export async function buildO7ConsumerTaskList(baseUrl: string): Promise<O7ConsumerTaskListResponse> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosedList(normalized.reason, baseUrl);
  }

  const url = new URL(`${normalized.normalized}${REMOTE_LIST_ENDPOINT}`);
  url.searchParams.set("view", DEFAULT_LIST_VIEW);
  url.searchParams.set("limit", "50");

  let remoteJson: unknown;
  try {
    const response = await fetch(url, { method: "GET" });
    remoteJson = await response.json();
  } catch {
    return failClosedList("consumer_list_fetch_failed", normalized.normalized);
  }

  const remote = asRecord(remoteJson);
  if (!remote) {
    return failClosedList("consumer_list_response_not_object", normalized.normalized);
  }
  if (asString(remote.schema, "") !== "trashbot.o6.consumer_read.v1") {
    return failClosedList("consumer_list_schema_mismatch", normalized.normalized);
  }
  const dangerous = scanDangerousTrueFields(remote);
  if (dangerous.length > 0) {
    return failClosedList(`dangerous_true_fields:${dangerous.join(",")}`, normalized.normalized);
  }

  const taskList = asRecord(remote.task_list);
  const rawTasks = Array.isArray(taskList?.tasks) ? taskList.tasks : [];
  return {
    schema: LIST_SCHEMA,
    list_status: "loaded_fail_closed_summary",
    source_base_url: normalized.normalized,
    remote_endpoint: `${REMOTE_LIST_ENDPOINT}?view=${DEFAULT_LIST_VIEW}&limit=50`,
    remote_schema: "trashbot.o6.consumer_read.v1",
    query_strategy: {
      view: DEFAULT_LIST_VIEW,
      include: [],
      limit: 50,
      primary_path: true,
      fail_closed_visible: true,
    },
    task_list: rawTasks.map((item) => mapTaskItem(item)),
    blocked_reasons: stringList(remote.blocked_reasons),
    not_proven: stringList(remote.not_proven),
    fail_closed_reason: "none",
    local_loopback_only: true,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

export async function buildO7ConsumerTaskDetail(baseUrl: string, taskId: string): Promise<O7ConsumerTaskDetailResponse> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosedDetail(normalized.reason, baseUrl, taskId);
  }
  const trimmedTaskId = taskId.trim();
  if (!trimmedTaskId) {
    return failClosedDetail("task_id_not_provided", normalized.normalized, taskId);
  }

  const url = new URL(`${normalized.normalized}${REMOTE_DETAIL_ENDPOINT_PREFIX}${encodeURIComponent(trimmedTaskId)}`);
  url.searchParams.set("view", DEFAULT_DETAIL_VIEW);
  url.searchParams.set("include", DEFAULT_DETAIL_INCLUDE.join(","));

  let remoteJson: unknown;
  try {
    const response = await fetch(url, { method: "GET" });
    remoteJson = await response.json();
  } catch {
    return failClosedDetail("consumer_detail_fetch_failed", normalized.normalized, trimmedTaskId);
  }

  const remote = asRecord(remoteJson);
  if (!remote) {
    return failClosedDetail("consumer_detail_response_not_object", normalized.normalized, trimmedTaskId);
  }
  if (asString(remote.schema, "") !== "trashbot.o6.consumer_read.v1") {
    return failClosedDetail("consumer_detail_schema_mismatch", normalized.normalized, trimmedTaskId);
  }
  const dangerous = scanDangerousTrueFields(remote);
  if (dangerous.length > 0) {
    return failClosedDetail(`dangerous_true_fields:${dangerous.join(",")}`, normalized.normalized, trimmedTaskId);
  }

  const taskSummary = asRecord(remote.task_summary);
  const trajectory = asRecord(remote.trajectory);
  const events = asRecord(remote.events);
  const evidence = asRecord(remote.evidence);
  const labeling = asRecord(remote.labeling);
  const inference = asRecord(remote.inference);
  const tunnel = asRecord(remote.tunnel_status);

  return {
    schema: DETAIL_SCHEMA,
    detail_status: "loaded_fail_closed_summary",
    source_base_url: normalized.normalized,
    remote_endpoint: `${REMOTE_DETAIL_ENDPOINT_PREFIX}${trimmedTaskId}?view=${DEFAULT_DETAIL_VIEW}&include=${DEFAULT_DETAIL_INCLUDE.join(",")}`,
    remote_schema: "trashbot.o6.consumer_read.v1",
    requested_task_id: trimmedTaskId,
    query_strategy: {
      view: DEFAULT_DETAIL_VIEW,
      include: [...DEFAULT_DETAIL_INCLUDE],
      primary_path: true,
      fail_closed_visible: true,
    },
    task_summary: taskSummary
      ? {
          task_id: asString(taskSummary.task_id, trimmedTaskId),
          robot_id: asString(taskSummary.robot_id, "unknown_robot"),
          task_status_summary: asString(taskSummary.task_status_summary),
          started_at_ms: asNumber(taskSummary.started_at_ms),
          finished_at_ms: asNumber(taskSummary.finished_at_ms),
        }
      : null,
    trajectory: {
      status: asString(trajectory?.status, "loaded_not_proven"),
      frame_count: asNumber(trajectory?.frame_count) ?? sampleObjectArray(trajectory?.frames).length,
      sample_frames: sampleObjectArray(trajectory?.frames),
    },
    events: {
      status: asString(events?.status, "loaded_not_proven"),
      count: asNumber(events?.count) ?? sampleObjectArray(events?.items).length,
      sample_events: sampleObjectArray(events?.items),
    },
    evidence: {
      status: asString(evidence?.status, "loaded_not_proven"),
      count: asNumber(evidence?.count) ?? sampleObjectArray(evidence?.items).length,
      sample_evidence: sampleObjectArray(evidence?.items),
    },
    labeling: {
      status: asString(labeling?.status, "pending"),
      label_count: asNumber(labeling?.label_count) ?? 0,
      sample_items: sampleObjectArray(labeling?.items),
    },
    inference: {
      status: asString(inference?.status, "absent"),
      count: asNumber(inference?.count) ?? sampleObjectArray(inference?.items).length,
      sample_results: sampleObjectArray(inference?.items),
    },
    tunnel_status: {
      status: asString(tunnel?.status, "blocked_not_proven"),
      latest_known_status: asString(tunnel?.latest_known_status, "blocked_not_proven"),
      temporal_alignment: asString(
        tunnel?.temporal_alignment,
        "latest_known_robot_snapshot_not_task_aligned",
      ),
    },
    blocked_reasons: stringList(remote.blocked_reasons),
    not_proven: stringList(remote.not_proven),
    fail_closed_reason: "none",
    local_loopback_only: true,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}
