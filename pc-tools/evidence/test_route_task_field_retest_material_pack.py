#!/usr/bin/env python3
"""route_task_field_retest_material_pack 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_material_pack as pack  # noqa: E402


# 测试约束 01：fixture 只表达 result review handoff，不创建材料目录。
# 测试约束 02：ready case 只能证明材料采集包 metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：needs case 验证 handoff 不 ready 时不能进入现场采集 ready。
# 测试约束 07：缺输入 case 验证没有 handoff 不能静默 ready。
# 测试约束 08：mismatch case 验证证据号不一致必须复跑。
# 测试约束 09：unsupported case 验证 schema 或 boundary 漂移必须 fail closed。
# 测试约束 10：weak same-ref case 验证字符串 true 不能通过。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 unsupported fail closed。
# 测试约束 13：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 14：单测不访问 ROS graph、Nav2 runtime 或硬件。
# 测试约束 15：单测不访问 cloud、phone、serial/UART 或 WAVE ROVER。
# 测试约束 16：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 17：未来新增 material_pack_status，必须同步补文档和测试。
# 测试约束 18：ready 测试同时检查 artifact 和 summary schema。
# 测试约束 19：ready 测试确认 field_capture_checklist 只是 required-not-collected。
# 测试约束 20：mapping 测试覆盖 needs、缺输入、unsupported 和 mismatch。
# 测试约束 21：wrapper 测试确认只通过安全 wrapper key 取 source。
# 测试约束 22：mismatch 测试确认 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 23：unsupported schema 测试确认 schema 漂移必须复跑。
# 测试约束 24：weak same-ref 测试确认字符串 true 不能替代布尔 true。
# 测试约束 25：unsafe 测试确认 raw path 不进入 summary。
# 测试约束 26：unsafe 测试确认 ROS topic 不进入 summary。
# 测试约束 27：success 测试确认 delivery_success=true 被阻断。
# 测试约束 28：所有 fixture 都使用安全 evidence_ref，不使用本机路径。
# 测试约束 29：所有 fixture 都保持 delivery_success=false，除专门 unsafe case。
# 测试约束 30：所有 fixture 都保持 primary_actions_enabled=false。
# 测试约束 31：测试不写仓库文件，只在 tempfile 中写临时 JSON。
# 测试约束 32：测试不依赖命令行输出，直接调用 build 函数。
# 测试约束 33：测试名称描述 fail-closed 行为，方便后续定位回归。
# 测试约束 34：材料采集包 fixture 仍不代表真实现场通过。
# 测试约束 35：材料清单 fixture 默认包含全部 required field materials。
# 测试约束 36：rg literal 覆盖 not_proven、delivery_success=false 和 action disabled。


class RouteTaskFieldRetestMaterialPackTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, evidence_ref: str = "ev-001", **extra: object) -> None:
        # 旧 material-dir fixture 只写脱敏元数据，保持 software proof 边界。
        payload = {
            "schema": f"fixture.{name}.v1",
            "evidence_ref": evidence_ref,
            "status": "provided",
            "observer_note": f"{name} collected for terminal review",
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        (root / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    def _complete_material_dir(self, root: Path, evidence_ref: str = "ev-001") -> None:
        # 八类材料文件名与 CLI 白名单对齐，避免测试靠任意文件发现通过。
        for name in pack.REQUIRED_MATERIALS:
            self._write_json(root, name, evidence_ref=evidence_ref)

    def _handoff_payload(
        self,
        handoff_status: str = "ready_for_owner_result_callback_not_proven",
        evidence_ref: str = "ev-material-pack-001",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上一轮 handoff 摘要，不包含真实材料正文或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_review_handoff_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_review_handoff_gate",
            "status": handoff_status,
            "handoff_status": handoff_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_package": {
                "status": "matched",
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "owner_work_orders": [{"owner": "Autonomy Algorithm Engineer", "action": "prepare_callback"}],
            "next_material_callback_requirements": [
                f"Callback must provide {name} for evidence_ref={evidence_ref}."
                for name in pack.FIELD_CAPTURE_MATERIALS
            ],
            "rerun_commands": [
                "python3 pc-tools/evidence/route_task_field_retest_result_review_handoff.py --once-json"
            ],
            "accepted_materials": list(pack.FIELD_CAPTURE_MATERIALS),
            "missing_materials": [],
            "rejected_materials": [],
            "safe_copy": {
                "handoff_status": handoff_status,
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(pack.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_material_dir_mode_stays_ready_not_proven_and_downstream_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-001")

            artifact, summary, exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_material_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_pack_summary.v1")
        self.assertEqual(artifact["material_pack_verdict"], "ready_for_field_retest_material_pack_not_proven")
        self.assertEqual(artifact["material_pack_status"], "ready_for_field_retest_material_pack_not_proven")
        self.assertEqual(summary["material_completeness"]["accepted_count"], len(pack.REQUIRED_MATERIALS))
        self.assertEqual(len(artifact["material_manifest"]), len(pack.REQUIRED_MATERIALS))
        self.assertIn("operator_next_steps", artifact)
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_material_dir_blocked_and_old_helpers_stay_importable(self) -> None:
        self.assertIn("delivery_result.json", pack.MATERIAL_ALIASES["delivery_result"])
        self.assertTrue(callable(pack._source_dir_status))
        self.assertTrue(callable(pack._scan_material))
        self.assertTrue(callable(pack._has_raw_path_copy))
        self.assertTrue(callable(pack._has_success_or_control_claim))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-002")
            (root / "delivery_result.json").unlink()
            self._write_json(root, "human_assistance_note", evidence_ref="ev-002", status="placeholder")

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-002")

        self.assertEqual(artifact["material_pack_verdict"], "blocked_missing_materials")
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertEqual(summary["rejected_materials"]["human_assistance_note"], ["placeholder_only"])
        self.assertFalse(summary["safe_copy"]["delivery_success"])

    def test_ready_handoff_maps_to_material_collection_pack_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")

            artifact, summary, exit_code = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_material_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_material_pack_gate",
        )
        self.assertEqual(artifact["material_pack_status"], "ready_for_field_retest_material_collection_not_proven")
        self.assertEqual(artifact["material_pack_verdict"], "ready_for_field_retest_material_collection_not_proven")
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_result_review_handoff_summary.v1")
        self.assertEqual(summary["source_boundary"], "software_proof_docker_route_task_field_retest_result_review_handoff_gate")
        self.assertEqual(len(summary["field_capture_checklist"]), len(pack.FIELD_CAPTURE_MATERIALS))
        self.assertEqual(summary["field_capture_checklist"][0]["collection_status"], "required_not_collected")
        self.assertEqual(summary["callback_payload_skeleton"]["safe_evidence_ref"], "ev-material-pack-001")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_not_ready_handoff_maps_to_needs_result_review_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "needs.json"
            path.write_text(
                json.dumps(
                    self._handoff_payload(
                        handoff_status="needs_result_material_callback_not_proven",
                        missing_materials=["elevator_door_state"],
                    )
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(path),
            )

        self.assertEqual(artifact["material_pack_status"], "needs_result_review_handoff_not_proven")
        self.assertEqual(summary["material_pack_verdict"], "needs_result_review_handoff_not_proven")
        self.assertIn("source_handoff_status:needs_result_material_callback_not_proven", summary["status_reasons"])
        self.assertEqual(summary["field_capture_checklist"][0]["collection_status"], "blocked_until_supported_result_review_handoff")

    def test_wrapper_and_nested_handoff_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps(
                    {
                        "payload": {
                            "route_task_field_retest_result_review_handoff_summary": self._handoff_payload(
                                evidence_ref="ev-material-pack-002",
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(result_review_handoff_json=str(path))

        self.assertEqual(artifact["material_pack_status"], "ready_for_field_retest_material_collection_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-material-pack-002")

    def test_missing_unsupported_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            weak_same_ref_path = root / "weak_same_ref.json"
            ready_path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._handoff_payload(schema="trashbot.other.v1")), encoding="utf-8")
            weak_same_ref_path.write_text(json.dumps(self._handoff_payload(same_evidence_ref_required="true")), encoding="utf-8")

            missing_artifact, _missing_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(root / "missing.json"),
            )
            schema_artifact, _schema_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(bad_schema_path),
            )
            mismatch_artifact, _mismatch_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="other-ref",
                result_review_handoff_json=str(ready_path),
            )
            weak_artifact, _weak_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(weak_same_ref_path),
            )

        self.assertEqual(missing_artifact["material_pack_status"], "blocked_missing_result_review_handoff_not_proven")
        self.assertEqual(schema_artifact["material_pack_status"], "unsupported_result_review_handoff_schema_not_proven")
        self.assertEqual(mismatch_artifact["material_pack_status"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(weak_artifact["material_pack_status"], "evidence_ref_mismatch_rerun_not_proven")

    def test_unsafe_handoff_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._handoff_payload(owner_work_orders=[{"note": "raw path /Users/m4/private.log /cmd_vel"}])),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._handoff_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(unsafe_path),
            )
            success_artifact, _success_summary, _ = pack.build_route_task_field_retest_material_pack(
                evidence_ref="ev-material-pack-001",
                result_review_handoff_json=str(success_path),
            )

        self.assertEqual(unsafe_artifact["material_pack_status"], "unsupported_result_review_handoff_schema_not_proven")
        self.assertEqual(success_artifact["material_pack_status"], "unsupported_result_review_handoff_schema_not_proven")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)


if __name__ == "__main__":
    unittest.main()
