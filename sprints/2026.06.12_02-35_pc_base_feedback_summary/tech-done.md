# PC Base Feedback Summary

## sprint_type

micro

## 目标

让 PC Robot Control summary 明确展示真实底盘 `T=1001` 反馈链路状态，同时保持“反馈链路活着”与“轮速非零/真实运动/HIL pass”之间的边界。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.base` 新增 `latest_t1001_observed_count` 和 `feedback_link_status`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `baseSummaryFromReadbacks`。
  - 从 `/api/base/status` 的 `latest_t1001_observed_count` 或 `/api/base/feedback-samples/latest` 的 `latest_t1001_observed_count/t1001_observed_count` 推导 base feedback 摘要。
  - `feedback_link_status=t1001_observed_not_motion_proof` 明确标识这不是运动证明。
  - map/localize/Nav2/operator/radar/base 只读 endpoint 统一使用 4s 读取窗口，减少真实板端状态页间歇性 timeout。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断 `Camera / LiDAR / Base` 行增加 `t1001` 与 `link`。
  - 普通 `.simple-user-console` 首屏未改变。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 `T=1001` count 和 feedback link status 回归断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC base feedback summary 合同和真实复测结果。

## 真实上位机验证

上位机：`root@192.168.1.11:37878`

Artifacts：

- `sprints/2026.06.12_02-35_pc_base_feedback_summary/artifacts/01_pc_summary_base_feedback.json`
  - 证明新 base 字段已出现，但仍有其它 1.5s readback timeout。
- `sprints/2026.06.12_02-35_pc_base_feedback_summary/artifacts/02_pc_summary_slow_readbacks.json`
  - 4s 只读窗口后真实 PC summary：
    - `console_status=loaded_fail_closed_summary`
    - `robot_api_connection.status=readable`
    - `loaded_count=13`
    - `blocked_count=0`
    - `failed_count=0`
    - `dangerous_true_fields=[]`
    - `readback_summary.base.status=loaded`
    - `readback_summary.base.latest_feedback_status=loaded`
    - `readback_summary.base.feedback_ack_status=t1001_observed`
    - `readback_summary.base.latest_t1001_observed_count=3`
    - `readback_summary.base.feedback_link_status=t1001_observed_not_motion_proof`

收尾：

- 临时 PC API 18815 已关闭。
- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video0`、`/dev/video1`、`/dev/video2` 无 holder 输出。

## 本地验证

- `npm run test -- catalog.test.ts`：77 passed。
- `npm run test`：94 passed。
- `npm run build`：通过。
- `npm run lint`：通过。
- `git diff --check`：通过。

## 剩余风险

- 这只证明 PC summary 能稳定展示 `T=1001` 反馈链路，不证明左右轮非零、真实运动、方向正确、HIL pass 或点动放行。
- 相机 `/dev/video1` 仍 first-frame timeout，实时可见图传仍 blocked。
- 非 stop motion gate 仍缺外部视频、可见相机、轮速非零反馈和 LiDAR motion delta。
