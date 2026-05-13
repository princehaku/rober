# Sprint 2026.05.14_00-01 Mobile Device Handoff Session Gate - PRD

## 产品目标

把现有 `mobile_device_evidence_capture` 推进为一个面向真实手机验收的 `mobile_device_handoff_session`。普通用户或测试人员打开手机页面后，应能获得一份可执行、可复制、边界清晰的验收会话包，用于把真实设备现场信息交给支持人员，而不是只看到若干 readiness panel。

## 用户价值和产品北极星

产品北极星：普通手机用户是唯一入口，用户不接触命令行、不理解 ROS2、不插线调试，也能发起任务、看懂状态、知道失败时如何求助。

本轮用户价值：

- 测试人员知道从哪个入口 URL 开始验收，而不是在多个本地/云/fixture 地址之间猜测。
- 测试人员按步骤观察真实手机浏览器、PWA/display-mode/install prompt、offline shell、touch target、viewport 和证据复制状态。
- 支持人员收到 phone-safe handoff session 后，可以判断当前缺的是设备/browser/PWA/production app 证据，还是云/robot/command gate 证据。
- 产品侧继续保持保守边界：handoff session 不是 Start/Confirm/Cancel 放行依据，也不是真实送达成功依据。

## OKR 映射

- 主要映射：Objective 4 KR5、KR7。真实手机用户验收标准要求普通用户不接触命令行、不插线调试，也能理解失败状态；手机端 UI 要适配真实设备，并满足美观、可用、首屏可交互和移动端验收口径。
- 支撑映射：Objective 5。当前 O5 约 68% 且最低，但在缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 时，不继续堆本地 O5 metadata。本轮转 O4 是对 `OKR.md` 第 6 节 fallback 规则的执行。
- 非映射：本轮不提升 Objective 1/2/3，不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff、真实 cancel 或真实 delivery。

## KR 拆解或更新

本轮不直接修改 `OKR.md`。计划中的可验收 KR 拆解如下：

- KR-A：`mobile/web/` 提供 `mobile_device_handoff_session`，可展示当前入口 URL、session id/reference、步骤清单和复制要求。
- KR-B：handoff session 明确列出真实手机设备/browser/PWA/install prompt/offline shell/touch target/viewport 观察项，并与已有 evidence capture package 对齐。
- KR-C：handoff session 的 copied package 为 phone-safe，只包含支持人员需要的 reproducer metadata，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、串口、WAVE ROVER 参数、本地路径、traceback、checksum 或完整 artifact。
- KR-D：Robot compatibility fence 证明 handoff session、summary、package 属于 metadata-only，不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。
- KR-E：Product closeout 只在 A/B 证据返回后决定 Objective 4 是否谨慎上调；若没有真实外部 O5 材料，Objective 5 不上调。

## 本轮核心抓手

把“请去真实手机上验收”转换成页面内可执行的 handoff session。这个 session 要给测试人员具体下一步，而不是让测试人员猜：

- 打开哪个 URL。
- 按什么顺序观察。
- 哪些设备/PWA/install prompt 行为需要人工确认。
- 复制什么证据包。
- 复制后仍有哪些 `not_proven`。
- ACK 为什么不是送达成功。

## 范围内需求

1. `mobile/web/` 新增或升级 `mobile_device_handoff_session` 面板。
2. 面板必须包含：
   - 当前入口 URL 或安全的入口摘要；
   - session id/reference 或 client reference；
   - 真实手机验收步骤清单；
   - 设备/browser/PWA/install prompt/offline shell/touch target/viewport 观察项；
   - 证据包复制要求；
   - `ack_semantics=accepted_processing_only_not_delivery_success`；
   - `evidence_boundary=software_proof_docker_mobile_device_handoff_session_gate`；
   - `not_proven`。
3. 面板可消费已有 `mobile_device_evidence_capture`、`mobile_device_evidence_capture_summary`、`mobile_device_evidence_package`，但不得把 capture package 写成真实设备验收通过。
4. Start Delivery、Confirm Dropoff、Cancel 必须继续受既有 readiness、browser acceptance bundle、terminal action confirmation 和 command safety 控制；handoff session 不能新增放行条件。
5. Robot side 必须证明 handoff session metadata-only，不进入 command、ACK、cursor、delivery result 或 production readiness。
6. `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 后续必须同步写清本功能的 phone-safe 字段、metadata-only 边界和 not-proven 范围。

## 范围外

- 不证明真实 iPhone/Android device behavior。
- 不证明 production app。
- 不证明真实 PWA install prompt。
- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实底盘运动、真实 dropoff/cancel completion 或真实 delivery。
- 不新增账户、登录、native app、生产云配置、真实外部流量验证或硬件配置。
- 不修改 `OKR.md` 或 sprint closeout 文档，直到 A/B 返回后 Product Task C 执行。

## 优先级和验收口径

P0：

- Handoff session 必须能在 `mobile/web/` 首屏或当前手机验收区域直接看到。
- 复制包必须 phone-safe，并保留 ACK 不是 delivery success 的边界。
- Start/Confirm/Cancel 不得因 handoff session 存在而启用。
- Robot compatibility fence 必须证明 metadata-only。

P1：

- 步骤清单要能指导真实手机测试人员观察入口 URL、PWA/install prompt、display-mode/offline shell、touch target 和 viewport。
- 相关 product/interface docs 同步更新。

Product 验收只接受 A/B targeted tests、`py_compile`、`node --check`、scoped `git diff --check` 以及 closeout 文档证据。不接受口头描述、happy path 截图或 copied package 本身作为真实设备通过证明。

## 对应责任 Engineer

- Full-stack Task A：`full-stack-software-engineer`
- Robot Task B：`robot-software-engineer`
- Product Task C：`product-okr-owner`

## 风险、阻塞和证据链

- 真实手机、production app、真实 PWA install prompt 仍需后续人工或设备侧证据补齐。
- O5 真实外部材料仍缺失；本轮不得把 O4 handoff session 解释为 O5 completion。
- 若 A/B 返回的测试只覆盖 fixture/local browser，则证据边界仍是 `software_proof_docker_mobile_device_handoff_session_gate`。
- 若 copied package 中出现凭证、raw ROS topic、串口/硬件参数、本地路径或完整 artifact，Product closeout 必须阻断。
- 若 Start/Confirm/Cancel 被 handoff session 放行，必须视为 P0 回归并退回对应 Engineer 修复。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/pre_start.md`
- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/prd.md`
- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/tech-plan.md`

A/B 返回后由 Product Task C 更新：

- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/tech-done.md`
- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/side2side_check.md`
- `sprints/2026.05.14_00-01_mobile-device-handoff-session-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验收口径

本 sprint 完成时，Product 只接受以下证据：

- Task A targeted mobile unittest、`py_compile`、`node --check`、scoped diff check 通过。
- Task B targeted remote bridge/protocol unittest、`py_compile`、scoped diff check 通过。
- Task C 核对 A/B 输出后，收口文档清楚区分 software proof、真实手机设备 proof、O5 外部材料 proof 和 delivery success。
- 没有真实外部 O5 材料时，Objective 5 不上调。
