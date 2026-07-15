"""health-only allowlist proxy 的隔离回归测试。"""

from __future__ import annotations

import http.client
import importlib.util
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


# 脚本不是 Python package，因此按受测文件路径显式加载。
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "healthz_allowlist_proxy.py"
SPEC = importlib.util.spec_from_file_location("healthz_allowlist_proxy", SCRIPT)
# 测试不复制实现，确保运行的是实际部署脚本而不是测试替身。
PROXY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PROXY)


class _FakeUpstreamHandler(BaseHTTPRequestHandler):
    """记录真正抵达 relay 的请求，供负向不穿透断言使用。"""

    # 使用 HTTP/1.1 覆盖真实 relay 的 Content-Length/连接关闭行为。
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        # 禁止测试日志回显 hostile target 或伪造的敏感 header。
        return

    def do_GET(self):  # noqa: N802 - 测试 HTTP handler 固定命名。
        # 只记录白名单摘要，测试本身也不保存敏感 header 值。
        # path/method 用于证明 proxy 只构造固定 GET /healthz。
        # 布尔值用于证明 Authorization/Cookie/Forwarded 没有穿透。
        self.server.requests.append(
            {
                "path": self.path,
                "method": self.command,
                "sensitive_headers_present": any(
                    name.lower() in {"authorization", "cookie", "forwarded", "x-forwarded-for"}
                    for name in self.headers
                ),
                "host": self.headers.get("Host", ""),
            }
        )
        if self.server.delay_seconds:
            # 可控 delay 仅模拟 upstream timeout，不访问外部网络。
            time.sleep(self.server.delay_seconds)
        body = b'{"ok":true}\n'
        self.send_response(200)
        # fake body 很小，便于同时验证 GET 透传与 HEAD 零 body。
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            # timeout 用例会主动关闭 proxy->upstream 连接，这是预期行为。
            pass


def _start_http_server(handler):
    """在随机 loopback 端口启动 helper-owned server。"""

    # port=0 由内核选空闲端口，避免测试写死机器状态。
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    # daemon thread 保证断言失败时测试进程仍可清理退出。
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class HealthzAllowlistProxyTest(unittest.TestCase):
    """验证正向健康能力和全部负向隔离边界。"""

    def setUp(self):
        # fake upstream 暴露 count/header 事实，但不实现任何任务或控制路由。
        # 所有 listener 都显式绑定 127.0.0.1，避免单测意外开放 LAN 端口。
        self.upstream, self.upstream_thread = _start_http_server(_FakeUpstreamHandler)
        self.upstream.requests = []
        # delay 默认关闭，只有 timeout 用例才临时开启。
        self.upstream.delay_seconds = 0.0
        self.proxy = PROXY.build_server(
            # proxy 和 upstream 都由本用例拥有，tearDown 负责完整回收。
            "127.0.0.1",
            0,
            "127.0.0.1",
            self.upstream.server_address[1],
            upstream_timeout=0.15,
        )
        self.proxy_thread = threading.Thread(target=self.proxy.serve_forever, daemon=True)
        # 先完成 bind 再启动线程，因此发请求时 server_address 已稳定。
        self.proxy_thread.start()

    def tearDown(self):
        # 每个用例收回两个监听 socket，避免测试残留影响 live gate。
        # shutdown 在 server_close 前执行，确保 serve_forever 循环先退出。
        self.proxy.shutdown()
        self.proxy.server_close()
        self.upstream.shutdown()
        self.upstream.server_close()
        self.proxy_thread.join(timeout=2)
        # join 设限避免测试清理自身成为无限等待 blocker。
        self.upstream_thread.join(timeout=2)

    def _request(self, method, target, *, headers=None, body=None):
        """通过正常 HTTP client 请求 proxy 并返回安全摘要。"""

        # 客户端只连 proxy，绝不在测试 helper 中直接请求 fake upstream。
        connection = http.client.HTTPConnection("127.0.0.1", self.proxy.server_address[1], timeout=2)
        connection.request(method, target, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        # 响应只保存在当前用例内，不落盘 hostile target 或 header。
        result = response.status, dict(response.getheaders()), payload
        connection.close()
        return result

    def _raw_request(self, target):
        """发送不被客户端库归一化的 request-target。"""

        # raw socket 保留 //、absolute-form 与超长 target，避免 http.client 预处理。
        with socket.create_connection(("127.0.0.1", self.proxy.server_address[1]), timeout=2) as sock:
            sock.sendall(f"GET {target} HTTP/1.1\r\nHost: rejected.invalid\r\nConnection: close\r\n\r\n".encode())
            response = sock.recv(4096)
        # 只返回 status code，hostile response/body 不进入测试输出。
        return int(response.split(b" ", 2)[1])

    def test_exact_get_and_head_are_the_only_forwarded_requests(self):
        # GET 返回 relay body；HEAD 复用 upstream GET 健康检查但公网 body 为零。
        # 两次 upstream 记录都必须是固定 path，证明外部 method 未透传。
        get_status, _, get_body = self._request("GET", "/healthz")
        head_status, head_headers, head_body = self._request("HEAD", "/healthz")
        self.assertEqual((get_status, get_body), (200, b'{"ok":true}\n'))
        self.assertEqual(head_status, 200)
        self.assertEqual(head_headers["Content-Length"], "0")
        self.assertEqual(head_body, b"")
        # HEAD 的 Content-Length 明确为零，不泄露 relay body 长度。
        self.assertEqual([item["path"] for item in self.upstream.requests], ["/healthz", "/healthz"])

    def test_negative_paths_queries_and_encodings_never_reach_upstream(self):
        # 这些 target 覆盖 status、archive、command、query、编码和解析绕过。
        # absolute-form 与反斜杠专门覆盖代理链常见解析差异。
        targets = [
            "/readyz",
            "/preflightz",
            "/api/status",
            "/api/commands/collect",
            "/api/o6/archive/tasks",
            "/healthz?x=1",
            "//healthz",
            "/%68ealthz",
            "/healthz/..",
            "/healthz\\escape",
            "http://127.0.0.1/healthz",
            "/" + "x" * (PROXY.MAX_REQUEST_TARGET_BYTES + 1),
        ]
        before = len(self.upstream.requests)
        # raw helper 保证每个 target 原样抵达 proxy 的 request-line。
        statuses = [self._raw_request(target) for target in targets]
        self.assertEqual(statuses, [404] * len(targets))
        # 404 本身不足够，upstream count 不变才证明真正的“不穿透”。
        self.assertEqual(len(self.upstream.requests), before)

    def test_non_allowed_methods_return_405_without_upstream_contact(self):
        # 精确 path 的 method gate 返回固定 Allow；不读取或转发 POST body。
        # 五种方法覆盖写入、删除、预检与常见 API method。
        before = len(self.upstream.requests)
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            # 故意携带 body，证明 proxy 关闭连接而非交给 relay handler。
            status, headers, _ = self._request(method, "/healthz", body=b"never-forward")
            self.assertEqual(status, 405)
            self.assertEqual(headers.get("Allow"), "GET, HEAD")
        self.assertEqual(len(self.upstream.requests), before)
        # 相同 POST 对非健康 path 必须是 404，不能泄露 method allowlist。
        self.assertEqual(self._request("POST", "/api/commands/collect")[0], 404)

    def test_sensitive_client_headers_are_not_forwarded(self):
        # Host 由 http.client 为固定 upstream 重建；其余敏感 header 完全丢弃。
        # 测试值是明显占位符，不能误用真实 token 或 cookie。
        status, _, _ = self._request(
            "GET",
            "/healthz",
            headers={
                "Authorization": "Bearer redacted-test-value",
                "Cookie": "session=redacted-test-value",
                "Forwarded": "for=203.0.113.1",
                "X-Forwarded-For": "203.0.113.1",
                "Host": "public.invalid",
            },
        )
        self.assertEqual(status, 200)
        observed = self.upstream.requests[-1]
        # upstream 只看到 http.client 为 loopback endpoint 构造的新 Host。
        self.assertFalse(observed["sensitive_headers_present"])
        self.assertTrue(observed["host"].startswith("127.0.0.1:"))

    def test_upstream_timeout_and_connection_error_are_redacted(self):
        # timeout 只返回固定 504，不包含异常、路径或上游响应片段。
        # 短 timeout 让回归快速完成，同时覆盖 socket.timeout 映射。
        self.upstream.delay_seconds = 0.4
        status, _, body = self._request("GET", "/healthz")
        self.assertEqual(status, 504)
        self.assertEqual(body, b'{"error":"upstream_timeout"}\n')
        self.proxy.upstream_port = 1
        # 本地关闭端口模拟 connection refused，不产生任何公网依赖。
        status, _, body = self._request("GET", "/healthz")
        self.assertEqual(status, 502)
        self.assertEqual(body, b'{"error":"upstream_unavailable"}\n')

    def test_non_loopback_configuration_is_rejected(self):
        # listen 或 upstream 任一越出字面 loopback 都必须在启动前失败。
        # 0.0.0.0 覆盖意外公网监听，localhost 覆盖 DNS/IPv6 语义漂移。
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            PROXY.build_server("0.0.0.0", 0, "127.0.0.1", 8088)
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            PROXY.build_server("127.0.0.1", 0, "localhost", 8088)


if __name__ == "__main__":
    unittest.main()
