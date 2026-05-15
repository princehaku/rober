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
        self.assertIn(
            'EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate"',
            script,
        )
        self.assertIn(
            'COMPATIBLE_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate"',
            script,
        )
        self.assertIn(
            'REFRESH_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate"',
            script,
        )
        self.assertIn(
            'LEGACY_ARTIFACT_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_web_browser_proof_gate"',
            script,
        )
        self.assertIn('"/api/status"', script)
        self.assertIn('"/api/diagnostics"', script)
        self.assertIn('"startButton"', script)
        self.assertIn('"confirmButton"', script)
        self.assertIn('"cancelButton"', script)
        self.assertIn('"primaryJourneyTitle"', script)
        self.assertIn('"recoveryDecisionTitle"', script)
        self.assertIn('"terminalActionTitle"', script)
        self.assertIn('"mobileDeviceEvidenceTitle"', script)
        self.assertIn('"mobileDeviceHandoffTitle"', script)
        self.assertIn('"mobilePwaInstallPromptTitle"', script)
        self.assertIn('"mobileRealDeviceRetestRequestTitle"', script)
        self.assertIn('"mobileRealDeviceRetestRequestSafeCopy"', script)
        self.assertIn('"copyRealDeviceRetestRequestButton"', script)
        self.assertIn('"mobileRealDeviceFieldTrialTitle"', script)
        self.assertIn('"mobileRealDeviceFieldTrialReviewTitle"', script)
        self.assertIn('"mobileRealDeviceFieldTrialRunbookExecutionTitle"', script)
        self.assertIn('"mobileRealDeviceFieldTrialEvidenceRecordTitle"', script)
        self.assertIn('"mobileRealDeviceFieldTrialEvidenceVerdictTitle"', script)
        self.assertIn('"mobileRealDeviceFieldTrialRetestExecutionTitle"', script)
        self.assertIn('"copyRealDeviceFieldTrialPackageButton"', script)
        self.assertIn('"copyRealDeviceFieldTrialReviewButton"', script)
        self.assertIn('"copyRealDeviceFieldTrialRunbookExecutionButton"', script)
        self.assertIn('"copyRealDeviceFieldTrialEvidenceRecordButton"', script)
        self.assertIn('"copyRealDeviceFieldTrialEvidenceVerdictButton"', script)
        self.assertIn('"copyRealDeviceFieldTrialRetestExecutionButton"', script)
        self.assertIn('"mobileBrowserSafeCopy"', script)
        self.assertIn('"copyAcceptanceBundleButton"', script)
        self.assertIn('"copyDeviceEvidencePackageButton"', script)
        self.assertIn('"copyDeviceHandoffPackageButton"', script)
        self.assertIn('"copyPwaInstallPromptPackageButton"', script)
        self.assertIn("CURRENT_PANEL_EXPECTATIONS", script)
        self.assertIn("CURRENT_BOUNDARY_EXPECTATIONS", script)
        self.assertIn("terminal_action_confirmation_visible", script)
        self.assertIn("pwa_install_prompt_evidence_visible", script)
        self.assertIn("device_handoff_session_visible", script)
        self.assertIn("device_evidence_capture_visible", script)
        self.assertIn("real_device_retest_request_visible", script)
        self.assertIn("real_device_retest_request_copyable", script)
        self.assertIn("field_trial_package_visible", script)
        self.assertIn("field_trial_review_visible", script)
        self.assertIn("field_trial_runbook_execution_visible", script)
        self.assertIn("field_trial_evidence_record_visible", script)
        self.assertIn("field_trial_evidence_verdict_visible", script)
        self.assertIn("field_trial_retest_execution_visible", script)
        self.assertIn("current_panels_status", script)
        self.assertIn("current_boundaries_status", script)
        self.assertIn("PHONE_BROWSER_CHROME", script)
        self.assertIn("--browser", script)
        self.assertNotIn("ros2_trashbot_behavior", script)
        self.assertNotIn("operator_gateway_http", script)
        self.assertNotIn("collectButton", script)

    def test_current_browser_gate_field_trial_boundary_keeps_compatibility(self):
        script = BROWSER_GATE.read_text(encoding="utf-8")

        # field-trial browser proof 使用本 sprint artifact 名，同时保留旧边界字段方便 closeout 核对。
        self.assertIn("mobile_current_pwa_field_trial_browser_{width}x{height}.png", script)
        self.assertIn("mobile_current_pwa_field_trial_browser_{width}x{height}.json", script)
        self.assertIn("mobile_current_pwa_field_trial_browser_acceptance_summary.json", script)
        self.assertIn("compatible_evidence_boundary", script)
        self.assertIn("refresh_evidence_boundary", script)
        self.assertIn("legacy_artifact_evidence_boundary", script)
        self.assertIn("boundary_compatibility", script)
        self.assertIn("software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate", script)
        self.assertIn("software_proof_docker_mobile_current_pwa_retest_browser_proof_gate", script)
        self.assertIn("software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate", script)
        self.assertIn("software_proof_docker_mobile_web_browser_proof_gate", script)

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
        self.assertIn("mobile_device_handoff_session", app)
        self.assertIn("mobile_device_handoff_session_summary", app)
        self.assertIn("mobile_device_handoff_package", app)
        self.assertIn("mobile_pwa_install_prompt_evidence", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_summary", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_package", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture_summary", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture_copy", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export_summary", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export_copy", app)
        self.assertIn("mobile_real_device_evidence_intake", app)
        self.assertIn("mobile_real_device_evidence_intake_summary", app)
        self.assertIn("mobile_real_device_evidence_package", app)
        self.assertIn("mobile_real_device_acceptance_decision", app)
        self.assertIn("mobile_real_device_acceptance_decision_summary", app)
        self.assertIn("mobile_real_device_acceptance_decision_package", app)
        self.assertIn("mobile_real_device_review_handoff", app)
        self.assertIn("mobile_real_device_review_handoff_summary", app)
        self.assertIn("mobile_real_device_review_handoff_package", app)
        self.assertIn("mobile_real_device_review_execution", app)
        self.assertIn("mobile_real_device_review_execution_summary", app)
        self.assertIn("mobile_real_device_review_execution_package", app)
        self.assertIn("mobile_real_device_retest_request", app)
        self.assertIn("mobile_real_device_retest_request_summary", app)
        self.assertIn("mobile_real_device_retest_request_package", app)
        self.assertIn("mobile_real_device_field_trial_package", app)
        self.assertIn("mobile_real_device_field_trial_package_summary", app)
        self.assertIn("mobile_real_device_field_trial_package_copy", app)
        self.assertIn("mobile_real_device_field_trial_review", app)
        self.assertIn("mobile_real_device_field_trial_review_summary", app)
        self.assertIn("mobile_real_device_field_trial_review_copy", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution_summary", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution_copy", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_summary", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_copy", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_archive", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict_summary", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict_copy", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution_summary", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution_copy", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session_summary", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session_copy", app)
        self.assertIn("mobile_current_pwa_field_trial_browser_proof", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionTitle", index)
        self.assertIn("route_task_completion_signal", app)
        self.assertIn("route_task_completion_signal_summary", app)
        self.assertIn("routeTaskCompletionSignalTitle", index)
        self.assertIn("route_task_field_run_console", app)
        self.assertIn("route_task_field_run_console_summary", app)
        self.assertIn("routeTaskFieldRunConsoleTitle", index)
        self.assertIn("route_task_field_run_evidence_kit", app)
        self.assertIn("route_task_field_run_evidence_kit_summary", app)
        self.assertIn("routeTaskFieldRunEvidenceKitTitle", index)
        self.assertIn("route_task_field_run_material_bundle", app)
        self.assertIn("route_task_field_run_material_bundle_summary", app)
        self.assertIn("routeTaskFieldRunMaterialBundleTitle", index)
        self.assertIn("route_task_field_run_material_validation", app)
        self.assertIn("route_task_field_run_material_validation_summary", app)
        self.assertIn("routeTaskFieldRunMaterialValidationTitle", index)
        self.assertIn("elevator_field_run_material_validation", app)
        self.assertIn("elevator_field_run_material_validation_summary", app)
        self.assertIn("elevatorFieldRunMaterialValidationTitle", app)
        self.assertIn("elevator_field_run_review", app)
        self.assertIn("elevator_field_run_review_summary", app)
        self.assertIn("elevatorFieldRunReviewTitle", app)
        self.assertIn("elevator_assist", app)
        self.assertIn("elevator_assist_summary", app)
        self.assertIn("phone_elevator_assist", app)
        self.assertIn("software_proof_docker_elevator_assist_default_mainline_gate", app)
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

    def test_route_task_completion_signal_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")

        # completion signal 只能消费 phone-safe summary，不能把完成信号升级成真实交付成功。
        self.assertIn("routeTaskCompletionSignalTitle", index)
        self.assertIn("路线任务完成信号", index)
        self.assertIn("routeTaskCompletionSignalVerdict", index)
        self.assertIn("routeTaskCompletionSignalEvidenceRef", index)
        self.assertIn("routeTaskCompletionSignalDropoff", index)
        self.assertIn("routeTaskCompletionSignalCancel", index)
        self.assertIn("routeTaskCompletionSignalFailureRecovery", index)
        self.assertIn("routeTaskCompletionSignalNextSteps", index)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", index)
        self.assertIn("software_proof_docker_route_task_completion_signal_gate", index)
        self.assertIn("routeTaskCompletionSignalCandidate", app)
        self.assertIn("routeTaskCompletionSignalFromStatus", app)
        self.assertIn("route_task_completion_signal", app)
        self.assertIn("route_task_completion_signal_summary", app)
        self.assertIn("diagnosticsSummary.route_task_completion_signal", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_completion_signal", app)
        self.assertIn("dropoff_completion", app)
        self.assertIn("cancel_completion", app)
        self.assertIn("failure_reason", app)
        self.assertIn("recovery_reason", app)
        self.assertIn("completion_verdict", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("UNSAFE_ROUTE_TASK_COMPLETION_TEXT", app)
        self.assertIn("complete bundle", app)
        self.assertIn("Objective 5 external proof", app)
        self.assertNotRegex(app, r"routeTaskCompletion.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"routeTaskCompletion.*fetchJson\(ENDPOINTS\.diagnostics")

    def test_route_task_field_run_console_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")

        # field-run console 只消费 phone-safe summary，不能读取 raw artifact 或改变动作 gating。
        self.assertIn("routeTaskFieldRunConsoleTitle", index)
        self.assertIn("路线现场运行准备", index)
        self.assertIn("routeTaskFieldRunConsoleVerdict", index)
        self.assertIn("routeTaskFieldRunConsoleEvidenceRef", index)
        self.assertIn("routeTaskFieldRunConsolePlan", index)
        self.assertIn("routeTaskFieldRunConsoleChecklist", index)
        self.assertIn("routeTaskFieldRunConsoleMaterialStatus", index)
        self.assertIn("routeTaskFieldRunConsoleNextSteps", index)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", index)
        self.assertIn("software_proof_docker_route_task_field_run_console_gate", index)
        self.assertIn("routeTaskFieldRunConsoleCandidate", app)
        self.assertIn("routeTaskFieldRunConsoleFromStatus", app)
        self.assertIn("route_task_field_run_console", app)
        self.assertIn("route_task_field_run_console_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_run_console", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_field_run_console", app)
        self.assertIn("field_run_plan", app)
        self.assertIn("capture_checklist", app)
        self.assertIn("dropoff_material_status", app)
        self.assertIn("cancel_material_status", app)
        self.assertIn("console_verdict", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("UNSAFE_FIELD_RUN_CONSOLE_TEXT", app)
        self.assertIn("Objective 5 external proof", app)
        self.assertNotRegex(app, r"routeTaskFieldRunConsole.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"routeTaskFieldRunConsole.*fetchJson\(ENDPOINTS\.diagnostics")

    def test_route_task_field_run_evidence_kit_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")
        fixture_text = json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8")), ensure_ascii=False)

        # evidence kit 只消费 phone-safe 摘要，不能展示原始材料、路径、校验值或控制话题。
        self.assertIn("routeTaskFieldRunEvidenceKitTitle", index)
        self.assertIn("路线现场证据包", index)
        self.assertIn("routeTaskFieldRunEvidenceKitVerdict", index)
        self.assertIn("routeTaskFieldRunEvidenceKitEvidenceRef", index)
        self.assertIn("routeTaskFieldRunEvidenceKitManifest", index)
        self.assertIn("routeTaskFieldRunEvidenceKitTemplates", index)
        self.assertIn("routeTaskFieldRunEvidenceKitCommands", index)
        self.assertIn("routeTaskFieldRunEvidenceKitMissing", index)
        self.assertIn("routeTaskFieldRunEvidenceKitHandoff", index)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", index)
        self.assertIn("software_proof_docker_route_task_field_run_evidence_kit_gate", index)
        self.assertIn("routeTaskFieldRunEvidenceKitCandidate", app)
        self.assertIn("routeTaskFieldRunEvidenceKitFromStatus", app)
        self.assertIn("route_task_field_run_evidence_kit", app)
        self.assertIn("route_task_field_run_evidence_kit_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_run_evidence_kit", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_field_run_evidence_kit", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_run_evidence_kit", app)
        self.assertIn("material_directory_manifest", app)
        self.assertIn("capture_templates", app)
        self.assertIn("commands_to_run", app)
        self.assertIn("commands_to_rerun", app)
        self.assertIn("operator_handoff", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("UNSAFE_FIELD_RUN_EVIDENCE_KIT_TEXT", app)
        self.assertIn("route_task_field_run_evidence_kit_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_evidence_kit_fixture_20260515_0001", fixture_text)
        self.assertNotRegex(app, r"routeTaskFieldRunEvidenceKit.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"routeTaskFieldRunEvidenceKit.*fetchJson\(ENDPOINTS\.diagnostics")

    def test_route_task_field_run_material_bundle_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")
        fixture_text = json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8")), ensure_ascii=False)

        # material bundle 只消费 phone-safe 摘要，不能展示 raw artifact、路径、token 或控制话题。
        self.assertIn("routeTaskFieldRunMaterialBundleTitle", index)
        self.assertIn("路线现场材料包", index)
        self.assertIn("routeTaskFieldRunMaterialBundleStatus", index)
        self.assertIn("routeTaskFieldRunMaterialBundleEvidenceRef", index)
        self.assertIn("routeTaskFieldRunMaterialBundleTemplates", index)
        self.assertIn("routeTaskFieldRunMaterialBundleMissing", index)
        self.assertIn("routeTaskFieldRunMaterialBundleNextSteps", index)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", index)
        self.assertIn("software_proof_docker_route_task_field_run_material_bundle_gate", index)
        self.assertIn("routeTaskFieldRunMaterialBundleCandidate", app)
        self.assertIn("routeTaskFieldRunMaterialBundleFromStatus", app)
        self.assertIn("route_task_field_run_material_bundle", app)
        self.assertIn("route_task_field_run_material_bundle_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_run_material_bundle", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_field_run_material_bundle", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_run_material_bundle", app)
        self.assertIn("template_files", app)
        self.assertIn("missing_materials", app)
        self.assertIn("operator_next_steps", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("UNSAFE_FIELD_RUN_MATERIAL_BUNDLE_TEXT", app)
        self.assertIn("route_task_field_run_material_bundle_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_material_bundle_fixture_20260515_0001", fixture_text)
        self.assertNotRegex(app, r"routeTaskFieldRunMaterialBundle.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"routeTaskFieldRunMaterialBundle.*fetchJson\(ENDPOINTS\.diagnostics")

    def test_route_task_field_run_material_validation_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")
        fixture_text = json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8")), ensure_ascii=False)

        # material validation 只消费 phone-safe 摘要，不能展示 raw validation artifact 或改变动作 gating。
        self.assertIn("routeTaskFieldRunMaterialValidationTitle", index)
        self.assertIn("路线材料校验", index)
        self.assertIn("routeTaskFieldRunMaterialValidationStatus", index)
        self.assertIn("routeTaskFieldRunMaterialValidationEvidenceRef", index)
        self.assertIn("routeTaskFieldRunMaterialValidationMissing", index)
        self.assertIn("routeTaskFieldRunMaterialValidationPlaceholders", index)
        self.assertIn("routeTaskFieldRunMaterialValidationMismatch", index)
        self.assertIn("routeTaskFieldRunMaterialValidationNextSteps", index)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", index)
        self.assertIn("software_proof_docker_route_task_field_run_material_validation_gate", index)
        self.assertIn("routeTaskFieldRunMaterialValidationCandidate", app)
        self.assertIn("routeTaskFieldRunMaterialValidationFromStatus", app)
        self.assertIn("route_task_field_run_material_validation", app)
        self.assertIn("route_task_field_run_material_validation_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_run_material_validation", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_field_run_material_validation", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_run_material_validation", app)
        self.assertIn("missing_materials", app)
        self.assertIn("placeholder_materials", app)
        self.assertIn("mismatch_materials", app)
        self.assertIn("operator_next_steps", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("UNSAFE_FIELD_RUN_MATERIAL_VALIDATION_TEXT", app)
        self.assertIn("route_task_field_run_material_validation_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_material_validation_fixture_20260515_0001", fixture_text)
        self.assertNotRegex(app, r"routeTaskFieldRunMaterialValidation.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"routeTaskFieldRunMaterialValidation.*fetchJson\(ENDPOINTS\.diagnostics")

    def test_elevator_assist_panel_is_read_only_dry_run_and_phone_safe(self):
        app = self.read("app.js")
        fixture_text = json.dumps(json.loads(FIXTURE.read_text(encoding="utf-8")), ensure_ascii=False)

        # 电梯辅助只解释后端摘要，不改 index 静态结构，不改变 Start/Confirm/Cancel gating。
        self.assertIn("ELEVATOR_ASSIST_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_ASSIST_TEXT", app)
        self.assertIn("safeElevatorAssistText", app)
        self.assertIn("elevatorAssistCandidate", app)
        self.assertIn("elevatorAssistFromStatus", app)
        self.assertIn("ensureElevatorAssistPanel", app)
        self.assertIn("renderElevatorAssist", app)
        self.assertIn("elevator_assist", app)
        self.assertIn("elevator_assist_summary", app)
        self.assertIn("phone_elevator_assist", app)
        self.assertIn("diagnosticsSummary.elevator_assist", app)
        self.assertIn("statusDiagnosticsSummary.elevator_assist_summary", app)
        self.assertIn("电梯辅助状态", app)
        self.assertIn("等待开门、进入电梯、请求人工按目标楼层、等待目标楼层、开门后驶出、继续送达", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("software_proof_docker_elevator_assist_default_mainline_gate", app)
        self.assertIn("真实电梯", app)
        self.assertIn("真实喇叭/TTS", app)
        self.assertIn("真实 Nav2/fixed-route", app)
        self.assertIn("HIL", app)
        self.assertIn("not_proven", app)
        self.assertNotRegex(app, r"elevatorAssist.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"elevatorAssist.*fetchJson\(ENDPOINTS\.diagnostics")

        self.assertIn("trashbot.elevator_assist_summary.v1", fixture_text)
        self.assertIn("default_dry_run_enabled", fixture_text)
        self.assertIn("requesting_floor_help", fixture_text)
        self.assertIn("waiting_target_floor", fixture_text)
        self.assertIn("disabled warning fixture", fixture_text)
        self.assertIn("未确认目标楼层或电梯未开门时需要人工接管", fixture_text)
        self.assertIn("software_proof_docker_elevator_assist_default_mainline_gate", fixture_text)
        self.assertIn("不证明真实电梯", fixture_text)
        self.assertIn("真实 Nav2/fixed-route", fixture_text)
        elevator_fixture_text = json.dumps(
            {
                "top_level": json.loads(FIXTURE.read_text(encoding="utf-8"))["elevator_assist"],
                "readiness": json.loads(FIXTURE.read_text(encoding="utf-8"))["phone_readiness"]["elevator_assist_summary"],
            },
            ensure_ascii=False,
        ).lower()
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover",
            "authorization",
            "token",
            "delivery_success\": true",
        ):
            self.assertNotIn(forbidden, elevator_fixture_text)

    def test_elevator_field_run_material_validation_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)

        # 电梯材料校验只消费 Robot diagnostics/status 摘要，不新增任何控制动作路径。
        self.assertIn("ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_MATERIAL_VALIDATION_TEXT", app)
        self.assertIn("safeElevatorFieldMaterialValidationText", app)
        self.assertIn("elevatorFieldRunMaterialValidationCandidate", app)
        self.assertIn("elevatorFieldRunMaterialValidationFromStatus", app)
        self.assertIn("ensureElevatorFieldRunMaterialValidationPanel", app)
        self.assertIn("renderElevatorFieldRunMaterialValidation", app)
        self.assertIn("电梯现场材料校验", app)
        self.assertIn("elevator_field_run_material_validation", app)
        self.assertIn("elevator_field_run_material_validation_summary", app)
        self.assertIn("diagnosticsSummary.elevator_field_run_material_validation", app)
        self.assertIn("nestedDiagnosticsSummary.elevator_field_run_material_validation", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_run_material_validation_summary", app)
        self.assertIn("validation_status", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("missing_materials", app)
        self.assertIn("template_materials", app)
        self.assertIn("mismatch_materials", app)
        self.assertIn("operator_next_steps", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("software_proof_docker_elevator_field_material_validation_gate", app)
        self.assertIn("真实电梯门状态", app)
        self.assertIn("真实目标楼层确认", app)
        self.assertIn("Objective 5 external proof", app)
        self.assertNotRegex(app, r"elevatorFieldRunMaterialValidation.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"elevatorFieldRunMaterialValidation.*fetchJson\(ENDPOINTS\.diagnostics")

        self.assertIn("trashbot.elevator_field_run_material_validation.v1", fixture_text)
        self.assertIn("trashbot.elevator_field_run_material_validation_summary.v1", fixture_text)
        self.assertIn("elevator_field_run_material_validation_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_elevator_validation_fixture_20260515_0001", fixture_text)
        self.assertIn("status_diagnostics_elevator_validation_fixture_20260515_0001", fixture_text)
        self.assertEqual(
            fixture["elevator_field_run_material_validation"]["evidence_boundary"],
            "software_proof_docker_elevator_field_material_validation_gate",
        )
        self.assertEqual(
            fixture["phone_readiness"]["elevator_field_run_material_validation_summary"]["primary_actions_enabled"],
            False,
        )
        self.assertEqual(
            fixture["diagnostics"]["summary"]["elevator_field_run_material_validation_summary"]["delivery_success"],
            False,
        )
        elevator_fixture_text = json.dumps(
            {
                "top_level": fixture["elevator_field_run_material_validation"],
                "readiness": fixture["phone_readiness"]["elevator_field_run_material_validation_summary"],
                "diagnostics": fixture["diagnostics"]["summary"]["elevator_field_run_material_validation_summary"],
            },
            ensure_ascii=False,
        ).lower()
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover",
            "authorization",
            "token",
            "raw artifact",
            "delivery_success\": true",
        ):
            self.assertNotIn(forbidden, elevator_fixture_text)

    def test_elevator_field_run_review_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)

        # 电梯现场复核决策只展示 phone-safe 摘要，不读取 raw review，也不改变控制按钮 gating。
        self.assertIn("ELEVATOR_FIELD_RUN_REVIEW_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_REVIEW_TEXT", app)
        self.assertIn("safeElevatorFieldReviewText", app)
        self.assertIn("elevatorFieldRunReviewCandidate", app)
        self.assertIn("elevatorFieldRunReviewFromStatus", app)
        self.assertIn("ensureElevatorFieldRunReviewPanel", app)
        self.assertIn("renderElevatorFieldRunReview", app)
        self.assertIn("电梯现场复核决策", app)
        self.assertIn("elevator_field_run_review", app)
        self.assertIn("elevator_field_run_review_summary", app)
        self.assertIn("diagnosticsSummary.elevator_field_run_review", app)
        self.assertIn("nestedDiagnosticsSummary.elevator_field_run_review", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_run_review_summary", app)
        self.assertIn("review_decision", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("blocked_categories", app)
        self.assertIn("operator_next_steps", app)
        self.assertIn("commands_to_rerun", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("software_proof_docker_elevator_field_review_decision_gate", app)
        self.assertIn("真实电梯门状态", app)
        self.assertIn("Objective 5 external proof", app)
        self.assertNotRegex(app, r"elevatorFieldRunReview.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"elevatorFieldRunReview.*fetchJson\(ENDPOINTS\.diagnostics")

        self.assertIn("trashbot.elevator_field_run_review.v1", fixture_text)
        self.assertIn("trashbot.elevator_field_run_review_summary.v1", fixture_text)
        self.assertIn("elevator_field_run_review_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_elevator_review_fixture_20260515_0001", fixture_text)
        self.assertIn("status_diagnostics_elevator_review_fixture_20260515_0001", fixture_text)
        self.assertEqual(
            fixture["elevator_field_run_review"]["evidence_boundary"],
            "software_proof_docker_elevator_field_review_decision_gate",
        )
        self.assertEqual(
            fixture["phone_readiness"]["elevator_field_run_review_summary"]["primary_actions_enabled"],
            False,
        )
        self.assertEqual(
            fixture["diagnostics"]["summary"]["elevator_field_run_review_summary"]["delivery_success"],
            False,
        )
        elevator_review_fixture_text = json.dumps(
            {
                "top_level": fixture["elevator_field_run_review"],
                "readiness": fixture["phone_readiness"]["elevator_field_run_review_summary"],
                "diagnostics": fixture["diagnostics"]["summary"]["elevator_field_run_review_summary"],
            },
            ensure_ascii=False,
        ).lower()
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover",
            "authorization",
            "token",
            "raw artifact",
            "raw review",
            "delivery_success\": true",
        ):
            self.assertNotIn(forbidden, elevator_review_fixture_text)

    def test_elevator_field_run_execution_pack_panel_is_read_only_and_phone_safe(self):
        app = self.read("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)

        # 电梯演练执行包只展示 phone-safe 执行准备元数据，不新增任何 Start/Confirm/Cancel 路径。
        self.assertIn("ELEVATOR_FIELD_RUN_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeElevatorFieldExecutionPackText", app)
        self.assertIn("elevatorFieldRunExecutionPackCandidate", app)
        self.assertIn("elevatorFieldRunExecutionPackFromStatus", app)
        self.assertIn("ensureElevatorFieldRunExecutionPackPanel", app)
        self.assertIn("renderElevatorFieldRunExecutionPack", app)
        self.assertIn("电梯演练执行包", app)
        self.assertIn("elevator_field_run_execution_pack", app)
        self.assertIn("elevator_field_run_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.elevator_field_run_execution_pack", app)
        self.assertIn("nestedDiagnosticsSummary.elevator_field_run_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_run_execution_pack_summary", app)
        self.assertIn("execution_pack_verdict", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("controlled_rehearsal_manifest", app)
        self.assertIn("required_material_templates", app)
        self.assertIn("first_run_commands", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("operator_handoff", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("safe_to_control=false / delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("software_proof_docker_elevator_field_rehearsal_execution_pack_gate", app)
        self.assertIn("真实电梯门状态", app)
        self.assertIn("Objective 5 external proof", app)
        self.assertNotRegex(app, r"elevatorFieldRunExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"elevatorFieldRunExecutionPack.*fetchJson\(ENDPOINTS\.diagnostics")

        self.assertIn("trashbot.elevator_field_run_execution_pack.v1", fixture_text)
        self.assertIn("trashbot.elevator_field_run_execution_pack_summary.v1", fixture_text)
        self.assertIn("elevator_field_run_execution_pack_fixture_20260515_0001", fixture_text)
        self.assertIn("phone_readiness_elevator_execution_pack_fixture_20260515_0001", fixture_text)
        self.assertIn("status_diagnostics_elevator_execution_pack_fixture_20260515_0001", fixture_text)
        self.assertEqual(
            fixture["elevator_field_run_execution_pack"]["evidence_boundary"],
            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate",
        )
        self.assertEqual(
            fixture["phone_readiness"]["elevator_field_run_execution_pack_summary"]["primary_actions_enabled"],
            False,
        )
        self.assertEqual(
            fixture["diagnostics"]["summary"]["elevator_field_run_execution_pack_summary"]["delivery_success"],
            False,
        )
        self.assertEqual(
            fixture["elevator_field_run_execution_pack"]["safe_to_control"],
            False,
        )
        elevator_execution_pack_fixture_text = json.dumps(
            {
                "top_level": fixture["elevator_field_run_execution_pack"],
                "readiness": fixture["phone_readiness"]["elevator_field_run_execution_pack_summary"],
                "diagnostics": fixture["diagnostics"]["summary"]["elevator_field_run_execution_pack_summary"],
            },
            ensure_ascii=False,
        ).lower()
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover",
            "authorization",
            "token",
            "raw artifact",
            "raw execution pack",
            "delivery_success\": true",
        ):
            self.assertNotIn(forbidden, elevator_execution_pack_fixture_text)

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

    def test_mobile_device_handoff_session_is_visible_copyable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileDeviceHandoffTitle", index)
        self.assertIn("真实手机验收交接会话", index)
        self.assertIn("mobileDeviceHandoffEntry", index)
        self.assertIn("mobileDeviceHandoffSessionId", index)
        self.assertIn("mobileDeviceHandoffClientReference", index)
        self.assertIn("mobileDeviceHandoffChecklist", index)
        self.assertIn("copyDeviceHandoffPackageButton", index)
        self.assertIn("mobileDeviceHandoffSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_device_handoff_session_gate", index)
        self.assertIn("trashbot.mobile_device_handoff_session.v1", app)
        self.assertIn("trashbot.mobile_device_handoff_package.v1", app)
        self.assertIn("mobileDeviceHandoffSessionFromStatus", app)
        self.assertIn("mobileDeviceHandoffSessionAllowsPrimaryActions", app)
        self.assertIn("mobile_device_handoff_session", app)
        self.assertIn("mobile_device_handoff_session_summary", app)
        self.assertIn("mobile_device_handoff_package", app)
        self.assertIn("deviceHandoffPackageCopyPayload", app)
        self.assertIn("safeEntryUrlSummary", app)
        self.assertIn("observation_checklist", app)
        self.assertIn("evidence_capture_reference", app)
        self.assertIn("mobile device handoff session 未显式放行主操作", app)
        self.assertIn("mobile device handoff session 未显式放行终端动作", app)
        self.assertIn("真实手机验收交接会话未放行主操作", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertIn("真实设备验收通过", app)
        self.assertNotRegex(app, r"mobileDeviceHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_pwa_install_prompt_evidence_is_visible_copyable_and_not_control_grant(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobilePwaInstallPromptTitle", index)
        self.assertIn("PWA 安装提示导出", index)
        self.assertIn("mobilePwaInstallPromptCapture", index)
        self.assertIn("mobilePwaInstallPromptOutcome", index)
        self.assertIn("mobilePwaInstallPromptDisplay", index)
        self.assertIn("mobilePwaInstallPromptShell", index)
        self.assertIn("mobilePwaInstallPromptControl", index)
        self.assertIn("copyPwaInstallPromptPackageButton", index)
        self.assertIn("downloadPwaInstallPromptPackageButton", index)
        self.assertIn("mobilePwaInstallPromptSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_pwa_install_prompt_evidence_gate", app)
        self.assertIn("software_proof_docker_mobile_pwa_install_prompt_event_capture_gate", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_summary.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_package.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_event_capture.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_event_capture_summary.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_event_capture_copy.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_export.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1", app)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1", app)
        self.assertIn("mobilePwaInstallPromptEvidenceFromStatus", app)
        self.assertIn("mobilePwaInstallPromptEventCaptureFromStatus", app)
        self.assertIn("mobilePwaInstallPromptEvidenceExportFromStatus", app)
        self.assertIn("mobile_pwa_install_prompt_evidence", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_summary", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_package", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture_summary", app)
        self.assertIn("mobile_pwa_install_prompt_event_capture_copy", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export_summary", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export_copy", app)
        self.assertIn("pwaInstallPromptPackageCopyPayload", app)
        self.assertIn("pwaInstallPromptEventCaptureCopyPayload", app)
        self.assertIn("pwaInstallPromptEvidenceExportCopyPayload", app)
        self.assertIn("downloadJsonPackage", app)
        self.assertIn("mobile_pwa_install_prompt_evidence_export_copy.json", app)
        self.assertIn("beforeinstallprompt", app)
        self.assertIn("appinstalled", app)
        self.assertIn("userChoice", app)
        self.assertIn("deferredPwaInstallPromptEvent", app)
        self.assertIn("完整 UA", app)
        self.assertIn("raw event", app)
        self.assertIn("linked_handoff_session", app)
        self.assertIn("linked_device_evidence_capture", app)
        self.assertIn("linked_browser_acceptance_bundle", app)
        self.assertIn("真实 PWA install prompt 通过", app)
        self.assertIn("安装提示导出只用于验收复现，不是 Start、Confirm 或 Cancel 放行条件", index)
        self.assertIn("software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate", index)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobilePwaInstallPromptAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobilePwaInstallPrompt.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_evidence_intake_is_importable_redacted_and_not_control_grant(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceEvidenceTitle", index)
        self.assertIn("真实设备验收材料", index)
        self.assertIn("mobileRealDeviceEvidenceImport", index)
        self.assertIn("importRealDeviceEvidenceButton", index)
        self.assertIn("generateRealDeviceEvidenceButton", index)
        self.assertIn("copyRealDeviceEvidencePackageButton", index)
        self.assertIn("mobileRealDeviceEvidenceSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_evidence_intake_gate", index)
        self.assertIn("trashbot.mobile_real_device_evidence_intake.v1", app)
        self.assertIn("trashbot.mobile_real_device_evidence_intake_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_evidence_package.v1", app)
        self.assertIn("mobileRealDeviceEvidencePackageFromStatus", app)
        self.assertIn("mobileRealDeviceEvidenceIntakeCandidate", app)
        self.assertIn("mobile_real_device_evidence_intake", app)
        self.assertIn("mobile_real_device_evidence_intake_summary", app)
        self.assertIn("mobile_real_device_evidence_package", app)
        self.assertIn("realDeviceEvidencePackageCopyPayload", app)
        self.assertIn("UNSAFE_REAL_DEVICE_TEXT", app)
        self.assertIn("redaction_status", app)
        self.assertIn("raw robot response", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("本 gate 不启用 Start、Confirm 或 Cancel", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceEvidenceAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceEvidence.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_acceptance_decision_is_phone_safe_and_not_control_grant(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceAcceptanceDecisionTitle", index)
        self.assertIn("真实设备验收决策", index)
        self.assertIn("copyRealDeviceAcceptanceDecisionButton", index)
        self.assertIn("mobileRealDeviceAcceptanceDecisionSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_acceptance_decision_gate", index)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision.v1", app)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision_package.v1", app)
        self.assertIn("mobileRealDeviceAcceptanceDecisionCandidate", app)
        self.assertIn("mobileRealDeviceAcceptanceDecisionFromStatus", app)
        self.assertIn("realDeviceAcceptanceDecisionPackageCopyPayload", app)
        self.assertIn("mobile_real_device_acceptance_decision", app)
        self.assertIn("mobile_real_device_acceptance_decision_summary", app)
        self.assertIn("mobile_real_device_acceptance_decision_package", app)
        self.assertIn("accepted_for_review", app)
        self.assertIn("blocked_missing_evidence", app)
        self.assertIn("rejected_unsafe_or_unredacted", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("source_evidence_boundary", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("accepted_for_review 只表示可人工复核", index)
        self.assertNotIn("mobileRealDeviceAcceptanceDecisionAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceAcceptanceDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_review_handoff_is_copyable_review_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceReviewHandoffTitle", index)
        self.assertIn("真实设备评审交接", index)
        self.assertIn("copyRealDeviceReviewHandoffButton", index)
        self.assertIn("mobileRealDeviceReviewHandoffSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_review_handoff_gate", index)
        self.assertIn("trashbot.mobile_real_device_review_handoff.v1", app)
        self.assertIn("trashbot.mobile_real_device_review_handoff_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_review_handoff_package.v1", app)
        self.assertIn("mobileRealDeviceReviewHandoffCandidate", app)
        self.assertIn("mobileRealDeviceReviewHandoffFromStatus", app)
        self.assertIn("realDeviceReviewHandoffPackageCopyPayload", app)
        self.assertIn("mobile_real_device_review_handoff", app)
        self.assertIn("mobile_real_device_review_handoff_summary", app)
        self.assertIn("mobile_real_device_review_handoff_package", app)
        self.assertIn("reviewer checklist", app)
        self.assertIn("review owner", app)
        self.assertIn("decision status", app)
        self.assertIn("evidence blocker", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("source_evidence_boundary", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("not_proven", app)
        self.assertIn("ACK 仍不是 delivery success", app)
        self.assertIn("mobile real device review handoff 未显式放行主操作", app)
        self.assertIn("mobile real device review handoff 未显式放行终端动作", app)
        self.assertIn("真实设备验收通过、真实 PWA install prompt、O5 外部 proof、HIL 或 delivery success", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotRegex(app, r"mobileRealDeviceReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_review_execution_is_copyable_execution_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceReviewExecutionTitle", index)
        self.assertIn("真实设备评审执行", index)
        self.assertIn("copyRealDeviceReviewExecutionButton", index)
        self.assertIn("mobileRealDeviceReviewExecutionSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_review_execution_gate", index)
        self.assertIn("trashbot.mobile_real_device_review_execution.v1", app)
        self.assertIn("trashbot.mobile_real_device_review_execution_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_review_execution_package.v1", app)
        self.assertIn("mobileRealDeviceReviewExecutionCandidate", app)
        self.assertIn("mobileRealDeviceReviewExecutionFromStatus", app)
        self.assertIn("realDeviceReviewExecutionPackageCopyPayload", app)
        self.assertIn("mobile_real_device_review_execution", app)
        self.assertIn("mobile_real_device_review_execution_summary", app)
        self.assertIn("mobile_real_device_review_execution_package", app)
        self.assertIn("review execution checklist", app)
        self.assertIn("review_result", app)
        self.assertIn("evidence_items_readiness", app)
        self.assertIn("operator_notes", app)
        self.assertIn("reviewer_notes", app)
        self.assertIn("blocked_reason", app)
        self.assertIn("next_evidence_request", app)
        self.assertIn("const nextEvidenceRequest", app)
        self.assertIn("nextEvidenceRequest.length ? nextEvidenceRequest", app)
        self.assertNotIn("next_evidence_request: (nextEvidence.length", app)
        self.assertIn("source_evidence_boundary", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("mobile real device review execution 未显式放行主操作", app)
        self.assertIn("mobile real device review execution 未显式放行终端动作", app)
        self.assertIn("review execution package 只表示人工评审执行记录", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotRegex(app, r"mobileRealDeviceReviewExecution.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_retest_request_is_copyable_request_only_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceRetestRequestTitle", index)
        self.assertIn("真实设备复测请求", index)
        self.assertIn("copyRealDeviceRetestRequestButton", index)
        self.assertIn("mobileRealDeviceRetestRequestSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_retest_request_gate", index)
        self.assertIn("trashbot.mobile_real_device_retest_request.v1", app)
        self.assertIn("trashbot.mobile_real_device_retest_request_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_retest_request_package.v1", app)
        self.assertIn("mobileRealDeviceRetestRequestCandidate", app)
        self.assertIn("mobileRealDeviceRetestRequestFromStatus", app)
        self.assertIn("realDeviceRetestRequestPackageCopyPayload", app)
        self.assertIn("mobile_real_device_retest_request", app)
        self.assertIn("mobile_real_device_retest_request_summary", app)
        self.assertIn("mobile_real_device_retest_request_package", app)
        self.assertIn("retest checklist", app)
        self.assertIn("missing evidence", app)
        self.assertIn("owner", app)
        self.assertIn("next_action", app)
        self.assertIn("blocked_reason", app)
        self.assertIn("rejection_reason", app)
        self.assertIn("source_evidence_boundary", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("mobile real device retest request 未显式放行主操作", app)
        self.assertIn("mobile real device retest request 未显式放行终端动作", app)
        self.assertIn("retest request package 只表示下一轮真实设备复测材料请求", app)
        self.assertIn("Objective 5 外部材料", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotRegex(app, r"mobileRealDeviceRetestRequest.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_package_is_whitelist_copy_only(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialTitle", index)
        self.assertIn("真实设备现场试跑包", index)
        self.assertIn("generateRealDeviceFieldTrialButton", index)
        self.assertIn("copyRealDeviceFieldTrialPackageButton", index)
        self.assertIn("mobileRealDeviceFieldTrialSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_package_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_package.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_package_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_package_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialPackageFromStatus", app)
        self.assertIn("realDeviceFieldTrialPackageCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_package", app)
        self.assertIn("mobile_real_device_field_trial_package_summary", app)
        self.assertIn("mobile_real_device_field_trial_package_copy", app)
        self.assertIn("viewport_css_width", app)
        self.assertIn("device_pixel_ratio", app)
        self.assertIn("orientation", app)
        self.assertIn("touch_capability", app)
        self.assertIn("display_mode", app)
        self.assertIn("manifest_link_present", app)
        self.assertIn("service_worker_registration_hint", app)
        self.assertIn("offline_shell_hint", app)
        self.assertIn("entry_url_summary", app)
        self.assertIn("device_type", app)
        self.assertIn("os_browser", app)
        self.assertIn("production_app_observed", app)
        self.assertIn("pwa_install_prompt_observed", app)
        self.assertIn("offline_reload_observed", app)
        self.assertIn("touch_target_issue", app)
        self.assertIn("visual_issue", app)
        self.assertIn("operator_note", app)
        self.assertIn("support_note", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe 字段", index)
        self.assertIn("本轮是 Docker/local mobile software proof", app)
        self.assertIn("Start Delivery、Confirm Dropoff、Cancel 继续由既有 gates 控制", index)
        self.assertNotIn("mobileRealDeviceFieldTrialAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrial.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_review_is_copyable_review_only_and_phone_safe(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialReviewTitle", index)
        self.assertIn("现场试跑证据复核", index)
        self.assertIn("copyRealDeviceFieldTrialReviewButton", index)
        self.assertIn("mobileRealDeviceFieldTrialReviewSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_review_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_review.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_review_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_review_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialReviewCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialReviewFromStatus", app)
        self.assertIn("realDeviceFieldTrialReviewCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_review", app)
        self.assertIn("mobile_real_device_field_trial_review_summary", app)
        self.assertIn("mobile_real_device_field_trial_review_copy", app)
        self.assertIn("real_device", app)
        self.assertIn("production_app", app)
        self.assertIn("pwa_install_prompt", app)
        self.assertIn("user_choice", app)
        self.assertIn("offline", app)
        self.assertIn("touch", app)
        self.assertIn("visual", app)
        self.assertIn("material_redaction", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe review 字段", index)
        self.assertIn("不是 delivery success、真实验收通过或控制放行", app)
        self.assertIn("凭证、入口参数、机器内部字段", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceFieldTrialReviewAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialReview.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_runbook_execution_is_copyable_execution_only(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialRunbookExecutionTitle", index)
        self.assertIn("现场试跑执行清单", index)
        self.assertIn("copyRealDeviceFieldTrialRunbookExecutionButton", index)
        self.assertIn("mobileRealDeviceFieldTrialRunbookExecutionSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_runbook_execution.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_runbook_execution_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialRunbookExecutionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialRunbookExecutionFromStatus", app)
        self.assertIn("realDeviceFieldTrialRunbookExecutionCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution_summary", app)
        self.assertIn("mobile_real_device_field_trial_runbook_execution_copy", app)
        self.assertIn("runbookExecutionChecklist", app)
        self.assertIn("runbookExecutionReadiness", app)
        self.assertIn("real_device", app)
        self.assertIn("production_app", app)
        self.assertIn("pwa_install_prompt", app)
        self.assertIn("user_choice", app)
        self.assertIn("offline", app)
        self.assertIn("touch", app)
        self.assertIn("visual", app)
        self.assertIn("material_redaction", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe execution 字段", index)
        self.assertIn("本轮是 Docker/local mobile software proof", app)
        self.assertIn("下一次真实手机现场试跑采证", index)
        self.assertIn("不复制 raw artifact、凭证、内部路径或机器人响应", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceFieldTrialRunbookExecutionAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialRunbookExecution.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_evidence_record_is_copyable_archivable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialEvidenceRecordTitle", index)
        self.assertIn("现场证据记录", index)
        self.assertIn("generateRealDeviceFieldTrialEvidenceRecordButton", index)
        self.assertIn("copyRealDeviceFieldTrialEvidenceRecordButton", index)
        self.assertIn("archiveRealDeviceFieldTrialEvidenceRecordButton", index)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceRecordSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_evidence_record_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_record.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_record_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_record_copy.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_record_archive.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceRecordCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceRecordFromStatus", app)
        self.assertIn("realDeviceFieldTrialEvidenceRecordCopyPayload", app)
        self.assertIn("realDeviceFieldTrialEvidenceRecordArchivePayload", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_summary", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_copy", app)
        self.assertIn("mobile_real_device_field_trial_evidence_record_archive", app)
        self.assertIn("real_device", app)
        self.assertIn("production_app", app)
        self.assertIn("pwa_install_prompt", app)
        self.assertIn("user_choice", app)
        self.assertIn("offline", app)
        self.assertIn("touch", app)
        self.assertIn("visual", app)
        self.assertIn("material_redaction", app)
        self.assertIn("operator_note", app)
        self.assertIn("support_note", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe record 字段", index)
        self.assertIn("本轮是 Docker/local mobile software proof", app)
        self.assertIn("不保存 raw intake 或完整附件", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertIn("window.localStorage.setItem", app)
        self.assertNotIn("mobileRealDeviceFieldTrialEvidenceRecordAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialEvidenceRecord.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_evidence_verdict_is_copyable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialEvidenceVerdictTitle", index)
        self.assertIn("现场证据 verdict", index)
        self.assertIn("generateRealDeviceFieldTrialEvidenceVerdictButton", index)
        self.assertIn("copyRealDeviceFieldTrialEvidenceVerdictButton", index)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_verdict.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_verdict_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceVerdictCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialEvidenceVerdictFromStatus", app)
        self.assertIn("realDeviceFieldTrialEvidenceVerdictCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict_summary", app)
        self.assertIn("mobile_real_device_field_trial_evidence_verdict_copy", app)
        self.assertIn("missing_evidence", app)
        self.assertIn("retest_request", app)
        self.assertIn("next_material_request", app)
        self.assertIn("linked_evidence_record", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe verdict 字段", index)
        self.assertIn("本轮是 Docker/local mobile software proof", app)
        self.assertIn("不复制 record/archive 原文或附件", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceFieldTrialEvidenceVerdictAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialEvidenceVerdict.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_retest_execution_is_copyable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialRetestExecutionTitle", index)
        self.assertIn("现场复测执行", index)
        self.assertIn("generateRealDeviceFieldTrialRetestExecutionButton", index)
        self.assertIn("copyRealDeviceFieldTrialRetestExecutionButton", index)
        self.assertIn("mobileRealDeviceFieldTrialRetestExecutionSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_retest_execution_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_retest_execution.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_retest_execution_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_retest_execution_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialRetestExecutionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialRetestExecutionFromStatus", app)
        self.assertIn("realDeviceFieldTrialRetestExecutionCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution_summary", app)
        self.assertIn("mobile_real_device_field_trial_retest_execution_copy", app)
        self.assertIn("retest_request", app)
        self.assertIn("material_request", app)
        self.assertIn("execution_checklist", app)
        self.assertIn("linked_evidence_verdict", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe retest execution 字段", index)
        self.assertIn("本轮仍是 Docker/local mobile software proof", app)
        self.assertIn("不复制 verdict 原文、附件或机器人内部响应", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceFieldTrialRetestExecutionAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialRetestExecution.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_mobile_real_device_field_trial_acceptance_session_is_copyable_and_fail_closed(self):
        app = self.read("app.js")
        index = self.read("index.html")

        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionTitle", index)
        self.assertIn("现场验收会话", index)
        self.assertIn("generateRealDeviceFieldTrialAcceptanceSessionButton", index)
        self.assertIn("copyRealDeviceFieldTrialAcceptanceSessionButton", index)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionSafeCopy", index)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate", index)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session_summary.v1", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session_copy.v1", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionFromStatus", app)
        self.assertIn("mobileCurrentPwaFieldTrialBrowserProofCandidate", app)
        self.assertIn("realDeviceFieldTrialAcceptanceSessionCopyPayload", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session_summary", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_session_copy", app)
        self.assertIn("mobile_current_pwa_field_trial_browser_proof", app)
        self.assertIn("field_trial_retest_execution", app)
        self.assertIn("field_trial_evidence_verdict", app)
        self.assertIn("current_pwa_field_trial_browser_proof", app)
        self.assertIn("blocked_by_design_session", app)
        self.assertIn("real_device_observed", app)
        self.assertIn("production_app_observed", app)
        self.assertIn("pwa_install_prompt_observed", app)
        self.assertIn("install_user_choice_observed", app)
        self.assertIn("offline_reload_observed", app)
        self.assertIn("touch_target_issue", app)
        self.assertIn("visual_issue", app)
        self.assertIn("material_redaction_status", app)
        self.assertIn("operator_note", app)
        self.assertIn("support_note", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("safe_to_control=false", index)
        self.assertIn("accepted_processing_only_not_delivery_success", app)
        self.assertIn("not_proven", app)
        self.assertIn("whitelist-only phone-safe acceptance session 字段", index)
        self.assertIn("本轮是 Docker/local mobile software proof", app)
        self.assertIn("不会提交 ACK、cursor 或控制 endpoint", app)
        self.assertIn("navigator.clipboard.writeText", app)
        self.assertNotIn("mobileRealDeviceFieldTrialAcceptanceSessionAllowsPrimaryActions", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceSession.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

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
        self.assertEqual(payload["elevator_assist"]["schema"], "trashbot.elevator_assist_summary.v1")
        self.assertEqual(payload["elevator_assist"]["mode"], "dry_run")
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertEqual(
            payload["elevator_assist"]["evidence_boundary"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["elevator_assist_summary"]["evidence_boundary"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
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
            payload["mobile_device_handoff_session"]["schema"],
            "trashbot.mobile_device_handoff_session.v1",
        )
        self.assertEqual(
            payload["mobile_device_handoff_session"]["package_schema"],
            "trashbot.mobile_device_handoff_package.v1",
        )
        self.assertEqual(payload["mobile_device_handoff_session"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_device_handoff_session"]["real_device_observed"], False)
        self.assertEqual(payload["mobile_device_handoff_session"]["production_app_ready"], False)
        self.assertEqual(payload["mobile_device_handoff_session"]["pwa_install_prompt_observed"], False)
        self.assertEqual(payload["mobile_device_handoff_session"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_device_handoff_session"]["evidence_boundary"],
            "software_proof_docker_mobile_device_handoff_session_gate",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence"]["summary_schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_summary.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence"]["package_schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_package.v1",
        )
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence"]["install_prompt_capture_status"], "not_proven")
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence"]["install_prompt_user_outcome"], "not_proven")
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence"]["production_app_ready"], False)
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence"]["evidence_boundary"],
            "software_proof_docker_mobile_pwa_install_prompt_evidence_gate",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_summary"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_summary.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_package"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_package.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_event_capture"]["schema"],
            "trashbot.mobile_pwa_install_prompt_event_capture.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_event_capture"]["evidence_boundary"],
            "software_proof_docker_mobile_pwa_install_prompt_event_capture_gate",
        )
        self.assertEqual(payload["mobile_pwa_install_prompt_event_capture"]["beforeinstallprompt_status"], "missing")
        self.assertEqual(payload["mobile_pwa_install_prompt_event_capture"]["user_choice_outcome"], "not_proven")
        self.assertEqual(payload["mobile_pwa_install_prompt_event_capture"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_pwa_install_prompt_event_capture_summary"]["schema"],
            "trashbot.mobile_pwa_install_prompt_event_capture_summary.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_event_capture_copy"]["schema"],
            "trashbot.mobile_pwa_install_prompt_event_capture_copy.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_export.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export"]["summary_schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export"]["copy_schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export"]["evidence_boundary"],
            "software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate",
        )
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence_export"]["safe_to_control"], False)
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export"]["ack_semantics"],
            "accepted_processing_only_not_delivery_success",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export_summary"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1",
        )
        self.assertEqual(
            payload["mobile_pwa_install_prompt_evidence_export_copy"]["schema"],
            "trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1",
        )
        self.assertEqual(payload["mobile_pwa_install_prompt_evidence_export_copy"]["source"], "mobile_web")
        self.assertIn("not_proven", payload["mobile_pwa_install_prompt_evidence_export_copy"])
        self.assertEqual(
            payload["mobile_real_device_evidence_intake"]["schema"],
            "trashbot.mobile_real_device_evidence_intake.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_evidence_intake"]["summary_schema"],
            "trashbot.mobile_real_device_evidence_intake_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_evidence_intake"]["package_schema"],
            "trashbot.mobile_real_device_evidence_package.v1",
        )
        self.assertEqual(payload["mobile_real_device_evidence_intake"]["overall_status"], "blocked")
        self.assertEqual(payload["mobile_real_device_evidence_intake"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_real_device_evidence_intake"]["evidence"]["redaction_status"], "passed")
        self.assertEqual(
            payload["mobile_real_device_evidence_intake"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_evidence_intake_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_evidence_intake_summary"]["schema"],
            "trashbot.mobile_real_device_evidence_intake_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_evidence_package"]["schema"],
            "trashbot.mobile_real_device_evidence_package.v1",
        )
        self.assertEqual(payload["mobile_real_device_evidence_package"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_real_device_evidence_package"]["redaction_status"], "passed")
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision"]["schema"],
            "trashbot.mobile_real_device_acceptance_decision.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision"]["summary_schema"],
            "trashbot.mobile_real_device_acceptance_decision_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision"]["package_schema"],
            "trashbot.mobile_real_device_acceptance_decision_package.v1",
        )
        self.assertEqual(payload["mobile_real_device_acceptance_decision"]["decision"], "blocked_missing_evidence")
        self.assertEqual(payload["mobile_real_device_acceptance_decision"]["accepted_for_review"], False)
        self.assertEqual(payload["mobile_real_device_acceptance_decision"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_real_device_acceptance_decision"]["redaction_status"], "passed")
        self.assertIn("next_required_evidence", payload["mobile_real_device_acceptance_decision"])
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_acceptance_decision_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision_summary"]["schema"],
            "trashbot.mobile_real_device_acceptance_decision_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_acceptance_decision_package"]["schema"],
            "trashbot.mobile_real_device_acceptance_decision_package.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_handoff"]["schema"],
            "trashbot.mobile_real_device_review_handoff.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_handoff"]["summary_schema"],
            "trashbot.mobile_real_device_review_handoff_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_handoff"]["package_schema"],
            "trashbot.mobile_real_device_review_handoff_package.v1",
        )
        self.assertEqual(payload["mobile_real_device_review_handoff"]["decision_status"], "blocked_missing_evidence")
        self.assertEqual(payload["mobile_real_device_review_handoff"]["review_owner"], "review_owner_unassigned")
        self.assertEqual(payload["mobile_real_device_review_handoff"]["review_status"], "blocked_missing_evidence")
        self.assertEqual(payload["mobile_real_device_review_handoff"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_real_device_review_handoff"]["redaction_status"], "passed")
        self.assertIn("reviewer_checklist", payload["mobile_real_device_review_handoff"])
        self.assertIn("next_required_evidence", payload["mobile_real_device_review_handoff"])
        self.assertEqual(
            payload["mobile_real_device_review_handoff"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_review_handoff_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_review_handoff_summary"]["schema"],
            "trashbot.mobile_real_device_review_handoff_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_handoff_package"]["schema"],
            "trashbot.mobile_real_device_review_handoff_package.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_execution"]["schema"],
            "trashbot.mobile_real_device_review_execution.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_review_execution"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_review_execution_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request"]["schema"],
            "trashbot.mobile_real_device_retest_request.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request"]["summary_schema"],
            "trashbot.mobile_real_device_retest_request_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request"]["package_schema"],
            "trashbot.mobile_real_device_retest_request_package.v1",
        )
        self.assertEqual(payload["mobile_real_device_retest_request"]["request_status"], "blocked_missing_evidence")
        self.assertEqual(payload["mobile_real_device_retest_request"]["safe_to_control"], False)
        self.assertEqual(payload["mobile_real_device_retest_request"]["redaction_status"], "passed")
        self.assertIn("missing_evidence_list", payload["mobile_real_device_retest_request"])
        self.assertIn("retest_checklist", payload["mobile_real_device_retest_request"])
        self.assertEqual(
            payload["mobile_real_device_retest_request"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_retest_request_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request"]["source_evidence_boundary"],
            "software_proof_docker_mobile_real_device_review_execution_gate",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request_summary"]["schema"],
            "trashbot.mobile_real_device_retest_request_summary.v1",
        )
        self.assertEqual(
            payload["mobile_real_device_retest_request_package"]["schema"],
            "trashbot.mobile_real_device_retest_request_package.v1",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_real_device_evidence_intake"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_evidence_intake_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_real_device_acceptance_decision"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_acceptance_decision_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_real_device_review_handoff"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_review_handoff_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_real_device_retest_request"]["evidence_boundary"],
            "software_proof_docker_mobile_real_device_retest_request_gate",
        )
        self.assertEqual(
            payload["phone_readiness"]["mobile_pwa_install_prompt_evidence"]["evidence_boundary"],
            "software_proof_docker_mobile_pwa_install_prompt_evidence_gate",
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
            payload["phone_readiness"]["mobile_device_handoff_session"]["evidence_boundary"],
            "software_proof_docker_mobile_device_handoff_session_gate",
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
        self.assertIn("trashbot.mobile_device_handoff_session.v1", encoded)
        self.assertIn("trashbot.mobile_device_handoff_package.v1", encoded)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence.v1", encoded)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_summary.v1", encoded)
        self.assertIn("trashbot.mobile_pwa_install_prompt_evidence_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_evidence_intake.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_evidence_intake_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_evidence_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_acceptance_decision_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_handoff.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_handoff_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_handoff_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_execution.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_execution_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_review_execution_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_retest_request.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_retest_request_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_retest_request_package.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session_summary.v1", encoded)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_session_copy.v1", encoded)
        self.assertIn("trashbot.mobile_browser_acceptance_bundle.v1", encoded)
        self.assertIn("blocked-by-design", encoded)
        self.assertIn("真实 pwa install prompt", encoded)
        self.assertIn("software_proof_docker_mobile_device_acceptance_readiness_gate", encoded)
        self.assertIn("software_proof_docker_mobile_device_evidence_capture_gate", encoded)
        self.assertIn("software_proof_docker_mobile_device_handoff_session_gate", encoded)
        self.assertIn("software_proof_docker_mobile_pwa_install_prompt_evidence_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_evidence_intake_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_acceptance_decision_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_review_handoff_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_review_execution_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate", encoded)
        self.assertIn("software_proof_docker_mobile_browser_acceptance_bundle_gate", encoded)
        self.assertIn("redaction", encoded)
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
            "checksum",
            "raw artifact",
            "complete artifact",
            "serial device",
            "local path",
        ):
            self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
