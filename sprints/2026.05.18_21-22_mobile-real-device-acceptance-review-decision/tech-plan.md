# Sprint 2026.05.18_21-22 Mobile Real Device Acceptance Review Decision - Tech Plan

## 1. Plan 状态

- sprint_type: epic
- 本轮主题：`mobile_real_device_field_trial_acceptance_review_decision`
- 目标边界：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`
- 执行原则：只推进 O4 手机真实设备材料链路，不碰硬件、route/elevator、云中转或 ROS2 主链路。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接推进 Objective 5。原因：本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。
3. 下一低项 Objective 1 约 81%，但真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料不可得。
4. Objective 2 / 3 / 4 约 99%，但最近两轮已连续消费 PR #4 route/elevator 真实现场材料 blocker。本 sprint 改道到 O4 的真机材料评审功能，不消耗同一 route/elevator blocker。

## 2. Task A - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

需要做什么：

- 新增 `mobile_real_device_field_trial_acceptance_review_decision*` 数据归一化、copy payload、render panel 与事件绑定。
- 从已有 `mobile_real_device_field_trial_acceptance_session*` 推导 review decision。
- fixture 增加示例字段。
- unittest 增加最小断言，保持测试围栏，不新增大套件。
- 文档追加本 gate 的 schema、summary schema、copy schema、boundary、not-proven 语义。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "mobile_real_device_field_trial_acceptance_review_decision|software_proof_docker_mobile_real_device_field_trial_acceptance_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. Task B - Product Manager / OKR Owner

文件范围：

- `sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision/tech-done.md`
- `sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision/side2side_check.md`
- `sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

需要做什么：

- 根据 Full-stack 验证结果完成 sprint 收口。
- `OKR.md` 只允许保守记录 O4 software proof 前移，不写真实手机验收完成。
- progress log 同步证据边界。

验收命令：

```bash
rg -n "mobile_real_device_field_trial_acceptance_review_decision|Objective 4|Objective 5|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision
```

## 4. 集成验收

```bash
node --check mobile/web/app.js
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "mobile_real_device_field_trial_acceptance_review_decision|software_proof_docker_mobile_real_device_field_trial_acceptance_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision
```

## 5. 风险边界

- 本轮不证明真实手机、production app、真实 PWA prompt/user choice、O5 external proof、HIL、dropoff/cancel completion 或 delivery success。
- 若 fixture 或 copy package 出现 raw artifact、凭证、路径、ROS topic、`/cmd_vel`、serial/UART 或 success/control wording，必须 fail closed 或移除。
