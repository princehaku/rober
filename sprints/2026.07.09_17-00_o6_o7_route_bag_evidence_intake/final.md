# O6/O7 Route Bag Evidence Intake Final

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 17:00 CST。

## 最终状态

状态：完成，边界为 `software_proof_route_bag_evidence_intake_only`。

本 sprint 已完成 Algorithm -> O6 -> O7 的 `route_bag_evidence` intake/readback/UI summary 证据链。安全字段保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 用户价值和产品北极星

用户价值：运营人员可以在同一 `task_id` 下看到准现场 DB3 route bag 摘要，知道 topic/message/timestamp 是否可读，以及还缺哪些证据才能相信真实路线执行和送达。

产品北极星：普通手机用户可验证地完成垃圾投递。本轮只推进路线证据 intake，不替代真实投递验收。

## OKR 映射和方向判断

- O6：继续。`route_bag_evidence` 已进入 O6 archive/readback 和 `include=route_bag_evidence`，O6 从约 56% 保守上调到约 59%。
- O7：继续。O7 已展示 route bag evidence 只读摘要并通过 test/build/lint，O7 从约 56% 保守上调到约 59%。
- 不调整 Objective，不暂停，不替换。
- 不归档任何 KR。本轮没有达到真实 production cloud、真实 live Nav2 route execution、真实 delivery record/operator confirmation 或 delivery success 的归档标准。

## KR 拆解和历史归档

本轮推进但不归档：

- O6 KR2 / KR6：任务记录、事件/证据存档和 consumer read 继续增强。
- O7 KR3 / KR4：历史路线回放 readiness 和数据标注工作台可见 route bag 摘要。

已完成 KR 的历史记录位置：本轮没有新增已完成 KR。历史记录只追加到 `docs/process/okr_progress_log.md` 顶部条目，并在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 留证。

证据来源：

- `artifacts/algorithm_worker_report.md`
- `artifacts/o6_worker_report.md`
- `artifacts/o7_worker_report.md`
- Product 收口验证命令

## 本轮核心抓手

核心抓手是消费已有准现场 DB3 route bag，而不是继续新增只读 wrapper。

关键事实：

- Algorithm route bag evidence generator 已加入 `field_route_evidence_manifest.py`。
- 准现场 DB3 smoke：`topic_count=3`、`message_count=1473`、sample topics `/tf_static`、`/scan`、`/camera/image_raw`、`contains_abs_path=false`。
- O6 支持 archive/readback 和 `include=route_bag_evidence`。
- O7 支持 consumer/UI 只读摘要，并修复 `ProofFlags.source` collision。

## 验证结果

- Algorithm：`Ran 26 tests in 0.100s OK`。
- O6：`Ran 158 tests in 56.274s OK`。
- O7：`npm run test` 输出 3 files / `479 passed`，build `built in 1.72s`，lint 通过。

Product 收口验证已运行通过：

```text
test -f artifacts/algorithm_worker_report.md
test -f artifacts/o6_worker_report.md
test -f artifacts/o7_worker_report.md
test -f tech-done.md
test -f side2side_check.md
test -f final.md
rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|O6|O7|safe_to_control=false|delivery_success=false|1473|479 passed|158 tests|26 tests|~59%" ...
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake
exit code 0
```

`rg` 输出较长，已确认命中 `route_bag_evidence`、`software_proof_route_bag_evidence_intake_only`、`safe_to_control=false`、`delivery_success=false`、`1473`、`479 passed`、`158 tests`、`26 tests` 和 `~59%`；`git diff --check` 无 whitespace 错误。

## 剩余风险和阻塞

剩余风险：

- 只读取 DB3 SQLite 元数据摘要，不解码 raw ROS message payload。
- 不证明真实 live Nav2 route execution、robot motion 或 route execution success。
- 不证明真实 production cloud、真实隧道、production DB/queue、OSS/CDN live traffic。
- 不证明真实 delivery record、operator confirmation 或 delivery success。
- 不证明真实 annotation API/export、dataset export 或完整路线长期验收。

阻塞：无新的流程 blocker；下一步需要真实或更接近真实现场的 live route / delivery 证据。

## 下一步

优先级：

1. live Nav2 pose progress 或 raw ROS message payload 解析/回放。
2. route execution result / failure reason。
3. delivery record、operator confirmation 和 dropoff 现场证据。
4. production cloud、OSS/CDN、annotation API/export 的真实链路验证。

责任 Engineer：

- `robot-algorithm-engineer`：raw ROS message payload 解析/回放、live Nav2 pose progress。
- `robot-software-engineer`：O6 production archive/readback、delivery record ingest。
- `full-stack-software-engineer`：O7 route replay、operator confirmation 展示和真实数据回放。
- `rober-hardware-engineer`：如进入真实上车运动验证，负责底盘和传感器事实核对。
