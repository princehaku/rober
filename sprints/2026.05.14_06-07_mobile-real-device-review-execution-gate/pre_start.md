# Sprint 2026.05.14_06-07 Mobile Real Device Review Execution Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-14 06:00 Asia/Shanghai
- 目标证据边界：`software_proof_docker_mobile_real_device_review_execution_gate`
- 新 sprint folder：`sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/`

## 用户价值和产品北极星

用户价值是把上一轮真实设备验收 `review handoff package` 推进到“人工评审执行记录/执行包”。评审者和支持同学需要在手机/PWA 首屏看到 checklist 执行状态、review result/status、evidence items readiness、operator/reviewer notes、blocked reason、next evidence request、redaction/source boundary 和 `not_proven`，而不是只能拿到一份待交接材料。

产品北极星不变：手机是普通用户唯一入口。当前主机只有 Docker，没有真实硬件、真实手机、真实公网或 Objective 5 外部材料，因此本轮只推进 Objective 4 的执行记录软件闭环和 Robot metadata-only 围栏，不能宣称真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、真实 delivery 或 Objective 5 完成度提升。

## 开工证据

- `OKR.md` 4.1 当前快照：Objective 5 约 68%，是数字最低 Objective；Objective 4 约 82%。但 `OKR.md` 第 6 节明确要求，只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料可用时才继续推进 Objective 5 completion。
- 最新 sprint `sprints/2026.05.14_05-06_mobile-real-device-review-handoff-gate/final.md`：已完成 `software_proof_docker_mobile_real_device_review_handoff_gate`，把真实设备验收材料从 decision 推进到可交接人工评审的 review handoff package，并用 Robot metadata-only fence 证明 metadata 不进入 command、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success。
- 最新 sprint final 明确下一步：如果继续没有 Objective 5 外部材料，应使用 review handoff package 进入 Objective 4 的真实设备人工验收执行、证据导入或真实 device behavior 记录。
- 用户要求：用 team 继续完成 OKR，重新在功能往前走；测试只做围栏；优先推进低完成度；最后提交并推送。

## 本轮核心抓手

本轮抓手是 `mobile_real_device_review_execution*`：把 `mobile_real_device_review_handoff*` 从“可交接”推进为“可记录人工评审执行”。它必须回答：

- checklist 是否被执行：review execution checklist、evidence items readiness、review result/status。
- 人工评审写了什么：operator notes、reviewer notes、blocked reason、next evidence request。
- 证据边界是否清楚：redaction status、source boundary、ACK-not-delivery、`not_proven`。
- 为什么不能放行动作：缺真实设备行为、production app、真实 PWA install prompt/user choice 或 O5 外部材料时，Start / Confirm / Cancel 继续 fail closed。

## Scope 和 Owner

- Task A Full-stack：实现手机/PWA review execution checklist、执行状态、notes、blocked reason、next evidence request、phone-safe copy package，并更新 `mobile/README.md`、`docs/product/mobile_user_flow.md` 和本 sprint `tech-done.md`。
- Task B Robot：实现 remote bridge `mobile_real_device_review_execution*` metadata-only fence tests，并更新 `docs/interfaces/ros_contracts.md` 和本 sprint `tech-done.md`。
- Task C Product：A/B 完成后验收证据，更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。

Task A 与 Task B 文件范围互不重叠，必须并行；Task C 必须在 A/B 返回后执行。

## 风险和阻塞

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；本轮转 Objective 4 是避免重复消费外部证据 blocker。
- 本轮仍缺真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice；review execution package 只能记录执行状态、blocker 和下一步证据请求，不能写成真实验收通过。
- 本轮没有 WAVE ROVER、Orange Pi UART、Nav2/fixed-route 或真实 delivery；Objective 1/2/3 不应被本轮证据抬升。
- Robot 侧必须证明 execution metadata 是 metadata-only，不触发 command/ACK/cursor/terminal ACK/production readiness/HIL/delivery success。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续执行完成后由 Task A/B/C 更新或创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
