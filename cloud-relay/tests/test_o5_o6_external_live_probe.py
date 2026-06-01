import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = REPO_ROOT / "cloud-relay" / "scripts" / "o5_o6_external_live_probe.py"
SPEC = importlib.util.spec_from_file_location("o5_o6_external_live_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class ProbeServer:
    """用最小 HTTP server 验证真实 urllib 行为，不引入第三方 test dependency。"""

    def __init__(self, routes):
        self.routes = routes
        self.requests = []
        self.server = None
        self.thread = None

    def __enter__(self):
        routes = self.routes
        requests = self.requests

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                # 记录 method/path/authorization，证明 probe 只 GET 且按边界处理 bearer。
                requests.append(
                    {
                        "method": "GET",
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                    }
                )
                status, body = routes.get(self.path, (404, {"schema": "missing"}))
                payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                # 单测不打印 HTTP access log，避免淹没失败断言。
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        return False

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_port}"


def _args(**overrides):
    values = {
        "once_json": True,
        "pc_base_url": "",
        "cloud_base_url": "",
        "timeout_ms": 1000,
    }
    values.update(overrides)
    return type("Args", (), values)()


class O5O6PythonExternalLiveProbeTest(unittest.TestCase):
    def test_missing_urls_fail_closed_without_secret_output(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            result = probe.run_probe(_args())

        # 未配置 URL 是可读 fail-closed 证据，不应崩溃成 traceback。
        self.assertEqual(result["schema"], "trashbot.o5_o6.external_live_probe.v1")
        self.assertEqual(result["runner"], "python_stdlib")
        self.assertEqual(result["probe_status"], "fail_closed")
        self.assertEqual(result["token_status"], "absent")
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["reads_hardware"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["delivery_success"])
        self.assertEqual(result["tls_evidence"]["tls_status"], "not_configured")
        self.assertFalse(result["tls_evidence"]["tls_observed"])
        self.assertEqual([item["failure_category"] for item in result["endpoints"]], ["base_url_not_configured"] * 3)
        self.assertNotIn("Bearer", json.dumps(result))

    def test_observed_contract_uses_get_and_redacts_bearer(self):
        with ProbeServer(
            {
                "/api/o5/readiness/health": (
                    200,
                    {
                        "schema": "trashbot.o5.readiness_health.v1",
                        "safe_to_control": False,
                        "sends_commands": False,
                        "robot_control_executed": False,
                        "delivery_success": False,
                    },
                ),
                "/api/o6/archive/health": (
                    200,
                    {
                        "schema": "trashbot.o6.archive_health.v1",
                        "safe_to_control": False,
                        "sends_commands": False,
                        "robot_control_executed": False,
                        "delivery_success": False,
                    },
                ),
            }
        ) as cloud:
            encoded = probe.urllib.parse.quote(cloud.base_url, safe="")
            pc_path = f"/api/o5-o6/cloud-relay-health?baseUrl={encoded}"
            with ProbeServer(
                {
                    pc_path: (
                        200,
                        {
                            "schema": "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1",
                            "token_status": "present",
                            "token_envs": ["ROBER_CLOUD_RELAY_BEARER_TOKEN"],
                            "safe_to_control": False,
                            "sends_commands": False,
                            "robot_control_executed": False,
                            "delivery_success": False,
                        },
                    )
                }
            ) as pc:
                with mock.patch.dict("os.environ", {"ROBER_CLOUD_RELAY_BEARER_TOKEN": "secret-token"}, clear=True):
                    result = probe.run_probe(_args(pc_base_url=pc.base_url, cloud_base_url=cloud.base_url))

        # 三个 endpoint 都通过 contract，但结论仍是 fail-closed contract，不代表可控制。
        self.assertEqual(result["probe_status"], "observed_fail_closed_contract")
        self.assertEqual(result["token_status"], "present")
        self.assertEqual(result["summary"]["reachable_count"], 3)
        self.assertEqual(result["summary"]["schema_matched_count"], 3)
        self.assertEqual(result["tls_evidence"]["tls_status"], "not_applicable")
        self.assertEqual(result["tls_evidence"]["scheme"], "http")
        self.assertEqual({item["contract_status"] for item in result["endpoints"]}, {"observed_fail_closed_contract"})
        self.assertTrue(all(item["method"] == "GET" for item in cloud.requests + pc.requests))
        self.assertTrue(all(item["authorization"] == "Bearer secret-token" for item in cloud.requests))
        self.assertTrue(all(item["authorization"] is None for item in pc.requests))
        self.assertNotIn("secret-token", json.dumps(result))

    def test_https_cloud_url_adds_sanitized_tls_evidence(self):
        # HTTPS 证据通过 mock 注入，避免单测访问真实公网或依赖现场证书。
        tls_evidence = {
            "tls_status": "observed",
            "scheme": "https",
            "hostname_redacted": "sha256:abcdef123456",
            "host_status": "redacted_public_or_custom_host",
            "port": 443,
            "tls_observed": True,
            "tls_version": "TLSv1.3",
            "cipher_status": "present",
            "cipher_bits": 256,
            "certificate": {
                "not_before": "Jan 01 00:00:00 2026 GMT",
                "not_after": "Jan 01 00:00:00 2027 GMT",
                "certificate_expiry_days": 200,
                "issuer_summary": {"field_count": 2, "common_name_status": "present"},
                "subject_summary": {"field_count": 2, "common_name_status": "present"},
                "subject_alt_name_summary": {"dns_name_count": 2, "ip_address_count": 0},
            },
            "verification_error": "none",
        }
        with ProbeServer(
            {
                "/api/o5/readiness/health": (200, {"schema": "trashbot.o5.readiness_health.v1"}),
                "/api/o6/archive/health": (200, {"schema": "trashbot.o6.archive_health.v1"}),
            }
        ) as cloud:
            cloud_base = "https://cloud.example.test"
            pc_path = f"/api/o5-o6/cloud-relay-health?baseUrl={probe.urllib.parse.quote(cloud_base, safe='')}"
            with ProbeServer({pc_path: (200, {"schema": "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1"})}) as pc:
                with mock.patch.object(probe, "fetch_json") as fetch_json:
                    fetch_json.side_effect = [
                        {"ok": True, "status": 200, "body": {"schema": "trashbot.o5.readiness_health.v1"}, "bad_json": False},
                        {"ok": True, "status": 200, "body": {"schema": "trashbot.o6.archive_health.v1"}, "bad_json": False},
                        {"ok": True, "status": 200, "body": {"schema": "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1"}, "bad_json": False},
                    ]
                    with mock.patch.object(probe, "collect_tls_evidence", return_value=tls_evidence):
                        result = probe.run_probe(_args(pc_base_url=pc.base_url, cloud_base_url=cloud_base))

        # TLS 摘要进入统一 artifact，但 host 和证书 DN 仍只保留脱敏/计数信息。
        self.assertEqual(result["probe_status"], "observed_fail_closed_contract")
        self.assertEqual(result["tls_evidence"]["tls_status"], "observed")
        self.assertEqual(result["tls_evidence"]["hostname_redacted"], "sha256:abcdef123456")
        self.assertEqual(result["tls_evidence"]["certificate"]["subject_alt_name_summary"]["dns_name_count"], 2)
        self.assertNotIn("cloud.example.test", json.dumps(result))

    def test_certificate_summary_bounds_subject_and_expiry(self):
        cert = {
            "notBefore": "Jan 01 00:00:00 2026 GMT",
            "notAfter": "Jan 11 00:00:00 2026 GMT",
            "issuer": ((("commonName", "Issuer CA"),), (("organizationName", "Issuer Org"),)),
            "subject": ((("commonName", "cloud.example.test"),),),
            "subjectAltName": (("DNS", "cloud.example.test"), ("DNS", "api.example.test")),
        }
        summary = probe.summarize_certificate(
            cert,
            now=probe.datetime.datetime(2026, 1, 1, tzinfo=probe.datetime.timezone.utc),
        )

        # 证书摘要只保留有效期、字段存在状态和 SAN 数量，不输出完整 subject/issuer 值。
        self.assertEqual(summary["certificate_expiry_days"], 10)
        self.assertEqual(summary["issuer_summary"]["common_name_status"], "present")
        self.assertEqual(summary["subject_summary"]["common_name_status"], "present")
        self.assertEqual(summary["subject_alt_name_summary"]["dns_name_count"], 2)
        self.assertNotIn("cloud.example.test", json.dumps(summary))

    def test_http_bad_json_schema_sensitive_and_dangerous_flags_are_classified(self):
        with ProbeServer(
            {
                "/api/o5/readiness/health": (401, {"schema": "trashbot.o5.readiness_health.v1"}),
                "/api/o6/archive/health": (503, b"not-json"),
            }
        ) as cloud:
            encoded = probe.urllib.parse.quote(cloud.base_url, safe="")
            pc_path = f"/api/o5-o6/cloud-relay-health?baseUrl={encoded}"
            with ProbeServer(
                {
                    pc_path: (
                        200,
                        {
                            "schema": "wrong.schema",
                            "safe_to_control": True,
                            "details": {"authorization": "Bearer abc"},
                        },
                    )
                }
            ) as pc:
                result = probe.run_probe(_args(pc_base_url=pc.base_url, cloud_base_url=cloud.base_url))

        by_name = {item["name"]: item for item in result["endpoints"]}
        # HTTP 状态、坏 JSON、schema drift、危险 true 字段和敏感 marker 都必须结构化落点。
        self.assertIn("http_401", by_name["o5_readiness"]["blocked_reasons"])
        self.assertIn("http_503", by_name["o6_archive"]["blocked_reasons"])
        self.assertIn("bad_json", by_name["o6_archive"]["blocked_reasons"])
        self.assertIn("schema_mismatch", by_name["pc_aggregate"]["blocked_reasons"])
        self.assertTrue(any(reason.startswith("dangerous_true:") for reason in by_name["pc_aggregate"]["blocked_reasons"]))
        self.assertTrue(any(reason.startswith("sensitive_marker:") for reason in by_name["pc_aggregate"]["blocked_reasons"]))
        self.assertEqual(result["probe_status"], "fail_closed")

    def test_invalid_url_and_network_unreachable_are_structured(self):
        with ProbeServer({}) as pc:
            result = probe.run_probe(
                _args(
                    pc_base_url=pc.base_url,
                    cloud_base_url="http://127.0.0.1:1",
                    timeout_ms=200,
                )
            )

        # 网络不可达归类为 endpoint failure，不影响整体 JSON 可解析性。
        by_name = {item["name"]: item for item in result["endpoints"]}
        self.assertEqual(by_name["o5_readiness"]["failure_category"], "network_or_service_unreachable")
        self.assertEqual(by_name["o6_archive"]["failure_category"], "network_or_service_unreachable")
        self.assertEqual(by_name["pc_aggregate"]["failure_category"], "http_404")
        credentialed = probe.normalize_base_url("http://user:pass@example.com/api")
        self.assertFalse(credentialed["ok"])
        self.assertEqual(credentialed["reason"], "base_url_must_not_include_credentials_query_or_hash")

    def test_cli_output_writes_same_sanitized_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "o5-o6-external-live-probe.json"
            with mock.patch.dict("os.environ", {}, clear=True):
                exit_code = probe.main(["--once-json", "--output", str(output)])

            # 输出文件用于 PC workstation 消费；内容仍是 fail-closed 脱敏 schema。
            self.assertEqual(exit_code, 2)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "trashbot.o5_o6.external_live_probe.v1")
            self.assertEqual(payload["probe_status"], "fail_closed")
            self.assertFalse(payload["safe_to_control"])
            self.assertFalse(payload["sends_commands"])
            self.assertFalse(payload["reads_hardware"])
            self.assertNotIn("Bearer", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
