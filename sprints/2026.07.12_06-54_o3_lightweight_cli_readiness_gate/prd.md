# PRD - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target lane: `O3/O1 strict no-motion runtime recovery`

## 用户价值和产品北极星

用户需要的是一条继续逼近 same-run path generation 的真实工程路径，而不是继续围绕 O5 readiness、credit、readback 做 support-only 包装。产品北极星仍是普通手机用户把垃圾交给小车后，小车沿固定路线送达垃圾点；本轮的产品价值，是把 true-board helper 的 CLI readiness 设计成更轻量、更可观测的 gate，让运行时验证重新回到 map server、AMCL、TF 和 planner path 这些真正决定路线闭环的前置门槛。

## 背景

上一轮 source-amortized preflight 已证明 source/path/rclpy 层不是当前 primary blocker：

- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`

但 helper 仍因为单一重型 CLI gate fail-closed：

- `ros2_cli_invocation_ok=false`
- `cli_ready=false`
- `runtime_ready=false`
- `board_source_preflight.classification=board_source_preflight_ros2_cli_invocation_timeout`
- `cli_invocation.command="ros2 --help >/dev/null"`
- `cli_invocation.timeout_s=6.0`
- `map_lifecycle_proof_not_clean`

这意味着继续延长 `ros2 --help` timeout，或者继续围绕 O5 support-only surface 做包装，都不是当前最短可执行路径。需要用更轻的 readiness 设计，把 CLI readiness 与 downstream runtime gate 分层。

## 问题定义

当前问题不是“ROS2 完全不可用”，而是 helper 把一个偏重的 CLI 调用当成唯一硬门槛，导致：

1. source/path/rclpy 已正常时，`cli_ready` 仍被 `ros2 --help` 冷启动卡死；
2. `runtime_ready` 无法回到 `/map_server`、AMCL、TF 和 planner path gate；
3. artifact 只能停在 `board_source_preflight_ros2_cli_invocation_timeout` 和 `map_lifecycle_proof_not_clean`，下一跳不够窄；
4. O3/O1 no-motion 现场 lane 被 helper preflight 选型卡住，而不是被真正的 localization/path blocker 卡住。

## 本轮不做什么

- 不做 O5 support-only wrapper、readback、credit、packet 或 readiness surface。
- 不修改 `OKR.md`、`docs/process/okr_progress_log.md` 或任何历史 sprint。
- 不实现 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不把 `cli_ready=true` 误判成 path generation、route execution、delivery、HIL 或 production success。

## 成功标准

计划阶段定义的成功标准如下：

1. `robot-software-engineer` 设计并实现 light/heavy 分层的 CLI readiness gate，不再把 `ros2 --help` 当唯一硬阻塞。
2. helper artifact 能同时记录 heavy help、lightweight readiness、`rclpy` import 和最终 `cli_ready` / `runtime_ready` 判断。
3. source/path/rclpy 已通过时，helper 应尽可能放行 `cli_ready=true` 进入下游 lifecycle/localization/path gate；若仍 fail-closed，必须给出更窄 blocker。
4. targeted tests 覆盖 readiness 分层、timeout/classification 和 no-motion false fields。
5. local dry-run 与 true-board strict no-motion run 都不触发运动，不误报 safe-to-control，不打开 base UART。

## 验收口径

Product 验收只看本轮是否让 helper 主路径更接近 same-run path generation：

- 可接受：`cli_ready=true`，并重新进入 `/map_server`、`/amcl_pose`、dynamic `map->odom`、planner path gate。
- 可接受：仍 blocked，但从 `board_source_preflight_ros2_cli_invocation_timeout` 收窄到更明确的 lightweight CLI / daemon / runtime blocker。
- 不可接受：只增加文案、只延长 timeout 而没有分层事实、只重复 O5 support-only surface、或让 no-motion safety fields 漂成 true。

## OKR 更新原则

本轮计划阶段不调整 OKR。执行收口时也不应调整 OKR 百分比，除非出现以下任一新证据：

- same-run path generation success；
- route execution；
- delivery/operator acceptance；
- current live HIL；
- production external evidence。

没有上述证据时，本轮只能记为 O3/O1 supporting no-motion diagnostic delta，不归档 KR。

## 责任划分

- Product：定义用户价值、方向判断、范围边界、验收口径和 closeout 规则。
- `robot-software-engineer`：实现 helper readiness gate、tests、navigation docs、local dry-run、true-board strict no-motion artifact 和 `tech-done.md`。
- Hardware：本轮不接触 UART、底盘协议或板级硬件配置；无实现责任。
- Algorithm：本轮不改规划算法，不触发 NavigateToPose；只允许在 helper 放行后读取 path gate 事实。
- Full-stack：本轮不新增 UI/API surface。

## 需要同步的 sprint 文档

计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行阶段由 `robot-software-engineer` 继续更新：

- `tech-done.md`
- `artifacts/`

验收/收口阶段后续补：

- `side2side_check.md`
- `final.md`
