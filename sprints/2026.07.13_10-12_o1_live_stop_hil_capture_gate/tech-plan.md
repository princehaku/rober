# Tech Plan - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Product plan status: ready for single-owner Hardware implementation
- Planned proof boundary: `software_proof_o1_live_stop_hil_capture_gate_mock_only`

## 已读资料和计划依据

- `AGENTS.md`：本任务按 epic sprint 留档，Product 只做计划和验收口径；工程实现、测试、修复由 owner Engineer 执行。
- `OKR.md`：O5 约 `85%`，O1 约 `94%`；O1 当前缺 current live HIL、safe-to-control、Nav2 route execution success 和 delivery/operator acceptance。
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`：O5 readiness packet 为 support-only，`support_only_reason=no_real_production_external_evidence`，不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser。
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/final.md`：已证明 no-motion stop path readiness；下一步是 explicit operator approval 下的 current live stop HIL。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节数字最低 Objective：O5，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。
2. 本 sprint 是否针对最低 Objective：否，本 sprint 针对 O1/O3 safety gate。
3. 不针对 O5 的理由：O5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser。最近 O5 production readiness packet 已明确 `okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence`、`production_ready=false`；当前 automation run 没有这些真实外部条件，继续 O5 只能重复 support-only wrapper。按同一 blocker 重复消费红线，本轮转向 O1/O3 下一条可软件推进、且直接解锁现场执行的 operator-gated live stop HIL capture gate。

## 技术方案

### 单 owner 闭环

- 主责：`rober-hardware-engineer`。
- 并行策略：不并行。文件范围集中在硬件 helper、硬件测试、硬件文档和本 sprint artifact/`tech-done.md`，由一个 Hardware owner 单线实现、验证、修复。
- Product 主节点不得直接实现 helper、测试或硬件配置；只在返回后做验收和 closeout。

### 允许的后续工程文件范围

Hardware implementation 预计改动：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`（仅在复用/补足零停止或 `T=1001` 解析纯函数确有必要时）
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py`
- `docs/hardware/wave_rover_stop_hil_capture_gate.md`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/tech-done.md`

不得改动 `OKR.md`；OKR 更新留到 Product closeout。不得修改 production cloud、O6/O7、Nav2 route execution 或真实硬件配置。

### Helper 行为

1. 提供 module entry：`python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate`。
2. 支持 `--mock`，在本地启动或调用 mock HTTP stop endpoint，不触达真实 robot API。
3. 支持 `--operator-approval-token`，mock 模式必须显式传入 `MOCK_APPROVED_STOP_ONLY`；缺失或错误 token 必须 fail-closed。
4. 支持 `--output` 写出 artifact。
5. 使用 fixture 验证 stop 后 `T=1001` feedback 归零解析路径，但必须标为 mock/fixture，不得写成 current live feedback。
6. 真实硬件模式必须默认关闭；当前 automation run 不允许打开 UART、不允许访问真实 `/api/base/stop`。
7. 任意 unsafe 参数、非零命令、真实 UART 开启尝试、手动控制 endpoint、`/cmd_vel` 或 NavigateToPose 迹象必须 fail-closed，并保持所有 success/safety 字段 false。

### Artifact 合同

Artifact schema：`trashbot.o1.current_stop_hil_capture_gate.v1`。

必须包含并固定：

- `hil_pass=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`

建议包含：

- `capture_gate_status=ready_for_mock_stop_hil_capture_gate_not_hil`
- `operator_approval_mode=mock_token_only`
- `stop_endpoint=/api/base/stop`
- `manual_endpoint_called=false`
- `cmd_vel_published=false`
- `navigate_to_pose_sent=false`
- `mock_http_stop_called=true`
- `mock_t1001_feedback_fixture_used=true`
- `t1001_feedback_zero_after_stop_fixture=true`
- `evidence_boundary=software_proof_o1_live_stop_hil_capture_gate_mock_only`
- `next_live_required_evidence=["explicit_operator_approval","current_live_stop_call","same_window_uart_zero_stop_frame_capture","post_stop_t1001_lr_zero","hil_acceptance"]`

## 接口影响

- `/api/base/stop`：只在 mock HTTP endpoint 中验证调用形状；当前 run 不触发真实 endpoint。
- `/api/base/manual`：禁止调用，artifact 必须记录未调用。
- `/cmd_vel`：禁止发布。
- NavigateToPose / Nav2 controller / BT：禁止触发。
- WAVE ROVER UART：禁止打开，`uses_real_uart=false`。

## Vendor 和文档同步要求

- Hardware owner 在实现前必须读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER 本地资料。
- Mock 阶段可使用 fixture，但 `docs/hardware/wave_rover_stop_hil_capture_gate.md` 必须写清 mock/local 与真实 HIL 的边界。
- 真实硬件集成时，必须在 `tech-done.md` 或实现注释中明确采用的 vendor 来源；本轮 Product plan 不替代 vendor source readback。

## 工程质量要求

- 代码技术注释必须使用中文，注释比例超过 20%。
- 注释重点解释 fail-closed、安全字段保持 false、mock 不等于 HIL、为什么当前 automation 禁止真实 UART/control。
- 测试必须覆盖 happy path 和危险输入 fail-closed。

## 验收命令

后续 Hardware agent 必须运行并记录结果：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
```

```bash
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py
```

```bash
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate --mock --operator-approval-token MOCK_APPROVED_STOP_ONLY --output sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
```

```bash
python3 -m json.tool sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
```

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py docs/hardware/wave_rover_stop_hil_capture_gate.md sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate
```

## Product 验收锚点

Product closeout 只在以下条件全部满足时接受：

- Artifact schema 为 `trashbot.o1.current_stop_hil_capture_gate.v1`。
- `capture_gate_status` 明确是 mock/local readiness，不是 HIL pass。
- 七个固定 false 字段全部存在且为 false。
- Artifact 明确 `uses_real_uart=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`。
- 验证命令全部通过；若裸 module import 因当前 macOS 未安装 package 失败，必须像 09:11 sprint 一样定位为 import-path 偏差，并用 `PYTHONPATH` 复跑同一 module entry 通过后才能接受。
- `tech-done.md` 写明实际改动、验证结果、失败定位和剩余风险。
- 没有生成 `final.md` 或 `side2side_check.md` 直到 Product acceptance 阶段。

## 失败处理

- 如果 py_compile 或 unittest 失败，Hardware owner 必须先定位并修复，再重跑。
- 如果 artifact 缺固定 false 字段、字段为 true、或混淆 mock 与 HIL，Product 必须退回返工。
- 如果 helper 尝试真实 UART、真实 `/api/base/stop`、`/api/base/manual`、`/cmd_vel`、NavigateToPose 或非零命令，本 sprint 直接 fail-closed，不能接受。

## 风险、阻塞和待补证据链

- 当前缺 explicit operator approval，不能执行 current live stop HIL。
- 当前不证明真实 UART frame capture、真实 ESP32 ACK、真实 `T=1001` feedback 或 HIL acceptance。
- O1 主百分比预计不调整，除非后续 Product closeout 有新的真实/准现场 HIL 证据。
- route execution 仍 blocked，必须等 stop HIL、同窗口 LiDAR/localization/TF readiness、Nav2/controller result 和 operator acceptance。
- O5 仍 blocked 于真实 external production evidence；本轮不消耗 O5 support-only blocker。

## 后续 sprint 文档流

- 本阶段已创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- Hardware implementation 完成后更新 `tech-done.md`。
- Product acceptance 后再创建 `side2side_check.md` 和 `final.md`。
- `OKR.md` 不在本轮 Product plan 阶段修改，留到 Product closeout。
