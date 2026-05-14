# Sprint 2026.05.14_15-16 Mobile Current PWA Field Trial Browser Proof - Pre Start

sprint_type: epic

## 启动结论

本轮启动 fresh Epic sprint：`sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/`。

核心抓手不是继续新增 O4 metadata panel，也不是继续堆 O5 本地 metadata，而是刷新当前 `mobile/web` PWA 的本地 Chromium-family browser proof。最近一次 current PWA browser proof 是 `2026.05.14_08-09_mobile-current-pwa-retest-browser-proof`，只覆盖到真实设备复测请求；之后 09-10 到 14-15 已连续新增 field-trial package、review、runbook execution、evidence record、evidence verdict、retest execution 多个首屏 panel。当前浏览器证据已经落后于首屏真实组合。

## 背景证据

- `OKR.md` 4.1 更新时间为 2026-05-14 14:15，Objective 5 约 68%，仍是最低完成度。
- 最新 sprint `2026.05.14_14-15_mobile-field-trial-retest-execution-gate/final.md` 已完成 `software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`，Objective 4 约 91%，Objective 5 约 68%，Objective 1/2/3 不变。
- Objective 5 当前真实进展依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；当前开发主机只有 Docker，无真实外部材料。
- 08-09 current PWA browser proof 的边界是 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`，只覆盖到真实设备复测请求，不覆盖 09-10 之后完整 field-trial 首屏组合。
- `docs/product/mobile_user_flow.md` 已连续记录 field-trial package/review/runbook/evidence record/verdict/retest execution 的 phone-safe 边界：`safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy、Start/Confirm/Cancel fail closed。

## 用户价值和产品北极星

产品北极星仍是：普通手机用户不接触 ROS2、SSH、串口或命令行，也能围绕手机首屏理解能不能发车、缺什么证据、失败后谁接手。

本轮用户价值是把当前 `mobile/web` PWA 的首屏真实状态重新落到浏览器可见证据：支持/验收人员可以用 390x844 与 768x900 的截图和 JSON summary 复查完整 field-trial 首屏组合，而不是只相信单测或文档描述。它为后续真实 iPhone/Android、production app、真实 PWA install prompt/user choice 做对照基线，但不宣称真实设备验收完成。

## OKR 映射

- Objective 4：主目标。刷新当前 PWA 浏览器 proof，覆盖手机首屏主路径和 field-trial 组合，补齐 14-15 后的可见证据缺口。
- Objective 5：明确不作为本轮实现目标。O5 仍最低，但缺真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 证据；继续本地 O5 metadata 不能提升 completion。
- Objective 1/2/3：不作为本轮目标。Robot 侧只做 metadata-only fence，防止浏览器 proof metadata 被误读为机器人控制、HIL、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 本轮 Owner

- Task A `full-stack-software-engineer`：更新 current PWA browser proof gate，生成本 sprint evidence，更新产品触点文档。
- Task B `robot-software-engineer`：更新 robot metadata-only fence，覆盖新的 browser proof metadata family，并同步 ROS contract 文档。

## 风险和阻塞

- 本轮仍没有真实手机、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice；浏览器 proof 只能声明 local Chromium-family proof。
- 本轮仍没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration；不能提高 Objective 5。
- 本轮仍没有 WAVE ROVER、真实串口、Nav2/fixed-route、HIL 或真实 delivery evidence；Robot fence 只能证明 metadata 不触发控制。
- 若 browser gate 直接调用 `mobile/web/app.js` 内部控制路径，可能重现 08-09 首次失败；Task A 必须优先验证 DOM/可见状态，不通过控制提交路径制造 proof。

## 本轮需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后必须补：`tech-done.md`。
- Epic 验收收口后必须补：`side2side_check.md`、`final.md`。
