# Side2Side Check - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Sprint time: 2026-07-13 10:12 CST
- Product acceptance status: accepted with mock-only boundary
- Proof boundary: `software_proof_o1_live_stop_hil_capture_gate_mock_only`

## Product 验收结论

Product 接受本轮为 O1/O3 mock-only operator-gated current stop HIL capture gate。它证明 mock/local capture pipeline 能稳定写出 `trashbot.o1.current_stop_hil_capture_gate.v1` artifact，并能用内存 mock 验证 `POST /api/base/stop` 调用形状和 `T=1001` fixture 后停归零解析路径。

Product 不接受本轮为 current live HIL、真实 `/api/base/stop`、真实 UART zero-stop frame、ESP32 ACK、safe-to-control、route execution、delivery/operator acceptance 或 O5 production/external evidence。主百分比不调整，KR `不归档`。

## Side-by-Side 核对

| 验收项 | Hardware artifact 事实 | Product 判定 |
| --- | --- | --- |
| Schema | `schema=trashbot.o1.current_stop_hil_capture_gate.v1` | 接受 |
| Gate status | `capture_gate_status=ready_for_mock_stop_hil_capture_gate_not_hil` | 接受为 mock-only readiness，不是 HIL |
| Stop 调用形状 | `mock_http_stop_called=true`，`method=POST`，`path=/api/base/stop` | 接受为形状验证 |
| 网络边界 | `mock_http_stop_call.network_transport=mock_in_memory_no_socket` | 接受为无 socket mock，不是真实 API |
| T1001 fixture | `mock_t1001_feedback_fixture_used=true`，`observed_t1001_count=1` | 接受为 fixture parser path |
| 后停归零 | `t1001_feedback_zero_after_stop_fixture=true` | 接受为 fixture 后停归零，不是真实 feedback |
| Safety fields | `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`、`uses_real_uart=false` | 接受 fail-closed 边界 |
| O5/O1/O6/O7 | O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%` | 不调整、不归档 |

## 用户价值和产品北极星

北极星仍是普通用户把垃圾交给小车后，小车沿固定路线安全送达并能随时停下。本轮用户价值是把下一次现场执行前的 stop HIL capture gate 做成可复验、可 fail-closed 的入口；没有 explicit operator approval 时，只允许 mock/local readiness，不触发真实硬件。

## OKR 映射和方向判断

- O5：继续约 `85%`，本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `94%`，本轮只补 mock-only stop HIL capture gate，不证明 current live HIL、safe-to-control、真实 UART ACK、ESP32 ACK、Nav2 route execution success 或 delivery/operator acceptance。
- O3 现场验证 lane：继续但不单独计分；后续 route execution 必须等待 current live stop HIL 和同窗口 LiDAR/localization/TF/Nav2 controller result。
- O6/O7：继续约 `93%`，本轮不做 readback-only wrapper。
- 方向判断：继续 O1/O3 安全准入链路；不调整、不暂停、不替换 Objective。
- KR 拆解/归档：本轮仅完成 mock/local gate；current live stop call、UART zero-stop frame、post-stop `T=1001` L/R zero、HIL acceptance 仍未完成，KR `不归档`。

## 责任 Engineer 和下一步

- 下一轮 Hardware owner：`rober-hardware-engineer`。只有 explicit operator approval 后，才采 current live `/api/base/stop` 调用、同窗口 UART zero-stop frame capture、stop 后 `T=1001` L/R 归零和 HIL acceptance。
- 后续 Algorithm owner：`robot-algorithm-engineer`。只有 current live stop HIL 加同窗口 LiDAR/localization/TF readiness 与 Nav2/controller result 可记录后，才推进 controlled route execution evidence。

## 风险和待补证据链

- 仍缺真实 operator approval。
- 仍缺真实 `/api/base/stop`、真实 UART zero-stop frame、ESP32 ACK、current live `T=1001` feedback、HIL acceptance。
- 仍缺 safe-to-control、route execution、delivery/operator acceptance。
- O5 仍缺真实 production/external evidence。

## Product Acceptance Artifact

- `artifacts/product_acceptance_stop_hil_capture_gate.json`
