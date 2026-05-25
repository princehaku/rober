# Behavior Structure Boundaries

本轮 behavior 重构只做内部结构治理，不改变 ROS2 action/topic/service
契约，也不新增产品能力。

## 模块边界

- `task_orchestrator.py` 仍是 `/trashbot/collect_trash`、`/trashbot/patrol`
  和 `/trashbot/confirm_dropoff` 的兼容入口。
- `delivery_contracts.py` 集中放置 `RobotState`、`NavigationResult` 和
  fixed-route 进度字段，避免状态机、导航结果和 task record 证据字段分散漂移。
- `delivery_elevator_assist.py` 集中维护电梯 assisted delivery dry-run /
  rehearsal artifact 的 schema、proof gate、not-proven 边界和安全校验。
- `delivery_remote_status.py` 只处理 remote bridge 状态落盘/回传前的安全过滤，
  不执行 collect、dropoff、cancel，也不触碰 ACK 游标推进。

## 兼容性

- 外部仍可从 `ros2_trashbot_behavior.task_orchestrator` 访问
  `RobotState`、`NavigationResult` 和电梯 assist 常量。
- `TrashCollection.Feedback` 继续使用既有字段；电梯子阶段仍通过
  `current_step=elevator:<phase>` 表达。
- remote cloud command envelope 仍由 `remote_bridge_protocol.py` 校验，
  只接受 `collect`、`confirm_dropoff`、`cancel` 三类命令。

## Evidence Boundary

所有 dry-run / rehearsal artifact 结果继续保持 `source=software_proof`、
`delivery_success=false`、`primary_actions_enabled=false`。这些结构化 helper
只减少重复和漂移风险，不证明真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route、
WAVE ROVER 运动、真实串口/UART、HIL 或真实送达成功。
