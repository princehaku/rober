# O6/O7 Field Motion Evidence Packet Tech Plan

## Sprint 类型

sprint_type: epic

## 目标

围绕已有 6 月现场 `map/route/keyframes/remote_capture` 运动材料制定一条实现计划，要求后续工程直接产出同一 `task_id` 的 field motion evidence packet，并由 O6 archive ingest / consumer detail 与 O7 consumer replay / labeling 主路径消费。

本轮只创建 planning docs，不进入代码实现、测试实现、ROS2 runtime、真实云写入、真实串口、真实底盘动作或真实上车补证。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6、O7，并列约 47%。
- 本 sprint 是否针对最低 Objective：是。它直接服务 O6 的现场证据 ingest/readback，以及 O7 的历史路线 replay / labeling 消费输入。
- 如不针对：不适用。CEO 已明确要求本轮推进最低 O6/O7，并消费已有现场材料。
- `final.md` 收口时需复核：是否真正把 6 月现场材料推到同一 `task_id` packet 计划；是否避免继续新增 wrapper；是否所有 false safety flags 继续保持。

## owner分工 / Owner 分工

### `robot-algorithm-engineer`

- 主责梳理 6 月现场 `map.yaml/.pgm`、`route.csv`、`manifest.json`、keyframes、remote_capture motion 日志之间的同一 `task_id` 关系。
- 定义 field motion evidence packet 的最小必需材料和 blocked reason。
- 明确 `route_bag_or_live_nav2_log` 是可选增强证据，不是 packet 生成前提。

### `robot-software-engineer`

- 主责 O6 archive ingest / consumer detail 的 packet contract。
- 设计 ingest/readback 最小字段、fail-closed 规则和危险字段过滤。
- 确保 packet 缺少 `route_bag` 时仍可依赖 route + manifest + replay + keyframe 摘要完成 local/offline 贯通。

### `full-stack-software-engineer`

- 主责 O7 consumer replay / labeling workspace 的消费计划。
- 只消费 O6 摘要字段，不直接读取原始路径、token、base64 媒体或控制字段。
- 对缺字段、schema mismatch、unsafe refs、dangerous true claim 做 fail-closed 展示。

### `product-okr-owner`

- 主责 PRD、验收口径、owner 路由、风险边界和最终收口判断。
- 监督本轮不把 planning 文档写成现场闭环完成，也不把 software proof 误写成真实送达成功。

## 允许改动范围

本次文档创建阶段只允许修改以下文件：

- `/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/pre_start.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/prd.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/tech-plan.md`

后续实现阶段拟改范围，供下一轮派单使用，不属于本轮文档创建动作：

- Algorithm / packet 语义与脚本文档：
  - `/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`
  - `/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`
  - `/Users/m1/apps/rober/sprints/2026.06.10_00-45_integrated-sensor-motion-capture/artifacts/`
- O6 ingest / archive / 测试：
  - `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- O7 consumer replay / 测试 / 文档：
  - `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
  - `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
  - `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
  - `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`

## 接口边界

### 输入边界

- 优先输入：同一 `task_id` 的 `map.yaml/.pgm`、`route.csv`、`manifest.json`、keyframes、remote_capture motion 日志、derived replay。
- 可选增强输入：`route_bag_or_live_nav2_log`。
- 不安全路径、跨任务混合材料、绝对路径泄漏、token 路径、base64 原始媒体、dangerous true claims 必须 fail-closed。

### O6 输出边界

后续实现建议输出 additive packet 摘要，至少包含：

- `task_id`
- `proof_scope`
- `field_motion_evidence_status`
- `map_ref_summary`
- `route_summary`
- `keyframe_summary`
- `motion_log_summary`
- `derived_replay_summary`
- `route_bag_or_live_nav2_log`
- `blocked_reasons`
- `next_required_evidence`
- `safe_to_control`
- `delivery_success`
- `primary_actions_enabled`
- `robot_control_executed`

### O7 消费边界

- O7 只读 O6 packet 摘要，不直接读原始文件系统路径。
- UI 只展示计数、basename/ref 摘要、blocked reasons、next required evidence 和 proof scope。
- 缺少 packet 摘要、字段不兼容或安全旗标异常时，必须 fail-closed。

## 技术方案

### Task A - Algorithm packet semantics

- 从 6 月现场 artifacts 中定义 packet 组成与最小合法集合。
- 明确哪些材料是必需，哪些是增强项。
- 把 `route_bag_or_live_nav2_log` 归类为增强证据，用于提高 replay/运动可信度，但不是首个 packet 的准入门槛。

### Task B - O6 archive ingest/readback

- 新增或扩展 O6 archive ingest 入口，让 field motion evidence packet 能围绕同一 `task_id` 写入。
- 确保 consumer detail 可回读 packet 摘要给 O7。
- 保持 fail-closed 和 additive contract，避免破坏既有 field evidence / artifact bundle / route-root seed gate 合同。

### Task C - O7 replay/labeling consumption

- 让 O7 历史路线回放与标注工作台优先消费 packet 摘要。
- 若 `route_bag_or_live_nav2_log` 缺失，仍展示可读的 offline readiness 与 next evidence，而不是把整个 workspace 标成完成。
- 保持所有主动作关闭。

## 验收命令

本轮 planning docs 创建完成后运行：

```bash
test -f sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/pre_start.md
test -f sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/prd.md
test -f sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O6|O7|field motion evidence|route_bag_or_live_nav2_log|robot-algorithm-engineer|robot-software-engineer|full-stack-software-engineer|验收命令|safe_to_control: false|delivery_success: false" sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet
```

后续实现阶段建议派单验收命令：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check
```

## false safety flags / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 风险

- 本轮仅产出计划，不产生 O6/O7 新 runtime 能力。
- 6 月现场材料若缺少统一 `task_id` 或时间线不连续，后续实现可能需要先补 packet lineage。
- `route_bag_or_live_nav2_log` 缺失时，必须守住“可 replay/readiness，不可宣称真实运动完成”的边界。
- 若后续实现无法在 additive contract 内表达 packet 摘要，必须先补接口文档和 fail-closed 测试，不能退回再造 wrapper。
