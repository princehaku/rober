# PC T130 Summary Exemption

## sprint_type

micro

## 目标

修复 PC Robot Control summary 把 WAVE ROVER `T=130` 只读反馈请求误判成危险控制动作的问题，让真实上位机 summary 从 blocked 回到 readable，同时不放松任何运动安全门。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/hardware/wave_rover_json_bridge.md`
- 上轮真实 evidence：`sprints/2026.06.12_02-00_pc_base_feedback_samples_proxy/artifacts/01_upper_base_feedback_samples.json`

采用事实：`T=130` 是 vendor 底盘反馈请求，反馈帧为 `T=1001`；该路径可以出现 `sends_commands=true`，但不等于 `sends_motion_commands=true` 或 `/api/base/manual`。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 endpoint/path 级危险字段豁免：
    - `/api/status`: `base.sends_commands`、`base.feedback_readback.sends_commands`
    - `/api/base/status`: `sends_commands`、`feedback_readback.sends_commands`
    - `/api/base/feedback-samples/latest`: `sends_commands`、`latest_result.sends_commands`
  - 保持 `sends_motion_commands`、`sends_base_motion_commands`、`calls_base_manual`、`publishes_cmd_vel`、`robot_control_executed` 等 hard dangerous 字段不豁免。
  - 将 `/api/base/status` 和 `/api/base/feedback-samples/latest` 读取窗口从 1.5s 调整为 4s，避免真实 `T=130` readback 被短超时误判离线。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增只读 `T=130 sends_commands` 不应进入 dangerous 的回归测试。
  - 更新慢 endpoint 测试，不再把 base feedback `sends_commands=true` 计入 blocked。
- `docs/product/pc_tools_workstation.md`
  - 记录本轮 PC summary 判定边界和真实复测结果。

## 真实上位机验证

上位机：`root@192.168.1.11:37878`

Artifact：

- `sprints/2026.06.12_02-20_pc_t130_summary_exemption/artifacts/01_pc_summary_after_t130_exemption.json`
  - 旧 1.5s base 读取预算下，dangerous 已为空，但 base status/latest 仍 timeout。
- `sprints/2026.06.12_02-20_pc_t130_summary_exemption/artifacts/03_pc_summary_after_restart.json`
  - 重启 PC API 并使用 4s base 读取预算后：
    - `console_status=loaded_fail_closed_summary`
    - `robot_api_connection.status=readable`
    - `loaded_count=13`
    - `blocked_count=0`
    - `failed_count=0`
    - `dangerous_true_fields=[]`
    - `blocked_reasons=[]`
    - `readback_summary.base.status=loaded`
    - `readback_summary.base.latest_feedback_status=loaded`

收尾：

- 临时 PC API 18814 已关闭。
- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video0`、`/dev/video1`、`/dev/video2` 无 holder 输出。

## 本地验证

- `npm run test -- catalog.test.ts`：77 passed。
- `npm run build`：通过。

## 剩余风险

- 本轮只修复 PC summary 对只读反馈的误判，不证明轮速非零、真实运动、HIL pass、NavigateToPose 或手动点动放行。
- 相机 `/dev/video1` 仍未恢复首帧，实时可见图传仍 blocked。
- 非 stop motion gate 仍缺外部视频、可见相机、轮速非零反馈和 LiDAR motion delta。
