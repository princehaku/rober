# O3 Managed Runtime Scan Attempt Recovery PRD

## 用户价值和产品北极星

产品北极星不变：让普通手机用户把垃圾交给机器人后，机器人能沿固定路线稳定送达并可复盘。本轮不追求运动、不追求 delivery success，本轮要解决的是“最新 true-board runtime 证据为何回不到 `/scan` attempt 层”，因为这个问题直接卡住定位、路径生成和后续 route evidence。

## 用户问题

当前 live no-motion 链路的问题不是没有设计出更多 proof 字段，而是最新板端 artifact 无法稳定复现到 `/scan` BEST_EFFORT / RELIABLE attempt 层。只要这一步缺失：

- `/amcl_pose` 无法继续判定；
- `map_to_odom` 无法继续判定；
- `path_generated=true` 无法形成 current-run proof；
- O1/O6/O7 都无法得到新的 current same-run path / route material。

## 产品目标

把上一轮“代码已支持双 QoS attempt，但最新现场 artifact 回退到 partial runtime”转成一个可执行、可收口的 epic：

1. 恢复 managed runtime / ROS2 source 后的稳定可用性。
2. 让最新 true-board artifact 重新进入 `/scan` attempt 层。
3. 如果仍不能进入 `/scan` attempt 层，收敛出更前置的 root cause，而不是继续修改 QoS 合同。

## 范围

必须做：

- 围绕 `managed runtime`、`ROS2 source`、CLI/runtime readiness、Nav2 lifecycle、`/scan` attempt 入口做恢复与诊断。
- 保留并复用现有 BEST_EFFORT / RELIABLE `/scan` attempt 合同；只有在 attempt 再次出现后，才继续解释 sample/timeout/classification。
- 运行本地 fail-closed、目标单测、true-board helper 和 artifact 拉回。
- 更新导航文档，使本轮 runtime recovery 的读取顺序、proof boundary 和 fail-closed 语义可查。
- 在 `tech-done.md` 中写清最新 artifact 是否进入 `/scan` attempt 层，以及没进入时的最前置 blocker。

不做：

- 不改 `OKR.md`；
- 不改 O5 relay / production readiness；
- 不改 O6 archive/readback；
- 不改 O7 workstation；
- 不做运动控制、不追求 route execution success；
- 不把 no-motion proof 外推成 HIL 或 delivery proof。

## 核心抓手

- 先恢复 runtime，再判断 `/scan`。
- 只接受 latest true-board artifact，不拿历史或首次偶发成功覆盖最新失败事实。
- 明确区分两类结论：
  - `scan_attempt_recovered`：已回到 `/scan` attempt 层；
  - `runtime_still_blocked_before_scan_attempt`：仍卡在更前置 blocker。

## 成功定义

强成功：

- 最新 true-board artifact 进入 `/scan` BEST_EFFORT / RELIABLE attempt 层，并能读出 sample/timeout/classification。

可接受成功：

- 最新 true-board artifact 仍未进入 `/scan` attempt 层，但 root cause 比上一轮更前置、更具体，例如：
  - `ros2_command_unavailable_after_bash_source`
  - `managed_runtime_wait_timeout`
  - `path_generation_requested_but_ros2_unavailable`
  - 或同等级别 lifecycle/runtime blocker

失败：

- 继续只改 `/scan` QoS 合同；
- 没有最新 true-board artifact；
- 不能回答“为什么最新 artifact 没进入 `/scan` attempt 层”；
- 误改 safety / delivery / HIL 顶层 false 字段。

## 优先级和验收字段

P0 关键字段：

- `status`
- `evidence_type`
- `proof.managed_runtime_started`
- `proof.map_server_active`
- `proof.amcl_active`
- `proof.localization_signal_freshness["/scan"].probe.boundary`
- `proof.localization_signal_freshness["/scan"].probe.best_effort_attempt`
- `proof.localization_signal_freshness["/scan"].probe.reliable_attempt`
- `proof.path_generated`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`
- `root_causes[*]`

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`

本轮不并行派发其他 owner；如需接口事实，仅允许只读咨询，不拆成多 owner 实现。

## 风险、阻塞和需要补齐的证据链

- 风险：managed runtime / ROS2 source 恢复后仍可能回不到 `/scan` attempt 层，说明 blocker 在更前置的 lifecycle / environment。
- 阻塞：若缺最新 live artifact，本轮无法收口为 mission-progress，只能收口为 fail-closed diagnostic progress。
- 证据链：需要最新 true-board runtime artifact、相关 stdout/stderr 摘要，以及 `tech-done.md` 对 root cause 的明确收敛。

## 需要创建或更新的 sprint 文档

planning 阶段：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

implementation / closeout 阶段：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
