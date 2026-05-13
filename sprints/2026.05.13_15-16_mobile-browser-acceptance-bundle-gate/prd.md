# Sprint 2026.05.13_15-16 Mobile Browser Acceptance Bundle Gate - PRD

## 用户价值

普通手机用户、测试者和售后支持需要一份可以直接复制/交接的手机浏览器验收材料，而不是分散在 readiness、operation log、action feedback、cloud summary 和 diagnostics 里的工程字段。最近多轮 closeout 反复留下同一缺口：没有真实手机设备/browser、production app、真实 PWA install prompt，且 ACK 不能当 delivery success，metadata 不能触发 robot action。

本轮把这些缺口做成手机首屏的“浏览器验收包/验收证据”能力：用户能看到当前浏览器入口能证明什么、不能证明什么、为什么动作仍被禁用，以及交给支持时应复制哪份脱敏摘要。

## 产品北极星

普通用户只用手机完成送垃圾任务；当系统尚未达到真实设备验收时，手机也必须清楚解释边界、阻止误操作，并提供可复盘的支持交接材料。

## OKR 映射

- Objective 4 KR1：手机最小流程补齐“验收证据/支持交接”步骤，连接设备后能确认当前浏览器入口是否达到可控条件。
- Objective 4 KR4：远程诊断最小数据包推进为用户可复制的 acceptance bundle，包含版本/状态/失败原因的 phone-safe 摘要而不是 raw diagnostics dump。
- Objective 4 KR5：普通用户不接触命令行、ROS2、串口或硬件调试，也能知道为什么不能发车、下一步应找支持还是等待真实设备验收。
- Objective 4 KR7：手机端 UI 继续向美观、直接可用、主路径清晰推进；本轮只证明 Docker/local software gate，不声明真实手机/browser 通过。

## KR 拆解或更新

- KR4.1：新增 `trashbot.mobile_browser_acceptance_bundle.v1` 或等价 phone-safe bundle 展示，覆盖 viewport、touch、PWA/offline、diagnostics、cloud gate、action fail-closed、ACK 语义和 client timestamp。
- KR4.2：Bundle 可复制/显示为支持交接材料，过滤 tokens、Authorization、OSS AK/SK、DB/queue URL、ROS topics、serial、`/cmd_vel`、local paths、tracebacks、checksums 和完整 artifacts。
- KR4.3：缺真实手机设备/browser、production app、真实 PWA install prompt 或 safe-to-control 证据时，Start/Confirm/Cancel 保持 disabled；Diagnostics/Support Handoff 保持可用。
- KR4.4：Robot compatibility fence 证明 bundle metadata-only 字段不触发 collect/dropoff/cancel、不 POST ACK、不推进或持久化 cursor。
- KR4.5：Closeout 只在 Task A/B 都完成且验证通过后，保守更新 Objective 4，并保留所有真实设备、真实云、真实机器人证据缺口。

## 本轮核心抓手

将已有 O4 mobile readiness 能力从“状态可见”推进到“验收证据可交接”：

- 在 mobile web 首屏组织一份可读、可复制、脱敏的 acceptance bundle。
- 在 fixture 和 smoke 中证明 blocked-by-design、fail-closed、ACK 语义和敏感字段过滤。
- 在 robot remote bridge/protocol 中证明这些 bundle 字段不会进入 command envelope。

## 范围

### In Scope

1. `mobile/web/` 首屏增加浏览器验收包/验收证据 panel 或等价交互。
2. Bundle 来源优先消费 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle`，缺失时可从已有 phone-safe readiness/status/diagnostics 派生 blocked-by-design 摘要。
3. `mobile/fixtures/mobile_web_status.fixture.json` 增加 blocked acceptance bundle 示例。
4. `mobile/test_mobile_web_entrypoint.py` 增加 targeted smoke，覆盖 panel 文案、copy material、安全过滤、fail-closed 和 ACK 不是 delivery success。
5. `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 同步证据边界和 metadata-only contract。
6. Robot tests 增加 bundle metadata-only compatibility fence。

### Out of Scope

- 不做真实手机设备/browser 验收。
- 不做 production app、账号、登录、应用商店打包或真实 PWA install prompt。
- 不做真实云/4G、OSS/CDN live traffic、production DB/queue。
- 不做 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- 不把 ACK、receipt、metadata、browser smoke 或 Docker/local fixture 写成真实任务成功。

## 优先级和验收口径

- P0：手机首屏存在“浏览器验收包/验收证据”能力，显示或复制 phone-safe bundle。
- P0：Bundle 包含 viewport/touch/PWA/offline/diagnostics/cloud/action fail-closed/ACK/client timestamp/evidence boundary/not-proven 摘要。
- P0：Bundle 和 diagnostics/support copy 不包含 tokens、ROS topics、serial、`/cmd_vel`、完整 artifact、credential URL 或本地敏感路径。
- P0：Start/Confirm/Cancel 在 blocked、offline、pending ACK、manual takeover、缺 production app 或缺 safe-to-control 时继续 fail closed；Diagnostics/Support 可用。
- P0：Robot metadata-only fence 覆盖三个字段名：`mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle`。
- P1：Closeout 文档只声明 `software_proof_docker_mobile_browser_acceptance_bundle_gate`，不声明真实设备、真实云、真实送达或 HIL。

## 对应责任 Engineer

- Task A Full-stack Mobile Browser Acceptance Bundle Gate：`full-stack-software-engineer`。
- Task B Robot Metadata Compatibility Fence：`robot-software-engineer`。
- Task C Product Closeout：`product-okr-owner`。

## 风险、阻塞和需要补齐的证据链

- 真实手机设备/browser、production app 和真实 PWA install prompt 仍是主要证据缺口。
- 当前主机 Docker-only，不能补真实云/4G、真实 OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Acceptance bundle 容易被误读为“验收完成”；文案必须写清 blocked-by-design 和 `not_proven`。
- ACK、HTTP accepted 或 action receipt 只能是 accepted/processing evidence，不是 delivery success。
- Bundle metadata 只属于 phone/support/readiness，不属于 command/status/ACK envelope。

## 需要创建或更新的 sprint 文档

- 已创建/填写：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 待 Task A/B 完成后更新：`tech-done.md`、`side2side_check.md`、`final.md`。
