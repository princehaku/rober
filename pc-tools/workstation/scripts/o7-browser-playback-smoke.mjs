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

async function loadPlaywright() {
  // 不把 Playwright 写入依赖；现场可以用 npx -p playwright 临时注入，缺失时 fail closed。
  try {
    return await import("playwright");
  } catch {
    return null;
  }
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
    const result = {
      ...baseResult(baseUrl, "playwright_dependency_missing_use_npx_p_playwright_or_install_browser_runtime"),
      status: "degraded",
      playwright_available: false,
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
  const result = {
    ...baseResult(baseUrl, "starting"),
    playwright_available: true,
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
      return {
        videoWidth: video?.videoWidth || null,
        videoHeight: video?.videoHeight || null,
        connectionState: peer?.connectionState || null,
        iceConnectionState: peer?.iceConnectionState || null,
        iceGatheringState: peer?.iceGatheringState || null,
        signalingState: peer?.signalingState || null,
      };
    });

    result.status = "ok";
    result.first_frame_received = true;
    result.video_width = videoState.videoWidth;
    result.video_height = videoState.videoHeight;
    result.first_frame_ms = Date.now() - startedAt;
    result.connection_state = videoState.connectionState;
    result.ice_connection_state = videoState.iceConnectionState;
    result.ice_gathering_state = videoState.iceGatheringState;
    result.signaling_state = videoState.signalingState;
    result.blocked_reason = "none";
  } catch (error) {
    const peerState = page
      ? await page
          .evaluate(() => {
            const peer = window.__roberLastPeer;
            return {
              connectionState: peer?.connectionState || null,
              iceConnectionState: peer?.iceConnectionState || null,
              iceGatheringState: peer?.iceGatheringState || null,
              signalingState: peer?.signalingState || null,
            };
          })
          .catch(() => ({}))
      : {};
    result.status = "failed";
    result.blocked_reason = error instanceof Error ? error.message : "browser_smoke_failed";
    result.connection_state = peerState.connectionState || null;
    result.ice_connection_state = peerState.iceConnectionState || null;
    result.ice_gathering_state = peerState.iceGatheringState || null;
    result.signaling_state = peerState.signalingState || null;
  } finally {
    if (browser) {
      await browser.close().catch(() => undefined);
    }
  }

  result.console_errors = consoleErrors;
  result.page_errors = pageErrors;
  await writeAndPrint(result, outputPath);
  process.exitCode = result.first_frame_received || process.env.ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME !== "1" ? 0 : 2;
}

run().catch(async (error) => {
  const outputPath = path.resolve(process.env.ROBER_O7_BROWSER_SMOKE_OUTPUT || defaultOutput);
  const result = baseResult(DEFAULT_BASE_URL, error instanceof Error ? error.message : "browser_smoke_uncaught_error");
  await writeAndPrint(result, outputPath);
  process.exitCode = 2;
});
