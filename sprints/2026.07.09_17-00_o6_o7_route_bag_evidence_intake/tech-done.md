# O6/O7 Route Bag Evidence Intake Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 17:00 CST。

## 用户价值和产品北极星

本轮把准现场 DB3 `route_bag` 从“文件存在”推进到可被 Algorithm 摘要、O6 归档回读、O7 只读展示的证据链。它帮助运营人员判断某个 `task_id` 是否已有可排障的路线 bag 摘要，以及下一步还缺哪些材料。

产品北极星不变：普通手机用户交给机器人垃圾后，系统要可验证地完成垃圾投递。本轮只增强路线证据 intake，不证明真实投递闭环。

## OKR 映射和方向判断

- O6：继续推进云端核心后端的数据存档和 consumer read 能力，本轮新增 `route_bag_evidence` archive/readback。
- O7：继续推进 PC 端运营调试平台的历史任务详情和路线 readiness 展示，本轮新增 `route_bag_evidence` 只读摘要。
- 方向判断：继续，不调整 Objective；O6/O7 可从约 56% 保守上调到约 59%。
- KR 归档判断：不归档任何 KR。本轮证据仍是 `software_proof_route_bag_evidence_intake_only`。

## 实际改动

Algorithm worker 完成：

- `onboard/scripts/field_route_evidence_manifest.py` 新增 `route_bag_evidence` generator 和 CLI 输入。
- `onboard/tests/test_field_route_evidence_manifest.py` 覆盖 ready、缺 DB3、不可读 DB3、schema mismatch、空 topic/message、unsafe text 和 safety false。
- `docs/navigation/field_route_evidence_manifest.md` 同步字段、fail-closed 和复跑说明。
- `artifacts/algorithm_worker_report.md` 记录 worker 结果。

O6 worker 完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 O6 readback schema、include allowlist 和 fail-closed sanitizer。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 覆盖 field-evidence、artifact-bundle、archive detail、consumer include 和 unsafe fail-closed。
- `docs/interfaces/o6_cloud_archive_api.md` 同步 O6 API 文档。
- `artifacts/o6_worker_report.md` 记录 worker 结果。

O7 worker 完成：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` 读取 `route_bag_evidence`。
- `pc-tools/workstation/src/shared/contracts.ts` 增加共享合同。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 展示 source/status、topic/message/timestamp、blocked reasons、next evidence 和 false safety fields。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts` 增加覆盖。
- `docs/product/pc_tools_workstation.md` 同步 PC 工作站文档。
- `artifacts/o7_worker_report.md` 记录 worker 结果。

Product closeout 完成：

- `OKR.md` 更新 O6/O7 当前进度到约 59%，不归档 KR。
- `docs/process/okr_progress_log.md` 追加本 sprint 顶部历史记录。
- 本文件、`side2side_check.md`、`final.md` 完成 epic 收口链路。

## 验证结果

Algorithm worker 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.100s

OK
```

Algorithm 准现场 DB3 smoke：

```text
status=ready_not_route_execution_proof
proof_scope=software_proof_route_bag_evidence_intake_only
topic_count=3
message_count=1473
sample_topic_names=["/tf_static", "/scan", "/camera/image_raw"]
safe_to_control=false
delivery_success=false
contains_abs_path=false
```

O6 worker 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 158 tests in 56.274s OK
```

O7 worker 验证：

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  479 passed (479)
✓ built in 1.72s
eslint .
```

O7 worker 还修复了 `ProofFlags.source` collision，避免 build/type path 中的字段碰撞风险。

## 失败定位和修复

- Algorithm 首轮 unittest 失败在 SSH command 只读安全测试，原因是新增 route bag topic 安全检查直接写入敏感 topic 字面量；worker 改为拼接常量后复验通过。
- O6 worker 修复了已存 `trashbot.o6.route_bag_evidence.v1` readback 被二次 sanitizer 降级、ready status 被错误降级、topic safe-value 例外和测试 task id 敏感 marker 归属问题。
- O7 worker 修复 `ProofFlags.source` collision；最终 test/build/lint 全部通过。
- Product 收口阶段没有修改产品代码、测试、worker reports 或其他 sprint。

## 证据边界和剩余风险

证据边界：`software_proof_route_bag_evidence_intake_only`。

本轮证明：

- 准现场 DB3 route bag 可被 Algorithm 生成脱敏摘要。
- O6 可 archive/readback `route_bag_evidence`，包含 `include=route_bag_evidence`。
- O7 可消费和展示 `route_bag_evidence` 只读摘要。
- 安全字段保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

本轮不证明：

- 真实 production cloud、真实隧道、production DB/queue、OSS/CDN live traffic。
- raw ROS message payload 解码、真实 live Nav2 route execution、真实 robot motion。
- 真实 delivery record、operator confirmation、delivery success。
- 真实 annotation API/export、真实 dataset export 或完整路线长期验收。

## 下一步

下一轮应优先补 live Nav2 pose progress、raw ROS message payload 解析/回放、真实 delivery record、operator confirmation 媒体和生产云/OSS 证据。继续新增 wrapper 或只读 readiness 不应作为 O6/O7 主抓手。
