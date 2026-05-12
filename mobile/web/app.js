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

let latestStatus = null;
let latestDiagnostics = null;
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
  renderSupport(status);
}

function buildStartPayload() {
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
    client_reference: `mobile_web_${Date.now()}`,
    evidence_boundary: latestStartGate.evidenceBoundary,
    ack_semantics: "accepted_processing_only_not_delivery_success",
  };
}

function requestOptionsForAction(actionName) {
  if (actionName !== "start") {
    return { method: "POST" };
  }
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildStartPayload()),
  };
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
      button.disabled = true;
      return;
    }
  }
  // 控制动作需要人工确认；失败时只提示重试，不做本地重放。
  if (!window.confirm(`${action.label}？请确认现场安全。`)) {
    return;
  }
  button.disabled = true;
  button.textContent = "提交中";
  try {
    await fetchJson(ENDPOINTS[actionName], requestOptionsForAction(actionName));
    await refreshStatus();
  } catch (_error) {
    $("commandSafetyCopy").textContent = `${action.label} 提交失败，请打开诊断或稍后重试。`;
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
