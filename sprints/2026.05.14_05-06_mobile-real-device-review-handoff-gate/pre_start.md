# Sprint 2026.05.14_05-06 Mobile Real Device Review Handoff Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-14 05:00 Asia/Shanghai
- 目标证据边界：`software_proof_docker_mobile_real_device_review_handoff_gate`
- 新 sprint folder：`sprints/2026.05.14_05-06_mobile-real-device-review-handoff-gate/`

## 用户价值和产品北极星

用户价值是把真实设备验收从上一轮的“acceptance decision”推进到“可交接给人工评审的 review handoff session/package”。普通用户、测试同学和支持同学看到的不是 raw JSON、ROS2、cloud internals 或 ACK，而是一份可复制、脱敏、可分配 owner、能说明 blocker 和下一步证据的人工评审交接包。

产品北极星不变：手机是普通用户唯一入口。当前主机只有 Docker，没有真实硬件、真实手机、真实公网或 O5 外部材料，因此本轮只能做 Docker/local software proof 与 robot metadata-only fence，不能宣称真实设备验收、真实 PWA prompt、真实公网/4G/OSS/CDN/DB/queue、HIL 或真实 delivery 通过。

## 开工证据

- `OKR.md` 4.1 当前快照：Objective 5 约 68%，Objective 4 约 81%；Objective 5 数字最低，但第 6 节明确写明没有真实外部材料时不要继续本地 O5 metadata depth，应转向 Objective 4 的真实设备行为、production app、PWA prompt/user choice 或移动设备验收。
- 最新 sprint `2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/final.md`：已完成 `software_proof_docker_mobile_real_device_acceptance_decision_gate`，把 intake 材料推进到 decision、blocker list、next required evidence、redaction status、source boundary、ACK semantics 和 `not_proven`。
- 最新 `tech-done.md`：Task A mobile targeted tests 25 OK；Task B robot remote bridge/protocol tests 137 OK；证据边界仍是 Docker/local software proof + metadata-only fence。
- 近期反复 blocker：Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；Objective 1 仍缺 WAVE ROVER/HIL/真实串口；Objective 4 仍缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice。

## 本轮核心抓手

本轮抓手是 `mobile_real_device_review_handoff*`：在上一轮 `mobile_real_device_acceptance_decision*` 基础上，把材料组织成人工评审可用的 session/package。它必须能回答：

- 谁评审：review owner / reviewer status / session id。
- 评什么：reviewer checklist、decision status、evidence blocker、next required evidence。
- 能不能交接：redaction status、source boundary、ACK-not-delivery、`not_proven`。
- 为什么不能放行动作：缺真实设备材料时 Start / Confirm / Cancel 继续 fail closed。

## Scope 和 Owner

- Task A Full-stack：实现手机首屏 review handoff session/package 与脱敏复制包。
- Task B Robot：实现 `mobile_real_device_review_handoff*` metadata-only response fence。
- Task C Product：A/B 完成后验收、收口 sprint、谨慎更新 OKR 和 progress log。

Task A 与 Task B 文件范围互不重叠，必须并行；Task C 必须在 A/B 返回后执行。

## 风险和阻塞

- 本轮没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice，因此 review handoff 只能说明“可交接人工评审”或“被证据 blocker 阻塞”，不能说明真实设备验收通过。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，因此 Objective 5 保持 blocked，不应继续堆本地 O5 metadata。
- 本轮没有 WAVE ROVER、Orange Pi UART、Nav2/fixed-route 或真实 delivery，因此 Objective 1/2/3 不应被本轮证据抬升。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续执行完成后由 Task A/B/C 更新或创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
