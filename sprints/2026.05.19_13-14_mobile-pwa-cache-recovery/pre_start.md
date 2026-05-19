# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - Pre Start

## sprint_type: epic

Run time: 2026-05-19 13:05 Asia/Shanghai。

## 1. 用户价值和产品北极星

产品北极星仍是让普通手机用户可以用手机完成低成本 ROS2 垃圾投递任务，并在失败时看懂机器人状态、证据边界和下一步动作。本轮不追求新增真实手机、真实 4G 或真实机器人运动证据，而是修复本地 Browser QA 的 PWA/service-worker 缓存恢复缺口：in-app browser 不能再被旧 offline shell 卡住，截图验证不能因为旧缓存长期停留而失真。

用户价值是让后续 O4 手机触点验证可以稳定看到当前 `mobile/web` 入口，而不是看到历史 offline shell。只有先恢复本地 Browser QA 的可重复性，后续真实 iPhone/Android device behavior、真实 PWA prompt/user choice 和 production app 验收才有可靠的预检基础。

## 2. 证据输入

- `OKR.md` 4.1 显示 Objective 5 当前约 68%，是最低完成度；但下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实 external proof。本机只有 Docker，本轮不能继续本地 O5 wrapper，也不提高 Objective 5。
- `OKR.md` 4.1 显示 Objective 1 当前约 81%；但仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。10-11 sprint 已做硬件真实材料升级请求，本轮不能再包装同一 blocker。
- 最新 `sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md` 第 3/5 节明确记录：Browser QA 尝试不计入通过证据，因为本地 PWA/service-worker 缓存导致 in-app browser 停在旧 offline shell，截图命令超时。
- PR #4 / PR #5 已把 elevator assisted delivery、hardware baseline、真实手机/browser 验收推到主链，但真实 route/elevator field materials、真实硬件材料和真实手机/browser 现场证据未到。本轮只选择可执行 Objective 4 touchpoint bugfix，不宣称真实手机通过。

## 3. 本轮核心抓手

本轮目标是 `mobile_pwa_cache_recovery_gate`。

核心抓手：

- Full-Stack owner 修复 `mobile/web` Service Worker/cache/version/offline shell recovery 相关代码和产品文档，使本地 Browser QA 能摆脱旧 offline shell。
- Robot owner 只读咨询，确认 Start Delivery、Confirm Dropoff、Cancel gating 不扩大，不触发 robot commands，不新增 ACK/cursor/diagnostics fetch 行为。
- Product owner 负责规划、后续收口 docs/OKR，并确保所有证据保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 4. OKR 映射

| Objective | 本轮关系 | 边界 |
| --- | --- | --- |
| Objective 5 | 不针对完成度提升。 | 不做 O5 local wrapper，不证明 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。 |
| Objective 1 | 不针对完成度提升。 | 不碰 WAVE ROVER/UART/HIL，不补 PR #5 2D LiDAR / ToF 真实材料，不新增硬件假设。 |
| Objective 4 | 本轮主要映射。 | 修复本地 PWA Browser QA 可重复性，为真实手机/browser 验收做前置护栏；不证明真实 iPhone/Android、production app 或真实 PWA prompt/user choice。 |

## 5. KR 拆解

- KR-A：`mobile/web` 的 service-worker version/cache 策略必须能让新版本接管旧 PWA shell，避免 Browser QA 长期停留在旧 offline shell。
- KR-B：offline shell recovery 必须明确 fail-closed：离线或旧缓存状态只提示恢复/刷新，不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- KR-C：本地 Browser QA 必须能通过清缓存/版本更新/恢复路径看到当前页面并完成截图；若仍失败，失败定位要区分 service-worker 缓存、旧 offline shell、截图命令超时和本地 browser 工具问题。
- KR-D：相关 `docs/product/` 文档和 sprint 收口必须同步写明 `mobile_pwa_cache_recovery` 只是 `software_proof`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 6. 责任 Engineer

- `full-stack-software-engineer`：主责实现和验证。文件范围预计覆盖 `mobile/web/service-worker.js`、`mobile/web/offline.html`、`mobile/web/app.js`、`mobile/web/manifest.webmanifest`、`mobile/web/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`，最终以 `tech-plan.md` 为准。
- `robot-software-engineer`：只读咨询。确认本轮不会扩大 Start Delivery、Confirm Dropoff、Cancel gating，不触发 robot commands，不引入 ROS2 或 Robot diagnostics 写路径。
- `product-okr-owner`：本轮规划和后续收口。当前阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；实现完成后再更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和相关 docs。

## 7. 风险、阻塞和证据链

- 风险：service-worker 注册、缓存版本、offline fallback 和 in-app browser 截图超时可能互相影响；Full-Stack 需要用本地 Browser QA 或等价 Playwright/静态 smoke 把问题定位清楚。
- 阻塞：真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、O5 external proof、WAVE ROVER/UART/HIL、PR #4 field materials 和 PR #5 hardware materials 均不在本轮解决范围。
- 证据链：本轮最多产出 `software_proof` / `not_proven` 的本地 Browser QA 恢复证据，不产出真实手机通过、真实 delivery success、真实 route/elevator field pass、真实 HIL 或真实 cloud proof。

## 8. 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/pre_start.md`
- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/prd.md`
- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/tech-plan.md`

本阶段禁止创建 `tech-done.md`、`side2side_check.md`、`final.md`，禁止修改产品代码、测试代码、`OKR.md` 或 `docs/process/okr_progress_log.md`。
