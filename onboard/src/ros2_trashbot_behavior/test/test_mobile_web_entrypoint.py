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


if __name__ == "__main__":
    unittest.main()
