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
const ACK_PROCESSING_COPY = "ACK 只代表 accepted/processing evidence，不代表送达成功、投放完成或取消已落地。";

let latestStatus = null;
let latestDiagnostics = null;
let latestActionFeedback = null;
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

function startGateFromStatus(status) {
  const readiness = readinessFromStatus(status);
  const commandSafety = commandSafetyFromReadiness(readiness);
  const actions = commandSafety.actions && typeof commandSafety.actions === "object" ? commandSafety.actions : {};
  const startGate = actions.start && typeof actions.start === "object" ? actions.start : {};
  const destination = destinationFromStatus(status, readiness);
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

  return {
    destination: destination.value,
    destinationReady: destination.ready,
    loadConfirmed,
    startEnabled: blockers.length === 0,
    blockedReason: blockers.join("；") || "可以提交发车请求。",
    commandSafetyAck: safeText(commandSafety.ack_semantics, "ACK 只表示指令受理或处理中，不代表送达成功。"),
    evidenceBoundary: "software_proof_docker_mobile_task_start_confirmation_gate",
    destinationSource: destination.source,
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
    const enabled = actionGate.enabled === true && permitted === true && (startGate ? startGate.startEnabled : true);
    // blocked、离线、等待 ACK、人工接管都会通过 command_safety 关闭按钮。
    button.disabled = !enabled;
    button.dataset.endpoint = ENDPOINTS[name];
    button.title = safeText(actionGate.safe_phone_copy, "后端 gate 未放行。");

    const item = document.createElement("li");
    const reason = name === "start" && startGate
      ? startGate.blockedReason
      : safeText(actionGate.blocking_reason || commandSafety.global_block_reason, "blocked");
    item.textContent = `${actionMeta.label}：${enabled ? "可操作" : reason}`;
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
  pushDerivedEvent(entries, "离线恢复", offlineResumeFromStatus(status, readiness));
  pushDerivedEvent(entries, "支持交接", status?.phone_support_bundle || readiness?.phone_support_bundle);
  pushDerivedEvent(entries, "语音提示", voicePromptFromStatus(status, readiness));
  return entries.slice(0, 6);
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
  Object.keys(ACTIONS).forEach((name) => {
    $(ACTIONS[name].buttonId).disabled = true;
  });
}

function renderStatus(status) {
  latestStatus = status;
  renderReadiness(status);
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
  $("supportButton").addEventListener("click", () => {
    const bundle = latestStatus?.phone_support_bundle || latestStatus?.phone_readiness?.phone_support_bundle || {};
    $("supportSafeCopy").textContent = safeText(bundle.safe_copy, "暂无脱敏支持摘要。");
  });
  Object.keys(ACTIONS).forEach((name) => {
    $(ACTIONS[name].buttonId).addEventListener("click", () => submitAction(name));
  });
  $("trashLoadedCheckbox").addEventListener("change", () => {
    if (latestStatus) {
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
