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
const MOBILE_REAL_DEVICE_EVIDENCE_INTAKE_BOUNDARY = "software_proof_docker_mobile_real_device_evidence_intake_gate";
const MOBILE_REAL_DEVICE_ACCEPTANCE_DECISION_BOUNDARY = "software_proof_docker_mobile_real_device_acceptance_decision_gate";
const MOBILE_REAL_DEVICE_REVIEW_HANDOFF_BOUNDARY = "software_proof_docker_mobile_real_device_review_handoff_gate";
const MOBILE_REAL_DEVICE_REVIEW_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_review_execution_gate";
const PRIMARY_JOURNEY_BOUNDARY = "software_proof_docker_mobile_primary_journey_gate";
const RECOVERY_DECISION_BOUNDARY = "software_proof_docker_mobile_recovery_decision_gate";
const TERMINAL_ACTION_BOUNDARY = "software_proof_docker_mobile_terminal_action_confirmation_gate";
const ACK_PROCESSING_COPY = "ACK 只代表 accepted/processing evidence，不代表送达成功、投放完成或取消已落地。";
const DEVICE_EVIDENCE_SCHEMA = "trashbot.mobile_device_evidence_capture.v1";
const DEVICE_EVIDENCE_PACKAGE_SCHEMA = "trashbot.mobile_device_evidence_package.v1";
const DEVICE_HANDOFF_SESSION_SCHEMA = "trashbot.mobile_device_handoff_session.v1";
const DEVICE_HANDOFF_PACKAGE_SCHEMA = "trashbot.mobile_device_handoff_package.v1";
const ACCEPTANCE_BUNDLE_SCHEMA = "trashbot.mobile_browser_acceptance_bundle.v1";
const PWA_INSTALL_PROMPT_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence.v1";
const PWA_INSTALL_PROMPT_SUMMARY_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_summary.v1";
const PWA_INSTALL_PROMPT_PACKAGE_SCHEMA = "trashbot.mobile_pwa_install_prompt_evidence_package.v1";
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
const UNSAFE_BUNDLE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|ros topic|\/cmd_vel|cmd_vel|serial|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/ws\/|traceback|checksum|artifact)/i;
const UNSAFE_RECOVERY_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;
const UNSAFE_TERMINAL_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;
const UNSAFE_REAL_DEVICE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|ttyusb|ttyacm|baudrate|wave rover|wave\s*rover|\/users\/|\/ws\/|\/var\/|traceback|checksum|complete artifact|artifact|raw robot response|robot response|password)/i;

let latestStatus = null;
let latestDiagnostics = null;
let latestActionFeedback = null;
let latestAcceptanceBundle = null;
let latestDeviceEvidencePackage = null;
let latestDeviceHandoffSession = null;
let latestPwaInstallPromptPackage = null;
let latestRealDeviceEvidencePackage = null;
let latestRealDeviceAcceptanceDecisionPackage = null;
let latestRealDeviceReviewHandoffPackage = null;
let latestRealDeviceReviewExecutionPackage = null;
let importedRealDeviceEvidence = null;
let pendingTerminalAction = null;
let stableHandoffClientReference = `mobile_web_handoff_${Date.now()}`;
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

function currentDisplayMode() {
  // display-mode 只能说明当前浏览器上下文，不能证明 production app 或真实 install prompt。
  const modes = ["standalone", "fullscreen", "minimal-ui", "browser"];
  return modes.find((mode) => window.matchMedia && window.matchMedia(`(display-mode: ${mode})`).matches) || "browser";
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

function mobilePwaInstallPromptEvidenceFromStatus(status, readiness, diagnostics) {
  const localEvidence = mobileDeviceEvidencePackageFromStatus(status, readiness, diagnostics);
  const handoffSession = mobileDeviceHandoffSessionFromStatus(status, readiness, diagnostics);
  const browserBundle = mobileBrowserAcceptanceBundleFromStatus(status, readiness, diagnostics);
  const provided = mobilePwaInstallPromptEvidenceCandidate(status, readiness, diagnostics) || {};
  return normalizePwaInstallPromptEvidence(provided, localEvidence, handoffSession, browserBundle);
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
    item.textContent = `${actionMeta.label}：${enabled ? "可操作" : `${reason}${cloudReason}${mobileDeviceReason}${browserBundleReason}${handoffReason}${reviewHandoffReason}${reviewExecutionReason}`}`;
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
  const badge = $("mobilePwaInstallPromptBadge");
  latestPwaInstallPromptPackage = packagePayload;

  badge.className = "gate-badge gate-blocked";
  badge.textContent = packagePayload.install_prompt_capture_status === "captured" &&
    packagePayload.install_prompt_user_outcome !== "not_proven"
    ? "仍需实机复核"
    : "install prompt 未证明";
  $("mobilePwaInstallPromptCopy").textContent = packagePayload.safe_phone_copy;
  $("mobilePwaInstallPromptCapture").textContent = packagePayload.install_prompt_capture_status;
  $("mobilePwaInstallPromptOutcome").textContent = packagePayload.install_prompt_user_outcome;
  $("mobilePwaInstallPromptDisplay").textContent =
    `display=${packagePayload.display_mode} / installability=${packagePayload.installability_status} / offline=${packagePayload.offline_shell_status}`;
  $("mobilePwaInstallPromptShell").textContent =
    `manifest=${packagePayload.manifest_present} / sw=${packagePayload.service_worker_status}`;
  $("mobilePwaInstallPromptControl").textContent =
    `production_app_ready=${packagePayload.production_app_ready} / safe_to_control=${packagePayload.safe_to_control}`;
  $("mobilePwaInstallPromptAck").textContent = packagePayload.ack_semantics;
  $("mobilePwaInstallPromptBoundary").textContent = packagePayload.evidence_boundary;
  $("mobilePwaInstallPromptNotProven").textContent = packagePayload.not_proven.join("、");
  $("mobilePwaInstallPromptRecoveryHint").textContent = packagePayload.recovery_hint;
  $("mobilePwaInstallPromptSafeCopy").textContent =
    JSON.stringify(pwaInstallPromptPackageCopyPayload(packagePayload), null, 2);
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
  const rows = [
    ["软件版本", payload?.software_version],
    ["地图版本", payload?.map_version],
    ["路线版本", payload?.route_version],
    ["当前状态", payload?.latest_status?.phone_copy || payload?.state],
    ["失败原因", payload?.failure?.message || payload?.failure_code],
    ["支持级别", payload?.phone_support_bundle?.support_level],
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
  renderMobileBrowserAcceptanceBundle({});
  renderRecoveryDecision({ connection_state: "offline" });
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
  renderCloudReadiness(status);
  renderMobileDeviceAcceptance(status);
  renderMobileDeviceEvidence(status);
  renderMobileDeviceHandoffSession(status);
  renderMobilePwaInstallPromptEvidence(status);
  renderMobileRealDeviceEvidenceIntake(status);
  renderMobileRealDeviceAcceptanceDecision(status);
  renderMobileRealDeviceReviewHandoff(status);
  renderMobileRealDeviceReviewExecution(status);
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
    renderMobileDeviceAcceptance(latestStatus || {});
    renderMobileDeviceEvidence(latestStatus || {});
    renderMobileDeviceHandoffSession(latestStatus || {});
    renderMobilePwaInstallPromptEvidence(latestStatus || {});
    renderMobileRealDeviceEvidenceIntake(latestStatus || {});
    renderMobileRealDeviceAcceptanceDecision(latestStatus || {});
    renderMobileRealDeviceReviewHandoff(latestStatus || {});
    renderMobileRealDeviceReviewExecution(latestStatus || {});
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
    const payload = JSON.stringify(pwaInstallPromptPackageCopyPayload(latestPwaInstallPromptPackage || {}), null, 2);
    $("mobilePwaInstallPromptSafeCopy").textContent = payload;
    // install prompt evidence 只服务验收复现；剪贴板失败时仍保留手动复制路径。
    try {
      await navigator.clipboard.writeText(payload);
      $("mobilePwaInstallPromptCopyStatus").textContent = "已复制脱敏安装提示证据包。";
    } catch (_error) {
      $("mobilePwaInstallPromptCopyStatus").textContent = "浏览器未授权剪贴板；请从下方文本框手动复制。";
    }
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
      renderCommandSafety(latestStatus);
    }
  });
}

if ("serviceWorker" in navigator) {
  // 注册范围限制在静态壳；动态控制流量由 service worker 明确绕过缓存。
  navigator.serviceWorker.register("./service-worker.js", { scope: "./" }).catch(() => {});
}

wireEvents();
refreshStatus();
