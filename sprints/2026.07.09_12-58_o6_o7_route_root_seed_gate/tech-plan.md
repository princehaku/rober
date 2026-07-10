# O6/O7 Route Root Seed Gate Tech Plan

## Sprint 类型

sprint_type: epic

## 目标

解决 route-root seed 对 `route_bag` gate 的硬依赖，让 local/mock O6/O7 smoke 可以从 allowlist route root 独立生成同一 `task_id` 的 seed readiness 摘要。`route_bag` 后续仍可作为增强证据，但不能阻止 route root 的 software proof。

本轮只创建 planning docs，不进入代码实现、测试实现、ROS2 runtime、真实云写入、真实串口或真实底盘动作。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O7，约 44%。
- 次低且作为本轮依赖支撑的 active Objective：O6，约 45%。
- 本 sprint 是否针对最低 Objective：是。目标直接服务 O7 的 route replay / labeling / training data readiness，并通过 O6 route-root seed gate 提供可消费数据合同。
- 如不针对：不适用。本 sprint 由 CEO 明确指定为 O7 lowest active objective with O6 support。
- `final.md` 收口时需复核：route-root seed 是否确实摆脱 `route_bag` gate；是否仍然只声明 local/mock software proof；是否所有 safe flags 继续保持 false。

## owner分工 / Owner 分工

### `robot-software-engineer`

- 主责后续 O6 route-root seed gate 的实现方案。
- 定义 O6 readback 字段、fail-closed 规则、危险字段过滤和单元测试。
- 确保 `route_bag` 缺失时不阻断 route-root seed local/mock smoke。

### `robot-algorithm-engineer`

- 主责路线材料语义归一。
- 明确 route root 内 `route.csv`、manifest、derived replay、keyframe/evidence refs 与可选 `route_bag` 的关系。
- 定义最小 route root seed 可用条件和缺失字段的 blocked reason。

### `full-stack-software-engineer`

- 主责 O7 consumer detail / UI readiness 方案。
- 只消费 O6 摘要字段，不读取任意本地路径或原始媒体。
- 覆盖缺字段、unsafe ref、schema mismatch、`route_bag` missing 的 fail-closed 展示。

### `product-okr-owner`

- 主责 PRD、验收口径、OKR 进度边界和最终收口判断。
- 验收时确认没有把 local/mock seed smoke 写成真实生产云、真实媒体、真实路线或真实控制成功。

## 文件范围

本次文档创建阶段只允许修改以下三个文件：

- `/Users/m1/apps/rober/sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/pre_start.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/prd.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/tech-plan.md`

后续实现阶段拟改范围，供子 agent 派发时参考，不属于本次文档创建动作：

- O6 runtime 与测试：`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`、`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`、`/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- O7 runtime 与测试：`/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`、`/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`、`/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`、`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`、`/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`、`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- 路线材料合同文档：`/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`

## 接口边界

### O6 输入边界

- 允许使用 allowlist root 内的 route root 作为 local/mock 输入，例如 `route.csv`、manifest、derived replay JSONL、keyframe/evidence ref 摘要。
- `route_bag` 是可选增强输入；缺失时只能产生 `route_bag_missing_optional` 类 blocked reason，不得让 route-root seed gate 直接失败。
- route root 不在 allowlist、路径不安全、schema mismatch、必需 seed 文件缺失或危险字段为 true 时必须 fail-closed。

### O6 输出边界

建议使用 additive 摘要结构，例如 `trashbot.o6.route_root_seed_gate.v1` 或等价字段，最小包含：

- `schema_version`
- `proof_scope`
- `task_id`
- `route_root_seed_status`
- `route_bag_required`
- `route_bag_present`
- `route_csv_summary`
- `manifest_summary`
- `derived_replay_summary`
- `evidence_ref_summary`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control`
- `delivery_success`
- `primary_actions_enabled`
- `robot_control_executed`

输出不得包含 token、绝对路径、base64 媒体、原始大对象、串口字段、`/cmd_vel` 控制字段或真实 delivery success 声明。

### O7 消费边界

- O7 只读取 O6 consumer detail 中的 route-root seed gate 摘要。
- UI/adapter 可以展示计数、basename/ref 摘要、blocked reasons、next required evidence 和 proof scope。
- 缺少摘要、字段不兼容、危险字段为 true、unsafe refs 或 `route_bag_required=true` 但无证据时，必须 fail-closed。

## 技术方案

### Task A - O6 route-root seed gate

- 在 O6 archive / consumer detail 主路径新增 additive route-root seed gate 摘要。
- 将 route root 与已有 offline artifact seed smoke 绑定到同一 `task_id`。
- 明确 `route_bag_required: false`，并在缺少 `route_bag` 时输出可读 blocked reason 与 next evidence。

### Task B - 路线语义归一

- 定义 route root 最小可用条件：至少能证明同一 `task_id` 的 route path、manifest 身份和 derived replay 帧摘要。
- 对 route CSV 行数、replay 帧数、关键字段缺失、时间戳不连续等情况给出 blocked reason。
- 不把 replay-only、manifest-only 或 ref-only 数据误报成真实路线执行成功。

### Task C - O7 consumer readiness

- 在 O7 adapter / UI 中优先消费 O6 route-root seed gate 摘要。
- 缺少 `route_bag` 时显示为 local/mock route-root seed 可用但 `route_bag` evidence pending。
- 保持 route replay / labeling readiness 与 artifact readiness 的安全边界一致。

## 验收命令

本轮 planning docs 创建完成后运行：

```bash
test -f sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/pre_start.md && test -f sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/prd.md && test -f sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O6|O7|route-root seed|route_bag|owner分工|文件范围|接口边界|验收命令|safe flags false|safe_to_control: false|delivery_success: false|primary_actions_enabled: false|robot_control_executed: false" sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate
git diff --check
```

后续实现阶段建议由对应子 agent 追加运行：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check
```

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 风险

- 本轮只产出 planning docs，不产生 O6/O7 runtime 能力。
- route-root seed 解耦后仍只代表 local/mock software proof，不代表真实 `route_bag`、真实媒体、真实生产云或真实机器人路线执行。
- 若后续发现现有 O6 contract 无法容纳 additive 摘要，应优先补接口文档和 fail-closed 测试，再扩大 UI 展示。
