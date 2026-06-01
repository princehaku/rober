#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCHEMA = "trashbot.o7.local_webrtc_browser_playback_smoke.v1";
const DEFAULT_BASE_URL = "http://192.168.1.11:8088/";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const defaultOutput = path.join(workstationRoot, ".workstation-runtime", "o7-browser-playback-smoke.json");

function nowIso() {
  return new Date().toISOString();
}

function normalizeBaseUrl(raw) {
  const value = String(raw || DEFAULT_BASE_URL).trim();
  const parsed = new URL(value);
  if (parsed.protocol !== "http:") {
    throw new Error("base_url_protocol_not_allowed");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("base_url_must_not_include_credentials_query_or_hash");
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "/");
  return parsed.toString();
}

function baseResult(baseUrl, blockedReason) {
  return {
    schema: SCHEMA,
    status: "fail_closed",
    base_url: baseUrl,
    page_url: baseUrl,
    executed_at: nowIso(),
    browser_engine: "chromium",
    browser_available: false,
    playwright_available: false,
    start_clicked: false,
    first_frame_received: false,
    video_width: null,
    video_height: null,
    first_frame_ms: null,
    connection_state: null,
    ice_connection_state: null,
    ice_gathering_state: null,
    signaling_state: null,
    failure_category: "not_started",
    remote_health_status: null,
    remote_active_peer_connections: null,
    offer_http_status: null,
    offer_error_reason: null,
    offer_error_detail: null,
    observation_window_ms: null,
    final_ready_state: null,
    stable_video_width: null,
    stable_video_height: null,
    ontrack_count: 0,
    receiver_track_states: [],
    transceiver_directions: [],
    inbound_video_stats: [],
    selected_candidate_pair: null,
    peer_state_timeline: [],
    post_smoke_remote_health: null,
    stability_summary: defaultStabilitySummary(),
    console_error_count: 0,
    page_error_count: 0,
    server_peer_id: null,
    server_peer_close_status: "not_attempted",
    console_errors: [],
    page_errors: [],
    blocked_reason: blockedReason,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    offer_executed_by_browser: false,
    workstation_api_offer_executed: false,
  };
}

function defaultStabilitySummary() {
  return {
    status: "not_observed",
    observation_window_ms: 0,
    sample_interval_ms: null,
    sample_count: 0,
    first_packets_received: null,
    last_packets_received: null,
    first_frames_decoded: null,
    last_frames_decoded: null,
    first_frames_received: null,
    last_frames_received: null,
    estimated_fps: null,
    estimated_packet_rate: null,
    video_size_stable: "not_available",
    stable_video_width: null,
    stable_video_height: null,
    connection_remained_connected: "not_available",
    ice_remained_connected: "not_available",
    console_errors_added: 0,
    page_errors_added: 0,
    remote_health_samples: 0,
    remote_health_statuses: [],
    remote_active_peer_connections_first: null,
    remote_active_peer_connections_last: null,
    remote_system_metrics: "not_available",
    remote_stability_metrics: "not_available",
    post_close_active_peer_connections: null,
    remote_active_peer_cleaned: "not_available",
  };
}

async function writeAndPrint(result, outputPath) {
  // smoke 结果固定落本地 runtime JSON，PC API 只读该文件，不会因此自动打开 /offer。
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ ...result, report_path: outputPath })}\n`);
}

async function loadRemoteHealth(baseUrl) {
  // 只读 health 能提前识别 active peer，占用时不需要猜测首帧失败根因。
  try {
    const response = await fetch(new URL("/health", baseUrl), {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(1500),
    });
    const payload = await response.json().catch(() => ({}));
    return {
      status: typeof payload.status === "string" ? payload.status : `http_${response.status}`,
      activePeerConnections:
        typeof payload.active_peer_connections === "number" ? payload.active_peer_connections : null,
      systemMetrics: sanitizeMetricRecord(payload.system_metrics),
      stabilityMetrics: sanitizeMetricRecord(payload.stability_metrics),
    };
  } catch {
    return {
      status: "remote_health_unreachable",
      activePeerConnections: null,
      systemMetrics: "not_available",
      stabilityMetrics: "not_available",
    };
  }
}

function sanitizeMetricRecord(value) {
  // Robot Software 可以逐步加 system/stability 指标；脚本只透传简单白名单值，缺字段不算失败。
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return "not_available";
  }
  const safe = {};
  for (const [key, item] of Object.entries(value).slice(0, 24)) {
    if (!/^[a-zA-Z0-9_]+$/.test(key)) {
      continue;
    }
    if (typeof item === "number" && Number.isFinite(item)) {
      safe[key] = item;
    } else if (typeof item === "boolean" || typeof item === "string") {
      safe[key] = String(item).slice(0, 120);
    }
  }
  return Object.keys(safe).length ? safe : "not_available";
}

async function loadPlaywright() {
  // Playwright 是 devDependency；现场未安装 node_modules 时仍要 fail closed 并留下 JSON 证据。
  try {
    return await import("playwright");
  } catch {
    return null;
  }
}

function summarizeOfferResponse(value) {
  // /offer 的非 200 响应是最关键的失败证据，只摘录白名单字段避免吞完整 SDP。
  if (!value || typeof value !== "object") {
    return {};
  }
  const payload = value.payload && typeof value.payload === "object" ? value.payload : {};
  return {
    offer_http_status: typeof value.status === "number" ? value.status : null,
    offer_error_reason: typeof payload.reason === "string" ? payload.reason : null,
    offer_error_detail: typeof payload.detail === "string" ? payload.detail.slice(0, 300) : null,
  };
}

function classifyFailure({ error, result, consoleErrors, pageErrors }) {
  // 分类字段给 sprint 证据直接归因：依赖、远端占用、ICE/浏览器、首帧超时或页面错误。
  const message = error instanceof Error ? error.message : String(error || "");
  const joinedConsole = consoleErrors.join("\n");
  if (/executable doesn't exist|browserType\.launch|playwright/i.test(message)) {
    return "dependency";
  }
  if (result.offer_http_status === 409 || /409|Conflict|camera_in_use/.test(`${message}\n${joinedConsole}\n${result.offer_error_reason ?? ""}`)) {
    return "remote_409";
  }
  if (/Timeout|waiting for function/i.test(message) && result.start_clicked) {
    if (result.ontrack_count > 0 && result.inbound_video_stats.some((item) => item.packetsReceived > 0 || item.framesDecoded > 0)) {
      return "video_element_decode_timeout";
    }
    if (result.ontrack_count > 0) {
      return "track_received_no_rtp";
    }
    return "first_frame_timeout";
  }
  if (pageErrors.length > 0 || consoleErrors.some((line) => line.startsWith("error:"))) {
    return "page_console_error";
  }
  if (result.connection_state || result.ice_connection_state || result.signaling_state) {
    return "ice_browser";
  }
  return "browser_smoke_failed";
}

async function collectPageState(page) {
  // 诊断字段只从浏览器 peer/video/stats 读取，不改变页面状态或触发新的 /offer。
  return await page
    .evaluate(async () => {
      const peer = window.__roberLastPeer;
      const video = document.querySelector("video");
      const offerPayload = window.__roberOfferPayloads?.[window.__roberOfferPayloads.length - 1];
      const offerResponse = window.__roberOfferResponses?.[window.__roberOfferResponses.length - 1];
      const transceiverDirections = peer
        ? peer.getTransceivers().map((item) => ({
            mid: item.mid,
            direction: item.direction,
            currentDirection: item.currentDirection,
            receiverTrackState: item.receiver?.track?.readyState || null,
            receiverTrackMuted: item.receiver?.track?.muted ?? null,
          }))
        : [];
      const receiverTrackStates = peer
        ? peer.getReceivers().map((receiver) => ({
            kind: receiver.track?.kind || null,
            id: receiver.track?.id || null,
            readyState: receiver.track?.readyState || null,
            muted: receiver.track?.muted ?? null,
          }))
        : [];
      const stats = peer ? Array.from((await peer.getStats()).values()) : [];
      const inboundVideoStats = stats
        .filter((item) => item.type === "inbound-rtp" && item.kind === "video")
        .map((item) => ({
          id: item.id,
          packetsReceived: item.packetsReceived ?? null,
          bytesReceived: item.bytesReceived ?? null,
          framesDecoded: item.framesDecoded ?? null,
          framesReceived: item.framesReceived ?? null,
          framesDropped: item.framesDropped ?? null,
          keyFramesDecoded: item.keyFramesDecoded ?? null,
          jitter: item.jitter ?? null,
        }));
      const selectedCandidatePair = stats.find((item) => item.type === "candidate-pair" && item.selected);
      return {
        videoWidth: video?.videoWidth || null,
        videoHeight: video?.videoHeight || null,
        readyState: video?.readyState ?? null,
        connectionState: peer?.connectionState || null,
        iceConnectionState: peer?.iceConnectionState || null,
        iceGatheringState: peer?.iceGatheringState || null,
        signalingState: peer?.signalingState || null,
        peerId: typeof offerPayload?.peer_id === "string" ? offerPayload.peer_id : null,
        offerResponse: offerResponse || null,
        ontrackCount: window.__roberOnTrackEvents?.length || 0,
        receiverTrackStates,
        transceiverDirections,
        inboundVideoStats,
        selectedCandidatePair: selectedCandidatePair
          ? {
              id: selectedCandidatePair.id,
              state: selectedCandidatePair.state || null,
              nominated: selectedCandidatePair.nominated ?? null,
              packetsSent: selectedCandidatePair.packetsSent ?? null,
              packetsReceived: selectedCandidatePair.packetsReceived ?? null,
              bytesSent: selectedCandidatePair.bytesSent ?? null,
              bytesReceived: selectedCandidatePair.bytesReceived ?? null,
              currentRoundTripTime: selectedCandidatePair.currentRoundTripTime ?? null,
            }
          : null,
        peerStateTimeline: window.__roberPeerStates || [],
      };
    })
    .catch(() => ({}));
}

function applyPageState(result, pageState) {
  result.final_ready_state = typeof pageState.readyState === "number" ? pageState.readyState : null;
  result.stable_video_width = typeof pageState.videoWidth === "number" ? pageState.videoWidth : null;
  result.stable_video_height = typeof pageState.videoHeight === "number" ? pageState.videoHeight : null;
  result.connection_state = pageState.connectionState || null;
  result.ice_connection_state = pageState.iceConnectionState || null;
  result.ice_gathering_state = pageState.iceGatheringState || null;
  result.signaling_state = pageState.signalingState || null;
  result.server_peer_id = pageState.peerId || null;
  result.ontrack_count = typeof pageState.ontrackCount === "number" ? pageState.ontrackCount : 0;
  result.receiver_track_states = Array.isArray(pageState.receiverTrackStates) ? pageState.receiverTrackStates.slice(0, 5) : [];
  result.transceiver_directions = Array.isArray(pageState.transceiverDirections) ? pageState.transceiverDirections.slice(0, 5) : [];
  result.inbound_video_stats = Array.isArray(pageState.inboundVideoStats) ? pageState.inboundVideoStats.slice(0, 5) : [];
  result.selected_candidate_pair = pageState.selectedCandidatePair || null;
  result.peer_state_timeline = Array.isArray(pageState.peerStateTimeline) ? pageState.peerStateTimeline.slice(-20) : [];
  Object.assign(result, summarizeOfferResponse(pageState.offerResponse));
}

function firstInboundVideo(pageState) {
  const stats = Array.isArray(pageState.inboundVideoStats) ? pageState.inboundVideoStats : [];
  return stats.find((item) => item && typeof item === "object") || {};
}

function metricDelta(first, last, field) {
  const left = firstInboundVideo(first)[field];
  const right = firstInboundVideo(last)[field];
  if (typeof left !== "number" || typeof right !== "number") {
    return { first: null, last: null, delta: null };
  }
  return { first: left, last: right, delta: Math.max(0, right - left) };
}

function sizeIsStable(samples) {
  const sizes = samples
    .map((sample) => ({
      width: typeof sample.pageState.videoWidth === "number" ? sample.pageState.videoWidth : null,
      height: typeof sample.pageState.videoHeight === "number" ? sample.pageState.videoHeight : null,
    }))
    .filter((item) => item.width && item.height);
  if (sizes.length === 0) {
    return { status: "not_available", width: null, height: null };
  }
  const first = sizes[0];
  const stable = sizes.every((item) => item.width === first.width && item.height === first.height);
  return { status: stable ? "stable" : "changed", width: first.width, height: first.height };
}

function allStatesConnected(samples, field) {
  const values = samples.map((sample) => sample.pageState[field]).filter((value) => typeof value === "string");
  if (values.length === 0) {
    return "not_available";
  }
  return values.every((value) => value === "connected" || value === "completed") ? "connected" : "changed";
}

function latestAvailableMetric(samples, field) {
  for (const sample of [...samples].reverse()) {
    const metric = sample.remoteHealth?.[field];
    if (metric && metric !== "not_available") {
      return metric;
    }
  }
  return "not_available";
}

function buildStabilitySummary({ samples, windowMs, intervalMs, consoleErrorBaseline, pageErrorBaseline, consoleErrors, pageErrors }) {
  // stability_summary 是 3-5 分钟证据的机器摘要；窗口为 0 时保持 not_observed，不伪造稳定结论。
  if (!windowMs || samples.length === 0) {
    return {
      ...defaultStabilitySummary(),
      observation_window_ms: windowMs,
      sample_interval_ms: intervalMs,
      console_errors_added: Math.max(0, consoleErrors.length - consoleErrorBaseline),
      page_errors_added: Math.max(0, pageErrors.length - pageErrorBaseline),
    };
  }
  const first = samples[0].pageState;
  const last = samples[samples.length - 1].pageState;
  const packets = metricDelta(first, last, "packetsReceived");
  const framesDecoded = metricDelta(first, last, "framesDecoded");
  const framesReceived = metricDelta(first, last, "framesReceived");
  const seconds = Math.max(1, (samples[samples.length - 1].at - samples[0].at) / 1000);
  const size = sizeIsStable(samples);
  const remoteSamples = samples.map((sample) => sample.remoteHealth).filter(Boolean);
  const remoteStatuses = [...new Set(remoteSamples.map((item) => item.status).filter(Boolean))].slice(0, 12);
  return {
    status: "observed",
    observation_window_ms: windowMs,
    sample_interval_ms: intervalMs,
    sample_count: samples.length,
    first_packets_received: packets.first,
    last_packets_received: packets.last,
    first_frames_decoded: framesDecoded.first,
    last_frames_decoded: framesDecoded.last,
    first_frames_received: framesReceived.first,
    last_frames_received: framesReceived.last,
    estimated_fps: framesDecoded.delta === null ? null : Number((framesDecoded.delta / seconds).toFixed(2)),
    estimated_packet_rate: packets.delta === null ? null : Number((packets.delta / seconds).toFixed(2)),
    video_size_stable: size.status,
    stable_video_width: size.width,
    stable_video_height: size.height,
    connection_remained_connected: allStatesConnected(samples, "connectionState"),
    ice_remained_connected: allStatesConnected(samples, "iceConnectionState"),
    console_errors_added: Math.max(0, consoleErrors.length - consoleErrorBaseline),
    page_errors_added: Math.max(0, pageErrors.length - pageErrorBaseline),
    remote_health_samples: remoteSamples.length,
    remote_health_statuses: remoteStatuses,
    remote_active_peer_connections_first: remoteSamples[0]?.activePeerConnections ?? null,
    remote_active_peer_connections_last: remoteSamples[remoteSamples.length - 1]?.activePeerConnections ?? null,
    remote_system_metrics: latestAvailableMetric(samples, "systemMetrics"),
    remote_stability_metrics: latestAvailableMetric(samples, "stabilityMetrics"),
    post_close_active_peer_connections: null,
    remote_active_peer_cleaned: "not_available",
  };
}

async function collectStabilitySamples({ page, baseUrl, windowMs, intervalMs }) {
  // 采样发生在首帧之后，目的只是观察现有 browser session，不新建 offer 或控制动作。
  if (!windowMs) {
    return [];
  }
  const samples = [];
  const deadline = Date.now() + windowMs;
  do {
    const [pageState, remoteHealth] = await Promise.all([collectPageState(page), loadRemoteHealth(baseUrl)]);
    samples.push({ at: Date.now(), pageState, remoteHealth });
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, Math.min(intervalMs, remaining)));
  } while (Date.now() <= deadline);
  return samples;
}

async function run() {
  const outputPath = path.resolve(process.env.ROBER_O7_BROWSER_SMOKE_OUTPUT || defaultOutput);
  const timeoutMs = Number(process.env.ROBER_O7_BROWSER_SMOKE_TIMEOUT_MS || 12000);
  const stabilityMs = Math.max(0, Number(process.env.ROBER_O7_BROWSER_SMOKE_STABILITY_MS || 0) || 0);
  const sampleIntervalMs = Math.max(1000, Number(process.env.ROBER_O7_BROWSER_SMOKE_SAMPLE_INTERVAL_MS || 5000) || 5000);
  let baseUrl = DEFAULT_BASE_URL;
  try {
    baseUrl = normalizeBaseUrl(process.env.ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL || process.env.ROBER_O7_BROWSER_SMOKE_BASE_URL || DEFAULT_BASE_URL);
  } catch (error) {
    const result = baseResult("blocked_unsafe_url", error instanceof Error ? error.message : "base_url_invalid");
    await writeAndPrint(result, outputPath);
    process.exitCode = 2;
    return;
  }

  const playwright = await loadPlaywright();
  if (!playwright) {
    const remoteHealth = await loadRemoteHealth(baseUrl);
    const result = {
      ...baseResult(baseUrl, "playwright_dependency_missing_use_npx_p_playwright_or_install_browser_runtime"),
      status: "degraded",
      failure_category: "dependency",
      playwright_available: false,
      remote_health_status: remoteHealth.status,
      remote_active_peer_connections: remoteHealth.activePeerConnections,
    };
    await writeAndPrint(result, outputPath);
    process.exitCode = process.env.ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME === "1" ? 2 : 0;
    return;
  }

  const consoleErrors = [];
  const pageErrors = [];
  let browser;
  let page;
  const startedAt = Date.now();
  const remoteHealth = await loadRemoteHealth(baseUrl);
  const result = {
    ...baseResult(baseUrl, "starting"),
    playwright_available: true,
    remote_health_status: remoteHealth.status,
    remote_active_peer_connections: remoteHealth.activePeerConnections,
  };

  try {
    browser = await playwright.chromium.launch({ headless: true });
    result.browser_available = true;
    page = await browser.newPage();
    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        consoleErrors.push(`${message.type()}:${message.text()}`.slice(0, 500));
      }
    });
    page.on("pageerror", (error) => {
      pageErrors.push(String(error.message || error).slice(0, 500));
    });

    await page.addInitScript(() => {
      window.__roberPeerStates = [];
      window.__roberOfferPayloads = [];
      window.__roberOfferResponses = [];
      window.__roberOnTrackEvents = [];
      const nativeFetch = window.fetch.bind(window);
      window.fetch = async (...args) => {
        const response = await nativeFetch(...args);
        const url = typeof args[0] === "string" ? args[0] : args[0]?.url;
        if (typeof url === "string" && url.endsWith("/offer")) {
          // 页面脚本不暴露 peer_id，smoke 包一层 fetch 只为后续释放服务端 peer。
          response
            .clone()
            .json()
            .then((payload) => {
              window.__roberOfferPayloads.push(payload);
              window.__roberOfferResponses.push({
                ok: response.ok,
                status: response.status,
                payload: {
                  peer_id: typeof payload?.peer_id === "string" ? payload.peer_id : undefined,
                  reason: typeof payload?.reason === "string" ? payload.reason : undefined,
                  detail: typeof payload?.detail === "string" ? payload.detail : undefined,
                },
              });
            })
            .catch(() => undefined);
        }
        return response;
      };
      const NativePeer = window.RTCPeerConnection;
      window.RTCPeerConnection = class RoberSmokePeer extends NativePeer {
        constructor(...args) {
          super(...args);
          window.__roberLastPeer = this;
          const update = () => {
            window.__roberPeerStates.push({
              connectionState: this.connectionState,
              iceConnectionState: this.iceConnectionState,
              iceGatheringState: this.iceGatheringState,
              signalingState: this.signalingState,
              at: Date.now(),
            });
          };
          ["connectionstatechange", "iceconnectionstatechange", "icegatheringstatechange", "signalingstatechange"].forEach((eventName) => {
            this.addEventListener(eventName, update);
          });
          this.addEventListener("track", (event) => {
            window.__roberOnTrackEvents.push({
              kind: event.track?.kind || null,
              id: event.track?.id || null,
              readyState: event.track?.readyState || null,
              muted: event.track?.muted ?? null,
              streamCount: event.streams?.length || 0,
              at: Date.now(),
            });
          });
          update();
        }
      };
    });

    await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    await page.locator("#start").click({ timeout: Math.min(timeoutMs, 5000) });
    result.start_clicked = true;
    result.offer_executed_by_browser = true;

    await page.waitForFunction(
      () => {
        const video = document.querySelector("video");
        return Boolean(video && video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0);
      },
      { timeout: timeoutMs },
    );

    const videoState = await collectPageState(page);
    const firstFrameMs = Date.now() - startedAt;
    const consoleErrorBaseline = consoleErrors.length;
    const pageErrorBaseline = pageErrors.length;
    const stabilitySamples = await collectStabilitySamples({
      page,
      baseUrl,
      windowMs: stabilityMs,
      intervalMs: sampleIntervalMs,
    });

    result.status = "ok";
    result.failure_category = "none";
    result.first_frame_received = true;
    result.video_width = videoState.videoWidth;
    result.video_height = videoState.videoHeight;
    result.first_frame_ms = firstFrameMs;
    result.observation_window_ms = stabilityMs || Math.min(1000, timeoutMs);
    result.final_ready_state = videoState.readyState;
    result.stable_video_width = videoState.videoWidth;
    result.stable_video_height = videoState.videoHeight;
    applyPageState(result, videoState);
    if (stabilitySamples.length > 0) {
      applyPageState(result, stabilitySamples[stabilitySamples.length - 1].pageState);
    }
    result.stability_summary = buildStabilitySummary({
      samples: stabilitySamples,
      windowMs: stabilityMs,
      intervalMs: sampleIntervalMs,
      consoleErrorBaseline,
      pageErrorBaseline,
      consoleErrors,
      pageErrors,
    });
    result.blocked_reason = "none";
  } catch (error) {
    const peerState = page ? await collectPageState(page) : {};
    result.status = "failed";
    result.blocked_reason = error instanceof Error ? error.message : "browser_smoke_failed";
    applyPageState(result, peerState);
    result.failure_category = classifyFailure({ error, result, consoleErrors, pageErrors });
    result.observation_window_ms = Date.now() - startedAt;
  } finally {
    if (page && result.server_peer_id) {
      // 浏览器关闭不会通知 HTTP signaling，显式 close 可以让下一轮 smoke 不被单 peer 保护挡住。
      result.server_peer_close_status = await page
        .evaluate(async (peerId) => {
          const response = await fetch(`/peers/${peerId}/close`, { method: "POST" });
          const payload = await response.json().catch(() => ({}));
          return `${response.status}:${payload.closed === true ? "closed" : payload.reason || "not_closed"}`;
        }, result.server_peer_id)
        .catch((error) => `close_failed:${error instanceof Error ? error.message : "unknown"}`);
    }
    if (browser) {
      await browser.close().catch(() => undefined);
    }
    result.post_smoke_remote_health = await loadRemoteHealth(baseUrl);
    if (result.stability_summary) {
      result.stability_summary.post_close_active_peer_connections = result.post_smoke_remote_health.activePeerConnections;
      result.stability_summary.remote_active_peer_cleaned =
        typeof result.post_smoke_remote_health.activePeerConnections === "number"
          ? result.post_smoke_remote_health.activePeerConnections === 0
            ? "cleaned"
            : "not_cleaned"
          : "not_available";
    }
  }

  result.console_errors = consoleErrors;
  result.page_errors = pageErrors;
  result.console_error_count = consoleErrors.length;
  result.page_error_count = pageErrors.length;
  if (result.status === "ok") {
    result.failure_category = "none";
  }
  await writeAndPrint(result, outputPath);
  process.exitCode = result.first_frame_received || process.env.ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME !== "1" ? 0 : 2;
}

run().catch(async (error) => {
  const outputPath = path.resolve(process.env.ROBER_O7_BROWSER_SMOKE_OUTPUT || defaultOutput);
  const result = baseResult(DEFAULT_BASE_URL, error instanceof Error ? error.message : "browser_smoke_uncaught_error");
  await writeAndPrint(result, outputPath);
  process.exitCode = 2;
});
