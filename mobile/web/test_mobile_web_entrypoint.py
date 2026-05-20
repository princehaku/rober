import json
import re
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parent
REPO_ROOT = WEB_ROOT.parent.parent
FIXTURE = WEB_ROOT / "fixtures" / "status.json"
CLOUD_PENDING_ACK_FIXTURE = WEB_ROOT / "fixtures" / "robot_diagnostics_cloud_pending_ack_status_guard.json"
CLOUD_COMMAND_EXPIRY_FIXTURE = WEB_ROOT / "fixtures" / "robot_diagnostics_cloud_command_expiry_safety_guard.json"
CLOUD_COMMAND_IDEMPOTENCY_FIXTURE = (
    WEB_ROOT / "fixtures" / "robot_diagnostics_cloud_command_idempotency_visibility_guard.json"
)
CLOUD_COMMAND_ID_CONFLICT_FIXTURE = (
    WEB_ROOT / "fixtures" / "robot_diagnostics_cloud_command_id_conflict_visibility_guard.json"
)
PR5_VENDOR_SOURCE_REVIEW_PACKET_FIXTURE = (
    WEB_ROOT / "fixtures" / "robot_diagnostics_pr5_vendor_source_review_packet_summary.json"
)
PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_FIXTURE = (
    WEB_ROOT / "fixtures" / "robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json"
)
MOBILE_STATUS_FIXTURE = REPO_ROOT / "mobile" / "fixtures" / "mobile_web_status.fixture.json"
DOC = REPO_ROOT / "docs" / "product" / "mobile_user_flow.md"


class FieldEvidenceRerunMaterialDispatchMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_evidence_rerun_material_dispatch_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场证据复跑材料派发只消费 Robot safe alias 和兼容 summary，不新增控制 endpoint。
        self.assertIn("现场证据复跑材料派发", app)
        self.assertIn("FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_BOUNDARY", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_material_dispatch_summary", app)
        self.assertIn("field_evidence_rerun_material_dispatch_summary", app)
        self.assertIn("software_proof_docker_field_evidence_rerun_material_dispatch_gate", app)
        self.assertIn("safe_to_control=false / delivery_success=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunMaterialDispatch.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 明确材料派发是 not_proven 软件证明，不改变三类主操作 gating。
        summary = fixture["robot_diagnostics_field_evidence_rerun_material_dispatch_summary"]
        self.assertEqual(summary["dispatch_status"], "ready_for_field_owner_material_dispatch_not_proven")
        self.assertEqual(summary["safe_to_control"], False)
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(fixture["can_collect"], False)
        self.assertEqual(fixture["can_confirm_dropoff"], False)
        self.assertEqual(fixture["can_cancel"], False)
        self.assertIn("same_evidence_ref_status=required_not_proven", fixture_text)
        self.assertIn("real phone/browser evidence", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("software_proof_docker_field_evidence_rerun_material_dispatch_gate", fixture_text)
        self.assertEqual(
            mobile_fixture["robot_diagnostics_field_evidence_rerun_material_dispatch_summary"]["safe_to_control"],
            False,
        )

        # 产品文档必须写清它不是现场通过、真实手机/browser、HIL、delivery success 或 O5 external proof。
        self.assertIn("现场证据复跑材料派发", doc)
        self.assertIn("robot_diagnostics_field_evidence_rerun_material_dispatch_summary", doc)
        self.assertIn("software_proof_docker_field_evidence_rerun_material_dispatch_gate", doc)
        self.assertIn("not real phone/browser proof", doc)
        self.assertIn("not a real route/elevator field pass", doc)
        self.assertIn("not dropoff/cancel completion", doc)
        self.assertIn("not delivery success", doc)
        self.assertIn("not HIL", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_material_dispatch_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        summary_text = json.dumps(
            fixture["robot_diagnostics_field_evidence_rerun_material_dispatch_summary"],
            ensure_ascii=False,
        ).lower()

        # 材料派发 fixture 只保留 phone-safe 摘要，不泄漏原始材料、底层通信、凭证或控制授权。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover detail",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, summary_text)


class FieldEvidenceRerunCallbackIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_evidence_rerun_callback_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场证据复跑回执入口只消费 safe summary，不读取 raw artifact 或改变主操作 gate。
        self.assertIn("现场证据复跑回执入口", app)
        self.assertIn("FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_callback_intake_summary", app)
        self.assertIn("field_evidence_rerun_callback_intake_summary", app)
        self.assertIn("software_proof_docker_field_evidence_rerun_callback_intake_gate", app)
        self.assertIn("safe_to_control=false / delivery_success=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 明确 callback intake 仍是 not_proven 软件证明，不能打开 Start/Confirm/Cancel。
        summary = fixture["robot_diagnostics_field_evidence_rerun_callback_intake_summary"]
        self.assertEqual(summary["intake_status"], "blocked_missing_field_evidence_rerun_callback_materials_not_proven")
        self.assertEqual(summary["safe_to_control"], False)
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(fixture["can_collect"], False)
        self.assertEqual(fixture["can_confirm_dropoff"], False)
        self.assertEqual(fixture["can_cancel"], False)
        self.assertIn("accepted=none accepted as field proof", fixture_text)
        self.assertIn("missing=real route completion signal", fixture_text)
        self.assertIn("rejected=unsafe_or_mismatched_materials_not_proven", fixture_text)
        self.assertIn("blocked=same safe evidence_ref callback packet not yet accepted", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("software_proof_docker_field_evidence_rerun_callback_intake_gate", fixture_text)
        self.assertEqual(
            mobile_fixture["robot_diagnostics_field_evidence_rerun_callback_intake_summary"]["safe_to_control"],
            False,
        )

        # 产品文档必须写清它不是现场通过、真实手机/browser、投放/取消完成、送达、HIL 或 O5 external proof。
        self.assertIn("现场证据复跑回执入口", doc)
        self.assertIn("robot_diagnostics_field_evidence_rerun_callback_intake_summary", doc)
        self.assertIn("software_proof_docker_field_evidence_rerun_callback_intake_gate", doc)
        self.assertIn("not real phone/browser proof", doc)
        self.assertIn("not a real route/elevator field pass", doc)
        self.assertIn("not dropoff/cancel completion", doc)
        self.assertIn("not delivery success", doc)
        self.assertIn("not HIL", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        summary_text = json.dumps(
            fixture["robot_diagnostics_field_evidence_rerun_callback_intake_summary"],
            ensure_ascii=False,
        ).lower()

        # 回执入口 fixture 只保留 accepted/missing/rejected/blocked 摘要，不泄漏 raw packet 或控制授权。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover detail",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, summary_text)


class CloudPendingAckStatusGuardMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_cloud_pending_ack_status_guard_is_consumed_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(CLOUD_PENDING_ACK_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # command_pending 使用已有 cloud readiness 面板和主操作 gate，不新增 endpoint 或控制动作。
        self.assertIn("CLOUD_PENDING_ACK_STATUS_BOUNDARY", app)
        self.assertIn("CLOUD_PENDING_ACK_STATUS_COPY", app)
        self.assertIn("software_proof_docker_cloud_pending_ack_status_guard", app)
        self.assertIn("degradation_state", app)
        self.assertIn("command_pending", app)
        self.assertIn("remote_readiness", app)
        self.assertIn("remote_ready=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"cloudPendingAck.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 覆盖 Robot/status readiness 语义：远程未就绪、主操作关闭、没有送达成功语义。
        self.assertEqual(fixture["degradation_state"], "command_pending")
        self.assertEqual(fixture["remote_ready"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertEqual(fixture["delivery_success"], False)
        self.assertIn("本地命令已终态，但云端 ACK 还没确认，暂不能拉取新命令", fixture_text)
        self.assertIn("remote_ready=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("software_proof_docker_cloud_pending_ack_status_guard", fixture_text)
        self.assertNotIn("delivery_success\": true", fixture_text)
        self.assertNotIn("delivery success claim", fixture_text.lower())

        # 产品文档必须把该状态写成 Docker/local fixture proof，而不是真实手机/4G/云/HIL/送达证明。
        self.assertIn("cloud_pending_ack_status_guard", doc)
        self.assertIn("command_pending", doc)
        self.assertIn("remote_ready=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("software_proof_docker_cloud_pending_ack_status_guard", doc)
        self.assertIn("不是真实手机/browser/4G/云/HIL/送达证明", doc)

    def test_cloud_pending_ack_fixture_stays_phone_safe(self):
        fixture = json.loads(CLOUD_PENDING_ACK_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # pending ACK fixture 只提供手机安全摘要，不能带 raw payload、凭证、底盘控制或成功证明。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover parameter",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


class CloudCommandExpirySafetyGuardMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_cloud_command_expiry_safety_guard_is_consumed_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(CLOUD_COMMAND_EXPIRY_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # command_expired 复用只读 cloud readiness 面板，手机端只能解释和重新提交新命令。
        self.assertIn("CLOUD_COMMAND_EXPIRY_BOUNDARY", app)
        self.assertIn("CLOUD_COMMAND_EXPIRY_COPY", app)
        self.assertIn("software_proof_docker_cloud_command_expiry_safety_guard", app)
        self.assertIn("degradation_state", app)
        self.assertIn("command_expired", app)
        self.assertIn("expired_command_id", app)
        self.assertIn("remote_readiness", app)
        self.assertIn("remote_ready=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"cloudCommandExpiry.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 明确旧命令只会 ignored，不缓存、不重放，也不产生送达成功语义。
        self.assertEqual(fixture["degradation_state"], "command_expired")
        self.assertEqual(fixture["expired_command_id"], "cmd_expired_20260520_001")
        self.assertEqual(fixture["remote_ready"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertEqual(fixture["delivery_success"], False)
        self.assertEqual(fixture["phone_readiness"]["remote_readiness"]["retry_hint"], "resubmit_command")
        self.assertIn("云端命令已过期", fixture_text)
        self.assertIn("不会缓存、不会重放", fixture_text)
        self.assertIn("ignored_expired_command_not_delivery_success", fixture_text)
        self.assertIn("remote_ready=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("software_proof_docker_cloud_command_expiry_safety_guard", fixture_text)
        self.assertNotIn("delivery_success\": true", fixture_text)
        self.assertNotIn("delivery success claim", fixture_text.lower())

        # 产品文档必须把 expired command 写成 Docker/local fixture proof，而不是真实云或送达证明。
        self.assertIn("cloud_command_expiry_safety_guard", doc)
        self.assertIn("command_expired", doc)
        self.assertIn("expired_command_id", doc)
        self.assertIn("remote_ready=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("software_proof_docker_cloud_command_expiry_safety_guard", doc)
        self.assertIn("不缓存、不重放控制请求", doc)
        self.assertIn("不是真实手机/browser/4G/云/HIL/送达证明", doc)

    def test_cloud_command_expiry_fixture_stays_phone_safe(self):
        fixture = json.loads(CLOUD_COMMAND_EXPIRY_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # expired command fixture 只提供安全摘要，不能泄漏原始命令、凭证、控制面或成功证明。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover parameter",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


class CloudCommandIdempotencyVisibilityGuardMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_cloud_command_idempotency_visibility_guard_is_consumed_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(CLOUD_COMMAND_IDEMPOTENCY_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # duplicate cached ACK 复用 cloud readiness 面板；手机端只能解释去重，不能新增控制 endpoint。
        self.assertIn("CLOUD_COMMAND_IDEMPOTENCY_BOUNDARY", app)
        self.assertIn("CLOUD_COMMAND_IDEMPOTENCY_COPY", app)
        self.assertIn("software_proof_docker_cloud_command_idempotency_visibility_guard", app)
        self.assertIn("command_duplicate_deduped", app)
        self.assertIn("duplicate_command_id", app)
        self.assertIn("cached_ack_state", app)
        self.assertIn("duplicate_cached_ack_not_delivery_success", app)
        self.assertIn("remote_ready=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"cloudCommandIdempotency.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 明确重复 command_id 已去重，cached ACK 不代表送达成功，三类主操作全关闭。
        self.assertEqual(fixture["degradation_state"], "command_duplicate_deduped")
        self.assertEqual(fixture["duplicate_command_id"], "cmd_duplicate_20260520_001")
        self.assertEqual(fixture["cached_ack_state"], "acked")
        self.assertEqual(fixture["remote_ready"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertEqual(fixture["delivery_success"], False)
        self.assertEqual(fixture["ack_semantics"], "duplicate_cached_ack_not_delivery_success")
        self.assertIn("重复云指令已去重", fixture_text)
        self.assertIn("机器人没有重复执行", fixture_text)
        self.assertIn("这不是送达成功", fixture_text)
        self.assertIn("自动重放", fixture_text)
        self.assertIn("自动 resubmit", fixture_text)
        self.assertIn("remote_ready=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("software_proof_docker_cloud_command_idempotency_visibility_guard", fixture_text)
        self.assertNotIn("delivery_success\": true", fixture_text)

        # 产品文档必须把 duplicate/deduped 写成只读可见性，不是真实云/手机/HIL/送达证明。
        self.assertIn("cloud_command_idempotency_visibility_guard", doc)
        self.assertIn("command_duplicate_deduped", doc)
        self.assertIn("duplicate_command_id", doc)
        self.assertIn("cached_ack_state", doc)
        self.assertIn("duplicate_cached_ack_not_delivery_success", doc)
        self.assertIn("重复云指令已去重", doc)
        self.assertIn("这不是送达成功", doc)
        self.assertIn("不自动重放、不自动 resubmit", doc)
        self.assertIn("software_proof_docker_cloud_command_idempotency_visibility_guard", doc)

    def test_cloud_command_idempotency_fixture_stays_phone_safe(self):
        fixture = json.loads(CLOUD_COMMAND_IDEMPOTENCY_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # duplicate/deduped fixture 只暴露安全摘要，不能携带原始命令、凭证、控制授权或成功证明。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover parameter",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


class CloudCommandIdConflictVisibilityGuardMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_cloud_command_id_conflict_visibility_guard_is_consumed_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(CLOUD_COMMAND_ID_CONFLICT_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # command_id_conflict 复用 cloud readiness 面板；手机端只能展示拒绝状态，不能新增控制 endpoint。
        self.assertIn("CLOUD_COMMAND_ID_CONFLICT_BOUNDARY", app)
        self.assertIn("CLOUD_COMMAND_ID_CONFLICT_COPY", app)
        self.assertIn("software_proof_docker_cloud_command_id_conflict_visibility_guard", app)
        self.assertIn("command_id_conflict", app)
        self.assertIn("conflict_command_id", app)
        self.assertIn("conflict_reason", app)
        self.assertIn("conflict_fields", app)
        self.assertIn("conflict_rejected_not_delivery_success", app)
        self.assertIn("remote_ready=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"cloudCommandIdConflict.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        # fixture 明确同一 command_id 的 type/payload 冲突已被拒绝，主操作三类都保持 fail closed。
        self.assertEqual(fixture["degradation_state"], "command_id_conflict")
        self.assertEqual(fixture["conflict_command_id"], "cmd_conflict_20260520_001")
        self.assertEqual(fixture["conflict_reason"], "duplicate_id_mismatched_type_or_payload")
        self.assertEqual(fixture["conflict_fields"], ["type", "payload"])
        self.assertEqual(fixture["remote_ready"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertEqual(fixture["delivery_success"], False)
        self.assertEqual(fixture["ack_semantics"], "conflict_rejected_not_delivery_success")
        self.assertIn("命令 ID 冲突", fixture_text)
        self.assertIn("机器人已拒绝执行", fixture_text)
        self.assertIn("这不是送达成功", fixture_text)
        self.assertIn("自动重放", fixture_text)
        self.assertIn("自动 resubmit", fixture_text)
        self.assertIn("ACK/cursor", fixture_text)
        self.assertIn("remote_ready=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("software_proof_docker_cloud_command_id_conflict_visibility_guard", fixture_text)
        self.assertNotIn("delivery_success\": true", fixture_text)

        # 产品文档必须把 conflict 写成只读可见性，不是真实云/手机/HIL/送达证明。
        self.assertIn("cloud_command_id_conflict_visibility_guard", doc)
        self.assertIn("command_id_conflict", doc)
        self.assertIn("conflict_command_id", doc)
        self.assertIn("conflict_reason", doc)
        self.assertIn("conflict_fields", doc)
        self.assertIn("conflict_rejected_not_delivery_success", doc)
        self.assertIn("命令 ID 冲突", doc)
        self.assertIn("机器人已拒绝执行", doc)
        self.assertIn("这不是送达成功", doc)
        self.assertIn("不自动重放、不自动 resubmit、不请求 ACK/cursor", doc)
        self.assertIn("software_proof_docker_cloud_command_id_conflict_visibility_guard", doc)

    def test_cloud_command_id_conflict_fixture_stays_phone_safe(self):
        fixture = json.loads(CLOUD_COMMAND_ID_CONFLICT_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # conflict fixture 只暴露安全摘要，不能携带原始命令、凭证、控制授权或成功证明。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "authorization",
            "bearer",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "serial device",
            "baudrate",
            "wave rover parameter",
            "traceback",
            "checksum",
            "complete artifact",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


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


class Pr5ReviewThreadCloseoutMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_pr5_review_thread_closeout_panel_is_read_only_and_whitelisted(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # PR #5 panel 只展示 safe summary，不新增主动 fetch、ACK、cursor 或主操作按钮。
        self.assertIn("PR #5 review thread closeout", app)
        self.assertIn("PR5_REVIEW_THREAD_CLOSEOUT_BOUNDARY", app)
        self.assertIn("UNSAFE_PR5_REVIEW_THREAD_CLOSEOUT_TEXT", app)
        self.assertIn("safePr5ReviewThreadCloseoutText", app)
        self.assertIn("pr5ReviewThreadCloseoutCandidate", app)
        self.assertIn("pr5ReviewThreadCloseoutFromStatus", app)
        self.assertIn("renderPr5ReviewThreadCloseoutThreads", app)
        self.assertIn("robot_diagnostics_pr5_review_thread_closeout_summary", app)
        self.assertIn("pr5_review_thread_closeout_summary", app)
        self.assertIn("pr5_review_thread_closeout", app)
        self.assertIn("ready_to_close_on_mainline_docs", fixture_text)
        self.assertIn("blocked_pending_real_materials", fixture_text)
        self.assertIn("still_open_missing_current_evidence", app)
        self.assertIn("pr5-review-thread-closeout-panel", styles)
        self.assertIn("pr5-review-thread-closeout-grid", styles)
        self.assertIn("thread-decision-list", styles)
        self.assertNotRegex(app, r"pr5ReviewThreadCloseout.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture、移动端 fixture 和文档都必须保留 software_proof/not_proven 控制边界。
        closeout = fixture["robot_diagnostics_pr5_review_thread_closeout_summary"]
        self.assertEqual(closeout["source"], "software_proof")
        self.assertEqual(closeout["overall_status"], "not_proven")
        self.assertEqual(closeout["delivery_success"], False)
        self.assertEqual(closeout["primary_actions_enabled"], False)
        self.assertEqual(closeout["thread_decisions"][0]["decision"], "ready_to_close_on_mainline_docs")
        self.assertEqual(closeout["thread_decisions"][1]["decision"], "blocked_pending_real_materials")
        mobile_closeout = mobile_fixture["pr5_review_thread_closeout_summary"]
        self.assertEqual(mobile_closeout["source"], "software_proof")
        self.assertEqual(mobile_closeout["overall_status"], "not_proven")
        self.assertEqual(mobile_closeout["delivery_success"], False)
        self.assertEqual(mobile_closeout["primary_actions_enabled"], False)
        self.assertIn("pr5_review_thread_closeout", doc)
        self.assertIn("robot_diagnostics_pr5_review_thread_closeout_summary", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_pr5_review_thread_closeout_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        closeout_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_pr5_review_thread_closeout_summary"],
                "mobile": mobile_fixture["pr5_review_thread_closeout_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # PR #5 closeout fixture 只能包含脱敏 thread decision，不携带 raw JSON、凭证、路径或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "github token",
            "ghp_",
            "serial path",
            "serial device",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "raw review body",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, closeout_text)


class HardwareRealMaterialEscalationRequestMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hardware_real_material_escalation_request_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 升级请求 panel 只消费 Robot safe alias；缺失时兼容 safe summary，不新增 fetch 或控制入口。
        self.assertIn("硬件真实材料升级请求", app)
        self.assertIn("HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_TEXT", app)
        self.assertIn("safeHardwareRealMaterialEscalationRequestText", app)
        self.assertIn("hardwareRealMaterialEscalationRequestCandidate", app)
        self.assertIn("hardwareRealMaterialEscalationRequestFromStatus", app)
        self.assertIn("robot_diagnostics_hardware_real_material_escalation_request_summary", app)
        self.assertIn("hardware_real_material_escalation_request_summary", app)
        self.assertIn("hardware-real-material-escalation-request-panel", styles)
        self.assertIn("hardware-real-material-escalation-request-grid", styles)
        self.assertIn("missing_hardware_materials", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertNotRegex(
            app,
            r"hardwareRealMaterialEscalationRequest.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # Web fixture 与 mobile fixture 都保留 fail-closed evidence boundary，不改变主按钮 gate。
        summary = fixture["robot_diagnostics_hardware_real_material_escalation_request_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["safe_status"], "hardware_real_material_escalation_request_not_proven")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        mobile_summary = mobile_fixture["hardware_real_material_escalation_request_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["safe_status"], "hardware_real_material_escalation_request_not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertIn("hardware_real_material_escalation_request", doc)
        self.assertIn("robot_diagnostics_hardware_real_material_escalation_request_summary", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_hardware_real_material_escalation_request_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        escalation_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_hardware_real_material_escalation_request_summary"],
                "mobile": mobile_fixture["hardware_real_material_escalation_request_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # fixture 只保留真实材料缺口和 owner handoff，不夹带底层路径、凭证、完整材料或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, escalation_text)


class Pr5VendorSourceReviewPacketMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_pr5_vendor_source_review_packet_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(PR5_VENDOR_SOURCE_REVIEW_PACKET_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # vendor/source review packet 只消费 Robot diagnostics safe alias，不新增 ACK、cursor 或控制入口。
        self.assertIn("PR #5 vendor/source review packet", app)
        self.assertIn("PR5_VENDOR_SOURCE_REVIEW_PACKET_BOUNDARY", app)
        self.assertIn("UNSAFE_PR5_VENDOR_SOURCE_REVIEW_PACKET_TEXT", app)
        self.assertIn("safePr5VendorSourceReviewPacketText", app)
        self.assertIn("pr5VendorSourceReviewPacketCandidate", app)
        self.assertIn("pr5VendorSourceReviewPacketFromStatus", app)
        self.assertIn("robot_diagnostics_pr5_vendor_source_review_packet_summary", app)
        self.assertIn("pr5_vendor_source_review_packet_summary", app)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", app)
        self.assertIn("pr5-vendor-source-review-packet-panel", styles)
        self.assertIn("pr5-vendor-source-review-packet-grid", styles)
        self.assertNotRegex(
            app,
            r"pr5VendorSourceReviewPacket.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # fixture 和产品文档必须固定保留 software_proof/not_proven 控制边界。
        self.assertEqual(fixture["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(fixture["source"], "software_proof")
        self.assertEqual(fixture["proof_status"], "not_proven")
        self.assertEqual(fixture["delivery_success"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_pr5_vendor_source_review_packet_gate", fixture_text)
        self.assertIn("2D LiDAR", fixture_text)
        self.assertIn("ToF", fixture_text)
        self.assertIn("不是真实采购/安装/标定/HIL/送达证明", fixture_text)
        self.assertIn("pr5_vendor_source_review_packet", doc)
        self.assertIn("robot_diagnostics_pr5_vendor_source_review_packet_summary", doc)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("不是真实采购/安装/标定/HIL/送达证明", doc)

    def test_pr5_vendor_source_review_packet_fixture_stays_phone_safe(self):
        fixture = json.loads(PR5_VENDOR_SOURCE_REVIEW_PACKET_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # fixture 只保留 Robot alias 安全摘要，不能夹带 raw vendor/source、凭证、路径或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw vendor docs",
            "raw source document",
            "github token",
            "ghp_",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


class Pr5VendorSourceReviewReplyDispatchMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_pr5_vendor_source_review_reply_dispatch_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # reply-dispatch 只消费 Robot diagnostics alias，展示可发布状态但不新增 endpoint/ACK/cursor/retry。
        self.assertIn("PR #5 vendor/source review reply-dispatch", app)
        self.assertIn("PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_BOUNDARY", app)
        self.assertIn("UNSAFE_PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_TEXT", app)
        self.assertIn("safePr5VendorSourceReviewReplyDispatchText", app)
        self.assertIn("pr5VendorSourceReviewReplyDispatchCandidate", app)
        self.assertIn("pr5VendorSourceReviewReplyDispatchFromStatus", app)
        self.assertIn("robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary", app)
        self.assertIn("pr5_vendor_source_review_reply_dispatch_summary", app)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", app)
        self.assertIn("可发布 reply 不是真实采购、真实安装、标定、HIL、真实手机验收或送达证明", app)
        self.assertIn("pr5-vendor-source-review-reply-dispatch-panel", styles)
        self.assertIn("pr5-vendor-source-review-reply-dispatch-grid", styles)
        self.assertNotRegex(
            app,
            r"pr5VendorSourceReviewReplyDispatch.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # fixture 和产品文档必须固定保留 software_proof/not_proven 和材料未证明边界。
        self.assertEqual(fixture["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(fixture["source"], "software_proof")
        self.assertEqual(fixture["dispatch_status"], "reply_ready_to_publish_not_proven")
        self.assertEqual(fixture["hardware_material_state"], "hardware_material_pending")
        self.assertEqual(fixture["delivery_success"], False)
        self.assertEqual(fixture["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate", fixture_text)
        self.assertIn("hardware_material_pending", fixture_text)
        self.assertIn("可发布 reply", fixture_text)
        self.assertIn("不是真实采购、真实安装、标定、HIL、真实手机验收或送达证明", fixture_text)
        self.assertIn("pr5_vendor_source_review_reply_dispatch", doc)
        self.assertIn("robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary", doc)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("hardware_material_pending", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("真实采购", doc)
        self.assertIn("真实安装", doc)
        self.assertIn("真实手机验收", doc)
        self.assertIn("送达证明", doc)

    def test_pr5_vendor_source_review_reply_dispatch_fixture_stays_phone_safe(self):
        fixture = json.loads(PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False).lower()

        # reply-dispatch fixture 不能夹带 raw reply、凭证、路径、控制请求或成功证明。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw reply body",
            "raw review reply",
            "raw dispatch payload",
            "raw vendor docs",
            "github token",
            "ghp_",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "retry request",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, fixture_text)


class TaskTerminalCompletionMainlineMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_task_terminal_completion_mainline_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # terminal mainline panel 只消费 Robot diagnostics safe alias；缺失时 fail closed。
        self.assertIn("任务终态主链路", app)
        self.assertIn("TASK_TERMINAL_COMPLETION_MAINLINE_BOUNDARY", app)
        self.assertIn("UNSAFE_TASK_TERMINAL_COMPLETION_MAINLINE_TEXT", app)
        self.assertIn("safeTaskTerminalCompletionMainlineText", app)
        self.assertIn("taskTerminalCompletionMainlineCandidate", app)
        self.assertIn("taskTerminalCompletionMainlineFromStatus", app)
        self.assertIn("robot_diagnostics_task_terminal_completion_mainline_summary", app)
        self.assertIn("task-terminal-completion-mainline-panel", styles)
        self.assertIn("task-terminal-completion-mainline-grid", styles)
        self.assertIn("safe_terminal_action", fixture_text)
        self.assertIn("operator_confirmation", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertNotIn("status?.task_terminal_completion_mainline_summary", app)
        self.assertNotIn("status?.task_terminal_completion_mainline", app)
        self.assertNotRegex(
            app,
            r"taskTerminalCompletionMainline.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # Web fixture 与 mobile fixture 都必须保留 software_proof / not_proven 控制边界。
        summary = fixture["robot_diagnostics_task_terminal_completion_mainline_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["status"], "blocked_not_proven")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        mobile_summary = mobile_fixture["robot_diagnostics_task_terminal_completion_mainline_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["status"], "blocked_not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertIn("task_terminal_completion_mainline", doc)
        self.assertIn("robot_diagnostics_task_terminal_completion_mainline_summary", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_task_terminal_completion_mainline_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        mainline_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_task_terminal_completion_mainline_summary"],
                "mobile": mobile_fixture["robot_diagnostics_task_terminal_completion_mainline_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # fixture 只保留 terminal action 摘要，不夹带 raw artifact、控制协议、路径、凭证或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, mainline_text)


class RealMaterialReadinessBoardMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_real_material_readiness_board_panel_is_read_only_and_grouped(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 看板优先消费 Robot diagnostics safe alias；兼容 summary/artifact，但只展示四类固定 group。
        self.assertIn("真实材料就绪看板", app)
        self.assertIn("REAL_MATERIAL_READINESS_BOARD_BOUNDARY", app)
        self.assertIn("UNSAFE_REAL_MATERIAL_READINESS_BOARD_TEXT", app)
        self.assertIn("safeRealMaterialReadinessBoardText", app)
        self.assertIn("realMaterialReadinessBoardCandidate", app)
        self.assertIn("realMaterialReadinessBoardFromStatus", app)
        self.assertIn("robot_diagnostics_real_material_readiness_board_summary", app)
        self.assertIn("real_material_readiness_board_summary", app)
        self.assertIn("real_material_readiness_board", app)
        self.assertIn("Objective 5 external", app)
        self.assertIn("Objective 1 / PR #5 hardware", app)
        self.assertIn("PR #4 route/elevator", app)
        self.assertIn("Objective 4 real phone", app)
        self.assertIn("real-material-readiness-board-panel", styles)
        self.assertIn("real-material-readiness-board-grid", styles)
        self.assertIn("real-material-readiness-board-group", styles)
        self.assertNotRegex(
            app,
            r"realMaterialReadinessBoard.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # fixture、mobile fixture 和产品文档都固定保留 fail-closed 控制边界。
        summary = fixture["robot_diagnostics_real_material_readiness_board_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["status"], "not_proven")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        self.assertEqual(len(summary["material_groups"]), 4)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", fixture_text)
        mobile_summary = mobile_fixture["real_material_readiness_board_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["status"], "not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertEqual(mobile_summary["safe_to_control"], False)
        self.assertIn("real_material_readiness_board", doc)
        self.assertIn("robot_diagnostics_real_material_readiness_board_summary", doc)
        self.assertIn("真实材料就绪看板", doc)
        self.assertIn("Objective 5", doc)
        self.assertIn("Objective 1", doc)
        self.assertIn("Objective 4", doc)
        self.assertIn("PR #4", doc)
        self.assertIn("PR #5", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_real_material_readiness_board_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        board_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_real_material_readiness_board_summary"],
                "mobile": mobile_fixture["real_material_readiness_board_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 看板 fixture 只能携带现场 owner 路由摘要，不夹带内部材料、凭证、路径或控制成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, board_text)


class RealMaterialEvidenceIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_real_material_evidence_intake_panel_is_read_only_and_whitelisted(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 真实材料回填入口只消费 phone-safe safe alias/summary，不新增控制或诊断请求。
        self.assertIn("真实材料回填入口", app)
        self.assertIn("REAL_MATERIAL_EVIDENCE_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_REAL_MATERIAL_EVIDENCE_INTAKE_TEXT", app)
        self.assertIn("safeRealMaterialEvidenceIntakeText", app)
        self.assertIn("realMaterialEvidenceIntakeCandidate", app)
        self.assertIn("realMaterialEvidenceIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_real_material_evidence_intake_summary", app)
        self.assertIn("real_material_evidence_intake_summary", app)
        self.assertIn("phone_safe_real_material_evidence_intake_summary", app)
        self.assertIn("real-material-evidence-intake-panel", styles)
        self.assertIn("real-material-evidence-intake-grid", styles)
        self.assertIn("accepted_items", fixture_text)
        self.assertIn("missing_items", fixture_text)
        self.assertIn("rejected_items", fixture_text)
        self.assertIn("manifest_template", app)
        self.assertIn("template_groups", app)
        self.assertIn("required_item_templates", app)
        self.assertIn("realMaterialEvidenceIntakeTemplateGroups", app)
        self.assertIn("same_safe_evidence_ref_required", app)
        self.assertIn("manifest_template", fixture_text)
        self.assertIn("template_groups", fixture_text)
        self.assertIn("required_item_templates", fixture_text)
        self.assertIn("o5_external", fixture_text)
        self.assertIn("o1_pr5_hardware", fixture_text)
        self.assertIn("pr4_route_elevator", fixture_text)
        self.assertIn("o4_real_phone", fixture_text)
        self.assertIn("next_action", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("real-material-evidence-intake-template-groups", styles)
        self.assertIn("real-material-evidence-intake-template-group", styles)
        self.assertNotRegex(
            app,
            r"realMaterialEvidenceIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # 两个 fixture 与产品文档都保留 Docker/software-proof 边界和 fail-closed 控制状态。
        summary = fixture["robot_diagnostics_real_material_evidence_intake_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["intake_status"], "blocked_missing_real_material_evidence_not_proven")
        self.assertEqual(summary["material_group"], "pr4_route_elevator")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        self.assertEqual(summary["manifest_template"]["same_safe_evidence_ref_required"], True)
        self.assertEqual(len(summary["manifest_template"]["template_groups"]), 4)
        self.assertGreaterEqual(
            sum(len(group["required_item_templates"]) for group in summary["manifest_template"]["template_groups"]),
            16,
        )
        mobile_summary = mobile_fixture["real_material_evidence_intake_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["intake_status"], "blocked_missing_real_material_evidence_not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertEqual(mobile_summary["safe_to_control"], False)
        self.assertEqual(mobile_summary["manifest_template"]["same_safe_evidence_ref_required"], True)
        self.assertEqual(len(mobile_summary["manifest_template"]["template_groups"]), 4)
        self.assertIn("real_material_evidence_intake", doc)
        self.assertIn("robot_diagnostics_real_material_evidence_intake_summary", doc)
        self.assertIn("真实材料回填入口", doc)
        self.assertIn("manifest_template", doc)
        self.assertIn("template_groups", doc)
        self.assertIn("required_item_templates", doc)
        self.assertIn("software_proof_docker_real_material_evidence_intake_gate", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_real_material_evidence_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_real_material_evidence_intake_summary"],
                "mobile": mobile_fixture["real_material_evidence_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 回填入口 fixture 只保留材料分类结果，不夹带原始材料、控制协议、路径、凭证或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, intake_text)


class RealMaterialFollowupEscalationStatusMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_real_material_followup_escalation_status_panel_is_read_only_and_grouped(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 升级状态 panel 只消费 phone-safe summary，展示 owner/due/rerun 状态，不新增控制或诊断请求。
        self.assertIn("真实材料升级状态", app)
        self.assertIn("REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_BOUNDARY", app)
        self.assertIn("UNSAFE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_TEXT", app)
        self.assertIn("safeRealMaterialFollowupEscalationStatusText", app)
        self.assertIn("realMaterialFollowupEscalationStatusCandidate", app)
        self.assertIn("realMaterialFollowupEscalationStatusFromStatus", app)
        self.assertIn("robot_diagnostics_real_material_followup_escalation_status_summary", app)
        self.assertIn("real_material_followup_escalation_status_summary", app)
        self.assertIn("phone_safe_real_material_followup_escalation_status_summary", app)
        self.assertIn("material_groups", app)
        self.assertIn("field_owner", app)
        self.assertIn("due_status", app)
        self.assertIn("blocked_reason", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("escalation_level", app)
        self.assertIn("rerun_command", app)
        self.assertIn("rerun_status_summary", app)
        self.assertIn("real-material-followup-escalation-status-panel", styles)
        self.assertIn("real-material-followup-escalation-status-grid", styles)
        self.assertIn("real-material-followup-escalation-status-group", styles)
        self.assertIn("software_proof_docker_real_material_followup_escalation_status_gate", fixture_text)
        self.assertIn("due_status", fixture_text)
        self.assertIn("blocked_reason", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("escalation_level", fixture_text)
        self.assertNotRegex(
            app,
            r"realMaterialFollowupEscalationStatus.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # Web fixture、mobile fixture 与产品文档都固定保留 fail-closed 控制边界。
        summary = fixture["robot_diagnostics_real_material_followup_escalation_status_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["overall_status"], "real_material_followup_escalation_status_not_proven")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        self.assertEqual(len(summary["material_groups"]), 4)
        mobile_summary = mobile_fixture["real_material_followup_escalation_status_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["overall_status"], "real_material_followup_escalation_status_not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertEqual(mobile_summary["safe_to_control"], False)
        self.assertEqual(len(mobile_summary["material_groups"]), 4)
        self.assertIn("real_material_followup_escalation_status", doc)
        self.assertIn("robot_diagnostics_real_material_followup_escalation_status_summary", doc)
        self.assertIn("真实材料升级状态", doc)
        self.assertIn("due_status", doc)
        self.assertIn("blocked_reason", doc)
        self.assertIn("next_required_evidence", doc)
        self.assertIn("escalation_level", doc)
        self.assertIn("software_proof_docker_real_material_followup_escalation_status_gate", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_real_material_followup_escalation_status_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        followup_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_real_material_followup_escalation_status_summary"],
                "mobile": mobile_fixture["real_material_followup_escalation_status_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # follow-up fixture 只保留追责元数据，不夹带原始材料、路径、凭证、底盘控制或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, followup_text)


class TaskTerminalFieldMaterialIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_task_terminal_field_material_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 现场材料回填入口只消费 Robot diagnostics safe alias；缺失时 fail closed。
        self.assertIn("现场材料回填入口", app)
        self.assertIn("TASK_TERMINAL_FIELD_MATERIAL_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_TASK_TERMINAL_FIELD_MATERIAL_INTAKE_TEXT", app)
        self.assertIn("safeTaskTerminalFieldMaterialIntakeText", app)
        self.assertIn("taskTerminalFieldMaterialIntakeCandidate", app)
        self.assertIn("taskTerminalFieldMaterialIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_task_terminal_field_material_intake_summary", app)
        self.assertIn("task-terminal-field-material-intake-panel", styles)
        self.assertIn("task-terminal-field-material-intake-grid", styles)
        self.assertIn("accepted_safe_refs", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("safe_to_control", fixture_text)
        self.assertNotIn("status?.task_terminal_field_material_intake_summary", app)
        self.assertNotIn("status?.task_terminal_field_material_intake", app)
        self.assertNotRegex(
            app,
            r"taskTerminalFieldMaterialIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # Web fixture 与 mobile fixture 都固定保持 software_proof / not_proven / safe_to_control=false。
        summary = fixture["robot_diagnostics_task_terminal_field_material_intake_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["intake_status"], "blocked_missing_field_materials")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        mobile_summary = mobile_fixture["robot_diagnostics_task_terminal_field_material_intake_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["intake_status"], "blocked_missing_field_materials")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertEqual(mobile_summary["safe_to_control"], False)
        self.assertIn("task_terminal_field_material_intake", doc)
        self.assertIn("robot_diagnostics_task_terminal_field_material_intake_summary", doc)
        self.assertIn("现场材料回填入口", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_task_terminal_field_material_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_task_terminal_field_material_intake_summary"],
                "mobile": mobile_fixture["robot_diagnostics_task_terminal_field_material_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # fixture 只保留材料回填白名单摘要，不夹带 raw artifact、控制协议、路径、凭证或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, intake_text)


class TaskTerminalFieldMaterialReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_task_terminal_field_material_review_decision_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 复核决策 panel 只读展示 Robot safe alias，不新增 ACK、cursor、diagnostics fetch 或主操作入口。
        self.assertIn("现场材料复核决策", app)
        self.assertIn("TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeTaskTerminalFieldMaterialReviewDecisionText", app)
        self.assertIn("taskTerminalFieldMaterialReviewDecisionCandidate", app)
        self.assertIn("taskTerminalFieldMaterialReviewDecisionFromStatus", app)
        self.assertIn("robot_diagnostics_task_terminal_field_material_review_decision_summary", app)
        self.assertIn("task-terminal-field-material-review-decision-panel", styles)
        self.assertIn("task-terminal-field-material-review-decision-grid", styles)
        self.assertIn("accepted_materials", fixture_text)
        self.assertIn("missing_materials", fixture_text)
        self.assertIn("rejected_materials", fixture_text)
        self.assertIn("blocked_materials", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("rerun_guidance", fixture_text)
        self.assertNotIn("status?.task_terminal_field_material_review_decision_summary", app)
        self.assertNotIn("status?.task_terminal_field_material_review_decision", app)
        self.assertNotRegex(
            app,
            r"taskTerminalFieldMaterialReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # fixtures 和产品文档必须固定 software_proof / not_proven / safe_to_control=false。
        summary = fixture["robot_diagnostics_task_terminal_field_material_review_decision_summary"]
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["review_decision"], "needs_required_material_backfill_not_proven")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        mobile_summary = mobile_fixture["robot_diagnostics_task_terminal_field_material_review_decision_summary"]
        self.assertEqual(mobile_summary["source"], "software_proof")
        self.assertEqual(mobile_summary["review_decision"], "needs_required_material_backfill_not_proven")
        self.assertEqual(mobile_summary["delivery_success"], False)
        self.assertEqual(mobile_summary["primary_actions_enabled"], False)
        self.assertEqual(mobile_summary["safe_to_control"], False)
        self.assertIn("task_terminal_field_material_review_decision", doc)
        self.assertIn("robot_diagnostics_task_terminal_field_material_review_decision_summary", doc)
        self.assertIn("现场材料复核决策", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_task_terminal_field_material_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        review_text = json.dumps(
            {
                "status": fixture["robot_diagnostics_task_terminal_field_material_review_decision_summary"],
                "mobile": mobile_fixture["robot_diagnostics_task_terminal_field_material_review_decision_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # fixture 只能携带复核白名单字段，不能带 raw review、旧状态推导、控制授权或成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw review",
            "raw artifact",
            "serial path",
            "serial device",
            "uart path",
            "baudrate",
            "/users/",
            "/tmp/",
            "credentials",
            "authorization",
            "bearer",
            "token",
            "database url",
            "queue url",
            "traceback",
            "checksum",
            "complete artifact",
            "hil_pass",
            "delivery success",
            "dropoff success",
            "cancel completed",
            "field pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, review_text)


class MobilePwaCacheRecoveryGateTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_service_worker_uses_versioned_network_first_shell_recovery(self):
        service_worker = self.read_web("service-worker.js")
        app = self.read_web("app.js")
        manifest = json.loads(self.read_web("manifest.webmanifest"))
        doc = DOC.read_text(encoding="utf-8")

        # service-worker 必须 bump cache version，并在 activate 只清理旧 shell/offline cache。
        self.assertIn("2026.05.19-mobile-pwa-cache-recovery-v2", service_worker)
        self.assertIn("rober-mobile-shell-${CACHE_VERSION}", service_worker)
        self.assertIn('SHELL_CACHE_PREFIX = "rober-mobile-shell-"', service_worker)
        self.assertIn("cacheName.startsWith(SHELL_CACHE_PREFIX) && cacheName !== CACHE_NAME", service_worker)
        self.assertIn("keys.filter(isOldShellCache)", service_worker)
        self.assertNotIn("keys.filter((key) => key !== CACHE_NAME)", service_worker)
        self.assertIn("caches.delete(key)", service_worker)
        self.assertIn("skipWaiting", service_worker)
        self.assertIn("clients.claim", service_worker)

        # 当前 app shell 和导航请求走 network-first，离线时才回退到本版本 offline.html。
        self.assertIn("isNavigationRequest", service_worker)
        self.assertIn("fetchAndRefreshCache(event.request, APP_SHELL_URL)", service_worker)
        self.assertIn('fetch(request, { cache: "no-store" })', service_worker)
        self.assertIn("cache.match(OFFLINE_URL)", service_worker)
        self.assertIn("mobile_pwa_cache_recovery", service_worker)

        # app 注册时绕过 HTTP cache 并请求更新，只作为 Browser QA marker，不改变控制 gate。
        self.assertIn("MOBILE_PWA_CACHE_RECOVERY_BOUNDARY", app)
        self.assertIn("software_proof_docker_mobile_pwa_cache_recovery_gate", app)
        self.assertIn('updateViaCache: "none"', app)
        self.assertIn("registration.update", app)
        self.assertIn("markMobilePwaCacheRecovery", app)
        self.assertIn("Start Delivery、Confirm Dropoff、Cancel 仍按原 gate fail closed", app)

        # manifest 和产品文档必须固定 evidence boundary，避免把本地恢复写成真实手机/PWA 通过。
        self.assertEqual(
            manifest["cache_recovery_evidence_boundary"],
            "software_proof_docker_mobile_pwa_cache_recovery_gate",
        )
        self.assertEqual(manifest["cache_recovery_version"], "2026.05.19-mobile-pwa-cache-recovery-v2")
        self.assertIn("mobile_pwa_cache_recovery", doc)
        self.assertIn("service-worker", doc)
        self.assertIn("offline shell", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_offline_shell_recovery_stays_fail_closed(self):
        offline = self.read_web("offline.html")
        service_worker = self.read_web("service-worker.js")

        # 离线 shell 只能给恢复按钮；三个主操作保持 disabled，不能排队或重放控制请求。
        self.assertIn("mobile_pwa_cache_recovery", offline)
        self.assertIn("recoveryButton", offline)
        self.assertIn("刷新当前入口", offline)
        self.assertIn("开始送达", offline)
        self.assertIn("确认投放", offline)
        self.assertIn("取消任务", offline)
        self.assertEqual(len(re.findall(r"<button type=\"button\" disabled>", offline)), 3)
        self.assertIn("不会发送、缓存、排队或重放", offline)
        self.assertIn("不启用 Start、Confirm 或 Cancel", offline)

        # 动态控制面仍绕过缓存；cache recovery 不新增 Start/Confirm/Cancel fetch 路径。
        self.assertIn('fetch(event.request, { cache: "no-store" })', service_worker)
        self.assertIn('path === "/api/collect"', service_worker)
        self.assertIn('path === "/api/dropoff/confirm"', service_worker)
        self.assertIn('path === "/api/cancel"', service_worker)
        self.assertNotRegex(service_worker, r"caches\.(open|match).*api/(collect|dropoff/confirm|cancel)")


class MobilePwaFreshBrowserProofGateTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def read_gate(self):
        return (REPO_ROOT / "pc-tools" / "evidence" / "phone_browser_acceptance_gate.py").read_text(
            encoding="utf-8",
        )

    def test_fresh_browser_flags_schema_and_boundary_are_static_contract(self):
        gate = self.read_gate()
        doc = DOC.read_text(encoding="utf-8")

        # fresh mode 是现有 browser gate 的增强路径；默认 artifact/boundary 仍保留。
        self.assertIn('"--fresh-profile"', gate)
        self.assertIn('"--require-console-zero"', gate)
        self.assertIn("mobile_pwa_fresh_browser_proof_summary.json", gate)
        self.assertIn('FRESH_ARTIFACT_PREFIX = "mobile_pwa_fresh_browser_proof"', gate)
        self.assertIn("config['artifact_prefix']}_{width}x{height}.json", gate)
        self.assertIn("config['artifact_prefix']}_{width}x{height}.png", gate)
        self.assertIn("software_proof_docker_mobile_pwa_fresh_browser_proof_gate", gate)
        self.assertIn("mobile_current_pwa_field_trial_browser_acceptance_summary.json", gate)
        self.assertIn("software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate", gate)

        # 产品文档必须写清入口和非真机边界，避免把 fresh browser proof 写成真实手机验收。
        self.assertIn("fresh browser proof", doc)
        self.assertIn("--fresh-profile --require-console-zero", doc)
        self.assertIn("mobile_pwa_fresh_browser_proof_summary.json", doc)
        self.assertIn("software_proof_docker_mobile_pwa_fresh_browser_proof_gate", doc)
        self.assertIn("not_proven", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)
        self.assertIn("safe_to_control=false", doc)

    def test_fresh_browser_console_zero_and_service_worker_markers_are_asserted(self):
        gate = self.read_gate()
        service_worker = self.read_web("service-worker.js")
        app = self.read_web("app.js")

        # CDP Runtime/Log 事件要被收集；require-console-zero 才把 console/runtime error 变成失败。
        self.assertIn("Runtime.consoleAPICalled", gate)
        self.assertIn("Runtime.exceptionThrown", gate)
        self.assertIn("Log.entryAdded", gate)
        self.assertIn("console_zero_status", gate)
        self.assertIn("console_error_count", gate)
        self.assertIn("console_runtime_failures_since", gate)

        # 当前 shell marker 和 service-worker cache recovery marker 都必须被 fresh proof 识别。
        self.assertIn("?mobile_pwa_cache_recovery=1", gate)
        self.assertIn("freshProbe", gate)
        self.assertIn("htmlMarker", gate)
        self.assertIn("serviceWorkerRegistrationScript", gate)
        self.assertIn("mobile_pwa_cache_recovery", service_worker)
        self.assertIn("RECOVERY_MARKER", service_worker)
        self.assertIn("markMobilePwaCacheRecovery", app)
        self.assertIn("dataset.mobilePwaCacheRecovery", app)

    def test_fresh_browser_dynamic_no_store_and_fail_closed_assertions(self):
        gate = self.read_gate()
        service_worker = self.read_web("service-worker.js")

        # fresh proof 依赖静态 SW 断言和运行时 response header 双重证明动态控制面不进缓存。
        self.assertIn("SERVICE_WORKER_DYNAMIC_ASSERTIONS", gate)
        self.assertIn("service_worker_static_assertions", gate)
        self.assertIn("service_worker_dynamic_no_store_status", gate)
        self.assertIn("statusCacheControl", gate)
        self.assertIn("diagnosticsCacheControl", gate)
        self.assertIn('fetch(event.request, { cache: "no-store" })', service_worker)
        for token in (
            'path.startsWith("/api/")',
            'path.startsWith("/robots/")',
            'path.includes("/commands")',
            'path.includes("/ack")',
            'path.includes("/diagnostics")',
            'request.method !== "GET"',
        ):
            self.assertIn(token, service_worker)

        # 证据 summary 固定 fail-closed 字段；gate 只能证明本地 fresh Chromium software proof。
        self.assertIn('"delivery_success": False', gate)
        self.assertIn('"primary_actions_enabled": False', gate)
        self.assertIn('"safe_to_control": False', gate)
        self.assertIn("primary_actions_disabled", gate)
        self.assertIn("fresh_profile", gate)
        self.assertIn("not_proven", gate)


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


class HardwareSensorHilEntryCallbackIntakeMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_hil_entry_callback_intake_panel_is_read_only_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 回调入口 panel 紧跟 execution pack，只展示回传材料和 operator 结果摘要。
        self.assertIn("hardwareSensorHilEntryCallbackIntakeTitle", app)
        self.assertIn("传感器 HIL 回调入口", app)
        self.assertIn("hardwareSensorHilEntryExecutionPackTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("hardware-sensor-hil-entry-callback-intake-panel", styles)
        self.assertIn("hardware-sensor-hil-entry-callback-intake-grid", styles)

        # 状态来源兼容 status、phone_readiness、diagnostics 和 nested diagnostics summary。
        self.assertIn("HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeHardwareSensorHilEntryCallbackIntakeText", app)
        self.assertIn("hardwareSensorHilEntryCallbackIntakeCandidate", app)
        self.assertIn("hardwareSensorHilEntryCallbackIntakeFromStatus", app)
        self.assertIn("hardware_sensor_hil_entry_callback_intake", app)
        self.assertIn("hardware_sensor_hil_entry_callback_intake_summary", app)
        self.assertIn("diagnosticsSummary.hardware_sensor_hil_entry_callback_intake", app)
        self.assertIn("statusDiagnosticsSummary.hardware_sensor_hil_entry_callback_intake", app)
        self.assertIn("ready_for_hardware_sensor_hil_entry_callback_intake_not_proven", app)
        self.assertIn("source_execution_pack_status", app)
        self.assertIn("hardware_material_status", app)
        self.assertIn("accepted_materials", app)
        self.assertIn("missing_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("operator_result_summary", app)
        self.assertIn("next_required_evidence", app)

        # copy/export whitelist 不新增 diagnostics fetch、ACK、cursor 或主控制端点。
        self.assertIn("hardwareSensorHilEntryCallbackIntakeCopyPayload", app)
        self.assertIn("trashbot.hardware_sensor_hil_entry_callback_intake_copy.v1", app)
        self.assertIn("copyHardwareSensorHilEntryCallbackIntakeButton", app)
        self.assertIn("downloadHardwareSensorHilEntryCallbackIntakeButton", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"hardwareSensorHilEntryCallbackIntake.*fetchJson\(ENDPOINTS\.(diagnostics|start|confirm_dropoff|cancel)")

        # fixture 和产品文档必须明确 fixed fields 与 software proof / not_proven 边界。
        callback_intake = fixture["hardware_sensor_hil_entry_callback_intake"]
        self.assertEqual(callback_intake["source"], "software_proof")
        self.assertEqual(callback_intake["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(callback_intake["evidence_status"], "not_proven")
        self.assertEqual(
            callback_intake["intake_status"],
            "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        )
        self.assertEqual(callback_intake["delivery_success"], False)
        self.assertEqual(callback_intake["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate", fixture_text)
        self.assertIn("hardware_sensor_hil_entry_callback_intake", doc)
        self.assertIn("传感器 HIL 回调入口", doc)

    def test_hil_entry_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        callback_intake_text = json.dumps(
            fixture["hardware_sensor_hil_entry_callback_intake"],
            ensure_ascii=False,
        ).lower()

        # 回调入口 fixture 只能携带脱敏摘要，不能把原始材料、凭证、路径或完成声明带进手机端。
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
            self.assertNotIn(forbidden, callback_intake_text)


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


class RouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_rerun_result_review_decision_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 复核决策跟在 rerun result intake 后，只读展示 handoff/backfill/mismatch/unsafe/unsupported。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionTitle", app)
        self.assertIn("受控复跑结果复核决策", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-review-decision-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-review-decision-grid", app)

        # Robot sanitized alias 必须先于主 summary / artifact，手机端不读取未脱敏复核决策。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_review_decision,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_review_decision", app)
        self.assertIn("decision_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("safe_evidence_ref", app)

        # 该 panel 不提供 copy/export，不 fetch diagnostics，也不触发 Start/Confirm/Cancel。
        decision_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionPanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(
            decision_block,
            r"routeTaskFieldRetestAcceptanceExecutionRerunResultReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionButton", app)

        # fixture、文档和 focused literals 覆盖 handoff/backfill/mismatch/unsafe/unsupported。
        decision = fixture["route_task_field_retest_acceptance_execution_rerun_result_review_decision"]
        self.assertEqual(
            decision["decision_status"],
            "ready_for_acceptance_execution_rerun_result_handoff",
        )
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary",
            fixture,
        )
        for literal in (
            "ready_for_acceptance_execution_rerun_result_handoff",
            "needs_acceptance_execution_rerun_result_backfill",
            "evidence_ref_mismatch_rerun_result",
            "blocked_unsafe_rerun_result",
            "blocked_unsupported_rerun_result_intake",
        ):
            self.assertIn(literal, fixture_text)
            self.assertIn(literal, doc)
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate",
            fixture_text,
        )
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_rerun_result_review_decision", doc)
        self.assertIn("受控复跑结果复核决策", doc)

    def test_field_retest_acceptance_execution_rerun_result_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_rerun_result_review_decision"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"],
            ensure_ascii=False,
        ).lower()

        # 复核决策 fixture 只能携带白名单 metadata，不能泄漏路径、凭证、底层控制或成功语义。
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
            self.assertNotIn(forbidden, decision_text)
            self.assertNotIn(forbidden, alias_text)


class RouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_field_retest_acceptance_execution_rerun_result_review_handoff_panel_is_read_only(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 受控复跑交接跟在复核决策后，只读解释 owner handoff，不改变 Start/Confirm/Cancel gating。
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffTitle", app)
        self.assertIn("受控复跑交接", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-review-handoff-panel", app)
        self.assertIn("route-task-field-retest-acceptance-execution-rerun-result-review-handoff-grid", app)

        # Robot sanitized alias 必须先于主 summary / artifact，手机端不读取未脱敏交接材料。
        alias_index = app.index(
            "status?.robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
        )
        summary_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
        )
        artifact_index = app.index(
            "status?.route_task_field_retest_acceptance_execution_rerun_result_review_handoff,"
        )
        self.assertLess(alias_index, summary_index)
        self.assertLess(summary_index, artifact_index)
        self.assertIn("ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffText", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffCandidate", app)
        self.assertIn("routeTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffFromStatus", app)
        self.assertIn("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary", app)
        self.assertIn("diagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_review_handoff", app)
        self.assertIn("statusDiagnosticsSummary.route_task_field_retest_acceptance_execution_rerun_result_review_handoff", app)
        self.assertIn("handoff_status", app)
        self.assertIn("owner_role", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_summary", app)
        self.assertIn("safe_evidence_ref", app)

        # 该 panel 不提供 copy/export，不 fetch diagnostics，也不触发 Start/Confirm/Cancel。
        handoff_block = app[
            app.index("function ensureRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffPanel"):
            app.index("function ensureRouteTaskFieldRetestEvidenceDispatchPanel")
        ]
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertIn("source=software_proof", app)
        self.assertNotRegex(
            handoff_block,
            r"routeTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffButton", app)
        self.assertNotIn("downloadRouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffButton", app)

        # fixture、文档和 focused literals 覆盖 owner handoff/backfill/mismatch/unsafe/unsupported。
        handoff = fixture["route_task_field_retest_acceptance_execution_rerun_result_review_handoff"]
        self.assertEqual(
            handoff["handoff_status"],
            "ready_for_acceptance_execution_rerun_result_owner_handoff",
        )
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
            fixture,
        )
        for literal in (
            "ready_for_acceptance_execution_rerun_result_owner_handoff",
            "needs_acceptance_execution_rerun_result_material_backfill",
            "evidence_ref_mismatch_rerun_result_handoff_blocked",
            "blocked_unsafe_rerun_result_handoff_copy",
            "blocked_unsupported_rerun_result_review_decision",
        ):
            self.assertIn(literal, fixture_text)
            self.assertIn(literal, doc)
        self.assertIn(
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("source=software_proof", fixture_text)
        self.assertIn("not_proven", fixture_text)
        self.assertIn("delivery_success=false", fixture_text)
        self.assertIn("primary_actions_enabled=false", fixture_text)
        self.assertIn("route_task_field_retest_acceptance_execution_rerun_result_review_handoff", doc)
        self.assertIn("受控复跑交接", doc)

    def test_field_retest_acceptance_execution_rerun_result_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["route_task_field_retest_acceptance_execution_rerun_result_review_handoff"],
            ensure_ascii=False,
        ).lower()
        alias_text = json.dumps(
            fixture["robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"],
            ensure_ascii=False,
        ).lower()

        # 复核交接 fixture 只能携带白名单 metadata，不能泄漏路径、凭证、底层控制或成功语义。
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
            self.assertNotIn(forbidden, handoff_text)
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

    def test_mobile_real_device_field_trial_acceptance_review_decision_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # acceptance review decision 从 acceptance session 派生，只读展示人工复核材料，不改变主按钮 gating。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_DECISION_SCHEMA", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewDecisionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewDecisionFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceReviewDecisionCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceSessionFromStatus", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewDecisionTitle", app)
        self.assertIn("现场验收复核决策", app)
        self.assertIn("generateRealDeviceFieldTrialAcceptanceReviewDecisionButton", app)
        self.assertIn("copyRealDeviceFieldTrialAcceptanceReviewDecisionButton", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        decision = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_review_decision"]
        self.assertEqual(
            decision["review_decision"],
            "blocked_missing_acceptance_review_materials_not_proven",
        )
        self.assertEqual(decision["safe_to_control"], False)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("accepted_materials", decision)
        self.assertIn("missing_materials", decision)
        self.assertIn("rejected_materials", decision)
        self.assertIn("owner_handoff", decision)
        self.assertIn("next_required_evidence", decision)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_review_decision_gate", fixture_text)
        self.assertIn("mobile_real_device_field_trial_acceptance_review_decision", doc)
        self.assertIn("现场验收复核决策", doc)

    def test_mobile_real_device_field_trial_acceptance_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_review_decision"],
            ensure_ascii=False,
        ).lower()

        # review decision fixture 只能携带白名单摘要，不能带 raw 材料、控制授权或真实验收成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
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
            "真实手机已验收",
            "验收通过",
            "control authorization",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_mobile_real_device_field_trial_acceptance_review_handoff_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # acceptance review handoff 消费上游 summary/copy，只读展示现场执行者需要的交接摘要。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceReviewHandoffText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewHandoffCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewHandoffFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceReviewHandoffCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceReviewHandoffTitle", app)
        self.assertIn("现场验收复核交接", app)
        self.assertIn("generateRealDeviceFieldTrialAcceptanceReviewHandoffButton", app)
        self.assertIn("copyRealDeviceFieldTrialAcceptanceReviewHandoffButton", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和文档必须固定 handoff 的 software proof / not_proven / not-control 边界。
        handoff = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_review_handoff"]
        self.assertEqual(
            handoff["handoff_status"],
            "blocked_missing_acceptance_review_handoff_summary_or_safe_copy_not_proven",
        )
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["safe_to_control"], False)
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("owner_handoff", handoff)
        self.assertIn("next_required_evidence", handoff)
        self.assertIn("accepted_materials_summary", handoff)
        self.assertIn("missing_materials_summary", handoff)
        self.assertIn("rejected_materials_summary", handoff)
        self.assertIn("rerun_commands_summary", handoff)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate", fixture_text)
        self.assertIn("mobile_real_device_field_trial_acceptance_review_handoff", doc)
        self.assertIn("现场验收复核交接", doc)

    def test_mobile_real_device_field_trial_acceptance_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_review_handoff"],
            ensure_ascii=False,
        ).lower()

        # handoff fixture 面向现场执行者，只能携带白名单摘要，不能带 raw 材料、控制授权或真实验收成功语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
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
            "credential url",
            "checksum",
            "complete acceptance materials",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "raw intake json",
            "ack payload",
            "cursor",
            "robot/internal",
            "control authorization",
            "真实手机已验收",
            "验收通过",
            "control grant",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_mobile_real_device_field_trial_acceptance_execution_pack_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # execution pack 消费上一轮 handoff safe summary/copy，只读展示现场真实手机验收执行清单。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionPackText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionPackCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionPackFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionPackCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionPackTitle", app)
        self.assertIn("现场真实手机验收执行包", app)
        self.assertIn("generateRealDeviceFieldTrialAcceptanceExecutionPackButton", app)
        self.assertIn("copyRealDeviceFieldTrialAcceptanceExecutionPackButton", app)
        self.assertIn("owner_checklist", app)
        self.assertIn("evidence_capture_steps", app)
        self.assertIn("redaction_requirements", app)
        self.assertIn("rerun_commands", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("safe_to_control: false", app)
        self.assertIn("delivery_success: false", app)
        self.assertIn("primary_actions_enabled: false", app)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture 和文档必须固定 execution pack 的 software proof / not_proven / not-control 边界。
        pack = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_pack"]
        self.assertEqual(
            pack["execution_pack_status"],
            "blocked_missing_acceptance_execution_pack_summary_or_handoff_safe_copy_not_proven",
        )
        self.assertEqual(pack["source"], "software_proof")
        self.assertEqual(pack["safe_to_control"], False)
        self.assertEqual(pack["delivery_success"], False)
        self.assertEqual(pack["primary_actions_enabled"], False)
        self.assertIn("owner_checklist", pack)
        self.assertIn("evidence_capture_steps", pack)
        self.assertIn("redaction_requirements", pack)
        self.assertIn("rerun_commands", pack)
        self.assertIn("next_required_evidence", pack)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_execution_pack_gate", fixture_text)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_pack", doc)
        self.assertIn("现场真实手机验收执行包", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        pack_text = json.dumps(
            fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_pack"],
            ensure_ascii=False,
        ).lower()

        # execution pack fixture 只能携带执行摘要和脱敏要求，不能带 raw 材料、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw review",
            "raw decision",
            "raw execution pack",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete acceptance materials",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "raw intake json",
            "ack payload",
            "cursor",
            "robot/internal",
            "control authorization",
            "field pass",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "control grant",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, pack_text)

    def test_mobile_real_device_field_trial_acceptance_execution_callback_intake_is_fail_closed(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # callback intake 消费 execution pack 或 Robot safe alias，只读展示回调材料分类和 same evidence_ref。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionCallbackIntakeText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackIntakeCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackIntakeFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionCallbackIntakeCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackIntakeTitle", app)
        self.assertIn("现场真实手机验收执行回调入口", app)
        self.assertIn("generateRealDeviceFieldTrialAcceptanceExecutionCallbackIntakeButton", app)
        self.assertIn("copyRealDeviceFieldTrialAcceptanceExecutionCallbackIntakeButton", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary", app)
        self.assertIn("accepted_callback_evidence", app)
        self.assertIn("missing_callback_evidence", app)
        self.assertIn("rejected_callback_evidence", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-intake-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-intake-grid", styles)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceExecutionCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # fixture、Web fixture 和文档必须固定 callback intake 的 software proof / not_proven / not-control 边界。
        callback = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_intake"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"]
        self.assertEqual(callback["callback_intake_status"], "callback_packet_intake_ready_for_review_not_proven")
        self.assertEqual(callback["source"], "software_proof")
        self.assertEqual(callback["safe_to_control"], False)
        self.assertEqual(callback["delivery_success"], False)
        self.assertEqual(callback["primary_actions_enabled"], False)
        self.assertIn("accepted_callback_evidence", callback)
        self.assertIn("missing_callback_evidence", callback)
        self.assertIn("rejected_callback_evidence", callback)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate", fixture_text)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_callback_intake", doc)
        self.assertIn("现场真实手机验收执行回调入口", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        callback_text = json.dumps(
            {
                "callback": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_intake"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # callback intake fixture 只能携带脱敏分类摘要，不能带 raw 回调、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "full callback",
            "complete callback",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete acceptance materials",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "raw intake json",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "field pass",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "control grant",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, callback_text)


    def test_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_is_fail_closed(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # callback review decision 只消费 safe alias/summary，不新增 ACK、diagnostics fetch 或控制请求。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionCallbackReviewDecisionText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecisionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecisionFromStatus", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecisionTitle", app)
        self.assertIn("现场真实手机验收执行回调复核决策", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary", app)
        self.assertIn("review_decision", app)
        self.assertIn("source_callback_intake_status", app)
        self.assertIn("decision_reasons", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-review-decision-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-review-decision-grid", styles)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecisionButton", app)
        self.assertNotIn("downloadRealDeviceFieldTrialAcceptanceExecutionCallbackReviewDecisionButton", app)

        # fixture、Web fixture 和文档必须固定 review decision 的 software proof / not_proven / not-control 边界。
        decision = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_review_decision"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"]
        self.assertEqual(decision["review_decision"], "needs_callback_backfill_not_proven")
        self.assertEqual(decision["source"], "software_proof")
        self.assertEqual(decision["safe_to_control"], False)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("decision_reasons", decision)
        self.assertIn("accepted_callback_evidence", decision)
        self.assertIn("missing_callback_evidence", decision)
        self.assertIn("rejected_callback_evidence", decision)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate",
            fixture_text,
        )
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_callback_review_decision", doc)
        self.assertIn("现场真实手机验收执行回调复核决策", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            {
                "decision": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_review_decision"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # review decision fixture 只能携带脱敏复核结论，不能带 raw review、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "full callback",
            "full review",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete acceptance materials",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "raw intake json",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "field pass",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "control grant",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_is_fail_closed_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # callback review handoff 只消费 Robot safe alias/summary，不新增 ACK、diagnostics fetch 或控制请求。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionCallbackReviewHandoffText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffTitle", app)
        self.assertIn("现场验收回调交接", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary", app)
        self.assertIn("handoff_status", app)
        self.assertIn("source_review_status", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("safe_copy_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-review-handoff-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-callback-review-handoff-grid", styles)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # copy/export 必须存在且只输出 whitelist payload，不能解锁 Start/Confirm/Cancel。
        self.assertIn("copyMobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffButton", app)
        self.assertIn("downloadMobileRealDeviceFieldTrialAcceptanceExecutionCallbackReviewHandoffButton", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_copy.v1", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_copy.json", app)
        self.assertNotRegex(app, r"CallbackReviewHandoff.*latestStartGate\.(startEnabled|can_collect|can_confirm_dropoff|can_cancel)")

        # fixture、Web fixture 和文档必须固定 handoff 的 software proof / not_proven / not-control 边界。
        handoff = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_review_handoff"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"]
        self.assertEqual(handoff["handoff_status"], "ready_for_field_owner_handoff_not_proven")
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["safe_to_control"], False)
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("blocker_summary", handoff)
        self.assertIn("safe_copy_status", handoff)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_callback_review_handoff", doc)
        self.assertIn("现场验收回调交接", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            {
                "handoff": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_callback_review_handoff"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # handoff fixture 只能携带脱敏交接摘要，不能带 raw handoff、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "raw handoff",
            "full callback",
            "full review",
            "full handoff",
            "complete callback",
            "complete review",
            "complete handoff",
            "complete artifact",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "control grant",
            "field pass",
            "hil_pass",
            "hil passed",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_intake_is_fail_closed_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # handoff intake 只消费 Robot safe alias/summary；它不提交 ACK、diagnostics fetch 或控制请求。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionHandoffIntakeText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntakeCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntakeFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionHandoffIntakeCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntakeTitle", app)
        self.assertIn("现场验收交接回执", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary", app)
        self.assertIn("handoff_intake_status", app)
        self.assertIn("source_handoff_status", app)
        self.assertIn("owner_ack_status", app)
        self.assertIn("missing_evidence", app)
        self.assertIn("next_owner", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-intake-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-intake-grid", styles)
        self.assertNotRegex(app, r"mobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")

        # copy/export 必须存在且只输出 whitelist payload，handoff intake metadata 不能解锁 Start/Confirm/Cancel。
        self.assertIn("copyMobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntakeButton", app)
        self.assertIn("downloadMobileRealDeviceFieldTrialAcceptanceExecutionHandoffIntakeButton", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_intake_copy.v1", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_intake_copy.json", app)
        self.assertNotRegex(app, r"HandoffIntake.*latestStartGate\.(startEnabled|can_collect|can_confirm_dropoff|can_cancel)")

        # fixture、Web fixture 和文档必须固定 intake 的 software proof / not_proven / not-control 边界。
        intake = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_intake"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"]
        self.assertEqual(intake["handoff_intake_status"], "ack_received_not_proven")
        self.assertEqual(intake["source"], "software_proof")
        self.assertEqual(intake["safe_to_control"], False)
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn("missing_evidence", intake)
        self.assertIn("next_owner", intake)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_intake_gate",
            fixture_text,
        )
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_intake", doc)
        self.assertIn("现场验收交接回执", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            {
                "handoff_intake": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_intake"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # handoff intake fixture 只能携带脱敏 owner ack 摘要，不能带 raw ack、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw owner ack",
            "raw ack",
            "full callback",
            "full review",
            "full handoff",
            "complete callback",
            "complete review",
            "complete handoff",
            "complete artifact",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "control grant",
            "field pass",
            "hil_pass",
            "hil passed",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, intake_text)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_is_fail_closed_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # handoff review decision 只消费 Robot safe alias/summary；它不提交 ACK、diagnostics fetch 或控制请求。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionHandoffReviewDecisionText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionTitle", app)
        self.assertIn("现场验收交接复核决策", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary", app)
        self.assertIn("review_decision", app)
        self.assertIn("source_handoff_intake_status", app)
        self.assertIn("accepted_summaries", app)
        self.assertIn("missing_summaries", app)
        self.assertIn("rejected_summaries", app)
        self.assertIn("blocked_summaries", app)
        self.assertIn("next_owner", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-review-decision-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-review-decision-grid", styles)
        self.assertNotRegex(
            app,
            r"mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # copy/export 只输出 whitelist payload，复核决策 metadata 不能解锁 Start/Confirm/Cancel。
        self.assertIn("copyMobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionButton", app)
        self.assertIn("downloadMobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewDecisionButton", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_copy.v1", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_copy.json", app)
        self.assertNotRegex(app, r"HandoffReviewDecision.*latestStartGate\.(startEnabled|can_collect|can_confirm_dropoff|can_cancel)")

        # fixture、Web fixture 和文档必须固定 review decision 的 software proof / not_proven / not-control 边界。
        decision = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_review_decision"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"]
        self.assertEqual(decision["review_decision"], "needs_field_owner_follow_up_not_proven")
        self.assertEqual(decision["source"], "software_proof")
        self.assertEqual(decision["safe_to_control"], False)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("accepted_summaries", decision)
        self.assertIn("missing_summaries", decision)
        self.assertIn("rejected_summaries", decision)
        self.assertIn("blocked_summaries", decision)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate",
            fixture_text,
        )
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_review_decision", doc)
        self.assertIn("现场验收交接复核决策", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_is_fail_closed_and_exportable(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # handoff review handoff 只读消费 safe summary；不能提交 ACK、cursor、diagnostics fetch 或控制请求。
        self.assertIn("MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA", app)
        self.assertIn("UNSAFE_REAL_DEVICE_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeRealDeviceAcceptanceExecutionHandoffReviewHandoffText", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffCandidate", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffFromStatus", app)
        self.assertIn("realDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffCopyPayload", app)
        self.assertIn("mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffTitle", app)
        self.assertIn("现场验收交接复核交接", app)
        self.assertIn("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary", app)
        self.assertIn("current_decision", app)
        self.assertIn("handoff_owner", app)
        self.assertIn("handoff_reason", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-review-handoff-panel", styles)
        self.assertIn("real-device-field-trial-acceptance-execution-handoff-review-handoff-grid", styles)
        self.assertNotRegex(
            app,
            r"mobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )

        # copy/export 只输出 whitelist payload，复核交接 metadata 不改变主操作 fail-closed 语义。
        self.assertIn("copyMobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffButton", app)
        self.assertIn("downloadMobileRealDeviceFieldTrialAcceptanceExecutionHandoffReviewHandoffButton", app)
        self.assertIn("trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_copy.v1", app)
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_copy.json", app)
        self.assertNotRegex(app, r"HandoffReviewHandoff.*latestStartGate\.(startEnabled|can_collect|can_confirm_dropoff|can_cancel)")

        # fixture、Web fixture 和文档必须固定 review handoff 的 software proof / not_proven / not-control 边界。
        handoff = fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff"]
        alias = fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"]
        web_alias = web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"]
        self.assertEqual(handoff["current_decision"], "needs_field_owner_follow_up_not_proven")
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["safe_to_control"], False)
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("accepted_summaries", handoff)
        self.assertIn("missing_summaries", handoff)
        self.assertIn("rejected_summaries", handoff)
        self.assertIn("blocked_summaries", handoff)
        self.assertIn("next_required_evidence", handoff)
        self.assertEqual(alias["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff", doc)
        self.assertIn("现场验收交接复核交接", doc)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            {
                "handoff_review_decision": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_review_decision"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # review decision fixture 只能携带脱敏复核摘要，不能带 raw JSON、完整 artifact、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw intake",
            "raw owner ack",
            "raw ack",
            "full callback",
            "full review",
            "full handoff",
            "full intake",
            "complete callback",
            "complete review",
            "complete handoff",
            "complete intake",
            "complete artifact",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "control grant",
            "field pass",
            "hil_pass",
            "hil passed",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            {
                "handoff_review_handoff": fixture["phone_readiness"]["mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff"],
                "alias": fixture["phone_readiness"]["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"],
                "web_alias": web_fixture["robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # review handoff fixture 只能携带脱敏交接摘要，不能带 raw handoff、ACK/cursor、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw intake",
            "raw owner ack",
            "raw ack",
            "full callback",
            "full review",
            "full handoff",
            "full intake",
            "complete callback",
            "complete review",
            "complete handoff",
            "complete intake",
            "complete artifact",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "control grant",
            "field pass",
            "hil_pass",
            "hil passed",
            "真实手机已验收",
            "验收通过",
            "现场通过",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

class ElevatorRealtimeActionFeedbackMobileTest(unittest.TestCase):
    def read_web(self, name):
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_elevator_realtime_stage_consumes_current_step_whitelist(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")

        # 实时阶段必须来自 action feedback 的 current_step=elevator:<phase>，不能从旧 checklist 推断。
        self.assertIn("ELEVATOR_ACTION_PHASES", app)
        self.assertIn("elevatorActionFeedbackCandidate", app)
        self.assertIn("elevatorCurrentStepFromFeedback", app)
        self.assertIn("elevatorActionFeedbackFromStatus", app)
        self.assertIn("current_step=elevator:<phase>", app)
        for phase in (
            "waiting_elevator_open",
            "entering_elevator",
            "requesting_floor_help",
            "waiting_target_floor",
            "exiting_elevator",
            "resume_delivery",
        ):
            self.assertIn(phase, app)

        # panel 只读展示，不新增 Start Delivery / Confirm Dropoff / Cancel 请求路径。
        self.assertIn("elevatorRealtimeStageTitle", app)
        self.assertIn("电梯实时阶段", app)
        self.assertIn("elevator-realtime-stage-panel", styles)
        self.assertIn("elevator-realtime-stage-grid", styles)
        self.assertIn("UNSAFE_ELEVATOR_ACTION_FEEDBACK_TEXT", app)
        self.assertIn("safeElevatorActionFeedbackText", app)
        self.assertNotRegex(app, r"elevatorRealtimeStage.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

        feedback = fixture["phone_action_feedback"]
        self.assertEqual(feedback["current_step"], "elevator:waiting_elevator_open")
        self.assertEqual(feedback["delivery_success"], False)
        self.assertEqual(feedback["primary_actions_enabled"], False)
        mobile_feedback = mobile_fixture["phone_action_feedback"]
        self.assertEqual(mobile_feedback["current_step"], "elevator:requesting_floor_help")
        self.assertEqual(mobile_feedback["delivery_success"], False)
        self.assertEqual(mobile_feedback["primary_actions_enabled"], False)
        self.assertIn("电梯实时阶段", doc)
        self.assertIn("software_proof", doc)
        self.assertIn("not_proven", doc)

    def test_elevator_action_feedback_trace_panel_is_read_only_and_whitelisted(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")

        # post-run trace 优先消费 Robot diagnostics safe summary，并保持白名单字段渲染。
        self.assertIn("ELEVATOR_ACTION_FEEDBACK_TRACE_BOUNDARY", app)
        self.assertIn("elevatorActionFeedbackTraceCandidate", app)
        self.assertIn("elevatorActionFeedbackTraceFromStatus", app)
        self.assertIn("robot_diagnostics_elevator_action_feedback_trace_summary", app)
        self.assertIn("status?.elevator_action_feedback_trace", app)
        self.assertIn("status?.last_task?.elevator_action_feedback_trace", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("source_boundary", app)
        self.assertIn("phases", app)
        self.assertIn("电梯动作反馈追踪", app)
        self.assertIn("elevator-action-feedback-trace-panel", styles)
        self.assertIn("elevator-action-feedback-trace-grid", styles)

        # panel 不新增任何控制请求，missing/unknown/non-elevator 必须 fail closed。
        self.assertIn("非电梯或未知阶段 fail closed", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"elevatorActionFeedbackTrace.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        trace = fixture["robot_diagnostics_elevator_action_feedback_trace_summary"]
        self.assertEqual(trace["source_boundary"], "software_proof")
        self.assertEqual(trace["status"], "not_proven")
        self.assertEqual(trace["current_step"], "elevator:waiting_elevator_open")
        self.assertEqual(trace["delivery_success"], False)
        self.assertEqual(trace["primary_actions_enabled"], False)
        mobile_trace = mobile_fixture["robot_diagnostics_elevator_action_feedback_trace_summary"]
        self.assertEqual(mobile_trace["current_step"], "elevator:requesting_floor_help")
        self.assertEqual(mobile_trace["delivery_success"], False)
        self.assertEqual(mobile_trace["primary_actions_enabled"], False)
        self.assertIn("elevator_action_feedback_trace", doc)
        self.assertIn("robot_diagnostics_elevator_action_feedback_trace_summary", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_action_feedback_trace_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        trace_text = json.dumps(
            fixture["robot_diagnostics_elevator_action_feedback_trace_summary"],
            ensure_ascii=False,
        ).lower()

        # trace fixture 只能包含 phone-safe 摘要，不能携带 raw ROS、路径、凭证、checksum 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "local path",
            "/users/",
            "/tmp/",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "control grant",
            "control enabled",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, trace_text)

    def test_elevator_field_evidence_trace_callback_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # callback intake panel 跟在 elevator action trace 后，只读展示 Robot diagnostics safe alias。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceCallbackIntakeText", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackIntakeCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary", app)
        self.assertIn("elevator_field_evidence_trace_callback_intake_summary", app)
        self.assertIn("status?.elevator_field_evidence_trace_callback_intake", app)
        self.assertIn("diagnosticsSummary.elevator_field_evidence_trace_callback_intake", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_evidence_trace_callback_intake", app)
        self.assertIn("电梯现场证据追踪回调入口", app)
        self.assertIn("elevator-field-evidence-trace-callback-intake-panel", styles)
        self.assertIn("elevator-field-evidence-trace-callback-intake-grid", styles)

        # panel 只显示白名单字段，不新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("intake_status", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("accepted_callback_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("not_proven", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceCallbackIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceCallbackIntakeButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceCallbackIntakeButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        intake = fixture["robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary"]
        self.assertEqual(intake["source"], "software_proof")
        self.assertEqual(
            intake["intake_status"],
            "blocked_missing_elevator_field_evidence_trace_callback_intake_not_proven",
        )
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        mobile_intake = mobile_fixture["elevator_field_evidence_trace_callback_intake_summary"]
        self.assertEqual(mobile_intake["delivery_success"], False)
        self.assertEqual(mobile_intake["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_elevator_field_evidence_trace_callback_intake_gate", fixture_text)
        self.assertIn("missing_required_materials", fixture_text)
        self.assertIn("accepted_callback_materials", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("elevator_field_evidence_trace_callback_intake", doc)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_callback_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            {
                "web": fixture["robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary"],
                "mobile": mobile_fixture["elevator_field_evidence_trace_callback_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # callback intake fixture 不能泄漏 raw callback、内部日志、路径、凭证、topic 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw diagnostics",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, intake_text)

    def test_elevator_field_evidence_trace_callback_review_decision_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # review decision panel 紧跟 callback intake，只读展示复核结论和下一步证据。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceCallbackReviewDecisionText", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewDecisionCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewDecisionFromStatus", app)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary", app)
        self.assertIn("elevator_field_evidence_trace_callback_review_decision_summary", app)
        self.assertIn("status?.elevator_field_evidence_trace_callback_review_decision", app)
        self.assertIn("diagnosticsSummary.elevator_field_evidence_trace_callback_review_decision", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_evidence_trace_callback_review_decision", app)
        self.assertIn("电梯现场证据回调复核决策", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackIntakeTitle", app)
        self.assertIn('anchor.insertAdjacentElement("afterend", panel)', app)
        self.assertIn("elevator-field-evidence-trace-callback-review-decision-panel", styles)
        self.assertIn("elevator-field-evidence-trace-callback-review-decision-grid", styles)

        # panel 只显示白名单字段，不新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("review_decision", app)
        self.assertIn("source_callback_intake", app)
        self.assertIn("decision_reasons", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("rejected_callback_materials", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceCallbackReviewDecisionButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceCallbackReviewDecisionButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        decision = fixture["robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary"]
        self.assertEqual(decision["source"], "software_proof")
        self.assertEqual(decision["overall_status"], "not_proven")
        self.assertEqual(decision["review_decision"], "needs_route_elevator_material_backfill_not_proven")
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        mobile_decision = mobile_fixture["elevator_field_evidence_trace_callback_review_decision_summary"]
        self.assertEqual(mobile_decision["delivery_success"], False)
        self.assertEqual(mobile_decision["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate",
            fixture_text,
        )
        self.assertIn("decision_reasons", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("elevator_field_evidence_trace_callback_review_decision", doc)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            {
                "web": fixture["robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary"],
                "mobile": mobile_fixture["elevator_field_evidence_trace_callback_review_decision_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # review decision fixture 不能泄漏 raw review、内部日志、路径、凭证、topic 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw review",
            "raw decision",
            "raw diagnostics",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_elevator_field_evidence_trace_callback_review_handoff_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # handoff panel 紧跟 review decision，只展示 owner 交接和缺口，不新增控制或诊断抓取。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceCallbackReviewHandoffText", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewHandoffCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewHandoffFromStatus", app)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary", app)
        self.assertIn("elevator_field_evidence_trace_callback_review_handoff_summary", app)
        self.assertIn("status?.elevator_field_evidence_trace_callback_review_handoff", app)
        self.assertIn("diagnosticsSummary.elevator_field_evidence_trace_callback_review_handoff", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_evidence_trace_callback_review_handoff", app)
        self.assertIn("电梯现场证据回调复核交接", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewDecisionTitle", app)
        self.assertIn("elevator-field-evidence-trace-callback-review-handoff-panel", styles)
        self.assertIn("elevator-field-evidence-trace-callback-review-handoff-grid", styles)

        # panel 只显示白名单 handoff 字段，不能新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("handoff_status", app)
        self.assertIn("source_review_decision", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceCallbackReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceCallbackReviewHandoffButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceCallbackReviewHandoffButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        handoff = fixture["robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary"]
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["overall_status"], "not_proven")
        self.assertEqual(handoff["handoff_status"], "ready_for_owner_material_backfill_not_proven")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        mobile_handoff = mobile_fixture["elevator_field_evidence_trace_callback_review_handoff_summary"]
        self.assertEqual(mobile_handoff["delivery_success"], False)
        self.assertEqual(mobile_handoff["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("handoff_status", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("owner_handoff", fixture_text)
        self.assertIn("elevator_field_evidence_trace_callback_review_handoff", doc)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_callback_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            {
                "web": fixture["robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary"],
                "mobile": mobile_fixture["elevator_field_evidence_trace_callback_review_handoff_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # handoff fixture 只能承载脱敏 owner 交接，不能泄漏 raw handoff 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw diagnostics",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_elevator_field_evidence_trace_material_backfill_intake_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # material backfill intake 紧跟 handoff，只展示 Robot diagnostics safe alias 和白名单字段。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceMaterialBackfillIntakeText", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillIntakeCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillIntakeFromStatus", app)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary", app)
        self.assertIn("elevator_field_evidence_trace_material_backfill_intake_summary", app)
        self.assertIn("status?.elevator_field_evidence_trace_material_backfill_intake", app)
        self.assertIn("diagnosticsSummary.elevator_field_evidence_trace_material_backfill_intake", app)
        self.assertIn("statusDiagnosticsSummary.elevator_field_evidence_trace_material_backfill_intake", app)
        self.assertIn("电梯现场证据材料回填入口", app)
        self.assertIn("elevatorFieldEvidenceTraceCallbackReviewHandoffTitle", app)
        self.assertIn("elevator-field-evidence-trace-material-backfill-intake-panel", styles)
        self.assertIn("elevator-field-evidence-trace-material-backfill-intake-grid", styles)

        # panel 只显示 intake 和材料回填摘要，不新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("intake_status", app)
        self.assertIn("source_review_handoff", app)
        self.assertIn("accepted_material_refs", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceMaterialBackfillIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceMaterialBackfillIntakeButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceMaterialBackfillIntakeButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        backfill = fixture["robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary"]
        self.assertEqual(backfill["source"], "software_proof")
        self.assertEqual(backfill["overall_status"], "not_proven")
        self.assertEqual(
            backfill["intake_status"],
            "blocked_missing_elevator_field_evidence_trace_material_backfill_intake_not_proven",
        )
        self.assertEqual(backfill["delivery_success"], False)
        self.assertEqual(backfill["primary_actions_enabled"], False)
        mobile_backfill = mobile_fixture["elevator_field_evidence_trace_material_backfill_intake_summary"]
        self.assertEqual(mobile_backfill["delivery_success"], False)
        self.assertEqual(mobile_backfill["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate",
            fixture_text,
        )
        self.assertIn("accepted_material_refs", fixture_text)
        self.assertIn("missing_required_materials", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("elevator_field_evidence_trace_material_backfill_intake", doc)
        self.assertIn("robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary", doc)
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_material_backfill_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        backfill_text = json.dumps(
            {
                "web": fixture["robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary"],
                "mobile": mobile_fixture["elevator_field_evidence_trace_material_backfill_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # backfill fixture 只能承载脱敏 material refs，不能泄漏 raw material 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw material",
            "raw backfill",
            "raw diagnostics",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, backfill_text)

    def test_elevator_field_evidence_trace_material_backfill_review_decision_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # review decision panel 优先消费 Robot diagnostics safe alias，fixture/artifact 仅作白名单回退。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceMaterialBackfillReviewDecisionText", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillReviewDecisionCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillReviewDecisionFromStatus", app)
        self.assertIn(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary",
            app,
        )
        self.assertIn("elevator_field_evidence_trace_material_backfill_review_decision_summary", app)
        self.assertIn("status?.elevator_field_evidence_trace_material_backfill_review_decision", app)
        self.assertIn(
            "diagnosticsSummary.elevator_field_evidence_trace_material_backfill_review_decision",
            app,
        )
        self.assertIn("电梯现场证据材料回填复核决策", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillIntakeTitle", app)
        self.assertIn("elevator-field-evidence-trace-material-backfill-review-decision-panel", styles)
        self.assertIn("elevator-field-evidence-trace-material-backfill-review-decision-grid", styles)

        # panel 展示复核结论和材料分类，但不新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("review_decision", app)
        self.assertIn("decision_reasons", app)
        self.assertIn("accepted_material_refs", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceMaterialBackfillReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceMaterialBackfillReviewDecisionButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceMaterialBackfillReviewDecisionButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        decision = fixture[
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ]
        self.assertEqual(decision["source"], "software_proof")
        self.assertEqual(decision["overall_status"], "not_proven")
        self.assertEqual(
            decision["review_decision"],
            "needs_required_material_backfill_not_proven",
        )
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        mobile_decision = mobile_fixture[
            "elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ]
        self.assertEqual(mobile_decision["delivery_success"], False)
        self.assertEqual(mobile_decision["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate",
            fixture_text,
        )
        self.assertIn("review_decision", fixture_text)
        self.assertIn("missing_required_materials", fixture_text)
        self.assertIn("next_required_evidence", fixture_text)
        self.assertIn("elevator_field_evidence_trace_material_backfill_review_decision", doc)
        self.assertIn(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary",
            doc,
        )
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_material_backfill_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            {
                "web": fixture[
                    "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary"
                ],
                "mobile": mobile_fixture[
                    "elevator_field_evidence_trace_material_backfill_review_decision_summary"
                ],
            },
            ensure_ascii=False,
        ).lower()

        # review decision fixture 只能承载脱敏复核材料，不能泄漏 raw review 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw material",
            "raw backfill",
            "raw diagnostics",
            "raw path",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_elevator_field_evidence_trace_material_backfill_review_handoff_panel_is_read_only(self):
        app = self.read_web("app.js")
        styles = self.read_web("styles.css")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # review handoff panel 优先消费 Robot diagnostics alias；summary 回退不能读取 raw artifact。
        self.assertIn("ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeElevatorFieldEvidenceTraceMaterialBackfillReviewHandoffText", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillReviewHandoffCandidate", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillReviewHandoffFromStatus", app)
        self.assertIn(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary",
            app,
        )
        self.assertIn("elevator_field_evidence_trace_material_backfill_review_handoff_summary", app)
        self.assertIn(
            "diagnosticsSummary.elevator_field_evidence_trace_material_backfill_review_handoff",
            app,
        )
        self.assertIn(
            "statusDiagnosticsSummary.elevator_field_evidence_trace_material_backfill_review_handoff",
            app,
        )
        self.assertIn("电梯现场证据材料回填复核交接", app)
        self.assertIn("elevatorFieldEvidenceTraceMaterialBackfillReviewDecisionTitle", app)
        self.assertIn("elevator-field-evidence-trace-material-backfill-review-handoff-panel", styles)
        self.assertIn("elevator-field-evidence-trace-material-backfill-review-handoff-grid", styles)

        # panel 只显示交接字段，不新增 copy/export、diagnostics fetch 或主操作请求。
        self.assertIn("handoff_status", app)
        self.assertIn("safe_evidence_ref", app)
        self.assertIn("field_owner_handoff", app)
        self.assertIn("safe_rerun_hints", app)
        self.assertIn("phone_safe_copy", app)
        self.assertIn("missing_required_materials", app)
        self.assertIn("rejected_materials", app)
        self.assertIn("delivery_success=false / primary_actions_enabled=false", app)
        self.assertIn("Start Delivery", app)
        self.assertIn("Confirm Dropoff", app)
        self.assertIn("Cancel", app)
        self.assertNotRegex(
            app,
            r"elevatorFieldEvidenceTraceMaterialBackfillReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)",
        )
        self.assertNotIn("copyElevatorFieldEvidenceTraceMaterialBackfillReviewHandoffButton", app)
        self.assertNotIn("downloadElevatorFieldEvidenceTraceMaterialBackfillReviewHandoffButton", app)

        # web/mobile fixture 和产品文档固定 software_proof/not_proven 边界。
        handoff = fixture[
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ]
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["overall_status"], "not_proven")
        self.assertEqual(handoff["handoff_status"], "ready_for_field_owner_follow_up_not_proven")
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        mobile_handoff = mobile_fixture[
            "elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ]
        self.assertEqual(mobile_handoff["delivery_success"], False)
        self.assertEqual(mobile_handoff["primary_actions_enabled"], False)
        self.assertIn(
            "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_handoff_gate",
            fixture_text,
        )
        self.assertIn("field_owner_handoff", fixture_text)
        self.assertIn("safe_rerun_hints", fixture_text)
        self.assertIn("phone_safe_copy", fixture_text)
        self.assertIn("elevator_field_evidence_trace_material_backfill_review_handoff", doc)
        self.assertIn(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary",
            doc,
        )
        self.assertIn("delivery_success=false", doc)
        self.assertIn("primary_actions_enabled=false", doc)

    def test_elevator_field_evidence_trace_material_backfill_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mobile_fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            {
                "web": fixture[
                    "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
                ],
                "mobile": mobile_fixture[
                    "elevator_field_evidence_trace_material_backfill_review_handoff_summary"
                ],
            },
            ensure_ascii=False,
        ).lower()

        # handoff fixture 只能承载脱敏交接和 rerun hint，不能泄漏 raw handoff 或成功/控制授权语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw callback",
            "raw packet",
            "raw review",
            "raw decision",
            "raw handoff",
            "raw material",
            "raw backfill",
            "raw diagnostics",
            "raw path",
            "raw internal log",
            "/users/",
            "/tmp/",
            "serial device",
            "uart device",
            "baudrate",
            "authorization",
            "token",
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "ack payload",
            "cursor",
            "robot command",
            "diagnostics fetch",
            "control grant",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_field_evidence_rerun_callback_review_decision_panel_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 回执复核 panel 只消费 Robot safe alias/summary，不新增 raw fetch、ACK、cursor 或控制请求。
        self.assertIn("FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_BOUNDARY", app)
        self.assertIn("UNSAFE_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_TEXT", app)
        self.assertIn("safeFieldEvidenceRerunCallbackReviewDecisionText", app)
        self.assertIn("fieldEvidenceRerunCallbackReviewDecisionCandidate", app)
        self.assertIn("fieldEvidenceRerunCallbackReviewDecisionFromStatus", app)
        self.assertIn("renderFieldEvidenceRerunCallbackReviewDecision", app)
        self.assertIn("现场证据复跑回执复核", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_callback_review_decision_summary", app)
        self.assertIn("field_evidence_rerun_callback_review_decision_summary", app)
        self.assertIn("field_evidence_rerun_callback_review_decision?.summary", app)
        self.assertIn("review_decision", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunCallbackReviewDecision.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyFieldEvidenceRerunCallbackReviewDecisionButton", app)
        self.assertNotIn("downloadFieldEvidenceRerunCallbackReviewDecisionButton", app)

        # fixture、Web fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        decision = fixture["robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"]
        fallback = fixture["field_evidence_rerun_callback_review_decision_summary"]
        web_alias = web_fixture["robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"]
        self.assertEqual(decision["review_decision"], "missing")
        self.assertEqual(decision["source"], "software_proof")
        self.assertEqual(decision["safe_to_control"], False)
        self.assertEqual(decision["delivery_success"], False)
        self.assertEqual(decision["primary_actions_enabled"], False)
        self.assertIn("owner_handoff", decision)
        self.assertIn("next_required_evidence", decision)
        self.assertIn("rerun_guidance", decision)
        self.assertIn("blocker_summary", decision)
        self.assertEqual(fallback["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_field_evidence_rerun_callback_review_decision_gate", fixture_text)
        self.assertIn("field_evidence_rerun_callback_review_decision", doc)
        self.assertIn("现场证据复跑回执复核", doc)

    def test_field_evidence_rerun_callback_review_decision_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        decision_text = json.dumps(
            {
                "decision": fixture["robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"],
                "fallback": fixture["field_evidence_rerun_callback_review_decision_summary"],
                "web_alias": web_fixture["robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 回执复核 fixture 只能承载脱敏复核结论，不能泄漏 raw review、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw decision",
            "full callback",
            "full review",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, decision_text)

    def test_field_evidence_rerun_callback_review_handoff_panel_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 复核交接 panel 只消费 safe handoff summary，不新增 raw fetch、ACK、cursor 或控制请求。
        self.assertIn("FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_BOUNDARY", app)
        self.assertIn("UNSAFE_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_TEXT", app)
        self.assertIn("safeFieldEvidenceRerunCallbackReviewHandoffText", app)
        self.assertIn("fieldEvidenceRerunCallbackReviewHandoffCandidate", app)
        self.assertIn("fieldEvidenceRerunCallbackReviewHandoffFromStatus", app)
        self.assertIn("renderFieldEvidenceRerunCallbackReviewHandoff", app)
        self.assertIn("现场证据复跑复核交接", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary", app)
        self.assertIn("field_evidence_rerun_callback_review_handoff_summary", app)
        self.assertIn("field_evidence_rerun_callback_review_handoff?.summary", app)
        self.assertIn("handoff_status", app)
        self.assertIn("handoff_owner", app)
        self.assertIn("handoff_reason", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunCallbackReviewHandoff.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyFieldEvidenceRerunCallbackReviewHandoffButton", app)
        self.assertNotIn("downloadFieldEvidenceRerunCallbackReviewHandoffButton", app)

        # fixture、Web fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        handoff = fixture["robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"]
        fallback = fixture["field_evidence_rerun_callback_review_handoff_summary"]
        web_alias = web_fixture["robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"]
        self.assertEqual(handoff["handoff_status"], "ready_for_field_owner_rerun_handoff_not_proven")
        self.assertEqual(handoff["source"], "software_proof")
        self.assertEqual(handoff["safe_to_control"], False)
        self.assertEqual(handoff["delivery_success"], False)
        self.assertEqual(handoff["primary_actions_enabled"], False)
        self.assertIn("handoff_owner", handoff)
        self.assertIn("handoff_reason", handoff)
        self.assertIn("next_required_evidence", handoff)
        self.assertIn("rerun_guidance", handoff)
        self.assertIn("blocker_summary", handoff)
        self.assertEqual(fallback["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertIn("software_proof_docker_field_evidence_rerun_callback_review_handoff_gate", fixture_text)
        self.assertIn("field_evidence_rerun_callback_review_handoff", doc)
        self.assertIn("现场证据复跑复核交接", doc)
        self.assertIn("not PR #5 hardware proof", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_callback_review_handoff_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        handoff_text = json.dumps(
            {
                "handoff": fixture["robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"],
                "fallback": fixture["field_evidence_rerun_callback_review_handoff_summary"],
                "web_alias": web_fixture["robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 复核交接 fixture 只能承载脱敏交接结论，不能泄漏 raw handoff、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw handoff",
            "full callback",
            "full review",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "robot command",
            "robot/internal",
            "control authorization",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, handoff_text)

    def test_field_evidence_rerun_handoff_intake_panel_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 交接回执 panel 只消费 safe intake summary，不新增 raw fetch、ACK、cursor、copy/export 或控制请求。
        self.assertIn("FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_BOUNDARY", app)
        self.assertIn("UNSAFE_FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_TEXT", app)
        self.assertIn("safeFieldEvidenceRerunHandoffIntakeText", app)
        self.assertIn("fieldEvidenceRerunHandoffIntakeCandidate", app)
        self.assertIn("fieldEvidenceRerunHandoffIntakeFromStatus", app)
        self.assertIn("renderFieldEvidenceRerunHandoffIntake", app)
        self.assertIn("现场证据复跑交接回执", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_handoff_intake_summary", app)
        self.assertIn("field_evidence_rerun_handoff_intake_summary", app)
        self.assertIn("field_evidence_rerun_handoff_intake?.summary", app)
        self.assertIn("intake_status", app)
        self.assertIn("handoff_owner", app)
        self.assertIn("intake_receipt", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunHandoffIntake.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyFieldEvidenceRerunHandoffIntakeButton", app)
        self.assertNotIn("downloadFieldEvidenceRerunHandoffIntakeButton", app)
        self.assertNotIn("automaticRetryFieldEvidenceRerunHandoffIntake", app)

        # fixture、Web fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        intake = fixture["robot_diagnostics_field_evidence_rerun_handoff_intake_summary"]
        fallback = fixture["field_evidence_rerun_handoff_intake_summary"]
        web_alias = web_fixture["robot_diagnostics_field_evidence_rerun_handoff_intake_summary"]
        self.assertEqual(intake["intake_status"], "ready_for_field_owner_handoff_intake_not_proven")
        self.assertEqual(intake["source"], "software_proof")
        self.assertEqual(intake["safe_to_control"], False)
        self.assertEqual(intake["delivery_success"], False)
        self.assertEqual(intake["primary_actions_enabled"], False)
        self.assertIn("handoff_owner", intake)
        self.assertIn("intake_receipt", intake)
        self.assertIn("next_required_evidence", intake)
        self.assertIn("rerun_guidance", intake)
        self.assertIn("blocker_summary", intake)
        self.assertEqual(fallback["source"], "software_proof")
        self.assertEqual(web_alias["primary_actions_enabled"], False)
        self.assertEqual(web_fixture["can_collect"], False)
        self.assertEqual(web_fixture["can_confirm_dropoff"], False)
        self.assertEqual(web_fixture["can_cancel"], False)
        self.assertIn("software_proof_docker_field_evidence_rerun_handoff_intake_gate", fixture_text)
        self.assertIn("field_evidence_rerun_handoff_intake", doc)
        self.assertIn("现场证据复跑交接回执", doc)
        self.assertIn("not PR #5 hardware proof", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_handoff_intake_fixture_stays_phone_safe(self):
        fixture = json.loads(MOBILE_STATUS_FIXTURE.read_text(encoding="utf-8"))
        web_fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        intake_text = json.dumps(
            {
                "intake": fixture["robot_diagnostics_field_evidence_rerun_handoff_intake_summary"],
                "fallback": fixture["field_evidence_rerun_handoff_intake_summary"],
                "web_alias": web_fixture["robot_diagnostics_field_evidence_rerun_handoff_intake_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 交接回执 fixture 只能承载脱敏回执结论，不能泄漏 raw intake、控制授权或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw handoff",
            "raw intake",
            "raw packet",
            "full callback",
            "full review",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "automatic retry",
            "copy/export control",
            "robot command",
            "robot/internal",
            "control authorization",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, intake_text)

    def test_field_evidence_rerun_queue_panel_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 复跑队列 panel 只消费 safe summary，不新增 queue scheduling、diagnostics fetch 或控制请求。
        self.assertIn("FIELD_EVIDENCE_RERUN_QUEUE_BOUNDARY", app)
        self.assertIn("UNSAFE_FIELD_EVIDENCE_RERUN_QUEUE_TEXT", app)
        self.assertIn("safeFieldEvidenceRerunQueueText", app)
        self.assertIn("fieldEvidenceRerunQueueCandidate", app)
        self.assertIn("fieldEvidenceRerunQueueFromStatus", app)
        self.assertIn("renderFieldEvidenceRerunQueue", app)
        self.assertIn("现场证据复跑队列", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_queue_summary", app)
        self.assertIn("field_evidence_rerun_queue_summary", app)
        self.assertIn("field_evidence_rerun_queue?.summary", app)
        self.assertIn("queue_status", app)
        self.assertIn("source_handoff_intake_status", app)
        self.assertIn("next_required_evidence", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("safe_rerun_hint", app)
        self.assertIn("rerun_guidance", app)
        self.assertIn("blocker_summary", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunQueue.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyFieldEvidenceRerunQueueButton", app)
        self.assertNotIn("downloadFieldEvidenceRerunQueueButton", app)
        self.assertNotIn("scheduleFieldEvidenceRerunQueue", app)

        # Web fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        queue = fixture["robot_diagnostics_field_evidence_rerun_queue_summary"]
        fallback = fixture["field_evidence_rerun_queue_summary"]
        self.assertEqual(queue["queue_status"], "ready_for_field_owner_rerun_queue_not_proven")
        self.assertEqual(queue["source"], "software_proof")
        self.assertEqual(queue["safe_to_control"], False)
        self.assertEqual(queue["delivery_success"], False)
        self.assertEqual(queue["primary_actions_enabled"], False)
        self.assertIn("source_handoff_intake_status", queue)
        self.assertIn("same_evidence_ref_status", queue)
        self.assertIn("blocker_summary", queue)
        self.assertIn("next_required_evidence", queue)
        self.assertIn("owner_handoff", queue)
        self.assertIn("rerun_guidance", queue)
        self.assertIn("safe_rerun_hint", queue)
        self.assertEqual(fallback["source"], "software_proof")
        self.assertEqual(fallback["primary_actions_enabled"], False)
        self.assertEqual(fixture["can_collect"], False)
        self.assertEqual(fixture["can_confirm_dropoff"], False)
        self.assertEqual(fixture["can_cancel"], False)
        self.assertIn("software_proof_docker_field_evidence_rerun_queue_gate", fixture_text)
        self.assertIn("field_evidence_rerun_queue", doc)
        self.assertIn("现场证据复跑队列", doc)
        self.assertIn("not PR #5 hardware proof", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_queue_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        queue_text = json.dumps(
            {
                "queue": fixture["robot_diagnostics_field_evidence_rerun_queue_summary"],
                "fallback": fixture["field_evidence_rerun_queue_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 队列 fixture 只能承载脱敏排队摘要，不能泄漏 raw queue、底层控制或现场通过语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw handoff",
            "raw intake",
            "raw packet",
            "raw queue",
            "full callback",
            "full review",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "automatic retry",
            "queue scheduling",
            "robot command",
            "robot/internal",
            "control authorization",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, queue_text)

    def test_field_evidence_rerun_execution_pack_panel_is_fail_closed(self):
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = json.dumps(fixture, ensure_ascii=False)
        doc = DOC.read_text(encoding="utf-8")

        # 执行包 panel 只消费 safe execution-pack summary，不新增 execution scheduling、diagnostics fetch 或控制请求。
        self.assertIn("FIELD_EVIDENCE_RERUN_EXECUTION_PACK_BOUNDARY", app)
        self.assertIn("UNSAFE_FIELD_EVIDENCE_RERUN_EXECUTION_PACK_TEXT", app)
        self.assertIn("safeFieldEvidenceRerunExecutionPackText", app)
        self.assertIn("fieldEvidenceRerunExecutionPackCandidate", app)
        self.assertIn("fieldEvidenceRerunExecutionPackFromStatus", app)
        self.assertIn("renderFieldEvidenceRerunExecutionPack", app)
        self.assertIn("现场证据复跑执行包", app)
        self.assertIn("robot_diagnostics_field_evidence_rerun_execution_pack_summary", app)
        self.assertIn("field_evidence_rerun_execution_pack_summary", app)
        self.assertIn("field_evidence_rerun_execution_pack?.summary", app)
        self.assertIn("execution_status", app)
        self.assertIn("source_queue_status", app)
        self.assertIn("execution_steps", app)
        self.assertIn("material_templates", app)
        self.assertIn("owner_handoff", app)
        self.assertIn("fail_thresholds", app)
        self.assertIn("pass_thresholds", app)
        self.assertIn("backfill_instructions", app)
        self.assertIn("same_evidence_ref_status", app)
        self.assertIn("source=software_proof", app)
        self.assertIn("safe_to_control=false", app)
        self.assertIn("delivery_success=false", app)
        self.assertIn("primary_actions_enabled=false", app)
        self.assertNotRegex(app, r"fieldEvidenceRerunExecutionPack.*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel|diagnostics)")
        self.assertNotIn("copyFieldEvidenceRerunExecutionPackButton", app)
        self.assertNotIn("downloadFieldEvidenceRerunExecutionPackButton", app)
        self.assertNotIn("scheduleFieldEvidenceRerunExecutionPack", app)
        self.assertNotIn("executionSchedulingFieldEvidenceRerunExecutionPack", app)

        # Web fixture 和文档必须固定 software proof / not_proven / not-control 边界。
        pack = fixture["robot_diagnostics_field_evidence_rerun_execution_pack_summary"]
        fallback = fixture["field_evidence_rerun_execution_pack_summary"]
        self.assertEqual(pack["execution_status"], "ready_for_field_owner_execution_pack_not_proven")
        self.assertEqual(pack["source"], "software_proof")
        self.assertEqual(pack["safe_to_control"], False)
        self.assertEqual(pack["delivery_success"], False)
        self.assertEqual(pack["primary_actions_enabled"], False)
        self.assertIn("source_queue_status", pack)
        self.assertIn("same_evidence_ref_status", pack)
        self.assertIn("execution_steps", pack)
        self.assertIn("material_templates", pack)
        self.assertIn("owner_handoff", pack)
        self.assertIn("fail_thresholds", pack)
        self.assertIn("pass_thresholds", pack)
        self.assertIn("backfill_instructions", pack)
        self.assertEqual(fallback["source"], "software_proof")
        self.assertEqual(fallback["primary_actions_enabled"], False)
        self.assertEqual(fixture["can_collect"], False)
        self.assertEqual(fixture["can_confirm_dropoff"], False)
        self.assertEqual(fixture["can_cancel"], False)
        self.assertIn("software_proof_docker_field_evidence_rerun_execution_pack_gate", fixture_text)
        self.assertIn("field_evidence_rerun_execution_pack", doc)
        self.assertIn("现场证据复跑执行包", doc)
        self.assertIn("not PR #5 hardware proof", doc)
        self.assertIn("not Objective 5 external proof", doc)

    def test_field_evidence_rerun_execution_pack_fixture_stays_phone_safe(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        pack_text = json.dumps(
            {
                "execution_pack": fixture["robot_diagnostics_field_evidence_rerun_execution_pack_summary"],
                "fallback": fixture["field_evidence_rerun_execution_pack_summary"],
            },
            ensure_ascii=False,
        ).lower()

        # 执行包 fixture 只能承载脱敏步骤/模板/阈值，不泄漏 raw execution pack、调度或机器人控制语义。
        for forbidden in (
            "/cmd_vel",
            "raw ros topic",
            "raw json",
            "raw path",
            "raw callback",
            "raw review",
            "raw handoff",
            "raw intake",
            "raw packet",
            "raw queue",
            "raw execution",
            "full execution pack",
            "complete callback",
            "complete review",
            "serial device",
            "uart",
            "baudrate",
            "wave rover parameter",
            "authorization",
            "token",
            "oss_access_key_secret",
            "database url",
            "queue url",
            "credential url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "raw robot response",
            "ack payload",
            "cursor",
            "diagnostics fetch",
            "automatic retry",
            "queue scheduling",
            "execution scheduling",
            "robot command",
            "robot/internal",
            "control authorization",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, pack_text)

    def test_elevator_realtime_stage_keeps_primary_actions_closed(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        app = self.read_web("app.js")
        feedback_text = json.dumps(fixture["phone_action_feedback"], ensure_ascii=False).lower()

        # 新 panel 即使展示实时阶段，也不能覆盖既有 primary action gating。
        self.assertEqual(fixture["can_collect"], False)
        self.assertEqual(fixture["can_confirm_dropoff"], False)
        self.assertEqual(fixture["can_cancel"], False)
        self.assertEqual(fixture["phone_action_feedback"]["primary_actions_enabled"], False)
        self.assertIn("startButton", app)
        self.assertIn("confirmButton", app)
        self.assertIn("cancelButton", app)
        self.assertIn("Start Delivery、Confirm Dropoff、Cancel 仍按原 gate fail closed", app)

        # action message 只能是 phone-safe 摘要，不能带 raw ROS、硬件、凭证、路径或成功证明。
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
            "database url",
            "queue url",
            "checksum",
            "complete artifact",
            "raw artifact",
            "hil_pass",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
        ):
            self.assertNotIn(forbidden, feedback_text)


if __name__ == "__main__":
    unittest.main()
