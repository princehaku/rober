# Motion Evidence Material Review

## sprint_type

micro

## 本轮功能点设计

- 新增一个纯文件脚本，用于把 `manual_response`、可选 `base_feedback`、可选 `scan_before`/`scan_after` 复核成 operator report 可用的材料草稿。
- 该脚本不打开串口、不发 HTTP、不连 ROS、不调用 `/api/base/manual`，也不发布 `/cmd_vel`。
- 输出必须 fail-closed，顶层安全字段全部保持 false，并把 wheel feedback 与 LiDAR delta 的判定结果写清楚。

## 实际改动

- 已新增：`onboard/scripts/motion_evidence_material_review.py`
  - 纯文件 CLI，读取 `manual_response`、可选 `base_feedback`、可选 `scan_before/scan_after`，
    输出 `trashbot.motion_evidence_material_review.v1`。
  - wheel proof 只接受可解析 `T=1001` 或明确 left/right wheel 字段，且要求同一帧左右轮都非零。
  - scan proof 同时支持 raw `ranges` 和已有 summary 字段；没有可比较材料时保持 false。
  - 顶层安全字段固定 fail-closed：`safe_to_control=false`、`delivery_success=false`、
    `hil_pass=false`、`robot_control_executed=false`、`sends_motion_commands=false`。
- 已新增：`onboard/tests/test_motion_evidence_material_review.py`
  - 覆盖 help/file-only 边界、synthetic pass、insufficient、invalid_input 和 summary-scan 模式。
- 已更新：`docs/hardware/field_hil_operator_report_template.md`
  - 新增 file-only 材料草稿工具章节，说明如何生成 wheel/scan material draft。
- 已更新：`docs/hardware/field_hil_execution_pack.md`
  - 在 operator report intake 章节补充本脚本的使用边界。
- 已新增 artifact：`sprints/2026.06.11_17-15_motion_evidence_material_review/artifacts/**`
  - 保存 synthetic pass / insufficient 的输入和输出 JSON，供本轮 smoke 复核。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_motion_evidence_material_review`
  - `Ran 5 tests in 0.085s`
  - `OK`
- 已通过：CLI smoke - synthetic pass
  - 输入：`artifacts/smoke_pass_manual_response.json`
    `artifacts/smoke_pass_feedback.jsonl`
    `artifacts/smoke_pass_scan_before.json`
    `artifacts/smoke_pass_scan_after.json`
  - 输出：`artifacts/smoke_pass_review.json`
  - 结果：`review_status=ready_for_operator_report_material`
    `wheel_feedback_lr_nonzero_proven=true`
    `physical_motion_lidar_delta_proven=true`
- 已通过：CLI smoke - insufficient input
  - 输入：`artifacts/smoke_insufficient_manual_response.json`
    `artifacts/smoke_insufficient_feedback.json`
  - 输出：`artifacts/smoke_insufficient_review.json`
  - 结果：`review_status=insufficient_material`
    `wheel_feedback_lr_nonzero_proven=false`
    `physical_motion_lidar_delta_proven=false`
    `failure_reasons` 包含 `wheel_feedback_single_side_nonzero_only` 和
    `scan_before_or_after_file_not_provided`
- 已通过：`git diff --check`

## 剩余风险

- 当前脚本对 wheel feedback 仅支持本轮明确要求的字段名集合；若后续 artifact 使用其他命名，
  需要先补充单测再扩展。
- summary-scan 模式默认把 `scan_after` 里的 delta summary 视为比较结果；如果后续 scan proof
  schema 再分层，需补 fixture 锁定嵌套路径。
- 本轮只完成 file-only 材料整理，不证明真实底盘运动、外部视频、route/map 或 delivery。
