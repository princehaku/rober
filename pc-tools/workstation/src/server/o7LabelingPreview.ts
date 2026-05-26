import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7LabelingPreviewDraftSample,
  O7LabelingPreviewItemSample,
  O7LabelingPreviewLabelSummary,
  O7LabelingPreviewResponse,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7LabelingPreviewOptions {
  fixtureJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.labeling_fixture.v1" as const;
const SAMPLE_ITEM_LIMIT = 3;
const SAMPLE_LABEL_LIMIT = 3;
const SAMPLE_REF_LIMIT = 8;
const SAMPLE_FIELD_LIMIT = 12;
const SAMPLE_FORMAT_LIMIT = 5;

const FORBIDDEN_COPY = [
  "Authorization",
  "access_key",
  "secret",
  "token",
  "password",
  "postgres://",
  "postgresql://",
  "mysql://",
  "redis://",
  "amqp://",
  "mongodb://",
  "/cmd_vel",
  "/dev/tty",
  "/dev/ttyUSB",
  "/dev/ttyACM",
  "serial",
  "UART",
  "baudrate",
  "WAVE ROVER",
  "Traceback",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\blabeling\s+(success|succeeded|completed|complete)\b/i,
  /\bannotation\s+(success|succeeded|completed|complete)\b/i,
  /"delivery_success"\s*:\s*true/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
  /"robot_control_executed"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
];

const SUBMIT_CLAIM_PATTERNS = [
  /"submit_enabled"\s*:\s*true/i,
  /"submit_available"\s*:\s*true/i,
  /\bsubmit\s+(enabled|available|ready|success|succeeded|completed)\b/i,
];

const ROLLBACK_CLAIM_PATTERNS = [
  /"rollback_enabled"\s*:\s*true/i,
  /"rollback_available"\s*:\s*true/i,
  /\brollback\s+(enabled|available|ready|success|succeeded|completed)\b/i,
];

const EXPORT_CLAIM_PATTERNS = [
  /"dataset_export_available"\s*:\s*true/i,
  /"export_available"\s*:\s*true/i,
  /\bdataset\s+export\s+(enabled|available|ready|success|succeeded|completed)\b/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\bAuthorization\s*:\s*[^,\s]+/gi, "Authorization: [REDACTED]"],
  [/\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/gi, "$1=[REDACTED]"],
  [/\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\/[^,\s]+/gi, "[REDACTED_URL]"],
  [/\/cmd_vel\b/g, "[REDACTED_ROS_TOPIC]"],
  [/\/dev\/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*/gi, "/dev/[REDACTED_DEVICE]"],
  [/\b[A-Za-z]:\\[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\/(Users|home|tmp|private|var|mnt|run|workspace|ws)\/[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+/gi, "$1=[REDACTED_RATE]"],
  [/WAVE\s+ROVER/gi, "[REDACTED_PLATFORM]"],
  [/Traceback \(most recent call last\):[\s\S]*/gi, "[REDACTED_TRACEBACK]"],
];

// 这个 adapter 只读取用户显式传入的本地 JSON，并把标注 fixture 压成安全摘要。
// 它不连接 O6 annotation API、不上传数据、不写标注文件，也不创建导出清单。
// 所有输出字段都走白名单，避免把媒体绝对路径、凭证或硬件控制 copy 泄露给 UI。
// submit/rollback/export 相关声明一旦出现在 fixture 中就 fail closed，防止 mock 被当真。
// review item、current labels、draft labels 都限量采样，完整标注数据不能通过预览 API 外泄。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一为空字符串，避免 null/undefined 被展示成业务状态。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 展示文本统一脱敏，避免 fixture 把凭证、设备路径或 traceback 传到前端。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // 引用只保留 basename；本机绝对目录结构不属于 PC preview 契约。
  const raw = asText(value).trim();
  if (!raw) {
    return "";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return safeText(raw);
}

function encoded(value: unknown): string {
  // fail-closed 扫描需要覆盖完整 payload；不可序列化时按空对象处理。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasPattern(value: unknown, patterns: RegExp[]): boolean {
  // 各类危险声明都用同一 JSON 文本扫描，避免深层字段绕过。
  const payload = encoded(value);
  return patterns.some((pattern) => pattern.test(payload));
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，不返回任何业务摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function safeStringList(value: unknown, limit: number, refMode = false): string[] {
  // 列表限量输出，防止 preview API 变成完整数据集导出通道。
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .slice(0, limit)
    .map((item) => (refMode ? safeRef(item) : safeText(item)))
    .filter(Boolean);
}

function sampleLabel(value: unknown): O7LabelingPreviewLabelSummary {
  // current/draft label 只保留类型、值、状态和证据引用，不透传原始 annotation。
  const label = isObject(value) ? value : {};
  return {
    label_type: safeText(label.label_type ?? label.type ?? "not_provided"),
    value: safeText(label.value ?? label.label ?? "not_provided"),
    status: safeText(label.status ?? "fixture_summary_only"),
    evidence_ref: safeRef(label.evidence_ref),
  };
}

function sampleReviewItem(value: unknown): O7LabelingPreviewItemSample {
  // review item 摘要保留 PC 标注面板需要定位的槽位，媒体引用仍按 basename 输出。
  const item = isObject(value) ? value : {};
  const currentLabels = Array.isArray(item.current_labels) ? item.current_labels : [];
  return {
    item_id: safeText(item.item_id ?? "not_provided"),
    task_id: safeText(item.task_id ?? "not_provided"),
    frame_id: safeText(item.frame_id ?? "not_provided"),
    media_ref: safeRef(item.media_ref),
    evidence_ref: safeRef(item.evidence_ref),
    current_labels: {
      count: currentLabels.length,
      sample: currentLabels.slice(0, SAMPLE_LABEL_LIMIT).map((label) => sampleLabel(label)),
    },
  };
}

function sampleDraftLabel(value: unknown): O7LabelingPreviewDraftSample {
  // draft 只是槽位预览，autosave 和 submit 都固定关闭。
  const draft = isObject(value) ? value : {};
  return {
    item_id: safeText(draft.item_id ?? "not_provided"),
    ...sampleLabel(draft),
  };
}

function collectItemEvidenceRefs(items: unknown[]): string[] {
  // evidence refs 仅用于证明 fixture 中有引用槽位，不证明媒体可访问。
  return items
    .slice(0, SAMPLE_REF_LIMIT)
    .map((item) => (isObject(item) ? safeRef(item.evidence_ref) : ""))
    .filter(Boolean);
}

function datasetExportGaps(payload: JsonObject): string[] {
  // gaps 描述从本地 fixture 到真实训练集导出的缺口，不代表云端已查询。
  const exportObject = isObject(payload.dataset_export) ? payload.dataset_export : {};
  const gaps = safeStringList(exportObject.gaps, SAMPLE_FIELD_LIMIT);
  const defaults = [
    "real_annotation_api_not_connected",
    "accepted_label_schema_not_proven",
    "reviewed_items_not_available",
    "dataset_manifest_export_not_available",
    "training_split_policy_not_defined",
  ];
  return Array.from(new Set([...gaps, ...defaults]));
}

function blockedResponse(
  status: O7LabelingPreviewResponse["input_status"]["status"],
  failureReason: string,
  fixturePath = "",
): O7LabelingPreviewResponse {
  // 所有失败都返回同一 schema，调用方不用根据 HTTP 错误猜测安全边界。
  return {
    schema: "trashbot.o7.labeling_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "blocked_not_proven",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_annotation_api_connected: false,
    submit_enabled: false,
    rollback_enabled: false,
    dataset_export_available: false,
    robot_control_executed: false,
    queue: {
      queue_id: "not_loaded",
      source: "local_json_fixture",
      review_item_count: 0,
      status: "blocked_not_proven",
    },
    review_items: {
      sample_limit: SAMPLE_ITEM_LIMIT,
      sample: [],
      status: "blocked_not_proven",
    },
    label_schema: {
      schema_ref: "not_loaded",
      version: "not_loaded",
      required_fields: [],
      allowed_fields: [],
      status: "blocked_not_proven",
    },
    allowed_label_types: [],
    draft_labels: {
      count: 0,
      sample: [],
      autosave_available: false,
      status: "blocked_not_proven",
    },
    dataset_export: {
      status: "blocked_not_available",
      export_ref: "not_loaded",
      supported_formats: [],
      gaps: [failureReason, "fixture_preview_blocked", "real_annotation_api_not_connected"],
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      queue_evidence_ref: "not_loaded",
      item_evidence_refs: [],
    },
    blocked_reasons: [failureReason],
    not_proven: [
      "real_o6_annotation_api",
      "real_labeling_review_queue",
      "real_annotation_submit",
      "real_annotation_rollback",
      "real_training_dataset_export",
      "delivery_success",
    ],
  };
}

async function loadFixture(filePath: string): Promise<{ payload: JsonObject | null; status: string; reason: string }> {
  // 只读单个 query 文件；目录、坏 JSON 和非对象都转换成 blocked 响应。
  if (!filePath.trim()) {
    return { payload: null, status: "not_provided", reason: "fixture_json_not_provided" };
  }
  try {
    const content = await fs.readFile(path.resolve(filePath), "utf8");
    const parsed = JSON.parse(content) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, status: "not_object", reason: "fixture_json_not_object" };
    }
    return { payload: parsed, status: "loaded", reason: "" };
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

export async function buildO7LabelingPreview(
  options: O7LabelingPreviewOptions = {},
): Promise<O7LabelingPreviewResponse> {
  // 主入口按固定顺序检查危险声明，任何 mock 成功或动作能力都不能进入 ready 摘要。
  const fixturePath = asText(options.fixtureJson).trim();
  const loaded = await loadFixture(fixturePath);
  if (!loaded.payload) {
    return blockedResponse(loaded.status as O7LabelingPreviewResponse["input_status"]["status"], loaded.reason, fixturePath);
  }
  if (loaded.payload.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "unsupported_fixture_schema", fixturePath);
  }
  if (hasForbiddenCopy(loaded.payload)) {
    return blockedResponse("unsafe_copy", "fixture_contains_unsafe_copy", fixturePath);
  }
  if (hasPattern(loaded.payload, SUCCESS_CLAIM_PATTERNS)) {
    return blockedResponse("success_claim", "fixture_contains_success_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, CONTROL_CLAIM_PATTERNS)) {
    return blockedResponse("control_claim", "fixture_contains_control_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, SUBMIT_CLAIM_PATTERNS)) {
    return blockedResponse("submit_claim", "fixture_contains_submit_availability_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ROLLBACK_CLAIM_PATTERNS)) {
    return blockedResponse("rollback_claim", "fixture_contains_rollback_availability_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, EXPORT_CLAIM_PATTERNS)) {
    return blockedResponse("export_claim", "fixture_contains_dataset_export_availability_claim", fixturePath);
  }

  const reviewItems = Array.isArray(loaded.payload.review_items) ? loaded.payload.review_items : [];
  const labelSchema = isObject(loaded.payload.label_schema) ? loaded.payload.label_schema : {};
  const draftLabels = Array.isArray(loaded.payload.draft_labels) ? loaded.payload.draft_labels : [];
  const datasetExport = isObject(loaded.payload.dataset_export) ? loaded.payload.dataset_export : {};
  const evidenceRef = safeRef(loaded.payload.evidence_ref);

  return {
    schema: "trashbot.o7.labeling_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "fixture_preview_ready",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_annotation_api_connected: false,
    submit_enabled: false,
    rollback_enabled: false,
    dataset_export_available: false,
    robot_control_executed: false,
    queue: {
      queue_id: safeText(loaded.payload.queue_id || "not_provided"),
      source: "local_json_fixture",
      review_item_count: reviewItems.length,
      status: "fixture_summary_only",
    },
    review_items: {
      sample_limit: SAMPLE_ITEM_LIMIT,
      sample: reviewItems.slice(0, SAMPLE_ITEM_LIMIT).map((item) => sampleReviewItem(item)),
      status: "fixture_summary_only",
    },
    label_schema: {
      schema_ref: safeRef(labelSchema.schema_ref ?? labelSchema.name ?? "not_provided"),
      version: safeText(labelSchema.version ?? "not_provided"),
      required_fields: safeStringList(labelSchema.required_fields, SAMPLE_FIELD_LIMIT),
      allowed_fields: safeStringList(labelSchema.allowed_fields, SAMPLE_FIELD_LIMIT),
      status: "fixture_schema_summary_only",
    },
    allowed_label_types: safeStringList(loaded.payload.allowed_label_types, SAMPLE_FIELD_LIMIT),
    draft_labels: {
      count: draftLabels.length,
      sample: draftLabels.slice(0, SAMPLE_LABEL_LIMIT).map((label) => sampleDraftLabel(label)),
      autosave_available: false,
      status: "fixture_draft_slots_only",
    },
    dataset_export: {
      status: "fixture_gap_summary_only",
      export_ref: safeRef(datasetExport.export_ref ?? "not_available"),
      supported_formats: safeStringList(datasetExport.supported_formats, SAMPLE_FORMAT_LIMIT),
      gaps: datasetExportGaps(loaded.payload),
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      queue_evidence_ref: evidenceRef,
      item_evidence_refs: collectItemEvidenceRefs(reviewItems),
    },
    blocked_reasons: [
      "real_annotation_api_not_connected",
      "submit_disabled",
      "rollback_disabled",
      "dataset_export_disabled",
      "delivery_success_not_proven",
    ],
    not_proven: [
      "real_o6_annotation_api",
      "real_labeling_review_queue",
      "real_label_schema_api",
      "real_review_item_media",
      "real_draft_label_autosave",
      "real_annotation_submit",
      "real_annotation_rollback",
      "real_training_dataset_export",
      "delivery_success",
    ],
  };
}
