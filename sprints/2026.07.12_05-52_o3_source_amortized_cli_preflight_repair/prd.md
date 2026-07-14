# PRD - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target lane: `O3/O1 strict no-motion runtime recovery`

## 用户价值和产品北极星

用户需要的是一条能把真实板继续推向路径生成的可复验工程路径，而不是更多只读 surface。产品北极星仍是普通手机用户把垃圾交给小车后，小车沿固定路线送达垃圾点；本轮的产品价值是修掉 helper 的 source/ROS2 CLI preflight 抖动，让后续验证重新落到 `/map_server`、AMCL、TF 和 planner path 这些真实路线前置门槛。

## 背景

上一轮已证明 manual same-run strict no-motion graph readback 成功，但 helper 主路径仍没有复现同样的 ready 状态：

- `board_source_preflight_ros2_cli_which_timeout`
- `workspace_source_or_env_mismatch`
- `skipped_without_sourced_ros2_cli_ready`
- `daemon_reset_not_executed`

同时，上一轮明确保留：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

因此本轮不能把 manual readback 包装成 mission progress。要先让 helper 自己在同一个 shell 中完成 source、path lookup 和 ROS2 CLI readiness，然后再回到 localization/path gate。

## 问题定义

当前问题不是“ROS2 graph 是否永远不可读”。manual readback 已证明 graph 可以在 strict no-motion 条件下可见。当前问题是 helper 的 source 与 CLI readiness 分段执行导致 artifact 主路径 fail-closed：

1. source stage 与 `command -v/which/type -a ros2` 不在同一个稳定 shell 里完成；
2. helper 看到的 ROS2 path/env 和 manual shell 看到的状态可能不一致；
3. CLI readiness 没有在一次 amortized shell 内被同时证明；
4. blocker 因此停留在 `workspace_source_or_env_mismatch`，阻止后续 `/map_server`、`/amcl_pose`、TF 和 planner path gate 继续执行。

## 本轮不做什么

- 不做 O5 support-only wrapper、readback、probe 或 readiness packet。
- 不改 `OKR.md`、`docs/process/okr_progress_log.md` 或历史 sprint。
- 不执行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不把 helper preflight ready 误判为 path generation、route execution、delivery、HIL 或 production success。

## 成功标准

计划阶段定义的成功标准如下：

1. `robot-software-engineer` 修复 helper，使 source、path lookup、ROS2 CLI readiness 和目标 CLI invocation 在同一个 amortized shell 中完成或产生结构化 fail-closed detail。
2. targeted unit tests 覆盖 amortized source/CLI preflight、timeout/root-cause classification 和 no-motion false fields。
3. local helper dry-run 在没有 true board 条件时 fail-closed，不触发运动，不误报 ready。
4. 若 true board SSH 可达，完成 strict no-motion push/run/pull，并产出本 sprint `artifacts/` 下的 raw artifact；不可达时写清 SSH/网络/权限边界。
5. artifact 若 ready，应继续尝试回到 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate；若仍 blocked，应给出比 `workspace_source_or_env_mismatch` 更窄的下一跳。

## 验收口径

Product 验收只看本轮是否让 helper 主路径比上一轮更接近 same-run path generation：

- 可接受：`board_source_preflight_ready` 后进入 lifecycle/localization/path gate，且所有 no-motion false fields 保持 false。
- 可接受：仍 blocked，但从 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 收窄到可执行下一跳。
- 不可接受：只复述 manual graph readback、只增加 summary surface、只调整 timeout 文案、或让 safety fields 漂成 true。

## OKR 更新原则

本轮计划阶段不调整 OKR。执行收口时也不应调整 OKR 百分比，除非出现以下任一新证据：

- same-run path generation success；
- route execution；
- delivery/operator acceptance；
- current live HIL；
- production external evidence。

没有上述证据时，本轮只能记为 O3/O1 supporting no-motion diagnostic delta，不归档 KR。

## 责任划分

- Product：定义用户价值、范围边界、验收口径和 closeout 判断。
- `robot-software-engineer`：实现 helper 修复、targeted tests、navigation docs 同步、local dry-run、true-board strict no-motion artifact 和 `tech-done.md`。
- Hardware：本轮不打开 WAVE ROVER UART，不修改底盘或串口配置；无实现责任。
- Algorithm：本轮不调 NavigateToPose，不改规划算法；仅在 helper ready 后由 Robot Software 读取 path gate 事实。
- Full-stack：本轮不新增 UI/API surface。

## 需要同步的 sprint 文档

计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行阶段由 `robot-software-engineer` 继续更新：

- `tech-done.md`
- `artifacts/`

验收/收口阶段后续再补：

- `side2side_check.md`
- `final.md`
