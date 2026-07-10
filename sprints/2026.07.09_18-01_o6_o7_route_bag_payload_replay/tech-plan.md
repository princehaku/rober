# O6/O7 Route Bag Payload Replay Tech Plan

## Sprint 类型

sprint_type: epic

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6、O7，并列约 59%。
- 本 sprint 是否针对最低 Objective：是。
- 选择理由：上一轮已经完成 DB3 route bag 元数据摘要 intake，本轮按产品方向升级为 payload-derived replay evidence，直接消费 `messages.data` BLOB 的安全摘要，而不是继续新增只读 wrapper 或停留在 metadata/readiness 层。
- final.md 收口时需复核：是否形成同一 `task_id` 的 Algorithm -> O6 -> O7 `route_bag_payload_replay` 链路；是否保持 `safe_to_control=false`、`delivery_success=false`；是否没有把 payload 可读性宣称成真实 live Nav2 run、route execution success 或 delivery success。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`：完成态，不是 blocked。剩余风险是缺真实 `route_bag`、live Nav2 pose progress、delivery record、operator confirmation 和 delivery success。
- `sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/final.md`：完成态，不是 blocked。剩余风险是只证明了 DB3 metadata 摘要 intake，没有证明 raw ROS message payload 的安全解析/回放。
- 结论：最近两轮没有同一 blocker 连续消费。本轮聚焦 payload-derived replay evidence，不依赖真实串口、真实生产云、4G、OSS/CDN 或真实投递现场。

## 新增接口合同

新增 additive 摘要名称：`route_bag_payload_replay`。

建议 source schema：`trashbot.route_bag_payload_replay.v1`。

建议 O6 readback schema：`trashbot.o6.route_bag_payload_replay.v1`。

建议 proof scope：`software_proof_route_bag_payload_replay_only`。

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
- `payload_sample_count`
- `payload_size_min_bytes`
- `payload_size_max_bytes`
- `payload_size_avg_bytes`
- `payload_sha256_prefix_samples`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

字段解释：

- `route_bag_payload_replay.status=ready_not_route_execution_proof` 只能表示 DB3/metadata/payload 摘要可读，不能表示真实路线执行成功。
- `sample_topic_names` 只能存 topic 名短文本，不存 ROS message payload。
- `payload_sha256_prefix_samples` 只取短前缀用于定位，不回显完整 hash 或完整 payload。
- `payload_size_*` 只记录统计值，不回显原始内容。
- O6/O7 禁止回显绝对路径、root、token、credential URL、raw payload、base64、完整 DB3 内容、串口路径或 `/cmd_vel`。

## 输入材料

Algorithm 可优先使用上一轮已知的准现场 route bag source。实现和 worker 报告可以引用这些绝对路径作为本地输入证据，但输出 JSON、O6 archive 和 O7 UI 必须只保留脱敏 source label / basename：

- `board-bringup-no-motion-sensor-route-bag`：`/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/route_bag/route_bag_0.db3`
- `board-live-full-stack-route-bag`：`/Users/m1/apps/rober/sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run/field_full_stack_20260609_230304/route_bag/route_bag_0.db3`

## 并行 owner 分工

### Task A - Algorithm / route bag payload replay generator

Owner：`robot-algorithm-engineer`

职责：

- 在 `field_route_evidence_manifest.py` 增加可选 route bag payload replay input，例如 `--route-bag-db3` / `--route-bag-metadata-yaml` / `--route-bag-source-label`。
- 使用 Python 标准库 `sqlite3` 只读摘要 DB3 的 `topics` / `messages` 表，并对 `messages.data` 做安全统计：payload size 分布、hash prefix sample、timestamp first/last、sample topic names；缺依赖时不得要求 ROS2 runtime。
- 生成 `route_bag_payload_replay`，写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_payload_replay`。
- 缺输入、DB3 不可读、SQLite schema 不符、空 topic/message、payload 为空、危险 true、path/root/token/raw/base64/credential URL 时输出同形 blocked 摘要。
- 更新导航文档与单元测试。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/algorithm_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/algorithm_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|safe_to_control|delivery_success" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/algorithm_worker_report.md
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/algorithm_worker_report.md
```

### Task B - O6 archive/readback support

Owner：`robot-software-engineer`

职责：

- 在 O6 field-evidence / artifact-bundle ingest 中接收和白名单 `route_bag_payload_replay`。
- 在 archive task detail、field evidence、artifact bundle、consumer detail alias 与 `include=route_bag_payload_replay` 中回读。
- 对坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64/credential URL/unsafe text 输出 fail-closed 摘要。
- 保持 additive，不破坏 field motion packet、Nav2 goal evidence、delivery result evidence、artifact access probe、offline seed smoke、route-root seed gate 和 route bag evidence intake。
- 更新 O6 API 文档与单元测试。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o6_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o6_worker_report.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|include=route_bag_payload_replay|safe_to_control|delivery_success" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o6_worker_report.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o6_worker_report.md
```

### Task C - O7 consumer/UI support

Owner：`full-stack-software-engineer`

职责：

- 在 O7 consumer adapter 中请求/读取 `route_bag_payload_replay`。
- 在 shared contracts 和 O7 fixture preview UI 中展示 route bag source/status、topic/message/timestamp 摘要、payload size/hash prefix 摘要、blocked reasons、next evidence 和 false safety fields。
- 将 `route_bag_payload_replay` 汇总进 artifact bundle readiness、route replay readiness 或同等只读 readiness 区块，不打开任何 submit/control/action。
- 更新 PC 文档和 Vitest 覆盖。代码技术注释必须使用中文，且保持注释比例超过 20%。
- 只写自己的 worker report：`/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o7_worker_report.md`。不得写 `tech-done.md`。

允许改动范围：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o7_worker_report.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|safe_to_control|delivery_success" pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o7_worker_report.md
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o7_worker_report.md
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
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/tech-done.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/side2side_check.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/final.md`

验收命令：

```bash
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/algorithm_worker_report.md
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o6_worker_report.md
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/artifacts/o7_worker_report.md
rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|O6|O7|safe_to_control=false|delivery_success=false" sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay
```

## 全局安全边界

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`
- `live_nav2_run_proven=false`
- `route_execution_success=false`

任何新增路径都不得回显绝对路径、root、token、credential URL、raw payload、base64、完整 DB3 内容、串口路径、`/cmd_vel` 或真实控制成功声明。DB3 可读只代表准现场 route bag payload replay evidence 可消费，不代表 production cloud、live Nav2 run、真实 delivery record、operator confirmation 或 delivery success。

## 本计划文档验收命令

```bash
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/pre_start.md
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/prd.md
test -f sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|route_bag_payload_replay|O6|O7|robot-algorithm-engineer|robot-software-engineer|full-stack-software-engineer|验收命令|safe_to_control=false|delivery_success=false" sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay
git diff --check -- sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay
```

