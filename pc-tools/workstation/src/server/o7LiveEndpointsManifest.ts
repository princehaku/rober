import { PROOF_FLAGS } from "../shared/contracts";
import type { O7LiveEndpointCapability, O7LiveEndpointsManifestResponse } from "../shared/contracts";

type CapabilityConfig = Pick<O7LiveEndpointCapability, "id" | "kr_ids" | "title" | "env" | "required_live_evidence" | "remaining_real_capability_gaps">;

const SCHEMA = "trashbot.o7.live_endpoints_manifest.v1";
const ENDPOINT = "/api/o7/live-endpoints/manifest";
// manifest 只做配置清点，允许 ws/wss 是为了覆盖 RTC signaling 的常见协议形态。
const SAFE_PROTOCOLS = new Set(["http:", "https:", "ws:", "wss:"]);

const CAPABILITY_CONFIGS: CapabilityConfig[] = [
  {
    // KR1/KR2 共用实时链路入口，因为 pose、地图和电梯状态通常来自同一实时通道。
    // 这里不拆成多个 URL，是为了让 operator 先看到最小可配置面，而不是伪装成已联通。
    id: "rtc_realtime_pose_elevator",
    kr_ids: ["O7-KR1", "O7-KR2"],
    title: "RTC/realtime pose/elevator state API",
    env: { url: "O7_RTC_REALTIME_URL", token: "O7_RTC_REALTIME_TOKEN" },
    // required_live_evidence 是后续真实联调清单，不是本 manifest 已经采集到的证据。
    required_live_evidence: ["rtc_signaling_trace", "realtime_pose_latency_trace", "elevator_state_chain_trace"],
    // gap 明确把配置存在和真实 RTC/TF/电梯状态分开，避免 O7 进度被错误抬升。
    remaining_real_capability_gaps: ["real_rtc_video_connected", "real_ros2_tf_forwarding", "real_elevator_state_chain"],
  },
  {
    // archive 是 O6/O7 的持久化入口；manifest 只确认 env 是否可安全展示。
    // 即使 configured，也不能说明任务列表或轨迹帧已经能从云端读取。
    id: "cloud_archive",
    kr_ids: ["O7-KR3"],
    title: "Cloud archive API",
    env: { url: "O7_CLOUD_ARCHIVE_URL", token: "O7_CLOUD_ARCHIVE_TOKEN" },
    // 证据要求保留 task、trajectory、keyframe 三层，方便后续真实 archive 验收逐项补齐。
    required_live_evidence: ["cloud_archive_task_query_trace", "trajectory_frame_archive_trace", "keyframe_object_ref_trace"],
    // 这些 gap 都是 live data 缺口，不能由本地 fixture 或 URL 配置替代。
    remaining_real_capability_gaps: ["real_cloud_archive_connected", "real_history_task_list", "real_trajectory_frames"],
  },
  {
    // route replay 独立于 archive，是为了未来可把回放数据源接到专门的 paged API。
    // 当前只读 readiness 不能触发 playback 或预取帧，所以依旧保持 not_proven。
    id: "route_replay_source",
    kr_ids: ["O7-KR3"],
    title: "Route replay data source API",
    env: { url: "O7_ROUTE_REPLAY_URL", token: "O7_ROUTE_REPLAY_TOKEN" },
    // frame/page/timeline/cursor 是真实回放最小闭环，manifest 不会替这些证据打勾。
    required_live_evidence: ["route_replay_frame_page_trace", "state_transition_timeline_trace", "readonly_playback_cursor_trace"],
    // map overlay 特意保留为 gap，防止 URL 配置被误读成地图叠加已经可用。
    remaining_real_capability_gaps: ["real_route_replay_frames", "real_state_transition_timeline", "real_map_overlay"],
  },
  {
    // annotation submit 是写 API，但本 manifest 只能展示 readiness，绝不提交或 autosave。
    // token 只展示 present/absent，避免把标注写权限泄露到 PC UI。
    id: "annotation_submit_api",
    kr_ids: ["O7-KR4"],
    title: "Annotation submit API",
    env: { url: "O7_ANNOTATION_API_URL", token: "O7_ANNOTATION_API_TOKEN" },
    // queue、submit、rollback 三类证据拆开，是为了后续确认标注链路可恢复。
    required_live_evidence: ["annotation_queue_query_trace", "annotation_submit_audit_trace", "annotation_rollback_trace"],
    // dataset export 仍是独立真实能力，不能因为 annotation URL 配置而默认可用。
    remaining_real_capability_gaps: ["real_annotation_api_connected", "real_annotation_submit", "real_dataset_export"],
  },
  {
    // voice API 同时覆盖 ASR 和 TTS，但这里不打开麦克风、不播放音频、不发送 TTS。
    // 配置存在只表示 operator 填了未来 API 入口，不表示音频设备或云端 runtime 可用。
    id: "voice_asr_tts_api",
    kr_ids: ["O7-KR5"],
    title: "Voice ASR/TTS API",
    env: { url: "O7_VOICE_API_URL", token: "O7_VOICE_API_TOKEN" },
    // ASR partial/final、TTS ACK、speaker failure 是 KR5 后续必须补的真实审计证据。
    required_live_evidence: ["asr_stream_partial_final_trace", "tts_payload_ack_trace", "speaker_dispatch_failure_trace"],
    // speaker ACK 保留在 gap 中，避免把云端语音 API 和机器人喇叭播报混为一谈。
    remaining_real_capability_gaps: ["real_voice_api_connected", "real_asr_tts_runtime_connected", "real_speaker_ack"],
  },
  {
    // safe command 是最高风险 future API；manifest 只允许只读清点，不允许 dispatch。
    // 这里把 robot ACK 和 HIL 安全放进 gap，确保 configured 不会变成 safe_to_control。
    id: "safe_command_api",
    kr_ids: ["O7-KR6"],
    title: "Safe command API",
    env: { url: "O7_SAFE_COMMAND_API_URL", token: "O7_SAFE_COMMAND_TOKEN" },
    // 幂等、ACK timeout、stop/cancel/recovery 是真实控制 API 的最低审计材料。
    required_live_evidence: ["idempotent_command_api_trace", "robot_ack_timeout_trace", "stop_cancel_recovery_ack_trace"],
    // 硬件安全必须由后续 HIL/现场证据证明，不能由 PC env readiness 外推。
    remaining_real_capability_gaps: ["real_command_api_connected", "real_robot_ack_connected", "real_hardware_hil_safety"],
  },
];

function summarizeUrl(rawUrl: string): O7LiveEndpointCapability["url"] {
  // URL 摘要只保留协议、host 和 path；query/hash/用户名/密码都直接 blocked，避免泄漏凭证。
  const trimmed = rawUrl.trim();
  if (!trimmed) {
    // 空 URL 是正常未配置状态，不是错误；UI 要明确显示 not_configured。
    return { configured: false, display_url: "not_configured", protocol: "", host: "", path: "", unsafe_reason: "" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    // 非法 URL 不能原样回显，因为其中可能混入 token 或本机路径。
    return { configured: false, display_url: "blocked_unsafe_url", protocol: "", host: "", path: "", unsafe_reason: "invalid_url" };
  }
  if (!SAFE_PROTOCOLS.has(parsed.protocol)) {
    // 非 HTTP/WS 协议不进入 readiness，避免 file:// 等本机资源路径被暴露到 UI。
    return {
      configured: false,
      display_url: "blocked_unsafe_url",
      protocol: parsed.protocol,
      host: parsed.host,
      path: parsed.pathname || "/",
      unsafe_reason: "protocol_not_allowed",
    };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    // query/hash/credentials 常承载 token 或签名参数，因此整条 URL blocked 且不展示原值。
    return {
      configured: false,
      display_url: "blocked_unsafe_url",
      protocol: parsed.protocol.replace(":", ""),
      host: parsed.host,
      path: parsed.pathname || "/",
      unsafe_reason: "url_must_not_include_credentials_query_or_hash",
    };
  }
  const protocol = parsed.protocol.replace(":", "");
  const path = parsed.pathname || "/";
  // display_url 只由 URL parser 的安全字段重新组装，不使用用户输入原文。
  return {
    configured: true,
    display_url: `${protocol}://${parsed.host}${path}`,
    protocol,
    host: parsed.host,
    path,
    unsafe_reason: "",
  };
}

function buildCapability(config: CapabilityConfig, env: NodeJS.ProcessEnv): O7LiveEndpointCapability {
  const url = summarizeUrl(env[config.env.url] ?? "");
  const tokenPresent = Boolean((env[config.env.token] ?? "").trim());
  // token 缺失只进入 missing，不会让 URL 安全摘要回退成 blocked。
  const missing = [url.configured || url.unsafe_reason ? "" : "url", tokenPresent ? "" : "token"].filter(Boolean);
  // blocked reason 带 env 名称，方便 operator 定位配置项，但不包含原始 URL。
  const blockedReasons = url.unsafe_reason ? [`${config.env.url}:${url.unsafe_reason}`] : [];
  // configured 只表示 URL 通过脱敏检查；token 缺失仍作为 missing 明确展示，不能推断 API 可用。
  const status = url.unsafe_reason ? "blocked" : url.configured ? "configured" : "not_configured";
  return {
    ...config,
    status,
    proof_status: "not_proven",
    url,
    token: {
      env: config.env.token,
      status: tokenPresent ? "present" : "absent",
    },
    missing,
    blocked_reasons: blockedReasons,
  };
}

export function buildO7LiveEndpointsManifest(env: NodeJS.ProcessEnv = process.env): O7LiveEndpointsManifestResponse {
  // 所有 capability 都来自静态白名单，避免任意 env key 被批量泄露到响应中。
  const capabilities = CAPABILITY_CONFIGS.map((config) => buildCapability(config, env));
  // summary 只统计状态，不包含 URL 原文或 token 值，适合 UI 顶部一屏展示。
  const summary = {
    configured: capabilities.filter((capability) => capability.status === "configured").length,
    not_configured: capabilities.filter((capability) => capability.status === "not_configured").length,
    blocked: capabilities.filter((capability) => capability.status === "blocked").length,
    token_present: capabilities.filter((capability) => capability.token.status === "present").length,
    token_absent: capabilities.filter((capability) => capability.token.status === "absent").length,
  };
  // 顶层 evidence/gap 是六个 capability 的去重合并，供 UI 一屏复核 O7-KR1..KR6 的真实缺口。
  const requiredLiveEvidence = Array.from(new Set(capabilities.flatMap((capability) => capability.required_live_evidence)));
  const remainingGaps = Array.from(new Set(capabilities.flatMap((capability) => capability.remaining_real_capability_gaps)));
  // 顶层 blocked reason 是 capability blocked 的索引，不包含具体 secret 或完整 URL。
  const blockedReasons = capabilities.flatMap((capability) => capability.blocked_reasons);

  return {
    schema: SCHEMA,
    schema_version: 1,
    ...PROOF_FLAGS,
    // 以下安全开关全部固定为 false，配置状态不能改变控制或生产连接边界。
    manifest_status: "readiness_manifest_ready",
    endpoint: ENDPOINT,
    env_only: true,
    network_probe_executed: false,
    sends_commands: false,
    safe_to_control: false,
    connects_cloud_production: false,
    robot_control_executed: false,
    reads_hardware: false,
    token_values_exposed: false,
    url_query_hash_credentials_exposed: false,
    capabilities,
    summary,
    required_live_evidence: requiredLiveEvidence,
    remaining_real_capability_gaps: remainingGaps,
    blocked_reasons: blockedReasons,
    not_proven: remainingGaps,
  };
}
