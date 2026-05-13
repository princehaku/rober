import json
import re
import unittest
from pathlib import Path


MOBILE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MOBILE_ROOT.parent
WEB_ROOT = MOBILE_ROOT / "web"
FIXTURE = MOBILE_ROOT / "fixtures" / "mobile_web_status.fixture.json"
BROWSER_GATE = REPO_ROOT / "pc-tools" / "evidence" / "phone_browser_acceptance_gate.py"
CLOUD_PWA_GATE = REPO_ROOT / "pc-tools" / "evidence" / "cloud_hosted_pwa_installability_gate.py"


class MobileWebEntrypointTest(unittest.TestCase):
    def read(self, relative):
        return (WEB_ROOT / relative).read_text(encoding="utf-8")

    def test_browser_acceptance_gate_targets_current_mobile_web_pwa(self):
        script = BROWSER_GATE.read_text(encoding="utf-8")

        # gate 必须验证当前 dependency-free PWA，不能回退到旧 operator gateway 或旧 DOM id。
        self.assertIn('MOBILE_WEB_ROOT = REPO_ROOT / "mobile" / "web"', script)
        self.assertIn('MOBILE_FIXTURE = REPO_ROOT / "mobile" / "fixtures" / "mobile_web_status.fixture.json"', script)
        self.assertIn('EVIDENCE_BOUNDARY = "software_proof_docker_mobile_web_browser_proof_gate"', script)
        self.assertIn('"/api/status"', script)
        self.assertIn('"/api/diagnostics"', script)
        self.assertIn('"startButton"', script)
        self.assertIn('"confirmButton"', script)
        self.assertIn('"cancelButton"', script)
        self.assertIn('"mobileBrowserSafeCopy"', script)
        self.assertIn('"copyAcceptanceBundleButton"', script)
        self.assertIn("PHONE_BROWSER_CHROME", script)
        self.assertIn("--browser", script)
        self.assertNotIn("ros2_trashbot_behavior", script)
        self.assertNotIn("operator_gateway_http", script)
        self.assertNotIn("collectButton", script)

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
        self.assertIn("mobile_device_evidence_capture", app)
        self.assertIn("mobile_device_evidence_capture_summary", app)
        self.assertIn("mobile_device_evidence_package", app)
        self.assertIn("mobile_browser_acceptance_bundle", app)
        self.assertIn("phone_browser_acceptance_bundle", app)
        self.assertIn("mobile_acceptance_evidence_bundle", app)
        self.assertIn("operation_log", app)
        self.assertIn("phone_operation_log", app)
        self.assertIn("mobile_action_receipt", app)
        self.assertIn("phone_action_feedback", app)
        self.assertIn("mobile_primary_journey_gate", json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8"))))
        self.assertIn("mobile_recovery_decision_gate", app)
        self.assertIn("mobile_recovery_decision_summary", app)
        self.assertIn("mobile_recovery_decision_gate", json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8"))))
        self.assertIn("primaryJourneyTitle", index)
        self.assertEqual(manifest["evidence_boundary"], "software_proof_docker_mobile_web_entrypoint_gate")
        self.assertEqual(
            manifest["installability_evidence_boundary"],
            "software_proof_docker_cloud_hosted_mobile_pwa_installability_gate",
        )
        self.assertIn("manifest.webmanifest", index)

    def test_cloud_hosted_pwa_installability_gate_uses_relay_and_browser(self):
        script = CLOUD_PWA_GATE.read_text(encoding="utf-8")

        # 新 gate 必须启动 cloud-relay hosted URL，不能退化成只读本地静态文件。
        self.assertIn("EVIDENCE_BOUNDARY = \"software_proof_docker_cloud_hosted_mobile_pwa_installability_gate\"", script)
        self.assertIn("TRASHBOT_REMOTE_CLOUD_MOBILE_WEB_ROOT", script)
        self.assertIn("ros2_trashbot_cloud_relay.remote_cloud_relay", script)
        self.assertIn("validate_manifest", script)
        self.assertIn("validate_service_worker", script)
        self.assertIn("validate_offline_shell", script)
        self.assertIn("run_browser_acceptance", script)
        self.assertIn("manifest.webmanifest", script)
        self.assertIn("installability_evidence_boundary", script)
        self.assertIn("request.method !== \"GET\"", script)
        self.assertIn("/api/collect", script)
        self.assertIn("/robots/trashbot-001/commands", script)
        self.assertIn("VIEWPORTS = ((390, 844), (768, 900))", script)
        self.assertIn("mobile_web_browser_*.*", script)
        self.assertIn("cloud_hosted_pwa_installability_summary.json", script)
        self.assertIn("真实 PWA install prompt", script)

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
        self.assertIn("mobileBrowserAcceptanceBundleAllowsPrimaryActions", app)
        self.assertIn("operationLogReadyForPrimaryJourney", app)
        self.assertIn("actionFeedbackReadyForPrimaryJourney", app)
        self.assertIn("journeyStateBlocksStart", app)
        self.assertIn("cloud readiness 未显式放行主操作", app)
        self.assertIn("device readiness 未显式放行主操作", app)
        self.assertIn("browser acceptance bundle 未显式放行主操作", app)
        self.assertIn("缺少 operation log / phone_operation_log", app)
        self.assertIn("缺少 action feedback / receipt 摘要", app)
        self.assertIn("云中转摘要未放行主操作", app)
        self.assertIn("手机验收准备未放行主操作", app)
        self.assertIn("浏览器验收包未放行主操作", app)
        self.assertIn("缺少 command_safety", app)
        self.assertIn("旧权限 can_collect", app)
        self.assertIn("缺少后端 phone-safe 目标垃圾站", app)
        self.assertIn("请先显式确认垃圾已放入", app)
        self.assertIn("renderOfflineFailure", app)
        self.assertIn("button.disabled = true", app)

    def test_primary_journey_summary_renders_three_step_gate(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("primaryJourneyTitle", index)
        self.assertIn("三步主路径", index)
        self.assertIn("目标垃圾站", index)
        self.assertIn("已放入垃圾确认", index)
        self.assertIn("发车安全 gate", index)
        self.assertIn("primaryJourneySteps", index)
        self.assertIn("primaryJourneyBadge", index)
        self.assertIn("software_proof_docker_mobile_primary_journey_gate", index)
        self.assertIn("PRIMARY_JOURNEY_BOUNDARY", app)
        self.assertIn("renderPrimaryJourney", app)
        self.assertIn("Start Delivery 保持关闭", app)
        self.assertIn("accepted/processing evidence", app)
        self.assertIn("不是自动载荷检测", index)
        self.assertNotIn("自动检测到垃圾", index)

    def test_recovery_decision_panel_is_visible_read_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("recoveryDecisionTitle", index)
        self.assertIn("恢复决策", index)
        self.assertIn("recoveryDecisionState", index)
        self.assertIn("recoveryDecisionNextAction", index)
        self.assertIn("recoveryDecisionBlockingReason", index)
        self.assertIn("recoveryDecisionSupportEntry", index)
        self.assertIn("recoveryDecisionAck", index)
        self.assertIn("software_proof_docker_mobile_recovery_decision_gate", index)
        self.assertIn("RECOVERY_DECISION_BOUNDARY", app)
        self.assertIn("recoveryDecisionFromStatus", app)
        self.assertIn("mobile_recovery_decision_gate", app)
        self.assertIn("mobile_recovery_decision_summary", app)
        self.assertIn("derivedRecoveryDecision", app)
        self.assertIn("blocked-by-design", app)
        self.assertIn("pending_ack", app)
        self.assertIn("offline_status_stale", app)
        self.assertIn("manual_takeover_required", app)
        self.assertIn("local_submit_failed", app)
        self.assertIn("missing_primary_journey_readiness", app)
        self.assertIn("missing_support_handoff", app)
        self.assertIn("ACK 只代表 accepted/processing evidence", app)
        self.assertIn("notProvenList", app)
        self.assertIn("UNSAFE_RECOVERY_TEXT", app)
        self.assertIn("safe_to_control: false", app)
        self.assertNotRegex(app, r"recoveryDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_recovery_decision_filters_success_words_and_keeps_ack_narrow(self):
        app = self.read("app.js")

        self.assertIn("delivery success", app)
        self.assertIn("dropoff success", app)
        self.assertIn("cancel completed", app)
        self.assertIn("送达已?成功", app)
        self.assertIn("投放已?完成", app)
        self.assertIn("取消已?完成", app)
        self.assertIn("return fallback", app)
        self.assertIn("不证明真实验收或机器人完成", app)
        self.assertIn("不代表送达成功、投放完成或取消已落地", app)
        self.assertNotIn("送达已成功", self.read("index.html"))
        self.assertNotIn("投放已完成", self.read("index.html"))
        self.assertNotIn("取消已完成", self.read("index.html"))

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

    def test_mobile_browser_acceptance_bundle_is_visible_copyable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileBrowserAcceptanceTitle", index)
        self.assertIn("浏览器验收包", index)
        self.assertIn("copyAcceptanceBundleButton", index)
        self.assertIn("mobileBrowserSafeCopy", index)
        self.assertIn("mobileBrowserNotProven", index)
        self.assertIn("software_proof_docker_mobile_browser_acceptance_bundle_gate", index)
        self.assertIn("trashbot.mobile_browser_acceptance_bundle.v1", app)
        self.assertIn("mobileBrowserAcceptanceBundleFromStatus", app)
        self.assertIn("mobile_browser_acceptance_bundle", app)
        self.assertIn("phone_browser_acceptance_bundle", app)
        self.assertIn("mobile_acceptance_evidence_bundle", app)
        self.assertIn("bundleCopyPayload", app)
        self.assertIn("UNSAFE_BUNDLE_TEXT", app)
        self.assertIn("safe_to_control === true", app)
        self.assertIn("production_app_ready === true", app)
        self.assertIn("blocked-by-design", app)
        self.assertIn("ACK_PROCESSING_COPY", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotRegex(app, r"mobileBrowserAcceptance.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_device_evidence_capture_is_visible_copyable_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileDeviceEvidenceTitle", index)
        self.assertIn("手机设备证据采集", index)
        self.assertIn("copyDeviceEvidencePackageButton", index)
        self.assertIn("mobileDeviceEvidenceSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_device_evidence_capture_gate", index)
        self.assertIn("trashbot.mobile_device_evidence_capture.v1", app)
        self.assertIn("trashbot.mobile_device_evidence_capture_summary.v1", app)
        self.assertIn("trashbot.mobile_device_evidence_package.v1", app)
        self.assertIn("mobileDeviceEvidencePackageFromStatus", app)
        self.assertIn("mobile_device_evidence_capture", app)
        self.assertIn("mobile_device_evidence_capture_summary", app)
        self.assertIn("mobile_device_evidence_package", app)
        self.assertIn("collectLocalDeviceEvidence", app)
        self.assertIn("currentDisplayMode", app)
        self.assertIn("deviceEvidencePackageCopyPayload", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertIn("no_store_required", app)
        self.assertIn("真实手机/browser、production app 和真实 PWA install prompt 仍未证明", app)
        self.assertNotRegex(app, r"mobileDeviceEvidence.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

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
        self.assertIn("software_proof_docker_mobile_primary_journey_gate", app)
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
        self.assertIn("TERMINAL_ACTION_BOUNDARY", app)
        self.assertIn("buildActionPayload(actionName, clientReference)", app)
        self.assertIn("requestOptionsForAction(actionName, payload)", app)
        self.assertIn("software_proof_docker_mobile_terminal_action_confirmation_gate", app)

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

    def test_terminal_action_confirmation_gate_is_visible_and_two_step(self):
        app = self.read("app.js")
        index = self.read("index.html")

        # Confirm/Cancel 首次点击只能打开本地确认 panel；真正 POST 被确认按钮二次触发。
        self.assertIn("terminalActionTitle", index)
        self.assertIn("终端动作二次确认", index)
        self.assertIn("terminalActionConfirmButton", index)
        self.assertIn("terminalActionBackButton", index)
        self.assertIn("terminalActionClientReference", index)
        self.assertIn("terminalActionNotProven", index)
        self.assertIn("software_proof_docker_mobile_terminal_action_confirmation_gate", index)
        self.assertIn("pendingTerminalAction", app)
        self.assertIn("terminalActionGateFromStatus", app)
        self.assertIn("openTerminalActionConfirmation(actionName)", app)
        self.assertIn("closeTerminalActionPanel", app)
        self.assertIn("postAction(actionName, clientReference)", app)
        self.assertIn("终端动作首次点击只进入确认，不提交 Confirm Dropoff / Cancel endpoint", index)
        self.assertRegex(
            app,
            r'if \(\["confirm_dropoff", "cancel"\]\.includes\(actionName\)\) \{\s+openTerminalActionConfirmation\(actionName\);\s+return;\s+\}',
        )
        self.assertRegex(
            app,
            r'terminalActionBackButton"\)\.addEventListener\("click", closeTerminalActionPanel\)',
        )
        self.assertRegex(
            app,
            re.compile(
                r'terminalActionConfirmButton"\)\.addEventListener\("click", async \(\) => \{.*?await postAction\(actionName, clientReference\);',
                re.S,
            ),
        )

    def test_terminal_action_gate_copy_filters_success_words_and_fails_closed(self):
        app = self.read("app.js")

        # 终端动作 gate 必须覆盖缺 command_safety、action disabled、pending ACK、离线、人工接管和 blocked。
        self.assertIn("UNSAFE_TERMINAL_TEXT", app)
        self.assertIn("safeTerminalActionText", app)
        self.assertIn("delivery success", app)
        self.assertIn("dropoff success", app)
        self.assertIn("cancel completed", app)
        self.assertIn("缺少 command_safety，终端动作确认 fail closed", app)
        self.assertIn("action disabled", app)
        self.assertIn("存在 pending ACK / accepted-processing 回执", app)
        self.assertIn("状态 offline/stale/unreachable", app)
        self.assertIn("当前需要人工接管或支持处理", app)
        self.assertIn("当前 blocked state 未解除", app)
        self.assertIn("cloud readiness 未显式放行终端动作", app)
        self.assertIn("device readiness 未显式放行终端动作", app)
        self.assertIn("browser acceptance bundle 未显式放行终端动作", app)
        self.assertIn("终端动作二次确认 gate fail closed", app)
        self.assertIn("这不是 delivery success、dropoff success 或 cancel completed", app)
        self.assertNotIn("投放已完成", self.read("index.html"))
        self.assertNotIn("取消已完成", self.read("index.html"))

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
            payload["mobile_device_evidence_capture"]["schema"],
            "trashbot.mobile_device_evidence_capture.v1",
        )
        self.assertEqual(
            payload["mobile_device_evidence_capture"]["evidence_boundary"],
            "software_proof_docker_mobile_device_evidence_capture_gate",
        )
        self.assertEqual(
            payload["mobile_device_evidence_capture_summary"]["schema"],
            "trashbot.mobile_device_evidence_capture_summary.v1",
        )
        self.assertEqual(
            payload["mobile_device_evidence_package"]["schema"],
            "trashbot.mobile_device_evidence_package.v1",
        )
        self.assertEqual(
            payload["mobile_device_evidence_package"]["evidence_boundary"],
            "software_proof_docker_mobile_device_evidence_capture_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_device_acceptance_readiness"]["evidence_boundary"],
            "software_proof_docker_mobile_device_acceptance_readiness_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_device_evidence_capture"]["evidence_boundary"],
            "software_proof_docker_mobile_device_evidence_capture_gate",
        )
        self.assertEqual(
            payload["mobile_browser_acceptance_bundle"]["schema"],
            "trashbot.mobile_browser_acceptance_bundle.v1",
        )
        self.assertEqual(payload["mobile_browser_acceptance_bundle"]["schema_version"], 1)
        self.assertEqual(payload["mobile_browser_acceptance_bundle"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_browser_acceptance_bundle"]["production_app_ready"], False)
        self.assertEqual(payload["mobile_browser_acceptance_bundle"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_browser_acceptance_bundle"]["evidence_boundary"],
            "software_proof_docker_mobile_browser_acceptance_bundle_gate",
        )
        self.assertEqual(payload["mobile_primary_journey_gate"]["schema"], "trashbot.mobile_primary_journey_gate.v1")
        self.assertEqual(payload["mobile_primary_journey_gate"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_primary_journey_gate"]["safe_to_start"], False)
        self.assertEqual(
            payload["mobile_primary_journey_gate"]["evidence_boundary"],
            "software_proof_docker_mobile_primary_journey_gate",
        )
        self.assertEqual(
            payload["mobile_primary_journey_summary"]["schema"],
            "trashbot.mobile_primary_journey_summary.v1",
        )
        self.assertEqual(len(payload["mobile_primary_journey_summary"]["steps"]), 3)
        self.assertEqual(payload["mobile_recovery_decision_gate"]["schema"], "trashbot.mobile_recovery_decision_gate.v1")
        self.assertEqual(payload["mobile_recovery_decision_gate"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_recovery_decision_gate"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_recovery_decision_gate"]["recovery_state"], "local_submit_failed")
        self.assertEqual(
            payload["mobile_recovery_decision_gate"]["evidence_boundary"],
            "software_proof_docker_mobile_recovery_decision_gate",
        )
        self.assertEqual(
            payload["mobile_recovery_decision_summary"]["schema"],
            "trashbot.mobile_recovery_decision_summary.v1",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_recovery_decision_gate"]["evidence_boundary"],
            "software_proof_docker_mobile_recovery_decision_gate",
        )
        self.assertEqual(
            payload["mobile_terminal_action_confirmation_gate"]["schema"],
            "trashbot.mobile_terminal_action_confirmation_gate.v1",
        )
        self.assertEqual(payload["mobile_terminal_action_confirmation_gate"]["overall_status"], "blocked")
        self.assertEqual(
            payload["mobile_terminal_action_confirmation_gate"]["evidence_boundary"],
            "software_proof_docker_mobile_terminal_action_confirmation_gate",
        )
        self.assertEqual(
            payload["mobile_terminal_action_confirmation_summary"]["schema"],
            "trashbot.mobile_terminal_action_confirmation_summary.v1",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_terminal_action_confirmation_gate"]["evidence_boundary"],
            "software_proof_docker_mobile_terminal_action_confirmation_gate",
        )
        for field in (
            "viewport",
            "touch_target",
            "pwa_install_prompt",
            "offline_shell",
            "diagnostics",
            "cloud_gate",
            "action_gate",
            "ack_semantics",
            "client_timestamp",
            "safe_phone_copy",
            "recovery_hint",
            "not_proven",
        ):
            self.assertIn(field, payload["mobile_browser_acceptance_bundle"])
        self.assertEqual(
            payload["phone_readiness"]["mobile_browser_acceptance_bundle"]["evidence_boundary"],
            "software_proof_docker_mobile_browser_acceptance_bundle_gate",
        )
        self.assertIn("trashbot.command_safety.v1", encoded)
        self.assertIn("trashbot.phone_cloud_readiness_summary.v1", encoded)
        self.assertIn("trashbot.mobile_device_acceptance_readiness.v1", encoded)
        self.assertIn("trashbot.mobile_device_evidence_capture.v1", encoded)
        self.assertIn("trashbot.mobile_device_evidence_capture_summary.v1", encoded)
        self.assertIn("trashbot.mobile_device_evidence_package.v1", encoded)
        self.assertIn("trashbot.mobile_browser_acceptance_bundle.v1", encoded)
        self.assertIn("blocked-by-design", encoded)
        self.assertIn("真实 pwa install prompt", encoded)
        self.assertIn("software_proof_docker_mobile_device_acceptance_readiness_gate", encoded)
        self.assertIn("software_proof_docker_mobile_device_evidence_capture_gate", encoded)
        self.assertIn("software_proof_docker_mobile_browser_acceptance_bundle_gate", encoded)
        self.assertIn("software_proof_docker_mobile_primary_journey_gate", encoded)
        self.assertIn("trashbot.mobile_recovery_decision_gate.v1", encoded)
        self.assertIn("trashbot.mobile_recovery_decision_summary.v1", encoded)
        self.assertIn("software_proof_docker_mobile_recovery_decision_gate", encoded)
        self.assertIn("trashbot.mobile_terminal_action_confirmation_gate.v1", encoded)
        self.assertIn("trashbot.mobile_terminal_action_confirmation_summary.v1", encoded)
        self.assertIn("software_proof_docker_mobile_terminal_action_confirmation_gate", encoded)
        self.assertIn("首次点击不提交", encoded)
        self.assertIn("local_submit_failed", encoded)
        self.assertIn("刷新状态后再决定是否重试", encoded)
        self.assertIn("真实取消完成", encoded)
        self.assertIn("trashbot.mobile_primary_journey_gate.v1", encoded)
        self.assertIn("trashbot.mobile_primary_journey_summary.v1", encoded)
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
