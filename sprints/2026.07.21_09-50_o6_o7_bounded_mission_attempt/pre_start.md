# Pre Start：O6/O7 当前服务复用的 bounded mission attempt

## Sprint metadata

- `sprint_type: epic`
- 时间：`2026-07-21 09:50 CST (+0800)`
- 目标 Objective：O6 / O7（各约 `93%`）
- 主责：`robot-software-engineer`
- 冻结证据评审：`robot-algorithm-engineer`
- Product 收口：`product-okr-owner`
- 状态：`planning_ready_for_engineering_dispatch`

## 上轮未完成项与 anti-repeat

- O5 约 `85%`，但 production provider/runtime 同根因已消费 `2/2`；本轮暂停 O5，不再创建 preflight、wrapper 或本地 provider receipt。
- O1 约 `95%`；`2026.07.21_08-50_o1_wheel_feedback_root_cause` 只完成规划，business worker 未执行。它与本轮路线任务无关，不复用 v8，不重复同参数 wheel jog/readback。
- `2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission` 的 holder blocker只禁止未授权释放服务。本轮选择另一条能力边界：复用现场已有 `trashbot-esp32-bridge.service` 与 `trashbot-lidar-lifecycle.service`，禁止 stop/restart/kill/replace，不要求独占维护窗口。
- 不再消费 deadline、stdin transport、readiness wrapper、holder inventory 或 browser/loopback support slice；本轮只有 same-window bounded mission evidence 才可能形成 OKR 增量。

## CEO 本轮授权与边界

CEO 本轮明确：小车运动已授权、物理位置受限、operator 看护、路线清空；上位机入口为 `ssh root@192.168.1.11 -p 37878`。

该授权仅允许本 sprint 在 Phase 0 全绿后进入一次 live action pipe：pre-stop、exactly-one `NavigateToPose` 到治理目标 `map (0.8, 0.25, yaw=0)`、同窗证据读取、post-stop 与 cleanup。授权不包含：

- stop/restart/kill/replace 既有 systemd 服务；
- 打开或抢占 `/dev/ttyS5`、`/dev/ttyACM0`；
- firmware 写入、`T=900`、直接 UART 写入；
- `/initialpose`、manual、direct `/cmd_vel`、第二个 goal 或 retry；
- 无人看护运动或超出已清空路线的目标。

Phase 0 只读 NO-GO 不消费运动 attempt；一旦唯一 live action pipe 发出 pre-stop，即视为授权已消费，后续失败只能进入 post-stop/abort/cleanup，不能重试。

## 本轮核心抓手

复用当前运行中的 base/LiDAR 服务和现有 Upper/Nav2 helper，在不改变现场 service/UART ownership 的前提下完成：

1. current runtime、地图、定位、TF、planner/controller、path、障碍物与 stop endpoint 的只读 Phase 0；
2. Phase 0 全绿后，exactly-one bounded `NavigateToPose`；
3. 同一窗口冻结 task、user action receipt、goal result、route progress、T=1001 与 pre/post-stop 材料；
4. 无论 success、abort 或 timeout，都执行一次 post-stop、action cancel（若需要）与 run-owned cleanup；
5. Algorithm 只读复核 frozen manifest，Product 保守判定是否达到 `C2 bounded_mission_attempt`，不把计划或 NO-GO 当成功。

## 成功与停止条件

- Phase 0 任一门失败：`READINESS_GO=false`，不进入 pre-stop/goal，封存一个 NO-GO artifact 后停止。
- 唯一 live pipe 发出后禁止 retry；goal success、abort、rejected、timeout 均须有结构化 terminal result 和 post-stop receipt。
- 只有 current task id、user action receipt、goal accepted/terminal、route progress、pre/post stop 与同窗 T=1001 可相互对齐，才可声明 `mission_attempt=true`；只有 action success 与清洁 cleanup 同时成立，才可考虑 `route_execution_success=true`。
- 本 sprint 不声明 `delivery_success=true` 或 `hil_pass=true`，除非出现本轮 tech-plan 明确要求之外的独立、可核查成功材料并由 Product 复核。
