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
const MOBILE_BROWSER_ACCEPTANCE_BOUNDARY = "software_proof_docker_mobile_browser_acceptance_bundle_gate";
const PRIMARY_JOURNEY_BOUNDARY = "software_proof_docker_mobile_primary_journey_gate";
const RECOVERY_DECISION_BOUNDARY = "software_proof_docker_mobile_recovery_decision_gate";
const ACK_PROCESSING_COPY = "ACK 只代表 accepted/processing evidence，不代表送达成功、投放完成或取消已落地。";
const ACCEPTANCE_BUNDLE_SCHEMA = "trashbot.mobile_browser_acceptance_bundle.v1";
const UNSAFE_BUNDLE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|ros topic|\/cmd_vel|cmd_vel|serial|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/ws\/|traceback|checksum|artifact)/i;
const UNSAFE_RECOVERY_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;

let latestStatus = null;
let latestDiagnostics = null;
let latestActionFeedback = null;
let latestAcceptanceBundle = null;
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
  const cloudAllowsPrimaryActions = cloudSummaryAllowsPrimaryActions(cloudSummary);
  const mobileDeviceAllowsPrimaryActions = mobileDeviceAcceptanceAllowsPrimaryActions(mobileDeviceAcceptance);
  const browserBundleAllowsPrimaryActions = mobileBrowserAcceptanceBundleAllowsPrimaryActions(mobileBrowserAcceptance);
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
    const enabled = actionGate.enabled === true && permitted === true &&
      cloudAllowsPrimaryActions &&
      mobileDeviceAllowsPrimaryActions &&
      browserBundleAllowsPrimaryActions &&
      (startGate ? startGate.startEnabled : true);
    // blocked、离线、等待 ACK、人工接管都会通过 command_safety 关闭按钮。
    button.disabled = !enabled;
    button.dataset.endpoint = ENDPOINTS[name];
    button.title = safeText(actionGate.safe_phone_copy, "后端 gate 未放行。");

    const item = document.createElement("li");
    const reason = name === "start" && startGate
      ? startGate.blockedReason
      : safeText(actionGate.blocking_reason || commandSafety.global_block_reason, "blocked");
    const cloudReason = cloudAllowsPrimaryActions ? "" : "；云中转摘要未放行主操作。";
    const mobileDeviceReason = mobileDeviceAllowsPrimaryActions ? "" : "；手机验收准备未放行主操作。";
    const browserBundleReason = browserBundleAllowsPrimaryActions ? "" : "；浏览器验收包未放行主操作。";
    item.textContent = `${actionMeta.label}：${enabled ? "可操作" : `${reason}${cloudReason}${mobileDeviceReason}${browserBundleReason}`}`;
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
  return entries.slice(0, 7);
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
  renderMobileBrowserAcceptanceBundle(status);
  renderTaskFlow(status);
  renderStartConfirmation(status);
  renderCommandSafety(status);
  renderOfflineResume(status);
  renderVoicePrompt(status);
  renderActionFeedback(status);
  renderOperationLog(status);
  renderSupport(status);
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
    safe_phone_copy: `${actionLabel(actionName)} 已由用户二次确认提交，等待 accepted/processing 证据。`,
    ack_semantics: "accepted_processing_only_not_delivery_success",
    evidence_boundary: ACTION_FEEDBACK_BOUNDARY,
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
  const clientReference = makeClientReference(actionName);
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
        evidence_boundary: responsePayload.evidence_boundary || ACTION_FEEDBACK_BOUNDARY,
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
  $("supportButton").addEventListener("click", () => {
    const bundle = latestStatus?.phone_support_bundle || latestStatus?.phone_readiness?.phone_support_bundle || {};
    $("supportSafeCopy").textContent = safeText(bundle.safe_copy, "暂无脱敏支持摘要。");
  });
  Object.keys(ACTIONS).forEach((name) => {
    $(ACTIONS[name].buttonId).addEventListener("click", () => submitAction(name));
  });
  $("trashLoadedCheckbox").addEventListener("change", () => {
    if (latestStatus) {
      renderPrimaryJourney(latestStatus);
      renderStartConfirmation(latestStatus);
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
