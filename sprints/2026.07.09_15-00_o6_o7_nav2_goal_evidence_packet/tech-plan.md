# O6/O7 Nav2 Goal Evidence Packet Tech Plan

## Sprint 类型

sprint_type: epic

## 目标

把已有 `onboard/scripts/o11_nav2_goal_execution_proof.py` 产出的 Nav2 goal execution proof JSON 作为输入，规划后续工程把它接入 `field_motion_evidence_packet` / O6 archive readback / O7 consumer detail，形成同一 `task_id` 下的 `nav2_goal_execution_evidence` 摘要。

O3 现场路线证据 lane 仍是更高优先级，但本轮通过消费 O11 proof 中的现场路线/运动相关证据，让 O6/O7 不再停留在 route/replay/keyframe surface，而是开始接住 Nav2 goal/result 这一类任务执行证据。

本轮只创建 planning docs，不进入代码实现、测试实现、ROS2 runtime、真实云写入、真实串口、真实底盘动作或真实上车补证。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6、O7，并列约 50%。
- 本 sprint 是否针对最低 Objective：是。它直接服务 O6 的 archive ingest/readback 与 O7 的 consumer detail / replay / labeling readiness。
- 与 O3 的关系：O3 现场 lane 是更高优先级，但本轮没有绕开现场路线证据；它通过 O11 proof 消费 Nav2 goal execution 相关证据，作为 O6/O7 对现场路线/运动证据的下游归档与展示补强。
- `final.md` 收口时需复核：是否真的形成同一 `task_id` 的 `nav2_goal_execution_evidence`；是否保留 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`；是否没有宣称真实 production cloud、真实 live Nav2 run 或真实送达。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/final.md` 为完成态，明确下一步补 `nonzero_odom_capture_or_bag_replay`、`route_bag_or_live_nav2_log_with_pose_progress`、`nav2_goal_result_or_delivery_record`。
- `sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/final.md` 为完成态，已解除 route-root seed 对 `route_bag` 的硬 gate。
- 结论：最近两轮没有同一 blocker 连续 blocked。本轮不消费真实 production cloud、真实硬件或真实送达缺口，而是用现有 O11 proof fixture/离线证据推进最低 O6/O7。

## 并行 owner 分工

### `robot-algorithm-engineer`

职责：

- 从 O11 proof JSON 中抽取 `nav2_goal_execution_evidence`。
- 把该摘要 additive 写入或关联到 `field_motion_evidence_packet`。
- 保留 proof scope、goal/result 摘要、pose progress 或 blocked reason，避免输出原始路径、raw payload 或 base64。

允许改动范围：

- `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/scripts/o11_nav2_goal_execution_proof.py`
- `/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`
- `/Users/m1/apps/rober/onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-done.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/o11_nav2_goal_execution_proof.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest onboard.tests.test_o11_nav2_goal_execution_proof
```

### `robot-software-engineer`

职责：

- 在 O6 archive ingest/readback 中白名单回读 `nav2_goal_execution_evidence`。
- 保持 additive contract，不破坏既有 field evidence、artifact bundle、artifact access probe、offline seed smoke、route-root seed gate、field motion packet。
- 对危险 true、path、root、token、raw、base64、unsafe refs、schema mismatch 继续 fail-closed。

允许改动范围：

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-done.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

### `full-stack-software-engineer`

职责：

- 在 O7 consumer detail 中消费 O6 回读的 `nav2_goal_execution_evidence`。
- 展示 readiness、blocked reasons、next required evidence、proof scope 和 false safety fields。
- 不直接读取原始路径、token、root、raw/base64 媒体；遇到 dangerous true 或 schema mismatch 必须 fail-closed。

允许改动范围：

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-done.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

### `product-okr-owner`

职责：

- 本轮创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续三个 Engineer 完成后，核对验证证据、更新 `tech-done.md` / `side2side_check.md` / `final.md`，必要时再更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 保守判断 O6/O7 进度，不把 `nav2_goal_execution_evidence` 误归档为真实送达或真实生产云完成。

本轮允许改动范围：

- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/pre_start.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/prd.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-plan.md`

## 接口方案

### 新增 additive 摘要

摘要名称统一使用：`nav2_goal_execution_evidence`。

建议 schema：`trashbot.nav2_goal_execution_evidence.v1`。

建议最小字段：

- `schema`
- `task_id`
- `source`
- `proof_scope`
- `goal_requested`
- `goal_accepted`
- `goal_result_status`
- `pose_progress_summary`
- `route_bag_or_live_nav2_log`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control`
- `delivery_success`
- `primary_actions_enabled`
- `robot_control_executed`

### 输入边界

- 输入来源：O11 proof JSON 或同等 fixture。
- 关联方式：必须围绕同一 `task_id` 接入 `field_motion_evidence_packet`。
- 不接受：跨任务混合数据、原始绝对路径、root 泄漏、token、raw payload、base64 媒体、危险 true claim。

### Algorithm 输出边界

- 可以输出 goal/result 摘要、pose progress 摘要、proof scope、blocked reasons 和 next evidence。
- 不输出任意本机路径、不可控 raw JSON、base64 媒体或真实控制成功断言。
- 如果 O11 proof 缺少 goal/result 字段，必须输出 blocked reason，而不是伪造成功字段。

### O6 输出边界

- O6 archive detail / consumer detail 只暴露白名单字段。
- 对 dangerous true、path、root、token、raw、base64、unsafe refs、schema mismatch 继续 fail-closed。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 必须保留。

### O7 消费边界

- O7 只展示 `nav2_goal_execution_evidence` 的 readiness、blocked reasons、next evidence、proof scope 和摘要字段。
- 不把 `goal_result_status` 解释为真实送达成功；真实 delivery record 仍需后续证据。
- 缺少摘要、字段不兼容、安全旗标异常或危险 claim 时，必须 fail-closed。

## 技术任务

### Task A - Algorithm / O11 proof to packet

- 从 O11 proof JSON 读取 Nav2 goal execution 相关摘要。
- 生成 `nav2_goal_execution_evidence` 并写入 field motion packet 或其同一 `task_id` 关联摘要。
- 新增或更新单元测试覆盖正常 fixture、缺字段、schema mismatch、dangerous true/path/root/token/raw/base64 fail-closed。

### Task B - O6 archive readback

- 在 O6 ingest/readback 路径中加入 `nav2_goal_execution_evidence` 白名单。
- 确保 archive task detail、field evidence/packet readback 与 consumer detail 能读到同一摘要。
- 保持既有 O6 测试通过，并新增 fail-closed 覆盖。

### Task C - O7 consumer detail

- 在 O7 consumer adapter 和 UI 中读取并展示该摘要。
- 将 Nav2 goal evidence 作为 readiness / blocked reasons / next evidence，不打开 primary action。
- 保持 O7 route replay / labeling / artifact readiness 既有展示不回退。

### Task D - Product 收口

- 核对三方验证日志与 diff check。
- 更新 `tech-done.md`、`side2side_check.md`、`final.md`，必要时更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 明确 KR 是否不归档，通常本轮应只保守提升 O6/O7 软件侧证据，不归档 KR。

## 本轮计划文档验收命令

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|nav2_goal_execution|O6|O7" sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet
git diff --check -- sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet
```

## 后续 Engineer 验收命令

Algorithm:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/o11_nav2_goal_execution_proof.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest onboard.tests.test_o11_nav2_goal_execution_proof
```

O6:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

O7:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

Final whitespace:

```bash
git diff --check
```

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 风险

- 本轮只产出计划，不产生新的 runtime 能力。
- O11 proof JSON 如果不是同一 `task_id`，后续实现必须补 lineage 或 blocked reason，不能强行合并。
- `nav2_goal_execution_evidence` 仍可能只是 fixture/software proof，不证明真实 live Nav2 run、真实 production cloud 或真实 delivery success。
- O7 展示必须克制，避免把 goal accepted/result status 写成用户可发车或已送达。
- 若后续实现触及真实硬件、WAVE ROVER、ESP32、Orange Pi、UART 或底盘反馈，必须先查 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。
