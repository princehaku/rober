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
    };
  } catch {
    return {
      status: "remote_health_unreachable",
      activePeerConnections: null,
    };
  }
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

async function run() {
  const outputPath = path.resolve(process.env.ROBER_O7_BROWSER_SMOKE_OUTPUT || defaultOutput);
  const timeoutMs = Number(process.env.ROBER_O7_BROWSER_SMOKE_TIMEOUT_MS || 12000);
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

    const videoState = await page.evaluate(() => {
      const video = document.querySelector("video");
      const peer = window.__roberLastPeer;
      const offerPayload = window.__roberOfferPayloads?.[window.__roberOfferPayloads.length - 1];
      const offerResponse = window.__roberOfferResponses?.[window.__roberOfferResponses.length - 1];
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
      };
    });

    result.status = "ok";
    result.failure_category = "none";
    result.first_frame_received = true;
    result.video_width = videoState.videoWidth;
    result.video_height = videoState.videoHeight;
    result.first_frame_ms = Date.now() - startedAt;
    result.observation_window_ms = Math.min(1000, timeoutMs);
    result.final_ready_state = videoState.readyState;
    result.stable_video_width = videoState.videoWidth;
    result.stable_video_height = videoState.videoHeight;
    result.connection_state = videoState.connectionState;
    result.ice_connection_state = videoState.iceConnectionState;
    result.ice_gathering_state = videoState.iceGatheringState;
    result.signaling_state = videoState.signalingState;
    result.server_peer_id = videoState.peerId;
    Object.assign(result, summarizeOfferResponse(videoState.offerResponse));
    result.blocked_reason = "none";
  } catch (error) {
    const peerState = page
      ? await page
          .evaluate(() => {
            const peer = window.__roberLastPeer;
            const video = document.querySelector("video");
            const offerPayload = window.__roberOfferPayloads?.[window.__roberOfferPayloads.length - 1];
            const offerResponse = window.__roberOfferResponses?.[window.__roberOfferResponses.length - 1];
            return {
              connectionState: peer?.connectionState || null,
              iceConnectionState: peer?.iceConnectionState || null,
              iceGatheringState: peer?.iceGatheringState || null,
              signalingState: peer?.signalingState || null,
              readyState: video?.readyState ?? null,
              videoWidth: video?.videoWidth || null,
              videoHeight: video?.videoHeight || null,
              peerId: typeof offerPayload?.peer_id === "string" ? offerPayload.peer_id : null,
              offerResponse: offerResponse || null,
            };
          })
          .catch(() => ({}))
      : {};
    result.status = "failed";
    result.blocked_reason = error instanceof Error ? error.message : "browser_smoke_failed";
    Object.assign(result, summarizeOfferResponse(peerState.offerResponse));
    result.failure_category = classifyFailure({ error, result, consoleErrors, pageErrors });
    result.observation_window_ms = Date.now() - startedAt;
    result.final_ready_state = typeof peerState.readyState === "number" ? peerState.readyState : null;
    result.stable_video_width = typeof peerState.videoWidth === "number" ? peerState.videoWidth : null;
    result.stable_video_height = typeof peerState.videoHeight === "number" ? peerState.videoHeight : null;
    result.connection_state = peerState.connectionState || null;
    result.ice_connection_state = peerState.iceConnectionState || null;
    result.ice_gathering_state = peerState.iceGatheringState || null;
    result.signaling_state = peerState.signalingState || null;
    result.server_peer_id = peerState.peerId || null;
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
