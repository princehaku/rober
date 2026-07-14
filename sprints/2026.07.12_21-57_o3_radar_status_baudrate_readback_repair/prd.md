# PRD - O3 Radar Status Baudrate Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`
- Product owner: `product-okr-owner`
- Primary owner: `robot-software-engineer` / Robot Software
- Conditional owner: `robot-algorithm-engineer` / Algorithm
- Product status: planning

## 用户价值和产品北极星

北极星是普通手机用户一键发车后获得可信送达结果。本轮的直接用户价值是让上位机状态页、PC/手机读回和后续 O3 helper 看到一致的 LiDAR runtime 参数，避免 `/api/radar/status` 显示 `baudrate=230400` 而实际 runtime 使用 `150000` 的误导。

这不是用户可见送达能力；它是 fixed-route/nav 现场链路的前置事实修复。只有当 readback 一致后，Algorithm 才能继续把 `/scan` 输入接到 `/amcl_pose`、dynamic `map->odom` 和 planner-only path proof。

## OKR 映射和方向判断

- O5 当前约 `85%`，仍缺真实 external production evidence；继续 support/readiness packet 不计分。
- O1/O6/O7 当前约 `93%`，但 O1 仍缺 current same-run path generation success、Nav2 route execution success、current live HIL pass 和 safe-to-control 证据。
- O3 归档 Objective 临时激活为现场 strict no-motion lane；当前 blocker 是 radar status / lifecycle config drift。
- 方向判断：调整执行方向到 O3/O1 strict no-motion；暂停 O5 support-only；不做 O6/O7 surface/readback 包装。
- OKR 百分比：本轮计划默认 `不调整`。
- KR 归档：本轮计划默认 `不归档`。

## 需求

### R1 - Radar Status Baudrate Readback

`GET /api/radar/status` top-level `baudrate` 必须从 current lifecycle/status command、`o1_lidar_lifecycle.sh status` readback 或 `driver_diagnostics_latest.runtime.serial_baudrate` 等当前材料中选择，而不是固定 stale default `230400`。

验收口径：

- 当 lifecycle/status 或 diagnostics 指向 `150000` 时，`/api/radar/status.baudrate` 返回 `150000`。
- `controls.start.command.argv` 和 `controls.scan_proof_refresh.runtime_command.argv` 中的 `--serial-baudrate 150000` 与 top-level readback 一致。
- 如果 lifecycle/status 和 diagnostics 都不可读，必须 fail-closed 并明确 `baudrate_readback_source` / `baudrate_readback_status`，不得伪造当前 `150000`。
- 保留 vendor/reference 边界：`230400` 只能作为 WAVE ROVER reference/default candidate，不能覆盖 current runtime readback。

### R2 - Strict No-Motion Safety Contract

Robot Software 的 readback 修复不得启动底盘、不得打开 WAVE ROVER UART、不得发布运动控制。

验收口径：

- `safe_to_control=false`。
- `publishes_cmd_vel=false`。
- `calls_base_manual=false`。
- `uses_base_uart=false`。
- `robot_control_executed=false`。
- `route_execution_success=false`。
- `delivery_success=false`。
- `hil_pass=false`。

### R3 - Conditional Algorithm Path Proof

Robot Software readback gate 通过后，Algorithm 复用现有 `150000` lifecycle 做同窗 strict no-motion proof。

验收口径：

- 不启动第二个 `lidar_driver`。
- 不 stop 当前 holder PID `550922`，除非 Product/Hardware 明确改派 exclusive-holder 检查。
- 在同一 run artifact 中报告 `/scan`、`/amcl_pose`、dynamic `map->odom` 和 planner-only path result。
- `path_generation_attempted=true` 只允许在 localization ready 且 planner-only opt-in 条件下出现。
- 即使 planner-only path 生成成功，也不得声明 route execution、delivery success、HIL 或 safe-to-control。

## 非目标

- 不验证 clean exclusive `230400` runtime。
- 不进行 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。
- 不修改硬件接线、电压、串口默认配置或 launch 硬件参数。
- 不更新 `OKR.md` 或历史 sprint。
- 不把 readback 一致性本身计为 mission progress。

## 优先级和验收口径

P0 Robot Software：

- 修复 `/api/radar/status` `baudrate` stale default。
- 补充 targeted unit tests，至少覆盖 lifecycle readback `150000`、diagnostics fallback `150000`、readback missing fail-closed、no-motion false fields。
- 补充 `docs/hardware/board_sensor_stack_smoke.md` 的 readback 合同说明。

P1 Algorithm conditional：

- 只有 P0 通过后执行。
- 复用当前 `150000` lifecycle。
- 重跑 `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof。
- 输出同 run artifact，若失败则输出最窄 blocker。

## 风险、阻塞和证据链缺口

- 当前 `/api/radar/status` top-level `baudrate=230400` 会误导后续调试与产品状态展示。
- 现有 `150000` lifecycle 能观察 `/scan`、raw packet、TF，但仍未证明 `/amcl_pose`、dynamic `map->odom`、same-run path generation、route execution 或 delivery。
- holder PID `550922` 正在占用 `/dev/ttyACM0`；任何 exclusive check 都可能中断当前可用 readback。
- 如果本轮仅修复 readback，OKR 百分比保持 `不调整`，KR `不归档`。

## 已完成 KR 历史记录位置

本轮不归档 KR。既有历史位置保持：

- `OKR.md` 的已归档 Objective / KR 区。
- `docs/process/okr_progress_log.md`。
- 最近事实证据为 `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md` 和 `tech-done.md`。
