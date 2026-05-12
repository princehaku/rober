import json
import re
import unittest
from pathlib import Path


MOBILE_ROOT = Path(__file__).resolve().parent
WEB_ROOT = MOBILE_ROOT / "web"
FIXTURE = MOBILE_ROOT / "fixtures" / "mobile_web_status.fixture.json"


class MobileWebEntrypointTest(unittest.TestCase):
    def read(self, relative):
        return (WEB_ROOT / relative).read_text(encoding="utf-8")

    def test_static_shell_files_exist_and_reference_phone_safe_schema(self):
        index = self.read("index.html")
        app = self.read("app.js")
        manifest = json.loads(self.read("manifest.webmanifest"))

        for name in ("styles.css", "app.js", "offline.html", "service-worker.js"):
            self.assertTrue((WEB_ROOT / name).exists(), name)

        # 静态入口必须消费既有 phone-safe schema，而不是新增机器人状态枚举。
        self.assertIn("/api/status", app)
        self.assertIn("/api/diagnostics", app)
        self.assertIn("phone_readiness", app)
        self.assertIn("command_safety", app)
        self.assertIn("phone_offline_resume_readiness", app)
        self.assertIn("phone_task_flow_readiness", app)
        self.assertIn("phone_support_bundle", app)
        self.assertIn("voice_prompt_readiness", app)
        self.assertEqual(manifest["evidence_boundary"], "software_proof_docker_mobile_web_entrypoint_gate")
        self.assertIn("manifest.webmanifest", index)

    def test_primary_actions_fail_closed_and_use_command_safety(self):
        app = self.read("app.js")
        index = self.read("index.html")

        # 按钮 HTML 默认 disabled；JS 只有 command_safety 与旧权限都允许时才启用。
        for button_id in ("startButton", "confirmButton", "cancelButton"):
            self.assertRegex(index, rf'id="{button_id}"[^>]*disabled')
        self.assertIn("actionGate.enabled === true && permitted === true", app)
        self.assertIn("command_safety", app)
        self.assertIn("can_collect", app)
        self.assertIn("can_confirm_dropoff", app)
        self.assertIn("can_cancel", app)
        self.assertIn("latestStartGate.startEnabled", app)
        self.assertIn("缺少 command_safety", app)
        self.assertIn("旧权限 can_collect", app)
        self.assertIn("缺少后端 phone-safe 目标垃圾站", app)
        self.assertIn("请先显式确认垃圾已放入", app)
        self.assertIn("renderOfflineFailure", app)
        self.assertIn("button.disabled = true", app)

    def test_start_confirmation_panel_and_payload_are_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("destinationSummary", index)
        self.assertIn("trashLoadedCheckbox", index)
        self.assertIn("不是自动载荷检测", index)
        self.assertIn("trashbot.mobile_task_start_confirmation.v1", app)
        self.assertIn('source: "mobile_web"', app)
        self.assertIn("trash_loaded_confirmed: true", app)
        self.assertIn("target: latestStartGate.destination", app)
        self.assertIn("client_timestamp", app)
        self.assertIn("client_reference", app)
        self.assertIn("software_proof_docker_mobile_task_start_confirmation_gate", app)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn('"Content-Type": "application/json"', app)
        self.assertNotRegex(app, r"fetchJson\\(ENDPOINTS\\[actionName\\], \\{ method: \"POST\" \\}\\)")

        for compatible_field in (
            "destination_summary",
            "destination_confirmed",
            "readiness?.destination",
            "status?.destination",
        ):
            self.assertIn(compatible_field, app)

    def test_service_worker_bypasses_dynamic_control_routes(self):
        service_worker = self.read("service-worker.js")

        # service worker 只能缓存静态壳；API、机器人、命令、ACK 和非 GET 必须直连 no-store。
        self.assertIn('request.method !== "GET"', service_worker)
        for marker in (
            'path.startsWith("/api/")',
            'path.startsWith("/robots/")',
            'path.includes("/commands")',
            'path.includes("/ack")',
            'path.includes("/diagnostics")',
            'path === "/api/collect"',
            'path === "/api/dropoff/confirm"',
            'path === "/api/cancel"',
            'cache: "no-store"',
        ):
            self.assertIn(marker, service_worker)
        shell_urls = re.search(r"SHELL_URLS = \[(.*?)\];", service_worker, re.S)
        self.assertIsNotNone(shell_urls)
        self.assertNotIn("/api/status", shell_urls.group(1))

    def test_offline_shell_keeps_primary_actions_disabled(self):
        offline = self.read("offline.html")

        self.assertIn("不会发送、缓存、排队或重放", offline)
        self.assertEqual(offline.count("disabled"), 3)
        self.assertIn("software_proof_docker_mobile_web_entrypoint_gate", offline)

    def test_fixture_is_explicit_and_phone_safe(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        encoded = json.dumps(payload, ensure_ascii=False).lower()

        self.assertTrue(payload["fixture"])
        self.assertIn("not live robot state", payload["fixture_note"])
        self.assertEqual(payload["phone_readiness"]["schema"], "trashbot.phone_readiness.v1")
        self.assertIn("trashbot.command_safety.v1", encoded)
        self.assertIn("destination_summary", encoded)
        self.assertIn("destination_confirmed", encoded)
        self.assertIn("ack 只表示指令受理或处理中，不代表送达成功", encoded)
        for forbidden in (
            "authorization",
            "oss ak",
            "oss sk",
            "database url",
            "queue url",
            "/cmd_vel",
            "baudrate",
            "wave rover",
            "checksum",
            "artifact",
            "serial device",
            "local path",
        ):
            self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
