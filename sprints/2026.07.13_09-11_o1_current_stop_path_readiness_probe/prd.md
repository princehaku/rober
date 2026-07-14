# PRD - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `rober-hardware-engineer`
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`

## 产品目标

把下一轮受控 route execution 前的 current stop path / emergency stop readiness 收敛成可机器校验的 no-motion artifact。该 artifact 只证明 stop-only 路径准备充分、边界明确、mock/虚拟串口验证通过；不触发机器人运动。

## 用户价值和北极星

普通用户真正需要的是小车可安全停下，而不是只有路线计划。本轮的价值是让后续任何非零 route execution sprint 都先具备可复核停车路径：`/api/base/stop` 应该落到 WAVE ROVER zero-stop command plan，而非 `/api/base/manual` 或非零控制路径。

## OKR 映射和方向判断

- O5：约 `85%`，当前最低，但下一步只有真实 external production evidence 可计增量；本轮不继续 O5 support-only packaging。
- O1：约 `94%`，仍缺 current live HIL / current stop path / safe-to-control / Nav2 route execution / delivery acceptance。本轮针对 O1/O3 route execution 前置安全证据。
- 方向判断：继续 O1/O3 current stop path readiness；不调整、不暂停、不替换 Objective。
- KR 归档：本轮 PRD 阶段不归档 KR；即使后续实现通过，也必须等 Product closeout 再决定是否写入 `OKR.md`，预计主百分比保持不变。

## 输入事实

必须引用的本地 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`

必须保持的上轮事实：

- 上轮 accepted sprint：`sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md`
- 上轮拒绝能力：route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL、safe-to-control、O5 production/external evidence。
- 本轮不能重复 helper/export/readiness/route-intent、packet packaging、gate packaging、bounded-plan packaging 或 O6/O7 readback-only wrapper。

## 功能需求

1. 新增 Hardware artifact：`sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json`。
2. artifact schema 建议：`trashbot.o1.current_stop_path_readiness.v1`。
3. artifact 必须包含 `current_stop_path_readiness_status=ready_for_mock_stop_only_probe_not_hil` 或更保守状态。
4. artifact 必须包含 `stop_endpoint=/api/base/stop`，并明确 no `/api/base/manual`。
5. artifact 必须包含 vendor source refs，覆盖 UART JSON framing、`T=1`、`T=11`、`T=13`、feedback/heartbeat 和 zero-stop 来源。
6. artifact 必须列出 zero-stop command plan：`{"T":1,"L":0,"R":0}`、`{"T":11,"L":0,"R":0}`、`{"T":13,"X":0,"Z":0}`。这些是 stop-only frames，不是 route execution frames。
7. mock/虚拟串口验证必须证明每条 frame 是 UTF-8 JSON + `\n`，且没有任何非零 `L/R/X/Z`。
8. artifact 必须记录 heartbeat 来源：vendor firmware 的 `heartBeatCtrl` 在 `HEART_BEAT_DELAY=3000` 后 `setGoalSpeed(0, 0)`，但本轮不宣称真实固件已触发。
9. 所有安全和 mission booleans 必须固定：`safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`。
10. `docs/hardware/wave_rover_stop_path_readiness.md` 必须同步说明本轮来源、边界、mock 验证和后续真实 HIL 缺口。
11. `tech-done.md` 必须记录实际改动、验证命令输出、失败定位和剩余风险。

## 非目标

- 不发 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不调用 NavigateToPose、Nav2 controller/BT 或 route execution。
- 不打开真实 WAVE ROVER UART，除非后续 CEO 明确给出硬件/安全授权；本轮默认 mock/虚拟串口。
- 不宣称 HIL、safe-to-control、route execution、delivery success、operator acceptance 或 O5 production evidence。
- 不修改 `OKR.md`、production cloud、O6/O7 UI/API、launch 参数或硬件配置。

## 验收口径

Product 只接受本轮为 O1/O3 no-motion current stop path readiness probe。通过条件：

- 有可解析 JSON artifact。
- artifact 明确 `/api/base/stop` 和 no `/api/base/manual`。
- vendor source refs 覆盖 UART JSON、`T=1`、`T=11`、`T=13`、heartbeat 和 zero-stop。
- mock/虚拟串口证明只输出 zero-stop frames，没有非零运动命令。
- `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false` 固定。
- 文档和 `tech-done.md` 同步完成。

不通过条件：

- 只写 prose checklist，没有机器可读 `stop_path_readiness.json`。
- 把 stop readiness 写成真实 HIL、safe-to-control 或 route execution success。
- 触发 `/api/base/manual`、非零 `T=1` / `T=11` / `T=13`、`/cmd_vel` 或 NavigateToPose。
- 未引用 vendor UART/JSON/heartbeat/zero-stop 来源。

## 已完成 KR 历史记录位置和剩余风险

本轮没有已完成 KR 可归档。既有证据位置：

- O1 current same-run planner-only path proof：`sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/final.md`
- O3/O1 bounded route command plan：`sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md`
- 当前 OKR 记录：`OKR.md` Objective 1 Key Results

剩余风险：这些证据仍不等于 current live HIL pass、真实 route execution、delivery/operator acceptance、safe-to-control 或真实 WAVE ROVER stop acknowledgement。

## 需要创建或更新的 sprint 文档

- 已创建/更新：`pre_start.md`、`prd.md`、`tech-plan.md`
- 后续实现必须更新：`tech-done.md`
- Product closeout 后如进入验收阶段再更新：`side2side_check.md`、`final.md`
