# O1 Same-Session PC Command Material Pre Start

## sprint_type

sprint_type: epic

## 本轮目标

本轮目标是把 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/02_pc_first_jog_samesession_timeoutfix.json` 和 `03_base_status_after_pc_jog.json` 安全接入 O1 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，形成 `same_session_pc_command_material` additive section。

本轮不宣称 current live rerun、HIL pass、safe-to-control、delivery success 或 Nav2 route execution success。核心价值是把同会话 PC proxy command、remote motion key values、after-jog base status readback 与上一轮已接入的 upper manual same-session wheel material放到同一个 fail-closed HIL acceptance gap view 中。

## 上轮未完成项与阻塞

- O5 仍是 `OKR.md` 当前最低进度项，约 85%，但缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence。继续做 O5 readiness/readback 会落入 `okr_credit_allowed=false` support-only lane。
- O1 约 92%，仍缺 current live same-run HIL acceptance、external video、current live Nav2 route execution success、wheel direction、IMU/battery 标定和真实 delivery success。
- 最近 O1 sprint `2026.07.11_01-33_o1_same_session_hil_acceptance_bundle` 只接入了同 session 的 upper manual artifact `01_upper_manual_samesession_012.json`，未接入同 session 的 PC command proxy 与 after-jog base status readback。

## Owner

- 主责：`robot-hardware-engineer`
- Product closeout：主节点汇总，必要时由 `product-okr-owner` 复核 OKR 口径。

## 验收口径

- 新增 additive fields 使用 `same_session_pc_command_*` 前缀，不输出裸名 `wheel_feedback_lr_nonzero_proven=true`。
- 只消费 allowlisted 字段：schema、proxy/status、direction、speed、duration、HIL checklist、`remote_motion_key_values` 的 wheel nonzero 摘要，以及 after-jog base status 的 T1001/feedback readback 摘要。
- 原始 URL、endpoint、`/root/`、`/dev/tty*`、baudrate、raw frame、token、traceback 不得进入最终 bundle。
- 顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false` 保持不变。

## 风险边界

- 这是 historical same-session upper-computer / PC proxy material，不是当前 live rerun。
- PC proxy material 中的 `remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true` 只能作为 prefix 化 material fact，不得升级为顶层 HIL 或 safe-control 结论。
- after-jog base status readback 的 latest wheel L/R 仍为 0，必须保留为 fail-closed context。
