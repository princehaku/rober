import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_ROOT = REPO_ROOT / "mobile" / "web"
FIXTURE = REPO_ROOT / "mobile" / "fixtures" / "mobile_web_status.fixture.json"
DOC = REPO_ROOT / "docs" / "product" / "mobile_user_flow.md"


class MobileWebRouteTaskReviewTest(unittest.TestCase):
    def read_web(self, name):
        # 测试只读静态入口文件，确保本轮 UI 合同不需要后端真实文件系统。
        return (WEB_ROOT / name).read_text(encoding="utf-8")

    def test_route_task_review_panel_is_visible_and_read_only(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")

        # operator review 是只读复盘面板；按钮授权仍由既有 Start/Confirm/Cancel gates 控制。
        self.assertIn("routeTaskReviewTitle", index)
        self.assertIn("路线/任务排练复盘", index)
        self.assertIn("routeTaskReviewOverall", index)
        self.assertIn("routeTaskReviewEvidenceRef", index)
        self.assertIn("routeTaskReviewCrosscheckHil", index)
        self.assertIn("routeTaskReviewMismatch", index)
        self.assertIn("routeTaskReviewNextDecision", index)
        self.assertIn("routeTaskReviewNotProven", index)
        self.assertIn("routeTaskReviewSafeCopy", index)
        self.assertIn("copyRouteTaskReviewButton", index)
        self.assertIn("software_proof_docker_route_task_rehearsal_operator_review_gate", index)
        self.assertRegex(index, r'id="copyRouteTaskReviewButton"[^>]*disabled')
        self.assertIn("renderRouteTaskReview", app)
        self.assertIn("routeTaskReviewFromStatus", app)
        self.assertIn("Start Delivery", index)
        self.assertIn("Confirm Dropoff", index)
        self.assertIn("Cancel", index)
        self.assertIn("actionGate.enabled === true && permitted === true", app)

    def test_route_task_review_consumes_phone_safe_sources_and_safe_copy_only(self):
        app = self.read_web("app.js")

        # 兼容来源必须覆盖 status、phone_readiness 和 diagnostics，但复制只走 safe_copy 白名单。
        self.assertIn("route_task_rehearsal_operator_review", app)
        self.assertIn("route_task_rehearsal_operator_review_summary", app)
        self.assertIn("route_task_rehearsal_review_summary", app)
        self.assertIn("route_task_rehearsal_summary", app)
        self.assertIn("diagnosticsReadiness.route_task_rehearsal_operator_review", app)
        self.assertIn("safe_copy_payload", app)
        self.assertIn("blocked copy unavailable", app)
        self.assertIn("UNSAFE_OPERATOR_REVIEW_TEXT", app)
        self.assertIn("raw artifact", app)
        self.assertIn("full execution bundle", app)
        self.assertIn("local path", app)
        self.assertNotRegex(app, r"renderRouteTaskReview[\s\S]*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")

    def test_fixture_and_docs_keep_software_proof_boundary(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")
        review = fixture["route_task_rehearsal_operator_review"]
        safe_copy = review["safe_copy"]
        safe_copy_text = json.dumps(safe_copy, ensure_ascii=False)

        # fixture 只能给 phone-safe summary；不能把 raw artifact 或 backend path 放进 copy/export。
        self.assertEqual(review["evidence_boundary"], "software_proof_docker_route_task_rehearsal_operator_review_gate")
        self.assertEqual(safe_copy["evidence_boundary"], "software_proof_docker_route_task_rehearsal_operator_review_gate")
        self.assertIn("next_rehearsal_decision", review)
        self.assertIn("not_proven", review)
        self.assertNotRegex(safe_copy_text, r"/Users/|/tmp/|/ws/|checksum|full execution bundle|backend filesystem")
        self.assertIn("not HIL", doc)
        self.assertIn("not real route execution", doc)
        self.assertIn("not delivery success", doc)
        self.assertIn("blocked copy unavailable", doc)

    def test_pc_route_debug_console_summary_is_read_only_and_not_proven(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")
        summary = fixture["pc_route_debug_console"]

        # PC console availability 只是支持/诊断摘要，不能进入手机主控制授权链路。
        self.assertIn("pcRouteDebugConsoleTitle", index)
        self.assertIn("PC 路线调试 Console", index)
        self.assertIn("pcRouteDebugConsoleAvailability", index)
        self.assertIn("pcRouteDebugConsoleRouteDebug", index)
        self.assertIn("pcRouteDebugConsoleRecentTask", index)
        self.assertIn("pcRouteDebugConsoleControlBoundary", index)
        self.assertIn("pcRouteDebugConsoleNotProven", index)
        self.assertIn("software_proof_docker_pc_route_debug_console_gate", index)
        self.assertIn("pcRouteDebugConsoleFromStatus", app)
        self.assertIn("pc_route_debug_console", app)
        self.assertIn("pc_route_debug_console_summary", app)
        self.assertIn("read_only_no_mobile_control_grant", app)
        self.assertNotRegex(app, r"renderPcRouteDebugConsole[\s\S]*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertIn("Start Delivery", index)
        self.assertIn("Confirm Dropoff", index)
        self.assertIn("Cancel", index)
        self.assertIn("actionGate.enabled === true && permitted === true", app)

        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_pc_route_debug_console_gate")
        self.assertEqual(summary["control_boundary"], "read_only_no_mobile_control_grant")
        self.assertIn("not_proven", summary)
        self.assertIn("delivery success", json.dumps(summary, ensure_ascii=False))
        self.assertIn("pc_route_debug_console", doc)
        self.assertIn("software_proof_docker_pc_route_debug_console_gate", doc)
        self.assertIn("not delivery success", doc)

    def test_route_task_field_run_readiness_panel_is_read_only(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")
        summary = fixture["route_task_field_run_readiness"]

        # 现场联跑准备度只展示下一次 evidence handoff，不进入 Start/Confirm/Cancel 授权链。
        self.assertIn("routeTaskFieldRunReadinessTitle", index)
        self.assertIn("路线任务现场联跑准备", index)
        self.assertIn("routeTaskFieldRunReadinessAvailability", index)
        self.assertIn("routeTaskFieldRunReadinessEvidenceRef", index)
        self.assertIn("routeTaskFieldRunReadinessSameRef", index)
        self.assertIn("routeTaskFieldRunReadinessNextEvidence", index)
        self.assertIn("routeTaskFieldRunReadinessCommands", index)
        self.assertIn("routeTaskFieldRunReadinessNotProven", index)
        self.assertIn("software_proof_docker_route_task_field_run_readiness_gate", index)
        self.assertIn("routeTaskFieldRunReadinessFromStatus", app)
        self.assertIn("routeTaskFieldRunReadinessCandidate", app)
        self.assertIn("route_task_field_run_readiness", app)
        self.assertIn("route_task_field_run_readiness_summary", app)
        self.assertIn("diagnosticsReadiness.route_task_field_run_readiness", app)
        self.assertNotRegex(app, r"renderRouteTaskFieldRunReadiness[\s\S]*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertIn("Start Delivery", index)
        self.assertIn("Confirm Dropoff", index)
        self.assertIn("Cancel", index)
        self.assertIn("actionGate.enabled === true && permitted === true", app)

        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_route_task_field_run_readiness_gate")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("not_proven", summary)
        self.assertIn("delivery success", json.dumps(summary, ensure_ascii=False))
        self.assertIn("route_task_field_run_readiness", doc)
        self.assertIn("software_proof_docker_route_task_field_run_readiness_gate", doc)
        self.assertIn("not HIL", doc)
        self.assertIn("not delivery success", doc)

    def test_route_task_field_run_readiness_missing_and_unsafe_fields_fail_closed(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture_text = FIXTURE.read_text(encoding="utf-8")

        # 缺 summary 时默认 blocked/not_proven；敏感词命中只走 safeFieldRunReadinessText 降级。
        self.assertIn("blocked_missing_route_task_field_run_readiness_summary", app)
        self.assertIn("缺少下一次 field run 所需材料摘要", app)
        self.assertIn("UNSAFE_FIELD_RUN_READINESS_TEXT", app)
        self.assertIn("safeFieldRunReadinessText", app)
        self.assertIn("raw robot response", app)
        self.assertIn("complete artifact", app)
        self.assertIn("credential-bearing url", app)
        self.assertIn("/cmd_vel", app)
        self.assertIn("serial", app)
        self.assertIn("baudrate", app)
        self.assertIn("wave rover", app)
        self.assertIn("traceback", app)
        self.assertIn("checksum", app)
        self.assertNotIn("routeTaskFieldRunReadinessRawArtifact", index)
        self.assertNotIn("routeTaskFieldRunReadinessExecutionBundle", index)
        self.assertNotIn("routeTaskFieldRunReadinessTraceback", index)
        self.assertNotRegex(fixture_text, r"/Users/|/tmp/|/ws/|checksum|traceback|Authorization|Bearer|OSS_ACCESS_KEY|raw robot response|full execution bundle")

    def test_route_task_field_run_intake_panel_is_read_only(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")
        summary = fixture["route_task_field_run_intake"]

        # intake crosscheck 只做材料复核；它不能参与 Start/Confirm/Cancel 授权链。
        self.assertIn("routeTaskFieldRunIntakeTitle", index)
        self.assertIn("路线任务现场材料复核", index)
        self.assertIn("routeTaskFieldRunIntakeStatus", index)
        self.assertIn("routeTaskFieldRunIntakeEvidenceRef", index)
        self.assertIn("routeTaskFieldRunIntakeMissing", index)
        self.assertIn("routeTaskFieldRunIntakeMismatch", index)
        self.assertIn("routeTaskFieldRunIntakeCommands", index)
        self.assertIn("routeTaskFieldRunIntakeNotProven", index)
        self.assertIn("software_proof_docker_route_task_field_run_intake_crosscheck_gate", index)
        self.assertIn("routeTaskFieldRunIntakeFromStatus", app)
        self.assertIn("routeTaskFieldRunIntakeCandidate", app)
        self.assertIn("route_task_field_run_intake", app)
        self.assertIn("route_task_field_run_intake_summary", app)
        self.assertIn("diagnosticsReadiness.route_task_field_run_intake", app)
        self.assertIn("provided.crosscheck && typeof provided.crosscheck === \"object\"", app)
        self.assertIn("crosscheck.missing_materials", app)
        self.assertIn("crosscheck.mismatch_reasons", app)
        self.assertIn("crosscheck.commands_to_rerun", app)
        self.assertNotRegex(app, r"renderRouteTaskFieldRunIntake[\s\S]*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertIn("Start Delivery", index)
        self.assertIn("Confirm Dropoff", index)
        self.assertIn("Cancel", index)
        self.assertIn("actionGate.enabled === true && permitted === true", app)

        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_intake_crosscheck.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_route_task_field_run_intake_crosscheck_gate")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("commands_to_rerun", summary)
        self.assertIn("not_proven", summary)
        self.assertIn("delivery success", json.dumps(summary, ensure_ascii=False))
        self.assertIn("crosscheck", fixture["route_task_field_run_intake_summary"])
        self.assertIn("missing_materials", fixture["route_task_field_run_intake_summary"]["crosscheck"])
        self.assertIn("mismatch_reasons", fixture["route_task_field_run_intake_summary"]["crosscheck"])
        self.assertIn("commands_to_rerun", fixture["route_task_field_run_intake_summary"]["crosscheck"])
        self.assertIn("route_task_field_run_intake", doc)
        self.assertIn("software_proof_docker_route_task_field_run_intake_crosscheck_gate", doc)
        self.assertIn("crosscheck.status", doc)
        self.assertIn("not HIL", doc)
        self.assertIn("not delivery success", doc)

    def test_route_task_field_run_intake_missing_and_unsafe_fields_fail_closed(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture_text = FIXTURE.read_text(encoding="utf-8")

        # 缺 intake summary 时默认 blocked；敏感字段必须被 safeFieldRunIntakeText 拦截。
        self.assertIn("blocked_missing_route_task_field_run_intake_summary", app)
        self.assertIn("未提供 missing_materials 摘要", app)
        self.assertIn("UNSAFE_FIELD_RUN_INTAKE_TEXT", app)
        self.assertIn("safeFieldRunIntakeText", app)
        self.assertIn("raw robot response", app)
        self.assertIn("complete artifact", app)
        self.assertIn("credential-bearing url", app)
        self.assertIn("/cmd_vel", app)
        self.assertIn("serial", app)
        self.assertIn("baudrate", app)
        self.assertIn("wave rover", app)
        self.assertIn("traceback", app)
        self.assertIn("checksum", app)
        self.assertNotIn("routeTaskFieldRunIntakeRawArtifact", index)
        self.assertNotIn("routeTaskFieldRunIntakeExecutionBundle", index)
        self.assertNotIn("routeTaskFieldRunIntakeTraceback", index)
        self.assertNotRegex(fixture_text, r"/Users/|/tmp/|/ws/|checksum|traceback|Authorization|Bearer|OSS_ACCESS_KEY|raw robot response|full execution bundle")

    def test_route_task_field_run_review_panel_is_read_only(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = DOC.read_text(encoding="utf-8")
        summary = fixture["route_task_field_run_review"]

        # review console 只展示操作者复盘结论；不得改变 Start/Confirm/Cancel 授权链。
        self.assertIn("routeTaskFieldRunReviewTitle", index)
        self.assertIn("路线任务现场复盘 Console", index)
        self.assertIn("routeTaskFieldRunReviewDecision", index)
        self.assertIn("routeTaskFieldRunReviewEvidenceRef", index)
        self.assertIn("routeTaskFieldRunReviewMissingMismatch", index)
        self.assertIn("routeTaskFieldRunReviewCommands", index)
        self.assertIn("routeTaskFieldRunReviewNextSteps", index)
        self.assertIn("routeTaskFieldRunReviewNotProven", index)
        self.assertIn("software_proof_docker_route_task_field_run_review_console_gate", index)
        self.assertIn("routeTaskFieldRunReviewFromStatus", app)
        self.assertIn("routeTaskFieldRunReviewCandidate", app)
        self.assertIn("route_task_field_run_review", app)
        self.assertIn("route_task_field_run_review_summary", app)
        self.assertIn("diagnosticsReadiness.route_task_field_run_review", app)
        self.assertIn("diagnosticsSummary.route_task_field_run_review_summary", app)
        self.assertIn("nestedDiagnosticsSummary.route_task_field_run_review_summary", app)
        self.assertNotRegex(app, r"renderRouteTaskFieldRunReview[\s\S]*fetchJson\(ENDPOINTS\.(start|confirm_dropoff|cancel)")
        self.assertIn("Start Delivery", index)
        self.assertIn("Confirm Dropoff", index)
        self.assertIn("Cancel", index)
        self.assertIn("actionGate.enabled === true && permitted === true", app)

        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_review_summary.v1")
        self.assertEqual(summary["source_artifact_schema"], "trashbot.route_task_field_run_review_console.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_route_task_field_run_review_console_gate")
        self.assertIn("review_decision", summary)
        self.assertIn("safe_evidence_ref", summary)
        self.assertIn("commands_to_rerun", summary)
        self.assertIn("operator_next_steps", summary)
        self.assertIn("not_proven", summary)
        self.assertIn("delivery success", json.dumps(summary, ensure_ascii=False))
        self.assertIn("route_task_field_run_review", doc)
        self.assertIn("software_proof_docker_route_task_field_run_review_console_gate", doc)
        self.assertIn("not HIL", doc)
        self.assertIn("not delivery success", doc)

    def test_route_task_field_run_review_missing_and_unsafe_fields_fail_closed(self):
        index = self.read_web("index.html")
        app = self.read_web("app.js")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture_text = FIXTURE.read_text(encoding="utf-8")

        # review console 缺 summary 时默认 blocked；敏感字段必须走 safeFieldRunReviewText 降级。
        self.assertIn("blocked_missing_route_task_field_run_review_summary", app)
        self.assertIn("等待 operator_next_steps 摘要", app)
        self.assertIn("UNSAFE_FIELD_RUN_REVIEW_TEXT", app)
        self.assertIn("safeFieldRunReviewText", app)
        self.assertIn("raw robot response", app)
        self.assertIn("complete artifact", app)
        self.assertIn("credential-bearing url", app)
        self.assertIn("/cmd_vel", app)
        self.assertIn("serial", app)
        self.assertIn("baudrate", app)
        self.assertIn("wave rover", app)
        self.assertIn("traceback", app)
        self.assertIn("checksum", app)
        self.assertNotIn("routeTaskFieldRunReviewRawArtifact", index)
        self.assertNotIn("routeTaskFieldRunReviewExecutionBundle", index)
        self.assertNotIn("routeTaskFieldRunReviewTraceback", index)
        self.assertNotRegex(fixture_text, r"/Users/|/tmp/|/ws/|checksum|traceback|Authorization|Bearer|OSS_ACCESS_KEY|raw robot response|full execution bundle")
        self.assertIn("crosscheck", fixture["route_task_field_run_review_summary"])
        self.assertIn("missing_materials", fixture["route_task_field_run_review_summary"]["crosscheck"])
        self.assertIn("mismatch_reasons", fixture["route_task_field_run_review_summary"]["crosscheck"])
        self.assertIn("commands_to_rerun", fixture["route_task_field_run_review_summary"]["crosscheck"])


if __name__ == "__main__":
    unittest.main()
