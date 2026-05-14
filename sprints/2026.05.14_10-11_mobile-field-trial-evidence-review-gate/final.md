# Sprint 2026.05.14_10-11 Mobile Field Trial Evidence Review Gate - Final

## 收口结论

本轮完成 `software_proof_docker_mobile_real_device_field_trial_review_gate`。Task A 把手机端真实设备现场试跑包推进为“现场试跑证据复核”package，Task B 证明该 package 在 Robot remote bridge 中保持 metadata-only，不进入 command、ACK、status、cursor 或 terminal result。

Objective 4 可从约 86% 保守上调到约 87%。Objective 5 保持约 68%；Objective 1/2/3 不调整。

## 用户价值和产品北极星

用户价值：现场试跑材料现在可以被复核，而不是只被收集。Product/Support 能看到 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction 的状态，知道哪些仍是 `not_proven`。

产品北极星：手机端继续靠近普通用户可执行的真实设备验收链路，但不把 ACK、HTTP accepted、copy package、review package 或 metadata-only response 包装成 delivery success。

## OKR 映射

- Objective 4：本轮新增现场材料复核能力，支持手机端真实设备验收准备链路，约 86% -> 约 87%。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration，保持约 68%。
- Objective 1/2/3：本轮未改硬件、Nav2/fixed-route、task orchestrator 或 HIL 证据，不调整。

## KR 拆解和本轮核心抓手

- KR4：远程诊断/支持材料更可复核，review package 可列出缺失和脱敏状态。
- KR5/KR7：手机端验收材料链路继续 phone-first，文案保守，主操作保持 fail closed。
- 核心抓手：`mobile_real_device_field_trial_review`、`mobile_real_device_field_trial_review_summary`、`mobile_real_device_field_trial_review_copy`，证据边界为 `software_proof_docker_mobile_real_device_field_trial_review_gate`。

## 责任 Engineer

- User Touchpoint Full-Stack Engineer：手机端 review panel、copy package、mobile tests、`docs/product/mobile_user_flow.md`、`mobile/README.md`。
- Robot Platform Engineer：remote bridge protocol/worker metadata-only fence、mixed valid-command coverage、`docs/interfaces/ros_contracts.md`。
- Product Manager / OKR Owner：本 closeout、OKR 进度、产品验收口径和风险边界同步。

## 验证摘要

- Task A：`mobile.test_mobile_web_entrypoint` `Ran 30 tests ... OK`；`py_compile` pass；`node --check mobile/web/app.js` pass；required rg pass；scoped diff check pass。
- Task B：remote bridge/protocol targeted unittest `Ran 161 tests in 82.342s OK`，有一个既有 ResourceWarning；`py_compile` pass；required rg pass；scoped diff check pass。
- Task C：Product closeout 后执行指定 `rg` 与 scoped `git diff --check`。

## 风险、阻塞和证据链

本轮证据仍是 `software_proof_docker_mobile_real_device_field_trial_review_gate`。它不是真实手机设备、production app、真实 PWA install prompt/user choice、Objective 5 外部 proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

下一步如果没有 Objective 5 外部材料，应继续围绕 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 做现场证据补齐；如果拿到外部云/4G/OSS/CDN/DB/queue 材料，再回到 Objective 5。
