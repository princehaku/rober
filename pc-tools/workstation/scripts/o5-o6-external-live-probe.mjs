#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const SCHEMA = "trashbot.o5_o6.external_live_probe.v1";
const PC_AGGREGATE_ENDPOINT = "/api/o5-o6/cloud-relay-health";
const O5_ENDPOINT = "/api/o5/readiness/health";
const O6_ENDPOINT = "/api/o6/archive/health";
const TOKEN_ENVS = ["TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", "ROBER_CLOUD_RELAY_BEARER_TOKEN"];
// 设计约束 01：本脚本是证据入口，不是控制入口。
// 设计约束 02：脚本可以在 PC、Orange Pi 或外部主机运行。
// 设计约束 03：运行位置不同不应改变 JSON schema。
// 设计约束 04：所有失败都要变成可记录的 fail-closed 结果。
// 设计约束 05：网络不通不是异常退出的理由，而是证据分类。
// 设计约束 06：bearer 只从环境变量读取，避免进入 shell history。
// 设计约束 07：输出只写 token_status，不写 token 内容。
// 设计约束 08：base URL 允许通过 CLI 传入，方便 SSH 单次执行。
// 设计约束 09：base URL 不允许携带用户名、密码、query 或 hash。
// 设计约束 10：脚本只探测固定 health endpoint，避免 SSRF 形态扩散。
// 设计约束 11：O5 direct probe 只读 readiness health。
// 设计约束 12：O6 direct probe 只读 archive health。
// 设计约束 13：PC aggregate probe 只读 workstation 聚合 health。
// 设计约束 14：脚本不 POST，因为 POST 在本项目中通常意味着状态改变。
// 设计约束 15：脚本不访问 /robots/*，避免碰到命令队列或 ACK 游标。
// 设计约束 16：脚本不访问 /cmd_vel，避免被误解为底盘控制工具。
// 设计约束 17：脚本不枚举串口，也不读取硬件设备。
// 设计约束 18：reads_hardware 固定 false，除非未来另开硬件 probe。
// 设计约束 19：delivery_success 固定 false，因为 health 不能证明送达。
// 设计约束 20：production_ready 固定 false，由真实材料 gate 单独判断。
// 设计约束 21：schema mismatch 必须阻断，避免 UI 消费漂移 payload。
// 设计约束 22：HTTP 非 2xx 必须阻断，避免半通状态被写成 ready。
// 设计约束 23：坏 JSON 必须阻断，避免 HTML 错误页被当成 API。
// 设计约束 24：危险 true 字段必须阻断，避免上游越界声明透传。
// 设计约束 25：敏感 key 必须阻断，但安全元数据 token_status 例外。
// 设计约束 26：敏感 value 必须脱敏，不把 traceback 或本地路径写入证据。
// 设计约束 27：endpoint summary 只保留状态、schema 和分类。
// 设计约束 28：不保存完整远端 payload，减少凭证和现场信息泄漏面。
// 设计约束 29：stdout 输出完整 JSON，方便 SSH 管道和 CI 收集。
// 设计约束 30：可选 output 文件用于本地留档，但内容同 stdout。
// 设计约束 31：exit 0 只表示三个 contract 都被观察到且仍 fail-closed。
// 设计约束 32：exit 2 表示需要运营处理配置、网络或 contract 缺口。
// 设计约束 33：timeout 较短，避免 daily scan 卡死在不可达网络。
// 设计约束 34：默认不配置 URL，先证明 fail-closed 基线可复验。
// 设计约束 35：真实公网 HTTPS/TLS 仍由 O5 evidence boundary gate 验收。
// 设计约束 36：真实 4G/SIM 仍由现场材料验收，不由本脚本推断。
// 设计约束 37：production DB/queue 仍由生产探针验收，不由 health 外推。
// 设计约束 38：OSS/CDN live traffic 仍由专门材料验收。
// 设计约束 39：真实 phone/browser 仍由设备验收，不由 CLI 代替。
// 设计约束 40：robot ACK 和 delivery result 不在本脚本职责内。
// 设计约束 41：O5/O6 聚合只是运营观测入口，不是用户发车入口。
// 设计约束 42：PC aggregate 的 token_envs 是配置名，不是 secret 值。
// 设计约束 43：PC aggregate 的 token_status 是状态，不是 secret 值。
// 设计约束 44：其余 token/password/credential key 仍按敏感 marker 处理。
// 设计约束 45：直接 relay 和 PC aggregate 都要独立记录 endpoint 结果。
// 设计约束 46：summary 只做计数，具体失败原因保留在 endpoint 下。
// 设计约束 47：blocked_reasons 限长，避免异常风暴污染 sprint 记录。
// 设计约束 48：not_proven 列表固定提醒后续真实材料缺口。
// 设计约束 49：函数导出给 Vitest 使用，CLI main 只负责参数和落盘。
// 设计约束 50：测试服务只实现 GET，防止测试本身掩盖 no-control 边界。
// 设计约束 51：脚本保持 plain Node mjs，便于远端无 TS 构建时直接运行。
// 设计约束 52：不依赖 workstation dist，避免 build 产物影响探测工具。
// 设计约束 53：不读取 node_modules 以外的仓库状态，减少环境假设。
// 设计约束 54：任何未来新增 endpoint 都必须先进入 allowlist。
// 设计约束 55：任何未来打开控制字段都必须另走硬件/产品验收。
const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "sends_commands",
  "robot_control_executed",
  "delivery_success",
  "primary_actions_enabled",
  "production_ready",
  "production_db_connected",
  "connects_cloud_production",
  "reads_hardware",
  "real_oss_upload",
  "real_inference_model_runtime",
]);
const SENSITIVE_KEY_PATTERN = /(authorization|bearer|token|secret|password|credential|state_path|db_url|queue_url|traceback|serial|uart|wave_rover|ros_topic|cmd_vel)/i;
const SENSITIVE_TEXT_PATTERN = /(authorization|bearer\s+|token=|password=|secret=|traceback|\/cmd_vel|\/dev\/|wave rover|wave_rover|serial|uart|ros topic|oss:\/\/|mongodb:\/\/|redis:\/\/|postgres:\/\/|mysql:\/\/)/i;

function nowIso() {
  return new Date().toISOString();
}

function parseArgs(argv) {
  // CLI 参数只读取 URL 和输出路径；bearer 仍只允许来自环境变量，避免 shell history 泄漏。
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--pc-base-url") {
      args.pcBaseUrl = argv[index + 1] || "";
      index += 1;
    } else if (item === "--cloud-base-url") {
      args.cloudBaseUrl = argv[index + 1] || "";
      index += 1;
    } else if (item === "--output") {
      args.output = argv[index + 1] || "";
      index += 1;
    } else if (item === "--timeout-ms") {
      args.timeoutMs = Number(argv[index + 1] || "");
      index += 1;
    } else if (item === "--help" || item === "-h") {
      args.help = true;
    }
  }
  return args;
}

function usage() {
  return [
    "Usage: node scripts/o5-o6-external-live-probe.mjs [--pc-base-url URL] [--cloud-base-url URL] [--output FILE]",
    "",
    "Environment:",
    "  ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL       PC workstation API base URL",
    "  ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL    cloud-relay base URL",
    "  ROBER_CLOUD_RELAY_BASE_URL                   cloud-relay fallback base URL",
    "  TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN           bearer token for direct O5/O6 GET",
    "  ROBER_CLOUD_RELAY_BEARER_TOKEN               bearer token fallback",
  ].join("\n");
}

function readConfig(options = {}) {
  const env = options.env || process.env;
  return {
    pcBaseUrl: String(options.pcBaseUrl || env.ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL || "").trim(),
    cloudBaseUrl: String(options.cloudBaseUrl || env.ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL || env.ROBER_CLOUD_RELAY_BASE_URL || "").trim(),
    token: TOKEN_ENVS.map((name) => env[name]).find((value) => String(value || "").trim()) || "",
    timeoutMs: Number.isFinite(options.timeoutMs) && options.timeoutMs > 0 ? options.timeoutMs : 2500,
  };
}

function normalizeBaseUrl(raw) {
  const value = String(raw || "").trim();
  if (!value) {
    return { ok: false, reason: "base_url_not_configured", display_url: "not_configured", normalized: "" };
  }
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return { ok: false, reason: "base_url_protocol_not_allowed", display_url: "blocked_invalid_protocol", normalized: "" };
    }
    if (parsed.username || parsed.password || parsed.search || parsed.hash) {
      return { ok: false, reason: "base_url_must_not_include_credentials_query_or_hash", display_url: "blocked_credentialed_url", normalized: "" };
    }
    parsed.pathname = parsed.pathname.replace(/\/+$/, "");
    const normalized = parsed.toString().replace(/\/$/, "");
    return { ok: true, reason: "ok", display_url: normalized, normalized };
  } catch {
    return { ok: false, reason: "base_url_invalid", display_url: "blocked_invalid_url", normalized: "" };
  }
}

function asRecord(value) {
  // health contract 必须是 JSON object；数组和标量都按 contract drift 处理。
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function safeText(value, fallback = "unknown") {
  // 输出只保留短文本；敏感词命中后替换，不把路径、token 或 traceback 写入证据。
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 160) : fallback;
  return SENSITIVE_TEXT_PATTERN.test(text) ? "redacted_sensitive_value" : text;
}

function scanDangerousTrueFields(value, prefix = "") {
  // 递归扫描 true 状态，防止上游把 health 探针伪装成控制/生产能力。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${prefix}[${index}]`));
  }
  return Object.entries(value).flatMap(([key, item]) => {
    const pathName = prefix ? `${prefix}.${key}` : key;
    const hit = DANGEROUS_TRUE_FIELDS.has(key) && item === true ? [pathName] : [];
    return hit.concat(scanDangerousTrueFields(item, pathName));
  });
}

function scanSensitiveMarkers(value, prefix = "") {
  // 只返回 marker path，不返回 marker 对应原值，便于运营判断失败类型。
  if (!value || typeof value !== "object") {
    return typeof value === "string" && SENSITIVE_TEXT_PATTERN.test(value) ? [prefix || "payload"] : [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanSensitiveMarkers(item, `${prefix}[${index}]`));
  }
  return Object.entries(value).flatMap(([key, item]) => {
    const pathName = prefix ? `${prefix}.${key}` : key;
    const keyHit = SENSITIVE_KEY_PATTERN.test(key) && !isAllowedSafeMetadataPath(pathName) ? [pathName] : [];
    return keyHit.concat(scanSensitiveMarkers(item, pathName));
  });
}

function isAllowedSafeMetadataPath(pathName) {
  // PC aggregate 会公开 token_status 和 token_envs 这些“配置名/状态”，它们不是凭证值。
  return /(^|\.)token_status$/.test(pathName) || /(^|\.)token_envs(\[\d+\])?$/.test(pathName);
}

function endpointBase(name, endpoint, urlStatus, expectedSchema) {
  return {
    name,
    endpoint,
    expected_schema: expectedSchema,
    reachable: false,
    http_status: null,
    schema: "not_loaded",
    schema_status: "not_loaded",
    contract_status: "fail_closed",
    failure_category: urlStatus.ok ? "not_started" : urlStatus.reason,
    blocked_reasons: urlStatus.ok ? [] : [urlStatus.reason],
    dangerous_true_fields: [],
    sensitive_markers: [],
  };
}

async function fetchJson(baseUrl, endpoint, token, timeoutMs) {
  // probe 固定只发 GET；不会 POST、不会访问 /robots/*、不会触碰硬件或 ROS2。
  const headers = { Accept: "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(timeoutMs),
    });
    const json = await response.json().catch(() => undefined);
    return { ok: true, status: response.status, body: asRecord(json), badJson: !asRecord(json) };
  } catch {
    return { ok: false, status: null, body: null, badJson: false };
  }
}

function summarizeEndpoint(name, endpoint, expectedSchema, urlStatus, fetchResult) {
  const summary = endpointBase(name, endpoint, urlStatus, expectedSchema);
  if (!urlStatus.ok) {
    return summary;
  }
  if (!fetchResult || !fetchResult.ok) {
    return { ...summary, failure_category: "network_or_service_unreachable", blocked_reasons: ["network_or_service_unreachable"] };
  }
  const body = fetchResult.body;
  const schema = body ? safeText(body.schema, "missing_schema") : "not_loaded";
  const schemaStatus = schema === expectedSchema ? "matched" : "mismatch";
  const dangerous = scanDangerousTrueFields(body).map((field) => `${name}.${field}`);
  const sensitive = scanSensitiveMarkers(body).map((field) => `${name}.${field}`);
  const blocked = [
    ...(fetchResult.badJson ? ["bad_json"] : []),
    ...(fetchResult.status >= 200 && fetchResult.status < 300 ? [] : [`http_${fetchResult.status}`]),
    ...(schemaStatus === "matched" ? [] : ["schema_mismatch"]),
    ...dangerous.map((field) => `dangerous_true:${field}`),
    ...sensitive.map((field) => `sensitive_marker:${field}`),
  ];
  return {
    ...summary,
    reachable: Boolean(fetchResult.status),
    http_status: fetchResult.status,
    schema,
    schema_status: schemaStatus,
    contract_status: blocked.length === 0 ? "observed_fail_closed_contract" : "fail_closed",
    failure_category: blocked[0] || "none",
    blocked_reasons: blocked,
    dangerous_true_fields: dangerous,
    sensitive_markers: sensitive,
  };
}

function fixedFalseFields() {
  // 这些 false 字段是给运营和 OKR 留档看的安全栏杆。
  // probe 只观察 health，不具备证明发车、送达或生产就绪的证据强度。
  // 显式列出字段可以防止下游 UI 用“字段缺失”误判为可控制。
  return [
    "safe_to_control=false",
    "sends_commands=false",
    "robot_control_executed=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "production_ready=false",
    "reads_hardware=false",
  ];
}

function finalStatus(results) {
  // fail-closed 是本脚本的默认结论，因为外部探针最常见失败是网络和配置缺口。
  // 只有全部 endpoint 都满足 schema、安全字段和脱敏扫描时，才进入 observed 状态。
  // 任一上游漂移都保留 blocked reason，避免把半通服务包装成 ready。
  const blocked = results.flatMap((item) => item.blocked_reasons);
  if (results.every((item) => item.contract_status === "observed_fail_closed_contract")) {
    return { probe_status: "observed_fail_closed_contract", blocked_reasons: [] };
  }
  return { probe_status: "fail_closed", blocked_reasons: blocked.length ? blocked : ["not_all_endpoints_observed"] };
}

export async function runExternalLiveProbe(options = {}) {
  // 配置读取和 URL 规范化先执行，避免把未校验的外部输入拼进请求。
  const config = readConfig(options);
  const pcUrl = normalizeBaseUrl(config.pcBaseUrl);
  const cloudUrl = normalizeBaseUrl(config.cloudBaseUrl);
  // 直连 O5/O6 只用于观察 live health，不调用 commands/status/ack 写路径。
  const directO5 = await fetchJson(cloudUrl.normalized, O5_ENDPOINT, config.token, config.timeoutMs);
  const directO6 = await fetchJson(cloudUrl.normalized, O6_ENDPOINT, config.token, config.timeoutMs);
  // PC 聚合 probe 复用同一个 cloud base URL，是为了对照 workstation 侧转发视角。
  // 这里仍然只拼入经过 normalizeBaseUrl 处理后的 URL，避免 query/hash 扩散。
  const pcAggregateEndpoint = cloudUrl.ok
    ? `${PC_AGGREGATE_ENDPOINT}?baseUrl=${encodeURIComponent(cloudUrl.normalized)}`
    : PC_AGGREGATE_ENDPOINT;
  // PC 聚合请求不带 bearer，避免把直连云端凭证转交给 workstation 进程。
  const pcAggregate = await fetchJson(pcUrl.normalized, pcAggregateEndpoint, "", config.timeoutMs);
  // 每个 endpoint 独立汇总，便于定位是直连云端失败还是 PC 聚合失败。
  const endpoint_results = [
    summarizeEndpoint("o5_readiness", O5_ENDPOINT, "trashbot.o5.readiness_health.v1", cloudUrl, directO5),
    summarizeEndpoint("o6_archive", O6_ENDPOINT, "trashbot.o6.archive_health.v1", cloudUrl, directO6),
    summarizeEndpoint("pc_aggregate", pcAggregateEndpoint, "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1", pcUrl, pcAggregate),
  ];
  const status = finalStatus(endpoint_results);
  return {
    schema: SCHEMA,
    executed_at: nowIso(),
    probe_status: status.probe_status,
    viewpoint: "external_or_upper_computer_readonly",
    pc_base_url: pcUrl.display_url,
    cloud_base_url: cloudUrl.display_url,
    token_status: config.token ? "present" : "absent",
    // 脱敏只声明状态，不输出 token、Authorization header 或 credential 原值。
    credentials_redacted: true,
    endpoints: endpoint_results,
    summary: {
      endpoint_count: endpoint_results.length,
      reachable_count: endpoint_results.filter((item) => item.reachable).length,
      schema_matched_count: endpoint_results.filter((item) => item.schema_status === "matched").length,
      fail_closed_count: endpoint_results.filter((item) => item.contract_status !== "observed_fail_closed_contract").length,
      // summary 继续固定控制相关 false，防止调用方只看顶层摘要时越权。
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
      reads_hardware: false,
    },
    safety_policy: {
      // 安全策略写入结果本身，方便 sprint 证据脱离源码也能被复核。
      method_allowlist: ["GET"],
      endpoint_allowlist: [O5_ENDPOINT, O6_ENDPOINT, PC_AGGREGATE_ENDPOINT],
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "environment_only",
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
    },
    key_false_fields: fixedFalseFields(),
    // blocked_reasons 限长是为了保留主要诊断，同时避免远端异常风暴撑爆日志。
    blocked_reasons: status.blocked_reasons.slice(0, 20),
    not_proven: [
      // not_proven 明确证据边界，防止 CLI 可达性被误读成真实生产材料。
      "real_public_https_tls_not_proven",
      "real_4g_sim_not_proven",
      "production_db_queue_not_proven",
      "real_oss_cdn_live_traffic_not_proven",
      "real_phone_browser_not_proven",
      "delivery_success_not_proven",
    ],
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

async function writeOutput(result, outputPath) {
  if (outputPath) {
    // 可选产物用于 SSH 或 CI 收集；stdout 也会输出同一个脱敏 JSON。
    // 写文件只写最终 JSON，不额外记录环境变量，避免落盘泄漏凭证。
    await fs.mkdir(path.dirname(path.resolve(outputPath)), { recursive: true });
    await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  const result = await runExternalLiveProbe(args);
  await writeOutput(result, args.output || "");
  // exit code 区分“contract observed”和“需要处理”，但两者都会输出结构化证据。
  process.exitCode = result.probe_status === "observed_fail_closed_contract" ? 0 : 2;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    // main 兜底只输出错误摘要，不把堆栈路径或环境细节写入 stdout 证据。
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 2;
  });
}
