import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7ConsumerArtifactAccessProbeSummary,
  O7ConsumerArtifactBundleConsumerIngestSummary,
  O7ConsumerArtifactBundleReadiness,
  O7ConsumerArtifactBundleSummary,
  O7FieldEvidenceConsumerIngestResponse,
  O7ConsumerArtifactMediaDependency,
  O7ConsumerArtifactMediaPreflight,
  O7ConsumerDeliveryResultEvidenceSummary,
  O7ConsumerFieldMotionEvidencePacketSummary,
  O7ConsumerNav2GoalExecutionEvidenceSummary,
  O7ConsumerOfflineArtifactSeedSmokeSummary,
  O7ConsumerRouteDeliveryClosurePacketSummary,
  O7ConsumerCurrentFieldEvidenceMaterialSummary,
  O7ConsumerLocalizationPathMaterialReadbackSummary,
  O7ConsumerCleanBaselineNav2PathMaterialSummary,
  O7ConsumerFieldOperatorConfirmationMaterialSummary,
  O7ConsumerSameTaskFieldMaterialPacketSummary,
  O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
  O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
  O7ConsumerSameTaskMissionEvidenceGateSummary,
  O7ConsumerSameTaskMissionMaterialChecklist,
  O7ConsumerRouteBagEvidenceSummary,
  O7ConsumerRouteBagPayloadReplaySummary,
  O7ConsumerRouteBagFullSemanticDecodeMatrixSummary,
  O7ConsumerRouteBagFullSemanticDecodeMatrixTopicTypeSummary,
  O7ConsumerRouteBagPoseProgressFramePairSummary,
  O7ConsumerRouteBagPoseProgressPoseSummary,
  O7ConsumerRouteBagPoseProgressReplaySummary,
  O7ConsumerRouteBagSemanticReplaySummary,
  O7ConsumerRouteRootSeedGateSummary,
  O7FieldEvidenceManifestArtifactSummary,
  O7FieldEvidenceManifestSummary,
  O7ConsumerLabelingMvp,
  O7ConsumerLabelingMvpLabel,
  O7ConsumerLabelingMvpReviewItem,
  O7ConsumerRouteReplayMvp,
  O7ConsumerRouteReplayMvpEvent,
  O7ConsumerRouteReplayMvpFrame,
  O7ConsumerTaskDetailResponse,
  O7ConsumerTaskListItem,
  O7ConsumerTaskListResponse,
  O7AnnotationDatasetExportResult,
  O7AnnotationDatasetExportRow,
  O7AnnotationSubmitLabel,
  O7AnnotationSubmitResult,
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
type DetailFieldEvidenceSourceContract =
  O7ConsumerTaskDetailResponse["field_evidence"]["source_contract"];
type DetailFieldEvidenceSourceOrigin =
  O7ConsumerTaskDetailResponse["field_evidence"]["source_origin"];

const LIST_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_list.v1" as const;
const DETAIL_SCHEMA = "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1" as const;
const ANNOTATION_SUBMIT_SCHEMA = "trashbot.pc_tools_workstation.o7_annotation_submit_result.v1" as const;
const ANNOTATION_EXPORT_SCHEMA = "trashbot.pc_tools_workstation.o7_annotation_dataset_export_result.v1" as const;
const REMOTE_LIST_ENDPOINT = "/api/o6/consumer/tasks" as const;
const REMOTE_DETAIL_ENDPOINT_PREFIX = "/api/o6/consumer/tasks/" as const;
const REMOTE_LABEL_SUBMIT_ENDPOINT = "/api/o6/archive/labels" as const;
const REMOTE_LABEL_EXPORT_ENDPOINT_PREFIX = "/api/o6/archive/labels/" as const;
const DEFAULT_BASE_URL = "http://127.0.0.1:8088" as const;
const DEFAULT_LIST_VIEW = "summary" as const;
const DEFAULT_DETAIL_VIEW = "default" as const;
const DEFAULT_DETAIL_INCLUDE = [
  "trajectory",
  "events",
  "evidence",
  "field_evidence",
  "labeling",
  "inference",
  "tunnel",
  "artifact_access_probe",
  "offline_artifact_seed_smoke",
  "route_root_seed_gate",
  "route_bag_evidence",
  "route_bag_payload_replay",
  "route_bag_semantic_replay",
  "route_bag_full_semantic_decode_matrix",
  "route_bag_pose_progress_replay",
  "nav2_goal_execution_evidence",
  "delivery_result_evidence",
  "route_execution_result_delivery_readiness",
  "route_delivery_closure_packet",
  "same_task_field_material_packet",
  "current_field_evidence_material",
  "clean_baseline_nav2_path_material",
  "localization_path_material_readback",
  "same_task_route_execution_material_packet",
  "same_task_mission_evidence_gate",
  "field_operator_confirmation_material",
] as const;
const FIELD_EVIDENCE_MANIFEST_SCHEMA = "trashbot.field_evidence_manifest.v1" as const;
const FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA =
  "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1" as const;
const O6_ARTIFACT_BUNDLE_SCHEMA = "trashbot.o6.artifact_bundle.v1" as const;
const O6_ARTIFACT_BUNDLE_CONSUMER_INGEST_SCHEMA = "trashbot.o6.artifact_bundle_consumer_ingest.v1" as const;
const O6_ARTIFACT_MEDIA_PREFLIGHT_SCHEMA = "trashbot.o6.artifact_media_preflight.v1" as const;
const O6_ARTIFACT_ACCESS_PROBE_SCHEMA = "trashbot.o6.artifact_access_probe.v1" as const;
const O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE = "software_proof_local_mock_artifact_access_probe_only" as const;
const O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA = "trashbot.o6.offline_artifact_seed_smoke.v1" as const;
const O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE =
  "software_proof_offline_artifact_seed_smoke_only" as const;
const O6_ROUTE_ROOT_SEED_GATE_SCHEMA = "trashbot.o6.route_root_seed_gate.v1" as const;
const ROUTE_BAG_EVIDENCE_SCHEMA = "trashbot.route_bag_evidence.v1" as const;
const O6_ROUTE_BAG_EVIDENCE_SCHEMA = "trashbot.o6.route_bag_evidence.v1" as const;
const ROUTE_BAG_EVIDENCE_PROOF_SCOPE =
  "software_proof_route_bag_evidence_intake_only" as const;
const ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA = "trashbot.route_bag_payload_replay.v1" as const;
const O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA = "trashbot.o6.route_bag_payload_replay.v1" as const;
const ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE =
  "software_proof_route_bag_payload_replay_only" as const;
const ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA = "trashbot.route_bag_semantic_replay.v1" as const;
const O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA = "trashbot.o6.route_bag_semantic_replay.v1" as const;
const ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE =
  "software_proof_route_bag_semantic_replay_only" as const;
const ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA =
  "trashbot.route_bag_full_semantic_decode_matrix.v1" as const;
const O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA =
  "trashbot.o6.route_bag_full_semantic_decode_matrix.v1" as const;
const ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE =
  "software_proof_route_bag_full_semantic_decode_matrix_only" as const;
const ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA = "trashbot.route_bag_pose_progress_replay.v1" as const;
const O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA = "trashbot.o6.route_bag_pose_progress_replay.v1" as const;
const ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE =
  "software_proof_route_bag_pose_progress_replay_only" as const;
const O6_FIELD_MOTION_EVIDENCE_PACKET_SCHEMA = "trashbot.o6.field_motion_evidence_packet.v1" as const;
const FIELD_MOTION_EVIDENCE_PACKET_SCHEMA = "trashbot.field_motion_evidence_packet.v1" as const;
const FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE = "software_proof_field_motion_evidence_packet_only" as const;
const NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA = "trashbot.nav2_goal_execution_evidence.v1" as const;
const NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE =
  "software_proof_nav2_goal_execution_evidence_only" as const;
const DELIVERY_RESULT_EVIDENCE_SCHEMA = "trashbot.delivery_result_evidence.v1" as const;
const DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE = "software_proof_delivery_result_evidence_only" as const;
const O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA =
  "trashbot.o6.route_execution_result_delivery_readiness.v1" as const;
const ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE =
  "software_proof_route_execution_result_delivery_readiness_only" as const;
const O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA = "trashbot.o6.route_delivery_closure_packet.v1" as const;
const ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE =
  "software_proof_route_delivery_closure_packet_only" as const;
const SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA = "trashbot.same_task_field_material_packet.v1" as const;
const O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA =
  "trashbot.o6.same_task_field_material_packet.v1" as const;
const SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE =
  "software_proof_same_task_field_material_packet_only" as const;
const CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA = "trashbot.current_field_evidence_material.v1" as const;
const O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA =
  "trashbot.o6.current_field_evidence_material.v1" as const;
const CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE =
  "software_proof_current_field_evidence_material_only" as const;
const CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA =
  "trashbot.clean_baseline_nav2_path_material.v1" as const;
const O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA =
  "trashbot.o6.clean_baseline_nav2_path_material.v1" as const;
const CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE =
  "software_proof_clean_baseline_nav2_path_material_only" as const;
const LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA =
  "trashbot.localization_path_material_readback.v1" as const;
const O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA =
  "trashbot.o6.localization_path_material_readback.v1" as const;
const O7_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA =
  "trashbot.pc_tools_workstation.o7_localization_path_material_readback.v1" as const;
const LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE =
  "software_proof_localization_path_material_readback_only" as const;
const LOCALIZATION_PATH_MATERIAL_READY_STATUSES = new Set([
  "localization_path_material_ready_not_route_execution_proof",
  "localization_path_material_readback_ready_not_route_execution_proof",
]);
const SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA =
  "trashbot.same_task_route_execution_material_packet.v1" as const;
const O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA =
  "trashbot.o6.same_task_route_execution_material_packet.v1" as const;
const SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE =
  "software_proof_same_task_route_execution_material_packet_only" as const;
const SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA = "trashbot.same_task_mission_evidence_gate.v1" as const;
const O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA =
  "trashbot.o6.same_task_mission_evidence_gate.v1" as const;
const SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE =
  "software_proof_same_task_mission_evidence_gate_only" as const;
const FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA =
  "trashbot.field_operator_confirmation_material.v1" as const;
const O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA =
  "trashbot.o6.field_operator_confirmation_material.v1" as const;
const O7_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA =
  "trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1" as const;
const FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE =
  "software_proof_field_operator_confirmation_material_only" as const;
const SAME_TASK_MISSION_MATERIAL_CHECKLIST_SCHEMA =
  "trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1" as const;
const FIELD_EVIDENCE_SOURCE_CONTRACTS = new Set<string>([
  FIELD_EVIDENCE_MANIFEST_SCHEMA,
  FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA,
]);
const MANIFEST_ARTIFACT_KEYS = ["map_yaml", "route_csv", "keyframes", "rosbag", "replay_jsonl"] as const;
const MANIFEST_ARTIFACT_STATUSES = new Set(["gated", "missing", "blocked"]);
const MANIFEST_GATE_STATUSES = new Set(["gated", "blocked_not_proven"]);
const MVP_FRAME_SAMPLE_LIMIT = 5;
const MVP_EVENT_SAMPLE_LIMIT = 8;
const MVP_REF_SAMPLE_LIMIT = 12;
const MVP_LABEL_SAMPLE_LIMIT = 5;
const O7_ANNOTATION_LABEL_LIMIT = 5;
const O7_ANNOTATION_EXPORT_ROW_LIMIT = 5;
const O6_MEDIA_PREFLIGHT_SECTION_NAMES = ["artifact_media_preflight", "route_replay_mvp", "labeling_mvp"] as const;
const O6_ARTIFACT_BUNDLE_SECTION_NAMES = [
  "artifact_bundle_readiness",
  "artifact_bundle",
  "artifact_bundle_consumer_ingest",
  "artifact_media_preflight",
  "route_replay_mvp",
  "labeling_mvp",
] as const;

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "connects_cloud_production",
  "real_cloud_archive_connected",
  "real_annotation_api_connected",
  "real_command_api_connected",
  "robot_control_executed",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "submit_enabled",
  "submit_available",
  "rollback_enabled",
  "rollback_available",
  "dataset_export_available",
  "export_available",
  "playback_available",
  "safe_to_play",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "real_cloud_db_connected",
  "real_oss_connected",
  "real_cdn_connected",
  "media_access_proven",
  "allowlist_root_echoed",
  "real_dataset_export_connected",
  "cloud_write_executed",
  "sends_to_robot",
  "route_execution_success",
  "hil_pass",
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
  "credential",
  "bearer",
  "token",
  "password",
  "://",
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

function fixedAnnotationFalseFields() {
  // local/mock 标注写入可以被记录，但真实 API、生产云、导出可用性和控制能力必须继续固定 false。
  return {
    submit_enabled: false as const,
    rollback_enabled: false as const,
    dataset_export_available: false as const,
    real_annotation_api_connected: false as const,
    real_dataset_export_connected: false as const,
    cloud_write_executed: false as const,
    ...fixedFalseFields(),
  };
}

function safeTaskId(value: string): { ok: true; taskId: string } | { ok: false; reason: string } {
  // task_id 会进入远端路径；只允许短 token，避免路径穿越、query 注入或空任务误提交。
  const trimmed = value.trim();
  if (!trimmed) {
    return { ok: false, reason: "task_id_not_provided" };
  }
  if (!/^[A-Za-z0-9._:-]{1,80}$/.test(trimmed)) {
    return { ok: false, reason: "task_id_unsafe" };
  }
  return { ok: true, taskId: trimmed };
}

function containsUnsafeAnnotationCopy(value: unknown): boolean {
  // 标注 submit/export 不允许 token、密码、URL 或控制面词汇混入任意字段。
  const encoded = JSON.stringify(value ?? {});
  return MANIFEST_UNSAFE_COPY_PATTERNS.some((token) => encoded.includes(token));
}

function annotationText(value: unknown, fallback = "not_provided", limit = 160): string {
  // 提交给 O6 的文本必须短且不含敏感片段；坏类型直接压成 fallback。
  const text = typeof value === "string" && value.trim() ? value.trim().slice(0, limit) : fallback;
  if (containsUnsafeAnnotationCopy(text)) {
    return "[unsafe]";
  }
  return text;
}

function annotationNumber(value: unknown): number | null {
  // confidence 只接受 0..1 的有限数字，避免把字符串或 NaN 当作有效标注置信度。
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return Math.min(Math.max(value, 0), 1);
}

function rawString(value: unknown): string {
  // 媒体引用安全扫描必须看原始字符串；不能先 basename 化再把危险 URL/path 误当安全 token。
  return typeof value === "string" ? value.trim().slice(0, 512) : "";
}

function rawStringList(value: unknown, limit = 12): string[] {
  // 原始列表只用于安全扫描和缺口派生，不直接透传到 UI。
  return Array.isArray(value) ? value.map((item) => rawString(item)).filter(Boolean).slice(0, limit) : [];
}

function unsafeMediaRefReason(value: unknown): string {
  // artifact/media preflight 不接受 query/hash/credential URL、绝对路径、token 或 raw content 片段。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    text.includes("?") ||
    text.includes("#") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("credential") ||
    lowered.includes("secret") ||
    lowered.includes("password") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text)
  ) {
    return "artifact_media_preflight_unsafe_ref";
  }
  return "";
}

function normalizeSubmitLabel(value: unknown): O7AnnotationSubmitLabel | null {
  // PC adapter 只允许 O6 labels API 的白名单字段，未知字段不会被透传到本地/mock 后端。
  const label = asRecord(value);
  if (!label) {
    return null;
  }
  const itemId = annotationText(label.item_id ?? label.itemId, "", 80);
  const labelType = annotationText(label.label_type ?? label.type, "", 120);
  const valueText = annotationText(label.value ?? label.label, "", 240);
  if (!itemId || !labelType || !valueText || [itemId, labelType, valueText].includes("[unsafe]")) {
    return null;
  }
  return {
    item_id: itemId,
    item_type: annotationText(label.item_type ?? label.itemType ?? "consumer_detail_review_item", "consumer_detail_review_item", 120),
    label_type: labelType,
    value: valueText,
    confidence: annotationNumber(label.confidence),
    annotator_id: annotationText(label.annotator_id ?? label.annotatorId ?? "pc_o7_local_mock", "pc_o7_local_mock", 120),
    evidence_ref: safePathToken(label.evidence_ref ?? label.evidenceRef ?? ""),
    notes: annotationText(label.notes ?? "local/mock submit from PC O7 consumer detail; not production", "", 240),
  };
}

function submitPayloadFromBody(body: unknown):
  | { ok: true; robotId: string; labels: O7AnnotationSubmitLabel[] }
  | { ok: false; reason: string } {
  // route body 只接收 robot_id 和 labels；task_id 来自路径，避免 body 覆盖 URL 任务。
  const payload = asRecord(body);
  if (!payload) {
    return { ok: false, reason: "submit_body_not_object" };
  }
  if (containsUnsafeAnnotationCopy(payload)) {
    return { ok: false, reason: "submit_body_contains_unsafe_copy" };
  }
  const allowedKeys = new Set(["robot_id", "labels"]);
  const extraKeys = Object.keys(payload).filter((key) => !allowedKeys.has(key));
  if (extraKeys.length > 0) {
    return { ok: false, reason: `submit_body_unknown_fields:${extraKeys.join(",")}` };
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return { ok: false, reason: `dangerous_true_fields:${dangerous.join(",")}` };
  }
  const robotId = annotationText(payload.robot_id, "", 80);
  if (!robotId || robotId === "[unsafe]") {
    return { ok: false, reason: "robot_id_not_provided" };
  }
  const rawLabels = Array.isArray(payload.labels) ? payload.labels : [];
  if (rawLabels.length === 0) {
    return { ok: false, reason: "labels_not_provided" };
  }
  if (rawLabels.length > O7_ANNOTATION_LABEL_LIMIT) {
    return { ok: false, reason: "labels_too_large" };
  }
  const labels = rawLabels.map((label) => normalizeSubmitLabel(label));
  if (labels.some((label) => label === null)) {
    return { ok: false, reason: "label_schema_mismatch" };
  }
  return { ok: true, robotId, labels: labels as O7AnnotationSubmitLabel[] };
}

function failClosedAnnotationSubmit(
  reason: string,
  baseUrl: string,
  taskId: string,
  o6HttpStatus: number | null = null,
): O7AnnotationSubmitResult {
  // submit 失败也返回完整 receipt，让 UI 能展示 blocker，而不是继续停在隐藏错误。
  return {
    schema: ANNOTATION_SUBMIT_SCHEMA,
    adapter_status: "fail_closed",
    source_base_url: baseUrl || DEFAULT_BASE_URL,
    remote_endpoint: REMOTE_LABEL_SUBMIT_ENDPOINT,
    remote_schema: "not_loaded",
    requested_task_id: taskId || "not_provided",
    o6_http_status: o6HttpStatus,
    submit_receipt: {
      status: "submit_blocked_fail_closed",
      receipt_id: "not_created",
      task_id: taskId || "not_provided",
      robot_id: "not_loaded",
      label_count: 0,
      write_status: "blocked_not_proven",
      duplicate: false,
      blocked_reason: reason,
    },
    submitted_labels: [],
    label_summary: {
      itemized_label_count: 0,
      pending_item_count: 0,
      labeled_item_count: 0,
      latest_label_updated_at_ms: null,
    },
    local_mock_annotation_submit_written: false,
    blocked_reasons: [reason],
    not_proven: ["real_annotation_submit", "real_annotation_api_connected", "delivery_success"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    ...fixedAnnotationFalseFields(),
    ...PROOF_FLAGS,
  };
}

function failClosedAnnotationExport(
  reason: string,
  baseUrl: string,
  taskId: string,
  o6HttpStatus: number | null = null,
): O7AnnotationDatasetExportResult {
  // export 失败同样保持 dataset_export_available=false，避免 local/mock 与真实导出语义混淆。
  return {
    schema: ANNOTATION_EXPORT_SCHEMA,
    adapter_status: "fail_closed",
    source_base_url: baseUrl || DEFAULT_BASE_URL,
    remote_endpoint: `${REMOTE_LABEL_EXPORT_ENDPOINT_PREFIX}${taskId || "<task_id>"}/export?format=jsonl`,
    remote_schema: "not_loaded",
    requested_task_id: taskId || "not_provided",
    o6_http_status: o6HttpStatus,
    format: "blocked",
    export_status: "blocked_not_proven",
    export_manifest: {
      manifest_id: "not_created",
      task_id: taskId || "not_provided",
      robot_id: "not_loaded",
      format: "blocked",
      label_count: 0,
      item_count: 0,
      row_count: 0,
      status: "blocked_not_proven",
    },
    sample_rows: [],
    local_mock_dataset_export_written: false,
    blocked_reasons: [reason],
    not_proven: ["real_dataset_export", "real_dataset_export_connected", "delivery_success"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    ...fixedAnnotationFalseFields(),
    ...PROOF_FLAGS,
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
  const artifactAccessProbe = blockedArtifactAccessProbe(reason, taskId);
  const offlineArtifactSeedSmoke = blockedOfflineArtifactSeedSmoke(reason, taskId);
  const routeRootSeedGate = blockedRouteRootSeedGate(reason, taskId);
  const routeBagEvidence = blockedRouteBagEvidence(reason, taskId);
  const routeBagSemanticReplay = blockedRouteBagSemanticReplay(reason, taskId);
  const routeBagFullSemanticDecodeMatrix = blockedRouteBagFullSemanticDecodeMatrix(reason, taskId);
  const routeBagPoseProgressReplay = blockedRouteBagPoseProgressReplay(reason, taskId);
  const fieldMotionEvidencePacket = blockedFieldMotionEvidencePacket(reason, taskId);
  const nav2GoalExecutionEvidence = blockedNav2GoalExecutionEvidence(reason, taskId);
  const deliveryResultEvidence = blockedDeliveryResultEvidence(reason, taskId);
  const routeExecutionResultDeliveryReadiness = blockedRouteExecutionResultDeliveryReadiness(reason, taskId);
  const routeDeliveryClosurePacket = blockedRouteDeliveryClosurePacket(reason, taskId);
  const sameTaskFieldMaterialPacket = blockedSameTaskFieldMaterialPacket(reason, taskId);
  const currentFieldEvidenceMaterial = blockedCurrentFieldEvidenceMaterial(reason, taskId);
  const sameTaskRouteExecutionMaterialPacket = blockedSameTaskRouteExecutionMaterialPacket(reason, taskId);
  const sameTaskMissionEvidenceGate = blockedSameTaskMissionEvidenceGate(reason, taskId);
  const sameTaskMissionMaterialChecklist = blockedSameTaskMissionMaterialChecklist(
    reason,
    taskId,
    sameTaskMissionEvidenceGate,
  );
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
      source_origin: "not_loaded",
      task_origin: "not_loaded",
      manifest_run_id: "not_loaded",
      artifact_root: "",
      artifact_health_summary: "not_loaded",
      present_artifacts: [],
      missing_artifacts: [],
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
    artifact_media_preflight: blockedArtifactMediaPreflight(reason, taskId),
    artifact_access_probe: artifactAccessProbe,
    offline_artifact_seed_smoke: offlineArtifactSeedSmoke,
    route_bag_evidence: routeBagEvidence,
    route_bag_payload_replay: blockedRouteBagPayloadReplay(reason, taskId),
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_root_seed_gate: routeRootSeedGate,
    field_motion_evidence_packet: fieldMotionEvidencePacket,
    nav2_goal_execution_evidence: nav2GoalExecutionEvidence,
    delivery_result_evidence: deliveryResultEvidence,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    current_field_evidence_material: currentFieldEvidenceMaterial,
    localization_path_material_readback: blockedLocalizationPathMaterialReadback(reason, taskId),
    clean_baseline_nav2_path_material: blockedCleanBaselineNav2PathMaterial(reason, taskId),
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(reason, taskId),
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_bundle: buildArtifactBundleSummary(null, taskId),
    artifact_bundle_consumer_ingest: buildArtifactBundleConsumerIngestSummary(
      null,
      buildArtifactBundleSummary(null, taskId),
      blockedArtifactMediaPreflight(reason, taskId),
      taskId,
    ),
    artifact_bundle_readiness: blockedArtifactBundleReadiness(
      reason,
      taskId,
      artifactAccessProbe,
      offlineArtifactSeedSmoke,
      routeRootSeedGate,
      routeBagEvidence,
      blockedRouteBagPayloadReplay(reason, taskId),
      routeBagSemanticReplay,
      routeBagFullSemanticDecodeMatrix,
      routeBagPoseProgressReplay,
      fieldMotionEvidencePacket,
      nav2GoalExecutionEvidence,
      deliveryResultEvidence,
      routeExecutionResultDeliveryReadiness,
      routeDeliveryClosurePacket,
      sameTaskFieldMaterialPacket,
      blockedLocalizationPathMaterialReadback(reason, taskId),
      sameTaskRouteExecutionMaterialPacket,
      sameTaskMissionEvidenceGate,
      blockedFieldOperatorConfirmationMaterial(reason, taskId),
      sameTaskMissionMaterialChecklist,
    ),
    route_replay_mvp: blockedRouteReplayMvp(reason, taskId),
    labeling_mvp: blockedLabelingMvp(reason, taskId),
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
  const fieldEvidence = asRecord(record?.field_evidence);
  // 任务卡片只映射 O7 文档已经确认的字段，不把其余 payload 当成 UI 事实。
  return {
    task_id: asString(record?.task_id, "unknown_task"),
    robot_id: asString(record?.robot_id, "unknown_robot"),
    task_origin: asString(record?.task_origin ?? fieldEvidence?.task_origin, "not_proven"),
    field_evidence_source: asString(
      record?.field_evidence_source ?? fieldEvidence?.source_contract ?? fieldEvidence?.source,
      "not_loaded",
    ),
    field_evidence_artifact_status: normalizeManifestArtifactStatus(
      record?.field_evidence_artifact_status ?? fieldEvidence?.artifact_status,
    ),
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

function firstObjectArray(...values: unknown[]): JsonRecord[] {
  // O6 detail 与 PC fixture 的数组字段名字可能不同；只取第一组可用 object 数组，避免跨来源拼接假事实。
  for (const value of values) {
    const records = sampleObjectArray(value, Number.MAX_SAFE_INTEGER);
    if (records.length > 0) {
      return records;
    }
  }
  return [];
}

function uniqueRefs(values: Array<string | null | undefined>, limit = MVP_REF_SAMPLE_LIMIT): string[] {
  // 证据引用只保留非空 basename/token，并去重限量，避免 UI 成为完整 archive 导出面。
  return [...new Set(values.map((value) => safePathToken(value ?? "")).filter(Boolean))].slice(0, limit);
}

function uniqueStrings(values: Array<string | null | undefined>, limit = MVP_REF_SAMPLE_LIMIT): string[] {
  // 纯文本样本也要去重截断，避免把完整 sha256 列表或噪声原因直接铺到页面。
  return [...new Set(values.map((value) => asString(value, "").trim()).filter(Boolean))].slice(0, limit);
}

function blockedMediaDependency(reason: string): O7ConsumerArtifactMediaDependency {
  // route replay / labeling 都复用同一套媒体缺口 contract，避免某个 panel 自行推断媒体可访问。
  return {
    status: "blocked_not_proven",
    route_ref: "blocked_not_proven",
    replay_ref: "blocked_not_proven",
    keyframe_ref: "blocked_not_proven",
    sample_refs: [],
    review_item_media_refs: [],
    blocked_reasons: [reason],
    next_required_evidence: [
      "media_manifest_with_safe_refs_only",
      "real_keyframe_media_access_probe_without_credentials",
      "real_review_item_media_capture_for_selected_task",
    ],
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
  };
}

function blockedArtifactMediaPreflight(reason: string, taskId: string): O7ConsumerArtifactMediaPreflight {
  // preflight 缺失时也要显式返回 route replay / labeling 的媒体依赖缺口，不能让 UI 自己拼。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    task_id: taskId || "not_provided",
    consumer_section_names: [...O6_MEDIA_PREFLIGHT_SECTION_NAMES],
    counts: {
      route_ref_count: 0,
      replay_ref_count: 0,
      keyframe_ref_count: 0,
      sample_ref_count: 0,
      review_item_media_ref_count: 0,
    },
    route_replay_dependency: blockedMediaDependency(reason),
    labeling_dependency: blockedMediaDependency(reason),
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      real_media_read_executed: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    blocked_reasons: [reason],
    next_required_evidence: [
      "artifact_media_preflight_contract_from_o6_consumer_detail",
      "real_keyframe_media_access_probe_without_credentials",
      "real_review_item_media_capture_for_selected_task",
    ],
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
  };
}

type ArtifactBundleSourceOrigin =
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence"
  | "remote_field_evidence_consumer_ingest"
  | "local_manifest_fallback"
  | "not_loaded";

interface ArtifactBundleSourceResult {
  payload: JsonRecord;
  source_origin: ArtifactBundleSourceOrigin;
  source_path: string;
}

type ArtifactAccessProbeSourceOrigin =
  | "remote_artifact_access_probe"
  | "remote_field_evidence"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "not_loaded";

interface ArtifactAccessProbeSourceResult {
  payload: JsonRecord;
  source_origin: ArtifactAccessProbeSourceOrigin;
  source_path: string;
}

type OfflineArtifactSeedSmokeSourceOrigin =
  | "remote_offline_artifact_seed_smoke"
  | "remote_field_evidence"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "not_loaded";

interface OfflineArtifactSeedSmokeSourceResult {
  payload: JsonRecord;
  source_origin: OfflineArtifactSeedSmokeSourceOrigin;
  source_path: string;
}

type RouteRootSeedGateSourceOrigin =
  | "remote_route_root_seed_gate"
  | "remote_field_evidence"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "not_loaded";

interface RouteRootSeedGateSourceResult {
  payload: JsonRecord;
  source_origin: RouteRootSeedGateSourceOrigin;
  source_path: string;
}

type RouteBagEvidenceSourceOrigin =
  | "remote_route_bag_evidence"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteBagEvidenceSourceResult {
  payload: JsonRecord;
  source_origin: RouteBagEvidenceSourceOrigin;
  source_path: string;
}

type RouteBagPayloadReplaySourceOrigin =
  | "remote_route_bag_payload_replay"
  | "remote_route_bag_evidence"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteBagPayloadReplaySourceResult {
  payload: JsonRecord;
  source_origin: RouteBagPayloadReplaySourceOrigin;
  source_path: string;
}

type RouteBagSemanticReplaySourceOrigin =
  | "remote_route_bag_semantic_replay"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteBagSemanticReplaySourceResult {
  payload: JsonRecord;
  source_origin: RouteBagSemanticReplaySourceOrigin;
  source_path: string;
}

type RouteBagFullSemanticDecodeMatrixSourceOrigin =
  | "remote_route_bag_full_semantic_decode_matrix"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteBagFullSemanticDecodeMatrixSourceResult {
  payload: JsonRecord;
  source_origin: RouteBagFullSemanticDecodeMatrixSourceOrigin;
  source_path: string;
}

type FieldMotionEvidencePacketSourceOrigin =
  | "remote_field_motion_evidence_packet"
  | "remote_field_evidence"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface FieldMotionEvidencePacketSourceResult {
  payload: JsonRecord;
  source_origin: FieldMotionEvidencePacketSourceOrigin;
  source_path: string;
}

type Nav2GoalExecutionEvidenceSourceOrigin =
  | "remote_nav2_goal_execution_evidence"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface Nav2GoalExecutionEvidenceSourceResult {
  payload: JsonRecord;
  source_origin: Nav2GoalExecutionEvidenceSourceOrigin;
  source_path: string;
}

type DeliveryResultEvidenceSourceOrigin =
  | "remote_delivery_result_evidence"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface DeliveryResultEvidenceSourceResult {
  payload: JsonRecord;
  source_origin: DeliveryResultEvidenceSourceOrigin;
  source_path: string;
}

type RouteExecutionResultDeliveryReadinessSourceOrigin =
  | "remote_route_execution_result_delivery_readiness"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteExecutionResultDeliveryReadinessSourceResult {
  payload: JsonRecord;
  source_origin: RouteExecutionResultDeliveryReadinessSourceOrigin;
  source_path: string;
}

type RouteDeliveryClosurePacketSourceOrigin =
  | "remote_route_delivery_closure_packet"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface RouteDeliveryClosurePacketSourceResult {
  payload: JsonRecord;
  source_origin: RouteDeliveryClosurePacketSourceOrigin;
  source_path: string;
}

type SameTaskFieldMaterialPacketSourceOrigin =
  | "remote_same_task_field_material_packet"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface SameTaskFieldMaterialPacketSourceResult {
  payload: JsonRecord;
  source_origin: SameTaskFieldMaterialPacketSourceOrigin;
  source_path: string;
}

type CurrentFieldEvidenceMaterialSourceOrigin =
  | "remote_current_field_evidence_material"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface CurrentFieldEvidenceMaterialSourceResult {
  payload: JsonRecord;
  source_origin: CurrentFieldEvidenceMaterialSourceOrigin;
  source_path: string;
}

type CleanBaselineNav2PathMaterialSourceOrigin =
  | "remote_clean_baseline_nav2_path_material"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface CleanBaselineNav2PathMaterialSourceResult {
  payload: JsonRecord;
  source_origin: CleanBaselineNav2PathMaterialSourceOrigin;
  source_path: string;
}

type LocalizationPathMaterialReadbackSourceOrigin =
  | "remote_localization_path_material_readback"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface LocalizationPathMaterialReadbackSourceResult {
  payload: JsonRecord;
  source_origin: LocalizationPathMaterialReadbackSourceOrigin;
  source_path: string;
}

type SameTaskRouteExecutionMaterialPacketSourceOrigin =
  | "remote_same_task_route_execution_material_packet"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface SameTaskRouteExecutionMaterialPacketSourceResult {
  payload: JsonRecord;
  source_origin: SameTaskRouteExecutionMaterialPacketSourceOrigin;
  source_path: string;
}

type SameTaskMissionEvidenceGateSourceOrigin =
  | "remote_same_task_mission_evidence_gate"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface SameTaskMissionEvidenceGateSourceResult {
  payload: JsonRecord;
  source_origin: SameTaskMissionEvidenceGateSourceOrigin;
  source_path: string;
}

type FieldOperatorConfirmationMaterialSourceOrigin =
  | "remote_field_operator_confirmation_material"
  | "remote_field_evidence"
  | "remote_field_motion_evidence_packet"
  | "remote_artifact_bundle"
  | "remote_artifact_bundle_consumer_ingest"
  | "remote_field_evidence_consumer_ingest"
  | "remote_artifact_bundle_readiness"
  | "not_loaded";

interface FieldOperatorConfirmationMaterialSourceResult {
  payload: JsonRecord;
  source_origin: FieldOperatorConfirmationMaterialSourceOrigin;
  source_path: string;
}

function nestedRecord(root: JsonRecord | null, ...keys: string[]): JsonRecord | null {
  // 这里只做有限层级的安全下钻，避免把任意深层结构当成可消费来源。
  let current: JsonRecord | null = root;
  for (const key of keys) {
    current = asRecord(current?.[key]);
    if (!current) {
      return null;
    }
  }
  return current;
}

function artifactAccessProbeCandidateFromRemote(remote: JsonRecord): ArtifactAccessProbeSourceResult | null {
  // probe 可以由 O6 detail 顶层或同一 task 的 field/bundle/ingest wrapper 暴露，但只按白名单路径读取。
  const direct = asRecord(remote.artifact_access_probe);
  if (direct) {
    return { payload: direct, source_origin: "remote_artifact_access_probe", source_path: "artifact_access_probe" };
  }
  const fieldEvidenceProbe =
    nestedRecord(remote, "field_evidence", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence_manifest", "artifact_access_probe");
  if (fieldEvidenceProbe) {
    return { payload: fieldEvidenceProbe, source_origin: "remote_field_evidence", source_path: "field_evidence.artifact_access_probe" };
  }
  const bundleProbe =
    nestedRecord(remote, "artifact_bundle", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "artifact_access_probe");
  if (bundleProbe) {
    return { payload: bundleProbe, source_origin: "remote_artifact_bundle", source_path: "artifact_bundle.artifact_access_probe" };
  }
  const ingestProbe =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_access_probe") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "artifact_access_probe");
  if (ingestProbe) {
    return {
      payload: ingestProbe,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.artifact_access_probe",
    };
  }
  const fieldIngestProbe =
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "artifact_access_probe") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "artifact_access_probe");
  if (fieldIngestProbe) {
    return {
      payload: fieldIngestProbe,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.artifact_access_probe",
    };
  }
  return null;
}

function unsafeArtifactAccessRefReason(value: unknown): string {
  // probe ref 在安全检查前保留原始字符串；通过后才降成 basename，避免路径/URL 先被洗白。
  const text = rawString(value);
  if (!text) {
    return "artifact_access_probe_empty_ref";
  }
  const lowered = text.toLowerCase();
  const normalizedParts = text.replace(/\\/g, "/").split("/");
  if (
    lowered.includes("://") ||
    text.includes("?") ||
    text.includes("#") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("credential") ||
    lowered.includes("secret") ||
    lowered.includes("password") ||
    lowered.startsWith("data:") ||
    lowered.includes("base64") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("\\") ||
    normalizedParts.includes("..")
  ) {
    return "artifact_access_probe_unsafe_ref";
  }
  return "";
}

function safeArtifactAccessRef(value: unknown): string {
  // UI 只看 basename/token，不能看到 O6 allowlist root、目录层级或真实本机路径。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  return path.basename(text.replace(/\\/g, "/")).slice(0, 160);
}

function safeArtifactAccessReason(value: unknown, fallback: string): string {
  // blocked reason 可能来自文件系统异常；出现路径形态时统一脱敏，保留枚举语义但不泄露路径。
  const text = asString(value, fallback);
  if (text.includes("/") || text.includes("\\") || text.toLowerCase().includes("allowlist_root")) {
    return "artifact_access_probe_blocked_redacted_path";
  }
  return text;
}

function sha256Prefix(value: unknown): string {
  // sha256 只显示短摘要，足够人工核对样本，同时避免把完整 digest 当成对象 ID 扩散。
  const text = typeof value === "string" ? value.trim() : "";
  return /^[a-fA-F0-9]{12,64}$/.test(text) ? text.slice(0, 12).toLowerCase() : "";
}

function blockedArtifactAccessProbe(reason: string, taskId: string): O7ConsumerArtifactAccessProbeSummary {
  // 缺失或被拒绝的 probe 也返回完整 contract，避免 UI 从 undefined 推断成“无需访问证明”。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    task_id: taskId || "not_provided",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    proof_scope: "not_loaded",
    allowlist_root_configured: false,
    allowlist_root_echoed: false,
    max_file_size_bytes: null,
    counts: {
      requested_ref_count: 0,
      readable_ref_count: 0,
      blocked_ref_count: 0,
      missing_ref_count: 0,
    },
    sample_probes: [],
    sample_refs: [],
    sample_sha256_prefixes: [],
    blocked_reasons: [reason],
    next_required_evidence: ["real_or_offline_artifact_access_probe_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      file_read_attempted: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
}

function offlineArtifactSeedSmokeCandidateFromRemote(remote: JsonRecord): OfflineArtifactSeedSmokeSourceResult | null {
  // offline seed smoke 可以从顶层、field_evidence 或 bundle/ingest wrapper 里下钻，但只走白名单路径。
  const readinessSmoke =
    nestedRecord(remote, "artifact_bundle_readiness", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_evidence", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "offline_artifact_seed_smoke");
  if (readinessSmoke) {
    return {
      payload: readinessSmoke,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle_readiness.offline_artifact_seed_smoke",
    };
  }
  const fieldEvidenceSmoke =
    nestedRecord(remote, "field_evidence", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence_manifest", "offline_artifact_seed_smoke");
  if (fieldEvidenceSmoke) {
    return {
      payload: fieldEvidenceSmoke,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.offline_artifact_seed_smoke",
    };
  }
  const bundleSmoke =
    nestedRecord(remote, "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "offline_artifact_seed_smoke");
  if (bundleSmoke) {
    return {
      payload: bundleSmoke,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.offline_artifact_seed_smoke",
    };
  }
  const ingestSmoke =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "offline_artifact_seed_smoke");
  if (ingestSmoke) {
    return {
      payload: ingestSmoke,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.offline_artifact_seed_smoke",
    };
  }
  const fieldIngestSmoke =
    nestedRecord(remote, "field_evidence_consumer_ingest", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence_ingest", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "offline_artifact_seed_smoke") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "offline_artifact_seed_smoke");
  if (fieldIngestSmoke) {
    return {
      payload: fieldIngestSmoke,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.offline_artifact_seed_smoke",
    };
  }
  const direct = asRecord(remote.offline_artifact_seed_smoke);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_offline_artifact_seed_smoke",
      source_path: "offline_artifact_seed_smoke",
    };
  }
  return null;
}

function blockedOfflineArtifactSeedSmoke(reason: string, taskId: string): O7ConsumerOfflineArtifactSeedSmokeSummary {
  // 缺失时也返回完整 summary，避免 UI 用缺字段推断出“数据准备完成”。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    task_id: taskId || "not_provided",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    proof_scope: "not_loaded",
    allowlist_root_echoed: false,
    counts: {
      route_ref_count: 0,
      replay_ref_count: 0,
      keyframe_ref_count: 0,
      evidence_ref_count: 0,
      sample_ref_count: 0,
      readable_ref_count: 0,
      blocked_ref_count: 0,
      missing_ref_count: 0,
    },
    sample_probes: [],
    sample_refs: [],
    sample_sha256_prefixes: [],
    blocked_reasons: [reason],
    next_required_evidence: ["real_or_offline_artifact_seed_smoke_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      file_read_attempted: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function offlineArtifactSeedSmokeHardFailReason(summary: O7ConsumerOfflineArtifactSeedSmokeSummary): string {
  // 这条摘要如果已经触发 schema mismatch / dangerous true / unsafe ref / allowlist 回显，就必须让 detail 直接 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(offline_artifact_seed_smoke_schema_mismatch|offline_artifact_seed_smoke_dangerous_true|offline_artifact_seed_smoke_unsafe_ref|offline_artifact_seed_smoke_allowlist_root_echoed)/.test(
    reason,
  )
    ? reason
    : "";
}

function routeRootSeedGateCandidateFromRemote(remote: JsonRecord): RouteRootSeedGateSourceResult | null {
  // route-root seed gate 只从 O6 consumer detail 的白名单摘要位置读取，不接受任意本地路径参数。
  const direct = asRecord(remote.route_root_seed_gate);
  if (direct) {
    return { payload: direct, source_origin: "remote_route_root_seed_gate", source_path: "route_root_seed_gate" };
  }
  const fieldEvidenceGate =
    nestedRecord(remote, "field_evidence", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence_manifest", "route_root_seed_gate");
  if (fieldEvidenceGate) {
    return { payload: fieldEvidenceGate, source_origin: "remote_field_evidence", source_path: "field_evidence.route_root_seed_gate" };
  }
  const bundleGate =
    nestedRecord(remote, "artifact_bundle", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_root_seed_gate");
  if (bundleGate) {
    return { payload: bundleGate, source_origin: "remote_artifact_bundle", source_path: "artifact_bundle.route_root_seed_gate" };
  }
  const ingestGate =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_root_seed_gate") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_root_seed_gate");
  if (ingestGate) {
    return {
      payload: ingestGate,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_root_seed_gate",
    };
  }
  const fieldIngestGate =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence_ingest", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_root_seed_gate") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_root_seed_gate");
  if (fieldIngestGate) {
    return {
      payload: fieldIngestGate,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_root_seed_gate",
    };
  }
  return null;
}

function unsafeRouteRootSeedTextReason(value: unknown): string {
  // blocked/next evidence 文本也不能携带 URL、token、base64 或控制面字段。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token=") ||
    lowered.includes("access_key") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.startsWith("data:") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty")
  ) {
    return "route_root_seed_gate_unsafe_text";
  }
  return "";
}

function routeRootTextList(value: unknown, limit = 12): string[] {
  // O6 文本列表只作为 operator 提示；先做危险文本过滤，再裁剪长度。
  return Array.isArray(value) ? value.map((item) => asString(item, "blocked_not_proven")).slice(0, limit) : [];
}

function routeRootRawRefs(payload: JsonRecord, routeCsvSummary: JsonRecord, manifestSummary: JsonRecord, derivedReplaySummary: JsonRecord, evidenceRefSummary: JsonRecord): string[] {
  // route-root 摘要中的 ref 可能散落在四个 summary 或 refs wrapper 中，统一先按原始字符串扫描。
  const refs = asRecord(payload.refs);
  return [
    rawString(routeCsvSummary.ref),
    rawString(routeCsvSummary.route_ref),
    rawString(routeCsvSummary.route_csv_ref),
    rawString(routeCsvSummary.path),
    rawString(manifestSummary.ref),
    rawString(manifestSummary.manifest_ref),
    rawString(manifestSummary.source_ref),
    rawString(manifestSummary.path),
    rawString(derivedReplaySummary.ref),
    rawString(derivedReplaySummary.replay_ref),
    rawString(derivedReplaySummary.output_ref),
    rawString(derivedReplaySummary.path),
    rawString(evidenceRefSummary.keyframe_ref),
    rawString(evidenceRefSummary.evidence_ref),
    ...rawStringList(evidenceRefSummary.keyframe_refs),
    ...rawStringList(evidenceRefSummary.evidence_refs),
    ...rawStringList(evidenceRefSummary.sample_refs),
    ...rawStringList(payload.sample_refs),
    ...rawStringList(refs?.route_refs),
    ...rawStringList(refs?.manifest_refs),
    ...rawStringList(refs?.replay_refs),
    ...rawStringList(refs?.keyframe_refs),
    ...rawStringList(refs?.evidence_refs),
    ...rawStringList(refs?.sample_refs),
  ].filter(Boolean);
}

function blockedRouteRootSeedGate(reason: string, taskId: string): O7ConsumerRouteRootSeedGateSummary {
  // 缺失或被拒绝时也返回完整 route-root gate，避免 UI 用 undefined 推断成 readiness 已通过。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    schema_version: null,
    task_id: taskId || "not_provided",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    proof_scope: "not_loaded",
    route_root_seed_status: "blocked_not_proven",
    route_bag_required: false,
    route_bag_present: false,
    counts: {
      route_frame_count: 0,
      derived_replay_frame_count: 0,
      route_ref_count: 0,
      manifest_ref_count: 0,
      replay_ref_count: 0,
      keyframe_ref_count: 0,
      evidence_ref_count: 0,
      sample_ref_count: 0,
    },
    sample_refs: [],
    blocked_reasons: [reason],
    next_required_evidence: ["route_root_seed_gate_summary_from_o6_consumer_detail"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_required: false,
      route_bag_present: false,
      real_route_bag_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeRootSeedGateHardFailReason(summary: O7ConsumerRouteRootSeedGateSummary): string {
  // route-root gate 的坏 schema、缺必填字段、危险 true 或不安全 ref 都要让 detail 主路径 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_root_seed_gate_schema_mismatch|route_root_seed_gate_missing_required_fields|route_root_seed_gate_dangerous_true|route_root_seed_gate_unsafe_ref|route_root_seed_gate_unsafe_text|route_root_seed_gate_route_bag_required_true|route_root_seed_gate_route_bag_present_true|route_root_seed_gate_allowlist_root_echoed)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildRouteRootSeedGateSummary(
  candidate: RouteRootSeedGateSourceResult | null,
  taskId: string,
): O7ConsumerRouteRootSeedGateSummary {
  // O7 只消费 O6 已脱敏的 route-root seed 摘要；本函数不读 route root，也不接受绝对路径回显。
  if (!candidate) {
    return blockedRouteRootSeedGate("route_root_seed_gate_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== O6_ROUTE_ROOT_SEED_GATE_SCHEMA) {
    return blockedRouteRootSeedGate("route_root_seed_gate_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteRootSeedGate(`route_root_seed_gate_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  if (asBoolean(payload.allowlist_root_echoed)) {
    return blockedRouteRootSeedGate("route_root_seed_gate_allowlist_root_echoed", taskId);
  }

  const counts = asRecord(payload.counts);
  const routeCsvSummary = asRecord(payload.route_csv_summary);
  const manifestSummary = asRecord(payload.manifest_summary);
  const derivedReplaySummary = asRecord(payload.derived_replay_summary);
  const evidenceRefSummary = asRecord(payload.evidence_ref_summary);
  const missingFields = [
    asNumber(payload.schema_version) === null ? "schema_version" : "",
    rawString(payload.route_root_seed_status).trim() ? "" : "route_root_seed_status",
    typeof payload.route_bag_required === "boolean" ? "" : "route_bag_required",
    typeof payload.route_bag_present === "boolean" ? "" : "route_bag_present",
    routeCsvSummary ? "" : "route_csv_summary",
    manifestSummary ? "" : "manifest_summary",
    derivedReplaySummary ? "" : "derived_replay_summary",
    evidenceRefSummary ? "" : "evidence_ref_summary",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0 || !routeCsvSummary || !manifestSummary || !derivedReplaySummary || !evidenceRefSummary) {
    return blockedRouteRootSeedGate(`route_root_seed_gate_missing_required_fields:${missingFields.join(",")}`, taskId);
  }
  if (payload.route_bag_required !== false) {
    return blockedRouteRootSeedGate("route_root_seed_gate_route_bag_required_true", taskId);
  }
  if (payload.route_bag_present !== false) {
    return blockedRouteRootSeedGate("route_root_seed_gate_route_bag_present_true", taskId);
  }

  const routeFrameCount = asNumber(routeCsvSummary.frame_count ?? routeCsvSummary.row_count ?? counts?.route_frame_count);
  const derivedReplayFrameCount = asNumber(
    derivedReplaySummary.frame_count ?? counts?.derived_replay_frame_count ?? counts?.replay_frame_count,
  );
  const manifestRefCount = asNumber(manifestSummary.ref_count ?? manifestSummary.artifact_count ?? counts?.manifest_ref_count);
  const evidenceRefCount = asNumber(evidenceRefSummary.evidence_ref_count ?? counts?.evidence_ref_count);
  const countMissingFields = [
    routeFrameCount === null ? "route_csv_summary.frame_count" : "",
    derivedReplayFrameCount === null ? "derived_replay_summary.frame_count" : "",
    manifestRefCount === null ? "manifest_summary.ref_count" : "",
    evidenceRefCount === null ? "evidence_ref_summary.evidence_ref_count" : "",
  ].filter(Boolean);
  if (countMissingFields.length > 0) {
    return blockedRouteRootSeedGate(`route_root_seed_gate_missing_required_fields:${countMissingFields.join(",")}`, taskId);
  }

  const rawRefs = routeRootRawRefs(payload, routeCsvSummary, manifestSummary, derivedReplaySummary, evidenceRefSummary);
  if (rawRefs.map((ref) => unsafeArtifactAccessRefReason(ref)).some(Boolean)) {
    return blockedRouteRootSeedGate("route_root_seed_gate_unsafe_ref", taskId);
  }
  const blockedReasons = routeRootTextList(payload.blocked_reasons);
  const nextRequiredEvidence = routeRootTextList(payload.next_required_evidence);
  if ([...blockedReasons, ...nextRequiredEvidence].map(unsafeRouteRootSeedTextReason).some(Boolean)) {
    return blockedRouteRootSeedGate("route_root_seed_gate_unsafe_text", taskId);
  }

  const sampleRefs = uniqueRefs(rawRefs.map((ref) => safeArtifactAccessRef(ref)));
  const routeRefCount = asNumber(counts?.route_ref_count ?? routeCsvSummary.ref_count) ?? (sampleRefs.length ? 1 : 0);
  const replayRefCount = asNumber(counts?.replay_ref_count ?? derivedReplaySummary.ref_count) ?? (sampleRefs.length ? 1 : 0);
  const keyframeRefCount = asNumber(counts?.keyframe_ref_count ?? evidenceRefSummary.keyframe_ref_count) ?? 0;
  const sampleRefCount = asNumber(counts?.sample_ref_count) ?? sampleRefs.length;
  const proofBoundary = asRecord(payload.proof_boundary);
  const routeRootSeedStatus = asString(payload.route_root_seed_status, "blocked_not_proven");
  const status = /ready|gated|available/i.test(routeRootSeedStatus)
    ? "local_mock_route_root_seed_ready"
    : "derived_blocked_not_proven";
  return {
    schema: O6_ROUTE_ROOT_SEED_GATE_SCHEMA,
    status,
    schema_version: asNumber(payload.schema_version),
    task_id: asString(payload.task_id, taskId || "not_provided"),
    source_contract: O6_ROUTE_ROOT_SEED_GATE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    proof_scope: asString(payload.proof_scope, "software_proof_route_root_seed_gate_only"),
    route_root_seed_status: routeRootSeedStatus,
    route_bag_required: false,
    route_bag_present: false,
    counts: {
      route_frame_count: routeFrameCount ?? 0,
      derived_replay_frame_count: derivedReplayFrameCount ?? 0,
      route_ref_count: routeRefCount,
      manifest_ref_count: manifestRefCount ?? 0,
      replay_ref_count: replayRefCount,
      keyframe_ref_count: keyframeRefCount,
      evidence_ref_count: evidenceRefCount ?? 0,
      sample_ref_count: sampleRefCount,
    },
    sample_refs: sampleRefs,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      payload.route_bag_present === false ? "route_bag_missing_optional" : "",
      "local_mock_only",
      "not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["route_root_seed_gate_summary_from_o6_consumer_detail", "route_bag_optional_for_enhanced_route_replay"],
    proof_boundary: {
      local_mock: asBoolean(proofBoundary?.local_mock) || true,
      not_proven: true,
      reads_local_path: false,
      route_bag_required: false,
      route_bag_present: false,
      real_route_bag_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeBagEvidenceCandidateFromRemote(remote: JsonRecord): RouteBagEvidenceSourceResult | null {
  // route bag evidence 只能来自 O6 已归一 wrapper；O7 不读取 DB3、metadata 或本地路径。
  const direct = asRecord(remote.route_bag_evidence);
  if (direct) {
    return { payload: direct, source_origin: "remote_route_bag_evidence", source_path: "route_bag_evidence" };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_manifest", "route_bag_evidence");
  if (fieldEvidence) {
    return { payload: fieldEvidence, source_origin: "remote_field_evidence", source_path: "field_evidence.route_bag_evidence" };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_bag_evidence");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_bag_evidence",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_motion_evidence_packet", "route_bag_evidence");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_bag_evidence",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_evidence");
  if (bundle) {
    return { payload: bundle, source_origin: "remote_artifact_bundle", source_path: "artifact_bundle.route_bag_evidence" };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_evidence");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_bag_evidence",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_bag_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_bag_evidence");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_bag_evidence",
    };
  }
  return null;
}

function routeBagPayloadReplayCandidateFromRemote(remote: JsonRecord): RouteBagPayloadReplaySourceResult | null {
  // payload replay 只从 O6 已归一 wrapper 读取，不读取 DB3、本地路径或原始 payload。
  const direct = asRecord(remote.route_bag_payload_replay);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_bag_payload_replay",
      source_path: "route_bag_payload_replay",
    };
  }
  const routeBagPayloadReplay = asRecord(remote.route_bag_evidence)?.route_bag_payload_replay;
  if (routeBagPayloadReplay && typeof routeBagPayloadReplay === "object") {
    return {
      payload: routeBagPayloadReplay as JsonRecord,
      source_origin: "remote_route_bag_evidence",
      source_path: "route_bag_evidence.route_bag_payload_replay",
    };
  }
  const wrappedRouteBagPayloadReplay =
    nestedRecord(remote, "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_evidence", "route_bag_payload_replay");
  if (wrappedRouteBagPayloadReplay) {
    return {
      payload: wrappedRouteBagPayloadReplay,
      source_origin: "remote_route_bag_evidence",
      source_path: "route_bag_evidence.route_bag_payload_replay",
    };
  }
  const ingestPayload =
    asRecord(remote.field_evidence_consumer_ingest)?.route_bag_payload_replay ??
    asRecord(remote.field_evidence_ingest)?.route_bag_payload_replay ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_bag_payload_replay");
  if (ingestPayload) {
    return {
      payload: ingestPayload as JsonRecord,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_bag_payload_replay",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_manifest", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "route_bag_payload_replay");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.route_bag_payload_replay",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_bag_payload_replay");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_bag_payload_replay",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_payload_replay");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_bag_payload_replay",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_payload_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_payload_replay");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_bag_payload_replay",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_bag_payload_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_bag_payload_replay");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_bag_payload_replay",
    };
  }
  return null;
}

function routeBagSemanticReplayCandidateFromRemote(remote: JsonRecord): RouteBagSemanticReplaySourceResult | null {
  // semantic replay 只从 O6 已归一 wrapper 读取，不读取原始 payload、DB3 文件路径或任意深层对象。
  const direct = asRecord(remote.route_bag_semantic_replay);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_bag_semantic_replay",
      source_path: "route_bag_semantic_replay",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence_manifest", "route_bag_semantic_replay");
  if (fieldEvidence) {
    return { payload: fieldEvidence, source_origin: "remote_field_evidence", source_path: "field_evidence.route_bag_semantic_replay" };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_bag_semantic_replay");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_bag_semantic_replay",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_semantic_replay");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_bag_semantic_replay",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_semantic_replay");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_bag_semantic_replay",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_bag_semantic_replay") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_bag_semantic_replay");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_bag_semantic_replay",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_bag_semantic_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_bag_semantic_replay");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_bag_semantic_replay",
    };
  }
  return null;
}

function routeBagFullSemanticDecodeMatrixCandidateFromRemote(
  remote: JsonRecord,
): RouteBagFullSemanticDecodeMatrixSourceResult | null {
  // full semantic matrix 只读取 O6/Algorithm 已脱敏 summary，不读取 DB3、raw payload 或任意本地路径。
  const direct = asRecord(remote.route_bag_full_semantic_decode_matrix);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_bag_full_semantic_decode_matrix",
      source_path: "route_bag_full_semantic_decode_matrix",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence_manifest", "route_bag_full_semantic_decode_matrix");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.route_bag_full_semantic_decode_matrix",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_bag_full_semantic_decode_matrix");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_bag_full_semantic_decode_matrix",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_full_semantic_decode_matrix");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_bag_full_semantic_decode_matrix",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(
      remote,
      "artifact_bundle_consumer_ingest",
      "artifact_bundle",
      "field_motion_evidence_packet",
      "route_bag_full_semantic_decode_matrix",
    ) ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(
      remote,
      "field_evidence",
      "artifact_bundle_consumer_ingest",
      "artifact_bundle",
      "route_bag_full_semantic_decode_matrix",
    );
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_bag_full_semantic_decode_matrix",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence_ingest", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_bag_full_semantic_decode_matrix");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_bag_full_semantic_decode_matrix",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_bag_full_semantic_decode_matrix") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_bag_full_semantic_decode_matrix");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_bag_full_semantic_decode_matrix",
    };
  }
  return null;
}

type RouteBagPoseProgressReplaySourceResult = {
  payload: JsonRecord;
  source_origin:
    | "remote_route_bag_pose_progress_replay"
    | "remote_field_evidence"
    | "remote_field_motion_evidence_packet"
    | "remote_artifact_bundle"
    | "remote_artifact_bundle_consumer_ingest"
    | "remote_artifact_bundle_readiness";
  source_path: string;
};

function routeBagPoseProgressReplayCandidateFromRemote(remote: JsonRecord): RouteBagPoseProgressReplaySourceResult | null {
  // pose progress replay 只从 O6 已归一 wrapper 读取，不读取原始 payload、DB3 文件路径或任意深层对象。
  const direct = asRecord(remote.route_bag_pose_progress_replay);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_bag_pose_progress_replay",
      source_path: "route_bag_pose_progress_replay",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence_manifest", "route_bag_pose_progress_replay");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.route_bag_pose_progress_replay",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_bag_pose_progress_replay");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_bag_pose_progress_replay",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_bag_pose_progress_replay");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_bag_pose_progress_replay",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_bag_pose_progress_replay");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_bag_pose_progress_replay",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_bag_pose_progress_replay") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_bag_pose_progress_replay");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_bag_pose_progress_replay",
    };
  }
  return null;
}

function routeBagSha256Prefix(value: unknown): string {
  // route bag 只展示短 checksum 前缀，既能人工定位，又不会扩散完整 DB3 digest。
  const text = rawString(value);
  return /^[a-fA-F0-9]{12,64}$/.test(text) ? text.slice(0, 12).toLowerCase() : "";
}

function unsafeRouteBagTextReason(value: unknown, reason = "route_bag_evidence_unsafe_text"): string {
  // 普通说明字段不能带 URL、token、raw/base64、路径、root 或控制话题。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("root=") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return reason;
  }
  return "";
}

function unsafeRouteBagTopicNameReason(
  value: unknown,
  reason = "route_bag_evidence_unsafe_topic_name",
): string {
  // topic name 可以是 /odom 这种 ROS 名称，但不能是控制话题、路径、URL 或携带凭证的文本。
  const text = rawString(value);
  const lowered = text.toLowerCase();
  if (
    !text ||
    text.length > 120 ||
    text.includes("\\") ||
    text.includes("..") ||
    text.includes("?") ||
    text.includes("#") ||
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("/dev/tty") ||
    lowered === "/cmd_vel" ||
    lowered.includes("/cmd_vel/") ||
    lowered.endsWith("/cmd_vel") ||
    lowered.startsWith("data:") ||
    !/^\/?[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(text)
  ) {
    return reason;
  }
  return "";
}

function safeRouteBagLabel(value: unknown, fallback: string): string {
  // source/source_label 只保留 label 或 basename；绝对路径和目录层级不能进入 O7 UI。
  const text = rawString(value) || fallback;
  const unsafe = unsafeRouteBagTextReason(text);
  const lowered = text.toLowerCase();
  const secretLike =
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.startsWith("data:");
  if (unsafe && !secretLike && (text.includes("/") || text.includes("\\") || path.isAbsolute(text))) {
    return path.basename(text.replace(/\\/g, "/")).slice(0, 160) || fallback;
  }
  return unsafe ? "route_bag_source_redacted" : asString(text, fallback);
}

function blockedRouteBagEvidence(reason: string, taskId: string): O7ConsumerRouteBagEvidenceSummary {
  // 缺失或被拒绝时也返回同形摘要，避免 UI 用 undefined 推断 route bag 已经 ready。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    task_id_source: "not_loaded",
    proof_scope: "not_loaded",
    route_bag_source: "not_loaded",
    source_label: "not_loaded",
    metadata_present: false,
    db3_present: false,
    db3_read_ok: false,
    db3_size_bytes: null,
    db3_sha256_prefix: "",
    topic_count: 0,
    message_count: 0,
    timestamp_first_ns: null,
    timestamp_last_ns: null,
    sample_topic_names: [],
    blocked_reasons: [reason],
    next_required_evidence: ["route_bag_evidence_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function blockedRouteBagPayloadReplay(
  reason: string,
  taskId: string,
): O7ConsumerRouteBagPayloadReplaySummary {
  // payload replay 缺失或被拒绝时也返回同形摘要，避免 UI 误判为 ready。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    task_id_source: "not_loaded",
    proof_scope: "not_loaded",
    route_bag_source: "not_loaded",
    source_label: "not_loaded",
    metadata_present: false,
    db3_present: false,
    db3_read_ok: false,
    db3_size_bytes: null,
    db3_sha256_prefix: "",
    topic_count: 0,
    message_count: 0,
    timestamp_first_ns: null,
    timestamp_last_ns: null,
    sample_topic_names: [],
    payload_sample_count: 0,
    payload_size_min_bytes: null,
    payload_size_max_bytes: null,
    payload_size_avg_bytes: null,
    payload_sha256_prefix_samples: [],
    blocked_reasons: [reason],
    next_required_evidence: ["route_bag_payload_replay_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeBagEvidenceHardFailReason(summary: O7ConsumerRouteBagEvidenceSummary): string {
  // route bag 摘要出现坏 schema、危险 true、unsafe topic/text 或 proof_scope mismatch 时必须整体 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_bag_evidence_schema_mismatch|route_bag_evidence_dangerous_true|route_bag_evidence_missing_required_fields|route_bag_evidence_unsafe_text|route_bag_evidence_unsafe_topic_name|route_bag_evidence_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function routeBagPayloadReplayHardFailReason(summary: O7ConsumerRouteBagPayloadReplaySummary): string {
  // payload replay 出现坏 schema、危险 true、unsafe topic/text 或 proof_scope mismatch 时必须整体 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_bag_payload_replay_schema_mismatch|route_bag_payload_replay_dangerous_true|route_bag_payload_replay_missing_required_fields|route_bag_payload_replay_unsafe_text|route_bag_payload_replay_unsafe_topic_name|route_bag_payload_replay_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function unsafeRouteBagSemanticTextReason(
  value: unknown,
  reason = "route_bag_semantic_replay_unsafe_text",
): string {
  // semantic replay 的普通说明字段不能带 URL、token、raw/base64、绝对路径或控制面词汇。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    text.includes("?") ||
    text.includes("#") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("\\") ||
    text.includes("..")
  ) {
    return reason;
  }
  return "";
}

function safeRouteBagSemanticTopicType(value: unknown): string {
  // topic type 允许 ROS 消息类型文本，但不能带控制面、路径或凭证碎片。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("\\") ||
    text.includes("..") ||
    !/^[A-Za-z0-9_]+\/[A-Za-z0-9_]+(?:\/[A-Za-z0-9_]+)*$/.test(text)
  ) {
    return "";
  }
  return text.slice(0, 120);
}

function unsafeRouteBagPoseFrameIdReason(value: unknown): string {
  // 位姿 frame id 只允许短标识符，不允许 URL、路径、token 或控制话题碎片。
  const text = rawString(value);
  if (!text) {
    return "route_bag_pose_progress_replay_unsafe_frame_id";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.startsWith("data:") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    text.includes("?") ||
    text.includes("#") ||
    text.includes("\\") ||
    text.includes("..") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    !/^[A-Za-z0-9_:-]{1,120}$/.test(text)
  ) {
    return "route_bag_pose_progress_replay_unsafe_frame_id";
  }
  return "";
}

function blockedRouteBagSemanticReplay(reason: string, taskId: string): O7ConsumerRouteBagSemanticReplaySummary {
  // semantic replay 缺失或被拒绝时也返回同形摘要，避免 UI 用缺字段误判为已解码。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    semantic_decode_status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    task_id_source: "not_loaded",
    proof_scope: "not_loaded",
    route_bag_source: "not_loaded",
    source_label: "not_loaded",
    metadata_present: false,
    db3_present: false,
    db3_read_ok: false,
    db3_size_bytes: null,
    db3_sha256_prefix: "",
    topic_count: 0,
    message_count: 0,
    timestamp_first_ns: null,
    timestamp_last_ns: null,
    sample_topic_names: [],
    semantic_sample_count: 0,
    semantic_decode_ok_count: 0,
    semantic_decode_failed_count: 0,
    semantic_topic_types: [],
    laser_scan_summary: {
      sample_count: 0,
      range_sample_length: null,
      finite_count: null,
      range_min: null,
      range_max: null,
      angle_min: null,
      angle_max: null,
      angle_increment: null,
    },
    image_summary: {
      sample_count: 0,
      width: null,
      height: null,
      encoding: "not_loaded",
      step: null,
      data_size: null,
    },
    tf_summary: {
      sample_count: 0,
      transform_count: null,
      frame_id_samples: [],
      child_frame_id_samples: [],
    },
    blocked_reasons: [reason],
    next_required_evidence: ["route_bag_semantic_replay_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function blockedRouteBagFullSemanticDecodeMatrix(
  reason: string,
  taskId: string,
): O7ConsumerRouteBagFullSemanticDecodeMatrixSummary {
  // matrix 缺失或被拒绝时仍返回完整 contract，避免 UI 把 undefined 当成“已全量解码”。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    semantic_decode_matrix_status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    task_id_source: "not_loaded",
    proof_scope: "not_loaded",
    route_bag_source: "not_loaded",
    source_label: "not_loaded",
    topic_type_count: 0,
    decoded_topic_type_count: 0,
    unsupported_topic_type_count: 0,
    failed_topic_type_count: 0,
    decoded_message_sample_count: 0,
    unsupported_message_sample_count: 0,
    decode_failed_message_sample_count: 0,
    coverage_ratio: 0,
    sample_topic_type_matrix: [],
    sample_topic_names: [],
    sample_topic_types: [],
    blocked_reasons: [reason],
    next_required_evidence: ["route_bag_full_semantic_decode_matrix_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function blockedRouteBagPoseProgressReplay(
  reason: string,
  taskId: string,
): O7ConsumerRouteBagPoseProgressReplaySummary {
  // pose progress 缺失或被拒绝时也返回同形摘要，避免 UI 把缺字段误判成 live Nav2 proof。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    pose_decode_status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    task_id_source: "not_loaded",
    proof_scope: "not_loaded",
    route_bag_source: "not_loaded",
    source_label: "not_loaded",
    metadata_present: false,
    db3_present: false,
    db3_read_ok: false,
    db3_size_bytes: null,
    db3_sha256_prefix: "",
    topic_count: 0,
    message_count: 0,
    timestamp_first_ns: null,
    timestamp_last_ns: null,
    sample_topic_names: [],
    pose_sample_count: 0,
    pose_decode_ok_count: 0,
    pose_decode_failed_count: 0,
    pose_topic_types: [],
    pose_frame_pairs: [],
    pose_time_span_ns: null,
    start_pose: {
      frame_id: "not_loaded",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      timestamp_ns: null,
    },
    end_pose: {
      frame_id: "not_loaded",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      timestamp_ns: null,
    },
    displacement_m: 0,
    nonzero_pose_progress_observed: false,
    blocked_reasons: [reason],
    next_required_evidence: ["route_bag_pose_progress_replay_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeBagSemanticReplayHardFailReason(summary: O7ConsumerRouteBagSemanticReplaySummary): string {
  // semantic replay 如果已经出现坏 schema、危险 true、unsafe topic/text 或 proof scope mismatch，就必须整体 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_bag_semantic_replay_schema_mismatch|route_bag_semantic_replay_dangerous_true|route_bag_semantic_replay_missing_required_fields|route_bag_semantic_replay_unsafe_text|route_bag_semantic_replay_unsafe_topic_type|route_bag_semantic_replay_proof_scope_mismatch|route_bag_semantic_replay_count_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function routeBagFullSemanticDecodeMatrixHardFailReason(
  summary: O7ConsumerRouteBagFullSemanticDecodeMatrixSummary,
): string {
  // matrix 的坏 schema、危险 true、unsafe topic/text/control topic、坏计数或 proof scope mismatch 必须整体 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_bag_full_semantic_decode_matrix_schema_mismatch|route_bag_full_semantic_decode_matrix_dangerous_true|route_bag_full_semantic_decode_matrix_missing_required_fields|route_bag_full_semantic_decode_matrix_unsafe_text|route_bag_full_semantic_decode_matrix_unsafe_topic|route_bag_full_semantic_decode_matrix_unsafe_topic_type|route_bag_full_semantic_decode_matrix_proof_scope_mismatch|route_bag_full_semantic_decode_matrix_count_mismatch|route_bag_full_semantic_decode_matrix_coverage_ratio_invalid)/.test(
    reason,
  )
    ? reason
    : "";
}

function routeBagPoseProgressReplayHardFailReason(summary: O7ConsumerRouteBagPoseProgressReplaySummary): string {
  // pose progress 如果已经出现坏 schema、危险 true、unsafe frame/topic 或 proof scope mismatch，就必须整体 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_bag_pose_progress_replay_schema_mismatch|route_bag_pose_progress_replay_dangerous_true|route_bag_pose_progress_replay_missing_required_fields|route_bag_pose_progress_replay_unsafe_text|route_bag_pose_progress_replay_unsafe_topic_type|route_bag_pose_progress_replay_unsafe_frame_id|route_bag_pose_progress_replay_proof_scope_mismatch|route_bag_pose_progress_replay_count_mismatch|route_bag_pose_progress_replay_zero_displacement_not_proven)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildRouteBagSemanticReplaySummary(
  candidate: RouteBagSemanticReplaySourceResult | null,
  taskId: string,
): O7ConsumerRouteBagSemanticReplaySummary {
  // O7 只消费白名单 topic type 的语义摘要，不读取 raw payload、完整 hash 或任何控制字段。
  if (!candidate) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA && schema !== O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteBagSemanticReplay(`route_bag_semantic_replay_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_proof_scope_mismatch", taskId);
  }

  const db3SizePresent = Object.prototype.hasOwnProperty.call(payload, "db3_size_bytes");
  const db3SizeBytes = payload.db3_size_bytes === null ? null : asNumber(payload.db3_size_bytes);
  const timestampFirstNs = payload.timestamp_first_ns === null ? null : asNumber(payload.timestamp_first_ns);
  const timestampLastNs = payload.timestamp_last_ns === null ? null : asNumber(payload.timestamp_last_ns);
  const topicCount = asNumber(payload.topic_count);
  const messageCount = asNumber(payload.message_count);
  const semanticSampleCount = asNumber(payload.semantic_sample_count);
  const semanticDecodeOkCount = asNumber(payload.semantic_decode_ok_count);
  const semanticDecodeFailedCount = asNumber(payload.semantic_decode_failed_count);
  const laserScan = asRecord(payload.laser_scan_summary);
  const imageSummary = asRecord(payload.image_summary);
  const tfSummary = asRecord(payload.tf_summary);
  const missingFields = [
    typeof payload.metadata_present === "boolean" ? "" : "metadata_present",
    typeof payload.db3_present === "boolean" ? "" : "db3_present",
    typeof payload.db3_read_ok === "boolean" ? "" : "db3_read_ok",
    db3SizePresent && db3SizeBytes !== null && db3SizeBytes >= 0 ? "" : "db3_size_bytes",
    topicCount !== null && topicCount >= 0 ? "" : "topic_count",
    messageCount !== null && messageCount >= 0 ? "" : "message_count",
    semanticSampleCount !== null && semanticSampleCount >= 0 ? "" : "semantic_sample_count",
    semanticDecodeOkCount !== null && semanticDecodeOkCount >= 0 ? "" : "semantic_decode_ok_count",
    semanticDecodeFailedCount !== null && semanticDecodeFailedCount >= 0 ? "" : "semantic_decode_failed_count",
    Array.isArray(payload.semantic_topic_types) ? "" : "semantic_topic_types",
    laserScan ? "" : "laser_scan_summary",
    imageSummary ? "" : "image_summary",
    tfSummary ? "" : "tf_summary",
    Array.isArray(payload.sample_topic_names) ? "" : "sample_topic_names",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteBagSemanticReplay(
      `route_bag_semantic_replay_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const safeLaserScan = laserScan as JsonRecord;
  const safeImageSummary = imageSummary as JsonRecord;
  const safeTfSummary = tfSummary as JsonRecord;

  const sampleTopicNames = stringList(payload.sample_topic_names, MVP_REF_SAMPLE_LIMIT);
  const rawSemanticTopicTypes = rawStringList(payload.semantic_topic_types);
  const safeSemanticTopicTypes = rawSemanticTopicTypes.map((value) => safeRouteBagSemanticTopicType(value)).filter(Boolean);
  if (safeSemanticTopicTypes.length !== rawSemanticTopicTypes.length) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_unsafe_topic_type", taskId);
  }
  const semanticTopicTypes = uniqueStrings(safeSemanticTopicTypes);

  const rawLaserScanEncoding = asString(safeLaserScan.encoding, "not_loaded");
  const laserScanUnsafeText = aggregateDistinct([
    unsafeRouteBagSemanticTextReason(payload.status),
    unsafeRouteBagSemanticTextReason(payload.route_bag_source),
    unsafeRouteBagSemanticTextReason(payload.source_label),
    unsafeRouteBagSemanticTextReason(rawLaserScanEncoding),
    stringList(payload.blocked_reasons).map((value) => unsafeRouteBagSemanticTextReason(value)),
    stringList(payload.next_required_evidence).map((value) => unsafeRouteBagSemanticTextReason(value)),
  ]);
  if (laserScanUnsafeText.length > 0) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_unsafe_text", taskId);
  }

  const laserScanRangeSampleLength = asNumber(safeLaserScan.range_sample_length);
  const laserScanFiniteCount = asNumber(safeLaserScan.finite_count);
  const laserScanRangeMin = asNumber(safeLaserScan.range_min);
  const laserScanRangeMax = asNumber(safeLaserScan.range_max);
  const laserScanAngleMin = asNumber(safeLaserScan.angle_min);
  const laserScanAngleMax = asNumber(safeLaserScan.angle_max);
  const laserScanAngleIncrement = asNumber(safeLaserScan.angle_increment);
  const imageWidth = asNumber(safeImageSummary.width);
  const imageHeight = asNumber(safeImageSummary.height);
  const imageStep = asNumber(safeImageSummary.step);
  const imageDataSize = asNumber(safeImageSummary.data_size);
  const tfTransformCount = asNumber(safeTfSummary.transform_count);
  const rawTfFrameIdSamples = rawStringList(safeTfSummary.frame_id_samples);
  const rawTfChildFrameIdSamples = rawStringList(safeTfSummary.child_frame_id_samples);
  const safeTfFrameIdSamples = rawTfFrameIdSamples.filter((value) => !unsafeRouteBagSemanticTextReason(value));
  const safeTfChildFrameIdSamples = rawTfChildFrameIdSamples.filter((value) => !unsafeRouteBagSemanticTextReason(value));
  if (safeTfFrameIdSamples.length !== rawTfFrameIdSamples.length || safeTfChildFrameIdSamples.length !== rawTfChildFrameIdSamples.length) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_unsafe_text", taskId);
  }
  const tfFrameIdSamples = uniqueStrings(safeTfFrameIdSamples);
  const tfChildFrameIdSamples = uniqueStrings(safeTfChildFrameIdSamples);
  const scalarMissingFields = [
    laserScanRangeSampleLength !== null ? "" : "laser_scan_summary.range_sample_length",
    laserScanFiniteCount !== null ? "" : "laser_scan_summary.finite_count",
    laserScanRangeMin !== null ? "" : "laser_scan_summary.range_min",
    laserScanRangeMax !== null ? "" : "laser_scan_summary.range_max",
    laserScanAngleMin !== null ? "" : "laser_scan_summary.angle_min",
    laserScanAngleMax !== null ? "" : "laser_scan_summary.angle_max",
    laserScanAngleIncrement !== null ? "" : "laser_scan_summary.angle_increment",
    imageWidth !== null ? "" : "image_summary.width",
    imageHeight !== null ? "" : "image_summary.height",
    imageStep !== null ? "" : "image_summary.step",
    imageDataSize !== null ? "" : "image_summary.data_size",
    tfTransformCount !== null ? "" : "tf_summary.transform_count",
  ].filter(Boolean);
  if (scalarMissingFields.length > 0) {
    return blockedRouteBagSemanticReplay(
      `route_bag_semantic_replay_missing_required_fields:${scalarMissingFields.join(",")}`,
      taskId,
    );
  }

  const semanticDecodeOk = semanticDecodeOkCount ?? 0;
  const semanticDecodeFailed = semanticDecodeFailedCount ?? 0;
  const semanticSample = semanticSampleCount ?? 0;
  if (semanticDecodeOk + semanticDecodeFailed !== semanticSample) {
    return blockedRouteBagSemanticReplay("route_bag_semantic_replay_count_mismatch", taskId);
  }

  const blockedReasons = aggregateDistinct([
    stringList(payload.blocked_reasons),
    "not_proven",
    "route_execution_success_not_proven",
    "delivery_success_not_proven",
    semanticDecodeFailed > 0 ? "route_bag_semantic_replay_decode_failed_not_proven" : "",
  ]);
  const nextRequiredEvidence = stringList(payload.next_required_evidence).length
    ? stringList(payload.next_required_evidence)
    : ["route_bag_semantic_replay_for_selected_task"];
  const ready =
    asString(payload.status, "derived_blocked_not_proven") === "ready_not_route_execution_proof" &&
    semanticDecodeFailed === 0 &&
    semanticDecodeOk > 0 &&
    semanticTopicTypes.length > 0;

  return {
    schema: schema as O7ConsumerRouteBagSemanticReplaySummary["schema"],
    status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    semantic_decode_status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerRouteBagSemanticReplaySummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    proof_scope: ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE,
    route_bag_source: safeRouteBagLabel(payload.route_bag_source ?? payload.source, "route_bag_semantic_replay"),
    source_label: safeRouteBagLabel(payload.source_label ?? payload.source, "route_bag_semantic_replay"),
    metadata_present: payload.metadata_present === true,
    db3_present: payload.db3_present === true,
    db3_read_ok: payload.db3_read_ok === true,
    db3_size_bytes: db3SizeBytes,
    db3_sha256_prefix: routeBagSha256Prefix(payload.db3_sha256_prefix),
    topic_count: topicCount ?? 0,
    message_count: messageCount ?? 0,
    timestamp_first_ns: timestampFirstNs,
    timestamp_last_ns: timestampLastNs,
    sample_topic_names: sampleTopicNames,
    semantic_sample_count: semanticSample,
    semantic_decode_ok_count: semanticDecodeOk,
    semantic_decode_failed_count: semanticDecodeFailed,
    semantic_topic_types: semanticTopicTypes,
    laser_scan_summary: {
      sample_count: asNumber(safeLaserScan.sample_count) ?? 0,
      range_sample_length: laserScanRangeSampleLength,
      finite_count: laserScanFiniteCount,
      range_min: laserScanRangeMin,
      range_max: laserScanRangeMax,
      angle_min: laserScanAngleMin,
      angle_max: laserScanAngleMax,
      angle_increment: laserScanAngleIncrement,
    },
    image_summary: {
      sample_count: asNumber(safeImageSummary.sample_count) ?? 0,
      width: imageWidth,
      height: imageHeight,
      encoding: asString(safeImageSummary.encoding, "not_loaded"),
      step: imageStep,
      data_size: imageDataSize,
    },
    tf_summary: {
      sample_count: asNumber(safeTfSummary.sample_count) ?? 0,
      transform_count: tfTransformCount,
      frame_id_samples: tfFrameIdSamples,
      child_frame_id_samples: tfChildFrameIdSamples,
    },
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeBagFullSemanticDecodeMatrixTopicTypeSummary(
  value: unknown,
): O7ConsumerRouteBagFullSemanticDecodeMatrixTopicTypeSummary | null {
  // matrix 行只保留 topic/type/status/count/decoder 摘要；任何控制 topic 或不安全文本都让整段 matrix fail-closed。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const topicName = asString(record.topic_name ?? record.topic ?? record.name, "");
  const topicType = safeRouteBagSemanticTopicType(record.topic_type ?? record.type ?? record.message_type);
  if (
    unsafeRouteBagTopicNameReason(topicName, "route_bag_full_semantic_decode_matrix_unsafe_topic") ||
    !topicType
  ) {
    return null;
  }
  const decodedCount = asNumber(record.decoded_message_sample_count ?? record.decoded_sample_count);
  const unsupportedCount = asNumber(record.unsupported_message_sample_count ?? record.unsupported_sample_count);
  const failedCount = asNumber(record.decode_failed_message_sample_count ?? record.failed_message_sample_count);
  if (
    decodedCount === null ||
    unsupportedCount === null ||
    failedCount === null ||
    decodedCount < 0 ||
    unsupportedCount < 0 ||
    failedCount < 0
  ) {
    return null;
  }
  const rawStatus = asString(record.decode_status ?? record.status, "");
  const derivedStatus =
    rawStatus === "decoded" || rawStatus === "unsupported" || rawStatus === "failed"
      ? rawStatus
      : decodedCount > 0
        ? "decoded"
        : unsupportedCount > 0
          ? "unsupported"
          : failedCount > 0
            ? "failed"
            : "blocked_not_proven";
  const decoderName = asString(record.decoder_name ?? record.decoder ?? "not_loaded", "not_loaded");
  const blockedReason = asString(
    record.blocked_reason,
    derivedStatus === "decoded" ? "none" : "semantic_decoder_gap_not_proven",
  );
  const unsafeText = aggregateDistinct([
    unsafeRouteBagSemanticTextReason(decoderName, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(blockedReason, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(rawStatus, "route_bag_full_semantic_decode_matrix_unsafe_text"),
  ]);
  if (unsafeText.length > 0) {
    return null;
  }
  return {
    topic_name: topicName,
    topic_type: topicType,
    decode_status: derivedStatus,
    decoder_name: decoderName,
    decoded_message_sample_count: decodedCount,
    unsupported_message_sample_count: unsupportedCount,
    decode_failed_message_sample_count: failedCount,
    blocked_reason: blockedReason,
  };
}

function buildRouteBagFullSemanticDecodeMatrixSummary(
  candidate: RouteBagFullSemanticDecodeMatrixSourceResult | null,
  taskId: string,
): O7ConsumerRouteBagFullSemanticDecodeMatrixSummary {
  // O7 只消费 O6/Algorithm 的覆盖矩阵摘要，不反序列化 ROS payload，也不从覆盖率推断路线成功。
  if (!candidate) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_missing",
      taskId,
    );
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA && schema !== O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_schema_mismatch",
      taskId,
    );
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      `route_bag_full_semantic_decode_matrix_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_proof_scope_mismatch",
      taskId,
    );
  }

  const topicTypeCount = asNumber(payload.topic_type_count);
  const decodedTopicTypeCount = asNumber(payload.decoded_topic_type_count);
  const unsupportedTopicTypeCount = asNumber(payload.unsupported_topic_type_count);
  const failedTopicTypeCount = asNumber(payload.failed_topic_type_count);
  const decodedMessageSampleCount = asNumber(payload.decoded_message_sample_count);
  const unsupportedMessageSampleCount = asNumber(payload.unsupported_message_sample_count);
  const decodeFailedMessageSampleCount = asNumber(payload.decode_failed_message_sample_count);
  const coverageRatio = asNumber(payload.coverage_ratio);
  const missingFields = [
    topicTypeCount !== null && topicTypeCount >= 0 ? "" : "topic_type_count",
    decodedTopicTypeCount !== null && decodedTopicTypeCount >= 0 ? "" : "decoded_topic_type_count",
    unsupportedTopicTypeCount !== null && unsupportedTopicTypeCount >= 0 ? "" : "unsupported_topic_type_count",
    failedTopicTypeCount !== null && failedTopicTypeCount >= 0 ? "" : "failed_topic_type_count",
    decodedMessageSampleCount !== null && decodedMessageSampleCount >= 0 ? "" : "decoded_message_sample_count",
    unsupportedMessageSampleCount !== null && unsupportedMessageSampleCount >= 0 ? "" : "unsupported_message_sample_count",
    decodeFailedMessageSampleCount !== null && decodeFailedMessageSampleCount >= 0 ? "" : "decode_failed_message_sample_count",
    coverageRatio !== null ? "" : "coverage_ratio",
    Array.isArray(payload.topic_type_matrix) || Array.isArray(payload.sample_topic_type_matrix)
      ? ""
      : "topic_type_matrix",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      `route_bag_full_semantic_decode_matrix_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  if (coverageRatio === null || coverageRatio < 0 || coverageRatio > 1) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_coverage_ratio_invalid",
      taskId,
    );
  }
  if ((decodedTopicTypeCount ?? 0) + (unsupportedTopicTypeCount ?? 0) + (failedTopicTypeCount ?? 0) !== (topicTypeCount ?? 0)) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_count_mismatch",
      taskId,
    );
  }

  const rawRows = Array.isArray(payload.topic_type_matrix)
    ? payload.topic_type_matrix
    : Array.isArray(payload.sample_topic_type_matrix)
      ? payload.sample_topic_type_matrix
      : [];
  const sampleRows = rawRows
    .slice(0, MVP_REF_SAMPLE_LIMIT)
    .map((row) => routeBagFullSemanticDecodeMatrixTopicTypeSummary(row));
  if (sampleRows.some((row) => row === null) || ((topicTypeCount ?? 0) > 0 && sampleRows.length === 0)) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_unsafe_topic_type",
      taskId,
    );
  }
  const sampleTopicTypeMatrix = sampleRows.filter(
    (row): row is O7ConsumerRouteBagFullSemanticDecodeMatrixTopicTypeSummary => Boolean(row),
  );
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const rawSource = payload.route_bag_source ?? payload.source;
  const rawSourceLabel = payload.source_label ?? payload.source;
  const source = safeRouteBagLabel(rawSource, "route_bag_full_semantic_decode_matrix");
  const sourceLabel = safeRouteBagLabel(rawSourceLabel, source);
  const unsafeText = aggregateDistinct([
    unsafeRouteBagSemanticTextReason(payload.status, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(payload.semantic_decode_matrix_status, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(rawSource, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(rawSourceLabel, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    unsafeRouteBagSemanticTextReason(payload.task_id_source, "route_bag_full_semantic_decode_matrix_unsafe_text"),
    blockedReasons.map((value) => unsafeRouteBagSemanticTextReason(value, "route_bag_full_semantic_decode_matrix_unsafe_text")),
    nextRequiredEvidence.map((value) => unsafeRouteBagSemanticTextReason(value, "route_bag_full_semantic_decode_matrix_unsafe_text")),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteBagFullSemanticDecodeMatrix(
      "route_bag_full_semantic_decode_matrix_unsafe_text",
      taskId,
    );
  }

  const payloadStatus = asString(payload.status, "derived_blocked_not_proven");
  const matrixStatus = asString(payload.semantic_decode_matrix_status ?? payloadStatus, payloadStatus);
  const ready =
    payloadStatus === "ready_not_route_execution_proof" &&
    matrixStatus === "ready_not_route_execution_proof" &&
    (topicTypeCount ?? 0) > 0 &&
    (decodedTopicTypeCount ?? 0) > 0 &&
    coverageRatio > 0;
  return {
    schema: schema as O7ConsumerRouteBagFullSemanticDecodeMatrixSummary["schema"],
    status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    semantic_decode_matrix_status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerRouteBagFullSemanticDecodeMatrixSummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    proof_scope: ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE,
    route_bag_source: source,
    source_label: sourceLabel,
    topic_type_count: topicTypeCount ?? 0,
    decoded_topic_type_count: decodedTopicTypeCount ?? 0,
    unsupported_topic_type_count: unsupportedTopicTypeCount ?? 0,
    failed_topic_type_count: failedTopicTypeCount ?? 0,
    decoded_message_sample_count: decodedMessageSampleCount ?? 0,
    unsupported_message_sample_count: unsupportedMessageSampleCount ?? 0,
    decode_failed_message_sample_count: decodeFailedMessageSampleCount ?? 0,
    coverage_ratio: coverageRatio,
    sample_topic_type_matrix: sampleTopicTypeMatrix,
    sample_topic_names: uniqueStrings(sampleTopicTypeMatrix.map((row) => row.topic_name)),
    sample_topic_types: uniqueStrings(sampleTopicTypeMatrix.map((row) => row.topic_type)),
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "not_proven",
      "route_execution_success_not_proven",
      "delivery_success_not_proven",
      (unsupportedTopicTypeCount ?? 0) > 0 ? "route_bag_full_semantic_decode_matrix_unsupported_types_present" : "",
      (failedTopicTypeCount ?? 0) > 0 ? "route_bag_full_semantic_decode_matrix_failed_types_present" : "",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "decoder_for_unsupported_topic_types",
          "decode_failure_repro_for_selected_task",
          "real_live_nav2_run_or_route_execution_proof",
          "delivery_result_for_selected_task",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeBagPoseProgressFrameSummary(value: unknown): O7ConsumerRouteBagPoseProgressFramePairSummary | null {
  // frame pair 只允许短 frame id 和有限样本计数，不允许路径、URL 或控制字段透传。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const sourceFrameId = asString(record.source_frame_id ?? record.source_frame ?? record.from_frame_id ?? record.from_frame, "");
  const targetFrameId = asString(record.target_frame_id ?? record.target_frame ?? record.to_frame_id ?? record.to_frame, "");
  const sampleCount = asNumber(record.sample_count ?? record.count);
  if (
    unsafeRouteBagPoseFrameIdReason(sourceFrameId) ||
    unsafeRouteBagPoseFrameIdReason(targetFrameId) ||
    sampleCount === null ||
    sampleCount < 0
  ) {
    return null;
  }
  return {
    source_frame_id: sourceFrameId,
    target_frame_id: targetFrameId,
    sample_count: sampleCount,
  };
}

function routeBagPoseProgressPoseSummary(value: unknown, fallbackFrameId: string): O7ConsumerRouteBagPoseProgressPoseSummary | null {
  // 起终点位姿只保留 frame / x / y / yaw / timestamp，其他字段一律丢弃。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const frameId = asString(record.frame_id ?? record.frameId ?? record.frame ?? fallbackFrameId, fallbackFrameId);
  if (unsafeRouteBagPoseFrameIdReason(frameId)) {
    return null;
  }
  return {
    frame_id: frameId,
    x_m: asNumber(record.x_m ?? record.x ?? record.position_x_m ?? record.position_x),
    y_m: asNumber(record.y_m ?? record.y ?? record.position_y_m ?? record.position_y),
    yaw_rad: asNumber(record.yaw_rad ?? record.yaw ?? record.heading_rad ?? record.theta_rad),
    timestamp_ns: asNumber(record.timestamp_ns ?? record.timestampNs ?? record.timestamp),
  };
}

function buildRouteBagPoseProgressReplaySummary(
  candidate: RouteBagPoseProgressReplaySourceResult | null,
  taskId: string,
): O7ConsumerRouteBagPoseProgressReplaySummary {
  // O7 只消费位姿进度安全摘要，不读取 raw payload、原始路径或控制面字段。
  if (!candidate) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA && schema !== O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteBagPoseProgressReplay(
      `route_bag_pose_progress_replay_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_proof_scope_mismatch", taskId);
  }

  const db3SizePresent = Object.prototype.hasOwnProperty.call(payload, "db3_size_bytes");
  const db3SizeBytes = payload.db3_size_bytes === null ? null : asNumber(payload.db3_size_bytes);
  const timestampFirstNs = payload.timestamp_first_ns === null ? null : asNumber(payload.timestamp_first_ns);
  const timestampLastNs = payload.timestamp_last_ns === null ? null : asNumber(payload.timestamp_last_ns);
  const topicCount = asNumber(payload.topic_count);
  const messageCount = asNumber(payload.message_count);
  const poseSampleCount = asNumber(payload.pose_sample_count);
  const poseDecodeOkCount = asNumber(payload.pose_decode_ok_count);
  const poseDecodeFailedCount = asNumber(payload.pose_decode_failed_count);
  const poseTimeSpanNs = payload.pose_time_span_ns === null ? null : asNumber(payload.pose_time_span_ns);
  const missingFields = [
    typeof payload.metadata_present === "boolean" ? "" : "metadata_present",
    typeof payload.db3_present === "boolean" ? "" : "db3_present",
    typeof payload.db3_read_ok === "boolean" ? "" : "db3_read_ok",
    db3SizePresent && (payload.db3_size_bytes === null || db3SizeBytes !== null) ? "" : "db3_size_bytes",
    topicCount !== null && topicCount >= 0 ? "" : "topic_count",
    messageCount !== null && messageCount >= 0 ? "" : "message_count",
    poseSampleCount !== null && poseSampleCount >= 0 ? "" : "pose_sample_count",
    poseDecodeOkCount !== null && poseDecodeOkCount >= 0 ? "" : "pose_decode_ok_count",
    poseDecodeFailedCount !== null && poseDecodeFailedCount >= 0 ? "" : "pose_decode_failed_count",
    poseTimeSpanNs !== null || payload.pose_time_span_ns === null ? "" : "pose_time_span_ns",
    Array.isArray(payload.sample_topic_names) ? "" : "sample_topic_names",
    Array.isArray(payload.pose_topic_types) ? "" : "pose_topic_types",
    Array.isArray(payload.pose_frame_pairs) ? "" : "pose_frame_pairs",
    typeof payload.start_pose === "object" && payload.start_pose !== null ? "" : "start_pose",
    typeof payload.end_pose === "object" && payload.end_pose !== null ? "" : "end_pose",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteBagPoseProgressReplay(
      `route_bag_pose_progress_replay_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }

  const sampleTopicNames = stringList(payload.sample_topic_names, MVP_REF_SAMPLE_LIMIT);
  const unsafeTopics = sampleTopicNames
    .map((topic) => unsafeRouteBagTopicNameReason(topic, "route_bag_pose_progress_replay_unsafe_topic_type"))
    .filter(Boolean);
  if (unsafeTopics.length > 0) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_unsafe_topic_type", taskId);
  }

  const rawPoseTopicTypes = rawStringList(payload.pose_topic_types);
  const safePoseTopicTypes = rawPoseTopicTypes.map((value) => safeRouteBagSemanticTopicType(value)).filter(Boolean);
  if (safePoseTopicTypes.length !== rawPoseTopicTypes.length) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_unsafe_topic_type", taskId);
  }

  const rawFramePairs = Array.isArray(payload.pose_frame_pairs) ? payload.pose_frame_pairs : [];
  const poseFramePairs = rawFramePairs
    .map((pair) => routeBagPoseProgressFrameSummary(pair))
    .filter((pair): pair is O7ConsumerRouteBagPoseProgressFramePairSummary => Boolean(pair));
  if (poseFramePairs.length !== rawFramePairs.length) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_unsafe_frame_id", taskId);
  }

  const startPose = routeBagPoseProgressPoseSummary(payload.start_pose, poseFramePairs[0]?.source_frame_id ?? "start");
  const endPose = routeBagPoseProgressPoseSummary(payload.end_pose, poseFramePairs[poseFramePairs.length - 1]?.target_frame_id ?? "end");
  if (!startPose || !endPose) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_unsafe_frame_id", taskId);
  }

  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const rawSource = payload.route_bag_source ?? payload.source;
  const rawSourceLabel = payload.source_label ?? payload.source;
  const source = safeRouteBagLabel(rawSource, "route_bag_pose_progress_replay");
  const sourceLabel = safeRouteBagLabel(rawSourceLabel, source);
  const unsafeText = aggregateDistinct([
    unsafeRouteBagSemanticTextReason(payload.status, "route_bag_pose_progress_replay_unsafe_text"),
    unsafeRouteBagSemanticTextReason(payload.pose_decode_status, "route_bag_pose_progress_replay_unsafe_text"),
    unsafeRouteBagSemanticTextReason(rawSource, "route_bag_pose_progress_replay_unsafe_text"),
    unsafeRouteBagSemanticTextReason(rawSourceLabel, "route_bag_pose_progress_replay_unsafe_text"),
    unsafeRouteBagSemanticTextReason(payload.task_id_source, "route_bag_pose_progress_replay_unsafe_text"),
    blockedReasons.map((value) => unsafeRouteBagSemanticTextReason(value, "route_bag_pose_progress_replay_unsafe_text")),
    nextRequiredEvidence.map((value) => unsafeRouteBagSemanticTextReason(value, "route_bag_pose_progress_replay_unsafe_text")),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_unsafe_text", taskId);
  }

  const displacement = asNumber(payload.displacement_m);
  const nonzeroProgress =
    asBoolean(payload.nonzero_pose_progress_observed) &&
    displacement !== null &&
    displacement > 0 &&
    poseFramePairs.some((pair) => pair.sample_count > 0);
  if (!nonzeroProgress) {
    return blockedRouteBagPoseProgressReplay("route_bag_pose_progress_replay_zero_displacement_not_proven", taskId);
  }

  const ready =
    asString(payload.status, "derived_blocked_not_proven") === "ready_not_live_nav2_proof" &&
    asString(payload.pose_decode_status, "derived_blocked_not_proven") === "ready_not_live_nav2_proof" &&
    poseSampleCount !== null &&
    poseDecodeOkCount !== null &&
    poseDecodeFailedCount !== null &&
    poseDecodeFailedCount === 0 &&
    poseDecodeOkCount > 0 &&
    poseSampleCount > 0 &&
    safePoseTopicTypes.length > 0 &&
    poseFramePairs.length > 0;

  return {
    schema: schema as O7ConsumerRouteBagPoseProgressReplaySummary["schema"],
    status: ready ? "ready_not_live_nav2_proof" : "derived_blocked_not_proven",
    pose_decode_status: ready ? "ready_not_live_nav2_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerRouteBagPoseProgressReplaySummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    proof_scope: ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
    route_bag_source: source,
    source_label: sourceLabel,
    metadata_present: payload.metadata_present === true,
    db3_present: payload.db3_present === true,
    db3_read_ok: payload.db3_read_ok === true,
    db3_size_bytes: db3SizeBytes,
    db3_sha256_prefix: routeBagSha256Prefix(payload.db3_sha256_prefix),
    topic_count: topicCount ?? 0,
    message_count: messageCount ?? 0,
    timestamp_first_ns: timestampFirstNs,
    timestamp_last_ns: timestampLastNs,
    sample_topic_names: sampleTopicNames,
    pose_sample_count: poseSampleCount ?? 0,
    pose_decode_ok_count: poseDecodeOkCount ?? 0,
    pose_decode_failed_count: poseDecodeFailedCount ?? 0,
    pose_topic_types: uniqueStrings(safePoseTopicTypes),
    pose_frame_pairs: poseFramePairs,
    pose_time_span_ns: poseTimeSpanNs,
    start_pose: startPose,
    end_pose: endPose,
    displacement_m: displacement ?? 0,
    nonzero_pose_progress_observed: asBoolean(payload.nonzero_pose_progress_observed),
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "not_proven",
      "route_execution_success_not_proven",
      "delivery_success_not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["real_live_nav2_run_or_route_execution_proof", "delivery_result_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
}

function buildRouteBagEvidenceSummary(
  candidate: RouteBagEvidenceSourceResult | null,
  taskId: string,
): O7ConsumerRouteBagEvidenceSummary {
  // O7 只消费 DB3 结构摘要：source/status、topic/message/timestamp、短 checksum 和 fail-closed flags。
  if (!candidate) {
    return blockedRouteBagEvidence("route_bag_evidence_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== ROUTE_BAG_EVIDENCE_SCHEMA && schema !== O6_ROUTE_BAG_EVIDENCE_SCHEMA) {
    return blockedRouteBagEvidence("route_bag_evidence_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteBagEvidence(`route_bag_evidence_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_BAG_EVIDENCE_PROOF_SCOPE) {
    return blockedRouteBagEvidence("route_bag_evidence_proof_scope_mismatch", taskId);
  }

  const db3SizePresent = Object.prototype.hasOwnProperty.call(payload, "db3_size_bytes");
  const timestampFirstPresent = Object.prototype.hasOwnProperty.call(payload, "timestamp_first_ns");
  const timestampLastPresent = Object.prototype.hasOwnProperty.call(payload, "timestamp_last_ns");
  const db3SizeBytes = payload.db3_size_bytes === null ? null : asNumber(payload.db3_size_bytes);
  const timestampFirstNs = payload.timestamp_first_ns === null ? null : asNumber(payload.timestamp_first_ns);
  const timestampLastNs = payload.timestamp_last_ns === null ? null : asNumber(payload.timestamp_last_ns);
  const topicCount = asNumber(payload.topic_count);
  const messageCount = asNumber(payload.message_count);
  const missingFields = [
    typeof payload.metadata_present === "boolean" ? "" : "metadata_present",
    typeof payload.db3_present === "boolean" ? "" : "db3_present",
    typeof payload.db3_read_ok === "boolean" ? "" : "db3_read_ok",
    db3SizePresent && (payload.db3_size_bytes === null || db3SizeBytes !== null) ? "" : "db3_size_bytes",
    topicCount !== null ? "" : "topic_count",
    messageCount !== null ? "" : "message_count",
    timestampFirstPresent && (payload.timestamp_first_ns === null || timestampFirstNs !== null) ? "" : "timestamp_first_ns",
    timestampLastPresent && (payload.timestamp_last_ns === null || timestampLastNs !== null) ? "" : "timestamp_last_ns",
    Array.isArray(payload.sample_topic_names) ? "" : "sample_topic_names",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteBagEvidence(`route_bag_evidence_missing_required_fields:${missingFields.join(",")}`, taskId);
  }

  const sampleTopicNames = stringList(payload.sample_topic_names, MVP_REF_SAMPLE_LIMIT);
  const unsafeTopics = sampleTopicNames.map((topic) => unsafeRouteBagTopicNameReason(topic)).filter(Boolean);
  if (unsafeTopics.length > 0) {
    return blockedRouteBagEvidence("route_bag_evidence_unsafe_topic_name", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const rawSource = payload.route_bag_source ?? payload.source;
  const rawSourceLabel = payload.source_label ?? payload.source;
  const source = safeRouteBagLabel(rawSource, "route_bag_evidence");
  const sourceLabel = safeRouteBagLabel(rawSourceLabel, source);
  const unsafeText = aggregateDistinct([
    unsafeRouteBagTextReason(payload.status),
    unsafeRouteBagTextReason(rawSource),
    unsafeRouteBagTextReason(rawSourceLabel),
    unsafeRouteBagTextReason(payload.task_id_source),
    blockedReasons.map((value) => unsafeRouteBagTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeRouteBagTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteBagEvidence("route_bag_evidence_unsafe_text", taskId);
  }

  const ready =
    asString(payload.status, "derived_blocked_not_proven") === "ready_not_route_execution_proof" ||
    (payload.db3_read_ok === true && (topicCount ?? 0) > 0 && (messageCount ?? 0) > 0);
  return {
    schema: schema as O7ConsumerRouteBagEvidenceSummary["schema"],
    status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerRouteBagEvidenceSummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    proof_scope: ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
    route_bag_source: source,
    source_label: sourceLabel,
    metadata_present: payload.metadata_present === true,
    db3_present: payload.db3_present === true,
    db3_read_ok: payload.db3_read_ok === true,
    db3_size_bytes: db3SizeBytes,
    db3_sha256_prefix: routeBagSha256Prefix(payload.db3_sha256_prefix),
    topic_count: topicCount ?? 0,
    message_count: messageCount ?? 0,
    timestamp_first_ns: timestampFirstNs,
    timestamp_last_ns: timestampLastNs,
    sample_topic_names: sampleTopicNames,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "not_proven",
      "route_execution_success_not_proven",
      "delivery_success_not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["real_live_nav2_run_or_route_execution_proof", "delivery_result_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function buildRouteBagPayloadReplaySummary(
  candidate: RouteBagPayloadReplaySourceResult | null,
  taskId: string,
): O7ConsumerRouteBagPayloadReplaySummary {
  // O7 只消费 DB3 payload 派生摘要：topic/message/timestamp、payload size/hash prefix 和 fail-closed flags。
  if (!candidate) {
    return blockedRouteBagPayloadReplay("route_bag_payload_replay_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA && schema !== O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA) {
    return blockedRouteBagPayloadReplay("route_bag_payload_replay_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteBagPayloadReplay(
      `route_bag_payload_replay_dangerous_true:${dangerous
        .map((field) => `route_bag_payload_replay.${field}`)
        .join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE) {
    return blockedRouteBagPayloadReplay("route_bag_payload_replay_proof_scope_mismatch", taskId);
  }

  const db3SizePresent = Object.prototype.hasOwnProperty.call(payload, "db3_size_bytes");
  const timestampFirstPresent = Object.prototype.hasOwnProperty.call(payload, "timestamp_first_ns");
  const timestampLastPresent = Object.prototype.hasOwnProperty.call(payload, "timestamp_last_ns");
  const db3SizeBytes = payload.db3_size_bytes === null ? null : asNumber(payload.db3_size_bytes);
  const timestampFirstNs = payload.timestamp_first_ns === null ? null : asNumber(payload.timestamp_first_ns);
  const timestampLastNs = payload.timestamp_last_ns === null ? null : asNumber(payload.timestamp_last_ns);
  const topicCount = asNumber(payload.topic_count);
  const messageCount = asNumber(payload.message_count);
  const payloadSampleCount = asNumber(payload.payload_sample_count);
  const payloadSizeMinBytes = payload.payload_size_min_bytes === null ? null : asNumber(payload.payload_size_min_bytes);
  const payloadSizeMaxBytes = payload.payload_size_max_bytes === null ? null : asNumber(payload.payload_size_max_bytes);
  const payloadSizeAvgBytes = payload.payload_size_avg_bytes === null ? null : asNumber(payload.payload_size_avg_bytes);
  const missingFields = [
    typeof payload.metadata_present === "boolean" ? "" : "metadata_present",
    typeof payload.db3_present === "boolean" ? "" : "db3_present",
    typeof payload.db3_read_ok === "boolean" ? "" : "db3_read_ok",
    db3SizePresent && db3SizeBytes !== null && db3SizeBytes >= 0 ? "" : "db3_size_bytes",
    topicCount !== null && topicCount >= 0 ? "" : "topic_count",
    messageCount !== null && messageCount >= 0 ? "" : "message_count",
    payloadSampleCount !== null && payloadSampleCount >= 0 ? "" : "payload_sample_count",
    payloadSizeMinBytes !== null && payloadSizeMinBytes >= 0 ? "" : "payload_size_min_bytes",
    payloadSizeMaxBytes !== null && payloadSizeMaxBytes >= 0 ? "" : "payload_size_max_bytes",
    payloadSizeAvgBytes !== null && payloadSizeAvgBytes >= 0 ? "" : "payload_size_avg_bytes",
    timestampFirstPresent && (payload.timestamp_first_ns === null || timestampFirstNs !== null) ? "" : "timestamp_first_ns",
    timestampLastPresent && (payload.timestamp_last_ns === null || timestampLastNs !== null) ? "" : "timestamp_last_ns",
    Array.isArray(payload.sample_topic_names) ? "" : "sample_topic_names",
    Array.isArray(payload.payload_sha256_prefix_samples) ? "" : "payload_sha256_prefix_samples",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteBagPayloadReplay(
      `route_bag_payload_replay_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }

  const sampleTopicNames = stringList(payload.sample_topic_names, MVP_REF_SAMPLE_LIMIT);
  const unsafeTopics = sampleTopicNames
    .map((topic) => unsafeRouteBagTopicNameReason(topic, "route_bag_payload_replay_unsafe_topic_name"))
    .filter(Boolean);
  if (unsafeTopics.length > 0) {
    return blockedRouteBagPayloadReplay("route_bag_payload_replay_unsafe_topic_name", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const rawSource = payload.route_bag_source ?? payload.source;
  const rawSourceLabel = payload.source_label ?? payload.source;
  const source = safeRouteBagLabel(rawSource, "route_bag_payload_replay");
  const sourceLabel = safeRouteBagLabel(rawSourceLabel, source);
  const unsafeText = aggregateDistinct([
    unsafeRouteBagTextReason(payload.status, "route_bag_payload_replay_unsafe_text"),
    unsafeRouteBagTextReason(rawSource, "route_bag_payload_replay_unsafe_text"),
    unsafeRouteBagTextReason(rawSourceLabel, "route_bag_payload_replay_unsafe_text"),
    unsafeRouteBagTextReason(payload.task_id_source, "route_bag_payload_replay_unsafe_text"),
    blockedReasons.map((value) => unsafeRouteBagTextReason(value, "route_bag_payload_replay_unsafe_text")),
    nextRequiredEvidence.map((value) => unsafeRouteBagTextReason(value, "route_bag_payload_replay_unsafe_text")),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteBagPayloadReplay("route_bag_payload_replay_unsafe_text", taskId);
  }

  const payloadSha256PrefixSamples = rawStringList(payload.payload_sha256_prefix_samples, MVP_REF_SAMPLE_LIMIT)
    .map((value) => routeBagSha256Prefix(value))
    .filter(Boolean);
  const ready =
    asString(payload.status, "derived_blocked_not_proven") === "ready_not_route_execution_proof" ||
    (payload.db3_read_ok === true &&
      (topicCount ?? 0) > 0 &&
      (messageCount ?? 0) > 0 &&
      (payloadSampleCount ?? 0) > 0 &&
      (payloadSizeMinBytes ?? -1) >= 0 &&
      (payloadSizeMaxBytes ?? -1) >= 0 &&
      (payloadSizeAvgBytes ?? -1) >= 0 &&
      payloadSha256PrefixSamples.length > 0);
  return {
    schema: schema as O7ConsumerRouteBagPayloadReplaySummary["schema"],
    status: ready ? "ready_not_route_execution_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerRouteBagPayloadReplaySummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    proof_scope: ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
    route_bag_source: source,
    source_label: sourceLabel,
    metadata_present: payload.metadata_present === true,
    db3_present: payload.db3_present === true,
    db3_read_ok: payload.db3_read_ok === true,
    db3_size_bytes: db3SizeBytes,
    db3_sha256_prefix: routeBagSha256Prefix(payload.db3_sha256_prefix),
    topic_count: topicCount ?? 0,
    message_count: messageCount ?? 0,
    timestamp_first_ns: timestampFirstNs,
    timestamp_last_ns: timestampLastNs,
    sample_topic_names: sampleTopicNames,
    payload_sample_count: payloadSampleCount ?? 0,
    payload_size_min_bytes: payloadSizeMinBytes,
    payload_size_max_bytes: payloadSizeMaxBytes,
    payload_size_avg_bytes: payloadSizeAvgBytes,
    payload_sha256_prefix_samples: payloadSha256PrefixSamples,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "not_proven",
      "route_execution_success_not_proven",
      "delivery_success_not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["real_live_nav2_run_or_route_execution_proof", "delivery_result_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_run_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function fieldMotionEvidencePacketCandidateFromRemote(remote: JsonRecord): FieldMotionEvidencePacketSourceResult | null {
  // field motion packet 只从 O6 约定白名单位置读取，不消费 route bag/live log 的原始文件路径。
  const direct = asRecord(remote.field_motion_evidence_packet);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet",
    };
  }
  const fieldEvidencePacket = nestedRecord(remote, "field_evidence", "field_motion_evidence_packet");
  if (fieldEvidencePacket) {
    return {
      payload: fieldEvidencePacket,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.field_motion_evidence_packet",
    };
  }
  const fieldEvidenceIngestPacket =
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_motion_evidence_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_motion_evidence_packet");
  if (fieldEvidenceIngestPacket) {
    return {
      payload: fieldEvidenceIngestPacket,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.field_motion_evidence_packet",
    };
  }
  const readinessPacket = nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet");
  if (readinessPacket) {
    return {
      payload: readinessPacket,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.field_motion_evidence_packet",
    };
  }
  return null;
}

function unsafeFieldMotionTextReason(value: unknown): string {
  // packet 的文本字段不能带 URL、token、base64、raw 内容、路径或根目录回显。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "field_motion_evidence_packet_unsafe_text";
  }
  return "";
}

function blockedFieldMotionEvidencePacket(
  reason: string,
  taskId: string,
): O7ConsumerFieldMotionEvidencePacketSummary {
  // 缺失或被拒绝时也返回完整 packet 摘要，避免 UI 把缺字段当成“已拿到现场运动证据”。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    route_summary: {
      frame_count: 0,
      nonzero_displacement_observed: false,
      displacement_m: 0,
    },
    motion_log_summary: {
      live_motion_evidence_present: false,
      evidence_sources: [],
    },
    route_bag_or_live_nav2_log: {
      present: false,
      source: "not_loaded",
      route_bag_present: false,
      live_motion_log_present: false,
    },
    blocked_reasons: [reason],
    next_required_evidence: ["field_motion_evidence_packet_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_log_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function fieldMotionEvidencePacketHardFailReason(summary: O7ConsumerFieldMotionEvidencePacketSummary): string {
  // 坏 schema、危险 true 或未脱敏文本都要让 detail 主路径直接 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(field_motion_evidence_packet_schema_mismatch|field_motion_evidence_packet_dangerous_true|field_motion_evidence_packet_missing_required_fields|field_motion_evidence_packet_unsafe_text|field_motion_evidence_packet_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildFieldMotionEvidencePacketSummary(
  candidate: FieldMotionEvidencePacketSourceResult | null,
  taskId: string,
): O7ConsumerFieldMotionEvidencePacketSummary {
  // O7 只消费 route frame / 位移 / motion log 来源摘要，不读取 route bag/live log 的原始位置。
  if (!candidate) {
    return blockedFieldMotionEvidencePacket("field_motion_evidence_packet_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_FIELD_MOTION_EVIDENCE_PACKET_SCHEMA && schema !== FIELD_MOTION_EVIDENCE_PACKET_SCHEMA) {
    return blockedFieldMotionEvidencePacket("field_motion_evidence_packet_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedFieldMotionEvidencePacket(`field_motion_evidence_packet_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  const routeSummary = asRecord(payload.route_summary);
  const motionLogSummary = asRecord(payload.motion_log_summary);
  const routeBagOrLiveNav2Log = asRecord(payload.route_bag_or_live_nav2_log);
  const proofScope = asString(payload.proof_scope, "not_loaded");
  const missingFields = [
    routeSummary ? "" : "route_summary",
    motionLogSummary ? "" : "motion_log_summary",
    routeBagOrLiveNav2Log ? "" : "route_bag_or_live_nav2_log",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0 || !routeSummary || !motionLogSummary || !routeBagOrLiveNav2Log) {
    return blockedFieldMotionEvidencePacket(
      `field_motion_evidence_packet_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  if (proofScope !== FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE) {
    return blockedFieldMotionEvidencePacket("field_motion_evidence_packet_proof_scope_mismatch", taskId);
  }
  const frameCount = asNumber(routeSummary.frame_count);
  const displacementM = asNumber(routeSummary.displacement_m);
  const nonzeroDisplacementObserved = typeof routeSummary.nonzero_displacement_observed === "boolean"
    ? routeSummary.nonzero_displacement_observed
    : null;
  const liveMotionEvidencePresent = typeof motionLogSummary.live_motion_evidence_present === "boolean"
    ? motionLogSummary.live_motion_evidence_present
    : null;
  const packetPresent = typeof routeBagOrLiveNav2Log.present === "boolean" ? routeBagOrLiveNav2Log.present : null;
  const routeBagPresent = typeof routeBagOrLiveNav2Log.route_bag_present === "boolean"
    ? routeBagOrLiveNav2Log.route_bag_present
    : null;
  const liveMotionLogPresent = typeof routeBagOrLiveNav2Log.live_motion_log_present === "boolean"
    ? routeBagOrLiveNav2Log.live_motion_log_present
    : null;
  const routeSource = asString(routeBagOrLiveNav2Log.source, "blocked_not_proven");
  const scalarMissingFields = [
    frameCount === null ? "route_summary.frame_count" : "",
    displacementM === null ? "route_summary.displacement_m" : "",
    nonzeroDisplacementObserved === null ? "route_summary.nonzero_displacement_observed" : "",
    liveMotionEvidencePresent === null ? "motion_log_summary.live_motion_evidence_present" : "",
    packetPresent === null ? "route_bag_or_live_nav2_log.present" : "",
    routeBagPresent === null ? "route_bag_or_live_nav2_log.route_bag_present" : "",
    liveMotionLogPresent === null ? "route_bag_or_live_nav2_log.live_motion_log_present" : "",
    routeSource ? "" : "route_bag_or_live_nav2_log.source",
  ].filter(Boolean);
  if (scalarMissingFields.length > 0) {
    return blockedFieldMotionEvidencePacket(
      `field_motion_evidence_packet_missing_required_fields:${scalarMissingFields.join(",")}`,
      taskId,
    );
  }
  const evidenceSources = stringList(motionLogSummary.evidence_sources, MVP_REF_SAMPLE_LIMIT);
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const unsafeText = aggregateDistinct([
    unsafeFieldMotionTextReason(payload.status),
    unsafeFieldMotionTextReason(routeSource),
    evidenceSources.map((value) => unsafeFieldMotionTextReason(value)),
    blockedReasons.map((value) => unsafeFieldMotionTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeFieldMotionTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedFieldMotionEvidencePacket("field_motion_evidence_packet_unsafe_text", taskId);
  }
  const ready = asString(payload.status, "blocked_not_proven") === "field_motion_packet_ready_not_delivery_proof";
  return {
    schema: schema as O7ConsumerFieldMotionEvidencePacketSummary["schema"],
    status: ready ? "field_motion_packet_ready_not_delivery_proof" : "derived_blocked_not_proven",
    source_contract: schema as O7ConsumerFieldMotionEvidencePacketSummary["source_contract"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE,
    route_summary: {
      frame_count: frameCount ?? 0,
      nonzero_displacement_observed: nonzeroDisplacementObserved ?? false,
      displacement_m: displacementM ?? 0,
    },
    motion_log_summary: {
      live_motion_evidence_present: liveMotionEvidencePresent ?? false,
      evidence_sources: evidenceSources,
    },
    route_bag_or_live_nav2_log: {
      present: packetPresent ?? false,
      source: routeSource,
      route_bag_present: routeBagPresent ?? false,
      live_motion_log_present: liveMotionLogPresent ?? false,
    },
    blocked_reasons: blockedReasons.length ? blockedReasons : ["local_mock_only", "not_proven"],
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["field_motion_evidence_packet_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_bag_connected: false,
      live_nav2_log_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function nav2GoalExecutionEvidenceCandidateFromRemote(
  remote: JsonRecord,
): Nav2GoalExecutionEvidenceSourceResult | null {
  // Nav2 goal 证据只从 O6 已归一的白名单 wrapper 读取，避免 O7 自己拼原始 action log。
  const direct = asRecord(remote.nav2_goal_execution_evidence);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_nav2_goal_execution_evidence",
      source_path: "nav2_goal_execution_evidence",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_manifest", "nav2_goal_execution_evidence");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.nav2_goal_execution_evidence",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "nav2_goal_execution_evidence");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.nav2_goal_execution_evidence",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_motion_evidence_packet", "nav2_goal_execution_evidence");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.nav2_goal_execution_evidence",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "nav2_goal_execution_evidence");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.nav2_goal_execution_evidence",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "nav2_goal_execution_evidence");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.nav2_goal_execution_evidence",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "nav2_goal_execution_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "nav2_goal_execution_evidence");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.nav2_goal_execution_evidence",
    };
  }
  return null;
}

function unsafeNav2GoalTextReason(value: unknown): string {
  // Nav2 evidence 的说明字段不能夹带 URL、token、raw payload、base64、路径或控制面话题。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "nav2_goal_execution_evidence_unsafe_text";
  }
  return "";
}

function nav2GoalSummaryText(value: unknown, fallback: string): string {
  // summary 允许上游给 object，但 O7 只展开少量 scalar，避免把原始 action payload 整包显示出来。
  const record = asRecord(value);
  if (!record) {
    return asString(value, fallback);
  }
  const parts = Object.entries(record)
    .flatMap(([key, nested]) => {
      if (typeof nested === "string" || typeof nested === "number" || typeof nested === "boolean") {
        return [`${key}=${String(nested).slice(0, 80)}`];
      }
      if (nested === null) {
        return [`${key}=null`];
      }
      return [];
    })
    .slice(0, 6);
  return parts.length ? parts.join(", ") : fallback;
}

function blockedNav2GoalExecutionEvidence(
  reason: string,
  taskId: string,
): O7ConsumerNav2GoalExecutionEvidenceSummary {
  // 缺失或被拒绝时仍返回完整 contract，让 UI 可见“还缺 Nav2 goal/result 证据”而不是静默缺字段。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    evidence_source: "not_loaded",
    goal_requested: false,
    goal_sent: false,
    goal_accepted: false,
    result_received: false,
    goal_result_status: "blocked_not_proven",
    result_status_code: null,
    nav2_goal_execution_proven: false,
    base_motion_command_nonzero_proven: false,
    requested_base_command_mode: "not_loaded",
    base_command_mode: "not_loaded",
    pose_progress_summary: "blocked_not_proven",
    base_feedback_summary: "blocked_not_proven",
    base_command_summary: "blocked_not_proven",
    blocked_reasons: [reason],
    next_required_evidence: ["nav2_goal_execution_evidence_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      base_feedback_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function nav2GoalExecutionEvidenceHardFailReason(summary: O7ConsumerNav2GoalExecutionEvidenceSummary): string {
  // 坏 schema、危险 true、缺必填、unsafe text 和 proof scope mismatch 都要让 detail 主路径 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(nav2_goal_execution_evidence_schema_mismatch|nav2_goal_execution_evidence_dangerous_true|nav2_goal_execution_evidence_missing_required_fields|nav2_goal_execution_evidence_unsafe_text|nav2_goal_execution_evidence_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildNav2GoalExecutionEvidenceSummary(
  candidate: Nav2GoalExecutionEvidenceSourceResult | null,
  taskId: string,
): O7ConsumerNav2GoalExecutionEvidenceSummary {
  // O7 只消费 goal/result/base command 的摘要字段，不打开任何真实控制或送达判断。
  if (!candidate) {
    return blockedNav2GoalExecutionEvidence("nav2_goal_execution_evidence_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA) {
    return blockedNav2GoalExecutionEvidence("nav2_goal_execution_evidence_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedNav2GoalExecutionEvidence(
      `nav2_goal_execution_evidence_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE) {
    return blockedNav2GoalExecutionEvidence("nav2_goal_execution_evidence_proof_scope_mismatch", taskId);
  }
  const resultStatusCodePresent = Object.prototype.hasOwnProperty.call(payload, "result_status_code");
  const resultStatusCode = payload.result_status_code === null ? null : asNumber(payload.result_status_code);
  const missingFields = [
    typeof payload.goal_requested === "boolean" ? "" : "goal_requested",
    typeof payload.goal_sent === "boolean" ? "" : "goal_sent",
    typeof payload.goal_accepted === "boolean" ? "" : "goal_accepted",
    typeof payload.result_received === "boolean" ? "" : "result_received",
    rawString(payload.goal_result_status) ? "" : "goal_result_status",
    resultStatusCodePresent && (payload.result_status_code === null || resultStatusCode !== null) ? "" : "result_status_code",
    typeof payload.nav2_goal_execution_proven === "boolean" ? "" : "nav2_goal_execution_proven",
    typeof payload.base_motion_command_nonzero_proven === "boolean" ? "" : "base_motion_command_nonzero_proven",
    rawString(payload.requested_base_command_mode) ? "" : "requested_base_command_mode",
    rawString(payload.base_command_mode) ? "" : "base_command_mode",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedNav2GoalExecutionEvidence(
      `nav2_goal_execution_evidence_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const poseProgressSummary = nav2GoalSummaryText(payload.pose_progress_summary, "blocked_not_proven");
  const baseFeedbackSummary = nav2GoalSummaryText(payload.base_feedback_summary, "blocked_not_proven");
  const baseCommandSummary = nav2GoalSummaryText(payload.base_command_summary, "blocked_not_proven");
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const unsafeText = aggregateDistinct([
    unsafeNav2GoalTextReason(payload.status),
    unsafeNav2GoalTextReason(payload.source),
    unsafeNav2GoalTextReason(payload.proof_status),
    unsafeNav2GoalTextReason(payload.goal_result_status),
    unsafeNav2GoalTextReason(payload.requested_base_command_mode),
    unsafeNav2GoalTextReason(payload.base_command_mode),
    unsafeNav2GoalTextReason(poseProgressSummary),
    unsafeNav2GoalTextReason(baseFeedbackSummary),
    unsafeNav2GoalTextReason(baseCommandSummary),
    blockedReasons.map((value) => unsafeNav2GoalTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeNav2GoalTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedNav2GoalExecutionEvidence("nav2_goal_execution_evidence_unsafe_text", taskId);
  }
  const payloadStatus = asString(payload.status, "derived_blocked_not_proven");
  const ready =
    payloadStatus === "nav2_goal_execution_evidence_ready_not_delivery_proof" ||
    (payload.goal_requested === true && payload.goal_sent === true && payload.goal_accepted === true);
  return {
    schema: NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
    status: ready ? "nav2_goal_execution_evidence_ready_not_delivery_proof" : "derived_blocked_not_proven",
    source_contract: NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    evidence_source: asString(payload.source, "o6_consumer_detail"),
    goal_requested: payload.goal_requested === true,
    goal_sent: payload.goal_sent === true,
    goal_accepted: payload.goal_accepted === true,
    result_received: payload.result_received === true,
    goal_result_status: asString(payload.goal_result_status, "blocked_not_proven"),
    result_status_code: resultStatusCode,
    nav2_goal_execution_proven: payload.nav2_goal_execution_proven === true,
    base_motion_command_nonzero_proven: payload.base_motion_command_nonzero_proven === true,
    requested_base_command_mode: asString(payload.requested_base_command_mode, "blocked_not_proven"),
    base_command_mode: asString(payload.base_command_mode, "blocked_not_proven"),
    pose_progress_summary: poseProgressSummary,
    base_feedback_summary: baseFeedbackSummary,
    base_command_summary: baseCommandSummary,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      payload.base_motion_command_nonzero_proven === true ? "" : "base_motion_command_nonzero_not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["delivery_result_for_selected_task", "nonzero_base_feedback_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      base_feedback_connected: payload.base_motion_command_nonzero_proven === true,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function deliveryResultEvidenceCandidateFromRemote(
  remote: JsonRecord,
): DeliveryResultEvidenceSourceResult | null {
  // delivery result 只从 O6 已脱敏的 additive wrapper 读取，不回看原始 delivery record。
  const direct = asRecord(remote.delivery_result_evidence);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_delivery_result_evidence",
      source_path: "delivery_result_evidence",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_manifest", "delivery_result_evidence");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.delivery_result_evidence",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "delivery_result_evidence");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.delivery_result_evidence",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_motion_evidence_packet", "delivery_result_evidence");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.delivery_result_evidence",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "delivery_result_evidence");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.delivery_result_evidence",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "delivery_result_evidence") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "delivery_result_evidence");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.delivery_result_evidence",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "delivery_result_evidence") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "delivery_result_evidence");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.delivery_result_evidence",
    };
  }
  return null;
}

function unsafeDeliveryResultTextReason(value: unknown): string {
  // delivery result 的说明文字不能夹带 URL、token、raw/base64、路径或 root 级调试内容。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("raw") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "delivery_result_evidence_unsafe_text";
  }
  return "";
}

function blockedDeliveryResultEvidence(
  reason: string,
  taskId: string,
): O7ConsumerDeliveryResultEvidenceSummary {
  // 缺失或被拒绝时也返回完整 contract，让 UI 明确知道 delivery result 仍未证明。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    evidence_source: "not_loaded",
    record_source: "not_loaded",
    source_schema: "not_loaded",
    task_id_source: "not_loaded",
    record_present: false,
    record_read_ok: false,
    record_status: "blocked_not_proven",
    delivery_result_claimed: false,
    operator_confirmation_present: false,
    dropoff_confirmation_type: "not_loaded",
    completed_at_utc: "not_loaded",
    linked_nav2_goal_execution_proven: false,
    blocked_reasons: [reason],
    next_required_evidence: ["delivery_result_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      operator_confirmation_connected: false,
      delivery_record_connected: false,
      linked_nav2_goal_execution_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function deliveryResultEvidenceHardFailReason(
  summary: O7ConsumerDeliveryResultEvidenceSummary,
): string {
  // 坏 schema、危险 true、缺必填和 unsafe text 都要让 detail 主路径 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(delivery_result_evidence_schema_mismatch|delivery_result_evidence_dangerous_true|delivery_result_evidence_missing_required_fields|delivery_result_evidence_unsafe_text|delivery_result_evidence_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildDeliveryResultEvidenceSummary(
  candidate: DeliveryResultEvidenceSourceResult | null,
  taskId: string,
): O7ConsumerDeliveryResultEvidenceSummary {
  // O7 只消费送达记录白名单摘要，不把 operator claim 升级成真实交付完成。
  if (!candidate) {
    return blockedDeliveryResultEvidence("delivery_result_evidence_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== DELIVERY_RESULT_EVIDENCE_SCHEMA) {
    return blockedDeliveryResultEvidence("delivery_result_evidence_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedDeliveryResultEvidence(
      `delivery_result_evidence_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE) {
    return blockedDeliveryResultEvidence("delivery_result_evidence_proof_scope_mismatch", taskId);
  }
  const missingFields = [
    typeof payload.record_present === "boolean" ? "" : "record_present",
    typeof payload.record_read_ok === "boolean" ? "" : "record_read_ok",
    typeof payload.delivery_result_claimed === "boolean" ? "" : "delivery_result_claimed",
    typeof payload.operator_confirmation_present === "boolean" ? "" : "operator_confirmation_present",
    typeof payload.linked_nav2_goal_execution_proven === "boolean" ? "" : "linked_nav2_goal_execution_proven",
    rawString(payload.record_status) ? "" : "record_status",
    rawString(payload.source_schema) ? "" : "source_schema",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedDeliveryResultEvidence(
      `delivery_result_evidence_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const completedAtUtc = asString(payload.completed_at_utc, "not_loaded");
  const unsafeText = aggregateDistinct([
    unsafeDeliveryResultTextReason(payload.status),
    unsafeDeliveryResultTextReason(payload.source),
    unsafeDeliveryResultTextReason(payload.record_source),
    unsafeDeliveryResultTextReason(payload.source_schema),
    unsafeDeliveryResultTextReason(payload.task_id_source),
    unsafeDeliveryResultTextReason(payload.record_status),
    unsafeDeliveryResultTextReason(payload.dropoff_confirmation_type),
    unsafeDeliveryResultTextReason(completedAtUtc),
    blockedReasons.map((value) => unsafeDeliveryResultTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeDeliveryResultTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedDeliveryResultEvidence("delivery_result_evidence_unsafe_text", taskId);
  }
  const ready =
    asString(payload.status, "derived_blocked_not_proven") ===
      "delivery_result_evidence_ready_not_delivery_proof" ||
    payload.record_present === true ||
    payload.operator_confirmation_present === true;
  return {
    schema: DELIVERY_RESULT_EVIDENCE_SCHEMA,
    status: ready ? "delivery_result_evidence_ready_not_delivery_proof" : "derived_blocked_not_proven",
    source_contract: DELIVERY_RESULT_EVIDENCE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    evidence_source: asString(payload.source, "o6_consumer_detail"),
    record_source: asString(payload.record_source ?? payload.source, "not_loaded"),
    source_schema: asString(payload.source_schema, "not_loaded"),
    task_id_source: asString(payload.task_id_source, "not_loaded"),
    record_present: payload.record_present === true,
    record_read_ok: payload.record_read_ok === true,
    record_status: asString(payload.record_status, "blocked_not_proven"),
    delivery_result_claimed: payload.delivery_result_claimed === true,
    operator_confirmation_present: payload.operator_confirmation_present === true,
    dropoff_confirmation_type: asString(payload.dropoff_confirmation_type, "not_loaded"),
    completed_at_utc: completedAtUtc,
    linked_nav2_goal_execution_proven: payload.linked_nav2_goal_execution_proven === true,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      payload.record_present === true ? "" : "delivery_record_missing",
      payload.record_read_ok === true ? "" : "delivery_record_read_not_proven",
      payload.operator_confirmation_present === true ? "" : "operator_confirmation_missing",
      payload.linked_nav2_goal_execution_proven === true ? "" : "linked_nav2_goal_execution_not_proven",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : ["delivery_record_or_operator_dropoff_confirmation", "delivery_result_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      operator_confirmation_connected: false,
      delivery_record_connected: false,
      linked_nav2_goal_execution_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeExecutionResultDeliveryReadinessCandidateFromRemote(
  remote: JsonRecord,
): RouteExecutionResultDeliveryReadinessSourceResult | null {
  // 统一结果链摘要只能从 O6 白名单位置读取，O7 不自己拼 route execution / delivery 成功语义。
  const direct = asRecord(remote.route_execution_result_delivery_readiness);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_execution_result_delivery_readiness",
      source_path: "route_execution_result_delivery_readiness",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_manifest", "route_execution_result_delivery_readiness");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.route_execution_result_delivery_readiness",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_execution_result_delivery_readiness");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_execution_result_delivery_readiness",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_motion_evidence_packet", "route_execution_result_delivery_readiness");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_execution_result_delivery_readiness",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle", "route_execution_result_delivery_readiness");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_execution_result_delivery_readiness",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle", "route_execution_result_delivery_readiness");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_execution_result_delivery_readiness",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_execution_result_delivery_readiness") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_execution_result_delivery_readiness");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_execution_result_delivery_readiness",
    };
  }
  return null;
}

function unsafeRouteExecutionResultDeliveryReadinessTextReason(value: unknown): string {
  // 结果链 readiness 只允许短标签，不允许 URL、token、路径、base64 或控制面语义混入。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "route_execution_result_delivery_readiness_unsafe_text";
  }
  return "";
}

function blockedRouteExecutionResultDeliveryReadiness(
  reason: string,
  taskId: string,
): O7ConsumerRouteExecutionResultDeliveryReadinessSummary {
  // 缺失或被拒绝时也返回完整 contract，避免 UI 把 undefined 误解为结果链已就绪。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    route_execution_result_status: "blocked_not_proven",
    route_execution_source: "not_loaded",
    delivery_result_readiness_status: "blocked_not_proven",
    delivery_result_source: "not_loaded",
    operator_confirmation_readiness_status: "blocked_not_proven",
    operator_confirmation_source: "not_loaded",
    nav2_goal_execution_ready: false,
    delivery_result_ready: false,
    operator_confirmation_ready: false,
    blocked_reasons: [reason],
    next_required_evidence: ["route_execution_result_delivery_readiness_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      operator_confirmation_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeExecutionResultDeliveryReadinessHardFailReason(
  summary: O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
): string {
  // 坏 schema、危险 true、缺必填和 unsafe text 都要让 detail 主路径 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_execution_result_delivery_readiness_schema_mismatch|route_execution_result_delivery_readiness_dangerous_true|route_execution_result_delivery_readiness_missing_required_fields|route_execution_result_delivery_readiness_unsafe_text|route_execution_result_delivery_readiness_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildRouteExecutionResultDeliveryReadinessSummary(
  candidate: RouteExecutionResultDeliveryReadinessSourceResult | null,
  taskId: string,
): O7ConsumerRouteExecutionResultDeliveryReadinessSummary {
  // O7 只消费 O6 的统一结果链 readiness，不用 Nav2/delivery 子摘要反向拼装“成功”。
  if (!candidate) {
    return blockedRouteExecutionResultDeliveryReadiness(
      "route_execution_result_delivery_readiness_missing",
      taskId,
    );
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA) {
    return blockedRouteExecutionResultDeliveryReadiness(
      "route_execution_result_delivery_readiness_schema_mismatch",
      taskId,
    );
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteExecutionResultDeliveryReadiness(
      `route_execution_result_delivery_readiness_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE) {
    return blockedRouteExecutionResultDeliveryReadiness(
      "route_execution_result_delivery_readiness_proof_scope_mismatch",
      taskId,
    );
  }
  const missingFields = [
    rawString(payload.route_execution_result_status) ? "" : "route_execution_result_status",
    rawString(payload.route_execution_source) ? "" : "route_execution_source",
    rawString(payload.delivery_result_readiness_status) ? "" : "delivery_result_readiness_status",
    rawString(payload.delivery_result_source) ? "" : "delivery_result_source",
    rawString(payload.operator_confirmation_readiness_status)
      ? ""
      : "operator_confirmation_readiness_status",
    rawString(payload.operator_confirmation_source) ? "" : "operator_confirmation_source",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteExecutionResultDeliveryReadiness(
      `route_execution_result_delivery_readiness_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const routeExecutionResultStatus = asString(payload.route_execution_result_status, "blocked_not_proven");
  const routeExecutionSource = asString(payload.route_execution_source, "not_loaded");
  const deliveryResultReadinessStatus = asString(payload.delivery_result_readiness_status, "blocked_not_proven");
  const deliveryResultSource = asString(payload.delivery_result_source, "not_loaded");
  const operatorConfirmationReadinessStatus = asString(
    payload.operator_confirmation_readiness_status,
    "blocked_not_proven",
  );
  const operatorConfirmationSource = asString(payload.operator_confirmation_source, "not_loaded");
  const unsafeText = aggregateDistinct([
    unsafeRouteExecutionResultDeliveryReadinessTextReason(payload.status),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(routeExecutionResultStatus),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(routeExecutionSource),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(deliveryResultReadinessStatus),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(deliveryResultSource),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(operatorConfirmationReadinessStatus),
    unsafeRouteExecutionResultDeliveryReadinessTextReason(operatorConfirmationSource),
    blockedReasons.map((value) => unsafeRouteExecutionResultDeliveryReadinessTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeRouteExecutionResultDeliveryReadinessTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteExecutionResultDeliveryReadiness(
      "route_execution_result_delivery_readiness_unsafe_text",
      taskId,
    );
  }
  const nav2GoalExecutionReady =
    asBoolean(payload.nav2_goal_execution_ready) ||
    /ready|result_received|succeeded/i.test(routeExecutionResultStatus);
  const deliveryResultReady =
    asBoolean(payload.delivery_result_ready) ||
    /ready|recorded|present/i.test(deliveryResultReadinessStatus);
  const operatorConfirmationReady =
    asBoolean(payload.operator_confirmation_ready) ||
    /ready|present|confirmed/i.test(operatorConfirmationReadinessStatus);
  const payloadTopLevelStatus = asString(payload.status, "derived_blocked_not_proven");
  // 顶层 ready 只能信任 O6 顶层状态；子 readiness 只做展示，不能把 blocked 反推成 ready。
  const payloadTopLevelReady =
    payloadTopLevelStatus === "route_execution_result_delivery_readiness_ready_not_delivery_proof";
  const summaryStatus = payloadTopLevelReady
    ? "route_execution_result_delivery_readiness_ready_not_delivery_proof"
    : payloadTopLevelStatus === "blocked_not_proven"
      ? "blocked_not_proven"
      : "derived_blocked_not_proven";
  return {
    schema: O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
    status: summaryStatus,
    source_contract: O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    route_execution_result_status: routeExecutionResultStatus,
    route_execution_source: routeExecutionSource,
    delivery_result_readiness_status: deliveryResultReadinessStatus,
    delivery_result_source: deliveryResultSource,
    operator_confirmation_readiness_status: operatorConfirmationReadinessStatus,
    operator_confirmation_source: operatorConfirmationSource,
    nav2_goal_execution_ready: nav2GoalExecutionReady,
    delivery_result_ready: deliveryResultReady,
    operator_confirmation_ready: operatorConfirmationReady,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      payloadTopLevelReady ? "" : "route_execution_result_delivery_readiness_not_ready",
      nav2GoalExecutionReady ? "" : "route_execution_result_not_ready",
      deliveryResultReady ? "" : "delivery_result_readiness_not_ready",
      operatorConfirmationReady ? "" : "operator_confirmation_readiness_not_ready",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "route_execution_result_for_selected_task",
          "delivery_record_or_operator_dropoff_confirmation",
          "real_drop_off_completion_proof",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      operator_confirmation_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeDeliveryClosurePacketCandidateFromRemote(
  remote: JsonRecord,
): RouteDeliveryClosurePacketSourceResult | null {
  // 闭合包只从 O6 白名单位置读取，O7 不自己拼成功语义。
  const direct = asRecord(remote.route_delivery_closure_packet);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_route_delivery_closure_packet",
      source_path: "route_delivery_closure_packet",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence_manifest", "route_delivery_closure_packet");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.route_delivery_closure_packet",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "route_delivery_closure_packet");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.route_delivery_closure_packet",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence_ingest", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "route_delivery_closure_packet");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.route_delivery_closure_packet",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "route_delivery_closure_packet") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "route_delivery_closure_packet");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.route_delivery_closure_packet",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "route_delivery_closure_packet") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "route_delivery_closure_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "route_delivery_closure_packet");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.route_delivery_closure_packet",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "route_delivery_closure_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "route_delivery_closure_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "route_delivery_closure_packet");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.route_delivery_closure_packet",
    };
  }
  return null;
}

function unsafeRouteDeliveryClosurePacketTextReason(value: unknown): string {
  // 闭合包文本只允许短标签，不允许 URL、token、路径或控制话题。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "route_delivery_closure_packet_unsafe_text";
  }
  return "";
}

function blockedRouteDeliveryClosurePacket(
  reason: string,
  taskId: string,
): O7ConsumerRouteDeliveryClosurePacketSummary {
  // 缺失或被拒绝时也返回完整 contract，避免 UI 把 undefined 误解成闭合已完成。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    closure_status: "blocked_not_proven",
    linked_evidence_flags: {
      nav2_goal_execution_ready: false,
      delivery_result_ready: false,
      operator_confirmation_ready: false,
      route_pose_progress_ready: false,
      route_execution_readiness_ready: false,
    },
    blocked_reasons: [reason],
    next_required_evidence: ["route_delivery_closure_packet_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      operator_confirmation_connected: false,
      route_pose_progress_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeDeliveryClosurePacketHardFailReason(summary: O7ConsumerRouteDeliveryClosurePacketSummary): string {
  // 坏 schema、危险 true、缺必填和 unsafe text 都要让 detail 主路径 fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(route_delivery_closure_packet_schema_mismatch|route_delivery_closure_packet_dangerous_true|route_delivery_closure_packet_missing_required_fields|route_delivery_closure_packet_unsafe_text|route_delivery_closure_packet_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildRouteDeliveryClosurePacketSummary(
  candidate: RouteDeliveryClosurePacketSourceResult | null,
  taskId: string,
): O7ConsumerRouteDeliveryClosurePacketSummary {
  // O7 只消费闭合状态和关联证据布尔值，不打开成功/控制语义。
  if (!candidate) {
    return blockedRouteDeliveryClosurePacket("route_delivery_closure_packet_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA) {
    return blockedRouteDeliveryClosurePacket("route_delivery_closure_packet_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedRouteDeliveryClosurePacket(
      `route_delivery_closure_packet_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE) {
    return blockedRouteDeliveryClosurePacket("route_delivery_closure_packet_proof_scope_mismatch", taskId);
  }
  const linkedFlagsRecord = asRecord(payload.linked_evidence_flags);
  const linkedFlags = {
    nav2_goal_execution_ready: asBoolean(
      linkedFlagsRecord?.nav2_goal_execution_ready ?? payload.nav2_goal_execution_ready,
    ),
    delivery_result_ready: asBoolean(linkedFlagsRecord?.delivery_result_ready ?? payload.delivery_result_ready),
    operator_confirmation_ready: asBoolean(
      linkedFlagsRecord?.operator_confirmation_ready ?? payload.operator_confirmation_ready,
    ),
    route_pose_progress_ready: asBoolean(
      linkedFlagsRecord?.route_pose_progress_ready ?? payload.route_pose_progress_ready,
    ),
    route_execution_readiness_ready: asBoolean(
      linkedFlagsRecord?.route_execution_readiness_ready ?? payload.route_execution_readiness_ready,
    ),
  };
  const closureStatus = asString(payload.closure_status ?? payload.status, "blocked_not_proven");
  const missingFields = [
    rawString(payload.closure_status ?? payload.status) ? "" : "closure_status",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
    Object.values(linkedFlags).some((value) => typeof value === "boolean") ? "" : "linked_evidence_flags",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedRouteDeliveryClosurePacket(
      `route_delivery_closure_packet_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const unsafeText = aggregateDistinct([
    unsafeRouteDeliveryClosurePacketTextReason(payload.status),
    unsafeRouteDeliveryClosurePacketTextReason(closureStatus),
    blockedReasons.map((value) => unsafeRouteDeliveryClosurePacketTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeRouteDeliveryClosurePacketTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedRouteDeliveryClosurePacket("route_delivery_closure_packet_unsafe_text", taskId);
  }
  const ready = asString(payload.status, "derived_blocked_not_proven") === "route_delivery_closure_ready_not_success_proof";
  return {
    schema: O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
    status: ready ? "route_delivery_closure_ready_not_success_proof" : "derived_blocked_not_proven",
    source_contract: O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    closure_status: closureStatus,
    linked_evidence_flags: linkedFlags,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      ready ? "" : "route_delivery_closure_packet_not_ready",
      linkedFlags.nav2_goal_execution_ready ? "" : "linked_nav2_goal_execution_missing",
      linkedFlags.delivery_result_ready ? "" : "linked_delivery_result_missing",
      linkedFlags.operator_confirmation_ready ? "" : "linked_operator_confirmation_missing",
      linkedFlags.route_pose_progress_ready ? "" : "linked_route_pose_progress_missing",
      linkedFlags.route_execution_readiness_ready ? "" : "linked_route_execution_readiness_missing",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "route_execution_result_for_selected_task",
          "delivery_record_or_operator_dropoff_confirmation",
          "route_pose_progress_replay_for_selected_task",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      live_nav2_goal_connected: false,
      delivery_result_connected: false,
      operator_confirmation_connected: false,
      route_pose_progress_connected: false,
      route_execution_success: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskFieldMaterialPacketCandidateFromRemote(
  remote: JsonRecord,
): SameTaskFieldMaterialPacketSourceResult | null {
  // same-task field material packet 只读取 O6/O6-first 脱敏摘要，不回看 route 文件或 rosbag 原始路径。
  const direct = asRecord(remote.same_task_field_material_packet);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_same_task_field_material_packet",
      source_path: "same_task_field_material_packet",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence_manifest", "same_task_field_material_packet");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.same_task_field_material_packet",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "same_task_field_material_packet");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.same_task_field_material_packet",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence_ingest", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "same_task_field_material_packet");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.same_task_field_material_packet",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "same_task_field_material_packet");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.same_task_field_material_packet",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "same_task_field_material_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "same_task_field_material_packet");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.same_task_field_material_packet",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "same_task_field_material_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "same_task_field_material_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "same_task_field_material_packet");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.same_task_field_material_packet",
    };
  }
  return null;
}

function unsafeSameTaskFieldMaterialPacketTextReason(value: unknown): string {
  // packet 文本只能是短状态和 basename 级材料标签，不能夹带路径、URL、token 或原始 payload。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "same_task_field_material_packet_unsafe_text";
  }
  return "";
}

function unsafeSameTaskFieldMaterialPacketListReason(value: unknown, fieldName: string): string {
  // 列表字段必须是短字符串数组，避免对象或长 payload 通过 sample/blocker 泄露出去。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `same_task_field_material_packet_unsafe_list:${fieldName}`;
}

function normalizeMaterialTokenList(value: unknown, limit = 8): string[] {
  // materials 列表只保留短 token，避免 UI 侧把任意文本当成安全标签展示。
  return stringList(value, limit).map((item) => normalizeSameTaskFieldMaterialKey(item.replace(/\s+/g, "_")));
}

function normalizeSameTaskFieldMaterialKey(value: string): string {
  // 历史 fixture 可能用 route_bag / rosbag；统一折叠成当前合同里的 route_bag_or_rosbag。
  if (value === "route_bag" || value === "rosbag") {
    return "route_bag_or_rosbag";
  }
  return value;
}

function sameTaskFieldMaterialSummaryRecord(payload: JsonRecord | null): JsonRecord | null {
  // Algorithm/O6 现态可能把 per-material 摘要放在 material_summaries / material_sample_refs / sample_ref_summaries / 旧 sample_refs dict。
  const preferred =
    asRecord(payload?.material_summaries) ??
    asRecord(payload?.material_sample_refs) ??
    asRecord(payload?.sample_ref_summaries);
  if (preferred) {
    return preferred;
  }
  const legacySampleRefs = payload?.sample_refs;
  return Array.isArray(legacySampleRefs) ? null : asRecord(legacySampleRefs);
}

function sameTaskFieldMaterialSummaryEntry(value: unknown) {
  // 单个材料摘要只保留 basename/size/hash/sample refs/count/present，不把原始路径或 payload 往 UI 透传。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const sampleRefs = stringList(record.sample_refs, 6).map((item) => safePathToken(item));
  const basename = safePathToken(record.basename ?? sampleRefs[0] ?? "not_loaded");
  return {
    present: asBoolean(record.present),
    basename: basename || "not_loaded",
    size_bytes: asNumber(record.size_bytes),
    sha256_prefix: asString(record.sha256_prefix, "not_loaded"),
    sample_refs: sampleRefs,
    count: asNumber(record.count),
  };
}

function sameTaskFieldMaterialSummaries(payload: JsonRecord | null) {
  const source = sameTaskFieldMaterialSummaryRecord(payload);
  const mapYaml = sameTaskFieldMaterialSummaryEntry(source?.map_yaml) ?? undefined;
  const routeCsv = sameTaskFieldMaterialSummaryEntry(source?.route_csv) ?? undefined;
  const keyframes = sameTaskFieldMaterialSummaryEntry(source?.keyframes) ?? undefined;
  const routeBagOrRosbag =
    sameTaskFieldMaterialSummaryEntry(source?.route_bag_or_rosbag ?? source?.route_bag ?? source?.rosbag) ?? undefined;
  const replayJsonl = sameTaskFieldMaterialSummaryEntry(source?.replay_jsonl) ?? undefined;
  return {
    map_yaml: mapYaml,
    route_csv: routeCsv,
    keyframes,
    route_bag_or_rosbag: routeBagOrRosbag,
    replay_jsonl: replayJsonl,
  };
}

function sameTaskFieldMaterialTopLevelSampleRefs(payload: JsonRecord | null): string[] {
  // 新 O6 会给 list-shaped top-level sample_refs；旧 O6 若把它做成 dict，这里降级从 per-material summary 汇总，不做 fail-closed。
  if (Array.isArray(payload?.sample_refs)) {
    return stringList(payload?.sample_refs, 8).map((value) => safePathToken(value));
  }
  const summaries = sameTaskFieldMaterialSummaries(payload);
  return aggregateDistinct([
    summaries.map_yaml?.sample_refs ?? [],
    summaries.route_csv?.sample_refs ?? [],
    summaries.keyframes?.sample_refs ?? [],
    summaries.route_bag_or_rosbag?.sample_refs ?? [],
    summaries.replay_jsonl?.sample_refs ?? [],
  ]).slice(0, 8);
}

function sameTaskFieldMaterialSummaryUnsafeReasons(
  summaries: ReturnType<typeof sameTaskFieldMaterialSummaries>,
): string[] {
  // per-material 摘要中的 basename/sample refs/hash 也必须过同一层文本安全检查。
  return aggregateDistinct(
    Object.values(summaries).flatMap((summary) => {
      if (!summary) {
        return [];
      }
      return [
        unsafeSameTaskFieldMaterialPacketTextReason(summary.basename),
        unsafeSameTaskFieldMaterialPacketTextReason(summary.sha256_prefix),
        ...summary.sample_refs.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
      ];
    }),
  );
}

function blockedSameTaskFieldMaterialPacket(
  reason: string,
  taskId: string,
): O7ConsumerSameTaskFieldMaterialPacketSummary {
  // packet 缺失或被拒绝时也返回完整结构，避免 UI 将 undefined 误读为已消费材料。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    packet_status: "blocked_not_proven",
    task_id_source: "not_loaded",
    same_task_id_consumed: false,
    live_or_field_material_consumed: false,
    present_materials: [],
    missing_materials: [],
    sample_refs: [],
    material_summaries: {},
    route_csv_present: false,
    keyframes_present: false,
    route_bag_or_rosbag_present: false,
    replay_jsonl_present: false,
    map_yaml_present: false,
    blocked_reasons: [reason],
    next_required_evidence: ["same_task_field_material_packet_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      field_materials_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskFieldMaterialPacketHardFailReason(summary: O7ConsumerSameTaskFieldMaterialPacketSummary): string {
  // 坏 schema、危险 true、缺必填、unsafe text/list 和 proof scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(same_task_field_material_packet_schema_mismatch|same_task_field_material_packet_task_mismatch|same_task_field_material_packet_dangerous_true|same_task_field_material_packet_missing_required_fields|same_task_field_material_packet_unsafe_text|same_task_field_material_packet_unsafe_list|same_task_field_material_packet_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildSameTaskFieldMaterialPacketSummary(
  candidate: SameTaskFieldMaterialPacketSourceResult | null,
  taskId: string,
): O7ConsumerSameTaskFieldMaterialPacketSummary {
  // O7 只消费 packet 的脱敏材料摘要，不把 ready 外推成真实 delivery success 或 production cloud。
  if (!candidate) {
    return blockedSameTaskFieldMaterialPacket("same_task_field_material_packet_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA && schema !== SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA) {
    return blockedSameTaskFieldMaterialPacket("same_task_field_material_packet_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedSameTaskFieldMaterialPacket(
      `same_task_field_material_packet_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE) {
    return blockedSameTaskFieldMaterialPacket("same_task_field_material_packet_proof_scope_mismatch", taskId);
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedSameTaskFieldMaterialPacket("same_task_field_material_packet_task_mismatch", taskId);
  }
  const unsafeList = aggregateDistinct([
    unsafeSameTaskFieldMaterialPacketListReason(payload.present_materials, "present_materials"),
    unsafeSameTaskFieldMaterialPacketListReason(payload.missing_materials, "missing_materials"),
    unsafeSameTaskFieldMaterialPacketListReason(payload.sample_refs, "sample_refs"),
    unsafeSameTaskFieldMaterialPacketListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeSameTaskFieldMaterialPacketListReason(payload.next_required_evidence, "next_required_evidence"),
  ]);
  if (unsafeList.length > 0) {
    return blockedSameTaskFieldMaterialPacket(
      unsafeList[0] ?? "same_task_field_material_packet_unsafe_list",
      taskId,
    );
  }
  const presentMaterials = normalizeMaterialTokenList(payload.present_materials);
  const missingMaterials = normalizeMaterialTokenList(payload.missing_materials);
  const materialSummaries = sameTaskFieldMaterialSummaries(payload);
  const sampleRefs = sameTaskFieldMaterialTopLevelSampleRefs(payload);
  const blockedReasons = stringList(payload.blocked_reasons, 12);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const taskIdSource = asString(payload.task_id_source, "not_loaded");
  const routeCsvPresent = asBoolean(payload.route_csv_present ?? materialSummaries.route_csv?.present);
  const keyframesPresent = asBoolean(payload.keyframes_present ?? materialSummaries.keyframes?.present);
  const routeBagOrRosbagPresent = asBoolean(
    payload.route_bag_or_rosbag_present ??
      payload.rosbag_present ??
      payload.route_bag_present ??
      materialSummaries.route_bag_or_rosbag?.present,
  );
  const replayJsonlPresent = asBoolean(payload.replay_jsonl_present ?? materialSummaries.replay_jsonl?.present);
  const mapYamlPresent = asBoolean(payload.map_yaml_present ?? materialSummaries.map_yaml?.present);
  const sameTaskIdConsumed = asBoolean(payload.same_task_id_consumed);
  const liveOrFieldMaterialConsumed = asBoolean(
    payload.live_or_field_material_consumed ?? payload.live_or_field_command_executed,
  );
  const sampleRefsShapeValid =
    Array.isArray(payload.sample_refs) ||
    Boolean(sameTaskFieldMaterialSummaryRecord(payload));
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    typeof payload.same_task_id_consumed === "boolean" ? "" : "same_task_id_consumed",
    typeof (payload.live_or_field_material_consumed ?? payload.live_or_field_command_executed) === "boolean"
      ? ""
      : "live_or_field_material_consumed",
    Array.isArray(payload.present_materials) ? "" : "present_materials",
    Array.isArray(payload.missing_materials) ? "" : "missing_materials",
    sampleRefsShapeValid ? "" : "sample_refs_or_material_summaries",
    typeof (payload.route_csv_present ?? materialSummaries.route_csv?.present) === "boolean" ? "" : "route_csv_present",
    typeof (payload.keyframes_present ?? materialSummaries.keyframes?.present) === "boolean" ? "" : "keyframes_present",
    typeof (
      payload.route_bag_or_rosbag_present ??
      payload.rosbag_present ??
      payload.route_bag_present ??
      materialSummaries.route_bag_or_rosbag?.present
    ) === "boolean"
      ? ""
      : "route_bag_or_rosbag_present",
    typeof (payload.replay_jsonl_present ?? materialSummaries.replay_jsonl?.present) === "boolean" ? "" : "replay_jsonl_present",
    typeof (payload.map_yaml_present ?? materialSummaries.map_yaml?.present) === "boolean" ? "" : "map_yaml_present",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedSameTaskFieldMaterialPacket(
      `same_task_field_material_packet_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const unsafeText = aggregateDistinct([
    unsafeSameTaskFieldMaterialPacketTextReason(payload.status),
    unsafeSameTaskFieldMaterialPacketTextReason(payload.task_id_source),
    presentMaterials.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
    missingMaterials.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
    sampleRefs.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
    blockedReasons.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeSameTaskFieldMaterialPacketTextReason(value)),
    sameTaskFieldMaterialSummaryUnsafeReasons(materialSummaries),
  ]);
  if (unsafeText.length > 0) {
    return blockedSameTaskFieldMaterialPacket("same_task_field_material_packet_unsafe_text", taskId);
  }
  const ready = packetStatus === "ready_not_delivery_proof";
  return {
    schema: schema === O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
      ? O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
      : SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
    status: ready
      ? "ready_not_delivery_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_contract: schema === O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
      ? O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
      : SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    packet_status: packetStatus,
    task_id_source: taskIdSource,
    same_task_id_consumed: sameTaskIdConsumed,
    live_or_field_material_consumed: liveOrFieldMaterialConsumed,
    present_materials: presentMaterials,
    missing_materials: missingMaterials,
    sample_refs: sampleRefs,
    material_summaries: materialSummaries,
    route_csv_present: routeCsvPresent,
    keyframes_present: keyframesPresent,
    route_bag_or_rosbag_present: routeBagOrRosbagPresent,
    replay_jsonl_present: replayJsonlPresent,
    map_yaml_present: mapYamlPresent,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      sameTaskIdConsumed ? "" : "same_task_id_not_consumed",
      routeCsvPresent ? "" : "route_csv_missing",
      keyframesPresent ? "" : "keyframes_missing",
      routeBagOrRosbagPresent ? "" : "route_bag_or_rosbag_missing",
      replayJsonlPresent ? "" : "replay_jsonl_missing",
      ready ? "" : "same_task_field_material_packet_not_ready",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "same_task_field_material_packet_for_selected_task",
          "same_task_live_or_replay_route_execution_materials",
          "real_drop_off_completion_proof",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      field_materials_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function currentFieldEvidenceMaterialCandidateFromRemote(
  remote: JsonRecord,
): CurrentFieldEvidenceMaterialSourceResult | null {
  // current field evidence material 只读 O6 当前现场材料摘要，不下钻成 route execution success。
  const direct = asRecord(remote.current_field_evidence_material);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_current_field_evidence_material",
      source_path: "current_field_evidence_material",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence_manifest", "current_field_evidence_material");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.current_field_evidence_material",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "current_field_evidence_material");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.current_field_evidence_material",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence_ingest", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "current_field_evidence_material");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.current_field_evidence_material",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "current_field_evidence_material");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.current_field_evidence_material",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "current_field_evidence_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "current_field_evidence_material");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.current_field_evidence_material",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "current_field_evidence_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "current_field_evidence_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "current_field_evidence_material");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.current_field_evidence_material",
    };
  }
  return null;
}

function unsafeCurrentFieldEvidenceMaterialTextReason(value: unknown): string {
  // current field evidence 文本只能是短状态/标签/摘要，不能夹带 URL、路径、token 或 raw payload。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "current_field_evidence_material_unsafe_text";
  }
  return "";
}

function unsafeCurrentFieldEvidenceMaterialListReason(value: unknown, fieldName: string): string {
  // 材料列表只能是短字符串数组，避免把对象 payload 直接灌进 UI。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `current_field_evidence_material_unsafe_list:${fieldName}`;
}

function blockedCurrentFieldEvidenceMaterial(
  reason: string,
  taskId: string,
): O7ConsumerCurrentFieldEvidenceMaterialSummary {
  // 缺失或被拒绝时也返回完整结构，避免 UI 把缺字段误读成当前现场材料已就绪。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    material_status: "blocked_not_proven",
    task_id_source: "not_loaded",
    same_task_id_consumed: false,
    live_or_field_material_consumed: false,
    present_materials: [],
    missing_materials: [],
    camera_frame_observed: false,
    radar_scan_observed: false,
    map_material_observed: false,
    nav2_no_motion_path_generated: false,
    manual_gate_blocked_expected: false,
    blocked_reasons: [reason],
    next_required_evidence: ["current_field_evidence_material_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      current_field_materials_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function currentFieldEvidenceMaterialHardFailReason(
  summary: O7ConsumerCurrentFieldEvidenceMaterialSummary,
): string {
  // 坏 schema、危险 true、缺必填、unsafe text/list 和 proof scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(current_field_evidence_material_schema_mismatch|current_field_evidence_material_task_mismatch|current_field_evidence_material_dangerous_true|current_field_evidence_material_missing_required_fields|current_field_evidence_material_unsafe_text|current_field_evidence_material_unsafe_list|current_field_evidence_material_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function currentFieldEvidenceMaterialMaterialList(payload: JsonRecord | null, summary: JsonRecord | null): string[] {
  // current field evidence 的 present/missing 材料优先读显式列表，缺失时从基础布尔位兜底。
  if (Array.isArray(payload?.present_materials)) {
    return stringList(payload?.present_materials, 10);
  }
  const fallback = [
    asBoolean(summary?.camera_frame_observed ?? payload?.camera_frame_observed) ? "camera_frame" : "",
    asBoolean(summary?.radar_scan_observed ?? payload?.radar_scan_observed) ? "radar_scan" : "",
    asBoolean(summary?.map_material_observed ?? payload?.map_material_observed) ? "map_material" : "",
    asBoolean(summary?.nav2_no_motion_path_generated ?? payload?.nav2_no_motion_path_generated) ? "nav2_material" : "",
  ];
  return fallback.filter(Boolean);
}

function buildCurrentFieldEvidenceMaterialSummary(
  candidate: CurrentFieldEvidenceMaterialSourceResult | null,
  taskId: string,
): O7ConsumerCurrentFieldEvidenceMaterialSummary {
  // O7 只消费 current field evidence 的脱敏材料摘要，不把 support-only 状态外推成 route execution success。
  if (!candidate) {
    return blockedCurrentFieldEvidenceMaterial("current_field_evidence_material_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA && schema !== CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA) {
    return blockedCurrentFieldEvidenceMaterial("current_field_evidence_material_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedCurrentFieldEvidenceMaterial(
      `current_field_evidence_material_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE) {
    return blockedCurrentFieldEvidenceMaterial("current_field_evidence_material_proof_scope_mismatch", taskId);
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedCurrentFieldEvidenceMaterial("current_field_evidence_material_task_mismatch", taskId);
  }
  const presentMaterials = currentFieldEvidenceMaterialMaterialList(payload, null);
  const missingMaterials = Array.isArray(payload.missing_materials)
    ? stringList(payload.missing_materials, 10)
    : [];
  const blockedReasons = stringList(payload.blocked_reasons, 12);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const cameraFrameObserved = asBoolean(payload.camera_frame_observed ?? presentMaterials.includes("camera_frame"));
  const radarScanObserved = asBoolean(payload.radar_scan_observed ?? presentMaterials.includes("radar_scan"));
  const mapMaterialObserved = asBoolean(payload.map_material_observed ?? presentMaterials.includes("map_material"));
  const nav2NoMotionPathGenerated = asBoolean(
    payload.nav2_no_motion_path_generated ?? presentMaterials.includes("nav2_material"),
  );
  const manualGateBlockedExpected = asBoolean(payload.manual_gate_blocked_expected);
  const sameTaskIdConsumed = asBoolean(payload.same_task_id_consumed);
  const liveOrFieldMaterialConsumed = asBoolean(payload.live_or_field_material_consumed);
  const materialStatus = asString(
    payload.material_status ?? payload.current_field_evidence_status ?? payload.status,
    "blocked_not_proven",
  );
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const taskIdSource = asString(payload.task_id_source, "not_loaded");
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    rawString(payload.proof_scope) ? "" : "proof_scope",
    typeof payload.same_task_id_consumed === "boolean" ? "" : "same_task_id_consumed",
    typeof payload.live_or_field_material_consumed === "boolean" ? "" : "live_or_field_material_consumed",
    typeof payload.camera_frame_observed === "boolean" || presentMaterials.includes("camera_frame") ? "" : "camera_frame_observed",
    typeof payload.radar_scan_observed === "boolean" || presentMaterials.includes("radar_scan") ? "" : "radar_scan_observed",
    typeof payload.map_material_observed === "boolean" || presentMaterials.includes("map_material") ? "" : "map_material_observed",
    typeof payload.nav2_no_motion_path_generated === "boolean" || presentMaterials.includes("nav2_material")
      ? ""
      : "nav2_no_motion_path_generated",
    typeof payload.manual_gate_blocked_expected === "boolean" ? "" : "manual_gate_blocked_expected",
    Array.isArray(payload.present_materials) ? "" : "present_materials",
    Array.isArray(payload.missing_materials) ? "" : "missing_materials",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedCurrentFieldEvidenceMaterial(
      `current_field_evidence_material_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const unsafeList = aggregateDistinct([
    unsafeCurrentFieldEvidenceMaterialListReason(payload.present_materials, "present_materials"),
    unsafeCurrentFieldEvidenceMaterialListReason(payload.missing_materials, "missing_materials"),
    unsafeCurrentFieldEvidenceMaterialListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeCurrentFieldEvidenceMaterialListReason(payload.next_required_evidence, "next_required_evidence"),
  ]);
  if (unsafeList.length > 0) {
    return blockedCurrentFieldEvidenceMaterial(unsafeList[0] ?? "current_field_evidence_material_unsafe_list", taskId);
  }
  const unsafeText = aggregateDistinct([
    unsafeCurrentFieldEvidenceMaterialTextReason(packetStatus),
    unsafeCurrentFieldEvidenceMaterialTextReason(taskIdSource),
    unsafeCurrentFieldEvidenceMaterialTextReason(materialStatus),
    presentMaterials.map((value) => unsafeCurrentFieldEvidenceMaterialTextReason(value)),
    missingMaterials.map((value) => unsafeCurrentFieldEvidenceMaterialTextReason(value)),
    blockedReasons.map((value) => unsafeCurrentFieldEvidenceMaterialTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeCurrentFieldEvidenceMaterialTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedCurrentFieldEvidenceMaterial("current_field_evidence_material_unsafe_text", taskId);
  }
  const ready = packetStatus === "current_field_evidence_ready_not_route_execution_proof";
  return {
    schema: schema === O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA
      ? O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA
      : CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA,
    status: ready
      ? "current_field_evidence_ready_not_route_execution_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_contract: schema === O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA
      ? O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA
      : CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    material_status: materialStatus,
    task_id_source: taskIdSource,
    same_task_id_consumed: sameTaskIdConsumed,
    live_or_field_material_consumed: liveOrFieldMaterialConsumed,
    present_materials: presentMaterials,
    missing_materials: missingMaterials,
    camera_frame_observed: cameraFrameObserved,
    radar_scan_observed: radarScanObserved,
    map_material_observed: mapMaterialObserved,
    nav2_no_motion_path_generated: nav2NoMotionPathGenerated,
    manual_gate_blocked_expected: manualGateBlockedExpected,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      sameTaskIdConsumed ? "" : "same_task_id_not_consumed",
      liveOrFieldMaterialConsumed ? "" : "live_or_field_material_not_consumed",
      cameraFrameObserved ? "" : "camera_frame_not_observed",
      radarScanObserved ? "" : "radar_scan_not_observed",
      mapMaterialObserved ? "" : "map_material_not_observed",
      nav2NoMotionPathGenerated ? "" : "nav2_no_motion_path_not_generated",
      manualGateBlockedExpected ? "" : "manual_gate_not_blocked_as_expected",
      ready ? "" : "current_field_evidence_material_not_ready",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "current_field_evidence_material_for_selected_task",
          "camera_frame_for_selected_task",
          "radar_scan_for_selected_task",
          "map_material_for_selected_task",
          "nav2_material_for_selected_task",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      current_field_materials_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function localizationPathMaterialReadbackCandidateFromRemote(
  remote: JsonRecord,
): LocalizationPathMaterialReadbackSourceResult | null {
  // localization/path 材料允许来自 O6 detail 的固定白名单来源，但只消费已脱敏的只读 packet。
  const direct = asRecord(remote.localization_path_material_readback);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_localization_path_material_readback",
      source_path: "localization_path_material_readback",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence_manifest", "localization_path_material_readback");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.localization_path_material_readback",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "localization_path_material_readback");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.localization_path_material_readback",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence_ingest", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "localization_path_material_readback");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.localization_path_material_readback",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "localization_path_material_readback");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.localization_path_material_readback",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "localization_path_material_readback") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "localization_path_material_readback");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.localization_path_material_readback",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "localization_path_material_readback") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "localization_path_material_readback") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "localization_path_material_readback");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.localization_path_material_readback",
    };
  }
  return null;
}

function unsafeLocalizationPathMaterialReadbackTextReason(value: unknown): string {
  // localization/path readback 文本只允许短状态和 basename 级摘要，不能泄露 URL、路径、token 或原始响应。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("traceback") ||
    lowered.includes("response body") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "localization_path_material_readback_unsafe_text";
  }
  return "";
}

function unsafeLocalizationPathMaterialReadbackListReason(value: unknown, fieldName: string): string {
  // blocker / next evidence 列表必须保持短字符串数组，避免对象 payload 泄露到 UI。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `localization_path_material_readback_unsafe_list:${fieldName}`;
}

function blockedLocalizationPathMaterialReadback(
  reason: string,
  taskId: string,
): O7ConsumerLocalizationPathMaterialReadbackSummary {
  // 缺失或异常时仍返回完整 O7 schema，防止 UI 把空值误读成 same-run path 成功。
  return {
    schema: O7_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA,
    status: "blocked_not_proven",
    source_schema: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    material_status: "blocked_not_proven",
    task_id_source: "not_loaded",
    localization_path_material_bridge_present: false,
    same_run_localization_material_present: false,
    same_run_map_once_observed: false,
    same_run_amcl_pose_observed: false,
    same_run_localization_tf_map_to_odom: false,
    same_run_localization_tf_map_to_base_link: false,
    same_run_planner_server_active: false,
    same_run_path_generation_requested: false,
    same_run_path_generation_succeeded: false,
    same_run_path_generated: false,
    same_run_path_point_count: 0,
    same_run_path_proven: false,
    cross_run_clean_baseline_path_comparator_present: false,
    cross_run_clean_baseline_path_summary: null,
    blocked_reasons: [reason],
    next_required_evidence: ["localization_path_material_readback_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      same_run_localization_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    nav2_route_execution_success: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function localizationPathMaterialReadbackHardFailReason(
  summary: O7ConsumerLocalizationPathMaterialReadbackSummary,
): string {
  // 坏 schema、危险 true、缺必填、task mismatch、unsafe text/list 和 scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(localization_path_material_readback_schema_mismatch|localization_path_material_readback_task_mismatch|localization_path_material_readback_dangerous_true|localization_path_material_readback_missing_required_fields|localization_path_material_readback_unsafe_text|localization_path_material_readback_unsafe_list|localization_path_material_readback_proof_scope_mismatch|localization_path_material_readback_same_run_path_success_claimed)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildLocalizationPathMaterialReadbackSummary(
  candidate: LocalizationPathMaterialReadbackSourceResult | null,
  taskId: string,
): O7ConsumerLocalizationPathMaterialReadbackSummary {
  // O7 只消费 same-run localization/path 摘要，并明确 cross-run comparator 不能覆盖 same-run path false 结论。
  if (!candidate) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA && schema !== LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedLocalizationPathMaterialReadback(
      `localization_path_material_readback_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope ?? payload.evidence_boundary, "not_loaded");
  if (proofScope !== LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_proof_scope_mismatch", taskId);
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_task_mismatch", taskId);
  }
  const sourceSchema = asString(payload.source_schema ?? payload.schema, "not_loaded");
  if (sourceSchema !== O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA && sourceSchema !== LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_schema_mismatch", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons, 16);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const materialStatus = asString(payload.material_status ?? payload.status, "blocked_not_proven");
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const taskIdSource = asString(payload.task_id_source, "not_loaded");
  const sameRunPathPointCount = asNumber(payload.same_run_path_point_count);
  const crossRunSummary = asRecord(payload.cross_run_clean_baseline_path_summary);
  const crossRunPathPointCount = asNumber(crossRunSummary?.path_point_count);
  // O6 初版 worker 的 ready/status 与 TF 字段存在别名漂移；O7 在这里兼容读取，但最终只输出归一后的 O7 字段。
  const bridgeFieldPresent = typeof payload.localization_path_material_bridge_present === "boolean";
  const legacyBridgeReady =
    !bridgeFieldPresent &&
    packetStatus === "localization_path_material_readback_ready_not_route_execution_proof" &&
    payload.same_run_localization_material_present === true;
  const localizationPathMaterialBridgePresent = bridgeFieldPresent
    ? asBoolean(payload.localization_path_material_bridge_present)
    : legacyBridgeReady;
  const sameRunLocalizationTfMapToOdomPresent =
    typeof payload.same_run_localization_tf_map_to_odom === "boolean" ||
    typeof payload.same_run_tf_map_to_odom_observed === "boolean";
  const sameRunLocalizationTfMapToBaseLinkPresent =
    typeof payload.same_run_localization_tf_map_to_base_link === "boolean" ||
    typeof payload.same_run_tf_map_to_base_link_observed === "boolean";
  const sameRunLocalizationTfMapToOdom =
    typeof payload.same_run_localization_tf_map_to_odom === "boolean"
      ? asBoolean(payload.same_run_localization_tf_map_to_odom)
      : asBoolean(payload.same_run_tf_map_to_odom_observed);
  const sameRunLocalizationTfMapToBaseLink =
    typeof payload.same_run_localization_tf_map_to_base_link === "boolean"
      ? asBoolean(payload.same_run_localization_tf_map_to_base_link)
      : asBoolean(payload.same_run_tf_map_to_base_link_observed);
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    rawString(payload.proof_scope ?? payload.evidence_boundary) ? "" : "proof_scope",
    bridgeFieldPresent || legacyBridgeReady ? "" : "localization_path_material_bridge_present",
    typeof payload.same_run_localization_material_present === "boolean" ? "" : "same_run_localization_material_present",
    typeof payload.same_run_map_once_observed === "boolean" ? "" : "same_run_map_once_observed",
    typeof payload.same_run_amcl_pose_observed === "boolean" ? "" : "same_run_amcl_pose_observed",
    sameRunLocalizationTfMapToOdomPresent ? "" : "same_run_localization_tf_map_to_odom",
    sameRunLocalizationTfMapToBaseLinkPresent ? "" : "same_run_localization_tf_map_to_base_link",
    typeof payload.same_run_planner_server_active === "boolean" ? "" : "same_run_planner_server_active",
    typeof payload.same_run_path_generation_requested === "boolean" ? "" : "same_run_path_generation_requested",
    typeof payload.same_run_path_generation_succeeded === "boolean" ? "" : "same_run_path_generation_succeeded",
    typeof payload.same_run_path_generated === "boolean" ? "" : "same_run_path_generated",
    sameRunPathPointCount === null ? "same_run_path_point_count" : "",
    typeof payload.same_run_path_proven === "boolean" ? "" : "same_run_path_proven",
    typeof payload.cross_run_clean_baseline_path_comparator_present === "boolean" ? "" : "cross_run_clean_baseline_path_comparator_present",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedLocalizationPathMaterialReadback(
      `localization_path_material_readback_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const unsafeList = aggregateDistinct([
    unsafeLocalizationPathMaterialReadbackListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeLocalizationPathMaterialReadbackListReason(payload.next_required_evidence, "next_required_evidence"),
  ]);
  if (unsafeList.length > 0) {
    return blockedLocalizationPathMaterialReadback(
      unsafeList[0] ?? "localization_path_material_readback_unsafe_list",
      taskId,
    );
  }
  const unsafeText = aggregateDistinct([
    unsafeLocalizationPathMaterialReadbackTextReason(packetStatus),
    unsafeLocalizationPathMaterialReadbackTextReason(materialStatus),
    unsafeLocalizationPathMaterialReadbackTextReason(taskIdSource),
    unsafeLocalizationPathMaterialReadbackTextReason(sourceSchema),
    blockedReasons.map((value) => unsafeLocalizationPathMaterialReadbackTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeLocalizationPathMaterialReadbackTextReason(value)),
    crossRunSummary ? Object.values(crossRunSummary).map((value) => unsafeLocalizationPathMaterialReadbackTextReason(value)) : [],
  ]);
  if (unsafeText.length > 0) {
    return blockedLocalizationPathMaterialReadback("localization_path_material_readback_unsafe_text", taskId);
  }
  const sameRunPathGenerationSucceeded = asBoolean(payload.same_run_path_generation_succeeded);
  const sameRunPathGenerated = asBoolean(payload.same_run_path_generated);
  const sameRunPathProven = asBoolean(payload.same_run_path_proven);
  if (sameRunPathGenerationSucceeded || sameRunPathGenerated || sameRunPathProven || (sameRunPathPointCount ?? 0) > 0) {
    return blockedLocalizationPathMaterialReadback(
      "localization_path_material_readback_same_run_path_success_claimed",
      taskId,
    );
  }
  const comparatorPresent = asBoolean(payload.cross_run_clean_baseline_path_comparator_present);
  const crossRunComparatorSummary =
    comparatorPresent && crossRunSummary
      ? {
          status: asString(crossRunSummary.status, "cross_run_clean_baseline_path_comparator_ready"),
          path_generation_succeeded: asBoolean(crossRunSummary.path_generation_succeeded),
          path_generated: asBoolean(crossRunSummary.path_generated),
          path_point_count: crossRunPathPointCount ?? 0,
          same_run_override_allowed: false as const,
        }
      : null;
  const sameRunLocalizationMaterialPresent = asBoolean(payload.same_run_localization_material_present);
  const sameRunMapOnceObserved = asBoolean(payload.same_run_map_once_observed);
  const sameRunAmclPoseObserved = asBoolean(payload.same_run_amcl_pose_observed);
  const sameRunPlannerServerActive = asBoolean(payload.same_run_planner_server_active);
  const sameRunPathGenerationRequested = asBoolean(payload.same_run_path_generation_requested);
  const ready =
    LOCALIZATION_PATH_MATERIAL_READY_STATUSES.has(packetStatus) &&
    localizationPathMaterialBridgePresent &&
    sameRunLocalizationMaterialPresent &&
    sameRunMapOnceObserved &&
    sameRunAmclPoseObserved &&
    sameRunLocalizationTfMapToOdom &&
    sameRunLocalizationTfMapToBaseLink &&
    sameRunPlannerServerActive &&
    sameRunPathGenerationRequested;
  return {
    schema: O7_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA,
    status: ready
      ? "localization_path_material_ready_not_route_execution_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_schema: sourceSchema as O7ConsumerLocalizationPathMaterialReadbackSummary["source_schema"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    material_status: materialStatus,
    task_id_source: taskIdSource,
    localization_path_material_bridge_present: localizationPathMaterialBridgePresent,
    same_run_localization_material_present: sameRunLocalizationMaterialPresent,
    same_run_map_once_observed: sameRunMapOnceObserved,
    same_run_amcl_pose_observed: sameRunAmclPoseObserved,
    same_run_localization_tf_map_to_odom: sameRunLocalizationTfMapToOdom,
    same_run_localization_tf_map_to_base_link: sameRunLocalizationTfMapToBaseLink,
    same_run_planner_server_active: sameRunPlannerServerActive,
    same_run_path_generation_requested: sameRunPathGenerationRequested,
    same_run_path_generation_succeeded: false,
    same_run_path_generated: false,
    same_run_path_point_count: sameRunPathPointCount ?? 0,
    same_run_path_proven: false,
    cross_run_clean_baseline_path_comparator_present: comparatorPresent,
    cross_run_clean_baseline_path_summary: crossRunComparatorSummary,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      "nav2_route_execution_success_not_proven",
      ready ? "" : "localization_path_material_not_ready",
      localizationPathMaterialBridgePresent ? "" : "localization_path_material_bridge_not_present",
      sameRunLocalizationMaterialPresent ? "" : "same_run_localization_material_not_present",
      sameRunMapOnceObserved ? "" : "same_run_map_once_not_observed",
      sameRunAmclPoseObserved ? "" : "same_run_amcl_pose_not_observed",
      sameRunLocalizationTfMapToOdom ? "" : "same_run_localization_tf_map_to_odom_not_observed",
      sameRunLocalizationTfMapToBaseLink ? "" : "same_run_localization_tf_map_to_base_link_not_observed",
      sameRunPlannerServerActive ? "" : "same_run_planner_server_not_active",
      sameRunPathGenerationRequested ? "" : "same_run_path_generation_not_requested",
      comparatorPresent ? "" : "cross_run_clean_baseline_path_comparator_missing",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "localization_path_material_readback_for_selected_task",
          "current_same_run_nav2_path_generation_result",
          "real_live_nav2_route_execution_result",
          "delivery_record_or_operator_dropoff_confirmation",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      same_run_localization_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    nav2_route_execution_success: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function cleanBaselineNav2PathMaterialCandidateFromRemote(
  remote: JsonRecord,
): CleanBaselineNav2PathMaterialSourceResult | null {
  // clean baseline 材料只读 O6 脱敏摘要，不把 no-motion 规划前置材料误读成真实路线执行。
  const direct = asRecord(remote.clean_baseline_nav2_path_material);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_clean_baseline_nav2_path_material",
      source_path: "clean_baseline_nav2_path_material",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence_manifest", "clean_baseline_nav2_path_material");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.clean_baseline_nav2_path_material",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "clean_baseline_nav2_path_material");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.clean_baseline_nav2_path_material",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence_ingest", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "clean_baseline_nav2_path_material");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.clean_baseline_nav2_path_material",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "clean_baseline_nav2_path_material");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.clean_baseline_nav2_path_material",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "clean_baseline_nav2_path_material");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.clean_baseline_nav2_path_material",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "clean_baseline_nav2_path_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "clean_baseline_nav2_path_material");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.clean_baseline_nav2_path_material",
    };
  }
  return null;
}

function unsafeCleanBaselineNav2PathMaterialTextReason(value: unknown): string {
  // clean baseline 文本只允许短状态/摘要，不能带 URL、路径、token、traceback 或原始 payload。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.includes("traceback") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "clean_baseline_nav2_path_material_unsafe_text";
  }
  return "";
}

function unsafeCleanBaselineNav2PathMaterialListReason(value: unknown, fieldName: string): string {
  // blocker / next evidence / root cause 列表必须是短字符串数组，避免对象 payload 透传到 UI。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `clean_baseline_nav2_path_material_unsafe_list:${fieldName}`;
}

function blockedCleanBaselineNav2PathMaterial(
  reason: string,
  taskId: string,
): O7ConsumerCleanBaselineNav2PathMaterialSummary {
  // 缺失或被拒绝时仍返回完整 contract，避免 UI 把 no-motion 材料误读成已通过。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    material_status: "blocked_not_proven",
    task_id_source: "not_loaded",
    first_attempt_status: "blocked_not_proven",
    first_failure_reason: "blocked_not_proven",
    first_failure_root_cause: "blocked_not_proven",
    retry_status: "blocked_not_proven",
    path_generation_succeeded: false,
    path_generated: false,
    path_point_count: 0,
    planner_server_active: false,
    managed_runtime_started: false,
    managed_runtime_cleanup_ok: false,
    initialpose_published: false,
    amcl_pose_observed: false,
    map_server_active: false,
    amcl_active: false,
    cleanup_readback_clean: false,
    blocked_reasons: [reason],
    next_required_evidence: ["clean_baseline_nav2_path_material_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function cleanBaselineNav2PathMaterialHardFailReason(
  summary: O7ConsumerCleanBaselineNav2PathMaterialSummary,
): string {
  // 坏 schema、危险 true、缺必填、unsafe text/list 和 proof scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(clean_baseline_nav2_path_material_schema_mismatch|clean_baseline_nav2_path_material_task_mismatch|clean_baseline_nav2_path_material_dangerous_true|clean_baseline_nav2_path_material_missing_required_fields|clean_baseline_nav2_path_material_unsafe_text|clean_baseline_nav2_path_material_unsafe_list|clean_baseline_nav2_path_material_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildCleanBaselineNav2PathMaterialSummary(
  candidate: CleanBaselineNav2PathMaterialSourceResult | null,
  taskId: string,
): O7ConsumerCleanBaselineNav2PathMaterialSummary {
  // O7 只消费 clean-baseline no-motion path 摘要，不把重试成功升级成真实路线执行或送达。
  if (!candidate) {
    return blockedCleanBaselineNav2PathMaterial("clean_baseline_nav2_path_material_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA && schema !== CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA) {
    return blockedCleanBaselineNav2PathMaterial("clean_baseline_nav2_path_material_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedCleanBaselineNav2PathMaterial(
      `clean_baseline_nav2_path_material_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE) {
    return blockedCleanBaselineNav2PathMaterial("clean_baseline_nav2_path_material_proof_scope_mismatch", taskId);
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedCleanBaselineNav2PathMaterial("clean_baseline_nav2_path_material_task_mismatch", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons, 12);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const rootCauses = stringList(payload.first_failure_root_causes ?? payload.root_causes, 6);
  const firstAttemptStatus = asString(payload.first_attempt_status, "blocked_not_proven");
  const firstFailureReason = asString(payload.first_failure_reason ?? payload.failure_reason, "blocked_not_proven");
  const firstFailureRootCause = rootCauses[0] ?? asString(payload.first_failure_root_cause, "blocked_not_proven");
  const retryStatus = asString(payload.retry_status, "blocked_not_proven");
  const materialStatus = asString(
    payload.material_status ?? payload.clean_baseline_nav2_path_material_status ?? payload.status,
    "blocked_not_proven",
  );
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const taskIdSource = asString(payload.task_id_source, "not_loaded");
  const pathPointCount = asNumber(payload.path_point_count);
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    rawString(payload.proof_scope) ? "" : "proof_scope",
    rawString(payload.first_attempt_status) ? "" : "first_attempt_status",
    rawString(payload.first_failure_reason ?? payload.failure_reason) ? "" : "first_failure_reason",
    rawString(payload.retry_status) ? "" : "retry_status",
    typeof payload.path_generation_succeeded === "boolean" ? "" : "path_generation_succeeded",
    typeof payload.path_generated === "boolean" ? "" : "path_generated",
    pathPointCount === null ? "path_point_count" : "",
    typeof payload.planner_server_active === "boolean" ? "" : "planner_server_active",
    typeof payload.managed_runtime_started === "boolean" ? "" : "managed_runtime_started",
    typeof payload.managed_runtime_cleanup_ok === "boolean" ? "" : "managed_runtime_cleanup_ok",
    typeof payload.initialpose_published === "boolean" ? "" : "initialpose_published",
    typeof payload.amcl_pose_observed === "boolean" ? "" : "amcl_pose_observed",
    typeof payload.map_server_active === "boolean" ? "" : "map_server_active",
    typeof payload.amcl_active === "boolean" ? "" : "amcl_active",
    typeof payload.cleanup_readback_clean === "boolean" ? "" : "cleanup_readback_clean",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedCleanBaselineNav2PathMaterial(
      `clean_baseline_nav2_path_material_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const unsafeList = aggregateDistinct([
    unsafeCleanBaselineNav2PathMaterialListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeCleanBaselineNav2PathMaterialListReason(payload.next_required_evidence, "next_required_evidence"),
    unsafeCleanBaselineNav2PathMaterialListReason(payload.first_failure_root_causes ?? payload.root_causes, "first_failure_root_causes"),
  ]);
  if (unsafeList.length > 0) {
    return blockedCleanBaselineNav2PathMaterial(
      unsafeList[0] ?? "clean_baseline_nav2_path_material_unsafe_list",
      taskId,
    );
  }
  const unsafeText = aggregateDistinct([
    unsafeCleanBaselineNav2PathMaterialTextReason(packetStatus),
    unsafeCleanBaselineNav2PathMaterialTextReason(taskIdSource),
    unsafeCleanBaselineNav2PathMaterialTextReason(materialStatus),
    unsafeCleanBaselineNav2PathMaterialTextReason(firstAttemptStatus),
    unsafeCleanBaselineNav2PathMaterialTextReason(firstFailureReason),
    unsafeCleanBaselineNav2PathMaterialTextReason(firstFailureRootCause),
    unsafeCleanBaselineNav2PathMaterialTextReason(retryStatus),
    blockedReasons.map((value) => unsafeCleanBaselineNav2PathMaterialTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeCleanBaselineNav2PathMaterialTextReason(value)),
    rootCauses.map((value) => unsafeCleanBaselineNav2PathMaterialTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedCleanBaselineNav2PathMaterial("clean_baseline_nav2_path_material_unsafe_text", taskId);
  }
  const ready = packetStatus === "clean_baseline_nav2_path_material_ready_not_route_execution_proof";
  const pathGenerationSucceeded = asBoolean(payload.path_generation_succeeded);
  const pathGenerated = asBoolean(payload.path_generated);
  const plannerServerActive = asBoolean(payload.planner_server_active);
  const managedRuntimeStarted = asBoolean(payload.managed_runtime_started);
  const managedRuntimeCleanupOk = asBoolean(payload.managed_runtime_cleanup_ok);
  const initialposePublished = asBoolean(payload.initialpose_published);
  const amclPoseObserved = asBoolean(payload.amcl_pose_observed);
  const mapServerActive = asBoolean(payload.map_server_active);
  const amclActive = asBoolean(payload.amcl_active);
  const cleanupReadbackClean = asBoolean(payload.cleanup_readback_clean);
  return {
    schema: schema === O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA
      ? O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA
      : CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA,
    status: ready
      ? "clean_baseline_nav2_path_material_ready_not_route_execution_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_contract: schema === O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA
      ? O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA
      : CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    material_status: materialStatus,
    task_id_source: taskIdSource,
    first_attempt_status: firstAttemptStatus,
    first_failure_reason: firstFailureReason,
    first_failure_root_cause: firstFailureRootCause,
    retry_status: retryStatus,
    path_generation_succeeded: pathGenerationSucceeded,
    path_generated: pathGenerated,
    path_point_count: pathPointCount ?? 0,
    planner_server_active: plannerServerActive,
    managed_runtime_started: managedRuntimeStarted,
    managed_runtime_cleanup_ok: managedRuntimeCleanupOk,
    initialpose_published: initialposePublished,
    amcl_pose_observed: amclPoseObserved,
    map_server_active: mapServerActive,
    amcl_active: amclActive,
    cleanup_readback_clean: cleanupReadbackClean,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      ready ? "" : "clean_baseline_nav2_path_material_not_ready",
      plannerServerActive ? "" : "planner_server_not_active",
      managedRuntimeStarted ? "" : "managed_runtime_not_started",
      managedRuntimeCleanupOk ? "" : "managed_runtime_cleanup_not_ok",
      initialposePublished ? "" : "initialpose_not_published",
      amclPoseObserved ? "" : "amcl_pose_not_observed",
      mapServerActive ? "" : "map_server_not_active",
      amclActive ? "" : "amcl_not_active",
      cleanupReadbackClean ? "" : "cleanup_readback_not_clean",
      pathGenerationSucceeded ? "" : "path_generation_not_succeeded",
      pathGenerated ? "" : "path_not_generated",
      (pathPointCount ?? 0) > 0 ? "" : "path_point_count_not_positive",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "clean_baseline_nav2_path_material_for_selected_task",
          "real_live_nav2_route_execution_result",
          "delivery_record_or_operator_dropoff_confirmation",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskRouteExecutionMaterialPacketCandidateFromRemote(
  remote: JsonRecord,
): SameTaskRouteExecutionMaterialPacketSourceResult | null {
  // route execution material packet 只读 O6/O6-first 摘要，不从子 readiness 自行拼 route success。
  const direct = asRecord(remote.same_task_route_execution_material_packet);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_same_task_route_execution_material_packet",
      source_path: "same_task_route_execution_material_packet",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence_manifest", "same_task_route_execution_material_packet");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.same_task_route_execution_material_packet",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "same_task_route_execution_material_packet");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.same_task_route_execution_material_packet",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence_ingest", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "same_task_route_execution_material_packet");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.same_task_route_execution_material_packet",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "same_task_route_execution_material_packet");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.same_task_route_execution_material_packet",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "same_task_route_execution_material_packet");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.same_task_route_execution_material_packet",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "same_task_route_execution_material_packet") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "same_task_route_execution_material_packet");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.same_task_route_execution_material_packet",
    };
  }
  return null;
}

function unsafeSameTaskRouteExecutionMaterialPacketTextReason(value: unknown): string {
  // packet 文本只能是状态、来源和 basename 级摘要，不能夹带路径、URL、token 或 raw payload。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "same_task_route_execution_material_packet_unsafe_text";
  }
  return "";
}

function unsafeSameTaskRouteExecutionMaterialPacketListReason(value: unknown, fieldName: string): string {
  // blocked/next/source/material 列表必须是短字符串数组，避免对象 payload 进入 UI。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `same_task_route_execution_material_packet_unsafe_list:${fieldName}`;
}

function normalizeRouteExecutionMaterialKey(value: string): string {
  // 上游可能使用旧别名；O7 展示统一成 route execution material packet 的材料键。
  const normalized = normalizeSameTaskFieldMaterialKey(value.replace(/\s+/g, "_"));
  if (normalized === "route_execution" || normalized === "route_execution_result_json") {
    return "route_execution_result";
  }
  if (normalized === "nav2_goal" || normalized === "nav2_result") {
    return "nav2_goal_execution";
  }
  if (normalized === "pose_progress" || normalized === "route_bag_pose_progress_replay") {
    return "pose_progress_replay";
  }
  if (normalized === "route_replay" || normalized === "replay_jsonl") {
    return "route_replay_jsonl";
  }
  return normalized;
}

function normalizeRouteExecutionMaterialTokenList(value: unknown, limit = 10): string[] {
  // operator 只需要材料标签，不能把任意说明对象当成材料展示。
  return stringList(value, limit).map((item) => normalizeRouteExecutionMaterialKey(item));
}

function sameTaskRouteExecutionMaterialSummaryRecord(payload: JsonRecord | null): JsonRecord | null {
  // 新旧 O6 shape 都兼容：优先 material_summaries，旧 sample_refs dict 只作为 per-material 摘要来源。
  const preferred =
    asRecord(payload?.material_summaries) ??
    asRecord(payload?.material_sample_refs) ??
    asRecord(payload?.sample_ref_summaries);
  if (preferred) {
    return preferred;
  }
  const legacySampleRefs = payload?.sample_refs;
  return Array.isArray(legacySampleRefs) ? null : asRecord(legacySampleRefs);
}

function sameTaskRouteExecutionMaterialSummaryEntry(value: unknown) {
  // 单个执行材料只展示状态、basename、短 hash 和少量 sample refs，不回显原始路径或 payload。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const sampleRefs = stringList(record.sample_refs, 6).map((item) => safePathToken(item));
  const basename = safePathToken(record.basename ?? sampleRefs[0] ?? "not_loaded");
  return {
    present: asBoolean(record.present),
    status: asString(record.status, asBoolean(record.present) ? "present" : "missing"),
    basename: basename || "not_loaded",
    size_bytes: asNumber(record.size_bytes),
    sha256_prefix: asString(record.sha256_prefix, "not_loaded"),
    sample_refs: sampleRefs,
    count: asNumber(record.count),
  };
}

function sameTaskRouteExecutionMaterialSummaries(payload: JsonRecord | null) {
  const source = sameTaskRouteExecutionMaterialSummaryRecord(payload);
  const sameTaskFieldMaterialPacket =
    sameTaskRouteExecutionMaterialSummaryEntry(source?.same_task_field_material_packet ?? source?.field_material_packet) ??
    undefined;
  const routeExecutionResult =
    sameTaskRouteExecutionMaterialSummaryEntry(source?.route_execution_result ?? source?.route_execution) ?? undefined;
  const nav2GoalExecution =
    sameTaskRouteExecutionMaterialSummaryEntry(source?.nav2_goal_execution ?? source?.nav2_goal ?? source?.nav2_result) ??
    undefined;
  const poseProgressReplay =
    sameTaskRouteExecutionMaterialSummaryEntry(
      source?.pose_progress_replay ?? source?.pose_progress ?? source?.route_bag_pose_progress_replay,
    ) ?? undefined;
  const routeReplayJsonl =
    sameTaskRouteExecutionMaterialSummaryEntry(source?.route_replay_jsonl ?? source?.route_replay ?? source?.replay_jsonl) ??
    undefined;
  const routeBagOrRosbag =
    sameTaskRouteExecutionMaterialSummaryEntry(source?.route_bag_or_rosbag ?? source?.route_bag ?? source?.rosbag) ??
    undefined;
  return {
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    route_execution_result: routeExecutionResult,
    nav2_goal_execution: nav2GoalExecution,
    pose_progress_replay: poseProgressReplay,
    route_replay_jsonl: routeReplayJsonl,
    route_bag_or_rosbag: routeBagOrRosbag,
  };
}

function sameTaskRouteExecutionMaterialTopLevelSampleRefs(payload: JsonRecord | null): string[] {
  // 新 packet 的 top-level sample_refs 是 list；旧 dict shape 则从材料摘要汇总 basename refs。
  if (Array.isArray(payload?.sample_refs)) {
    return stringList(payload?.sample_refs, 10).map((value) => safePathToken(value));
  }
  const summaries = sameTaskRouteExecutionMaterialSummaries(payload);
  return aggregateDistinct([
    summaries.same_task_field_material_packet?.sample_refs ?? [],
    summaries.route_execution_result?.sample_refs ?? [],
    summaries.nav2_goal_execution?.sample_refs ?? [],
    summaries.pose_progress_replay?.sample_refs ?? [],
    summaries.route_replay_jsonl?.sample_refs ?? [],
    summaries.route_bag_or_rosbag?.sample_refs ?? [],
  ]).slice(0, 10);
}

function sameTaskRouteExecutionMaterialSummaryUnsafeReasons(
  summaries: ReturnType<typeof sameTaskRouteExecutionMaterialSummaries>,
): string[] {
  // per-material 摘要中的 status/basename/hash/sample refs 全部复用 packet 安全扫描。
  return aggregateDistinct(
    Object.values(summaries).flatMap((summary) => {
      if (!summary) {
        return [];
      }
      return [
        unsafeSameTaskRouteExecutionMaterialPacketTextReason(summary.status),
        unsafeSameTaskRouteExecutionMaterialPacketTextReason(summary.basename),
        unsafeSameTaskRouteExecutionMaterialPacketTextReason(summary.sha256_prefix),
        ...summary.sample_refs.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
      ];
    }),
  );
}

function routeExecutionResultPacketSummary(
  payload: JsonRecord,
  summaries: ReturnType<typeof sameTaskRouteExecutionMaterialSummaries>,
) {
  // O6 可以给专用 route_execution_result_summary；否则从材料摘要和状态字段派生只读展示。
  const record =
    asRecord(payload.route_execution_result_summary) ??
    asRecord(payload.route_execution_summary) ??
    null;
  const material = summaries.route_execution_result;
  return {
    status: asString(record?.status ?? payload.route_execution_result_status ?? material?.status, "blocked_not_proven"),
    source: asString(record?.source ?? payload.route_execution_source ?? "not_loaded", "not_loaded"),
    sample_refs: stringList(record?.sample_refs ?? material?.sample_refs ?? [], 6).map((item) => safePathToken(item)),
    result_count: asNumber(record?.result_count ?? record?.count ?? material?.count),
    nav2_goal_status: asString(record?.nav2_goal_status ?? payload.nav2_goal_execution_status, "blocked_not_proven"),
    delivery_result_status: asString(record?.delivery_result_status ?? payload.delivery_result_status, "blocked_not_proven"),
  };
}

function poseProgressReplayTimelinePacketSummary(
  payload: JsonRecord,
  summaries: ReturnType<typeof sameTaskRouteExecutionMaterialSummaries>,
) {
  // 位姿/回放 timeline 只暴露样本数、frame count、位移和短 refs，不暴露原始轨迹或 ROS payload。
  const record =
    asRecord(payload.pose_progress_replay_timeline_summary) ??
    asRecord(payload.pose_progress_timeline_summary) ??
    asRecord(payload.replay_timeline_summary) ??
    null;
  const material = summaries.pose_progress_replay ?? summaries.route_replay_jsonl;
  return {
    status: asString(record?.status ?? payload.pose_progress_replay_status ?? material?.status, "blocked_not_proven"),
    source: asString(record?.source ?? payload.pose_progress_source ?? "not_loaded", "not_loaded"),
    sample_refs: stringList(record?.sample_refs ?? material?.sample_refs ?? [], 6).map((item) => safePathToken(item)),
    pose_sample_count: asNumber(record?.pose_sample_count ?? material?.count),
    replay_frame_count: asNumber(record?.replay_frame_count ?? record?.frame_count),
    nonzero_pose_progress_observed: asBoolean(
      record?.nonzero_pose_progress_observed ?? payload.nonzero_pose_progress_observed,
    ),
    displacement_m: asNumber(record?.displacement_m ?? payload.displacement_m),
    timeline_span_ms: asNumber(record?.timeline_span_ms ?? record?.time_span_ms),
  };
}

function blockedSameTaskRouteExecutionMaterialPacket(
  reason: string,
  taskId: string,
): O7ConsumerSameTaskRouteExecutionMaterialPacketSummary {
  // 缺失或被拒绝时也返回完整 packet 结构，避免 UI 通过 undefined 推断材料已就绪。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    packet_status: "blocked_not_proven",
    task_id_source: "not_loaded",
    same_task_id_consumed: false,
    route_execution_material_consumed: false,
    live_or_field_command_evidence_present: false,
    delivery_or_operator_material_consumed: false,
    route_execution_credit_candidate: false,
    credit_support_only_reason: "blocked_not_proven",
    credit_required_evidence: ["same_task_route_execution_material_packet_for_selected_task"],
    same_task_field_material_packet_status: "blocked_not_proven",
    present_materials: [],
    missing_materials: [],
    source_sections: [],
    sample_refs: [],
    material_summaries: {},
    route_execution_result_summary: {
      status: "blocked_not_proven",
      source: "not_loaded",
      sample_refs: [],
      result_count: null,
      nav2_goal_status: "blocked_not_proven",
      delivery_result_status: "blocked_not_proven",
    },
    pose_progress_replay_timeline_summary: {
      status: "blocked_not_proven",
      source: "not_loaded",
      sample_refs: [],
      pose_sample_count: null,
      replay_frame_count: null,
      nonzero_pose_progress_observed: false,
      displacement_m: null,
      timeline_span_ms: null,
    },
    blocked_reasons: [reason],
    next_required_evidence: ["same_task_route_execution_material_packet_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_execution_materials_connected: false,
      live_nav2_route_execution_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskRouteExecutionMaterialPacketHardFailReason(
  summary: O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
): string {
  // 坏 schema、危险 true、缺必填、unsafe text/list 和 proof scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(same_task_route_execution_material_packet_schema_mismatch|same_task_route_execution_material_packet_task_mismatch|same_task_route_execution_material_packet_dangerous_true|same_task_route_execution_material_packet_missing_required_fields|same_task_route_execution_material_packet_unsafe_text|same_task_route_execution_material_packet_unsafe_list|same_task_route_execution_material_packet_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildSameTaskRouteExecutionMaterialPacketSummary(
  candidate: SameTaskRouteExecutionMaterialPacketSourceResult | null,
  taskId: string,
): O7ConsumerSameTaskRouteExecutionMaterialPacketSummary {
  // O7 只信任 O6 顶层 status 判断 packet ready；子材料摘要只用于解释 present/missing 和下一步证据。
  if (!candidate) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      "same_task_route_execution_material_packet_missing",
      taskId,
    );
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA && schema !== SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      "same_task_route_execution_material_packet_schema_mismatch",
      taskId,
    );
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      `same_task_route_execution_material_packet_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      "same_task_route_execution_material_packet_proof_scope_mismatch",
      taskId,
    );
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      "same_task_route_execution_material_packet_task_mismatch",
      taskId,
    );
  }
  const unsafeList = aggregateDistinct([
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.present_materials, "present_materials"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.missing_materials, "missing_materials"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.source_sections, "source_sections"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.sample_refs, "sample_refs"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.credit_required_evidence, "credit_required_evidence"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeSameTaskRouteExecutionMaterialPacketListReason(payload.next_required_evidence, "next_required_evidence"),
  ]);
  if (unsafeList.length > 0) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      unsafeList[0] ?? "same_task_route_execution_material_packet_unsafe_list",
      taskId,
    );
  }

  const materialSummaries = sameTaskRouteExecutionMaterialSummaries(payload);
  const sampleRefs = sameTaskRouteExecutionMaterialTopLevelSampleRefs(payload);
  const presentMaterials = normalizeRouteExecutionMaterialTokenList(payload.present_materials);
  const missingMaterials = normalizeRouteExecutionMaterialTokenList(payload.missing_materials);
  const blockedReasons = stringList(payload.blocked_reasons, 12);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const creditRequiredEvidence = stringList(payload.credit_required_evidence, 12);
  const sourceSections = stringList(payload.source_sections ?? payload.source_section_names, 10);
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const taskIdSource = asString(payload.task_id_source, "not_loaded");
  const sameTaskIdConsumed = asBoolean(payload.same_task_id_consumed);
  const routeExecutionMaterialConsumed = asBoolean(
    payload.route_execution_material_consumed ?? payload.live_or_replay_route_execution_material_consumed,
  );
  const liveOrFieldCommandEvidencePresent = asBoolean(payload.live_or_field_command_evidence_present);
  const deliveryOrOperatorMaterialConsumed = asBoolean(payload.delivery_or_operator_material_consumed);
  const routeExecutionCreditCandidate = asBoolean(payload.route_execution_credit_candidate);
  const rawCreditSupportOnlyReason = rawString(payload.credit_support_only_reason);
  const creditSupportOnlyReason = routeExecutionCreditCandidate
    ? rawCreditSupportOnlyReason
    : asString(payload.credit_support_only_reason, "blocked_not_proven");
  const sameTaskFieldMaterialPacketStatus = asString(
    payload.same_task_field_material_packet_status ??
      materialSummaries.same_task_field_material_packet?.status,
    "blocked_not_proven",
  );
  const sampleRefsShapeValid =
    Array.isArray(payload.sample_refs) ||
    Boolean(sameTaskRouteExecutionMaterialSummaryRecord(payload));
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.task_id_source) ? "" : "task_id_source",
    typeof payload.same_task_id_consumed === "boolean" ? "" : "same_task_id_consumed",
    typeof (payload.route_execution_material_consumed ?? payload.live_or_replay_route_execution_material_consumed) === "boolean"
      ? ""
      : "route_execution_material_consumed",
    typeof payload.live_or_field_command_evidence_present === "boolean"
      ? ""
      : "live_or_field_command_evidence_present",
    typeof payload.delivery_or_operator_material_consumed === "boolean"
      ? ""
      : "delivery_or_operator_material_consumed",
    typeof payload.route_execution_credit_candidate === "boolean"
      ? ""
      : "route_execution_credit_candidate",
    routeExecutionCreditCandidate || rawCreditSupportOnlyReason ? "" : "credit_support_only_reason",
    Array.isArray(payload.credit_required_evidence) ? "" : "credit_required_evidence",
    rawString(payload.same_task_field_material_packet_status ?? materialSummaries.same_task_field_material_packet?.status)
      ? ""
      : "same_task_field_material_packet_status",
    Array.isArray(payload.present_materials) ? "" : "present_materials",
    Array.isArray(payload.missing_materials) ? "" : "missing_materials",
    sampleRefsShapeValid ? "" : "sample_refs_or_material_summaries",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      `same_task_route_execution_material_packet_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }

  const routeExecutionSummary = routeExecutionResultPacketSummary(payload, materialSummaries);
  const poseProgressSummary = poseProgressReplayTimelinePacketSummary(payload, materialSummaries);
  const unsafeText = aggregateDistinct([
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(payload.status),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(payload.task_id_source),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(sameTaskFieldMaterialPacketStatus),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(creditSupportOnlyReason),
    presentMaterials.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    missingMaterials.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    sourceSections.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    sampleRefs.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    creditRequiredEvidence.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    blockedReasons.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    sameTaskRouteExecutionMaterialSummaryUnsafeReasons(materialSummaries),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(routeExecutionSummary.status),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(routeExecutionSummary.source),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(routeExecutionSummary.nav2_goal_status),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(routeExecutionSummary.delivery_result_status),
    routeExecutionSummary.sample_refs.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(poseProgressSummary.status),
    unsafeSameTaskRouteExecutionMaterialPacketTextReason(poseProgressSummary.source),
    poseProgressSummary.sample_refs.map((value) => unsafeSameTaskRouteExecutionMaterialPacketTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedSameTaskRouteExecutionMaterialPacket(
      "same_task_route_execution_material_packet_unsafe_text",
      taskId,
    );
  }

  const ready = packetStatus === "route_execution_material_ready_not_delivery_proof";
  return {
    schema: schema === O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA
      ? O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA
      : SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
    status: ready
      ? "route_execution_material_ready_not_delivery_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_contract: schema === O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA
      ? O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA
      : SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    packet_status: packetStatus,
    task_id_source: taskIdSource,
    same_task_id_consumed: sameTaskIdConsumed,
    route_execution_material_consumed: routeExecutionMaterialConsumed,
    live_or_field_command_evidence_present: liveOrFieldCommandEvidencePresent,
    delivery_or_operator_material_consumed: deliveryOrOperatorMaterialConsumed,
    route_execution_credit_candidate: routeExecutionCreditCandidate,
    credit_support_only_reason: creditSupportOnlyReason,
    credit_required_evidence: creditRequiredEvidence.length
      ? creditRequiredEvidence
      : [
          "real_live_nav2_route_execution_result",
          "delivery_record_or_operator_dropoff_confirmation",
          "operator_confirmation_for_selected_task",
        ],
    same_task_field_material_packet_status: sameTaskFieldMaterialPacketStatus,
    present_materials: presentMaterials,
    missing_materials: missingMaterials,
    source_sections: sourceSections,
    sample_refs: sampleRefs,
    material_summaries: materialSummaries,
    route_execution_result_summary: routeExecutionSummary,
    pose_progress_replay_timeline_summary: poseProgressSummary,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      sameTaskIdConsumed ? "" : "same_task_id_not_consumed",
      routeExecutionMaterialConsumed ? "" : "route_execution_material_not_consumed",
      liveOrFieldCommandEvidencePresent ? "" : "live_or_field_command_evidence_missing",
      deliveryOrOperatorMaterialConsumed ? "" : "delivery_or_operator_material_missing",
      routeExecutionCreditCandidate ? "" : `credit_support_only:${creditSupportOnlyReason}`,
      ready ? "" : "same_task_route_execution_material_packet_not_ready",
      presentMaterials.includes("route_execution_result") ? "" : "route_execution_result_missing",
      presentMaterials.includes("pose_progress_replay") ? "" : "pose_progress_replay_missing",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "same_task_route_execution_material_packet_for_selected_task",
          "real_live_nav2_route_execution_result",
          "route_pose_progress_replay_for_selected_task",
          "delivery_record_or_operator_dropoff_confirmation",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      route_execution_materials_connected: false,
      live_nav2_route_execution_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskMissionEvidenceGateCandidateFromRemote(
  remote: JsonRecord,
): SameTaskMissionEvidenceGateSourceResult | null {
  // same-task gate 只读取 O6 已归一化摘要，O7 不回看 raw cloud terminal result 或 route payload。
  const direct = asRecord(remote.same_task_mission_evidence_gate);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_same_task_mission_evidence_gate",
      source_path: "same_task_mission_evidence_gate",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence_manifest", "same_task_mission_evidence_gate");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.same_task_mission_evidence_gate",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "same_task_mission_evidence_gate");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.same_task_mission_evidence_gate",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence_ingest", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_motion_evidence_packet", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence_ingest", "field_motion_evidence_packet", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "same_task_mission_evidence_gate");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.same_task_mission_evidence_gate",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "artifact_bundle", "field_motion_evidence_packet", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "same_task_mission_evidence_gate");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.same_task_mission_evidence_gate",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "same_task_mission_evidence_gate");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.same_task_mission_evidence_gate",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "artifact_bundle_readiness", "field_motion_evidence_packet", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "same_task_mission_evidence_gate") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "same_task_mission_evidence_gate");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.same_task_mission_evidence_gate",
    };
  }
  return null;
}

function unsafeSameTaskMissionEvidenceGateTextReason(value: unknown): string {
  // gate 文本只能是短状态、schema 或来源标签，不能夹带 URL、token、路径、base64 或控制 topic。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "same_task_mission_evidence_gate_unsafe_text";
  }
  return "";
}

function sameTaskMissionArtifactDeltaSummary(value: unknown): string {
  // 新 gate 允许 mission_artifact_delta 升级成结构化对象；O7 仍只抽一行短摘要，不把整段对象透传到 UI。
  const text = rawString(value);
  if (text) {
    return text;
  }
  const record = asRecord(value);
  if (!record) {
    return "blocked_not_proven";
  }
  return asString(record.summary ?? record.status ?? record.kind ?? record.mission_artifact_delta, "blocked_not_proven");
}

function sameTaskMissionArtifactDeltaRecord(value: unknown): JsonRecord | null {
  // 旧 payload 是字符串；新 payload 可能把 delta 明细放进对象。这里统一抽象成可选 record。
  return asRecord(value);
}

function unsafeSameTaskMissionEvidenceGateListReason(value: unknown, fieldName: string): string {
  // blocked/next 列表是 operator 下一步依据，不能把对象、数字或嵌套 payload 当成安全材料。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `same_task_mission_evidence_gate_unsafe_list:${fieldName}`;
}

function blockedSameTaskMissionEvidenceGate(
  reason: string,
  taskId: string,
): O7ConsumerSameTaskMissionEvidenceGateSummary {
  // 缺失或被拒绝时也返回完整 gate，避免 UI 把 undefined 误读为任务证据已经配对。
  return {
    schema: "not_loaded",
    status: "blocked_not_proven",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    gate_status: "blocked_not_proven",
    terminal_result_source: "not_loaded",
    terminal_result_ref: "not_loaded",
    terminal_source_schema: "not_loaded",
    terminal_result_status: "blocked_not_proven",
    route_execution_materials_status: "blocked_not_proven",
    mission_artifact_delta: "blocked_not_proven",
    same_task_id_consumed: false,
    live_or_field_command_executed: false,
    support_only_reason: "blocked_not_proven",
    okr_credit_allowed: false,
    linked_evidence_flags: {
      same_task_id: false,
      terminal_result_ready: false,
      cloud_terminal_source_ready: false,
      route_execution_readiness_ready: false,
      route_delivery_closure_ready: false,
      route_pose_progress_ready: false,
    },
    blocked_reasons: [reason],
    next_required_evidence: ["same_task_terminal_result_and_route_execution_materials_for_selected_task"],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      terminal_result_connected: false,
      route_execution_materials_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function sameTaskMissionEvidenceGateHardFailReason(summary: O7ConsumerSameTaskMissionEvidenceGateSummary): string {
  // 坏 schema、危险 true、缺必填、unsafe text 和 proof scope mismatch 都必须让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(same_task_mission_evidence_gate_schema_mismatch|same_task_mission_evidence_gate_task_mismatch|same_task_mission_evidence_gate_dangerous_true|same_task_mission_evidence_gate_missing_required_fields|same_task_mission_evidence_gate_unsafe_text|same_task_mission_evidence_gate_unsafe_list|same_task_mission_evidence_gate_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildSameTaskMissionEvidenceGateSummary(
  candidate: SameTaskMissionEvidenceGateSourceResult | null,
  taskId: string,
): O7ConsumerSameTaskMissionEvidenceGateSummary {
  // O7 只信任 gate 顶层 status；linked flags 做解释和阻塞原因，不反推出 delivery success。
  if (!candidate) {
    return blockedSameTaskMissionEvidenceGate("same_task_mission_evidence_gate_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA && schema !== SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA) {
    return blockedSameTaskMissionEvidenceGate("same_task_mission_evidence_gate_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedSameTaskMissionEvidenceGate(
      `same_task_mission_evidence_gate_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope, "not_loaded");
  if (proofScope !== SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE) {
    return blockedSameTaskMissionEvidenceGate("same_task_mission_evidence_gate_proof_scope_mismatch", taskId);
  }
  const linkedFlagsRecord = asRecord(payload.linked_evidence_flags) ?? asRecord(payload.linked_flags);
  const linkedFlags = {
    same_task_id: asBoolean(linkedFlagsRecord?.same_task_id ?? linkedFlagsRecord?.same_task_id_matched ?? payload.same_task_id_matched),
    terminal_result_ready: asBoolean(linkedFlagsRecord?.terminal_result_ready ?? payload.terminal_result_ready),
    cloud_terminal_source_ready: asBoolean(
      linkedFlagsRecord?.cloud_terminal_source_ready ?? payload.cloud_terminal_source_ready,
    ),
    route_execution_readiness_ready: asBoolean(
      linkedFlagsRecord?.route_execution_readiness_ready ?? payload.route_execution_readiness_ready,
    ),
    route_delivery_closure_ready: asBoolean(
      linkedFlagsRecord?.route_delivery_closure_ready ?? payload.route_delivery_closure_ready,
    ),
    route_pose_progress_ready: asBoolean(linkedFlagsRecord?.route_pose_progress_ready ?? payload.route_pose_progress_ready),
  };
  const terminalRefs = rawStringList(payload.terminal_refs ?? payload.terminal_result_refs);
  const terminalResultSource = asString(
    payload.terminal_result_source ?? payload.terminal_source ?? payload.cloud_terminal_result_source,
    "not_loaded",
  );
  const terminalSourceSchema = asString(
    payload.terminal_source_schema ?? payload.source_schema ?? payload.cloud_terminal_source_schema,
    "not_loaded",
  );
  const terminalResultStatus = asString(
    payload.terminal_result_status ?? payload.delivery_result_status ?? payload.record_status,
    "blocked_not_proven",
  );
  const routeExecutionMaterialsStatus = asString(
    payload.route_execution_materials_status ?? payload.route_execution_status ?? payload.route_execution_result_status,
    "blocked_not_proven",
  );
  const missionArtifactDeltaPayload = payload.mission_artifact_delta;
  const missionArtifactDeltaRecord = sameTaskMissionArtifactDeltaRecord(missionArtifactDeltaPayload);
  const missionArtifactDelta = sameTaskMissionArtifactDeltaSummary(missionArtifactDeltaPayload);
  const sameTaskIdConsumed = asBoolean(
    payload.same_task_id_consumed ??
      missionArtifactDeltaRecord?.same_task_id_consumed ??
      linkedFlags.same_task_id,
  );
  const liveOrFieldCommandExecuted = asBoolean(
    payload.live_or_field_command_executed ?? missionArtifactDeltaRecord?.live_or_field_command_executed,
  );
  const supportOnlyReason = asString(
    payload.support_only_reason ?? missionArtifactDeltaRecord?.support_only_reason,
    "blocked_not_proven",
  );
  const okrCreditAllowed = asBoolean(payload.okr_credit_allowed ?? missionArtifactDeltaRecord?.okr_credit_allowed);
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(terminalResultSource) ? "" : "terminal_result_source",
    rawString(terminalSourceSchema) ? "" : "terminal_source_schema",
    rawString(terminalResultStatus) ? "" : "terminal_result_status",
    rawString(routeExecutionMaterialsStatus) ? "" : "route_execution_materials_status",
    rawString(missionArtifactDelta) ? "" : "mission_artifact_delta",
    typeof (payload.same_task_id_consumed ?? missionArtifactDeltaRecord?.same_task_id_consumed ?? linkedFlags.same_task_id) === "boolean"
      ? ""
      : "same_task_id_consumed",
    typeof (payload.live_or_field_command_executed ?? missionArtifactDeltaRecord?.live_or_field_command_executed) === "boolean"
      ? ""
      : "live_or_field_command_executed",
    rawString(payload.support_only_reason ?? missionArtifactDeltaRecord?.support_only_reason) ? "" : "support_only_reason",
    typeof (payload.okr_credit_allowed ?? missionArtifactDeltaRecord?.okr_credit_allowed) === "boolean"
      ? ""
      : "okr_credit_allowed",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
    linkedFlagsRecord ? "" : "linked_evidence_flags",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedSameTaskMissionEvidenceGate(
      `same_task_mission_evidence_gate_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedSameTaskMissionEvidenceGate("same_task_mission_evidence_gate_task_mismatch", taskId);
  }
  const unsafeList = aggregateDistinct([
    unsafeSameTaskMissionEvidenceGateListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeSameTaskMissionEvidenceGateListReason(payload.next_required_evidence, "next_required_evidence"),
  ]);
  if (unsafeList.length > 0) {
    return blockedSameTaskMissionEvidenceGate(unsafeList[0] ?? "same_task_mission_evidence_gate_unsafe_list", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons);
  const nextRequiredEvidence = stringList(payload.next_required_evidence);
  const terminalResultRef = safePathToken(
    payload.terminal_result_ref ?? payload.terminal_ref ?? terminalRefs[0] ?? "not_loaded",
  );
  const unsafeText = aggregateDistinct([
    unsafeSameTaskMissionEvidenceGateTextReason(payload.status),
    unsafeSameTaskMissionEvidenceGateTextReason(terminalResultSource),
    unsafeSameTaskMissionEvidenceGateTextReason(payload.terminal_result_ref ?? payload.terminal_ref),
    unsafeSameTaskMissionEvidenceGateTextReason(terminalResultRef),
    unsafeSameTaskMissionEvidenceGateTextReason(terminalSourceSchema),
    unsafeSameTaskMissionEvidenceGateTextReason(terminalResultStatus),
    unsafeSameTaskMissionEvidenceGateTextReason(routeExecutionMaterialsStatus),
    unsafeSameTaskMissionEvidenceGateTextReason(missionArtifactDelta),
    unsafeSameTaskMissionEvidenceGateTextReason(supportOnlyReason),
    terminalRefs.map((value) => unsafeSameTaskMissionEvidenceGateTextReason(value)),
    blockedReasons.map((value) => unsafeSameTaskMissionEvidenceGateTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeSameTaskMissionEvidenceGateTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedSameTaskMissionEvidenceGate("same_task_mission_evidence_gate_unsafe_text", taskId);
  }
  const payloadTopLevelStatus = asString(payload.status, "derived_blocked_not_proven");
  const ready = payloadTopLevelStatus === "same_task_mission_gate_ready_not_success_proof";
  return {
    schema: schema === O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA
      ? O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA
      : SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
    status: ready
      ? "same_task_mission_gate_ready_not_success_proof"
      : payloadTopLevelStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_contract: schema === O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA
      ? O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA
      : SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    proof_scope: SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    gate_status: payloadTopLevelStatus,
    terminal_result_source: terminalResultSource,
    terminal_result_ref: terminalResultRef,
    terminal_source_schema: terminalSourceSchema,
    terminal_result_status: terminalResultStatus,
    route_execution_materials_status: routeExecutionMaterialsStatus,
    mission_artifact_delta: missionArtifactDelta,
    same_task_id_consumed: sameTaskIdConsumed,
    live_or_field_command_executed: liveOrFieldCommandExecuted,
    support_only_reason: supportOnlyReason,
    okr_credit_allowed: okrCreditAllowed,
    linked_evidence_flags: linkedFlags,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      okrCreditAllowed ? "" : "okr_credit_not_allowed",
      okrCreditAllowed ? "" : supportOnlyReason,
      "delivery_success_not_proven",
      ready ? "" : "same_task_mission_evidence_gate_not_ready",
      linkedFlags.same_task_id ? "" : "same_task_id_not_matched",
      linkedFlags.terminal_result_ready ? "" : "terminal_result_not_ready",
      linkedFlags.cloud_terminal_source_ready ? "" : "cloud_terminal_source_not_ready",
      linkedFlags.route_execution_readiness_ready ? "" : "route_execution_readiness_not_ready",
      linkedFlags.route_delivery_closure_ready ? "" : "route_delivery_closure_not_ready",
      linkedFlags.route_pose_progress_ready ? "" : "route_pose_progress_not_ready",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "same_task_cloud_terminal_result_for_selected_task",
          "same_task_live_or_replay_route_execution_materials",
          "real_drop_off_completion_proof",
        ],
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      terminal_result_connected: false,
      route_execution_materials_connected: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function fieldOperatorConfirmationMaterialCandidateFromRemote(
  remote: JsonRecord,
): FieldOperatorConfirmationMaterialSourceResult | null {
  // operator material 只从 O6/Algorithm 白名单 section 读取，O7 不从散落字段拼人工确认事实。
  const direct = asRecord(remote.field_operator_confirmation_material);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_field_operator_confirmation_material",
      source_path: "field_operator_confirmation_material",
    };
  }
  const fieldEvidence =
    nestedRecord(remote, "field_evidence", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence_manifest", "field_operator_confirmation_material");
  if (fieldEvidence) {
    return {
      payload: fieldEvidence,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.field_operator_confirmation_material",
    };
  }
  const fieldMotion =
    nestedRecord(remote, "field_motion_evidence_packet", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence", "field_motion_evidence_packet", "field_operator_confirmation_material");
  if (fieldMotion) {
    return {
      payload: fieldMotion,
      source_origin: "remote_field_motion_evidence_packet",
      source_path: "field_motion_evidence_packet.field_operator_confirmation_material",
    };
  }
  const fieldIngest =
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence_ingest", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest", "field_operator_confirmation_material");
  if (fieldIngest) {
    return {
      payload: fieldIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest.field_operator_confirmation_material",
    };
  }
  const bundle =
    nestedRecord(remote, "artifact_bundle", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle", "field_operator_confirmation_material");
  if (bundle) {
    return {
      payload: bundle,
      source_origin: "remote_artifact_bundle",
      source_path: "artifact_bundle.field_operator_confirmation_material",
    };
  }
  const ingest =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "field_operator_confirmation_material") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "field_operator_confirmation_material");
  if (ingest) {
    return {
      payload: ingest,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.field_operator_confirmation_material",
    };
  }
  const readiness =
    nestedRecord(remote, "artifact_bundle_readiness", "field_operator_confirmation_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle", "field_operator_confirmation_material") ??
    nestedRecord(remote, "artifact_bundle_readiness", "artifact_bundle_consumer_ingest", "field_operator_confirmation_material");
  if (readiness) {
    return {
      payload: readiness,
      source_origin: "remote_artifact_bundle_readiness",
      source_path: "artifact_bundle_readiness.field_operator_confirmation_material",
    };
  }
  return null;
}

function unsafeFieldOperatorConfirmationMaterialTextReason(value: unknown): string {
  // 人工材料文本只允许短状态/时间/材料标签，不允许 URL、路径、凭证、raw payload 或 traceback。
  const text = rawString(value);
  if (!text) {
    return "";
  }
  const lowered = text.toLowerCase();
  if (
    lowered.includes("://") ||
    lowered.includes("authorization") ||
    lowered.includes("bearer") ||
    lowered.includes("token") ||
    lowered.includes("secret") ||
    lowered.includes("credential") ||
    lowered.includes("password") ||
    lowered.includes("base64") ||
    lowered.includes("allowlist_root") ||
    lowered.includes("raw") ||
    lowered.includes("traceback") ||
    lowered.includes("response body") ||
    lowered.includes("/cmd_vel") ||
    lowered.includes("/dev/tty") ||
    lowered.startsWith("data:") ||
    path.isAbsolute(text) ||
    /^[A-Za-z]:\\/.test(text) ||
    text.includes("/") ||
    text.includes("\\")
  ) {
    return "field_operator_confirmation_material_unsafe_text";
  }
  return "";
}

function unsafeFieldOperatorConfirmationMaterialListReason(value: unknown, fieldName: string): string {
  // blocked/next/sample_refs 列表只能是短字符串数组，避免对象或 raw note 进入 UI。
  if (!Array.isArray(value)) {
    return "";
  }
  return value.every((item) => typeof item === "string")
    ? ""
    : `field_operator_confirmation_material_unsafe_list:${fieldName}`;
}

function fieldOperatorMaterialSummaryKey(
  key: string,
): keyof O7ConsumerFieldOperatorConfirmationMaterialSummary["material_summaries"] | null {
  // 上游材料摘要可能使用短别名；O7 展示统一成四类 operator/route/delivery 材料。
  const normalized = normalizeSameTaskFieldMaterialKey(key);
  if (normalized === "operator_report" || normalized === "report") {
    return "operator_report";
  }
  if (normalized === "operator_confirmation" || normalized === "confirmation" || normalized === "dropoff_confirmation") {
    return "operator_confirmation";
  }
  if (normalized === "linked_route_material" || normalized === "route_material" || normalized === "route_execution_material") {
    return "linked_route_material";
  }
  if (normalized === "linked_delivery_material" || normalized === "delivery_material" || normalized === "delivery_record") {
    return "linked_delivery_material";
  }
  return null;
}

function fieldOperatorMaterialSummaryEntry(
  value: unknown,
): O7ConsumerFieldOperatorConfirmationMaterialSummary["material_summaries"]["operator_report"] | null {
  // 每个 material summary 只保留 present/status/count/reported_at/sample_refs，不回显人工备注或原始 report。
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  return {
    present: asBoolean(record.present),
    status: asString(record.status, asBoolean(record.present) ? "present" : "missing"),
    sample_refs: stringList(record.sample_refs, 6).map((item) => safePathToken(item)),
    count: asNumber(record.count ?? record.sample_count),
    reported_at: asString(record.reported_at, "not_loaded"),
  };
}

function fieldOperatorMaterialSummaries(
  payload: JsonRecord | null,
): O7ConsumerFieldOperatorConfirmationMaterialSummary["material_summaries"] {
  // material_summaries 是 O6/Algorithm 安全摘要；未知键忽略，避免 UI 展示非合同内容。
  const source = asRecord(payload?.material_summaries);
  if (!source) {
    return {};
  }
  return Object.entries(source).reduce<O7ConsumerFieldOperatorConfirmationMaterialSummary["material_summaries"]>(
    (acc, [key, value]) => {
      const normalizedKey = fieldOperatorMaterialSummaryKey(key);
      const summary = fieldOperatorMaterialSummaryEntry(value);
      if (normalizedKey && summary) {
        acc[normalizedKey] = summary;
      }
      return acc;
    },
    {},
  );
}

function fieldOperatorMaterialSummaryUnsafeReasons(payload: JsonRecord | null): string[] {
  // 原始 summary 先做文本/列表安全扫描，再投影到 UI 白名单字段。
  const source = asRecord(payload?.material_summaries);
  if (!source) {
    return [];
  }
  return aggregateDistinct(
    Object.entries(source).flatMap(([key, value]) => {
      const record = asRecord(value);
      return [
        unsafeFieldOperatorConfirmationMaterialTextReason(key),
        record ? unsafeFieldOperatorConfirmationMaterialTextReason(record.status) : "",
        record ? unsafeFieldOperatorConfirmationMaterialTextReason(record.reported_at) : "",
        record ? unsafeFieldOperatorConfirmationMaterialListReason(record.sample_refs, `${key}.sample_refs`) : "",
        record ? stringList(record.sample_refs, 6).map((item) => unsafeFieldOperatorConfirmationMaterialTextReason(item)) : [],
      ];
    }),
  );
}

function blockedFieldOperatorConfirmationMaterial(
  reason: string,
  taskId: string,
): O7ConsumerFieldOperatorConfirmationMaterialSummary {
  // 缺失或不可信时也返回完整 O7 schema，避免 UI 用空字段推断 operator material 已接入。
  return {
    schema: O7_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA,
    status: "blocked_not_proven",
    source_schema: "not_loaded",
    source_origin: "not_loaded",
    source_path: "not_loaded",
    task_id: taskId || "not_provided",
    proof_scope: "not_loaded",
    source_proof_status: "not_proven",
    material_status: "blocked_not_proven",
    operator_report_present: false,
    operator_report_status: "blocked_not_proven",
    operator_confirmation_present: false,
    operator_confirmation_status: "blocked_not_proven",
    operator_present: false,
    physical_clearance_confirmed: false,
    emergency_stop_ready: false,
    observed_motion: false,
    observed_stop: false,
    reported_at: "not_loaded",
    same_task_id_consumed: false,
    linked_route_material_present: false,
    linked_delivery_material_present: false,
    operator_material_consumed: false,
    support_only_reason: "field_operator_confirmation_material_missing_or_blocked",
    blocked_reasons: [reason],
    next_required_evidence: ["field_operator_confirmation_material_for_selected_task"],
    material_summaries: {},
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      operator_material_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    route_execution_success: false,
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function fieldOperatorConfirmationMaterialHardFailReason(
  summary: O7ConsumerFieldOperatorConfirmationMaterialSummary,
): string {
  // 坏 schema、危险 true、缺必填、task mismatch、unsafe text/list 和 proof scope mismatch 都让 detail fail-closed。
  const reason = summary.blocked_reasons[0] ?? "";
  return /^(field_operator_confirmation_material_schema_mismatch|field_operator_confirmation_material_task_mismatch|field_operator_confirmation_material_dangerous_true|field_operator_confirmation_material_missing_required_fields|field_operator_confirmation_material_unsafe_text|field_operator_confirmation_material_unsafe_list|field_operator_confirmation_material_proof_scope_mismatch)/.test(
    reason,
  )
    ? reason
    : "";
}

function buildFieldOperatorConfirmationMaterialSummary(
  candidate: FieldOperatorConfirmationMaterialSourceResult | null,
  taskId: string,
): O7ConsumerFieldOperatorConfirmationMaterialSummary {
  // O7 只消费 O6/Algorithm 脱敏 operator material，不把人工确认材料升级成控制或送达证明。
  if (!candidate) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_missing", taskId);
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  if (schema !== O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA && schema !== FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedFieldOperatorConfirmationMaterial(
      `field_operator_confirmation_material_dangerous_true:${dangerous.join(",")}`,
      taskId,
    );
  }
  const proofScope = asString(payload.proof_scope ?? payload.evidence_boundary, "not_loaded");
  if (proofScope !== FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_proof_scope_mismatch", taskId);
  }
  const payloadTaskId = asString(payload.task_id, taskId || "not_provided");
  if (payloadTaskId !== (taskId || "not_provided")) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_task_mismatch", taskId);
  }
  const sourceSchema = asString(payload.source_schema, "not_loaded");
  if (sourceSchema !== O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA && sourceSchema !== FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_schema_mismatch", taskId);
  }
  const blockedReasons = stringList(payload.blocked_reasons, 12);
  const nextRequiredEvidence = stringList(payload.next_required_evidence, 12);
  const materialSummaries = fieldOperatorMaterialSummaries(payload);
  const packetStatus = asString(payload.status, "blocked_not_proven");
  const materialStatus = asString(payload.material_status ?? payload.status, "blocked_not_proven");
  const operatorReportStatus = asString(payload.operator_report_status, "blocked_not_proven");
  const operatorConfirmationStatus = asString(payload.operator_confirmation_status, "blocked_not_proven");
  const reportedAt = asString(payload.reported_at, "not_loaded");
  const supportOnlyReason = asString(payload.support_only_reason, "field_operator_confirmation_material_only_not_delivery_proof");
  const missingFields = [
    rawString(payload.status) ? "" : "status",
    rawString(payload.source_schema) ? "" : "source_schema",
    rawString(payload.proof_scope ?? payload.evidence_boundary) ? "" : "proof_scope",
    typeof payload.operator_report_present === "boolean" ? "" : "operator_report_present",
    rawString(payload.operator_report_status) ? "" : "operator_report_status",
    typeof payload.operator_confirmation_present === "boolean" ? "" : "operator_confirmation_present",
    rawString(payload.operator_confirmation_status) ? "" : "operator_confirmation_status",
    typeof payload.operator_present === "boolean" ? "" : "operator_present",
    typeof payload.physical_clearance_confirmed === "boolean" ? "" : "physical_clearance_confirmed",
    typeof payload.emergency_stop_ready === "boolean" ? "" : "emergency_stop_ready",
    typeof payload.observed_motion === "boolean" ? "" : "observed_motion",
    typeof payload.observed_stop === "boolean" ? "" : "observed_stop",
    rawString(payload.reported_at) ? "" : "reported_at",
    typeof payload.same_task_id_consumed === "boolean" ? "" : "same_task_id_consumed",
    typeof payload.linked_route_material_present === "boolean" ? "" : "linked_route_material_present",
    typeof payload.linked_delivery_material_present === "boolean" ? "" : "linked_delivery_material_present",
    typeof payload.operator_material_consumed === "boolean" ? "" : "operator_material_consumed",
    rawString(payload.support_only_reason) ? "" : "support_only_reason",
    Array.isArray(payload.blocked_reasons) ? "" : "blocked_reasons",
    Array.isArray(payload.next_required_evidence) ? "" : "next_required_evidence",
    asRecord(payload.material_summaries) ? "" : "material_summaries",
  ].filter(Boolean);
  if (missingFields.length > 0) {
    return blockedFieldOperatorConfirmationMaterial(
      `field_operator_confirmation_material_missing_required_fields:${missingFields.join(",")}`,
      taskId,
    );
  }
  const unsafeList = aggregateDistinct([
    unsafeFieldOperatorConfirmationMaterialListReason(payload.blocked_reasons, "blocked_reasons"),
    unsafeFieldOperatorConfirmationMaterialListReason(payload.next_required_evidence, "next_required_evidence"),
    fieldOperatorMaterialSummaryUnsafeReasons(payload),
  ]);
  if (unsafeList.length > 0) {
    return blockedFieldOperatorConfirmationMaterial(
      unsafeList[0] ?? "field_operator_confirmation_material_unsafe_list",
      taskId,
    );
  }
  const unsafeText = aggregateDistinct([
    unsafeFieldOperatorConfirmationMaterialTextReason(payloadTaskId),
    unsafeFieldOperatorConfirmationMaterialTextReason(packetStatus),
    unsafeFieldOperatorConfirmationMaterialTextReason(materialStatus),
    unsafeFieldOperatorConfirmationMaterialTextReason(sourceSchema),
    unsafeFieldOperatorConfirmationMaterialTextReason(operatorReportStatus),
    unsafeFieldOperatorConfirmationMaterialTextReason(operatorConfirmationStatus),
    unsafeFieldOperatorConfirmationMaterialTextReason(reportedAt),
    unsafeFieldOperatorConfirmationMaterialTextReason(supportOnlyReason),
    blockedReasons.map((value) => unsafeFieldOperatorConfirmationMaterialTextReason(value)),
    nextRequiredEvidence.map((value) => unsafeFieldOperatorConfirmationMaterialTextReason(value)),
  ]);
  if (unsafeText.length > 0) {
    return blockedFieldOperatorConfirmationMaterial("field_operator_confirmation_material_unsafe_text", taskId);
  }
  const operatorReportPresent = asBoolean(payload.operator_report_present);
  const operatorConfirmationPresent = asBoolean(payload.operator_confirmation_present);
  const sameTaskIdConsumed = asBoolean(payload.same_task_id_consumed);
  const linkedRouteMaterialPresent = asBoolean(payload.linked_route_material_present);
  const linkedDeliveryMaterialPresent = asBoolean(payload.linked_delivery_material_present);
  const operatorMaterialConsumed = asBoolean(payload.operator_material_consumed);
  const operatorPresent = asBoolean(payload.operator_present);
  const physicalClearanceConfirmed = asBoolean(payload.physical_clearance_confirmed);
  const emergencyStopReady = asBoolean(payload.emergency_stop_ready);
  const observedMotion = asBoolean(payload.observed_motion);
  const observedStop = asBoolean(payload.observed_stop);
  const ready =
    packetStatus === "field_operator_confirmation_material_ready_not_delivery_proof" &&
    sameTaskIdConsumed &&
    operatorMaterialConsumed &&
    (operatorReportPresent || operatorConfirmationPresent);
  return {
    schema: O7_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA,
    status: ready
      ? "field_operator_confirmation_material_ready_not_delivery_proof"
      : packetStatus === "blocked_not_proven"
        ? "blocked_not_proven"
        : "derived_blocked_not_proven",
    source_schema: sourceSchema as O7ConsumerFieldOperatorConfirmationMaterialSummary["source_schema"],
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    task_id: payloadTaskId,
    proof_scope: FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE,
    source_proof_status: asString(payload.proof_status, "not_proven"),
    material_status: materialStatus,
    operator_report_present: operatorReportPresent,
    operator_report_status: operatorReportStatus,
    operator_confirmation_present: operatorConfirmationPresent,
    operator_confirmation_status: operatorConfirmationStatus,
    operator_present: operatorPresent,
    physical_clearance_confirmed: physicalClearanceConfirmed,
    emergency_stop_ready: emergencyStopReady,
    observed_motion: observedMotion,
    observed_stop: observedStop,
    reported_at: reportedAt,
    same_task_id_consumed: sameTaskIdConsumed,
    linked_route_material_present: linkedRouteMaterialPresent,
    linked_delivery_material_present: linkedDeliveryMaterialPresent,
    operator_material_consumed: operatorMaterialConsumed,
    support_only_reason: supportOnlyReason,
    blocked_reasons: aggregateDistinct([
      blockedReasons,
      "delivery_success_not_proven",
      ready ? "" : "field_operator_confirmation_material_not_ready",
      sameTaskIdConsumed ? "" : "same_task_id_not_consumed",
      operatorReportPresent ? "" : "operator_report_missing",
      operatorConfirmationPresent ? "" : "operator_confirmation_missing",
      linkedRouteMaterialPresent ? "" : "linked_route_material_missing",
      linkedDeliveryMaterialPresent ? "" : "linked_delivery_material_missing",
      operatorMaterialConsumed ? "" : "operator_material_not_consumed",
      operatorPresent ? "" : "operator_not_present",
      physicalClearanceConfirmed ? "" : "physical_clearance_not_confirmed",
      emergencyStopReady ? "" : "emergency_stop_not_ready",
      observedMotion ? "" : "observed_motion_not_confirmed",
      observedStop ? "" : "observed_stop_not_confirmed",
    ]),
    next_required_evidence: nextRequiredEvidence.length
      ? nextRequiredEvidence
      : [
          "field_operator_confirmation_material_for_selected_task",
          "operator_report_for_selected_task",
          "operator_confirmation_for_selected_task",
          "delivery_record_or_operator_dropoff_confirmation",
        ],
    material_summaries: materialSummaries,
    proof_boundary: {
      local_mock: true,
      not_proven: true,
      reads_local_path: false,
      operator_material_connected: false,
      route_execution_success: false,
      delivery_success_proven: false,
      real_production_cloud_connected: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    route_execution_success: false,
    hil_pass: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function checklistItem(
  id: O7ConsumerSameTaskMissionMaterialChecklist["items"][number]["id"],
  label: string,
  materialStatus: O7ConsumerSameTaskMissionMaterialChecklist["items"][number]["material_status"],
  sourceSummary: string,
  blockedReasons: string[],
  nextRequiredEvidence: string[],
  ownerHint: string,
): O7ConsumerSameTaskMissionMaterialChecklist["items"][number] {
  // item 是 operator 操作清单的最小单位，只放脱敏摘要和下一步材料，不放原始 payload。
  return {
    id,
    label,
    material_status: materialStatus,
    source_summary: sourceSummary,
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    owner_hint: ownerHint,
  };
}

function checklistStatus(ready: boolean, blocked: boolean): O7ConsumerSameTaskMissionMaterialChecklist["items"][number]["material_status"] {
  // ready 仍然是 not-success-proof；blocked 用于 operator 需要补材料的项。
  if (ready) {
    return "ready_not_success_proof";
  }
  return blocked ? "blocked" : "not_proven";
}

function checklistReasons(
  gate: O7ConsumerSameTaskMissionEvidenceGateSummary,
  localReason: string,
): string[] {
  // 每个材料项继承 gate 的 blocker，再追加本项缺口，保证 operator 不需要回看原始 JSON。
  return aggregateDistinct([gate.blocked_reasons, localReason, "delivery_success_not_proven"]);
}

function checklistNextEvidence(
  gate: O7ConsumerSameTaskMissionEvidenceGateSummary,
  required: string[],
): string[] {
  // next evidence 以本项行动为主，同时保留 O6 gate 给出的上游下一步材料。
  return aggregateDistinct([required, gate.next_required_evidence]);
}

function blockedSameTaskMissionMaterialChecklist(
  reason: string,
  taskId: string,
  gate = blockedSameTaskMissionEvidenceGate(reason, taskId),
): O7ConsumerSameTaskMissionMaterialChecklist {
  // gate 缺失或上游形状不可信时，checklist 自身也 fail-closed，避免 UI 隐去关键材料缺口。
  return {
    schema: SAME_TASK_MISSION_MATERIAL_CHECKLIST_SCHEMA,
    status: "fail_closed",
    overall_status: "fail_closed",
    task_id: taskId || "not_provided",
    source_gate_schema: gate.schema,
    source_gate_status: gate.status,
    source_gate_task_id: gate.task_id,
    source_gate_source_origin: gate.source_origin,
    okr_credit_allowed: false,
    support_only_reason: gate.support_only_reason,
    same_task_id_consumed: false,
    live_or_field_command_executed: false,
    items: [
      checklistItem(
        "same_task_identity",
        "Same task identity",
        "blocked",
        `requested_task_id=${taskId || "not_provided"} · gate_task_id=${gate.task_id}`,
        [reason],
        ["same_task_mission_evidence_gate_for_selected_task"],
        "full-stack-software-engineer",
      ),
      checklistItem(
        "terminal_cloud_result",
        "Terminal / cloud result",
        "blocked",
        "terminal_result_source=not_loaded · terminal_source_schema=not_loaded",
        [reason],
        ["same_task_cloud_terminal_result_for_selected_task"],
        "robot-software-engineer",
      ),
      checklistItem(
        "route_execution_material",
        "Route execution material",
        "blocked",
        "route_execution_materials_status=blocked_not_proven",
        [reason],
        ["same_task_live_or_replay_route_execution_materials"],
        "robot-algorithm-engineer",
      ),
      checklistItem(
        "same_task_field_material_packet",
        "Same-task field material packet",
        "blocked",
        "same_task_field_material_packet=blocked_not_proven",
        [reason],
        ["same_task_field_material_packet_for_selected_task"],
        "full-stack-software-engineer",
      ),
      checklistItem(
        "delivery_record",
        "Delivery record",
        "blocked",
        "delivery_result_evidence=not_loaded",
        [reason],
        ["delivery_record_or_operator_dropoff_confirmation"],
        "robot-software-engineer",
      ),
      checklistItem(
        "operator_confirmation",
        "Operator confirmation",
        "blocked",
        "operator_confirmation_present=false",
        [reason],
        ["operator_confirmation_for_selected_task"],
        "full-stack-software-engineer",
      ),
      checklistItem(
        "route_pose_progress",
        "Route pose progress",
        "blocked",
        "route_pose_progress_ready=false",
        [reason],
        ["route_pose_progress_replay_for_selected_task"],
        "robot-algorithm-engineer",
      ),
      checklistItem(
        "production_cloud_readback",
        "Production cloud readback",
        "blocked",
        "connects_cloud_production=false · production_cloud_readback_not_proven",
        [reason],
        ["production_cloud_db_queue_endpoint_readback_for_same_task"],
        "robot-software-engineer",
      ),
      checklistItem(
        "safety_invariants",
        "Safety invariants",
        "ready_not_success_proof",
        "delivery_success=false · safe_to_control=false · primary_actions_enabled=false · robot_control_executed=false",
        ["observe_only_no_robot_control"],
        ["keep_primary_actions_disabled_until_real_hil_and_product_acceptance"],
        "full-stack-software-engineer",
      ),
    ],
    blocked_reasons: [reason],
    next_required_evidence: ["same_task_mission_evidence_gate_for_selected_task"],
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function buildSameTaskMissionMaterialChecklist(
  sameTaskFieldMaterialPacket: O7ConsumerSameTaskFieldMaterialPacketSummary,
  sameTaskRouteExecutionMaterialPacket: O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
  gate: O7ConsumerSameTaskMissionEvidenceGateSummary,
  deliveryResultEvidence: O7ConsumerDeliveryResultEvidenceSummary,
  routeExecutionResultDeliveryReadiness: O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
  routeDeliveryClosurePacket: O7ConsumerRouteDeliveryClosurePacketSummary,
  routeBagPoseProgressReplay: O7ConsumerRouteBagPoseProgressReplaySummary,
  taskId: string,
): O7ConsumerSameTaskMissionMaterialChecklist {
  // checklist 以 O6 same-task gate 为事实入口，其他 O7 摘要只用于把 gate 缺口翻译成 operator 材料。
  if (gate.schema === "not_loaded") {
    return blockedSameTaskMissionMaterialChecklist(
      gate.blocked_reasons[0] ?? "same_task_mission_evidence_gate_missing",
      taskId,
      gate,
    );
  }
  if (gate.task_id !== (taskId || "not_provided")) {
    return blockedSameTaskMissionMaterialChecklist("same_task_mission_evidence_gate_task_mismatch", taskId, gate);
  }

  const gateReady = gate.status === "same_task_mission_gate_ready_not_success_proof";
  const creditAllowed = gate.okr_credit_allowed;
  const deliveryRecordReady =
    deliveryResultEvidence.schema === DELIVERY_RESULT_EVIDENCE_SCHEMA &&
    deliveryResultEvidence.status === "delivery_result_evidence_ready_not_delivery_proof";
  const operatorConfirmationReady =
    deliveryResultEvidence.operator_confirmation_present ||
    routeExecutionResultDeliveryReadiness.operator_confirmation_ready;
  const routeExecutionReady =
    gate.linked_evidence_flags.route_execution_readiness_ready &&
    routeExecutionResultDeliveryReadiness.status === "route_execution_result_delivery_readiness_ready_not_delivery_proof";
  const routeClosureReady =
    gate.linked_evidence_flags.route_delivery_closure_ready &&
    routeDeliveryClosurePacket.status === "route_delivery_closure_ready_not_success_proof";
  const fieldMaterialPacketReady =
    (sameTaskFieldMaterialPacket.schema === O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA ||
      sameTaskFieldMaterialPacket.schema === SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA) &&
    sameTaskFieldMaterialPacket.status === "ready_not_delivery_proof";
  const routeExecutionMaterialPacketReady =
    (sameTaskRouteExecutionMaterialPacket.schema === O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA ||
      sameTaskRouteExecutionMaterialPacket.schema === SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA) &&
    sameTaskRouteExecutionMaterialPacket.status === "route_execution_material_ready_not_delivery_proof";
  const poseProgressReady =
    gate.linked_evidence_flags.route_pose_progress_ready ||
    routeDeliveryClosurePacket.linked_evidence_flags.route_pose_progress_ready ||
    routeBagPoseProgressReplay.status === "ready_not_live_nav2_proof";
  const terminalReady =
    gate.linked_evidence_flags.terminal_result_ready &&
    gate.linked_evidence_flags.cloud_terminal_source_ready &&
    gate.terminal_result_source !== "not_loaded" &&
    gate.terminal_source_schema !== "not_loaded";
  const overallStatus =
    gateReady && creditAllowed && fieldMaterialPacketReady && routeExecutionMaterialPacketReady
      ? "materials_ready_not_success_proof"
      : "blocked_not_proven";

  return {
    schema: SAME_TASK_MISSION_MATERIAL_CHECKLIST_SCHEMA,
    status: overallStatus,
    overall_status: overallStatus,
    task_id: taskId || "not_provided",
    source_gate_schema: gate.schema,
    source_gate_status: gate.status,
    source_gate_task_id: gate.task_id,
    source_gate_source_origin: gate.source_origin,
    okr_credit_allowed: creditAllowed,
    support_only_reason: gate.support_only_reason,
    same_task_id_consumed: gate.same_task_id_consumed,
    live_or_field_command_executed: gate.live_or_field_command_executed,
    items: [
      checklistItem(
        "same_task_identity",
        "Same task identity",
        checklistStatus(gate.linked_evidence_flags.same_task_id && gate.task_id === taskId, true),
        `requested_task_id=${taskId || "not_provided"} · gate_task_id=${gate.task_id} · same_task_id=${gate.linked_evidence_flags.same_task_id} · same_task_id_consumed=${gate.same_task_id_consumed}`,
        checklistReasons(gate, gate.linked_evidence_flags.same_task_id ? "" : "same_task_id_not_matched"),
        checklistNextEvidence(gate, ["same_task_mission_evidence_gate_for_selected_task"]),
        "full-stack-software-engineer",
      ),
      checklistItem(
        "terminal_cloud_result",
        "Terminal / cloud result",
        checklistStatus(terminalReady, true),
        `terminal_result_source=${gate.terminal_result_source} · terminal_source_schema=${gate.terminal_source_schema} · terminal_result_status=${gate.terminal_result_status} · okr_credit_allowed=${gate.okr_credit_allowed}`,
        checklistReasons(gate, terminalReady ? "" : "terminal_cloud_result_material_missing"),
        checklistNextEvidence(gate, ["same_task_cloud_terminal_result_for_selected_task"]),
        "robot-software-engineer",
      ),
      checklistItem(
        "route_execution_material",
        "Route execution material",
        checklistStatus(routeExecutionMaterialPacketReady || (routeExecutionReady && routeClosureReady), true),
        `same_task_route_execution_material_packet=${sameTaskRouteExecutionMaterialPacket.status} · route_execution_materials_status=${gate.route_execution_materials_status} · route_execution_readiness=${routeExecutionResultDeliveryReadiness.status} · route_delivery_closure=${routeDeliveryClosurePacket.status} · route_execution_material_consumed=${sameTaskRouteExecutionMaterialPacket.route_execution_material_consumed}`,
        checklistReasons(
          gate,
          routeExecutionMaterialPacketReady || (routeExecutionReady && routeClosureReady)
            ? ""
            : "same_task_route_execution_material_packet_missing",
        ),
        checklistNextEvidence(gate, [
          "same_task_route_execution_material_packet_for_selected_task",
          "same_task_live_or_replay_route_execution_materials",
          "real_live_nav2_route_execution_result",
        ]),
        "robot-algorithm-engineer",
      ),
      checklistItem(
        "same_task_field_material_packet",
        "Same-task field material packet",
        checklistStatus(fieldMaterialPacketReady, true),
        `packet_status=${sameTaskFieldMaterialPacket.status} · present_materials=${sameTaskFieldMaterialPacket.present_materials.join(",") || "none"} · sample_refs=${sameTaskFieldMaterialPacket.sample_refs.join(",") || "none"} · live_or_field_material_consumed=${sameTaskFieldMaterialPacket.live_or_field_material_consumed}`,
        checklistReasons(gate, fieldMaterialPacketReady ? "" : "same_task_field_material_packet_missing"),
        checklistNextEvidence(gate, [
          "same_task_field_material_packet_for_selected_task",
          "same_task_live_or_replay_route_execution_materials",
        ]),
        "full-stack-software-engineer",
      ),
      checklistItem(
        "delivery_record",
        "Delivery record",
        checklistStatus(deliveryRecordReady, true),
        `delivery_result_evidence=${deliveryResultEvidence.status} · record_present=${deliveryResultEvidence.record_present} · record_read_ok=${deliveryResultEvidence.record_read_ok}`,
        checklistReasons(gate, deliveryRecordReady ? "" : "delivery_record_material_missing"),
        checklistNextEvidence(gate, ["delivery_record_or_operator_dropoff_confirmation", "real_drop_off_completion_proof"]),
        "robot-software-engineer",
      ),
      checklistItem(
        "operator_confirmation",
        "Operator confirmation",
        checklistStatus(operatorConfirmationReady, true),
        `operator_confirmation_present=${deliveryResultEvidence.operator_confirmation_present} · operator_confirmation_ready=${routeExecutionResultDeliveryReadiness.operator_confirmation_ready}`,
        checklistReasons(gate, operatorConfirmationReady ? "" : "operator_confirmation_material_missing"),
        checklistNextEvidence(gate, ["operator_confirmation_for_selected_task", "manual_dropoff_confirmation_evidence"]),
        "full-stack-software-engineer",
      ),
      checklistItem(
        "route_pose_progress",
        "Route pose progress",
        checklistStatus(poseProgressReady, true),
        `gate_route_pose_progress_ready=${gate.linked_evidence_flags.route_pose_progress_ready} · route_bag_pose_progress_replay=${routeBagPoseProgressReplay.status}`,
        checklistReasons(gate, poseProgressReady ? "" : "route_pose_progress_material_missing"),
        checklistNextEvidence(gate, ["route_pose_progress_replay_for_selected_task", "route_bag_or_live_nav2_pose_progress_material"]),
        "robot-algorithm-engineer",
      ),
      checklistItem(
        "production_cloud_readback",
        "Production cloud readback",
        "not_proven",
        `connects_cloud_production=false · production_cloud_readback_not_proven · support_only_reason=${gate.support_only_reason}`,
        checklistReasons(gate, "production_cloud_readback_not_proven"),
        checklistNextEvidence(gate, ["production_cloud_db_queue_endpoint_readback_for_same_task"]),
        "robot-software-engineer",
      ),
      checklistItem(
        "safety_invariants",
        "Safety invariants",
        "ready_not_success_proof",
        "delivery_success=false · safe_to_control=false · primary_actions_enabled=false · robot_control_executed=false",
        ["observe_only_no_robot_control"],
        ["keep_primary_actions_disabled_until_real_hil_and_product_acceptance"],
        "full-stack-software-engineer",
      ),
    ],
    blocked_reasons: aggregateDistinct([
      gate.blocked_reasons,
      sameTaskFieldMaterialPacket.blocked_reasons,
      sameTaskRouteExecutionMaterialPacket.blocked_reasons,
      gateReady && creditAllowed ? "materials_ready_not_success_proof" : "same_task_mission_materials_blocked_not_proven",
      creditAllowed ? "" : gate.support_only_reason,
      fieldMaterialPacketReady ? "" : "same_task_field_material_packet_missing",
      routeExecutionMaterialPacketReady ? "" : "same_task_route_execution_material_packet_missing",
      "delivery_success_not_proven",
      "production_cloud_readback_not_proven",
    ]),
    next_required_evidence: checklistNextEvidence(gate, [
      "same_task_field_material_packet_for_selected_task",
      "same_task_route_execution_material_packet_for_selected_task",
      "production_cloud_db_queue_endpoint_readback_for_same_task",
      "real_live_nav2_route_execution_result",
      "delivery_record_or_operator_dropoff_confirmation",
      "operator_confirmation_for_selected_task",
      ...sameTaskFieldMaterialPacket.next_required_evidence,
      ...sameTaskRouteExecutionMaterialPacket.next_required_evidence,
    ]),
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function buildOfflineArtifactSeedSmokeSummary(
  candidate: OfflineArtifactSeedSmokeSourceResult | null,
  taskId: string,
): O7ConsumerOfflineArtifactSeedSmokeSummary {
  // offline seed smoke 只读取 route/replay/keyframe/evidence 的离线摘要，不把绝对路径或完整 digest 传给 UI。
  if (!candidate) {
    return blockedOfflineArtifactSeedSmoke("offline_artifact_seed_smoke_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA) {
    return blockedOfflineArtifactSeedSmoke("offline_artifact_seed_smoke_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedOfflineArtifactSeedSmoke(`offline_artifact_seed_smoke_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  if (asBoolean(payload.allowlist_root_echoed)) {
    return blockedOfflineArtifactSeedSmoke("offline_artifact_seed_smoke_allowlist_root_echoed", taskId);
  }

  const sampleProbes = Array.isArray(payload.sample_probes)
    ? payload.sample_probes.map((probe) => asRecord(probe)).filter((probe): probe is JsonRecord => Boolean(probe))
    : [];
  const sampleProbeRouteRefs = sampleProbes
    .filter((probe) => /route/i.test(asString(probe.ref_kind, "")))
    .map((probe) => rawString(probe.ref));
  const sampleProbeReplayRefs = sampleProbes
    .filter((probe) => /replay/i.test(asString(probe.ref_kind, "")))
    .map((probe) => rawString(probe.ref));
  const sampleProbeKeyframeRefs = sampleProbes
    .filter((probe) => /keyframe/i.test(asString(probe.ref_kind, "")))
    .map((probe) => rawString(probe.ref));
  const sampleProbeEvidenceRefs = sampleProbes
    .filter((probe) => !/route|replay|keyframe/i.test(asString(probe.ref_kind, "")))
    .map((probe) => rawString(probe.ref));
  const nonEmpty = (values: string[]) => values.filter(Boolean);

  const rawRouteRefs = [
    ...nonEmpty(rawStringList(payload.route_refs)),
    ...nonEmpty([rawString(payload.route_ref)]),
    ...nonEmpty(rawStringList(asRecord(payload.refs)?.route_refs)),
    ...nonEmpty([rawString(asRecord(payload.refs)?.route_ref)]),
    ...sampleProbeRouteRefs,
  ];
  const rawReplayRefs = [
    ...nonEmpty(rawStringList(payload.replay_refs)),
    ...nonEmpty([rawString(payload.replay_ref)]),
    ...nonEmpty(rawStringList(asRecord(payload.refs)?.replay_refs)),
    ...nonEmpty([rawString(asRecord(payload.refs)?.replay_ref)]),
    ...sampleProbeReplayRefs,
  ];
  const rawKeyframeRefs = [
    ...nonEmpty(rawStringList(payload.keyframe_refs)),
    ...nonEmpty([rawString(payload.keyframe_ref)]),
    ...nonEmpty(rawStringList(asRecord(payload.refs)?.keyframe_refs)),
    ...nonEmpty([rawString(asRecord(payload.refs)?.keyframe_ref)]),
    ...sampleProbeKeyframeRefs,
  ];
  const rawEvidenceRefs = [
    ...nonEmpty(rawStringList(payload.evidence_refs)),
    ...nonEmpty([rawString(payload.evidence_ref)]),
    ...nonEmpty(rawStringList(asRecord(payload.refs)?.evidence_refs)),
    ...nonEmpty([rawString(asRecord(payload.refs)?.evidence_ref)]),
    ...nonEmpty(rawStringList(payload.sample_refs)),
    ...sampleProbeEvidenceRefs,
  ];
  const unsafeRefs = aggregateDistinct([
    rawRouteRefs.map((ref) => unsafeArtifactAccessRefReason(ref)),
    rawReplayRefs.map((ref) => unsafeArtifactAccessRefReason(ref)),
    rawKeyframeRefs.map((ref) => unsafeArtifactAccessRefReason(ref)),
    rawEvidenceRefs.map((ref) => unsafeArtifactAccessRefReason(ref)),
  ]);
  if (unsafeRefs.length > 0) {
    return blockedOfflineArtifactSeedSmoke("offline_artifact_seed_smoke_unsafe_ref", taskId);
  }
  const routeRefs = uniqueRefs(rawRouteRefs);
  const replayRefs = uniqueRefs(rawReplayRefs);
  const keyframeRefs = uniqueRefs(rawKeyframeRefs);
  const evidenceRefs = uniqueRefs(rawEvidenceRefs);
  const rawSampleRefs = uniqueRefs([
    ...routeRefs,
    ...replayRefs,
    ...keyframeRefs,
    ...evidenceRefs,
    ...uniqueRefs(sampleProbes.map((probe) => rawString(probe.ref))),
  ]);

  const sampleRefs = uniqueRefs([
    ...rawSampleRefs,
    ...rawStringList(payload.sample_refs),
    ...rawStringList(asRecord(payload.sample_refs)?.sample_refs),
    ...uniqueRefs(sampleProbes.map((probe) => rawString(probe.ref))),
  ]);
  const counts = asRecord(payload.counts);
  const sampleSha256Prefixes = uniqueStrings([
    ...rawStringList(payload.sample_sha256_prefixes).map((value) => sha256Prefix(value)),
    ...rawStringList(asRecord(payload.refs)?.sample_sha256_prefixes).map((value) => sha256Prefix(value)),
    ...sampleProbes.map((probe) => sha256Prefix(probe.sha256 ?? probe.sha256_prefix)),
  ]);
  const sampleProbeReadableCount = sampleProbes.filter((probe) => asBoolean(probe.exists)).length;
  const sampleProbeBlockedCount = sampleProbes.filter((probe) => asString(probe.blocked_reason, "none") !== "none").length;
  const sampleProbeMissingCount = sampleProbes.filter((probe) => !asBoolean(probe.exists)).length;
  const readableRefCount =
    asNumber(counts?.readable_ref_count) ??
    (sampleProbes.length > 0 ? sampleProbeReadableCount : sampleRefs.length) ??
    sampleRefs.length;
  const blockedRefCount =
    asNumber(counts?.blocked_ref_count) ??
    (sampleProbes.length > 0 ? sampleProbeBlockedCount : 0) ??
    0;
  const missingRefCount =
    asNumber(counts?.missing_ref_count) ??
    (sampleProbes.length > 0 ? sampleProbeMissingCount : 0) ??
    0;
  const routeRefCount = asNumber(counts?.route_ref_count) ?? routeRefs.length;
  const replayRefCount = asNumber(counts?.replay_ref_count) ?? replayRefs.length;
  const keyframeRefCount = asNumber(counts?.keyframe_ref_count) ?? keyframeRefs.length;
  const evidenceRefCount = asNumber(counts?.evidence_ref_count) ?? evidenceRefs.length;
  const sampleRefCount =
    asNumber(counts?.sample_ref_count) ?? sampleRefs.length;
  const blockedReasons = aggregateDistinct([
    stringList(payload.blocked_reasons),
    sampleProbes
      .map((probe) => safeArtifactAccessReason(probe.blocked_reason, "blocked_not_proven"))
      .filter((reason) => reason && reason !== "none"),
    "local_mock_only",
    "not_proven",
  ]);
  const nextRequiredEvidence = stringList(payload.next_required_evidence).length
    ? stringList(payload.next_required_evidence)
    : ["real_or_offline_artifact_seed_smoke_for_selected_task"];
  const proofBoundary = asRecord(payload.proof_boundary);
  const status =
    asString(payload.status, "") === "local_mock_offline_artifact_seed_smoke_ready"
      ? "local_mock_offline_artifact_seed_smoke_ready"
      : blockedReasons.length > 2
        ? "derived_blocked_not_proven"
        : "blocked_not_proven";
  return {
    schema: O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA,
    status,
    task_id: asString(payload.task_id, taskId || "not_provided"),
    source_contract: O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    proof_scope: O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE,
    allowlist_root_echoed: false,
    counts: {
      route_ref_count: routeRefCount,
      replay_ref_count: replayRefCount,
      keyframe_ref_count: keyframeRefCount,
      evidence_ref_count: evidenceRefCount,
      sample_ref_count: sampleRefCount,
      readable_ref_count: readableRefCount,
      blocked_ref_count: blockedRefCount,
      missing_ref_count: missingRefCount,
    },
    sample_probes: sampleProbes.slice(0, MVP_REF_SAMPLE_LIMIT).map((probe) => ({
      task_id: asString(probe.task_id, taskId || "not_provided"),
      ref_kind: asString(probe.ref_kind, "artifact"),
      ref: safeArtifactAccessRef(probe.ref),
      exists: asBoolean(probe.exists),
      size_bytes: asNumber(probe.size_bytes),
      sha256_prefix: sha256Prefix(probe.sha256 ?? probe.sha256_prefix),
      detected_type: asString(probe.detected_type, "unknown"),
      blocked_reason: safeArtifactAccessReason(probe.blocked_reason, "blocked_not_proven"),
      proof_scope: O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE,
    })),
    sample_refs: sampleRefs,
    sample_sha256_prefixes: sampleSha256Prefixes,
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    proof_boundary: {
      local_mock: asBoolean(proofBoundary?.local_mock) || true,
      not_proven: true,
      file_read_attempted: asBoolean(proofBoundary?.file_read_attempted),
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function buildArtifactAccessProbeSummary(
  candidate: ArtifactAccessProbeSourceResult | null,
  taskId: string,
): O7ConsumerArtifactAccessProbeSummary {
  // O7 只消费 O6 probe 的安全摘要，不回显 allowlist root、原始 ref、文件内容或完整 sha256。
  if (!candidate) {
    return blockedArtifactAccessProbe("artifact_access_probe_missing", taskId);
  }
  const payload = candidate.payload;
  if (asString(payload.schema, "") !== O6_ARTIFACT_ACCESS_PROBE_SCHEMA) {
    return blockedArtifactAccessProbe("artifact_access_probe_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return blockedArtifactAccessProbe(`artifact_access_probe_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  if (asBoolean(payload.allowlist_root_echoed)) {
    return blockedArtifactAccessProbe("artifact_access_probe_allowlist_root_echoed", taskId);
  }
  const allProbes = Array.isArray(payload.probes)
    ? payload.probes.map((probe) => asRecord(probe)).filter((probe): probe is JsonRecord => Boolean(probe))
    : [];
  const probes = allProbes.slice(0, MVP_REF_SAMPLE_LIMIT);
  const unsafeRefs = aggregateDistinct(allProbes.map((probe) => unsafeArtifactAccessRefReason(probe.ref)));
  if (unsafeRefs.length > 0) {
    return blockedArtifactAccessProbe(unsafeRefs[0] ?? "artifact_access_probe_unsafe_ref", taskId);
  }
  const counts = asRecord(payload.counts);
  const proofBoundary = asRecord(payload.proof_boundary);
  const safeSamples = probes.slice(0, 6).map((probe) => ({
    task_id: asString(probe.task_id, taskId || "not_provided"),
    ref_kind: asString(probe.ref_kind, "artifact"),
    ref: safeArtifactAccessRef(probe.ref),
    exists: asBoolean(probe.exists),
    size_bytes: asNumber(probe.size_bytes),
    sha256_prefix: sha256Prefix(probe.sha256),
    detected_type: asString(probe.detected_type, "unknown"),
    blocked_reason: safeArtifactAccessReason(probe.blocked_reason, asBoolean(probe.exists) ? "none" : "blocked_not_proven"),
    proof_scope: asString(probe.proof_scope, O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE),
  }));
  const blockedReasons = aggregateDistinct([
    stringList(payload.blocked_reasons),
    safeSamples.map((probe) => (probe.blocked_reason === "none" ? "" : probe.blocked_reason)),
    asString(payload.proof_scope, "") === O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE ? "" : "artifact_access_probe_proof_scope_mismatch",
    "local_mock_only",
    "not_proven",
  ]);
  return {
    schema: O6_ARTIFACT_ACCESS_PROBE_SCHEMA,
    status:
      asString(payload.status, "") === "local_mock_artifact_access_probe_ready"
        ? "local_mock_artifact_access_probe_ready"
        : "blocked_not_proven",
    task_id: asString(payload.task_id ?? safeSamples[0]?.task_id, taskId || "not_provided"),
    source_contract: O6_ARTIFACT_ACCESS_PROBE_SCHEMA,
    source_origin: candidate.source_origin,
    source_path: candidate.source_path,
    proof_scope: O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE,
    allowlist_root_configured: asBoolean(payload.allowlist_root_configured),
    allowlist_root_echoed: false,
    max_file_size_bytes: asNumber(payload.max_file_size_bytes),
    counts: {
      requested_ref_count: asNumber(counts?.requested_ref_count) ?? allProbes.length,
      readable_ref_count: asNumber(counts?.readable_ref_count) ?? safeSamples.filter((probe) => probe.exists).length,
      blocked_ref_count: asNumber(counts?.blocked_ref_count) ?? safeSamples.filter((probe) => probe.blocked_reason !== "none").length,
      missing_ref_count: asNumber(counts?.missing_ref_count) ?? safeSamples.filter((probe) => !probe.exists).length,
    },
    sample_probes: safeSamples,
    sample_refs: uniqueRefs(safeSamples.map((probe) => probe.ref)),
    sample_sha256_prefixes: uniqueRefs(safeSamples.map((probe) => probe.sha256_prefix)),
    blocked_reasons: blockedReasons,
    next_required_evidence: ["real_or_offline_artifact_access_probe_for_selected_task"],
    proof_boundary: {
      local_mock: asBoolean(proofBoundary?.local_mock) || true,
      not_proven: true,
      file_read_attempted: asBoolean(proofBoundary?.file_read_attempted),
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function artifactAccessProbeHardFailReason(probe: O7ConsumerArtifactAccessProbeSummary): string {
  // 不安全 probe 要让整个 detail fail-closed；缺失 probe 则留在 readiness blocked 状态里给 operator 补证据。
  const reason = probe.blocked_reasons[0] ?? "";
  return /^(artifact_access_probe_schema_mismatch|artifact_access_probe_dangerous_true|artifact_access_probe_unsafe_ref|artifact_access_probe_allowlist_root_echoed)/.test(
    reason,
  )
    ? reason
    : "";
}

function artifactBundleCandidateFromRemote(remote: JsonRecord): ArtifactBundleSourceResult | null {
  // bundle 主路径先看顶层 alias，再看 consumer_ingest / field_evidence / wrapper 的安全嵌套。
  const direct = asRecord(remote.artifact_bundle);
  if (direct) {
    return { payload: direct, source_origin: "remote_artifact_bundle", source_path: "artifact_bundle" };
  }
  const ingestBundle =
    nestedRecord(remote, "artifact_bundle_consumer_ingest", "artifact_bundle") ??
    nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest", "artifact_bundle") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "artifact_bundle") ??
    nestedRecord(remote, "field_evidence_ingest", "artifact_bundle");
  if (ingestBundle) {
    return {
      payload: ingestBundle,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest.artifact_bundle",
    };
  }
  const fieldEvidenceBundle =
    nestedRecord(remote, "field_evidence", "artifact_bundle") ??
    nestedRecord(remote, "field_evidence_consumer_ingest", "field_evidence_manifest", "artifact_bundle") ??
    nestedRecord(remote, "field_evidence_ingest", "field_evidence_manifest", "artifact_bundle");
  if (fieldEvidenceBundle) {
    return {
      payload: fieldEvidenceBundle,
      source_origin: "remote_field_evidence",
      source_path: "field_evidence.artifact_bundle",
    };
  }
  return null;
}

function artifactBundleConsumerIngestCandidateFromRemote(remote: JsonRecord): ArtifactBundleSourceResult | null {
  // consumer ingest 也允许从 wrapper 里下钻，但最终仍要输出 O6 归一摘要。
  const direct = asRecord(remote.artifact_bundle_consumer_ingest);
  if (direct) {
    return {
      payload: direct,
      source_origin: "remote_artifact_bundle_consumer_ingest",
      source_path: "artifact_bundle_consumer_ingest",
    };
  }
  const fieldEvidenceIngest =
    nestedRecord(remote, "field_evidence", "field_evidence_consumer_ingest") ??
    nestedRecord(remote, "field_evidence", "field_evidence_ingest") ??
    asRecord(remote.field_evidence_consumer_ingest) ??
    asRecord(remote.field_evidence_ingest);
  if (fieldEvidenceIngest) {
    return {
      payload: fieldEvidenceIngest,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence_consumer_ingest",
    };
  }
  const wrapped = nestedRecord(remote, "field_evidence", "artifact_bundle_consumer_ingest");
  if (wrapped) {
    return {
      payload: wrapped,
      source_origin: "remote_field_evidence_consumer_ingest",
      source_path: "field_evidence.artifact_bundle_consumer_ingest",
    };
  }
  return null;
}

function safeBundleRefs(value: unknown): string[] {
  // bundle 只允许保存 basename/token 级别 refs；绝对路径和危险 URL 会在调用方先 fail-closed。
  return rawStringList(value).map((ref) => safePathToken(ref));
}

function buildArtifactBundleSummary(
  candidate: ArtifactBundleSourceResult | null,
  taskId: string,
): O7ConsumerArtifactBundleSummary {
  // bundle summary 先占位 preflight，后续由主流程把真正的 O7 preflight 结果回填进去。
  if (!candidate) {
    return {
      schema: "not_loaded",
      task_origin: "not_loaded",
      bundle_status: "blocked_not_proven",
      request_summary: { task_id: taskId || "not_provided", robot_id: "not_provided", status: "blocked_not_proven" },
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      route_bag_payload_replay: blockedRouteBagPayloadReplay("artifact_bundle_missing", taskId),
      route_bag_semantic_replay: blockedRouteBagSemanticReplay("artifact_bundle_missing", taskId),
      route_bag_full_semantic_decode_matrix: blockedRouteBagFullSemanticDecodeMatrix("artifact_bundle_missing", taskId),
      route_bag_pose_progress_replay: blockedRouteBagPoseProgressReplay("artifact_bundle_missing", taskId),
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        "artifact_bundle_missing",
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket("artifact_bundle_missing", taskId),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket("artifact_bundle_missing", taskId),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback("artifact_bundle_missing", taskId),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        "artifact_bundle_missing",
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate("artifact_bundle_missing", taskId),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        "artifact_bundle_missing",
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist("artifact_bundle_missing", taskId),
      artifact_media_preflight: blockedArtifactMediaPreflight("artifact_bundle_missing", taskId),
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  const payload = candidate.payload;
  const routeBagPayloadReplay = buildRouteBagPayloadReplaySummary(routeBagPayloadReplayCandidateFromRemote(payload), taskId);
  const routeBagSemanticReplay = buildRouteBagSemanticReplaySummary(routeBagSemanticReplayCandidateFromRemote(payload), taskId);
  const routeBagFullSemanticDecodeMatrix = buildRouteBagFullSemanticDecodeMatrixSummary(
    routeBagFullSemanticDecodeMatrixCandidateFromRemote(payload),
    taskId,
  );
  const routeBagPoseProgressReplay = buildRouteBagPoseProgressReplaySummary(
    routeBagPoseProgressReplayCandidateFromRemote(payload),
    taskId,
  );
  const routeDeliveryClosurePacket = buildRouteDeliveryClosurePacketSummary(
    routeDeliveryClosurePacketCandidateFromRemote(payload),
    taskId,
  );
  const schema = asString(payload.schema, "");
  if (schema !== O6_ARTIFACT_BUNDLE_SCHEMA) {
    return {
      schema: "not_loaded",
      task_origin: "not_loaded",
      bundle_status: "artifact_bundle_schema_mismatch",
      request_summary: { task_id: taskId || "not_provided", robot_id: "not_provided", status: "artifact_bundle_schema_mismatch" },
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      route_bag_payload_replay: routeBagPayloadReplay,
      route_bag_semantic_replay: routeBagSemanticReplay,
      route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
      route_bag_pose_progress_replay: routeBagPoseProgressReplay,
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        "artifact_bundle_schema_mismatch",
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket("artifact_bundle_schema_mismatch", taskId),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket("artifact_bundle_schema_mismatch", taskId),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback("artifact_bundle_schema_mismatch", taskId),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        "artifact_bundle_schema_mismatch",
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate("artifact_bundle_schema_mismatch", taskId),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        "artifact_bundle_schema_mismatch",
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist(
        "artifact_bundle_schema_mismatch",
        taskId,
      ),
      artifact_media_preflight: blockedArtifactMediaPreflight("artifact_bundle_schema_mismatch", taskId),
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  const dangerous = scanDangerousTrueFields(payload);
  if (dangerous.length > 0) {
    return {
      schema: "not_loaded",
      task_origin: "not_loaded",
      bundle_status: `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
      request_summary: { task_id: taskId || "not_provided", robot_id: "not_provided", status: "artifact_bundle_dangerous_true" },
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      route_bag_payload_replay: routeBagPayloadReplay,
      route_bag_semantic_replay: routeBagSemanticReplay,
      route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
      route_bag_pose_progress_replay: routeBagPoseProgressReplay,
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist(
        `artifact_bundle_dangerous_true:${dangerous.join(",")}`,
        taskId,
      ),
      artifact_media_preflight: blockedArtifactMediaPreflight(`artifact_bundle_dangerous_true:${dangerous.join(",")}`, taskId),
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  const routeRefs = safeBundleRefs(payload.route_refs);
  const replayRefs = safeBundleRefs(payload.replay_refs);
  const keyframeRefs = safeBundleRefs(payload.keyframe_refs);
  const evidenceRefs = safeBundleRefs(payload.evidence_refs ?? payload.bundle_evidence_refs);
  const unsafeRefs = aggregateDistinct([
    rawStringList(payload.route_refs).map(unsafeMediaRefReason),
    rawStringList(payload.replay_refs).map(unsafeMediaRefReason),
    rawStringList(payload.keyframe_refs).map(unsafeMediaRefReason),
    rawStringList(payload.evidence_refs ?? payload.bundle_evidence_refs).map(unsafeMediaRefReason),
  ]);
  if (unsafeRefs.length > 0) {
    return {
      schema: "not_loaded",
      task_origin: "not_loaded",
      bundle_status: unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
      request_summary: { task_id: taskId || "not_provided", robot_id: "not_provided", status: "artifact_bundle_unsafe_ref" },
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      route_bag_payload_replay: routeBagPayloadReplay,
      route_bag_semantic_replay: routeBagSemanticReplay,
      route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
      route_bag_pose_progress_replay: routeBagPoseProgressReplay,
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket(unsafeRefs[0] ?? "artifact_bundle_unsafe_ref", taskId),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist(
        unsafeRefs[0] ?? "artifact_bundle_unsafe_ref",
        taskId,
      ),
      artifact_media_preflight: blockedArtifactMediaPreflight(unsafeRefs[0] ?? "artifact_bundle_unsafe_ref", taskId),
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  if (routeRefs.length === 0 && replayRefs.length === 0 && keyframeRefs.length === 0 && evidenceRefs.length === 0) {
    return {
      schema: "not_loaded",
      task_origin: "not_loaded",
      bundle_status: "artifact_bundle_empty_refs",
      request_summary: { task_id: taskId || "not_provided", robot_id: "not_provided", status: "artifact_bundle_empty_refs" },
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      route_bag_payload_replay: routeBagPayloadReplay,
      route_bag_semantic_replay: routeBagSemanticReplay,
      route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
      route_bag_pose_progress_replay: routeBagPoseProgressReplay,
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        "artifact_bundle_empty_refs",
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket("artifact_bundle_empty_refs", taskId),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket("artifact_bundle_empty_refs", taskId),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback("artifact_bundle_empty_refs", taskId),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        "artifact_bundle_empty_refs",
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate("artifact_bundle_empty_refs", taskId),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        "artifact_bundle_empty_refs",
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist("artifact_bundle_empty_refs", taskId),
      artifact_media_preflight: blockedArtifactMediaPreflight("artifact_bundle_empty_refs", taskId),
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  const requestSummary = asRecord(payload.request_summary);
  const routeExecutionResultDeliveryReadiness = buildRouteExecutionResultDeliveryReadinessSummary(
    routeExecutionResultDeliveryReadinessCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskFieldMaterialPacket = buildSameTaskFieldMaterialPacketSummary(
    sameTaskFieldMaterialPacketCandidateFromRemote(payload),
    taskId,
  );
  const localizationPathMaterialReadback = buildLocalizationPathMaterialReadbackSummary(
    localizationPathMaterialReadbackCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskRouteExecutionMaterialPacket = buildSameTaskRouteExecutionMaterialPacketSummary(
    sameTaskRouteExecutionMaterialPacketCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskMissionEvidenceGate = buildSameTaskMissionEvidenceGateSummary(
    sameTaskMissionEvidenceGateCandidateFromRemote(payload),
    taskId,
  );
  const fieldOperatorConfirmationMaterial = buildFieldOperatorConfirmationMaterialSummary(
    fieldOperatorConfirmationMaterialCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskMissionMaterialChecklist = buildSameTaskMissionMaterialChecklist(
    sameTaskFieldMaterialPacket,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    blockedDeliveryResultEvidence("artifact_bundle_readiness_pending_delivery_result_evidence", taskId),
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    routeBagPoseProgressReplay,
    taskId,
  );
  return {
    schema: O6_ARTIFACT_BUNDLE_SCHEMA,
    task_origin: "artifact_bundle",
    bundle_status: asString(payload.bundle_status, "local_mock_artifact_bundle_ready"),
    request_summary: {
      task_id: safePathToken((requestSummary?.task_id ?? taskId) || "not_provided"),
      robot_id: safePathToken(requestSummary?.robot_id ?? "not_provided"),
      status: asString(requestSummary?.status, "local_mock_artifact_bundle_ready"),
    },
    route_refs: routeRefs,
    replay_refs: replayRefs,
    keyframe_refs: keyframeRefs,
    evidence_refs: evidenceRefs,
    route_bag_payload_replay: routeBagPayloadReplay,
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    localization_path_material_readback: localizationPathMaterialReadback,
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: fieldOperatorConfirmationMaterial,
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_media_preflight: blockedArtifactMediaPreflight("artifact_bundle_readiness_pending_preflight", taskId),
    real_cloud_db_connected: false,
    real_oss_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function buildArtifactBundleConsumerIngestSummary(
  candidate: ArtifactBundleSourceResult | null,
  bundle: O7ConsumerArtifactBundleSummary,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
  taskId: string,
): O7ConsumerArtifactBundleConsumerIngestSummary {
  // consumer ingest 只补充来源和 gate 摘要，不扩大真实读写能力边界。
  if (!candidate) {
    return {
      schema: "not_loaded",
      status: "blocked_not_proven",
      task_origin: "not_loaded",
      run_id: "not_loaded",
      manifest_schema: "not_loaded",
      manifest_status: "blocked_not_proven",
      bundle_status: "blocked_not_proven",
      artifact_summary: { summary: "not_loaded", artifact_count: 0, gate_pass: false },
      field_evidence_summary: { run_id: "not_loaded", summary: "not_loaded", artifact_count: 0, gate_pass: false },
      manifest_gate: {
        schema: "not_loaded",
        status: "blocked_not_proven",
        gate_pass: false,
        blocked_reason: "artifact_bundle_consumer_ingest_missing",
        source: "not_loaded",
      },
      artifact_bundle: null,
      route_bag_payload_replay: blockedRouteBagPayloadReplay("artifact_bundle_consumer_ingest_missing", taskId),
      route_bag_semantic_replay: blockedRouteBagSemanticReplay("artifact_bundle_consumer_ingest_missing", taskId),
      route_bag_full_semantic_decode_matrix: blockedRouteBagFullSemanticDecodeMatrix(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      route_bag_pose_progress_replay: blockedRouteBagPoseProgressReplay("artifact_bundle_consumer_ingest_missing", taskId),
      route_execution_result_delivery_readiness: blockedRouteExecutionResultDeliveryReadiness(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      route_delivery_closure_packet: blockedRouteDeliveryClosurePacket(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      same_task_field_material_packet: blockedSameTaskFieldMaterialPacket(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      localization_path_material_readback: blockedLocalizationPathMaterialReadback(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      same_task_route_execution_material_packet: blockedSameTaskRouteExecutionMaterialPacket(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      same_task_mission_evidence_gate: blockedSameTaskMissionEvidenceGate(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      field_operator_confirmation_material: blockedFieldOperatorConfirmationMaterial(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      same_task_mission_material_checklist: blockedSameTaskMissionMaterialChecklist(
        "artifact_bundle_consumer_ingest_missing",
        taskId,
      ),
      artifact_media_preflight: artifactMediaPreflight,
      real_cloud_db_connected: false,
      real_oss_connected: false,
      ...fixedFalseFields(),
      ...PROOF_FLAGS,
    };
  }
  const payload = candidate.payload;
  const schema = asString(payload.schema, "");
  const ingestSchema =
    schema === O6_ARTIFACT_BUNDLE_CONSUMER_INGEST_SCHEMA
      ? O6_ARTIFACT_BUNDLE_CONSUMER_INGEST_SCHEMA
      : O6_ARTIFACT_BUNDLE_CONSUMER_INGEST_SCHEMA;
  const status = asString(payload.status, "local_mock_artifact_bundle_ready");
  const manifestGate = asRecord(payload.manifest_gate);
  const artifactSummary = asRecord(payload.artifact_summary);
  const fieldEvidenceSummary = asRecord(payload.field_evidence_summary);
  const routeBagPayloadReplay = buildRouteBagPayloadReplaySummary(routeBagPayloadReplayCandidateFromRemote(payload), taskId);
  const routeBagSemanticReplay = buildRouteBagSemanticReplaySummary(routeBagSemanticReplayCandidateFromRemote(payload), taskId);
  const routeBagFullSemanticDecodeMatrix = buildRouteBagFullSemanticDecodeMatrixSummary(
    routeBagFullSemanticDecodeMatrixCandidateFromRemote(payload),
    taskId,
  );
  const routeBagPoseProgressReplay = buildRouteBagPoseProgressReplaySummary(
    routeBagPoseProgressReplayCandidateFromRemote(payload),
    taskId,
  );
  const routeExecutionResultDeliveryReadiness = buildRouteExecutionResultDeliveryReadinessSummary(
    routeExecutionResultDeliveryReadinessCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskFieldMaterialPacket = buildSameTaskFieldMaterialPacketSummary(
    sameTaskFieldMaterialPacketCandidateFromRemote(payload),
    taskId,
  );
  const localizationPathMaterialReadback = buildLocalizationPathMaterialReadbackSummary(
    localizationPathMaterialReadbackCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskRouteExecutionMaterialPacket = buildSameTaskRouteExecutionMaterialPacketSummary(
    sameTaskRouteExecutionMaterialPacketCandidateFromRemote(payload),
    taskId,
  );
  const routeDeliveryClosurePacket = buildRouteDeliveryClosurePacketSummary(
    routeDeliveryClosurePacketCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskMissionEvidenceGate = buildSameTaskMissionEvidenceGateSummary(
    sameTaskMissionEvidenceGateCandidateFromRemote(payload),
    taskId,
  );
  const fieldOperatorConfirmationMaterial = buildFieldOperatorConfirmationMaterialSummary(
    fieldOperatorConfirmationMaterialCandidateFromRemote(payload),
    taskId,
  );
  const sameTaskMissionMaterialChecklist = buildSameTaskMissionMaterialChecklist(
    sameTaskFieldMaterialPacket,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    blockedDeliveryResultEvidence("artifact_bundle_consumer_ingest_pending_delivery_result_evidence", taskId),
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    routeBagPoseProgressReplay,
    taskId,
  );
  return {
    schema: ingestSchema,
    status,
    task_origin: asString(payload.task_origin, "artifact_bundle") as "artifact_bundle" | "field_evidence_manifest" | "not_loaded",
    run_id: asString(payload.run_id, taskId || "not_provided"),
    manifest_schema: asString(payload.manifest_schema, O6_ARTIFACT_BUNDLE_SCHEMA) as
      | "trashbot.o6.artifact_bundle.v1"
      | "trashbot.field_evidence_manifest.v1"
      | "not_loaded",
    manifest_status: asString(payload.manifest_status, "blocked_not_proven"),
    bundle_status: asString(payload.bundle_status, bundle.bundle_status),
    artifact_summary: {
      summary: asString(artifactSummary?.summary, bundle.bundle_status),
      artifact_count: asNumber(artifactSummary?.artifact_count) ?? routeRefsLength(bundle),
      gate_pass: asBoolean(artifactSummary?.gate_pass),
    },
    field_evidence_summary: {
      run_id: asString(fieldEvidenceSummary?.run_id, taskId || "not_provided"),
      summary: asString(fieldEvidenceSummary?.summary, bundle.bundle_status),
      artifact_count: asNumber(fieldEvidenceSummary?.artifact_count) ?? routeRefsLength(bundle),
      gate_pass: asBoolean(fieldEvidenceSummary?.gate_pass),
    },
    manifest_gate: {
      schema: asString(manifestGate?.schema, O6_ARTIFACT_BUNDLE_SCHEMA) as
        | "trashbot.o6.artifact_bundle.v1"
        | "trashbot.field_evidence_manifest.v1"
        | "not_loaded",
      status: asString(manifestGate?.status, "blocked_not_proven"),
      gate_pass: asBoolean(manifestGate?.gate_pass),
      blocked_reason: asString(manifestGate?.blocked_reason, "artifact_bundle_consumer_ingest_blocked"),
      source: asString(manifestGate?.source, candidate.source_origin),
    },
    artifact_bundle: bundle,
    route_bag_payload_replay: routeBagPayloadReplay,
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    localization_path_material_readback: localizationPathMaterialReadback,
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: fieldOperatorConfirmationMaterial,
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_media_preflight: artifactMediaPreflight,
    real_cloud_db_connected: false,
    real_oss_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function routeRefsLength(bundle: O7ConsumerArtifactBundleSummary): number {
  // 让 ingest 的简单计数复用 bundle 里的安全 refs，避免两个摘要各算各的。
  return Math.max(bundle.route_refs.length, bundle.replay_refs.length, bundle.keyframe_refs.length, bundle.evidence_refs.length);
}

function artifactBundleReadinessRefs(
  bundle: O7ConsumerArtifactBundleSummary,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
  labeling: O7ConsumerLabelingMvp | null,
): O7ConsumerArtifactBundleReadiness["refs"] {
  // readiness 里优先展示 bundle/preflight 已读到的 refs，旧 detail 只做兼容兜底。
  const labelingReviewItems = labeling?.review_items?.sample ?? [];
  const routeRefs = uniqueRefs([
    ...bundle.route_refs,
    artifactMediaPreflight.route_replay_dependency.route_ref,
    ...artifactMediaPreflight.route_replay_dependency.sample_refs,
    ...artifactMediaPreflight.labeling_dependency.sample_refs,
  ]);
  const replayRefs = uniqueRefs([
    ...bundle.replay_refs,
    artifactMediaPreflight.route_replay_dependency.replay_ref,
  ]);
  const keyframeRefs = uniqueRefs([
    ...bundle.keyframe_refs,
    artifactMediaPreflight.route_replay_dependency.keyframe_ref,
  ]);
  const evidenceRefs = uniqueRefs([
    ...bundle.evidence_refs,
    ...artifactMediaPreflight.route_replay_dependency.sample_refs,
    ...artifactMediaPreflight.labeling_dependency.sample_refs,
  ]);
  const reviewItemMediaRefs = uniqueRefs([
    ...artifactMediaPreflight.labeling_dependency.review_item_media_refs,
    ...labelingReviewItems.map((item) => item.media_ref),
  ]);
  const sampleRefs = uniqueRefs([...routeRefs, ...replayRefs, ...keyframeRefs, ...evidenceRefs, ...reviewItemMediaRefs]);
  return {
    route_refs: routeRefs,
    replay_refs: replayRefs,
    keyframe_refs: keyframeRefs,
    evidence_refs: evidenceRefs,
    review_item_media_refs: reviewItemMediaRefs,
    sample_refs: sampleRefs,
  };
}

function artifactBundleReadinessBlockedReasons(
  bundle: O7ConsumerArtifactBundleSummary,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
  artifactAccessProbe: O7ConsumerArtifactAccessProbeSummary,
  offlineArtifactSeedSmoke: O7ConsumerOfflineArtifactSeedSmokeSummary,
  routeRootSeedGate: O7ConsumerRouteRootSeedGateSummary,
  routeBagEvidence: O7ConsumerRouteBagEvidenceSummary,
  routeBagPayloadReplay: O7ConsumerRouteBagPayloadReplaySummary,
  routeBagSemanticReplay: O7ConsumerRouteBagSemanticReplaySummary,
  routeBagFullSemanticDecodeMatrix: O7ConsumerRouteBagFullSemanticDecodeMatrixSummary,
  routeBagPoseProgressReplay: O7ConsumerRouteBagPoseProgressReplaySummary,
  nav2GoalExecutionEvidence: O7ConsumerNav2GoalExecutionEvidenceSummary,
  deliveryResultEvidence: O7ConsumerDeliveryResultEvidenceSummary,
  routeExecutionResultDeliveryReadiness: O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
  routeDeliveryClosurePacket: O7ConsumerRouteDeliveryClosurePacketSummary,
  sameTaskFieldMaterialPacket: O7ConsumerSameTaskFieldMaterialPacketSummary,
  localizationPathMaterialReadback: O7ConsumerLocalizationPathMaterialReadbackSummary,
  sameTaskRouteExecutionMaterialPacket: O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
  sameTaskMissionEvidenceGate: O7ConsumerSameTaskMissionEvidenceGateSummary,
  fieldOperatorConfirmationMaterial: O7ConsumerFieldOperatorConfirmationMaterialSummary,
  refs: O7ConsumerArtifactBundleReadiness["refs"],
  requestedTaskId: string,
): string[] {
  // readiness 的阻塞原因先读 bundle/preflight，再保留旧 fallback 以兼容缺字段 fixture。
  return aggregateDistinct([
    bundle.bundle_status === "local_mock_artifact_bundle_ready" ? "" : bundle.bundle_status,
    artifactAccessProbe.blocked_reasons,
    artifactAccessProbe.schema === O6_ARTIFACT_ACCESS_PROBE_SCHEMA ? "" : "artifact_access_probe_missing",
    offlineArtifactSeedSmoke.blocked_reasons,
    offlineArtifactSeedSmoke.schema === O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA ? "" : "offline_artifact_seed_smoke_missing",
    routeRootSeedGate.blocked_reasons,
    routeRootSeedGate.schema === O6_ROUTE_ROOT_SEED_GATE_SCHEMA ? "" : "route_root_seed_gate_missing",
    routeBagEvidence.blocked_reasons,
    routeBagEvidence.schema === ROUTE_BAG_EVIDENCE_SCHEMA || routeBagEvidence.schema === O6_ROUTE_BAG_EVIDENCE_SCHEMA
      ? ""
      : "route_bag_evidence_missing",
    routeBagPayloadReplay.blocked_reasons,
    routeBagPayloadReplay.schema === ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA ||
    routeBagPayloadReplay.schema === O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA
      ? ""
      : "route_bag_payload_replay_missing",
    routeBagSemanticReplay.blocked_reasons,
    routeBagSemanticReplay.schema === ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA ||
    routeBagSemanticReplay.schema === O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA
      ? ""
      : "route_bag_semantic_replay_missing",
    routeBagFullSemanticDecodeMatrix.blocked_reasons,
    routeBagFullSemanticDecodeMatrix.schema === ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA ||
    routeBagFullSemanticDecodeMatrix.schema === O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA
      ? ""
      : "route_bag_full_semantic_decode_matrix_missing",
    routeBagPoseProgressReplay.blocked_reasons,
    routeBagPoseProgressReplay.schema === ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA ||
    routeBagPoseProgressReplay.schema === O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA
      ? ""
      : "route_bag_pose_progress_replay_missing",
    nav2GoalExecutionEvidence.blocked_reasons,
    nav2GoalExecutionEvidence.schema === NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA
      ? ""
      : "nav2_goal_execution_evidence_missing",
    deliveryResultEvidence.blocked_reasons,
    deliveryResultEvidence.schema === DELIVERY_RESULT_EVIDENCE_SCHEMA ? "" : "delivery_result_evidence_missing",
    routeExecutionResultDeliveryReadiness.blocked_reasons,
    routeExecutionResultDeliveryReadiness.schema === O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA
      ? ""
      : "route_execution_result_delivery_readiness_missing",
    routeDeliveryClosurePacket.blocked_reasons,
    routeDeliveryClosurePacket.schema === O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA
      ? ""
      : "route_delivery_closure_packet_missing",
    sameTaskFieldMaterialPacket.blocked_reasons,
    sameTaskFieldMaterialPacket.schema === O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA ||
    sameTaskFieldMaterialPacket.schema === SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
      ? ""
      : "same_task_field_material_packet_missing",
    localizationPathMaterialReadback.blocked_reasons,
    localizationPathMaterialReadback.schema === O7_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA
      ? ""
      : "localization_path_material_readback_missing",
    sameTaskRouteExecutionMaterialPacket.blocked_reasons,
    sameTaskRouteExecutionMaterialPacket.schema === O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA ||
    sameTaskRouteExecutionMaterialPacket.schema === SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA
      ? ""
      : "same_task_route_execution_material_packet_missing",
    sameTaskMissionEvidenceGate.blocked_reasons,
    sameTaskMissionEvidenceGate.schema === O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA ||
    sameTaskMissionEvidenceGate.schema === SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA
      ? ""
      : "same_task_mission_evidence_gate_missing",
    fieldOperatorConfirmationMaterial.blocked_reasons,
    fieldOperatorConfirmationMaterial.schema === O7_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA
      ? ""
      : "field_operator_confirmation_material_missing",
    artifactMediaPreflight.blocked_reasons,
    artifactMediaPreflight.route_replay_dependency.blocked_reasons,
    artifactMediaPreflight.labeling_dependency.blocked_reasons,
    refs.route_refs.length > 0 ? "" : "route_refs_missing",
    refs.replay_refs.length > 0 ? "" : "replay_refs_missing",
    refs.keyframe_refs.length > 0 ? "" : "keyframe_refs_missing",
    refs.evidence_refs.length > 0 ? "" : "evidence_refs_missing",
    refs.review_item_media_refs.length > 0 ? "" : "review_item_media_refs_missing",
    requestedTaskId.trim() ? "" : "task_id_missing",
  ]);
}

function blockedArtifactBundleReadiness(
  reason: string,
  taskId: string,
  artifactAccessProbe = blockedArtifactAccessProbe(reason, taskId),
  offlineArtifactSeedSmoke = blockedOfflineArtifactSeedSmoke(reason, taskId),
  routeRootSeedGate = blockedRouteRootSeedGate(reason, taskId),
  routeBagEvidence = blockedRouteBagEvidence(reason, taskId),
  routeBagPayloadReplay = blockedRouteBagPayloadReplay(reason, taskId),
  routeBagSemanticReplay = blockedRouteBagSemanticReplay(reason, taskId),
  routeBagFullSemanticDecodeMatrix = blockedRouteBagFullSemanticDecodeMatrix(reason, taskId),
  routeBagPoseProgressReplay = blockedRouteBagPoseProgressReplay(reason, taskId),
  fieldMotionEvidencePacket = blockedFieldMotionEvidencePacket(reason, taskId),
  nav2GoalExecutionEvidence = blockedNav2GoalExecutionEvidence(reason, taskId),
  deliveryResultEvidence = blockedDeliveryResultEvidence(reason, taskId),
  routeExecutionResultDeliveryReadiness = blockedRouteExecutionResultDeliveryReadiness(reason, taskId),
  routeDeliveryClosurePacket = blockedRouteDeliveryClosurePacket(reason, taskId),
  sameTaskFieldMaterialPacket = blockedSameTaskFieldMaterialPacket(reason, taskId),
  localizationPathMaterialReadback = blockedLocalizationPathMaterialReadback(reason, taskId),
  sameTaskRouteExecutionMaterialPacket = blockedSameTaskRouteExecutionMaterialPacket(reason, taskId),
  sameTaskMissionEvidenceGate = blockedSameTaskMissionEvidenceGate(reason, taskId),
  fieldOperatorConfirmationMaterial = blockedFieldOperatorConfirmationMaterial(reason, taskId),
  sameTaskMissionMaterialChecklist = blockedSameTaskMissionMaterialChecklist(reason, taskId, sameTaskMissionEvidenceGate),
): O7ConsumerArtifactBundleReadiness {
  // fail-closed 时也要给出同结构 readiness，避免 UI 通过缺字段误判为旧 debug 路径。
  const blockedArtifactMedia = blockedArtifactMediaPreflight(reason, taskId);
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_artifact_bundle_readiness.v1",
    status: "blocked_not_proven",
    selected_task_id: taskId || "not_provided",
    source_detail_task_id: taskId || "not_provided",
    source_contract: "not_loaded",
    source_origin: "not_loaded",
    task_id: taskId || "not_provided",
    bundle_status: "blocked_not_proven",
    counts: {
      route_ref_count: 0,
      replay_ref_count: 0,
      keyframe_ref_count: 0,
      evidence_ref_count: 0,
      review_item_count: 0,
      sample_ref_count: 0,
      review_item_media_ref_count: 0,
    },
    refs: {
      route_refs: [],
      replay_refs: [],
      keyframe_refs: [],
      evidence_refs: [],
      review_item_media_refs: [],
      sample_refs: [],
    },
      blocked_reasons: [reason],
    next_required_evidence: aggregateDistinct([
      blockedArtifactMedia.next_required_evidence,
      artifactAccessProbe.next_required_evidence,
      offlineArtifactSeedSmoke.next_required_evidence,
      routeRootSeedGate.next_required_evidence,
      routeBagEvidence.next_required_evidence,
      routeBagPayloadReplay.next_required_evidence,
      routeBagSemanticReplay.next_required_evidence,
      routeBagFullSemanticDecodeMatrix.next_required_evidence,
      routeBagPoseProgressReplay.next_required_evidence,
      nav2GoalExecutionEvidence.next_required_evidence,
      deliveryResultEvidence.next_required_evidence,
      routeExecutionResultDeliveryReadiness.next_required_evidence,
      routeDeliveryClosurePacket.next_required_evidence,
      sameTaskFieldMaterialPacket.next_required_evidence,
      localizationPathMaterialReadback.next_required_evidence,
      sameTaskRouteExecutionMaterialPacket.next_required_evidence,
      sameTaskMissionEvidenceGate.next_required_evidence,
      fieldOperatorConfirmationMaterial.next_required_evidence,
      sameTaskMissionMaterialChecklist.next_required_evidence,
    ]),
    route_bag_evidence: routeBagEvidence,
    route_bag_payload_replay: routeBagPayloadReplay,
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_root_seed_gate: routeRootSeedGate,
    field_motion_evidence_packet: fieldMotionEvidencePacket,
    nav2_goal_execution_evidence: nav2GoalExecutionEvidence,
    delivery_result_evidence: deliveryResultEvidence,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    localization_path_material_readback: localizationPathMaterialReadback,
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: fieldOperatorConfirmationMaterial,
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_access_probe: artifactAccessProbe,
    offline_artifact_seed_smoke: offlineArtifactSeedSmoke,
    artifact_media_preflight: blockedArtifactMedia,
    route_replay_dependency: blockedArtifactMedia.route_replay_dependency,
    labeling_dependency: blockedArtifactMedia.labeling_dependency,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
}

function mediaDependency(
  routeRef: string,
  replayRef: string,
  keyframeRef: string,
  sampleRefs: string[],
  reviewItemMediaRefs: string[],
  blockedReasons: string[],
  nextRequiredEvidence: string[],
  status: string,
): O7ConsumerArtifactMediaDependency {
  // 依赖摘要固定把媒体可访问性锁死为 false；sample refs 只是 operator 下一步该补什么的线索。
  return {
    status,
    route_ref: routeRef || "blocked_not_proven",
    replay_ref: replayRef || "blocked_not_proven",
    keyframe_ref: keyframeRef || "blocked_not_proven",
    sample_refs: sampleRefs,
    review_item_media_refs: reviewItemMediaRefs,
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
  };
}

function artifactMediaSampleRefs(record: JsonRecord | null): string[] {
  // O6 preflight sample_refs 目前是命名字段 object；这里只摘 route/replay/keyframe 和任何显式数组样本。
  if (!record) {
    return [];
  }
  return uniqueRefs([
    rawString(record.route_ref),
    rawString(record.replay_ref),
    rawString(record.keyframe_ref),
    ...rawStringList(record.sample_refs),
  ]);
}

function mvpRouteFrame(value: unknown, cursorIndex: number): O7ConsumerRouteReplayMvpFrame {
  // route replay MVP 帧只暴露位姿、速度、状态和证据引用；原始 frame payload 不透传。
  const frame = asRecord(value) ?? {};
  const pose = asRecord(frame.pose);
  const velocity = asRecord(frame.velocity);
  const frameIndex = asNumber(frame.frame_index ?? frame.frameIndex ?? frame.index) ?? cursorIndex;
  return {
    frame_index: Math.trunc(frameIndex),
    cursor_index: cursorIndex,
    timestamp_ms: asNumber(frame.timestamp_ms ?? frame.timestampMs ?? frame.t_ms),
    pose: {
      x_m: asNumber(frame.x_m ?? pose?.x_m ?? pose?.x ?? pose?.xM),
      y_m: asNumber(frame.y_m ?? pose?.y_m ?? pose?.y ?? pose?.yM),
      yaw_rad: asNumber(frame.yaw_rad ?? pose?.yaw_rad ?? pose?.yaw ?? pose?.yawRad),
    },
    velocity: {
      linear_mps: asNumber(frame.speed_mps ?? frame.linear_mps ?? velocity?.linear_mps ?? velocity?.linear ?? velocity?.speed_mps),
      angular_radps: asNumber(frame.angular_radps ?? frame.angular_mps ?? velocity?.angular_radps ?? velocity?.wz_radps),
    },
    state: asString(frame.state ?? frame.status ?? frame.event_type, "not_provided"),
    evidence_ref: safePathToken(frame.evidence_ref ?? frame.evidenceRef ?? frame.media_ref ?? ""),
    keyframe_ref: safePathToken(frame.keyframe_ref ?? frame.keyframeRef ?? frame.evidence_ref ?? ""),
  };
}

function mvpRouteEvent(value: unknown): O7ConsumerRouteReplayMvpEvent {
  // events timeline 保持事件类型、状态、时间和证据四个字段，便于和当前帧并排审阅。
  const event = asRecord(value) ?? {};
  return {
    event_type: asString(event.event_type ?? event.type, "event_type_missing"),
    state: asString(event.state ?? event.status, "state_missing"),
    timestamp_ms: asNumber(event.timestamp_ms ?? event.timestampMs ?? event.t_ms),
    evidence_ref: safePathToken(event.evidence_ref ?? event.evidenceRef ?? ""),
  };
}

function routeReplayMvpRefs(
  frames: O7ConsumerRouteReplayMvpFrame[],
  events: O7ConsumerRouteReplayMvpEvent[],
  evidenceItems: JsonRecord[],
  manifest: O7FieldEvidenceManifestSummary,
): { sample_refs: string[]; keyframe_refs: string[] } {
  // evidence_refs 同时来自帧、事件、evidence section 和 field_evidence artifact，保证同一 task_id 证据链不断裂。
  const evidenceRefs = uniqueRefs([
    ...frames.map((frame) => frame.evidence_ref),
    ...events.map((event) => event.evidence_ref),
    ...evidenceItems.flatMap((item) => [
      asString(item.evidence_ref ?? item.evidenceRef ?? item.media_ref, ""),
      asString(item.ref ?? item.object_ref, ""),
    ]),
    manifest.artifacts.replay_jsonl.path,
  ]);
  const keyframeRefs = uniqueRefs([
    ...frames.map((frame) => frame.keyframe_ref),
    ...evidenceItems
      .filter((item) => /keyframe/i.test(asString(item.evidence_type ?? item.type, "")))
      .map((item) => asString(item.evidence_ref ?? item.evidenceRef ?? item.media_ref, "")),
    manifest.artifacts.keyframes.path,
  ]);
  return { sample_refs: evidenceRefs, keyframe_refs: keyframeRefs };
}

function artifactMediaPreflightSource(remote: JsonRecord): JsonRecord | null {
  // O6 可能把 preflight 放在顶层 consumer detail，也可能挂在 field_evidence / ingest 摘要下。
  const wrappedFieldEvidence = asRecord(remote.field_evidence);
  const fieldEvidenceIngest =
    asRecord(remote.field_evidence_consumer_ingest) ??
    asRecord(remote.field_evidence_ingest) ??
    asRecord(wrappedFieldEvidence?.field_evidence_consumer_ingest);
  return (
    asRecord(remote.artifact_media_preflight) ??
    asRecord(wrappedFieldEvidence?.artifact_media_preflight) ??
    asRecord(fieldEvidenceIngest?.artifact_media_preflight) ??
    asRecord(asRecord(fieldEvidenceIngest?.field_evidence_manifest)?.artifact_media_preflight) ??
    asRecord(asRecord(remote.field_evidence_manifest)?.artifact_media_preflight)
  );
}

function buildConsumerArtifactMediaPreflight(
  remote: JsonRecord,
  manifest: O7FieldEvidenceManifestSummary,
  requestedTaskId: string,
  artifactBundle: O7ConsumerArtifactBundleSummary | null = null,
): O7ConsumerArtifactMediaPreflight {
  // 优先消费 O6 主路径的 artifact_media_preflight；缺失时再从 manifest/trajectory/labeling 派生保守摘要。
  const taskSummary = asRecord(remote.task_summary);
  const taskId = asString(taskSummary?.task_id, requestedTaskId || "not_provided");
  const routeReplay = buildConsumerRouteReplayMvp(remote, manifest, taskId, blockedArtifactMediaPreflight("artifact_media_preflight_bootstrap", taskId));
  const labeling = buildConsumerLabelingMvp(remote, taskId, blockedArtifactMediaPreflight("artifact_media_preflight_bootstrap", taskId));
  const bundleRouteRef = artifactBundle?.route_refs[0] ?? "";
  const bundleReplayRef = artifactBundle?.replay_refs[0] ?? "";
  const bundleKeyframeRef = artifactBundle?.keyframe_refs[0] ?? "";
  const derivedRouteRef = bundleRouteRef || (manifest.artifacts.route_csv.present ? manifest.artifacts.route_csv.path : "");
  const derivedReplayRef = bundleReplayRef || (manifest.artifacts.replay_jsonl.present ? manifest.artifacts.replay_jsonl.path : "");
  const derivedKeyframeRef = bundleKeyframeRef || (manifest.artifacts.keyframes.present ? manifest.artifacts.keyframes.path : "");
  const derivedReviewMediaRefs = uniqueRefs((labeling?.review_items?.sample ?? []).map((item) => item.media_ref));
  const candidate = artifactMediaPreflightSource(remote);
  if (!candidate) {
    const routeBlockedReasons = aggregateDistinct([
      derivedRouteRef ? "" : "route_ref_missing",
      derivedReplayRef ? "" : "replay_ref_missing",
      derivedKeyframeRef ? "" : "keyframe_ref_missing",
      routeReplay.evidence_refs.sample_refs.length > 0 ? "" : "route_replay_sample_refs_missing",
      "local_mock_only",
      "not_proven",
    ]);
    const labelingBlockedReasons = aggregateDistinct([
      derivedReviewMediaRefs.length > 0 ? "" : "review_item_media_refs_missing",
      "local_mock_only",
      "not_proven",
    ]);
    const nextRequiredEvidence = [
      "real_keyframe_media_access_probe_without_credentials",
      "review_item_media_capture_for_selected_task",
      "oss_or_cdn_read_probe_without_query_or_tokens",
    ];
    return {
      schema: "not_loaded",
      status: "derived_blocked_not_proven",
      task_id: taskId,
      consumer_section_names: [...O6_MEDIA_PREFLIGHT_SECTION_NAMES],
      counts: {
        route_ref_count: derivedRouteRef ? 1 : 0,
        replay_ref_count: derivedReplayRef ? 1 : 0,
        keyframe_ref_count: derivedKeyframeRef ? 1 : 0,
        sample_ref_count: routeReplay.evidence_refs.sample_refs.length,
        review_item_media_ref_count: derivedReviewMediaRefs.length,
      },
      route_replay_dependency: mediaDependency(
        derivedRouteRef,
        derivedReplayRef,
        derivedKeyframeRef,
        uniqueRefs([
          ...(artifactBundle?.route_refs ?? []),
          ...(artifactBundle?.replay_refs ?? []),
          ...(artifactBundle?.keyframe_refs ?? []),
          ...(artifactBundle?.evidence_refs ?? []),
          ...routeReplay.evidence_refs.sample_refs,
        ]),
        [],
        routeBlockedReasons,
        nextRequiredEvidence,
        "derived_blocked_not_proven",
      ),
      labeling_dependency: mediaDependency(
        derivedRouteRef,
        derivedReplayRef,
        derivedKeyframeRef,
        uniqueRefs([
          ...(artifactBundle?.route_refs ?? []),
          ...(artifactBundle?.replay_refs ?? []),
          ...(artifactBundle?.keyframe_refs ?? []),
          ...(artifactBundle?.evidence_refs ?? []),
          ...routeReplay.evidence_refs.sample_refs,
        ]),
        derivedReviewMediaRefs,
        labelingBlockedReasons,
        nextRequiredEvidence,
        "derived_blocked_not_proven",
      ),
      proof_boundary: {
        local_mock: true,
        not_proven: true,
        real_media_read_executed: false,
        real_oss_connected: false,
        real_cdn_connected: false,
      },
      blocked_reasons: aggregateDistinct([
        "artifact_media_preflight_missing",
        "local_mock_only",
        "not_proven",
      ]),
      next_required_evidence: nextRequiredEvidence,
      media_access_proven: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    };
  }

  if (asString(candidate.schema, "") !== O6_ARTIFACT_MEDIA_PREFLIGHT_SCHEMA) {
    return blockedArtifactMediaPreflight("artifact_media_preflight_schema_mismatch", taskId);
  }
  const dangerous = scanDangerousTrueFields(candidate);
  if (dangerous.length > 0) {
    return blockedArtifactMediaPreflight(`artifact_media_preflight_dangerous_true:${dangerous.join(",")}`, taskId);
  }
  const unsafeRefs = aggregateDistinct([
    unsafeMediaRefReason(asRecord(candidate.sample_refs)?.route_ref),
    unsafeMediaRefReason(asRecord(candidate.sample_refs)?.replay_ref),
    unsafeMediaRefReason(asRecord(candidate.sample_refs)?.keyframe_ref),
    rawStringList(asRecord(candidate.sample_refs)?.sample_refs).map((refValue) => unsafeMediaRefReason(refValue)),
  ]);
  if (unsafeRefs.length > 0) {
    return blockedArtifactMediaPreflight(unsafeRefs[0] ?? "artifact_media_preflight_unsafe_ref", taskId);
  }

  const counts = asRecord(candidate.counts);
  const sampleRefs = asRecord(candidate.sample_refs);
  const routeRef = safePathToken(sampleRefs?.route_ref ?? derivedRouteRef);
  const replayRef = safePathToken(sampleRefs?.replay_ref ?? derivedReplayRef);
  const keyframeRef = safePathToken(sampleRefs?.keyframe_ref ?? derivedKeyframeRef);
  const routeSampleRefs = uniqueRefs([
    routeRef,
    replayRef,
    keyframeRef,
    ...(artifactBundle?.route_refs ?? []),
    ...(artifactBundle?.replay_refs ?? []),
    ...(artifactBundle?.keyframe_refs ?? []),
    ...(artifactBundle?.evidence_refs ?? []),
    ...routeReplay.evidence_refs.sample_refs,
    ...artifactMediaSampleRefs(sampleRefs),
  ]);
  const reviewItemMediaRefs = uniqueRefs([
    ...derivedReviewMediaRefs,
    ...(artifactBundle?.evidence_refs ?? []),
    ...rawStringList(sampleRefs?.review_item_media_refs),
    rawString(sampleRefs?.review_item_media_ref),
  ]);
  const blockedReasons = aggregateDistinct([
    stringList(candidate.blocked_reasons),
    "local_mock_only",
    "not_proven",
  ]);
  const nextRequiredEvidence = stringList(candidate.next_required_evidence).length > 0
    ? stringList(candidate.next_required_evidence)
    : [
        "real_keyframe_media_access_probe_without_credentials",
        "review_item_media_capture_for_selected_task",
        "oss_or_cdn_read_probe_without_query_or_tokens",
      ];
  return {
    schema: O6_ARTIFACT_MEDIA_PREFLIGHT_SCHEMA,
    status:
      asString(candidate.status, "") === "local_mock_media_preflight_ready"
        ? "local_mock_media_preflight_ready"
        : "derived_blocked_not_proven",
    task_id: asString(candidate.task_id, taskId),
    consumer_section_names: [...O6_MEDIA_PREFLIGHT_SECTION_NAMES],
    counts: {
      route_ref_count: asNumber(counts?.route_ref_count) ?? (routeRef ? 1 : 0),
      replay_ref_count: asNumber(counts?.replay_ref_count) ?? (replayRef ? 1 : 0),
      keyframe_ref_count: asNumber(counts?.keyframe_ref_count) ?? (keyframeRef ? 1 : 0),
      sample_ref_count: asNumber(counts?.sample_ref_count) ?? routeSampleRefs.length,
      review_item_media_ref_count: asNumber(counts?.review_item_media_ref_count) ?? reviewItemMediaRefs.length,
    },
    route_replay_dependency: mediaDependency(
      routeRef,
      replayRef,
      keyframeRef,
      routeSampleRefs,
      [],
      blockedReasons,
      nextRequiredEvidence,
      "local_mock_media_preflight_ready",
    ),
    labeling_dependency: mediaDependency(
      routeRef,
      replayRef,
      keyframeRef,
      routeSampleRefs,
      reviewItemMediaRefs,
      aggregateDistinct([
        blockedReasons,
        reviewItemMediaRefs.length > 0 ? "" : "review_item_media_refs_missing",
      ]),
      nextRequiredEvidence,
      "local_mock_media_preflight_ready",
    ),
    proof_boundary: {
      local_mock: asBoolean(asRecord(candidate.proof_boundary)?.local_mock) || true,
      not_proven: true,
      real_media_read_executed: false,
      real_oss_connected: false,
      real_cdn_connected: false,
    },
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    media_access_proven: false,
    real_oss_connected: false,
    real_cdn_connected: false,
  };
}

function blockedRouteReplayMvp(reason: string, taskId: string): O7ConsumerRouteReplayMvp {
  // blocked contract 仍完整返回 cursor 和 false 字段，前端不用从缺字段猜测安全边界。
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_route_replay_mvp.v1",
    status: "blocked_not_proven",
    selected_task_id: taskId || "not_provided",
    source_detail_task_id: taskId || "not_provided",
    source_contract: "not_loaded",
    trajectory: {
      frame_count: 0,
      current_frame: null,
      sample_frames: [],
      status: "blocked_not_proven",
    },
    events_timeline: {
      count: 0,
      sample: [],
      status: "blocked_not_proven",
    },
    evidence_refs: {
      count: 0,
      sample_refs: [],
      keyframe_refs: [],
      status: "blocked_not_proven",
    },
    cursor_contract: {
      local_cursor_only: true,
      supported_actions: ["previous_frame", "next_frame", "reset_cursor", "toggle_playing"],
      initial_frame_index: null,
      playing_initial: false,
      safe_to_play: false,
      playback_available: false,
      sends_to_robot: false,
      status: "blocked_not_proven",
    },
    media_preflight_dependency: blockedMediaDependency(reason),
    blocked_reasons: [reason],
    not_proven: ["real_route_replay_playback", "real_cloud_archive_connected", "delivery_success"],
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    robot_control_executed: false,
  };
}

function buildConsumerRouteReplayMvp(
  remote: JsonRecord,
  manifest: O7FieldEvidenceManifestSummary,
  requestedTaskId: string,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
): O7ConsumerRouteReplayMvp {
  // consumer detail 是本轮主路径；route replay MVP 从同一个 O6 detail 派生，不读取本地 fixture。
  const taskSummary = asRecord(remote.task_summary);
  const trajectory = asRecord(remote.trajectory);
  const events = asRecord(remote.events);
  const evidence = asRecord(remote.evidence);
  const taskId = asString(taskSummary?.task_id, requestedTaskId || "not_provided");
  const rawFrames = firstObjectArray(trajectory?.frames, trajectory?.sample_frames);
  const rawEvents = firstObjectArray(events?.items, events?.sample_events, events?.timeline);
  const evidenceItems = firstObjectArray(evidence?.items, evidence?.sample_evidence, evidence?.refs);
  const sampleFrames = rawFrames.slice(0, MVP_FRAME_SAMPLE_LIMIT).map((frame, index) => mvpRouteFrame(frame, index));
  const sampleEvents = rawEvents.slice(0, MVP_EVENT_SAMPLE_LIMIT).map((event) => mvpRouteEvent(event));
  const refs = routeReplayMvpRefs(sampleFrames, sampleEvents, evidenceItems, manifest);
  const frameCount = asNumber(trajectory?.frame_count) ?? rawFrames.length;
  const eventCount = asNumber(events?.count) ?? rawEvents.length;
  const blockedReasons = aggregateDistinct([
    frameCount > 0 && sampleFrames.length > 0 ? "" : "trajectory_missing",
    eventCount > 0 && sampleEvents.length > 0 ? "" : "events_missing",
    refs.sample_refs.length > 0 || refs.keyframe_refs.length > 0 ? "" : "evidence_refs_missing",
    taskId === "not_provided" || taskId === "unknown_task" ? "task_id_missing" : "",
  ]);
  const ready = blockedReasons.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_route_replay_mvp.v1",
    status: ready ? "consumer_detail_replay_ready" : "blocked_not_proven",
    selected_task_id: taskId,
    source_detail_task_id: requestedTaskId || taskId,
    source_contract: "trashbot.o6.consumer_read.v1",
    trajectory: {
      frame_count: frameCount,
      current_frame: sampleFrames[0] ?? null,
      sample_frames: sampleFrames,
      status: ready ? "consumer_detail_trajectory_summary_only" : "blocked_not_proven",
    },
    events_timeline: {
      count: eventCount,
      sample: sampleEvents,
      status: sampleEvents.length > 0 ? "consumer_detail_events_summary_only" : "blocked_not_proven",
    },
    evidence_refs: {
      count: refs.sample_refs.length + refs.keyframe_refs.length,
      sample_refs: refs.sample_refs,
      keyframe_refs: refs.keyframe_refs,
      status: refs.sample_refs.length > 0 || refs.keyframe_refs.length > 0 ? "consumer_detail_refs_summary_only" : "blocked_not_proven",
    },
    cursor_contract: {
      local_cursor_only: true,
      supported_actions: ["previous_frame", "next_frame", "reset_cursor", "toggle_playing"],
      initial_frame_index: sampleFrames[0]?.frame_index ?? null,
      playing_initial: false,
      safe_to_play: false,
      playback_available: false,
      sends_to_robot: false,
      status: ready ? "local_cursor_ready" : "blocked_not_proven",
    },
    media_preflight_dependency: artifactMediaPreflight.route_replay_dependency,
    blocked_reasons: ready ? ["robot_control_disabled", "playback_available_false", "delivery_success_not_proven"] : blockedReasons,
    not_proven: [
      "real_route_replay_playback",
      "real_map_overlay",
      "real_keyframe_media_access",
      "real_robot_control",
      "delivery_success",
    ],
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    robot_control_executed: false,
  };
}

function mvpLabel(value: unknown): O7ConsumerLabelingMvpLabel {
  // label 摘要只保留类型、值、状态和 evidence_ref，避免透传 reviewer 或训练集内部字段。
  const label = asRecord(value) ?? {};
  return {
    label_type: asString(label.label_type ?? label.type, "not_provided"),
    value: asString(label.value ?? label.label, "not_provided"),
    status: asString(label.status, "consumer_detail_summary_only"),
    evidence_ref: safePathToken(label.evidence_ref ?? label.evidenceRef ?? ""),
  };
}

function mvpReviewItem(value: unknown, taskId: string): O7ConsumerLabelingMvpReviewItem {
  // review item 必须绑定同一个 task_id；缺失 task_id 时用 detail task_id 补齐，但不补出提交能力。
  const item = asRecord(value) ?? {};
  const currentLabels = firstObjectArray(item.current_labels, item.labels);
  return {
    item_id: asString(item.item_id ?? item.id, "not_provided"),
    task_id: asString(item.task_id, taskId),
    frame_id: asString(item.frame_id ?? item.frame_index, "not_provided"),
    media_ref: safePathToken(item.media_ref ?? item.image_ref ?? item.frame_ref ?? item.evidence_ref ?? ""),
    evidence_ref: safePathToken(item.evidence_ref ?? item.evidenceRef ?? ""),
    current_labels: {
      count: asNumber(item.current_label_count) ?? currentLabels.length,
      sample: currentLabels.slice(0, MVP_LABEL_SAMPLE_LIMIT).map((label) => mvpLabel(label)),
    },
  };
}

function blockedLabelingMvp(reason: string, taskId: string): O7ConsumerLabelingMvp {
  // 标注 submit 没有真实 API 时也返回 receipt，让 operator 明确知道请求被 fail-closed。
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_labeling_mvp.v1",
    status: "blocked_not_proven",
    selected_task_id: taskId || "not_provided",
    source_detail_task_id: taskId || "not_provided",
    review_items: {
      review_item_count: 0,
      current_item: null,
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
    submit_receipt: {
      status: "submit_blocked_fail_closed",
      receipt_id: "not_created",
      submit_enabled: false,
      rollback_enabled: false,
      dataset_export_available: false,
      real_annotation_api_connected: false,
      cloud_write_executed: false,
      blocked_reason: reason,
    },
    media_preflight_dependency: blockedMediaDependency(reason),
    blocked_reasons: [reason],
    not_proven: ["real_annotation_submit", "real_annotation_api_connected", "real_training_dataset_export"],
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    robot_control_executed: false,
  };
}

function buildConsumerLabelingMvp(
  remote: JsonRecord,
  requestedTaskId: string,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
): O7ConsumerLabelingMvp {
  // labeling MVP 同样只从当前 detail 派生，真实 submit/export/rollback 统一固定关闭。
  const taskSummary = asRecord(remote.task_summary);
  const labeling = asRecord(remote.labeling);
  const taskId = asString(taskSummary?.task_id, requestedTaskId || "not_provided");
  const reviewItems = firstObjectArray(labeling?.review_items, labeling?.items)
    .slice(0, MVP_LABEL_SAMPLE_LIMIT)
    .map((item) => mvpReviewItem(item, taskId));
  const labelSchema = asRecord(labeling?.label_schema);
  const allowedLabelTypes = stringList(labeling?.allowed_label_types ?? labelSchema?.allowed_label_types ?? labelSchema?.allowed_types);
  const draftLabels = firstObjectArray(labeling?.draft_labels, labeling?.drafts)
    .slice(0, MVP_LABEL_SAMPLE_LIMIT)
    .map((label) => mvpLabel(label));
  const requiredFields = stringList(labelSchema?.required_fields);
  const allowedFields = stringList(labelSchema?.allowed_fields);
  const reviewItemCount = asNumber(labeling?.review_item_count ?? labeling?.label_count) ?? reviewItems.length;
  const blockedReasons = aggregateDistinct([
    reviewItemCount > 0 && reviewItems.length > 0 ? "" : "labeling_missing",
    allowedLabelTypes.length > 0 ? "" : "allowed_label_types_missing",
    draftLabels.length > 0 ? "" : "draft_labels_missing",
    labelSchema ? "" : "label_schema_missing",
    taskId === "not_provided" || taskId === "unknown_task" ? "task_id_missing" : "",
  ]);
  const ready = blockedReasons.length === 0;
  const submitBlockedReason = ready ? "submit_disabled_no_annotation_api" : blockedReasons[0] ?? "labeling_missing";
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_labeling_mvp.v1",
    status: ready ? "consumer_detail_labeling_ready" : "blocked_not_proven",
    selected_task_id: taskId,
    source_detail_task_id: requestedTaskId || taskId,
    review_items: {
      review_item_count: reviewItemCount,
      current_item: reviewItems[0] ?? null,
      sample: reviewItems,
      status: ready ? "consumer_detail_review_items_summary_only" : "blocked_not_proven",
    },
    label_schema: {
      schema_ref: safePathToken(labelSchema?.schema_ref ?? labelSchema?.name ?? "not_provided"),
      version: asString(labelSchema?.version, "not_provided"),
      required_fields: requiredFields,
      allowed_fields: allowedFields,
      status: labelSchema ? "consumer_detail_schema_summary_only" : "blocked_not_proven",
    },
    allowed_label_types: allowedLabelTypes,
    draft_labels: {
      count: asNumber(labeling?.draft_label_count) ?? draftLabels.length,
      sample: draftLabels,
      autosave_available: false,
      status: draftLabels.length > 0 ? "consumer_detail_draft_slots_only" : "blocked_not_proven",
    },
    submit_receipt: {
      status: "submit_blocked_fail_closed",
      receipt_id: "not_created",
      submit_enabled: false,
      rollback_enabled: false,
      dataset_export_available: false,
      real_annotation_api_connected: false,
      cloud_write_executed: false,
      blocked_reason: submitBlockedReason,
    },
    media_preflight_dependency: artifactMediaPreflight.labeling_dependency,
    blocked_reasons: ready
      ? ["submit_disabled_no_annotation_api", "rollback_disabled", "dataset_export_disabled", "delivery_success_not_proven"]
      : blockedReasons,
    not_proven: [
      "real_annotation_api_connected",
      "real_annotation_submit",
      "real_annotation_rollback",
      "real_training_dataset_export",
      "delivery_success",
    ],
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    robot_control_executed: false,
  };
}

function buildConsumerArtifactBundleReadiness(
  remote: JsonRecord,
  manifest: O7FieldEvidenceManifestSummary,
  requestedTaskId: string,
  artifactBundle: O7ConsumerArtifactBundleSummary,
  artifactBundleConsumerIngest: O7ConsumerArtifactBundleConsumerIngestSummary,
  artifactMediaPreflight: O7ConsumerArtifactMediaPreflight,
  artifactAccessProbe: O7ConsumerArtifactAccessProbeSummary,
  offlineArtifactSeedSmoke: O7ConsumerOfflineArtifactSeedSmokeSummary,
  routeRootSeedGate: O7ConsumerRouteRootSeedGateSummary,
  routeBagEvidence: O7ConsumerRouteBagEvidenceSummary,
  routeBagPayloadReplay: O7ConsumerRouteBagPayloadReplaySummary,
  routeBagSemanticReplay: O7ConsumerRouteBagSemanticReplaySummary,
  routeBagFullSemanticDecodeMatrix: O7ConsumerRouteBagFullSemanticDecodeMatrixSummary,
  routeBagPoseProgressReplay: O7ConsumerRouteBagPoseProgressReplaySummary,
  fieldMotionEvidencePacket: O7ConsumerFieldMotionEvidencePacketSummary,
  nav2GoalExecutionEvidence: O7ConsumerNav2GoalExecutionEvidenceSummary,
  deliveryResultEvidence: O7ConsumerDeliveryResultEvidenceSummary,
  routeExecutionResultDeliveryReadiness: O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
  routeDeliveryClosurePacket: O7ConsumerRouteDeliveryClosurePacketSummary,
  sameTaskFieldMaterialPacket: O7ConsumerSameTaskFieldMaterialPacketSummary,
  localizationPathMaterialReadback: O7ConsumerLocalizationPathMaterialReadbackSummary,
  sameTaskRouteExecutionMaterialPacket: O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
  sameTaskMissionEvidenceGate: O7ConsumerSameTaskMissionEvidenceGateSummary,
  fieldOperatorConfirmationMaterial: O7ConsumerFieldOperatorConfirmationMaterialSummary,
  labelingMvp: O7ConsumerLabelingMvp | null,
  bundleCandidate: ArtifactBundleSourceResult | null,
  ingestCandidate: ArtifactBundleSourceResult | null,
): O7ConsumerArtifactBundleReadiness {
  // readiness 把 bundle/preflight 先收成一个主入口摘要，再把 route replay / labeling 当作消费面板。
  const taskSummary = asRecord(remote.task_summary);
  const taskId = asString(taskSummary?.task_id, requestedTaskId || "not_provided");
  const sourceContract = bundleCandidate
    ? O6_ARTIFACT_BUNDLE_SCHEMA
    : ingestCandidate
      ? O6_ARTIFACT_BUNDLE_CONSUMER_INGEST_SCHEMA
      : "not_loaded";
  const sourceOrigin = bundleCandidate?.source_origin ?? ingestCandidate?.source_origin ?? "not_loaded";
  const refs = artifactBundleReadinessRefs(artifactBundle, artifactMediaPreflight, labelingMvp);
  const blockedReasons = artifactBundleReadinessBlockedReasons(
    artifactBundle,
    artifactMediaPreflight,
    artifactAccessProbe,
    offlineArtifactSeedSmoke,
    routeRootSeedGate,
    routeBagEvidence,
    routeBagPayloadReplay,
    routeBagSemanticReplay,
    routeBagFullSemanticDecodeMatrix,
    routeBagPoseProgressReplay,
    nav2GoalExecutionEvidence,
    deliveryResultEvidence,
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    sameTaskFieldMaterialPacket,
    localizationPathMaterialReadback,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    fieldOperatorConfirmationMaterial,
    refs,
    taskId,
  );
  const manifestBlocker =
    manifest.status === "field_evidence_manifest_ready_not_delivery_proof"
      ? ""
      : manifest.blocked_reason || manifest.status || "";
  const ingestBlocker =
    artifactBundleConsumerIngest.schema === "not_loaded"
      ? "artifact_bundle_consumer_ingest_missing"
      : artifactBundleConsumerIngest.status === "local_mock_artifact_bundle_ready"
        ? ""
        : artifactBundleConsumerIngest.status;
  if (manifestBlocker) {
    blockedReasons.unshift(manifestBlocker);
  }
  if (ingestBlocker) {
    blockedReasons.unshift(ingestBlocker);
  }
  const probeReady =
    artifactAccessProbe.schema === O6_ARTIFACT_ACCESS_PROBE_SCHEMA &&
    artifactAccessProbe.status === "local_mock_artifact_access_probe_ready";
  const offlineSeedSmokeReady =
    offlineArtifactSeedSmoke.schema === O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA &&
    offlineArtifactSeedSmoke.status === "local_mock_offline_artifact_seed_smoke_ready";
  const routeRootSeedReady =
    routeRootSeedGate.schema === O6_ROUTE_ROOT_SEED_GATE_SCHEMA &&
    routeRootSeedGate.status === "local_mock_route_root_seed_ready";
  const routeBagReady =
    (routeBagEvidence.schema === ROUTE_BAG_EVIDENCE_SCHEMA || routeBagEvidence.schema === O6_ROUTE_BAG_EVIDENCE_SCHEMA) &&
    routeBagEvidence.status === "ready_not_route_execution_proof";
  const routeBagPayloadReplayReady =
    (routeBagPayloadReplay.schema === ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA ||
      routeBagPayloadReplay.schema === O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA) &&
    routeBagPayloadReplay.status === "ready_not_route_execution_proof";
  const routeBagFullSemanticDecodeMatrixReady =
    (routeBagFullSemanticDecodeMatrix.schema === ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA ||
      routeBagFullSemanticDecodeMatrix.schema === O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA) &&
    routeBagFullSemanticDecodeMatrix.status === "ready_not_route_execution_proof";
  const nav2GoalExecutionReady =
    nav2GoalExecutionEvidence.schema === NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA &&
    nav2GoalExecutionEvidence.status === "nav2_goal_execution_evidence_ready_not_delivery_proof";
  const deliveryResultReady =
    deliveryResultEvidence.schema === DELIVERY_RESULT_EVIDENCE_SCHEMA &&
    deliveryResultEvidence.status === "delivery_result_evidence_ready_not_delivery_proof";
  const routeExecutionResultDeliveryReadinessReady =
    routeExecutionResultDeliveryReadiness.schema === O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA &&
    routeExecutionResultDeliveryReadiness.status ===
      "route_execution_result_delivery_readiness_ready_not_delivery_proof";
  const routeDeliveryClosurePacketReady =
    routeDeliveryClosurePacket.schema === O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA &&
    routeDeliveryClosurePacket.status === "route_delivery_closure_ready_not_success_proof";
  const sameTaskFieldMaterialPacketReady =
    (sameTaskFieldMaterialPacket.schema === O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA ||
      sameTaskFieldMaterialPacket.schema === SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA) &&
    sameTaskFieldMaterialPacket.status === "ready_not_delivery_proof";
  const localizationPathMaterialReadbackReady =
    localizationPathMaterialReadback.schema === O7_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA &&
    localizationPathMaterialReadback.status === "localization_path_material_ready_not_route_execution_proof";
  const sameTaskRouteExecutionMaterialPacketReady =
    (sameTaskRouteExecutionMaterialPacket.schema === O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA ||
      sameTaskRouteExecutionMaterialPacket.schema === SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA) &&
    sameTaskRouteExecutionMaterialPacket.status === "route_execution_material_ready_not_delivery_proof";
  const sameTaskMissionGateReady =
    (sameTaskMissionEvidenceGate.schema === O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA ||
      sameTaskMissionEvidenceGate.schema === SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA) &&
    sameTaskMissionEvidenceGate.status === "same_task_mission_gate_ready_not_success_proof";
  const fieldOperatorConfirmationMaterialReady =
    fieldOperatorConfirmationMaterial.schema === O7_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA &&
    fieldOperatorConfirmationMaterial.status === "field_operator_confirmation_material_ready_not_delivery_proof";
  const ready =
    artifactBundle.schema !== "not_loaded" &&
    probeReady &&
    offlineSeedSmokeReady &&
    routeRootSeedReady &&
    routeBagReady &&
    routeBagPayloadReplayReady &&
    routeBagFullSemanticDecodeMatrixReady &&
    nav2GoalExecutionReady &&
    deliveryResultReady &&
    routeExecutionResultDeliveryReadinessReady &&
    routeDeliveryClosurePacketReady &&
    sameTaskFieldMaterialPacketReady &&
    localizationPathMaterialReadbackReady &&
    sameTaskRouteExecutionMaterialPacketReady &&
    sameTaskMissionGateReady &&
    fieldOperatorConfirmationMaterialReady;
  const sameTaskMissionMaterialChecklist = buildSameTaskMissionMaterialChecklist(
    sameTaskFieldMaterialPacket,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    deliveryResultEvidence,
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    routeBagPoseProgressReplay,
    taskId,
  );
  const nextRequiredEvidence = artifactMediaPreflight.next_required_evidence.length
    ? aggregateDistinct([
        artifactMediaPreflight.next_required_evidence,
        artifactAccessProbe.next_required_evidence,
        offlineArtifactSeedSmoke.next_required_evidence,
        routeRootSeedGate.next_required_evidence,
        routeBagEvidence.next_required_evidence,
        routeBagPayloadReplay.next_required_evidence,
        routeBagSemanticReplay.next_required_evidence,
        routeBagFullSemanticDecodeMatrix.next_required_evidence,
        routeBagPoseProgressReplay.next_required_evidence,
        nav2GoalExecutionEvidence.next_required_evidence,
        deliveryResultEvidence.next_required_evidence,
        routeExecutionResultDeliveryReadiness.next_required_evidence,
        routeDeliveryClosurePacket.next_required_evidence,
        sameTaskFieldMaterialPacket.next_required_evidence,
        localizationPathMaterialReadback.next_required_evidence,
        sameTaskRouteExecutionMaterialPacket.next_required_evidence,
        sameTaskMissionEvidenceGate.next_required_evidence,
        fieldOperatorConfirmationMaterial.next_required_evidence,
        sameTaskMissionMaterialChecklist.next_required_evidence,
      ])
    : aggregateDistinct([
        "artifact_media_preflight_contract_from_o6_consumer_detail",
        "real_keyframe_media_access_probe_without_credentials",
        "real_review_item_media_capture_for_selected_task",
        artifactAccessProbe.next_required_evidence,
        offlineArtifactSeedSmoke.next_required_evidence,
        routeRootSeedGate.next_required_evidence,
        routeBagEvidence.next_required_evidence,
        routeBagPayloadReplay.next_required_evidence,
        routeBagSemanticReplay.next_required_evidence,
        routeBagFullSemanticDecodeMatrix.next_required_evidence,
        routeBagPoseProgressReplay.next_required_evidence,
        nav2GoalExecutionEvidence.next_required_evidence,
        deliveryResultEvidence.next_required_evidence,
        routeExecutionResultDeliveryReadiness.next_required_evidence,
        routeDeliveryClosurePacket.next_required_evidence,
        sameTaskFieldMaterialPacket.next_required_evidence,
        localizationPathMaterialReadback.next_required_evidence,
        sameTaskRouteExecutionMaterialPacket.next_required_evidence,
        sameTaskMissionEvidenceGate.next_required_evidence,
        fieldOperatorConfirmationMaterial.next_required_evidence,
        sameTaskMissionMaterialChecklist.next_required_evidence,
      ]);
  return {
    schema: "trashbot.pc_tools_workstation.o7_consumer_artifact_bundle_readiness.v1",
    status: ready ? "consumer_detail_artifact_bundle_ready" : bundleCandidate || ingestCandidate ? "derived_blocked_not_proven" : "blocked_not_proven",
    selected_task_id: taskId,
    source_detail_task_id: requestedTaskId || taskId,
    source_contract: sourceContract,
    source_origin: sourceOrigin,
    task_id: taskId,
    bundle_status: artifactBundle.bundle_status,
    counts: {
      route_ref_count: refs.route_refs.length,
      replay_ref_count: refs.replay_refs.length,
      keyframe_ref_count: refs.keyframe_refs.length,
      evidence_ref_count: refs.evidence_refs.length,
      review_item_count: labelingMvp?.review_items?.review_item_count ?? 0,
      sample_ref_count: refs.sample_refs.length,
      review_item_media_ref_count: refs.review_item_media_refs.length,
    },
    refs,
    blocked_reasons: blockedReasons,
    next_required_evidence: nextRequiredEvidence,
    route_bag_evidence: routeBagEvidence,
    route_bag_payload_replay: routeBagPayloadReplay,
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_root_seed_gate: routeRootSeedGate,
    field_motion_evidence_packet: fieldMotionEvidencePacket,
    nav2_goal_execution_evidence: nav2GoalExecutionEvidence,
    delivery_result_evidence: deliveryResultEvidence,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    localization_path_material_readback: localizationPathMaterialReadback,
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: fieldOperatorConfirmationMaterial,
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_access_probe: artifactAccessProbe,
    offline_artifact_seed_smoke: offlineArtifactSeedSmoke,
    artifact_media_preflight: {
      ...artifactMediaPreflight,
      consumer_section_names: [...O6_ARTIFACT_BUNDLE_SECTION_NAMES],
    },
    route_replay_dependency: artifactMediaPreflight.route_replay_dependency,
    labeling_dependency: artifactMediaPreflight.labeling_dependency,
    real_oss_connected: false,
    real_cdn_connected: false,
    ...fixedFalseFields(),
    ...PROOF_FLAGS,
  };
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

function normalizeTaskFieldEvidenceSource(source: unknown): O7FieldEvidenceManifestSummary["source"] {
  // O6 consumer detail 的 field_evidence/source 可能是本地 mock 标记或 SSH 标记，这里只收敛到安全枚举。
  const raw = asString(source, "not_loaded");
  if (raw.includes("ssh")) {
    return "ssh_remote";
  }
  if (raw.includes("local")) {
    return "local_fixture";
  }
  return "not_loaded";
}

function normalizeTaskFieldEvidenceMode(source: O7FieldEvidenceManifestSummary["source"]): O7FieldEvidenceManifestSummary["mode"] {
  // source 只描述来源语义，mode 只用来区分 local 与 ssh 两条只读路径。
  if (source === "ssh_remote") {
    return "ssh";
  }
  if (source === "local_fixture") {
    return "local";
  }
  return "not_loaded";
}

function taskFieldEvidenceArtifactSummary(artifact: unknown): O7FieldEvidenceManifestArtifactSummary {
  // O6 task.field_evidence.artifacts[] 是 basename/size/checksum 摘要，这里转成 workstation 统一结构。
  const record = asRecord(artifact);
  if (!record) {
    return missingManifestArtifact(".", "artifact", "missing");
  }
  const capturedAtMs = asNumber(record.captured_at_ms ?? record.capturedAtMs);
  return {
    required: asBoolean(record.required),
    present: asBoolean(record.present),
    path: safePathToken(record.artifact_name ?? record.evidence_ref ?? record.evidenceRef ?? "artifact"),
    size_bytes: asNumber(record.size_bytes) ?? 0,
    mtime_utc: capturedAtMs === null ? null : new Date(capturedAtMs).toISOString(),
    sha256: typeof record.checksum === "string" ? record.checksum : typeof record.sha256 === "string" ? record.sha256 : null,
    reason: typeof record.reason === "string" ? record.reason : asBoolean(record.present) ? null : "missing",
  };
}

function looksLikeTaskFieldEvidenceSummary(value: JsonRecord): boolean {
  // O6 新 consumer detail 会直接返回 field_evidence 摘要，这里通过 summary 专有字段识别它。
  return (
    "artifact_summary" in value ||
    "derived_replay" in value ||
    "preflight" in value ||
    "source_manifest" in value ||
    (Array.isArray(value.artifacts) && value.artifacts.length > 0)
  );
}

function buildManifestSummaryFromTaskFieldEvidence(fieldEvidence: JsonRecord): O7FieldEvidenceManifestSummary {
  // 这里不回收绝对路径或原始内容，只把 O6 consumer detail 的 field_evidence 摘要映射成 workstation 统一 summary。
  const source = normalizeTaskFieldEvidenceSource(fieldEvidence.source);
  const rawArtifacts = Array.isArray(fieldEvidence.artifacts)
    ? fieldEvidence.artifacts.slice(0, MANIFEST_ARTIFACT_KEYS.length)
    : [];
  const artifactsByName = new Map<string, O7FieldEvidenceManifestArtifactSummary>();
  for (const artifact of rawArtifacts) {
    const record = asRecord(artifact);
    const key = asString(record?.artifact_name ?? record?.evidence_type ?? record?.evidence_ref, "artifact");
    artifactsByName.set(key, taskFieldEvidenceArtifactSummary(artifact));
  }
  const artifactNames = MANIFEST_ARTIFACT_KEYS.map((name) => asString(name, "artifact"));
  const presentArtifacts = artifactNames.filter((name) => artifactsByName.get(name)?.present);
  const missingArtifacts = artifactNames.filter((name) => !artifactsByName.get(name)?.present);
  const artifactHealth = asRecord(fieldEvidence.artifact_summary);
  const manifestGate = asRecord(fieldEvidence.manifest_gate);
  const preflight = asRecord(fieldEvidence.preflight);
  return {
    schema: FIELD_EVIDENCE_MANIFEST_SCHEMA,
    run_id: asString(fieldEvidence.run_id ?? fieldEvidence.manifest_run_id, "not_loaded"),
    source,
    mode: normalizeTaskFieldEvidenceMode(source),
    status: asString(fieldEvidence.manifest_status ?? fieldEvidence.status, "manifest_not_loaded"),
    gate_pass: asBoolean(manifestGate?.gate_pass ?? fieldEvidence.gate_pass),
    artifact_status: normalizeManifestArtifactStatus(fieldEvidence.artifact_status),
    blocked_reason: asString(
      manifestGate?.blocked_reason ?? fieldEvidence.blocked_reason ?? fieldEvidence.manifest_status,
      "manifest_not_loaded",
    ),
    not_proven: true,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    artifact_root: "",
    preflight_status: typeof preflight?.status === "string" ? preflight.status : null,
    manifest_gate: {
      schema: asString(manifestGate?.schema, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA ? FIELD_EVIDENCE_MANIFEST_SCHEMA : "not_loaded",
      status: normalizeManifestGateStatus(manifestGate?.status),
      gate_pass: asBoolean(manifestGate?.gate_pass),
      blocked_reason: asString(manifestGate?.blocked_reason, "manifest_not_loaded"),
      source: source,
    },
    artifact_health: {
      status: normalizeManifestArtifactStatus(artifactHealth?.status ?? fieldEvidence.artifact_status),
      required_count: asNumber(artifactHealth?.required_count) ?? rawArtifacts.length,
      present_count: asNumber(artifactHealth?.present_count) ?? presentArtifacts.length,
      missing_count: asNumber(artifactHealth?.missing_count) ?? missingArtifacts.length,
      blocked_count: asNumber(artifactHealth?.blocked_count) ?? 0,
      empty_count: asNumber(artifactHealth?.empty_count) ?? 0,
      present_artifacts: presentArtifacts.slice(0, MANIFEST_ARTIFACT_KEYS.length),
      missing_artifacts: missingArtifacts.slice(0, MANIFEST_ARTIFACT_KEYS.length),
      blocked_artifacts: missingArtifacts.slice(0, MANIFEST_ARTIFACT_KEYS.length),
      summary: asString(artifactHealth?.summary, "field_evidence_summary_loaded"),
    },
    artifacts: {
      map_yaml:
        artifactsByName.get("map_yaml") ??
        missingManifestArtifact(".", "map.yaml", "field_evidence_summary_missing_map_yaml"),
      route_csv:
        artifactsByName.get("route_csv") ??
        missingManifestArtifact(".", "route.csv", "field_evidence_summary_missing_route_csv"),
      keyframes:
        artifactsByName.get("keyframes") ??
        missingManifestArtifact(".", "keyframes", "field_evidence_summary_missing_keyframes"),
      rosbag:
        artifactsByName.get("rosbag") ??
        missingManifestArtifact(".", "rosbag", "field_evidence_summary_missing_rosbag"),
      replay_jsonl:
        artifactsByName.get("replay_jsonl") ??
        missingManifestArtifact(".", "replay.jsonl", "field_evidence_summary_missing_replay_jsonl"),
    },
  };
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
  sourceContract: DetailFieldEvidenceSourceContract,
  sourceOrigin: DetailFieldEvidenceSourceOrigin,
  taskOrigin: string,
): O7ConsumerTaskDetailResponse["field_evidence"] {
  // consumer detail 统一把 manifest 关键边界收敛到一处，供 O7 页面直接展示。
  return {
    source_contract: sourceContract,
    source_origin: sourceOrigin,
    task_origin: taskOrigin,
    manifest_run_id: manifest.run_id,
    artifact_root: manifest.artifact_root,
    artifact_health_summary: manifest.artifact_health.summary,
    present_artifacts: manifest.artifact_health.present_artifacts,
    missing_artifacts: manifest.artifact_health.missing_artifacts,
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

function detailFieldEvidenceSourceFromTaskFieldEvidence(
  fieldEvidence: JsonRecord,
  sourceOrigin: DetailFieldEvidenceSourceOrigin,
  taskOrigin: string,
): DetailFieldEvidenceSourceResult {
  // O6 新 consumer detail 会直接给出 field_evidence 摘要；只要能识别其 summary 形状就不再退回本地 manifest。
  if (asString(fieldEvidence.schema, "") !== FIELD_EVIDENCE_MANIFEST_SCHEMA) {
    return { errorReason: "field_evidence_manifest_schema_mismatch", inputStatus: "schema_mismatch" };
  }
  if (!looksLikeTaskFieldEvidenceSummary(fieldEvidence)) {
    return { errorReason: "field_evidence_manifest_missing", inputStatus: "invalid_shape" };
  }
  return {
    manifest: buildManifestSummaryFromTaskFieldEvidence(fieldEvidence),
    inputStatus: "loaded",
    sourceContract: FIELD_EVIDENCE_MANIFEST_SCHEMA,
    sourceOrigin,
    taskOrigin: taskOrigin || asString(fieldEvidence.task_origin, "field_evidence_manifest"),
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

function manifestCandidateFromFieldEvidenceWrapper(wrapper: JsonRecord): JsonRecord | null {
  // O6 新读模型可能把来源包在 field_evidence 下；没有完整 manifest 时只构造安全摘要。
  const nestedManifest =
    asRecord(wrapper.field_evidence_manifest) ??
    asRecord(wrapper.manifest) ??
    asRecord(wrapper.manifest_summary);
  if (nestedManifest) {
    return nestedManifest;
  }
  const manifestGate = asRecord(wrapper.manifest_gate);
  const declaresManifest =
    asString(wrapper.source_contract, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA ||
    asString(manifestGate?.schema, "") === FIELD_EVIDENCE_MANIFEST_SCHEMA;
  if (!declaresManifest) {
    return null;
  }
  return {
    schema: FIELD_EVIDENCE_MANIFEST_SCHEMA,
    run_id: wrapper.manifest_run_id ?? wrapper.run_id,
    source: wrapper.manifest_source ?? wrapper.source ?? manifestGate?.source,
    mode: wrapper.manifest_mode ?? wrapper.mode,
    status: wrapper.manifest_status ?? wrapper.status,
    gate_pass: wrapper.gate_pass ?? manifestGate?.gate_pass,
    artifact_status: wrapper.artifact_status,
    blocked_reason: wrapper.blocked_reason ?? manifestGate?.blocked_reason,
    // wrapper 摘要只代表可读来源，不继承任何“已证明”语义。
    not_proven: true,
    artifact_root: wrapper.artifact_root,
    preflight_status: wrapper.preflight_status,
    manifest_gate: wrapper.manifest_gate,
    artifact_health: wrapper.artifact_health,
    artifacts: wrapper.artifacts,
  };
}

function detailFieldEvidenceSourceFromManifest(
  manifestPayload: JsonRecord,
  sourceOrigin: DetailFieldEvidenceSourceOrigin,
  taskOrigin: string,
): DetailFieldEvidenceSourceResult {
  const safety = manifestInputSafetyStatus(manifestPayload);
  if (safety.status !== "loaded") {
    return { errorReason: safety.reason, inputStatus: "unsafe_claim" };
  }
  if (asString(manifestPayload.schema, "") !== FIELD_EVIDENCE_MANIFEST_SCHEMA) {
    return { errorReason: "field_evidence_manifest_schema_mismatch", inputStatus: "schema_mismatch" };
  }
  return {
    manifest: buildManifestSummary(manifestPayload),
    inputStatus: "loaded",
    sourceContract: FIELD_EVIDENCE_MANIFEST_SCHEMA,
    sourceOrigin,
    taskOrigin,
  };
}

function detailFieldEvidenceSourceFromConsumerIngest(
  ingestPayload: JsonRecord,
  sourceOrigin: DetailFieldEvidenceSourceOrigin,
  taskOrigin: string,
): DetailFieldEvidenceSourceResult {
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
    sourceOrigin,
    taskOrigin,
  };
}

function detailFieldEvidenceSourceFromWrapper(wrapper: JsonRecord): DetailFieldEvidenceSourceResult {
  // field_evidence wrapper 是 O6 本轮接入点；只接受明确 manifest/ingest 合同，其他形态 fail-closed。
  const sourceContract = asString(wrapper.source_contract, "");
  const taskOrigin = asString(wrapper.task_origin, "field_evidence_manifest");
  if (looksLikeTaskFieldEvidenceSummary(wrapper)) {
    if (sourceContract && !FIELD_EVIDENCE_SOURCE_CONTRACTS.has(sourceContract)) {
      return { errorReason: "field_evidence_source_contract_mismatch", inputStatus: "schema_mismatch" };
    }
    return detailFieldEvidenceSourceFromTaskFieldEvidence(wrapper, "remote_field_evidence", taskOrigin);
  }
  const ingestPayload =
    asRecord(wrapper.field_evidence_consumer_ingest) ??
    asRecord(wrapper.field_evidence_ingest) ??
    asRecord(wrapper.consumer_ingest);
  if (sourceContract && !FIELD_EVIDENCE_SOURCE_CONTRACTS.has(sourceContract)) {
    return { errorReason: "field_evidence_source_contract_mismatch", inputStatus: "schema_mismatch" };
  }
  if (sourceContract === FIELD_EVIDENCE_CONSUMER_INGEST_SCHEMA || ingestPayload) {
    if (!ingestPayload) {
      return { errorReason: "field_evidence_consumer_ingest_missing", inputStatus: "invalid_shape" };
    }
    return detailFieldEvidenceSourceFromConsumerIngest(
      ingestPayload,
      "remote_field_evidence",
      taskOrigin,
    );
  }
  const manifest = manifestCandidateFromFieldEvidenceWrapper(wrapper);
  if (!manifest) {
    return { errorReason: "field_evidence_manifest_missing", inputStatus: "invalid_shape" };
  }
  return detailFieldEvidenceSourceFromManifest(manifest, "remote_field_evidence", taskOrigin);
}

function detailFieldEvidenceSource(
  remote: JsonRecord,
):
  | {
      manifest: O7FieldEvidenceManifestSummary;
      inputStatus: DetailFieldEvidenceInputStatus;
      sourceContract: DetailFieldEvidenceSourceContract;
      sourceOrigin: DetailFieldEvidenceSourceOrigin;
      taskOrigin: string;
    }
  | {
      errorReason: string;
      inputStatus: DetailFieldEvidenceInputStatus;
    } {
  // O7 detail 允许两种上游形态：直接挂 manifest，或挂现有 ingest contract。
  const wrappedFieldEvidence = asRecord(remote.field_evidence);
  if (wrappedFieldEvidence) {
    return detailFieldEvidenceSourceFromWrapper(wrappedFieldEvidence);
  }

  const directManifest = asRecord(remote.field_evidence_manifest) ?? asRecord(remote.manifest);
  if (directManifest) {
    return detailFieldEvidenceSourceFromManifest(
      directManifest,
      "remote_field_evidence_manifest",
      "field_evidence_manifest",
    );
  }

  const ingestPayload = asRecord(remote.field_evidence_consumer_ingest) ?? asRecord(remote.field_evidence_ingest);
  if (ingestPayload) {
    return detailFieldEvidenceSourceFromConsumerIngest(
      ingestPayload,
      "remote_field_evidence_consumer_ingest",
      "field_evidence_manifest",
    );
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
      sourceContract: DetailFieldEvidenceSourceContract;
      sourceOrigin: DetailFieldEvidenceSourceOrigin;
      taskOrigin: string;
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
    sourceOrigin: "local_manifest_fallback",
    taskOrigin: "field_evidence_manifest",
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
    if (dangerous.some((path) => path.startsWith("route_bag_payload_replay"))) {
      return failClosedDetail(
        `route_bag_payload_replay_dangerous_true:${dangerous.join(",")}`,
        normalized.normalized,
        trimmedTaskId,
      );
    }
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
  const artifactBundleCandidate = artifactBundleCandidateFromRemote(remote);
  const artifactBundle = buildArtifactBundleSummary(artifactBundleCandidate, trimmedTaskId);
  const artifactBundleFailClosedReason =
    artifactBundle.schema === "not_loaded" &&
    /^(artifact_bundle_dangerous_true|artifact_bundle_unsafe_ref|artifact_media_preflight_unsafe_ref|artifact_bundle_schema_mismatch)/.test(
      artifactBundle.bundle_status,
    )
      ? artifactBundle.bundle_status
      : "";
  if (artifactBundleFailClosedReason) {
    return failClosedDetail(artifactBundleFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const artifactBundleConsumerIngestCandidate = artifactBundleConsumerIngestCandidateFromRemote(remote);
  const artifactAccessProbeCandidate = artifactAccessProbeCandidateFromRemote(remote);
  const artifactAccessProbe = buildArtifactAccessProbeSummary(artifactAccessProbeCandidate, trimmedTaskId);
  const artifactAccessProbeFailClosedReason = artifactAccessProbeHardFailReason(artifactAccessProbe);
  if (artifactAccessProbeFailClosedReason) {
    return failClosedDetail(artifactAccessProbeFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const offlineArtifactSeedSmokeCandidate = offlineArtifactSeedSmokeCandidateFromRemote(remote);
  const offlineArtifactSeedSmoke = buildOfflineArtifactSeedSmokeSummary(offlineArtifactSeedSmokeCandidate, trimmedTaskId);
  const offlineArtifactSeedSmokeFailClosedReason = offlineArtifactSeedSmokeHardFailReason(offlineArtifactSeedSmoke);
  if (offlineArtifactSeedSmokeFailClosedReason) {
    return failClosedDetail(offlineArtifactSeedSmokeFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeRootSeedGateCandidate = routeRootSeedGateCandidateFromRemote(remote);
  const routeRootSeedGate = buildRouteRootSeedGateSummary(routeRootSeedGateCandidate, trimmedTaskId);
  const routeRootSeedGateFailClosedReason = routeRootSeedGateHardFailReason(routeRootSeedGate);
  if (routeRootSeedGateFailClosedReason) {
    return failClosedDetail(routeRootSeedGateFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeBagEvidenceCandidate = routeBagEvidenceCandidateFromRemote(remote);
  const routeBagEvidence = buildRouteBagEvidenceSummary(routeBagEvidenceCandidate, trimmedTaskId);
  const routeBagEvidenceFailClosedReason = routeBagEvidenceHardFailReason(routeBagEvidence);
  if (routeBagEvidenceFailClosedReason) {
    return failClosedDetail(routeBagEvidenceFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeBagPayloadReplayCandidate = routeBagPayloadReplayCandidateFromRemote(remote);
  const routeBagPayloadReplay = buildRouteBagPayloadReplaySummary(routeBagPayloadReplayCandidate, trimmedTaskId);
  const routeBagPayloadReplayFailClosedReason = routeBagPayloadReplayHardFailReason(routeBagPayloadReplay);
  if (routeBagPayloadReplayFailClosedReason) {
    return failClosedDetail(routeBagPayloadReplayFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeBagSemanticReplayCandidate = routeBagSemanticReplayCandidateFromRemote(remote);
  const routeBagSemanticReplay = buildRouteBagSemanticReplaySummary(
    routeBagSemanticReplayCandidate,
    trimmedTaskId,
  );
  const routeBagSemanticReplayFailClosedReason =
    routeBagSemanticReplayHardFailReason(routeBagSemanticReplay);
  if (routeBagSemanticReplayFailClosedReason) {
    return failClosedDetail(routeBagSemanticReplayFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeBagFullSemanticDecodeMatrixCandidate = routeBagFullSemanticDecodeMatrixCandidateFromRemote(remote);
  const routeBagFullSemanticDecodeMatrix = buildRouteBagFullSemanticDecodeMatrixSummary(
    routeBagFullSemanticDecodeMatrixCandidate,
    trimmedTaskId,
  );
  const routeBagFullSemanticDecodeMatrixFailClosedReason =
    routeBagFullSemanticDecodeMatrixHardFailReason(routeBagFullSemanticDecodeMatrix);
  if (routeBagFullSemanticDecodeMatrixFailClosedReason) {
    return failClosedDetail(routeBagFullSemanticDecodeMatrixFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeBagPoseProgressReplayCandidate = routeBagPoseProgressReplayCandidateFromRemote(remote);
  const routeBagPoseProgressReplay = buildRouteBagPoseProgressReplaySummary(
    routeBagPoseProgressReplayCandidate,
    trimmedTaskId,
  );
  const routeBagPoseProgressReplayFailClosedReason =
    routeBagPoseProgressReplayHardFailReason(routeBagPoseProgressReplay);
  if (routeBagPoseProgressReplayFailClosedReason) {
    return failClosedDetail(routeBagPoseProgressReplayFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const fieldMotionEvidencePacketCandidate = fieldMotionEvidencePacketCandidateFromRemote(remote);
  const fieldMotionEvidencePacket = buildFieldMotionEvidencePacketSummary(
    fieldMotionEvidencePacketCandidate,
    trimmedTaskId,
  );
  const fieldMotionEvidencePacketFailClosedReason = fieldMotionEvidencePacketHardFailReason(fieldMotionEvidencePacket);
  if (fieldMotionEvidencePacketFailClosedReason) {
    return failClosedDetail(fieldMotionEvidencePacketFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const nav2GoalExecutionEvidenceCandidate = nav2GoalExecutionEvidenceCandidateFromRemote(remote);
  const nav2GoalExecutionEvidence = buildNav2GoalExecutionEvidenceSummary(
    nav2GoalExecutionEvidenceCandidate,
    trimmedTaskId,
  );
  const nav2GoalExecutionEvidenceFailClosedReason =
    nav2GoalExecutionEvidenceHardFailReason(nav2GoalExecutionEvidence);
  if (nav2GoalExecutionEvidenceFailClosedReason) {
    return failClosedDetail(nav2GoalExecutionEvidenceFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const deliveryResultEvidenceCandidate = deliveryResultEvidenceCandidateFromRemote(remote);
  const deliveryResultEvidence = buildDeliveryResultEvidenceSummary(
    deliveryResultEvidenceCandidate,
    trimmedTaskId,
  );
  const deliveryResultEvidenceFailClosedReason = deliveryResultEvidenceHardFailReason(deliveryResultEvidence);
  if (deliveryResultEvidenceFailClosedReason) {
    return failClosedDetail(deliveryResultEvidenceFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const routeExecutionResultDeliveryReadinessCandidate =
    routeExecutionResultDeliveryReadinessCandidateFromRemote(remote);
  const routeExecutionResultDeliveryReadiness = buildRouteExecutionResultDeliveryReadinessSummary(
    routeExecutionResultDeliveryReadinessCandidate,
    trimmedTaskId,
  );
  const routeExecutionResultDeliveryReadinessFailClosedReason =
    routeExecutionResultDeliveryReadinessHardFailReason(routeExecutionResultDeliveryReadiness);
  if (routeExecutionResultDeliveryReadinessFailClosedReason) {
    return failClosedDetail(
      routeExecutionResultDeliveryReadinessFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const routeDeliveryClosurePacketCandidate = routeDeliveryClosurePacketCandidateFromRemote(remote);
  const routeDeliveryClosurePacket = buildRouteDeliveryClosurePacketSummary(
    routeDeliveryClosurePacketCandidate,
    trimmedTaskId,
  );
  const routeDeliveryClosurePacketFailClosedReason =
    routeDeliveryClosurePacketHardFailReason(routeDeliveryClosurePacket);
  if (routeDeliveryClosurePacketFailClosedReason) {
    return failClosedDetail(routeDeliveryClosurePacketFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const sameTaskFieldMaterialPacketCandidate = sameTaskFieldMaterialPacketCandidateFromRemote(remote);
  const sameTaskFieldMaterialPacket = buildSameTaskFieldMaterialPacketSummary(
    sameTaskFieldMaterialPacketCandidate,
    trimmedTaskId,
  );
  const sameTaskFieldMaterialPacketFailClosedReason =
    sameTaskFieldMaterialPacketHardFailReason(sameTaskFieldMaterialPacket);
  if (sameTaskFieldMaterialPacketFailClosedReason) {
    return failClosedDetail(sameTaskFieldMaterialPacketFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const currentFieldEvidenceMaterialCandidate = currentFieldEvidenceMaterialCandidateFromRemote(remote);
  const currentFieldEvidenceMaterial = buildCurrentFieldEvidenceMaterialSummary(
    currentFieldEvidenceMaterialCandidate,
    trimmedTaskId,
  );
  const currentFieldEvidenceMaterialFailClosedReason = currentFieldEvidenceMaterialHardFailReason(
    currentFieldEvidenceMaterial,
  );
  if (currentFieldEvidenceMaterialFailClosedReason) {
    return failClosedDetail(
      currentFieldEvidenceMaterialFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const cleanBaselineNav2PathMaterialCandidate = cleanBaselineNav2PathMaterialCandidateFromRemote(remote);
  const cleanBaselineNav2PathMaterial = buildCleanBaselineNav2PathMaterialSummary(
    cleanBaselineNav2PathMaterialCandidate,
    trimmedTaskId,
  );
  const cleanBaselineNav2PathMaterialFailClosedReason = cleanBaselineNav2PathMaterialHardFailReason(
    cleanBaselineNav2PathMaterial,
  );
  if (cleanBaselineNav2PathMaterialFailClosedReason) {
    return failClosedDetail(
      cleanBaselineNav2PathMaterialFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const localizationPathMaterialReadbackCandidate =
    localizationPathMaterialReadbackCandidateFromRemote(remote);
  const localizationPathMaterialReadback = buildLocalizationPathMaterialReadbackSummary(
    localizationPathMaterialReadbackCandidate,
    trimmedTaskId,
  );
  const localizationPathMaterialReadbackFailClosedReason =
    localizationPathMaterialReadbackHardFailReason(localizationPathMaterialReadback);
  if (localizationPathMaterialReadbackFailClosedReason) {
    return failClosedDetail(
      localizationPathMaterialReadbackFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const sameTaskRouteExecutionMaterialPacketCandidate =
    sameTaskRouteExecutionMaterialPacketCandidateFromRemote(remote);
  const sameTaskRouteExecutionMaterialPacket = buildSameTaskRouteExecutionMaterialPacketSummary(
    sameTaskRouteExecutionMaterialPacketCandidate,
    trimmedTaskId,
  );
  const sameTaskRouteExecutionMaterialPacketFailClosedReason =
    sameTaskRouteExecutionMaterialPacketHardFailReason(sameTaskRouteExecutionMaterialPacket);
  if (sameTaskRouteExecutionMaterialPacketFailClosedReason) {
    return failClosedDetail(
      sameTaskRouteExecutionMaterialPacketFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const sameTaskMissionEvidenceGateCandidate = sameTaskMissionEvidenceGateCandidateFromRemote(remote);
  const sameTaskMissionEvidenceGate = buildSameTaskMissionEvidenceGateSummary(
    sameTaskMissionEvidenceGateCandidate,
    trimmedTaskId,
  );
  const sameTaskMissionEvidenceGateFailClosedReason =
    sameTaskMissionEvidenceGateHardFailReason(sameTaskMissionEvidenceGate);
  if (sameTaskMissionEvidenceGateFailClosedReason) {
    return failClosedDetail(sameTaskMissionEvidenceGateFailClosedReason, normalized.normalized, trimmedTaskId);
  }
  const fieldOperatorConfirmationMaterialCandidate = fieldOperatorConfirmationMaterialCandidateFromRemote(remote);
  const fieldOperatorConfirmationMaterial = buildFieldOperatorConfirmationMaterialSummary(
    fieldOperatorConfirmationMaterialCandidate,
    trimmedTaskId,
  );
  const fieldOperatorConfirmationMaterialFailClosedReason = fieldOperatorConfirmationMaterialHardFailReason(
    fieldOperatorConfirmationMaterial,
  );
  if (fieldOperatorConfirmationMaterialFailClosedReason) {
    return failClosedDetail(
      fieldOperatorConfirmationMaterialFailClosedReason,
      normalized.normalized,
      trimmedTaskId,
    );
  }
  const artifactMediaPreflight = buildConsumerArtifactMediaPreflight(
    remote,
    fieldEvidenceSource.manifest,
    trimmedTaskId,
    artifactBundle,
  );
  artifactBundle.artifact_media_preflight = artifactMediaPreflight;
  const routeReplayMvp = buildConsumerRouteReplayMvp(remote, fieldEvidenceSource.manifest, trimmedTaskId, artifactMediaPreflight);
  const labelingMvp = buildConsumerLabelingMvp(remote, trimmedTaskId, artifactMediaPreflight);
  const artifactBundleConsumerIngest = buildArtifactBundleConsumerIngestSummary(
    artifactBundleConsumerIngestCandidate,
    artifactBundle,
    artifactMediaPreflight,
    trimmedTaskId,
  );
  artifactBundleConsumerIngest.artifact_bundle = artifactBundle;
  artifactBundleConsumerIngest.artifact_media_preflight = artifactMediaPreflight;
  const artifactBundleReadiness = buildConsumerArtifactBundleReadiness(
    remote,
    fieldEvidenceSource.manifest,
    trimmedTaskId,
    artifactBundle,
    artifactBundleConsumerIngest,
    artifactMediaPreflight,
    artifactAccessProbe,
    offlineArtifactSeedSmoke,
    routeRootSeedGate,
    routeBagEvidence,
    routeBagPayloadReplay,
    routeBagSemanticReplay,
    routeBagFullSemanticDecodeMatrix,
    routeBagPoseProgressReplay,
    fieldMotionEvidencePacket,
    nav2GoalExecutionEvidence,
    deliveryResultEvidence,
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    sameTaskFieldMaterialPacket,
    localizationPathMaterialReadback,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    fieldOperatorConfirmationMaterial,
    labelingMvp,
    artifactBundleCandidate,
    artifactBundleConsumerIngestCandidate,
  );
  const sameTaskMissionMaterialChecklist = buildSameTaskMissionMaterialChecklist(
    sameTaskFieldMaterialPacket,
    sameTaskRouteExecutionMaterialPacket,
    sameTaskMissionEvidenceGate,
    deliveryResultEvidence,
    routeExecutionResultDeliveryReadiness,
    routeDeliveryClosurePacket,
    routeBagPoseProgressReplay,
    trimmedTaskId,
  );

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
      fieldEvidenceSource.sourceOrigin,
      fieldEvidenceSource.taskOrigin,
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
    artifact_media_preflight: artifactMediaPreflight,
    artifact_access_probe: artifactAccessProbe,
    offline_artifact_seed_smoke: offlineArtifactSeedSmoke,
    route_bag_evidence: routeBagEvidence,
    route_bag_payload_replay: routeBagPayloadReplay,
    route_bag_semantic_replay: routeBagSemanticReplay,
    route_bag_full_semantic_decode_matrix: routeBagFullSemanticDecodeMatrix,
    route_bag_pose_progress_replay: routeBagPoseProgressReplay,
    route_root_seed_gate: routeRootSeedGate,
    field_motion_evidence_packet: fieldMotionEvidencePacket,
    nav2_goal_execution_evidence: nav2GoalExecutionEvidence,
    delivery_result_evidence: deliveryResultEvidence,
    route_execution_result_delivery_readiness: routeExecutionResultDeliveryReadiness,
    route_delivery_closure_packet: routeDeliveryClosurePacket,
    same_task_field_material_packet: sameTaskFieldMaterialPacket,
    current_field_evidence_material: currentFieldEvidenceMaterial,
    localization_path_material_readback: localizationPathMaterialReadback,
    clean_baseline_nav2_path_material: cleanBaselineNav2PathMaterial,
    same_task_route_execution_material_packet: sameTaskRouteExecutionMaterialPacket,
    same_task_mission_evidence_gate: sameTaskMissionEvidenceGate,
    field_operator_confirmation_material: fieldOperatorConfirmationMaterial,
    same_task_mission_material_checklist: sameTaskMissionMaterialChecklist,
    artifact_bundle: artifactBundle,
    artifact_bundle_consumer_ingest: artifactBundleConsumerIngest,
    artifact_bundle_readiness: artifactBundleReadiness,
    route_replay_mvp: routeReplayMvp,
    labeling_mvp: labelingMvp,
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

export async function buildO7ConsumerAnnotationSubmit(
  baseUrl: string,
  taskId: string,
  body: unknown,
): Promise<O7AnnotationSubmitResult> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosedAnnotationSubmit(normalized.reason, baseUrl, taskId);
  }
  const safeId = safeTaskId(taskId);
  if (!safeId.ok) {
    return failClosedAnnotationSubmit(safeId.reason, normalized.normalized, taskId);
  }
  const submitPayload = submitPayloadFromBody(body);
  if (!submitPayload.ok) {
    return failClosedAnnotationSubmit(submitPayload.reason, normalized.normalized, safeId.taskId);
  }

  let responseStatus: number | null = null;
  let remoteJson: unknown;
  try {
    const response = await fetch(`${normalized.normalized}${REMOTE_LABEL_SUBMIT_ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        robot_id: submitPayload.robotId,
        task_id: safeId.taskId,
        labels: submitPayload.labels,
      }),
    });
    responseStatus = response.status;
    remoteJson = await response.json();
    if (!response.ok) {
      return failClosedAnnotationSubmit(`o6_annotation_submit_http_${response.status}`, normalized.normalized, safeId.taskId, responseStatus);
    }
  } catch {
    return failClosedAnnotationSubmit("o6_annotation_submit_fetch_failed", normalized.normalized, safeId.taskId, responseStatus);
  }

  const remote = asRecord(remoteJson);
  if (!remote) {
    return failClosedAnnotationSubmit("o6_annotation_submit_response_not_object", normalized.normalized, safeId.taskId, responseStatus);
  }
  if (asString(remote.schema, "") !== "trashbot.o6.archive_labeling.v1") {
    return failClosedAnnotationSubmit("o6_annotation_submit_schema_mismatch", normalized.normalized, safeId.taskId, responseStatus);
  }
  const dangerous = scanDangerousTrueFields(remote);
  if (dangerous.length > 0) {
    return failClosedAnnotationSubmit(`dangerous_true_fields:${dangerous.join(",")}`, normalized.normalized, safeId.taskId, responseStatus);
  }
  if (containsUnsafeAnnotationCopy(remote)) {
    return failClosedAnnotationSubmit("o6_annotation_submit_contains_unsafe_copy", normalized.normalized, safeId.taskId, responseStatus);
  }

  const labelSummary = asRecord(remote.label_summary);
  const itemizedLabels = sampleObjectArray(remote.itemized_labels, O7_ANNOTATION_LABEL_LIMIT)
    .map((label) => normalizeSubmitLabel(label))
    .filter((label): label is O7AnnotationSubmitLabel => Boolean(label));
  const writeStatus = asString(remote.write_status, "blocked_not_proven");
  if (!["created", "updated"].includes(writeStatus)) {
    return failClosedAnnotationSubmit("o6_annotation_submit_write_status_mismatch", normalized.normalized, safeId.taskId, responseStatus);
  }
  const labelCount = asNumber(labelSummary?.itemized_label_count) ?? itemizedLabels.length;
  const submitReceipt = asRecord(remote.submit_receipt);
  return {
    schema: ANNOTATION_SUBMIT_SCHEMA,
    adapter_status: "local_mock_annotation_written",
    source_base_url: normalized.normalized,
    remote_endpoint: REMOTE_LABEL_SUBMIT_ENDPOINT,
    remote_schema: "trashbot.o6.archive_labeling.v1",
    requested_task_id: safeId.taskId,
    o6_http_status: responseStatus,
    submit_receipt: {
      status: "local_mock_annotation_written",
      receipt_id: asString(submitReceipt?.receipt_id, `local_mock:${safeId.taskId}:${writeStatus}:${labelCount}`),
      task_id: asString(remote.task_id, safeId.taskId),
      robot_id: asString(remote.robot_id, submitPayload.robotId),
      label_count: labelCount,
      write_status: writeStatus as "created" | "updated",
      duplicate: asBoolean(remote.duplicate),
      blocked_reason: "none_local_mock_annotation_written_not_real_api",
    },
    submitted_labels: itemizedLabels.length > 0 ? itemizedLabels : submitPayload.labels,
    label_summary: {
      itemized_label_count: labelCount,
      pending_item_count: asNumber(labelSummary?.pending_item_count) ?? 0,
      labeled_item_count: asNumber(labelSummary?.labeled_item_count) ?? 0,
      latest_label_updated_at_ms: asNumber(labelSummary?.latest_label_updated_at_ms),
    },
    local_mock_annotation_submit_written: true,
    blocked_reasons: ["real_annotation_api_connected_false", "cloud_write_executed_false"],
    not_proven: stringList(remote.not_proven).length > 0
      ? stringList(remote.not_proven)
      : ["real_annotation_submit_success", "real_annotation_review_api", "delivery_success"],
    fail_closed_reason: "none",
    local_loopback_only: true,
    ...fixedAnnotationFalseFields(),
    ...PROOF_FLAGS,
  };
}

function normalizeExportRow(value: unknown, rowIndex: number, taskId: string): O7AnnotationDatasetExportRow | null {
  // dataset sample row 只展示训练数据最小可复核字段，不透传图片、base64 或路径。
  const row = asRecord(value);
  if (!row) {
    return null;
  }
  const itemId = annotationText(row.item_id ?? row.itemId, "", 80);
  const labelType = annotationText(row.label_type ?? row.type, "", 120);
  const valueText = annotationText(row.value ?? row.label, "", 240);
  if (!itemId || !labelType || !valueText || [itemId, labelType, valueText].includes("[unsafe]")) {
    return null;
  }
  return {
    row_index: Math.trunc(asNumber(row.row_index ?? row.index) ?? rowIndex),
    task_id: annotationText(row.task_id, taskId, 80),
    item_id: itemId,
    label_type: labelType,
    value: valueText,
    evidence_ref: safePathToken(row.evidence_ref ?? row.evidenceRef ?? ""),
  };
}

export async function buildO7ConsumerAnnotationExport(
  baseUrl: string,
  taskId: string,
  format = "jsonl",
): Promise<O7AnnotationDatasetExportResult> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosedAnnotationExport(normalized.reason, baseUrl, taskId);
  }
  const safeId = safeTaskId(taskId);
  if (!safeId.ok) {
    return failClosedAnnotationExport(safeId.reason, normalized.normalized, taskId);
  }
  if (format.trim() !== "jsonl") {
    return failClosedAnnotationExport("export_format_not_allowed", normalized.normalized, safeId.taskId);
  }

  const url = new URL(`${normalized.normalized}${REMOTE_LABEL_EXPORT_ENDPOINT_PREFIX}${encodeURIComponent(safeId.taskId)}/export`);
  url.searchParams.set("format", "jsonl");
  let responseStatus: number | null = null;
  let remoteJson: unknown;
  try {
    const response = await fetch(url, { method: "GET" });
    responseStatus = response.status;
    remoteJson = await response.json();
    if (!response.ok) {
      return failClosedAnnotationExport(`o6_annotation_export_http_${response.status}`, normalized.normalized, safeId.taskId, responseStatus);
    }
  } catch {
    return failClosedAnnotationExport("o6_annotation_export_fetch_failed", normalized.normalized, safeId.taskId, responseStatus);
  }

  const remote = asRecord(remoteJson);
  if (!remote) {
    return failClosedAnnotationExport("o6_annotation_export_response_not_object", normalized.normalized, safeId.taskId, responseStatus);
  }
  if (asString(remote.schema, "") !== "trashbot.o6.annotation_dataset_export.v1") {
    return failClosedAnnotationExport("o6_annotation_export_schema_mismatch", normalized.normalized, safeId.taskId, responseStatus);
  }
  const dangerous = scanDangerousTrueFields(remote);
  if (dangerous.length > 0) {
    return failClosedAnnotationExport(`dangerous_true_fields:${dangerous.join(",")}`, normalized.normalized, safeId.taskId, responseStatus);
  }
  if (containsUnsafeAnnotationCopy(remote)) {
    return failClosedAnnotationExport("o6_annotation_export_contains_unsafe_copy", normalized.normalized, safeId.taskId, responseStatus);
  }
  if (asString(remote.export_status, "blocked_not_proven") !== "local_mock_export_ready") {
    return failClosedAnnotationExport("o6_annotation_export_status_mismatch", normalized.normalized, safeId.taskId, responseStatus);
  }

  const manifest = asRecord(remote.export_manifest);
  const sampleRows = sampleObjectArray(remote.sample_rows, O7_ANNOTATION_EXPORT_ROW_LIMIT)
    .map((row, index) => normalizeExportRow(row, index, safeId.taskId))
    .filter((row): row is O7AnnotationDatasetExportRow => Boolean(row));
  const labelCount = asNumber(remote.label_count ?? manifest?.label_count) ?? sampleRows.length;
  const itemCount = asNumber(remote.item_count ?? manifest?.item_count) ?? sampleRows.length;
  const rowCount = asNumber(remote.row_count ?? manifest?.row_count) ?? sampleRows.length;
  return {
    schema: ANNOTATION_EXPORT_SCHEMA,
    adapter_status: "local_mock_export_ready",
    source_base_url: normalized.normalized,
    remote_endpoint: `${REMOTE_LABEL_EXPORT_ENDPOINT_PREFIX}${safeId.taskId}/export?format=jsonl`,
    remote_schema: "trashbot.o6.annotation_dataset_export.v1",
    requested_task_id: safeId.taskId,
    o6_http_status: responseStatus,
    format: "jsonl",
    export_status: "local_mock_export_ready",
    export_manifest: {
      manifest_id: asString(manifest?.manifest_id ?? manifest?.dataset_id ?? remote.export_id, `local_mock_export:${safeId.taskId}`),
      task_id: asString(remote.task_id ?? manifest?.task_id, safeId.taskId),
      robot_id: asString(remote.robot_id ?? manifest?.robot_id, "unknown_robot"),
      format: "jsonl",
      label_count: labelCount,
      item_count: itemCount,
      row_count: rowCount,
      status: "local_mock_export_ready",
    },
    sample_rows: sampleRows,
    local_mock_dataset_export_written: true,
    blocked_reasons: ["real_dataset_export_connected_false", "dataset_export_available_false"],
    not_proven: stringList(remote.not_proven).length > 0
      ? stringList(remote.not_proven)
      : ["real_dataset_export", "real_dataset_export_connected", "delivery_success"],
    fail_closed_reason: "none",
    local_loopback_only: true,
    ...fixedAnnotationFalseFields(),
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
