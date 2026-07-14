# Sprint Pre-Start

- sprint_type: epic
- sprint_id: `2026.07.15_00-53_o3_current_localization_runtime_recovery`
- 状态：前置决策完成，等待 Engineer 实施。
- 目标 Objective：O1（94%）中的 O3 live strict-no-motion localization runtime。
- 最低 Objective：O5（85%）。
- 切换原因：O5 缺真实 production endpoint/凭证，support-only 已重复消费。
- 当前 blocker：current graph 无 `/map_server`、`/amcl`。
- 已知 compact fix 边界：`local_fix_not_live_verified`。

## 用户价值

- 在不驱动车体的前提下恢复定位 runtime，取得同一窗口的 live localization 证据。
- 把阻塞从“缺 localization 节点”推进为可观测的 `/scan`、`/amcl_pose`、`map->odom` 事实。
- 不把本地修复、启动成功或静态图误报为 HIL、路线执行或交付成功。

## Owner 与协作

- 主责：`robot-algorithm-engineer`，负责上位机启动、重部署、采集、验证、修复和 `tech-done.md`。
- 咨询：`robot-software-engineer`，同轮并行只读核对 launch/graph/source，不改文件。
- Product：只做范围、验收和阶段收口，不写工程代码。

## 实施边界

- 目标上位机：`ssh root@192.168.1.11 -p 37878`。
- 使用现有 helper：`--strict-no-motion --managed-runtime-opt-in` 与现有 map YAML。
- 仅启动 localization-only runtime，并重部署 compact collector。
- 禁止 `--path-generation-opt-in`、planner/controller、NavigateToPose。
- 禁止 `cmd_vel`、base/manual 与任何 motion 行为。
- 同窗采集 `/scan`、`/amcl_pose`、dynamic `map->odom` 的 AMCL endpoint/timestamp/freshness。

## 开工门槛与风险

- map YAML 必须存在且可被 localization runtime 读取，否则 fail-closed。
- 若节点、topic、TF freshness 任一不满足，不得提升 OKR 百分比。
- cleanup 必须停止本轮启动的 runtime/collector，且不得影响既有进程。
- 结果固定保持 `safe_to_control=false`、`route_execution_success=false`。
- 同时保持 `delivery_success=false`、`hil_pass=false`。
