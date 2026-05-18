# Sprint 2026.05.18_23-24 Mobile Real Device Acceptance Execution Pack - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-18 23:24 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 本轮切口：`mobile_real_device_field_trial_acceptance_execution_pack*`
- 证据边界：`software_proof` / `not_proven`
- 安全边界：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 用户原话和本轮方向

CEO 要求：“开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的OKR；每条建议都要基于具体证据；用team继续完成OKR，重新在功能往前走；测试只围栏；优先推进OKR低完成度；本机没有真实硬件，只有docker；最后提交并推送。”

本轮不继续堆本地 O5 metadata，也不把 O1 / PR #4 / PR #5 的真实材料缺口包装成完成。当前 Docker-only 主机没有真实硬件、真实串口、真实外部云、真实手机 device/browser 证据，因此选择 Objective 4 的可执行 fallback：把上一轮真实手机验收复核交接材料推进为现场 owner 可执行的验收执行包。

## 3. 上轮未完成项和阻塞

- Objective 5 数字最低，约 68%，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser external proof。
- Objective 1 约 81%，但缺真实 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 指出的真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #4 电梯 assisted delivery 已并入主线，但仍缺真实 route/elevator field materials：真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` task record/completion signal、dropoff/cancel completion 或 delivery result。
- 最新 `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/final.md` 已完成 `mobile_real_device_field_trial_acceptance_review_handoff*`，下一步最可执行的是生成真实手机验收 execution package，而不是声称真实手机或 delivery success。

## 4. PR / Review 证据

- PR #5 P1：`docs/product/production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 曾矛盾，说明硬件完成叙事必须严守真实材料边界。
- PR #5 P2：新增 sensor mix / ToF channel assumptions 缺 `docs/vendor/` source，说明 Objective 1 / hardware ladder 不能在无 vendor/source/receipt/installation evidence 时继续包装为完成。
- PR #5 P2：OKR lowest narrative 曾与表格不一致，本轮必须在 `tech-plan.md` 明确 Objective 5 数字最低但不可执行、Objective 1 次低但硬件材料不可得、选择 Objective 4 的理由。
- PR #4：电梯 assisted delivery 已并入主线，但后续缺真实 route/elevator field materials，本轮不能把手机执行包写成真实电梯、Nav2、fixed-route 或投放完成。
- 20-21 final：已明确 O5/O1 真实材料不可得，切到 Objective 4 真机材料链路。
- 21-22 final：完成 `mobile_real_device_field_trial_acceptance_review_decision*`，保持 fail-closed。
- 22-23 final：完成 `mobile_real_device_field_trial_acceptance_review_handoff*`，建议下一步把 handoff packet 带到真实 iPhone/Android / production app / PWA prompt/user choice 现场。

## 5. 本轮核心抓手

新增 `mobile_real_device_field_trial_acceptance_execution_pack*`，消费上一轮 acceptance review handoff / summary / copy，生成：

- 现场 owner checklist。
- evidence capture steps。
- redaction requirements。
- rerun commands。
- `next_required_evidence`。
- 面向手机和现场 owner 的 `safe_copy`。

执行包必须通过 mobile/web 只读 panel、Robot diagnostics safe alias、产品文档和接口文档暴露。所有主操作继续 fail-closed，不证明真实手机验收、真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL 或 O5 external proof。

## 6. Owner 和团队分工

- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读 panel、fixture、前端围栏测试、`docs/product/mobile_user_flow.md`。
- Robot Platform Engineer：主责 Robot diagnostics safe alias、接口文档和 diagnostics 围栏测试。
- Product Manager / OKR Owner：主责 sprint closeout、OKR/progress log 收口口径和 evidence boundary 审核。
- Hardware Infra Engineer：只读事实补充，核对 PR #5 2D LiDAR / ToF 仍缺真实 source/receipt/installation/HIL-entry，不改硬件配置。

## 7. 预启动风险

- 本轮只生成执行包与只读暴露，不会产生真实手机现场材料。
- 没有真实手机、真实云、真实 WAVE ROVER/UART/HIL，因此 OKR 不应因本轮 planning 或 local software proof 大幅上调。
- 若 Engineer 在实现中触碰硬件事实、引脚、电压、UART、波特率、反馈协议或传感器材料，必须重新查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向文件并在说明中引用。
- 本轮文件范围应拆清，所有 owner 都不独占整个仓库，禁止回滚他人改动。

