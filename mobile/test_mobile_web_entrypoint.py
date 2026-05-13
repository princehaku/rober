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
        self.assertIn("phone_cloud_readiness_summary", app)
        self.assertIn("mobile_cloud_readiness_summary", app)
        self.assertIn("cloud_readiness", app)
        self.assertIn("mobile_device_acceptance_readiness", app)
        self.assertIn("phone_device_acceptance_readiness", app)
        self.assertIn("mobile_browser_acceptance_readiness", app)
        self.assertIn("operation_log", app)
        self.assertIn("phone_operation_log", app)
        self.assertIn("mobile_action_receipt", app)
        self.assertIn("phone_action_feedback", app)
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
        self.assertIn("cloudSummaryAllowsPrimaryActions", app)
        self.assertIn("mobileDeviceAcceptanceAllowsPrimaryActions", app)
        self.assertIn("云中转摘要未放行主操作", app)
        self.assertIn("手机验收准备未放行主操作", app)
        self.assertIn("缺少 command_safety", app)
        self.assertIn("旧权限 can_collect", app)
        self.assertIn("缺少后端 phone-safe 目标垃圾站", app)
        self.assertIn("请先显式确认垃圾已放入", app)
        self.assertIn("renderOfflineFailure", app)
        self.assertIn("button.disabled = true", app)

    def test_operation_log_panel_is_visible_and_read_only(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("operationLogTitle", index)
        self.assertIn("操作日志", index)
        self.assertIn("operationLogList", index)
        self.assertIn("operationSupportEntry", index)
        self.assertIn("不会打开控制动作", index)
        self.assertIn("operationLogFromStatus", app)
        self.assertIn("deriveOperationLogEntries", app)
        self.assertIn("phone_readiness", app)
        self.assertIn("commandSafetyFromReadiness", app)
        self.assertIn("phone_task_flow_readiness", app)
        self.assertIn("phone_offline_resume_readiness", app)
        self.assertIn("phone_support_bundle", app)
        self.assertIn("voice_prompt_readiness", app)
        self.assertNotRegex(app, r"operationLog.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_cloud_readiness_panel_is_visible_read_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("cloudReadinessTitle", index)
        self.assertIn("云中转状态", index)
        self.assertIn("cloudReadinessBadge", index)
        self.assertIn("cloudPreflightState", index)
        self.assertIn("cloudDbQueueState", index)
        self.assertIn("cloudProductionReady", index)
        self.assertIn("cloudAckSemantics", index)
        self.assertIn("software_proof_docker_mobile_cloud_readiness_summary_gate", index)
        self.assertIn("cloudReadinessSummaryFromStatus", app)
        self.assertIn("phone_cloud_readiness_summary", app)
        self.assertIn("mobile_cloud_readiness_summary", app)
        self.assertIn("readiness?.cloud_readiness", app)
        self.assertIn("production_ready=false / 未证明", app)
        self.assertIn("ACK_PROCESSING_COPY", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("cloudAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"cloudReadiness.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_device_acceptance_panel_is_visible_read_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileDeviceAcceptanceTitle", index)
        self.assertIn("手机验收准备", index)
        self.assertIn("mobileDeviceViewportTouch", index)
        self.assertIn("mobileDevicePwaOffline", index)
        self.assertIn("mobileDeviceDiagnosticsCloud", index)
        self.assertIn("mobileDeviceProductionApp", index)
        self.assertIn("software_proof_docker_mobile_device_acceptance_readiness_gate", index)
        self.assertIn("mobileDeviceAcceptanceReadinessFromStatus", app)
        self.assertIn("mobile_device_acceptance_readiness", app)
        self.assertIn("phone_device_acceptance_readiness", app)
        self.assertIn("mobile_browser_acceptance_readiness", app)
        self.assertIn("production_app_ready: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("production_app_ready === true", app)
        self.assertIn("safe_to_control === true", app)
        self.assertIn("真实 PWA install prompt", app)
        self.assertIn("ACK_PROCESSING_COPY", app)
        self.assertNotRegex(app, r"mobileDeviceAcceptance.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_action_feedback_panel_consumes_receipt_and_fail_closed_copy(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("actionFeedbackTitle", index)
        self.assertIn("动作回执", index)
        self.assertIn("actionFeedbackClientReference", index)
        self.assertIn("actionFeedbackAck", index)
        self.assertIn("software_proof_docker_mobile_action_feedback_gate", index)
        self.assertIn("actionFeedbackFromStatus", app)
        self.assertIn("normalizeActionFeedback", app)
        self.assertIn("mobile_action_receipt", app)
        self.assertIn("phone_action_feedback", app)
        self.assertIn("local_submit_failed", app)
        self.assertIn("ACK 只代表 accepted/processing evidence", app)
        self.assertIn("不是完成证明", app)
        self.assertNotIn("投放已完成", app)
        self.assertNotIn("取消已完成", app)
        self.assertNotIn("送达已成功", app)

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

    def test_confirm_and_cancel_use_generic_mobile_action_confirmation_payload(self):
        app = self.read("app.js")

        self.assertIn("buildGenericActionPayload", app)
        self.assertIn('schema: "trashbot.mobile_action_confirmation.v1"', app)
        self.assertIn("schema_version: 1", app)
        self.assertIn('source: "mobile_web"', app)
        self.assertIn("action: actionName", app)
        self.assertIn("user_confirmed: true", app)
        self.assertIn("client_reference: clientReference", app)
        self.assertIn("client_timestamp", app)
        self.assertIn("safe_phone_copy", app)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("ACTION_FEEDBACK_BOUNDARY", app)
        self.assertIn("buildActionPayload(actionName, clientReference)", app)
        self.assertIn("requestOptionsForAction(actionName, payload)", app)

        generic_builder = re.search(
            r"function buildGenericActionPayload\(actionName, clientReference\) \{(.*?)\n\}",
            app,
            re.S,
        )
        self.assertIsNotNone(generic_builder)
        generic_source = generic_builder.group(1).lower()
        for forbidden in (
            "destination:",
            "target:",
            "ros",
            "/cmd_vel",
            "serial",
            "baudrate",
            "wave rover",
            "authorization",
            "token",
            "oss",
            "checksum",
            "artifact",
        ):
            self.assertNotIn(forbidden, generic_source)

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
        self.assertEqual(payload["operation_log"]["schema"], "trashbot.phone_operation_log.v1")
        self.assertEqual(
            payload["operation_log"]["evidence_boundary"],
            "software_proof_docker_mobile_operation_log_gate",
        )
        self.assertEqual(payload["mobile_action_receipt"]["schema"], "trashbot.mobile_action_receipt.v1")
        self.assertEqual(
            payload["mobile_action_receipt"]["evidence_boundary"],
            "software_proof_docker_mobile_action_feedback_gate",
        )
        self.assertEqual(payload["phone_action_feedback"]["schema"], "trashbot.phone_action_feedback.v1")
        self.assertEqual(payload["phone_cloud_readiness_summary"]["schema"], "trashbot.phone_cloud_readiness_summary.v1")
        self.assertEqual(payload["phone_cloud_readiness_summary"]["production_ready"], False)
        self.assertEqual(payload["phone_cloud_readiness_summary"]["overall_status"], "blocked")
        self.assertEqual(
            payload["phone_cloud_readiness_summary"]["evidence_boundary"],
            "software_proof_docker_mobile_cloud_readiness_summary_gate",
        )
        self.assertEqual(
            payload["phone_cloud_readiness_summary"]["source_evidence_boundary"],
            "software_proof_docker_cloud_db_queue_config_gate",
        )
        self.assertEqual(payload["phone_readiness"]["cloud_readiness"]["primary_actions_enabled"], False)
        self.assertEqual(
            payload["mobile_device_acceptance_readiness"]["schema"],
            "trashbot.mobile_device_acceptance_readiness.v1",
        )
        self.assertEqual(payload["mobile_device_acceptance_readiness"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_device_acceptance_readiness"]["primary_actions_enabled"], False)
        self.assertEqual(payload["mobile_device_acceptance_readiness"]["production_app_ready"], False)
        self.assertEqual(payload["mobile_device_acceptance_readiness"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_device_acceptance_readiness"]["evidence_boundary"],
            "software_proof_docker_mobile_device_acceptance_readiness_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_device_acceptance_readiness"]["evidence_boundary"],
            "software_proof_docker_mobile_device_acceptance_readiness_gate",
        )
        self.assertIn("trashbot.command_safety.v1", encoded)
        self.assertIn("trashbot.phone_cloud_readiness_summary.v1", encoded)
        self.assertIn("trashbot.mobile_device_acceptance_readiness.v1", encoded)
        self.assertIn("blocked-by-design", encoded)
        self.assertIn("真实 pwa install prompt", encoded)
        self.assertIn("software_proof_docker_mobile_device_acceptance_readiness_gate", encoded)
        self.assertIn("software_proof_docker_cloud_db_queue_config_gate", encoded)
        self.assertIn("production_ready", encoded)
        self.assertIn("真实云就绪", encoded)
        self.assertIn("trashbot.mobile_action_confirmation.v1", encoded)
        self.assertIn("最近状态：等待用户确认垃圾已放入", encoded)
        self.assertIn("勾选已放入垃圾后再尝试开始送达", encoded)
        self.assertIn("accepted/processing evidence", encoded)
        self.assertIn("client_reference", encoded)
        self.assertIn("提交失败", encoded)
        self.assertIn("支持交接：可复制脱敏摘要给支持人员", encoded)
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
