#!/usr/bin/env python3
"""只把 loopback relay 的健康探针暴露给受控临时隧道。"""

from __future__ import annotations

import argparse
import http.client
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# 外部请求目标必须足够短，避免把拒绝入口变成内存放大器。
MAX_REQUEST_TARGET_BYTES = 2048
# 请求头只用于本地限流检查，绝不会转发给上游 relay。
MAX_REQUEST_HEADER_BYTES = 8192
MAX_REQUEST_HEADERS = 40
# 健康响应应很小；异常大的上游 body 必须 fail closed。
MAX_UPSTREAM_BODY_BYTES = 65536
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 2.0
LOOPBACK_HOST = "127.0.0.1"
ALLOWED_TARGET = "/healthz"


def _raw_request_target(handler: BaseHTTPRequestHandler) -> str:
    """从原始 request-line 取 target，绕开标准库对双斜杠的归一化。"""

    # requestline 仍保留网络原文；只分三段可避免 path 中空白被静默接受。
    # 不能直接依赖 handler.path，因为 Python 会把双斜杠 target 归一化。
    # 保留 raw target 是阻断 //healthz 绕过 allowlist 的关键安全边界。
    parts = handler.requestline.split()
    return parts[1] if len(parts) == 3 else ""


def _request_headers_within_limit(handler: BaseHTTPRequestHandler) -> bool:
    """限制 header 数量和字节数，但不消费或转发任何敏感值。"""

    # 这里只计算长度，不把 Authorization、Cookie、Host 等内容写入日志。
    # header 计数与总字节数同时设限，避免大量短 header 绕过单项限制。
    # UTF-8 长度按网络可见字节估算，不按 Python 字符数低估开销。
    items = list(handler.headers.items())
    if len(items) > MAX_REQUEST_HEADERS:
        return False
    total = sum(len(name.encode("utf-8")) + len(value.encode("utf-8")) + 4 for name, value in items)
    return total <= MAX_REQUEST_HEADER_BYTES


class HealthzAllowlistHandler(BaseHTTPRequestHandler):
    """只允许精确 GET/HEAD /healthz 的最小反向代理。"""

    protocol_version = "HTTP/1.1"
    # 固定产品标识，避免默认响应泄露 Python 小版本与操作系统信息。
    server_version = "trashbot-healthz-proxy"
    sys_version = ""

    # 关闭默认访问日志，避免 raw target、Host 或公网地址进入 capture 日志。
    def log_message(self, _format: str, *_args: object) -> None:
        return

    def version_string(self) -> str:
        """固定 Server 值，避免泄露 Python 运行时版本。"""

        return self.server_version

    def _send_fixed(self, status: int, body: bytes = b"", *, allow: bool = False) -> None:
        """返回不含请求细节的固定响应，并主动关闭连接。"""

        # 每个公网 probe 都独立关闭，避免请求 body 或流水线污染下一次解析。
        # 所有错误 body 都是固定常量，不能拼接 raw target 或异常字符串。
        # HEAD 分支仍发送 Content-Length=0，明确保证公网侧没有响应 body。
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        if allow:
            # Allow 只在精确 /healthz method gate 上出现，不向其他 path 暴露能力。
            self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _target_is_allowed(self) -> bool:
        """只接受原始字节可精确表示为 ASCII /healthz 的 target。"""

        # 精确字符串比较自然拒绝 query、fragment-like 文本、absolute-form 与点段。
        target = _raw_request_target(self)
        try:
            # 非 ASCII target 不能与健康路径建立等价关系，直接 fail closed。
            encoded = target.encode("ascii")
        except UnicodeEncodeError:
            return False
        return len(encoded) <= MAX_REQUEST_TARGET_BYTES and target == ALLOWED_TARGET

    def _request_shape_is_safe(self) -> bool:
        """拒绝超量 header 与任何带 body/分块编码的正向健康请求。"""

        if not _request_headers_within_limit(self):
            # 431 不暴露哪个 header 触发限制，避免回显凭证字段。
            self._send_fixed(431, b'{"error":"request_headers_too_large"}\n')
            return False
        # 健康探针无需 body；拒绝它能避免外部数据滞留在连接缓冲区。
        # Transfer-Encoding 也一律拒绝，避免 chunked body 规避 Content-Length。
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            self._send_fixed(413, b'{"error":"request_body_not_allowed"}\n')
            return False
        return True

    def _fetch_upstream(self) -> tuple[int, bytes]:
        """构造固定 loopback GET；客户端 headers、body 和 target 均不可参与。"""

        # server 上的三个值只由启动参数注入，并在建服前验证为严格 loopback。
        # 每次新建短连接，不复用来自不可信公网请求的连接上下文。
        connection = http.client.HTTPConnection(
            self.server.upstream_host,
            self.server.upstream_port,
            timeout=self.server.upstream_timeout,
        )
        try:
            # 只发送固定 Connection header，不透传 Authorization/Cookie/Host/Forwarded。
            # upstream path 也是常量，公网 target 永远不能改写 relay 请求目标。
            connection.request("GET", ALLOWED_TARGET, headers={"Connection": "close"})
            response = connection.getresponse()
            body = response.read(MAX_UPSTREAM_BODY_BYTES + 1)
            # 多读一个字节用于判断是否越界，但越界内容不会返回给客户端。
            if len(body) > MAX_UPSTREAM_BODY_BYTES:
                raise http.client.HTTPException("upstream response exceeds safe limit")
            return response.status, body
        finally:
            # 即使 read/status 解析失败也关闭 socket，避免 helper cleanup 留残余连接。
            connection.close()

    def _serve_health(self, *, head_only: bool) -> None:
        """代理固定健康请求；HEAD 只返回状态且 body 长度明确为零。"""

        if not self._target_is_allowed():
            # 负向 path 在任何 upstream 操作之前返回，因此 relay request count 不变。
            self._send_fixed(404, b'{"error":"not_found"}\n')
            return
        if not self._request_shape_is_safe():
            return
        try:
            # HEAD 也调用同一个固定 GET，避免假设 relay 原生支持 HEAD。
            status, body = self._fetch_upstream()
        except (socket.timeout, TimeoutError):
            # timeout 与其他连接错误分开映射，便于运维恢复但不泄露内部详情。
            self._send_fixed(504, b'{"error":"upstream_timeout"}\n')
            return
        except (OSError, http.client.HTTPException):
            # 不把 exception 文本、上游地址或 traceback 送到公网。
            self._send_fixed(502, b'{"error":"upstream_unavailable"}\n')
            return
        self._send_fixed(status, b"" if head_only else body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """仅代理精确 GET /healthz。"""

        self._serve_health(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """以固定 upstream GET 验证健康，但公网响应不含 body。"""

        self._serve_health(head_only=True)

    def _reject_method(self) -> None:
        """精确健康路径返回 405，其他路径统一 404 避免泄露路由。"""

        if self._target_is_allowed():
            # method gate 不读取 body，并通过 Connection: close 丢弃剩余网络数据。
            self._send_fixed(405, b'{"error":"method_not_allowed"}\n', allow=True)
        else:
            # 非白名单 path 统一 404，避免用 method 差异枚举 relay 路由。
            self._send_fixed(404, b'{"error":"not_found"}\n')

    # 明确覆盖常见读写/探测方法，保证它们不会落入标准库的 501 页面。
    do_POST = _reject_method
    do_PUT = _reject_method
    do_PATCH = _reject_method
    do_DELETE = _reject_method
    do_OPTIONS = _reject_method
    do_TRACE = _reject_method
    do_CONNECT = _reject_method


class HealthzAllowlistServer(ThreadingHTTPServer):
    """保存固定 upstream 配置的并发 loopback HTTP server。"""

    # daemon worker 让 helper 终止主进程时不会被慢客户端无限拖住。
    daemon_threads = True
    # reuse 仅服务测试/一次 capture 的及时回收，不改变 loopback 监听边界。
    allow_reuse_address = True


def build_server(
    listen_host: str,
    listen_port: int,
    upstream_host: str,
    upstream_port: int,
    *,
    upstream_timeout: float = DEFAULT_UPSTREAM_TIMEOUT_SECONDS,
) -> HealthzAllowlistServer:
    """验证严格 loopback 边界后创建 server。"""

    # 不接受 localhost 或其他 127/8 地址，便于配置审计做字面确认。
    # tunnel target 与 upstream 两侧都必须是同一明确的 IPv4 loopback 语义。
    if listen_host != LOOPBACK_HOST or upstream_host != LOOPBACK_HOST:
        raise ValueError("listen and upstream hosts must both be 127.0.0.1")
    if not (0 <= int(listen_port) <= 65535) or not (1 <= int(upstream_port) <= 65535):
        # listen port=0 只允许单测自动选端口；CLI/live 会传入显式非零端口。
        raise ValueError("listen/upstream ports are outside the valid range")
    if not (0.01 <= float(upstream_timeout) <= 30.0):
        # timeout 下限防止误配置为忙等，上限避免 tunnel 请求长时间占用 worker。
        raise ValueError("upstream timeout is outside the safe range")
    server = HealthzAllowlistServer((listen_host, int(listen_port)), HealthzAllowlistHandler)
    # upstream 配置绑定到 server 实例，handler 不读取环境变量或客户端参数。
    server.upstream_host = upstream_host
    server.upstream_port = int(upstream_port)
    server.upstream_timeout = float(upstream_timeout)
    return server


def main(argv: list[str] | None = None) -> int:
    """解析显式 CLI 参数并持续服务，直到 helper 负责清理。"""

    # CLI 只暴露网络边界与 timeout，不提供自定义 allowlist/upstream path 参数。
    parser = argparse.ArgumentParser(description="Loopback-only /healthz allowlist proxy")
    # 四个网络参数全部 required，避免默认值掩盖 tunnel target 配错。
    parser.add_argument("--listen-host", required=True)
    parser.add_argument("--listen-port", required=True, type=int)
    parser.add_argument("--upstream-host", required=True)
    parser.add_argument("--upstream-port", required=True, type=int)
    parser.add_argument("--upstream-timeout", type=float, default=DEFAULT_UPSTREAM_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    # build_server 会在打开 socket 前完成 host、port 和 timeout 的 fail-closed 校验。
    server = build_server(
        args.listen_host,
        args.listen_port,
        args.upstream_host,
        args.upstream_port,
        upstream_timeout=args.upstream_timeout,
    )
    try:
        # 生命周期由 capture helper 的 PID/process-group ownership 统一管理。
        server.serve_forever()
    finally:
        # server_close 保证 helper 发终止信号后监听 socket 被及时回收。
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
