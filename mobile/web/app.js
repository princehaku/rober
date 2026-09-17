const ENDPOINTS = {
  status: "/api/status",
  diagnostics: "/api/diagnostics",
  start: "/api/commands/collect",
  confirm_dropoff: "/api/commands/confirm-dropoff",
  cancel: "/api/commands/cancel",
};


const ACTIONS = {
  start: { buttonId: "startButton", permission: "can_collect", label: "开始送达" },
  confirm_dropoff: { buttonId: "confirmButton", permission: "can_confirm_dropoff", label: "确认投放" },
  cancel: { buttonId: "cancelButton", permission: "can_cancel", label: "取消任务" },
};


const SAFE_EMPTY = "等待后端提供安全摘要。";

const ACTION_FEEDBACK_BOUNDARY = "software_proof_docker_mobile_action_feedback_gate";

const CLOUD_READINESS_BOUNDARY = "software_proof_docker_mobile_cloud_readiness_summary_gate";

const CLOUD_AUTH_FAILURE_STATUS_BOUNDARY = "software_proof_docker_cloud_auth_failure_status_guard";

const CLOUD_AUTH_FAILURE_STATUS_COPY = "登录或访问码未通过；请重新登录或检查凭证；这不是送达成功。";

const CLOUD_MANUAL_TAKEOVER_BOUNDARY = "software_proof_docker_cloud_manual_takeover_command_safety_guard";

const CLOUD_MANUAL_TAKEOVER_COPY = "需要人工接管；远程主操作已暂停，请按现场/支持指引处理。这不是送达成功。";

const CLOUD_CANCEL_PENDING_COMMAND_SAFETY_BOUNDARY = "software_proof_docker_cloud_cancel_pending_command_safety_guard";

const CLOUD_CANCEL_PENDING_COMMAND_SAFETY_COPY = "取消请求已被阻塞在 collect goal 接受窗口；请等待 goal 接受后重试或联系支持。这不是取消完成、送达成功或真实云证明。";

const CLOUD_STATUS_STALE_BOUNDARY = "software_proof_docker_cloud_status_stale_guard";

const CLOUD_STATUS_STALE_COPY = "正在等待小车上报最新状态；当前状态已过期，不能作为送达成功依据。";

const CLOUD_PENDING_ACK_STATUS_BOUNDARY = "software_proof_docker_cloud_pending_ack_status_guard";

const CLOUD_PENDING_ACK_STATUS_COPY = "本地命令已终态，但云端 ACK 还没确认，暂不能拉取新命令";

const CLOUD_ACK_LOOKUP_PENDING_STATUS_BOUNDARY = "software_proof_docker_cloud_ack_lookup_pending_status_guard";

const CLOUD_ACK_LOOKUP_PENDING_STATUS_COPY = "机器人尚未处理该命令；请继续等待或联系支持。这不是失败完成、送达成功，也不能继续发主操作。";

const CLOUD_ACK_ACCEPTED_RESULT_PENDING_BOUNDARY = "software_proof_docker_cloud_ack_accepted_result_pending_guard";

const CLOUD_ACK_ACCEPTED_RESULT_PENDING_COPY = "命令已接收/处理中；尚无真实 delivery、dropoff 或 cancel result。主操作保持禁用，请等待结果或联系支持。";

const CLOUD_TERMINAL_RESULT_VERIFICATION_BOUNDARY = "software_proof_docker_cloud_terminal_result_verification_guard";

const CLOUD_TERMINAL_RESULT_VERIFICATION_COPY = "命令/result 字段存在，但 verified terminal delivery、dropoff 或 cancel result 仍缺失；主操作保持禁用，请等待结果或联系支持。";

const CLOUD_POLL_BACKOFF_RATE_LIMIT_BOUNDARY = "software_proof_docker_cloud_poll_backoff_rate_limit_guard";

const CLOUD_POLL_BACKOFF_RATE_LIMIT_COPY = "远程控制正在等待重试退避窗口；窗口结束前 Start Delivery、Confirm Dropoff、Cancel 保持禁用。";

const CLOUD_COMMAND_EXPIRY_BOUNDARY = "software_proof_docker_cloud_command_expiry_safety_guard";

const CLOUD_COMMAND_EXPIRY_COPY = "云端命令已过期，机器人已忽略旧命令；请重新下发一次安全指令。";

const CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY = "software_proof_docker_cloud_command_idempotency_visibility_guard";

const CLOUD_COMMAND_IDEMPOTENCY_COPY = "重复云指令已去重；机器人没有重复执行；这不是送达成功。";

const CLOUD_COMMAND_ID_CONFLICT_BOUNDARY = "software_proof_docker_cloud_command_id_conflict_visibility_guard";

const CLOUD_COMMAND_ID_CONFLICT_COPY = "命令 ID 冲突；机器人已拒绝执行；这不是送达成功。";

const CLOUD_COMMAND_SEQUENCE_REGRESSION_BOUNDARY = "software_proof_docker_cloud_command_sequence_regression_guard";

const CLOUD_COMMAND_SEQUENCE_REGRESSION_COPY = "命令队列序号倒退；机器人已拒绝按旧顺序推进；这不是送达成功。";

const CLOUD_UNREACHABLE_MALFORMED_RESPONSE_BOUNDARY = "software_proof_docker_cloud_unreachable_malformed_response_guard";

const CLOUD_HOSTED_DEGRADATION_PASSTHROUGH_BOUNDARY = "software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate";

// 云端不可达和响应格式异常都只能解释为只读降级，不能触发手机端重试、ACK/cursor 或主操作。
const CLOUD_UNREACHABLE_MALFORMED_RESPONSE_COPY = {
  cloud_unreachable: "云端暂时不可达；当前不能下发主操作，请刷新状态或联系支持。",
  malformed_response: "云端响应格式异常；机器人没有确认执行，请刷新状态或联系支持。",
};

// 媒体链路降级和云命令失败共用 cloud readiness 面板，避免新增任何手机端控制通道。
const CLOUD_MEDIA_DEGRADATION_BOUNDARY = "software_proof_docker_cloud_media_degradation_status_guard";

// 两类媒体失败都必须显式告诉用户不是送达成功，避免把照片/快照失败误读成任务完成。
const CLOUD_MEDIA_DEGRADATION_COPY = {
  oss_write_failed: "OSS 写失败：媒体没有持久化，远程图片/快照不可作为任务完成依据；这不是送达成功。",
  cdn_unavailable: "CDN 不可达：媒体暂时不能通过公开只读入口获取；这不是送达成功。",
};

const MOBILE_DEVICE_ACCEPTANCE_BOUNDARY = "software_proof_docker_mobile_device_acceptance_readiness_gate";

const MOBILE_DEVICE_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_device_evidence_capture_gate";

const MOBILE_DEVICE_HANDOFF_SESSION_BOUNDARY = "software_proof_docker_mobile_device_handoff_session_gate";

const MOBILE_BROWSER_ACCEPTANCE_BOUNDARY = "software_proof_docker_mobile_browser_acceptance_bundle_gate";

const MOBILE_PWA_INSTALL_PROMPT_BOUNDARY = "software_proof_docker_mobile_pwa_install_prompt_evidence_gate";

const MOBILE_REAL_DEVICE_EVIDENCE_INTAKE_BOUNDARY = "software_proof_docker_mobile_real_device_evidence_intake_gate";

const MOBILE_REAL_DEVICE_ACCEPTANCE_DECISION_BOUNDARY = "software_proof_docker_mobile_real_device_acceptance_decision_gate";

const MOBILE_REAL_DEVICE_REVIEW_HANDOFF_BOUNDARY = "software_proof_docker_mobile_real_device_review_handoff_gate";

const MOBILE_REAL_DEVICE_REVIEW_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_review_execution_gate";

const MOBILE_REAL_DEVICE_RETEST_REQUEST_BOUNDARY = "software_proof_docker_mobile_real_device_retest_request_gate";

const MOBILE_REAL_DEVICE_FIELD_TRIAL_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_package_gate";

const MOBILE_REAL_DEVICE_FIELD_TRIAL_REVIEW_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_review_gate";

const MOBILE_REAL_DEVICE_FIELD_TRIAL_RUNBOOK_EXECUTION_BOUNDARY = "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate";

const PRIMARY_JOURNEY_BOUNDARY = "software_proof_docker_mobile_primary_journey_gate";

const RECOVERY_DECISION_BOUNDARY = "software_proof_docker_mobile_recovery_decision_gate";

const MOBILE_PWA_CACHE_RECOVERY_BOUNDARY = "software_proof_docker_mobile_pwa_cache_recovery_gate";

const TERMINAL_ACTION_BOUNDARY = "software_proof_docker_mobile_terminal_action_confirmation_gate";

const ACK_PROCESSING_COPY = "ACK 只代表 accepted/processing evidence，不代表送达成功、投放完成或取消已落地。";

const ACK_PROCESSING_ENUM = "accepted_processing_only_not_delivery_success";

const CLOUD_PHONE_COMMAND_API_BOUNDARY = "software_proof_docker_cloud_phone_command_api_gate";

const CLOUD_PHONE_COMMAND_API_COPY = "云端命令已入队，等待机器人处理；这不是送达成功、投放完成或取消完成。";

const CLOUD_COMMAND_RESULT_RECONCILIATION_BOUNDARY = "software_proof_docker_cloud_command_result_reconciliation_gate";

const CLOUD_COMMAND_RESULT_RECONCILIATION_COPY = {
  queued: "已入队，等待机器人处理；不是送达成功。",
  processing: "命令已接收/处理中；尚无真实 delivery/dropoff/cancel result。",
  terminal_result_recorded: "命令已返回终态结果，但这只是 software proof；仍不是送达成功。",
  terminal_result_pending: "命令已终态，但 verified terminal result 仍缺失；不是送达成功。",
  terminal_result_conflict: "终态结果与已记录摘要冲突；请联系支持复核同一 command_id。",
  terminal_result_missing: "没有找到这条命令的终态结果；请等待机器人上报或联系支持。",
  store_unavailable: "云端结果存储暂时不可用；请稍后刷新或联系支持。",
  unavailable: "暂时无法确认命令状态；请等待或联系支持。",
};

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

const UNSAFE_BUNDLE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|credential-bearing url|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|uart|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/ws\/|traceback|checksum|complete artifact|artifact|raw browser event|raw event|raw promise|complete ua|full ua|完整 ua|raw robot response|raw intake json|robot\/internal|internal technical)/i;

const UNSAFE_CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_TEXT = /(authorization|bearer|token|github[_ -]?token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|credential|signed url|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|uart|ttyusb|ttyacm|baudrate|wave rover|\/users\/|\/private\/|\/tmp\/|\/ws\/|\/var\/|[a-z]:\\|traceback|checksum|raw artifact|complete artifact|raw json|raw diagnostics|raw status|raw response|raw command|command route|ack route|cursor route|robot\/internal|internal technical|password|ack payload|cursor request|retry request|replay request|resubmit request|robot command|control authorization|safe_to_control\s*=\s*true|delivery[_ ]success(?!\s*=\s*false)|dropoff success|cancel completed|primary_actions_enabled\s*=\s*true|hil_pass|field pass|public https passed|4g passed|oss live traffic passed|production db passed)/i;

const UNSAFE_CLOUD_COMMAND_RESULT_RECONCILIATION_TEXT = UNSAFE_CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_TEXT;

const UNSAFE_RECOVERY_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;

const UNSAFE_TERMINAL_TEXT = /(delivery success|dropoff success|cancel completed|送达已?成功|投放已?完成|取消已?完成|hil_pass|\/cmd_vel|authorization|bearer|token|oss\s*(ak|sk)|database url|queue url|serial|baudrate|wave rover|traceback|checksum|artifact)/i;

const UNSAFE_REAL_DEVICE_TEXT = /(authorization|bearer|token|oss\s*(ak|sk)|access[_-]?key|secret|root password|database url|db url|queue url|https?:\/\/[^\s/]+:[^\s@]+@|raw ros topic|ros topic|\/cmd_vel|cmd_vel|serial|ttyusb|ttyacm|baudrate|wave rover|wave\s*rover|\/users\/|\/private\/|\/tmp\/|\/ws\/|\/var\/|[a-z]:\\|traceback|checksum|complete artifact|artifact|raw robot response|robot response|raw intake json|robot\/internal|internal technical|password)/i;


let latestStatus = null;

let latestDiagnostics = null;

let latestActionFeedback = null;

let latestCloudPhoneCommandReceipt = null;

let latestCloudCommandResultReconciliation = null;

let deferredPwaInstallPromptEvent = null;

let pwaInstallPromptEventState = null;

let importedRealDeviceEvidence = null;

let pendingTerminalAction = null;

let stableHandoffClientReference = `mobile_web_handoff_${Date.now()}`;

let stableFieldTrialReference = `field_trial_${Date.now()}`;

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


function cloudHostedPassthroughBoundary(summary) {
  // hosted /api/status 的本轮证明边界必须透传到页面，不能被历史单状态 guard 覆盖。
  if (!summary || typeof summary !== "object") {
    return "";
  }
  if (summary.proof_boundary === CLOUD_HOSTED_DEGRADATION_PASSTHROUGH_BOUNDARY ||
      summary.evidence_boundary === CLOUD_HOSTED_DEGRADATION_PASSTHROUGH_BOUNDARY) {
    return CLOUD_HOSTED_DEGRADATION_PASSTHROUGH_BOUNDARY;
  }
  return "";
}


function cloudReadinessSummaryFromStatus(status, readiness) {
  // 云摘要只读消费后端 phone-safe 字段，避免前端把配置证明误写成真实云可用。
  const candidates = [
    status?.phone_cloud_readiness_summary,
    status?.mobile_cloud_readiness_summary,
    status?.cloud_readiness_summary,
    status?.remote_readiness,
    status?.remote_status,
    readiness?.cloud_readiness,
    readiness?.remote_readiness,
    readiness?.remote_status,
    readiness?.phone_cloud_readiness_summary,
    readiness?.mobile_cloud_readiness_summary,
    readiness?.cloud_readiness_summary,
    (status?.degradation_state || status?.remote_ready === false) ? status : null,
    (readiness?.degradation_state || readiness?.remote_ready === false) ? readiness : null,
  ];
  const provided = candidates.find((value) => value && typeof value === "object");
  if (provided) {
    const hostedBoundary = cloudHostedPassthroughBoundary(provided);
    if (provided.degradation_state === "auth_failed" ||
        provided.auth_state === "auth_failed" ||
        provided.proof_boundary === CLOUD_AUTH_FAILURE_STATUS_BOUNDARY ||
        provided.evidence_boundary === CLOUD_AUTH_FAILURE_STATUS_BOUNDARY) {
      // auth_failed 只说明登录/访问码没有通过；手机端不能暴露凭证，也不能把失败 ACK 当成送达结果。
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "auth_failed",
        auth_state: "auth_failed",
        db_queue_status: "auth_failed / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "check_auth",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_AUTH_FAILURE_STATUS_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请重新登录或检查访问码/凭证；手机端不重放、不请求 ACK/cursor，也不提交控制动作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "auth_failed_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_AUTH_FAILURE_STATUS_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_AUTH_FAILURE_STATUS_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "manual_takeover_required" ||
        provided.manual_takeover_required === true ||
        provided.proof_boundary === CLOUD_MANUAL_TAKEOVER_BOUNDARY ||
        provided.evidence_boundary === CLOUD_MANUAL_TAKEOVER_BOUNDARY) {
      // manual takeover 说明远程主操作已暂停，手机端只能展示人工接管指引，不能重放、请求下游游标或打开控制。
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "manual_takeover_required",
        degradation_state: "manual_takeover_required",
        manual_takeover_required: true,
        db_queue_status: "manual_takeover_required / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "contact_support",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_MANUAL_TAKEOVER_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请按现场/支持指引人工接管；手机端不重放、不 resubmit、不请求下游确认游标，也不提交控制动作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "manual_takeover_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_MANUAL_TAKEOVER_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_MANUAL_TAKEOVER_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "status_stale" ||
        provided.status_stale === true ||
        provided.proof_boundary === CLOUD_STATUS_STALE_BOUNDARY ||
        provided.evidence_boundary === CLOUD_STATUS_STALE_BOUNDARY) {
      // status_stale 只说明云端看到的小车状态过期；手机端必须等待新状态，不能把旧状态当成可控或成功。
      const statusAgeSeconds = safeText(provided.status_age_seconds, "");
      const staleContext = statusAgeSeconds
        ? `status_age_seconds=${statusAgeSeconds} / remote_ready=false / primary_actions_enabled=false`
        : "status_stale=true / remote_ready=false / primary_actions_enabled=false";
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "status_stale",
        db_queue_status: staleContext,
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        status_stale: true,
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_STATUS_STALE_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请等待机器人重新上报状态或打开 Diagnostics；手机端不重放、不 resubmit，也不提交控制动作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "stale_status_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_STATUS_STALE_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_STATUS_STALE_BOUNDARY,
        status_age_seconds: statusAgeSeconds,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "cancel_pending_goal_acceptance" ||
        provided.capability === "cloud_cancel_pending_command_safety_guard" ||
        provided.proof_boundary === CLOUD_CANCEL_PENDING_COMMAND_SAFETY_BOUNDARY ||
        provided.evidence_boundary === CLOUD_CANCEL_PENDING_COMMAND_SAFETY_BOUNDARY) {
      // cancel_pending_goal_acceptance 只说明取消撞上 collect goal 接受窗口；前端不能把它写成取消完成或送达成功。
      return {
        ...provided,
        missing: false,
        capability: "cloud_cancel_pending_command_safety_guard",
        overall_status: "blocked",
        preflight_status: "cancel_pending_goal_acceptance",
        degradation_state: "cancel_pending_goal_acceptance",
        db_queue_status: "cancel_pending_goal_acceptance / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "wait_for_goal_acceptance",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_CANCEL_PENDING_COMMAND_SAFETY_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "等待 collect goal 接受后再重试 cancel；如果持续阻塞，请联系支持。手机端不自动重放、不 resubmit。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "cancel_pending_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_CANCEL_PENDING_COMMAND_SAFETY_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_CANCEL_PENDING_COMMAND_SAFETY_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "command_pending" ||
        provided.proof_boundary === CLOUD_PENDING_ACK_STATUS_BOUNDARY ||
        provided.evidence_boundary === CLOUD_PENDING_ACK_STATUS_BOUNDARY) {
      // command_pending 代表本地终态命令等待云端 ACK；手机端必须只读展示并维持 fail closed。
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "command_pending",
        db_queue_status: "remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: CLOUD_PENDING_ACK_STATUS_COPY,
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "等待 Robot 成功补发 pending terminal ACK；补发前不要重复提交主操作。",
        ),
        ack_semantics: ACK_PROCESSING_COPY,
        evidence_boundary: hostedBoundary || CLOUD_PENDING_ACK_STATUS_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_PENDING_ACK_STATUS_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "ack_lookup_pending" ||
        provided.capability === "cloud_ack_lookup_pending_status_guard" ||
        provided.proof_boundary === CLOUD_ACK_LOOKUP_PENDING_STATUS_BOUNDARY ||
        provided.evidence_boundary === CLOUD_ACK_LOOKUP_PENDING_STATUS_BOUNDARY) {
      // ack_lookup_pending 只说明 Robot/API 还没查到命令处理结果；手机端必须继续等待或交给支持，不能补发主操作。
      return {
        ...provided,
        missing: false,
        capability: "cloud_ack_lookup_pending_status_guard",
        overall_status: "blocked",
        preflight_status: "ack_lookup_pending",
        degradation_state: "ack_lookup_pending",
        db_queue_status: "ack_lookup_pending / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "continue_polling_or_contact_support",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_ACK_LOOKUP_PENDING_STATUS_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "继续等待 Robot/API 轮询命令处理结果；若长时间未更新，请联系支持。手机端不请求 ACK/cursor、不拉取 raw diagnostics，也不提交控制动作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "ack_lookup_pending_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_ACK_LOOKUP_PENDING_STATUS_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_ACK_LOOKUP_PENDING_STATUS_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "ack_accepted_result_pending" ||
        provided.capability === "cloud_ack_accepted_result_pending_guard" ||
        provided.proof_boundary === CLOUD_ACK_ACCEPTED_RESULT_PENDING_BOUNDARY ||
        provided.evidence_boundary === CLOUD_ACK_ACCEPTED_RESULT_PENDING_BOUNDARY) {
      // ack_accepted_result_pending 只能说明云端 ACK 已 accepted/processing；没有真实 result 前绝不能放开主操作。
      return {
        ...provided,
        missing: false,
        capability: "cloud_ack_accepted_result_pending_guard",
        overall_status: "blocked",
        preflight_status: "ack_accepted_result_pending",
        degradation_state: "ack_accepted_result_pending",
        db_queue_status: "ack_accepted_result_pending / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "wait_for_delivery_result_or_contact_support",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_ACK_ACCEPTED_RESULT_PENDING_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "等待 Robot/API 产出真实 delivery、dropoff 或 cancel result；手机端不请求 ACK/cursor、不拉取 raw diagnostics，也不提交控制动作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "accepted_processing_only_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_ACK_ACCEPTED_RESULT_PENDING_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_ACK_ACCEPTED_RESULT_PENDING_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "terminal_result_pending" ||
        provided.capability === "cloud_terminal_result_verification_guard" ||
        provided.proof_boundary === CLOUD_TERMINAL_RESULT_VERIFICATION_BOUNDARY ||
        provided.evidence_boundary === CLOUD_TERMINAL_RESULT_VERIFICATION_BOUNDARY) {
      // terminal_result_pending 专门处理“result 字段存在但语义未终态”的情况；前端不能把 truthy 字段当成送达证明。
      return {
        ...provided,
        missing: false,
        capability: "cloud_terminal_result_verification_guard",
        overall_status: "blocked",
        preflight_status: "terminal_result_pending",
        degradation_state: "terminal_result_pending",
        // 即使后端返回了 result-like 字段，未 verified 前仍按云端未放行处理。
        db_queue_status: "terminal_result_pending / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "wait_for_verified_terminal_result_or_contact_support",
        // 文案必须直接解释“字段存在但结果缺失”，避免用户把 pending 当完成。
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_TERMINAL_RESULT_VERIFICATION_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "等待 Robot/API 产出 verified terminal delivery、dropoff 或 cancel result；手机端不请求 ACK/cursor、不拉取 raw diagnostics，也不提交控制动作。",
        ),
        // ACK accepted/processing 只保留处理中语义，不能升级成 success 语义。
        ack_semantics: safeText(
          provided.ack_semantics,
          "accepted_processing_only_not_delivery_success",
        ),
        // proof/evidence boundary 透传到页面，便于支持人员区分 Docker 证明和真实云/手机/HIL。
        evidence_boundary: hostedBoundary || CLOUD_TERMINAL_RESULT_VERIFICATION_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_TERMINAL_RESULT_VERIFICATION_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "cloud_poll_backoff" ||
        provided.proof_boundary === CLOUD_POLL_BACKOFF_RATE_LIMIT_BOUNDARY ||
        provided.evidence_boundary === CLOUD_POLL_BACKOFF_RATE_LIMIT_BOUNDARY) {
      // cloud_poll_backoff 只说明远程轮询进入退避/限频窗口；手机端必须等待后端窗口结束，不能主动补发控制。
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "cloud_poll_backoff",
        db_queue_status: "cloud_poll_backoff / remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        retry_hint: "wait_for_backoff_window",
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_POLL_BACKOFF_RATE_LIMIT_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "等待重试退避窗口结束后刷新状态；手机端不自动重放、不 resubmit，也不提交主操作。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "poll_backoff_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_POLL_BACKOFF_RATE_LIMIT_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_POLL_BACKOFF_RATE_LIMIT_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "command_expired" ||
        provided.proof_boundary === CLOUD_COMMAND_EXPIRY_BOUNDARY ||
        provided.evidence_boundary === CLOUD_COMMAND_EXPIRY_BOUNDARY) {
      // command_expired 代表云端旧命令已经被 Robot 忽略；前端只能提示重新下发，不能缓存或重放控制请求。
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "command_expired",
        db_queue_status: "remote_ready=false / primary_actions_enabled=false",
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_COMMAND_EXPIRY_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "旧命令已过期并被忽略；请确认当前状态后重新下发新命令。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "ignored_expired_command_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_COMMAND_EXPIRY_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_COMMAND_EXPIRY_BOUNDARY,
        expired_command_id: safeText(provided.expired_command_id, ""),
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "command_duplicate_deduped" ||
        provided.proof_boundary === CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY ||
        provided.evidence_boundary === CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY) {
      // duplicate cached ACK 只说明重复 command_id 被去重；前端不能把 cached ACK 升格成送达结果。
      const duplicateCommandId = safeText(provided.duplicate_command_id, "");
      const cachedAckState = safeText(provided.cached_ack_state, "cached_ack");
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "command_duplicate_deduped",
        db_queue_status: `duplicate_command_id=${duplicateCommandId || "[redacted]"} / cached_ack_state=${cachedAckState} / remote_ready=false / primary_actions_enabled=false`,
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_COMMAND_IDEMPOTENCY_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "刷新状态确认最新任务；不要自动重放或 resubmit 重复云指令。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "duplicate_cached_ack_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY,
        duplicate_command_id: duplicateCommandId,
        cached_ack_state: cachedAckState,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "command_id_conflict" ||
        provided.proof_boundary === CLOUD_COMMAND_ID_CONFLICT_BOUNDARY ||
        provided.evidence_boundary === CLOUD_COMMAND_ID_CONFLICT_BOUNDARY) {
      // command_id_conflict 代表同一 command.id 携带了不同 type/payload；前端只解释拒绝结果，不发起重放或 ACK/cursor 请求。
      const conflictCommandId = safeText(provided.conflict_command_id, "");
      const conflictReason = safeText(
        provided.conflict_reason,
        "duplicate_id_mismatched_type_or_payload",
      );
      const conflictFields = Array.isArray(provided.conflict_fields)
        ? provided.conflict_fields.map((field) => safeText(field, "")).filter(Boolean).join(",")
        : safeText(provided.conflict_fields, "type,payload");
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "command_id_conflict",
        db_queue_status: `conflict_command_id=${conflictCommandId || "[redacted]"} / conflict_fields=${conflictFields || "type,payload"} / remote_ready=false / primary_actions_enabled=false`,
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_COMMAND_ID_CONFLICT_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请刷新状态或联系支持；手机端不要自动重放、自动 resubmit 或请求 ACK/cursor。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "conflict_rejected_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_COMMAND_ID_CONFLICT_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_COMMAND_ID_CONFLICT_BOUNDARY,
        conflict_command_id: conflictCommandId,
        conflict_reason: conflictReason,
        conflict_fields: conflictFields,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "command_sequence_regression" ||
        provided.proof_boundary === CLOUD_COMMAND_SEQUENCE_REGRESSION_BOUNDARY ||
        provided.evidence_boundary === CLOUD_COMMAND_SEQUENCE_REGRESSION_BOUNDARY) {
      // command_sequence_regression 只说明本地/mock 队列检测到序号倒退；前端不能把拒绝 ACK 当成真实队列顺序证明。
      const regressionCommandId = safeText(provided.regression_command_id, "");
      const observedSequence = safeText(provided.observed_sequence, "");
      const previousSequence = safeText(provided.previous_sequence, "");
      const sequenceContext = [
        regressionCommandId ? `regression_command_id=${regressionCommandId}` : "",
        observedSequence ? `observed_sequence=${observedSequence}` : "",
        previousSequence ? `previous_sequence=${previousSequence}` : "",
      ].filter(Boolean).join(" / ");
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "command_sequence_regression",
        db_queue_status: `${sequenceContext || "sequence_regression_detected"} / remote_ready=false / primary_actions_enabled=false`,
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, CLOUD_COMMAND_SEQUENCE_REGRESSION_COPY),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请刷新状态或联系支持；手机端不要自动重放、自动 resubmit 或请求 ACK/cursor。",
        ),
        ack_semantics: safeText(
          provided.ack_semantics,
          "sequence_regression_not_delivery_success",
        ),
        evidence_boundary: hostedBoundary || CLOUD_COMMAND_SEQUENCE_REGRESSION_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_COMMAND_SEQUENCE_REGRESSION_BOUNDARY,
        regression_command_id: regressionCommandId,
        observed_sequence: observedSequence,
        previous_sequence: previousSequence,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "cloud_unreachable" ||
        provided.degradation_state === "malformed_response" ||
        provided.proof_boundary === CLOUD_UNREACHABLE_MALFORMED_RESPONSE_BOUNDARY ||
        provided.evidence_boundary === CLOUD_UNREACHABLE_MALFORMED_RESPONSE_BOUNDARY) {
      // 云端连接和响应解析失败都不能证明机器人执行，前端只展示安全文案并保持所有主操作关闭。
      const degradationState = provided.degradation_state === "malformed_response"
        ? "malformed_response"
        : "cloud_unreachable";
      const fallbackCopy = CLOUD_UNREACHABLE_MALFORMED_RESPONSE_COPY[degradationState];
      const ackSemantics = degradationState === "malformed_response"
        ? "malformed_response_not_delivery_success"
        : "cloud_unreachable_not_delivery_success";
      const retryHint = degradationState === "malformed_response"
        ? "contact_support"
        : "refresh_status_or_contact_support";
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: degradationState,
        degradation_state: degradationState,
        db_queue_status: `${degradationState} / remote_ready=false / primary_actions_enabled=false`,
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        delivery_success: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, fallbackCopy),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "请刷新状态或联系支持；手机端不重放、不 resubmit、不请求 ACK/cursor，也不提交控制动作。",
        ),
        ack_semantics: safeText(provided.ack_semantics, ackSemantics),
        retry_hint: safeText(provided.retry_hint, retryHint),
        evidence_boundary: hostedBoundary || CLOUD_UNREACHABLE_MALFORMED_RESPONSE_BOUNDARY,
        proof_boundary: hostedBoundary || CLOUD_UNREACHABLE_MALFORMED_RESPONSE_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
    if (provided.degradation_state === "media_degraded" ||
        provided.proof_boundary === CLOUD_MEDIA_DEGRADATION_BOUNDARY ||
        provided.evidence_boundary === CLOUD_MEDIA_DEGRADATION_BOUNDARY) {
      // media_degraded 只说明 OSS/CDN 媒体链路降级；媒体失败不能被解释成送达、投放或远程可用。
      const mediaState = safeText(provided.media_state, "media_degraded");
      // 未知 media_state 也按保守文案处理，保证新增枚举不会意外打开成功语义。
      const fallbackCopy = CLOUD_MEDIA_DEGRADATION_COPY[mediaState] ||
        "媒体链路降级：远程媒体不可作为任务完成依据；这不是送达成功。";
      // ACK 文案只描述媒体持久化/获取失败，不能触发下游 ACK success 或 cursor 推进。
      const ackSemantics = mediaState === "cdn_unavailable"
        ? "media_not_fetchable_not_delivery_success"
        : "media_not_persisted_not_delivery_success";
      return {
        ...provided,
        missing: false,
        overall_status: "blocked",
        preflight_status: "media_degraded",
        media_state: mediaState,
        db_queue_status: `media_state=${mediaState} / remote_ready=false / primary_actions_enabled=false`,
        // 媒体失败属于只读降级状态，所有主操作 gate 必须继续 fail closed。
        production_ready: false,
        primary_actions_enabled: false,
        safe_to_control: false,
        remote_ready: false,
        safe_phone_copy: safeText(provided.safe_phone_copy, fallbackCopy),
        recovery_hint: safeText(
          provided.recovery_hint || provided.retry_hint,
          "媒体链路降级时仅展示只读状态；手机端不重放、不 resubmit、不请求 ACK/cursor，也不提交控制动作。",
        ),
        ack_semantics: safeText(provided.ack_semantics, ackSemantics),
        evidence_boundary: CLOUD_MEDIA_DEGRADATION_BOUNDARY,
        proof_boundary: CLOUD_MEDIA_DEGRADATION_BOUNDARY,
        not_proven: notProvenList(provided.not_proven),
      };
    }
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
    : (Array.isArray(value?.next_required_evidence) ? value.next_required_evidence : handoffPayload.next_required_evidence || []);
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
    next_evidence_request: (nextEvidenceRequest.length ? nextEvidenceRequest : ["真实设备、production app 和真实 PWA install prompt/user choice"])
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


// 缓存只存在于一次同步渲染内，跨状态、诊断变更和用户点击均重新判断。
let activeSafetySnapshot = null;
function sharedSafetyInputs(status, readiness) {
  if (activeSafetySnapshot?.status === status) return activeSafetySnapshot.inputs;
  const cloudSummary = cloudReadinessSummaryFromStatus(status, readiness);
  const mobileDeviceAcceptance = mobileDeviceAcceptanceReadinessFromStatus(status, readiness, latestDiagnostics);
  const mobileBrowserAcceptance = mobileBrowserAcceptanceBundleFromStatus(status, readiness, latestDiagnostics);
  const mobileDeviceHandoff = mobileDeviceHandoffSessionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewHandoff = mobileRealDeviceReviewHandoffFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceReviewExecution = mobileRealDeviceReviewExecutionFromStatus(status, readiness, latestDiagnostics);
  const mobileRealDeviceRetestRequest = mobileRealDeviceRetestRequestFromStatus(status, readiness, latestDiagnostics);
  const inputs = { cloudSummary, mobileDeviceAcceptance, mobileBrowserAcceptance, mobileDeviceHandoff, mobileRealDeviceReviewHandoff, mobileRealDeviceReviewExecution, mobileRealDeviceRetestRequest };
  // 状态页内多个视图共享相同派生对象，避免反复生成验收 fallback 大对象。
  if (activeSafetySnapshot !== null) activeSafetySnapshot = { status, inputs };
  return inputs;
}

function terminalActionGateFromStatus(status, actionName) {
  const readiness = readinessFromStatus(status);
  const commandSafety = commandSafetyFromReadiness(readiness);
  const actions = commandSafety.actions && typeof commandSafety.actions === "object" ? commandSafety.actions : {};
  const actionGate = actions[actionName] && typeof actions[actionName] === "object" ? actions[actionName] : {};
  // 同一轮渲染复用派生输入，安全判定表达式和原后端字段保持不变。
  const { cloudSummary, mobileDeviceAcceptance, mobileBrowserAcceptance, mobileDeviceHandoff, mobileRealDeviceReviewHandoff, mobileRealDeviceReviewExecution, mobileRealDeviceRetestRequest } = sharedSafetyInputs(status, readiness);
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
  // 同一轮渲染复用派生输入，安全判定表达式和原后端字段保持不变。
  const { cloudSummary, mobileDeviceAcceptance, mobileBrowserAcceptance, mobileDeviceHandoff, mobileRealDeviceReviewHandoff, mobileRealDeviceReviewExecution, mobileRealDeviceRetestRequest } = sharedSafetyInputs(status, readiness);
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
  // 同一轮渲染复用派生输入，安全判定表达式和原后端字段保持不变。
  const { cloudSummary, mobileDeviceAcceptance, mobileBrowserAcceptance, mobileDeviceHandoff, mobileRealDeviceReviewHandoff, mobileRealDeviceReviewExecution, mobileRealDeviceRetestRequest } = sharedSafetyInputs(status, readiness);
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
    // 前台轮询不得在控制 POST 尚未完成时重新放开同一组按钮。
    button.disabled = actionRequestInFlight || !enabled;
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


function rerenderPwaInstallPromptEventCapture() {
  // 安装事件只记录轻量状态；诊断模块打开后再更新证据面板。
  window.mobileDiagnostics?.refreshInstallPrompt();
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


function safeRobotIdForCloudCommand(status) {
  // robot_id 是云命令路由字段；缺失时使用保守占位，不读取本地路径、topic 或硬件细节。
  const readiness = readinessFromStatus(status || {});
  return safeText(
    status?.robot_id || status?.robotId || readiness.robot_id || readiness.robotId,
    "trashbot-default",
  );
}


function normalizeCloudPhoneCommandReceipt(value, fallbackAction = "unknown") {
  // receipt 只保留用户可读的入队/等待语义；不展示 token、raw route、ROS topic 或队列内部结构。
  if (!value || typeof value !== "object") {
    return null;
  }
  const actionName = safeText(value.action || value.command || fallbackAction, fallbackAction);
  const state = safeText(
    value.submission_status || value.receipt_status || value.status || value.ack_state,
    "queued",
  );
  return {
    capability: safeText(value.capability, "cloud_phone_command_api"),
    action: actionName,
    actionCopy: safeText(value.action_copy || value.label, actionLabel(actionName)),
    state,
    commandId: safeText(value.safe_command_id || value.command_id || value.request_id, "未提供"),
    robotId: safeText(value.robot_id || value.safe_robot_id, "未提供"),
    clientReference: safeText(value.client_reference || value.idempotency_key, "未提供"),
    ackSemantics: safeText(value.ack_semantics, "queued_not_delivery_success"),
    safePhoneCopy: safeText(value.safe_phone_copy || value.summary, CLOUD_PHONE_COMMAND_API_COPY),
    recoveryHint: safeText(value.recovery_hint || value.next_action || value.retry_hint, "等待机器人处理；长时间无更新时打开诊断或联系支持。"),
    evidenceBoundary: safeText(value.evidence_boundary || value.proof_boundary, CLOUD_PHONE_COMMAND_API_BOUNDARY),
    deliverySuccess: value.delivery_success === true ? false : false,
    primaryActionsEnabled: value.primary_actions_enabled === true ? false : false,
    safeToControl: value.safe_to_control === true ? false : false,
  };
}


function cloudPhoneCommandReceiptFromStatus(status, readiness) {
  // 后端可通过 status/readiness 回传上次 receipt；缺失时保留本地提交后的 receipt。
  const candidates = [
    status?.cloud_phone_command_receipt,
    status?.mobile_action_receipt,
    status?.phone_action_feedback,
    readiness?.cloud_phone_command_receipt,
    readiness?.mobile_action_receipt,
    readiness?.phone_action_feedback,
  ];
  const provided = candidates.find((value) => value && typeof value === "object" &&
    safeText(value.capability, "") === "cloud_phone_command_api");
  return provided ? normalizeCloudPhoneCommandReceipt(provided, "unknown") : latestCloudPhoneCommandReceipt;
}


function ensureCloudPhoneCommandReceiptPanel() {
  // 本轮只改 app.js，所以 receipt panel 用运行时注入；它只读展示回执，不新增控制按钮。
  let panel = $("cloudPhoneCommandReceiptPanel");
  if (panel) {
    return panel;
  }
  const anchor = $("actionFeedbackStatusBadge")?.closest("section") ||
    $("terminalActionPanel") ||
    $("primaryJourneyTitle")?.closest("section");
  if (!anchor || !anchor.parentElement) {
    return null;
  }
  panel = document.createElement("section");
  panel.id = "cloudPhoneCommandReceiptPanel";
  panel.className = "cloud-phone-command-receipt-panel";
  panel.setAttribute("aria-labelledby", "cloudPhoneCommandReceiptTitle");
  panel.innerHTML = `
    <div class="section-heading">
      <h2 id="cloudPhoneCommandReceiptTitle">云端指令回执</h2>
      <span id="cloudPhoneCommandReceiptBadge" class="gate-badge gate-blocked">等待回执</span>
    </div>
    <p id="cloudPhoneCommandReceiptCopy" class="message">提交 Start、Confirm 或 Cancel 后，这里只显示 cloud_phone_command_api 的 phone-safe receipt。</p>
    <dl class="cloud-phone-command-receipt-grid">
      <div><dt>Capability</dt><dd id="cloudPhoneCommandReceiptCapability">cloud_phone_command_api</dd></div>
      <div><dt>动作 / 状态</dt><dd id="cloudPhoneCommandReceiptState">暂无提交</dd></div>
      <div><dt>Safe Command ID</dt><dd id="cloudPhoneCommandReceiptCommandId">未提供</dd></div>
      <div><dt>Robot ID</dt><dd id="cloudPhoneCommandReceiptRobotId">未提供</dd></div>
      <div><dt>Client Reference</dt><dd id="cloudPhoneCommandReceiptClientReference">未提供</dd></div>
      <div><dt>ACK Semantics</dt><dd id="cloudPhoneCommandReceiptAck">queued_not_delivery_success</dd></div>
      <div><dt>Control Boundary</dt><dd id="cloudPhoneCommandReceiptControls">delivery_success=false / primary_actions_enabled=false / safe_to_control=false</dd></div>
      <div><dt>Evidence Boundary</dt><dd id="cloudPhoneCommandReceiptBoundary">software_proof_docker_cloud_phone_command_api_gate</dd></div>
    </dl>
    <p id="cloudPhoneCommandReceiptRecovery" class="hint">入队只代表等待机器人处理；不是送达成功。</p>
  `;
  anchor.insertAdjacentElement("afterend", panel);
  return panel;
}


function renderCloudPhoneCommandReceipt(status) {
  const panel = ensureCloudPhoneCommandReceiptPanel();
  if (!panel) {
    return;
  }
  const readiness = readinessFromStatus(status || {});
  const receipt = cloudPhoneCommandReceiptFromStatus(status || {}, readiness);
  const badge = $("cloudPhoneCommandReceiptBadge");
  if (!receipt) {
    badge.className = "gate-badge gate-blocked";
    badge.textContent = "等待回执";
    $("cloudPhoneCommandReceiptCopy").textContent = "提交 Start、Confirm 或 Cancel 后，这里只显示 cloud_phone_command_api 的 phone-safe receipt。";
    $("cloudPhoneCommandReceiptState").textContent = "暂无提交";
    $("cloudPhoneCommandReceiptCommandId").textContent = "未提供";
    $("cloudPhoneCommandReceiptRobotId").textContent = "未提供";
    $("cloudPhoneCommandReceiptClientReference").textContent = "未提供";
    $("cloudPhoneCommandReceiptAck").textContent = "queued_not_delivery_success";
    $("cloudPhoneCommandReceiptRecovery").textContent = "入队只代表等待机器人处理；不是送达成功。";
    return;
  }
  latestCloudPhoneCommandReceipt = receipt;
  badge.className = "gate-badge gate-waiting";
  badge.textContent = "已入队";
  $("cloudPhoneCommandReceiptCapability").textContent = receipt.capability;
  $("cloudPhoneCommandReceiptCopy").textContent = receipt.safePhoneCopy;
  $("cloudPhoneCommandReceiptState").textContent = `${receipt.actionCopy} / ${receipt.state}`;
  $("cloudPhoneCommandReceiptCommandId").textContent = receipt.commandId;
  $("cloudPhoneCommandReceiptRobotId").textContent = receipt.robotId;
  $("cloudPhoneCommandReceiptClientReference").textContent = receipt.clientReference;
  $("cloudPhoneCommandReceiptAck").textContent = receipt.ackSemantics;
  $("cloudPhoneCommandReceiptControls").textContent =
    `delivery_success=${receipt.deliverySuccess} / primary_actions_enabled=${receipt.primaryActionsEnabled} / safe_to_control=${receipt.safeToControl}`;
  $("cloudPhoneCommandReceiptBoundary").textContent = receipt.evidenceBoundary;
  $("cloudPhoneCommandReceiptRecovery").textContent = receipt.recoveryHint;
}


function safeCloudCommandResultReconciliationText(value, fallback = "not_proven") {
  // lifecycle summary 只展示同源 safe contract；命中 raw route、凭证或成功语义时 fail closed。
  const text = safeText(value, fallback);
  return UNSAFE_CLOUD_COMMAND_RESULT_RECONCILIATION_TEXT.test(text) ? fallback : text;
}


function cloudCommandResultReconciliationCandidates(status, readiness, diagnostics) {
  const diagnosticsReadiness = readinessFromStatus(diagnostics || {});
  const diagnosticsSummary = diagnostics && typeof diagnostics.summary === "object" ? diagnostics.summary : {};
  const nestedDiagnostics = diagnostics && typeof diagnostics.diagnostics === "object" ? diagnostics.diagnostics : {};
  const nestedDiagnosticsSummary = nestedDiagnostics && typeof nestedDiagnostics.summary === "object"
    ? nestedDiagnostics.summary
    : {};
  const statusDiagnostics = status && typeof status.diagnostics === "object" ? status.diagnostics : {};
  const statusDiagnosticsSummary = statusDiagnostics && typeof statusDiagnostics.summary === "object"
    ? statusDiagnostics.summary
    : {};
  const artifact = status?.cloud_command_result_reconciliation?.summary ||
    readiness?.cloud_command_result_reconciliation?.summary ||
    diagnostics?.cloud_command_result_reconciliation?.summary ||
    diagnosticsSummary.cloud_command_result_reconciliation?.summary ||
    nestedDiagnosticsSummary.cloud_command_result_reconciliation?.summary ||
    statusDiagnosticsSummary.cloud_command_result_reconciliation?.summary;
  const directCandidates = [
    status?.robot_diagnostics_cloud_command_result_reconciliation_summary,
    readiness?.robot_diagnostics_cloud_command_result_reconciliation_summary,
    diagnostics?.robot_diagnostics_cloud_command_result_reconciliation_summary,
    diagnosticsReadiness.robot_diagnostics_cloud_command_result_reconciliation_summary,
    diagnosticsSummary.robot_diagnostics_cloud_command_result_reconciliation_summary,
    nestedDiagnosticsSummary.robot_diagnostics_cloud_command_result_reconciliation_summary,
    statusDiagnosticsSummary.robot_diagnostics_cloud_command_result_reconciliation_summary,
    status?.cloud_command_result_reconciliation_summary,
    readiness?.cloud_command_result_reconciliation_summary,
    diagnostics?.cloud_command_result_reconciliation_summary,
    diagnosticsReadiness.cloud_command_result_reconciliation_summary,
    diagnosticsSummary.cloud_command_result_reconciliation_summary,
    nestedDiagnosticsSummary.cloud_command_result_reconciliation_summary,
    statusDiagnosticsSummary.cloud_command_result_reconciliation_summary,
    artifact,
  ];
  const listCandidates = [
    status?.robot_diagnostics_cloud_command_result_reconciliation_summaries,
    readiness?.robot_diagnostics_cloud_command_result_reconciliation_summaries,
    diagnostics?.robot_diagnostics_cloud_command_result_reconciliation_summaries,
    diagnosticsSummary.robot_diagnostics_cloud_command_result_reconciliation_summaries,
    status?.cloud_command_result_reconciliation_summaries,
    readiness?.cloud_command_result_reconciliation_summaries,
    diagnostics?.cloud_command_result_reconciliation_summaries,
    diagnosticsSummary.cloud_command_result_reconciliation_summaries,
    status?.cloud_command_result_reconciliation?.lifecycle_summaries,
    readiness?.cloud_command_result_reconciliation?.lifecycle_summaries,
    diagnostics?.cloud_command_result_reconciliation?.lifecycle_summaries,
    diagnosticsSummary.cloud_command_result_reconciliation?.lifecycle_summaries,
  ];
  return [
    ...directCandidates.filter((value) => value && typeof value === "object" && !Array.isArray(value)),
    ...listCandidates.flatMap((value) => Array.isArray(value) ? value : [])
      .filter((value) => value && typeof value === "object" && !Array.isArray(value)),
  ];
}


function selectedCloudCommandResultReconciliation(status, readiness, diagnostics, commandId) {
  const requestedId = safeCloudCommandResultReconciliationText(commandId, "");
  const candidates = cloudCommandResultReconciliationCandidates(status, readiness, diagnostics);
  return candidates.find((candidate) => {
    const candidateId = safeCloudCommandResultReconciliationText(
      candidate.safe_command_id || candidate.command_id,
      "",
    );
    return requestedId && candidateId === requestedId;
  }) || candidates[0] || null;
}


function normalizeCloudCommandResultReconciliation(value, requestedCommandId) {
  // terminal ACK 只能说明命令生命周期结束；没有 verified terminal result 仍不能写成送达成功。
  const requestedId = safeCloudCommandResultReconciliationText(requestedCommandId, "");
  const lifecycleState = safeCloudCommandResultReconciliationText(
    value?.lifecycle_state ||
      value?.command_state ||
      value?.result_state ||
      value?.degradation_state,
    "unavailable",
  );
  const terminalState = safeCloudCommandResultReconciliationText(
    value?.terminal_result_status || value?.verified_terminal_result_status,
    "",
  );
  const state = lifecycleState !== "unavailable" ? lifecycleState : (terminalState || "unavailable");
  let bucket = "unavailable";
  if (state.includes("terminal_result_recorded") || state.includes("recorded")) {
    bucket = "terminal_result_recorded";
  } else if (state.includes("terminal_result_conflict") || state.includes("conflict")) {
    bucket = "terminal_result_conflict";
  } else if (state.includes("store_unavailable")) {
    bucket = "store_unavailable";
  } else if (state.includes("terminal_result_missing") || state.includes("missing_or_expired") || state.includes("missing")) {
    bucket = "terminal_result_missing";
  } else if (state.includes("queued")) {
    bucket = "queued";
  } else if (state.includes("processing") || state.includes("accepted")) {
    bucket = "processing";
  } else if (state.includes("terminal_result_pending") || state.includes("terminal")) {
    bucket = "terminal_result_pending";
  }
  const fallbackCopy = CLOUD_COMMAND_RESULT_RECONCILIATION_COPY[bucket] ||
    CLOUD_COMMAND_RESULT_RECONCILIATION_COPY.unavailable;
  const resultType = safeCloudCommandResultReconciliationText(
    value?.terminal_result_type || value?.result_type,
    bucket === "terminal_result_recorded" ? "delivery_terminal" : "not_recorded",
  );
  const resultCode = safeCloudCommandResultReconciliationText(
    value?.result_code,
    bucket === "terminal_result_recorded" ? "task_terminal_recorded_software_proof" : "not_available",
  );
  const errorCode = safeCloudCommandResultReconciliationText(
    value?.error_code,
    bucket === "terminal_result_conflict" ? "terminal_result_conflict" : "none",
  );
  return {
    capability: safeCloudCommandResultReconciliationText(
      value?.capability,
      "cloud_command_result_reconciliation",
    ),
    commandId: safeCloudCommandResultReconciliationText(
      value?.safe_command_id || value?.command_id || requestedId,
      requestedId || "未提供",
    ),
    lifecycleState: bucket,
    lifecycleStatus: safeCloudCommandResultReconciliationText(value?.lifecycle_status || lifecycleState, state),
    safePhoneCopy: safeCloudCommandResultReconciliationText(value?.safe_phone_copy || value?.summary, fallbackCopy),
    ackSemantics: safeCloudCommandResultReconciliationText(
      value?.ack_semantics,
      bucket === "queued" ? "queued_not_delivery_success" : "accepted_processing_only_not_delivery_success",
    ),
    terminalResultStatus: safeCloudCommandResultReconciliationText(
      terminalState,
      bucket === "terminal_result_recorded" ? "terminal_result_recorded"
        : (bucket === "terminal_result_pending" ? "terminal_result_pending"
          : (bucket === "terminal_result_conflict" ? "terminal_result_conflict"
            : (bucket === "terminal_result_missing" ? "terminal_result_missing"
              : (bucket === "store_unavailable" ? "store_unavailable" : "not_verified")))),
    ),
    terminalResultType: resultType,
    resultCode,
    errorCode,
    safeEvidenceRef: safeCloudCommandResultReconciliationText(
      value?.safe_evidence_ref || value?.evidence_ref,
      "evidence_ref=not_provided",
    ),
    nextRequiredEvidence: safeCloudCommandResultReconciliationText(
      value?.next_required_evidence,
      "next_required_evidence=真实 field/HIL/送达材料、同一 safe evidence_ref、真实手机/browser proof。",
    ),
    recoveryHint: safeCloudCommandResultReconciliationText(
      value?.recovery_hint || value?.retry_hint || value?.next_action,
      (bucket === "unavailable" || bucket === "store_unavailable" || bucket === "terminal_result_missing")
        ? fallbackCopy
        : "等待同一 command_id 的真实现场材料；不要重放、重复提交或请求 ACK cursor。",
    ),
    evidenceBoundary: safeCloudCommandResultReconciliationText(
      value?.evidence_boundary || value?.proof_boundary,
      CLOUD_COMMAND_RESULT_RECONCILIATION_BOUNDARY,
    ),
    deliverySuccess: false,
    primaryActionsEnabled: false,
    safeToControl: false,
  };
}


function cloudCommandResultReconciliationFromStatus(status, readiness, diagnostics) {
  const inputId = $("cloudCommandResultReconciliationCommandId")?.value ||
    latestCloudPhoneCommandReceipt?.commandId ||
    "";
  const provided = selectedCloudCommandResultReconciliation(status, readiness, diagnostics, inputId);
  return normalizeCloudCommandResultReconciliation(provided, inputId);
}


function ensureCloudCommandResultReconciliationPanel() {
  // 查询入口只刷新安全状态摘要；不请求底层诊断、不 replay、不 resubmit。
  let panel = $("cloudCommandResultReconciliationPanel");
  if (panel) {
    return panel;
  }
  const anchor = $("cloudPhoneCommandReceiptPanel") ||
    $("actionFeedbackStatusBadge")?.closest("section") ||
    $("terminalActionPanel") ||
    $("primaryJourneyTitle")?.closest("section");
  if (!anchor || !anchor.parentElement) {
    return null;
  }
  panel = document.createElement("section");
  panel.id = "cloudCommandResultReconciliationPanel";
  panel.className = "cloud-command-result-reconciliation-panel";
  panel.setAttribute("aria-labelledby", "cloudCommandResultReconciliationTitle");
  panel.innerHTML = `
    <div class="section-heading">
      <h2 id="cloudCommandResultReconciliationTitle">命令结果核对</h2>
      <span id="cloudCommandResultReconciliationBadge" class="gate-badge gate-blocked">等待查询</span>
    </div>
    <p id="cloudCommandResultReconciliationCopy" class="message">输入 Safe Command ID 后刷新同源 lifecycle summary；不会重放、重复提交或拉取底层诊断。</p>
    <label for="cloudCommandResultReconciliationCommandId">Safe Command ID</label>
    <input id="cloudCommandResultReconciliationCommandId" type="text" autocomplete="off" placeholder="cmd_mobile_web_start_001">
    <button id="cloudCommandResultReconciliationRefreshButton" type="button">刷新 lifecycle summary</button>
    <dl class="cloud-command-result-reconciliation-grid">
      <div><dt>Capability</dt><dd id="cloudCommandResultReconciliationCapability">cloud_command_result_reconciliation</dd></div>
      <div><dt>Lifecycle State</dt><dd id="cloudCommandResultReconciliationState">unavailable</dd></div>
      <div><dt>Safe Command ID</dt><dd id="cloudCommandResultReconciliationSafeCommandId">未提供</dd></div>
      <div><dt>ACK Semantics</dt><dd id="cloudCommandResultReconciliationAck">accepted_processing_only_not_delivery_success</dd></div>
      <div><dt>Terminal Result</dt><dd id="cloudCommandResultReconciliationTerminal">not_verified</dd></div>
      <div><dt>Result Type</dt><dd id="cloudCommandResultReconciliationResultType">not_recorded</dd></div>
      <div><dt>Result Code</dt><dd id="cloudCommandResultReconciliationResultCode">not_available</dd></div>
      <div><dt>Error Code</dt><dd id="cloudCommandResultReconciliationErrorCode">none</dd></div>
      <div><dt>Safe Evidence Ref</dt><dd id="cloudCommandResultReconciliationEvidenceRef">evidence_ref=not_provided</dd></div>
      <div><dt>Next Required Evidence</dt><dd id="cloudCommandResultReconciliationNextEvidence">真实 field/HIL/送达材料</dd></div>
      <div><dt>Control Boundary</dt><dd id="cloudCommandResultReconciliationControls">delivery_success=false / primary_actions_enabled=false / safe_to_control=false</dd></div>
      <div><dt>Evidence Boundary</dt><dd id="cloudCommandResultReconciliationBoundary">software_proof_docker_cloud_command_result_reconciliation_gate</dd></div>
    </dl>
    <p id="cloudCommandResultReconciliationRecovery" class="hint">暂时无法确认命令状态；请等待或联系支持。</p>
  `;
  anchor.insertAdjacentElement("afterend", panel);
  $("cloudCommandResultReconciliationRefreshButton")?.addEventListener("click", refreshCloudCommandResultReconciliation);
  return panel;
}


function renderCloudCommandResultReconciliation(status) {
  const panel = ensureCloudCommandResultReconciliationPanel();
  if (!panel) {
    return;
  }
  const readiness = readinessFromStatus(status || {});
  const summary = cloudCommandResultReconciliationFromStatus(status || {}, readiness, latestDiagnostics || {});
  latestCloudCommandResultReconciliation = summary;
  const input = $("cloudCommandResultReconciliationCommandId");
  if (input && !input.value && summary.commandId !== "未提供") {
    input.value = summary.commandId;
  }
  const badge = $("cloudCommandResultReconciliationBadge");
  badge.className = "gate-badge";
  badge.classList.add(summary.lifecycleState === "unavailable" ? "gate-blocked" : "gate-waiting");
  badge.textContent = summary.lifecycleState === "terminal_result_recorded"
    ? "已记录终态"
    : (summary.lifecycleState === "unavailable" ? "无法确认" : "等待结果");
  $("cloudCommandResultReconciliationCapability").textContent = summary.capability;
  $("cloudCommandResultReconciliationCopy").textContent = summary.safePhoneCopy;
  $("cloudCommandResultReconciliationState").textContent = summary.lifecycleStatus;
  $("cloudCommandResultReconciliationSafeCommandId").textContent = summary.commandId;
  $("cloudCommandResultReconciliationAck").textContent = summary.ackSemantics;
  $("cloudCommandResultReconciliationTerminal").textContent = summary.terminalResultStatus;
  $("cloudCommandResultReconciliationResultType").textContent = summary.terminalResultType;
  $("cloudCommandResultReconciliationResultCode").textContent = summary.resultCode;
  $("cloudCommandResultReconciliationErrorCode").textContent = summary.errorCode;
  $("cloudCommandResultReconciliationEvidenceRef").textContent = summary.safeEvidenceRef;
  $("cloudCommandResultReconciliationNextEvidence").textContent = summary.nextRequiredEvidence;
  $("cloudCommandResultReconciliationControls").textContent =
    `delivery_success=${summary.deliverySuccess} / primary_actions_enabled=${summary.primaryActionsEnabled} / safe_to_control=${summary.safeToControl}`;
  $("cloudCommandResultReconciliationBoundary").textContent = summary.evidenceBoundary;
  $("cloudCommandResultReconciliationRecovery").textContent = summary.recoveryHint;
}


async function refreshCloudCommandResultReconciliation() {
  // 手动刷新只重新读取现有 status safe summary，不自动重放、不 resubmit、不请求底层诊断。
  await refreshStatus();
  renderCloudCommandResultReconciliation(latestStatus || {});
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


function renderOfflineFailure() {
  latestStatus = null;
  // 读取失败同时撤销未提交的二次确认，避免界面继续展示旧授权。
  pendingTerminalAction = null;
  renderTerminalActionPanel();
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
  renderCloudPhoneCommandReceipt({});
  renderCloudCommandResultReconciliation({});
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
  activeSafetySnapshot = {};
  try {
    renderReadiness(status);
    renderPrimaryJourney(status);
    renderRecoveryDecision(status);
    renderTaskFlow(status);
    renderStartConfirmation(status);
    renderCommandSafety(status);
    renderOfflineResume(status);
    renderVoicePrompt(status);
    renderActionFeedback(status);
    renderCloudPhoneCommandReceipt(status);
    renderCloudCommandResultReconciliation(status);
    renderOperationLog(status);
    renderSupport(status);
    renderTerminalActionPanel();
  } finally {
    // 绝不把本次快照当作下一次控制授权或后台状态缓存。
    activeSafetySnapshot = null;
  }
}


function makeClientReference(actionName) {
  // client_reference 只用于手机端追溯，不携带本地路径、artifact、checksum 或后端秘密。
  return `mobile_web_${actionName}_${Date.now()}`;
}


function commandTypeForAction(actionName) {
  // UI 动作名映射到云端任务级 command_type，不暴露任何 ROS topic 或底盘控制细节。
  if (actionName === "confirm_dropoff") {
    return "confirm_dropoff";
  }
  return actionName === "cancel" ? "cancel" : "collect";
}


function cloudPhoneCommandEnvelope(actionName, clientReference, taskPayload) {
  // cloud_phone_command_api envelope 是手机到云的任务请求；入队回执不是机器人终态。
  return {
    schema: "trashbot.cloud_phone_command_api_request.v1",
    schema_version: 1,
    capability: "cloud_phone_command_api",
    source: "mobile_web",
    robot_id: safeRobotIdForCloudCommand(latestStatus || {}),
    command_type: commandTypeForAction(actionName),
    command_id: clientReference,
    idempotency_key: clientReference,
    client_reference: clientReference,
    client_timestamp: new Date().toISOString(),
    payload: taskPayload,
    safe_phone_copy: CLOUD_PHONE_COMMAND_API_COPY,
    ack_semantics: "queued_not_delivery_success",
    evidence_boundary: CLOUD_PHONE_COMMAND_API_BOUNDARY,
    delivery_success: false,
    primary_actions_enabled: false,
    safe_to_control: false,
  };
}


function buildStartPayload(clientReference) {
  // collect body 是手机确认 envelope，不是 ROS2 action result，也不证明送达成功。
  const taskPayload = {
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
  return {
    ...cloudPhoneCommandEnvelope("start", clientReference, taskPayload),
    destination: taskPayload.destination,
    target: taskPayload.target,
    trash_loaded_confirmed: taskPayload.trash_loaded_confirmed,
  };
}


function buildGenericActionPayload(actionName, clientReference) {
  // Confirm/Cancel 使用通用手机动作确认 envelope；ACK 仍只是接收/处理中证据。
  const taskPayload = {
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
  return cloudPhoneCommandEnvelope(actionName, clientReference, taskPayload);
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
  latestCloudPhoneCommandReceipt = normalizeCloudPhoneCommandReceipt({
    capability: "cloud_phone_command_api",
    action: actionName,
    action_copy: actionLabel(actionName),
    submission_status: state === "submitted" ? "queued_waiting_robot" : state,
    safe_command_id: payload?.command_id,
    robot_id: payload?.robot_id,
    client_reference: payload?.client_reference,
    ack_semantics: "queued_not_delivery_success",
    safe_phone_copy: overrides.safe_phone_copy || CLOUD_PHONE_COMMAND_API_COPY,
    recovery_hint: overrides.recovery_hint || "等待机器人处理；如长时间无 ACK，请打开诊断。",
    evidence_boundary: CLOUD_PHONE_COMMAND_API_BOUNDARY,
    delivery_success: false,
    primary_actions_enabled: false,
    safe_to_control: false,
  }, actionName);
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
  renderCloudPhoneCommandReceipt(latestStatus || {});
  renderCloudCommandResultReconciliation(latestStatus || {});
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
  confirmButton.disabled = actionRequestInFlight || !gate.enabled;
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


// 动作只由人工触发一次；状态轮询不参与控制重放。
let actionRequestInFlight = false;
async function postAction(actionName, clientReference) {
  if (actionRequestInFlight) return;
  actionRequestInFlight = true;
  const action = ACTIONS[actionName];
  const button = $(action.buttonId);
  const payload = buildActionPayload(actionName, clientReference);
  setLocalActionFeedback(actionName, "submitted", payload);
  // 在途动作锁住整个操作组；即使轮询返回允许状态也不能二次下发。
  Object.values(ACTIONS).forEach(({ buttonId }) => { $(buttonId).disabled = true; });
  button.textContent = "提交中";
  try {
    const responsePayload = await fetchJson(ENDPOINTS[actionName], requestOptionsForAction(actionName, payload));
    if (responsePayload && typeof responsePayload === "object") {
      latestCloudPhoneCommandReceipt = normalizeCloudPhoneCommandReceipt({
        ...responsePayload,
        action: responsePayload.action || actionName,
        action_copy: responsePayload.action_copy || action.label,
        safe_command_id: responsePayload.safe_command_id || responsePayload.command_id || payload.command_id,
        robot_id: responsePayload.robot_id || payload.robot_id,
        client_reference: responsePayload.client_reference || payload.client_reference,
        ack_semantics: responsePayload.ack_semantics || "queued_not_delivery_success",
        safe_phone_copy: responsePayload.safe_phone_copy || CLOUD_PHONE_COMMAND_API_COPY,
        evidence_boundary: responsePayload.evidence_boundary || CLOUD_PHONE_COMMAND_API_BOUNDARY,
        delivery_success: false,
        primary_actions_enabled: false,
        safe_to_control: false,
      }, actionName);
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
      renderCloudPhoneCommandReceipt(latestStatus || {});
      renderCloudCommandResultReconciliation(latestStatus || {});
    }
  } catch (_error) {
    $("commandSafetyCopy").textContent = `${action.label} 提交失败，请打开诊断或稍后重试。`;
    setLocalActionFeedback(actionName, "local_submit_failed", payload, {
      safe_phone_copy: `${action.label} 提交失败；手机端没有收到 accepted/processing 证据。`,
      failure_reason: "HTTP 请求失败或本地网络不可用。",
      recovery_hint: "不要重复点击；先刷新状态，仍失败时打开诊断或联系支持。",
    });
  } finally {
    actionRequestInFlight = false;
    button.textContent = action.label;
    // 成功和失败都重新读取；相同 JSON 也需要刷新本地回执与重试按钮。
    statusGeneration += 1;
    lastStatusFingerprint = null;
    statusController?.abort();
    resumeStatusUpdates();
  }
}


// 状态读取只有一个调度源；动作后刷新与前台定时器共用在途 promise。
const STATUS_REFRESH_MS = 2000;
const STATUS_TIMEOUT_MS = 4000;
let statusFlight = null;
// controller 只指向当前读取；响应结束后释放，下一请求不会复用旧信号。
let statusController = null;
let statusTimer = null;
let statusGeneration = 0;
let statusFailures = 0;
// 指纹只优化展示，绝不用于证明命令已完成或允许重发。
let lastStatusFingerprint = null;
let pageActive = true;

function statusUpdatesAllowed() {
  // 后台页面不消费网络和派生状态；回到前台必须重新读取才能恢复动作。
  // pagehide 也可能发生在可见页面，独立标记覆盖浏览器返回缓存生命周期。
  return pageActive && document.visibilityState !== "hidden";
}

function scheduleStatusRefresh() {
  // 每次替换旧定时器，避免手动刷新和自动刷新产生两条循环。
  window.clearTimeout(statusTimer);
  statusTimer = null;
  if (!statusUpdatesAllowed()) return;
  // 错误退避仅控制只读轮询，绝不把失败控制请求放入重试队列。
  const delay = Math.min(STATUS_REFRESH_MS * 2 ** statusFailures, 30000);
  // 从上次请求结束时计时，慢请求不会堆积待执行的 interval 回调。
  statusTimer = window.setTimeout(() => void refreshStatus(), delay);
}

function refreshStatus() {
  // 人工刷新主动消费下一次调度机会，仍保留唯一请求入口。
  window.clearTimeout(statusTimer);
  statusTimer = null;
  if (!statusUpdatesAllowed()) return Promise.resolve();
  // 返回同一 promise，让调用者等待相同读取结果而非另建网络请求。
  if (statusFlight) return statusFlight;
  const generation = statusGeneration;
  // 控制动作或页面暂停使代次失效，响应内容再新也不能跨越这道边界。
  const controller = new AbortController();
  statusController = controller;
  // 读取超时及时关闭动作；后台主动中止由代次隔离，旧响应不能恢复按钮。
  const deadline = window.setTimeout(() => controller.abort(), STATUS_TIMEOUT_MS);
  // 整个获取与 JSON 解析都在同一个 deadline 中，慢响应体也会被中止。
  const flight = (async () => {
    try {
      // 仅 GET 使用 AbortSignal；控制请求不因可见性变化自动撤销或重放。
      const payload = await fetchJson(ENDPOINTS.status, { signal: controller.signal });
      if (controller.signal.aborted || generation !== statusGeneration || !statusUpdatesAllowed()) return;
      // 成功读取恢复正常刷新速度，旧错误退避不影响之后的状态新鲜度。
      statusFailures = 0;
      const fingerprint = JSON.stringify(payload);
      // 相同状态无需重复派生安全摘要或触碰 DOM；授权仍来自原始后端 gate。
      if (fingerprint !== lastStatusFingerprint) {
        // 保留完整 JSON 指纹，新增后端字段也会触发一次渲染。
        lastStatusFingerprint = fingerprint;
        // 核心渲染保留全部安全 gate，详情展示不在这条频繁路径中。
        renderStatus(payload);
      }
    } catch (_error) {
      // 后台主动中止无需额外显示网络失败，旧代次也无权更新界面。
      if (generation !== statusGeneration || !statusUpdatesAllowed()) return;
      statusFailures = Math.min(statusFailures + 1, 4);
      // 清指纹确保相同数据恢复时也会重绘离线提示与按钮。
      lastStatusFingerprint = null;
      renderOfflineFailure();
    } finally {
      // 成功、超时和后台中止统一释放 deadline，防止完成后再次中止。
      window.clearTimeout(deadline);
      if (statusController === controller) statusController = null;
      // 中止也等待原 fetch settle，防止旧读取未退出时又启动第二条请求。
      if (statusFlight === flight) statusFlight = null;
      // 调度函数会再次检查可见性，因此 finally 不会意外唤醒后台读取。
      scheduleStatusRefresh();
    }
  })();
  statusFlight = flight;
  // 外部 await 只等待读取；下一周期由 finally 统一安排。
  return flight;
}

function suspendStatusUpdates() {
  // 先撤销定时器，再标记代次失效，覆盖中止事件异步送达的窗口。
  window.clearTimeout(statusTimer);
  statusTimer = null;
  statusGeneration += 1;
  lastStatusFingerprint = null;
  statusController?.abort();
  // 后台暂停时清掉可操作快照，恢复后等待新状态，避免操作沿用过期授权。
  latestStatus = null;
  // 未提交的 Confirm/Cancel 二次确认随状态一起作废，恢复后需重新选择。
  pendingTerminalAction = null;
  Object.values(ACTIONS).forEach(({ buttonId }) => { $(buttonId).disabled = true; });
  renderTerminalActionPanel();
}

function resumeStatusUpdates() {
  // online 与 pageshow 可能同时到达，均归并到同一个状态入口。
  if (!statusUpdatesAllowed()) return;
  // 网络可能延迟交付 AbortError；等待唯一在途请求结束后立即读取新状态。
  if (statusFlight) void statusFlight.finally(() => { if (statusUpdatesAllowed()) void refreshStatus(); });
  // 直接读取优先于原退避计时，让用户回到前台后及时得到新状态。
  else void refreshStatus();
}

// 诊断与验收面板的声明及事件只加载一次，不参与默认状态更新循环。
let diagnosticsLoad = null;
// 下载模块与请求诊断分别去重，方便网络失败后的明确恢复。
let diagnosticsOpen = null;
function loadDiagnosticsModule() {
  // 模块加载与初始化共用一个 promise，快速连续点击不会重复装载。
  if (diagnosticsLoad) return diagnosticsLoad;
  diagnosticsLoad = new Promise((resolve, reject) => {
    // 使用普通 script 保留与核心函数共享的原全局词法环境。
    const script = document.createElement("script");
    // 固定版本与壳一起发布，避免离线或热更新时混用两套全局声明。
    script.src = "./diagnostics.js?v=2026.09.17-control-status-v1";
    script.onload = () => {
      try {
        // 下载与脚本求值完成后再挂载详情，失败时保留轻量主路径。
        const template = $("diagnosticsTemplate");
        const host = $("diagnosticsDetails");
        // 模板只有展开后才挂载；原 ID 与 phone-safe 复制接口保持兼容。
        host.appendChild(template.content.cloneNode(true));
        host.hidden = false;
        // 初始化负责详情监听；核心监听仍完全归属 wireEvents。
        window.mobileDiagnostics.initialize();
        // 模块可用后才对点击调用者完成承诺，避免使用未绑定的面板。
        resolve(window.mobileDiagnostics);
      // 求值或初始化失败保持原错误，不重复执行包含 const 声明的模块。
      } catch (error) { reject(error); }
    };
    script.onerror = () => {
      // 网络失败允许下次人工重试；已经执行的模块不会再次求值或重复绑定。
      script.remove();
      diagnosticsLoad = null;
      // 只有下载失败才清除 promise，明确允许下一次人工重试。
      reject(new Error("diagnostics_module_unavailable"));
    };
    document.head.appendChild(script);
  });
  return diagnosticsLoad;
}

function openDiagnostics() {
  // 详情请求也去重，双击不会重复生成数百个支持摘要。
  if (diagnosticsOpen) return diagnosticsOpen;
  diagnosticsOpen = (async () => {
    try {
      const module = await loadDiagnosticsModule();
      // 每次独立展开都读取新诊断，但模块初始化始终只发生一次。
      await module.open();
    } catch (_error) {
      // 诊断失败仍可查看主状态与支持摘要，且不改变任何动作授权。
      $("supportSafeCopy").textContent = "诊断暂不可用，请稍后重试或联系支持人员。";
    } finally { diagnosticsOpen = null; }
  })();
  // 调用者可等待整个展开流程，辅助入口无需轮询 DOM 猜测进度。
  return diagnosticsOpen;
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
  ensureCloudCommandResultReconciliationPanel();
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
      renderCommandSafety(latestStatus);
    }
  });
}


function markMobilePwaCacheRecovery() {
  const params = new URLSearchParams(window.location.search);
  const active = params.has("mobile_pwa_cache_recovery");
  // 该 marker 只帮助 Browser QA 识别当前壳版本，不参与控制授权。
  document.documentElement.dataset.mobilePwaCacheRecovery = active
    ? "mobile_pwa_cache_recovery"
    : "current_app_shell";
  document.documentElement.dataset.mobilePwaCacheRecoveryBoundary = MOBILE_PWA_CACHE_RECOVERY_BOUNDARY;
}


if ("serviceWorker" in navigator) {
  // 注册范围限制在静态壳；动态控制流量由 service worker 明确绕过缓存。
  navigator.serviceWorker
    .register("./service-worker.js", { scope: "./", updateViaCache: "none" })
    .then((registration) => {
      // update 明确拉取当前 service-worker.js，避免 Browser QA 卡在旧 offline shell。
      registration.update().catch(() => {});
      if (registration.active) {
        registration.active.postMessage({ type: "mobile_pwa_cache_recovery" });
      }
    })
    .catch(() => {});
}


markMobilePwaCacheRecovery();

initializePwaInstallPromptEventCapture();

// 先渲染一次空状态，让动态只读 panel 的按钮进入 DOM；事件绑定只连接已有安全按钮，不创建任何控制授权。
renderStatus({});

wireEvents();

// 页面生命周期只调度读状态；离线与后台都不会发送或重放控制请求。
document.addEventListener("visibilitychange", () => {
  // 可见性事件只调整状态调度和本地按钮，不调用任何运动或任务 API。
  if (statusUpdatesAllowed()) resumeStatusUpdates();
  else suspendStatusUpdates();
});
// 返回缓存中的页面不卸载 script；用生命周期标记停掉其网络活动。
window.addEventListener("pagehide", () => { pageActive = false; suspendStatusUpdates(); });
window.addEventListener("pageshow", () => { pageActive = true; resumeStatusUpdates(); });
// 联网仅恢复读取，离线明确清空授权，两条事件都不重放用户动作。
window.addEventListener("online", resumeStatusUpdates);
window.addEventListener("offline", () => { suspendStatusUpdates(); renderOfflineFailure(); });
refreshStatus();
