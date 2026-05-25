import { promises as fs } from "node:fs";
import path from "node:path";
import { NOT_PROVEN_ITEMS } from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface RouteDebugLoadOptions {
  statusJson?: string;
  taskRecord?: string;
  taskRecordDir?: string;
  elevatorRouteReconciliation?: string;
}

interface LoadedJson {
  payload: JsonObject | null;
  issue: string;
  safeRef: string;
}

const ROUTE_CONSOLE_BOUNDARY = "software_proof_docker_pc_route_debug_console_gate" as const;
const ROUTE_ELEVATOR_CONSOLE_INTEGRATION_BOUNDARY =
  "software_proof_docker_pc_route_elevator_console_integration_gate" as const;
const ELEVATOR_ROUTE_RECONCILIATION_BOUNDARY =
  "software_proof_docker_elevator_route_evidence_reconciliation_gate";
const ELEVATOR_ROUTE_RECONCILIATION_SOURCE = "software_proof";

interface ReconciliationSummary extends JsonObject {
  lookup_status: string;
  evidence_boundary: typeof ROUTE_ELEVATOR_CONSOLE_INTEGRATION_BOUNDARY;
}

const ELEVATOR_ROUTE_RECONCILIATION_SCHEMAS = new Set([
  "trashbot.elevator_route_evidence_reconciliation.v1",
  "trashbot.elevator_route_evidence_reconciliation_summary.v1",
]);

const FORBIDDEN_COPY = [
  "Authorization",
  "OSS_ACCESS_KEY",
  "OSS_SECRET",
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
  "/dev/ttyUSB",
  "/dev/ttyACM",
  "serial",
  "UART",
  "baudrate",
  "baud_rate",
  "WAVE ROVER",
  "Traceback",
  "checksum",
  "complete artifact",
  "raw robot response",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\bdropoff\s+(success|succeeded|completed|complete)\b/i,
  /\bcancel\s+(completed|complete|success|succeeded)\b/i,
  /\bhil_pass\s*[:=]\s*true\b/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
  /\bworkstation_executes_control\s*[:=]\s*true\b/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\bAuthorization\s*:\s*[^,\s]+/gi, "Authorization: [REDACTED]"],
  [/\bOSS_ACCESS_KEY[A-Z_]*\b\s*[:=]\s*[^,\s]+/gi, "OSS_ACCESS_KEY=[REDACTED]"],
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

// 该模块只读本地 JSON 并压成 safe summary。
// 它不执行 Python、不写 evidence/route 文件，也不触发任何 ROS2 或串口能力。
// 这里保留 route console 的证明边界常量，是为了 Node API 与历史证据口径一致。
// 所有失败都转成 blocked/not_proven 字段，前端不得自行猜测成功。
// 输入路径只用于读取，输出只保留 file:basename，避免把本机目录暴露到页面。
// JSON 内容先经过 forbidden/success 检查，再进入递归脱敏摘要。
// `delivery_success=false` 是允许字段；自然语言成功声明仍必须拒绝。
// reconciliation 只接受旧 gate 的 schema/source/boundary 白名单。
// task_record_dir 自动匹配 evidence_ref，避免把历史任务错配给当前路线。
// 如果 evidence_ref 不一致，摘要仍返回固定结构，但状态必须 blocked。
// 路线 status 本身没有强制 schema；若出现 schema/boundary 且不匹配则拒绝。
// 这兼容旧样例，同时阻止其他 artifact 假冒 route status。
// 所有辅助函数都返回普通对象，便于 Vitest 直接断言 API 契约。
// 后续若需要真实控制，应新建 schema，不能扩展本 loader 的只读语义。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown): string {
  // 统一文本转换便于做脱敏和 evidence_ref 对齐，不让 null 变成 "null"。
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

function safeText(value: unknown): string {
  // 展示文本先做敏感模式替换，避免坏 JSON 把硬件或凭证细节带到 UI。
  return SENSITIVE_PATTERNS.reduce((acc, [pattern, replacement]) => acc.replace(pattern, replacement), text(value));
}

function safeRef(value: unknown): string {
  // 路径引用只保留文件名；普通逻辑引用原样脱敏后展示。
  const raw = text(value).trim();
  if (!raw) {
    return "";
  }
  const basename = path.basename(raw);
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${basename}`;
  }
  return safeText(raw);
}

function safeValue(value: unknown): unknown {
  // safe summary 递归脱敏键和值，防止嵌套 artifact 夹带敏感文本。
  if (Array.isArray(value)) {
    return value.map((item) => safeValue(item));
  }
  if (isObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [safeText(key), safeValue(item)]));
  }
  return typeof value === "string" ? safeText(value) : value;
}

function encoded(value: unknown): string {
  // 安全扫描覆盖完整对象；无法序列化时退回文本扫描。
  try {
    return JSON.stringify(value);
  } catch {
    return safeText(value);
  }
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中控制、凭证、串口、traceback 或 checksum 说明输入不适合复制到 PC UI。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function hasSuccessClaim(value: unknown): boolean {
  // 禁止自然语言完成声明和 hil_pass=true，避免软件证明冒充现场成功。
  const payload = encoded(value);
  return SUCCESS_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasControlClaim(value: unknown): boolean {
  // 任意输入声称可控制都必须 blocked，PC 工作站本轮没有控制授权。
  const payload = encoded(value);
  return CONTROL_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function firstText(...values: unknown[]): string {
  // 不同阶段 status 字段有别名；只取第一个非空值保持兼容。
  for (const value of values) {
    const candidate = safeText(value).trim();
    if (candidate) {
      return candidate;
    }
  }
  return "";
}

function safeList(value: unknown, limit = 12): unknown[] {
  // 列表限长避免把完整 artifact 搬进工作站响应。
  if (Array.isArray(value)) {
    return value.slice(0, limit).map((item) => safeValue(item));
  }
  return value === undefined || value === null || value === "" ? [] : [safeValue(value)];
}

async function loadJson(filePath: string | undefined, label: string): Promise<LoadedJson> {
  // 缺路径、缺文件、坏 JSON 都返回 issue，不抛给 Express 造成 500。
  const rawPath = text(filePath).trim();
  if (!rawPath) {
    return { payload: null, issue: "not_provided", safeRef: "" };
  }
  try {
    const content = await fs.readFile(path.resolve(rawPath), "utf8");
    const parsed = JSON.parse(content) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, issue: `${label}_not_object`, safeRef: safeRef(rawPath) };
    }
    return { payload: parsed, issue: "", safeRef: safeRef(rawPath) };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return { payload: null, issue: `${label}_missing`, safeRef: safeRef(rawPath) };
    }
    return { payload: null, issue: `${label}_read_error`, safeRef: safeRef(rawPath) };
  }
}

function routeProgress(status: JsonObject | null): JsonObject | null {
  // route_progress 是复盘主视图；缺少嵌套对象时从顶层字段保守补齐。
  if (!status) {
    return null;
  }
  const progress = isObject(status.route_progress) ? status.route_progress : {};
  const rawTarget = isObject(progress.target) ? progress.target : isObject(status.target) ? status.target : status.current_target;
  return {
    route_id: firstText(progress.route_id, status.route_id, "unknown_route"),
    route_file_basename: firstText(progress.route_file_basename, status.route_file_basename, path.basename(text(status.route_file))),
    checkpoint_id: firstText(progress.checkpoint_id, status.checkpoint_id),
    checkpoint: progress.checkpoint ?? status.checkpoint ?? status.current_index ?? null,
    current_index: progress.current_index ?? status.current_index ?? status.checkpoint ?? null,
    total_checkpoints: progress.total_checkpoints ?? status.total ?? null,
    target: isObject(rawTarget) ? safeValue(rawTarget) : {},
    route_contract_version: firstText(progress.route_contract_version, status.route_contract_version, "fixed_route.v1"),
    source: firstText(progress.source, status.source, "fixed_route_status_json"),
    failure_code: firstText(progress.failure_code, status.failure_code),
    evidence_ref: safeRef(firstText(progress.evidence_ref, status.evidence_ref)),
  };
}

function keyframePreflight(status: JsonObject | null): JsonObject | null {
  // keyframe_preflight 只展示计数和缺失摘要，不复制关键帧绝对路径。
  if (!status) {
    return null;
  }
  const preflight = isObject(status.keyframe_preflight) ? status.keyframe_preflight : {};
  return {
    enabled: Boolean(preflight.enabled ?? status.enable_visual_gate ?? false),
    route_visual_ready: Boolean(preflight.route_visual_ready ?? false),
    total_checkpoints: preflight.total_checkpoints ?? status.total ?? null,
    loaded_keyframes: Array.isArray(preflight.loaded_keyframes)
      ? preflight.loaded_keyframes.length
      : preflight.loaded_keyframes ?? 0,
    missing_keyframes: safeValue(preflight.missing_keyframes ?? []),
    invalid_keyframes: safeValue(preflight.invalid_keyframes ?? []),
    visual_gate_status: firstText(status.visual_gate_status, "not_checked"),
    visual_gate_detail: firstText(status.visual_gate_detail, status.failure_reason),
  };
}

function evidenceRefFrom(payload: JsonObject | null): string {
  // evidence_ref 可能位于顶层或 route_progress 内，统一取原始文本用于对齐。
  if (!payload) {
    return "";
  }
  const progress = isObject(payload.route_progress) ? payload.route_progress : {};
  return text(progress.evidence_ref || payload.evidence_ref || payload.result_path).trim();
}

function matchesEvidenceRef(payload: JsonObject, evidenceRef: string): boolean {
  // task_record_dir 只接受同 evidence_ref 的历史任务，避免误选其它 run。
  if (!evidenceRef) {
    return false;
  }
  if (evidenceRefFrom(payload) === evidenceRef) {
    return true;
  }
  const navResults = Array.isArray(payload.nav_results) ? payload.nav_results : [];
  return navResults.some((item) => {
    if (!isObject(item) || !isObject(item.evidence) || !isObject(item.evidence.route_progress)) {
      return false;
    }
    return text(item.evidence.route_progress.evidence_ref).trim() === evidenceRef;
  });
}

async function selectTaskRecord(options: RouteDebugLoadOptions, evidenceRef: string): Promise<LoadedJson> {
  // 显式 taskRecord 优先；目录模式只做同 run 自动定位。
  if (options.taskRecord) {
    return loadJson(options.taskRecord, "task_record");
  }
  if (!options.taskRecordDir) {
    return { payload: null, issue: "not_provided", safeRef: "" };
  }
  try {
    const root = path.resolve(options.taskRecordDir);
    const entries = await fs.readdir(root, { withFileTypes: true });
    for (const entry of entries.filter((item) => item.isFile() && item.name.endsWith(".json")).sort((a, b) => a.name.localeCompare(b.name))) {
      const candidate = await loadJson(path.join(root, entry.name), "task_record");
      if (candidate.payload && matchesEvidenceRef(candidate.payload, evidenceRef)) {
        return candidate;
      }
    }
  } catch {
    return { payload: null, issue: "task_record_dir_missing", safeRef: safeRef(options.taskRecordDir) };
  }
  return { payload: null, issue: "task_record_dir_no_matching_evidence_ref", safeRef: safeRef(options.taskRecordDir) };
}

function taskSummary(taskRecord: LoadedJson): JsonObject | null {
  // 最近任务只显示摘要字段，不声明任务完成或投放成功。
  if (!taskRecord.payload) {
    return {
      provided: false,
      lookup_status: taskRecord.issue,
      resolved_task_record: taskRecord.safeRef,
    };
  }
  const navResults = Array.isArray(taskRecord.payload.nav_results) ? taskRecord.payload.nav_results : [];
  const lastCandidate = navResults.length > 0 ? navResults[navResults.length - 1] : null;
  const lastNav = isObject(lastCandidate) ? lastCandidate : {};
  const evidence = isObject(lastNav.evidence) ? lastNav.evidence : {};
  return {
    provided: true,
    lookup_status: "found",
    resolved_task_record: taskRecord.safeRef,
    task_id: safeText(taskRecord.payload.task_id),
    final_status: firstText(taskRecord.payload.final_status, taskRecord.payload.status),
    failure_code: firstText(taskRecord.payload.failure_code, lastNav.failure_code),
    evidence_ref: safeRef(taskRecord.payload.evidence_ref),
    has_route_progress: isObject(taskRecord.payload.route_progress) && Object.keys(taskRecord.payload.route_progress).length > 0,
    has_nav_route_progress: isObject(evidence.route_progress) && Object.keys(evidence.route_progress).length > 0,
  };
}

function blockedReconciliation(issue: string, sourceRef = "", sourceSchema = ""): ReconciliationSummary {
  // 所有 reconciliation 失败返回同构对象，UI 不需要按缺字段猜原因。
  return {
    provided: false,
    lookup_status: issue,
    source_ref: sourceRef,
    source_schema: sourceSchema,
    status: issue,
    reconciliation_verdict: issue,
    evidence_boundary: ROUTE_ELEVATOR_CONSOLE_INTEGRATION_BOUNDARY,
    source_evidence_boundary: ELEVATOR_ROUTE_RECONCILIATION_BOUNDARY,
    same_evidence_ref_required: true,
    same_evidence_ref_status: "not_checked",
    evidence_ref: "",
    materials_status: {
      missing_materials: ["elevator_route_reconciliation_json"],
      mismatch_reasons: [],
      missing_materials_count: 1,
      mismatch_reasons_count: 0,
      unsafe_copy_detected: issue === "unsafe_copy",
      success_claimed_by_input: issue === "success_claim",
      control_claimed_by_input: issue === "control_claim",
    },
    operator_next_steps: [
      "Provide elevator-route-reconciliation software-proof JSON from the same evidence_ref before field-run review.",
      "Do not claim real elevator, Nav2/fixed-route, HIL, dropoff/cancel completion, or delivery success from this console.",
    ],
    not_proven: [...NOT_PROVEN_ITEMS],
    delivery_success: false as const,
    primary_actions_enabled: false as const,
  };
}

function reconciliationMaterials(payload: JsonObject): JsonObject {
  // artifact 和 phone_safe_summary 字段形态不同，这里统一成计数与短列表。
  const materials = isObject(payload.materials_status) ? payload.materials_status : {};
  return {
    missing_materials: safeList(materials.missing_materials ?? payload.missing_materials ?? []),
    mismatch_reasons: safeList(materials.mismatch_reasons ?? payload.mismatch_reasons ?? []),
    missing_materials_count: materials.missing_materials_count ?? payload.missing_materials_count ?? 0,
    mismatch_reasons_count: materials.mismatch_reasons_count ?? payload.mismatch_reasons_count ?? 0,
    unsafe_copy_detected: Boolean(materials.unsafe_copy_detected ?? false),
    success_claimed_by_input: Boolean(materials.success_claimed_by_input ?? false),
    control_claimed_by_input: Boolean(materials.control_claimed_by_input ?? false),
  };
}

async function reconciliationSummary(
  options: RouteDebugLoadOptions,
  statusEvidenceRef: string,
): Promise<ReconciliationSummary> {
  // 电梯复账 JSON 只读白名单字段，任何 schema/source/boundary 漂移都 blocked。
  const loaded = await loadJson(options.elevatorRouteReconciliation, "elevator_route_reconciliation");
  if (!loaded.payload) {
    return blockedReconciliation(loaded.issue, loaded.safeRef);
  }
  const sourcePayload = isObject(loaded.payload.phone_safe_summary) ? loaded.payload.phone_safe_summary : loaded.payload;
  const schema = firstText(sourcePayload.schema, loaded.payload.schema);
  const boundary = firstText(sourcePayload.evidence_boundary, loaded.payload.evidence_boundary);
  const source = firstText(sourcePayload.source, loaded.payload.source);
  if (!ELEVATOR_ROUTE_RECONCILIATION_SCHEMAS.has(schema)) {
    return blockedReconciliation("unsupported_schema", loaded.safeRef, schema);
  }
  if (boundary !== ELEVATOR_ROUTE_RECONCILIATION_BOUNDARY) {
    return blockedReconciliation("unsupported_boundary", loaded.safeRef, schema);
  }
  if (source && source !== ELEVATOR_ROUTE_RECONCILIATION_SOURCE) {
    return blockedReconciliation("unsupported_source", loaded.safeRef, schema);
  }
  if (loaded.payload.delivery_success === true || sourcePayload.delivery_success === true) {
    return blockedReconciliation("success_claim", loaded.safeRef, schema);
  }
  if (loaded.payload.primary_actions_enabled === true || sourcePayload.primary_actions_enabled === true) {
    return blockedReconciliation("control_claim", loaded.safeRef, schema);
  }
  if (hasForbiddenCopy(loaded.payload)) {
    return blockedReconciliation("unsafe_copy", loaded.safeRef, schema);
  }
  if (hasSuccessClaim(loaded.payload)) {
    return blockedReconciliation("success_claim", loaded.safeRef, schema);
  }
  const reconciliationEvidenceRef = text(sourcePayload.evidence_ref || loaded.payload.evidence_ref).trim();
  if (statusEvidenceRef && reconciliationEvidenceRef && reconciliationEvidenceRef !== statusEvidenceRef) {
    return blockedReconciliation("evidence_ref_mismatch", loaded.safeRef, schema);
  }
  return safeValue({
    provided: true,
    lookup_status: "found",
    source_ref: loaded.safeRef,
    source_schema: schema,
    status: firstText(sourcePayload.status, loaded.payload.reconciliation_verdict, "reconciled_not_proven"),
    reconciliation_verdict: firstText(sourcePayload.reconciliation_verdict, sourcePayload.status, "reconciled_not_proven"),
    source: source || ELEVATOR_ROUTE_RECONCILIATION_SOURCE,
    evidence_boundary: ROUTE_ELEVATOR_CONSOLE_INTEGRATION_BOUNDARY,
    source_evidence_boundary: boundary,
    same_evidence_ref_required: Boolean(sourcePayload.same_evidence_ref_required ?? loaded.payload.same_evidence_ref_required ?? true),
    same_evidence_ref_status: firstText(sourcePayload.same_evidence_ref_status, loaded.payload.same_evidence_ref_status, "not_checked"),
    evidence_ref: safeRef(reconciliationEvidenceRef),
    source_states: sourcePayload.source_states ?? loaded.payload.source_states ?? {},
    materials_status: reconciliationMaterials(sourcePayload),
    operator_next_steps: safeList(sourcePayload.operator_next_steps ?? loaded.payload.operator_next_steps ?? [], 5),
    not_proven: safeList(sourcePayload.not_proven ?? loaded.payload.not_proven ?? NOT_PROVEN_ITEMS, 24),
    delivery_success: false as const,
    primary_actions_enabled: false as const,
  }) as ReconciliationSummary;
}

function statusBoundaryIssue(status: JsonObject | null): string {
  // status JSON 没 schema 时兼容旧 fixed-route debug；出现冲突 schema/boundary 才拒绝。
  if (!status) {
    return "";
  }
  const schema = firstText(status.schema);
  const boundary = firstText(status.evidence_boundary);
  if (schema && !schema.includes("route") && !schema.includes("fixed_route")) {
    return "unsupported_schema";
  }
  if (boundary && boundary !== ROUTE_CONSOLE_BOUNDARY && boundary !== "software_proof") {
    return "unsupported_boundary";
  }
  return "";
}

export async function buildLoadedRouteConsoleSummary(options: RouteDebugLoadOptions) {
  // 主入口永远返回 fail-closed 摘要；调用方只负责合并外层 ProofFlags。
  const status = await loadJson(options.statusJson, "status_json");
  const statusIssue = status.issue && status.issue !== "not_provided" ? status.issue : "";
  const statusBoundary = statusBoundaryIssue(status.payload);
  const statusEvidenceRef = evidenceRefFrom(status.payload);
  const taskRecord = await selectTaskRecord(options, statusEvidenceRef);
  const taskEvidenceRef = evidenceRefFrom(taskRecord.payload);
  const taskMismatch = statusEvidenceRef && taskEvidenceRef && taskEvidenceRef !== statusEvidenceRef;
  const reconciliation = await reconciliationSummary(options, statusEvidenceRef);
  const blockedReasons = [
    !options.statusJson ? "status_json_not_provided" : "",
    statusIssue,
    statusBoundary,
    status.payload && hasForbiddenCopy(status.payload) ? "unsafe_copy" : "",
    status.payload && hasSuccessClaim(status.payload) ? "success_claim" : "",
    status.payload && hasControlClaim(status.payload) ? "control_claim" : "",
    taskRecord.payload && hasForbiddenCopy(taskRecord.payload) ? "task_record_unsafe_copy" : "",
    taskRecord.payload && hasSuccessClaim(taskRecord.payload) ? "task_record_success_claim" : "",
    taskRecord.payload && hasControlClaim(taskRecord.payload) ? "task_record_control_claim" : "",
    taskMismatch ? "task_record_evidence_ref_mismatch" : "",
    typeof reconciliation.lookup_status === "string" && !["found", "not_provided"].includes(reconciliation.lookup_status)
      ? String(reconciliation.lookup_status)
      : "",
  ].filter(Boolean);
  const blocked = blockedReasons.length > 0;

  return {
    route_console_summary: {
      schema: "trashbot.pc_route_debug_console.v1" as const,
      evidence_boundary: ROUTE_CONSOLE_BOUNDARY,
      route_progress: blocked && !status.payload ? null : routeProgress(status.payload),
      keyframe_preflight: blocked && !status.payload ? null : keyframePreflight(status.payload),
      current_position: status.payload
        ? ((safeValue(status.payload.current_position ?? status.payload.pose ?? {}) as JsonObject) ?? {})
        : null,
      current_checkpoint: status.payload ? (routeProgress(status.payload)?.checkpoint ?? null) : null,
      target: status.payload ? ((routeProgress(status.payload)?.target as JsonObject) ?? {}) : null,
      match_status: blocked ? "blocked_not_proven" : firstText(status.payload?.visual_gate_status, status.payload?.state, "not_checked"),
      failure: {
        status: blocked ? "blocked_not_proven" : "loaded_not_proven",
        failure_code: status.payload ? firstText(status.payload.failure_code) : "",
        failure_reason: blocked ? blockedReasons.join(",") : firstText(status.payload?.failure_reason),
        last_error: status.payload ? safeText(status.payload.last_error) : "",
        blocked_reasons: blockedReasons,
        fail_closed_conditions: [
          "missing_file",
          "bad_json",
          "unsupported_schema_or_boundary",
          "unsafe_copy",
          "success_or_control_claim",
          "evidence_ref_mismatch",
        ],
      },
      recent_task: taskSummary(taskRecord),
      route_elevator_reconciliation: reconciliation,
      not_proven: [...NOT_PROVEN_ITEMS],
      delivery_success: false as const,
      primary_actions_enabled: false as const,
      console_controls: "read_only" as const,
    },
    blocked_reasons: blockedReasons,
    input_status: {
      statusJson: status.payload ? "loaded" : status.issue,
      taskRecord: options.taskRecord ? (taskRecord.payload ? "loaded" : taskRecord.issue) : "not_provided",
      taskRecordDir: options.taskRecordDir ? (taskRecord.payload ? "matched" : taskRecord.issue) : "not_provided",
      elevatorRouteReconciliation: options.elevatorRouteReconciliation
        ? String(reconciliation.lookup_status ?? "blocked")
        : "not_provided",
    },
  };
}
