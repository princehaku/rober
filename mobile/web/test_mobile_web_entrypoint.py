import json
import re
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parent
REPO_ROOT = WEB_ROOT.parent.parent
FIXTURE = WEB_ROOT / "fixtures" / "status.json"
MOBILE_STATUS_FIXTURE = REPO_ROOT / "mobile" / "fixtures" / "mobile_web_status.fixture.json"
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


class HardwareSensorHilEntryReadinessReviewMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hil_entry_readiness_review_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 准入评审 panel 接在 config precheck 后，只展示 Hardware/Robot 脱敏 summary。
        self.assertIn("hardwareSensorHilEntryReadinessReviewTitle", app)
        self.assertIn("传感器 HIL 准入评审", app)
        self.assertIn("hardwareSensorHilEntryConfigPrecheckTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-hil-entry-readiness-review-panel", styles)
        self.assertIn("hardware-sensor-hil-entry-readiness-review-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_TEXT", app)
        self.assertIn("safeHardwareSensorHilEntryReadinessReviewText", app)
        self.assertIn("hardwareSensorHilEntryReadinessReviewCandidate", app)
        self.assertIn("hardwareSensorHilEntryReadinessReviewFromStatus", app)
        self.assertIn("hardware_sensor_hil_entry_readiness_review", app)
        self.assertIn("hardware_sensor_hil_entry_readiness_review_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_hil_entry_readiness_review", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_hil_entry_readiness_review", app)
        self.assertIn("readiness_status", app)
        self.assertIn("missing_materials", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("boundary_summary", app)

        # copy/export whitelist 不新增任何 Start/Confirm/Cancel 请求或控制授权。
        self.assertIn("hardwareSensorHilEntryReadinessReviewCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_hil_entry_readiness_review_copy.v1", app)
        self.assertIn("copyHardwareSensorHilEntryReadinessReviewButton", app)
        self.assertIn("downloadHardwareSensorHilEntryReadinessReviewButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareSensorHilEntryReadinessReview.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        review = fixture["hardware_sensor_hil_entry_readiness_review"]
        self.assertEqual(
            review["readiness_status"],
            "hardware_sensor_hil_entry_readiness_review_not_proven",
        )
        self.assertEqual(review["delivery_success"], False)
        self.assertEqual(review["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_sensor_hil_entry_readiness_review", doc)
        self.assertIn("传感器 HIL 准入评审", doc)

    def test_hil_entry_readiness_review_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        review_text = json.dumps(
            fixture["hardware_sensor_hil_entry_readiness_review"],
            ensure_ascii=False,
        ).lower()

        # 准入评审 fixture 不能携带 raw vendor、raw JSON、串口、路径、凭证、完整材料或成功语义。
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
            "complete artifacts",
            "raw vendor document",
            "raw material",
            "absolute path",
            "control grant",
            "hil passed",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, review_text)


class HardwareSensorHilEntryExecutionPackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hil_entry_execution_pack_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 执行包 panel 接在 readiness review 后，只展示 HIL-entry 现场交接摘要。
        self.assertIn("hardwareSensorHilEntryExecutionPackTitle", app)
        self.assertIn("传感器 HIL 准入执行包", app)
        self.assertIn("hardwareSensorHilEntryReadinessReviewTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-hil-entry-execution-pack-panel", styles)
        self.assertIn("hardware-sensor-hil-entry-execution-pack-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeHardwareSensorHilEntryExecutionPackText", app)
        self.assertIn("hardwareSensorHilEntryExecutionPackCandidate", app)
        self.assertIn("hardwareSensorHilEntryExecutionPackFromStatus", app)
        self.assertIn("hardware_sensor_hil_entry_execution_pack", app)
        self.assertIn("hardware_sensor_hil_entry_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_hil_entry_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_hil_entry_execution_pack", app)
        self.assertIn("execution_status", app)
        self.assertIn("readiness_status", app)
        self.assertIn("required_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("boundary_summary", app)

        # copy/export whitelist 不新增任何 Start Delivery / Confirm Dropoff / Cancel 请求或控制授权。
        self.assertIn("hardwareSensorHilEntryExecutionPackCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_hil_entry_execution_pack_copy.v1", app)
        self.assertIn("copyHardwareSensorHilEntryExecutionPackButton", app)
        self.assertIn("downloadHardwareSensorHilEntryExecutionPackButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"hardwareSensorHilEntryExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 software proof / not_proven 边界。
        execution_pack = fixture["hardware_sensor_hil_entry_execution_pack"]
        self.assertEqual(
            execution_pack["execution_status"],
            "hardware_sensor_hil_entry_execution_pack_not_proven",
        )
        self.assertEqual(execution_pack["delivery_success"], False)
        self.assertEqual(execution_pack["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("hardware_sensor_hil_entry_execution_pack", doc)
        self.assertIn("传感器 HIL 准入执行包", doc)

    def test_hil_entry_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        execution_pack_text = json.dumps(
            fixture["hardware_sensor_hil_entry_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # 执行包 fixture 只能携带脱敏摘要，不能把原始材料、凭证、路径或完成声明带进手机端。
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
            "complete artifacts",
            "raw vendor document",
            "raw material",
            "absolute path",
            "control grant",
            "hil passed",
            "field pass",
            "采购完成",
            "安装完成",
            "接线完成",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, execution_pack_text)


class WaveRoverFeedbackReplayMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_wave_rover_feedback_replay_panel_is_read_only_and_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # feedback replay panel 接在硬件材料链后，只消费 phone-safe summary，不新增控制入口。
        self.assertIn("waveRoverFeedbackReplayTitle", app)
        self.assertIn("WAVE ROVER feedback replay", app)
        self.assertIn("hardwareSensorHilEntryExecutionPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("WAVE_ROVER_FEEDBACK_REPLAY_BOUNDARY", app)
        self.assertIn("UNSAFE_WAVE_ROVER_FEEDBACK_REPLAY_TEXT", app)
        self.assertIn("safeWaveRoverFeedbackReplayText", app)
        self.assertIn("waveRoverFeedbackReplayCandidate", app)
        self.assertIn("waveRoverFeedbackReplayFromStatus", app)
        self.assertIn("wave_rover_feedback_replay", app)
        self.assertIn("wave_rover_feedback_replay_summary", app)
        self.assertIn("robot_diagnostics_wave_rover_feedback_replay_summary", app)
        self.assertIn("diagnosticsSummary.wave_rover_feedback_replay", app)
        self.assertIn("statusDiagnosticsSummary.wave_rover_feedback_replay", app)
        self.assertIn("replay_status", app)
        self.assertIn("interval_status", app)
        self.assertIn("topic_alignment_status", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("next_required_evidence", app)

        # 只读 panel 不调用 Start Delivery / Confirm Dropoff / Cancel，也保持 fail-closed flags。
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"waveRoverFeedbackReplay.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        replay = fixture["wave_rover_feedback_replay"]
        self.assertEqual(replay["replay_status"], "wave_rover_feedback_replay_not_proven")
        self.assertEqual(replay["delivery_success"], False)
        self.assertEqual(replay["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_wave_rover_feedback_replay_gate", fixture_text)
        self.assertIn("interval_summary", fixture_text)
        self.assertIn("topic_alignment_status", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("wave_rover_feedback_replay", doc)
        self.assertIn("WAVE ROVER feedback replay", doc)

    def test_wave_rover_feedback_replay_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        replay_text = json.dumps(
            fixture["wave_rover_feedback_replay"],
            ensure_ascii=False,
        ).lower()

        # feedback replay fixture 只能携带白名单摘要，不能带原始反馈、路径、串口、校验和或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw feedback",
            "full feedback",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "traceback",
            "hil passed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, replay_text)


class WaveRoverHilPacketIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_wave_rover_hil_packet_intake_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # HIL packet intake panel 复用 feedback replay 后的安全摘要链路，不新增控制入口。
        self.assertIn("waveRoverHilPacketIntakeTitle", app)
        self.assertIn("WAVE ROVER HIL packet intake", app)
        self.assertIn("waveRoverFeedbackReplayTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("WAVE_ROVER_HIL_PACKET_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_WAVE_ROVER_HIL_PACKET_INTAKE_TEXT", app)
        self.assertIn("safeWaveRoverHilPacketIntakeText", app)
        self.assertIn("waveRoverHilPacketIntakeCandidate", app)
        self.assertIn("waveRoverHilPacketIntakeFromStatus", app)
        self.assertIn("wave_rover_hil_packet_intake", app)
        self.assertIn("wave_rover_hil_packet_intake_summary", app)
        self.assertIn("robot_diagnostics_wave_rover_hil_packet_intake_summary", app)
        self.assertIn("diagnosticsSummary.wave_rover_hil_packet_intake", app)
        self.assertIn("statusDiagnosticsSummary.wave_rover_hil_packet_intake", app)
        self.assertIn("packet_status", app)
        self.assertIn("required_files_summary", app)
        self.assertIn("missing_files_summary", app)
        self.assertIn("operator_report_status", app)
        self.assertIn("same_evidence_ref_required", app)

        # copy/export 必须走 whitelist-only payload，并保持 Start/Confirm/Cancel gating 不变。
        self.assertIn("waveRoverHilPacketIntakeCopyPayload", app)
        self.assertIn("trashbot.wave_rover_hil_packet_intake_copy.v1", app)
        self.assertIn("copyWaveRoverHilPacketIntakeButton", app)
        self.assertIn("downloadWaveRoverHilPacketIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"waveRoverHilPacketIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和产品文档必须固定 HIL packet intake 的 software proof / not_proven 边界。
        intake = fixture["wave_rover_hil_packet_intake"]
        self.assertEqual(intake["packet_status"], "wave_rover_hil_packet_intake_not_proven")
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertEqual(intake["same_evidence_ref_required"], True)
        self.assertIn("software_proof_docker_wave_rover_hil_packet_intake_gate", fixture_text)
        self.assertIn("required_files_summary", fixture_text)
        self.assertIn("missing_files_summary", fixture_text)
        self.assertIn("operator_report_status", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("wave_rover_hil_packet_intake", doc)
        self.assertIn("WAVE ROVER HIL packet intake", doc)

    def test_wave_rover_hil_packet_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["wave_rover_hil_packet_intake"],
            ensure_ascii=False,
        ).lower()

        # intake fixture 只能携带白名单摘要，不能带原始 packet、路径、串口设备、校验和或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw artifact",
            "raw packet",
            "raw feedback",
            "full feedback",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "traceback",
            "hil passed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)


class WaveRoverHilPacketReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_wave_rover_hil_packet_review_decision_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # review-decision panel 跟在 intake 后，只展示评审摘要，不新增控制入口。
        self.assertIn("waveRoverHilPacketReviewDecisionTitle", app)
        self.assertIn("WAVE ROVER HIL packet review decision", app)
        self.assertIn("waveRoverHilPacketIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeWaveRoverHilPacketReviewDecisionText", app)
        self.assertIn("waveRoverHilPacketReviewDecisionCandidate", app)
        self.assertIn("waveRoverHilPacketReviewDecisionFromStatus", app)
        self.assertIn("wave_rover_hil_packet_review_decision", app)
        self.assertIn("wave_rover_hil_packet_review_decision_summary", app)
        self.assertIn("robot_diagnostics_wave_rover_hil_packet_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.wave_rover_hil_packet_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.wave_rover_hil_packet_review_decision", app)
        self.assertIn("accepted_required_materials", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("rejected_required_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("same_evidence_ref_required", app)

        # copy/export 必须走 whitelist-only payload，并保持 Start/Confirm/Cancel gating 不变。
        self.assertIn("waveRoverHilPacketReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.wave_rover_hil_packet_review_decision_copy.v1", app)
        self.assertIn("copyWaveRoverHilPacketReviewDecisionButton", app)
        self.assertIn("downloadWaveRoverHilPacketReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"waveRoverHilPacketReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和产品文档必须固定 review-decision 的 software proof / not_proven 边界。
        decision = fixture["wave_rover_hil_packet_review_decision"]
        self.assertEqual(decision["review_decision"], "blocked_pending_real_hil_packet")
        self.assertEqual(decision["overall_status"], "not_proven")
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertEqual(decision["same_evidence_ref_required"], True)
        self.assertIn("software_proof_docker_wave_rover_hil_packet_review_decision_gate", fixture_text)
        self.assertIn("accepted_required_materials", fixture_text)
        self.assertIn("missing_required_materials", fixture_text)
        self.assertIn("rejected_required_materials", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("wave_rover_hil_packet_review_decision", doc)
        self.assertIn("WAVE ROVER HIL packet review decision", doc)

    def test_wave_rover_hil_packet_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["wave_rover_hil_packet_review_decision"],
            ensure_ascii=False,
        ).lower()

        # review-decision fixture 只能携带白名单摘要，不能带原始评审、底层设备、校验和或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw artifact",
            "raw packet",
            "raw review",
            "raw feedback",
            "full raw feedback",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "traceback",
            "hil passed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)


class WaveRoverHilPacketExecutionPackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_wave_rover_hil_packet_execution_pack_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # execution-pack panel 接在 review-decision 后，只展示白名单交接材料，不新增控制入口。
        self.assertIn("waveRoverHilPacketExecutionPackTitle", app)
        self.assertIn("WAVE ROVER HIL packet execution pack", app)
        self.assertIn("waveRoverHilPacketReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeWaveRoverHilPacketExecutionPackText", app)
        self.assertIn("waveRoverHilPacketExecutionPackCandidate", app)
        self.assertIn("waveRoverHilPacketExecutionPackFromStatus", app)
        self.assertIn("wave_rover_hil_packet_execution_pack", app)
        self.assertIn("wave_rover_hil_packet_execution_pack_summary", app)
        self.assertIn("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.wave_rover_hil_packet_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.wave_rover_hil_packet_execution_pack", app)
        self.assertIn("execution_pack_status", app)
        self.assertIn("required_material_templates", app)
        self.assertIn("collection_sequence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("same_evidence_ref_required", app)

        # copy/export 必须走 whitelist-only payload，并保持 Start/Confirm/Cancel gating 不变。
        self.assertIn("waveRoverHilPacketExecutionPackCopyPayload", app)
        self.assertIn("trashbot.wave_rover_hil_packet_execution_pack_copy.v1", app)
        self.assertIn("copyWaveRoverHilPacketExecutionPackButton", app)
        self.assertIn("downloadWaveRoverHilPacketExecutionPackButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"waveRoverHilPacketExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和产品文档必须固定 execution-pack 的 software proof / not_proven 边界。
        execution_pack = fixture["wave_rover_hil_packet_execution_pack"]
        self.assertEqual(
            execution_pack["execution_pack_status"],
            "wave_rover_hil_packet_execution_pack_not_proven",
        )
        self.assertEqual(execution_pack["overall_status"], "not_proven")
        self.assertEqual(execution_pack["delivery_success"], False)
        self.assertEqual(execution_pack["primary_actions_enabled"], False)
        self.assertEqual(execution_pack["same_evidence_ref_required"], True)
        self.assertIn("software_proof_docker_wave_rover_hil_packet_execution_pack_gate", fixture_text)
        self.assertIn("required_material_templates", fixture_text)
        self.assertIn("collection_sequence", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("rerun_commands", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("wave_rover_hil_packet_execution_pack", doc)
        self.assertIn("WAVE ROVER HIL packet execution pack", doc)

    def test_wave_rover_hil_packet_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        execution_pack_text = json.dumps(
            fixture["wave_rover_hil_packet_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # execution-pack fixture 只能携带白名单摘要，不能带原始包、设备参数、校验和或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw artifact",
            "raw packet",
            "raw execution pack",
            "raw feedback",
            "full raw feedback",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "traceback",
            "hil passed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, execution_pack_text)


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


class RouteTaskFieldRetestExecutionPackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_execution_pack_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场复测执行包 panel 紧跟终态复核决策，只读展示下一次真实复测需要的安全摘要。
        self.assertIn("routeTaskFieldRetestExecutionPackTitle", app)
        self.assertIn("现场复测执行包", app)
        self.assertIn("routeTaskTerminalReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-execution-pack-panel", styles)
        self.assertIn("route-task-field-retest-execution-pack-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestExecutionPackText", app)
        self.assertIn("routeTaskFieldRetestExecutionPackCandidate", app)
        self.assertIn("routeTaskFieldRetestExecutionPackFromStatus", app)
        self.assertIn("route_task_field_retest_execution_pack", app)
        self.assertIn("route_task_field_retest_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_execution_pack", app)
        self.assertIn("execution_status", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("same_evidence_ref_required", app)
        self.assertIn("required_field_materials_summary", app)
        self.assertIn("rerun_command_summary", app)
        self.assertIn("operator_handoff", app)
        self.assertIn("field_retest_checklist", app)

        # copy/export whitelist 只输出执行包交接字段，不新增 Start/Confirm/Cancel 请求或成功文案。
        self.assertIn("routeTaskFieldRetestExecutionPackCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_execution_pack_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestExecutionPackButton", app)
        self.assertIn("downloadRouteTaskFieldRetestExecutionPackButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        execution_pack = fixture["route_task_field_retest_execution_pack"]
        self.assertEqual(execution_pack["execution_status"], "blocked_missing_real_field_retest_materials_not_proven")
        self.assertEqual(execution_pack["delivery_success"], False)
        self.assertEqual(execution_pack["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_execution_pack_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_execution_pack", doc)
        self.assertIn("现场复测执行包", doc)

    def test_field_retest_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        execution_pack_text = json.dumps(
            fixture["route_task_field_retest_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # 现场复测执行包 fixture 只能携带白名单摘要，不能带 raw 材料、底层控制或成功状态。
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
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, execution_pack_text)


class RouteTaskFieldRetestSessionHandoffMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_session_handoff_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # session handoff 是 execution pack 后的新独立 panel，不修改旧 execution pack 语义。
        self.assertIn("routeTaskFieldRetestSessionHandoffTitle", app)
        self.assertIn("路线任务现场复测交接", app)
        self.assertIn("routeTaskFieldRetestExecutionPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-session-handoff-panel", styles)
        self.assertIn("route-task-field-retest-session-handoff-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_BOUNDARY", app)
        self.assertIn("routeTaskFieldRetestSessionHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestSessionHandoffFromStatus", app)
        self.assertIn("route_task_field_retest_session_handoff", app)
        self.assertIn("route_task_field_retest_session_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_session_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_session_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("session_owner", app)
        self.assertIn("required_field_materials_summary", app)
        self.assertIn("rerun_commands_summary", app)
        self.assertIn("operator_next_steps_summary", app)

        # copy/export 必须由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw 交接包。
        self.assertIn("routeTaskFieldRetestSessionHandoffCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_session_handoff_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestSessionHandoffButton", app)
        self.assertIn("downloadRouteTaskFieldRetestSessionHandoffButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestSessionHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 session handoff 的 software proof / not_proven 边界。
        handoff = fixture["route_task_field_retest_session_handoff"]
        self.assertEqual(handoff["handoff_status"], "ready_for_field_retest_session_handoff_not_proven")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_session_handoff_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_session_handoff", doc)
        self.assertIn("路线任务现场复测交接", doc)

    def test_field_retest_session_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_session_handoff"],
            ensure_ascii=False,
        ).lower()

        # session handoff fixture 只能携带白名单摘要，不能带 raw 材料、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)


class RouteTaskFieldRetestResultIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_result_intake_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # result intake 跟在 session handoff 后，只读解释现场结果材料缺口。
        self.assertIn("routeTaskFieldRetestResultIntakeTitle", app)
        self.assertIn("路线任务现场复测结果入口", app)
        self.assertIn("routeTaskFieldRetestSessionHandoffTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-result-intake-panel", styles)
        self.assertIn("route-task-field-retest-result-intake-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultIntakeText", app)
        self.assertIn("routeTaskFieldRetestResultIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestResultIntakeFromStatus", app)
        self.assertIn("route_task_field_retest_result_intake", app)
        self.assertIn("route_task_field_retest_result_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_intake", app)
        self.assertIn("intake_status", app)
        self.assertIn("material_completeness", app)
        self.assertIn("result_materials_summary", app)
        self.assertIn("missing_material_list", app)
        self.assertIn("operator_next_steps_summary", app)

        # copy/export 必须由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw result 包。
        self.assertIn("routeTaskFieldRetestResultIntakeCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_intake_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultIntakeButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 result intake 的 software proof / not_proven 边界。
        result_intake = fixture["route_task_field_retest_result_intake"]
        self.assertEqual(
            result_intake["intake_status"],
            "blocked_missing_route_task_field_retest_result_materials_not_proven",
        )
        self.assertEqual(result_intake["delivery_success"], False)
        self.assertEqual(result_intake["primary_actions_enabled"], False)
        self.assertEqual(
            result_intake["source_review_result_handoff_schema"],
            "trashbot.route_task_field_retest_review_result_handoff_summary.v1",
        )
        self.assertIn("software_proof_docker_route_task_field_retest_result_intake_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_intake", doc)
        self.assertIn("路线任务现场复测结果入口", doc)

    def test_field_retest_result_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result_intake_text = json.dumps(
            fixture["route_task_field_retest_result_intake"],
            ensure_ascii=False,
        ).lower()

        # result intake fixture 只能携带白名单摘要，不能带 raw result、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw result",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, result_intake_text)

    def test_field_retest_result_reconciliation_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # result reconciliation 跟在 result intake 后，只读解释同一 evidence_ref 的复账结论。
        self.assertIn("routeTaskFieldRetestResultReconciliationTitle", app)
        self.assertIn("路线任务现场结果复账", app)
        self.assertIn("routeTaskFieldRetestResultIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-result-reconciliation-panel", styles)
        self.assertIn("route-task-field-retest-result-reconciliation-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultReconciliationText", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationCandidate", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationFromStatus", app)
        self.assertIn("route_task_field_retest_result_reconciliation", app)
        self.assertIn("route_task_field_retest_result_reconciliation_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_reconciliation_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_reconciliation", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_reconciliation", app)
        self.assertIn("reconciliation_verdict", app)
        self.assertIn("source_lineage_chain", app)
        self.assertIn("source_result_intake_schema", app)
        self.assertIn("source_result_intake_status", app)
        self.assertIn("source_review_result_handoff_schema", app)
        self.assertIn("source_review_result_handoff_status", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationLineage", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationSourceIntake", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationSourceHandoff", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("result_materials_status", app)
        self.assertIn("missing_material_list", app)
        self.assertIn("mismatch_reasons_summary", app)
        self.assertIn("operator_next_steps_summary", app)

        # copy/export 必须由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw 复账包。
        self.assertIn("routeTaskFieldRetestResultReconciliationCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_reconciliation_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultReconciliationButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultReconciliationButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultReconciliation.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 result reconciliation 的 software proof / not_proven 边界。
        reconciliation = fixture["route_task_field_retest_result_reconciliation"]
        self.assertEqual(
            reconciliation["reconciliation_verdict"],
            "blocked_missing_route_task_field_retest_result_reconciliation_materials_not_proven",
        )
        self.assertEqual(
            reconciliation["source_result_intake_schema"],
            "trashbot.route_task_field_retest_result_intake_summary.v1",
        )
        self.assertEqual(
            reconciliation["source_review_result_handoff_schema"],
            "trashbot.route_task_field_retest_review_result_handoff_summary.v1",
        )
        self.assertIn("source_review_result_handoff -> source_result_intake", reconciliation["source_lineage_chain"])
        self.assertEqual(reconciliation["delivery_success"], False)
        self.assertEqual(reconciliation["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_reconciliation_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_reconciliation", doc)
        self.assertIn("路线任务现场结果复账", doc)

    def test_field_retest_result_reconciliation_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        reconciliation_text = json.dumps(
            fixture["route_task_field_retest_result_reconciliation"],
            ensure_ascii=False,
        ).lower()

        # result reconciliation fixture 只能携带白名单摘要，不能带 raw 复账、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw result",
            "raw reconciliation",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, reconciliation_text)

    def test_field_retest_result_acceptance_packet_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # acceptance packet 跟在 result reconciliation 后，只读解释验收准备材料和后续重跑口径。
        self.assertIn("routeTaskFieldRetestResultAcceptancePacketTitle", app)
        self.assertIn("路线任务结果验收包", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultAcceptancePacketText", app)
        self.assertIn("routeTaskFieldRetestResultAcceptancePacketCandidate", app)
        self.assertIn("routeTaskFieldRetestResultAcceptancePacketFromStatus", app)
        self.assertIn("route_task_field_retest_result_acceptance_packet", app)
        self.assertIn("route_task_field_retest_result_acceptance_packet_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_acceptance_packet_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_acceptance_packet", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_acceptance_packet", app)
        self.assertIn("packet_status", app)
        self.assertIn("safe_lineage", app)
        self.assertIn("result_materials_summary", app)
        self.assertIn("missing_items_summary", app)
        self.assertIn("owner_handoff_summary", app)
        self.assertIn("rerun_commands_summary", app)
        self.assertIn("pass_fail_criteria_summary", app)

        # copy/export 必须由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成验收包。
        self.assertIn("routeTaskFieldRetestResultAcceptancePacketCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_acceptance_packet_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultAcceptancePacketButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultAcceptancePacketButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultAcceptancePacket.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 acceptance packet 的 software proof / not_proven 边界。
        packet = fixture["route_task_field_retest_result_acceptance_packet"]
        self.assertEqual(
            packet["packet_status"],
            "blocked_missing_route_task_field_retest_result_acceptance_packet_not_proven",
        )
        self.assertEqual(
            packet["source_reconciliation_schema"],
            "trashbot.route_task_field_retest_result_reconciliation_summary.v1",
        )
        self.assertIn("route_task_field_retest_result_reconciliation -> route_task_field_retest_result_acceptance_packet", packet["safe_lineage"])
        self.assertEqual(packet["delivery_success"], False)
        self.assertEqual(packet["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_acceptance_packet_gate", fixture_text)
        self.assertIn("pass/fail criteria", fixture_text)
        self.assertIn("rerun commands", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_acceptance_packet", doc)
        self.assertIn("路线任务结果验收包", doc)

    def test_field_retest_result_acceptance_packet_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        packet_text = json.dumps(
            fixture["route_task_field_retest_result_acceptance_packet"],
            ensure_ascii=False,
        ).lower()

        # acceptance packet fixture 只能携带白名单摘要，不能带底层控制、凭证、原始材料或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw acceptance packet",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, packet_text)

    def test_field_retest_result_acceptance_backfill_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # acceptance backfill 跟在 acceptance packet 后，只读解释回填状态和同一 evidence_ref 对齐。
        self.assertIn("routeTaskFieldRetestResultAcceptanceBackfillTitle", app)
        self.assertIn("路线任务结果回填", app)
        self.assertIn("routeTaskFieldRetestResultAcceptancePacketTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultAcceptanceBackfillText", app)
        self.assertIn("routeTaskFieldRetestResultAcceptanceBackfillCandidate", app)
        self.assertIn("routeTaskFieldRetestResultAcceptanceBackfillFromStatus", app)
        self.assertIn("route_task_field_retest_result_acceptance_backfill", app)
        self.assertIn("route_task_field_retest_result_acceptance_backfill_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_acceptance_backfill_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_acceptance_backfill", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_acceptance_backfill", app)
        self.assertIn("backfill_status", app)
        self.assertIn("source_packet_status", app)
        self.assertIn("material_completeness", app)
        self.assertIn("same_evidence_ref_alignment", app)
        self.assertIn("missing_material_categories", app)
        self.assertIn("rejected_material_categories", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("rerun_commands", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单 metadata，不触发主操作。
        self.assertIn("routeTaskFieldRetestResultAcceptanceBackfillCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_acceptance_backfill_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultAcceptanceBackfillButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultAcceptanceBackfillButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultAcceptanceBackfill.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 backfill 的 software proof / not_proven 边界。
        backfill = fixture["route_task_field_retest_result_acceptance_backfill"]
        self.assertEqual(
            backfill["backfill_status"],
            "blocked_missing_route_task_field_retest_result_acceptance_backfill_not_proven",
        )
        self.assertEqual(
            backfill["source_packet_schema"],
            "trashbot.route_task_field_retest_result_acceptance_packet_summary.v1",
        )
        self.assertEqual(backfill["delivery_success"], False)
        self.assertEqual(backfill["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate", fixture_text)
        self.assertIn("material completeness", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_acceptance_backfill", doc)
        self.assertIn("路线任务结果回填", doc)

    def test_field_retest_result_acceptance_backfill_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        backfill_text = json.dumps(
            fixture["route_task_field_retest_result_acceptance_backfill"],
            ensure_ascii=False,
        ).lower()

        # backfill fixture 只能携带白名单 summary，不能带 raw backfill、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw backfill",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, backfill_text)

    def test_field_retest_result_backfill_review_decision_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 复核决策必须跟在结果回填后，只读展示材料决策，不触发任何主操作或 ACK/cursor。
        self.assertIn("routeTaskFieldRetestResultBackfillReviewDecisionTitle", app)
        self.assertIn("路线任务回填复核决策", app)
        self.assertIn("routeTaskFieldRetestResultAcceptanceBackfillTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultBackfillReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestResultBackfillReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestResultBackfillReviewDecisionFromStatus", app)
        self.assertIn("route_task_field_retest_result_backfill_review_decision", app)
        self.assertIn("route_task_field_retest_result_backfill_review_decision_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_backfill_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_backfill_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_backfill_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("material_status", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_commands", app)

        # copy/export 只能由 safe_copy 驱动，并且导出白名单字段。
        self.assertIn("routeTaskFieldRetestResultBackfillReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_backfill_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultBackfillReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultBackfillReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultBackfillReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestResultBackfillReviewDecisionButton.*fetchJson")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        decision = fixture["route_task_field_retest_result_backfill_review_decision"]
        self.assertEqual(
            decision["review_decision"],
            "blocked_missing_route_task_field_retest_result_backfill_review_decision_not_proven",
        )
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate", fixture_text)
        self.assertIn("accepted_materials", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("rejected_materials", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("rerun_commands", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_backfill_review_decision", doc)
        self.assertIn("路线任务回填复核决策", doc)

    def test_field_retest_result_backfill_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_result_backfill_review_decision"],
            ensure_ascii=False,
        ).lower()

        # 复核决策 fixture 不得包含 raw 材料、底层控制、硬件细节或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw backfill",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_field_retest_result_review_dispatch_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场派发必须跟在回填复核决策后，只读展示 owner 工单和 callback 要求。
        self.assertIn("routeTaskFieldRetestResultReviewDispatchTitle", app)
        self.assertIn("路线任务现场派发", app)
        self.assertIn("routeTaskFieldRetestResultBackfillReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultReviewDispatchText", app)
        self.assertIn("routeTaskFieldRetestResultReviewDispatchCandidate", app)
        self.assertIn("routeTaskFieldRetestResultReviewDispatchFromStatus", app)
        self.assertIn("route_task_field_retest_result_review_dispatch", app)
        self.assertIn("route_task_field_retest_result_review_dispatch_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_review_dispatch_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_review_dispatch", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_review_dispatch", app)
        self.assertIn("dispatch_status", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_work_orders", app)
        self.assertIn("callback_packet_requirements", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("same_evidence_ref_required=true", app)

        # copy/export 只能由 safe_copy 驱动，并且导出白名单字段。
        self.assertIn("routeTaskFieldRetestResultReviewDispatchCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_review_dispatch_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultReviewDispatchButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultReviewDispatchButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultReviewDispatch.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestResultReviewDispatchButton.*fetchJson")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        dispatch = fixture["route_task_field_retest_result_review_dispatch"]
        self.assertEqual(
            dispatch["dispatch_status"],
            "blocked_missing_route_task_field_retest_result_review_dispatch_not_proven",
        )
        self.assertEqual(dispatch["same_evidence_ref_required"], True)
        self.assertEqual(dispatch["delivery_success"], False)
        self.assertEqual(dispatch["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_review_dispatch_gate", fixture_text)
        self.assertIn("accepted_materials", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("rejected_materials", fixture_text)
        self.assertIn("owner_work_orders", fixture_text)
        self.assertIn("callback_packet_requirements", fixture_text)
        self.assertIn("rerun_commands", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_review_dispatch", doc)
        self.assertIn("路线任务现场派发", doc)

    def test_field_retest_result_review_dispatch_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        dispatch_text = json.dumps(
            fixture["route_task_field_retest_result_review_dispatch"],
            ensure_ascii=False,
        ).lower()

        # 现场派发 fixture 不得包含 raw 工单、底层控制、硬件细节或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw work order",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "same_evidence_ref_required\": false",
        ):
            self.assertNotIn(forbidden, dispatch_text)

    def test_field_retest_result_callback_intake_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 回调入口必须紧跟现场派发，只读展示回调更新，不新增控制按钮语义。
        self.assertIn("routeTaskFieldRetestResultCallbackIntakeTitle", app)
        self.assertIn("路线任务回调入口", app)
        self.assertIn("routeTaskFieldRetestResultReviewDispatchTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultCallbackIntakeText", app)
        self.assertIn("routeTaskFieldRetestResultCallbackIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestResultCallbackIntakeFromStatus", app)
        self.assertIn("route_task_field_retest_result_callback_intake", app)
        self.assertIn("route_task_field_retest_result_callback_intake_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_callback_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_callback_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_callback_intake", app)
        self.assertIn("intake_status", app)
        self.assertIn("accepted_updates", app)
        self.assertIn("missing_updates", app)
        self.assertIn("rejected_updates", app)
        self.assertIn("owner_follow_up", app)
        self.assertIn("review_decision_handoff", app)
        self.assertIn("same_evidence_ref_required=true", app)

        # copy/export 只能由 safe_copy 驱动，并且不触发 Start/Confirm/Cancel 或 diagnostics fetch。
        self.assertIn("routeTaskFieldRetestResultCallbackIntakeCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_callback_intake_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultCallbackIntakeButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultCallbackIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestResultCallbackIntakeButton.*fetchJson")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        intake = fixture["route_task_field_retest_result_callback_intake"]
        self.assertEqual(
            intake["intake_status"],
            "blocked_missing_route_task_field_retest_result_callback_intake_not_proven",
        )
        self.assertEqual(intake["same_evidence_ref_required"], True)
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_callback_intake_gate", fixture_text)
        self.assertIn("accepted_updates", fixture_text)
        self.assertIn("missing_updates", fixture_text)
        self.assertIn("rejected_updates", fixture_text)
        self.assertIn("owner_follow_up", fixture_text)
        self.assertIn("review_decision_handoff", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_callback_intake", doc)
        self.assertIn("路线任务回调入口", doc)

    def test_field_retest_result_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["route_task_field_retest_result_callback_intake"],
            ensure_ascii=False,
        ).lower()

        # 回调入口 fixture 不得包含 raw 回调、底层控制、硬件细节或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw update",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "same_evidence_ref_required\": false",
        ):
            self.assertNotIn(forbidden, intake_text)

    def test_field_retest_result_callback_review_decision_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果回调复核决策跟在 result callback intake 后，只读展示下一步，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestResultCallbackReviewDecisionTitle", app)
        self.assertIn("路线任务回调复核决策", app)
        self.assertIn("routeTaskFieldRetestResultCallbackIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultCallbackReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestResultCallbackReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestResultCallbackReviewDecisionFromStatus", app)
        self.assertIn("route_task_field_retest_result_callback_review_decision", app)
        self.assertIn("route_task_field_retest_result_callback_review_decision_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_callback_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_callback_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("material_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("same_evidence_ref_required=true", app)

        # copy/export 只能由 safe_copy 驱动，不合成 raw review，也不触发 Start/Confirm/Cancel。
        self.assertIn("routeTaskFieldRetestResultCallbackReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_callback_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultCallbackReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultCallbackReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("ready_for_result_review", app)
        self.assertIn("needs_material_backfill", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestResultCallbackReviewDecisionButton.*fetchJson")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        decision = fixture["route_task_field_retest_result_callback_review_decision"]
        self.assertEqual(decision["review_decision"], "needs_material_backfill")
        self.assertEqual(decision["same_evidence_ref_required"], True)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_callback_review_decision_gate", fixture_text)
        self.assertIn("material_status", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("safe_evidence_ref", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_callback_review_decision", doc)
        self.assertIn("路线任务回调复核决策", doc)

    def test_field_retest_result_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_result_callback_review_decision"],
            ensure_ascii=False,
        ).lower()

        # 结果回调复核 fixture 只能携带白名单 summary，不能带 raw review、底层控制、硬件细节或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw update",
            "raw review",
            "raw decision",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "same_evidence_ref_required\": false",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_field_retest_result_callback_review_handoff_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果回调复核交接跟在 review decision 后，只读展示 owner 跟进和复跑包，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestResultCallbackReviewHandoffTitle", app)
        self.assertIn("路线任务回调复核交接", app)
        self.assertIn("routeTaskFieldRetestResultCallbackReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultCallbackReviewHandoffText", app)
        self.assertIn("routeTaskFieldRetestResultCallbackReviewHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestResultCallbackReviewHandoffFromStatus", app)
        self.assertIn("route_task_field_retest_result_callback_review_handoff", app)
        self.assertIn("route_task_field_retest_result_callback_review_handoff_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_callback_review_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_callback_review_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("owner_follow_up", app)
        self.assertIn("review_ready_package", app)
        self.assertIn("rerun_package", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("same_evidence_ref_required=true", app)

        # copy/export 只能由 safe_copy 驱动，不合成 raw handoff，也不触发 Start/Confirm/Cancel/ACK/review 请求。
        self.assertIn("routeTaskFieldRetestResultCallbackReviewHandoffCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_callback_review_handoff_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultCallbackReviewHandoffButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultCallbackReviewHandoffButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("ready_for_result_review_handoff", app)
        self.assertIn("needs_owner_follow_up", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultCallbackReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestResultCallbackReviewHandoffButton.*fetchJson")

        # fixture 和产品文档必须固定 software proof / not_proven 边界。
        handoff = fixture["route_task_field_retest_result_callback_review_handoff"]
        self.assertEqual(handoff["handoff_status"], "needs_owner_follow_up")
        self.assertEqual(handoff["same_evidence_ref_required"], True)
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate", fixture_text)
        self.assertIn("review_ready_package", fixture_text)
        self.assertIn("rerun_package", fixture_text)
        self.assertIn("owner_follow_up", fixture_text)
        self.assertIn("safe_evidence_ref", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_result_callback_review_handoff", doc)
        self.assertIn("路线任务回调复核交接", doc)

    def test_field_retest_result_callback_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_result_callback_review_handoff"],
            ensure_ascii=False,
        ).lower()

        # 结果回调复核交接 fixture 只能携带白名单 summary，不能带 raw handoff、底层控制、硬件细节或成功宣称。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw update",
            "raw review",
            "raw decision",
            "raw handoff",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "same_evidence_ref_required\": false",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_field_retest_material_pack_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # material pack 跟在 result reconciliation 后，只读解释现场材料包完整性和同一 evidence_ref。
        self.assertIn("routeTaskFieldRetestMaterialPackTitle", app)
        self.assertIn("路线/电梯现场材料包", app)
        self.assertIn("routeTaskFieldRetestResultReconciliationTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-material-pack-panel", styles)
        self.assertIn("route-task-field-retest-material-pack-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestMaterialPackText", app)
        self.assertIn("routeTaskFieldRetestMaterialPackCandidate", app)
        self.assertIn("routeTaskFieldRetestMaterialPackFromStatus", app)
        self.assertIn("route_task_field_retest_material_pack", app)
        self.assertIn("route_task_field_retest_material_pack_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_material_pack_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_material_pack", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_material_pack", app)
        self.assertIn("material_completeness", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("material_status_summary", app)
        self.assertIn("missing_material_list", app)
        self.assertIn("rejected_material_list", app)
        self.assertIn("field_capture_checklist", app)
        self.assertIn("callback_payload_skeleton", app)
        self.assertIn("owner_work_orders", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("operator_next_steps_summary", app)

        # copy/export 必须由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw 材料包。
        self.assertIn("routeTaskFieldRetestMaterialPackCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_material_pack_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestMaterialPackButton", app)
        self.assertIn("downloadRouteTaskFieldRetestMaterialPackButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestMaterialPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 material pack 的 software proof / not_proven 边界。
        material_pack = fixture["route_task_field_retest_material_pack"]
        self.assertEqual(
            material_pack["material_pack_status"],
            "blocked_missing_route_task_field_retest_material_pack_not_proven",
        )
        self.assertEqual(material_pack["pack_status"], material_pack["material_pack_status"])
        self.assertEqual(material_pack["delivery_success"], False)
        self.assertEqual(material_pack["primary_actions_enabled"], False)
        self.assertIn("field_capture_checklist", material_pack)
        self.assertIn("callback_payload_skeleton", material_pack)
        self.assertIn("owner_work_orders", material_pack)
        self.assertIn("rerun_commands", material_pack)
        self.assertIn("software_proof_docker_route_task_field_retest_material_pack_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_material_pack", doc)
        self.assertIn("路线/电梯现场材料包", doc)

    def test_field_retest_material_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        material_pack_text = json.dumps(
            fixture["route_task_field_retest_material_pack"],
            ensure_ascii=False,
        ).lower()

        # material pack fixture 只能携带白名单摘要，不能带 raw 材料包、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw material pack",
            "full material pack",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, material_pack_text)

    def test_field_retest_material_callback_packet_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # material callback packet 跟在 material pack 后，只读解释现场回执，不新增任何控制入口。
        self.assertIn("routeTaskFieldRetestMaterialCallbackPacketTitle", app)
        self.assertIn("路线/电梯现场材料回执", app)
        self.assertIn("routeTaskFieldRetestMaterialPackTitle", app)
        self.assertIn("routeTaskFieldRetestOperatorDrillTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestMaterialCallbackPacketText", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackPacketCandidate", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackPacketFromStatus", app)
        self.assertIn("route_task_field_retest_material_callback_packet", app)
        self.assertIn("route_task_field_retest_material_callback_packet_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_material_callback_packet_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_material_callback_packet", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_material_callback_packet", app)
        self.assertIn("callback_packet_status", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_acknowledgement", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_commands", app)

        # copy/export 只能由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw callback packet。
        self.assertIn("routeTaskFieldRetestMaterialCallbackPacketCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_material_callback_packet_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestMaterialCallbackPacketButton", app)
        self.assertIn("downloadRouteTaskFieldRetestMaterialCallbackPacketButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestMaterialCallbackPacket.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestMaterialCallbackPacketButton.*fetchJson")

        # fixture 和产品文档必须固定 callback packet 的 software proof / not_proven 边界。
        packet = fixture["route_task_field_retest_material_callback_packet"]
        self.assertEqual(
            packet["callback_packet_status"],
            "blocked_missing_route_task_field_retest_material_callback_packet_not_proven",
        )
        self.assertEqual(packet["delivery_success"], False)
        self.assertEqual(packet["primary_actions_enabled"], False)
        self.assertIn("accepted_materials", packet)
        self.assertIn("missing_materials", packet)
        self.assertIn("rejected_materials", packet)
        self.assertIn("owner_acknowledgement", packet)
        self.assertIn("next_required_evidence", packet)
        self.assertIn("rerun_commands", packet)
        self.assertIn("software_proof_docker_route_task_field_retest_material_callback_packet_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_material_callback_packet", doc)
        self.assertIn("路线/电梯现场材料回执", doc)

    def test_field_retest_material_callback_packet_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        packet_text = json.dumps(
            fixture["route_task_field_retest_material_callback_packet"],
            ensure_ascii=False,
        ).lower()

        # callback packet fixture 只能携带白名单摘要，不能带 raw 回执、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw callback packet",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, packet_text)

    def test_field_retest_material_callback_review_decision_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # material callback review decision 跟在材料回执后，只读展示复核决策，不新增控制按钮语义。
        self.assertIn("routeTaskFieldRetestMaterialCallbackReviewDecisionTitle", app)
        self.assertIn("现场材料回执复核决策", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackPacketTitle", app)
        self.assertIn("routeTaskFieldRetestOperatorDrillTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestMaterialCallbackReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackReviewDecisionFromStatus", app)
        self.assertIn("route_task_field_retest_material_callback_review_decision", app)
        self.assertIn("route_task_field_retest_material_callback_review_decision_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_material_callback_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_material_callback_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("material_callback_review_summary", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_acknowledgement", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_commands", app)

        # copy/export 只能由 safe_copy 驱动；缺失时显示 blocked copy unavailable，不合成 raw review。
        self.assertIn("routeTaskFieldRetestMaterialCallbackReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_material_callback_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestMaterialCallbackReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestMaterialCallbackReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestMaterialCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestMaterialCallbackReviewDecisionButton.*fetchJson")

        # fixture 和产品文档必须固定 review decision 的 software proof / not_proven 边界。
        decision = fixture["route_task_field_retest_material_callback_review_decision"]
        self.assertEqual(
            decision["review_decision"],
            "needs_material_callback_backfill_not_proven",
        )
        self.assertEqual(decision["same_evidence_ref_required"], True)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("accepted_materials", decision)
        self.assertIn("missing_materials", decision)
        self.assertIn("rejected_materials", decision)
        self.assertIn("owner_acknowledgement", decision)
        self.assertIn("next_required_evidence", decision)
        self.assertIn("rerun_commands", decision)
        self.assertIn("software_proof_docker_route_task_field_retest_material_callback_review_decision_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_material_callback_review_decision", doc)
        self.assertIn("现场材料回执复核决策", doc)

    def test_field_retest_material_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_material_callback_review_decision"],
            ensure_ascii=False,
        ).lower()

        # material callback review decision fixture 只能携带白名单摘要，不能带 raw 复核、控制授权或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "现场已通过",
            "真实手机已验收",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "same_evidence_ref_required\": false",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_field_retest_operator_drill_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # operator drill 跟在 material callback review decision 后，只读解释下一步命令标签和现场 callback checklist。
        self.assertIn("routeTaskFieldRetestOperatorDrillTitle", app)
        self.assertIn("现场操作演练", app)
        self.assertIn("routeTaskFieldRetestMaterialCallbackReviewDecisionTitle", app)
        self.assertIn("routeTaskFieldRetestMaterialPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-operator-drill-panel", styles)
        self.assertIn("route-task-field-retest-operator-drill-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestOperatorDrillText", app)
        self.assertIn("routeTaskFieldRetestOperatorDrillCandidate", app)
        self.assertIn("routeTaskFieldRetestOperatorDrillFromStatus", app)
        self.assertIn("route_task_field_retest_operator_drill", app)
        self.assertIn("route_task_field_retest_operator_drill_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_operator_drill_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_operator_drill", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_operator_drill", app)
        self.assertIn("drill_status", app)
        self.assertIn("source_schema", app)
        self.assertIn("next_operator_commands", app)
        self.assertIn("required_outputs", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("operator_callback_checklist", app)
        self.assertIn("Callback Checklist", app)

        # copy/export 必须由 safe_copy 驱动；缺失时不合成 raw drill 或真实命令。
        self.assertIn("routeTaskFieldRetestOperatorDrillCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_operator_drill_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestOperatorDrillButton", app)
        self.assertIn("downloadRouteTaskFieldRetestOperatorDrillButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestOperatorDrill.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 operator drill 的 software proof / not_proven 边界。
        operator_drill = fixture["route_task_field_retest_operator_drill"]
        self.assertEqual(
            operator_drill["operator_drill_status"],
            "needs_material_callback_backfill_before_operator_drill_not_proven",
        )
        self.assertEqual(
            operator_drill["source_schema"],
            "trashbot.route_task_field_retest_material_callback_review_decision_summary.v1",
        )
        self.assertEqual(operator_drill["delivery_success"], False)
        self.assertEqual(operator_drill["primary_actions_enabled"], False)
        self.assertIn("next_operator_commands", operator_drill)
        self.assertIn("callback_checklist", operator_drill)
        self.assertIn("required_outputs", operator_drill)
        self.assertIn("rerun_commands", operator_drill)
        self.assertIn("software_proof_docker_route_task_field_retest_operator_drill_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_operator_drill", doc)
        self.assertIn("现场操作演练", doc)

    def test_field_retest_operator_drill_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        operator_drill_text = json.dumps(
            fixture["route_task_field_retest_operator_drill"],
            ensure_ascii=False,
        ).lower()

        # operator drill fixture 只能携带命令标签和 checklist，不能带 raw drill、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw operator drill",
            "raw drill",
            "full drill",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, operator_drill_text)

    def test_field_retest_drill_console_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # drill console 跟在 operator drill 后，只读解释复测演练状态，不新增控制按钮语义。
        self.assertIn("routeTaskFieldRetestDrillConsoleTitle", app)
        self.assertIn("现场复测演练控制台", app)
        self.assertIn("routeTaskFieldRetestOperatorDrillTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-drill-console-panel", styles)
        self.assertIn("route-task-field-retest-drill-console-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestDrillConsoleText", app)
        self.assertIn("routeTaskFieldRetestDrillConsoleCandidate", app)
        self.assertIn("routeTaskFieldRetestDrillConsoleFromStatus", app)
        self.assertIn("route_task_field_retest_drill_console", app)
        self.assertIn("route_task_field_retest_drill_console_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_drill_console_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_drill_console", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_drill_console", app)
        self.assertIn("console_status", app)
        self.assertIn("safe_checklist", app)
        self.assertIn("command_labels", app)
        self.assertIn("operator_command_groups", app)
        self.assertIn("missing_material_prompts", app)
        self.assertIn("operator_callback_checklist", app)
        self.assertIn("required_outputs", app)
        self.assertIn("rerun_summary", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作 endpoint。
        self.assertIn("routeTaskFieldRetestDrillConsoleCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_drill_console_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestDrillConsoleButton", app)
        self.assertIn("downloadRouteTaskFieldRetestDrillConsoleButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestDrillConsole.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 drill console 的 software proof / not_proven 边界。
        drill_console = fixture["route_task_field_retest_drill_console"]
        self.assertEqual(
            drill_console["console_status"],
            "blocked_missing_route_task_field_retest_drill_console_not_proven",
        )
        self.assertEqual(drill_console["delivery_success"], False)
        self.assertEqual(drill_console["primary_actions_enabled"], False)
        self.assertIn("operator_command_groups", drill_console)
        self.assertIn("required_outputs", drill_console)
        self.assertIn("rerun_summary", drill_console)
        self.assertIn("software_proof_docker_route_task_field_retest_drill_console_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_drill_console", doc)
        self.assertIn("现场复测演练控制台", doc)

    def test_field_retest_drill_console_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        drill_console_text = json.dumps(
            fixture["route_task_field_retest_drill_console"],
            ensure_ascii=False,
        ).lower()

        # drill console fixture 只能携带白名单 summary，不能带 raw artifact、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw drill console",
            "raw console",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, drill_console_text)

    def test_field_retest_acceptance_brief_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # acceptance brief 跟在 drill console 后，只读解释验收简报，不新增控制按钮语义。
        self.assertIn("routeTaskFieldRetestAcceptanceBriefTitle", app)
        self.assertIn("现场复测验收简报", app)
        self.assertIn("routeTaskFieldRetestDrillConsoleTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-brief-panel", styles)
        self.assertIn("route-task-field-retest-acceptance-brief-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceBriefText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceBriefCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceBriefFromStatus", app)
        self.assertIn("route_task_field_retest_acceptance_brief", app)
        self.assertIn("route_task_field_retest_acceptance_brief_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_brief_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_brief", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_brief", app)
        self.assertIn("acceptance_status", app)
        self.assertIn("pass_fail_criteria", app)
        self.assertIn("required_evidence_packet", app)
        self.assertIn("owner_handoff", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作 endpoint。
        self.assertIn("routeTaskFieldRetestAcceptanceBriefCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_acceptance_brief_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestAcceptanceBriefButton", app)
        self.assertIn("downloadRouteTaskFieldRetestAcceptanceBriefButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestAcceptanceBrief.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 acceptance brief 的 software proof / not_proven 边界。
        acceptance_brief = fixture["route_task_field_retest_acceptance_brief"]
        robot_alias = fixture["robot_diagnostics_route_task_field_retest_acceptance_brief_summary"]
        self.assertEqual(
            acceptance_brief["acceptance_status"],
            "blocked_missing_route_task_field_retest_acceptance_brief_not_proven",
        )
        self.assertEqual(
            robot_alias["acceptance_status"],
            acceptance_brief["acceptance_status"],
        )
        self.assertEqual(robot_alias["source_alias"], "robot_diagnostics_route_task_field_retest_acceptance_brief_summary")
        self.assertEqual(robot_alias["delivery_success"], False)
        self.assertEqual(robot_alias["primary_actions_enabled"], False)
        self.assertIn("Robot diagnostics acceptance brief summary", robot_alias["safe_phone_copy"])
        self.assertEqual(acceptance_brief["delivery_success"], False)
        self.assertEqual(acceptance_brief["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_acceptance_brief_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_brief_summary", doc)
        self.assertIn("route_task_field_retest_acceptance_brief", doc)
        self.assertIn("现场复测验收简报", doc)

    def test_field_retest_acceptance_brief_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        acceptance_brief_text = json.dumps(
            fixture["route_task_field_retest_acceptance_brief"],
            ensure_ascii=False,
        ).lower()
        robot_alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_brief_summary"],
            ensure_ascii=False,
        ).lower()

        # acceptance brief fixture 只能携带白名单 summary，不能带 raw artifact、底层控制、凭证或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw acceptance",
            "raw brief",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, acceptance_brief_text)
            self.assertNotIn(forbidden, robot_alias_text)

    def test_field_retest_evidence_dispatch_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # dispatch panel 跟在 acceptance brief 后，只读解释现场证据包派发，不新增控制按钮语义。
        self.assertIn("routeTaskFieldRetestEvidenceDispatchTitle", app)
        self.assertIn("现场证据包派发", app)
        self.assertIn("routeTaskFieldRetestAcceptanceBriefTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-evidence-dispatch-panel", styles)
        self.assertIn("route-task-field-retest-evidence-dispatch-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestEvidenceDispatchText", app)
        self.assertIn("routeTaskFieldRetestEvidenceDispatchCandidate", app)
        self.assertIn("routeTaskFieldRetestEvidenceDispatchFromStatus", app)
        self.assertIn("route_task_field_retest_evidence_dispatch", app)
        self.assertIn("route_task_field_retest_evidence_dispatch_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_evidence_dispatch_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_evidence_dispatch", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_evidence_dispatch", app)
        self.assertIn("dispatch_status", app)
        self.assertIn("material_owners", app)
        self.assertIn("recommended_filenames", app)
        self.assertIn("backfill_order", app)
        self.assertIn("callback_checklist", app)
        self.assertIn("fail_closed_rerun_notes", app)
        self.assertIn("required_evidence_packet", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作 endpoint。
        self.assertIn("routeTaskFieldRetestEvidenceDispatchCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_evidence_dispatch_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestEvidenceDispatchButton", app)
        self.assertIn("downloadRouteTaskFieldRetestEvidenceDispatchButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestEvidenceDispatch.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 evidence dispatch 的 software proof / not_proven 边界。
        dispatch = fixture["route_task_field_retest_evidence_dispatch"]
        self.assertEqual(
            dispatch["dispatch_status"],
            "blocked_missing_route_task_field_retest_evidence_dispatch_not_proven",
        )
        self.assertEqual(dispatch["delivery_success"], False)
        self.assertEqual(dispatch["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_evidence_dispatch_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_evidence_dispatch", doc)
        self.assertIn("现场证据包派发", doc)

    def test_field_retest_evidence_dispatch_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        dispatch_text = json.dumps(
            fixture["route_task_field_retest_evidence_dispatch"],
            ensure_ascii=False,
        ).lower()

        # dispatch fixture 只能携带白名单 summary，不能带 raw artifact、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw dispatch",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, dispatch_text)


class RouteTaskFieldRetestCallbackIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_callback_intake_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # callback intake 跟在 evidence dispatch 后，只读解释现场回执，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestCallbackIntakeTitle", app)
        self.assertIn("现场回执入口", app)
        self.assertIn("routeTaskFieldRetestEvidenceDispatchTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-callback-intake-panel", styles)
        self.assertIn("route-task-field-retest-callback-intake-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestCallbackIntakeText", app)
        self.assertIn("routeTaskFieldRetestCallbackIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestCallbackIntakeFromStatus", app)
        self.assertIn("route_task_field_retest_callback_intake", app)
        self.assertIn("route_task_field_retest_callback_intake_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_callback_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_callback_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_callback_intake", app)
        self.assertIn("received_filenames_summary", app)
        self.assertIn("missing_materials", app)
        self.assertIn("same_evidence_ref_match", app)
        self.assertIn("next_backfill_action", app)
        self.assertIn("callback_checklist_result", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作 endpoint。
        self.assertIn("routeTaskFieldRetestCallbackIntakeCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_callback_intake_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestCallbackIntakeButton", app)
        self.assertIn("downloadRouteTaskFieldRetestCallbackIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 callback intake 的 software proof / not_proven 边界。
        callback = fixture["route_task_field_retest_callback_intake"]
        self.assertEqual(
            callback["intake_status"],
            "blocked_missing_route_task_field_retest_callback_intake_materials_not_proven",
        )
        self.assertEqual(callback["delivery_success"], False)
        self.assertEqual(callback["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_callback_intake_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_callback_intake", doc)
        self.assertIn("现场回执入口", doc)

    def test_field_retest_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        callback_text = json.dumps(
            fixture["route_task_field_retest_callback_intake"],
            ensure_ascii=False,
        ).lower()

        # callback intake fixture 只能携带白名单 summary，不能带 raw artifact、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw callback",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, callback_text)


class RouteTaskFieldRetestCallbackReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_callback_review_decision_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # review decision 跟在 callback intake 后，只读解释下一步，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestCallbackReviewDecisionTitle", app)
        self.assertIn("现场回执复核决策", app)
        self.assertIn("routeTaskFieldRetestCallbackIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-callback-review-decision-panel", styles)
        self.assertIn("route-task-field-retest-callback-review-decision-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestCallbackReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestCallbackReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestCallbackReviewDecisionFromStatus", app)
        self.assertIn("route_task_field_retest_callback_review_decision", app)
        self.assertIn("route_task_field_retest_callback_review_decision_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_callback_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_callback_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_callback_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("source_intake_status", app)
        self.assertIn("missing_backfill_summary", app)
        self.assertIn("same_evidence_ref_verdict", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("result_intake_readiness", app)
        self.assertIn("owner_handoff", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作或 result-intake 请求。
        self.assertIn("routeTaskFieldRetestCallbackReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_callback_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestCallbackReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestCallbackReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertIn("ready_for_result_intake", app)
        self.assertIn("needs_material_backfill", app)
        self.assertIn("evidence_ref_mismatch_rerun", app)
        self.assertIn("unsupported_callback_schema", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 review decision 的 software proof / not_proven 边界。
        decision = fixture["route_task_field_retest_callback_review_decision"]
        self.assertEqual(decision["review_decision"], "needs_material_backfill")
        self.assertEqual(decision["result_intake_readiness"].startswith("ready_for_result_intake=false"), True)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_callback_review_decision_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("route_task_field_retest_callback_review_decision", doc)
        self.assertIn("现场回执复核决策", doc)

    def test_field_retest_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_callback_review_decision"],
            ensure_ascii=False,
        ).lower()

        # review decision fixture 只能携带白名单 summary，不能带 raw review、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw callback",
            "raw review",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)


class RouteTaskFieldRetestReviewResultHandoffMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_review_result_handoff_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果交接跟在 review decision 后，只读解释 owner 分工，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestReviewResultHandoffTitle", app)
        self.assertIn("现场复测结果交接", app)
        self.assertIn("routeTaskFieldRetestCallbackReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-review-result-handoff-panel", styles)
        self.assertIn("route-task-field-retest-review-result-handoff-grid", styles)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestReviewResultHandoffText", app)
        self.assertIn("routeTaskFieldRetestReviewResultHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestReviewResultHandoffFromStatus", app)
        self.assertIn("route_task_field_retest_review_result_handoff", app)
        self.assertIn("route_task_field_retest_review_result_handoff_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_review_result_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_review_result_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_review_result_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("source_review_decision", app)
        self.assertIn("result_intake_readiness", app)
        self.assertIn("required_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("blocked_reasons", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作、ACK、cursor 或 result-intake 请求。
        self.assertIn("routeTaskFieldRetestReviewResultHandoffCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_review_result_handoff_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestReviewResultHandoffButton", app)
        self.assertIn("downloadRouteTaskFieldRetestReviewResultHandoffButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestReviewResultHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 handoff 的 software proof / not_proven 边界。
        handoff = fixture["route_task_field_retest_review_result_handoff"]
        self.assertEqual(handoff["handoff_status"], "blocked_waiting_result_intake_materials")
        self.assertEqual(handoff["source_review_decision"], "needs_material_backfill")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_review_result_handoff_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_review_result_handoff", doc)
        self.assertIn("现场复测结果交接", doc)

    def test_field_retest_review_result_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_review_result_handoff"],
            ensure_ascii=False,
        ).lower()

        # handoff fixture 只能携带白名单 summary，不能带 raw handoff、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw callback",
            "raw review",
            "raw handoff",
            "raw robot response",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)


class RouteTaskFieldRetestResultReviewIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_result_review_intake_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果复核入口跟在 handoff 后，只读解释材料入口，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestResultReviewIntakeTitle", app)
        self.assertIn("路线/电梯结果复核入口", app)
        self.assertIn("routeTaskFieldRetestReviewResultHandoffTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-result-review-intake-panel", app)
        self.assertIn("route-task-field-retest-result-review-intake-grid", app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics compatible summary。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultReviewIntakeText", app)
        self.assertIn("routeTaskFieldRetestResultReviewIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestResultReviewIntakeFromStatus", app)
        self.assertIn("route_task_field_retest_result_review_intake", app)
        self.assertIn("route_task_field_retest_result_review_intake_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_review_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_review_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_review_intake", app)
        self.assertIn("intake_status", app)
        self.assertIn("missing_materials", app)
        self.assertIn("owner_follow_up", app)
        self.assertIn("review_ready_package", app)
        self.assertIn("rerun_package", app)
        self.assertIn("next_required_evidence", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作、ACK、cursor、diagnostics fetch 或 robot command。
        self.assertIn("routeTaskFieldRetestResultReviewIntakeCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_review_intake_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultReviewIntakeButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultReviewIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultReviewIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 result review intake 的 software proof / not_proven 边界。
        intake = fixture["route_task_field_retest_result_review_intake"]
        self.assertEqual(
            intake["intake_status"],
            "blocked_missing_route_task_field_retest_result_review_intake_not_proven",
        )
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_review_intake_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_result_review_intake", doc)
        self.assertIn("路线/电梯结果复核入口", doc)

    def test_field_retest_result_review_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["route_task_field_retest_result_review_intake"],
            ensure_ascii=False,
        ).lower()

        # result review intake fixture 只能携带白名单 summary，不能带 raw intake、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw intake",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)


class RouteTaskFieldRetestAcceptanceReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_review_decision_panel_is_read_only_and_alias_first(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 验收复核决策跟在 acceptance brief 后，只读消费 Robot safe alias，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestAcceptanceReviewDecisionTitle", app)
        self.assertIn("现场复测验收复核决策", app)
        self.assertIn("routeTaskFieldRetestAcceptanceBriefTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-review-decision-panel", app)
        self.assertIn("route-task-field-retest-acceptance-review-decision-grid", app)

        # Robot diagnostics safe alias 必须在候选列表里早于普通 artifact/summary，保持 Robot 摘要优先。
        alias_index = app.index("status?.robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary")
        artifact_index = app.index("status?.route_task_field_retest_acceptance_review_decision")
        self.assertLess(alias_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceReviewDecisionFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("material_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("boundary_flags", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发 Start/Confirm/Cancel。
        self.assertIn("routeTaskFieldRetestAcceptanceReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_acceptance_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestAcceptanceReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestAcceptanceReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestAcceptanceReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # 两套 fixture 和产品文档都必须固定 software proof / not_proven / safe alias 口径。
        decision = fixture["route_task_field_retest_acceptance_review_decision"]
        self.assertEqual(
            decision["review_decision"],
            "blocked_missing_acceptance_review_materials_not_proven",
        )
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary",
            web_fixture,
        )
        self.assertIn("software_proof_docker_route_task_field_retest_acceptance_review_decision_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_review_decision", doc)
        self.assertIn("现场复测验收复核决策", doc)

    def test_field_retest_acceptance_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_acceptance_review_decision"],
            ensure_ascii=False,
        ).lower()

        # acceptance review decision fixture 只能携带白名单 metadata，不能泄漏 raw decision、路径、凭证或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw decision",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)


class RouteTaskFieldRetestAcceptanceExecutionPackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_pack_panel_is_read_only_and_alias_first(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 验收执行包跟在 review decision 后，只读消费 Robot safe alias，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionPackTitle", app)
        self.assertIn("现场复测验收执行包", app)
        self.assertIn("routeTaskFieldRetestAcceptanceReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-pack-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-pack-grid", app)

        # Robot diagnostics safe alias 必须在候选列表里早于 summary/artifact，保持 Robot 摘要优先。
        alias_index = app.index("status?.robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary")
        summary_index = app.index("status?.route_task_field_retest_acceptance_execution_pack_summary")
        artifact_index = app.index("status?.route_task_field_retest_acceptance_execution_pack,")
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionPackText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionPackCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionPackFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_pack", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_pack", app)
        self.assertIn("owner_checklist", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("safe_evidence_bundle", app)
        self.assertIn("required_route_elevator_materials", app)
        self.assertIn("handoff_owner", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("boundary_flags", app)

        # copy/export 必须由 safe_copy 或 safe_evidence_bundle 驱动，只导出白名单字段且不触发主操作。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionPackCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_acceptance_execution_pack_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestAcceptanceExecutionPackButton", app)
        self.assertIn("downloadRouteTaskFieldRetestAcceptanceExecutionPackButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestAcceptanceExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # 两套 fixture 和产品文档都必须固定 execution-pack software proof / not_proven / safe alias 口径。
        pack = fixture["route_task_field_retest_acceptance_execution_pack"]
        self.assertEqual(
            pack["execution_pack_status"],
            "blocked_missing_acceptance_execution_pack_materials_not_proven",
        )
        self.assertEqual(pack["delivery_success"], False)
        self.assertEqual(pack["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary",
            web_fixture,
        )
        self.assertIn("software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_pack", doc)
        self.assertIn("现场复测验收执行包", doc)

    def test_field_retest_acceptance_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        pack_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # acceptance execution pack fixture 只能携带白名单 metadata，不能泄漏 raw pack、路径、凭证或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw execution pack",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, pack_text)


class RouteTaskFieldRetestAcceptanceExecutionCallbackIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_callback_intake_panel_is_read_only_and_alias_first(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 执行回调入口跟在 execution pack 后，只读展示 callback packet intake，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackIntakeTitle", app)
        self.assertIn("现场复测验收执行回调入口", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-intake-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-intake-grid", app)

        # Robot diagnostics safe alias 必须早于普通 summary，再早于 artifact。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_intake_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_intake,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionCallbackIntakeText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_callback_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_callback_intake", app)
        self.assertIn("source_execution_pack", app)
        self.assertIn("callback_packet_status", app)
        self.assertIn("received_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_next_steps", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("boundary_flags", app)

        # copy/export 只能由 safe_copy 解锁，且不触发 Start/Confirm/Cancel 或 diagnostics fetch。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackIntakeCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_acceptance_execution_callback_intake_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestAcceptanceExecutionCallbackIntakeButton", app)
        self.assertIn("downloadRouteTaskFieldRetestAcceptanceExecutionCallbackIntakeButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"routeTaskFieldRetestAcceptanceExecutionCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestAcceptanceExecutionCallbackIntakeButton.*fetchJson")

        # 两套 fixture 和产品文档都固定 execution callback intake 的 software proof / not_proven 口径。
        intake = fixture["route_task_field_retest_acceptance_execution_callback_intake"]
        self.assertEqual(
            intake["intake_status"],
            "blocked_missing_acceptance_execution_callback_intake_not_proven",
        )
        self.assertEqual(intake["same_evidence_ref_required"], True)
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary",
            web_fixture,
        )
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate",
            fixture_text,
        )
        self.assertIn("received_materials", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("rejected_materials", fixture_text)
        self.assertIn("owner_next_steps", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_callback_intake", doc)
        self.assertIn("现场复测验收执行回调入口", doc)

    def test_field_retest_acceptance_execution_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_callback_intake"],
            ensure_ascii=False,
        ).lower()
        robot_alias_text = json.dumps(
            web_fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"],
            ensure_ascii=False,
        ).lower()

        # execution callback intake fixture 只能携带白名单 metadata，不能泄漏 raw callback 或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw callback packet",
            "raw execution pack",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)
            self.assertNotIn(forbidden, robot_alias_text)


class RouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_callback_review_decision_panel_is_read_only_and_alias_first(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)

        # 回执复核决策跟在 execution callback intake 后，只读展示 Robot safe alias，不改变主操作 gating。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionTitle", app)
        self.assertIn("现场回执复核决策", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-review-decision-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-review-decision-grid", app)

        # Robot diagnostics safe alias 必须早于普通 summary，再早于 artifact，避免手机端优先读未复核材料。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_review_decision,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_callback_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_callback_review_decision", app)
        self.assertIn("review_decision", app)
        self.assertIn("source_callback_intake_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_rerun_hint", app)
        self.assertIn("boundary_flags", app)

        # copy/export 只能由 safe_copy 或 safe summary 解锁，不能触发 Start/Confirm/Cancel、diagnostics fetch 或机器人命令。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotRegex(app, r"copyRouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionButton.*fetchJson")

        # 两套 fixture 固定 callback review decision 的 software proof / not_proven 口径。
        decision = fixture["route_task_field_retest_acceptance_execution_callback_review_decision"]
        self.assertEqual(
            decision["review_decision"],
            "blocked_missing_acceptance_execution_callback_review_materials_not_proven",
        )
        self.assertEqual(decision["same_evidence_ref_required"], True)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary",
            web_fixture,
        )
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate",
            fixture_text,
        )
        self.assertIn("source_callback_intake_status", fixture_text)
        self.assertIn("safe_rerun_hint", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)

    def test_field_retest_acceptance_execution_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_callback_review_decision"],
            ensure_ascii=False,
        ).lower()
        robot_alias_text = json.dumps(
            web_fixture[
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
            ],
            ensure_ascii=False,
        ).lower()

        # 回执复核决策 fixture 只能携带白名单 metadata，不能泄漏 raw callback、凭证、控制成功或诊断拉取语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw callback",
            "raw review",
            "raw decision",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)


class RouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_callback_review_handoff_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场复核交接跟在 callback review decision 后，只读展示 handoff metadata。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffTitle", app)
        self.assertIn("现场复核交接", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-review-handoff-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-callback-review-handoff-grid", app)

        # Robot safe alias、主 summary 和主 artifact 三种来源都被支持，且 alias 优先。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_callback_review_handoff,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_callback_review_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_callback_review_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("source_review_decision_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_rerun_hint", app)
        self.assertIn("boundary_flags", app)

        # 该 panel 不提供网络提交、diagnostics fetch、ACK 或 cursor 路径，主按钮 gating 仍由既有逻辑控制。
        handoff_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffPanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            handoff_block,
            r"routeTaskFieldRetestAcceptanceExecutionCallbackReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffButton", app)

        # fixture 和产品文档必须固定 software proof / not_proven / 主操作禁用边界。
        handoff = fixture["route_task_field_retest_acceptance_execution_callback_review_handoff"]
        self.assertEqual(handoff["handoff_status"], "needs_owner_follow_up")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
            fixture,
        )
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("source_review_decision_status", fixture_text)
        self.assertIn("safe_rerun_hint", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_callback_review_handoff", doc)
        self.assertIn("现场复核交接", doc)

    def test_field_retest_acceptance_execution_callback_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_callback_review_handoff"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"],
            ensure_ascii=False,
        ).lower()

        # handoff fixture 只能携带白名单 metadata，不能泄漏 raw handoff、凭证、控制成功或底层链路。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "traceback",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)
            self.assertNotIn(forbidden, alias_text)


class RouteTaskFieldRetestAcceptanceExecutionHandoffIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_handoff_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)

        # 现场交接回执入口跟在现场复核交接后，只读展示 handoff intake metadata。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionHandoffIntakeTitle", app)
        self.assertIn("现场交接回执入口", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-handoff-intake-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-handoff-intake-grid", app)

        # Robot safe alias、主 summary 和主 artifact 三种来源都被支持，且 alias 优先。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_handoff_intake_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_handoff_intake,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionHandoffIntakeText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionHandoffIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionHandoffIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_handoff_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_handoff_intake", app)
        self.assertIn("handoff_intake_status", app)
        self.assertIn("source_handoff_status", app)
        self.assertIn("owner_acknowledgement_state", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_rerun_hint", app)
        self.assertIn("boundary_flags", app)

        # 该 panel 不提交 ACK/cursor/diagnostics fetch/robot command，也不改变 Start/Confirm/Cancel gating。
        intake_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionHandoffIntakePanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            intake_block,
            r"routeTaskFieldRetestAcceptanceExecutionHandoffIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionHandoffIntakeButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionHandoffIntakeButton", app)

        # fixture 必须固定 software proof / not_proven / 主操作禁用边界。
        intake = fixture["route_task_field_retest_acceptance_execution_handoff_intake"]
        self.assertEqual(intake["handoff_intake_status"], "needs_owner_acknowledgement")
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary",
            fixture,
        )
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate",
            fixture_text,
        )
        self.assertIn("source_handoff_status", fixture_text)
        self.assertIn("owner_acknowledgement_state", fixture_text)
        self.assertIn("safe_rerun_hint", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)

    def test_field_retest_acceptance_execution_handoff_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_handoff_intake"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"],
            ensure_ascii=False,
        ).lower()

        # 回执入口 fixture 只能携带白名单 metadata，不能泄漏 raw intake、凭证、ACK 或底层链路。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "complete artifacts",
            "traceback",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)
            self.assertNotIn(forbidden, alias_text)


class RouteTaskFieldRetestAcceptanceExecutionRerunQueueMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_rerun_queue_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 受控复跑队列跟在 handoff intake 后，只读展示队列 metadata。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunQueueTitle", app)
        self.assertIn("受控复跑队列", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionHandoffIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-queue-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-queue-grid", app)

        # Robot worker alias 必须早于主 summary / artifact，避免手机端读取 raw queue。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_queue_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_queue,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionRerunQueueText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunQueueCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunQueueFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_queue", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_queue", app)
        self.assertIn("queue_status", app)
        self.assertIn("source_handoff_status", app)
        self.assertIn("queue_position", app)
        self.assertIn("queue_readiness", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_rerun_hint", app)

        # 该 panel 不提供 copy/export，不 fetch raw artifact，也不触发主操作或 diagnostics 拉取。
        queue_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionRerunQueuePanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(
            queue_block,
            r"routeTaskFieldRetestAcceptanceExecutionRerunQueue.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionRerunQueueButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionRerunQueueButton", app)

        # fixture 和产品文档必须明确 software proof / not_proven / 主操作禁用边界。
        queue = fixture["route_task_field_retest_acceptance_execution_rerun_queue"]
        self.assertEqual(queue["queue_status"], "queued_pending_same_evidence_ref_owner_ack")
        self.assertEqual(queue["delivery_success"], False)
        self.assertEqual(queue["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary",
            fixture,
        )
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate",
            fixture_text,
        )
        self.assertIn("queue_readiness", fixture_text)
        self.assertIn("queue_position", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_rerun_queue", doc)
        self.assertIn("受控复跑队列", doc)

    def test_field_retest_acceptance_execution_rerun_queue_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        queue_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_rerun_queue"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"],
            ensure_ascii=False,
        ).lower()

        # 队列 fixture 只能携带白名单 metadata，不能泄漏 raw artifact、路径、凭证或底层链路。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "local path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover detail",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "complete artifacts",
            "traceback",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, queue_text)
            self.assertNotIn(forbidden, alias_text)


class RouteTaskFieldRetestAcceptanceExecutionRerunResultIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_rerun_result_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果回执入口跟在 rerun queue 后，只读展示结果回执 metadata。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultIntakeTitle", app)
        self.assertIn("受控复跑结果回执入口", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunQueueTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-intake-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-intake-grid", app)

        # Robot sanitized alias 必须先于主 summary / artifact，手机端不读取未脱敏复跑结果。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_intake,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionRerunResultIntakeText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultIntakeCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_intake", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_intake", app)
        self.assertIn("intake_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_evidence_ref", app)

        # 该 panel 不提供 copy/export，不 fetch diagnostics，也不触发 Start/Confirm/Cancel。
        result_intake_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionRerunResultIntakePanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(
            result_intake_block,
            r"routeTaskFieldRetestAcceptanceExecutionRerunResultIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionRerunResultIntakeButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionRerunResultIntakeButton", app)

        # fixture、文档和 focused status literals 覆盖 ready/backfill/mismatch/unsafe/unsupported。
        intake = fixture["route_task_field_retest_acceptance_execution_rerun_result_intake"]
        self.assertEqual(
            intake["intake_status"],
            "ready_for_acceptance_execution_rerun_result_review_not_proven",
        )
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary",
            fixture,
        )
        for literal in (
            "ready_for_acceptance_execution_rerun_result_review_not_proven",
            "needs_acceptance_execution_rerun_result_backfill",
            "evidence_ref_mismatch_rerun_result",
            "blocked_unsafe_rerun_result",
            "blocked_unsupported_rerun_queue",
        ):
            self.assertIn(literal, fixture_text)
            self.assertIn(literal, doc)
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate",
            fixture_text,
        )
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_rerun_result_intake", doc)
        self.assertIn("受控复跑结果回执入口", doc)

    def test_field_retest_acceptance_execution_rerun_result_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_rerun_result_intake"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"],
            ensure_ascii=False,
        ).lower()

        # 复跑结果回执 fixture 只能携带白名单 metadata，不能泄漏路径、凭证、底层控制或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "local path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover detail",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "complete artifacts",
            "traceback",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)
            self.assertNotIn(forbidden, alias_text)


class RouteTaskFieldRetestResultReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_result_review_decision_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果复核决策跟在 intake 后，只读解释 decision，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestResultReviewDecisionTitle", app)
        self.assertIn("路线/电梯结果复核决策", app)
        self.assertIn("routeTaskFieldRetestResultReviewIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-result-review-decision-panel", app)
        self.assertIn("route-task-field-retest-result-review-decision-grid", app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics aliases。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestResultReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestResultReviewDecisionFromStatus", app)
        self.assertIn("route_task_field_retest_result_review_decision", app)
        self.assertIn("route_task_field_retest_result_review_decision_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_review_decision", app)
        self.assertIn("decision_status", app)
        self.assertIn("missing_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_commands", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作、ACK、cursor、diagnostics fetch 或 robot command。
        self.assertIn("routeTaskFieldRetestResultReviewDecisionCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_review_decision_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultReviewDecisionButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultReviewDecisionButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 result review decision 的 software proof / not_proven 边界。
        decision = fixture["route_task_field_retest_result_review_decision"]
        self.assertEqual(
            decision["decision_status"],
            "needs_route_elevator_material_backfill_not_proven",
        )
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_review_decision_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_result_review_decision", doc)
        self.assertIn("路线/电梯结果复核决策", doc)

    def test_field_retest_result_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_result_review_decision"],
            ensure_ascii=False,
        ).lower()

        # result review decision fixture 只能携带白名单 summary，不能带 raw decision、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw decision",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "result route",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_field_retest_result_review_handoff_panel_is_read_only_and_copy_gated(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 结果复核交接跟在 decision 后，只读展示 owner work orders，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestResultReviewHandoffTitle", app)
        self.assertIn("路线/电梯结果复核交接", app)
        self.assertIn("routeTaskFieldRetestResultReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-result-review-handoff-panel", app)
        self.assertIn("route-task-field-retest-result-review-handoff-grid", app)

        # 状态来源兼容 artifact、summary 和 Robot diagnostics aliases。
        self.assertIn("ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestResultReviewHandoffText", app)
        self.assertIn("routeTaskFieldRetestResultReviewHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestResultReviewHandoffFromStatus", app)
        self.assertIn("route_task_field_retest_result_review_handoff", app)
        self.assertIn("route_task_field_retest_result_review_handoff_summary", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_result_review_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_result_review_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_result_review_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("owner_work_orders", app)
        self.assertIn("accepted_reasons", app)
        self.assertIn("blocked_reasons", app)
        self.assertIn("rerun_reasons", app)
        self.assertIn("next_material_callback_requirements", app)
        self.assertIn("rerun_commands", app)

        # copy/export 必须由 safe_copy 驱动，只导出白名单字段，且不触发主操作、ACK、cursor、diagnostics fetch 或 robot command。
        self.assertIn("routeTaskFieldRetestResultReviewHandoffCopyPayload", app)
        self.assertIn("trashbot.route_task_field_retest_result_review_handoff_copy.v1", app)
        self.assertIn("copyRouteTaskFieldRetestResultReviewHandoffButton", app)
        self.assertIn("downloadRouteTaskFieldRetestResultReviewHandoffButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(app, r"routeTaskFieldRetestResultReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须固定 result review handoff 的 software proof / not_proven 边界。
        handoff = fixture["route_task_field_retest_result_review_handoff"]
        self.assertEqual(
            handoff["handoff_status"],
            "needs_result_material_callback_not_proven",
        )
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_route_task_field_retest_result_review_handoff_gate", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_result_review_handoff", doc)
        self.assertIn("路线/电梯结果复核交接", doc)

    def test_field_retest_result_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_result_review_handoff"],
            ensure_ascii=False,
        ).lower()

        # result review handoff fixture 只能携带白名单 summary，不能带 raw handoff、路径、凭证、底层控制或成功状态。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "serial device",
            "uart device",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw handoff",
            "raw diagnostics",
            "raw robot response",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "result route",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)


if __name__ == "__main__":
    unittest.main()
