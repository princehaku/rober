import json
from pathlib import Path
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[2]
# 测试从仓库源码直接导入，避免依赖开发机是否已经 pip install 本包。
sys.path.insert(0, str(REPO_ROOT / "cloud-relay" / "src"))
# remote relay 的主体还在 onboard behavior 包中，cloud-relay wrapper 负责重导出。
sys.path.insert(0, str(REPO_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"))

import ros2_trashbot_cloud_relay.remote_cloud_relay as relay


def _request_json(url, *, token=None, payload=None, method=None):
    # 测试只传递 bearer 占位值，不读取真实 .env，避免把生产凭证带入本地 smoke。
    headers = {"Content-Type": "application/json"}
    if token:
        # 这里显式拼出 Authorization，是为了验证 HTTP bearer gate 而不是绕过 handler。
        headers["Authorization"] = f"Bearer {token}"
    # GET 请求不带 body；POST 请求统一走 JSON object，贴近手机/机器人控制面。
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    # urllib 会在非 2xx 时抛 HTTPError，测试可直接断言 fail-closed 状态码。
    return json.loads(urllib.request.urlopen(request, timeout=5).read().decode("utf-8"))


class Objective5MockControlPlaneTest(unittest.TestCase):
    def test_commands_status_ack_and_env_bearer_are_mock_90_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # bearer 从环境变量注入，证明代码路径不依赖仓库内真实密钥或生产 .env 文件。
            previous = os.environ.get("TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN")
            os.environ["TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN"] = "o5-mock-token"
            token = os.environ["TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN"]
            # SQLite proof store 模拟控制面队列持久化，但仍不是 production DB/queue。
            server = relay.build_server("127.0.0.1", 0, f"{tmpdir}/remote.sqlite", token, state_backend="sqlite")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                # 未授权请求必须停在 bearer gate，不能因为 mock 模式放开控制面入口。
                command_url = f"{base_url}/robots/robot-o5/commands"
                command = {
                    "protocol_version": "trashbot.remote.v1",
                    "id": "cmd-o5-collect",
                    "type": "collect",
                    "expires_at": time.time() + 300.0,
                    "payload": {"target": "mock_trash_station", "source": "Objective 5 mock/software proof"},
                }
                with self.assertRaises(urllib.error.HTTPError) as exc:
                    _request_json(command_url, payload=command, method="POST")
                self.assertEqual(exc.exception.code, 401)

                # commands/status/ack 共用同一个本地 SQLite mock store，模拟 production queue 的 envelope。
                submitted = _request_json(command_url, token=token, payload=command, method="POST")
                # command id 会成为机器人 outbound polling 和 ACK 对账的幂等锚点。
                self.assertEqual(submitted["command"]["id"], "cmd-o5-collect")
                next_command = _request_json(
                    f"{base_url}/robots/robot-o5/commands/next?last_ack_id=",
                    token=token,
                )
                # next command 证明机器人只需主动轮询云端，不需要公网 inbound 直连小车。
                self.assertEqual(next_command["command"]["id"], "cmd-o5-collect")

                status = _request_json(
                    f"{base_url}/robots/robot-o5/status",
                    token=token,
                    payload={
                        "protocol_version": "trashbot.remote.v1",
                        "state": "delivering",
                        "updated_at": time.time(),
                        "diagnostics": {"transport": "mock_4g", "software_proof": True},
                    },
                    method="POST",
                )
                # status 写入只更新控制面状态，不触发 Nav2、底盘或真实投放动作。
                self.assertTrue(status["ok"])

                ack = _request_json(
                    f"{base_url}/robots/robot-o5/commands/cmd-o5-collect/ack",
                    token=token,
                    payload={
                        "protocol_version": "trashbot.remote.v1",
                        "state": "acked",
                        "updated_at": time.time(),
                        "result": {"envelope_processed": True, "delivery_success": False},
                    },
                    method="POST",
                )
                # ACK 语义固定为 envelope processed；测试刻意保留 delivery_success=false。
                self.assertEqual(ack["ack"]["state"], "acked")
                self.assertFalse(ack["ack"]["result"]["delivery_success"])

                # ACK 后 cursor 收口只证明 envelope 处理完成，不证明真实送达或真实 4G。
                after_ack = _request_json(
                    f"{base_url}/robots/robot-o5/commands/next?last_ack_id=cmd-o5-collect",
                    token=token,
                )
                self.assertIsNone(after_ack["command"])
                # readyz 只验证本地 proof service 可写和凭证 gate 存在，不代表公网 ready。
                ready = _request_json(f"{base_url}/readyz")
                self.assertTrue(ready["ok"])
            finally:
                # HTTP server 必须关闭，否则后续测试会留下线程和端口状态噪声。
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                if previous is None:
                    # 还原环境变量，避免一个测试的 bearer 占位影响其他 gate 断言。
                    os.environ.pop("TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", None)
                else:
                    os.environ["TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN"] = previous

    def test_mock_4g_db_queue_and_oss_cdn_degrade_without_real_material(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # mock 4G 中断使用本地 unreachable 等价故障，验证恢复后 envelope 可重放。
            network = relay.network_recovery_drill_payload(
                f"{tmpdir}/network.sqlite",
                state_backend="sqlite",
                robot_id="robot-o5",
            )
            self.assertEqual(network["overall_status"], "passed")
            # not_proven 必须保留真实 4G/SIM 缺口，避免 mock 网络恢复被误写成现场材料。
            self.assertIn("real_4g_sim", network["not_proven"])
            self.assertFalse(network["cursor_invariant"]["ack_is_delivery_success"])

            # mock DB/queue 只生成 phone-safe artifact，仍显式保留 production DB/queue 缺口。
            store_queue = relay.create_production_store_queue_artifact(
                f"{tmpdir}/production_store_queue.json",
                "robot-o5",
            )
            self.assertTrue(store_queue["ok"])
            # artifact 通过只说明 schema/checksum/摘要可消费，不说明生产数据库已连接。
            self.assertIn("production_db_or_queue", store_queue["not_proven"])

            # OSS/CDN manifest 只证明对象引用规则；live traffic 和真实上传继续 fail-closed。
            manifest = relay.create_oss_cdn_manifest_artifact(
                f"{tmpdir}/oss_cdn_manifest.json",
                "robot-o5",
                "task-o5",
                "2026-05-28",
            )
            self.assertTrue(manifest["ok"])
            # 对象引用可验证时也不能移除真实上传和 CDN 回源缺口。
            self.assertIn("real_oss_upload", manifest["not_proven"])
            self.assertIn("cdn_origin_fetch", manifest["not_proven"])

            # preflight 汇总多个 mock artifact 后仍应 blocked，因为真实外部材料未到位。
            preflight = relay.production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "o5-mock-token",
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT": f"{tmpdir}/production_store_queue.json",
                    "TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT": f"{tmpdir}/oss_cdn_manifest.json",
                }
            )
            # production_ready=false 是本测试的关键安全边界。
            self.assertFalse(preflight["production_ready"])
            # 这些 not_proven 项对应 O5 不允许被 mock 替代的真实材料。
            self.assertIn("real_https_tls", preflight["not_proven"])
            self.assertIn("real_4g_sim", preflight["not_proven"])
            self.assertIn("oss_cdn_live_probe_gate", preflight["not_proven"])
            self.assertIn("production_db_or_queue", preflight["not_proven"])

    def test_o5_readiness_health_is_bearer_gated_and_phone_safe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token = "o5-readiness-health-token"
            server = relay.build_server("127.0.0.1", 0, f"{tmpdir}/remote.sqlite", token, state_backend="sqlite")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            health_url = f"{base_url}/api/o5/readiness/health"
            try:
                # readiness health 是 support/phone/external probe 入口；缺 bearer 必须 fail closed。
                with self.assertRaises(urllib.error.HTTPError) as exc:
                    _request_json(health_url)
                self.assertEqual(exc.exception.code, 401)

                payload = _request_json(health_url, token=token)
                # schema/capability 固定，方便 phone/support 在不解析 preflight 全量细节时做稳定展示。
                self.assertEqual(payload["schema"], "trashbot.o5.readiness_health.v1")
                self.assertEqual(payload["capability"], "o5_readiness_live_health")
                self.assertEqual(payload["overall_status"], "blocked")

                # 这些字段是 O5 当前安全边界：只观测 readiness，不声明生产可控或真实送达。
                self.assertFalse(payload["production_ready"])
                self.assertFalse(payload["safe_to_control"])
                self.assertFalse(payload["sends_commands"])
                self.assertFalse(payload["robot_control_executed"])
                self.assertFalse(payload["delivery_success"])

                # readiness endpoint 复用 preflight 缺口口径，但只返回枚举和计数，不返回完整 artifact/details。
                self.assertGreater(payload["blocked_count"], 0)
                self.assertEqual(payload["blocked_count"], payload["status_counts"]["blocked"])
                self.assertIn("real_https_tls", payload["real_material_gaps"])
                self.assertIn("real_4g_sim", payload["real_material_gaps"])
                self.assertIn("production_db_or_queue", payload["real_material_gaps"])
                self.assertIn("external_https_tls_probe", payload["next_required_evidence"])
                self.assertTrue(payload["readiness_items"])

                encoded = json.dumps(payload, ensure_ascii=False)
                forbidden = [
                    token,
                    "Authorization",
                    "Bearer ",
                    "://",
                    "/cmd_vel",
                    "serial",
                    "UART",
                    "WAVE ROVER",
                    "checksum",
                    "TRASHBOT_REMOTE_CLOUD",
                    tmpdir,
                ]
                for marker in forbidden:
                    # 响应面向外部部署探测，不能泄露凭证、URL、本地路径、硬件或底层控制细节。
                    self.assertNotIn(marker, encoded)
            finally:
                # 关闭测试 server，避免 readiness 线程影响后续 unittest 进程退出。
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
