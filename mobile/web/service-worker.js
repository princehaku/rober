const CACHE_VERSION = "2026.05.19-mobile-pwa-cache-recovery-v2";
const CACHE_NAME = `rober-mobile-shell-${CACHE_VERSION}`;
const APP_SHELL_URL = "./index.html";
const OFFLINE_URL = "./offline.html";
const RECOVERY_MARKER = "mobile_pwa_cache_recovery";
const SHELL_CACHE_PREFIX = "rober-mobile-shell-";
const SHELL_URLS = [
  APP_SHELL_URL,
  "./styles.css",
  "./app.js",
  OFFLINE_URL,
  "./manifest.webmanifest",
  "./icon-192.svg",
  "./icon-512.svg",
];

function isControlOrDynamicRequest(request) {
  // 非 GET 一律绕过缓存，避免离线时缓存、排队或重放控制请求。
  if (request.method !== "GET") {
    return true;
  }
  const url = new URL(request.url);
  const path = url.pathname;
  // 后端状态、诊断、机器人命令和 ACK 都是动态控制面，必须 no-store。
  return (
    path.startsWith("/api/") ||
    path.startsWith("/robots/") ||
    path.includes("/commands") ||
    path.includes("/ack") ||
    path.includes("/diagnostics") ||
    path === "/api/collect" ||
    path === "/api/dropoff/confirm" ||
    path === "/api/cancel"
  );
}

function isNavigationRequest(request) {
  // 导航必须优先走网络，避免旧 offline shell 长期盖住当前 app shell。
  return request.mode === "navigate" || request.destination === "document";
}

function isShellAssetRequest(request) {
  const url = new URL(request.url);
  // 当前 shell 关键文件也优先走网络，离线时才回退到本版本缓存。
  return SHELL_URLS.some((asset) => url.pathname.endsWith(asset.replace("./", "/")));
}

function isOldShellCache(cacheName) {
  // 只清理本 PWA 自己的旧 shell cache，避免误删同源下其他功能的缓存。
  return cacheName.startsWith(SHELL_CACHE_PREFIX) && cacheName !== CACHE_NAME;
}

async function fetchAndRefreshCache(request, fallbackUrl) {
  const cache = await caches.open(CACHE_NAME);
  try {
    // no-store 防止浏览器 HTTP 缓存把上一轮旧壳继续交给 service worker。
    const response = await fetch(request, { cache: "no-store" });
    if (response && response.ok) {
      await cache.put(fallbackUrl || request, response.clone());
    }
    return response;
  } catch (_error) {
    // 离线 fallback 只展示恢复路径；不缓存、排队或重放控制请求。
    return (await cache.match(fallbackUrl || request)) || cache.match(OFFLINE_URL);
  }
}

self.addEventListener("install", (event) => {
  // 只预缓存静态 shell；真实机器人状态必须每次从后端读取。
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // 清理旧 shell 缓存，避免过期 UI 或旧 offline shell 继续展示错误安全策略。
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(isOldShellCache).map((key) => caches.delete(key))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (isControlOrDynamicRequest(event.request)) {
    event.respondWith(fetch(event.request, { cache: "no-store" }));
    return;
  }
  if (isNavigationRequest(event.request)) {
    event.respondWith(fetchAndRefreshCache(event.request, APP_SHELL_URL));
    return;
  }
  if (isShellAssetRequest(event.request)) {
    event.respondWith(fetchAndRefreshCache(event.request));
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).catch(() => {
        if (isNavigationRequest(event.request)) {
          return caches.match(OFFLINE_URL);
        }
        throw new Error("static_shell_unavailable");
      });
    }),
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === RECOVERY_MARKER) {
    // 页面只请求刷新静态壳缓存；这里不触发任何机器人控制面流量。
    event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)));
  }
});
