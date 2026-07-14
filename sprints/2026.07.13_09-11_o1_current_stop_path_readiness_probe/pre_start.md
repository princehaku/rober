# Pre Start - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Start time: 2026-07-13 09:11 CST
- Product owner: `product-okr-owner`
- Planned implementation owner: `rober-hardware-engineer`
- Execution model: single owner closed loop after Product planning
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`

## 用户价值和产品北极星

北极星仍是让普通用户把垃圾交给小车后，小车能安全沿固定路线送达并可随时停下。本轮不做路线执行，也不证明底盘可控；本轮只把下一轮受控 route execution 前必须存在的 current stop path / emergency stop readiness 做成可机读、可 mock/虚拟串口验证的前置证据。

用户价值是减少下一轮发车前的安全歧义：在任何非零 route execution 命令前，系统必须能说明 `/api/base/stop` 对应的停车路径、WAVE ROVER UART JSON zero-stop 帧、heartbeat 超时停车来源、mock 验证结果和禁止 `/api/base/manual` 的边界。

## 上轮未完成项和本轮切入

上一轮 `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md` 已接受为 O3/O1 no-motion bounded route command plan only。它明确拒绝 route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL、safe-to-control 或 O5 production/external evidence。

上一轮 next owner/action 要求：只有在 explicit operator approval、current live HIL/stop path、同窗口 LiDAR/localization/TF readiness 与 Nav2/controller result 可记录后，才用同一 `packet_id` / `route_intent_id` 收集受控 route execution record；不要重复 helper/export/readiness/route-intent、packet packaging、gate packaging、bounded-plan packaging 或 O6/O7 readback-only wrapper。

本轮只切入其中一个最窄缺口：current stop path / emergency stop readiness。它必须是 no-motion readiness probe，不触发非零运动，不调用 `/api/base/manual`，不宣称 HIL、route execution、safe-to-control 或 delivery。

## 当前最低 OKR 和切换原因

当前 `OKR.md` 4.1 数字完成度最低 Objective 是 O5，约 `85%`。本轮不继续 O5，因为最近 O5 production cutover readiness packet 已经是 `support_only`，下一步只有真实 external production evidence 才能考虑增量；继续 readiness packet、handoff、checklist 或 production wrapper 会重复消费同一 external-evidence blocker。

O1 约 `94%`，缺 current live WAVE ROVER HIL pass、current stop path、safe-to-control、Nav2 route execution success、delivery/operator acceptance、轮速方向、IMU/battery 标定和真实 route execution。相对 O5，O1 的 stop path readiness 可以在当前环境中用 vendor 资料、mock/虚拟串口和可机读 artifact 推进，但必须保持 support-only / no-motion 边界。

方向判断：继续 O1/O3 受控执行前置链路，不调整 OKR 主百分比，不暂停或替换 Objective。本轮不是 KR 完成，不做 KR 历史归档。

## Vendor 资料前置核对

本轮涉及 WAVE ROVER UART、JSON 指令、heartbeat 和 zero-stop，已按 `AGENTS.md` 要求先读 `docs/vendor/VENDOR_INDEX.md`，后续 Hardware owner 必须继续引用本地 vendor 来源：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：`BaseController` 使用 UART serial，`process_commands` 写入 `json.dumps(data) + '\n'`，示例默认 `/dev/ttyAMA0` at `115200`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`T=1` 是 speed control，`T=11` 是 PWM input，`T=13` 是 ROS linear/angular control，`T=130` / `T=131` 是反馈相关命令。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`：`T=1`、`T=11`、`T=13` 收到后都会刷新 `lastCmdRecvTime` 并清 `heartbeatStopFlag`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h` 和 `ugv_config.h`：`heartBeatCtrl` 在超过 `HEART_BEAT_DELAY=3000` 后执行 `setGoalSpeed(0, 0)`。

这些事实只支撑 mock/虚拟串口 stop path readiness，不等于真实串口、真实 HIL 或 safe-to-control。后续实现必须把 `T=1`、`T=11`、`T=13` 的 zero-stop 帧写成待验证 stop plan，并固定 `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`。

## 核心抓手和责任人

核心抓手：新增一份 O1/O3 current stop path readiness artifact，证明当前 stop-only 路径可以被机器复核。artifact 必须包含 `/api/base/stop` endpoint、vendor source refs、T=1/T=11/T=13 zero-stop frame plan、heartbeat zero-stop source、virtual serial newline JSON bytes、no `/api/base/manual` guard 和所有 safety false fields。

责任 Engineer：`rober-hardware-engineer`。这是硬件协议和 WAVE ROVER stop path readiness，不交给 Algorithm 继续包装 route plan。

## KR 拆解和历史归档口径

- 当前 KR 拆解：本轮只补 O1 的 stop/emergency-stop 前置证据；不补 route execution、delivery、HIL 或 production evidence。
- 更新口径：实现验收后最多记录为 `software_proof_o1_o3_current_stop_path_readiness_probe_only`，预计 OKR 主百分比保持不变。
- 历史归档：本阶段不修改 `OKR.md`，不归档 KR。已完成材料仍以既有 `OKR.md` 中 2026-07-12 21-57 planner-only path proof、2026-07-13 08-09 bounded route command plan 和各自 sprint final 为证据；本轮只引用，不移动历史区。

## 本轮需要做什么

后续 Hardware owner 需要实现并验证：

1. 生成 `trashbot.o1.current_stop_path_readiness.v1` JSON artifact。
2. 从 vendor 资料和项目 stop endpoint 事实构造 stop-only contract：`/api/base/stop`、`T=1` zero、`T=11` zero、`T=13` zero、heartbeat zero-stop。
3. 用 mock/虚拟串口验证只写 newline-delimited zero JSON frames，不写非零帧。
4. 明确 no `/api/base/manual`、no `/cmd_vel` route execution、no NavigateToPose、no real UART by default。
5. 固定 `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`。

## 风险、阻塞和证据链缺口

- 缺 current live HIL pass、真实 WAVE ROVER 串口 stop acknowledgement、真实 operator approval、真实 route execution 和 delivery/operator acceptance。
- `/api/base/stop` readiness 在本轮只能通过 mock/虚拟串口或纯函数验证；不得把 HTTP endpoint 存在解读成真实停车成功。
- heartbeat zero-stop 是 vendor 固件行为来源，但本轮不烧录固件、不读取真实 ESP32 状态。
- 如果 Hardware owner 发现现有 stop command order 或 protocol helper 与 vendor 资料冲突，必须 fail closed 并在 `tech-done.md` 写出冲突，不能改硬件配置或 launch 绕过。
