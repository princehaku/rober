# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - Side2Side Check

sprint_type: epic

## PRD 对照

| PRD / Tech Plan 要求 | 收口结果 | 判定 |
| --- | --- | --- |
| `mobile/web` 监听 `beforeinstallprompt`、`userChoice`、`appinstalled` | Task A 已新增运行时事件监听；`beforeinstallprompt.userChoice` 被纳入捕获链路 | 通过 |
| 生成 `mobile_pwa_install_prompt_event_capture*` phone-safe package | Task A 已新增 schema、summary/copy package、fixture 和 evidence JSON | 通过 |
| 缺事件时 blocked-by-design / `not_proven`，不能静默成功 | Task A 已保留缺事件 not_proven 口径 | 通过 |
| `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、whitelist-only copy | Task A 文档、fixture、测试和 evidence 包均保持该口径 | 通过 |
| Start/Confirm/Cancel fail closed | Task A 明确事件出现也不启用 Start/Confirm/Cancel | 通过 |
| Robot metadata-only fence 不触发控制或成功语义 | Task B 覆盖 metadata-only 和 mixed valid-command 场景 | 通过 |
| 文档同步更新 | Task A 更新 mobile/product 文档，Task B 更新 ROS contract，Task C 更新 sprint/OKR/process log | 通过 |

## OKR 对照

- Objective 4：本轮直接推进 PWA install prompt/user choice 事件捕获准备能力。证据从“展示/记录 install prompt 材料”推进到“手机端可监听浏览器事件并生成事件证据包”，且 Robot fence 已证明该 metadata 不会触发控制或成功语义。因此 Objective 4 可从约 93% 谨慎上调到约 94%。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部 O5 材料，保持约 68%。
- Objective 1/2/3：本轮未新增硬件、Nav2/fixed-route、任务闭环或 HIL 证据，不上调。

## 证据边界

本轮统一证据边界是 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`。

已证明：

- `mobile_pwa_install_prompt_event_capture*` 已进入手机端事件监听、证据包、测试、文档和 Task A evidence。
- `mobile_pwa_install_prompt_event_capture*` 已进入 Robot metadata-only fence。
- 事件捕获 metadata 不启用 Start/Confirm/Cancel，不改变合法 `trashbot.remote.v1` command envelope。

未证明：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA prompt/user choice 现场验收。
- O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

## 验收结论

本轮满足 PRD 和 Tech Plan 的软件侧 closeout 条件。所有产品口径必须继续包含 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy 和 Start/Confirm/Cancel fail closed。
