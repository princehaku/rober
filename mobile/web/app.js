const ENDPOINTS = {
  status: "/api/status",
  diagnostics: "/api/diagnostics",
  start: "/api/collect",
  confirm_dropoff: "/api/dropoff/confirm",
  cancel: "/api/cancel",
};

const ACTIONS = {
  start: { buttonId: "startButton", permission: "can_collect", label: "开始送达" },
  confirm_dropoff: { buttonId: "confirmButton", permission: "can_confirm_dropoff", label: "确认投放" },
  cancel: { buttonId: "cancelButton", permission: "can_cancel", label: "取消任务" },
};

const SAFE_EMPTY = "等待后端提供安全摘要。";
const ACTION_FEEDBACK_BOUNDARY = "software_proof_docker_mobile_action_feedback_gate";
const CLOUD_READINESS_BOUNDARY = "software_proof_docker_mobile_cloud_readiness_summary_gate";
const MOBILE_DEVICE_ACCEPTANCE_BOUNDARY = "software_proof_docker_mobile_device_acceptance_readiness_gate";
const MOBILE_DEVICE_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_device_evidence_capture_gate";
const MOBILE_DEVICE_HANDOFF_SESSION_BOUNDARY = "software_proof_docker_mobile_device_handoff_session_gate";
const MOBILE_BROWSER_ACCEPTANCE_BOUNDARY = "software_proof_docker_mobile_browser_acceptance_bundle_gate";
const MOBILE_PWA_INSTALL_PROMPT_BOUNDARY = "software_proof_docker_mobile_pwa_install_prompt_evidence_gate";
const MOBILE_PWA_INSTALL_PROMPT_EVENT_CAPTURE_BOUNDARY = "software_proof_docker_mobile_pwa_install_prompt_event_capture_gate";
const MOBILE_PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_BOUNDARY = "software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate";
const MOBILE_REAL_DEVICE_EVIDENCE_INTAKE_BOUNDARY = "software_proof_docker_mobile_real_device_evidence_intake_gate";
const MOBILE_REAL_DEVICE_ACCEPTANCE_DECISION_BOUNDARY = "software_proof_docker_mobile_real_device_acceptance_decision_gate";
const MOBILE_REAL_DEVICE_REVIEW_HANDOFF_BOUNDARY = "software_proof_docker_mobile_real_device_review_handoff_gate";
const MOBILE_REAL_DEVICE_REVIEW_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_review_execution_gate";
const MOBILE_REAL_DEVICE_RETEST_REQUEST_BOUNDARY = "software_proof_docker_mobile_real_device_retest_request_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_package_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_review_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate";
const MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate";
const PRIMARY_JOURNEY_BOUNDARY = "software_proof_docker_mobile_primary_journey_gate";
const RECOVERY_DECISION_BOUNDARY = "software_proof_docker_mobile_recovery_decision_gate";
const ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_BOUNDARY = "software_proof_docker_route_task_rehearsal_operator_review_gate";
const TERMINAL_ACTION_BOUNDARY = "software_proof_docker_mobile_terminal_action_confirmation_gate";
const ACK_PROCESSING_COPY = "ACK 只代表 accepted/processing evidence，不代表送达成功、投放完成或取消已落地。";
const ACK_PROCESSING_ENUM = "accepted_processing_only_not_delivery_success";
const DEVICE_EVIDENCE_SCHEMA = "trashbot.mobile_device_evidence_capture.v1";
const DEVICE_EVIDENCE_PACKAGE_SCHEMA = "trashbot.mobile_device_evidence_package.v1";
const DEVICE_HANDOFF_SESSION_SCHEMA = "trashbot.mobile_device_handoff_session.v1";
const DEVICE_HANDOFF_PACKAGE_SCHEMA = "trashbot.mobile_device_handoff_package.v1";
const ACCEPTANCE_BUNDLE_SCHEMA = "trashbot.mobile_browser_acceptance_bundle.v1";
const PWA_INSTALL_PROMPT_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence.v1";
const PWA_INSTALL_PROMPT_SUMMARY_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_summary.v1";
const PWA_INSTALL_PROMPT_PACKAGE_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_package.v1";
const PWA_INSTALL_PROMPT_EVENT_CAPTURE_SCHEMA = "trashbot.mobile_pwa_install_prompt_event_capture.v1";
const PWA_INSTALL_PROMPT_EVENT_CAPTURE_SUMMARY_SCHEMA = "trashbot.mobile_pwa_install_prompt_event_capture_summary.v1";
const PWA_INSTALL_PROMPT_EVENT_CAPTURE_COPY_SCHEMA = "trashbot.mobile_pwa_install_prompt_event_capture_copy.v1";
const PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_export.v1";
const PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_SUMMARY_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1";
const PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_COPY_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1";
const REAL_DEVICE_EVIDENCE_INTAKE_SCHEMA = "trashbot.mobile_real_device_evidence_intake.v1";
const REAL_DEVICE_EVIDENCE_INTAKE_SUMMARY_SCHEMA = "trashbot.mobile_real_device_evidence_intake_summary.v1";
const REAL_DEVICE_EVIDENCE_PACKAGE_SCHEMA = "trashbot.mobile_real_device_evidence_package.v1";
const REAL_DEVICE_ACCEPTANCE_DECISION_SCHEMA = "trashbot.mobile_real_device_acceptance_decision.v1";
const REAL_DEVICE_ACCEPTANCE_DECISION_SUMMARY_SCHEMA = "trashbot.mobile_real_device_acceptance_decision_summary.v1";
const REAL_DEVICE_ACCEPTANCE_DECISION_PACKAGE_SCHEMA = "trashbot.mobile_real_device_acceptance_decision_package.v1";
const REAL_DEVICE_REVIEW_HANDOFF_SCHEMA = "trashbot.mobile_real_device_review_handoff.v1";
const REAL_DEVICE_REVIEW_HANDOFF_SUMMARY_SCHEMA = "trashbot.mobile_real_device_review_handoff_summary.v1";
const REAL_DEVICE_REVIEW_HANDOFF_PACKAGE_SCHEMA = "trashbot.mobile_real_device_review_handoff_package.v1";
const REAL_DEVICE_REVIEW_EXECUTION_SCHEMA = "trashbot.mobile_real_device_review_execution.v1";
const REAL_DEVICE_REVIEW_EXECUTION_SUMMARY_SCHEMA = "trashbot.mobile_real_device_review_execution_summary.v1";
const REAL_DEVICE_REVIEW_EXECUTION_PACKAGE_SCHEMA = "trashbot.mobile_real_device_review_execution_package.v1";
const REAL_DEVICE_RETEST_REQUEST_SCHEMA = "trashbot.mobile_real_device_retest_request.v1";
const REAL_DEVICE_RETEST_REQUEST_SUMMARY_SCHEMA = "trashbot.mobile_real_device_retest_request_summary.v1";
const REAL_DEVICE_RETEST_REQUEST_PACKAGE_SCHEMA = "trashbot.mobile_real_device_retest_request_package.v1";
const REAL_DEVICE_FIELD_TRIAL_SCHEMA = "trashbot.mobile_real_device_field_trial_package.v1";
const REAL_DEVICE_FIELD_TRIAL_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_package_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_package_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_REVIEW_SCHEMA = "trashbot.mobile_real_device_field_trial_review.v1";
const REAL_DEVICE_FIELD_TRIAL_REVIEW_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_review_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_REVIEW_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_review_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SCHEMA = "trashbot.mobile_real_device_field_trial_runbook_execution.v1";
const REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_runbook_execution_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_record.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_record_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_record_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_ARCHIVE_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_record_archive.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_verdict.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_verdict_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SCHEMA = "trashbot.mobile_real_device_field_trial_retest_execution.v1";
const REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_retest_execution_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_retest_execution_copy.v1";
const REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SCHEMA = "trashbot.mobile_real_device_field_trial_acceptance_session.v1";
const REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SUMMARY_SCHEMA = "trashbot.mobile_real_device_field_trial_acceptance_session_summary.v1";
const REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_COPY_SCHEMA = "trashbot.mobile_real_device_field_trial_acceptance_session_copy.v1";
const UNSAFE_BUNDLE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|credential-bearing url|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|uart|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/ws\/|traceback|checksum|complete artifact|artifact|raw browser event|raw event|raw promise|complete ua|full ua|完整 ua|raw robot response|raw intake json|robot\/internal|internal technical)/i;
const UNSAFE_RECOVERY_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;
const UNSAFE_OPERATOR_REVIEW_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|raw ros topic|\/cmd_vel|cmd_vel|serial|uart|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/private\/|\/tmp\/|\/ws\/|\/var\/|[a-z]:\\|traceback|checksum|raw artifact|full execution bundle|complete artifact|raw robot response|robot\/internal|internal technical|password)/i;
const UNSAFE_TERMINAL_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;
const UNSAFE_REAL_DEVICE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|https?:\/\/[^\s/]+:[^\s@]+@|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|ttyusb|ttyacm|baudrate|wave rover|wave\s*rover|\/users\/|\/private\/|\/tmp\/|\/ws\/|\/var\/|[a-z]:\\|traceback|checksum|complete artifact|artifact|raw robot response|robot response|raw intake json|robot\/internal|internal technical|password)/i;

let latestStatus = null;
let latestDiagnostics = null;
let latestActionFeedback = null;
let latestAcceptanceBundle = null;
let latestDeviceEvidencePackage = null;
let latestDeviceHandoffSession = null;
let latestPwaInstallPromptPackage = null;
let latestPwaInstallPromptEventCapturePackage = null;
let latestPwaInstallPromptEvidenceExportPackage = null;
let latestRouteTaskReview = null;
let deferredPwaInstallPromptEvent = null;
let pwaInstallPromptEventState = null;
let latestRealDeviceEvidencePackage = null;
let latestRealDeviceAcceptanceDecisionPackage = null;
let latestRealDeviceReviewHandoffPackage = null;
let latestRealDeviceReviewExecutionPackage = null;
let latestRealDeviceRetestRequestPackage = null;
let latestRealDeviceFieldTrialPackage = null;
let latestRealDeviceFieldTrialReviewPackage = null;
let latestRealDeviceFieldTrialRunbookExecutionPackage = null;
let latestRealDeviceFieldTrialEvidenceRecordPackage = null;
let archivedRealDeviceFieldTrialEvidenceRecordPackage = null;
let latestRealDeviceFieldTrialEvidenceVerdictPackage = null;
let latestRealDeviceFieldTrialRetestExecutionPackage = null;
let latestRealDeviceFieldTrialAcceptanceSessionPackage = null;
let importedRealDeviceEvidence = null;
let pendingTerminalAction = null;
let stableHandoffClientReference = `mobile_web_handoff_${Date.now()}`;
let stablePwaInstallPromptExportReference = `mobile_web_pwa_install_export_${Date.now()}`;
let stableFieldTrialReference = `field_trial_${Date.now()}`;
let stableFieldTrialEvidenceRecordReference = `field_trial_evidence_record_${Date.now()}`;
let stableFieldTrialEvidenceVerdictReference = `field_trial_evidence_verdict_${Date.now()}`;
let stableFieldTrialRetestExecutionReference = `field_trial_retest_execution_${Date.now()}`;
let stableFieldTrialAcceptanceSessionReference = `field_trial_acceptance_session_${Date.now()}`;
let latestStartGate = {
  destination: null,
  destinationReady: false,
  loadConfirmed: false,
  blockedReason: "等待状态刷新。",
};

function $(id) {
  return document.getElementById(id);
}

function safeText(value, fallback = SAFE_EMPTY) {
  // 所有可见文案只取 phone-safe 字段；对象和数组不直接展示，避免泄漏调试结构。
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return fallback;
}

function safeBundleText(value, fallback = "未证明") {
  // 验收包面向手机用户和支持人员复制；命中敏感词时直接降级为安全摘要。
  const text = safeText(value, fallback);
  if (UNSAFE_BUNDLE_TEXT.test(text)) {
    return fallback;
  }
  return text;
}

function safeRecoveryText(value, fallback = "等待安全摘要") {
  // 恢复决策会放在首屏，命中成功/硬件/凭证等高风险词时只能显示保守文案。
  const text = safeText(value, fallback);
  if (UNSAFE_RECOVERY_TEXT.test(text)) {
    return fallback;
  }
  return text;
}

function safeOperatorReviewText(value, fallback = "not_proven") {
  // 排练复盘来自诊断/状态摘要，必须过滤路径、raw artifact、完整 bundle 和凭证。
  const text = safeText(value, fallback);
  if (UNSAFE_OPERATOR_REVIEW_TEXT.test(text)) {
    return fallback;
  }
  return text;
}

function safeTerminalActionText(value, fallback = "等待安全摘要") {
  // 终端动作确认直接影响投放/取消入口，任何成功暗示或内部细节都降级为保守文案。
  const text = safeText(value, fallback);
  if (UNSAFE_TERMINAL_TEXT.test(text)) {
    return fallback;
  }
  return text;
}

function safeRealDeviceEvidenceText(value, fallback = "not_proven") {
  // 真实设备材料来自用户粘贴或后端摘要，必须先过滤凭证、ROS/硬件细节和原始响应。
  const text = safeText(value, fallback);
  if (UNSAFE_REAL_DEVICE_TEXT.test(text)) {
    return fallback;
  }
  return text;
}

function safeBundleBoolean(value) {
  // 只有显式布尔 true 才能参与放行，避免字符串或缺字段误开主操作。
  return value === true;
}

async function fetchJson(url, options = {}) {
  // 控制请求不做离线队列；失败直接进入可恢复错误文案。
  const response = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      "Accept": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(`request_failed_${response.status}`);
  }
  return response.json();
}

function readinessFromStatus(status) {
  // mobile/web 只是 consumer：优先消费后端聚合的 phone_readiness。
  return status && typeof status.phone_readiness === "object" ? status.phone_readiness : {};
}

function offlineResumeFromStatus(status, readiness) {
  // offline/resume 可能在顶层或 readiness 内；两处都来自同一后端契约。
  if (status && typeof status.phone_offline_resume_readiness === "object") {
    return status.phone_offline_resume_readiness;
  }
  if (readiness && typeof readiness.phone_offline_resume_readiness === "object") {
    return readiness.phone_offline_resume_readiness;
  }
  return {};
}

function voicePromptFromStatus(status, readiness) {
  // 语音提示 readiness 只展示后端安全文案，不推断真实播放结果。
  if (status && typeof status.voice_prompt_readiness === "object") {
    return status.voice_prompt_readiness;
  }
  if (readiness && typeof readiness.voice_prompt_readiness === "object") {
    return readiness.voice_prompt_readiness;
  }
  return {};
}

function cloudReadinessSummaryFromStatus(status, readiness) {
  // 云摘要只读消费后端 phone-safe 字段，避免前端把配置证明误写成真实云可用。
  const candidates = [
    status?.phone_cloud_readiness_summary,
    status?.mobile_cloud_readiness_summary,
    status?.cloud_readiness_summary,
    readiness?.cloud_readiness,
    readiness?.phone_cloud_readiness_summary,
    readiness?.mobile_cloud_readiness_summary,
    readiness?.cloud_readiness_summary,
  ];
  const provided = candidates.find((value) => value && typeof value === "object");
  if (provided) {
    return { ...provided, missing: false };
  }
  return {
    missing: true,
    schema: "trashbot.phone_cloud_readiness_summary.v1",
    overall_status: "waiting_summary",
    preflight_status: "waiting_summary",
    db_queue_status: "waiting_summary",
    production_ready: false,
    primary_actions_enabled: false,
    safe_phone_copy: "等待后端提供 cloud/preflight/DB/queue 的 phone-safe 摘要。",
    recovery_hint: "摘要缺失时不启用 Start、Confirm 或 Cancel；请刷新状态或打开诊断。",
    ack_semantics: ACK_PROCESSING_COPY,
    evidence_boundary: CLOUD_READINESS_BOUNDARY,
  };
}

function mobileDeviceAcceptanceReadinessFromStatus(status, readiness, diagnostics) {
  // 真实手机/browser 验收必须来自后端或诊断摘要；静态页面不能把本地 smoke 升格成真机证明。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_device_acceptance_readiness,
    status?.phone_device_acceptance_readiness,
    status?.mobile_browser_acceptance_readiness,
    readiness?.mobile_device_acceptance_readiness,
    readiness?.phone_device_acceptance_readiness,
    readiness?.mobile_browser_acceptance_readiness,
    diagnostics?.mobile_device_acceptance_readiness,
    diagnostics?.phone_device_acceptance_readiness,
    diagnostics?.mobile_browser_acceptance_readiness,
    diagnosticsReadiness.mobile_device_acceptance_readiness,
    diagnosticsReadiness.phone_device_acceptance_readiness,
    diagnosticsReadiness.mobile_browser_acceptance_readiness,
  ];
  const provided = candidates.find((value) => value && typeof value === "object");
  if (provided) {
    return { ...provided, missing: false };
  }
  return {
    missing: true,
    schema: "trashbot.mobile_device_acceptance_readiness.v1",
    schema_version: 1,
    overall_status: "blocked",
    primary_actions_enabled: false,
    production_app_ready: false,
    safe_to_control: false,
    viewport_status: "not_proven",
    touch_target_status: "not_proven",
    pwa_install_prompt_status: "not_proven",
    offline_status: "not_proven",
    diagnostics_status: "not_proven",
    cloud_gate_status: "not_proven",
    safe_phone_copy: "缺少真实手机设备/browser、production app 和真实 PWA install prompt 验收摘要；手机主操作安全关闭。",
    recovery_hint: "请完成真实手机浏览器/设备验收或由后端提供 blocked-by-design 摘要；Diagnostics 和 Support Handoff 仍可用。",
    ack_semantics: ACK_PROCESSING_COPY,
    evidence_boundary: MOBILE_DEVICE_ACCEPTANCE_BOUNDARY,
    not_proven: [
      "真实手机设备/browser",
      "production app",
      "真实 PWA install prompt",
      "真实云/4G",
      "HIL",
      "真实送达",
    ],
  };
}

function mobileBrowserAcceptanceBundleCandidate(status, readiness, diagnostics) {
  // 新 bundle 可能来自 status、phone_readiness 或 diagnostics；按后端显式字段优先消费。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_browser_acceptance_bundle,
    status?.phone_browser_acceptance_bundle,
    status?.mobile_acceptance_evidence_bundle,
    readiness?.mobile_browser_acceptance_bundle,
    readiness?.phone_browser_acceptance_bundle,
    readiness?.mobile_acceptance_evidence_bundle,
    diagnostics?.mobile_browser_acceptance_bundle,
    diagnostics?.phone_browser_acceptance_bundle,
    diagnostics?.mobile_acceptance_evidence_bundle,
    diagnosticsReadiness.mobile_browser_acceptance_bundle,
    diagnosticsReadiness.phone_browser_acceptance_bundle,
    diagnosticsReadiness.mobile_acceptance_evidence_bundle,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileDeviceEvidenceCandidate(status, readiness, diagnostics) {
  // 证据采集包可来自 status/readiness/diagnostics；前端只合并白名单字段。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_device_evidence_capture,
    status?.mobile_device_evidence_capture_summary,
    status?.mobile_device_evidence_package,
    readiness?.mobile_device_evidence_capture,
    readiness?.mobile_device_evidence_capture_summary,
    readiness?.mobile_device_evidence_package,
    diagnostics?.mobile_device_evidence_capture,
    diagnostics?.mobile_device_evidence_capture_summary,
    diagnostics?.mobile_device_evidence_package,
    diagnosticsReadiness.mobile_device_evidence_capture,
    diagnosticsReadiness.mobile_device_evidence_capture_summary,
    diagnosticsReadiness.mobile_device_evidence_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileDeviceHandoffSessionCandidate(status, readiness, diagnostics) {
  // 交接会话是支持/验收 metadata；只从后端 phone-safe 字段读取，不消费 raw robot 响应。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_device_handoff_session,
    status?.mobile_device_handoff_session_summary,
    status?.mobile_device_handoff_package,
    readiness?.mobile_device_handoff_session,
    readiness?.mobile_device_handoff_session_summary,
    readiness?.mobile_device_handoff_package,
    diagnostics?.mobile_device_handoff_session,
    diagnostics?.mobile_device_handoff_session_summary,
    diagnostics?.mobile_device_handoff_package,
    diagnosticsReadiness.mobile_device_handoff_session,
    diagnosticsReadiness.mobile_device_handoff_session_summary,
    diagnosticsReadiness.mobile_device_handoff_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobilePwaInstallPromptEvidenceCandidate(status, readiness, diagnostics) {
  // install prompt evidence 可能由 status、phone_readiness 或 diagnostics 提供；前端只消费 phone-safe 摘要。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_pwa_install_prompt_evidence,
    status?.mobile_pwa_install_prompt_evidence_summary,
    status?.mobile_pwa_install_prompt_evidence_package,
    readiness?.mobile_pwa_install_prompt_evidence,
    readiness?.mobile_pwa_install_prompt_evidence_summary,
    readiness?.mobile_pwa_install_prompt_evidence_package,
    diagnostics?.mobile_pwa_install_prompt_evidence,
    diagnostics?.mobile_pwa_install_prompt_evidence_summary,
    diagnostics?.mobile_pwa_install_prompt_evidence_package,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence_summary,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobilePwaInstallPromptEventCaptureCandidate(status, readiness, diagnostics) {
  // event capture 是浏览器事件观测包；兼容 status、phone_readiness 与 diagnostics 三个来源。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_pwa_install_prompt_event_capture,
    status?.mobile_pwa_install_prompt_event_capture_summary,
    status?.mobile_pwa_install_prompt_event_capture_copy,
    readiness?.mobile_pwa_install_prompt_event_capture,
    readiness?.mobile_pwa_install_prompt_event_capture_summary,
    readiness?.mobile_pwa_install_prompt_event_capture_copy,
    diagnostics?.mobile_pwa_install_prompt_event_capture,
    diagnostics?.mobile_pwa_install_prompt_event_capture_summary,
    diagnostics?.mobile_pwa_install_prompt_event_capture_copy,
    diagnosticsReadiness.mobile_pwa_install_prompt_event_capture,
    diagnosticsReadiness.mobile_pwa_install_prompt_event_capture_summary,
    diagnosticsReadiness.mobile_pwa_install_prompt_event_capture_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobilePwaInstallPromptEvidenceExportCandidate(status, readiness, diagnostics) {
  // export 是现场验收材料包的最外层合同；只接受显式 phone-safe export 字段。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_pwa_install_prompt_evidence_export,
    status?.mobile_pwa_install_prompt_evidence_export_summary,
    status?.mobile_pwa_install_prompt_evidence_export_copy,
    readiness?.mobile_pwa_install_prompt_evidence_export,
    readiness?.mobile_pwa_install_prompt_evidence_export_summary,
    readiness?.mobile_pwa_install_prompt_evidence_export_copy,
    diagnostics?.mobile_pwa_install_prompt_evidence_export,
    diagnostics?.mobile_pwa_install_prompt_evidence_export_summary,
    diagnostics?.mobile_pwa_install_prompt_evidence_export_copy,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence_export,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence_export_summary,
    diagnosticsReadiness.mobile_pwa_install_prompt_evidence_export_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceEvidenceIntakeCandidate(status, readiness, diagnostics) {
  // 真实设备材料 intake 可能来自 status、phone_readiness 或 diagnostics；导入 JSON 只作为本地白名单输入。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    importedRealDeviceEvidence,
    status?.mobile_real_device_evidence_intake,
    status?.mobile_real_device_evidence_intake_summary,
    status?.mobile_real_device_evidence_package,
    readiness?.mobile_real_device_evidence_intake,
    readiness?.mobile_real_device_evidence_intake_summary,
    readiness?.mobile_real_device_evidence_package,
    diagnostics?.mobile_real_device_evidence_intake,
    diagnostics?.mobile_real_device_evidence_intake_summary,
    diagnostics?.mobile_real_device_evidence_package,
    diagnosticsReadiness.mobile_real_device_evidence_intake,
    diagnosticsReadiness.mobile_real_device_evidence_intake_summary,
    diagnosticsReadiness.mobile_real_device_evidence_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceAcceptanceDecisionCandidate(status, readiness, diagnostics) {
  // 决策 gate 优先消费后端/诊断显式决策；缺失时才从 intake/package 派生保守结论。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_acceptance_decision,
    status?.mobile_real_device_acceptance_decision_summary,
    status?.mobile_real_device_acceptance_decision_package,
    readiness?.mobile_real_device_acceptance_decision,
    readiness?.mobile_real_device_acceptance_decision_summary,
    readiness?.mobile_real_device_acceptance_decision_package,
    diagnostics?.mobile_real_device_acceptance_decision,
    diagnostics?.mobile_real_device_acceptance_decision_summary,
    diagnostics?.mobile_real_device_acceptance_decision_package,
    diagnosticsReadiness.mobile_real_device_acceptance_decision,
    diagnosticsReadiness.mobile_real_device_acceptance_decision_summary,
    diagnosticsReadiness.mobile_real_device_acceptance_decision_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceReviewHandoffCandidate(status, readiness, diagnostics) {
  // review handoff 只消费 phone-safe 评审交接字段；缺失时从 acceptance decision 派生保守会话。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_review_handoff,
    status?.mobile_real_device_review_handoff_summary,
    status?.mobile_real_device_review_handoff_package,
    readiness?.mobile_real_device_review_handoff,
    readiness?.mobile_real_device_review_handoff_summary,
    readiness?.mobile_real_device_review_handoff_package,
    diagnostics?.mobile_real_device_review_handoff,
    diagnostics?.mobile_real_device_review_handoff_summary,
    diagnostics?.mobile_real_device_review_handoff_package,
    diagnosticsReadiness.mobile_real_device_review_handoff,
    diagnosticsReadiness.mobile_real_device_review_handoff_summary,
    diagnosticsReadiness.mobile_real_device_review_handoff_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceReviewExecutionCandidate(status, readiness, diagnostics) {
  // review execution 是人工评审执行记录，只消费 phone-safe 字段；缺失时从 handoff 派生 blocked 记录。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_review_execution,
    status?.mobile_real_device_review_execution_summary,
    status?.mobile_real_device_review_execution_package,
    readiness?.mobile_real_device_review_execution,
    readiness?.mobile_real_device_review_execution_summary,
    readiness?.mobile_real_device_review_execution_package,
    diagnostics?.mobile_real_device_review_execution,
    diagnostics?.mobile_real_device_review_execution_summary,
    diagnostics?.mobile_real_device_review_execution_package,
    diagnosticsReadiness.mobile_real_device_review_execution,
    diagnosticsReadiness.mobile_real_device_review_execution_summary,
    diagnosticsReadiness.mobile_real_device_review_execution_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceRetestRequestCandidate(status, readiness, diagnostics) {
  // retest request 是下一轮真实设备复测材料请求，只消费 phone-safe 字段；缺失时从 review execution 派生。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_retest_request,
    status?.mobile_real_device_retest_request_summary,
    status?.mobile_real_device_retest_request_package,
    readiness?.mobile_real_device_retest_request,
    readiness?.mobile_real_device_retest_request_summary,
    readiness?.mobile_real_device_retest_request_package,
    diagnostics?.mobile_real_device_retest_request,
    diagnostics?.mobile_real_device_retest_request_summary,
    diagnostics?.mobile_real_device_retest_request_package,
    diagnosticsReadiness.mobile_real_device_retest_request,
    diagnosticsReadiness.mobile_real_device_retest_request_summary,
    diagnosticsReadiness.mobile_real_device_retest_request_package,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialCandidate(status, readiness, diagnostics) {
  // field trial package 是现场试跑记录包，只消费 phone-safe 字段；缺失时从当前浏览器和表单派生。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_package,
    status?.mobile_real_device_field_trial_package_summary,
    status?.mobile_real_device_field_trial_package_copy,
    readiness?.mobile_real_device_field_trial_package,
    readiness?.mobile_real_device_field_trial_package_summary,
    readiness?.mobile_real_device_field_trial_package_copy,
    diagnostics?.mobile_real_device_field_trial_package,
    diagnostics?.mobile_real_device_field_trial_package_summary,
    diagnostics?.mobile_real_device_field_trial_package_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_package,
    diagnosticsReadiness.mobile_real_device_field_trial_package_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_package_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialReviewCandidate(status, readiness, diagnostics) {
  // review package 是现场材料复核支持 metadata；只消费 phone-safe 字段，不触发控制或 ACK。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_review,
    status?.mobile_real_device_field_trial_review_summary,
    status?.mobile_real_device_field_trial_review_copy,
    readiness?.mobile_real_device_field_trial_review,
    readiness?.mobile_real_device_field_trial_review_summary,
    readiness?.mobile_real_device_field_trial_review_copy,
    diagnostics?.mobile_real_device_field_trial_review,
    diagnostics?.mobile_real_device_field_trial_review_summary,
    diagnostics?.mobile_real_device_field_trial_review_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_review,
    diagnosticsReadiness.mobile_real_device_field_trial_review_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_review_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialRunbookExecutionCandidate(status, readiness, diagnostics) {
  // runbook execution package 只描述下一次现场试跑怎么执行；不作为控制命令或验收通过证明。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_runbook_execution,
    status?.mobile_real_device_field_trial_runbook_execution_summary,
    status?.mobile_real_device_field_trial_runbook_execution_copy,
    readiness?.mobile_real_device_field_trial_runbook_execution,
    readiness?.mobile_real_device_field_trial_runbook_execution_summary,
    readiness?.mobile_real_device_field_trial_runbook_execution_copy,
    diagnostics?.mobile_real_device_field_trial_runbook_execution,
    diagnostics?.mobile_real_device_field_trial_runbook_execution_summary,
    diagnostics?.mobile_real_device_field_trial_runbook_execution_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_runbook_execution,
    diagnosticsReadiness.mobile_real_device_field_trial_runbook_execution_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_runbook_execution_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialEvidenceRecordCandidate(status, readiness, diagnostics) {
  // evidence record package 是现场记录 metadata；只消费 phone-safe 字段，不能进入控制或 ACK 路径。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_evidence_record,
    status?.mobile_real_device_field_trial_evidence_record_summary,
    status?.mobile_real_device_field_trial_evidence_record_copy,
    status?.mobile_real_device_field_trial_evidence_record_archive,
    readiness?.mobile_real_device_field_trial_evidence_record,
    readiness?.mobile_real_device_field_trial_evidence_record_summary,
    readiness?.mobile_real_device_field_trial_evidence_record_copy,
    readiness?.mobile_real_device_field_trial_evidence_record_archive,
    diagnostics?.mobile_real_device_field_trial_evidence_record,
    diagnostics?.mobile_real_device_field_trial_evidence_record_summary,
    diagnostics?.mobile_real_device_field_trial_evidence_record_copy,
    diagnostics?.mobile_real_device_field_trial_evidence_record_archive,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_record,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_record_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_record_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_record_archive,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialEvidenceVerdictCandidate(status, readiness, diagnostics) {
  // verdict package 只做现场证据复核结论和下一步材料请求，不进入任何控制或 ACK 提交流程。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_evidence_verdict,
    status?.mobile_real_device_field_trial_evidence_verdict_summary,
    status?.mobile_real_device_field_trial_evidence_verdict_copy,
    readiness?.mobile_real_device_field_trial_evidence_verdict,
    readiness?.mobile_real_device_field_trial_evidence_verdict_summary,
    readiness?.mobile_real_device_field_trial_evidence_verdict_copy,
    diagnostics?.mobile_real_device_field_trial_evidence_verdict,
    diagnostics?.mobile_real_device_field_trial_evidence_verdict_summary,
    diagnostics?.mobile_real_device_field_trial_evidence_verdict_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_verdict,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_verdict_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_evidence_verdict_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialRetestExecutionCandidate(status, readiness, diagnostics) {
  // retest execution 只消费后端显式 summary/copy；缺失时从 verdict 的请求字段派生执行清单。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_retest_execution,
    status?.mobile_real_device_field_trial_retest_execution_summary,
    status?.mobile_real_device_field_trial_retest_execution_copy,
    readiness?.mobile_real_device_field_trial_retest_execution,
    readiness?.mobile_real_device_field_trial_retest_execution_summary,
    readiness?.mobile_real_device_field_trial_retest_execution_copy,
    diagnostics?.mobile_real_device_field_trial_retest_execution,
    diagnostics?.mobile_real_device_field_trial_retest_execution_summary,
    diagnostics?.mobile_real_device_field_trial_retest_execution_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_retest_execution,
    diagnosticsReadiness.mobile_real_device_field_trial_retest_execution_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_retest_execution_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileCurrentPwaFieldTrialBrowserProofCandidate(status, readiness, diagnostics) {
  // current PWA browser proof 只是上游本地浏览器 proof；只能作为 session 的保守来源摘要。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_current_pwa_field_trial_browser_proof,
    status?.mobile_current_pwa_field_trial_browser_proof_summary,
    status?.mobile_current_pwa_field_trial_browser_proof_copy,
    readiness?.mobile_current_pwa_field_trial_browser_proof,
    readiness?.mobile_current_pwa_field_trial_browser_proof_summary,
    readiness?.mobile_current_pwa_field_trial_browser_proof_copy,
    diagnostics?.mobile_current_pwa_field_trial_browser_proof,
    diagnostics?.mobile_current_pwa_field_trial_browser_proof_summary,
    diagnostics?.mobile_current_pwa_field_trial_browser_proof_copy,
    diagnosticsReadiness.mobile_current_pwa_field_trial_browser_proof,
    diagnosticsReadiness.mobile_current_pwa_field_trial_browser_proof_summary,
    diagnosticsReadiness.mobile_current_pwa_field_trial_browser_proof_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function mobileRealDeviceFieldTrialAcceptanceSessionCandidate(status, readiness, diagnostics) {
  // acceptance session 优先消费显式字段；缺失时再按 tech-plan 的上游 proof 层级派生。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_real_device_field_trial_acceptance_session,
    status?.mobile_real_device_field_trial_acceptance_session_summary,
    status?.mobile_real_device_field_trial_acceptance_session_copy,
    readiness?.mobile_real_device_field_trial_acceptance_session,
    readiness?.mobile_real_device_field_trial_acceptance_session_summary,
    readiness?.mobile_real_device_field_trial_acceptance_session_copy,
    diagnostics?.mobile_real_device_field_trial_acceptance_session,
    diagnostics?.mobile_real_device_field_trial_acceptance_session_summary,
    diagnostics?.mobile_real_device_field_trial_acceptance_session_copy,
    diagnosticsReadiness.mobile_real_device_field_trial_acceptance_session,
    diagnosticsReadiness.mobile_real_device_field_trial_acceptance_session_summary,
    diagnosticsReadiness.mobile_real_device_field_trial_acceptance_session_copy,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function currentDisplayMode() {
  // display-mode 只能说明当前浏览器上下文，不能证明 production app 或真实 install prompt。
  const modes = ["standalone", "fullscreen", "minimal-ui", "browser"];
  return modes.find((mode) => window.matchMedia && window.matchMedia(`(display-mode: ${mode})`).matches) || "browser";
}

function safeBrowserFamilySummary() {
  // 只输出浏览器族摘要，避免完整 UA、版本长串或能力对象进入复制包。
  const brands = navigator.userAgentData?.brands || [];
  const brandText = brands.map((brand) => brand.brand).join(" ").toLowerCase();
  const ua = (navigator.userAgent || "").toLowerCase();
  const source = `${brandText} ${ua}`;
  if (source.includes("edg")) {
    return "edge_family";
  }
  if (source.includes("firefox")) {
    return "firefox_family";
  }
  if (source.includes("crios") || source.includes("chrome") || source.includes("chromium")) {
    return "chromium_family";
  }
  if (source.includes("safari")) {
    return "safari_family";
  }
  return "unknown_browser_family";
}

function pwaEventRuntimeMetadata() {
  // 运行时元数据只保留平台/浏览器概要和 display-mode，不保存 raw event 或完整 UA。
  return {
    client_timestamp: new Date().toISOString(),
    display_mode: currentDisplayMode(),
    platform_summary: safeBundleText(navigator.userAgentData?.platform || navigator.platform, "unknown_platform"),
    browser_summary: safeBrowserFamilySummary(),
  };
}

function safeEntryUrlSummary() {
  // 入口摘要只保留 origin/path，去掉 query/hash 和 file 路径，避免 token 或本机路径进入交接包。
  if (!window.location) {
    return "当前手机入口 URL 未提供。";
  }
  if (!window.location.origin || window.location.origin === "null" || window.location.protocol === "file:") {
    return "local_static_entry/mobile_web";
  }
  return `${window.location.origin}${window.location.pathname}`;
}

function collectLocalDeviceEvidence() {
  // 本地采集只保留浏览器安全元数据，绝不复制 robot/raw 调试字段。
  const coarsePointer = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  const touchCapable = navigator.maxTouchPoints > 0 || "ontouchstart" in window;
  const serviceWorkerState = "serviceWorker" in navigator
    ? (navigator.serviceWorker.controller ? "controller_present" : "registered_or_pending")
    : "not_supported";
  return {
    viewport: {
      width_css_px: window.innerWidth || document.documentElement.clientWidth || 0,
      height_css_px: window.innerHeight || document.documentElement.clientHeight || 0,
      device_pixel_ratio: window.devicePixelRatio || 1,
      orientation: window.screen?.orientation?.type || "unknown",
    },
    touch_target: {
      min_target_css_px: 48,
      coarse_pointer: coarsePointer,
      max_touch_points: navigator.maxTouchPoints || 0,
      touch_capable: touchCapable,
    },
    display_mode: currentDisplayMode(),
    pwa: {
      manifest_link_present: Boolean(document.querySelector('link[rel="manifest"]')),
      install_prompt_status: "not_proven",
      production_app_ready: false,
    },
    service_worker: {
      status: serviceWorkerState,
      offline_shell_status: "static_shell_only",
      dynamic_control_cache_policy: "no_store_required",
    },
    client_timestamp: new Date().toISOString(),
  };
}

function normalizeDeviceEvidence(value, localEvidence) {
  // 后端/诊断字段和本地采集字段都要经过白名单，复制包不能带原始 JSON。
  const notProven = notProvenList(value?.not_proven);
  return {
    schema: DEVICE_EVIDENCE_SCHEMA,
    schema_version: 1,
    capture_summary_schema: "trashbot.mobile_device_evidence_capture_summary.v1",
    package_schema: DEVICE_EVIDENCE_PACKAGE_SCHEMA,
    viewport: {
      width_css_px: Number(value?.viewport?.width_css_px || localEvidence.viewport.width_css_px || 0),
      height_css_px: Number(value?.viewport?.height_css_px || localEvidence.viewport.height_css_px || 0),
      device_pixel_ratio: Number(value?.viewport?.device_pixel_ratio || localEvidence.viewport.device_pixel_ratio || 1),
      orientation: safeBundleText(value?.viewport?.orientation || localEvidence.viewport.orientation, "unknown"),
    },
    touch_target: {
      min_target_css_px: Number(value?.touch_target?.min_target_css_px || localEvidence.touch_target.min_target_css_px),
      coarse_pointer: value?.touch_target?.coarse_pointer === true || localEvidence.touch_target.coarse_pointer === true,
      max_touch_points: Number(value?.touch_target?.max_touch_points || localEvidence.touch_target.max_touch_points || 0),
      touch_capable: value?.touch_target?.touch_capable === true || localEvidence.touch_target.touch_capable === true,
    },
    display_mode: safeBundleText(value?.display_mode || localEvidence.display_mode, "browser"),
    pwa: {
      manifest_link_present: value?.pwa?.manifest_link_present === true || localEvidence.pwa.manifest_link_present === true,
      install_prompt_status: safeBundleText(value?.pwa?.install_prompt_status, localEvidence.pwa.install_prompt_status),
      production_app_ready: value?.pwa?.production_app_ready === true,
    },
    service_worker: {
      status: safeBundleText(value?.service_worker?.status || localEvidence.service_worker.status, "not_supported"),
      offline_shell_status: safeBundleText(
        value?.service_worker?.offline_shell_status || localEvidence.service_worker.offline_shell_status,
        "static_shell_only",
      ),
      dynamic_control_cache_policy: "no_store_required",
    },
    client_timestamp: safeBundleText(value?.client_timestamp || localEvidence.client_timestamp, localEvidence.client_timestamp),
    overall_status: safeBundleText(value?.overall_status || value?.status, "blocked"),
    safe_phone_copy: safeBundleText(
      value?.safe_phone_copy || value?.safe_summary,
      "手机设备证据包只记录 phone-safe 浏览器元数据；真实手机/browser、production app 和真实 PWA install prompt 仍未证明。",
    ),
    recovery_hint: safeBundleText(
      value?.recovery_hint || value?.retry_hint,
      "把证据包交给支持人员复现；主操作仍由 readiness 和 command_safety fail closed。",
    ),
    ack_semantics: safeBundleText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeBundleText(value?.evidence_boundary, MOBILE_DEVICE_EVIDENCE_BOUNDARY),
    not_proven: notProven,
  };
}

function mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics) {
  const localEvidence = collectLocalDeviceEvidence();
  const provided = mobileDeviceEvidenceCandidate(status, readiness, diagnostics);
  return normalizeDeviceEvidence(provided || {}, localEvidence);
}

function observationChecklistFromSession(value, deviceEvidence) {
  // 清单是验收会议的执行提示，不是自动验收；缺字段时根据 evidence package 生成保守观察项。
  const provided = Array.isArray(value?.observation_checklist) ? value.observation_checklist : [];
  const base = provided.length ? provided : [
    { item: "device_browser", status: "not_proven", safe_phone_copy: "在真实 iPhone/Android 浏览器打开当前入口。" },
    { item: "pwa_install_prompt", status: "not_proven", safe_phone_copy: "观察是否出现真实 PWA install prompt；未出现时记录 not_proven。" },
    { item: "offline_shell", status: deviceEvidence.service_worker.offline_shell_status, safe_phone_copy: "断网后只允许静态离线壳，不缓存或重放控制请求。" },
    { item: "touch_target", status: deviceEvidence.touch_target.touch_capable ? "observed_metadata" : "not_proven", safe_phone_copy: "检查主要按钮触控目标不小于 44 CSS px。" },
    { item: "viewport", status: "observed_metadata", safe_phone_copy: `${deviceEvidence.viewport.width_css_px}x${deviceEvidence.viewport.height_css_px} CSS viewport。` },
  ];
  return base.slice(0, 8).map((step) => ({
    item: safeBundleText(step?.item || step?.id || step?.label, "handoff_step"),
    status: safeBundleText(step?.status || step?.state, "not_proven"),
    safe_phone_copy: safeBundleText(step?.safe_phone_copy || step?.copy || step?.summary, "等待真实手机验收记录。"),
  }));
}

function normalizeDeviceHandoffSession(value, deviceEvidence, acceptance, browserBundle) {
  // 交接包复用设备证据采集包，但只复制白名单和边界；不能升格为真实设备验收通过。
  const notProven = notProvenList(value?.not_proven || deviceEvidence.not_proven || browserBundle.not_proven);
  const sessionId = safeBundleText(value?.session_id || value?.handoff_session_id, stableHandoffClientReference);
  const clientReference = safeBundleText(value?.client_reference, stableHandoffClientReference);
  return {
    schema: DEVICE_HANDOFF_SESSION_SCHEMA,
    schema_version: 1,
    package_schema: DEVICE_HANDOFF_PACKAGE_SCHEMA,
    session_id: sessionId,
    client_reference: clientReference,
    entry_url: safeBundleText(value?.entry_url || value?.entry_url_summary || safeEntryUrlSummary(), safeEntryUrlSummary()),
    safe_entry_summary: safeBundleText(
      value?.safe_entry_summary || value?.safe_entry_copy,
      "使用当前手机入口 URL 开始真实设备验收；复制包不包含 token、raw robot 字段或本地证据文件。",
    ),
    overall_status: safeBundleText(value?.overall_status || value?.status, "blocked"),
    real_device_observed: value?.real_device_observed === true,
    production_app_ready: value?.production_app_ready === true || acceptance.production_app_ready === true,
    pwa_install_prompt_observed: value?.pwa_install_prompt_observed === true,
    safe_to_control: value?.safe_to_control === true,
    observation_checklist: observationChecklistFromSession(value, deviceEvidence),
    evidence_capture_reference: {
      schema: deviceEvidence.schema,
      package_schema: DEVICE_EVIDENCE_PACKAGE_SCHEMA,
      evidence_boundary: deviceEvidence.evidence_boundary,
      overall_status: deviceEvidence.overall_status,
      client_timestamp: deviceEvidence.client_timestamp,
    },
    device_observations: {
      viewport: deviceEvidence.viewport,
      touch_target: deviceEvidence.touch_target,
      display_mode: deviceEvidence.display_mode,
      pwa: deviceEvidence.pwa,
      service_worker: deviceEvidence.service_worker,
    },
    browser_acceptance_reference: {
      schema: browserBundle.schema,
      overall_status: browserBundle.overall_status,
      production_app_ready: browserBundle.production_app_ready,
      safe_to_control: browserBundle.safe_to_control,
      evidence_boundary: browserBundle.evidence_boundary,
    },
    safe_phone_copy: safeBundleText(
      value?.safe_phone_copy || value?.safe_summary,
      "真实手机验收交接会话 blocked-by-design：当前只整理入口、session、设备观察项和 evidence capture 引用，不证明真实设备验收通过。",
    ),
    recovery_hint: safeBundleText(
      value?.recovery_hint || value?.retry_hint,
      "请在真实 iPhone/Android 浏览器或 production app 入口完成会话记录；缺真实 PWA install prompt 时主操作继续 fail closed。",
    ),
    ack_semantics: safeBundleText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeBundleText(value?.evidence_boundary, MOBILE_DEVICE_HANDOFF_SESSION_BOUNDARY),
    not_proven: notProven,
  };
}

function mobileDeviceHandoffSessionFromStatus(status, readiness, diagnostics) {
  const evidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const acceptance = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, diagnostics);
  const browserBundle = mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics);
  const provided = mobileDeviceHandoffSessionCandidate(status, readiness, diagnostics) || {};
  return normalizeDeviceHandoffSession(provided, evidence, acceptance, browserBundle);
}

function normalizePwaInstallPromptEvidence(value, localEvidence, handoffSession, browserBundle) {
  // 该包只记录 install prompt 验收证据边界；不能把 handoff/browser bundle 升格成真实 prompt 通过。
  const pwa = value?.pwa && typeof value.pwa === "object" ? value.pwa : {};
  const serviceWorker = value?.service_worker && typeof value.service_worker === "object" ? value.service_worker : {};
  return {
    schema: PWA_INSTALL_PROMPT_SCHEMA,
    schema_version: 1,
    summary_schema: PWA_INSTALL_PROMPT_SUMMARY_SCHEMA,
    package_schema: PWA_INSTALL_PROMPT_PACKAGE_SCHEMA,
    source: safeBundleText(value?.source, "mobile_web"),
    overall_status: safeBundleText(value?.overall_status || value?.status, "blocked"),
    install_prompt_capture_status: safeBundleText(
      value?.install_prompt_capture_status || value?.capture_status || pwa.install_prompt_status,
      "not_proven",
    ),
    install_prompt_user_outcome: safeBundleText(
      value?.install_prompt_user_outcome || value?.user_outcome || value?.prompt_outcome,
      "not_proven",
    ),
    display_mode: safeBundleText(value?.display_mode || localEvidence.display_mode, "browser"),
    installability_status: safeBundleText(value?.installability_status || value?.installability, "not_proven"),
    offline_shell_status: safeBundleText(
      value?.offline_shell_status || serviceWorker.offline_shell_status || localEvidence.service_worker.offline_shell_status,
      "static_shell_only",
    ),
    manifest_present: value?.manifest_present === true ||
      value?.manifest_link_present === true ||
      pwa.manifest_link_present === true ||
      localEvidence.pwa.manifest_link_present === true,
    service_worker_status: safeBundleText(
      value?.service_worker_status || serviceWorker.status || localEvidence.service_worker.status,
      "registered_or_pending",
    ),
    production_app_ready: value?.production_app_ready === true,
    safe_to_control: value?.safe_to_control === true,
    linked_handoff_session: {
      schema: handoffSession.schema,
      session_id: handoffSession.session_id,
      overall_status: handoffSession.overall_status,
      evidence_boundary: handoffSession.evidence_boundary,
      pwa_install_prompt_observed: handoffSession.pwa_install_prompt_observed,
    },
    linked_device_evidence_capture: {
      schema: DEVICE_EVIDENCE_SCHEMA,
      evidence_boundary: localEvidence.evidence_boundary,
      display_mode: localEvidence.display_mode,
      install_prompt_status: localEvidence.pwa.install_prompt_status,
    },
    linked_browser_acceptance_bundle: {
      schema: browserBundle.schema,
      overall_status: browserBundle.overall_status,
      pwa_install_prompt: browserBundle.pwa_install_prompt,
      evidence_boundary: browserBundle.evidence_boundary,
    },
    safe_phone_copy: safeBundleText(
      value?.safe_phone_copy || value?.safe_summary,
      "PWA 安装提示证据 blocked-by-design：当前只整理 phone-safe install prompt capture metadata，不证明真实 PWA install prompt 通过。",
    ),
    recovery_hint: safeBundleText(
      value?.recovery_hint || value?.retry_hint,
      "请在真实 iPhone/Android 浏览器或 production app 入口触发并记录真实 install prompt；缺失时主操作继续 fail closed。",
    ),
    ack_semantics: safeBundleText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeBundleText(value?.evidence_boundary, MOBILE_PWA_INSTALL_PROMPT_BOUNDARY),
    not_proven: notProvenList(value?.not_proven),
  };
}

function defaultPwaInstallPromptEventState() {
  // 缺少事件时必须生成 blocked-by-design 包，不能把浏览器未触发误写成安装准备完成。
  const metadata = pwaEventRuntimeMetadata();
  return {
    source: "mobile_web_runtime",
    beforeinstallprompt_status: "missing",
    beforeinstallprompt_client_timestamp: metadata.client_timestamp,
    display_mode: metadata.display_mode,
    platform_summary: metadata.platform_summary,
    browser_summary: metadata.browser_summary,
    prompt_availability: "blocked_or_missing_browser_event",
    user_choice_outcome: "not_proven",
    user_choice_client_timestamp: "not_proven",
    appinstalled_observed: false,
    appinstalled_client_timestamp: "not_proven",
    safe_phone_copy: "PWA 安装提示事件捕获 blocked-by-design：当前浏览器没有触发 beforeinstallprompt、userChoice 或 appinstalled 事件。",
    recovery_hint: "请在真实浏览器环境继续观察事件；缺事件时 Start、Confirm、Cancel 继续 fail closed。",
  };
}

function normalizePwaInstallPromptEventCapture(value) {
  // event capture copy 是 whitelist-only：不复制 deferred prompt、raw Promise、raw event、完整 UA 或内部技术字段。
  const runtime = pwaInstallPromptEventState || defaultPwaInstallPromptEventState();
  const source = value && Object.keys(value).length > 0 ? value : runtime;
  const beforeStatus = safeBundleText(
    source.beforeinstallprompt_status || source.install_prompt_event_status || source.capture_status,
    runtime.beforeinstallprompt_status || "missing",
  );
  const userOutcome = safeBundleText(
    source.user_choice_outcome || source.install_prompt_user_outcome || source.prompt_outcome,
    runtime.user_choice_outcome || "not_proven",
  );
  const appinstalledObserved = source.appinstalled_observed === true || runtime.appinstalled_observed === true;
  return {
    schema: PWA_INSTALL_PROMPT_EVENT_CAPTURE_SCHEMA,
    schema_version: 1,
    summary_schema: PWA_INSTALL_PROMPT_EVENT_CAPTURE_SUMMARY_SCHEMA,
    copy_schema: PWA_INSTALL_PROMPT_EVENT_CAPTURE_COPY_SCHEMA,
    source: safeBundleText(source.source, "mobile_web_runtime"),
    overall_status: beforeStatus === "observed" || appinstalledObserved ? "observed_not_proven" : "blocked",
    beforeinstallprompt_status: beforeStatus,
    beforeinstallprompt_client_timestamp: safeBundleText(
      source.beforeinstallprompt_client_timestamp || source.client_timestamp,
      runtime.beforeinstallprompt_client_timestamp,
    ),
    display_mode: safeBundleText(source.display_mode, runtime.display_mode || "browser"),
    platform_summary: safeBundleText(source.platform_summary, runtime.platform_summary || "unknown_platform"),
    browser_summary: safeBundleText(source.browser_summary, runtime.browser_summary || "unknown_browser_family"),
    prompt_availability: safeBundleText(source.prompt_availability, runtime.prompt_availability),
    user_choice_outcome: ["accepted", "dismissed", "unknown", "not_proven"].includes(userOutcome)
      ? userOutcome
      : "unknown",
    user_choice_client_timestamp: safeBundleText(
      source.user_choice_client_timestamp || source.choice_client_timestamp,
      runtime.user_choice_client_timestamp || "not_proven",
    ),
    appinstalled_observed: appinstalledObserved,
    appinstalled_client_timestamp: safeBundleText(
      source.appinstalled_client_timestamp || source.installed_client_timestamp,
      runtime.appinstalled_client_timestamp || "not_proven",
    ),
    production_app_ready: false,
    safe_to_control: false,
    safe_phone_copy: safeBundleText(
      source.safe_phone_copy || source.safe_summary,
      "PWA install prompt event capture 只记录浏览器事件观察结果；not_proven 时不是安装成功或 production app readiness。",
    ),
    recovery_hint: safeBundleText(
      source.recovery_hint || source.retry_hint,
      "缺真实手机/browser 事件材料时继续按 blocked-by-design 处理，主操作保持关闭。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_PWA_INSTALL_PROMPT_EVENT_CAPTURE_BOUNDARY,
    not_proven: notProvenList(source.not_proven),
  };
}

function mobilePwaInstallPromptEvidenceFromStatus(status, readiness, diagnostics) {
  const localEvidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const handoffSession = mobileDeviceHandoffSessionFromStatus(status, readiness, diagnostics);
  const browserBundle = mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics);
  const provided = mobilePwaInstallPromptEvidenceCandidate(status, readiness, diagnostics) || {};
  return normalizePwaInstallPromptEvidence(provided, localEvidence, handoffSession, browserBundle);
}

function mobilePwaInstallPromptEventCaptureFromStatus(status, readiness, diagnostics) {
  const provided = mobilePwaInstallPromptEventCaptureCandidate(status, readiness, diagnostics) || {};
  return normalizePwaInstallPromptEventCapture(provided);
}

function exportStatusFromAppinstalled(value) {
  // 导出合同只保留枚举式安装状态，避免把 raw browser event 或 Promise 泄漏到材料包。
  if (value?.appinstalled_status) {
    return safeBundleText(value.appinstalled_status, "not_proven");
  }
  if (value?.appinstalled_observed === true) {
    return "observed_not_proven";
  }
  return "not_proven";
}

function normalizePwaInstallPromptEvidenceExport(value, sourceLayer, eventCapture, pwaEvidence, deviceEvidence, handoffSession, browserBundle) {
  // export copy 是现场验收材料最小白名单；即使上游更丰富，也只复制 support/acceptance metadata。
  const source = value && typeof value === "object" ? value : {};
  const notProven = notProvenList(
    source.not_proven ||
      eventCapture.not_proven ||
      pwaEvidence.not_proven ||
      handoffSession.not_proven ||
      deviceEvidence.not_proven ||
      browserBundle.not_proven,
  );
  const installPromptCaptureStatus = safeBundleText(
    source.install_prompt_capture_status ||
      source.beforeinstallprompt_status ||
      source.capture_status ||
      eventCapture.beforeinstallprompt_status ||
      pwaEvidence.install_prompt_capture_status ||
      deviceEvidence.pwa.install_prompt_status ||
      browserBundle.pwa_install_prompt,
    "not_proven",
  );
  const installPromptUserChoice = safeBundleText(
    source.install_prompt_user_choice ||
      source.install_prompt_user_outcome ||
      source.user_choice_outcome ||
      source.user_outcome ||
      eventCapture.user_choice_outcome ||
      pwaEvidence.install_prompt_user_outcome,
    "not_proven",
  );
  const clientTimestamp = safeBundleText(
    source.client_timestamp ||
      source.beforeinstallprompt_client_timestamp ||
      eventCapture.beforeinstallprompt_client_timestamp ||
      pwaEvidence.client_timestamp ||
      deviceEvidence.client_timestamp,
    new Date().toISOString(),
  );
  return {
    schema: PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_SCHEMA,
    schema_version: 1,
    summary_schema: PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_SUMMARY_SCHEMA,
    copy_schema: PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_COPY_SCHEMA,
    source: "mobile_web",
    source_layer: safeBundleText(source.source_layer || sourceLayer, "blocked_by_design"),
    overall_status: safeBundleText(source.overall_status || source.status, eventCapture.overall_status || "blocked"),
    install_prompt_capture_status: installPromptCaptureStatus,
    install_prompt_user_choice: ["accepted", "dismissed", "unknown", "not_proven"].includes(installPromptUserChoice)
      ? installPromptUserChoice
      : "unknown",
    appinstalled_status: exportStatusFromAppinstalled(source.appinstalled_status ? source : eventCapture),
    display_mode: safeBundleText(source.display_mode || eventCapture.display_mode || pwaEvidence.display_mode, "browser"),
    manifest_present: source.manifest_present === true || pwaEvidence.manifest_present === true ||
      deviceEvidence.pwa.manifest_link_present === true,
    service_worker_status: safeBundleText(
      source.service_worker_status || pwaEvidence.service_worker_status || deviceEvidence.service_worker.status,
      "registered_or_pending",
    ),
    client_reference: safeBundleText(source.client_reference, stablePwaInstallPromptExportReference),
    client_timestamp: clientTimestamp,
    safe_to_control: false,
    safe_phone_copy: safeBundleText(
      source.safe_phone_copy || source.safe_summary,
      "PWA install prompt evidence export 只导出 whitelist-only phone-safe 现场验收 metadata；不证明真实安装、production app、HIL 或 delivery success。",
    ),
    recovery_hint: safeBundleText(
      source.recovery_hint || source.retry_hint,
      "把导出包交给支持人员复核真实手机/browser 材料；Start、Confirm、Cancel 继续 fail closed。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_BOUNDARY,
    not_proven: notProven,
  };
}

function mobilePwaInstallPromptEvidenceExportFromStatus(status, readiness, diagnostics) {
  // 输入优先级按 sprint 合同固定：显式 export -> event capture -> 旧 evidence/handoff/device/browser -> blocked。
  const explicitExport = mobilePwaInstallPromptEvidenceExportCandidate(status, readiness, diagnostics);
  const explicitEventCapture = mobilePwaInstallPromptEventCaptureCandidate(status, readiness, diagnostics);
  const explicitEvidence = mobilePwaInstallPromptEvidenceCandidate(status, readiness, diagnostics);
  const explicitHandoff = mobileDeviceHandoffSessionCandidate(status, readiness, diagnostics);
  const explicitDevice = mobileDeviceEvidenceCandidate(status, readiness, diagnostics);
  const explicitBrowser = mobileBrowserAcceptanceBundleCandidate(status, readiness, diagnostics);
  const eventCapture = mobilePwaInstallPromptEventCaptureFromStatus(status, readiness, diagnostics);
  const pwaEvidence = mobilePwaInstallPromptEvidenceFromStatus(status, readiness, diagnostics);
  const deviceEvidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const handoffSession = mobileDeviceHandoffSessionFromStatus(status, readiness, diagnostics);
  const browserBundle = mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics);
  if (explicitExport) {
    return normalizePwaInstallPromptEvidenceExport(
      explicitExport,
      "mobile_pwa_install_prompt_evidence_export",
      eventCapture,
      pwaEvidence,
      deviceEvidence,
      handoffSession,
      browserBundle,
    );
  }
  if (explicitEventCapture) {
    return normalizePwaInstallPromptEvidenceExport(
      explicitEventCapture,
      "mobile_pwa_install_prompt_event_capture",
      eventCapture,
      pwaEvidence,
      deviceEvidence,
      handoffSession,
      browserBundle,
    );
  }
  if (explicitEvidence || explicitHandoff || explicitDevice || explicitBrowser) {
    return normalizePwaInstallPromptEvidenceExport(
      explicitEvidence || explicitHandoff || explicitDevice || explicitBrowser,
      explicitEvidence ? "mobile_pwa_install_prompt_evidence" : "derived_support_metadata",
      eventCapture,
      pwaEvidence,
      deviceEvidence,
      handoffSession,
      browserBundle,
    );
  }
  return normalizePwaInstallPromptEvidenceExport(
    {},
    "blocked_by_design",
    eventCapture,
    pwaEvidence,
    deviceEvidence,
    handoffSession,
    browserBundle,
  );
}

function normalizeRealDeviceEvidenceIntake(value, localEvidence, pwaEvidence) {
  // intake 包只输出 redacted phone-safe summary；即使用户粘贴完整 JSON，也不复制 raw 输入。
  const device = value?.device && typeof value.device === "object" ? value.device : {};
  const browser = value?.browser && typeof value.browser === "object" ? value.browser : {};
  const viewport = browser.viewport_css && typeof browser.viewport_css === "object" ? browser.viewport_css : {};
  const pwa = value?.pwa && typeof value.pwa === "object" ? value.pwa : {};
  const productionApp = value?.production_app && typeof value.production_app === "object" ? value.production_app : {};
  const evidence = value?.evidence && typeof value.evidence === "object" ? value.evidence : {};
  const browserSummary = `${safeRealDeviceEvidenceText(browser.family, "unknown")} ${safeRealDeviceEvidenceText(browser.version_summary, "not_provided")}`.trim();
  return {
    schema: REAL_DEVICE_EVIDENCE_INTAKE_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_EVIDENCE_INTAKE_SUMMARY_SCHEMA,
    package_schema: REAL_DEVICE_EVIDENCE_PACKAGE_SCHEMA,
    source: safeRealDeviceEvidenceText(value?.source, importedRealDeviceEvidence ? "mobile_web_import" : "mobile_web_local_metadata"),
    overall_status: safeRealDeviceEvidenceText(value?.overall_status || value?.status, "blocked"),
    device: {
      platform: safeRealDeviceEvidenceText(device.platform || navigator.platform, "unknown"),
      model_summary: safeRealDeviceEvidenceText(device.model_summary, "not_provided"),
      os_summary: safeRealDeviceEvidenceText(device.os_summary, "not_provided"),
    },
    browser: {
      family: safeRealDeviceEvidenceText(browser.family, "unknown"),
      version_summary: safeRealDeviceEvidenceText(browser.version_summary || browserSummary, "not_provided"),
      viewport_css: {
        width: Number(viewport.width || viewport.width_css_px || localEvidence.viewport.width_css_px || 0),
        height: Number(viewport.height || viewport.height_css_px || localEvidence.viewport.height_css_px || 0),
      },
      device_pixel_ratio: Number(browser.device_pixel_ratio || localEvidence.viewport.device_pixel_ratio || 1),
      orientation: safeRealDeviceEvidenceText(browser.orientation || localEvidence.viewport.orientation, "unknown"),
      touch_target_summary: safeRealDeviceEvidenceText(browser.touch_target_summary, "not_proven"),
    },
    pwa: {
      display_mode: safeRealDeviceEvidenceText(pwa.display_mode || localEvidence.display_mode, "browser"),
      install_prompt_status: safeRealDeviceEvidenceText(
        pwa.install_prompt_status || pwaEvidence.install_prompt_capture_status,
        "not_proven",
      ),
      install_prompt_user_choice: safeRealDeviceEvidenceText(
        pwa.install_prompt_user_choice || pwaEvidence.install_prompt_user_outcome,
        "not_provided",
      ),
      manifest_status: safeRealDeviceEvidenceText(pwa.manifest_status, localEvidence.pwa.manifest_link_present ? "present" : "unknown"),
      service_worker_status: safeRealDeviceEvidenceText(pwa.service_worker_status || localEvidence.service_worker.status, "unknown"),
      offline_shell_status: safeRealDeviceEvidenceText(pwa.offline_shell_status || localEvidence.service_worker.offline_shell_status, "unknown"),
    },
    production_app: {
      ready: productionApp.ready === true || value?.production_app_ready === true,
      entry_url_summary: safeRealDeviceEvidenceText(productionApp.entry_url_summary || value?.entry_url_summary, "not_provided"),
      release_summary: safeRealDeviceEvidenceText(productionApp.release_summary, "not_provided"),
    },
    evidence: {
      screenshot_summary: safeRealDeviceEvidenceText(evidence.screenshot_summary || value?.screenshot_summary, "not_provided"),
      url_summary: safeRealDeviceEvidenceText(evidence.url_summary || value?.url_summary || safeEntryUrlSummary(), "not_provided"),
      observer_note: safeRealDeviceEvidenceText(evidence.observer_note || value?.observer_note, "not_provided"),
      redaction_status: safeRealDeviceEvidenceText(evidence.redaction_status || value?.redaction_status, "passed"),
    },
    safe_to_control: false,
    not_proven: notProvenList(value?.not_proven),
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "真实设备验收材料 intake blocked-by-design：当前只生成 redacted phone-safe package，不证明真实手机设备、production app 或 PWA install prompt 通过。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "请导入真实 iPhone/Android 或 production app 的脱敏摘要；本 gate 不启用 Start、Confirm 或 Cancel。",
    ),
    ack_semantics: safeRealDeviceEvidenceText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_EVIDENCE_INTAKE_BOUNDARY),
  };
}

function mobileRealDeviceEvidencePackageFromStatus(status, readiness, diagnostics) {
  const localEvidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const pwaEvidence = mobilePwaInstallPromptEvidenceFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceEvidenceIntakeCandidate(status, readiness, diagnostics) || {};
  return normalizeRealDeviceEvidenceIntake(provided, localEvidence, pwaEvidence);
}

function realDeviceDecisionFromEvidence(packagePayload) {
  // 决策只判断材料是否可进入人工复核，不声明真实设备验收或 production app 已通过。
  const blockers = realDeviceDecisionBlockers(packagePayload);
  const redaction = String(packagePayload?.evidence?.redaction_status || packagePayload?.redaction_status || "missing").toLowerCase();
  if (!["passed", "redacted", "phone_safe"].includes(redaction)) {
    return "rejected_unsafe_or_unredacted";
  }
  return blockers.length ? "blocked_missing_evidence" : "accepted_for_review";
}

function realDeviceDecisionBlockers(packagePayload) {
  // blocker list 逐项说明缺口，避免把下一步泛化建议误写成验收事实。
  const redaction = String(packagePayload?.evidence?.redaction_status || packagePayload?.redaction_status || "missing").toLowerCase();
  const blockers = [];
  if (!["passed", "redacted", "phone_safe"].includes(redaction)) {
    blockers.push("redaction_status 不是 passed/redacted/phone_safe。");
  }
  if (packagePayload?.production_app?.ready !== true) {
    blockers.push("缺少 production app readiness 证据。");
  }
  if (String(packagePayload?.pwa?.install_prompt_status || "").toLowerCase().includes("not_proven")) {
    blockers.push("缺少真实 PWA install prompt capture。");
  }
  if (String(packagePayload?.pwa?.install_prompt_user_choice || "").toLowerCase().includes("not_provided")) {
    blockers.push("缺少真实 install prompt user choice。");
  }
  if (!packagePayload?.evidence?.screenshot_summary || packagePayload.evidence.screenshot_summary === "not_provided") {
    blockers.push("缺少真实手机截图摘要。");
  }
  if (!packagePayload?.evidence?.url_summary || packagePayload.evidence.url_summary === "not_provided") {
    blockers.push("缺少 production app / HTTPS 入口 URL 摘要。");
  }
  return blockers;
}

function realDeviceDecisionCopy(decision) {
  // 三态文案用于支持同学快速分流：可复核、缺材料、或必须先脱敏重交。
  if (decision === "accepted_for_review") {
    return "真实设备验收材料已脱敏且可进入人工复核；这仍不是 production app、PWA install prompt 或真实送达通过。";
  }
  if (decision === "rejected_unsafe_or_unredacted") {
    return "真实设备验收材料被拒绝：材料未脱敏或包含不安全字段，请提交 redacted phone-safe summary。";
  }
  return "真实设备验收材料仍缺关键证据，保持 blocked_missing_evidence 和 not_proven。";
}

function realDeviceDecisionNextEvidence(packagePayload) {
  // 下一步证据清单保持 phone-safe，不要求用户提交原始截图、完整 URL 或内部日志。
  return [
    "真实 iPhone/Android device behavior 摘要",
    "production app 入口与 release summary",
    "真实 PWA install prompt capture status",
    "真实 install prompt user choice",
    "脱敏 screenshot summary",
    "脱敏 production HTTPS URL summary",
  ].filter((item) => {
    if (item.startsWith("production app") && packagePayload?.production_app?.ready === true) {
      return false;
    }
    return true;
  }).slice(0, 6);
}

function normalizeRealDeviceAcceptanceDecision(value, packagePayload) {
  // 显式决策和派生决策都只保留白名单；safe_to_control 固定为 false。
  const derivedDecision = realDeviceDecisionFromEvidence(packagePayload);
  const decision = safeRealDeviceEvidenceText(value?.decision || value?.overall_status || value?.status, derivedDecision);
  const blockerList = Array.isArray(value?.blocker_list) ? value.blocker_list : realDeviceDecisionBlockers(packagePayload);
  const nextEvidence = Array.isArray(value?.next_required_evidence) ? value.next_required_evidence : realDeviceDecisionNextEvidence(packagePayload);
  const notProven = notProvenList(value?.not_proven || packagePayload.not_proven);
  return {
    schema: REAL_DEVICE_ACCEPTANCE_DECISION_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_ACCEPTANCE_DECISION_SUMMARY_SCHEMA,
    package_schema: REAL_DEVICE_ACCEPTANCE_DECISION_PACKAGE_SCHEMA,
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "derived_from_mobile_real_device_evidence_intake"),
    decision,
    overall_status: decision,
    accepted_for_review: decision === "accepted_for_review",
    safe_to_control: false,
    blocker_list: (blockerList.length ? blockerList : ["等待人工复核后确认是否仍缺材料。"])
      .slice(0, 8)
      .map((item) => safeRealDeviceEvidenceText(item, "blocked_missing_evidence")),
    next_required_evidence: nextEvidence
      .slice(0, 8)
      .map((item) => safeRealDeviceEvidenceText(item, "真实设备验收材料")),
    redaction_status: safeRealDeviceEvidenceText(
      value?.redaction_status || packagePayload?.evidence?.redaction_status || packagePayload?.redaction_status,
      "missing",
    ),
    safe_phone_copy: safeRealDeviceEvidenceText(value?.safe_phone_copy || value?.safe_summary, realDeviceDecisionCopy(decision)),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按 next_required_evidence 补齐脱敏材料；ACK、receipt 和 evidence package 仍不是 delivery success。",
    ),
    ack_semantics: safeRealDeviceEvidenceText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_ACCEPTANCE_DECISION_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || packagePayload.evidence_boundary,
      MOBILE_REAL_DEVICE_EVIDENCE_INTAKE_BOUNDARY,
    ),
    linked_intake_package: {
      schema: REAL_DEVICE_EVIDENCE_PACKAGE_SCHEMA,
      intake_schema: packagePayload.schema,
      summary_schema: packagePayload.summary_schema,
      evidence_boundary: packagePayload.evidence_boundary,
      redaction_status: packagePayload?.evidence?.redaction_status || packagePayload?.redaction_status || "missing",
      safe_to_control: false,
    },
    not_proven: notProven,
  };
}

function mobileRealDeviceAcceptanceDecisionFromStatus(status, readiness, diagnostics) {
  const packagePayload = mobileRealDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceAcceptanceDecisionCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceAcceptanceDecision(provided, packagePayload);
}

function defaultReviewChecklist(decisionPayload) {
  // reviewer checklist 明确人工复核要看的材料，不能把 decision package 当自动验收结果。
  const blockerCount = Array.isArray(decisionPayload.blocker_list) ? decisionPayload.blocker_list.length : 0;
  return [
    {
      item: "decision status",
      status: decisionPayload.decision,
      safe_phone_copy: "确认 acceptance decision 是否仅为 accepted_for_review、blocked_missing_evidence 或 rejected_unsafe_or_unredacted。",
    },
    {
      item: "redaction",
      status: decisionPayload.redaction_status,
      safe_phone_copy: "确认复制包未包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、/cmd_vel、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact 或 raw robot response。",
    },
    {
      item: "evidence blocker",
      status: blockerCount ? "blocked_missing_evidence" : "ready_for_manual_review",
      safe_phone_copy: blockerCount ? decisionPayload.blocker_list.join("；") : "没有自动 blocker；仍需人工确认真实设备材料。",
    },
    {
      item: "not_proven",
      status: "must_remain_visible",
      safe_phone_copy: "真实设备、production app、真实 PWA install prompt、O5 外部 proof、HIL 和 delivery success 未证明时必须保留。",
    },
  ];
}

function normalizeReviewerChecklist(value, decisionPayload) {
  // checklist 可以来自后端，但每项仍要经过敏感词过滤，避免复制原始评审材料。
  const provided = Array.isArray(value?.reviewer_checklist) ? value.reviewer_checklist : defaultReviewChecklist(decisionPayload);
  return provided.slice(0, 8).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.label, "reviewer checklist"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "not_proven"),
    safe_phone_copy: safeRealDeviceEvidenceText(
      step?.safe_phone_copy || step?.copy || step?.summary,
      "等待人工评审补充 phone-safe 结论。",
    ),
  }));
}

function reviewHandoffDefaultStatus(decisionPayload) {
  // accepted_for_review 只表示可以交给人看；缺材料或未脱敏时必须停在 blocked。
  if (decisionPayload.decision === "accepted_for_review") {
    return "ready_for_manual_review";
  }
  if (decisionPayload.decision === "rejected_unsafe_or_unredacted") {
    return "blocked_redaction_required";
  }
  return "blocked_missing_evidence";
}

function normalizeRealDeviceReviewHandoff(value, decisionPayload) {
  // review handoff package 从 acceptance decision 派生，但固定 safe_to_control=false，避免评审交接变成控制授权。
  const reviewerChecklist = normalizeReviewerChecklist(value, decisionPayload);
  const blockerList = Array.isArray(value?.evidence_blocker)
    ? value.evidence_blocker
    : (Array.isArray(value?.blocker_list) ? value.blocker_list : decisionPayload.blocker_list);
  const nextEvidence = Array.isArray(value?.next_required_evidence)
    ? value.next_required_evidence
    : decisionPayload.next_required_evidence;
  const notProven = notProvenList(value?.not_proven || decisionPayload.not_proven);
  const reviewStatus = safeRealDeviceEvidenceText(
    value?.review_status || value?.overall_status || value?.status,
    reviewHandoffDefaultStatus(decisionPayload),
  );
  return {
    schema: REAL_DEVICE_REVIEW_HANDOFF_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    package_schema: REAL_DEVICE_REVIEW_HANDOFF_PACKAGE_SCHEMA,
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "derived_from_mobile_real_device_acceptance_decision"),
    handoff_session_id: safeRealDeviceEvidenceText(value?.handoff_session_id || value?.session_id, `review_handoff_${Date.now()}`),
    decision_status: safeRealDeviceEvidenceText(value?.decision_status || decisionPayload.decision, decisionPayload.decision),
    review_owner: safeRealDeviceEvidenceText(value?.review_owner || value?.owner, "review_owner_unassigned"),
    review_status: reviewStatus,
    safe_to_control: false,
    evidence_blocker: (blockerList.length ? blockerList : ["等待 reviewer 确认真实设备材料。"])
      .slice(0, 8)
      .map((item) => safeRealDeviceEvidenceText(item, "blocked_missing_evidence")),
    next_required_evidence: nextEvidence
      .slice(0, 8)
      .map((item) => safeRealDeviceEvidenceText(item, "真实设备验收材料")),
    reviewer_checklist: reviewerChecklist,
    redaction_status: safeRealDeviceEvidenceText(value?.redaction_status || decisionPayload.redaction_status, "missing"),
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "review handoff package 只表示人工评审交接；不是真实设备验收通过、真实 PWA install prompt、O5 外部 proof、HIL 或 delivery success。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "请由 review owner 按 reviewer checklist 补齐 next required evidence；ACK 仍不是 delivery success。",
    ),
    ack_semantics: safeRealDeviceEvidenceText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_REVIEW_HANDOFF_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || decisionPayload.evidence_boundary,
      MOBILE_REAL_DEVICE_ACCEPTANCE_DECISION_BOUNDARY,
    ),
    linked_acceptance_decision: {
      schema: REAL_DEVICE_ACCEPTANCE_DECISION_PACKAGE_SCHEMA,
      decision_schema: decisionPayload.schema,
      summary_schema: decisionPayload.summary_schema,
      decision: decisionPayload.decision,
      accepted_for_review: decisionPayload.accepted_for_review,
      redaction_status: decisionPayload.redaction_status,
      evidence_boundary: decisionPayload.evidence_boundary,
      source_evidence_boundary: decisionPayload.source_evidence_boundary,
      safe_to_control: false,
    },
    not_proven: notProven,
  };
}

function mobileRealDeviceReviewHandoffFromStatus(status, readiness, diagnostics) {
  const decisionPayload = mobileRealDeviceAcceptanceDecisionFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceReviewHandoffCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceReviewHandoff(provided, decisionPayload);
}

function executionChecklistFromHandoff(value, handoffPayload) {
  // execution checklist 记录人工评审是否执行，不把 reviewer checklist 自动升级为验收通过。
  const provided = Array.isArray(value?.review_execution_checklist)
    ? value.review_execution_checklist
    : (Array.isArray(value?.execution_checklist) ? value.execution_checklist : []);
  const base = provided.length ? provided : [
    {
      item: "handoff package reviewed",
      status: "not_executed",
      safe_phone_copy: "确认已查看 review handoff package 的 decision status、blocker、next evidence 和 redaction status。",
    },
    {
      item: "evidence items readiness",
      status: handoffPayload.evidence_blocker.length ? "blocked_missing_evidence" : "ready_for_manual_review",
      safe_phone_copy: handoffPayload.evidence_blocker.join("；") || "没有自动 blocker；仍需 reviewer 人工确认材料。",
    },
    {
      item: "operator notes",
      status: "required",
      safe_phone_copy: "记录 operator notes；只写 phone-safe 摘要，不粘贴原始机器人响应或完整 artifact。",
    },
    {
      item: "reviewer notes",
      status: "required",
      safe_phone_copy: "记录 reviewer notes；ACK、receipt 和 handoff package 不得写成 delivery success。",
    },
  ];
  return base.slice(0, 8).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.label, "review execution checklist"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "not_executed"),
    safe_phone_copy: safeRealDeviceEvidenceText(
      step?.safe_phone_copy || step?.copy || step?.summary,
      "等待 reviewer 执行并补充 phone-safe 记录。",
    ),
  }));
}

function reviewExecutionDefaultStatus(handoffPayload) {
  // ready_for_manual_review 只能进入待执行评审；缺材料或脱敏问题保持 blocked。
  if (handoffPayload.review_status === "ready_for_manual_review") {
    return "pending_manual_execution";
  }
  if (handoffPayload.review_status === "blocked_redaction_required") {
    return "blocked_redaction_required";
  }
  return "blocked_missing_evidence";
}

function executionEvidenceItemsReadiness(value, handoffPayload) {
  // readiness 是人工执行记录的摘要，不是实机设备、PWA prompt 或交付成功证明。
  const provided = value?.evidence_items_readiness;
  if (provided && typeof provided === "object") {
    return {
      device_materials: safeRealDeviceEvidenceText(provided.device_materials, "not_proven"),
      production_app: safeRealDeviceEvidenceText(provided.production_app, "not_proven"),
      pwa_install_prompt: safeRealDeviceEvidenceText(provided.pwa_install_prompt, "not_proven"),
      redaction: safeRealDeviceEvidenceText(provided.redaction, handoffPayload.redaction_status),
    };
  }
  const blockerText = handoffPayload.evidence_blocker.join(" ").toLowerCase();
  return {
    device_materials: /device|手机|iphone|android/.test(blockerText) ? "blocked_missing_evidence" : "ready_for_manual_review",
    production_app: /production app/.test(blockerText) ? "blocked_missing_evidence" : "ready_for_manual_review",
    pwa_install_prompt: /pwa|install prompt/.test(blockerText) ? "blocked_missing_evidence" : "ready_for_manual_review",
    redaction: handoffPayload.redaction_status,
  };
}

function normalizeRealDeviceReviewExecution(value, handoffPayload) {
  // review execution package 是人工执行记录；safe_to_control 固定 false，避免人工记录被误作控制授权。
  const executionStatus = safeRealDeviceEvidenceText(
    value?.review_result || value?.review_status || value?.overall_status || value?.status,
    reviewExecutionDefaultStatus(handoffPayload),
  );
  const blockedReason = safeRealDeviceEvidenceText(
    value?.blocked_reason || value?.blocking_reason,
    handoffPayload.evidence_blocker.join("；") || "等待 reviewer 完成人工评审执行记录。",
  );
  const nextEvidenceRequest = Array.isArray(value?.next_evidence_request)
    ? value.next_evidence_request
    : (Array.isArray(value?.next_required_evidence) ? value.next_required_evidence : handoffPayload.next_required_evidence);
  const notProven = notProvenList(value?.not_proven || handoffPayload.not_proven);
  return {
    schema: REAL_DEVICE_REVIEW_EXECUTION_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_REVIEW_EXECUTION_SUMMARY_SCHEMA,
    package_schema: REAL_DEVICE_REVIEW_EXECUTION_PACKAGE_SCHEMA,
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "derived_from_mobile_real_device_review_handoff"),
    execution_session_id: safeRealDeviceEvidenceText(
      value?.execution_session_id || value?.session_id,
      `review_execution_${Date.now()}`,
    ),
    handoff_session_id: safeRealDeviceEvidenceText(value?.handoff_session_id, handoffPayload.handoff_session_id),
    decision_status: safeRealDeviceEvidenceText(value?.decision_status, handoffPayload.decision_status),
    review_owner: safeRealDeviceEvidenceText(value?.review_owner || value?.owner, handoffPayload.review_owner),
    review_status: safeRealDeviceEvidenceText(value?.review_status, handoffPayload.review_status),
    review_result: executionStatus,
    overall_status: executionStatus,
    safe_to_control: false,
    evidence_items_readiness: executionEvidenceItemsReadiness(value, handoffPayload),
    operator_notes: safeRealDeviceEvidenceText(
      value?.operator_notes || value?.operator_note,
      "operator notes 未提供；只能记录 phone-safe 摘要。",
    ),
    reviewer_notes: safeRealDeviceEvidenceText(
      value?.reviewer_notes || value?.reviewer_note,
      "reviewer notes 未提供；等待人工执行记录。",
    ),
    blocked_reason: blockedReason,
    next_evidence_request: (nextEvidence.length ? nextEvidence : ["真实设备、production app 和真实 PWA install prompt/user choice"])
      .slice(0, 8)
      .map((item) => safeRealDeviceEvidenceText(item, "真实设备验收材料")),
    review_execution_checklist: executionChecklistFromHandoff(value, handoffPayload),
    redaction_status: safeRealDeviceEvidenceText(value?.redaction_status, handoffPayload.redaction_status),
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "review execution package 只表示人工评审执行记录；不是真实设备验收通过、真实 PWA install prompt、O5 外部 proof、HIL 或 delivery success。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按 blocked reason 和 next evidence request 补齐材料；Start、Confirm、Cancel 继续 fail closed。",
    ),
    ack_semantics: safeRealDeviceEvidenceText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_REVIEW_EXECUTION_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || handoffPayload.evidence_boundary,
      MOBILE_REAL_DEVICE_REVIEW_HANDOFF_BOUNDARY,
    ),
    linked_review_handoff: {
      schema: REAL_DEVICE_REVIEW_HANDOFF_PACKAGE_SCHEMA,
      handoff_schema: handoffPayload.schema,
      summary_schema: handoffPayload.summary_schema,
      handoff_session_id: handoffPayload.handoff_session_id,
      decision_status: handoffPayload.decision_status,
      review_owner: handoffPayload.review_owner,
      review_status: handoffPayload.review_status,
      redaction_status: handoffPayload.redaction_status,
      evidence_boundary: handoffPayload.evidence_boundary,
      source_evidence_boundary: handoffPayload.source_evidence_boundary,
      safe_to_control: false,
    },
    not_proven: notProven,
  };
}

function mobileRealDeviceReviewExecutionFromStatus(status, readiness, diagnostics) {
  const handoffPayload = mobileRealDeviceReviewHandoffFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceReviewExecutionCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceReviewExecution(provided, handoffPayload);
}

function retestMaterialReadiness(value, executionPayload) {
  // readiness 面向复测排期，不代表实机材料已经通过；默认继承 review execution 的缺口。
  const provided = value?.material_readiness || value?.evidence_items_readiness;
  const fallback = executionPayload.evidence_items_readiness || {};
  return {
    device_materials: safeRealDeviceEvidenceText(
      provided?.device_materials || provided?.device || fallback.device_materials,
      "not_proven",
    ),
    production_app: safeRealDeviceEvidenceText(
      provided?.production_app || fallback.production_app,
      "not_proven",
    ),
    pwa_install_prompt: safeRealDeviceEvidenceText(
      provided?.pwa_install_prompt || fallback.pwa_install_prompt,
      "not_proven",
    ),
    redaction: safeRealDeviceEvidenceText(
      provided?.redaction || executionPayload.redaction_status,
      "missing",
    ),
    // Objective 5 外部材料必须单独保留，避免 retest request 被误读成 O5 proof。
    objective5_external_materials: safeRealDeviceEvidenceText(
      provided?.objective5_external_materials || provided?.o5_external_materials,
      "not_proven",
    ),
  };
}

function retestMissingEvidenceList(value, executionPayload) {
  // missing evidence list 必须是可执行材料摘要，不能要求复制原始文件、完整 URL 或内部日志。
  const provided = Array.isArray(value?.missing_evidence_list)
    ? value.missing_evidence_list
    : (Array.isArray(value?.missing_evidence) ? value.missing_evidence : []);
  const source = provided.length ? provided : executionPayload.next_evidence_request;
  const fallback = [
    "真实 iPhone/Android device behavior 摘要",
    "production app 入口与 release summary",
    "真实 PWA install prompt capture status",
    "真实 install prompt user choice",
  ];
  return (source && source.length ? source : fallback)
    .slice(0, 8)
    .map((item) => safeRealDeviceEvidenceText(item, "真实设备复测材料"));
}

function retestChecklistFromExecution(value, executionPayload, missingEvidence) {
  // retest checklist 是下一轮复测执行入口，不是验收结果；每项都保留 owner/next action。
  const provided = Array.isArray(value?.retest_checklist)
    ? value.retest_checklist
    : (Array.isArray(value?.checklist) ? value.checklist : []);
  const base = provided.length ? provided : missingEvidence.map((item) => ({
    item,
    status: "missing evidence",
    owner: executionPayload.review_owner,
    next_action: `补齐 ${item} 的脱敏摘要`,
    safe_phone_copy: `复测前补齐 ${item}；保持 ACK-not-delivery 和 not_proven 边界。`,
  }));
  return base.slice(0, 8).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.label, "retest checklist"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "missing evidence"),
    owner: safeRealDeviceEvidenceText(step?.owner || step?.review_owner, executionPayload.review_owner),
    next_action: safeRealDeviceEvidenceText(
      step?.next_action || step?.next_step || step?.safe_phone_copy,
      "补齐真实设备复测材料",
    ),
    safe_phone_copy: safeRealDeviceEvidenceText(
      step?.safe_phone_copy || step?.copy || step?.summary,
      "复测请求只记录下一轮需要补齐的 phone-safe 材料。",
    ),
  }));
}

function retestRequestDefaultStatus(executionPayload) {
  // review execution 的 blocked/rejected 状态进入复测请求；pending/approved 也不能直接放行动作。
  const result = String(executionPayload.review_result || "").toLowerCase();
  if (/rejected|redaction/.test(result)) {
    return "rejected_needs_redaction";
  }
  if (/pending/.test(result)) {
    return "pending_retest_materials";
  }
  return "blocked_missing_evidence";
}

function normalizeRealDeviceRetestRequest(value, executionPayload) {
  // retest request package 从 review execution 派生，固定 safe_to_control=false，避免复测请求变成控制授权。
  const missingEvidence = retestMissingEvidenceList(value || {}, executionPayload);
  const materialReadiness = retestMaterialReadiness(value || {}, executionPayload);
  const requestStatus = safeRealDeviceEvidenceText(
    value?.request_status || value?.overall_status || value?.status,
    retestRequestDefaultStatus(executionPayload),
  );
  const notProven = notProvenList(value?.not_proven || executionPayload.not_proven);
  const blockedReason = safeRealDeviceEvidenceText(
    value?.blocked_reason || value?.blocking_reason,
    executionPayload.blocked_reason || missingEvidence.join("；"),
  );
  const rejectionReason = safeRealDeviceEvidenceText(
    value?.rejection_reason || value?.reject_reason,
    requestStatus.includes("rejected") ? blockedReason : "not_rejected",
  );
  const owner = safeRealDeviceEvidenceText(value?.owner || value?.review_owner, executionPayload.review_owner);
  const nextAction = safeRealDeviceEvidenceText(
    value?.next_action || value?.next_step,
    missingEvidence.length ? `补齐 ${missingEvidence[0]}` : "补齐真实设备复测材料",
  );
  return {
    schema: REAL_DEVICE_RETEST_REQUEST_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_RETEST_REQUEST_SUMMARY_SCHEMA,
    package_schema: REAL_DEVICE_RETEST_REQUEST_PACKAGE_SCHEMA,
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "derived_from_mobile_real_device_review_execution"),
    retest_request_id: safeRealDeviceEvidenceText(
      value?.retest_request_id || value?.request_id,
      `retest_request_${Date.now()}`,
    ),
    execution_session_id: safeRealDeviceEvidenceText(value?.execution_session_id, executionPayload.execution_session_id),
    request_status: requestStatus,
    overall_status: requestStatus,
    review_result: safeRealDeviceEvidenceText(value?.review_result, executionPayload.review_result),
    review_status: safeRealDeviceEvidenceText(value?.review_status, executionPayload.review_status),
    owner,
    next_action: nextAction,
    safe_to_control: false,
    material_readiness: materialReadiness,
    missing_evidence_list: missingEvidence,
    blocked_reason: blockedReason,
    rejection_reason: rejectionReason,
    retest_checklist: retestChecklistFromExecution(value || {}, executionPayload, missingEvidence),
    redaction_status: safeRealDeviceEvidenceText(value?.redaction_status, executionPayload.redaction_status),
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "retest request package 只表示下一轮真实设备复测材料请求；不是真实设备验收通过、真实 PWA install prompt、O5 外部 proof、HIL 或 delivery success。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按 missing evidence list 补齐材料；Start、Confirm、Cancel 继续 fail closed。",
    ),
    ack_semantics: safeRealDeviceEvidenceText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_RETEST_REQUEST_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || executionPayload.evidence_boundary,
      MOBILE_REAL_DEVICE_REVIEW_EXECUTION_BOUNDARY,
    ),
    linked_review_execution: {
      schema: REAL_DEVICE_REVIEW_EXECUTION_PACKAGE_SCHEMA,
      execution_schema: executionPayload.schema,
      summary_schema: executionPayload.summary_schema,
      execution_session_id: executionPayload.execution_session_id,
      review_result: executionPayload.review_result,
      review_status: executionPayload.review_status,
      review_owner: executionPayload.review_owner,
      redaction_status: executionPayload.redaction_status,
      evidence_boundary: executionPayload.evidence_boundary,
      source_evidence_boundary: executionPayload.source_evidence_boundary,
      safe_to_control: false,
    },
    not_proven: notProven,
  };
}

function mobileRealDeviceRetestRequestFromStatus(status, readiness, diagnostics) {
  const executionPayload = mobileRealDeviceReviewExecutionFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceRetestRequestCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceRetestRequest(provided, executionPayload);
}

function fieldTrialInputValue(id, fallback = "not_proven") {
  // 表单字段属于人工 observation，只复制短文本摘要，敏感内容由 safeRealDeviceEvidenceText 过滤。
  const element = $(id);
  if (!element) {
    return fallback;
  }
  return safeRealDeviceEvidenceText(element.value, fallback);
}

function collectFieldTrialObservationFields(value) {
  // observation fields 是人工现场记录，不自动证明真实设备、production app 或 PWA prompt。
  const provided = value?.observation_fields && typeof value.observation_fields === "object"
    ? value.observation_fields
    : {};
  return {
    device_type: safeRealDeviceEvidenceText(
      provided.device_type,
      fieldTrialInputValue("fieldTrialDeviceType", "not_proven"),
    ),
    os_browser: safeRealDeviceEvidenceText(
      provided.os_browser,
      fieldTrialInputValue("fieldTrialOsBrowser", "not_proven"),
    ),
    production_app_observed: safeRealDeviceEvidenceText(
      provided.production_app_observed,
      fieldTrialInputValue("fieldTrialProductionAppObserved", "not_proven"),
    ),
    pwa_install_prompt_observed: safeRealDeviceEvidenceText(
      provided.pwa_install_prompt_observed,
      fieldTrialInputValue("fieldTrialPwaPromptObserved", "not_proven"),
    ),
    user_choice: safeRealDeviceEvidenceText(
      provided.user_choice,
      fieldTrialInputValue("fieldTrialUserChoice", "not_proven"),
    ),
    offline_reload_observed: safeRealDeviceEvidenceText(
      provided.offline_reload_observed,
      fieldTrialInputValue("fieldTrialOfflineReloadObserved", "not_proven"),
    ),
    touch_target_issue: safeRealDeviceEvidenceText(
      provided.touch_target_issue,
      fieldTrialInputValue("fieldTrialTouchTargetIssue", "not_proven"),
    ),
    visual_issue: safeRealDeviceEvidenceText(
      provided.visual_issue,
      fieldTrialInputValue("fieldTrialVisualIssue", "not_proven"),
    ),
    operator_note: safeRealDeviceEvidenceText(
      provided.operator_note,
      fieldTrialInputValue("fieldTrialOperatorNote", "not_provided"),
    ),
    support_note: safeRealDeviceEvidenceText(
      provided.support_note,
      fieldTrialInputValue("fieldTrialSupportNote", "not_provided"),
    ),
  };
}

function collectFieldTrialRuntimeMetadata(localEvidence) {
  // runtime metadata 只包含浏览器可安全读取的 phone-safe 元数据，不包含 raw URL query 或内部机器人字段。
  const serviceWorkerSupported = "serviceWorker" in navigator;
  return {
    viewport_css_width: localEvidence.viewport.width_css_px,
    viewport_css_height: localEvidence.viewport.height_css_px,
    device_pixel_ratio: localEvidence.viewport.device_pixel_ratio,
    orientation: localEvidence.viewport.orientation,
    touch_capability: localEvidence.touch_target.touch_capable,
    max_touch_points: localEvidence.touch_target.max_touch_points,
    coarse_pointer: localEvidence.touch_target.coarse_pointer,
    display_mode: localEvidence.display_mode,
    manifest_link_present: localEvidence.pwa.manifest_link_present,
    service_worker_supported: serviceWorkerSupported,
    service_worker_registration_hint: serviceWorkerSupported ? localEvidence.service_worker.status : "not_supported",
    offline_shell_hint: localEvidence.service_worker.offline_shell_status,
    client_timestamp: new Date().toISOString(),
    entry_url_summary: safeEntryUrlSummary(),
  };
}

function fieldTrialNotProven(value) {
  // 现场试跑包本轮仍是 Docker/local software proof，not_proven 必须保留外部和真实设备缺口。
  const provided = notProvenList(value?.not_proven);
  const required = [
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "Objective 5 外部 proof",
    "HIL",
    "delivery success",
  ];
  return Array.from(new Set([...provided, ...required])).slice(0, 12);
}

function normalizeRealDeviceFieldTrialPackage(value, localEvidence, retestRequest) {
  // package、summary、copy 三层都从同一个白名单对象派生，避免复制路径和展示路径分叉。
  const runtimeMetadata = collectFieldTrialRuntimeMetadata(localEvidence);
  const observationFields = collectFieldTrialObservationFields(value || {});
  const overallStatus = safeRealDeviceEvidenceText(
    value?.overall_status || value?.status,
    "blocked_software_proof_only",
  );
  const notProven = fieldTrialNotProven(value || {});
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_SUMMARY_SCHEMA,
    schema_version: 1,
    package_schema: REAL_DEVICE_FIELD_TRIAL_SCHEMA,
    overall_status: overallStatus,
    safe_to_control: false,
    runtime_summary: `${runtimeMetadata.viewport_css_width}x${runtimeMetadata.viewport_css_height} DPR=${runtimeMetadata.device_pixel_ratio} display=${runtimeMetadata.display_mode}`,
    observation_summary: `device=${observationFields.device_type} / app=${observationFields.production_app_observed} / prompt=${observationFields.pwa_install_prompt_observed}`,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_COPY_SCHEMA,
    field_trial_id: safeRealDeviceEvidenceText(value?.field_trial_id || value?.trial_id, stableFieldTrialReference),
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "mobile_web_local_field_trial_form"),
    overall_status: overallStatus,
    safe_to_control: false,
    runtime_metadata: runtimeMetadata,
    observation_fields: observationFields,
    mobile_real_device_field_trial_package_summary: summary,
    linked_retest_request: {
      schema: REAL_DEVICE_RETEST_REQUEST_PACKAGE_SCHEMA,
      request_schema: retestRequest.schema,
      request_status: retestRequest.request_status,
      evidence_boundary: retestRequest.evidence_boundary,
      source_evidence_boundary: retestRequest.source_evidence_boundary,
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "真实设备现场试跑包只整理 phone-safe runtime metadata 和人工 observation fields；本轮是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "把 mobile_real_device_field_trial_package_copy 交给 Product closeout；不要把它当作真实 iPhone/Android、production app、O5、HIL 或 delivery success。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialPackageFromStatus(status, readiness, diagnostics) {
  const localEvidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const retestRequest = mobileRealDeviceRetestRequestFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialPackage(provided, localEvidence, retestRequest);
}

function fieldTrialReviewStatusFromPackage(value, packagePayload) {
  // 复核状态覆盖每个现场验收维度；缺字段时保守继承 field trial observation 的 not_proven。
  const provided = value?.review_status && typeof value.review_status === "object" ? value.review_status : {};
  const observation = packagePayload?.observation_fields || {};
  const runtime = packagePayload?.runtime_metadata || {};
  return {
    real_device: safeRealDeviceEvidenceText(provided.real_device, observation.device_type || "not_proven"),
    production_app: safeRealDeviceEvidenceText(
      provided.production_app,
      observation.production_app_observed || "not_proven",
    ),
    pwa_install_prompt: safeRealDeviceEvidenceText(
      provided.pwa_install_prompt,
      observation.pwa_install_prompt_observed || "not_proven",
    ),
    user_choice: safeRealDeviceEvidenceText(provided.user_choice, observation.user_choice || "not_proven"),
    offline: safeRealDeviceEvidenceText(
      provided.offline,
      observation.offline_reload_observed || runtime.offline_shell_hint || "not_proven",
    ),
    touch: safeRealDeviceEvidenceText(provided.touch, observation.touch_target_issue || "not_proven"),
    visual: safeRealDeviceEvidenceText(provided.visual, observation.visual_issue || "not_proven"),
    material_redaction: safeRealDeviceEvidenceText(
      provided.material_redaction || value?.material_redaction_status || value?.redaction_status,
      "phone_safe_review_only",
    ),
  };
}

function fieldTrialReviewBlockers(reviewStatus, packagePayload) {
  // blocker list 面向 Product/Support 复核，逐项说明缺口而不是给出验收结论。
  const blockers = [];
  if (/not_proven|unknown|not_provided/i.test(reviewStatus.real_device)) {
    blockers.push("real device evidence not_proven。");
  }
  if (/not_proven|not_observed|not_provided/i.test(reviewStatus.production_app)) {
    blockers.push("production app material not_proven。");
  }
  if (/not_proven|not_observed|not_provided/i.test(reviewStatus.pwa_install_prompt)) {
    blockers.push("PWA install prompt material not_proven。");
  }
  if (/not_proven|not_observed|not_provided/i.test(reviewStatus.user_choice)) {
    blockers.push("PWA user choice material not_proven。");
  }
  if (/not_proven|not_observed|not_provided/i.test(reviewStatus.offline)) {
    blockers.push("offline behavior material not_proven。");
  }
  if (/issue_observed|not_proven|not_provided/i.test(reviewStatus.touch)) {
    blockers.push("touch material needs review。");
  }
  if (/issue_observed|not_proven|not_provided/i.test(reviewStatus.visual)) {
    blockers.push("visual material needs review。");
  }
  if (!/phone_safe|passed|redacted/i.test(reviewStatus.material_redaction)) {
    blockers.push("material redaction not confirmed phone-safe。");
  }
  if (packagePayload?.safe_to_control !== false) {
    blockers.push("source package safe_to_control must remain false。");
  }
  return blockers.slice(0, 10);
}

function fieldTrialReviewChecklist(value, reviewStatus) {
  // checklist 固定覆盖八个 review status，避免 UI 只复核截图而遗漏离线、触控或脱敏。
  const provided = Array.isArray(value?.review_checklist) ? value.review_checklist : [];
  const base = provided.length ? provided : [
    ["real device", reviewStatus.real_device, "核对是否有真实 iPhone/Android device behavior 摘要。"],
    ["production app", reviewStatus.production_app, "核对是否有 production app 入口和 release summary。"],
    ["PWA install prompt", reviewStatus.pwa_install_prompt, "核对是否有真实 install prompt capture status。"],
    ["user choice", reviewStatus.user_choice, "核对是否记录真实 install prompt user choice。"],
    ["offline", reviewStatus.offline, "核对弱网或离线 reload 只说明静态壳行为。"],
    ["touch", reviewStatus.touch, "核对主要触控目标是否有 phone-safe 观察摘要。"],
    ["visual", reviewStatus.visual, "核对首屏视觉问题是否有 phone-safe 观察摘要。"],
    ["material redaction", reviewStatus.material_redaction, "核对复制包只包含复核白名单和 phone-safe 摘要。"],
  ].map(([item, status, safe_phone_copy]) => ({ item, status, safe_phone_copy }));
  return base.slice(0, 8).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.label, "review checklist"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "not_proven"),
    safe_phone_copy: safeRealDeviceEvidenceText(
      step?.safe_phone_copy || step?.copy || step?.summary,
      "等待 Product/Support 复核 phone-safe 现场材料。",
    ),
  }));
}

function fieldTrialReviewNotProven(value, packagePayload) {
  // review gate 必须完整继承现场试跑缺口，并补充复核本身不证明的材料状态。
  const required = [
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "offline real-device behavior",
    "touch and visual acceptance",
    "Objective 5 外部 proof",
    "HIL",
    "delivery success",
  ];
  return Array.from(new Set([
    ...notProvenList(value?.not_proven || packagePayload?.not_proven),
    ...required,
  ])).slice(0, 12);
}

function normalizeRealDeviceFieldTrialReview(value, packagePayload) {
  // review、summary、copy 都只从白名单字段生成；safe_to_control 固定 false，避免复核包变控制授权。
  const reviewStatus = fieldTrialReviewStatusFromPackage(value || {}, packagePayload || {});
  const blockers = Array.isArray(value?.blocker_list)
    ? value.blocker_list.map((item) => safeRealDeviceEvidenceText(item, "blocked_missing_evidence"))
    : fieldTrialReviewBlockers(reviewStatus, packagePayload || {});
  const overallStatus = safeRealDeviceEvidenceText(
    value?.overall_status || value?.status,
    blockers.length ? "blocked_review_not_proven" : "ready_for_product_review_not_control",
  );
  const notProven = fieldTrialReviewNotProven(value || {}, packagePayload || {});
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SUMMARY_SCHEMA,
    schema_version: 1,
    review_schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SCHEMA,
    overall_status: overallStatus,
    safe_to_control: false,
    review_status: reviewStatus,
    blocker_count: blockers.length,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_COPY_SCHEMA,
    review_id: safeRealDeviceEvidenceText(value?.review_id || value?.field_trial_review_id, `field_trial_review_${Date.now()}`),
    source: safeRealDeviceEvidenceText(value?.source, value ? "status_or_diagnostics" : "derived_from_mobile_real_device_field_trial_package"),
    overall_status: overallStatus,
    safe_to_control: false,
    review_status: reviewStatus,
    blocker_list: blockers,
    review_checklist: fieldTrialReviewChecklist(value || {}, reviewStatus),
    material_redaction_status: reviewStatus.material_redaction,
    mobile_real_device_field_trial_review_summary: summary,
    linked_field_trial_package: {
      schema: REAL_DEVICE_FIELD_TRIAL_SCHEMA,
      summary_schema: REAL_DEVICE_FIELD_TRIAL_SUMMARY_SCHEMA,
      field_trial_id: safeRealDeviceEvidenceText(packagePayload?.field_trial_id, stableFieldTrialReference),
      overall_status: safeRealDeviceEvidenceText(packagePayload?.overall_status, "blocked_software_proof_only"),
      evidence_boundary: safeRealDeviceEvidenceText(packagePayload?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY),
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "现场试跑证据复核只核对材料 shape、缺失项和脱敏状态；不是 delivery success、真实验收通过或控制放行。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按 blocker list 补齐 real device、production app、PWA prompt/user choice、offline、touch、visual 和 redaction 摘要。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || packagePayload?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY,
    ),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialReviewFromStatus(status, readiness, diagnostics) {
  const fieldTrialPackage = mobileRealDeviceFieldTrialPackageFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialReviewCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialReview(provided, fieldTrialPackage);
}

function runbookExecutionChecklist(value, reviewPayload) {
  // 执行清单覆盖真实手机现场试跑的关键步骤，但每项仍是待执行 metadata，不证明现场已发生。
  const provided = Array.isArray(value?.execution_checklist) ? value.execution_checklist : [];
  const reviewStatus = reviewPayload?.review_status || {};
  const base = provided.length ? provided : [
    ["real device", reviewStatus.real_device || "not_proven", "准备真实 iPhone/Android 设备和浏览器，不用本地桌面 proof 代替。"],
    ["production app", reviewStatus.production_app || "not_proven", "确认 production app 或 production-like 入口材料，只记录 phone-safe release 摘要。"],
    ["PWA install prompt", reviewStatus.pwa_install_prompt || "not_proven", "观察真实 PWA install prompt 是否出现；只记录 capture status。"],
    ["user choice", reviewStatus.user_choice || "not_proven", "记录用户选择 accepted/dismissed summary，不粘贴账号、URL 参数或截图原文。"],
    ["offline", reviewStatus.offline || "not_proven", "执行弱网/离线 reload，结论只写静态壳或 blocked 行为摘要。"],
    ["touch", reviewStatus.touch || "not_proven", "检查 Start、Confirm、Cancel、复制按钮触控是否可达，动作仍 fail closed。"],
    ["visual", reviewStatus.visual || "not_proven", "检查首屏 panel、copy 区域和按钮是否溢出或遮挡。"],
    ["material redaction", reviewStatus.material_redaction || "phone_safe_review_only", "确认所有材料已脱敏，不复制 token、凭证、内部路径或机器人原始响应。"],
  ].map(([item, status, safe_phone_copy]) => ({ item, status, safe_phone_copy }));
  return base.slice(0, 8).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.label, "runbook checklist"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "not_proven"),
    safe_phone_copy: safeRealDeviceEvidenceText(
      step?.safe_phone_copy || step?.copy || step?.summary,
      "按现场试跑 runbook 执行并只记录 phone-safe 摘要。",
    ),
  }));
}

function runbookExecutionReadiness(value, reviewPayload) {
  // readiness 面向执行前核对；缺字段时继承 review 缺口，不升级成真实手机或 production app 证明。
  const provided = value?.execution_readiness && typeof value.execution_readiness === "object"
    ? value.execution_readiness
    : {};
  const reviewStatus = reviewPayload?.review_status || {};
  return {
    real_device: safeRealDeviceEvidenceText(provided.real_device, reviewStatus.real_device || "not_proven"),
    production_app: safeRealDeviceEvidenceText(provided.production_app, reviewStatus.production_app || "not_proven"),
    pwa_install_prompt: safeRealDeviceEvidenceText(
      provided.pwa_install_prompt,
      reviewStatus.pwa_install_prompt || "not_proven",
    ),
    user_choice: safeRealDeviceEvidenceText(provided.user_choice, reviewStatus.user_choice || "not_proven"),
    offline: safeRealDeviceEvidenceText(provided.offline, reviewStatus.offline || "not_proven"),
    touch: safeRealDeviceEvidenceText(provided.touch, reviewStatus.touch || "not_proven"),
    visual: safeRealDeviceEvidenceText(provided.visual, reviewStatus.visual || "not_proven"),
    material_redaction: safeRealDeviceEvidenceText(
      provided.material_redaction,
      reviewStatus.material_redaction || "phone_safe_review_only",
    ),
  };
}

function runbookExecutionNotProven(value, reviewPayload) {
  // runbook execution gate 是执行准备包；真实设备、云、HIL、delivery success 缺口必须继续明示。
  const required = [
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "offline real-device behavior",
    "touch and visual acceptance",
    "Objective 5 外部 proof",
    "HIL",
    "dropoff/cancel completion",
    "delivery success",
  ];
  return Array.from(new Set([
    ...notProvenList(value?.not_proven || reviewPayload?.not_proven),
    ...required,
  ])).slice(0, 12);
}

function normalizeRealDeviceFieldTrialRunbookExecution(value, reviewPayload) {
  // package/summary/copy 固定 safe_to_control=false，确保执行清单不改变 Start/Confirm/Cancel gating。
  const executionReadiness = runbookExecutionReadiness(value || {}, reviewPayload || {});
  const checklist = runbookExecutionChecklist(value || {}, reviewPayload || {});
  const openItems = checklist
    .filter((step) => !/ready|observed|phone_safe|passed|none_observed/i.test(step.status))
    .map((step) => `${step.item}: ${step.status}`)
    .slice(0, 8);
  const overallStatus = safeRealDeviceEvidenceText(
    value?.overall_status || value?.status,
    openItems.length ? "blocked_runbook_execution_not_proven" : "ready_for_real_device_runbook_execution_not_control",
  );
  const notProven = runbookExecutionNotProven(value || {}, reviewPayload || {});
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SUMMARY_SCHEMA,
    schema_version: 1,
    execution_schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SCHEMA,
    overall_status: overallStatus,
    safe_to_control: false,
    execution_readiness: executionReadiness,
    open_item_count: openItems.length,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_COPY_SCHEMA,
    runbook_execution_id: safeRealDeviceEvidenceText(
      value?.runbook_execution_id || value?.execution_id,
      `field_trial_runbook_execution_${Date.now()}`,
    ),
    source: safeRealDeviceEvidenceText(
      value?.source,
      value ? "status_or_diagnostics" : "derived_from_mobile_real_device_field_trial_review",
    ),
    overall_status: overallStatus,
    safe_to_control: false,
    execution_readiness: executionReadiness,
    execution_checklist: checklist,
    open_items: openItems,
    material_redaction_status: executionReadiness.material_redaction,
    mobile_real_device_field_trial_runbook_execution_summary: summary,
    linked_field_trial_review: {
      schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SCHEMA,
      summary_schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SUMMARY_SCHEMA,
      review_id: safeRealDeviceEvidenceText(reviewPayload?.review_id, "field_trial_review_not_provided"),
      overall_status: safeRealDeviceEvidenceText(reviewPayload?.overall_status, "blocked_review_not_proven"),
      evidence_boundary: safeRealDeviceEvidenceText(
        reviewPayload?.evidence_boundary,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY,
      ),
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "现场试跑执行清单只指导下一次真实手机现场试跑采证；本轮是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按清单逐项采集 real device、production app、PWA prompt/user choice、offline、touch、visual 和 redacted material 摘要。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(
      value?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY,
    ),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || reviewPayload?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY,
    ),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialRunbookExecutionFromStatus(status, readiness, diagnostics) {
  const reviewPayload = mobileRealDeviceFieldTrialReviewFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialRunbookExecutionCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialRunbookExecution(provided, reviewPayload);
}

function evidenceRecordInputValue(id, fallback = "not_proven") {
  // 现场记录表单只允许短文本/枚举摘要进入复制包，敏感词会被 safeRealDeviceEvidenceText 降级。
  const element = $(id);
  if (!element) {
    return fallback;
  }
  return safeRealDeviceEvidenceText(element.value, fallback);
}

function evidenceRecordObservations(value, runbookPayload) {
  // 记录字段覆盖现场试跑关键信息；缺字段时继承 runbook readiness，但仍保持 not_proven。
  const provided = value?.record_fields && typeof value.record_fields === "object"
    ? value.record_fields
    : {};
  const readiness = runbookPayload?.execution_readiness || {};
  return {
    real_device: safeRealDeviceEvidenceText(
      provided.real_device,
      evidenceRecordInputValue("evidenceRecordRealDevice", readiness.real_device || "not_proven"),
    ),
    production_app: safeRealDeviceEvidenceText(
      provided.production_app,
      evidenceRecordInputValue("evidenceRecordProductionApp", readiness.production_app || "not_proven"),
    ),
    pwa_install_prompt: safeRealDeviceEvidenceText(
      provided.pwa_install_prompt,
      evidenceRecordInputValue("evidenceRecordPwaPrompt", readiness.pwa_install_prompt || "not_proven"),
    ),
    user_choice: safeRealDeviceEvidenceText(
      provided.user_choice,
      evidenceRecordInputValue("evidenceRecordUserChoice", readiness.user_choice || "not_proven"),
    ),
    offline: safeRealDeviceEvidenceText(
      provided.offline,
      evidenceRecordInputValue("evidenceRecordOffline", readiness.offline || "not_proven"),
    ),
    touch: safeRealDeviceEvidenceText(
      provided.touch,
      evidenceRecordInputValue("evidenceRecordTouch", readiness.touch || "not_proven"),
    ),
    visual: safeRealDeviceEvidenceText(
      provided.visual,
      evidenceRecordInputValue("evidenceRecordVisual", readiness.visual || "not_proven"),
    ),
    material_redaction: safeRealDeviceEvidenceText(
      provided.material_redaction || value?.material_redaction_status || value?.redaction_status,
      evidenceRecordInputValue("evidenceRecordMaterialRedaction", readiness.material_redaction || "not_proven"),
    ),
    operator_note: safeRealDeviceEvidenceText(
      provided.operator_note || value?.operator_note,
      evidenceRecordInputValue("evidenceRecordOperatorNote", "not_provided"),
    ),
    support_note: safeRealDeviceEvidenceText(
      provided.support_note || value?.support_note,
      evidenceRecordInputValue("evidenceRecordSupportNote", "not_provided"),
    ),
  };
}

function evidenceRecordOpenItems(fields) {
  // open_items 只根据白名单状态生成，避免把人工备注里的原始材料复制进归档。
  return [
    ["real_device", fields.real_device],
    ["production_app", fields.production_app],
    ["pwa_install_prompt", fields.pwa_install_prompt],
    ["user_choice", fields.user_choice],
    ["offline", fields.offline],
    ["touch", fields.touch],
    ["visual", fields.visual],
    ["material_redaction", fields.material_redaction],
  ]
    .filter(([, status]) => !/observed|captured|accepted|dismissed|static_shell|none_observed|phone_safe|redacted|passed/i.test(status))
    .map(([item, status]) => `${item}: ${status}`)
    .slice(0, 8);
}

function evidenceRecordNotProven(value, runbookPayload) {
  // record gate 只是现场记录容器；真实设备、外部云和机器人完成缺口必须继续可见。
  const required = [
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "offline real-device behavior",
    "touch and visual acceptance",
    "Objective 5 外部 proof",
    "HIL",
    "dropoff/cancel completion",
    "delivery success",
  ];
  return Array.from(new Set([
    ...notProvenList(value?.not_proven || runbookPayload?.not_proven),
    ...required,
  ])).slice(0, 12);
}

function normalizeRealDeviceFieldTrialEvidenceRecord(value, runbookPayload) {
  // record、summary、copy、archive 共用同一个白名单对象，归档也不保存 raw JSON 或完整材料。
  const recordFields = evidenceRecordObservations(value || {}, runbookPayload || {});
  const openItems = evidenceRecordOpenItems(recordFields);
  const overallStatus = safeRealDeviceEvidenceText(
    value?.overall_status || value?.status,
    openItems.length ? "blocked_evidence_record_not_proven" : "recorded_phone_safe_summary_not_control",
  );
  const notProven = evidenceRecordNotProven(value || {}, runbookPayload || {});
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SUMMARY_SCHEMA,
    schema_version: 1,
    record_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SCHEMA,
    overall_status: overallStatus,
    safe_to_control: false,
    record_fields: recordFields,
    open_item_count: openItems.length,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_COPY_SCHEMA,
    archive_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_ARCHIVE_SCHEMA,
    evidence_record_id: safeRealDeviceEvidenceText(
      value?.evidence_record_id || value?.record_id,
      stableFieldTrialEvidenceRecordReference,
    ),
    source: safeRealDeviceEvidenceText(
      value?.source,
      value ? "status_or_diagnostics" : "derived_from_mobile_real_device_field_trial_runbook_execution",
    ),
    overall_status: overallStatus,
    safe_to_control: false,
    record_fields: recordFields,
    open_items: openItems,
    material_redaction_status: recordFields.material_redaction,
    mobile_real_device_field_trial_evidence_record_summary: summary,
    linked_runbook_execution: {
      schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SCHEMA,
      summary_schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SUMMARY_SCHEMA,
      runbook_execution_id: safeRealDeviceEvidenceText(runbookPayload?.runbook_execution_id, "runbook_execution_not_provided"),
      overall_status: safeRealDeviceEvidenceText(runbookPayload?.overall_status, "blocked_runbook_execution_not_proven"),
      evidence_boundary: safeRealDeviceEvidenceText(
        runbookPayload?.evidence_boundary,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY,
      ),
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "现场证据记录只归档 phone-safe 观察摘要；本轮是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按记录字段补齐 real device、production app、PWA prompt/user choice、offline、touch、visual 和 redaction 摘要。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(
      value?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_BOUNDARY,
    ),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || runbookPayload?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY,
    ),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialEvidenceRecordFromStatus(status, readiness, diagnostics) {
  const runbookPayload = mobileRealDeviceFieldTrialRunbookExecutionFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialEvidenceRecordCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialEvidenceRecord(provided, runbookPayload);
}

function verdictMissingEvidence(recordPayload) {
  // verdict 缺口只来自 record/archive 白名单字段，避免 reviewer 从备注中复制完整材料或内部日志。
  const fields = recordPayload?.record_fields || {};
  const base = [
    ["real_device", fields.real_device, "真实 iPhone/Android device behavior 摘要"],
    ["production_app", fields.production_app, "production app release/entry 摘要"],
    ["pwa_install_prompt", fields.pwa_install_prompt, "真实 PWA install prompt capture"],
    ["user_choice", fields.user_choice, "真实 install prompt user choice"],
    ["offline", fields.offline, "真实设备 offline/reload 行为摘要"],
    ["touch", fields.touch, "真实触控目标观察摘要"],
    ["visual", fields.visual, "真实视觉/首屏可读性观察摘要"],
    ["material_redaction", fields.material_redaction, "phone-safe redaction passed 证明"],
  ];
  const missing = base
    .filter(([, status]) => !/observed|captured|accepted|dismissed|static_shell|none_observed|phone_safe|redacted|passed/i.test(status || ""))
    .map(([field, status, request]) => ({
      field,
      status: safeRealDeviceEvidenceText(status, "not_proven"),
      material_request: request,
    }));
  return missing.length ? missing : [{
    field: "human_review",
    status: "pending_verdict_review",
    material_request: "人工复核 record/archive package 后再安排真实手机验收。",
  }];
}

function normalizeRealDeviceFieldTrialEvidenceVerdict(value, recordPayload, archivePayload) {
  // verdict package 固定为 metadata-only：只总结缺口和下一步，不把 record 变成验收通过。
  const missingEvidence = Array.isArray(value?.missing_evidence)
    ? value.missing_evidence.slice(0, 10).map((item) => ({
      field: safeRealDeviceEvidenceText(item?.field || item?.id, "field_trial_evidence"),
      status: safeRealDeviceEvidenceText(item?.status || item?.state, "not_proven"),
      material_request: safeRealDeviceEvidenceText(item?.material_request || item?.request, "补齐 phone-safe evidence summary。"),
    }))
    : verdictMissingEvidence(recordPayload || {});
  const verdict = safeRealDeviceEvidenceText(
    value?.verdict || value?.review_verdict,
    missingEvidence.length ? "blocked_missing_field_trial_evidence" : "ready_for_human_retest_review_not_control",
  );
  const notProven = Array.from(new Set([
    ...notProvenList(value?.not_proven || recordPayload?.not_proven),
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "Objective 5 外部 proof",
    "HIL",
    "delivery success",
  ])).slice(0, 12);
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SUMMARY_SCHEMA,
    schema_version: 1,
    verdict_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA,
    verdict,
    missing_evidence_count: missingEvidence.length,
    safe_to_control: false,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_COPY_SCHEMA,
    verdict_id: safeRealDeviceEvidenceText(value?.verdict_id, stableFieldTrialEvidenceVerdictReference),
    source: safeRealDeviceEvidenceText(value?.source, "derived_from_mobile_real_device_field_trial_evidence_record_archive"),
    verdict,
    safe_to_control: false,
    missing_evidence: missingEvidence,
    retest_request: safeRealDeviceEvidenceText(
      value?.retest_request,
      "按 missing_evidence 逐项补齐后重新执行真实手机 field trial。",
    ),
    next_material_request: safeRealDeviceEvidenceText(
      value?.next_material_request,
      "提交脱敏 real device、production app、PWA prompt/user choice、offline、touch、visual 和 redaction 摘要。",
    ),
    mobile_real_device_field_trial_evidence_verdict_summary: summary,
    linked_evidence_record: {
      schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SCHEMA,
      evidence_record_id: safeRealDeviceEvidenceText(recordPayload?.evidence_record_id, "evidence_record_not_provided"),
      overall_status: safeRealDeviceEvidenceText(recordPayload?.overall_status, "blocked_evidence_record_not_proven"),
      evidence_boundary: safeRealDeviceEvidenceText(recordPayload?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_BOUNDARY),
      archive_status: safeRealDeviceEvidenceText(archivePayload?.archive_status, "archive_not_present"),
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "现场证据 verdict 只复核 field trial evidence record/archive 缺口；本轮是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "补齐 verdict missing_evidence 后再发起真实手机 retest；Start、Confirm、Cancel 继续 fail closed。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || recordPayload?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_BOUNDARY,
    ),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialEvidenceVerdictFromStatus(status, readiness, diagnostics) {
  const recordPayload = mobileRealDeviceFieldTrialEvidenceRecordFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialEvidenceVerdictCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialEvidenceVerdict(provided, recordPayload, archivedRealDeviceFieldTrialEvidenceRecordPackage);
}

function retestExecutionChecklistFromVerdict(value, verdictPayload) {
  // 清单来自 verdict 的 missing evidence/material request，避免手写一份和 verdict 脱节的复测说明。
  const provided = Array.isArray(value?.execution_checklist) ? value.execution_checklist : [];
  const base = provided.length
    ? provided
    : (verdictPayload.missing_evidence || []).map((item) => ({
      item: item.field,
      status: item.status,
      material_request: item.material_request,
      owner: "field_trial_operator",
      evidence_slot: item.field,
    }));
  return base.slice(0, 10).map((step) => ({
    item: safeRealDeviceEvidenceText(step?.item || step?.id || step?.evidence_slot, "field_trial_evidence"),
    status: safeRealDeviceEvidenceText(step?.status || step?.state, "not_proven"),
    material_request: safeRealDeviceEvidenceText(
      step?.material_request || step?.request,
      "补齐 phone-safe evidence summary。",
    ),
    owner: safeRealDeviceEvidenceText(step?.owner, "field_trial_operator"),
    evidence_slot: safeRealDeviceEvidenceText(step?.evidence_slot || step?.field, "field_trial_evidence"),
  }));
}

function normalizeRealDeviceFieldTrialRetestExecution(value, verdictPayload) {
  // 该 gate 把 verdict 的下一步变成可执行复测清单，但仍固定为只读 support metadata。
  const executionChecklist = retestExecutionChecklistFromVerdict(value || {}, verdictPayload);
  const missingEvidence = executionChecklist.map((step) => `${step.evidence_slot}=${step.status}`);
  const notProven = Array.from(new Set([
    ...notProvenList(value?.not_proven || verdictPayload?.not_proven),
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "真实公网 HTTPS/TLS",
    "4G/SIM",
    "OSS/CDN live traffic",
    "production DB/queue",
    "HIL",
    "delivery success",
  ])).slice(0, 14);
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SUMMARY_SCHEMA,
    schema_version: 1,
    execution_schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SCHEMA,
    execution_status: safeRealDeviceEvidenceText(
      value?.execution_status || value?.overall_status || value?.status,
      "blocked_waiting_retest_materials",
    ),
    missing_evidence_count: executionChecklist.filter((step) => step.status === "not_proven").length,
    safe_to_control: false,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_BOUNDARY,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_COPY_SCHEMA,
    execution_id: safeRealDeviceEvidenceText(value?.execution_id, stableFieldTrialRetestExecutionReference),
    source: safeRealDeviceEvidenceText(value?.source, "derived_from_mobile_real_device_field_trial_evidence_verdict"),
    execution_status: summary.execution_status,
    safe_to_control: false,
    retest_request: safeRealDeviceEvidenceText(value?.retest_request, verdictPayload.retest_request),
    material_request: safeRealDeviceEvidenceText(
      value?.material_request || value?.next_material_request,
      verdictPayload.next_material_request,
    ),
    missing_evidence_summary: missingEvidence,
    execution_checklist: executionChecklist,
    mobile_real_device_field_trial_retest_execution_summary: summary,
    linked_evidence_verdict: {
      schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA,
      verdict_id: safeRealDeviceEvidenceText(verdictPayload?.verdict_id, "verdict_not_provided"),
      verdict: safeRealDeviceEvidenceText(verdictPayload?.verdict, "blocked_missing_field_trial_evidence"),
      evidence_boundary: safeRealDeviceEvidenceText(
        verdictPayload?.evidence_boundary,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY,
      ),
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "复测执行包只把 verdict 的 retest/material request 转成现场执行清单；本轮仍是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按清单补齐真实手机、production app、PWA prompt/user choice、外部云材料后再提交人工复核；主操作继续 fail closed。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_BOUNDARY),
    source_evidence_boundary: safeRealDeviceEvidenceText(
      value?.source_evidence_boundary || verdictPayload?.evidence_boundary,
      MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY,
    ),
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialRetestExecutionFromStatus(status, readiness, diagnostics) {
  const verdictPayload = mobileRealDeviceFieldTrialEvidenceVerdictFromStatus(status, readiness, diagnostics);
  const provided = mobileRealDeviceFieldTrialRetestExecutionCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialRetestExecution(provided, verdictPayload);
}

function fieldTrialAcceptanceSessionSource(status, readiness, diagnostics) {
  // 输入优先级必须稳定，避免低可信 browser proof 覆盖显式 acceptance session 字段。
  const explicitSession = mobileRealDeviceFieldTrialAcceptanceSessionCandidate(status, readiness, diagnostics);
  if (explicitSession) {
    return { kind: "explicit_acceptance_session", value: explicitSession };
  }
  const retestExecution = mobileRealDeviceFieldTrialRetestExecutionCandidate(status, readiness, diagnostics);
  if (retestExecution) {
    return { kind: "field_trial_retest_execution", value: retestExecution };
  }
  const evidenceVerdict = mobileRealDeviceFieldTrialEvidenceVerdictCandidate(status, readiness, diagnostics);
  if (evidenceVerdict) {
    return { kind: "field_trial_evidence_verdict", value: evidenceVerdict };
  }
  const currentBrowserProof = mobileCurrentPwaFieldTrialBrowserProofCandidate(status, readiness, diagnostics);
  if (currentBrowserProof) {
    return { kind: "current_pwa_field_trial_browser_proof", value: currentBrowserProof };
  }
  return { kind: "blocked_by_design_session", value: null };
}

function acceptanceSessionStatusFromSource(value, sourceKind) {
  // session 只允许保守状态；即使上游 proof 看起来完整，也不提升为 control-safe。
  return safeRealDeviceEvidenceText(
    value?.session_status || value?.overall_status || value?.execution_status || value?.verdict || value?.status,
    sourceKind === "blocked_by_design_session" ? "blocked_missing_field_trial_acceptance_materials" : "ready_for_human_acceptance_session_not_control",
  );
}

function acceptanceSessionSourceBoundary(value, sourceKind) {
  // source boundary 只用于追溯输入层级，不把上游 proof 升级成真实设备验收。
  const fallback = {
    explicit_acceptance_session: MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_BOUNDARY,
    field_trial_retest_execution: MOBILE_REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_BOUNDARY,
    field_trial_evidence_verdict: MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY,
    current_pwa_field_trial_browser_proof: "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
    blocked_by_design_session: MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_BOUNDARY,
  }[sourceKind];
  return safeRealDeviceEvidenceText(value?.source_evidence_boundary || value?.evidence_boundary, fallback);
}

function acceptanceSessionField(value, keys, fallback) {
  // 字段可能来自显式 session、retest execution、verdict 或当前 browser proof，只抽取白名单摘要键。
  const source = value && typeof value === "object" ? value : {};
  for (const key of keys) {
    if (source[key] !== undefined) {
      return safeRealDeviceEvidenceText(source[key], fallback);
    }
  }
  return fallback;
}

function fieldTrialAcceptanceChecklist(value, sourceKind, retestPayload, verdictPayload, currentProof) {
  // checklist 固定覆盖现场验收会必须检查的 9 类材料，缺失时全部保持 not_proven。
  const provided = Array.isArray(value?.acceptance_checklist || value?.session_checklist)
    ? value.acceptance_checklist || value.session_checklist
    : [];
  const providedByItem = new Map(provided.map((item) => [safeRealDeviceEvidenceText(item?.item, "unknown"), item]));
  const retestMissing = Array.isArray(retestPayload?.missing_evidence_summary)
    ? retestPayload.missing_evidence_summary.join("；")
    : "field_trial_retest_execution_missing";
  const verdictMissing = Array.isArray(verdictPayload?.missing_evidence)
    ? verdictPayload.missing_evidence.map((item) => `${item.field}=${item.status}`).join("；")
    : "field_trial_evidence_verdict_missing";
  const browserSummary = currentProof && typeof currentProof === "object"
    ? safeRealDeviceEvidenceText(
      currentProof.current_panels_status || currentProof.current_boundaries_status || currentProof.overall_status,
      "current_pwa_browser_proof_summary_only",
    )
    : "current_pwa_browser_proof_missing";
  const defaults = [
    ["real_device_observed", "not_proven", "记录真实 iPhone/Android 设备型号和浏览器；当前只接受脱敏摘要。"],
    ["production_app_observed", "not_proven", "确认是否为 production app 入口；未确认时保持 not_proven。"],
    ["pwa_install_prompt_observed", "not_proven", "记录真实 PWA install prompt 是否出现；本地 browser proof 不能替代。"],
    ["install_user_choice_observed", "not_proven", "记录用户选择 accept/dismiss 的脱敏摘要；不复制截图或原始材料。"],
    ["offline_reload_observed", "not_proven", "切换离线后重载，只记录 static/offline shell 的安全结论。"],
    ["touch_target_issue", "not_proven", "记录触控目标问题摘要；不能包含设备日志、路径或内部字段。"],
    ["visual_issue", "not_proven", "记录首屏遮挡/溢出/重叠摘要；不能粘贴完整材料。"],
    ["material_redaction_status", "not_proven", "确认材料已 whitelist-only redaction；发现敏感字段则 blocked。"],
    ["operator_support_note", "not_provided", "记录 operator/support note 的 phone-safe 摘要。"],
  ];
  return defaults.map(([item, fallbackStatus, fallbackCopy]) => {
    const providedStep = providedByItem.get(item) || {};
    const status = safeRealDeviceEvidenceText(
      providedStep.status || providedStep.state || value?.[item],
      acceptanceSessionField(value, [item], fallbackStatus),
    );
    const sourceHint = {
      real_device_observed: retestMissing,
      production_app_observed: verdictMissing,
      pwa_install_prompt_observed: browserSummary,
    }[item] || sourceKind;
    return {
      item,
      status,
      source_hint: safeRealDeviceEvidenceText(providedStep.source_hint, sourceHint),
      safe_phone_copy: safeRealDeviceEvidenceText(providedStep.safe_phone_copy, fallbackCopy),
    };
  });
}

function normalizeRealDeviceFieldTrialAcceptanceSession(value, sourceKind, retestPayload, verdictPayload, currentProof) {
  // acceptance session 是现场执行 surface，不是验收通过、控制授权或 delivery result。
  const sessionStatus = acceptanceSessionStatusFromSource(value, sourceKind);
  const sourceBoundary = acceptanceSessionSourceBoundary(value, sourceKind);
  const checklist = fieldTrialAcceptanceChecklist(value || {}, sourceKind, retestPayload, verdictPayload, currentProof);
  const blockingItems = checklist.filter((step) => step.status === "not_proven" || step.status === "not_provided");
  const notProven = Array.from(new Set([
    ...notProvenList(value?.not_proven || retestPayload?.not_proven || verdictPayload?.not_proven),
    "真实 iPhone/Android device behavior",
    "production app",
    "真实 PWA install prompt/user choice",
    "Objective 5 external proof",
    "HIL",
    "delivery success",
  ])).slice(0, 14);
  const summary = {
    schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SUMMARY_SCHEMA,
    schema_version: 1,
    session_schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SCHEMA,
    session_status: sessionStatus,
    source_priority: sourceKind,
    checklist_blocked_count: blockingItems.length,
    safe_to_control: false,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_BOUNDARY,
    source_evidence_boundary: sourceBoundary,
    not_proven: notProven,
  };
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SCHEMA,
    schema_version: 1,
    summary_schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SUMMARY_SCHEMA,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_COPY_SCHEMA,
    session_id: safeRealDeviceEvidenceText(value?.session_id, stableFieldTrialAcceptanceSessionReference),
    source: safeRealDeviceEvidenceText(value?.source, sourceKind),
    source_priority: sourceKind,
    session_status: sessionStatus,
    safe_to_control: false,
    acceptance_checklist: checklist,
    blocked_items: blockingItems.map((step) => step.item),
    material_redaction_status: acceptanceSessionField(
      value,
      ["material_redaction_status", "redaction_status"],
      checklist.find((step) => step.item === "material_redaction_status")?.status || "not_proven",
    ),
    operator_note: acceptanceSessionField(value, ["operator_note", "operator_support_note"], "not_provided"),
    support_note: acceptanceSessionField(value, ["support_note", "operator_support_note"], "not_provided"),
    mobile_real_device_field_trial_acceptance_session_summary: summary,
    linked_field_trial_retest_execution: {
      schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SCHEMA,
      execution_id: safeRealDeviceEvidenceText(retestPayload?.execution_id, "field_trial_retest_execution_not_provided"),
      execution_status: safeRealDeviceEvidenceText(retestPayload?.execution_status, "not_proven"),
      evidence_boundary: safeRealDeviceEvidenceText(retestPayload?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_BOUNDARY),
      safe_to_control: false,
    },
    linked_field_trial_evidence_verdict: {
      schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA,
      verdict_id: safeRealDeviceEvidenceText(verdictPayload?.verdict_id, "field_trial_evidence_verdict_not_provided"),
      verdict: safeRealDeviceEvidenceText(verdictPayload?.verdict, "not_proven"),
      evidence_boundary: safeRealDeviceEvidenceText(verdictPayload?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_BOUNDARY),
      safe_to_control: false,
    },
    linked_current_pwa_browser_proof: {
      schema: "trashbot.mobile_current_pwa_field_trial_browser_proof.v1",
      status: safeRealDeviceEvidenceText(
        currentProof?.overall_status || currentProof?.current_panels_status || currentProof?.current_boundaries_status,
        "not_proven",
      ),
      evidence_boundary: "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
      safe_to_control: false,
    },
    safe_phone_copy: safeRealDeviceEvidenceText(
      value?.safe_phone_copy || value?.safe_summary,
      "现场验收会话只把 retest/verdict/current PWA proof 转成 whitelist-only 执行清单；本轮是 Docker/local mobile software proof。",
    ),
    recovery_hint: safeRealDeviceEvidenceText(
      value?.recovery_hint || value?.retry_hint,
      "按 checklist 补齐真实手机、production app、真实 PWA prompt/user choice、offline、touch、visual 和 redaction 摘要；主操作继续 fail closed。",
    ),
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: safeRealDeviceEvidenceText(value?.evidence_boundary, MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_BOUNDARY),
    source_evidence_boundary: sourceBoundary,
    not_proven: notProven,
  };
}

function mobileRealDeviceFieldTrialAcceptanceSessionFromStatus(status, readiness, diagnostics) {
  const source = fieldTrialAcceptanceSessionSource(status, readiness, diagnostics);
  const retestPayload = mobileRealDeviceFieldTrialRetestExecutionFromStatus(status, readiness, diagnostics);
  const verdictPayload = mobileRealDeviceFieldTrialEvidenceVerdictFromStatus(status, readiness, diagnostics);
  const currentProof = mobileCurrentPwaFieldTrialBrowserProofCandidate(status, readiness, diagnostics);
  return normalizeRealDeviceFieldTrialAcceptanceSession(
    source.value,
    source.kind,
    retestPayload,
    verdictPayload,
    currentProof,
  );
}

function bundleFieldSummary(value, fallback = "not_proven") {
  // 字段可能是安全字符串，也可能是状态对象；只抽取摘要键，不展示原始对象。
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return safeBundleText(value, fallback);
  }
  if (value && typeof value === "object") {
    return safeBundleText(
      value.status || value.state || value.overall_status || value.safe_phone_copy || value.safe_summary,
      fallback,
    );
  }
  return fallback;
}

function notProvenList(value) {
  // not_proven 是边界声明，不允许塞入路径、凭证、硬件参数或完整证据内容。
  const list = Array.isArray(value) ? value : [];
  const safe = list.map((item) => safeBundleText(item, "")).filter(Boolean);
  if (safe.length) {
    return safe.slice(0, 10);
  }
  return [
    "真实手机设备/browser",
    "production app",
    "真实 PWA install prompt",
    "真实云/4G",
    "production DB/queue",
    "Nav2/fixed-route",
    "真实底盘运动",
    "HIL",
    "真实送达",
  ];
}

function recoveryDecisionCandidate(status, readiness, diagnostics) {
  // 后端显式 recovery gate/summary 优先；diagnostics 只作为同源 phone-safe 后备。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.mobile_recovery_decision_gate,
    status?.mobile_recovery_decision_summary,
    readiness?.mobile_recovery_decision_gate,
    readiness?.mobile_recovery_decision_summary,
    diagnostics?.mobile_recovery_decision_gate,
    diagnostics?.mobile_recovery_decision_summary,
    diagnosticsReadiness.mobile_recovery_decision_gate,
    diagnosticsReadiness.mobile_recovery_decision_summary,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function recoveryDecisionStateFromPhoneSafe(status, readiness) {
  const offline = offlineResumeFromStatus(status, readiness);
  const feedback = actionFeedbackFromStatus(status, readiness) || latestActionFeedback;
  const raw = `${readiness?.primary_state || ""} ${readiness?.next_action || ""} ${readiness?.support_level || ""} ${commandSafetyFromReadiness(readiness)?.global_block_reason || ""}`.toLowerCase();
  const connection = `${offline.connection_state || status?.connection_state || ""}`.toLowerCase();
  const feedbackState = `${feedback?.state || ""}`.toLowerCase();
  if (["submitted", "waiting_ack", "accepted_or_processing"].includes(feedbackState) || /waiting_ack|pending_ack|ack_pending/.test(raw)) {
    return "pending_ack";
  }
  if (connection && connection !== "online" || /offline|stale|unreachable|disconnect|network/.test(raw)) {
    return "offline_status_stale";
  }
  if (/manual_takeover|human_help|support_required/.test(raw)) {
    return "manual_takeover_required";
  }
  if (feedbackState === "local_submit_failed" || feedbackState === "failed") {
    return "local_submit_failed";
  }
  if (!status?.mobile_primary_journey_gate && !status?.mobile_primary_journey_summary &&
      !readiness?.mobile_primary_journey_gate && !readiness?.mobile_primary_journey_summary) {
    return "missing_primary_journey_readiness";
  }
  if (!status?.phone_support_bundle && !readiness?.phone_support_bundle) {
    return "missing_support_handoff";
  }
  return "blocked_by_design";
}

function recoveryDecisionCopyForState(state) {
  // 中文优先恢复建议覆盖本轮要求的典型阻塞场景；这些文案不放行任何动作。
  const copy = {
    pending_ack: {
      nextAction: "等待 ACK 或刷新状态，暂时不要重复提交。",
      blockingReason: "最近动作仍是 accepted/processing evidence，不能当作任务完成。",
      hint: "超过预期仍无变化时打开诊断，把 client_reference 交给支持人员。",
    },
    offline_status_stale: {
      nextAction: "恢复网络后刷新状态。",
      blockingReason: "手机端状态离线或过期，不能确认机器人当前状态。",
      hint: "离线壳不会缓存、排队或重放控制请求。",
    },
    manual_takeover_required: {
      nextAction: "先人工接管或联系现场支持。",
      blockingReason: "当前需要 human help / manual takeover，手机端不能继续主操作。",
      hint: "使用 Support Handoff 复制脱敏摘要，不要重复点击控制按钮。",
    },
    local_submit_failed: {
      nextAction: "刷新状态后再决定是否重试。",
      blockingReason: "本地提交失败，手机端没有收到 accepted/processing evidence。",
      hint: "若连续失败，请打开诊断并联系支持。",
    },
    missing_primary_journey_readiness: {
      nextAction: "等待后端补齐三步主路径摘要。",
      blockingReason: "缺少 mobile_primary_journey_gate / summary，不能说明目标、载荷确认和发车 gate。",
      hint: "页面只展示 blocked-by-design，不自行推断机器人状态。",
    },
    missing_support_handoff: {
      nextAction: "等待或请求后端提供支持交接摘要。",
      blockingReason: "缺少 phone_support_bundle，用户无法安全复现问题给支持人员。",
      hint: "Diagnostics 仍可尝试打开；主操作保持 fail closed。",
    },
    blocked_by_design: {
      nextAction: "按页面阻塞原因逐项处理。",
      blockingReason: "恢复决策是 Docker/local software proof，不是放行控制动作。",
      hint: "真实验收摘要缺失时只显示 not_proven 边界。",
    },
  };
  return copy[state] || copy.blocked_by_design;
}

function derivedRecoveryDecision(status, readiness, diagnostics) {
  const state = recoveryDecisionStateFromPhoneSafe(status, readiness);
  const copy = recoveryDecisionCopyForState(state);
  const support = status?.phone_support_bundle || readiness?.phone_support_bundle || diagnostics?.phone_support_bundle || {};
  const primary = status?.mobile_primary_journey_gate || readiness?.mobile_primary_journey_gate || {};
  const browser = mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics);
  return {
    missing: true,
    schema: "trashbot.mobile_recovery_decision_gate.v1",
    schema_version: 1,
    recovery_state: state,
    overall_status: "blocked",
    safe_to_control: false,
    next_action: copy.nextAction,
    blocking_reason: primary.safe_phone_copy || copy.blockingReason,
    support_entry: support.safe_copy || support.status_summary || "Diagnostics / Support Handoff 可用时只用于脱敏交接。",
    safe_phone_copy: "恢复决策 blocked-by-design：当前只从既有 phone-safe 字段派生，不证明真实验收或机器人完成。",
    recovery_hint: copy.hint,
    ack_semantics: ACK_PROCESSING_COPY,
    evidence_boundary: RECOVERY_DECISION_BOUNDARY,
    not_proven: notProvenList(browser.not_proven),
  };
}

function normalizeRecoveryDecision(value, fallback) {
  // 显式 summary 也只取白名单字段，防止后端误塞入成功语义或内部调试内容。
  const state = safeRecoveryText(
    value?.recovery_state || value?.status || value?.overall_status || fallback.recovery_state,
    fallback.recovery_state,
  );
  return {
    missing: value?.missing === true,
    schema: "trashbot.mobile_recovery_decision_gate.v1",
    schema_version: 1,
    recovery_state: state,
    overall_status: safeRecoveryText(value?.overall_status || value?.status, fallback.overall_status),
    safe_to_control: false,
    next_action: safeRecoveryText(value?.next_action || value?.recommended_next_action, fallback.next_action),
    blocking_reason: safeRecoveryText(value?.blocking_reason || value?.reason, fallback.blocking_reason),
    support_entry: safeRecoveryText(value?.support_entry || value?.support_handoff, fallback.support_entry),
    safe_phone_copy: safeRecoveryText(value?.safe_phone_copy || value?.safe_summary, fallback.safe_phone_copy),
    recovery_hint: safeRecoveryText(value?.recovery_hint || value?.retry_hint, fallback.recovery_hint),
    ack_semantics: safeRecoveryText(value?.ack_semantics, ACK_PROCESSING_COPY),
    evidence_boundary: safeRecoveryText(value?.evidence_boundary, RECOVERY_DECISION_BOUNDARY),
    not_proven: notProvenList(value?.not_proven || fallback.not_proven),
  };
}

function recoveryDecisionFromStatus(status, readiness, diagnostics) {
  const fallback = derivedRecoveryDecision(status, readiness, diagnostics);
  const provided = recoveryDecisionCandidate(status, readiness, diagnostics);
  return provided ? normalizeRecoveryDecision(provided, fallback) : fallback;
}

function routeTaskReviewCandidate(status, readiness, diagnostics) {
  // operator review 只接受 status/readiness/diagnostics 的摘要字段，不读取 raw artifact 或 backend filesystem。
  const diagnosticsReadiness = diagnostics && typeof diagnostics.phone_readiness === "object"
    ? diagnostics.phone_readiness
    : {};
  const candidates = [
    status?.route_task_rehearsal_operator_review,
    status?.route_task_rehearsal_operator_review_summary,
    status?.route_task_rehearsal_review_summary,
    status?.route_task_rehearsal_summary,
    readiness?.route_task_rehearsal_operator_review,
    readiness?.route_task_rehearsal_operator_review_summary,
    readiness?.route_task_rehearsal_review_summary,
    readiness?.route_task_rehearsal_summary,
    diagnostics?.route_task_rehearsal_operator_review,
    diagnostics?.route_task_rehearsal_operator_review_summary,
    diagnostics?.route_task_rehearsal_review_summary,
    diagnostics?.route_task_rehearsal_summary,
    diagnosticsReadiness.route_task_rehearsal_operator_review,
    diagnosticsReadiness.route_task_rehearsal_operator_review_summary,
    diagnosticsReadiness.route_task_rehearsal_review_summary,
    diagnosticsReadiness.route_task_rehearsal_summary,
  ];
  return candidates.find((value) => value && typeof value === "object") || null;
}

function routeTaskMismatchSummary(value) {
  // mismatch 只显示计数/摘要；原始 mismatch 列表和完整执行 bundle 不进入手机页面。
  if (value?.mismatch_summary || value?.mismatches_summary) {
    return safeOperatorReviewText(value.mismatch_summary || value.mismatches_summary, "mismatch_summary=not_proven");
  }
  if (typeof value?.mismatch_count === "number") {
    return `mismatch_count=${value.mismatch_count}`;
  }
  if (Array.isArray(value?.mismatches)) {
    return `mismatch_count=${value.mismatches.length} / raw details omitted`;
  }
  if (value?.crosscheck_status === "pass" || value?.crosscheck_status === "passed") {
    return "mismatch_count=0 / crosscheck pass";
  }
  return "mismatch_summary=not_proven";
}

function operatorReviewNotProvenList(value) {
  // 本 review 的 not_proven 必须固定保留 HIL、真实路线和终端动作缺口。
  const provided = notProvenList(value?.not_proven);
  const required = [
    "HIL",
    "真实路线运行",
    "真实 Nav2/fixed-route",
    "真实 dropoff completion",
    "真实 cancel completion",
    "delivery success",
  ];
  return Array.from(new Set([...provided, ...required])).slice(0, 12);
}

function routeTaskSafeCopyPayload(value) {
  // 复制路径只能使用 safe_copy；若后端没给 safe_copy，按钮保持 disabled。
  const safeCopy = value?.safe_copy;
  if (!safeCopy) {
    return null;
  }
  const source = typeof safeCopy === "object" ? safeCopy : { safe_phone_copy: safeCopy };
  return {
    schema: safeOperatorReviewText(source.schema, "trashbot.route_task_rehearsal_operator_review.safe_copy.v1"),
    schema_version: Number(source.schema_version || 1),
    source: safeOperatorReviewText(source.source, "mobile_web"),
    overall_status: safeOperatorReviewText(source.overall_status || value?.overall_status || value?.status, "blocked"),
    evidence_ref: safeOperatorReviewText(source.evidence_ref || value?.evidence_ref, "not_provided"),
    crosscheck_status: safeOperatorReviewText(source.crosscheck_status || value?.crosscheck_status, "not_proven"),
    hil_alignment_status: safeOperatorReviewText(
      source.hil_alignment_status || value?.hil_alignment_status || value?.hil_boundary,
      "not_proven",
    ),
    mismatch_summary: safeOperatorReviewText(source.mismatch_summary || routeTaskMismatchSummary(value), "mismatch_summary=not_proven"),
    next_rehearsal_decision: safeOperatorReviewText(
      source.next_rehearsal_decision || value?.next_rehearsal_decision,
      "rehearsal_blocked_until_real_route_or_hil_evidence",
    ),
    safe_phone_copy: safeOperatorReviewText(
      source.safe_phone_copy,
      "路线/任务排练复盘 safe_copy 只包含 phone-safe 摘要；不是 HIL、真实路线运行或 delivery success。",
    ),
    evidence_boundary: safeOperatorReviewText(
      source.evidence_boundary || value?.evidence_boundary,
      ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_BOUNDARY,
    ),
    not_proven: operatorReviewNotProvenList(source.not_proven ? source : value),
  };
}

function routeTaskReviewFromStatus(status, readiness, diagnostics) {
  const provided = routeTaskReviewCandidate(status, readiness, diagnostics) || {};
  const safeCopyPayload = routeTaskSafeCopyPayload(provided);
  return {
    missing: !Object.keys(provided).length,
    schema: "trashbot.route_task_rehearsal_operator_review.v1",
    schema_version: 1,
    overall_status: safeOperatorReviewText(provided.overall_status || provided.status, "blocked"),
    evidence_ref: safeOperatorReviewText(provided.evidence_ref || provided.evidence_reference, "not_provided"),
    crosscheck_hil_boundary: safeOperatorReviewText(
      provided.crosscheck_hil_boundary ||
        `crosscheck=${provided.crosscheck_status || "not_proven"} / HIL=${provided.hil_alignment_status || provided.hil_boundary || "not_proven"}`,
      "crosscheck=not_proven / HIL=not_proven",
    ),
    mismatch_summary: routeTaskMismatchSummary(provided),
    next_rehearsal_decision: safeOperatorReviewText(
      provided.next_rehearsal_decision || provided.next_decision || provided.next_step,
      "rehearsal_blocked_until_real_route_or_hil_evidence",
    ),
    safe_phone_copy: safeOperatorReviewText(
      provided.safe_phone_copy || provided.safe_summary,
      "路线/任务排练复盘缺少后端 phone-safe 摘要；这里只显示 blocked-by-design。",
    ),
    recovery_hint: safeOperatorReviewText(
      provided.recovery_hint || provided.retry_hint,
      "需要下一次真实路线/任务排练或 HIL 材料时，由 Robot/Autonomy 提供新的安全摘要。",
    ),
    evidence_boundary: safeOperatorReviewText(
      provided.evidence_boundary,
      ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_BOUNDARY,
    ),
    not_proven: operatorReviewNotProvenList(provided),
    safe_copy_payload: safeCopyPayload,
  };
}

function derivedMobileBrowserAcceptanceBundle(status, readiness, diagnostics) {
  // 缺显式 bundle 时，从既有 phone-safe gate 派生 blocked 摘要，不能自行证明真机或生产入口。
  const device = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, diagnostics);
  const cloud = cloudReadinessSummaryFromStatus(status, readiness);
  const offline = offlineResumeFromStatus(status, readiness);
  const commandSafety = commandSafetyFromReadiness(readiness);
  return {
    missing: true,
    schema: ACCEPTANCE_BUNDLE_SCHEMA,
    schema_version: 1,
    overall_status: "blocked",
    production_app_ready: false,
    safe_to_control: false,
    viewport: bundleFieldSummary(device.viewport_status || device.viewport_gate || device.viewport, "not_proven"),
    touch_target: bundleFieldSummary(device.touch_target_status || device.touch_gate || device.touch, "not_proven"),
    pwa_install_prompt: bundleFieldSummary(device.pwa_install_prompt_status || device.pwa_status, "not_proven"),
    offline_shell: bundleFieldSummary(offline.connection_state || device.offline_status || device.offline_gate, "not_proven"),
    diagnostics: bundleFieldSummary(device.diagnostics_status || device.diagnostics_gate, latestDiagnostics ? "phone_safe_visible" : "not_proven"),
    cloud_gate: bundleFieldSummary(cloud.overall_status || cloud.preflight_status, "blocked"),
    action_gate: bundleFieldSummary(commandSafety.global_block_reason, "blocked_by_design"),
    ack_semantics: ACK_PROCESSING_COPY,
    client_timestamp: new Date().toISOString(),
    safe_phone_copy: "浏览器验收包 blocked-by-design：当前只有 Docker/local 软件证明，没有真实手机设备/browser、production app 或真实 PWA install prompt。",
    recovery_hint: "请在真实手机浏览器和 production app 入口完成验收；在此之前 Start、Confirm、Cancel fail closed，Diagnostics 和 Support Handoff 可用。",
    evidence_boundary: MOBILE_BROWSER_ACCEPTANCE_BOUNDARY,
    not_proven: notProvenList(device.not_proven),
  };
}

function normalizeMobileBrowserAcceptanceBundle(value, fallback) {
  // 即使后端给了 bundle，前端也只保留白名单字段，复制包不带原始响应结构。
  return {
    missing: value?.missing === true,
    schema: ACCEPTANCE_BUNDLE_SCHEMA,
    schema_version: 1,
    overall_status: safeBundleText(value?.overall_status || value?.status || fallback.overall_status, "blocked"),
    production_app_ready: safeBundleBoolean(value?.production_app_ready),
    safe_to_control: safeBundleBoolean(value?.safe_to_control),
    viewport: bundleFieldSummary(value?.viewport, fallback.viewport),
    touch_target: bundleFieldSummary(value?.touch_target, fallback.touch_target),
    pwa_install_prompt: bundleFieldSummary(value?.pwa_install_prompt, fallback.pwa_install_prompt),
    offline_shell: bundleFieldSummary(value?.offline_shell, fallback.offline_shell),
    diagnostics: bundleFieldSummary(value?.diagnostics, fallback.diagnostics),
    cloud_gate: bundleFieldSummary(value?.cloud_gate, fallback.cloud_gate),
    action_gate: bundleFieldSummary(value?.action_gate, fallback.action_gate),
    ack_semantics: safeBundleText(value?.ack_semantics, ACK_PROCESSING_COPY),
    client_timestamp: new Date().toISOString(),
    safe_phone_copy: safeBundleText(value?.safe_phone_copy || value?.safe_summary, fallback.safe_phone_copy),
    recovery_hint: safeBundleText(value?.recovery_hint || value?.retry_hint, fallback.recovery_hint),
    evidence_boundary: safeBundleText(value?.evidence_boundary, MOBILE_BROWSER_ACCEPTANCE_BOUNDARY),
    not_proven: notProvenList(value?.not_proven || fallback.not_proven),
  };
}

function mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics) {
  const fallback = derivedMobileBrowserAcceptanceBundle(status, readiness, diagnostics);
  const provided = mobileBrowserAcceptanceBundleCandidate(status, readiness, diagnostics);
  return provided
    ? normalizeMobileBrowserAcceptanceBundle(provided, fallback)
    : fallback;
}

function cloudSummaryAllowsPrimaryActions(summary) {
  // Docker/local proof 不能自动开控制动作；只有后端显式 phone-safe 放行才允许继续。
  if (!summary || summary.missing === true) {
    return false;
  }
  if (summary.primary_actions_enabled === true || summary.safe_to_control === true) {
    return summary.overall_status !== "blocked" && summary.production_ready !== false;
  }
  return false;
}

function mobileDeviceAcceptanceAllowsPrimaryActions(summary) {
  // production app ready 必须和 primary action grant 同时出现；safe_to_control 是后端显式兼容放行。
  if (!summary || summary.missing === true) {
    return false;
  }
  if (summary.safe_to_control === true) {
    return summary.overall_status !== "blocked";
  }
  return summary.primary_actions_enabled === true &&
    summary.production_app_ready === true &&
    summary.overall_status !== "blocked";
}

function mobileBrowserAcceptanceBundleAllowsPrimaryActions(summary) {
  // 浏览器验收包是新增最终 gate；blocked-by-design 时不能被其他权限绕过。
  if (!summary || summary.missing === true) {
    return false;
  }
  return summary.safe_to_control === true &&
    summary.production_app_ready === true &&
    summary.overall_status !== "blocked";
}

function mobileDeviceHandoffSessionAllowsPrimaryActions(summary) {
  // 交接会话必须同时有真实设备、production app 和真实 install prompt 观察，避免 capture package 误放行动作。
  if (!summary || summary.missing === true) {
    return false;
  }
  return summary.safe_to_control === true &&
    summary.real_device_observed === true &&
    summary.production_app_ready === true &&
    summary.pwa_install_prompt_observed === true &&
    summary.overall_status !== "blocked";
}

function mobileRealDeviceReviewHandoffAllowsPrimaryActions(summary) {
  // review handoff 默认不是控制授权；只有后端显式清掉 not_proven 且标记控制批准时才可能继续。
  if (!summary || summary.missing === true) {
    return false;
  }
  const joined = Array.isArray(summary.not_proven) ? summary.not_proven.join(" ").toLowerCase() : "";
  return summary.safe_to_control === true &&
    summary.decision_status === "accepted_for_review" &&
    summary.review_status === "approved_for_control" &&
    !/真实手机|iphone|android|production app|pwa install prompt|hil|delivery|送达/.test(joined);
}

function mobileRealDeviceReviewExecutionAllowsPrimaryActions(summary) {
  // review execution 仍默认不是控制授权；真实设备/production/PWA 缺口存在时必须 fail closed。
  if (!summary || summary.missing === true) {
    return false;
  }
  const joined = Array.isArray(summary.not_proven) ? summary.not_proven.join(" ").toLowerCase() : "";
  return summary.safe_to_control === true &&
    summary.review_result === "approved_for_control" &&
    !/真实手机|iphone|android|production app|pwa install prompt|hil|delivery|送达/.test(joined);
}

function mobileRealDeviceRetestRequestAllowsPrimaryActions(summary) {
  // retest request 只是材料请求；缺真实设备、production app、PWA prompt 或 O5 外部材料时必须 fail closed。
  if (!summary || summary.missing === true) {
    return false;
  }
  const joined = Array.isArray(summary.not_proven) ? summary.not_proven.join(" ").toLowerCase() : "";
  const missing = Array.isArray(summary.missing_evidence_list) ? summary.missing_evidence_list.join(" ").toLowerCase() : "";
  return summary.safe_to_control === true &&
    summary.request_status === "approved_for_control" &&
    !/真实手机|iphone|android|production app|pwa install prompt|o5|objective 5|hil|delivery|送达/.test(joined) &&
    !/真实手机|iphone|android|production app|pwa|install prompt|objective 5|o5/.test(missing);
}

function operationLogFromStatus(status, readiness) {
  // 后端显式日志优先；没有日志时才从已知 phone-safe readiness 派生最小事件。
  const candidates = [
    status?.operation_log,
    status?.phone_operation_log,
    readiness?.operation_log,
    readiness?.phone_operation_log,
  ];
  const provided = candidates.find((value) => value && (Array.isArray(value) || typeof value === "object"));
  if (provided) {
    return { source: "operation_log", entries: normalizeOperationLogEntries(provided) };
  }
  return { source: "derived_phone_safe_fields", entries: deriveOperationLogEntries(status, readiness) };
}

function actionFeedbackFromStatus(status, readiness) {
  // 动作回执只消费 phone-safe metadata；没有后端字段时保留本地提交结果，不发明机器人执行状态。
  const candidates = [
    status?.mobile_action_receipt,
    status?.phone_action_feedback,
    readiness?.mobile_action_receipt,
    readiness?.phone_action_feedback,
  ];
  const provided = candidates.find((value) => value && typeof value === "object");
  return provided ? normalizeActionFeedback(provided, "status") : null;
}

function commandSafetyFromReadiness(readiness) {
  // 若 command_safety 缺失，前端必须 fail closed，不能用 UI 猜测状态。
  return readiness && typeof readiness.command_safety === "object" ? readiness.command_safety : {};
}

function taskFlowFromReadiness(status, readiness) {
  const taskFlow = status?.phone_task_flow_readiness || readiness?.phone_task_flow_readiness || {};
  return Array.isArray(taskFlow.steps) ? taskFlow.steps : [];
}

function taskFlowObjectFromStatus(status, readiness) {
  // destination 只能来自后端 phone-safe 任务摘要；缺字段时 Start 必须 fail closed。
  const direct = status?.phone_task_flow_readiness;
  if (direct && typeof direct === "object") {
    return direct;
  }
  const nested = readiness?.phone_task_flow_readiness;
  return nested && typeof nested === "object" ? nested : {};
}

function safeDestinationFromValue(value) {
  // 目的地只允许展示和提交短文本/安全摘要，避免把完整 artifact 或硬件细节传回控制口。
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (value && typeof value === "object") {
    return (
      safeDestinationFromValue(value.label) ||
      safeDestinationFromValue(value.name) ||
      safeDestinationFromValue(value.station) ||
      safeDestinationFromValue(value.destination) ||
      safeDestinationFromValue(value.safe_phone_copy)
    );
  }
  return "";
}

function destinationFromStatus(status, readiness) {
  const taskFlow = taskFlowObjectFromStatus(status, readiness);
  const steps = Array.isArray(taskFlow.steps) ? taskFlow.steps : [];
  const destinationStep = steps.find((step) => (
    step &&
    (step.step === "destination_confirmed" || step.id === "destination_confirmed") &&
    (step.confirmed === true || step.ready === true || step.state === "confirmed")
  ));
  const destination = (
    safeDestinationFromValue(taskFlow.destination_summary) ||
    safeDestinationFromValue(destinationStep?.destination_summary) ||
    safeDestinationFromValue(destinationStep?.destination) ||
    safeDestinationFromValue(destinationStep?.safe_phone_copy) ||
    safeDestinationFromValue(readiness?.destination) ||
    safeDestinationFromValue(status?.destination)
  );
  const ready = Boolean(destination) && (
    taskFlow.destination_confirmed === true ||
    taskFlow.destination_ready === true ||
    destinationStep !== undefined ||
    Boolean(taskFlow.destination_summary || readiness?.destination || status?.destination)
  );
  return {
    value: destination,
    ready,
    source: destinationStep ? "phone_task_flow_readiness.steps.destination_confirmed" : "phone_safe_destination",
  };
}

function loadConfirmationChecked() {
  const checkbox = $("trashLoadedCheckbox");
  return checkbox ? checkbox.checked === true : false;
}

function operationLogReadyForPrimaryJourney(status, readiness) {
  // 主路径要能复现问题，所以只把显式 operation_log / phone_operation_log 当作可追溯证据。
  const hasExplicitLog = Boolean(status?.operation_log || status?.phone_operation_log ||
    readiness?.operation_log || readiness?.phone_operation_log);
  const log = operationLogFromStatus(status, readiness);
  return {
    ready: hasExplicitLog && log.entries.length > 0,
    copy: hasExplicitLog
      ? `operation log 可用：${log.entries.length} 条 phone-safe 事件。`
      : "缺少 operation log / phone_operation_log，Start 安全关闭。",
  };
}

function actionFeedbackReadyForPrimaryJourney(status, readiness) {
  // 回执 gate 防止 pending ACK 或本地失败被用户误读成可以继续发车。
  const feedback = actionFeedbackFromStatus(status, readiness);
  if (!feedback) {
    return { ready: false, copy: "缺少 action feedback / receipt 摘要，Start 安全关闭。" };
  }
  const state = String(feedback.state || "").toLowerCase();
  const pending = ["submitted", "waiting_ack", "accepted_or_processing"].includes(state);
  const blocked = ["failed", "blocked", "rejected", "local_submit_failed"].includes(state);
  if (pending) {
    return { ready: false, copy: "存在 pending ACK / accepted-processing 回执，Start 安全关闭。" };
  }
  if (blocked) {
    return { ready: false, copy: `最近动作回执为 ${feedback.state}，请先按恢复建议处理。` };
  }
  return { ready: true, copy: `动作回执安全：${feedback.state}。` };
}

function actionFeedbackBlocksTerminalAction(status, readiness) {
  // Confirm/Cancel 也不能在等待 ACK 或失败未处理时重复提交终端动作。
  const feedback = actionFeedbackFromStatus(status, readiness) || latestActionFeedback;
  if (!feedback) {
    return null;
  }
  const state = String(feedback.state || "").toLowerCase();
  if (["submitted", "waiting_ack", "accepted_or_processing"].includes(state)) {
    return "存在 pending ACK / accepted-processing 回执，终端动作确认 fail closed。";
  }
  if (["failed", "blocked", "rejected", "local_submit_failed"].includes(state)) {
    return `最近动作回执为 ${feedback.state}，请先按恢复建议处理。`;
  }
  return null;
}

function terminalActionGateFromStatus(status, actionName) {
  const readiness = readinessFromStatus(status);
  const commandSafety = commandSafetyFromReadiness(readiness);
  const actions = commandSafety.actions && typeof commandSafety.actions === "object" ? commandSafety.actions : {};
  const actionGate = actions[actionName] && typeof actions[actionName] === "object" ? actions[actionName] : {};
  const cloudSummary = cloudReadinessSummaryFromStatus(status, readiness);
  const mobileDeviceAcceptance = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics);
  const mobileBrowserAcceptance = mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics);
  const mobileDeviceHandoff = mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewHandoff = mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewExecution = mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceRetestRequest = mobileRealDeviceRetestRequestFromStatus(status, readiness, latestDiagnostics);
  const offline = offlineResumeFromStatus(status, readiness);
  const permitted = actionPermission(status, readiness, actionName);
  const hasCommandSafety = commandSafety.schema === "trashbot.command_safety.v1" || Boolean(commandSafety.actions);
  const raw = `${readiness?.primary_state || ""} ${readiness?.next_action || ""} ${readiness?.support_level || ""} ${commandSafety?.global_block_reason || ""}`.toLowerCase();
  const connection = `${offline.connection_state || status?.connection_state || ""}`.toLowerCase();
  const blockers = [];

  if (!["confirm_dropoff", "cancel"].includes(actionName)) {
    blockers.push("该 gate 只处理 Confirm Dropoff / Cancel。");
  }
  if (!hasCommandSafety) {
    blockers.push("缺少 command_safety，终端动作确认 fail closed。");
  }
  if (actionGate.enabled !== true) {
    blockers.push(safeTerminalActionText(actionGate.blocking_reason || commandSafety.global_block_reason, "action disabled。"));
  }
  if (permitted !== true) {
    blockers.push(`旧权限 ${ACTIONS[actionName]?.permission || "can_*"} 未放行。`);
  }
  if (!cloudSummaryAllowsPrimaryActions(cloudSummary)) {
    blockers.push("cloud readiness 未显式放行终端动作。");
  }
  if (!mobileDeviceAcceptanceAllowsPrimaryActions(mobileDeviceAcceptance)) {
    blockers.push("device readiness 未显式放行终端动作。");
  }
  if (!mobileBrowserAcceptanceBundleAllowsPrimaryActions(mobileBrowserAcceptance)) {
    blockers.push("browser acceptance bundle 未显式放行终端动作。");
  }
  if (!mobileDeviceHandoffSessionAllowsPrimaryActions(mobileDeviceHandoff)) {
    blockers.push("mobile device handoff session 未显式放行终端动作。");
  }
  if (!mobileRealDeviceReviewHandoffAllowsPrimaryActions(mobileRealDeviceReviewHandoff)) {
    blockers.push("mobile real device review handoff 未显式放行终端动作。");
  }
  if (!mobileRealDeviceReviewExecutionAllowsPrimaryActions(mobileRealDeviceReviewExecution)) {
    blockers.push("mobile real device review execution 未显式放行终端动作。");
  }
  if (!mobileRealDeviceRetestRequestAllowsPrimaryActions(mobileRealDeviceRetestRequest)) {
    blockers.push("mobile real device retest request 未显式放行终端动作。");
  }
  if (connection && connection !== "online" || /offline|stale|unreachable|disconnect|network/.test(raw)) {
    blockers.push("状态 offline/stale/unreachable，终端动作确认 fail closed。");
  }
  if (/waiting_ack|pending_ack|ack_pending/.test(raw)) {
    blockers.push("当前仍在等待 ACK，终端动作确认 fail closed。");
  }
  if (/manual_takeover|human_help|support_required/.test(raw)) {
    blockers.push("当前需要人工接管或支持处理，终端动作确认 fail closed。");
  }
  if (/blocked/.test(raw) || status?.overall_status === "blocked") {
    blockers.push("当前 blocked state 未解除，终端动作确认 fail closed。");
  }
  const feedbackBlocker = actionFeedbackBlocksTerminalAction(status, readiness);
  if (feedbackBlocker) {
    blockers.push(feedbackBlocker);
  }

  return {
    enabled: blockers.length === 0,
    blockedReason: blockers.join("；") || "可以进入终端动作二次确认。",
    action: actionName,
    actionCopy: actionLabel(actionName),
    riskCopy: actionName === "cancel"
      ? "取消任务可能停止当前用户流程；确认后仍只得到 accepted/processing evidence。"
      : "确认投放会进入终端投放确认流程；确认后仍不能当作 dropoff success。",
    safePhoneCopy: `${actionLabel(actionName)} 需要用户显式确认；提交后只表示 accepted/processing evidence。`,
    ackSemantics: safeTerminalActionText(commandSafety.ack_semantics, ACK_PROCESSING_COPY),
    evidenceBoundary: TERMINAL_ACTION_BOUNDARY,
    notProven: [
      "真实手机设备/browser",
      "production app",
      "真实 PWA install prompt",
      "真实云/4G",
      "Nav2/fixed-route",
      "WAVE ROVER",
      "HIL",
      "真实 dropoff completion",
      "真实 cancel completion",
      "真实 delivery",
    ],
  };
}

function journeyStateBlocksStart(readiness, commandSafety) {
  // 后端 primary_state 是用户旅程的粗粒度状态；这些状态都不能被按钮层绕过。
  const raw = `${readiness?.primary_state || ""} ${readiness?.next_action || ""} ${readiness?.support_level || ""} ${commandSafety?.global_block_reason || ""}`.toLowerCase();
  const blockers = [];
  if (/offline|disconnect|unreachable|network/.test(raw)) {
    blockers.push("当前状态包含 offline/unreachable，Start 安全关闭。");
  }
  if (/waiting_ack|pending_ack|ack_pending/.test(raw)) {
    blockers.push("当前仍在等待 ACK，Start 安全关闭。");
  }
  if (/manual_takeover|human_help|support_required/.test(raw)) {
    blockers.push("当前需要人工接管或支持处理，Start 安全关闭。");
  }
  return blockers;
}

function startGateFromStatus(status) {
  const readiness = readinessFromStatus(status);
  const commandSafety = commandSafetyFromReadiness(readiness);
  const actions = commandSafety.actions && typeof commandSafety.actions === "object" ? commandSafety.actions : {};
  const startGate = actions.start && typeof actions.start === "object" ? actions.start : {};
  const destination = destinationFromStatus(status, readiness);
  const cloudSummary = cloudReadinessSummaryFromStatus(status, readiness);
  const mobileDeviceAcceptance = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics);
  const mobileBrowserAcceptance = mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics);
  const mobileDeviceHandoff = mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewHandoff = mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewExecution = mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceRetestRequest = mobileRealDeviceRetestRequestFromStatus(status, readiness, latestDiagnostics);
  const operationLogGate = operationLogReadyForPrimaryJourney(status, readiness);
  const actionFeedbackGate = actionFeedbackReadyForPrimaryJourney(status, readiness);
  const permitted = actionPermission(status, readiness, "start");
  const hasCommandSafety = commandSafety.schema === "trashbot.command_safety.v1" || Boolean(commandSafety.actions);
  const loadConfirmed = loadConfirmationChecked();
  const blockers = [];

  if (!hasCommandSafety) {
    blockers.push("缺少 command_safety，Start 安全关闭。");
  }
  if (startGate.enabled !== true) {
    blockers.push(safeText(startGate.blocking_reason || commandSafety.global_block_reason, "command_safety 未放行。"));
  }
  if (permitted !== true) {
    blockers.push("旧权限 can_collect 未放行。");
  }
  if (!destination.ready) {
    blockers.push("缺少后端 phone-safe 目标垃圾站。");
  }
  if (!loadConfirmed) {
    blockers.push("请先显式确认垃圾已放入。");
  }
  if (!cloudSummaryAllowsPrimaryActions(cloudSummary)) {
    blockers.push("cloud readiness 未显式放行主操作。");
  }
  if (!mobileDeviceAcceptanceAllowsPrimaryActions(mobileDeviceAcceptance)) {
    blockers.push("device readiness 未显式放行主操作。");
  }
  if (!mobileBrowserAcceptanceBundleAllowsPrimaryActions(mobileBrowserAcceptance)) {
    blockers.push("browser acceptance bundle 未显式放行主操作。");
  }
  if (!mobileDeviceHandoffSessionAllowsPrimaryActions(mobileDeviceHandoff)) {
    blockers.push("mobile device handoff session 未显式放行主操作。");
  }
  if (!mobileRealDeviceReviewHandoffAllowsPrimaryActions(mobileRealDeviceReviewHandoff)) {
    blockers.push("mobile real device review handoff 未显式放行主操作。");
  }
  if (!mobileRealDeviceReviewExecutionAllowsPrimaryActions(mobileRealDeviceReviewExecution)) {
    blockers.push("mobile real device review execution 未显式放行主操作。");
  }
  if (!mobileRealDeviceRetestRequestAllowsPrimaryActions(mobileRealDeviceRetestRequest)) {
    blockers.push("mobile real device retest request 未显式放行主操作。");
  }
  if (!operationLogGate.ready) {
    blockers.push(operationLogGate.copy);
  }
  if (!actionFeedbackGate.ready) {
    blockers.push(actionFeedbackGate.copy);
  }
  blockers.push(...journeyStateBlocksStart(readiness, commandSafety));

  return {
    destination: destination.value,
    destinationReady: destination.ready,
    loadConfirmed,
    startEnabled: blockers.length === 0,
    blockedReason: blockers.join("；") || "可以提交发车请求。",
    commandSafetyAck: safeText(commandSafety.ack_semantics, "ACK 只表示指令受理或处理中，不代表送达成功。"),
    evidenceBoundary: PRIMARY_JOURNEY_BOUNDARY,
    destinationSource: destination.source,
    operationLogReady: operationLogGate.ready,
    actionFeedbackReady: actionFeedbackGate.ready,
  };
}

function renderStartConfirmation(status) {
  latestStartGate = startGateFromStatus(status);
  const badge = $("destinationGateBadge");
  $("destinationSummary").textContent = latestStartGate.destination || "等待后端提供垃圾站。";
  $("startBlockReason").textContent = latestStartGate.blockedReason;
  $("startPayloadBoundary").textContent = `${latestStartGate.evidenceBoundary}；${latestStartGate.commandSafetyAck}`;
  badge.className = "gate-badge";
  if (latestStartGate.destinationReady) {
    badge.classList.add("gate-ready");
    badge.textContent = "目的地已确认";
  } else {
    badge.classList.add("gate-blocked");
    badge.textContent = "未确认目的地";
  }
}

function renderPrimaryJourney(status) {
  // 首屏三步主路径复用同一套 Start gate，避免 summary 与实际按钮状态分叉。
  const gate = startGateFromStatus(status);
  const steps = [
    {
      title: "目标垃圾站",
      ready: gate.destinationReady,
      copy: gate.destinationReady
        ? `目标：${gate.destination}。来源：${gate.destinationSource}。`
        : "缺少后端 phone-safe 目标垃圾站。",
    },
    {
      title: "已放入垃圾确认",
      ready: gate.loadConfirmed,
      copy: gate.loadConfirmed
        ? "用户已手动确认垃圾已放入；这不是自动载荷检测。"
        : "需要用户手动勾选“垃圾已放入”。",
    },
    {
      title: "发车安全 gate",
      ready: gate.startEnabled,
      copy: gate.startEnabled
        ? "command_safety、旧权限、云、设备、浏览器、日志和回执均已放行。"
        : gate.blockedReason,
    },
  ];
  const badge = $("primaryJourneyBadge");
  const list = $("primaryJourneySteps");
  list.textContent = "";
  steps.forEach((step, index) => {
    const item = document.createElement("li");
    const marker = document.createElement("span");
    const body = document.createElement("span");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    item.className = step.ready ? "ready" : "blocked";
    marker.className = "step-index";
    marker.textContent = String(index + 1);
    title.textContent = step.title;
    copy.textContent = step.copy;
    body.append(title, copy);
    item.append(marker, body);
    list.appendChild(item);
  });
  badge.className = "gate-badge";
  badge.classList.add(gate.startEnabled ? "gate-ready" : "gate-blocked");
  badge.textContent = gate.startEnabled ? "可提交" : "fail closed";
  $("primaryJourneyCopy").textContent = gate.startEnabled
    ? "三步主路径已满足；提交后仍只等待 accepted/processing evidence。"
    : "三步主路径缺少安全条件，Start Delivery 保持关闭。";
  $("primaryJourneyBoundary").textContent = PRIMARY_JOURNEY_BOUNDARY;
}

function renderRecoveryDecision(status) {
  const readiness = readinessFromStatus(status);
  const decision = recoveryDecisionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("recoveryDecisionBadge");
  const ready = decision.overall_status === "ready" && decision.safe_to_control === true;

  badge.className = "gate-badge";
  badge.classList.add(ready ? "gate-ready" : (decision.missing ? "gate-waiting" : "gate-blocked"));
  badge.textContent = decision.missing ? "安全派生" : (ready ? "恢复允许" : "恢复阻塞");
  $("recoveryDecisionCopy").textContent = decision.safe_phone_copy;
  $("recoveryDecisionState").textContent = decision.recovery_state;
  $("recoveryDecisionNextAction").textContent = decision.next_action;
  $("recoveryDecisionBlockingReason").textContent = decision.blocking_reason;
  $("recoveryDecisionSupportEntry").textContent = decision.support_entry;
  $("recoveryDecisionAck").textContent = decision.ack_semantics;
  $("recoveryDecisionBoundary").textContent = decision.evidence_boundary;
  $("recoveryDecisionHint").textContent = decision.recovery_hint;
  $("recoveryDecisionNotProven").textContent = decision.not_proven.join("、");
}

function renderRouteTaskReview(status) {
  const readiness = readinessFromStatus(status);
  const review = routeTaskReviewFromStatus(status, readiness, latestDiagnostics);
  const badge = $("routeTaskReviewBadge");
  const copyButton = $("copyRouteTaskReviewButton");
  latestRouteTaskReview = review;

  badge.className = "gate-badge";
  badge.classList.add(review.missing ? "gate-waiting" : "gate-blocked");
  badge.textContent = review.missing ? "等待 review" : "software proof";
  $("routeTaskReviewCopy").textContent = review.safe_phone_copy;
  $("routeTaskReviewOverall").textContent = review.overall_status;
  $("routeTaskReviewEvidenceRef").textContent = review.evidence_ref;
  $("routeTaskReviewCrosscheckHil").textContent = review.crosscheck_hil_boundary;
  $("routeTaskReviewMismatch").textContent = review.mismatch_summary;
  $("routeTaskReviewNextDecision").textContent = review.next_rehearsal_decision;
  $("routeTaskReviewBoundary").textContent = review.evidence_boundary;
  $("routeTaskReviewNotProven").textContent = review.not_proven.join("、");
  if (review.safe_copy_payload) {
    $("routeTaskReviewSafeCopy").textContent = JSON.stringify(review.safe_copy_payload, null, 2);
    $("routeTaskReviewCopyStatus").textContent = "safe_copy 可复制；内容仅限后端白名单摘要字段。";
    copyButton.disabled = false;
  } else {
    $("routeTaskReviewSafeCopy").textContent = "blocked copy unavailable";
    $("routeTaskReviewCopyStatus").textContent = "blocked copy unavailable";
    copyButton.disabled = true;
  }
}

function setBadge(state, copy) {
  const badge = $("connectionBadge");
  badge.className = "badge";
  if (state === "ready") {
    badge.classList.add("badge-ready");
  } else if (state === "blocked" || state === "offline") {
    badge.classList.add("badge-blocked");
  } else {
    badge.classList.add("badge-waiting");
  }
  badge.textContent = copy;
}

function renderReadiness(status) {
  const readiness = readinessFromStatus(status);
  const state = safeText(readiness.primary_state || status?.state, "waiting");
  const canContinue = readiness.can_continue === true;
  $("readinessTitle").textContent = canContinue ? "可以继续手机流程" : "当前需要等待或处理";
  $("safePhoneCopy").textContent = safeText(readiness.safe_phone_copy || status?.phone_copy);
  $("recoveryHint").textContent = safeText(readiness.recovery_hint, "等待状态刷新或打开诊断。");
  $("boundaryCopy").textContent = safeText(
    readiness.evidence_boundary,
    "software_proof_docker_mobile_web_entrypoint_gate",
  );
  $("nextAction").textContent = safeText(readiness.next_action, "wait");
  $("supportLevel").textContent = safeText(readiness.support_level, "support_required");
  setBadge(canContinue ? "ready" : "blocked", state);
}

function renderTaskFlow(status) {
  const readiness = readinessFromStatus(status);
  const steps = taskFlowFromReadiness(status, readiness);
  const list = $("taskFlowList");
  list.textContent = "";
  if (!steps.length) {
    const item = document.createElement("li");
    item.textContent = "后端尚未返回任务步骤，主操作保持安全 gate 控制。";
    list.appendChild(item);
    return;
  }
  steps.forEach((step) => {
    const item = document.createElement("li");
    const label = safeText(step.label || step.step, "任务步骤");
    const copy = safeText(step.safe_phone_copy || step.status || step.blocking_reason, "等待后端说明");
    item.textContent = `${label}：${copy}`;
    if (step.current === true || step.state === "current") {
      item.classList.add("current");
    }
    list.appendChild(item);
  });
}

function actionPermission(status, readiness, actionName) {
  const action = ACTIONS[actionName];
  const permissions = readiness.action_permissions || {};
  // 旧权限字段仍是后端 gate 输入；command_safety 允许也不能绕过旧权限。
  if (typeof permissions[action.permission] === "boolean") {
    return permissions[action.permission];
  }
  return status?.[action.permission] === true;
}

function renderCommandSafety(status) {
  const readiness = readinessFromStatus(status);
  const commandSafety = commandSafetyFromReadiness(readiness);
  const cloudSummary = cloudReadinessSummaryFromStatus(status, readiness);
  const mobileDeviceAcceptance = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics);
  const mobileBrowserAcceptance = mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics);
  const mobileDeviceHandoff = mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewHandoff = mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewExecution = mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics);
  const cloudAllowsPrimaryActions = cloudSummaryAllowsPrimaryActions(cloudSummary);
  const mobileDeviceAllowsPrimaryActions = mobileDeviceAcceptanceAllowsPrimaryActions(mobileDeviceAcceptance);
  const browserBundleAllowsPrimaryActions = mobileBrowserAcceptanceBundleAllowsPrimaryActions(mobileBrowserAcceptance);
  const handoffSessionAllowsPrimaryActions = mobileDeviceHandoffSessionAllowsPrimaryActions(mobileDeviceHandoff);
  const reviewHandoffAllowsPrimaryActions = mobileRealDeviceReviewHandoffAllowsPrimaryActions(mobileRealDeviceReviewHandoff);
  const reviewExecutionAllowsPrimaryActions = mobileRealDeviceReviewExecutionAllowsPrimaryActions(mobileRealDeviceReviewExecution);
  const retestRequestAllowsPrimaryActions = mobileRealDeviceRetestRequestAllowsPrimaryActions(mobileRealDeviceRetestRequest);
  const actions = commandSafety.actions && typeof commandSafety.actions === "object" ? commandSafety.actions : {};
  $("commandSafetyCopy").textContent = safeText(commandSafety.safe_phone_copy, "主操作保持禁用。");
  $("ackCopy").textContent = safeText(
    commandSafety.ack_semantics,
    "ACK 只表示指令受理或处理中，不代表送达成功。",
  );

  const reasons = $("actionReasons");
  reasons.textContent = "";
  Object.keys(ACTIONS).forEach((name) => {
    const actionMeta = ACTIONS[name];
    const button = $(actionMeta.buttonId);
    const actionGate = actions[name] && typeof actions[name] === "object" ? actions[name] : {};
    const permitted = actionPermission(status, readiness, name);
    const startGate = name === "start" ? latestStartGate : null;
    const terminalGate = ["confirm_dropoff", "cancel"].includes(name)
      ? terminalActionGateFromStatus(status, name)
      : null;
    const enabled = actionGate.enabled === true && permitted === true &&
      cloudAllowsPrimaryActions &&
      mobileDeviceAllowsPrimaryActions &&
      browserBundleAllowsPrimaryActions &&
      handoffSessionAllowsPrimaryActions &&
      reviewHandoffAllowsPrimaryActions &&
      reviewExecutionAllowsPrimaryActions &&
      retestRequestAllowsPrimaryActions &&
      (startGate ? startGate.startEnabled : true) &&
      (terminalGate ? terminalGate.enabled : true);
    // blocked、离线、等待 ACK、人工接管都会通过 command_safety 关闭按钮。
    button.disabled = !enabled;
    button.dataset.endpoint = ENDPOINTS[name];
    button.title = safeText(actionGate.safe_phone_copy, "后端 gate 未放行。");

    const item = document.createElement("li");
    const reason = name === "start" && startGate
      ? startGate.blockedReason
      : (terminalGate
        ? terminalGate.blockedReason
        : safeText(actionGate.blocking_reason || commandSafety.global_block_reason, "blocked"));
    const cloudReason = cloudAllowsPrimaryActions ? "" : "；云中转摘要未放行主操作。";
    const mobileDeviceReason = mobileDeviceAllowsPrimaryActions ? "" : "；手机验收准备未放行主操作。";
    const browserBundleReason = browserBundleAllowsPrimaryActions ? "" : "；浏览器验收包未放行主操作。";
    const handoffReason = handoffSessionAllowsPrimaryActions ? "" : "；真实手机验收交接会话未放行主操作。";
    const reviewHandoffReason = reviewHandoffAllowsPrimaryActions ? "" : "；真实设备 review handoff 未放行主操作。";
    const reviewExecutionReason = reviewExecutionAllowsPrimaryActions ? "" : "；真实设备 review execution 未放行主操作。";
    const retestRequestReason = retestRequestAllowsPrimaryActions ? "" : "；真实设备 retest request 未放行主操作。";
    item.textContent = `${actionMeta.label}：${enabled ? "可操作" : `${reason}${cloudReason}${mobileDeviceReason}${browserBundleReason}${handoffReason}${reviewHandoffReason}${reviewExecutionReason}${retestRequestReason}`}`;
    reasons.appendChild(item);
  });

  const diagnosticsAction = actions.diagnostics || {};
  $("diagnosticsButton").disabled = diagnosticsAction.enabled === false ? false : false;
  $("supportButton").disabled = false;
}

function renderOfflineResume(status) {
  const readiness = readinessFromStatus(status);
  const offlineResume = offlineResumeFromStatus(status, readiness);
  $("offlineCopy").textContent = safeText(offlineResume.safe_phone_copy, "离线时主操作保持禁用。");
  $("offlineHint").textContent = safeText(offlineResume.recovery_hint, "恢复连接后刷新状态。");
}

function renderVoicePrompt(status) {
  const readiness = readinessFromStatus(status);
  const voicePrompt = voicePromptFromStatus(status, readiness);
  $("voiceCopy").textContent = safeText(
    voicePrompt.safe_phone_copy || voicePrompt.current_prompt,
    "提示词 readiness 不是实际播放证明。",
  );
  $("voiceBoundary").textContent = safeText(
    voicePrompt.evidence_boundary || voicePrompt.ack_semantics,
    "本地软件证明不代表真实喇叭或 TTS 播放。",
  );
}

function normalizeOperationLogEntries(value) {
  // 只识别显式事件数组或对象内 events/items；对象本身不作为原始 JSON 展示。
  const events = Array.isArray(value)
    ? value
    : (Array.isArray(value.events) ? value.events : value.items);
  if (!Array.isArray(events)) {
    return [];
  }
  return events.slice(0, 6).map((event, index) => ({
    title: safeText(event?.title || event?.label || event?.event_type || event?.state, `事件 ${index + 1}`),
    copy: safeText(event?.safe_phone_copy || event?.summary || event?.status_copy, "等待后端提供事件说明。"),
    hint: safeText(event?.recovery_hint || event?.next_step || event?.support_hint, "按页面提示继续或联系支持。"),
    timestamp: safeText(event?.time || event?.timestamp || event?.generated_at, "最近"),
  }));
}

function pushDerivedEvent(entries, title, source) {
  if (!source || typeof source !== "object") {
    return;
  }
  const copy = source.safe_phone_copy || source.status_summary || source.safe_copy || source.current_prompt;
  const hint = source.recovery_hint || source.next_action || source.ack_semantics || source.support_level;
  // 派生事件只能来自 phone-safe 字段；缺少可读文案时跳过，避免前端自行编造状态。
  if (!copy && !hint) {
    return;
  }
  entries.push({
    title,
    copy: safeText(copy, "等待后端提供事件说明。"),
    hint: safeText(hint, "按页面提示继续或联系支持。"),
    timestamp: safeText(source.generated_at || source.updated_at, "当前"),
  });
}

function deriveOperationLogEntries(status, readiness) {
  const entries = [];
  pushDerivedEvent(entries, "手机就绪", readiness);
  pushDerivedEvent(entries, "操作安全", commandSafetyFromReadiness(readiness));
  pushDerivedEvent(entries, "任务流程", taskFlowObjectFromStatus(status, readiness));
  pushDerivedEvent(entries, "云中转状态", cloudReadinessSummaryFromStatus(status, readiness));
  pushDerivedEvent(entries, "浏览器验收包", mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "离线恢复", offlineResumeFromStatus(status, readiness));
  pushDerivedEvent(entries, "支持交接", status?.phone_support_bundle || readiness?.phone_support_bundle);
  pushDerivedEvent(entries, "语音提示", voicePromptFromStatus(status, readiness));
  pushDerivedEvent(entries, "手机验收准备", mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实手机验收交接会话", mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "PWA 安装提示证据", mobilePwaInstallPromptEvidenceFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备验收材料", mobileRealDeviceEvidencePackageFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备验收决策", mobileRealDeviceAcceptanceDecisionFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备评审交接", mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备评审执行", mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备复测请求", mobileRealDeviceRetestRequestFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "真实设备现场试跑包", mobileRealDeviceFieldTrialPackageFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "现场试跑证据复核", mobileRealDeviceFieldTrialReviewFromStatus(status, readiness, latestDiagnostics));
  pushDerivedEvent(entries, "现场试跑执行清单", mobileRealDeviceFieldTrialRunbookExecutionFromStatus(status, readiness, latestDiagnostics));
  return entries.slice(0, 8);
}

function renderCloudReadiness(status) {
  const readiness = readinessFromStatus(status);
  const summary = cloudReadinessSummaryFromStatus(status, readiness);
  const badge = $("cloudReadinessBadge");
  const allowed = cloudSummaryAllowsPrimaryActions(summary);
  const overall = safeText(summary.overall_status || summary.state, "waiting_summary");

  badge.className = "gate-badge";
  badge.classList.add(allowed ? "gate-ready" : (summary.missing ? "gate-waiting" : "gate-blocked"));
  badge.textContent = summary.missing ? "等待摘要" : (allowed ? "摘要允许" : "摘要阻塞");
  $("cloudReadinessCopy").textContent = safeText(summary.safe_phone_copy || summary.safe_summary);
  $("cloudPreflightState").textContent = safeText(summary.preflight_status || summary.cloud_preflight_status || overall);
  $("cloudDbQueueState").textContent = safeText(summary.db_queue_status || summary.cloud_db_queue_status || summary.queue_status);
  $("cloudProductionReady").textContent = summary.production_ready === true
    ? "后端声明可用"
    : "production_ready=false / 未证明";
  $("cloudAckSemantics").textContent = safeText(summary.ack_semantics, ACK_PROCESSING_COPY);
  $("cloudRecoveryHint").textContent = safeText(
    summary.recovery_hint || summary.retry_hint,
    "等待 cloud readiness 摘要；主操作保持禁用。",
  );
  $("cloudEvidenceBoundary").textContent = safeText(summary.evidence_boundary, CLOUD_READINESS_BOUNDARY);
}

function renderMobileDeviceAcceptance(status) {
  const readiness = readinessFromStatus(status);
  const summary = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileDeviceAcceptanceBadge");
  const allowed = mobileDeviceAcceptanceAllowsPrimaryActions(summary);
  const viewport = safeText(summary.viewport_status || summary.viewport_gate || summary.viewport, "not_proven");
  const touch = safeText(summary.touch_target_status || summary.touch_gate || summary.touch, "not_proven");
  const pwa = safeText(summary.pwa_install_prompt_status || summary.pwa_status || summary.pwa_installability, "not_proven");
  const offline = safeText(summary.offline_status || summary.offline_gate, "not_proven");
  const diagnostics = safeText(summary.diagnostics_status || summary.diagnostics_gate, "not_proven");
  const cloud = safeText(summary.cloud_gate_status || summary.cloud_status, "not_proven");

  badge.className = "gate-badge";
  badge.classList.add(allowed ? "gate-ready" : (summary.missing ? "gate-waiting" : "gate-blocked"));
  badge.textContent = allowed ? "验收允许" : (summary.missing ? "等待摘要" : "验收阻塞");
  $("mobileDeviceAcceptanceCopy").textContent = safeText(summary.safe_phone_copy || summary.safe_summary);
  $("mobileDeviceViewportTouch").textContent = `viewport=${viewport} / touch=${touch}`;
  $("mobileDevicePwaOffline").textContent = `PWA=${pwa} / offline=${offline}`;
  $("mobileDeviceDiagnosticsCloud").textContent = `diagnostics=${diagnostics} / cloud=${cloud}`;
  $("mobileDeviceProductionApp").textContent = summary.production_app_ready === true
    ? "production_app_ready=true"
    : "production_app_ready=false / 未证明";
  $("mobileDeviceAckSemantics").textContent = safeText(summary.ack_semantics, ACK_PROCESSING_COPY);
  $("mobileDeviceEvidenceBoundary").textContent = safeText(summary.evidence_boundary, MOBILE_DEVICE_ACCEPTANCE_BOUNDARY);
  $("mobileDeviceRecoveryHint").textContent = safeText(
    summary.recovery_hint || summary.retry_hint,
    "缺少真实手机验收摘要时，Start、Confirm、Cancel 保持禁用。",
  );
}

function bundleCopyPayload(bundle) {
  // 复制内容只包含验收白名单；这是支持交接和单测共用的稳定 contract。
  return {
    schema: bundle.schema,
    schema_version: bundle.schema_version,
    overall_status: bundle.overall_status,
    production_app_ready: bundle.production_app_ready,
    safe_to_control: bundle.safe_to_control,
    viewport: bundle.viewport,
    touch_target: bundle.touch_target,
    pwa_install_prompt: bundle.pwa_install_prompt,
    offline_shell: bundle.offline_shell,
    diagnostics: bundle.diagnostics,
    cloud_gate: bundle.cloud_gate,
    action_gate: bundle.action_gate,
    ack_semantics: bundle.ack_semantics,
    client_timestamp: bundle.client_timestamp,
    safe_phone_copy: bundle.safe_phone_copy,
    recovery_hint: bundle.recovery_hint,
    evidence_boundary: bundle.evidence_boundary,
    not_proven: bundle.not_proven,
  };
}

function deviceEvidencePackageCopyPayload(packagePayload) {
  // 复制包固定为白名单 schema，过滤凭证、机器人原始字段和完整证据文件。
  return {
    schema: DEVICE_EVIDENCE_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    capture_schema: packagePayload.schema,
    capture_summary_schema: packagePayload.capture_summary_schema,
    overall_status: packagePayload.overall_status,
    viewport: packagePayload.viewport,
    touch_target: packagePayload.touch_target,
    display_mode: packagePayload.display_mode,
    pwa: packagePayload.pwa,
    service_worker: packagePayload.service_worker,
    client_timestamp: packagePayload.client_timestamp,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function deviceHandoffPackageCopyPayload(session) {
  // handoff package 只保留会议交接字段和 evidence capture 白名单引用，过滤 robot/raw 技术字段。
  return {
    schema: DEVICE_HANDOFF_PACKAGE_SCHEMA,
    schema_version: session.schema_version,
    session_schema: session.schema,
    session_id: session.session_id,
    client_reference: session.client_reference,
    entry_url: session.entry_url,
    safe_entry_summary: session.safe_entry_summary,
    overall_status: session.overall_status,
    real_device_observed: session.real_device_observed,
    production_app_ready: session.production_app_ready,
    pwa_install_prompt_observed: session.pwa_install_prompt_observed,
    safe_to_control: session.safe_to_control,
    observation_checklist: session.observation_checklist,
    evidence_capture_reference: session.evidence_capture_reference,
    device_observations: session.device_observations,
    browser_acceptance_reference: session.browser_acceptance_reference,
    safe_phone_copy: session.safe_phone_copy,
    recovery_hint: session.recovery_hint,
    ack_semantics: session.ack_semantics,
    evidence_boundary: session.evidence_boundary,
    not_proven: session.not_proven,
  };
}

function pwaInstallPromptPackageCopyPayload(packagePayload) {
  // install prompt 复制包只保留白名单字段；不复制 raw browser、robot 或 artifact 内容。
  return {
    schema: PWA_INSTALL_PROMPT_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    evidence_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    install_prompt_capture_status: packagePayload.install_prompt_capture_status,
    install_prompt_user_outcome: packagePayload.install_prompt_user_outcome,
    display_mode: packagePayload.display_mode,
    installability_status: packagePayload.installability_status,
    offline_shell_status: packagePayload.offline_shell_status,
    manifest_present: packagePayload.manifest_present,
    service_worker_status: packagePayload.service_worker_status,
    production_app_ready: packagePayload.production_app_ready,
    safe_to_control: packagePayload.safe_to_control,
    linked_handoff_session: packagePayload.linked_handoff_session,
    linked_device_evidence_capture: packagePayload.linked_device_evidence_capture,
    linked_browser_acceptance_bundle: packagePayload.linked_browser_acceptance_bundle,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function pwaInstallPromptEventCaptureCopyPayload(packagePayload) {
  // event capture 复制包只保留 schema、状态、时间、平台/浏览器概要和安全边界。
  return {
    schema: PWA_INSTALL_PROMPT_EVENT_CAPTURE_COPY_SCHEMA,
    schema_version: packagePayload.schema_version,
    event_capture_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    beforeinstallprompt_status: packagePayload.beforeinstallprompt_status,
    beforeinstallprompt_client_timestamp: packagePayload.beforeinstallprompt_client_timestamp,
    display_mode: packagePayload.display_mode,
    platform_summary: packagePayload.platform_summary,
    browser_summary: packagePayload.browser_summary,
    prompt_availability: packagePayload.prompt_availability,
    user_choice_outcome: packagePayload.user_choice_outcome,
    user_choice_client_timestamp: packagePayload.user_choice_client_timestamp,
    appinstalled_observed: packagePayload.appinstalled_observed,
    appinstalled_client_timestamp: packagePayload.appinstalled_client_timestamp,
    production_app_ready: packagePayload.production_app_ready,
    safe_to_control: packagePayload.safe_to_control,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function pwaInstallPromptEvidenceExportCopyPayload(packagePayload) {
  // export copy 是现场材料包最终输出，只允许合同列出的字段进入剪贴板/下载材料。
  return {
    schema: PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_COPY_SCHEMA,
    schema_version: 1,
    source: "mobile_web",
    overall_status: packagePayload.overall_status,
    install_prompt_capture_status: packagePayload.install_prompt_capture_status,
    install_prompt_user_choice: packagePayload.install_prompt_user_choice,
    appinstalled_status: packagePayload.appinstalled_status,
    display_mode: packagePayload.display_mode,
    manifest_present: packagePayload.manifest_present,
    service_worker_status: packagePayload.service_worker_status,
    client_reference: packagePayload.client_reference,
    client_timestamp: packagePayload.client_timestamp,
    safe_to_control: false,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: MOBILE_PWA_INSTALL_PROMPT_EVIDENCE_EXPORT_BOUNDARY,
    not_proven: packagePayload.not_proven,
    safe_phone_copy: packagePayload.safe_phone_copy,
  };
}

function downloadJsonPackage(filename, payload) {
  // 下载路径复用同一份白名单 JSON，避免复制和下载两种材料出现字段漂移。
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function realDeviceEvidencePackageCopyPayload(packagePayload) {
  // 真实设备材料复制包是最终 redacted contract，不能包含用户粘贴原文或控制放行字段。
  return {
    schema: REAL_DEVICE_EVIDENCE_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    intake_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    device: packagePayload.device,
    browser: packagePayload.browser,
    pwa: packagePayload.pwa,
    production_app: packagePayload.production_app,
    evidence: packagePayload.evidence,
    safe_to_control: false,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceAcceptanceDecisionPackageCopyPayload(packagePayload) {
  // 决策复制包只描述材料评审状态，不复制原始 intake JSON，也不新增控制授权。
  return {
    schema: REAL_DEVICE_ACCEPTANCE_DECISION_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    decision_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    decision: packagePayload.decision,
    accepted_for_review: packagePayload.accepted_for_review,
    safe_to_control: false,
    blocker_list: packagePayload.blocker_list,
    next_required_evidence: packagePayload.next_required_evidence,
    redaction_status: packagePayload.redaction_status,
    linked_intake_package: packagePayload.linked_intake_package,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceReviewHandoffPackageCopyPayload(packagePayload) {
  // review handoff package 只保留评审交接白名单，过滤原始 decision/intake、机器人响应和敏感字段。
  return {
    schema: REAL_DEVICE_REVIEW_HANDOFF_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    handoff_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    handoff_session_id: packagePayload.handoff_session_id,
    decision_status: packagePayload.decision_status,
    review_owner: packagePayload.review_owner,
    review_status: packagePayload.review_status,
    safe_to_control: false,
    evidence_blocker: packagePayload.evidence_blocker,
    next_required_evidence: packagePayload.next_required_evidence,
    reviewer_checklist: packagePayload.reviewer_checklist,
    redaction_status: packagePayload.redaction_status,
    linked_acceptance_decision: packagePayload.linked_acceptance_decision,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceReviewExecutionPackageCopyPayload(packagePayload) {
  // review execution 复制包只保留执行记录白名单，不复制 raw handoff、raw intake 或机器人响应。
  return {
    schema: REAL_DEVICE_REVIEW_EXECUTION_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    execution_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    execution_session_id: packagePayload.execution_session_id,
    handoff_session_id: packagePayload.handoff_session_id,
    decision_status: packagePayload.decision_status,
    review_owner: packagePayload.review_owner,
    review_status: packagePayload.review_status,
    review_result: packagePayload.review_result,
    safe_to_control: false,
    evidence_items_readiness: packagePayload.evidence_items_readiness,
    operator_notes: packagePayload.operator_notes,
    reviewer_notes: packagePayload.reviewer_notes,
    blocked_reason: packagePayload.blocked_reason,
    next_evidence_request: packagePayload.next_evidence_request,
    review_execution_checklist: packagePayload.review_execution_checklist,
    redaction_status: packagePayload.redaction_status,
    linked_review_handoff: packagePayload.linked_review_handoff,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceRetestRequestPackageCopyPayload(packagePayload) {
  // retest request 复制包只保留复测请求白名单，不复制 raw intake JSON、机器人响应或内部技术字段。
  return {
    schema: REAL_DEVICE_RETEST_REQUEST_PACKAGE_SCHEMA,
    schema_version: packagePayload.schema_version,
    request_schema: packagePayload.schema,
    summary_schema: packagePayload.summary_schema,
    source: packagePayload.source,
    retest_request_id: packagePayload.retest_request_id,
    execution_session_id: packagePayload.execution_session_id,
    request_status: packagePayload.request_status,
    review_result: packagePayload.review_result,
    review_status: packagePayload.review_status,
    owner: packagePayload.owner,
    next_action: packagePayload.next_action,
    safe_to_control: false,
    material_readiness: packagePayload.material_readiness,
    missing_evidence_list: packagePayload.missing_evidence_list,
    blocked_reason: packagePayload.blocked_reason,
    rejection_reason: packagePayload.rejection_reason,
    retest_checklist: packagePayload.retest_checklist,
    redaction_status: packagePayload.redaction_status,
    linked_review_execution: packagePayload.linked_review_execution,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: packagePayload.ack_semantics,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialPackageCopyPayload(packagePayload) {
  // field trial copy 是 whitelist-only 现场试跑包，固定 safe_to_control=false，ACK 只保留枚举语义。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    field_trial_id: packagePayload.field_trial_id,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    safe_to_control: false,
    runtime_metadata: packagePayload.runtime_metadata,
    observation_fields: packagePayload.observation_fields,
    mobile_real_device_field_trial_package_summary:
      packagePayload.mobile_real_device_field_trial_package_summary,
    linked_retest_request: packagePayload.linked_retest_request,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialReviewCopyPayload(packagePayload) {
  // review copy 只保留复核白名单，不复制凭证、入口参数、机器内部字段或 field trial 原始输入。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_REVIEW_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    review_id: packagePayload.review_id,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    safe_to_control: false,
    review_status: packagePayload.review_status,
    blocker_list: packagePayload.blocker_list,
    review_checklist: packagePayload.review_checklist,
    material_redaction_status: packagePayload.material_redaction_status,
    mobile_real_device_field_trial_review_summary:
      packagePayload.mobile_real_device_field_trial_review_summary,
    linked_field_trial_package: packagePayload.linked_field_trial_package,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialRunbookExecutionCopyPayload(packagePayload) {
  // runbook execution copy 是 whitelist-only 执行清单，不复制 raw artifact、凭证、内部路径或机器人响应。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    runbook_execution_id: packagePayload.runbook_execution_id,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    safe_to_control: false,
    execution_readiness: packagePayload.execution_readiness,
    execution_checklist: packagePayload.execution_checklist,
    open_items: packagePayload.open_items,
    material_redaction_status: packagePayload.material_redaction_status,
    mobile_real_device_field_trial_runbook_execution_summary:
      packagePayload.mobile_real_device_field_trial_runbook_execution_summary,
    linked_field_trial_review: packagePayload.linked_field_trial_review,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialEvidenceRecordCopyPayload(packagePayload) {
  // evidence record copy 只保留现场记录白名单，不复制原始材料、凭证、ROS/硬件字段或完整证据。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    evidence_record_id: packagePayload.evidence_record_id,
    source: packagePayload.source,
    overall_status: packagePayload.overall_status,
    safe_to_control: false,
    record_fields: packagePayload.record_fields,
    open_items: packagePayload.open_items,
    material_redaction_status: packagePayload.material_redaction_status,
    mobile_real_device_field_trial_evidence_record_summary:
      packagePayload.mobile_real_device_field_trial_evidence_record_summary,
    linked_runbook_execution: packagePayload.linked_runbook_execution,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialEvidenceRecordArchivePayload(packagePayload) {
  // archive package 是 copy package 的归档外壳，只增加归档时间和 schema，不保存 raw intake 或完整附件。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_RECORD_ARCHIVE_SCHEMA,
    schema_version: packagePayload.schema_version,
    archive_status: "archived_whitelist_only",
    archived_at: new Date().toISOString(),
    evidence_record_copy: realDeviceFieldTrialEvidenceRecordCopyPayload(packagePayload),
    safe_to_control: false,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialEvidenceVerdictCopyPayload(packagePayload) {
  // verdict copy 只保留复核结论、字段缺口和下一步材料请求，不复制 record/archive 原文或附件。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_EVIDENCE_VERDICT_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    verdict_id: packagePayload.verdict_id,
    source: packagePayload.source,
    verdict: packagePayload.verdict,
    safe_to_control: false,
    missing_evidence: packagePayload.missing_evidence,
    retest_request: packagePayload.retest_request,
    next_material_request: packagePayload.next_material_request,
    mobile_real_device_field_trial_evidence_verdict_summary:
      packagePayload.mobile_real_device_field_trial_evidence_verdict_summary,
    linked_evidence_record: packagePayload.linked_evidence_record,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialRetestExecutionCopyPayload(packagePayload) {
  // retest execution copy 只保留复测执行白名单，不复制 verdict 原文、附件或机器人内部响应。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_RETEST_EXECUTION_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    execution_id: packagePayload.execution_id,
    source: packagePayload.source,
    execution_status: packagePayload.execution_status,
    safe_to_control: false,
    retest_request: packagePayload.retest_request,
    material_request: packagePayload.material_request,
    missing_evidence_summary: packagePayload.missing_evidence_summary,
    execution_checklist: packagePayload.execution_checklist,
    mobile_real_device_field_trial_retest_execution_summary:
      packagePayload.mobile_real_device_field_trial_retest_execution_summary,
    linked_evidence_verdict: packagePayload.linked_evidence_verdict,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function realDeviceFieldTrialAcceptanceSessionCopyPayload(packagePayload) {
  // acceptance session copy 是 whitelist-only 会话包，不复制原始材料、附件、路径、凭证或机器人内部字段。
  return {
    schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_SCHEMA,
    schema_version: packagePayload.schema_version,
    copy_schema: REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_SESSION_COPY_SCHEMA,
    summary_schema: packagePayload.summary_schema,
    session_id: packagePayload.session_id,
    source: packagePayload.source,
    source_priority: packagePayload.source_priority,
    session_status: packagePayload.session_status,
    safe_to_control: false,
    acceptance_checklist: packagePayload.acceptance_checklist,
    blocked_items: packagePayload.blocked_items,
    material_redaction_status: packagePayload.material_redaction_status,
    operator_note: packagePayload.operator_note,
    support_note: packagePayload.support_note,
    mobile_real_device_field_trial_acceptance_session_summary:
      packagePayload.mobile_real_device_field_trial_acceptance_session_summary,
    linked_field_trial_retest_execution: packagePayload.linked_field_trial_retest_execution,
    linked_field_trial_evidence_verdict: packagePayload.linked_field_trial_evidence_verdict,
    linked_current_pwa_browser_proof: packagePayload.linked_current_pwa_browser_proof,
    safe_phone_copy: packagePayload.safe_phone_copy,
    recovery_hint: packagePayload.recovery_hint,
    ack_semantics: ACK_PROCESSING_ENUM,
    evidence_boundary: packagePayload.evidence_boundary,
    source_evidence_boundary: packagePayload.source_evidence_boundary,
    not_proven: packagePayload.not_proven,
  };
}

function renderMobileDeviceEvidence(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileDeviceEvidencePackageFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileDeviceEvidenceBadge");
  latestDeviceEvidencePackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.overall_status === "ready" ? "仍需实机复核" : "证据未证明";
  $("mobileDeviceEvidenceCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileDeviceEvidenceViewportTouch").textContent =
    `${packagePayload.viewport.width_css_px}x${packagePayload.viewport.height_css_px} @${packagePayload.viewport.device_pixel_ratio} / touch=${packagePayload.touch_target.touch_capable}`;
  $("mobileDeviceEvidenceDisplayPwa").textContent =
    `display=${packagePayload.display_mode} / install_prompt=${packagePayload.pwa.install_prompt_status}`;
  $("mobileDeviceEvidenceServiceWorker").textContent =
    `sw=${packagePayload.service_worker.status} / offline=${packagePayload.service_worker.offline_shell_status}`;
  $("mobileDeviceEvidenceTimestamp").textContent = packagePayload.client_timestamp;
  $("mobileDeviceEvidenceAck").textContent = packagePayload.ack_semantics;
  $("mobileDeviceEvidenceBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileDeviceEvidenceNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileDeviceEvidenceSafeCopy").textContent =
    JSON.stringify(deviceEvidencePackageCopyPayload(packagePayload), null, 2);
}

function renderMobilePwaInstallPromptEvidence(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobilePwaInstallPromptEvidenceFromStatus(status, readiness, latestDiagnostics);
  const eventCapturePayload = mobilePwaInstallPromptEventCaptureFromStatus(status, readiness, latestDiagnostics);
  const exportPayload = mobilePwaInstallPromptEvidenceExportFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobilePwaInstallPromptBadge");
  latestPwaInstallPromptPackage = packagePayload;
  latestPwaInstallPromptEventCapturePackage = eventCapturePayload;
  latestPwaInstallPromptEvidenceExportPackage = exportPayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = exportPayload.install_prompt_capture_status === "observed" ||
    exportPayload.appinstalled_status === "observed_not_proven"
    ? "导出材料已生成但不放行"
    : "export not_proven";
  $("mobilePwaInstallPromptCopy").textContent = exportPayload.safe_phone_copy;
  $("mobilePwaInstallPromptCapture").textContent = exportPayload.install_prompt_capture_status;
  $("mobilePwaInstallPromptOutcome").textContent = exportPayload.install_prompt_user_choice;
  $("mobilePwaInstallPromptDisplay").textContent =
    `display=${exportPayload.display_mode} / appinstalled=${exportPayload.appinstalled_status}`;
  $("mobilePwaInstallPromptShell").textContent =
    `manifest=${exportPayload.manifest_present} / sw=${exportPayload.service_worker_status}`;
  $("mobilePwaInstallPromptControl").textContent =
    `source_layer=${exportPayload.source_layer} / safe_to_control=${exportPayload.safe_to_control}`;
  $("mobilePwaInstallPromptAck").textContent = exportPayload.ack_semantics;
  $("mobilePwaInstallPromptBoundary").textContent = exportPayload.evidence_boundary;
  $("mobilePwaInstallPromptNotProven").textContent = exportPayload.not_proven.join("、");
  $("mobilePwaInstallPromptRecoveryHint").textContent = exportPayload.recovery_hint;
  $("mobilePwaInstallPromptSafeCopy").textContent =
    JSON.stringify(pwaInstallPromptEvidenceExportCopyPayload(exportPayload), null, 2);
}

function renderMobileRealDeviceEvidenceIntake(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceEvidencePackageFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceEvidenceBadge");
  latestRealDeviceEvidencePackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.overall_status === "ready" ? "材料已导入但不放行" : "not_proven";
  $("mobileRealDeviceEvidenceCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceEvidenceDevice").textContent =
    `platform=${packagePayload.device.platform} / model=${packagePayload.device.model_summary} / os=${packagePayload.device.os_summary}`;
  $("mobileRealDeviceEvidenceBrowser").textContent =
    `${packagePayload.browser.family} ${packagePayload.browser.version_summary}`;
  $("mobileRealDeviceEvidenceViewport").textContent =
    `${packagePayload.browser.viewport_css.width}x${packagePayload.browser.viewport_css.height} / DPR=${packagePayload.browser.device_pixel_ratio} / orientation=${packagePayload.browser.orientation}`;
  $("mobileRealDeviceEvidencePwa").textContent =
    `display=${packagePayload.pwa.display_mode} / PWA install prompt=${packagePayload.pwa.install_prompt_status} / user_choice=${packagePayload.pwa.install_prompt_user_choice}`;
  $("mobileRealDeviceEvidenceProduction").textContent =
    `production app ready=${packagePayload.production_app.ready} / release=${packagePayload.production_app.release_summary}`;
  $("mobileRealDeviceEvidenceScreenshot").textContent = packagePayload.evidence.screenshot_summary;
  $("mobileRealDeviceEvidenceUrl").textContent = packagePayload.evidence.url_summary;
  $("mobileRealDeviceEvidenceObserver").textContent = packagePayload.evidence.observer_note;
  $("mobileRealDeviceEvidenceRedaction").textContent = packagePayload.evidence.redaction_status;
  $("mobileRealDeviceEvidenceAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceEvidenceBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceEvidenceNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceEvidenceRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobileRealDeviceEvidenceSafeCopy").textContent =
    JSON.stringify(realDeviceEvidencePackageCopyPayload(packagePayload), null, 2);
}

function rerenderPwaInstallPromptEventCapture() {
  // 事件监听发生在页面生命周期任意时刻；只刷新证据 panel，不触碰控制按钮授权。
  if ($("mobilePwaInstallPromptTitle")) {
    renderMobilePwaInstallPromptEvidence(latestStatus || {});
  }
}

function updatePwaInstallPromptEventState(patch) {
  // runtime state 只保存白名单字段；deferred prompt 单独存在内存变量，不进入 copy package。
  pwaInstallPromptEventState = {
    ...defaultPwaInstallPromptEventState(),
    ...(pwaInstallPromptEventState || {}),
    ...patch,
  };
  rerenderPwaInstallPromptEventCapture();
}

function initializePwaInstallPromptEventCapture() {
  // beforeinstallprompt、userChoice、appinstalled 都是浏览器事件证据，不是控制 grant。
  pwaInstallPromptEventState = defaultPwaInstallPromptEventState();
  window.addEventListener("beforeinstallprompt", (event) => {
    const metadata = pwaEventRuntimeMetadata();
    if (typeof event.preventDefault === "function") {
      event.preventDefault();
    }
    deferredPwaInstallPromptEvent = event;
    updatePwaInstallPromptEventState({
      beforeinstallprompt_status: "observed",
      beforeinstallprompt_client_timestamp: metadata.client_timestamp,
      display_mode: metadata.display_mode,
      platform_summary: metadata.platform_summary,
      browser_summary: metadata.browser_summary,
      prompt_availability: "runtime_deferred_prompt_available",
      safe_phone_copy: "已观察到 beforeinstallprompt 事件；deferred prompt 仅保存在 runtime，不进入复制包，也不放行控制动作。",
      recovery_hint: "如需 userChoice，请由人工在真实浏览器环境触发安装提示；结果仍需实机复核。",
    });
    if (event.userChoice && typeof event.userChoice.then === "function") {
      event.userChoice.then((choice) => {
        const outcome = choice && ["accepted", "dismissed"].includes(choice.outcome)
          ? choice.outcome
          : "unknown";
        updatePwaInstallPromptEventState({
          user_choice_outcome: outcome,
          user_choice_client_timestamp: new Date().toISOString(),
          safe_phone_copy: `已记录 userChoice=${outcome}；该结果仍不是 production app readiness、真实送达或控制授权。`,
        });
      }).catch(() => {
        updatePwaInstallPromptEventState({
          user_choice_outcome: "unknown",
          user_choice_client_timestamp: new Date().toISOString(),
          safe_phone_copy: "userChoice promise 未返回可证明结果；按 unknown/not_proven 处理。",
        });
      });
    }
  });
  window.addEventListener("appinstalled", () => {
    const metadata = pwaEventRuntimeMetadata();
    updatePwaInstallPromptEventState({
      appinstalled_observed: true,
      appinstalled_client_timestamp: metadata.client_timestamp,
      display_mode: metadata.display_mode,
      platform_summary: metadata.platform_summary,
      browser_summary: metadata.browser_summary,
      safe_phone_copy: "已观察到 appinstalled 事件；这只证明浏览器事件捕获能力，不证明 production app 或 delivery success。",
    });
  });
}

function renderMobileRealDeviceAcceptanceDecision(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceAcceptanceDecisionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceAcceptanceDecisionBadge");
  latestRealDeviceAcceptanceDecisionPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.decision === "accepted_for_review" ? "gate-waiting" : "gate-blocked");
  badge.textContent = packagePayload.decision;
  $("mobileRealDeviceAcceptanceDecisionCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceAcceptanceDecisionState").textContent = packagePayload.decision;
  $("mobileRealDeviceAcceptanceDecisionReview").textContent =
    `accepted_for_review=${packagePayload.accepted_for_review} / safe_to_control=${packagePayload.safe_to_control}`;
  $("mobileRealDeviceAcceptanceDecisionBlockers").textContent = packagePayload.blocker_list.join("；");
  $("mobileRealDeviceAcceptanceDecisionNextEvidence").textContent = packagePayload.next_required_evidence.join("；");
  $("mobileRealDeviceAcceptanceDecisionRedaction").textContent = packagePayload.redaction_status;
  $("mobileRealDeviceAcceptanceDecisionAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceAcceptanceDecisionBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceAcceptanceDecisionSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceAcceptanceDecisionNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceAcceptanceDecisionRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobileRealDeviceAcceptanceDecisionSafeCopy").textContent =
    JSON.stringify(realDeviceAcceptanceDecisionPackageCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceReviewHandoff(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceReviewHandoffBadge");
  latestRealDeviceReviewHandoffPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.review_status === "ready_for_manual_review" ? "gate-waiting" : "gate-blocked");
  badge.textContent = packagePayload.review_status;
  $("mobileRealDeviceReviewHandoffCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceReviewHandoffDecision").textContent = packagePayload.decision_status;
  $("mobileRealDeviceReviewHandoffOwner").textContent =
    `review owner=${packagePayload.review_owner} / review status=${packagePayload.review_status}`;
  $("mobileRealDeviceReviewHandoffBlockers").textContent = packagePayload.evidence_blocker.join("；");
  $("mobileRealDeviceReviewHandoffNextEvidence").textContent = packagePayload.next_required_evidence.join("；");
  $("mobileRealDeviceReviewHandoffRedaction").textContent = packagePayload.redaction_status;
  $("mobileRealDeviceReviewHandoffAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceReviewHandoffBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceReviewHandoffSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceReviewHandoffNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceReviewHandoffRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceReviewHandoffChecklist");
  list.textContent = "";
  packagePayload.reviewer_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = step.safe_phone_copy;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceReviewHandoffSafeCopy").textContent =
    JSON.stringify(realDeviceReviewHandoffPackageCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceReviewExecution(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceReviewExecutionBadge");
  latestRealDeviceReviewExecutionPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.review_result === "pending_manual_execution" ? "gate-waiting" : "gate-blocked");
  badge.textContent = packagePayload.review_result;
  $("mobileRealDeviceReviewExecutionCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceReviewExecutionResult").textContent = packagePayload.review_result;
  $("mobileRealDeviceReviewExecutionStatus").textContent =
    `review owner=${packagePayload.review_owner} / review status=${packagePayload.review_status}`;
  $("mobileRealDeviceReviewExecutionEvidenceReadiness").textContent =
    `device=${packagePayload.evidence_items_readiness.device_materials} / production_app=${packagePayload.evidence_items_readiness.production_app} / PWA install prompt=${packagePayload.evidence_items_readiness.pwa_install_prompt} / redaction=${packagePayload.evidence_items_readiness.redaction}`;
  $("mobileRealDeviceReviewExecutionOperatorNotes").textContent = packagePayload.operator_notes;
  $("mobileRealDeviceReviewExecutionReviewerNotes").textContent = packagePayload.reviewer_notes;
  $("mobileRealDeviceReviewExecutionBlockedReason").textContent = packagePayload.blocked_reason;
  $("mobileRealDeviceReviewExecutionNextEvidence").textContent = packagePayload.next_evidence_request.join("；");
  $("mobileRealDeviceReviewExecutionRedaction").textContent = packagePayload.redaction_status;
  $("mobileRealDeviceReviewExecutionAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceReviewExecutionBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceReviewExecutionSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceReviewExecutionNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceReviewExecutionRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceReviewExecutionChecklist");
  list.textContent = "";
  packagePayload.review_execution_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = step.safe_phone_copy;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceReviewExecutionSafeCopy").textContent =
    JSON.stringify(realDeviceReviewExecutionPackageCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceRetestRequest(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceRetestRequestFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceRetestRequestBadge");
  latestRealDeviceRetestRequestPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.request_status === "pending_retest_materials" ? "gate-waiting" : "gate-blocked");
  badge.textContent = packagePayload.request_status;
  $("mobileRealDeviceRetestRequestCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceRetestRequestStatus").textContent = packagePayload.request_status;
  $("mobileRealDeviceRetestRequestOwner").textContent =
    `owner=${packagePayload.owner} / next action=${packagePayload.next_action}`;
  $("mobileRealDeviceRetestRequestMissingEvidence").textContent = packagePayload.missing_evidence_list.join("；");
  $("mobileRealDeviceRetestRequestReadiness").textContent =
    `device=${packagePayload.material_readiness.device_materials} / production app=${packagePayload.material_readiness.production_app} / PWA install prompt=${packagePayload.material_readiness.pwa_install_prompt} / O5=${packagePayload.material_readiness.objective5_external_materials} / redaction=${packagePayload.material_readiness.redaction}`;
  $("mobileRealDeviceRetestRequestBlockedReason").textContent = packagePayload.blocked_reason;
  $("mobileRealDeviceRetestRequestRejectionReason").textContent = packagePayload.rejection_reason;
  $("mobileRealDeviceRetestRequestRedaction").textContent = packagePayload.redaction_status;
  $("mobileRealDeviceRetestRequestAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceRetestRequestBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceRetestRequestSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceRetestRequestNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceRetestRequestRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceRetestRequestChecklist");
  list.textContent = "";
  packagePayload.retest_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status} / owner=${step.owner}`;
    copy.textContent = `${step.safe_phone_copy} next action=${step.next_action}`;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceRetestRequestSafeCopy").textContent =
    JSON.stringify(realDeviceRetestRequestPackageCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialPackage(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialPackageFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialBadge");
  latestRealDeviceFieldTrialPackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.overall_status;
  $("mobileRealDeviceFieldTrialCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialRuntime").textContent =
    `${packagePayload.runtime_metadata.viewport_css_width}x${packagePayload.runtime_metadata.viewport_css_height} ` +
    `DPR=${packagePayload.runtime_metadata.device_pixel_ratio} ` +
    `orientation=${packagePayload.runtime_metadata.orientation} ` +
    `touch=${packagePayload.runtime_metadata.touch_capability} ` +
    `display=${packagePayload.runtime_metadata.display_mode} ` +
    `manifest=${packagePayload.runtime_metadata.manifest_link_present} ` +
    `sw=${packagePayload.runtime_metadata.service_worker_registration_hint} ` +
    `offline=${packagePayload.runtime_metadata.offline_shell_hint} ` +
    `entry=${packagePayload.runtime_metadata.entry_url_summary}`;
  $("mobileRealDeviceFieldTrialObservations").textContent =
    `device=${packagePayload.observation_fields.device_type} / ` +
    `os_browser=${packagePayload.observation_fields.os_browser} / ` +
    `production_app=${packagePayload.observation_fields.production_app_observed} / ` +
    `pwa_prompt=${packagePayload.observation_fields.pwa_install_prompt_observed} / ` +
    `user_choice=${packagePayload.observation_fields.user_choice} / ` +
    `offline_reload=${packagePayload.observation_fields.offline_reload_observed} / ` +
    `touch_issue=${packagePayload.observation_fields.touch_target_issue} / ` +
    `visual_issue=${packagePayload.observation_fields.visual_issue}`;
  $("mobileRealDeviceFieldTrialSummary").textContent =
    JSON.stringify(packagePayload.mobile_real_device_field_trial_package_summary);
  $("mobileRealDeviceFieldTrialSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobileRealDeviceFieldTrialSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialPackageCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialReview(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialReviewFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialReviewBadge");
  latestRealDeviceFieldTrialReviewPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.blocker_list.length ? "gate-blocked" : "gate-waiting");
  badge.textContent = packagePayload.overall_status;
  $("mobileRealDeviceFieldTrialReviewCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialReviewRealDevice").textContent = packagePayload.review_status.real_device;
  $("mobileRealDeviceFieldTrialReviewProductionApp").textContent = packagePayload.review_status.production_app;
  $("mobileRealDeviceFieldTrialReviewPrompt").textContent = packagePayload.review_status.pwa_install_prompt;
  $("mobileRealDeviceFieldTrialReviewUserChoice").textContent = packagePayload.review_status.user_choice;
  $("mobileRealDeviceFieldTrialReviewOffline").textContent = packagePayload.review_status.offline;
  $("mobileRealDeviceFieldTrialReviewTouch").textContent = packagePayload.review_status.touch;
  $("mobileRealDeviceFieldTrialReviewVisual").textContent = packagePayload.review_status.visual;
  $("mobileRealDeviceFieldTrialReviewRedaction").textContent = packagePayload.material_redaction_status;
  $("mobileRealDeviceFieldTrialReviewSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialReviewAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialReviewBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialReviewNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialReviewRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceFieldTrialReviewChecklist");
  list.textContent = "";
  packagePayload.review_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = step.safe_phone_copy;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceFieldTrialReviewSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialReviewCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialRunbookExecution(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialRunbookExecutionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialRunbookExecutionBadge");
  latestRealDeviceFieldTrialRunbookExecutionPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.open_items.length ? "gate-blocked" : "gate-waiting");
  badge.textContent = packagePayload.overall_status;
  $("mobileRealDeviceFieldTrialRunbookExecutionCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialRunbookExecutionReadiness").textContent =
    `device=${packagePayload.execution_readiness.real_device} / ` +
    `production_app=${packagePayload.execution_readiness.production_app} / ` +
    `pwa_prompt=${packagePayload.execution_readiness.pwa_install_prompt} / ` +
    `user_choice=${packagePayload.execution_readiness.user_choice}`;
  $("mobileRealDeviceFieldTrialRunbookExecutionOfflineTouch").textContent =
    `offline=${packagePayload.execution_readiness.offline} / ` +
    `touch=${packagePayload.execution_readiness.touch} / ` +
    `visual=${packagePayload.execution_readiness.visual}`;
  $("mobileRealDeviceFieldTrialRunbookExecutionRedaction").textContent = packagePayload.material_redaction_status;
  $("mobileRealDeviceFieldTrialRunbookExecutionOpenItems").textContent =
    packagePayload.open_items.length ? packagePayload.open_items.join("；") : "open_items=0 / still not control proof";
  $("mobileRealDeviceFieldTrialRunbookExecutionSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialRunbookExecutionAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialRunbookExecutionBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialRunbookExecutionNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialRunbookExecutionRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceFieldTrialRunbookExecutionChecklist");
  list.textContent = "";
  packagePayload.execution_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = step.safe_phone_copy;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceFieldTrialRunbookExecutionSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialRunbookExecutionCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialEvidenceRecord(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialEvidenceRecordFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialEvidenceRecordBadge");
  latestRealDeviceFieldTrialEvidenceRecordPackage = packagePayload;

  badge.className = "gate-badge";
  badge.classList.add(packagePayload.open_items.length ? "gate-blocked" : "gate-waiting");
  badge.textContent = packagePayload.overall_status;
  $("mobileRealDeviceFieldTrialEvidenceRecordCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialEvidenceRecordDeviceApp").textContent =
    `real_device=${packagePayload.record_fields.real_device} / ` +
    `production_app=${packagePayload.record_fields.production_app} / ` +
    `pwa_prompt=${packagePayload.record_fields.pwa_install_prompt}`;
  $("mobileRealDeviceFieldTrialEvidenceRecordUserOffline").textContent =
    `user_choice=${packagePayload.record_fields.user_choice} / ` +
    `offline=${packagePayload.record_fields.offline} / ` +
    `touch=${packagePayload.record_fields.touch} / ` +
    `visual=${packagePayload.record_fields.visual}`;
  $("mobileRealDeviceFieldTrialEvidenceRecordRedaction").textContent = packagePayload.material_redaction_status;
  $("mobileRealDeviceFieldTrialEvidenceRecordSummary").textContent =
    JSON.stringify(packagePayload.mobile_real_device_field_trial_evidence_record_summary);
  $("mobileRealDeviceFieldTrialEvidenceRecordSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialEvidenceRecordAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialEvidenceRecordBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialEvidenceRecordArchive").textContent = archivedRealDeviceFieldTrialEvidenceRecordPackage
    ? `mobile_real_device_field_trial_evidence_record_archive=${archivedRealDeviceFieldTrialEvidenceRecordPackage.archive_status}`
    : "mobile_real_device_field_trial_evidence_record_archive 未归档。";
  $("mobileRealDeviceFieldTrialEvidenceRecordNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialEvidenceRecordRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobileRealDeviceFieldTrialEvidenceRecordSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialEvidenceRecordCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialEvidenceVerdict(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialEvidenceVerdictFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialEvidenceVerdictBadge");
  latestRealDeviceFieldTrialEvidenceVerdictPackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.verdict;
  $("mobileRealDeviceFieldTrialEvidenceVerdictCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialEvidenceVerdictState").textContent = packagePayload.verdict;
  $("mobileRealDeviceFieldTrialEvidenceVerdictMissingEvidence").textContent =
    packagePayload.missing_evidence.map((item) => `${item.field}=${item.status}`).join("；");
  $("mobileRealDeviceFieldTrialEvidenceVerdictRetest").textContent = packagePayload.retest_request;
  $("mobileRealDeviceFieldTrialEvidenceVerdictMaterialRequest").textContent = packagePayload.next_material_request;
  $("mobileRealDeviceFieldTrialEvidenceVerdictSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialEvidenceVerdictAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialEvidenceVerdictBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialEvidenceVerdictSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceFieldTrialEvidenceVerdictNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialEvidenceVerdictRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialEvidenceVerdictCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialRetestExecution(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialRetestExecutionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialRetestExecutionBadge");
  latestRealDeviceFieldTrialRetestExecutionPackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.execution_status;
  $("mobileRealDeviceFieldTrialRetestExecutionCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialRetestExecutionStatus").textContent = packagePayload.execution_status;
  $("mobileRealDeviceFieldTrialRetestExecutionRetest").textContent = packagePayload.retest_request;
  $("mobileRealDeviceFieldTrialRetestExecutionMaterial").textContent = packagePayload.material_request;
  $("mobileRealDeviceFieldTrialRetestExecutionMissing").textContent =
    packagePayload.missing_evidence_summary.join("；");
  $("mobileRealDeviceFieldTrialRetestExecutionSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialRetestExecutionAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialRetestExecutionBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialRetestExecutionSourceBoundary").textContent = packagePayload.source_evidence_boundary;
  $("mobileRealDeviceFieldTrialRetestExecutionNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialRetestExecutionRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceFieldTrialRetestExecutionChecklist");
  list.textContent = "";
  packagePayload.execution_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status} / owner=${step.owner}`;
    copy.textContent = `${step.material_request} evidence=${step.evidence_slot}`;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceFieldTrialRetestExecutionSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialRetestExecutionCopyPayload(packagePayload), null, 2);
}

function renderMobileRealDeviceFieldTrialAcceptanceSession(status) {
  const readiness = readinessFromStatus(status);
  const packagePayload = mobileRealDeviceFieldTrialAcceptanceSessionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileRealDeviceFieldTrialAcceptanceSessionBadge");
  latestRealDeviceFieldTrialAcceptanceSessionPackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.session_status;
  $("mobileRealDeviceFieldTrialAcceptanceSessionCopy").textContent = packagePayload.safe_phone_copy;
  $("mobileRealDeviceFieldTrialAcceptanceSessionStatus").textContent = packagePayload.session_status;
  $("mobileRealDeviceFieldTrialAcceptanceSessionSource").textContent =
    `${packagePayload.source_priority} / ${packagePayload.source_evidence_boundary}`;
  $("mobileRealDeviceFieldTrialAcceptanceSessionBlocked").textContent =
    packagePayload.blocked_items.length ? packagePayload.blocked_items.join("；") : "blocked_items=0 / still not control proof";
  $("mobileRealDeviceFieldTrialAcceptanceSessionRedaction").textContent = packagePayload.material_redaction_status;
  $("mobileRealDeviceFieldTrialAcceptanceSessionNotes").textContent =
    `operator=${packagePayload.operator_note} / support=${packagePayload.support_note}`;
  $("mobileRealDeviceFieldTrialAcceptanceSessionSafeControl").textContent = "safe_to_control=false";
  $("mobileRealDeviceFieldTrialAcceptanceSessionAck").textContent = packagePayload.ack_semantics;
  $("mobileRealDeviceFieldTrialAcceptanceSessionBoundary").textContent = packagePayload.evidence_boundary;
  $("mobileRealDeviceFieldTrialAcceptanceSessionNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobileRealDeviceFieldTrialAcceptanceSessionRecoveryHint").textContent = packagePayload.recovery_hint;

  const list = $("mobileRealDeviceFieldTrialAcceptanceSessionChecklist");
  list.textContent = "";
  packagePayload.acceptance_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = `${step.safe_phone_copy} source=${step.source_hint}`;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileRealDeviceFieldTrialAcceptanceSessionSafeCopy").textContent =
    JSON.stringify(realDeviceFieldTrialAcceptanceSessionCopyPayload(packagePayload), null, 2);
}

function renderMobileDeviceHandoffSession(status) {
  const readiness = readinessFromStatus(status);
  const session = mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics);
  const badge = $("mobileDeviceHandoffBadge");
  const allowed = mobileDeviceHandoffSessionAllowsPrimaryActions(session);
  latestDeviceHandoffSession = session;

  badge.className = "gate-badge";
  badge.classList.add(allowed ? "gate-ready" : "gate-blocked");
  badge.textContent = allowed ? "会话允许" : "会话阻塞";
  $("mobileDeviceHandoffCopy").textContent = session.safe_phone_copy;
  $("mobileDeviceHandoffEntry").textContent = session.entry_url || session.safe_entry_summary;
  $("mobileDeviceHandoffSessionId").textContent = session.session_id;
  $("mobileDeviceHandoffClientReference").textContent = session.client_reference;
  $("mobileDeviceHandoffEvidenceRef").textContent =
    `${session.evidence_capture_reference.schema} / ${session.evidence_capture_reference.evidence_boundary}`;
  $("mobileDeviceHandoffObservations").textContent =
    `device=${session.real_device_observed} / app=${session.production_app_ready} / install_prompt=${session.pwa_install_prompt_observed}`;
  $("mobileDeviceHandoffAck").textContent = session.ack_semantics;
  $("mobileDeviceHandoffBoundary").textContent = session.evidence_boundary;
  $("mobileDeviceHandoffHint").textContent = session.recovery_hint;
  $("mobileDeviceHandoffNotProven").textContent = session.not_proven.join("、");

  const list = $("mobileDeviceHandoffChecklist");
  list.textContent = "";
  session.observation_checklist.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    const copy = document.createElement("em");
    title.textContent = `${step.item}：${step.status}`;
    copy.textContent = step.safe_phone_copy;
    item.append(title, copy);
    list.appendChild(item);
  });
  $("mobileDeviceHandoffSafeCopy").textContent =
    JSON.stringify(deviceHandoffPackageCopyPayload(session), null, 2);
}

function renderMobileBrowserAcceptanceBundle(status) {
  const readiness = readinessFromStatus(status);
  const bundle = mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics);
  const allowed = mobileBrowserAcceptanceBundleAllowsPrimaryActions(bundle);
  const badge = $("mobileBrowserAcceptanceBadge");
  latestAcceptanceBundle = bundle;

  badge.className = "gate-badge";
  badge.classList.add(allowed ? "gate-ready" : "gate-blocked");
  badge.textContent = allowed ? "验收包允许" : "验收包阻塞";
  $("mobileBrowserAcceptanceCopy").textContent = bundle.safe_phone_copy;
  $("mobileBrowserOverall").textContent = bundle.overall_status;
  $("mobileBrowserProductionApp").textContent = bundle.production_app_ready
    ? "production_app_ready=true"
    : "production_app_ready=false / 未证明";
  $("mobileBrowserSafeControl").textContent = bundle.safe_to_control
    ? "safe_to_control=true"
    : "safe_to_control=false / fail closed";
  $("mobileBrowserViewportTouch").textContent = `viewport=${bundle.viewport} / touch=${bundle.touch_target}`;
  $("mobileBrowserPwaOffline").textContent = `PWA=${bundle.pwa_install_prompt} / offline=${bundle.offline_shell}`;
  $("mobileBrowserDiagnosticsCloud").textContent = `diagnostics=${bundle.diagnostics} / cloud=${bundle.cloud_gate}`;
  $("mobileBrowserActionGate").textContent = bundle.action_gate;
  $("mobileBrowserAck").textContent = bundle.ack_semantics;
  $("mobileBrowserTimestamp").textContent = bundle.client_timestamp;
  $("mobileBrowserBoundary").textContent = bundle.evidence_boundary;
  $("mobileBrowserRecoveryHint").textContent = bundle.recovery_hint;
  $("mobileBrowserNotProven").textContent = bundle.not_proven.join("、");
  $("mobileBrowserSafeCopy").textContent = JSON.stringify(bundleCopyPayload(bundle), null, 2);
}

function renderOperationLog(status) {
  const readiness = readinessFromStatus(status);
  const operationLog = operationLogFromStatus(status, readiness);
  const list = $("operationLogList");
  list.textContent = "";

  $("operationLogSource").className = "gate-badge gate-ready";
  $("operationLogSource").textContent = operationLog.source === "operation_log" ? "后端日志" : "安全派生";
  $("operationLogHint").textContent = operationLog.source === "operation_log"
    ? "优先展示后端 operation_log / phone_operation_log。"
    : "后端未提供日志时，仅从既有 phone-safe readiness 字段派生。";

  if (!operationLog.entries.length) {
    $("operationLogSource").className = "gate-badge gate-blocked";
    $("operationLogSource").textContent = "暂无事件";
    const item = document.createElement("li");
    item.textContent = "暂无可展示的 phone-safe 操作事件；主操作继续由 command_safety 控制。";
    list.appendChild(item);
  } else {
    operationLog.entries.forEach((event) => {
      const item = document.createElement("li");
      const meta = document.createElement("span");
      const copy = document.createElement("span");
      const hint = document.createElement("span");
      meta.className = "event-meta";
      copy.className = "event-copy";
      hint.className = "event-hint";
      meta.textContent = `${event.timestamp} / ${event.title}`;
      copy.textContent = event.copy;
      hint.textContent = `恢复提示：${event.hint}`;
      item.append(meta, copy, hint);
      list.appendChild(item);
    });
  }

  const bundle = status?.phone_support_bundle || readiness.phone_support_bundle || {};
  $("operationSupportEntry").textContent = safeText(
    bundle.safe_copy || bundle.status_summary,
    "支持交接入口保持可见；不会触发 Start、Confirm 或 Cancel。",
  );
}

function actionLabel(actionName) {
  return ACTIONS[actionName]?.label || safeText(actionName, "用户动作");
}

function normalizeActionFeedback(value, source) {
  const actionName = safeText(value.action || value.user_action || value.command, "unknown");
  const state = safeText(
    value.submission_status || value.state || value.status || value.ack_state,
    "waiting_ack",
  );
  // 失败原因与恢复建议必须来自安全字段或本地请求错误；不要展示原始异常、路径或硬件细节。
  return {
    source,
    action: actionName,
    actionCopy: safeText(value.action_copy || value.label, actionLabel(actionName)),
    state,
    safePhoneCopy: safeText(value.safe_phone_copy || value.summary, "动作已提交，等待 accepted/processing 证据。"),
    failureReason: safeText(
      value.failure_reason || value.blocking_reason || value.reason || value.error_safe_copy,
      "无后端失败原因；请继续观察状态。",
    ),
    recoveryHint: safeText(
      value.recovery_hint || value.next_action || value.retry_hint,
      "等待状态刷新；如长时间无 ACK，请打开诊断或联系支持。",
    ),
    clientReference: safeText(value.client_reference || value.request_id, "未提供"),
    ackSemantics: safeText(value.ack_semantics, ACK_PROCESSING_COPY),
    evidenceBoundary: safeText(value.evidence_boundary, ACTION_FEEDBACK_BOUNDARY),
  };
}

function renderActionFeedback(status) {
  const readiness = readinessFromStatus(status);
  const feedback = actionFeedbackFromStatus(status, readiness) || latestActionFeedback;
  const badge = $("actionFeedbackStatusBadge");

  if (!feedback) {
    badge.className = "gate-badge gate-blocked";
    badge.textContent = "等待动作";
    $("actionFeedbackCopy").textContent = "提交 Start、Confirm 或 Cancel 后，这里只显示 phone-safe 回执和恢复建议。";
    $("actionFeedbackAction").textContent = "暂无";
    $("actionFeedbackState").textContent = "等待提交";
    $("actionFeedbackClientReference").textContent = "暂无";
    $("actionFeedbackAck").textContent = ACK_PROCESSING_COPY;
    $("actionFeedbackReason").textContent = "失败原因会由后端或本地提交错误提供。";
    $("actionFeedbackRecovery").textContent = "恢复建议会保持可读、可重试、可交接。";
    $("actionFeedbackBoundary").textContent = ACTION_FEEDBACK_BOUNDARY;
    return;
  }

  latestActionFeedback = feedback;
  const failed = ["failed", "blocked", "rejected", "local_submit_failed"].includes(feedback.state);
  const waiting = ["submitted", "waiting_ack", "accepted_or_processing"].includes(feedback.state);
  badge.className = "gate-badge";
  badge.classList.add(failed ? "gate-blocked" : (waiting ? "gate-waiting" : "gate-ready"));
  badge.textContent = failed ? "需要处理" : "处理中";
  $("actionFeedbackCopy").textContent = feedback.safePhoneCopy;
  $("actionFeedbackAction").textContent = feedback.actionCopy;
  $("actionFeedbackState").textContent = feedback.state;
  $("actionFeedbackClientReference").textContent = feedback.clientReference;
  $("actionFeedbackAck").textContent = feedback.ackSemantics;
  $("actionFeedbackReason").textContent = `失败/阻塞原因：${feedback.failureReason}`;
  $("actionFeedbackRecovery").textContent = `恢复建议：${feedback.recoveryHint}`;
  $("actionFeedbackBoundary").textContent = feedback.evidenceBoundary;
}

function renderSupport(status) {
  const readiness = readinessFromStatus(status);
  const bundle = status?.phone_support_bundle || readiness.phone_support_bundle || {};
  $("supportCopy").textContent = safeText(
    bundle.safe_copy || bundle.status_summary,
    "诊断和支持交接不触发机器人动作。",
  );
  $("supportSafeCopy").textContent = safeText(bundle.safe_copy, "暂无脱敏支持摘要。");
}

function renderDiagnosticsSummary(payload) {
  const panel = $("diagnosticsPanel");
  const grid = $("diagnosticsSummary");
  grid.textContent = "";
  const routeReview = routeTaskReviewFromStatus(latestStatus || {}, readinessFromStatus(latestStatus || {}), payload || {});
  const rows = [
    ["软件版本", payload?.software_version],
    ["地图版本", payload?.map_version],
    ["路线版本", payload?.route_version],
    ["当前状态", payload?.latest_status?.phone_copy || payload?.state],
    ["失败原因", payload?.failure?.message || payload?.failure_code],
    ["支持级别", payload?.phone_support_bundle?.support_level],
    ["路线/任务排练复盘", routeReview.overall_status],
  ];
  rows.forEach(([label, value]) => {
    const box = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = safeText(value, "未提供");
    box.append(dt, dd);
    grid.appendChild(box);
  });
  panel.hidden = false;
}

function renderOfflineFailure() {
  latestStatus = null;
  setBadge("offline", "离线");
  $("readinessTitle").textContent = "手机已离线";
  $("safePhoneCopy").textContent = "无法读取后端状态，主操作已保持禁用。";
  $("recoveryHint").textContent = "请恢复网络后刷新；离线壳不会发送或排队控制请求。";
  $("commandSafetyCopy").textContent = "离线状态下 Start、Confirm、Cancel 全部禁用。";
  $("offlineCopy").textContent = "离线壳只显示恢复提示，不缓存控制请求。";
  $("operationLogSource").textContent = "离线";
  $("operationLogSource").className = "gate-badge gate-blocked";
  $("operationLogHint").textContent = "离线时不派生新机器人状态，主操作保持禁用。";
  $("operationLogList").textContent = "";
  const offlineEvent = document.createElement("li");
  offlineEvent.textContent = "无法读取后端 operation log；请恢复网络后刷新。";
  $("operationLogList").appendChild(offlineEvent);
  $("operationSupportEntry").textContent = "离线时可保留恢复提示，但不发送控制请求。";
  renderCloudReadiness({});
  renderMobileDeviceAcceptance({});
  renderMobileDeviceEvidence({});
  renderMobileDeviceHandoffSession({});
  renderMobilePwaInstallPromptEvidence({});
  renderMobileRealDeviceEvidenceIntake({});
  renderMobileRealDeviceAcceptanceDecision({});
  renderMobileRealDeviceReviewHandoff({});
  renderMobileRealDeviceReviewExecution({});
  renderMobileRealDeviceRetestRequest({});
  renderMobileRealDeviceFieldTrialPackage({});
  renderMobileRealDeviceFieldTrialReview({});
  renderMobileRealDeviceFieldTrialRunbookExecution({});
  renderMobileRealDeviceFieldTrialEvidenceRecord({});
  renderMobileRealDeviceFieldTrialEvidenceVerdict({});
  renderMobileRealDeviceFieldTrialRetestExecution({});
  renderMobileRealDeviceFieldTrialAcceptanceSession({});
  renderMobileBrowserAcceptanceBundle({});
  renderRecoveryDecision({ connection_state: "offline" });
  renderRouteTaskReview({});
  latestActionFeedback = normalizeActionFeedback({
    action: "status_refresh",
    submission_status: "blocked",
    safe_phone_copy: "状态刷新失败，手机端不会提交或重放控制请求。",
    failure_reason: "无法读取后端 /api/status。",
    recovery_hint: "恢复网络后刷新页面；需要时打开诊断或联系支持。",
    client_reference: "local_offline",
    ack_semantics: ACK_PROCESSING_COPY,
    evidence_boundary: ACTION_FEEDBACK_BOUNDARY,
  }, "local");
  renderActionFeedback({});
  $("destinationSummary").textContent = "离线，无法确认目标垃圾站。";
  $("startBlockReason").textContent = "离线状态下 Start 安全关闭。";
  $("destinationGateBadge").textContent = "未确认目的地";
  $("destinationGateBadge").className = "gate-badge gate-blocked";
  renderPrimaryJourney({});
  Object.keys(ACTIONS).forEach((name) => {
    $(ACTIONS[name].buttonId).disabled = true;
  });
}

function renderStatus(status) {
  latestStatus = status;
  renderReadiness(status);
  renderPrimaryJourney(status);
  renderRecoveryDecision(status);
  renderRouteTaskReview(status);
  renderCloudReadiness(status);
  renderMobileDeviceAcceptance(status);
  renderMobileDeviceEvidence(status);
  renderMobileDeviceHandoffSession(status);
  renderMobilePwaInstallPromptEvidence(status);
  renderMobileRealDeviceEvidenceIntake(status);
  renderMobileRealDeviceAcceptanceDecision(status);
  renderMobileRealDeviceReviewHandoff(status);
  renderMobileRealDeviceReviewExecution(status);
  renderMobileRealDeviceRetestRequest(status);
  renderMobileRealDeviceFieldTrialPackage(status);
  renderMobileRealDeviceFieldTrialReview(status);
  renderMobileRealDeviceFieldTrialRunbookExecution(status);
  renderMobileRealDeviceFieldTrialEvidenceRecord(status);
  renderMobileRealDeviceFieldTrialEvidenceVerdict(status);
  renderMobileRealDeviceFieldTrialRetestExecution(status);
  renderMobileRealDeviceFieldTrialAcceptanceSession(status);
  renderMobileBrowserAcceptanceBundle(status);
  renderTaskFlow(status);
  renderStartConfirmation(status);
  renderCommandSafety(status);
  renderOfflineResume(status);
  renderVoicePrompt(status);
  renderActionFeedback(status);
  renderOperationLog(status);
  renderSupport(status);
  renderTerminalActionPanel();
}

function makeClientReference(actionName) {
  // client_reference 只用于手机端追溯，不携带本地路径、artifact、checksum 或后端秘密。
  return `mobile_web_${actionName}_${Date.now()}`;
}

function buildStartPayload(clientReference) {
  // collect body 是手机确认 envelope，不是 ROS2 action result，也不证明送达成功。
  return {
    schema: "trashbot.mobile_task_start_confirmation.v1",
    schema_version: 1,
    source: "mobile_web",
    destination: latestStartGate.destination,
    target: latestStartGate.destination,
    destination_source: latestStartGate.destinationSource,
    trash_loaded_confirmed: true,
    client_timestamp: new Date().toISOString(),
    client_reference: clientReference,
    evidence_boundary: latestStartGate.evidenceBoundary,
    ack_semantics: "accepted_processing_only_not_delivery_success",
  };
}

function buildGenericActionPayload(actionName, clientReference) {
  // Confirm/Cancel 使用通用手机动作确认 envelope；ACK 仍只是接收/处理中证据。
  return {
    schema: "trashbot.mobile_action_confirmation.v1",
    schema_version: 1,
    source: "mobile_web",
    action: actionName,
    user_confirmed: true,
    client_reference: clientReference,
    client_timestamp: new Date().toISOString(),
    safe_phone_copy: `${actionLabel(actionName)} 已由用户二次确认提交，等待 accepted/processing evidence；这不是 delivery success、dropoff success 或 cancel completed。`,
    ack_semantics: "accepted_processing_only_not_delivery_success",
    evidence_boundary: TERMINAL_ACTION_BOUNDARY,
  };
}

function buildActionPayload(actionName, clientReference) {
  return actionName === "start"
    ? buildStartPayload(clientReference)
    : buildGenericActionPayload(actionName, clientReference);
}

function requestOptionsForAction(actionName, payload) {
  if (!payload) {
    return { method: "POST" };
  }
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

function setLocalActionFeedback(actionName, state, payload, overrides = {}) {
  // 本地反馈只描述手机提交层，不越权写成机器人已执行、已到站或已取消。
  latestActionFeedback = normalizeActionFeedback({
    action: actionName,
    action_copy: actionLabel(actionName),
    submission_status: state,
    safe_phone_copy: overrides.safe_phone_copy || `${actionLabel(actionName)} 已提交，等待 accepted/processing 证据。`,
    failure_reason: overrides.failure_reason || "无本地失败原因；继续等待后端回执。",
    recovery_hint: overrides.recovery_hint || "等待状态刷新；如长时间无 ACK，请打开诊断。",
    client_reference: payload?.client_reference,
    ack_semantics: ACK_PROCESSING_COPY,
    evidence_boundary: ACTION_FEEDBACK_BOUNDARY,
  }, "local");
  renderRecoveryDecision(latestStatus || {});
  renderActionFeedback(latestStatus || {});
}

function renderTerminalActionPanel() {
  const panel = $("terminalActionPanel");
  const badge = $("terminalActionBadge");
  const confirmButton = $("terminalActionConfirmButton");
  const state = pendingTerminalAction;
  if (!state) {
    panel.hidden = true;
    confirmButton.disabled = true;
    return;
  }
  const gate = terminalActionGateFromStatus(latestStatus || {}, state.actionName);
  panel.hidden = false;
  badge.className = "gate-badge";
  badge.classList.add(gate.enabled ? "gate-ready" : "gate-blocked");
  badge.textContent = gate.enabled ? "等待用户确认" : "fail closed";
  $("terminalActionCopy").textContent = safeTerminalActionText(gate.safePhoneCopy);
  $("terminalActionName").textContent = gate.actionCopy;
  $("terminalActionRisk").textContent = safeTerminalActionText(gate.riskCopy);
  $("terminalActionAck").textContent = safeTerminalActionText(gate.ackSemantics, ACK_PROCESSING_COPY);
  $("terminalActionClientReference").textContent = state.clientReference;
  $("terminalActionBoundary").textContent = gate.evidenceBoundary;
  $("terminalActionNotProven").textContent = gate.notProven.join("、");
  $("terminalActionReason").textContent = gate.blockedReason;
  confirmButton.disabled = !gate.enabled;
}

function closeTerminalActionPanel() {
  // 返回只清除本地 pending 确认，不调用 endpoint，也不写成本地失败。
  pendingTerminalAction = null;
  renderTerminalActionPanel();
}

function openTerminalActionConfirmation(actionName) {
  const action = ACTIONS[actionName];
  const button = $(action.buttonId);
  const gate = terminalActionGateFromStatus(latestStatus || {}, actionName);
  if (button.disabled || !gate.enabled) {
    setLocalActionFeedback(actionName, "blocked", null, {
      safe_phone_copy: `${action.label} 未提交；终端动作二次确认 gate fail closed。`,
      failure_reason: gate.blockedReason,
      recovery_hint: "先处理 command_safety、pending ACK、离线、人工接管或 blocked 状态后再试。",
    });
    renderTerminalActionPanel();
    return;
  }
  pendingTerminalAction = {
    actionName,
    clientReference: makeClientReference(actionName),
  };
  renderTerminalActionPanel();
}

async function postAction(actionName, clientReference) {
  const action = ACTIONS[actionName];
  const button = $(action.buttonId);
  const payload = buildActionPayload(actionName, clientReference);
  setLocalActionFeedback(actionName, "submitted", payload);
  button.disabled = true;
  button.textContent = "提交中";
  try {
    const responsePayload = await fetchJson(ENDPOINTS[actionName], requestOptionsForAction(actionName, payload));
    if (responsePayload && typeof responsePayload === "object") {
      latestActionFeedback = normalizeActionFeedback({
        action: actionName,
        action_copy: action.label,
        submission_status: responsePayload.submission_status || responsePayload.status || "accepted_or_processing",
        safe_phone_copy: responsePayload.safe_phone_copy || `${action.label} 请求已被接口接收，等待机器人状态继续更新。`,
        failure_reason: responsePayload.failure_reason || responsePayload.blocking_reason || "接口已返回 accepted/processing 证据；不是完成证明。",
        recovery_hint: responsePayload.recovery_hint || "继续观察任务状态；需要时打开诊断。",
        client_reference: responsePayload.client_reference || payload.client_reference,
        ack_semantics: responsePayload.ack_semantics || ACK_PROCESSING_COPY,
        evidence_boundary: responsePayload.evidence_boundary || payload.evidence_boundary || ACTION_FEEDBACK_BOUNDARY,
      }, "http_success");
      renderActionFeedback(latestStatus || {});
    }
    await refreshStatus();
  } catch (_error) {
    $("commandSafetyCopy").textContent = `${action.label} 提交失败，请打开诊断或稍后重试。`;
    setLocalActionFeedback(actionName, "local_submit_failed", payload, {
      safe_phone_copy: `${action.label} 提交失败；手机端没有收到 accepted/processing 证据。`,
      failure_reason: "HTTP 请求失败或本地网络不可用。",
      recovery_hint: "不要重复点击；先刷新状态，仍失败时打开诊断或联系支持。",
    });
  } finally {
    button.textContent = action.label;
  }
}

async function refreshStatus() {
  try {
    const payload = await fetchJson(ENDPOINTS.status);
    renderStatus(payload);
  } catch (_error) {
    renderOfflineFailure();
  }
}

async function openDiagnostics() {
  try {
    latestDiagnostics = await fetchJson(ENDPOINTS.diagnostics);
    renderPrimaryJourney(latestStatus || {});
    renderRecoveryDecision(latestStatus || {});
    renderRouteTaskReview(latestStatus || {});
    renderMobileDeviceAcceptance(latestStatus || {});
    renderMobileDeviceEvidence(latestStatus || {});
    renderMobileDeviceHandoffSession(latestStatus || {});
    renderMobilePwaInstallPromptEvidence(latestStatus || {});
    renderMobileRealDeviceEvidenceIntake(latestStatus || {});
    renderMobileRealDeviceAcceptanceDecision(latestStatus || {});
    renderMobileRealDeviceReviewHandoff(latestStatus || {});
    renderMobileRealDeviceReviewExecution(latestStatus || {});
    renderMobileRealDeviceRetestRequest(latestStatus || {});
    renderMobileRealDeviceFieldTrialPackage(latestStatus || {});
    renderMobileRealDeviceFieldTrialReview(latestStatus || {});
    renderMobileRealDeviceFieldTrialRunbookExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    renderMobileBrowserAcceptanceBundle(latestStatus || {});
    renderCommandSafety(latestStatus || {});
    renderDiagnosticsSummary(latestDiagnostics);
  } catch (_error) {
    $("supportSafeCopy").textContent = "诊断暂不可用，请稍后重试或联系支持人员。";
  }
}

async function submitAction(actionName) {
  const action = ACTIONS[actionName];
  if (!action) {
    return;
  }
  const button = $(action.buttonId);
  if (button.disabled) {
    return;
  }
  if (["confirm_dropoff", "cancel"].includes(actionName)) {
    openTerminalActionConfirmation(actionName);
    return;
  }
  if (actionName === "start") {
    latestStartGate = startGateFromStatus(latestStatus || {});
    renderStartConfirmation(latestStatus || {});
    if (!latestStartGate.startEnabled) {
      $("commandSafetyCopy").textContent = latestStartGate.blockedReason;
      setLocalActionFeedback(actionName, "blocked", null, {
        safe_phone_copy: "Start 未提交；手机端安全 gate fail closed。",
        failure_reason: latestStartGate.blockedReason,
        recovery_hint: "补齐目的地、垃圾已放入确认和 command_safety 后再试。",
      });
      button.disabled = true;
      return;
    }
  }
  // 控制动作需要人工确认；失败时只提示重试，不做本地重放。
  if (!window.confirm(`${action.label}？请确认现场安全。`)) {
    return;
  }
  await postAction(actionName, makeClientReference(actionName));
}

function wireEvents() {
  $("diagnosticsButton").addEventListener("click", openDiagnostics);
  $("copyRouteTaskReviewButton").addEventListener("click", async () => {
    // operator review 复制只使用后端提供的 safe_copy 白名单对象，缺失时不生成替代 bundle。
    if (!latestRouteTaskReview?.safe_copy_payload) {
      $("routeTaskReviewCopyStatus").textContent = "blocked copy unavailable";
      return;
    }
    const payload = JSON.stringify(latestRouteTaskReview.safe_copy_payload, null, 2);
    $("routeTaskReviewSafeCopy").textContent = payload;
    try {
      await navigator.clipboard.writeText(payload);
      $("routeTaskReviewCopyStatus").textContent = "已复制 route_task_rehearsal_operator_review safe_copy。";
    } catch (_error) {
      $("routeTaskReviewCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyAcceptanceBundleButton").addEventListener("click", async () => {
    const payload = JSON.stringify(bundleCopyPayload(latestAcceptanceBundle || {}), null, 2);
    $("mobileBrowserSafeCopy").textContent = payload;
    // Clipboard 权限不是验收前提；pre 区域始终保留可手动复制的脱敏内容。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileBrowserCopyStatus").textContent = "已复制脱敏验收包。";
    } catch (_error) {
      $("mobileBrowserCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyDeviceEvidencePackageButton").addEventListener("click", async () => {
    const payload = JSON.stringify(deviceEvidencePackageCopyPayload(latestDeviceEvidencePackage || {}), null, 2);
    $("mobileDeviceEvidenceSafeCopy").textContent = payload;
    // 剪贴板失败不影响验收，pre 区域始终保留 phone-safe 手动复制路径。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileDeviceEvidenceCopyStatus").textContent = "已复制脱敏设备证据包。";
    } catch (_error) {
      $("mobileDeviceEvidenceCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyDeviceHandoffPackageButton").addEventListener("click", async () => {
    const payload = JSON.stringify(deviceHandoffPackageCopyPayload(latestDeviceHandoffSession || {}), null, 2);
    $("mobileDeviceHandoffSafeCopy").textContent = payload;
    // 真实手机验收会话需要可转交给支持人员；剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileDeviceHandoffCopyStatus").textContent = "已复制脱敏交接包。";
    } catch (_error) {
      $("mobileDeviceHandoffCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyPwaInstallPromptPackageButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      pwaInstallPromptEvidenceExportCopyPayload(latestPwaInstallPromptEvidenceExportPackage || {}),
      null,
      2,
    );
    $("mobilePwaInstallPromptSafeCopy").textContent = payload;
    // install prompt export 只服务验收复现；剪贴板失败时仍保留手动复制路径。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobilePwaInstallPromptCopyStatus").textContent = "已复制脱敏安装提示证据包。";
    } catch (_error) {
      $("mobilePwaInstallPromptCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("downloadPwaInstallPromptPackageButton").addEventListener("click", () => {
    const payload = JSON.stringify(
      pwaInstallPromptEvidenceExportCopyPayload(latestPwaInstallPromptEvidenceExportPackage || {}),
      null,
      2,
    );
    $("mobilePwaInstallPromptSafeCopy").textContent = payload;
    downloadJsonPackage("mobile_pwa_install_prompt_evidence_export_copy.json", payload);
    $("mobilePwaInstallPromptCopyStatus").textContent = "已生成 whitelist-only 安装提示导出包下载。";
  });
  $("importRealDeviceEvidenceButton").addEventListener("click", () => {
    // 用户导入只接受 JSON 摘要，解析失败或命中敏感字段时保持 blocked-by-design。
    const raw = $("mobileRealDeviceEvidenceImport").value || "";
    try {
      const parsed = JSON.parse(raw);
      const redactedText = JSON.stringify(parsed);
      if (UNSAFE_REAL_DEVICE_TEXT.test(redactedText)) {
        importedRealDeviceEvidence = {
          overall_status: "blocked",
          evidence: { redaction_status: "failed_sensitive_input_filtered" },
          safe_phone_copy: "导入 JSON 含敏感字段，已拒绝复制原文；请提供 redacted phone-safe summary。",
          recovery_hint: "移除 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、/cmd_vel、serial、baudrate、WAVE ROVER、local paths、traceback、checksum、complete artifact 或 raw robot response 后重试。",
        };
      } else {
        importedRealDeviceEvidence = parsed;
      }
      $("mobileRealDeviceEvidenceImportStatus").textContent = "已导入并重新生成 redacted package。";
    } catch (_error) {
      importedRealDeviceEvidence = null;
      $("mobileRealDeviceEvidenceImportStatus").textContent = "JSON 解析失败；继续使用本地 blocked-by-design package。";
    }
    renderMobileRealDeviceEvidenceIntake(latestStatus || {});
    renderMobileRealDeviceAcceptanceDecision(latestStatus || {});
    renderMobileRealDeviceReviewHandoff(latestStatus || {});
    renderMobileRealDeviceReviewExecution(latestStatus || {});
    renderMobileRealDeviceRetestRequest(latestStatus || {});
    renderMobileRealDeviceFieldTrialPackage(latestStatus || {});
    renderMobileRealDeviceFieldTrialReview(latestStatus || {});
    renderMobileRealDeviceFieldTrialRunbookExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    renderCommandSafety(latestStatus || {});
  });
  $("generateRealDeviceEvidenceButton").addEventListener("click", () => {
    // 生成本地 blocked package 便于支持复现，但它不是实机证明或控制放行来源。
    importedRealDeviceEvidence = null;
    $("mobileRealDeviceEvidenceImportStatus").textContent = "已使用当前本地浏览器 metadata 生成 blocked-by-design package。";
    renderMobileRealDeviceEvidenceIntake(latestStatus || {});
    renderMobileRealDeviceAcceptanceDecision(latestStatus || {});
    renderMobileRealDeviceReviewHandoff(latestStatus || {});
    renderMobileRealDeviceReviewExecution(latestStatus || {});
    renderMobileRealDeviceRetestRequest(latestStatus || {});
    renderMobileRealDeviceFieldTrialPackage(latestStatus || {});
    renderMobileRealDeviceFieldTrialReview(latestStatus || {});
    renderMobileRealDeviceFieldTrialRunbookExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
  });
  $("copyRealDeviceEvidencePackageButton").addEventListener("click", async () => {
    const payload = JSON.stringify(realDeviceEvidencePackageCopyPayload(latestRealDeviceEvidencePackage || {}), null, 2);
    $("mobileRealDeviceEvidenceSafeCopy").textContent = payload;
    // 复制失败不影响 intake；pre 区域始终显示最终 redacted phone-safe package。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceEvidenceCopyStatus").textContent = "已复制 redacted phone-safe package。";
    } catch (_error) {
      $("mobileRealDeviceEvidenceCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceAcceptanceDecisionButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceAcceptanceDecisionPackageCopyPayload(latestRealDeviceAcceptanceDecisionPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceAcceptanceDecisionSafeCopy").textContent = payload;
    // 决策包要能转交给 PM/Robot 复核；剪贴板失败时仍保留可手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceAcceptanceDecisionCopyStatus").textContent = "已复制 acceptance decision package。";
    } catch (_error) {
      $("mobileRealDeviceAcceptanceDecisionCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceReviewHandoffButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceReviewHandoffPackageCopyPayload(latestRealDeviceReviewHandoffPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceReviewHandoffSafeCopy").textContent = payload;
    // review handoff package 只给人工评审交接，剪贴板失败时仍能从 pre 手动复制。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceReviewHandoffCopyStatus").textContent = "已复制 review handoff package。";
    } catch (_error) {
      $("mobileRealDeviceReviewHandoffCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceReviewExecutionButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceReviewExecutionPackageCopyPayload(latestRealDeviceReviewExecutionPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceReviewExecutionSafeCopy").textContent = payload;
    // review execution package 只记录人工执行状态；剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceReviewExecutionCopyStatus").textContent = "已复制 review execution package。";
    } catch (_error) {
      $("mobileRealDeviceReviewExecutionCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceRetestRequestButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceRetestRequestPackageCopyPayload(latestRealDeviceRetestRequestPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceRetestRequestSafeCopy").textContent = payload;
    // retest request package 只给下一轮复测排期，剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceRetestRequestCopyStatus").textContent = "已复制 retest request package。";
    } catch (_error) {
      $("mobileRealDeviceRetestRequestCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("generateRealDeviceFieldTrialButton").addEventListener("click", () => {
    // 现场试跑包每次生成都重新读取本地 runtime metadata 和人工 observation，但不创建控制授权。
    stableFieldTrialReference = `field_trial_${Date.now()}`;
    renderMobileRealDeviceFieldTrialPackage(latestStatus || {});
    renderMobileRealDeviceFieldTrialReview(latestStatus || {});
    renderMobileRealDeviceFieldTrialRunbookExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialCopyStatus").textContent = "已生成 mobile_real_device_field_trial_package_summary。";
  });
  $("copyRealDeviceFieldTrialPackageButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialPackageCopyPayload(latestRealDeviceFieldTrialPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialSafeCopy").textContent = payload;
    // field trial package 只给支持/产品收口；剪贴板失败时仍保留 whitelist-only 文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialCopyStatus").textContent = "已复制 mobile_real_device_field_trial_package_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceFieldTrialReviewButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialReviewCopyPayload(latestRealDeviceFieldTrialReviewPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialReviewSafeCopy").textContent = payload;
    // review copy 只给 Product/Support 复核材料缺口；剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialReviewCopyStatus").textContent = "已复制 mobile_real_device_field_trial_review_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialReviewCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("copyRealDeviceFieldTrialRunbookExecutionButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialRunbookExecutionCopyPayload(latestRealDeviceFieldTrialRunbookExecutionPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialRunbookExecutionSafeCopy").textContent = payload;
    // runbook execution copy 只服务现场试跑排程和采证；剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialRunbookExecutionCopyStatus").textContent =
        "已复制 mobile_real_device_field_trial_runbook_execution_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialRunbookExecutionCopyStatus").textContent =
        "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("generateRealDeviceFieldTrialEvidenceRecordButton").addEventListener("click", () => {
    // 现场证据记录每次生成都重新读取 observation fields，但仍固定为 metadata-only。
    stableFieldTrialEvidenceRecordReference = `field_trial_evidence_record_${Date.now()}`;
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialEvidenceRecordCopyStatus").textContent =
      "已生成 mobile_real_device_field_trial_evidence_record_summary。";
  });
  $("copyRealDeviceFieldTrialEvidenceRecordButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialEvidenceRecordCopyPayload(latestRealDeviceFieldTrialEvidenceRecordPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialEvidenceRecordSafeCopy").textContent = payload;
    // evidence record copy 只给 Product/Support 归档，剪贴板失败时仍保留手动复制文本。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialEvidenceRecordCopyStatus").textContent =
        "已复制 mobile_real_device_field_trial_evidence_record_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialEvidenceRecordCopyStatus").textContent =
        "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("archiveRealDeviceFieldTrialEvidenceRecordButton").addEventListener("click", () => {
    // localStorage 只保存 whitelist-only archive package；不可用时仍在页面保留归档文本。
    archivedRealDeviceFieldTrialEvidenceRecordPackage = realDeviceFieldTrialEvidenceRecordArchivePayload(
      latestRealDeviceFieldTrialEvidenceRecordPackage || {},
    );
    const payload = JSON.stringify(archivedRealDeviceFieldTrialEvidenceRecordPackage, null, 2);
    $("mobileRealDeviceFieldTrialEvidenceRecordSafeCopy").textContent = payload;
    try {
      window.localStorage.setItem("mobile_real_device_field_trial_evidence_record_archive", payload);
      $("mobileRealDeviceFieldTrialEvidenceRecordCopyStatus").textContent =
        "已归档 mobile_real_device_field_trial_evidence_record_archive。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialEvidenceRecordCopyStatus").textContent =
        "浏览器无法写入本地归档；请从下方文本框手动保留。";
    }
    renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus || {});
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialEvidenceRecordSafeCopy").textContent = payload;
  });
  $("generateRealDeviceFieldTrialEvidenceVerdictButton").addEventListener("click", () => {
    // verdict 每次生成都重新读取 record/archive 缺口，但仍然只是材料复核 metadata。
    stableFieldTrialEvidenceVerdictReference = `field_trial_evidence_verdict_${Date.now()}`;
    renderMobileRealDeviceFieldTrialEvidenceVerdict(latestStatus || {});
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialEvidenceVerdictCopyStatus").textContent =
      "已生成 mobile_real_device_field_trial_evidence_verdict_summary。";
  });
  $("copyRealDeviceFieldTrialEvidenceVerdictButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialEvidenceVerdictCopyPayload(latestRealDeviceFieldTrialEvidenceVerdictPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy").textContent = payload;
    // verdict copy 只给 Product/Support 安排 retest/material request；剪贴板失败时仍可手动复制。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialEvidenceVerdictCopyStatus").textContent =
        "已复制 mobile_real_device_field_trial_evidence_verdict_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialEvidenceVerdictCopyStatus").textContent =
        "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("generateRealDeviceFieldTrialRetestExecutionButton").addEventListener("click", () => {
    // retest execution 每次生成都从 verdict 的 retest/material request 重建清单，不创建控制授权。
    stableFieldTrialRetestExecutionReference = `field_trial_retest_execution_${Date.now()}`;
    renderMobileRealDeviceFieldTrialRetestExecution(latestStatus || {});
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialRetestExecutionCopyStatus").textContent =
      "已生成 mobile_real_device_field_trial_retest_execution_summary。";
  });
  $("copyRealDeviceFieldTrialRetestExecutionButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialRetestExecutionCopyPayload(latestRealDeviceFieldTrialRetestExecutionPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialRetestExecutionSafeCopy").textContent = payload;
    // retest execution copy 只给 Product/Support 执行复测清单；剪贴板失败时仍可手动复制。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialRetestExecutionCopyStatus").textContent =
        "已复制 mobile_real_device_field_trial_retest_execution_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialRetestExecutionCopyStatus").textContent =
        "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("generateRealDeviceFieldTrialAcceptanceSessionButton").addEventListener("click", () => {
    // acceptance session 每次生成都重新按显式字段、retest、verdict、current PWA proof 的优先级派生。
    stableFieldTrialAcceptanceSessionReference = `field_trial_acceptance_session_${Date.now()}`;
    renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus || {});
    $("mobileRealDeviceFieldTrialAcceptanceSessionCopyStatus").textContent =
      "已生成 mobile_real_device_field_trial_acceptance_session_summary。";
  });
  $("copyRealDeviceFieldTrialAcceptanceSessionButton").addEventListener("click", async () => {
    const payload = JSON.stringify(
      realDeviceFieldTrialAcceptanceSessionCopyPayload(latestRealDeviceFieldTrialAcceptanceSessionPackage || {}),
      null,
      2,
    );
    $("mobileRealDeviceFieldTrialAcceptanceSessionSafeCopy").textContent = payload;
    // acceptance session copy 只用于现场验收会执行，不会提交 ACK、cursor 或控制 endpoint。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobileRealDeviceFieldTrialAcceptanceSessionCopyStatus").textContent =
        "已复制 mobile_real_device_field_trial_acceptance_session_copy。";
    } catch (_error) {
      $("mobileRealDeviceFieldTrialAcceptanceSessionCopyStatus").textContent =
        "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
  });
  $("supportButton").addEventListener("click", () => {
    const bundle = latestStatus?.phone_support_bundle || latestStatus?.phone_readiness?.phone_support_bundle || {};
    $("supportSafeCopy").textContent = safeText(bundle.safe_copy, "暂无脱敏支持摘要。");
  });
  $("terminalActionBackButton").addEventListener("click", closeTerminalActionPanel);
  $("terminalActionConfirmButton").addEventListener("click", async () => {
    if (!pendingTerminalAction) {
      return;
    }
    const { actionName, clientReference } = pendingTerminalAction;
    const gate = terminalActionGateFromStatus(latestStatus || {}, actionName);
    if (!gate.enabled) {
      renderTerminalActionPanel();
      return;
    }
    pendingTerminalAction = null;
    renderTerminalActionPanel();
    await postAction(actionName, clientReference);
  });
  Object.keys(ACTIONS).forEach((name) => {
    $(ACTIONS[name].buttonId).addEventListener("click", () => submitAction(name));
  });
  $("trashLoadedCheckbox").addEventListener("change", () => {
    if (latestStatus) {
      renderPrimaryJourney(latestStatus);
      renderStartConfirmation(latestStatus);
      renderMobileDeviceHandoffSession(latestStatus);
      renderMobileRealDeviceReviewHandoff(latestStatus);
      renderMobileRealDeviceReviewExecution(latestStatus);
      renderMobileRealDeviceRetestRequest(latestStatus);
      renderMobileRealDeviceFieldTrialPackage(latestStatus);
      renderMobileRealDeviceFieldTrialReview(latestStatus);
      renderMobileRealDeviceFieldTrialRunbookExecution(latestStatus);
      renderMobileRealDeviceFieldTrialEvidenceRecord(latestStatus);
      renderMobileRealDeviceFieldTrialAcceptanceSession(latestStatus);
      renderCommandSafety(latestStatus);
    }
  });
}

if ("serviceWorker" in navigator) {
  // 注册范围限制在静态壳；动态控制流量由 service worker 明确绕过缓存。
  navigator.serviceWorker.register("./service-worker.js", { scope: "./" }).catch(() => {});
}

initializePwaInstallPromptEventCapture();
wireEvents();
refreshStatus();
