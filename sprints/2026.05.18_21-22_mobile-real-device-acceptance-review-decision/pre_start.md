# Sprint 2026.05.18_21-22 Mobile Real Device Acceptance Review Decision - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-18 20:41 Asia/Shanghai
- 本轮目标：在 O5 / O1 / PR #4 真实材料不可得、且同一 route/elevator blocker 已连续消费后，推进 Objective 4 的真实手机材料链路功能。
- 证据边界：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 上轮结论

20-21 sprint 已裁决：

- Objective 5 数字最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1 次低，但缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料。
- PR #4 route/elevator 真实现场材料缺口已被 18-19 / 19-20 连续消费，本轮不能继续本地 wrapper。
- Objective 4 的可执行改道是手机真实设备材料链路，但必须继续 fail-closed。

## 3. 本轮 Owner

- User Touchpoint Full-Stack Engineer：主责实现 `mobile_real_device_field_trial_acceptance_review_decision*`。
- Product Manager / OKR Owner：收口 sprint 文档、OKR 与 progress log；不得上调真实验收完成度。

## 4. 文件范围

Full-stack 可改：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product 可改：

- `sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision/`
- `OKR.md`
- `docs/process/okr_progress_log.md`

禁止修改硬件、route/elevator、云中转和 ROS2 行为链路代码。

## 5. 验收口径

- 新 panel / summary 消费已有 `mobile_real_device_field_trial_acceptance_session*`。
- 输出 review decision、blocked items、next required evidence、owner handoff、safe copy。
- 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，不放开 Start Delivery / Confirm Dropoff / Cancel。
- 不声称真实手机验收、production app、真实 PWA prompt/user choice、O5 external proof、HIL、dropoff/cancel completion 或 delivery success。
