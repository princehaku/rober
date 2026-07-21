import fs from "node:fs";

const logPath = process.env.LATENCY_NETWORK_GUARD_LOG;
const originalFetch = globalThis.fetch;
const loopbackHosts = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);

function append(record) {
  // 网络审计采用逐行追加，进程异常退出时也尽量保留最后一次目标判断。
  if (logPath) {
    fs.appendFileSync(logPath, `${JSON.stringify(record)}\n`, "utf8");
  }
}

globalThis.fetch = async function loopbackOnlyFetch(input, init) {
  const rawUrl = typeof input === "string" || input instanceof URL ? String(input) : input.url;
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    // Node 上游代理应始终使用绝对 URL；无法解析时 fail closed。
    append({ at_ms: Date.now(), allowed: false, url: rawUrl, reason: "invalid_absolute_url" });
    throw new Error("latency_fixture_blocked_invalid_url");
  }
  const allowed = ["http:", "https:"].includes(parsed.protocol) && loopbackHosts.has(parsed.hostname);
  append({
    at_ms: Date.now(),
    allowed,
    method: String(init?.method ?? (typeof input === "object" && "method" in input ? input.method : "GET")),
    url: parsed.toString(),
    host: parsed.hostname,
  });
  if (!allowed) {
    // 非 loopback 一律拒绝，不能因为 UI 默认值或遗漏 query 触达现场设备。
    throw new Error(`latency_fixture_blocked_non_loopback_host:${parsed.hostname}`);
  }
  return originalFetch(input, init);
};
