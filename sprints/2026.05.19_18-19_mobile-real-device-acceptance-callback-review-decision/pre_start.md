# Sprint 2026.05.19_18-19 Mobile Real Device Acceptance Callback Review Decision - Pre Start

## 1. Sprint 类型

sprint_type: epic

主题：`mobile-real-device-acceptance-callback-review-decision`

本轮启动 fresh Epic sprint，目标是在上一轮 `2026.05.19_17-18_mobile-real-device-acceptance-callback-intake` 的基础上继续功能往前走：新增 fail-closed `mobile_real_device_field_trial_acceptance_execution_callback_review_decision`，把真实手机验收执行回调入口中的 received / missing / rejected 状态转成只读复核决策、owner handoff、next_required_evidence 和 rerun guidance。

## 2. 开工证据

- `OKR.md` 4.1 更新时间为 2026-05-19 17:19 Asia/Shanghai。
- 最新 sprint 是 `2026.05.19_17-18_mobile-real-device-acceptance-callback-intake`。
- 上一轮已完成 `mobile_real_device_field_trial_acceptance_execution_callback_intake`：手机端和 Robot diagnostics 能展示 accepted / missing / rejected callback evidence、same safe `evidence_ref`、owner handoff、next_required_evidence 和 rerun_guidance。
- 当前还没有 callback review decision，因此现场材料回调只能被接收，不能被产品化地复核为 blocked / needs_rerun / ready_for_field_owner_decision 之类的只读决策。

## 3. 用户价值和产品北极星

用户价值：现场 owner 提交真实手机验收执行回调后，普通手机用户和调试 owner 能看到“这批回调材料是否足够、缺什么、由谁继续补、是否需要重跑”，而不是只看到原始 intake 状态。

产品北极星：普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能完成送垃圾任务并理解失败时下一步。本轮只补真实手机验收材料的复核决策链，不声明真实手机验收通过。

## 4. OKR 映射和启动理由

- Objective 5 约 68%，数字最低，但 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof，不能继续本地 O5 metadata depth。
- Objective 1 约 81%，PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 和 WAVE ROVER/UART/HIL；本轮不能关闭或提高 O1。
- Objective 2 / Objective 3 约 99%，route/elevator real-material blocker 已多轮进入 software-proof wrapper；没有真实现场材料时不再重复消费同一 blocker。
- Objective 4 约 99%，但真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 现场验收仍未证明。上一轮已完成 callback intake，本轮继续 O4 的 fail-closed review decision 是当前最可执行的下一步。

## 5. 证据边界

本轮证据边界必须保持：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

本轮不证明真实手机验收通过，不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice、Objective 5 external proof、PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需真实硬件材料、WAVE ROVER/UART/HIL、真实 Nav2/fixed-route、真实 route/elevator field pass、dropoff/cancel completion 或 delivery success。

## 6. Owner 和阶段职责

- Full-Stack owner：实现手机端只读 callback review decision panel、fixture、targeted tests，并同步 `docs/product/mobile_user_flow.md`。
- Robot owner：实现 operator gateway diagnostics 的 review decision safe alias、targeted diagnostics unittest，并同步接口文档。
- Product owner：本轮先创建 `pre_start.md`、`prd.md`、`tech-plan.md`；实现完成后负责 `tech-done.md`、`side2side_check.md`、`final.md`、OKR 证据边界和 progress log 收口。

实现阶段必须并行启动 Full-Stack 与 Robot 两个 worker；Product 只做计划和最后 closeout，不写产品代码或测试代码。

## 7. 风险、阻塞和待补证据

- 本机没有真实硬件，只有 Docker；所有验证只能是 software proof。
- 缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover。
- 缺 PR #5 `PRRT_kwDOSWB9286CJ3tX` 的真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 缺 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- 缺真实 route/elevator field pass、Nav2/fixed-route runtime log、route completion signal、真实 task record、dropoff/cancel completion 和 delivery result。

## 8. 本轮需要创建或更新的 sprint 文档

计划阶段创建：

- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/pre_start.md`
- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/prd.md`
- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-plan.md`

实现和收口阶段后续必须补齐：

- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/tech-done.md`
- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/side2side_check.md`
- `sprints/2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision/final.md`

