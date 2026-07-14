# Pre Start - O3 Radar Status Baudrate Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`
- Product owner: `product-okr-owner`
- Primary implementation owner: `robot-software-engineer` / Robot Software
- Conditional implementation owner: `robot-algorithm-engineer` / Algorithm
- Start time: `2026-07-12 21:57 CST`
- Scope: O3/O1 strict no-motion radar status baudrate readback repair, then conditional planner-only localization/path proof.
- OKR handling: 如果本轮仍只能证明 readback，而不能证明 same-run path/route/delivery，则 OKR 百分比保持 `不调整`，KR `不归档`。

## 用户价值和产品北极星

产品北极星仍是普通手机用户一键发车后，小车可验证地完成固定路线送达，或给出可信失败原因。本轮不允许发车、不允许底盘控制；用户价值是把现场 LiDAR/定位链路里的配置事实纠正为可信 readback，避免后续 Algorithm 在错误 baudrate 认知上继续定位 `/scan`、`/amcl_pose` 和 TF。

## 上轮事实基线

事实基线采用 `sprints/2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md` 和 `tech-done.md`：

- `existing_lifecycle_readonly_collector_final.json` 已证明 `proof.status=scan_once_hz_raw_packet_tf_observed`。
- 现有 `150000` lifecycle 已观察 `/scan` once/hz、`/lidar/raw_packet` 和 TF。
- holder PID `550922` owns `/dev/ttyACM0`。
- actual lifecycle start command 和 scan-proof command 均使用 `--serial-baudrate 150000`。
- `/api/radar/status` top-level 仍报告 `baudrate=230400`，形成 radar status / lifecycle config drift。
- 首轮 `230400` smoke 被 preexisting/new holder overlap 与 `serial.serialutil.SerialException` 污染；clean retry 已 fail-closed on holder PID `550922`，不是 clean exclusive `230400` proof。
- 安全字段继续固定：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 最近两轮 Blocker 扫描结论

- `2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/final.md` 的 blocker 是 `/scan_reliable_and_best_effort_timeout` 被拆成 endpoint visible、QoS compatible/no sample、LiDAR runtime exception candidate。该轮把下一步指向 Hardware after vendor docs。
- `2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md` 已把上一轮 broad `/scan` timeout / LiDAR runtime exception candidate 推进到更窄的 radar status / lifecycle config drift：现有 `150000` lifecycle 可读 `/scan`、raw packet、TF，但 `/api/radar/status` 仍显示 stale `230400`。
- 本 sprint 不连续消费同一个根因第三轮；它使用更窄的新 blocker：`/api/radar/status` baudrate readback stale default。若本轮只得到 readback 一致性而没有 Algorithm same-run path proof，仍按 support/blocker narrowing 收口，不计 OKR 增量。

## 本轮核心抓手

1. Robot Software 先修 `/api/radar/status` baudrate readback，使 top-level `baudrate` 来自 current lifecycle/status command 或 driver diagnostics，而不是 stale default `230400`。
2. Robot Software 必须证明 status controls 中 `start` 和 `scan_proof_refresh` 的 `--serial-baudrate 150000` 与 top-level readback 一致，并保持 no-motion false fields。
3. 只有 Robot Software readback gate 通过后，Algorithm 才复用现有 `150000` lifecycle，不启动第二个 driver，重跑 `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof。
4. 若 Algorithm 无法在同一 run 证明 path generation，必须输出最窄 blocker，不得把 readback 修复包装成 mission progress。

## Owner 分工

- Robot Software: P0，修改 radar status readback、补单元测试、补 docs、在 `tech-done.md` 写实现与验证证据。
- Algorithm: P1 conditional，只有 Robot Software gate 通过后进入；复用现有 `150000` lifecycle 做 strict no-motion localization/path proof。
- Hardware: 本轮不默认进入。仅当 Robot Software 或 Algorithm 证明需要 exclusive-holder USB/power/baud check 时重入；重入前必须读 `docs/vendor/VENDOR_INDEX.md`。
- Product: 验收事实边界、更新 `side2side_check.md` / `final.md`，只有 mission-grade evidence 到位才建议 OKR 调整。

## 安全边界

本轮继续 strict no-motion：

- 禁止 `/cmd_vel`。
- 禁止 `/api/base/manual`。
- 禁止 NavigateToPose。
- 禁止 WAVE ROVER UART / `/dev/ttyS5`。
- 禁止为了比较 baudrate 随意 stop 当前 `150000` holder。
- 所有 artifacts 必须继续固定 `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 需要创建或更新的 Sprint 文档

本轮计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现和收口阶段必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
