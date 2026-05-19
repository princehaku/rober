# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - PRD

## sprint_type: epic

Run time: 2026-05-19 13:05 Asia/Shanghai。

## 1. 用户价值和产品北极星

普通用户最终只应该打开手机入口并看到当前任务状态、阻塞原因和安全动作，而不是被旧 PWA offline shell 卡住。本轮 PRD 将 `mobile_pwa_cache_recovery_gate` 定义为 Objective 4 的触点可靠性修复：恢复本地 Browser QA 对当前 `mobile/web` shell 的可见性，降低后续真实手机/browser 验收前的工具性噪声。

产品北极星不变：手机端是普通用户入口，控制动作必须 fail-closed，所有证据必须可解释。本轮不做真实手机通过声明，不做 Objective 5 external proof，不做 Objective 1 HIL，不改变 robot command gating。

## 2. 问题陈述

最新 `sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md` 记录 Browser QA 失败：本地 PWA/service-worker 缓存让 in-app browser 停在旧 offline shell，截图命令超时，未计入通过证据。

这会造成两个产品问题：

- QA 看到的不是当前手机入口，导致 Objective 4 的触点证据不可重复。
- 旧 offline shell 可能遮蔽真实 UI 变更，使 Start Delivery、Confirm Dropoff、Cancel 的 fail-closed 状态无法被本地 browser 复核。

## 3. OKR 映射

| Objective | 当前状态 | 本轮处理 |
| --- | --- | --- |
| Objective 5 | 约 68%，最低，但需要真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。 | 不推进 O5 completion；本机只有 Docker，不能继续本地 O5 wrapper。 |
| Objective 1 | 约 81%，但需要真实 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 真实材料。 | 不推进 O1 completion；10-11 sprint 已做硬件真实材料升级请求，本轮不包装同一 blocker。 |
| Objective 4 | 约 99%，仍缺真实手机/browser、production app、真实 PWA prompt/user choice。 | 推进本地 Browser QA 可重复性，作为真实手机/browser 验收前的软件护栏；不宣称真实手机通过。 |

## 4. KR 拆解或更新

- Objective 4 KR7 补充本轮软件护栏：本地 `mobile/web` PWA 必须有可恢复的 service-worker/cache/offline shell 策略，Browser QA 能看到当前页面，而不是旧 offline shell。
- Objective 4 KR5 补充验收可解释性：当 PWA 处于离线、旧缓存或恢复状态时，页面必须继续解释失败原因并保持 primary actions disabled。
- Objective 5 KR 不更新：本轮没有 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。
- Objective 1 KR 不更新：本轮没有 WAVE ROVER/UART/HIL、真实串口日志、PR #5 2D LiDAR / ToF 真实材料。

## 5. 本轮核心抓手

`mobile_pwa_cache_recovery` 的产品定义：

1. 新版本 PWA 能主动摆脱旧 service-worker cache 和旧 offline shell。
2. Offline shell 只作为恢复提示，不作为长期主界面；它不能启用 Start Delivery、Confirm Dropoff、Cancel。
3. Browser QA 截图能复核当前 mobile shell；如果失败，失败原因要能被定位到 service-worker、cache version、offline shell 或 browser timeout。
4. 文档和收口必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 6. 需要做什么

Full-Stack implementation 需要：

- 审视 `mobile/web/service-worker.js` 的 cache name/version、install/activate/fetch 策略，确保旧缓存可被清理或被新版本接管。
- 审视 `mobile/web/offline.html` 和恢复文案，确保旧 offline shell 不冒充当前 app，不启用控制动作，不暗示真实手机/browser 通过。
- 如需要，调整 `mobile/web/app.js` 或 manifest 相关字段，让 Browser QA 能触发当前 shell 渲染和恢复提示。
- 更新 `docs/product/mobile_user_flow.md`，补充 `mobile_pwa_cache_recovery_gate` 的证据边界。
- 补充或调整 `mobile/web/test_mobile_web_entrypoint.py` 中围绕 cache recovery/offline shell 的最小软件测试。

Robot consultation 需要：

- 只读确认 Full-Stack 方案没有改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 只读确认没有新增 robot commands、ACK、cursor、diagnostics fetch 或 ROS2 control path。

Product closeout 后续需要：

- 实现完成后更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 仅在有实际可复核证据后保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；不得提高 O5/O1，不得宣称真实手机通过。

## 7. 优先级和验收口径

P0：

- 本地 PWA 不再长期停在旧 offline shell。
- Browser QA 能看到当前 `mobile/web` shell 或给出可定位失败。
- Start Delivery、Confirm Dropoff、Cancel 保持 fail-closed，除既有安全 gate 外不得被 cache recovery 放开。

P1：

- Offline shell recovery 文案中文优先，明确这是恢复/刷新路径，不是成功或真实手机 proof。
- 文档同步更新，写清 `software_proof` / `not_proven` 边界。

验收口径：

- Full-Stack 必须运行 targeted unit/static/browser validation 和 scoped `git diff --check`。
- Robot 咨询必须明确 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍成立。
- Product 最终必须明确 Objective 5 和 Objective 1 不提高；Objective 4 只记录本地 Browser QA recovery 的 software-proof，不写成真实手机/browser external proof。

## 8. 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 只读咨询：`robot-software-engineer`
- 规划和收口：`product-okr-owner`

## 9. 风险、阻塞和需要补齐的证据链

- 真实手机/browser 证据仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 未证明。
- Objective 5 external proof 仍缺：真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 未证明。
- Objective 1 / PR #5 仍缺：WAVE ROVER/UART/HIL、真实反馈日志、2D LiDAR / ToF 真实材料未证明。
- PR #4 仍缺：真实 route/elevator field pass、真实 Nav2/fixed-route、真实门状态、真实楼层确认、真实 delivery result 未证明。

## 10. 需要创建或更新的 sprint 文档

当前规划阶段只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后再创建/更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
