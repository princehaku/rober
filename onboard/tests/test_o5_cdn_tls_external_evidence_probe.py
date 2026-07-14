"""O5 CDN/TLS external evidence probe 单测。"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o5_cdn_tls_external_evidence_probe.py"
SPEC = importlib.util.spec_from_file_location("o5_cdn_tls_external_evidence_probe", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
# dataclass 会从 sys.modules 回查模块命名空间；手动加载时必须先注册。
sys.modules[SPEC.name] = PROBE
SPEC.loader.exec_module(PROBE)


def fake_target() -> str:
    """测试 URL 只用于内存输入；artifact 必须证明它没有被持久化。"""

    return "https://cdn.example.test/rober/"


class O5CdnTlsExternalEvidenceProbeTests(unittest.TestCase):
    """只测 probe contract，不访问真实公网，真实访问由 sprint smoke 命令覆盖。"""

    def test_successful_head_probe_writes_only_sanitized_external_delta(self) -> None:
        """HEAD 返回 2xx 时只接受窄 O5 CDN/TLS delta，不提升生产或控制声明。"""

        calls: list[str] = []

        def request_once(target, method, timeout_sec):
            calls.append(method)
            return PROBE.HttpObservation(
                method=method,
                status_code=204,
                elapsed_ms=180,
                content_length=0,
                tls_handshake_observed=True,
                certificate_valid_for_host=True,
            )

        artifact = PROBE.build_probe_artifact(
            fake_target(),
            "env_override",
            generated_at="2026-07-13T05:13:00Z",
            request_once=request_once,
        )

        self.assertEqual(["HEAD"], calls)
        self.assertEqual(PROBE.SCHEMA, artifact["schema"])
        self.assertEqual("cdn_tls_external_evidence", artifact["evidence_key"])
        self.assertEqual("cdn_tls_external_evidence_observed", artifact["cdn_tls_external_evidence_status"])
        self.assertTrue(artifact["probe_attempted"])
        self.assertTrue(artifact["external_request_attempted"])
        self.assertTrue(artifact["tls_handshake_observed"])
        self.assertTrue(artifact["certificate_valid_for_host"])
        self.assertEqual("2xx", artifact["http_status_class"])
        self.assertEqual("o5_cdn_tls_external_evidence_delta", artifact["accepted_claim"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["robot_control_executed"])
        self.assertFalse(artifact["route_execution_success"])
        self.assertFalse(artifact["hil_pass"])
        self.assertFalse(artifact["production_cloud_ready"])
        self.assertIn("delivery_success=false", artifact["fixed_false_invariants"])
        self.assertIn("safe_to_control=false", artifact["fixed_false_invariants"])
        self.assertNotIn("cdn.example.test", json.dumps(artifact, sort_keys=True))
        self.assertFalse(PROBE.redaction_violations(artifact))

    def test_head_rejected_uses_bounded_get_without_body_or_headers(self) -> None:
        """HEAD 被 CDN 拒绝时允许 GET fallback，但仍只保留状态类别和长度桶。"""

        calls: list[str] = []

        def request_once(target, method, timeout_sec):
            calls.append(method)
            if method == "HEAD":
                return PROBE.HttpObservation(
                    method="HEAD",
                    status_code=405,
                    elapsed_ms=90,
                    content_length=None,
                    tls_handshake_observed=True,
                    certificate_valid_for_host=True,
                )
            return PROBE.HttpObservation(
                method="GET",
                status_code=206,
                elapsed_ms=120,
                content_length=1,
                tls_handshake_observed=True,
                certificate_valid_for_host=True,
            )

        artifact = PROBE.build_probe_artifact(
            fake_target(),
            "env_override",
            generated_at="2026-07-13T05:13:01Z",
            request_once=request_once,
        )

        self.assertEqual(["HEAD", "GET"], calls)
        self.assertEqual("GET", artifact["http_method"])
        self.assertTrue(artifact["head_rejected_get_fallback_attempted"])
        self.assertEqual("2xx", artifact["http_status_class"])
        self.assertEqual("1b_1kb", artifact["content_length_bucket"])
        self.assertFalse(PROBE.redaction_violations(artifact))

    def test_http_non_success_class_fails_closed_but_preserves_tls_evidence(self) -> None:
        """4xx/5xx 不能声明成功，但 TLS/cert 观察结果仍可作为窄 blocker。"""

        def request_once(target, method, timeout_sec):
            return PROBE.HttpObservation(
                method=method,
                status_code=404,
                elapsed_ms=260,
                content_length=512,
                tls_handshake_observed=True,
                certificate_valid_for_host=True,
            )

        artifact = PROBE.build_probe_artifact(
            fake_target(),
            "env_override",
            generated_at="2026-07-13T05:13:02Z",
            request_once=request_once,
        )

        self.assertEqual("blocked_http_status_not_success_class", artifact["cdn_tls_external_evidence_status"])
        self.assertTrue(artifact["probe_attempted"])
        self.assertTrue(artifact["external_request_attempted"])
        self.assertTrue(artifact["tls_handshake_observed"])
        self.assertTrue(artifact["certificate_valid_for_host"])
        self.assertEqual(["http_status_not_success_class"], artifact["blocked_reasons"])
        self.assertEqual("none", artifact["accepted_claim"])
        self.assertFalse(PROBE.redaction_violations(artifact))

    def test_tls_runtime_failure_is_sanitized_without_exception_text(self) -> None:
        """TLS/网络异常只能进入 reason code，不能把 traceback 或 URL 写入 artifact。"""

        def request_once(target, method, timeout_sec):
            raise PROBE.ProbeRuntimeError(
                "tls_failed",
                tls_handshake_observed=False,
                certificate_valid_for_host=False,
                elapsed_ms=70,
            )

        artifact = PROBE.build_probe_artifact(
            fake_target(),
            "env_override",
            generated_at="2026-07-13T05:13:03Z",
            request_once=request_once,
        )
        encoded = json.dumps(artifact, sort_keys=True)

        self.assertEqual("blocked_tls_failed", artifact["cdn_tls_external_evidence_status"])
        self.assertTrue(artifact["probe_attempted"])
        self.assertTrue(artifact["external_request_attempted"])
        self.assertFalse(artifact["tls_handshake_observed"])
        self.assertNotIn("https://", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertFalse(PROBE.redaction_violations(artifact))

    def test_unsafe_targets_fail_closed_before_network_io(self) -> None:
        """非 HTTPS、query、userinfo、localhost 和 secret marker 都不能发起外部请求。"""

        unsafe_targets = [
            "http://cdn.example.test/rober/",
            "https://cdn.example.test/rober/?token=abc",
            "https://user:pass@cdn.example.test/rober/",
            "https://localhost/rober/",
            "https://cdn.example.test/secret/rober/",
        ]
        for raw_target in unsafe_targets:
            with self.subTest(raw_target=raw_target):
                artifact = PROBE.build_probe_artifact(
                    raw_target,
                    "env_override",
                    generated_at="2026-07-13T05:13:04Z",
                    request_once=lambda target, method, timeout_sec: self.fail("network should not run"),
                )

                self.assertFalse(artifact["probe_attempted"])
                self.assertFalse(artifact["external_request_attempted"])
                self.assertTrue(artifact["blocked_reasons"])
                self.assertEqual("unavailable", artifact["target_host_hash_prefix"])
                self.assertFalse(artifact["delivery_success"])
                self.assertFalse(artifact["safe_to_control"])
                self.assertFalse(PROBE.redaction_violations(artifact))

    def test_main_writes_sanitized_json_artifact(self) -> None:
        """CLI 写出的 JSON artifact 仍必须通过 redaction gate 和 json.tool 级读取。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "summary.json"
            old_value = os.environ.get(PROBE.DEFAULT_ENV_VAR)
            os.environ[PROBE.DEFAULT_ENV_VAR] = "https://localhost/rober/"
            try:
                # CLI 本身会打印 sanitized JSON；单测只关心写文件结果，避免污染 unittest 输出。
                with redirect_stdout(io.StringIO()):
                    rc = PROBE.main(["--output", str(output), "--timeout-sec", "1"])
            finally:
                if old_value is None:
                    os.environ.pop(PROBE.DEFAULT_ENV_VAR, None)
                else:
                    os.environ[PROBE.DEFAULT_ENV_VAR] = old_value
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(PROBE.SCHEMA, payload["schema"])
        self.assertEqual("cdn_tls_external_evidence", payload["evidence_key"])
        self.assertIn("next_live_command", payload)
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(PROBE.redaction_violations(payload))


if __name__ == "__main__":
    unittest.main()
