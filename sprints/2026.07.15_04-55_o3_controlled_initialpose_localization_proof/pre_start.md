# Sprint Pre-Start

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/`
- 状态：Epic 开工边界已冻结；本文、PRD 与 tech plan 创建后停止，由主节点另行派发实施。
- 唯一 owner：`robot-algorithm-engineer`
- 目标上位机：`root@192.168.1.11:37878`
- 目标 lane：O3/O1 current live strict-no-motion 定位初始化证明。

## 用户价值与产品北极星

用户价值是让机器人在完全不运动、不触发路线执行的前提下，获得可审计、可复验的当前定位初值，并形成 fresh `/amcl_pose` 与 AMCL dynamic `map->odom`。这直接服务于“可验证地可靠送达”的北极星，但本轮只恢复定位前提，不把定位输出包装成路线执行、HIL 或送达成功。

## 上轮事实与本轮授权

- 上轮 `2026.07.15_00-53_o3_current_localization_runtime_recovery` 已证明 map_server/AMCL active、fresh `/scan` 与 helper PGID clean cleanup。
- 上轮 `/amcl_pose` 为 `sample_count=0`，dynamic `map->odom` missing，AMCL 日志明确要求 initial pose。
- 上轮 helper 临时参数显式为 `set_initial_pose: false`；仓库 config 中存在 `set_initial_pose: true` 不能当作 live persisted pose 已被消费的证据。
- CEO 本轮授权：先审计 persisted pose；只有没有 live 消费证据，且 canonical map free-cell/world pose 可审计、AMCL `/initialpose` subscriber active、TF authority 清楚时，最多一次发布 `/initialpose`。

## OKR 映射与方向判断

- 当前最低 Objective 是 O5=`85%`；方向判断为本轮暂不继续 O5。
- 原因：production/cloud success blocker 仍需外部条件，support wrapper 已重复消费；继续包装不会形成 mission delta。
- 本轮调整到 O3/O1 current live localization，属于有真实上位机、可执行命令和可验证现场材料的抓手。
- O1=`94%` 主百分比默认保持；只有完成本轮 clean gate 才形成新的定位证据，但仍不等于 route/delivery/HIL credit。
- 当前 KR `不归档`；已完成 KR 历史区不做变更，证据来源仍为上一轮 `tech-done.md` 与 `final.md`。

## 范围、优先级与责任

- P0：persisted pose live 消费审计与 canonical map free-cell/world pose 审计。
- P0：受控 `/initialpose` 最多一次，以及同窗口 fresh `/scan`、fresh `/amcl_pose`、唯一 AMCL dynamic `map->odom` 证明。
- P0：helper 自有 PGID cleanup clean 与全部 false safety flags。
- 唯一责任 Engineer：`robot-algorithm-engineer`，单线负责实现、测试、SSH live capture、失败修复复验和 `tech-done.md`。
- Product 只负责范围、验收和阶段收口，不写工程代码。

## 强制禁止项

- 禁止 planner/controller/path、`--path-generation-opt-in`、NavigateToPose。
- 禁止 `/cmd_vel`、`/api/base/manual`、base manual、UART 或任何运动。
- 禁止 `pkill`、`killall`，禁止改 launch/config，禁止影响既有 LiDAR、ESP32 bridge 或 Upper API。
- 禁止以 config 中 `set_initial_pose: true`、旧窗口 pose/TF、静态 `map->odom` 或 endpoint 可见代替 current live 消费。

## 开工与收口边界

- Clean gate：同窗口 fresh `/scan`、fresh `/amcl_pose`、唯一 AMCL dynamic `map->odom` endpoint/publisher/header timestamp/freshness；`initialpose` 实际 publish attempt `<=1`；helper PGID residual `0`。
- 固定 `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`robot_control_executed=false`。
- 任一前置 gate 不清楚即不得发布；任一后置 gate 不满足即 fail-closed，不得进入 planner、控制或运动。
