import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7FieldEvidenceConsumerIngestResponse,
  O7FieldEvidenceManifestArtifactSummary,
  O7FieldEvidenceManifestSummary,
  O7ConsumerTaskDetailResponse,
  O7ConsumerTaskListItem,
  O7ConsumerTaskListResponse,
  O7LabelingPreviewResponse,
  O7RouteReplayPreviewResponse,
} from "../shared/contracts";
import { buildO7LabelingPreview } from "./o7LabelingPreview";
import { buildO7RouteReplayPreview } from "./o7RouteReplayPreview";

type JsonRecord = Record<string, unknown>;
type ManifestArtifactStatus = "gated" | "missing" | "blocked";
type ManifestGateStatus = "gated" | "blocked_not_proven";
type DetailFieldEvidenceInputStatus =
  O7ConsumerTaskDetailResponse["field_evidence"]["input_status"];

const LIST_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_list.v1" as const;
const DETAIL_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1" as const;
const REMOTE_LIST_ENDPOINT = "/api/o6/consumer/tasks" as const;
const REMOTE_DETAIL_ENDPOINT_PREFIX = "/api/o6/consumer/tasks/" as const;
const DEFAULT_BASE_URL = "http://127.0.0.1:8088" as const;
const DEFAULT_LIST_VIEW = "summary" as const;
const DEFAULT_DETAIL_VIEW = "default" as const;
const DEFAULT_DETAIL_INCLUDE = ["trajectory", "events", "evidence", "labeling", "inference", "tunnel"] as const;
const FIELD_EVIDENCE_MANIFEST_SCHEMA = "trashbot.field_evidence_manifest.v1" as const;
const FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA =
  "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1" as const;
const MANIFEST_ARTIFACT_KEYS = ["map_yaml", "route_csv", "keyframes", "rosbag", "replay_jsonl"] as const;
const MANIFEST_ARTIFACT_STATUSES = new Set(["gated", "missing", "blocked"]);
const MANIFEST_GATE_STATUSES = new Set(["gated", "blocked_not_proven"]);

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

const MANIFEST_UNSAFE_COPY_PATTERNS = [
  "/cmd_vel",
  "/dev/tty",
  "/dev/ttyUSB",
  "/dev/ttyACM",
  "Traceback",
  "Authorization",
  "access_key",
  "secret",
  "token",
  "password",
];

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

function safePathToken(value: unknown): string {
  // 本地/SSH 路径只给 basename 级别摘要，避免把工作站绝对路径透传到 UI。
  const raw = asString(value, "").trim();
  if (!raw) {
    return "";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return raw;
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

function scanUnsafeManifestCopy(value: unknown): string[] {
  // manifest 允许保留本地材料目录摘要，但不能把控制面、串口或 traceback 误当成可消费内容。
  const payload = JSON.stringify(value ?? {});
  return MANIFEST_UNSAFE_COPY_PATTERNS.filter((token) => payload.includes(token));
}

function manifestInputSafetyStatus(payload: JsonRecord | null): { status: LoadJsonStatus; reason: string } {
  // manifest 本身也要过一层安全扫描，避免把危险控制语义当成可消费输入。
  if (!payload) {
    return { status: "not_object", reason: "manifest_not_loaded" };
  }
  const encoded = JSON.stringify(payload);
  if (scanUnsafeManifestCopy(payload).length > 0) {
    return { status: "unsafe_copy", reason: "manifest_contains_unsafe_copy" };
  }
  if (/"delivery_success"\s*:\s*true/i.test(encoded) || /"safe_to_control"\s*:\s*true/i.test(encoded)) {
    return { status: "success_claim", reason: "manifest_contains_success_or_control_claim" };
  }
  if (/"primary_actions_enabled"\s*:\s*true/i.test(encoded) || /"command_dispatch_enabled"\s*:\s*true/i.test(encoded)) {
    return { status: "control_claim", reason: "manifest_contains_control_claim" };
  }
  return { status: "loaded", reason: "" };
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

function normalizeManifestArtifactStatus(value: unknown): ManifestArtifactStatus {
  // artifact_status 只接受 manifest 约定的三种枚举，避免上游自由字符串污染 UI 语义。
  return typeof value === "string" && MANIFEST_ARTIFACT_STATUSES.has(value) ? (value as ManifestArtifactStatus) : "blocked";
}

function normalizeManifestGateStatus(value: unknown): ManifestGateStatus {
  // manifest_gate 只有 gated / blocked_not_proven；其他值一律按 fail-closed 处理。
  return typeof value === "string" && MANIFEST_GATE_STATUSES.has(value) ? (value as ManifestGateStatus) : "blocked_not_proven";
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
    field_evidence: {
      source_contract: "not_loaded",
      input_status: "missing",
      artifact_status: "blocked",
      manifest_gate: {
        schema: "not_loaded",
        status: "blocked_not_proven",
        gate_pass: false,
        blocked_reason: reason,
        source: "not_loaded",
      },
      blocked_reason: reason,
      not_proven: true,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
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

type LoadJsonStatus =
  | "loaded"
  | "not_provided"
  | "missing"
  | "read_error"
  | "bad_json"
  | "not_object"
  | "unsupported_schema"
  | "unsafe_copy"
  | "success_claim"
  | "control_claim";

interface LoadJsonResult {
  payload: JsonRecord | null;
  status: LoadJsonStatus;
  reason: string;
}

async function loadJsonObject(filePath: string): Promise<LoadJsonResult> {
  // 这里统一封装 manifest / preview 输入读取逻辑，避免各个入口各写一套 fail-closed 分支。
  const trimmed = filePath.trim();
  if (!trimmed) {
    return { payload: null, status: "not_provided", reason: "fixture_json_not_provided" };
  }
  try {
    const content = await fs.readFile(path.resolve(trimmed), "utf8");
    const parsed = JSON.parse(content) as unknown;
    if (!asRecord(parsed)) {
      return { payload: null, status: "not_object", reason: "fixture_json_not_object" };
    }
    return { payload: parsed as JsonRecord, status: "loaded", reason: "" };
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return { payload: null, status: "missing", reason: "fixture_json_missing" };
    }
    if (error instanceof SyntaxError) {
      return { payload: null, status: "bad_json", reason: "fixture_json_bad_json" };
    }
    return { payload: null, status: "read_error", reason: "fixture_json_read_error" };
  }
}

function missingManifestArtifact(root: string, name: string, reason: string): O7FieldEvidenceManifestArtifactSummary {
  // 缺失项保留统一空摘要，便于 UI 直接显示缺口，而不是猜测是否“可能存在”。
  return {
    required: true,
    present: false,
    path: safePathToken(path.join(root || ".", name)),
    size_bytes: 0,
    mtime_utc: null,
    sha256: null,
    reason,
  };
}

function manifestArtifactSummary(
  artifact: unknown,
  root: string,
  fallbackName: string,
): O7FieldEvidenceManifestArtifactSummary {
  // 只读摘要沿用 manifest 脚本的字段语义，但仍把绝对路径压缩成安全 token。
  const record = asRecord(artifact);
  if (!record) {
    return missingManifestArtifact(root, fallbackName, "missing");
  }
  const summary: O7FieldEvidenceManifestArtifactSummary = {
    required: asBoolean(record.required),
    present: asBoolean(record.present),
    path: safePathToken(record.path ?? path.join(root || ".", fallbackName)),
    size_bytes: asNumber(record.size_bytes) ?? 0,
    mtime_utc: typeof record.mtime_utc === "string" ? record.mtime_utc : null,
    sha256: typeof record.sha256 === "string" ? record.sha256 : null,
    reason: typeof record.reason === "string" ? record.reason : null,
  };
  if (typeof record.file_count === "number" && Number.isFinite(record.file_count)) {
    summary.file_count = record.file_count;
  }
  if (Array.isArray(record.files)) {
    summary.files = record.files
      .slice(0, 10)
      .map((file) => asRecord(file))
      .filter((file): file is JsonRecord => Boolean(file))
      .map((file) => ({
        path: safePathToken(file.path),
        size_bytes: asNumber(file.size_bytes) ?? 0,
        sha256: asString(file.sha256, ""),
      }));
  }
  return summary;
}

function buildManifestSummary(manifest: JsonRecord | null): O7FieldEvidenceManifestSummary {
  // manifest 只接收本轮脚本输出的安全摘要；一旦结构偏移，就按 not_loaded 处理。
  if (!manifest) {
    return {
      schema: "not_loaded",
      run_id: "not_loaded",
      source: "not_loaded",
      mode: "not_loaded",
      status: "manifest_not_loaded",
      gate_pass: false,
      artifact_status: "blocked",
      blocked_reason: "manifest_not_loaded",
      not_proven: true,
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      artifact_root: "",
      preflight_status: null,
      manifest_gate: {
        schema: "not_loaded",
        status: "blocked_not_proven",
        gate_pass: false,
        blocked_reason: "manifest_not_loaded",
        source: "not_loaded",
      },
      artifact_health: {
        status: "blocked",
        required_count: MANIFEST_ARTIFACT_KEYS.length,
        present_count: 0,
        missing_count: MANIFEST_ARTIFACT_KEYS.length,
        blocked_count: 0,
        empty_count: 0,
        present_artifacts: [],
        missing_artifacts: [...MANIFEST_ARTIFACT_KEYS],
        blocked_artifacts: [],
        summary: "manifest_not_loaded",
      },
      artifacts: {
        map_yaml: missingManifestArtifact(".", "map.yaml", "manifest_not_loaded"),
        route_csv: missingManifestArtifact(".", "route.csv", "manifest_not_loaded"),
        keyframes: missingManifestArtifact(".", "keyframes", "manifest_not_loaded"),
        rosbag: missingManifestArtifact(".", "rosbag", "manifest_not_loaded"),
        replay_jsonl: missingManifestArtifact(".", "replay.jsonl", "manifest_not_loaded"),
      },
    };
  }

  const artifactRoot = asString(manifest.artifact_root, "");
  const artifacts = asRecord(manifest.artifacts);
  const manifestGate = asRecord(manifest.manifest_gate);
  const artifactHealth = asRecord(manifest.artifact_health);
  return {
    schema: asString(manifest.schema, "not_loaded") === FIELD_EVIDENCE_MANIFEST_SCHEMA ? FIELD_EVIDENCE_MANIFEST_SCHEMA : "not_loaded",
    run_id: asString(manifest.run_id, "not_loaded"),
    source: asString(manifest.source, "not_loaded") as O7FieldEvidenceManifestSummary["source"],
    mode: asString(manifest.mode, "not_loaded") as O7FieldEvidenceManifestSummary["mode"],
    status: asString(manifest.status, "manifest_not_loaded"),
    gate_pass: asBoolean(manifest.gate_pass),
    artifact_status: normalizeManifestArtifactStatus(manifest.artifact_status),
    blocked_reason: asString(manifest.blocked_reason, "manifest_not_loaded"),
    not_proven: asBoolean(manifest.not_proven),
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    artifact_root: safePathToken(artifactRoot),
    preflight_status: typeof manifest.preflight_status === "string" ? manifest.preflight_status : null,
    manifest_gate: {
      schema:
        asString(manifestGate?.schema, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA ? FIELD_EVIDENCE_MANIFEST_SCHEMA : "not_loaded",
      status: normalizeManifestGateStatus(manifestGate?.status),
      gate_pass: asBoolean(manifestGate?.gate_pass),
      blocked_reason: asString(manifestGate?.blocked_reason, "manifest_not_loaded"),
      source: asString(manifestGate?.source, "not_loaded") as O7FieldEvidenceManifestSummary["manifest_gate"]["source"],
    },
    artifact_health: {
      status: normalizeManifestArtifactStatus(artifactHealth?.status ?? manifest.artifact_status),
      required_count: asNumber(artifactHealth?.required_count) ?? MANIFEST_ARTIFACT_KEYS.length,
      present_count: asNumber(artifactHealth?.present_count) ?? 0,
      missing_count: asNumber(artifactHealth?.missing_count) ?? MANIFEST_ARTIFACT_KEYS.length,
      blocked_count: asNumber(artifactHealth?.blocked_count) ?? 0,
      empty_count: asNumber(artifactHealth?.empty_count) ?? 0,
      present_artifacts: stringList(artifactHealth?.present_artifacts),
      missing_artifacts: stringList(artifactHealth?.missing_artifacts),
      blocked_artifacts: stringList(artifactHealth?.blocked_artifacts),
      summary: asString(artifactHealth?.summary, "manifest_not_loaded"),
    },
    artifacts: {
      map_yaml: manifestArtifactSummary(artifacts?.map_yaml, artifactRoot, "map.yaml"),
      route_csv: manifestArtifactSummary(artifacts?.route_csv, artifactRoot, "route.csv"),
      keyframes: manifestArtifactSummary(artifacts?.keyframes, artifactRoot, "keyframes"),
      rosbag: manifestArtifactSummary(artifacts?.rosbag, artifactRoot, "rosbag"),
      replay_jsonl: manifestArtifactSummary(artifacts?.replay_jsonl, artifactRoot, "replay.jsonl"),
    },
  };
}

function detailFieldEvidenceSectionFromManifest(
  manifest: O7FieldEvidenceManifestSummary,
  inputStatus: DetailFieldEvidenceInputStatus,
  sourceContract: O7ConsumerTaskDetailResponse["field_evidence"]["source_contract"],
): O7ConsumerTaskDetailResponse["field_evidence"] {
  // consumer detail 统一把 manifest 关键边界收敛到一处，供 O7 页面直接展示。
  return {
    source_contract: sourceContract,
    input_status: inputStatus,
    artifact_status: manifest.artifact_status,
    manifest_gate: manifest.manifest_gate,
    blocked_reason: manifest.blocked_reason,
    not_proven: manifest.not_proven,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function extractManifestFromConsumerIngest(payload: JsonRecord): JsonRecord | null {
  // 兼容现有 ingest contract：如果 O6 detail 已挂了 ingest 摘要，就优先复用其中的 manifest。
  if (asString(payload.schema, "") !== FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA) {
    return null;
  }
  const manifest = asRecord(payload.manifest);
  return manifest && asString(manifest.schema, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA ? manifest : null;
}

function detailFieldEvidenceSource(
  remote: JsonRecord,
):
  | {
      manifest: O7FieldEvidenceManifestSummary;
      inputStatus: DetailFieldEvidenceInputStatus;
      sourceContract: O7ConsumerTaskDetailResponse["field_evidence"]["source_contract"];
    }
  | {
      errorReason: string;
      inputStatus: DetailFieldEvidenceInputStatus;
    } {
  // O7 detail 允许两种上游形态：直接挂 manifest，或挂现有 ingest contract。
  const directManifest = asRecord(remote.field_evidence_manifest) ?? asRecord(remote.manifest);
  if (directManifest) {
    const safety = manifestInputSafetyStatus(directManifest);
    if (safety.status !== "loaded") {
      return { errorReason: safety.reason, inputStatus: "unsafe_claim" };
    }
    if (asString(directManifest.schema, "") !== FIELD_EVIDENCE_MANIFEST_SCHEMA) {
      return { errorReason: "field_evidence_manifest_schema_mismatch", inputStatus: "schema_mismatch" };
    }
    return {
      manifest: buildManifestSummary(directManifest),
      inputStatus: "loaded",
      sourceContract: FIELD_EVIDENCE_MANIFEST_SCHEMA,
    };
  }

  const ingestPayload = asRecord(remote.field_evidence_consumer_ingest) ?? asRecord(remote.field_evidence_ingest);
  if (ingestPayload) {
    if (asString(ingestPayload.schema, "") !== FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA) {
      return { errorReason: "field_evidence_consumer_ingest_schema_mismatch", inputStatus: "schema_mismatch" };
    }
    const dangerous = scanDangerousTrueFields(ingestPayload);
    if (dangerous.length > 0) {
      return { errorReason: `field_evidence_consumer_ingest_unsafe_claim:${dangerous.join(",")}`, inputStatus: "unsafe_claim" };
    }
    const manifest = extractManifestFromConsumerIngest(ingestPayload);
    if (!manifest) {
      return { errorReason: "field_evidence_consumer_ingest_manifest_missing", inputStatus: "invalid_shape" };
    }
    return {
      manifest: buildManifestSummary(manifest),
      inputStatus: "loaded",
      sourceContract: FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA,
    };
  }

  return { errorReason: "field_evidence_contract_missing", inputStatus: "missing" };
}

function detailInputStatusFromLocalManifestStatus(
  status: LoadJsonStatus,
): DetailFieldEvidenceInputStatus {
  // 详情页只暴露少量 operator 可理解状态；底层读取状态在 blocked_reason 里保留细分原因。
  switch (status) {
    case "loaded":
      return "loaded";
    case "not_provided":
      return "not_provided";
    case "missing":
      return "missing";
    case "bad_json":
      return "bad_json";
    case "read_error":
      return "read_error";
    case "not_object":
      return "invalid_shape";
    case "unsupported_schema":
      return "schema_mismatch";
    case "unsafe_copy":
    case "success_claim":
    case "control_claim":
      return "unsafe_claim";
  }
}

type DetailFieldEvidenceSourceResult =
  | {
      manifest: O7FieldEvidenceManifestSummary;
      inputStatus: DetailFieldEvidenceInputStatus;
      sourceContract: O7ConsumerTaskDetailResponse["field_evidence"]["source_contract"];
    }
  | {
      errorReason: string;
      inputStatus: DetailFieldEvidenceInputStatus;
    };

async function localManifestFieldEvidenceSource(
  manifestJson: string,
): Promise<DetailFieldEvidenceSourceResult> {
  // 本地 manifest 只在远端完全缺 field evidence 时才作为补齐来源，不能覆盖远端有效合同。
  const manifestInput = await loadJsonObject(manifestJson);
  if (manifestInput.status !== "loaded") {
    return {
      errorReason: `field_evidence_manifest_json_${manifestInput.status}`,
      inputStatus: detailInputStatusFromLocalManifestStatus(manifestInput.status),
    };
  }
  const manifestSafety = manifestInputSafetyStatus(manifestInput.payload);
  if (manifestSafety.status !== "loaded") {
    return {
      errorReason: `field_evidence_manifest_json_${manifestSafety.status}`,
      inputStatus: detailInputStatusFromLocalManifestStatus(manifestSafety.status),
    };
  }
  if (asString(manifestInput.payload?.schema, "") !== FIELD_EVIDENCE_MANIFEST_SCHEMA) {
    return {
      errorReason: "field_evidence_manifest_json_schema_mismatch",
      inputStatus: "schema_mismatch",
    };
  }
  return {
    manifest: buildManifestSummary(manifestInput.payload),
    inputStatus: "loaded",
    sourceContract: FIELD_EVIDENCE_MANIFEST_SCHEMA,
  };
}

function aggregateDistinct(values: Array<string | string[] | null | undefined>): string[] {
  // 这里把 manifest、route replay 和 labeling 的缺口合并成单一展示列，避免 reviewer 来回比对。
  const flattened = values.flatMap((item) => (Array.isArray(item) ? item : item ? [item] : []));
  return [...new Set(flattened.filter((item) => item.trim()))];
}

function consumerEntryBlockedReason(
  manifest: O7FieldEvidenceManifestSummary,
  routeReplay: O7RouteReplayPreviewResponse,
  labeling: O7LabelingPreviewResponse,
): string {
  // 主入口只给第一条高信号 blocker，便于 UI 直接展示 fail-closed 原因。
  if (manifest.status !== "field_evidence_manifest_ready_not_delivery_proof") {
    return manifest.blocked_reason || manifest.status || "manifest_not_ready";
  }
  if (routeReplay.preview_status !== "fixture_preview_ready") {
    return routeReplay.input_status.failure_reason || routeReplay.blocked_reasons[0] || "route_replay_fixture_not_ready";
  }
  if (labeling.preview_status !== "fixture_preview_ready") {
    return labeling.input_status.failure_reason || labeling.blocked_reasons[0] || "labeling_fixture_not_ready";
  }
  return "";
}

function consumerEntryFallbackMode(manifest: O7FieldEvidenceManifestSummary): O7FieldEvidenceConsumerIngestResponse["consumer_entry"]["fallback_mode"] {
  // 这里仅区分 manifest 来源，不把本地 mock 和未来 live SSH 混成同一条证据。
  if (manifest.source === "local_fixture") {
    return "local_mock";
  }
  if (manifest.source === "ssh_remote") {
    return "ssh_remote";
  }
  return "blocked_not_proven";
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

export async function buildO7ConsumerTaskDetail(
  baseUrl: string,
  taskId: string,
  fieldEvidenceManifestJson = "",
): Promise<O7ConsumerTaskDetailResponse> {
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
  let fieldEvidenceSource = detailFieldEvidenceSource(remote);
  if ("errorReason" in fieldEvidenceSource) {
    if (fieldEvidenceSource.errorReason === "field_evidence_contract_missing") {
      fieldEvidenceSource = await localManifestFieldEvidenceSource(fieldEvidenceManifestJson);
    }
  }
  if ("errorReason" in fieldEvidenceSource) {
    const failClosed = failClosedDetail(fieldEvidenceSource.errorReason, normalized.normalized, trimmedTaskId);
    failClosed.field_evidence = {
      ...failClosed.field_evidence,
      input_status: fieldEvidenceSource.inputStatus,
    };
    return failClosed;
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
    field_evidence: detailFieldEvidenceSectionFromManifest(
      fieldEvidenceSource.manifest,
      fieldEvidenceSource.inputStatus,
      fieldEvidenceSource.sourceContract,
    ),
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

export interface O7FieldEvidenceConsumerIngestOptions {
  manifestJson?: string;
  routeReplayFixtureJson?: string;
  labelingFixtureJson?: string;
}

export async function buildO7FieldEvidenceConsumerIngest(
  options: O7FieldEvidenceConsumerIngestOptions = {},
): Promise<O7FieldEvidenceConsumerIngestResponse> {
  // 这条主入口把 manifest / route replay / labeling 三个只读输入拼到同一份消费摘要里。
  // 任一层失效都必须保留对应 blocked reason，但不把本地 mock 误报成真实现场成功。
  const manifestPath = asString(options.manifestJson, "").trim();
  const routeReplayPath = asString(options.routeReplayFixtureJson, "").trim();
  const labelingPath = asString(options.labelingFixtureJson, "").trim();

  const manifestInput = await loadJsonObject(manifestPath);
  const manifestSafety = manifestInputSafetyStatus(manifestInput.payload);
  const manifestSchemaOk =
    manifestInput.status === "loaded" &&
    manifestSafety.status === "loaded" &&
    asString(manifestInput.payload?.schema, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA;
  const manifestSummary = buildManifestSummary(manifestSchemaOk ? manifestInput.payload : null);
  const routeReplayPreview = await buildO7RouteReplayPreview({ fixtureJson: routeReplayPath });
  const labelingPreview = await buildO7LabelingPreview({ fixtureJson: labelingPath });

  const manifestInputStatus: O7FieldEvidenceConsumerIngestResponse["manifest_input_status"] = {
    manifest_json: safePathToken(manifestPath),
    status: (() => {
      if (manifestInput.status !== "loaded") {
        return manifestInput.status;
      }
      if (manifestSafety.status !== "loaded") {
        return manifestSafety.status;
      }
      if (!manifestSchemaOk) {
        return "unsupported_schema";
      }
      return "loaded";
    })(),
    failure_reason: (() => {
      if (manifestInput.status !== "loaded") {
        return manifestInput.reason;
      }
      if (manifestSafety.status !== "loaded") {
        return manifestSafety.reason;
      }
      if (!manifestSchemaOk) {
        return "unsupported_manifest_schema";
      }
      return "";
    })(),
  };

  const routeReplayInputStatus: O7FieldEvidenceConsumerIngestResponse["route_replay_input_status"] = {
    fixture_json: safePathToken(routeReplayPath),
    status: routeReplayPreview.input_status.status,
    failure_reason: routeReplayPreview.input_status.failure_reason,
  };

  const labelingInputStatus: O7FieldEvidenceConsumerIngestResponse["labeling_input_status"] = {
    fixture_json: safePathToken(labelingPath),
    status: labelingPreview.input_status.status,
    failure_reason: labelingPreview.input_status.failure_reason,
  };

  const entryBlockedReason = consumerEntryBlockedReason(manifestSummary, routeReplayPreview, labelingPreview);
  const blockedReasons = aggregateDistinct([
    manifestInputStatus.failure_reason,
    manifestSummary.blocked_reason,
    routeReplayPreview.blocked_reasons,
    labelingPreview.blocked_reasons,
    entryBlockedReason,
  ]);
  const notProven = aggregateDistinct([
    manifestSummary.not_proven ? "field_evidence_manifest_not_delivery_proof" : "",
    routeReplayPreview.not_proven,
    labelingPreview.not_proven,
  ]);
  const nextRequiredEvidence = aggregateDistinct([
    manifestSummary.gate_pass ? "" : "field_evidence_manifest_artifacts_complete_and_preflight_ready",
    routeReplayPreview.not_proven,
    labelingPreview.not_proven,
  ]);

  const ingestReady =
    manifestSummary.schema === FIELD_EVIDENCE_MANIFEST_SCHEMA &&
    manifestSummary.status === "field_evidence_manifest_ready_not_delivery_proof" &&
    manifestSummary.gate_pass &&
    manifestSummary.not_proven &&
    routeReplayPreview.preview_status === "fixture_preview_ready" &&
    labelingPreview.preview_status === "fixture_preview_ready";

  return {
    schema: FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA,
    ingest_status: ingestReady ? "fixture_consumer_ready_not_proven" : "blocked_not_proven",
    manifest_input_status: manifestInputStatus,
    route_replay_input_status: routeReplayInputStatus,
    labeling_input_status: labelingInputStatus,
    source_manifest_schema: manifestSchemaOk ? FIELD_EVIDENCE_MANIFEST_SCHEMA : "not_loaded",
    manifest: manifestSummary,
    route_replay_preview: routeReplayPreview,
    labeling_preview: labelingPreview,
    consumer_entry: {
      primary_path: "/api/o7/field-evidence-consumer-ingest",
      route_replay_path: "/api/o7/route-replay-preview",
      labeling_path: "/api/o7/labeling-preview",
      fallback_mode: consumerEntryFallbackMode(manifestSummary),
      blocked_reason: entryBlockedReason,
    },
    blocked_reasons: blockedReasons,
    not_proven: notProven,
    next_required_evidence: nextRequiredEvidence,
    ...PROOF_FLAGS,
  };
}
