# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - Pre Start

## 启动声明

- sprint_type: epic
- Fresh sprint 目录：`sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/`
- 最新参考 sprint：`sprints/2026.05.14_08-09_mobile-current-pwa-retest-browser-proof/`
- 本轮目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 当前环境边界：本机只有 macOS + Docker/Chromium-family proof 能力，没有真实硬件、真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 上轮未完成项和阻塞

上轮 `2026.05.14_08-09_mobile-current-pwa-retest-browser-proof` 已完成 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`，把真实设备复测请求纳入当前 `mobile/web` PWA 的本地 Chromium-family browser proof，并由 Robot metadata-only fence 限定边界。

仍未完成的真实证据：

- 真实手机设备行为：真实 iPhone/Android device behavior 仍未验证。
- production app：仍无正式 App 或生产分发证据。
- 真实 PWA install prompt/user choice：仍无真实 beforeinstallprompt、安装提示或用户选择材料。
- Objective 5 外部材料：仍无公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Robot/HIL：仍无 Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实 dropoff/cancel completion 或真实 delivery。

## 同一 Blocker 重复消费检查

最近多轮 O5 进展已反复记录同一类 blocker：没有真实外部云/4G/OSS/CDN/DB/queue/worker 材料。`OKR.md` 4.1 明确 Objective 5 当前约 68%，但只有拿到至少一种真实外部材料时才应继续推进 O5 completion。继续堆 O5 本地 metadata 会重复消费 blocker，不能形成真实外部 proof。

本轮按 stop rule 切换到 Objective 4 的真实设备/production app/PWA install prompt 主路径缺口，但仍保持边界：本机/Docker/Chromium 下只能形成 `software_proof_docker_mobile_real_device_field_trial_package_gate`。

## 用户价值和产品北极星

北极星仍是让普通手机用户不接触命令行、ROS2、串口或硬件调试，也能完成一次送垃圾任务并知道失败时如何处理。

本轮用户价值不是证明真实手机已通过，而是把真实 iPhone/Android 或 production app 现场试跑前需要复制、观察、记录和回传的材料做成 phone-safe package。现场人员可以打开当前 `mobile/web`，收集 viewport/touch/display-mode/service-worker/offline/client-time 和人工 observation fields，复制一份可进入验收/复盘链路的材料，减少真实设备试跑时口径散、材料漏、误把 ACK 当 delivery success 的风险。

## 本轮核心抓手

新增“真实设备现场试跑包 / field trial package”能力：

- Full-stack 在 `mobile/web` 中新增 UI、生成逻辑、复制包、测试和文档。
- Robot 增加 metadata-only compatibility fence，证明 `mobile_real_device_field_trial_package*` 不触发机器人控制语义。
- Product 收口时只在 Task A/B 证据通过后保守调整 Objective 4，Objective 5 不动，并同步 OKR 进度日志。

## Owner 和团队拆分

- Task A Full-stack：`full-stack-software-engineer`，负责 `mobile/web` UI/logic/tests/docs。
- Task B Robot：`robot-software-engineer`，负责 remote bridge/protocol metadata-only fence 和接口文档。
- Task C Product closeout：`product-okr-owner`，负责 sprint closeout、OKR.md、`docs/process/okr_progress_log.md`。

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 依赖 Task A/B 返回的实际验证结果。

## 验收口径

本轮完成后只能声称：

- `software_proof_docker_mobile_real_device_field_trial_package_gate`
- Docker/local `mobile/web` 可以生成 phone-safe field trial package。
- Robot fence 证明该 metadata-only package 不触发 command envelope、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

本轮不得声称：

- 真实手机设备行为已通过。
- production app 已通过。
- 真实 PWA install prompt/user choice 已通过。
- O5 外部材料已通过。
- Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery 已通过。

## 需要创建或更新的 sprint 文档

本轮 Epic 必须继续完成：

- 已创建：`pre_start.md`
- 已创建：`prd.md`
- 已创建：`tech-plan.md`
- 待 Task A/B 后更新：`tech-done.md`
- 待验收后更新：`side2side_check.md`
- 待 OKR closeout 后更新：`final.md`
