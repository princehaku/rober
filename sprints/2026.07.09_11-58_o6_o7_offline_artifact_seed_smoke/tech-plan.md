# O6/O7 Offline Artifact Seed Smoke Tech Plan

## Sprint 类型

sprint_type: epic

## 目标

把离线路线材料 `route.csv` / `manifest.json` / `derived_replay.jsonl` 统一接到 O6/O7 的 software proof 链路中，形成一个可重复的 offline artifact seed smoke 计划。

本 sprint 只定义计划，不触发真实机器人控制、底盘动作、串口通信、云端生产写入或现场任务执行。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O6 与 O7 并列，均约 42%。
- 本 sprint 是否针对该 Objective：是，直接针对 O6/O7 的 offline artifact seed smoke。
- 如不针对：不适用，本 sprint 就是为这两个最低 active Objective 设计离线证据链。
- 收口时复核：后续实现是否仍然停留在软件侧离线 seed smoke，是否没有把摘要误写成真实生产云、真实媒体或真实控制成功。

## Owner 分工

### `robot-software-engineer`

- 主责 O6 seed ingest / readback 的实现方案。
- 将离线路线 seed 绑定到同一 `task_id`，产出可读摘要、blocked reason 和 next evidence。
- 负责后续单元测试与回归验证主链路。

### `robot-algorithm-engineer`

- 主责离线路线材料语义整理。
- 负责确认 `route.csv`、`manifest.json`、`derived_replay.jsonl` 的字段对应关系、时序关系和 seed 归属。
- 负责把路线语义写成可供 O6/O7 消费的稳定输入定义。

### `full-stack-software-engineer`

- 主责 O7 consumer detail / readiness 展示方案。
- 只消费 O6 摘要，不把 ref 字符串、绝对路径或不可访问资源误报为真实媒体。
- 负责后续 UI、adapter 和前端测试验证。

### `product-okr-owner`

- 主责范围裁剪、验收口径和最终收口判断。
- 只做计划与验收，不改实现代码。

## 文件范围

本次文档创建阶段只允许修改以下三个文件：

- `/Users/m1/apps/rober/sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/pre_start.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/prd.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/tech-plan.md`

后续实现阶段拟改范围，供未来子 agent 参考，不属于本次文档创建动作：

- O6 runtime 与测试：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`、`docs/interfaces/o6_cloud_archive_api.md`
- O7 runtime 与测试：`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`、`pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`、`docs/product/pc_tools_workstation.md`
- 离线 seed 输入：`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/`、`sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl`

## 接口边界

1. 仅做 additive 变更，不破坏现有 O6 archive/read 和 O7 consumer contract。
2. 任何对外输出都必须是摘要、计数、blocked reason、next evidence 或可控的元数据，不得输出原始大对象、token、绝对路径、base64 媒体、串口、底盘或控制字段。
3. 离线 seed smoke 只验证 software proof，不把 `route.csv` 或 `derived_replay.jsonl` 误标为真实生产云数据或真实现场成功。
4. 若 seed 缺失、格式不兼容或不在 allowlist，则必须 fail-closed。

## 技术方案

### Task A - O6 offline seed ingest / readback

- 以离线路线材料为输入，构造一条可读的 O6 seed smoke 计划。
- 统一把 route、manifest、replay 归到同一 `task_id`，并保留 route/event/evidence 的摘要关系。
- 对危险字段和不可访问资源返回明确 blocked reason。

### Task B - O7 consumer readiness / preview

- O7 只消费 O6 输出的摘要和 blocked reason。
- UI/adapter 显示 readiness、next evidence、seed 来源和失败原因，但不暴露原始内容。
- 缺字段或 schema 不匹配时继续 fail-closed。

### Task C - Offline seed semantics normalization

- 把 `route.csv` 与 `derived_replay.jsonl` 视为同一离线路线证据链的两个视图。
- 通过 manifest 或等价索引把它们串成稳定的 seed 定义。
- 避免把 replay-only 数据误当作真实控制或真实投递证据。

## 验收命令

本轮文档创建完成后，先做文档存在性与关键字检查，再做无差异检查：

```bash
test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/pre_start.md && test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/prd.md && test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O6|O7|offline artifact seed|robot-algorithm-engineer|robot-software-engineer|full-stack-software-engineer|验收命令|safe_to_control: false|delivery_success: false|primary_actions_enabled: false|robot_control_executed: false" sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke
git diff --check
```

## 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 风险

- 这只是离线 artifact seed smoke 计划，不是现场闭环。
- 真实生产云、真实媒体、真实 annotation API、真实 dataset export、真实机器人运动和长期路线验收仍未证明。
- 如果后续实现阶段发现 seed 结构与现有 O6/O7 合同不兼容，需要优先修正接口边界，而不是扩大输出字段。
