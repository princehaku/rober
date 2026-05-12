const CACHE_NAME = "rober-mobile-shell-v1";
const SHELL_URLS = [
  "./index.html",
  "./styles.css",
  "./app.js",
  "./offline.html",
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

self.addEventListener("install", (event) => {
  // 只预缓存静态 shell；真实机器人状态必须每次从后端读取。
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // 清理旧 shell 缓存，避免过期 UI 继续展示错误安全策略。
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (isControlOrDynamicRequest(event.request)) {
    event.respondWith(fetch(event.request, { cache: "no-store" }));
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).catch(() => {
        if (event.request.mode === "navigate") {
          return caches.match("./offline.html");
        }
        throw new Error("static_shell_unavailable");
      });
    }),
  );
});
