import json
import re
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parent
REPO_ROOT = WEB_ROOT.parent.parent
FIXTURE = WEB_ROOT / "fixtures" / "status.json"
DOC = REPO_ROOT / "docs" / "product" / "mobile_user_flow.md"


class HardwareSensorProcurementExecutionPackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hardware_baseline_source_alignment_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 来源对齐 panel 由 JS 放在 hardware baseline review 后，避免本轮越权改静态 index。
        self.assertIn("hardwareBaselineSourceAlignmentTitle", app)
        self.assertIn("硬件基线来源对齐", app)
        self.assertIn("hardwareBaselineReviewTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-baseline-source-alignment-panel", styles)
        self.assertIn("hardware-baseline-source-alignment-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_BASELINE_SOURCE_ALIGNMENT_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_BASELINE_SOURCE_ALIGNMENT_TEXT", app)
        self.assertIn("safeHardwareBaselineSourceAlignmentText", app)
        self.assertIn("hardwareBaselineSourceAlignmentCandidate", app)
        self.assertIn("hardwareBaselineSourceAlignmentFromStatus", app)
        self.assertIn("hardware_baseline_source_alignment", app)
        self.assertIn("hardware_baseline_source_alignment_summary", app)
        self.assertIn("diagnosticsSummary.hardware_baseline_source_alignment", app)
        self.assertIn("statusDiagnosticsSummary.hardware_baseline_source_alignment", app)
        self.assertIn("alignment_status", app)
        self.assertIn("default_hardware_set_summary", app)
        self.assertIn("target_sensor_baseline_summary", app)
        self.assertIn("vendor_source_boundary", app)
        self.assertIn("missing_alignment_items", app)
        self.assertIn("safe_evidence_ref", app)

        # copy/export 只输出白名单字段，不能新增主操作请求或控制授权。
        self.assertIn("hardwareBaselineSourceAlignmentCopyPayload", app)
        self.assertIn("trashbot.hardware_baseline_source_alignment_copy.v1", app)
        self.assertIn("copyHardwareBaselineSourceAlignmentButton", app)
        self.assertIn("downloadHardwareBaselineSourceAlignmentButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareBaselineSourceAlignment.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        alignment = fixture["hardware_baseline_source_alignment"]
        self.assertEqual(alignment["alignment_status"], "hardware_baseline_source_alignment_not_proven")
        self.assertEqual(alignment["delivery_success"], False)
        self.assertEqual(alignment["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_baseline_source_alignment_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_baseline_source_alignment", doc)
        self.assertIn("硬件基线来源对齐", doc)

    def test_hardware_baseline_source_alignment_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        alignment_text = json.dumps(
            fixture["hardware_baseline_source_alignment"],
            ensure_ascii=False,
        ).lower()

        # 来源对齐 fixture 只允许脱敏 metadata，不允许 raw vendor、路径、串口或控制成功语义外流。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "serial/uart",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw vendor document",
            "control grant",
            "hil passed",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, alignment_text)

    def test_execution_pack_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 执行包 panel 由 JS 放在 review decision 后，避免本轮越权改静态 index 结构。
        self.assertIn("hardwareSensorProcurementExecutionPackTitle", app)
        self.assertIn("传感器采购执行包", app)
        self.assertIn("hardwareSensorProcurementReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-procurement-execution-pack-panel", styles)
        self.assertIn("hardware-sensor-procurement-execution-pack-grid", styles)

        # 状态来源只接受 phone-safe 摘要，不展示 raw 包、路径、凭证或底盘控制细节。
        self.assertIn("HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeHardwareSensorProcurementExecutionPackText", app)
        self.assertIn("hardwareSensorProcurementExecutionPackCandidate", app)
        self.assertIn("hardwareSensorProcurementExecutionPackFromStatus", app)
        self.assertIn("hardware_sensor_procurement_execution_pack", app)
        self.assertIn("hardware_sensor_procurement_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_procurement_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_procurement_execution_pack", app)
        self.assertIn("execution_pack_status", app)
        self.assertIn("material_templates", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("safe_rerun_command", app)
        self.assertIn("safe_evidence_ref", app)

        # copy/export whitelist 只输出执行包交接字段，不能改变 Start/Confirm/Cancel gating。
        self.assertIn("hardwareSensorProcurementExecutionPackCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_procurement_execution_pack_copy.v1", app)
        self.assertIn("copyHardwareSensorProcurementExecutionPackButton", app)
        self.assertIn("downloadHardwareSensorProcurementExecutionPackButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareSensorProcurementExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        execution_pack = fixture["hardware_sensor_procurement_execution_pack"]
        self.assertEqual(execution_pack["execution_pack_status"], "hardware_material_pending")
        self.assertEqual(execution_pack["delivery_success"], False)
        self.assertEqual(execution_pack["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_procurement_execution_pack_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_sensor_procurement_execution_pack", doc)
        self.assertIn("传感器采购执行包", doc)

    def test_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        execution_pack_text = json.dumps(
            fixture["hardware_sensor_procurement_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # 白名单 fixture 不能把真实控制、底层硬件或凭证材料伪装成可复制执行包。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw vendor document",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, execution_pack_text)


class HardwareSensorProcurementReceiptIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_receipt_intake_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 收货回填 panel 由 JS 放在执行包后，保持首屏材料链顺序且不改静态 shell。
        self.assertIn("hardwareSensorProcurementReceiptIntakeTitle", app)
        self.assertIn("传感器采购收货回填", app)
        self.assertIn("hardwareSensorProcurementExecutionPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-procurement-receipt-intake-panel", styles)
        self.assertIn("hardware-sensor-procurement-receipt-intake-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_TEXT", app)
        self.assertIn("safeHardwareSensorProcurementReceiptIntakeText", app)
        self.assertIn("hardwareSensorProcurementReceiptIntakeCandidate", app)
        self.assertIn("hardwareSensorProcurementReceiptIntakeFromStatus", app)
        self.assertIn("hardware_sensor_procurement_receipt_intake", app)
        self.assertIn("hardware_sensor_procurement_receipt_intake_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_procurement_receipt_intake", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_procurement_receipt_intake", app)
        self.assertIn("receipt_intake_status", app)
        self.assertIn("material_status", app)
        self.assertIn("missing_materials", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("safe_evidence_ref", app)

        # copy/export 只输出白名单字段，不能新增任何主操作请求或控制授权。
        self.assertIn("hardwareSensorProcurementReceiptIntakeCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_procurement_receipt_intake_copy.v1", app)
        self.assertIn("copyHardwareSensorProcurementReceiptIntakeButton", app)
        self.assertIn("downloadHardwareSensorProcurementReceiptIntakeButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareSensorProcurementReceiptIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        receipt_intake = fixture["hardware_sensor_procurement_receipt_intake"]
        self.assertEqual(receipt_intake["receipt_intake_status"], "hardware_material_pending")
        self.assertEqual(receipt_intake["material_status"], "hardware_material_pending")
        self.assertEqual(receipt_intake["delivery_success"], False)
        self.assertEqual(receipt_intake["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_procurement_receipt_intake_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_sensor_procurement_receipt_intake", doc)
        self.assertIn("传感器采购收货回填", doc)

    def test_receipt_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        receipt_intake_text = json.dumps(
            fixture["hardware_sensor_procurement_receipt_intake"],
            ensure_ascii=False,
        ).lower()

        # 收货回填 fixture 只能承载脱敏摘要，不能把真实控制、凭证或成功语义带进手机端。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw vendor document",
            "procurement success",
            "采购成功",
            "hil passed",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, receipt_intake_text)


class HardwareSensorHilEntryConfigPrecheckMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hil_entry_config_precheck_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # HIL-entry config precheck panel 由 JS 放在收货回填后，只展示 phone-safe 配置摘要。
        self.assertIn("hardwareSensorHilEntryConfigPrecheckTitle", app)
        self.assertIn("传感器 HIL 入口配置预检", app)
        self.assertIn("hardwareSensorProcurementReceiptIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-hil-entry-config-precheck-panel", styles)
        self.assertIn("hardware-sensor-hil-entry-config-precheck-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_TEXT", app)
        self.assertIn("safeHardwareSensorHilEntryConfigPrecheckText", app)
        self.assertIn("hardwareSensorHilEntryConfigPrecheckCandidate", app)
        self.assertIn("hardwareSensorHilEntryConfigPrecheckFromStatus", app)
        self.assertIn("hardware_sensor_hil_entry_config_precheck", app)
        self.assertIn("hardware_sensor_hil_entry_config_precheck_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_hil_entry_config_precheck", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_hil_entry_config_precheck", app)
        self.assertIn("precheck_status", app)
        self.assertIn("sensor_count_summary", app)
        self.assertIn("threshold_summary", app)
        self.assertIn("frame_ids_summary", app)
        self.assertIn("safety_policy_summary", app)
        self.assertIn("missing_config_material_summary", app)
        self.assertIn("blocked copy unavailable", app)

        # copy/export whitelist 不新增任何 Start/Confirm/Cancel 请求或控制授权。
        self.assertIn("hardwareSensorHilEntryConfigPrecheckCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_hil_entry_config_precheck_copy.v1", app)
        self.assertIn("copyHardwareSensorHilEntryConfigPrecheckButton", app)
        self.assertIn("downloadHardwareSensorHilEntryConfigPrecheckButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareSensorHilEntryConfigPrecheck.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        precheck = fixture["hardware_sensor_hil_entry_config_precheck"]
        self.assertEqual(
            precheck["precheck_status"],
            "hardware_sensor_hil_entry_config_precheck_not_proven",
        )
        self.assertEqual(precheck["delivery_success"], False)
        self.assertEqual(precheck["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_sensor_hil_entry_config_precheck", doc)
        self.assertIn("传感器 HIL 入口配置预检", doc)

    def test_hil_entry_config_precheck_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        precheck_text = json.dumps(
            fixture["hardware_sensor_hil_entry_config_precheck"],
            ensure_ascii=False,
        ).lower()

        # 配置预检 fixture 不能把 raw config、底盘控制、凭证、路径或成功语义带进手机端。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw config",
            "serial device",
            "serial/uart",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw sensor config",
            "control grant",
            "hil passed",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, precheck_text)


class RouteTaskTerminalCompletionRehearsalMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_terminal_completion_rehearsal_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 终态复账 panel 靠近 completion signal，但只展示终态复核摘要，不新增控制授权。
        self.assertIn("routeTaskTerminalCompletionRehearsalTitle", app)
        self.assertIn("任务终态复账", app)
        self.assertIn("routeTaskCompletionSignalTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-terminal-completion-panel", styles)
        self.assertIn("route-task-terminal-completion-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_TERMINAL_COMPLETION_TEXT", app)
        self.assertIn("safeRouteTaskTerminalCompletionText", app)
        self.assertIn("routeTaskTerminalCompletionRehearsalCandidate", app)
        self.assertIn("routeTaskTerminalCompletionRehearsalFromStatus", app)
        self.assertIn("route_task_terminal_completion_rehearsal", app)
        self.assertIn("route_task_terminal_completion_rehearsal_summary", app)
        self.assertIn("diagnosticsSummary.route_task_terminal_completion_rehearsal", app)
        self.assertIn("statusDiagnosticsSummary.route_task_terminal_completion_rehearsal", app)
        self.assertIn("terminal_verdict", app)
        self.assertIn("dropoff_material_status", app)
        self.assertIn("cancel_material_status", app)
        self.assertIn("failure_recovery_reason", app)
        self.assertIn("operator_next_steps", app)
        self.assertIn("safe_evidence_ref", app)

        # copy/export 只输出白名单字段，不能新增 Start/Confirm/Cancel 请求或成功文案。
        self.assertIn("routeTaskTerminalCompletionRehearsalCopyPayload", app)
        self.assertIn("trashbot.route_task_terminal_completion_rehearsal_copy.v1", app)
        self.assertIn("copyRouteTaskTerminalCompletionRehearsalButton", app)
        self.assertIn("downloadRouteTaskTerminalCompletionRehearsalButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskTerminalCompletionRehearsal.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        rehearsal = fixture["route_task_terminal_completion_rehearsal"]
        self.assertEqual(rehearsal["terminal_verdict"], "blocked_missing_real_terminal_materials_not_proven")
        self.assertEqual(rehearsal["delivery_success"], False)
        self.assertEqual(rehearsal["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_terminal_completion_rehearsal_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_terminal_completion_rehearsal", doc)
        self.assertIn("任务终态复账", doc)

    def test_terminal_completion_rehearsal_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        rehearsal_text = json.dumps(
            fixture["route_task_terminal_completion_rehearsal"],
            ensure_ascii=False,
        ).lower()

        # 终态复账 fixture 不能携带 raw JSON、底层控制、完整 artifact、校验值或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, rehearsal_text)


class RouteTaskTerminalReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_terminal_review_decision_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 终态复核决策 panel 紧跟终态复账，只做复测指导展示，不改变主操作 gating。
        self.assertIn("routeTaskTerminalReviewDecisionTitle", app)
        self.assertIn("终态复核决策", app)
        self.assertIn("routeTaskTerminalCompletionRehearsalTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-terminal-review-decision-panel", styles)
        self.assertIn("route-task-terminal-review-decision-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("ROUTE_TASK_TERMINAL_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_TERMINAL_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskTerminalReviewDecisionText", app)
        self.assertIn("routeTaskTerminalReviewDecisionCandidate", app)
        self.assertIn("routeTaskTerminalReviewDecisionFromStatus", app)
        self.assertIn("route_task_terminal_review_decision", app)
        self.assertIn("route_task_terminal_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_terminal_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_terminal_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("decision_reason", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("field_retest_request_guidance", app)
        self.assertIn("safe_evidence_ref", app)

        # copy/export 只输出白名单字段，不能新增 Start/Confirm/Cancel 请求或成功文案。
        self.assertIn("routeTaskTerminalReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_terminal_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskTerminalReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskTerminalReviewDecisionButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskTerminalReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        review = fixture["route_task_terminal_review_decision"]
        self.assertEqual(review["review_decision"], "blocked_missing_real_terminal_materials_not_proven")
        self.assertEqual(review["delivery_success"], False)
        self.assertEqual(review["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_terminal_review_decision_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_terminal_review_decision", doc)
        self.assertIn("终态复核决策", doc)

    def test_terminal_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        review_text = json.dumps(
            fixture["route_task_terminal_review_decision"],
            ensure_ascii=False,
        ).lower()

        # 终态复核决策 fixture 只能携带复测指导摘要，不能带 raw 材料、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "hil",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, review_text)


if __name__ == "__main__":
    unittest.main()
