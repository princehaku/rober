# O6/O7 Route Bag Evidence Intake Tech Plan

## Sprint 类型

sprint_type: epic

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6、O7，并列约 56%。
- 本 sprint 是否针对最低 Objective：是。
- 选择理由：最近 O6/O7 已连续完成 field motion、Nav2 goal 和 delivery result 的 software proof，但 final 都要求下一轮优先消费真实或准现场 `route_bag` / live Nav2 pose progress / delivery record。本轮直接消费已有 DB3 route bag 材料，形成 `route_bag_evidence`，避免继续堆叠 review、handoff、readiness wrapper。
- final.md 收口时需复核：是否形成同一 `task_id` 的 Algorithm -> O6 -> O7 `route_bag_evidence` 链路；是否保持 `safe_to_control=false`、`delivery_success=false`；是否没有把 DB3 存在性宣称成 live Nav2 run、route execution success 或 delivery success。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/final.md`：完成态，不是 blocked。下一轮建议补 `route_bag`、live Nav2 pose progress、真实或准现场 Nav2 result、媒体可访问证据或 delivery record。
- `sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`：完成态，不是 blocked。下一轮建议补真实或准现场 delivery record、operator confirmation 媒体、`route_bag` / live Nav2 pose progress。
- 结论：最近两轮不是同一 blocker 连续消费。本轮使用已存在准现场 bag DB3，不依赖真实串口、真实生产云、4G、OSS/CDN 或真实投递现场。

## 新增接口合同

新增 additive 摘要名称：`route_bag_evidence`。

建议 source schema：`trashbot.route_bag_evidence.v1`。

建议 O6 readback schema：`trashbot.o6.route_bag_evidence.v1`。

建议 proof scope：`software_proof_route_bag_evidence_intake_only`。

最小字段：

- `schema`
- `proof_scope`
- `source`
- `source_label`
- `status`
- `task_id`
- `task_id_source`
- `metadata_present`
- `db3_present`
- `db3_read_ok`
- `db3_size_bytes`
- `db3_sha256_prefix`
- `topic_count`
- `message_count`
- `timestamp_first_ns`
- `timestamp_last_ns`
- `sample_topic_names`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

字段解释：

- `route_bag_evidence.status=ready_not_route_execution_proof` 只能表示 DB3/metadata 摘要可读，不能表示真实路线执行成功。
- `sample_topic_names` 只能存 topic 名短文本，不存 ROS message payload。
- `db3_sha256_prefix` 只取短前缀用于定位，不回显完整 hash 或完整 artifact。
- O6/O7 禁止回显绝对路径、root、token、credential URL、raw payload、base64、完整 DB3 内容、串口路径或 `/cmd_vel`。

## 输入材料

Algorithm 可优先使用以下两个 route bag source。实现和 worker 报告可以引用这些绝对路径作为本地输入证据，但输出 JSON、O6 archive 和 O7 UI 必须只保留脱敏 source label / basename：

- `board-bringup-no-motion-sensor-route-bag`：`/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/route_bag/route_bag_0.db3`
- `board-live-full-stack-route-bag`：`/Users/m1/apps/rober/sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run/field_full_stack_20260609_230304/route_bag/route_bag_0.db3`

## 并行 owner 分工

### Task A - Algorithm / route bag evidence generator

Owner：`robot-algorithm-engineer`

职责：

- 在 `field_route_evidence_manifest.py` 增加可选 route bag evidence input，例如 `--route-bag-db3` / `--route-bag-metadata-yaml` / `--route-bag-source-label`。
- 使用 Python 标准库 `sqlite3` 摘要 DB3 的 `topics` / `messages` 表，统计 topic count、message count、timestamp first/last 和 sample topic names；缺依赖时不得要求 ROS2 runtime。
- 生成 `route_bag_evidence`，写入 manifest 顶层与 `field_motion_evidence_packet.route_bag_evidence`。
- 缺输入、DB3 不可读、SQLite schema 不符、空 topic/message、危险 true、path/root/token/raw/base64/credential URL 时输出同形 blocked 摘要。
- 更新导航文档与单元测试。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/algorithm_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/algorithm_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|safe_to_control|delivery_success" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/algorithm_worker_report.md
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/algorithm_worker_report.md
```

### Task B - O6 archive/readback support

Owner：`robot-software-engineer`

职责：

- 在 O6 field-evidence / artifact-bundle ingest 中接收和白名单 `route_bag_evidence`。
- 在 archive task detail、field evidence、artifact bundle、consumer detail alias 与 `include=route_bag_evidence` 中回读。
- 对坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64/credential URL/unsafe text 输出 fail-closed 摘要。
- 保持 additive，不破坏 field motion packet、Nav2 goal evidence、delivery result evidence、artifact access probe、offline seed smoke 和 route-root seed gate。
- 更新 O6 API 文档与单元测试。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|include=route_bag_evidence|safe_to_control|delivery_success" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md
```

### Task C - O7 consumer/UI support

Owner：`full-stack-software-engineer`

职责：

- 在 O7 consumer adapter 中请求/读取 `route_bag_evidence`。
- 在 shared contracts 和 O7 fixture preview UI 中展示 route bag source/status、topic/message/timestamp 摘要、blocked reasons、next evidence 和 false safety fields。
- 将 `route_bag_evidence` 汇总进 artifact bundle readiness、route replay readiness 或同等只读 readiness 区块，不打开任何 submit/control/action。
- 更新 PC 文档和 Vitest 覆盖。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|safe_to_control|delivery_success" pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md
```

### Task D - Product 收口

Owner：`product-okr-owner`

职责：

- 等三个 worker report 全部返回后，核对改动文件、验证命令、失败定位和剩余风险。
- 统一写 `tech-done.md`、`side2side_check.md`、`final.md`，不让工程 owner 并行写 `tech-done.md`。
- 根据证据保守判断 O6/O7 是否上调；除非出现真实 production cloud、真实 live Nav2 route run、真实 delivery record/operator confirmation 或完整路线验收，否则不归档 KR。
- 当前计划创建阶段不修改 `OKR.md`；implementation 收口阶段如需要更新 OKR，必须引用 worker report 和 sprint 收口证据。

建议后续允许改动范围：

- `/Users/m1/apps/rober/OKR.md`
- `/Users/m1/apps/rober/docs/process/okr_progress_log.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/tech-done.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/side2side_check.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/final.md`

验收命令：

```bash
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/algorithm_worker_report.md
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o7_worker_report.md
rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|O6|O7|safe_to_control=false|delivery_success=false" sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake
```

## 全局安全边界

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`
- `live_nav2_run_proven=false`
- `route_execution_success=false`

任何新增路径都不得回显绝对路径、root、token、credential URL、raw payload、base64、完整 DB3 内容、串口路径、`/cmd_vel` 或真实控制成功声明。DB3 可读只代表准现场 route bag evidence 可消费，不代表 production cloud、live Nav2 run、真实 delivery record、operator confirmation 或 delivery success。

## 本计划文档验收命令

```bash
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/pre_start.md
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/prd.md
test -f sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|route_bag_evidence|O6|O7|robot-algorithm-engineer|robot-software-engineer|full-stack-software-engineer|验收命令|safe_to_control=false|delivery_success=false" sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake
git diff --check -- sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake
```
