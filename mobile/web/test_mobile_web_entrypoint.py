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


if __name__ == "__main__":
    unittest.main()
