import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7CloudArchiveTaskSafeSummaries,
  O7CloudArchiveTasksResponse,
  O7CloudArchiveTaskSummary,
  O7RouteReplayInspector,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7CloudArchiveTasksOptions {
  archiveJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.cloud_archive_fixture.v1" as const;
const TASK_LIMIT = 20;
const SAMPLE_LIMIT = 5;

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
  "Traceback",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\bdropoff\s+(success|succeeded|completed|complete)\b/i,
  /\bcloud\s+archive\s+(connected|ready|live|success)\b/i,
  /"delivery_success"\s*:\s*true/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"safe_to_control"\s*:\s*true/i,
  /"primary_actions_enabled"\s*:\s*true/i,
  /"robot_control_executed"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
];

const REAL_API_CLAIM_PATTERNS = [
  /"real_cloud_archive_connected"\s*:\s*true/i,
  /"real_realtime_api_connected"\s*:\s*true/i,
  /"real_annotation_api_connected"\s*:\s*true/i,
  /"real_voice_api_connected"\s*:\s*true/i,
  /"real_command_api_connected"\s*:\s*true/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/gi, "$1=[REDACTED]"],
  [/\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\/[^,\s]+/gi, "[REDACTED_URL]"],
  [/\/cmd_vel\b/g, "[REDACTED_ROS_TOPIC]"],
  [/\/dev\/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*/gi, "/dev/[REDACTED_DEVICE]"],
  [/\b[A-Za-z]:\\[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\/(Users|home|tmp|private|var|mnt|run|workspace|ws)\/[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/Traceback \(most recent call last\):[\s\S]*/gi, "[REDACTED_TRACEBACK]"],
];

// 该 adapter 是 O7 统一数据源的最小 software-proof 入口，只读取 operator 显式指定的本地 archive JSON。
// 它不连接 O6 云归档、不轮询 realtime、不提交标注、不发送 TTS、不下发手控/寻路命令。
// 响应只输出白名单摘要和 fixed false 字段，防止历史任务 fixture 被误读为真实云端已接通。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一为空字符串，避免 null/undefined 在 UI 中看起来像真实业务值。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 所有可展示文本都脱敏，archive fixture 不允许泄露本机路径、凭证或控制 topic。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // evidence/media 引用只保留 basename；绝对路径不会进入 API 响应。
  const raw = asText(value).trim();
  if (!raw) {
    return "";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return safeText(raw);
}

function safeNumber(value: unknown): number | null {
  // 只接受真实有限 number，避免把字符串里的不可信 payload 提升为业务时间戳。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function encoded(value: unknown): string {
  // 安全扫描覆盖完整 payload；异常对象退回空对象文本并走正常 fail-closed 分支。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，不生成任何任务摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function hasSuccessClaim(value: unknown): boolean {
  // 本地 archive fixture 不能自证云归档已接通或任务交付成功。
  const payload = encoded(value);
  return SUCCESS_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasControlClaim(value: unknown): boolean {
  // 任意控制开关为 true 都说明 fixture 越界，必须 fail closed。
  const payload = encoded(value);
  return CONTROL_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasRealApiClaim(value: unknown): boolean {
  // 真实云端、实时、标注、语音和命令 API 都不能由 fixture 自证 connected。
  const payload = encoded(value);
  return REAL_API_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function fixedFalseFields(): O7CloudArchiveTasksResponse["fixed_false_fields"] {
  // fixed_false_fields 让 UI 和测试能集中复核所有危险能力都保持关闭。
  return {
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    robot_control_executed: false,
  };
}

function emptyRouteReplayInspector(
  blockedReasons: string[],
  selectedTaskId: string | null = null,
): O7RouteReplayInspector {
  // inspector 失败时也返回完整只读结构，前端不用根据缺字段自行补安全状态。
  return {
    status: "blocked_not_proven",
    selected_task_id: selectedTaskId,
    map_frame: "",
    frame_count: 0,
    sample_frames: [],
    event_timeline: [],
    keyframe_refs: [],
    cursor_initial_state: {
      playing: false,
      safe_to_play: false,
      speed: 0,
      frame_index: null,
    },
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_history_route_replay",
      "real_o7_cloud_archive_task_api",
      "safe_route_playback",
      "real_robot_control",
    ],
  };
}

function emptySummaries(status: "fixture_summary_only" | "blocked_not_proven"): O7CloudArchiveTaskSafeSummaries {
  // 空摘要也显式带 false 字段，避免前端根据缺字段自行推断。
  return {
    trajectory: { frame_count: 0, sample_refs: [], status },
    events: { event_count: 0, sample_types: [], status },
    labels: { label_count: 0, sample_types: [], real_annotation_api_connected: false, status },
    voice: { asr_event_count: 0, tts_draft_count: 0, real_voice_api_connected: false, status },
    commands: { command_count: 0, sample_kinds: [], real_command_api_connected: false, robot_control_executed: false, status },
  };
}

function blockedResponse(
  status: O7CloudArchiveTasksResponse["input_status"]["status"],
  failureReason: string,
  archivePath = "",
): O7CloudArchiveTasksResponse {
  const blockedReasons = [failureReason];
  // 失败也返回完整 schema，调用方不用靠 HTTP 500 或缺字段判断安全边界。
  return {
    schema: "trashbot.o7.cloud_archive_tasks.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    archive_status: "blocked_not_proven",
    input_status: {
      archive_json: safeRef(archivePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    robot_control_executed: false,
    task_list: {
      source: "local_json_fixture",
      total_tasks: 0,
      tasks: [],
      status: "blocked_not_proven",
    },
    selected_task: null,
    latest_task: null,
    safe_summaries: emptySummaries("blocked_not_proven"),
    route_replay_inspector: emptyRouteReplayInspector(blockedReasons),
    fixed_false_fields: fixedFalseFields(),
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_cloud_archive_task_api",
      "real_o7_realtime_api",
      "real_o7_annotation_api",
      "real_o7_voice_api",
      "real_o7_command_api",
      "real_robot_control",
      "delivery_success",
    ],
  };
}

function taskSummary(value: unknown): O7CloudArchiveTaskSummary {
  // task 摘要只保留 selector 需要的稳定字段，不透传完整任务 payload。
  const task = isObject(value) ? value : {};
  return {
    task_id: safeText(task.task_id || task.id || "task_id_missing"),
    robot_id: safeText(task.robot_id || "robot_id_missing"),
    route_id: safeText(task.route_id || "route_id_missing"),
    status: safeText(task.status || task.task_status || "status_missing"),
    started_at_ms: safeNumber(task.started_at_ms),
    updated_at_ms: safeNumber(task.updated_at_ms ?? task.completed_at_ms),
    evidence_ref: safeRef(task.evidence_ref),
  };
}

function listFromTask(task: JsonObject, key: string): unknown[] {
  // archive fixture 允许按任务内嵌数组给出数据；非数组一律按空处理。
  const value = task[key];
  return Array.isArray(value) ? value : [];
}

function sampleTypes(values: unknown[], keys: string[]): string[] {
  // 类型列表只用于 operator 快速判断数据形态，限量后不会泄露完整 event/label/command。
  return values.slice(0, SAMPLE_LIMIT).map((value) => {
    const item = isObject(value) ? value : {};
    const found = keys.map((key) => item[key]).find((candidate) => asText(candidate).trim());
    return safeText(found || "type_missing");
  });
}

function sampleRefs(values: unknown[]): string[] {
  // 轨迹/关键帧引用只返回安全 basename，完整 archive 不通过该 API 搬运。
  return values.slice(0, SAMPLE_LIMIT).map((value) => {
    const item = isObject(value) ? value : {};
    return safeRef(item.evidence_ref ?? item.frame_ref ?? item.keyframe_ref);
  }).filter(Boolean);
}

function nestedObject(value: unknown): JsonObject {
  // trajectory frame 常把 pose/velocity 放在子对象里；非对象按空对象处理来保持 fail-soft 摘要。
  return isObject(value) ? value : {};
}

function frameNumber(frame: JsonObject, key: string, nested: JsonObject): number | null {
  // 只接受有限 number，字符串数值不会被提升，避免 fixture 文本注入成真实轨迹坐标。
  return safeNumber(frame[key]) ?? safeNumber(nested[key]);
}

function routeReplayInspectorFor(task: JsonObject | null): O7RouteReplayInspector {
  if (!task) {
    return emptyRouteReplayInspector(["selected_task_missing"]);
  }

  const selectedTaskId = safeText(task.task_id || task.id || "task_id_missing");
  const trajectory = listFromTask(task, "trajectory_frames");
  const events = [...listFromTask(task, "events"), ...listFromTask(task, "state_transitions")];
  const sampleFrames = trajectory.slice(0, SAMPLE_LIMIT).map((value, index) => {
    const frame = isObject(value) ? value : {};
    const pose = nestedObject(frame.pose);
    const velocity = nestedObject(frame.velocity);
    const frameIndex = safeNumber(frame.frame_index) ?? index;
    return {
      frame_index: frameIndex,
      timestamp_ms: safeNumber(frame.timestamp_ms),
      x_m: frameNumber(frame, "x_m", pose) ?? safeNumber(pose.x),
      y_m: frameNumber(frame, "y_m", pose) ?? safeNumber(pose.y),
      yaw_rad: frameNumber(frame, "yaw_rad", pose),
      speed_mps: safeNumber(frame.speed_mps) ?? safeNumber(frame.linear_mps) ?? safeNumber(velocity.speed_mps) ?? safeNumber(velocity.linear_mps),
      state: safeText(frame.state || frame.task_state || "state_missing"),
      evidence_ref: safeRef(frame.evidence_ref ?? frame.frame_ref ?? frame.keyframe_ref),
    };
  });
  const keyframeRefs = listFromTask(task, "keyframe_refs").slice(0, SAMPLE_LIMIT).map((value) => (
    isObject(value) ? safeRef(value.evidence_ref ?? value.keyframe_ref ?? value.frame_ref) : safeRef(value)
  )).filter(Boolean);

  return {
    status: trajectory.length > 0 ? "fixture_inspector_ready" : "blocked_not_proven",
    selected_task_id: selectedTaskId,
    map_frame: safeText(task.map_frame || "map"),
    frame_count: trajectory.length,
    sample_frames: sampleFrames,
    event_timeline: events.slice(0, SAMPLE_LIMIT).map((value) => {
      const event = isObject(value) ? value : {};
      return {
        event_type: safeText(event.event_type || event.type || "event_type_missing"),
        state: safeText(event.state || event.to || event.to_state || "state_missing"),
        timestamp_ms: safeNumber(event.timestamp_ms),
        evidence_ref: safeRef(event.evidence_ref ?? event.event_ref),
      };
    }),
    keyframe_refs: keyframeRefs,
    cursor_initial_state: {
      playing: false,
      safe_to_play: false,
      speed: 0,
      frame_index: sampleFrames[0]?.frame_index ?? null,
    },
    blocked_reasons: [
      "real_cloud_archive_not_connected",
      "safe_route_playback_not_enabled",
      "robot_control_disabled",
    ],
    not_proven: [
      "real_o7_history_route_replay",
      "real_o7_cloud_archive_task_api",
      "safe_route_playback",
      "real_robot_control",
    ],
  };
}

function safeSummariesFor(task: JsonObject | null): O7CloudArchiveTaskSafeSummaries {
  if (!task) {
    return emptySummaries("blocked_not_proven");
  }
  const trajectory = listFromTask(task, "trajectory_frames");
  const events = listFromTask(task, "events");
  const labels = listFromTask(task, "labels");
  const asrEvents = listFromTask(task, "asr_events");
  const ttsDrafts = listFromTask(task, "tts_drafts");
  const commands = listFromTask(task, "commands");
  return {
    trajectory: {
      frame_count: trajectory.length,
      sample_refs: sampleRefs(trajectory),
      status: "fixture_summary_only",
    },
    events: {
      event_count: events.length,
      sample_types: sampleTypes(events, ["event_type", "type", "state"]),
      status: "fixture_summary_only",
    },
    labels: {
      label_count: labels.length,
      sample_types: sampleTypes(labels, ["label_type", "type"]),
      real_annotation_api_connected: false,
      status: "fixture_summary_only",
    },
    voice: {
      asr_event_count: asrEvents.length,
      tts_draft_count: ttsDrafts.length,
      real_voice_api_connected: false,
      status: "fixture_summary_only",
    },
    commands: {
      command_count: commands.length,
      sample_kinds: sampleTypes(commands, ["command_type", "kind", "type"]),
      real_command_api_connected: false,
      robot_control_executed: false,
      status: "fixture_summary_only",
    },
  };
}

function latestTask(tasks: JsonObject[]): JsonObject | null {
  // latest 只基于 fixture 时间戳排序；没有时间戳时回退到最后一个任务，仍是 software proof。
  if (tasks.length === 0) {
    return null;
  }
  return [...tasks].sort((left, right) => {
    const leftTime = safeNumber(left.updated_at_ms ?? left.started_at_ms) ?? -1;
    const rightTime = safeNumber(right.updated_at_ms ?? right.started_at_ms) ?? -1;
    return rightTime - leftTime;
  })[0] ?? tasks[tasks.length - 1] ?? null;
}

export async function buildO7CloudArchiveTasks(options: O7CloudArchiveTasksOptions = {}): Promise<O7CloudArchiveTasksResponse> {
  const archiveJson = options.archiveJson?.trim() ?? "";
  if (!archiveJson) {
    return blockedResponse("not_provided", "archive_json_not_provided");
  }

  let raw = "";
  try {
    raw = await fs.readFile(archiveJson, "utf8");
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    return blockedResponse(code === "ENOENT" ? "missing" : "read_error", "archive_json_read_failed", archiveJson);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return blockedResponse("bad_json", "archive_json_bad_json", archiveJson);
  }

  if (!isObject(parsed)) {
    return blockedResponse("not_object", "archive_json_not_object", archiveJson);
  }
  if (parsed.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "archive_json_unsupported_schema", archiveJson);
  }
  if (hasForbiddenCopy(parsed)) {
    return blockedResponse("unsafe_copy", "archive_json_unsafe_copy", archiveJson);
  }
  if (hasSuccessClaim(parsed)) {
    return blockedResponse("success_claim", "archive_json_success_claim", archiveJson);
  }
  if (hasControlClaim(parsed)) {
    return blockedResponse("control_claim", "archive_json_control_claim", archiveJson);
  }
  if (hasRealApiClaim(parsed)) {
    return blockedResponse("real_api_claim", "archive_json_real_api_claim", archiveJson);
  }

  const taskObjects = (Array.isArray(parsed.tasks) ? parsed.tasks : []).filter(isObject);
  const selectedId = safeText(parsed.selected_task_id);
  const selected = taskObjects.find((task) => safeText(task.task_id || task.id) === selectedId) ?? latestTask(taskObjects);
  const latest = latestTask(taskObjects);

  return {
    schema: "trashbot.o7.cloud_archive_tasks.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    archive_status: "fixture_archive_ready",
    input_status: {
      archive_json: safeRef(archiveJson),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    robot_control_executed: false,
    task_list: {
      source: "local_json_fixture",
      total_tasks: taskObjects.length,
      tasks: taskObjects.slice(0, TASK_LIMIT).map(taskSummary),
      status: "fixture_summary_only",
    },
    selected_task: selected ? taskSummary(selected) : null,
    latest_task: latest ? taskSummary(latest) : null,
    safe_summaries: safeSummariesFor(selected),
    route_replay_inspector: routeReplayInspectorFor(selected),
    fixed_false_fields: fixedFalseFields(),
    blocked_reasons: [
      "real_cloud_archive_not_connected",
      "real_realtime_api_not_connected",
      "real_annotation_api_not_connected",
      "real_voice_api_not_connected",
      "real_command_api_not_connected",
      "robot_control_disabled",
    ],
    not_proven: [
      "real_o7_cloud_archive_task_api",
      "real_o7_history_route_replay",
      "real_o7_annotation_api",
      "real_o7_voice_api",
      "real_o7_command_api",
      "real_robot_control",
      "delivery_success",
    ],
  };
}
